"""Agent 运行上下文：一次完整执行（需求->拆解->执行->汇总->落库）共享的状态。

包含：
- 身份信息：user_id / conversation_id / agent_session_id
- Redis 实时通道句柄（状态、对话上下文、任务队列）
- DB Session（在编排器外层开启，各 Agent 共享同一事务）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from db.cache import AgentStatusStore, ContextStore, TaskQueue


@dataclass
class AgentRunContext:
    """单轮 Agent 执行的上下文。"""

    user_id: int
    conversation_id: Optional[int]
    agent_session_id: int                      # agent_sessions.id
    session: Session                           # 共享事务
    input_text: str = ""                       # 原始用户需求
    history: list = field(default_factory=list)  # 对话上下文（可含过往消息）

    @property
    def run_key(self) -> str:
        return f"session:{self.agent_session_id}"

    @property
    def status_store(self) -> AgentStatusStore:
        return AgentStatusStore(self.run_key)

    @property
    def queue(self) -> TaskQueue:
        return TaskQueue(self.run_key)

    def ctx_store(self, conversation_id: Optional[int] = None) -> Optional[ContextStore]:
        cid = conversation_id or self.conversation_id
        return ContextStore(cid) if cid else None
