"""
LLM 调用模块 —— 全项目唯一和模型打交道的地方。

异常体系
--------
LLMError           基类
├── LLMAPIError    API 调用失败（网络、限流、超时等），重试耗尽后抛出
└── LLMJSONError   JSON 解析失败（即使经过自修正后仍失败）

核心函数
--------
chat(messages, ...) -> str      普通对话，返回文本
chat_json(messages, ...) -> dict  要 JSON 的对话，返回解析好的 dict

注意：openai 库采用延迟导入，只有首次实际调用 LLM 时才会 import openai。
这样没装 openai 的环境也能安全导入本模块（比如纯逻辑测试）。
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from LLM.src import config

# ---------------------------------------------------------------------------
# 异常定义
# ---------------------------------------------------------------------------


class LLMError(Exception):
    """LLM 调用相关异常的基类。"""


class LLMAPIError(LLMError):
    """API 调用失败（网络、限流、超时、鉴权等）。"""


class LLMJSONError(LLMError):
    """LLM 输出的 JSON 解析失败（即使经过自修正后）。"""

    def __init__(
        self,
        message: str,
        raw_response: str | None = None,
        corrected_response: str | None = None,
    ) -> None:
        self.raw_response = raw_response
        self.corrected_response = corrected_response
        super().__init__(message)


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

_client: Any | None = None


def _get_client() -> Any:
    """延迟导入 openai 并返回 OpenAI 客户端实例（单例）。"""
    global _client
    if _client is None:
        import openai  # noqa: F401 — 延迟导入，纯逻辑测试时可跳过

        _client = openai.OpenAI(api_key=config.api_key, base_url=config.base_url)
    return _client


def _call_openai(
    messages: list[dict[str, str]],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    max_retries: int,
) -> str:
    """调用 LLM 并返回文本。

    内部处理指数退避重试（2^attempt 秒），覆盖网络断开、限流、超时等。
    所有重试耗尽后抛出 LLMAPIError。
    """
    client = _get_client()
    last_exception: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content: str | None = response.choices[0].message.content
            return content or ""
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                sleep_seconds = 2**attempt
                time.sleep(sleep_seconds)

    raise LLMAPIError(
        f"API 调用失败，已重试 {max_retries} 次",
    ) from last_exception


def _clean_json(text: str) -> str:
    """从 LLM 输出的文本中提取最有可能的 JSON 字符串。

    处理步骤（按优先级）：
    1. 去除首尾空白
    2. 尝试提取 markdown 代码块 ```json ... ```
    3. 尝试提取 markdown 代码块 ``` ... ```
    4. 以 "{" 开头则直接返回
    5. 正则提取第一个 { ... } 块
    6. 全部失败则原样返回（交由 json.loads 报错）
    """
    text = text.strip()

    # 提取 ```json ... ```
    m = re.search(r"```(?:json)\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        candidate = m.group(1).strip()
        if candidate:
            return candidate

    # 提取 ``` ... ```
    m = re.search(r"```\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        candidate = m.group(1).strip()
        if candidate:
            return candidate

    # 直接以 "{" 开头
    if text.startswith("{"):
        return text

    # 正则取第一个 { ... }
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    return text


def _try_parse_json(raw: str) -> dict[str, Any]:
    """尝试将 raw 文本清洗后解析成 dict。

    返回 (parsed_dict, error_message) 元组。
    成功时 error_message 为 None，失败时 parsed_dict 为 None。
    """
    cleaned = _clean_json(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMJSONError(
            f"JSON 解析失败：{e}\n清洗后文本：{cleaned[:500]}",
            raw_response=raw,
        ) from e


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    max_retries: int | None = None,
) -> str:
    """普通对话：发消息、拿回文本。

    遇到网络错误 / 限流会自动以指数退避重试。
    所有参数均有合理的默认值（来自 config），也可按需覆盖。
    """
    return _call_openai(
        messages,
        model=model or config.model,
        temperature=temperature if temperature is not None else config.chaper_temperature,
        max_tokens=max_tokens or config.max_tokens,
        max_retries=max_retries or config.max_retries,
    )


def chat_json(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    max_retries: int | None = None,
) -> dict[str, Any]:
    """要 JSON 的对话：发消息、拿回一个解析好的字典。

    流程：
    1. 调用 chat() 获取原始响应
    2. 清洗、解析 JSON
    3. 如果解析失败，把错误回喂给模型，让模型自修正一次
    4. 仍失败则抛 LLMJSONError（携带原始响应和修正响应）

    自修正时会在原 messages 末尾追加一条消息，
    说明「你刚才的输出不是合法 JSON，请只输出 JSON」。
    """
    raw = chat(
        messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
    )

    try:
        return _try_parse_json(raw)
    except LLMJSONError as first_err:
        pass

    # ----- 自修正：回喂错误信息，让模型自己改一次 -----
    correction_prompt = (
        "你上面的输出不是合法的 JSON。请只输出合法的 JSON 对象，"
        "不要添加任何 markdown 格式标记（不要用 ```），不要添加任何额外文字。\n\n"
        f"你的输出：\n{raw}\n\n"
        f"解析错误：\n{first_err}"
    )
    corrected_messages = [
        *messages,
        {"role": "assistant", "content": raw},
        {"role": "user", "content": correction_prompt},
    ]
    raw2 = chat(
        corrected_messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
    )

    try:
        return _try_parse_json(raw2)
    except LLMJSONError as second_err:
        raise LLMJSONError(
            "JSON 解析失败（自修正后仍失败）",
            raw_response=raw,
            corrected_response=raw2,
        ) from second_err