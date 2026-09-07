"""Chat 服务：串联 对话 -> Agent 编排 -> 持久化。

职责：
1. 确保会话存在（无 conversation_id 时新建并命名）；
2. 用户消息落库 + 写入 Redis 上下文；
3. 根据是否 replan 调用 run_planning / replan；
4. 汇总响应返回给 API 层。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from db import repos
from db.cache import ContextStore
from agents.orchestrator import run_planning
from agents.replanner import replan


def _load_context(session: Session, conversation_id: int) -> List[Dict[str, str]]:
    """从 DB 读历史消息，构造成 [{role, content}]（供 Agent/LLM 使用）。"""
    msgs = repos.conversation.list_messages(session, conversation_id, limit=20)
    return [{"role": m["role"], "content": m.get("content") or ""} for m in msgs]


def handle_chat(session: Session, *, user_id: int,
                message: str,
                conversation_id: Optional[int],
                replan: bool = False,
                previous_session_id: Optional[int] = None) -> Dict[str, Any]:
    """处理一次对话请求，返回给路由的 dict。"""
    # 1. 保证会话存在
    if conversation_id is None:
        conv = repos.conversation.create_conversation(
            session, user_id=user_id, title=message[:30])
        conversation_id = conv["id"]
    else:
        conv = repos.conversation.get_conversation(session, conversation_id)
        if not conv:
            raise ValueError("会话不存在")
        conversation_id = conv["id"]

    # 2. 用户消息落库 + Redis 上下文
    repos.conversation.add_message(session, conversation_id=conversation_id,
                                   role="user", content=message)
    ctx_store = ContextStore(conversation_id)
    ctx_store.push("user", message)
    # 提交本会话的变更，确保编排器(独立事务)能读到该会话与用户消息
    session.commit()

    # 3. 触发 Agent（replan 为反馈重规划，否则为新规划）
    history = _load_context(session, conversation_id)
    if replan:
        result = replan(user_id=user_id, feedback=message,
                        conversation_id=conversation_id,
                        previous_session_id=previous_session_id,
                        history=history)
    else:
        result = run_planning(user_id=user_id, input_text=message,
                              conversation_id=conversation_id,
                              history=history)

    return result
