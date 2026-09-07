"""任务与计划域表：综合任务、任务依赖、日程、行动方案及明细。

这部分是 Agent 规划的"产物"，是本项目最核心的业务数据。
"""
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
)

from db.models.base import metadata, pk, ts_columns

#: 综合任务表（Agent 拆解/规划的待办任务；可由考试/作业/活动/对话产生）
tasks = Table(
    "tasks",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("title", String(200), nullable=False, comment="任务标题"),
    Column("description", Text, comment="任务说明"),
    Column("task_type", String(16), default="general", comment="academic/schedule/finance/general"),
    Column("source_type", String(16), comment="来源：exam/assignment/activity/manual/agent"),
    Column("source_id", ForeignKey("tasks.id"), comment="来源对象ID(暂存其业务表ID)"),
    Column("priority", SmallInteger, default=3, comment="优先级1-5"),
    Column("status", String(16), default="pending",
           comment="pending/planned/in_progress/done/postponed/cancelled/overdue"),
    Column("deadline", DateTime, comment="截止时间"),
    Column("estimated_hours", DECIMAL(5, 1), default=0, comment="预计耗时(小时)"),
    Column("plan_date", Date, comment="计划执行日期"),
    Column("actual_hours", DECIMAL(5, 1), comment="实际耗时(小时)"),
    Column("conversation_id", ForeignKey("conversations.id"), comment="产生该任务的对话"),
    *ts_columns(),
    Index("ix_tasks_user_status", "user_id", "status"),
    comment="综合任务",
)

#: 任务依赖表（任务间依赖关系）
task_dependencies = Table(
    "task_dependencies",
    metadata,
    pk(),
    Column("task_id", ForeignKey("tasks.id"), nullable=False, comment="后置任务"),
    Column("depends_on_task_id", ForeignKey("tasks.id"), nullable=False, comment="前置任务"),
    UniqueConstraint("task_id", "depends_on_task_id", name="uk_task_dep"),
    comment="任务依赖",
)

#: 日程表（按天/时段的排程结果：课程/任务/活动/考试等时间块）
schedules = Table(
    "schedules",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("day", Date, nullable=False, comment="日期"),
    Column("start_time", Time, nullable=False, comment="开始时间"),
    Column("end_time", Time, nullable=False, comment="结束时间"),
    Column("schedule_type", String(16), nullable=False, comment="course/task/activity/exam/free"),
    Column("ref_type", String(16), comment="来源业务类型"),
    Column("ref_id", Integer, comment="来源业务ID"),
    Column("title", String(200), comment="标题"),
    Column("location", String(128), comment="地点"),
    Column("status", String(16), default="planned", comment="planned/done/skipped"),
    Column("conversation_id", ForeignKey("conversations.id"), comment="产生该日程的对话"),
    *ts_columns(),
    Index("ix_schedules_user_day", "user_id", "day"),
    comment="日程",
)

#: 行动方案表（一轮规划的结果；被重规划覆盖后标记 superseded）
action_plans = Table(
    "action_plans",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("conversation_id", ForeignKey("conversations.id"), comment="关联对话"),
    Column("title", String(200), comment="方案标题"),
    Column("goal", Text, comment="总体目标(需求理解)"),
    Column("summary", Text, comment="方案说明"),
    Column("status", String(16), default="active", comment="draft/active/completed/superseded"),
    Column("replan_of_id", ForeignKey("action_plans.id"), comment="由哪个旧方案重规划而来"),
    *ts_columns(),
    Index("ix_action_plans_user", "user_id"),
    comment="行动方案",
)

#: 行动方案明细（一条条"做什么/何时做/为什么"）
action_plan_items = Table(
    "action_plan_items",
    metadata,
    pk(),
    Column("plan_id", ForeignKey("action_plans.id"), nullable=False, comment="所属方案"),
    Column("task_id", ForeignKey("tasks.id"), comment="关联任务(可空)"),
    Column("content", String(500), nullable=False, comment="执行内容"),
    Column("reason", String(500), comment="如此安排的原因"),
    Column("day", Date, comment="计划日期"),
    Column("start_time", Time, comment="开始时间"),
    Column("end_time", Time, comment="结束时间"),
    Column("status", String(16), default="pending", comment="pending/in_progress/done/postponed"),
    Column("sort_order", Integer, default=0, comment="排序"),
    Column("created_at", DateTime, nullable=False, comment="创建时间"),
    Index("ix_plan_items_plan", "plan_id"),
    comment="行动方案明细",
)
