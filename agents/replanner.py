"""Replanner：针对用户反馈对既有行动方案进行重规划。

对应需求中的闭环：Plan -> Execute -> Feedback -> Replan。
思路：拿到上轮会话/方案 + 用户反馈 -> 生成新一轮 agent_sessions
（replan_of_id 指向旧会话）-> 复用 Orchestrator 落库（新方案覆盖旧方案）。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from db import repos
from db.engine import get_session
from agents import prompts
from agents.orchestrator import run_planning


def replan(*, user_id: int, feedback: str,
           conversation_id: Optional[int] = None,
           previous_session_id: Optional[int] = None,
           history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """对反馈执行一次重规划。

    previous_session_id 为被反馈的旧 agent_sessions.id（用于记录 replan_of_id 关联）。
    """
    # 可选用 LLM 判定"局部微调 vs 整体重排"，当前直接整体重排（以反馈为新输入）
    with get_session() as session:
        old_plan = None
        if previous_session_id:
            old = repos.agent_run.get_session(session, previous_session_id)
            if old and old.get("plan_id"):
                old_plan = repos.task.get_plan_with_items(session, old["plan_id"])
        session.commit()

    replan_prompt = feedback
    if old_plan:
        old_items = "\n".join(f"- {i.get('content')} {i.get('day')} {i.get('start_time')}~{i.get('end_time')}"
                              for i in old_plan.get("items", []))
        replan_prompt = (
            f"旧方案明细如下，请根据反馈调整：\n{old_items}\n\n反馈：{feedback}"
        )

    # 复用主编排流程执行新规划
    result = run_planning(user_id=user_id, input_text=replan_prompt,
                          conversation_id=conversation_id, history=history)
    if result.get("ok") and previous_session_id:
        # 补记 replan 关联（run_planning 内部新建了会话；此处通过 replan_of 字段关联）
        with get_session() as session:
            new_id = result["agent_session_id"]
            repos.agent_run.update_session(
                session, new_id, replan_of_id=previous_session_id)
            session.commit()
    result["type"] = "replan"
    result["previous_session_id"] = previous_session_id
    return result


def decide_replan_strategy(feedback: str) -> str:
    """返回重规划策略说明（供前端展示）：局部 / 整体。"""
    from agents.llm import get_llm
    llm = get_llm()
    if llm.available:
        raw = llm.chat_json([
            {"role": "system", "content": prompts.REPLAN_ROLE},
            {"role": "user",
             "content": f"用户反馈：{feedback}\n请输出 JSON：{{\"strategy\":\"local|full\"}}"},
        ])
        if raw and raw.get("strategy") in ("local", "full"):
            return raw["strategy"]
    return "full"
