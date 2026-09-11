"""Manager Agent：总调度——需求理解、任务拆解、结果汇总。

离线降级：无 LLM 时按关键词做简单路由，保证框架可运行。
"""
from __future__ import annotations

from typing import Any, Dict, List

from agents import prompts
from agents.base import BaseAgent
from agents.context import AgentRunContext
from agents.registry import registry

#: 领域关键词 -> Agent
_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "academic": ["考试", "作业", "课设", "复习", "学习", "课程", "成绩", "exam", "assignment", "homework"],
    "schedule": ["安排", "时间", "日程", "冲突", "规划", "计划", "排", "schedule", "plan", "时间表"],
    "finance": ["钱", "消费", "预算", "记账", "支出", "超支", "省钱", "money", "budget", "expense"],
}


class ManagerAgent(BaseAgent):
    name = "manager"
    display_name = "总调度 Agent"
    description = "理解用户需求、向专业子 Agent 分派任务并汇总结果。"
    role = prompts.MANAGER_ROLE

    # -- 需求理解 ---------------------------------------------------------
    def understand(self, context: AgentRunContext, user_text: str) -> str:
        """返回对用户需求的一句话理解（LLM 或规则降级）。"""
        text = self.chat(context, user_text,
                         system="请用一句话概括用户想做什么，直接输出，不要多余解释。")
        if text:
            return text.strip()
        # 规则降级：截取前 60 字作为目标概述
        return user_text.strip()[:60]

    # -- 任务拆解 ---------------------------------------------------------
    def decompose(self, context: AgentRunContext, user_text: str,
                  goal: str) -> List[Dict[str, str]]:
        """把需求拆成 {agent, query} 列表（LLM 或关键词降级）。"""
        from agents.llm import get_llm
        llm = get_llm()
        if llm.available:
            prompt = prompts.MANAGER_DECOMPOSE_TEMPLATE.format(user_text=user_text)
            raw = llm.chat_json([
                {"role": "system", "content": prompts.MANAGER_ROLE},
                {"role": "user", "content": prompt},
            ])
            if raw and isinstance(raw.get("subtasks"), list):
                subs = [s for s in raw["subtasks"]
                        if s.get("agent") in ("academic", "schedule", "finance")]
                if subs:
                    return [{"agent": s["agent"], "query": s.get("query", user_text)}
                            for s in subs]
        return self._decompose_by_keyword(user_text)

    @staticmethod
    def _decompose_by_keyword(user_text: str) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []
        for agent, kws in _INTENT_KEYWORDS.items():
            if any(k in user_text for k in kws):
                hits.append({"agent": agent, "query": user_text})
        if not hits:
            hits.append({"agent": "academic", "query": user_text})
        return hits

    # -- 汇总 ---------------------------------------------------------------
    def aggregate(self, context: AgentRunContext, goal: str,
                  results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """汇总各子 Agent 结论；无 LLM 时按模板拼接。"""
        parts = []
        data_bundle: Dict[str, Any] = {}
        for r in results:
            if not r.get("ok"):
                parts.append(f"[{r.get('agent')}] 处理失败：{r.get('error')}")
                continue
            if r.get("text"):
                parts.append(f"【{r.get('display_name', r.get('agent'))}】\n{r['text']}")
            agent_name = r.get("agent")
            if r.get("data") and isinstance(agent_name, str):
                data_bundle[agent_name] = r["data"]
        fallback = "\n\n".join(parts) or "（各子 Agent 未返回有效内容，请稍后再试。）"

        text = self.chat(
            context, user_text=goal,
            system=prompts.MANAGER_ROLE + "\n下面是各子Agent的结果，请汇总成一段给用户看的完整回答：\n\n" + fallback)
        if not text:
            text = fallback
        return {"text": text, "data": data_bundle, "agent": self.name}


registry.register(ManagerAgent)
