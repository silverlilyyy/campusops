"""用户相关接口：当前用户信息、偏好。"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from db import repos
from app.api.deps import get_db, get_default_user
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ApiResponse)
def me(user=Depends(get_default_user), session=Depends(get_db)) -> ApiResponse:
    pref = repos.user.get_preference(session, user["id"])
    return ApiResponse.success({"user": user, "preference": pref})


@router.put("/me/preference", response_model=ApiResponse)
def update_preference(payload: dict, session=Depends(get_db),
                      user=Depends(get_default_user)) -> ApiResponse:
    repos.user.upsert_preference(session, user_id=user["id"], **payload)
    return ApiResponse.success(repos.user.get_preference(session, user["id"]),
                               message="偏好已更新")
