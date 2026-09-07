"""Multi-Agent 协作层。

包含：
- ``llm``         : 大模型客户端封装（DeepSeek / OpenAI 兼容）
- ``context``     : 单轮执行上下文（DB + Redis 句柄）
- ``base``        : BaseAgent 抽象基类
- ``registry``    : Agent 注册表
- ``tools``       : Agent 可用的数据/写操作工具
- ``prompts``     : 系统提示词集中管理
- ``orchestrator``: 编排器（需求->拆解->执行->落库->汇总 闭环）
- ``replanner``   : 反馈重规划

导入本包即触发各 Agent 注册（registry）。
"""
from __future__ import annotations

# 触发注册（顺序无关，模块顶部 import 保证执行 register）
from agents import (  # noqa: F401
    academic_agent,
    base,
    context,
    finance_agent,
    llm,
    manager_agent,
    orchestrator,
    prompts,
    registry,
    replanner,
    schedule_agent,
    tools,
)

__all__ = [
    "academic_agent", "base", "context", "finance_agent", "llm",
    "manager_agent", "orchestrator", "prompts", "registry",
    "replanner", "schedule_agent", "tools",
]
