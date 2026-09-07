"""Agent 运行域表：Agent 注册表、Agent 执行会话、Agent 动作记录。

用于实现需求中的"Agent 执行过程记录"：
保存 Agent 的任务、调用过程与执行结果，方便前端展示与后续复盘。
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
)

from db.models.base import metadata, pk, ts_columns

#: Agent 注册表（与代码中 agents 注册表对应，便于展示与权限管理）
agents = Table(
    "agents",
    metadata,
    pk(),
    Column("name", String(32), nullable=False, unique=True, comment="manager/academic/schedule/finance"),
    Column("display_name", String(64), comment="展示名"),
    Column("description", Text, comment="职责描述"),
    Column("enabled", Boolean, default=True, comment="是否启用"),
    *ts_columns(),
    comment="Agent注册表",
)

#: Agent 执行会话（一次"需求->执行->结果"的完整运行）
agent_sessions = Table(
    "agent_sessions",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("conversation_id", ForeignKey("conversations.id"), comment="关联对话"),
    Column("input_text", Text, nullable=False, comment="原始用户需求"),
    Column("status", String(16), default="running", comment="queued/running/completed/failed"),
    Column("current_agent", String(32), comment="当前执行中的 Agent"),
    Column("result", Text, comment="最终汇总结果/回答文本"),
    Column("plan_id", ForeignKey("action_plans.id"), comment="本轮生成的行动方案"),
    Column("replan_of_id", ForeignKey("agent_sessions.id"), comment="由哪次执行触发的重规划"),
    Column("started_at", DateTime, comment="开始时间"),
    Column("ended_at", DateTime, comment="结束时间"),
    Column("created_at", DateTime, nullable=False, comment="创建时间"),
    Index("ix_agent_sessions_user", "user_id"),
    comment="Agent执行会话",
)

#: Agent 动作记录（每次 Agent 分析/工具调用/汇总/重规划）
agent_actions = Table(
    "agent_actions",
    metadata,
    pk(),
    Column("session_id", ForeignKey("agent_sessions.id"), nullable=False, comment="所属执行会话"),
    Column("agent_name", String(32), nullable=False, comment="执行 Agent"),
    Column("action", String(32), nullable=False,
           comment="understand/decompose/analyze/tool_call/aggregate/replan"),
    Column("status", String(16), default="running", comment="running/completed/failed"),
    Column("request", Text, comment="动作输入(JSON/文本)"),
    Column("response", Text, comment="动作输出(JSON/文本)"),
    Column("started_at", DateTime, comment="开始时间"),
    Column("ended_at", DateTime, comment="结束时间"),
    Index("ix_agent_actions_session", "session_id"),
    comment="Agent动作记录",
)
