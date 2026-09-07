"""学术域表：课程、考试、作业（Academic Agent 的数据基础）。"""
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Table,
    Text,
    Time,
)

from db.models.base import metadata, pk, ts_columns

#: 课程表
courses = Table(
    "courses",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("name", String(128), nullable=False, comment="课程名"),
    Column("teacher", String(64), comment="教师"),
    Column("location", String(128), comment="上课地点"),
    Column("weekday", SmallInteger, comment="星期(1-7)"),
    Column("start_time", Time, comment="开始时间"),
    Column("end_time", Time, comment="结束时间"),
    Column("semester", String(32), comment="学期，如 2025-2026-1"),
    Column("credit", DECIMAL(3, 1), comment="学分"),
    Column("start_date", Date, comment="学期开始日期"),
    Column("end_date", Date, comment="学期结束日期"),
    Column("note", Text, comment="备注"),
    *ts_columns(),
    Index("ix_courses_user", "user_id"),
    comment="课程",
)

#: 考试表
exams = Table(
    "exams",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("course_id", ForeignKey("courses.id"), comment="关联课程(可空)"),
    Column("name", String(128), nullable=False, comment="考试名称"),
    Column("exam_date", Date, nullable=False, comment="考试日期"),
    Column("start_time", Time, comment="开始时间"),
    Column("end_time", Time, comment="结束时间"),
    Column("location", String(128), comment="考试地点"),
    Column("weight", DECIMAL(5, 2), comment="成绩占比(%)"),
    Column("importance", SmallInteger, default=3, comment="重要度1-5"),
    Column("status", String(16), default="pending", comment="pending/done/cancelled"),
    Column("note", Text, comment="备注"),
    *ts_columns(),
    Index("ix_exams_user", "user_id"),
    comment="考试",
)

#: 作业/课程设计表
assignments = Table(
    "assignments",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("course_id", ForeignKey("courses.id"), comment="关联课程(可空)"),
    Column("title", String(200), nullable=False, comment="作业/课设标题"),
    Column("kind", String(16), default="homework", comment="homework/project/lab/report/other"),
    Column("description", Text, comment="详细要求"),
    Column("deadline", DateTime, nullable=False, comment="截止时间"),
    Column("estimated_hours", DECIMAL(5, 1), default=0, comment="预计耗时(小时)"),
    Column("priority", SmallInteger, default=3, comment="优先级1-5"),
    Column("status", String(16), default="pending", comment="pending/in_progress/completed/overdue"),
    Column("note", Text, comment="备注"),
    *ts_columns(),
    Index("ix_assignments_user", "user_id"),
    comment="作业/课程设计",
)
