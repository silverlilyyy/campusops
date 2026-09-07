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
    repos.task.sync_academic_schedules(session, user["id"])
    session.commit()
    return ApiResponse.success(row, message="课程已添加")


@router.put("/courses/{course_id}", response_model=ApiResponse)
def update_course(course_id: int, payload: dict, session=Depends(get_db),
                  user=Depends(get_default_user)) -> ApiResponse:
    existing = repos.academic.get_course(session, course_id)
    if not existing or existing["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="课程不存在")
    if not payload.get("name"):
        raise HTTPException(status_code=422, detail="课程名为必填项")
    repos.academic.update_course(session, course_id, **payload)
    repos.task.sync_academic_schedules(session, user["id"])
    session.commit()
    return ApiResponse.success(repos.academic.get_course(session, course_id), message="课程已更新")


@router.delete("/courses/{course_id}", response_model=ApiResponse)
def delete_course(course_id: int, session=Depends(get_db),
                  user=Depends(get_default_user)) -> ApiResponse:
    existing = repos.academic.get_course(session, course_id)
    if not existing or existing["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="课程不存在")
    repos.academic.delete_course(session, course_id)
    repos.task.sync_academic_schedules(session, user["id"])
    session.commit()
    return ApiResponse.success(None, message="课程已删除")


# -- 考试 -------------------------------------------------------------
@router.get("/exams", response_model=ApiResponse)
def list_exams(session=Depends(get_db), user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(repos.academic.list_exams(session, user["id"]))


@router.get("/exams/upcoming", response_model=ApiResponse)
def upcoming_exams(days: int = Query(30), session=Depends(get_db),
                   user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(repos.academic.upcoming_exams(session, user["id"], days))


@router.post("/exams", response_model=ApiResponse)
def add_exam(payload: dict, session=Depends(get_db),
             user=Depends(get_default_user)) -> ApiResponse:
    if not payload.get("name") or not payload.get("exam_date"):
        raise HTTPException(status_code=422, detail="考试名称和考试日期为必填项")
    row = repos.academic.create_exam(session, user_id=user["id"], **payload)
    repos.task.sync_academic_schedules(session, user["id"])
    session.commit()
    return ApiResponse.success(row, message="考试已添加")


@router.put("/exams/{exam_id}", response_model=ApiResponse)
def update_exam(exam_id: int, payload: dict, session=Depends(get_db),
                user=Depends(get_default_user)) -> ApiResponse:
    existing = repos.academic.get_exam(session, exam_id)
    if not existing or existing["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not payload.get("name") or not payload.get("exam_date"):
        raise HTTPException(status_code=422, detail="考试名称和考试日期为必填项")
    repos.academic.update_exam(session, exam_id, **payload)
    repos.task.sync_academic_schedules(session, user["id"])
    session.commit()
    return ApiResponse.success(repos.academic.get_exam(session, exam_id), message="考试已更新")


@router.delete("/exams/{exam_id}", response_model=ApiResponse)
def delete_exam(exam_id: int, session=Depends(get_db),
                user=Depends(get_default_user)) -> ApiResponse:
    existing = repos.academic.get_exam(session, exam_id)
    if not existing or existing["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="考试不存在")
    repos.academic.delete_exam(session, exam_id)
    repos.task.sync_academic_schedules(session, user["id"])
    session.commit()
    return ApiResponse.success(None, message="考试已删除")


# -- 作业 -------------------------------------------------------------
@router.get("/assignments", response_model=ApiResponse)
def list_assignments(status: str | None = None, session=Depends(get_db),
                     user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(
        repos.academic.list_assignments(session, user["id"], status))


@router.post("/assignments", response_model=ApiResponse)
def add_assignment(payload: dict, session=Depends(get_db),
                   user=Depends(get_default_user)) -> ApiResponse:
    if not payload.get("title") or not payload.get("deadline"):
        raise HTTPException(status_code=422, detail="作业标题和截止时间为必填项")
    row = repos.academic.create_assignment(session, user_id=user["id"], **payload)
    repos.task.sync_academic_schedules(session, user["id"])
    session.commit()
    return ApiResponse.success(row, message="作业已添加")


@router.put("/assignments/{assignment_id}", response_model=ApiResponse)
def update_assignment(assignment_id: int, payload: dict, session=Depends(get_db),
                      user=Depends(get_default_user)) -> ApiResponse:
    existing = repos.academic.get_assignment(session, assignment_id)
    if not existing or existing["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="作业不存在")
    if not payload.get("title") or not payload.get("deadline"):
        raise HTTPException(status_code=422, detail="作业标题和截止时间为必填项")
    repos.academic.update_assignment(session, assignment_id, **payload)
    repos.task.sync_academic_schedules(session, user["id"])
    session.commit()
    return ApiResponse.success(repos.academic.get_assignment(session, assignment_id),
                               message="作业已更新")


@router.delete("/assignments/{assignment_id}", response_model=ApiResponse)
def delete_assignment(assignment_id: int, session=Depends(get_db),
                      user=Depends(get_default_user)) -> ApiResponse:
    existing = repos.academic.get_assignment(session, assignment_id)
    if not existing or existing["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="作业不存在")
    repos.academic.delete_assignment(session, assignment_id)
    repos.task.sync_academic_schedules(session, user["id"])
    session.commit()
    return ApiResponse.success(None, message="作业已删除")


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


@router.get("/budgets", response_model=ApiResponse)
def list_budgets(session=Depends(get_db),
                 user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(repos.life.list_budgets(session, user["id"]))


@router.post("/budgets", response_model=ApiResponse)
def add_budget(payload: dict, session=Depends(get_db),
               user=Depends(get_default_user)) -> ApiResponse:
    from calendar import monthrange
    from datetime import date, timedelta

    amount = payload.get("amount")
    if amount is None or float(amount) <= 0:
        raise HTTPException(status_code=422, detail="预算金额必须大于 0")

    period_type = payload.get("period_type") or "monthly"
    category = payload.get("category")  # 空 = 总预算

    period_start = payload.get("period_start")
    period_end = payload.get("period_end")
    today = date.today()
    if not period_start:
        if period_type == "weekly":
            period_start = today - timedelta(days=today.weekday())
        elif period_type == "daily":
            period_start = today
        else:
            period_start = today.replace(day=1)
    if not period_end:
        if period_type == "weekly":
            period_end = period_start + timedelta(days=6)
        elif period_type == "daily":
            period_end = period_start
        else:
            period_end = period_start.replace(day=monthrange(period_start.year, period_start.month)[1])

    row = repos.life.upsert_budget(
        session, user_id=user["id"], period_type=period_type, amount=amount,
        period_start=period_start, period_end=period_end, category=category,
    )
    return ApiResponse.success(row, message="预算已保存")


# -- 日程/任务 ----------------------------------------------------------
@router.get("/schedules", response_model=ApiResponse)
def list_schedules(session=Depends(get_db),
                   user=Depends(get_default_user)) -> ApiResponse:
    from datetime import date, timedelta
    # 读取前先做一次同步，确保手动录入的课程/考试/作业能出现在日程里
    repos.task.sync_academic_schedules(session, user["id"])
    start = date.today()
    end = start + timedelta(days=7)
    return ApiResponse.success(repos.task.list_schedules(session, user["id"], start, end))


@router.get("/tasks", response_model=ApiResponse)
def list_tasks(status: str | None = None, session=Depends(get_db),
               user=Depends(get_default_user)) -> ApiResponse:
    return ApiResponse.success(repos.task.list_tasks(session, user["id"], status=status))
