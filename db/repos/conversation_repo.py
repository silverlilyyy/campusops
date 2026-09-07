"""对话域数据访问：conversations / messages。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.conversation import conversations, messages
from db.repos.base import insert_and_fetch, row_to_dict, rows_to_dicts


# ---------------------------------------------------------------------------
# conversations
# ---------------------------------------------------------------------------
def create_conversation(session: Session, *, user_id: int, title: str | None = None) -> Dict[str, Any]:
    return insert_and_fetch(session, conversations,
                            {"user_id": user_id, "title": title or "新对话"})


def get_conversation(session: Session, conversation_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(
        select(conversations).where(conversations.c.id == conversation_id)
    ).first()
    return row_to_dict(row) if row else None


def list_conversations(session: Session, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    return rows_to_dicts(session.execute(
        select(conversations)
        .where(conversations.c.user_id == user_id)
        .order_by(conversations.c.id.desc()).limit(limit)
    ).all())


def close_conversation(session: Session, conversation_id: int) -> None:
    session.execute(
        conversations.update().where(conversations.c.id == conversation_id)
        .values(status="closed")
    )


def add_message(session: Session, *, conversation_id: int, role: str, content: str,
                agent_name: str | None = None, session_id: int | None = None) -> Dict[str, Any]:
    return insert_and_fetch(session, messages, {
        "conversation_id": conversation_id, "role": role, "content": content,
        "agent_name": agent_name, "session_id": session_id,
        "created_at": datetime.now(),
    })


def list_messages(session: Session, conversation_id: int,
                  limit: int = 200) -> List[Dict[str, Any]]:
    return rows_to_dicts(session.execute(
        select(messages)
        .where(messages.c.conversation_id == conversation_id)
        .order_by(messages.c.id).limit(limit)
    ).all())
