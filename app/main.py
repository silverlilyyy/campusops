"""FastAPI 入口：应用工厂 + 中间件 + 路由挂载。

启动方式（项目根目录）::

    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.registry import registry
from app.api.router import api_router
from app.api.routes.health import router as health_router
from db import repos
from db.engine import get_session

#: 允许跨域的来源（前端开发服务器地址，可按需扩展）
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:3000", "http://127.0.0.1:3000"]


def sync_agents_to_db() -> None:
    """把 Agent 注册表同步写入 agents 表（幂等；失败不影响启动）。"""
    try:
        with get_session() as session:
            for meta in registry.metadata():
                repos.agent_run.register_agent(
                    session, name=meta["name"],
                    display_name=meta["display_name"],
                    description=meta["description"])
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    sync_agents_to_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="CampusOps AI 校园生活规划系统",
        description="基于 Multi-Agent 协作的校园生活规划后端（FastAPI + MySQL + Redis）",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/")
    def root() -> dict:
        return {"service": "campusops", "docs": "/docs", "health": "/health"}

    return app


#: 模块级实例（供 uvicorn app.main:app 使用）
app = create_app()
