"""生活域数据访问：activities / expenses / budgets。

消费汇总类查询（按类别、按周期、预算对比）以原生 SQL 聚合示例给出，
作为数据库课程设计中的报表查询展示点。
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models.life import activities, budgets, expenses
from db.repos.base import fetch_all, insert_and_fetch, row_to_dict, rows_to_dicts, scalar


# ---------------------------------------------------------------------------
# activities
# ---------------------------------------------------------------------------
def create_activity(session: Session, **data: Any) -> Dict[str, Any]:
    allowed = ("user_id", "name", "category", "start_time", "end_time", "location",
               "importance", "note")
    vals = {k: v for k, v in data.items() if k in allowed and v is not None}
    return insert_and_fetch(session, activities, vals)


def list_activities(session: Session, user_id: int, start: date | None = None,
                    end: date | None = None) -> List[Dict[str, Any]]:
    stmt = select(activities).where(activities.c.user_id == user_id)
    if start:
        stmt = stmt.where(activities.c.start_time >= datetime.combine(start, datetime.min.time()))
    if end:
        stmt = stmt.where(activities.c.start_time < datetime.combine(end, datetime.min.time()))
    return rows_to_dicts(session.execute(stmt.order_by(activities.c.start_time)).all())


def get_activity(session: Session, activity_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(select(activities).where(activities.c.id == activity_id)).first()
    return row_to_dict(row) if row else None


def update_activity(session: Session, activity_id: int, **data: Any) -> None:
    allowed = ("name", "category", "start_time", "end_time", "location", "importance", "note")
    vals = {k: v for k, v in data.items() if k in allowed and v is not None}
    if vals:
        session.execute(activities.update().where(activities.c.id == activity_id).values(**vals))


def delete_activity(session: Session, activity_id: int) -> None:
    session.execute(activities.delete().where(activities.c.id == activity_id))


# ---------------------------------------------------------------------------
# expenses
# ---------------------------------------------------------------------------
def add_expense(session: Session, *, user_id: int, amount, category: str = "other",
                paid_at: datetime | None = None, note: str | None = None) -> Dict[str, Any]:
    return insert_and_fetch(session, expenses, {
        "user_id": user_id, "amount": amount, "category": category,
        "paid_at": paid_at or datetime.now(), "note": note,
        "created_at": datetime.now(),
    })


def list_expenses(session: Session, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    return rows_to_dicts(session.execute(
        select(expenses).where(expenses.c.user_id == user_id)
        .order_by(expenses.c.paid_at.desc()).limit(limit)).all())


def sum_by_category(session: Session, user_id: int, start: datetime | None = None,
                    end: datetime | None = None) -> List[Dict[str, Any]]:
    """【原生 SQL 示例】按消费类别汇总金额（可用于柱状/饼图）。"""
    where = "WHERE user_id=:uid"
    params: Dict[str, Any] = {"uid": user_id}
    if start:
        where += " AND paid_at >= :start"
        params["start"] = start
    if end:
        where += " AND paid_at < :end"
        params["end"] = end
    return fetch_all(
        session,
        f"""
        SELECT category,
               COUNT(*)            AS cnt,
               SUM(amount)         AS total,
               ROUND(AVG(amount),2) AS avg_amount
        FROM expenses
        {where}
        GROUP BY category
        ORDER BY total DESC
        """,
        **params,
    )


def trend_by_day(session: Session, user_id: int, start: date, end: date) -> List[Dict[str, Any]]:
    """【原生 SQL 示例】按天统计消费趋势。"""
    return fetch_all(
        session,
        """
        SELECT DATE(paid_at) AS day, SUM(amount) AS total, COUNT(*) AS cnt
        FROM expenses
        WHERE user_id = :uid AND DATE(paid_at) BETWEEN :start AND :end
        GROUP BY DATE(paid_at)
        ORDER BY day
        """,
        uid=user_id, start=start, end=end,
    )


# ---------------------------------------------------------------------------
# budgets
# ---------------------------------------------------------------------------
def upsert_budget(session: Session, *, user_id: int, period_type: str, amount,
                  period_start: date, period_end: date,
                  category: str | None = None) -> Dict[str, Any]:
    """预算按 (user, period_type, period_start, category) 唯一，存在则覆盖。"""
    category = category or ""  # 总预算用空串表示，保证唯一约束生效
    existing = scalar(
        session,
        "SELECT id FROM budgets WHERE user_id=:uid AND period_type=:pt "
        "AND period_start=:ps AND category=:cat",
        uid=user_id, pt=period_type, ps=period_start, cat=category,
    )
    if existing:
        session.execute(
            budgets.update().where(budgets.c.id == existing)
            .values(amount=amount, period_end=period_end)
        )
        budget_id = existing
    else:
        budget_id = insert_and_fetch(session, budgets, {
            "user_id": user_id, "period_type": period_type, "period_start": period_start,
            "period_end": period_end, "category": category, "amount": amount,
        })["id"]
    return get_budget(session, budget_id)


def get_budget(session: Session, budget_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(select(budgets).where(budgets.c.id == budget_id)).first()
    return row_to_dict(row) if row else None


def list_budgets(session: Session, user_id: int) -> List[Dict[str, Any]]:
    """返回该用户全部预算（按周期开始时间倒序）。"""
    return rows_to_dicts(session.execute(
        select(budgets).where(budgets.c.user_id == user_id)
        .order_by(budgets.c.period_start.desc())
    ).all())


def current_month_budget_with_spent(session: Session, user_id: int,
                                    month_start: date, month_end: date) -> List[Dict[str, Any]]:
    """【原生 SQL 示例】月度预算 vs 实际消费（LEFT JOIN 聚合）。"""
    return fetch_all(
        session,
        """
        SELECT b.id, b.category, b.amount AS budget_amount,
               COALESCE(s.spent, 0) AS spent,
               b.amount - COALESCE(s.spent, 0) AS remaining,
               CASE WHEN b.amount > 0
                    THEN ROUND(COALESCE(s.spent,0)/b.amount*100,1) ELSE 0 END AS used_percent
        FROM budgets b
        LEFT JOIN (
            SELECT COALESCE(category, 'other') AS category, SUM(amount) AS spent
            FROM expenses
            WHERE user_id = :uid AND DATE(paid_at) BETWEEN :ms AND :me
            GROUP BY COALESCE(category, 'other')
            UNION ALL
            SELECT '' AS category, SUM(amount) AS spent
            FROM expenses
            WHERE user_id = :uid AND DATE(paid_at) BETWEEN :ms AND :me
        ) s ON s.category = b.category
        WHERE b.user_id = :uid AND b.period_type = 'monthly'
          AND b.period_start = :ms
        ORDER BY b.id
        """,
        uid=user_id, ms=month_start, me=month_end,
    )
