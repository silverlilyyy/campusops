"""Agent 运行域数据访问：agents / agent_sessions / agent_actions。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.agent_run import agent_actions, agent_sessions, agents
from db.repos.base import insert_and_fetch, row_to_dict, rows_to_dicts


# ---------------------------------------------------------------------------
# agents（注册表）
# ---------------------------------------------------------------------------
def register_agent(session: Session, *, name: str, display_name: str,
                   description: str) -> Dict[str, Any]:
    """登记 Agent（存在则跳过，返回已有记录）。"""
    existing = session.execute(select(agents).where(agents.c.name == name)).first()
    if existing:
        return row_to_dict(existing)
    return insert_and_fetch(session, agents, {
        "name": name, "display_name": display_name, "description": description,
    })


def list_agents(session: Session) -> List[Dict[str, Any]]:
    return rows_to_dicts(session.execute(
        select(agents).where(agents.c.enabled == True).order_by(agents.c.id)  # noqa: E712
    ).all())


# ---------------------------------------------------------------------------
# agent_sessions
# ---------------------------------------------------------------------------
def create_session(session: Session, *, user_id: int, conversation_id: int | None,
                   input_text: str, replan_of_id: int | None = None) -> Dict[str, Any]:
    return insert_and_fetch(session, agent_sessions, {
        "user_id": user_id, "conversation_id": conversation_id, "input_text": input_text,
        "status": "running", "replan_of_id": replan_of_id,
        "started_at": datetime.now(), "created_at": datetime.now(),
    })


def update_session(session: Session, session_id: int, **fields: Any) -> None:
    allowed = {"status", "error", "plan_id", "ended_at", "replan_of_id"}
    vals = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if vals:
        session.execute(agent_sessions.update().where(agent_sessions.c.id == session_id).values(**vals))


def complete_session(session: Session, session_id: int, *,
                     plan_id: int | None = None) -> None:
    update_session(session, session_id, status="completed",
                   plan_id=plan_id, ended_at=datetime.now())


def fail_session(session: Session, session_id: int, *, error: str) -> None:
    update_session(session, session_id, status="failed", error=error, ended_at=datetime.now())


def get_session(session: Session, session_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(select(agent_sessions).where(agent_sessions.c.id == session_id)).first()
    return row_to_dict(row) if row else None


def list_sessions(session: Session, user_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    return rows_to_dicts(session.execute(
        select(agent_sessions).where(agent_sessions.c.user_id == user_id)
        .order_by(agent_sessions.c.id.desc()).limit(limit)
    ).all())


# ---------------------------------------------------------------------------
# agent_actions（过程记录）
# ---------------------------------------------------------------------------
def start_action(session: Session, *, session_id: int, agent_name: str, action: str,
                 request: str | None = None) -> int:
    return insert_and_fetch(session, agent_actions, {
        "session_id": session_id, "agent_name": agent_name, "action": action,
        "status": "running", "request": request, "started_at": datetime.now(),
    })["id"]


def finish_action(session: Session, action_id: int, *, response: str,
                  status: str = "completed") -> None:
    session.execute(
        agent_actions.update().where(agent_actions.c.id == action_id)
        .values(status=status, response=response, ended_at=datetime.now())
    )


def list_actions(session: Session, session_id: int) -> List[Dict[str, Any]]:
    return rows_to_dicts(session.execute(
        select(agent_actions).where(agent_actions.c.session_id == session_id)
        .order_by(agent_actions.c.id)
    ).all())
