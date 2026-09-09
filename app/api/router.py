"""API 路由聚合：统一挂载到 /api/v1。"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, campus, chat, conversations, plans, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(campus.router)
api_router.include_router(conversations.router)
api_router.include_router(plans.router)
api_router.include_router(users.router)
