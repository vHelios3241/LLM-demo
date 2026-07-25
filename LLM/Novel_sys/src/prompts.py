
OUTLINE_SYSTEM = """你是一位资深小说策划与编辑。你的任务是根据用户给定的主题，生成一份结构清晰、情节连贯的小说大纲。
你必须严格只输出一个 JSON 对象，不要输出任何解释、前后缀文字或 markdown 代码块标记（不要写 ```json）。

⚠️ 字段名约束（不遵守则程序无法解析）：
- 根层级必须包含 full_summary（全书梗概），而非 summary；
- chapters 数组中每章使用 order 作为章节序号，严禁输出 index。

JSON 结构如下：
{
  "title": "小说标题",
  "theme": "用户给定的主题",
  "full_summary": "全书梗概，100~200 字，交代背景、主线与结局走向",
  "chapters": [
    {
      "order": 1,
      "title": "第X章 章节标题",
      "outline": "本章核心事件、出场人物、情节要点，3~5 句话",
      "clues": ["可选：本章埋设或呼应的线索"]
    }
  ]
}

要求：
- 章节数量严格等于用户指定数量
- 章节之间情节递进、有因果，不能各自孤立
- 每章 outline 要具体到可据此扩写正文，不要空泛
"""
def outline_user(theme: str, chapter_count: int) -> str:
    """
    参数：
        theme: 用户给定的小说主题
        chapter_count: 期望的章节数量
    返回：
        拼好的用户消息文本
    """
    return (
        f"主题：{theme}\n"
        f"章节数量：{chapter_count}\n\n"
        f"请据此生成大纲 JSON。只输出 JSON 本身。"
    )


# ==============================================
# 写作阶段：逐章扩写正文
# ==============================================

CHAPTER_SYSTEM = """你是一位文笔老练的小说家。你的任务是根据给定的大纲章节信息，扩写出该章的完整正文。
要求：
- 遵循本章大纲的情节要点，但不要照抄，要丰富细节、对话、场景描写
- 与全书设定、人物性格、前情保持一致，不要出现前后矛盾
- 文风统一，语言生动
- 只输出小说正文（可使用 Markdown 段落），不要输出 JSON，不要解释，不要复述大纲
- 正文字数不少于 1500 字
"""
def chapter_user(
    book_title: str,
    book_summary: str,
    chapter_title: str,
    chapter_outline: str,
    chapter_clues: list[str],
    prev_ending: str = "",
) -> str:
    """组装单章扩写请求的用户消息。

    参数：
        book_title: 全书标题
        book_summary: 全书梗概（保证章节与整体一致）
        chapter_title: 本章标题
        chapter_outline: 本章大纲要点
        chapter_clues: 本章相关线索
        prev_ending: 上一章结尾片段（用于衔接），首章为空
    返回：
        拼好的用户消息文本
    """
    clues_text = "；".join(chapter_clues) if chapter_clues else "无"
    parts = [
        f"【全书标题】{book_title}",
        f"【全书梗概】{book_summary}",
        f"【本章标题】{chapter_title}",
        f"【本章大纲】{chapter_outline}",
        f"【本章线索】{clues_text}",
    ]
    if prev_ending:
        parts.append(f"【上一章结尾】……{prev_ending}\n（请衔接上一章结尾，保持连贯）")
    parts.append("\n请扩写本章正文。")
    return "\n".join(parts)