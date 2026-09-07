"""行动方案/执行记录查询：供前端回放 Multi-Agent 的规划结果与过程。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from db import repos
from app.api.deps import get_db, get_default_user
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/latest", response_model=ApiResponse)
def latest_plan(session=Depends(get_db),
                user=Depends(get_default_user)) -> ApiResponse:
    """最近一份行动方案（含明细）。"""
    plan = repos.task.get_latest_plan_with_items(session, user["id"])
    if not plan:
        return ApiResponse.success(None, message="暂无行动方案")
    return ApiResponse.success(plan)


@router.get("/sessions", response_model=ApiResponse)
def list_sessions(session=Depends(get_db),
                  user=Depends(get_default_user)) -> ApiResponse:
    """Agent 执行历史（用于过程回放入口）。"""
    return ApiResponse.success(repos.agent_run.list_sessions(session, user["id"]))


@router.get("/sessions/{session_id}/actions", response_model=ApiResponse)
def session_actions(session_id: int, session=Depends(get_db),
                    user=Depends(get_default_user)) -> ApiResponse:
    """某次执行的 Agent 动作轨迹。"""
    run = repos.agent_run.get_session(session, session_id)
    if not run:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    actions = repos.agent_run.list_actions(session, session_id)
    return ApiResponse.success({"session": run, "actions": actions})


@router.get("/{plan_id}", response_model=ApiResponse)
def get_plan(plan_id: int, session=Depends(get_db),
             user=Depends(get_default_user)) -> ApiResponse:
    plan = repos.task.get_plan_with_items(session, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="方案不存在")
    return ApiResponse.success(plan)


@router.post("/{plan_id}/complete", response_model=ApiResponse)
def complete_plan(plan_id: int, session=Depends(get_db),
                  user=Depends(get_default_user)) -> ApiResponse:
    plan = repos.task.get_plan_with_items(session, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="方案不存在")
    repos.task.mark_plan_status(session, plan_id, "completed")
    return ApiResponse.success(None, message="方案已标记完成")

