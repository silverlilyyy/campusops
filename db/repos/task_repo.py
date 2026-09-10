"""任务与计划域数据访问：tasks / task_dependencies / schedules / action_plans / action_plan_items。

包含 Agent 规划写入的**核心事务**（创建一份完整行动方案 = 方案+明细，且覆盖旧方案），
以及"时间冲突检测"等原生 SQL 示例。
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, insert, select
from sqlalchemy.orm import Session

from db.models.task_plan import (
    action_plan_items,
    action_plans,
    schedules,
    task_dependencies,
    tasks,
)
from db.repos.base import fetch_all, insert_and_fetch, row_to_dict, rows_to_dicts, scalar

_TASK_FIELDS = ("title", "description", "task_type", "source_type", "source_id",
                "priority", "status", "deadline", "estimated_hours", "plan_date",
                "actual_hours", "conversation_id")


# ---------------------------------------------------------------------------
# tasks
# ---------------------------------------------------------------------------
def create_task(session: Session, *, user_id: int, **data: Any) -> Dict[str, Any]:
    vals = {k: v for k, v in data.items() if k in _TASK_FIELDS and v is not None}
    return insert_and_fetch(session, tasks, {"user_id": user_id, **vals})


def get_task(session: Session, task_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(select(tasks).where(tasks.c.id == task_id)).first()
    return row_to_dict(row) if row else None


def list_tasks(session: Session, user_id: int, status: str | None = None,
               task_type: str | None = None, from_day: date | None = None) -> List[Dict[str, Any]]:
    stmt = select(tasks).where(tasks.c.user_id == user_id)
    if status:
        stmt = stmt.where(tasks.c.status == status)
    if task_type:
        stmt = stmt.where(tasks.c.task_type == task_type)
    if from_day:
        stmt = stmt.where(tasks.c.plan_date >= from_day)
    return rows_to_dicts(session.execute(stmt.order_by(tasks.c.deadline, tasks.c.priority)).all())


def update_task(session: Session, task_id: int, **data: Any) -> Optional[Dict[str, Any]]:
    vals = {k: v for k, v in data.items() if k in _TASK_FIELDS and v is not None}
    if vals:
        session.execute(tasks.update().where(tasks.c.id == task_id).values(**vals))
    return get_task(session, task_id)


def update_task_status(session: Session, task_id: int, status: str,
                       actual_hours: float | None = None) -> Optional[Dict[str, Any]]:
    fields: Dict[str, Any] = {"status": status}
    if actual_hours is not None:
        fields["actual_hours"] = actual_hours
    session.execute(tasks.update().where(tasks.c.id == task_id).values(**fields))
    return get_task(session, task_id)


def add_task_dependency(session: Session, task_id: int, depends_on_task_id: int) -> None:
    session.execute(
        task_dependencies.insert()
        .values(task_id=task_id, depends_on_task_id=depends_on_task_id)
    )


def pending_task_count(session: Session, user_id: int) -> int:
    """【原生 SQL 示例】进行中/待办任务数。"""
    return scalar(
        session,
        "SELECT COUNT(*) FROM tasks WHERE user_id=:uid AND status NOT IN ('done','cancelled')",
        uid=user_id,
    )


# ---------------------------------------------------------------------------
# schedules
# ---------------------------------------------------------------------------
def list_schedules(session: Session, user_id: int, start: date, end: date) -> List[Dict[str, Any]]:
    return rows_to_dicts(session.execute(
        select(schedules)
        .where(and_(schedules.c.user_id == user_id,
                    schedules.c.day >= start, schedules.c.day <= end))
        .order_by(schedules.c.day, schedules.c.start_time)
    ).all())


def create_schedule(session: Session, *, user_id: int, **data: Any) -> Dict[str, Any]:
    allowed = ("day", "start_time", "end_time", "schedule_type", "ref_type", "ref_id",
               "title", "location", "status", "conversation_id")
    vals = {k: v for k, v in data.items() if k in allowed and v is not None}
    return insert_and_fetch(session, schedules, {"user_id": user_id, **vals})


def replace_day_schedules(session: Session, user_id: int, day: date,
                          items: List[Dict[str, Any]]) -> None:
    """先删后插：清空某一天的计划日程后，写入新的排程（重规划时使用）。"""
    session.execute(
        delete(schedules)
        .where(and_(schedules.c.user_id == user_id, schedules.c.day == day,
                    schedules.c.schedule_type.in_(["task", "free"])))
    )
    for item in items:
        create_schedule(session, user_id=user_id, **item)


def sync_academic_schedules(session: Session, user_id: int,
                            days: int = 28) -> Dict[str, int]:
    """把课程/考试/作业同步为日程块（覆盖式：先删该来源的旧日程再重建）。

    课程按 ``weekday`` 在时间窗内逐周展开；考试落在 ``exam_date`` 当天；
    未完成作业落在 ``deadline`` 当天。返回各来源生成的块数。
    """
    from db.repos import academic as academic_repo

    today = date.today()
    end = today + timedelta(days=days)
    counts: Dict[str, int] = {"course": 0, "exam": 0, "assignment": 0}

    # 1) 清空旧的学术来源日程，保证幂等、无重复/残留
    session.execute(
        delete(schedules).where(
            and_(schedules.c.user_id == user_id,
                 schedules.c.ref_type.in_(["course", "exam", "assignment"]))
        )
    )

    # 2) 课程：按 weekday 展开为每周的时间块
    for c in academic_repo.list_courses(session, user_id):
        weekday = c.get("weekday")
        start_time = c.get("start_time")
        end_time = c.get("end_time")
        if not weekday or not start_time or not end_time:
            continue
        d = today
        while d <= end:
            if d.isoweekday() == int(weekday):
                create_schedule(
                    session, user_id=user_id, day=d,
                    start_time=start_time, end_time=end_time,
                    schedule_type="course", ref_type="course", ref_id=c["id"],
                    title=c.get("name"), location=c.get("location"),
                )
                counts["course"] += 1
            d += timedelta(days=1)

    # 3) 考试：exam_date 当天一个时间块
    for e in academic_repo.list_exams(session, user_id):
        exam_date = e.get("exam_date")
        if not exam_date or exam_date < today or exam_date > end:
            continue
        create_schedule(
            session, user_id=user_id, day=exam_date,
            start_time=e.get("start_time") or time(9, 0),
            end_time=e.get("end_time") or time(11, 0),
            schedule_type="exam", ref_type="exam", ref_id=e["id"],
            title=e.get("name"), location=e.get("location"),
        )
        counts["exam"] += 1

    # 4) 作业：deadline 当天一个时间块（已完成的不再排）
    for a in academic_repo.list_assignments(session, user_id):
        if a.get("status") in ("completed",):
            continue
        deadline = a.get("deadline")
        if not deadline:
            continue
        d = deadline.date() if isinstance(deadline, datetime) else deadline
        if d < today or d > end:
            continue
        create_schedule(
            session, user_id=user_id, day=d,
            start_time=time(20, 0), end_time=time(21, 0),
            schedule_type="task", ref_type="assignment", ref_id=a["id"],
            title=a.get("title"),
        )
        counts["assignment"] += 1

    return counts


def detect_conflicts(session: Session, user_id: int, day: date) -> List[Dict[str, Any]]:
    """【原生 SQL 示例】检测同一天时间重叠的日程块（自连接）。"""
    return fetch_all(
        session,
        """
        SELECT a.id AS a_id, a.title AS a_title, a.start_time AS a_start, a.end_time AS a_end,
               b.id AS b_id, b.title AS b_title, b.start_time AS b_start, b.end_time AS b_end
        FROM schedules a
        JOIN schedules b ON a.user_id = b.user_id AND a.day = b.day AND a.id < b.id
        WHERE a.user_id = :uid AND a.day = :day
          AND a.start_time < b.end_time AND b.start_time < a.end_time
        """,
        uid=user_id, day=day,
    )


# ---------------------------------------------------------------------------
# action_plans + action_plan_items（核心事务：创建一份完整行动方案）
# ---------------------------------------------------------------------------
def get_active_plan(session: Session, user_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(
        select(action_plans)
        .where(and_(action_plans.c.user_id == user_id,
                    action_plans.c.status == "active"))
        .order_by(action_plans.c.id.desc())
    ).first()
    return row_to_dict(row) if row else None


def create_plan(session: Session, *, user_id: int, items: List[Dict[str, Any]],
                goal: str | None = None, summary: str | None = None,
                title: str | None = None, conversation_id: int | None = None,
                supersede_old: bool = True) -> Dict[str, Any]:
    """创建行动方案及明细。

    这是一个**事务性**操作：旧方案标记 superseded -> 新方案落库 -> 逐条写入明细。
    （调用方保证在整个 db.engine.get_session() 事务内执行）
    """
    if supersede_old:
        old = get_active_plan(session, user_id)
        if old:
            session.execute(
                action_plans.update()
                .where(action_plans.c.id == old["id"])
                .values(status="superseded")
            )

    plan = insert_and_fetch(session, action_plans, {
        "user_id": user_id, "conversation_id": conversation_id, "title": title,
        "goal": goal, "summary": summary,
        "status": "active",
    })

    for i, item in enumerate(items):
        session.execute(
            action_plan_items.insert().values(
                plan_id=plan["id"],
                task_id=item.get("task_id"),
                content=item.get("content") or "",
                reason=item.get("reason"),
                day=item.get("day"),
                start_time=item.get("start_time"),
                end_time=item.get("end_time"),
                status="pending",
                sort_order=i,
                created_at=datetime.now(),
            )
        )
    return plan


def get_plan_with_items(session: Session, plan_id: int) -> Dict[str, Any]:
    plan = row_to_dict(session.execute(
        select(action_plans).where(action_plans.c.id == plan_id)).first())
    items = rows_to_dicts(session.execute(
        select(action_plan_items)
        .where(action_plan_items.c.plan_id == plan_id)
        .order_by(action_plan_items.c.sort_order)
    ).all())
    plan["items"] = items
    return plan


def get_latest_plan_with_items(session: Session, user_id: int) -> Optional[Dict[str, Any]]:
    """获取最近一份（active 优先）行动方案及其明细。"""
    row = session.execute(
        select(action_plans)
        .where(action_plans.c.user_id == user_id)
        .order_by(action_plans.c.id.desc())
    ).first()
    if not row:
        return None
    plan = row_to_dict(row)
    plan["items"] = rows_to_dicts(session.execute(
        select(action_plan_items)
        .where(action_plan_items.c.plan_id == plan["id"])
        .order_by(action_plan_items.c.sort_order)
    ).all())
    return plan


def mark_plan_status(session: Session, plan_id: int, status: str) -> None:
    session.execute(
        action_plans.update().where(action_plans.c.id == plan_id).values(status=status)
    )


def update_plan_item_status(session: Session, item_id: int, status: str) -> None:
    session.execute(
        action_plan_items.update()
        .where(action_plan_items.c.id == item_id).values(status=status)
    )
