"""AI 大模型客户端封装（DeepSeek，OpenAI 兼容接口）。

对外只暴露两个能力：
- ``chat()``：普通对话补全
- ``chat_json()``：强制返回 JSON（结构化输出，供 Agent 拆解/汇总）

当未配置 ``DEEPSEEK_API_KEY`` 时进入 **离线降级模式**（return None），
调用方可回退到规则化逻辑，保证整套框架可无密钥运行演示。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import settings


class LLMClient:
    """轻量 LLM 客户端（可被替换/扩展为其它兼容服务）。"""

    def __init__(self) -> None:
        self._client: Optional[OpenAI] = None
        if settings.ai.api_key:
            self._client = OpenAI(
                api_key=settings.ai.api_key,
                base_url=settings.ai.base_url,
                timeout=60,
                max_retries=2,
            )

    @property
    def available(self) -> bool:
        """是否已配置 API Key（否则只能走离线降级逻辑）。"""
        return self._client is not None

    def chat(self, messages: List[Dict[str, str]], *,
             temperature: float | None = None,
             max_tokens: int | None = None) -> Optional[str]:
        """普通对话补全；无 Key 或出错返回 None。"""
        if not self._client:
            return None
        try:
            resp = self._client.chat.completions.create(
                model=settings.ai.model,
                messages=messages,
                temperature=temperature if temperature is not None else settings.ai.temperature,
                max_tokens=max_tokens or settings.ai.max_tokens,
            )
            return resp.choices[0].message.content
        except Exception:
            return None

    def chat_json(self, messages: List[Dict[str, str]], *,
                  temperature: float | None = None) -> Optional[Dict[str, Any]]:
        """以 JSON 模式对话；解析失败返回 None。"""
        if not self._client:
            return None
        try:
            resp = self._client.chat.completions.create(
                model=settings.ai.model,
                messages=messages,
                temperature=temperature if temperature is not None else settings.ai.temperature,
                max_tokens=settings.ai.max_tokens,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content)
        except Exception:
            return None


#: 全局唯一客户端（懒构造）
_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
