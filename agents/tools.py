"""Agent 可用工具：封装对 DB（repos）与 Redis（cache）的只读/轻量访问。

Agent 不直接 import repos 的细节，而是通过这些工具函数取数据，
工具内部捕获异常，保证无数据 / DB 不可用时也能返回可读结果。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from agents.context import AgentRunContext


# ---------------------------------------------------------------------------
# 学业域
# ---------------------------------------------------------------------------
def academic_context(ctx: AgentRunContext) -> Dict[str, Any]:
    """拉取学业相关数据摘要：课程、临考、待办作业。"""
    from db import repos
    uid = ctx.user_id
    out: Dict[str, Any] = {"has_data": False}
    try:
        courses = repos.academic.list_courses(ctx.session, uid)
        exams = repos.academic.upcoming_exams(ctx.session, uid, days=30)
        assigns = repos.academic.pending_assignments_sorted(ctx.session, uid, within_days=30)
        overdue = repos.academic.count_overdue_assignments(ctx.session, uid)
        out.update(courses=courses, exams=exams, assignments=assigns,
                   overdue_count=overdue, has_data=True)
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    return out


# ---------------------------------------------------------------------------
# 时间/日程域
# ---------------------------------------------------------------------------
def schedule_context(ctx: AgentRunContext, start: Optional[date] = None,
                     end: Optional[date] = None) -> Dict[str, Any]:
    """拉取某时间窗内的日程与待办任务。"""
    from db import repos
    uid = ctx.user_id
    start = start or date.today()
    end = end or (start + timedelta(days=7))
    out: Dict[str, Any] = {"has_data": False, "range": [start.isoformat(), end.isoformat()]}
    try:
        schedules = repos.task.list_schedules(ctx.session, uid, start, end)
        tasks = repos.task.list_tasks(ctx.session, uid, status="pending")
        conflicts = repos.task.detect_conflicts(ctx.session, uid, start)
        out.update(schedules=schedules, pending_tasks=tasks, conflicts=conflicts,
                   has_data=True)
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    return out


def find_free_slots(ctx: AgentRunContext, day: date) -> List[Dict[str, Any]]:
    """返回某一天的空闲时间段（默认 08:00-22:00 内的空隙）。"""
    from datetime import time as dtime

    from db import repos
    slots: List[Dict[str, Any]] = []
    try:
        blocks = repos.task.list_schedules(ctx.session, ctx.user_id, day, day)
        blocks = [b for b in blocks if b.get("day") == day]
        blocks.sort(key=lambda b: (b.get("start_time") or dtime(0, 0)))
        cursor = dtime(8, 0)
        for b in blocks:
            st = b.get("start_time") or cursor
            en = b.get("end_time") or cursor
            if st > cursor:
                slots.append({"start": cursor.isoformat(), "end": st.isoformat(),
                              "minutes": _mins(cursor, st)})
            cursor = max(cursor, en)
        if cursor < dtime(22, 0):
            slots.append({"start": cursor.isoformat(), "end": dtime(22, 0).isoformat(),
                          "minutes": _mins(cursor, dtime(22, 0))})
    except Exception as e:  # noqa: BLE001
        return [{"error": str(e)}]
    return slots


def _mins(a: Any, b: Any) -> int:
    from datetime import datetime as _dt
    x = _dt.combine(date.today(), a) if not isinstance(a, _dt) else a
    y = _dt.combine(date.today(), b) if not isinstance(b, _dt) else b
    return max(0, int((y - x).total_seconds() // 60))


# ---------------------------------------------------------------------------
# 消费/预算域
# ---------------------------------------------------------------------------
def finance_context(ctx: AgentRunContext) -> Dict[str, Any]:
    """拉取消费与预算数据摘要。"""
    from db import repos
    uid = ctx.user_id
    out: Dict[str, Any] = {"has_data": False}
    try:
        today = date.today()
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        expenses = repos.life.list_expenses(ctx.session, uid, limit=20)
        by_cat = repos.life.sum_by_category(
            ctx.session, uid,
            start=datetime.combine(month_start, datetime.min.time()),
            end=datetime.combine(month_end, datetime.min.time()))
        budget = repos.life.current_month_budget_with_spent(
            ctx.session, uid, month_start, month_end)
        out.update(expenses=expenses, by_category=by_cat, budget=budget,
                   has_data=True)
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    return out


def record_expense(ctx: AgentRunContext, *, amount: float, category: str,
                   note: Optional[str] = None) -> Dict[str, Any]:
    """录入一笔消费（写操作工具示例）。"""
    from datetime import datetime
    from db import repos
    try:
        row = repos.life.add_expense(ctx.session, user_id=ctx.user_id,
                                     amount=amount, category=category,
                                     paid_at=datetime.now(), note=note)
        return {"ok": True, "expense": row}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
