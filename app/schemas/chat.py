"""聊天/Agent Schema。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """一次对话请求。"""

    user_id: int = 0
    conversation_id: Optional[int] = None
    message: str = Field(..., min_length=1, max_length=4000)
    replan: bool = Field(False, description="是否为对上一方案的反馈重规划")
    previous_session_id: Optional[int] = None


class ChatResponse(BaseModel):
    ok: bool = True
    message: str = ""
    conversation_id: Optional[int] = None
    agent_session_id: Optional[int] = None
    answer: Optional[str] = None
    plan: Optional[Any] = None
    agent_results: List[Dict[str, Any]] = []
    agent_status: Dict[str, str] = {}


class ConversationListItem(BaseModel):
    id: int
    title: Optional[str] = None
    status: Optional[str] = None


class MessageItem(BaseModel):
    id: int
    role: str
    content: Optional[str] = None
    agent_name: Optional[str] = None
