"""用户域数据访问：users / user_preferences。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.user import user_preferences, users
from db.repos.base import insert_and_fetch, row_to_dict, rows_to_dicts


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------
def create_user(session: Session, *, username: str, password_hash: str,
                nickname: str | None = None, email: str | None = None) -> Dict[str, Any]:
    """新增用户并返回其记录。"""
    return insert_and_fetch(session, users, {
        "username": username, "password_hash": password_hash,
        "nickname": nickname, "email": email,
    })


def get_user(session: Session, user_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(select(users).where(users.c.id == user_id)).first()
    return row_to_dict(row) if row else None


def get_user_by_username(session: Session, username: str) -> Optional[Dict[str, Any]]:
    row = session.execute(select(users).where(users.c.username == username)).first()
    return row_to_dict(row) if row else None


def list_users(session: Session, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    rows = session.execute(select(users).order_by(users.c.id).limit(limit).offset(offset)).all()
    return rows_to_dicts(rows)


def update_user(session: Session, user_id: int, **fields: Any) -> Optional[Dict[str, Any]]:
    """按白名单字段更新用户。"""
    allowed = {"nickname", "email", "avatar_url", "password_hash"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_user(session, user_id)
    stmt = users.update().where(users.c.id == user_id).values(**updates)
    session.execute(stmt)
    return get_user(session, user_id)


# ---------------------------------------------------------------------------
# user_preferences（一对一）
# ---------------------------------------------------------------------------
def upsert_preference(session: Session, user_id: int, **fields: Any) -> Dict[str, Any]:
    """新增/更新用户偏好（存在则更新，不存在则插入）。"""
    allowed = {"study_start", "study_end", "weekly_study_hours", "monthly_budget",
               "notification_enabled"}
    values = {k: v for k, v in fields.items() if k in allowed and v is not None}
    existing = get_preference(session, user_id)
    if existing:
        if values:
            session.execute(
                user_preferences.update()
                .where(user_preferences.c.user_id == user_id)
                .values(**values)
            )
    else:
        session.execute(user_preferences.insert().values(user_id=user_id, **values))
    return get_preference(session, user_id)  # type: ignore[return-value]


def get_preference(session: Session, user_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(
        select(user_preferences).where(user_preferences.c.user_id == user_id)
    ).first()
    return row_to_dict(row) if row else None
