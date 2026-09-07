"""Schedule Agent：时间规划——把待办排进具体时段、规避冲突。

输出 ``items`` 列表（可被 Orchestrator 转为 action_plan_items / schedules），
每项含 day / start_time / end_time / content / reason。
"""
from __future__ import annotations

from datetime import date, datetime, time as dtime, timedelta
from typing import Any, Dict, List

from agents import prompts, tools
from agents.base import BaseAgent
from agents.context import AgentRunContext
from agents.registry import registry


def _default_plan(ctx: AgentRunContext, subtask: str) -> List[Dict[str, Any]]:
    """离线降级：把未来 3 天作为任务日，各排 1 个 2 小时学习块。"""
    items: List[Dict[str, Any]] = []
    for off in range(1, 4):
        day = date.today() + timedelta(days=off)
        free = tools.find_free_slots(ctx, day)
        st = dtime(19, 0)
        en = dtime(21, 0)
        if free and free[0].get("start"):
            try:
                st = dtime.fromisoformat(free[0]["start"])
                en = dtime.fromisoformat(free[0].get("end", "21:00:00"))
            except ValueError:
                pass
        items.append({
            "day": day, "start_time": st, "end_time": en,
            "content": f"完成：{subtask}（第 {off} 天）",
            "reason": "离线模式自动分配的可学习时段",
        })
    return items


class ScheduleAgent(BaseAgent):
    name = "schedule"
    display_name = "时间规划 Agent"
    description = "将任务安排进具体日期与时段，检测并规避时间冲突。"
    role = prompts.SCHEDULE_ROLE

    def run(self, context: AgentRunContext, subtask: str,
            extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.on_start(context)
        from agents.llm import get_llm
        llm = get_llm()

        ctx_data = tools.schedule_context(context)
        tasks_txt = self._render_tasks(ctx_data)
        items: List[Dict[str, Any]] = []

        if llm.available:
            prompt = (
                f"今天：{date.today().isoformat()}\n"
                f"现有日程：{tasks_txt}\n\n"
                f"需求：{subtask}\n"
                "请把需要安排的事项排进具体日期与时段（未来1~3天），输出 JSON：\n"
                '{"items": [{"day":"YYYY-MM-DD","start":"HH:MM","end":"HH:MM",'
                '"content":"做什么","reason":"为什么这样排"}]}\n'
                "要求：不与现有日程冲突。"
            )
            raw = llm.chat_json([
                {"role": "system", "content": self.role},
                {"role": "user", "content": prompt},
            ])
            items = self._parse_items(raw)

        if not items:
            items = _default_plan(context, subtask)

        text = self._render_items(items, ctx_data)
        self.on_end(context, ok=True)
        return {"agent": self.name, "display_name": self.display_name,
                "ok": True, "text": text, "items": items,
                "data": {"conflicts": ctx_data.get("conflicts", [])}}

    # -- 渲染 / 解析 ---------------------------------------------------------
    @staticmethod
    def _render_tasks(ctx_data: Dict[str, Any]) -> str:
        if not ctx_data.get("has_data"):
            return "（暂无可用的日程数据）"
        lines = ["近期待办任务："]
        for t in ctx_data.get("pending_tasks", []):
            lines.append(f"- {t.get('title')} (截止 {t.get('deadline')})")
        if ctx_data.get("conflicts"):
            lines.append(f"⚠ 检测到 {len(ctx_data['conflicts'])} 处时间冲突")
        return "\n".join(lines)

    @staticmethod
    def _parse_items(raw: Any) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        if not raw or not isinstance(raw.get("items"), list):
            return out
        for it in raw["items"]:
            try:
                day = date.fromisoformat(it["day"])
                st = dtime.fromisoformat(it.get("start", "19:00"))
                en = dtime.fromisoformat(it.get("end", "21:00"))
            except (KeyError, ValueError):
                continue
            out.append({"day": day, "start_time": st, "end_time": en,
                        "content": it.get("content", ""), "reason": it.get("reason")})
        return out

    @staticmethod
    def _render_items(items: List[Dict[str, Any]], ctx_data: Dict[str, Any]) -> str:
        if not items:
            return "没有需要排程的事项。"
        lines = ["为你安排如下："]
        for it in items:
            lines.append(f"- {it['day']} {it['start_time']}~{it['end_time']}  {it['content']}")
        if ctx_data.get("conflicts"):
            lines.append(f"\n（注意：检测到 {len(ctx_data['conflicts'])} 处原有时间冲突，"
                         "可在对话中让我重新调整。）")
        return "\n".join(lines)


registry.register(ScheduleAgent)
