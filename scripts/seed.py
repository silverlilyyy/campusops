"""向数据库写入演示数据（demo 用户 + 学术/生活/偏好样例）。

用法::

    python scripts/seed.py            # 写入演示数据
    python scripts/seed.py --reset    # 先清空所有业务表再写入
"""
from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import delete, text

import db.models  # noqa: F401
import db.repos as repos
from db.engine import get_session

USERNAME = "demo"


def _ensure_user(session) -> dict:
    existing = repos.user.get_user_by_username(session, USERNAME)
    if existing:
        return existing
    return repos.user.create_user(session, username=USERNAME, password_hash="demo_hash_000",
                                  nickname="演示用户", email="demo@example.com")


def seed() -> None:
    with get_session() as session:
        session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for t in reversed(db.models.metadata.sorted_tables):
            session.execute(delete(t))
        session.execute(text("SET FOREIGN_KEY_CHECKS=1"))

        user = _ensure_user(session)
        uid = user["id"]

        repos.user.upsert_preference(session, user_id=uid, study_start=time(8, 0),
                                     study_end=time(22, 0), weekly_study_hours=30.0,
                                     monthly_budget=1500.0)

        # 课程
        c1 = repos.academic.create_course(session, user_id=uid, name="数据库系统原理",
                                          teacher="张老师", location="教一-203",
                                          weekday=1, start_time=time(8, 0), end_time=time(9, 40),
                                          semester="2025-2026-1", credit=3.0,
                                          start_date=date(2025, 9, 1), end_date=date(2026, 1, 16))
        c2 = repos.academic.create_course(session, user_id=uid, name="操作系统",
                                          teacher="李老师", location="教二-501",
                                          weekday=3, start_time=time(10, 0), end_time=time(11, 40),
                                          semester="2025-2026-1", credit=3.5,
                                          start_date=date(2025, 9, 1), end_date=date(2026, 1, 16))

        # 考试
        repos.academic.create_exam(session, user_id=uid, course_id=c1["id"],
                                   name="数据库期中考试", exam_date=date(2025, 11, 15),
                                   start_time=time(9, 0), end_time=time(11, 0),
                                   location="教一-203", weight=30.0, importance=4)

        # 作业
        repos.academic.create_assignment(session, user_id=uid, course_id=c1["id"],
                                         title="SQL 实验报告（一）", kind="lab",
                                         description="完成 ER 图与 10 条 SQL 练习",
                                         deadline=datetime(2025, 10, 20, 23, 59),
                                         estimated_hours=6, priority=4)
        repos.academic.create_assignment(session, user_id=uid, course_id=c2["id"],
                                         title="操作系统进程调度实验", kind="lab",
                                         deadline=datetime(2025, 10, 28, 23, 59),
                                         estimated_hours=8, priority=3)

        # 活动
        repos.life.create_activity(session, user_id=uid, name="社团迎新晚会", category="社团",
                                   start_time=datetime(2025, 10, 12, 19, 0),
                                   end_time=datetime(2025, 10, 12, 21, 0),
                                   location="大学生活动中心", importance=2)

        # 消费
        repos.life.add_expense(session, user_id=uid, amount=25.5, category="餐饮",
                               paid_at=datetime(2025, 10, 8, 12, 10), note="午饭")
        repos.life.add_expense(session, user_id=uid, amount=12.0, category="餐饮",
                               paid_at=datetime(2025, 10, 9, 8, 5), note="早餐")
        repos.life.add_expense(session, user_id=uid, amount=60.0, category="学习",
                               paid_at=datetime(2025, 10, 9, 15, 30), note="买参考书")

        # 预算
        repos.life.upsert_budget(session, user_id=uid, period_type="monthly",
                                 amount=1500.0, period_start=date(2025, 10, 1),
                                 period_end=date(2025, 10, 31))
        repos.life.upsert_budget(session, user_id=uid, period_type="monthly",
                                 amount=500.0, period_start=date(2025, 10, 1),
                                 period_end=date(2025, 10, 31), category="餐饮")

        print(f"[seed] 演示数据写入完成：user_id={uid} ({USERNAME})")


if __name__ == "__main__":
    seed()
