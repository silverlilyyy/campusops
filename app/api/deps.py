"""公共依赖：DB Session / Redis / 当前用户（简化版鉴权）。

鉴权方式：优先解析请求头 ``Authorization: Bearer <token>``，
解析到合法令牌则返回对应登录用户；否则回退到演示用户 demo（不存在则自动创建）。
这样既有"简单登录"，又保证未登录时课程演示仍可直接联调。
"""
from __future__ import annotations

from typing import Iterator

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from app.security import verify_token
from db import repos
from db.engine import get_session as _engine_session

DEFAULT_USERNAME = "demo"


def get_db() -> Iterator[Session]:
    """FastAPI 依赖：提供事务性 DB Session。"""
    with _engine_session() as session:
        yield session


def _ensure_demo(session: Session) -> dict:
    """确保 demo 用户存在并返回其记录（演示回退用户）。"""
    user = repos.user.get_user_by_username(session, DEFAULT_USERNAME)
    if user:
        return user
    return repos.user.create_user(
        session, username=DEFAULT_USERNAME, password_hash="demo", nickname="演示用户")


def get_current_user(request: Request, session: Session = Depends(get_db)) -> dict:
    """解析当前登录用户：Bearer token 优先，否则回退 demo。"""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        payload = verify_token(auth[7:].strip())
        if payload and payload.get("uid"):
            user = repos.user.get_user(session, int(payload["uid"]))
            if user:
                return user
    return _ensure_demo(session)


def get_default_user(user=Depends(get_current_user)) -> dict:
    """返回当前用户（兼容旧依赖名；已接入 token 鉴权）。"""
    return user


def user_id_dep(
    user_id: int = Query(default=0, description="演示用：指定用户ID(默认0表示使用demo用户)"),
) -> int:
    """占位依赖：预留真实鉴权位置。"""
    return user_id
