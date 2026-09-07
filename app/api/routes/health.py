"""健康检查：MySQL/Redis 连通性与 Agent 注册信息。"""
from __future__ import annotations

from fastapi import APIRouter

from db import cache
from db.engine import ping as mysql_ping
from app.schemas.common import HealthInfo

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthInfo)
def health() -> HealthInfo:
    """返回各依赖组件的健康状态。"""
    agents = []
    try:
        from agents.registry import registry
        agents = registry.metadata()
    except Exception:  # noqa: BLE001
        agents = []
    return HealthInfo(mysql=mysql_ping(), redis=cache.ping(), agents=agents)
