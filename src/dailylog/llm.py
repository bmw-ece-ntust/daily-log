from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMResponse:
    text: str
    raw: dict[str, Any]


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat_completions(*, base_url: str, model: str, api_key_env: str, messages: list[dict[str, str]]) -> LLMResponse:
    """OpenAI-compatible chat.completions call."""

    api_key = os.getenv(api_key_env, "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }

    raw = _post_json(url, payload, headers)
    text = ""
    try:
        text = raw["choices"][0]["message"]["content"]
    except Exception:
        text = ""

    return LLMResponse(text=text, raw=raw)
