from __future__ import annotations

import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMConfig:
    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
        self.enabled = bool(self.api_key)

    def status_text(self) -> str:
        if self.enabled:
            return f"已启用 · {self.model} @ {self.base_url}"
        return "未配置 LLM_API_KEY（将使用本地模板生成，适合先跑通流程）"


def chat_json(system: str, user: str, config: LLMConfig | None = None) -> dict[str, Any]:
    """Call OpenAI-compatible chat API and parse JSON object from the reply."""
    cfg = config or LLMConfig()
    if not cfg.enabled:
        raise RuntimeError("LLM 未启用")

    payload = {
        "model": cfg.model,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=90.0) as client:
        resp = client.post(f"{cfg.base_url}/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)
