"""数据访问层（Repository）。

每个业务域一个模块，供 services/agents 调用。约定：
- 函数第一个参数为 ``Session``（事务边界由 ``db.engine.get_session`` 控制）；
- 业务报表/统计使用**手写 SQL**（见 academic/life/task 各 repo 中的原生 SQL 示例）。
"""
from __future__ import annotations

from db.repos import (
    academic_repo as academic,
    agent_run_repo as agent_run,
    conversation_repo as conversation,
    life_repo as life,
    task_repo as task,
    user_repo as user,
)

__all__ = ["academic", "agent_run", "conversation", "life", "task", "user"]
