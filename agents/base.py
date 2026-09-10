"""Agent 抽象基类。

约定：每个 Agent 必须实现 ``run(context, subtask) -> dict``，返回形如::

    {
        "agent": "academic",
        "ok": True,
        "text": "面向用户的自然语言结论",
        "data": {...},        # 结构化数据（供 Manager 汇总/前端展示）
        "items": [...],       # 可转为行动方案明细的条目（schedule/finance 等）
    }

Agent 只负责"分析 + 决策"，不直接提交事务；编排器(Orchestrator)负责
把各 Agent 输出统一落库（tasks / action_plans / schedules）。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from db import repos
from agents.context import AgentRunContext


class BaseAgent:
    """Agent 基类。

    Attributes:
        name:          唯一标识，如 manager/academic/schedule/finance
        display_name:  展示名
        description:   职责说明（注册到 agents 表）
        role:          系统提示词中的角色定位（子类覆盖）
    """

    name: str = "base"
    display_name: str = "Base Agent"
    description: str = ""
    role: str = "你是 CampusOps 校园生活规划助手的一个子 Agent。"

    def __init__(self) -> None:
        self._client = None  # 由 llm.get_llm() 惰性填充

    # -- 生命周期钩子：供编排器调用 -----------------------------------------
    def on_start(self, context: AgentRunContext) -> None:
        """Agent 开始：更新 Redis 状态。"""
        try:
            context.status_store.set(self.name, "running")
        except Exception:
            pass  # Redis 异常不影响主流程

    def on_end(self, context: AgentRunContext, ok: bool = True) -> None:
        try:
            context.status_store.set(self.name, "completed" if ok else "failed")
        except Exception:
            pass

    # -- 动作记录 -------------------------------------------------------------
    def log_action(self, context: AgentRunContext, action: str, request: str,
                   response: Optional[str] = None) -> None:
        """记录一次 Agent 动作到 agent_actions（可被前端回放）。"""
        try:
            repos.agent_run.start_action(
                context.session, session_id=context.agent_session_id,
                agent_name=self.name, action=action, request=request)
        except Exception:
            pass

    # -- LLM 辅助 -------------------------------------------------------------
    def _llm_messages(self, context: AgentRunContext, user_text: str,
                      system: Optional[str] = None) -> list:
        return [
            {"role": "system", "content": system or self.role},
            {"role": "user", "content": user_text},
        ]

    def chat(self, context: AgentRunContext, user_text: str,
             system: Optional[str] = None) -> Optional[str]:
        """调用大模型（无 Key 时返回 None，交由调用方降级）。"""
        from agents.llm import get_llm
        llm = get_llm()
        if not llm.available:
            return None
        return llm.chat(self._llm_messages(context, user_text, system))

    # -- 业务实现 ---------------------------------------------------------------
    def run(self, context: AgentRunContext, subtask: str,
            extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行一次子任务分析，返回结果 dict。

        各专业子 Agent（academic/schedule/finance）必须覆盖实现；
        manager 作为协调者只实现 understand/decompose/aggregate，不直接执行。
        """
        raise NotImplementedError(
            f"{self.name} 不直接执行子任务（仅协调者具备 run 实现）")
