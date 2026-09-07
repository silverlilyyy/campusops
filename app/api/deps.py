"""公共依赖：DB Session / Redis / 当前用户（简化版鉴权）。

课程设计中默认使用单演示用户（demo）；如需多用户，可在此处扩展 token 解析。
"""
from __future__ import annotations

from typing import Iterator

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import repos
from db.engine import get_session as _engine_session

DEFAULT_USERNAME = "demo"


def get_db() -> Iterator[Session]:
    """FastAPI 依赖：提供事务性 DB Session。"""
    with _engine_session() as session:
        yield session


def get_default_user(session: Session = Depends(get_db)):
    """返回当前用户（演示环境固定为 demo，不存在则自动创建）。

    课程展示阶段便于直接联调；后续接入登录后替换为真实鉴权。
    """
    user = repos.user.get_user_by_username(session, DEFAULT_USERNAME)
    if user:
        return user
    from db.engine import get_engine
    return repos.user.create_user(
        session, username=DEFAULT_USERNAME, password_hash="demo", nickname="演示用户")


def user_id_dep(
    user_id: int = Query(default=0, description="演示用：指定用户ID(默认0表示使用demo用户)"),
) -> int:
    """占位依赖：预留真实鉴权位置。"""
    return user_id
