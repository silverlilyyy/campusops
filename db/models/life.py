"""生活域表：活动、消费、预算（Finance Agent / Schedule Agent 数据基础）。"""
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
    UniqueConstraint,
)

from db.models.base import metadata, pk, ts_columns

#: 活动表（社团活动等）
activities = Table(
    "activities",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("name", String(128), nullable=False, comment="活动名称"),
    Column("category", String(32), comment="活动类型，如 社团/讲座/团建"),
    Column("start_time", DateTime, nullable=False, comment="开始时间"),
    Column("end_time", DateTime, comment="结束时间"),
    Column("location", String(128), comment="地点"),
    Column("importance", SmallInteger, default=3, comment="重要度1-5"),
    Column("note", Text, comment="备注"),
    *ts_columns(),
    Index("ix_activities_user", "user_id"),
    comment="活动",
)

#: 消费记录表
expenses = Table(
    "expenses",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("amount", DECIMAL(10, 2), nullable=False, comment="金额(元)"),
    Column("category", String(32), default="other", comment="类别：餐饮/学习/交通/娱乐/生活/other"),
    Column("paid_at", DateTime, nullable=False, comment="消费时间"),
    Column("note", String(255), comment="备注"),
    Column("created_at", DateTime, nullable=False, comment="创建时间"),
    Index("ix_expenses_user_time", "user_id", "paid_at"),
    comment="消费记录",
)

#: 预算表（daily/weekly/monthly；category 为空表示总预算）
budgets = Table(
    "budgets",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("period_type", String(16), nullable=False, comment="daily/weekly/monthly"),
    Column("period_start", Date, nullable=False, comment="周期开始"),
    Column("period_end", Date, nullable=False, comment="周期结束"),
    Column("category", String(32), comment="类别预算，空=总预算"),
    Column("amount", DECIMAL(10, 2), nullable=False, comment="预算金额"),
    *ts_columns(),
    UniqueConstraint("user_id", "period_type", "period_start", "category", name="uk_budget"),
    comment="预算",
)
