"""对话域表：会话 + 消息（含 Agent 产生的消息）。"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Table, Text

from db.models.base import metadata, pk, ts_columns

#: 会话表（一次用户对话/多轮）
conversations = Table(
    "conversations",
    metadata,
    pk(),
    Column("user_id", ForeignKey("users.id"), nullable=False, comment="所属用户"),
    Column("title", String(200), comment="会话标题(可自动生成)"),
    Column("status", String(16), default="active", comment="active/closed"),
    *ts_columns(),
    Index("ix_conversations_user", "user_id"),
    comment="会话",
)

#: 消息表（user/assistant/system/agent；agent 消息记录 Agent 过程输出）
messages = Table(
    "messages",
    metadata,
    pk(),
    Column("conversation_id", ForeignKey("conversations.id"), nullable=False, comment="所属会话"),
    Column("role", String(16), nullable=False, comment="user/assistant/system/agent"),
    Column("content", Text, comment="消息内容"),
    Column("agent_name", String(32), comment="若为 agent 消息，记录来源 Agent"),
    Column("session_id", ForeignKey("agent_sessions.id"), comment="关联的 Agent 执行会话"),
    Column("created_at", DateTime, nullable=False, comment="创建时间"),
    Index("ix_messages_conversation", "conversation_id"),
    comment="消息",
)
