"""学术域数据访问：courses / exams / assignments。

同时提供若干"业务型"原生 SQL 示例（近 N 天考试、逾期作业等），
作为数据库课程设计中的查询展示点。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from db.models.academic import assignments, courses, exams
from db.repos.base import fetch_all, insert_and_fetch, row_to_dict, rows_to_dicts, scalar

_INSERTABLE = {
    "courses": ("user_id", "name", "teacher", "location", "weekday", "start_time",
                "end_time", "semester", "credit", "start_date", "end_date", "note"),
    "exams": ("user_id", "course_id", "name", "exam_date", "start_time", "end_time",
              "location", "weight", "importance", "status", "note"),
    "assignments": ("user_id", "course_id", "title", "kind", "description", "deadline",
                    "estimated_hours", "priority", "status", "note"),
}


def _filter_fields(fields: Dict[str, Any], allowed: tuple) -> Dict[str, Any]:
    return {k: v for k, v in fields.items() if k in allowed and v is not None}


# ---------------------------------------------------------------------------
# courses
# ---------------------------------------------------------------------------
def create_course(session: Session, **data: Any) -> Dict[str, Any]:
    vals = _filter_fields(data, _INSERTABLE["courses"])
    return insert_and_fetch(session, courses, vals)


def list_courses(session: Session, user_id: int, semester: str | None = None) -> List[Dict[str, Any]]:
    stmt = select(courses).where(courses.c.user_id == user_id)
    if semester:
        stmt = stmt.where(courses.c.semester == semester)
    return rows_to_dicts(session.execute(stmt.order_by(courses.c.weekday, courses.c.start_time)).all())


def get_course(session: Session, course_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(select(courses).where(courses.c.id == course_id)).first()
    return row_to_dict(row) if row else None


def update_course(session: Session, course_id: int, **data: Any) -> None:
    vals = _filter_fields(data, _INSERTABLE["courses"])
    if vals:
        session.execute(courses.update().where(courses.c.id == course_id).values(**vals))


def delete_course(session: Session, course_id: int) -> None:
    session.execute(courses.delete().where(courses.c.id == course_id))


# ---------------------------------------------------------------------------
# exams
# ---------------------------------------------------------------------------
def create_exam(session: Session, **data: Any) -> Dict[str, Any]:
    vals = _filter_fields(data, _INSERTABLE["exams"])
    return insert_and_fetch(session, exams, vals)


def list_exams(session: Session, user_id: int) -> List[Dict[str, Any]]:
    return rows_to_dicts(session.execute(
        select(exams).where(exams.c.user_id == user_id).order_by(exams.c.exam_date)
    ).all())


def get_exam(session: Session, exam_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(select(exams).where(exams.c.id == exam_id)).first()
    return row_to_dict(row) if row else None


def update_exam_status(session: Session, exam_id: int, status: str) -> None:
    session.execute(exams.update().where(exams.c.id == exam_id).values(status=status))


def upcoming_exams(session: Session, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """【原生 SQL 示例】未来 days 天内、且未完成的考试。"""
    return fetch_all(
        session,
        """
        SELECT e.id, e.name, e.exam_date, e.start_time, e.end_time, e.location,
               e.weight, e.importance, c.name AS course_name
        FROM exams e
        LEFT JOIN courses c ON c.id = e.course_id
        WHERE e.user_id = :uid
          AND e.status <> 'done'
          AND e.exam_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL :days DAY)
        ORDER BY e.exam_date, e.start_time
        """,
        uid=user_id, days=days,
    )


# ---------------------------------------------------------------------------
# assignments
# ---------------------------------------------------------------------------
def create_assignment(session: Session, **data: Any) -> Dict[str, Any]:
    vals = _filter_fields(data, _INSERTABLE["assignments"])
    return insert_and_fetch(session, assignments, vals)


def list_assignments(session: Session, user_id: int, status: str | None = None) -> List[Dict[str, Any]]:
    stmt = select(assignments).where(assignments.c.user_id == user_id)
    if status:
        stmt = stmt.where(assignments.c.status == status)
    return rows_to_dicts(session.execute(stmt.order_by(assignments.c.deadline)).all())


def get_assignment(session: Session, assignment_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(select(assignments).where(assignments.c.id == assignment_id)).first()
    return row_to_dict(row) if row else None


def update_assignment(session: Session, assignment_id: int, **data: Any) -> None:
    vals = _filter_fields(data, _INSERTABLE["assignments"])
    if vals:
        session.execute(assignments.update().where(assignments.c.id == assignment_id).values(**vals))


def pending_assignments_sorted(session: Session, user_id: int, within_days: int = 30) -> List[Dict[str, Any]]:
    """【原生 SQL 示例】未来 within_days 天内到期、按剩余时间紧迫度排序的作业。"""
    return fetch_all(
        session,
        """
        SELECT a.id, a.title, a.kind, a.deadline, a.estimated_hours, a.priority,
               a.status, c.name AS course_name,
               TIMESTAMPDIFF(HOUR, NOW(), a.deadline) AS remain_hours
        FROM assignments a
        LEFT JOIN courses c ON c.id = a.course_id
        WHERE a.user_id = :uid
          AND a.status IN ('pending', 'in_progress')
          AND a.deadline BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL :days DAY)
        ORDER BY a.deadline
        """,
        uid=user_id, days=within_days,
    )


def count_overdue_assignments(session: Session, user_id: int) -> int:
    """【原生 SQL 示例】已逾期未完成的作业数量。"""
    return scalar(
        session,
        "SELECT COUNT(*) FROM assignments WHERE user_id=:uid "
        "AND status IN ('pending','in_progress') AND deadline < NOW()",
        uid=user_id,
    )
