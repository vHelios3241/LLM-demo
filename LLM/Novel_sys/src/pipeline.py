"""
编排模块：串起「生成大纲 → 逐章扩写 → 导出成书」的完整流程。

对外入口函数
------------
run(theme, chapter_count, output_dir)  -> dict
"""

from __future__ import annotations

from typing import Any

from LLM.src import config
from LLM.src.export import export_markdown, export_word
from LLM.src.llm_client import chat, chat_json
from LLM.src.prompts import CHAPTER_SYSTEM, OUTLINE_SYSTEM, chapter_user, outline_user
from LLM.src.schema import Chapter, Novel


# ---------------------------------------------------------------------------
# 1. 生成大纲
# ---------------------------------------------------------------------------


def generate_outline(
    theme: str,
    chapter_count: int,
    temperature: float | None = None,
) -> Novel:
    """调用 LLM 生成小说大纲，并以 Pydantic 模型校验。

    流程：
    1. 请求 LLM 输出 JSON 格式大纲
    2. 用 ``Novel.model_validate()`` 校验结构合法性
    3. 校验失败 → temperature 降低 0.2（下限 0.1）后重试一次
    4. 仍失败则抛出异常

    Args:
        theme: 小说主题。
        chapter_count: 章节数。
        temperature: 可选，覆盖默认温度。

    Returns:
        校验通过的 Novel 对象（各章 body 为空字符串）。

    Raises:
        ValueError: 大纲校验失败（重试后仍失败）。
    """
    messages = [
        {"role": "system", "content": OUTLINE_SYSTEM},
        {"role": "user", "content": outline_user(theme, chapter_count)},
    ]

    temp = temperature if temperature is not None else config.outline_temperature

    for attempt in range(2):  # 最多尝试两次（含降温重试）
        response: dict[str, Any] = chat_json(
            messages,
            temperature=temp,
            max_tokens=4096,
        )

        try:
            novel = Novel.model_validate(response)
            # 确认章节数与要求一致
            if len(novel.chapters) != chapter_count:
                raise ValueError(
                    f"期望 {chapter_count} 章，但 LLM 返回了 {len(novel.chapters)} 章"
                )
            # 将所有 chapter.body 清空
            for ch in novel.chapters:
                ch.body = ""
            return novel
        except Exception as e:
            if attempt == 0:
                # 降温后重试
                temp = max(temp - 0.2, 0.1)
                continue
            raise ValueError(f"大纲校验失败，已重试仍不合法：{e}") from e

    # 不会走到这里，但满足类型检查
    raise RuntimeError("unreachable")


# ---------------------------------------------------------------------------
# 2. 扩写单章
# ---------------------------------------------------------------------------


def write_chapter(novel: Novel, chapter_index: int, prev_ending: str) -> str:
    """调用 LLM 扩写指定章节的正文。

    Args:
        novel: 包含全部章节目录及大纲的小说对象。
        chapter_index: 从 0 开始的章节索引。
        prev_ending: 上一章末尾文本（首章传空字符串）。

    Returns:
        扩写完成的本章正文。
    """
    chapter = novel.chapters[chapter_index]

    user_msg = chapter_user(
        book_title=novel.title,
        book_summary=novel.full_summary,
        chapter_title=f"第{chapter.order}章 {chapter.title}",
        chapter_outline=chapter.outline,
        chapter_clues=chapter.clues,
        prev_ending=prev_ending,
    )

    messages = [
        {"role": "system", "content": CHAPTER_SYSTEM},
        {"role": "user", "content": user_msg},
    ]

    body = chat(
        messages,
        temperature=config.chaper_temperature,
        max_tokens=4096,
    )

    return body.strip()


# ---------------------------------------------------------------------------
# 3. 主流程
# ---------------------------------------------------------------------------


def run(
    theme: str,
    chapter_count: int,
    output_dir: str = "output",
) -> dict[str, Any]:
    """完整的写书流程：生成大纲 → 逐章扩写 → 导出。

    Args:
        theme: 小说主题。
        chapter_count: 章节数量。
        output_dir: 导出目录，默认为 ``output``。

    Returns:
        包含执行结果的字典：:

            {
                "novel": Novel,          # 已填充正文的小说对象
                "errors": list[str],     # 失败的章节错误信息列表
            }
    """
    # ── 阶段一：生成大纲 ──
    print(f"📖 正在生成大纲……（主题：{theme} | {chapter_count} 章）")
    novel = generate_outline(theme, chapter_count)
    print(f"✅ 大纲生成完成：《{novel.title}》")

    # ── 阶段二：逐章扩写 ──
    prev_ending = ""
    errors: list[str] = []
    total = len(novel.chapters)

    for i, chapter in enumerate(novel.chapters):
        print(f"✍️  正在扩写第 {i + 1}/{total} 章：{chapter.title}……")
        try:
            body = write_chapter(novel, i, prev_ending)
            chapter.body = body
            # 取末尾 200 字作为下一章的衔接
            prev_ending = body[-200:] if len(body) >= 200 else body
            print(f"   ✅ 第 {i + 1} 章完成（{len(body)} 字）")
        except Exception as e:
            errors.append(f"第 {i + 1} 章「{chapter.title}」：{e}")
            print(f"   ❌ 第 {i + 1} 章失败：{e}")
            # 不中断，继续下一章

    # ── 阶段三：导出 ──
    print(f"📁 正在导出……")
    md_path = export_markdown(novel, output_dir)
    print(f"   ✅ Markdown -> {md_path}")
    try:
        docx_path = export_word(novel, output_dir)
        print(f"   ✅ Word      -> {docx_path}")
    except Exception as e:
        print(f"   ⚠️  Word 导出失败（可能未安装 python-docx）：{e}")

    # ── 总结 ──
    success_count = total - len(errors)
    print(f"\n{'='*40}")
    print(f"📚 《{novel.title}》 生成完毕")
    print(f"   总章节：{total} | 成功：{success_count} | 失败：{len(errors)}")
    if errors:
        print(f"\n失败详情：")
        for err in errors:
            print(f"  - {err}")

    return {"novel": novel, "errors": errors}