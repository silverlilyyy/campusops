"""认证接口：注册 / 登录 / 当前用户（简单用户名密码，无外部 OAuth）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.common import ApiResponse
from app.security import create_token, hash_password, verify_password
from db import repos

router = APIRouter(prefix="/auth", tags=["auth"])


def _safe_user(user: dict) -> dict:
    """剔除敏感字段（password_hash）后的用户信息。"""
    return {k: v for k, v in user.items() if k != "password_hash"}


def _auth_payload(user: dict, session: Session) -> dict:
    """登录/注册成功后返回的统一载荷。"""
    pref = repos.user.get_preference(session, user["id"])
    return {"token": create_token(user), "user": _safe_user(user), "preference": pref}


@router.post("/register", response_model=ApiResponse)
def register(payload: dict, session=Depends(get_db)) -> ApiResponse:
    """注册新用户（用户名唯一）。"""
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        raise HTTPException(status_code=422, detail="用户名和密码不能为空")
    if len(password) < 4:
        raise HTTPException(status_code=422, detail="密码至少 4 位")
    if repos.user.get_user_by_username(session, username):
        raise HTTPException(status_code=409, detail="用户名已存在")
    user = repos.user.create_user(
        session, username=username, password_hash=hash_password(password),
        nickname=(payload.get("nickname") or "").strip() or username,
        email=(payload.get("email") or "").strip() or None)
    session.commit()
    return ApiResponse.success(_auth_payload(user, session), message="注册成功")


@router.post("/login", response_model=ApiResponse)
def login(payload: dict, session=Depends(get_db)) -> ApiResponse:
    """用户名 + 密码登录，返回令牌。"""
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    user = repos.user.get_user_by_username(session, username)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return ApiResponse.success(_auth_payload(user, session), message="登录成功")


@router.get("/me", response_model=ApiResponse)
def me(user=Depends(get_current_user), session=Depends(get_db)) -> ApiResponse:
    """返回当前登录用户信息与偏好。"""
    pref = repos.user.get_preference(session, user["id"])
    return ApiResponse.success({"user": _safe_user(user), "preference": pref})
