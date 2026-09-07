"""校园数据查询接口：课程/考试/作业/活动/消费/预算/日程。

面向前端展示与"用户手动录入数据"场景，直接走 repos 层。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from db import repos
from app.api.deps import get_db, get_default_user
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/campus", tags=["campus"])


def _current_uid(session, user) -> int:
    return user["id"]


# -- 课程 -------------------------------------------------------------
@router.get("/courses", response_model=ApiResponse)
def list_courses(session=Depends(get_db), user=Depends(get_default_user)) -> ApiResponse:
    data = repos.academic.list_courses(session, _current_uid(session, user))
    return ApiResponse.success(data)


@router.post("/courses", response_model=ApiResponse)
def add_course(payload: dict, session=Depends(get_db),
               user=Depends(get_default_user)) -> ApiResponse:
    row = repos.academic.create_course(session, user_id=user["id"], **payload)
    return ApiResponse.success(row, message="课程已添加")


# -- 考试 -------------------------------------------------------------
@router.get("/exams", response_model=ApiResponse)
def list_exams(session=Depends(get_db), user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(repos.academic.list_exams(session, user["id"]))


@router.get("/exams/upcoming", response_model=ApiResponse)
def upcoming_exams(days: int = Query(30), session=Depends(get_db),
                   user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(repos.academic.upcoming_exams(session, user["id"], days))


# -- 作业 -------------------------------------------------------------
@router.get("/assignments", response_model=ApiResponse)
def list_assignments(status: str | None = None, session=Depends(get_db),
                     user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(
        repos.academic.list_assignments(session, user["id"], status))


# -- 活动 -------------------------------------------------------------
@router.get("/activities", response_model=ApiResponse)
def list_activities(session=Depends(get_db),
                    user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(repos.life.list_activities(session, user["id"]))


# -- 消费/预算 ---------------------------------------------------------
@router.get("/expenses", response_model=ApiResponse)
def list_expenses(session=Depends(get_db),
                  user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(repos.life.list_expenses(session, user["id"]))


@router.post("/expenses", response_model=ApiResponse)
def add_expense(payload: dict, session=Depends(get_db),
                user=Depends(get_default_user)) -> ApiResponse:
    row = repos.life.add_expense(session, user_id=user["id"], **payload)
    return ApiResponse.success(row, message="已记账")


@router.get("/finance/summary", response_model=ApiResponse)
def finance_summary(session=Depends(get_db),
                    user=Depends(get_default_user)) -> ApiResponse:
    from agents import tools
    from agents.context import AgentRunContext
    # 复用 Agent 工具：以最小上下文聚合财务摘要（只读，不落 agent_session）
    fake = AgentRunContext(user_id=user["id"], conversation_id=None,
                           agent_session_id=0, session=session)
    return ApiResponse.success(tools.finance_context(fake))


# -- 日程/任务 ----------------------------------------------------------
@router.get("/schedules", response_model=ApiResponse)
def list_schedules(session=Depends(get_db),
                   user=Depends(get_default_user)) -> ApiResponse:
    from datetime import date, timedelta
    start = date.today()
    end = start + timedelta(days=7)
    return ApiResponse.success(repos.task.list_schedules(session, user["id"], start, end))


@router.get("/tasks", response_model=ApiResponse)
def list_tasks(status: str | None = None, session=Depends(get_db),
               user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(repos.task.list_tasks(session, user["id"], status=status))
