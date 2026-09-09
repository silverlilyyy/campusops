"""向数据库写入完整、可重复的演示数据（demo 用户 + 学业/生活/预算样例）。

用法::

    python scripts/seed.py            # 清空业务数据后写入演示数据
    python scripts/seed.py --reset    # 同默认行为（显式清空）

说明：
- 所有日期相对"今天"计算，保证课程表/考试/作业在时间窗内可被同步为日程；
- 幂等：每次运行先清空全部业务表再重建，不会产生重复数据；
- demo 用户密码为 ``demo``（PBKDF2 哈希存储）。
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

# 允许直接以 `python scripts/seed.py` 运行（把项目根目录加入 sys.path）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, text  # noqa: E402

import db.models  # noqa: F401,E402 注册全部表元数据
import db.repos as repos  # noqa: E402
from app.security import hash_password  # noqa: E402
from db.engine import get_session  # noqa: E402

USERNAME = "demo"
PASSWORD = "demo"

TODAY = date.today()


def _day(delta: int) -> date:
    return TODAY + timedelta(days=delta)


def _dt(delta: int, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(_day(delta), time(hour, minute))


def _ensure_user(session) -> dict:
    existing = repos.user.get_user_by_username(session, USERNAME)
    if existing:
        return existing
    return repos.user.create_user(
        session, username=USERNAME, password_hash=hash_password(PASSWORD),
        nickname="小明", email="xiaoming@example.com")


def _clear_all(session) -> None:
    """关闭外键校验后清空全部表（users 一并重建）。"""
    session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    for t in reversed(db.models.metadata.sorted_tables):
        session.execute(delete(t))
    session.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def _semester_label() -> str:
    """按当前月份估算学期标签，如 2025-2026-1 / 2025-2026-2。"""
    y = TODAY.year
    if TODAY.month >= 8:  # 秋季学期
        return f"{y}-{y + 1}-1"
    return f"{y - 1}-{y}-2"


def seed_courses(session, uid: int) -> dict:
    """8 门典型课程，覆盖周一到周五。返回 {课程标识: 课程 dict}。"""
    spec = [
        ("高数", "高等数学（上）", "王教授", "教一-101", 1, (8, 0), (9, 40), 4.0),
        ("线代", "线性代数", "陈教授", "教一-203", 2, (10, 0), (11, 40), 3.0),
        ("英语", "大学英语", "刘老师", "外语楼-302", 3, (8, 0), (9, 40), 2.0),
        ("数据结构", "数据结构", "赵教授", "机房-204", 3, (14, 0), (15, 40), 3.5),
        ("操作系统", "操作系统", "孙教授", "教二-501", 4, (10, 0), (11, 40), 3.5),
        ("数据库", "数据库系统原理", "李教授", "教二-305", 4, (14, 0), (15, 40), 3.0),
        ("计网", "计算机网络", "周教授", "教一-406", 5, (8, 0), (9, 40), 3.0),
        ("体育", "大学体育（羽毛球）", "吴老师", "体育馆", 5, (14, 0), (15, 40), 1.0),
    ]
    semester = _semester_label()
    out: dict = {}
    for key, name, teacher, loc, wd, (sh, sm), (eh, em), credit in spec:
        out[key] = repos.academic.create_course(
            session, user_id=uid, name=name, teacher=teacher, location=loc,
            weekday=wd, start_time=time(sh, sm), end_time=time(eh, em),
            semester=semester, credit=credit,
            start_date=_day(-30), end_date=_day(90))
    return out


def seed_exams(session, uid: int, courses: dict) -> None:
    spec = [
        ("高数", "高等数学期中考试", 7, (9, 0), (11, 0), "教一-101", 30, 4),
        ("操作系统", "操作系统期中考试", 10, (10, 0), (12, 0), "教二-501", 25, 4),
        ("数据库", "数据库系统期中考试", 14, (14, 0), (16, 0), "教二-305", 30, 3),
        ("数据结构", "数据结构期末考试", 21, (14, 0), (16, 0), "机房-204", 40, 5),
        ("英语", "大学英语期末考试", 25, (8, 0), (10, 0), "外语楼-302", 50, 4),
    ]
    for key, name, dd, (sh, sm), (eh, em), loc, weight, importance in spec:
        repos.academic.create_exam(
            session, user_id=uid, course_id=courses[key]["id"], name=name,
            exam_date=_day(dd), start_time=time(sh, sm), end_time=time(eh, em),
            location=loc, weight=weight, importance=importance)


def seed_assignments(session, uid: int, courses: dict) -> None:
    # (课程键, 标题, kind, 距今天数, 预计耗时, 优先级, 状态)
    spec = [
        ("高数", "高数作业一：极限与连续", "homework", 3, 4, 4, "pending"),
        ("高数", "高数作业二：导数与微分", "homework", 8, 4, 4, "pending"),
        ("高数", "高数章节复习整理", "homework", 1, 3, 3, "in_progress"),
        ("数据结构", "链表实验报告", "lab", 5, 6, 5, "pending"),
        ("数据结构", "二叉树遍历作业", "homework", 12, 5, 4, "pending"),
        ("数据结构", "排序算法对比实验", "lab", 22, 8, 4, "pending"),
        ("数据库", "SQL 实验一：单表查询", "lab", 6, 6, 4, "pending"),
        ("数据库", "数据库课程设计", "course_design", 18, 20, 5, "pending"),
        ("数据库", "SQL 实验零：环境搭建", "lab", -3, 2, 3, "completed"),
        ("操作系统", "进程调度实验", "lab", 9, 8, 4, "pending"),
        ("操作系统", "内存管理实验报告", "report", 15, 6, 3, "pending"),
        ("计网", "Wireshark 抓包实验", "lab", 11, 5, 4, "pending"),
        ("计网", "TCP 三次握手分析报告", "report", 17, 4, 3, "pending"),
        ("英语", "英语作文：我的大学生活", "homework", 4, 2, 3, "pending"),
        ("英语", "英语口语练习打卡", "homework", 20, 2, 2, "pending"),
    ]
    for key, title, kind, dd, hours, priority, status in spec:
        repos.academic.create_assignment(
            session, user_id=uid, course_id=courses[key]["id"], title=title,
            kind=kind, description=f"{title}（自动生成的演示数据）",
            deadline=_dt(dd, 23, 59), estimated_hours=hours,
            priority=priority, status=status)


def seed_activities(session, uid: int) -> None:
    spec = [
        ("社团迎新晚会", "社团", 2, 19, 21, "大学生活动中心", 2),
        ("人工智能前沿讲座", "讲座", 5, 15, 17, "图书馆报告厅", 3),
        ("班级团建聚餐", "团建", 9, 18, 21, "校外餐厅", 2),
        ("校运动会", "体育", 13, 8, 17, "田径场", 4),
        ("编程竞赛宣讲会", "比赛", 16, 19, 20, "教二-101", 3),
        ("志愿服务：社区支教", "志愿", 23, 14, 17, "阳光社区", 2),
    ]
    for name, category, dd, sh, eh, loc, importance in spec:
        repos.life.create_activity(
            session, user_id=uid, name=name, category=category,
            start_time=_dt(dd, sh), end_time=_dt(dd, eh), location=loc,
            importance=importance)


def seed_expenses(session, uid: int) -> None:
    # 近 60 天、约 30 笔消费：(距今天数, 金额, 类别, 备注)
    rows = [
        (0, 18.0, "餐饮", "午餐"),
        (0, 6.5, "餐饮", "早餐"),
        (1, 22.0, "餐饮", "晚餐"),
        (1, 3.0, "交通", "公交"),
        (2, 45.0, "学习", "购买实验报告纸"),
        (2, 15.5, "餐饮", "午餐"),
        (3, 30.0, "娱乐", "电影票"),
        (3, 8.0, "餐饮", "早餐"),
        (4, 20.0, "餐饮", "午餐"),
        (5, 88.0, "学习", "数据库参考书"),
        (6, 12.0, "交通", "地铁"),
        (7, 25.0, "餐饮", "聚餐"),
        (8, 60.0, "生活", "洗衣液、纸巾"),
        (9, 19.0, "餐饮", "午餐"),
        (10, 15.0, "娱乐", "游戏充值"),
        (11, 6.0, "餐饮", "早餐"),
        (12, 40.0, "学习", "打印复习资料"),
        (13, 24.0, "餐饮", "晚餐"),
        (14, 10.0, "交通", "共享单车月卡"),
        (15, 55.0, "生活", "理发"),
        (17, 21.0, "餐饮", "午餐"),
        (19, 35.0, "娱乐", "KTV"),
        (21, 13.0, "餐饮", "早餐"),
        (23, 120.0, "学习", "在线课程会员"),
        (25, 28.0, "餐饮", "周末聚餐"),
        (28, 70.0, "生活", "日用品采购"),
        (31, 18.5, "餐饮", "午餐"),
        (35, 42.0, "学习", "U 盘"),
        (40, 26.0, "餐饮", "晚餐"),
        (45, 90.0, "生活", "宿舍用品"),
    ]
    for days_ago, amount, category, note in rows:
        paid = datetime.combine(_day(-days_ago), time(12, 30))
        repos.life.add_expense(
            session, user_id=uid, amount=amount, category=category,
            paid_at=paid, note=note)


def seed_budgets(session, uid: int) -> None:
    month_start = TODAY.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    month_end = next_month - timedelta(days=1)
    repos.life.upsert_budget(session, user_id=uid, period_type="monthly",
                             amount=2000.0, period_start=month_start,
                             period_end=month_end)
    for category, amount in [("餐饮", 800.0), ("学习", 200.0),
                             ("交通", 100.0), ("娱乐", 150.0), ("生活", 150.0)]:
        repos.life.upsert_budget(session, user_id=uid, period_type="monthly",
                                 amount=amount, period_start=month_start,
                                 period_end=month_end, category=category)


def seed() -> None:
    with get_session() as session:
        _clear_all(session)
        user = _ensure_user(session)
        uid = user["id"]

        repos.user.upsert_preference(
            session, user_id=uid, study_start=time(8, 0), study_end=time(22, 30),
            weekly_study_hours=32.0, monthly_budget=2000.0, notification_enabled=True)

        courses = seed_courses(session, uid)
        seed_exams(session, uid, courses)
        seed_assignments(session, uid, courses)
        seed_activities(session, uid)
        seed_expenses(session, uid)
        seed_budgets(session, uid)

        # 将课程/考试/作业同步为日程块
        counts = repos.task.sync_academic_schedules(session, uid)

        print(f"[seed] 演示数据写入完成：user_id={uid} ({USERNAME}, 密码 {PASSWORD})")
        print(f"[seed] 课程 {len(courses)} 门，日程同步："
              f"课程块 {counts['course']}、考试块 {counts['exam']}、作业块 {counts['assignment']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="写入 CampusOps 演示数据")
    parser.add_argument("--reset", action="store_true",
                        help="先清空全部业务表再写入（默认即清空）")
    args = parser.parse_args()
    seed()
