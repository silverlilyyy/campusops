"""Academic Agent：学业分析——课程/考试/作业的风险与建议。"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict

from agents import prompts, tools
from agents.base import BaseAgent
from agents.context import AgentRunContext
from agents.registry import registry


def _fmt(d: Any) -> str:
    """把日期/时间对象转字符串，None 转空串。"""
    if d is None:
        return ""
    return d.strftime("%Y-%m-%d %H:%M") if hasattr(d, "strftime") else str(d)


def _summarize_data(ctx: AgentRunContext) -> str:
    """把工具拉到的学业数据整理成给 LLM 看的纯文本。"""
    data = tools.academic_context(ctx)
    if not data.get("has_data"):
        return "（暂无可用的学业数据）"
    lines = []
    if data.get("exams"):
        lines.append("近期考试：")
        for e in data["exams"]:
            lines.append(f"- {e.get('name')} | {_fmt(e.get('exam_date'))} | 重要度{e.get('importance')}")
    if data.get("assignments"):
        lines.append("待完成作业：")
        for a in data["assignments"]:
            lines.append(f"- {a.get('title')} | 截止 {_fmt(a.get('deadline'))} | "
                         f"剩余 {a.get('remain_hours')} 小时")
    if data.get("overdue_count"):
        lines.append(f"⚠ 已逾期作业 {data['overdue_count']} 项")
    return "\n".join(lines)


class AcademicAgent(BaseAgent):
    name = "academic"
    display_name = "学业 Agent"
    description = "分析课程、考试、作业，给出学习优先级与复习建议。"
    role = prompts.ACADEMIC_ROLE

    def run(self, context: AgentRunContext, subtask: str,
            extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.on_start(context)
        summary = _summarize_data(context)
        today = date.today().isoformat()
        user_prompt = (
            f"今天是 {today}。\n{summary}\n\n用户关注/询问：{subtask}\n"
            "请给出结论、优先级排序与建议（纯文本，分点）。"
        )
        text = self.chat(context, user_prompt)
        if not text:
            text = self._fallback(summary)
        data = tools.academic_context(context)
        self.on_end(context, ok=bool(text))
        return {"agent": self.name, "display_name": self.display_name,
                "ok": True, "text": text, "data": data}

    @staticmethod
    def _fallback(summary: str) -> str:
        if not summary or "暂无可用的学业数据" in summary:
            return ("当前没有临近的考试或待办作业，学业状态较轻松。"
                    "如有具体课程/作业需求，可以告诉我。")
        return summary + "\n（离线模式：以上为学业数据概览，联网后可由模型给出优先级建议。）"


registry.register(AcademicAgent)
