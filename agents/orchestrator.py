"""编排器 Orchestrator：执行一次完整的 Multi-Agent 规划闭环。

流程（与需求中的 Plan->Execute->Feedback->Replan 对应）:
1. 建 agent_sessions 记录（running），在 Redis 登记会话状态；
2. Manager: 理解需求 + 拆解子任务（可并行）；
3. 执行各子 Agent（academic / schedule / finance），记录 agent_actions；
4. Schedule 产物 items -> 落库 action_plans + action_plan_items（新方案覆盖旧方案）；
5. 汇总结果 -> 写回 agent_sessions(status/plan_id，失败写 error) 与对话消息。

约定：
- 全程使用共享 Session 的事务（get_session 上下文内完成提交）；
- 单 Agent 失败不中断整体，其余结果照常汇总。
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from db import repos
from db.cache import AgentStatusStore
from db.engine import get_session
from agents.context import AgentRunContext
from agents.registry import registry

#: 各子 Agent 输出若带 items，交由 Schedule 兜底/整理后统一落库。
PLAN_PROVIDERS = ("schedule", "finance", "academic")


def _agent_status(session_id: int) -> AgentStatusStore:
    return AgentStatusStore(f"session:{session_id}")


def run_planning(*, user_id: int, input_text: str,
                 conversation_id: Optional[int] = None,
                 history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """执行一轮规划，返回面向调用方(API/CLI)的结果 dict。"""
    with get_session() as session:
        # 1. 建执行会话
        run = repos.agent_run.create_session(
            session, user_id=user_id, conversation_id=conversation_id,
            input_text=input_text)
        run_id = run["id"]
        status = _agent_status(run_id)
        status.set("orchestrator", "running")

        ctx = AgentRunContext(
            user_id=user_id, conversation_id=conversation_id,
            agent_session_id=run_id, session=session,
            input_text=input_text, history=history or [])

        try:
            # 2. Manager 理解 + 拆解
            manager = registry.get("manager")
            manager.on_start(ctx)
            act_decompose = repos.agent_run.start_action(
                session, session_id=run_id, agent_name="manager", action="decompose",
                request=input_text)
            goal = manager.understand(ctx, input_text)
            subtasks = manager.decompose(ctx, input_text, goal)
            manager.on_end(ctx)
            repos.agent_run.finish_action(
                session, act_decompose,
                response=json.dumps({"goal": goal, "subtasks": len(subtasks)},
                                    ensure_ascii=False)[:2000],
                status="completed" if subtasks else "failed")

            # 3. 依次执行子 Agent（示例为串行；可改成按 need_data 并行）
            results: List[Dict[str, Any]] = []
            plan_items: List[Dict[str, Any]] = []
            for sub in subtasks:
                agent_name = sub.get("agent")
                try:
                    agent = registry.get(agent_name)
                except KeyError:
                    continue
                agent.on_start(ctx)
                action_id = repos.agent_run.start_action(
                    session, session_id=run_id, agent_name=agent_name,
                    action="analyze", request=sub.get("query", input_text))
                result = agent.run(ctx, sub.get("query", input_text))
                results.append(result)
                # 收集可落库的计划明细
                for item in result.get("items") or []:
                    plan_items.append(item)
                repos.agent_run.finish_action(
                    session, action_id,
                    response=(result.get("text") or "")[:2000],
                    status="completed" if result.get("ok") else "failed")
                agent.on_end(ctx, ok=result.get("ok", True))

            # 4. 落库行动方案（事务内，覆盖旧 active 方案）
            plan = None
            if plan_items:
                plan = repos.task.create_plan(
                    session, user_id=user_id, conversation_id=conversation_id,
                    goal=goal, summary="由 Multi-Agent 协作生成", items=plan_items)
                plan_id = plan["id"]
            else:
                plan_id = None

            # 5. 汇总
            act_aggregate = repos.agent_run.start_action(
                session, session_id=run_id, agent_name="manager", action="aggregate",
                request=json.dumps({"goal": goal}, ensure_ascii=False))
            agg = manager.aggregate(ctx, goal, results)
            final_text = agg["text"]
            repos.agent_run.finish_action(session, act_aggregate,
                                          response=final_text[:2000],
                                          status="completed")

            # 记录收尾
            repos.agent_run.complete_session(session, run_id, plan_id=plan_id)
            if conversation_id:
                repos.conversation.add_message(
                    session, conversation_id=conversation_id, role="assistant",
                    content=final_text, agent_name="manager", session_id=run_id)

            status.set("orchestrator", "completed")
            session.commit()

            return {
                "ok": True,
                "agent_session_id": run_id,
                "conversation_id": conversation_id,
                "goal": goal,
                "answer": final_text,
                "plan": repos.task.get_latest_plan_with_items(session, user_id),
                "agent_results": [
                    {"agent": r.get("agent"), "ok": r.get("ok", True),
                     "text": (r.get("text") or "")[:500], "has_items": bool(r.get("items"))}
                    for r in results
                ],
                "agent_status": status.all(),
            }
        except Exception as exc:  # noqa: BLE001
            repos.agent_run.fail_session(session, run_id, error=str(exc))
            status.set("orchestrator", "failed")
            session.commit()
            return {"ok": False, "agent_session_id": run_id, "error": str(exc)}


def get_orchestrator_info() -> Dict[str, Any]:
    """返回 Agent 注册信息（供 API / 注册表展示）。"""
    return {"agents": registry.metadata()}
