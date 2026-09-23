"""AI 代码解释服务（sidecar 端，纯标准库）。

调用 DeepSeek（OpenAI 兼容）chat completions 流式接口，逐 chunk 通过
JSON-RPC notification 推送给 Electron 主进程。key 由主进程注入，
本模块不持久化、不写日志。
"""

from __future__ import annotations

import http.client
import json
import ssl
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = 60  # 秒

SYSTEM_PROMPT = (
    "你是一位资深的 Python 导师。请用中文简洁地解释代码的功能、关键语法和注意事项。"
    "如果代码存在潜在问题，请一并指出。使用 Markdown 格式，分点说明，不要复述代码。"
)


def build_user_prompt(code: str, file_name: str = "", context: str = "") -> str:
    """构建发送给 AI 的用户提示词。"""
    parts: list[str] = []
    if file_name:
        parts.append(f"文件名：{file_name}")
    if context:
        parts.append(f"上下文说明：{context}")
    parts.append("请分析以下 Python 代码：")
    parts.append("```python")
    parts.append(code)
    parts.append("```")
    return "\n".join(parts)


def explain_code_streaming(
    code: str,
    api_key: str,
    *,
    file_name: str = "",
    context: str = "",
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT,
    on_chunk: Callable[[str], None] | None = None,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """流式调用 DeepSeek，返回 {ok, full_text, model, tokens, error}。

    on_chunk 在每个 delta 到达时调用（在调用线程内同步执行）。
    cancel_event 被设置时中断流式读取，返回 cancelled 状态。
    """
    if not api_key or not api_key.strip():
        return {"ok": False, "error": "no_api_key", "full_text": "", "model": model, "tokens": 0}
    if not code or not code.strip():
        return {"ok": False, "error": "empty_code", "full_text": "", "model": model, "tokens": 0}

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(code, file_name, context)},
        ],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip()}",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    max_retries = 2
    for attempt in range(max_retries + 1):
        if cancel_event and cancel_event.is_set():
            return {"ok": False, "error": "cancelled", "full_text": "", "model": model, "tokens": 0}
        full_text_parts: list[str] = []
        tokens = 0
        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                # 非 SSE 响应（如认证失败、限流时返回普通 JSON）：直接读 body 作错误
                content_type = resp.headers.get("Content-Type", "")
                if "text/event-stream" not in content_type:
                    try:
                        body = resp.read().decode("utf-8", errors="replace")[:500]
                    except Exception:  # noqa: BLE001
                        body = ""
                    return {
                        "ok": False,
                        "error": f"non_sse_response: {body or content_type}",
                        "full_text": "",
                        "model": model,
                        "tokens": 0,
                    }
                for raw_line in resp:
                    if cancel_event and cancel_event.is_set():
                        return {
                            "ok": False,
                            "error": "cancelled",
                            "full_text": "".join(full_text_parts),
                            "model": model,
                            "tokens": tokens,
                        }
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[len("data:") :].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content:
                        full_text_parts.append(content)
                        if on_chunk:
                            on_chunk(content)
                    usage = data.get("usage") or {}
                    if usage.get("total_tokens"):
                        tokens = int(usage["total_tokens"])
            return {
                "ok": True,
                "error": "",
                "full_text": "".join(full_text_parts),
                "model": model,
                "tokens": tokens,
            }
        except urllib.error.HTTPError as e:
            # 5xx 服务端错误可重试；4xx（如 401 key 无效、400 参数错误）不重试。
            # 已向前端流式输出过内容时不重试：重试会让第二流的全文追加在
            # 第一流残片之后（文本重复错乱，且与 done 的 full_text 不一致）
            if e.code >= 500 and attempt < max_retries and not full_text_parts:
                time.sleep(2**attempt)  # 1s, 2s 指数退避
                continue
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:  # noqa: BLE001
                pass
            return {
                "ok": False,
                "error": f"http_{e.code}: {body or e.reason}",
                "full_text": "".join(full_text_parts),
                "model": model,
                "tokens": tokens,
            }
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as e:
            # HTTPException（如 IncompleteRead）是流中途断开，同样只在
            # 尚未输出任何内容时重试，理由同上
            if attempt < max_retries and not full_text_parts:
                time.sleep(2**attempt)
                continue
            return {
                "ok": False,
                "error": f"network: {e}",
                "full_text": "".join(full_text_parts),
                "model": model,
                "tokens": tokens,
            }

    # 循环每轮要么 return 要么 continue，理论上不可达；防御性兜底
    return {"ok": False, "error": "retry_exhausted", "full_text": "", "model": model, "tokens": 0}
