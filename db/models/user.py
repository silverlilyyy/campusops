"""用户域表：用户 + 用户偏好。"""
from sqlalchemy import Boolean, Column, Date, DECIMAL, ForeignKey, String, Table, Time

from db.models.base import metadata, pk, ts_columns

#: 用户表
users = Table(
    "users",
    metadata,
    pk(),
    Column("username", String(64), nullable=False, unique=True, comment="登录名"),
    Column("password_hash", String(255), nullable=False, comment="密码哈希"),
    Column("nickname", String(64), comment="昵称"),
    Column("email", String(128), comment="邮箱"),
    Column("avatar_url", String(255), comment="头像地址"),
    *ts_columns(),
    comment="用户",
)

#: 用户偏好（与用户一对一）
user_preferences = Table(
    "user_preferences",
    metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True, comment="用户ID(主键)"),
    Column("study_start", Time, comment="习惯学习开始时间"),
    Column("study_end", Time, comment="习惯学习结束时间"),
    Column("weekly_study_hours", DECIMAL(4, 1), comment="每周计划学习时长(小时)"),
    Column("monthly_budget", DECIMAL(10, 2), comment="月度总预算"),
    Column("notification_enabled", Boolean, default=True, comment="是否开启提醒"),
    *ts_columns(),
    comment="用户偏好",
)
