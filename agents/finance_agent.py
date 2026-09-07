"""Finance Agent：消费规划——分析消费构成、预算对比、记账。

支持两类意图：
- 分析/建议：汇总消费与预算，给出省支建议；
- 记账（工具调用）：把用户描述的消费写入 expenses 表。
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, List

from agents import prompts, tools
from agents.base import BaseAgent
from agents.context import AgentRunContext
from agents.registry import registry


def _summarize(ctx: AgentRunContext) -> str:
    data = tools.finance_context(ctx)
    if not data.get("has_data"):
        return "（暂无可用的消费/预算数据）"
    lines = ["近期消费："]
    for e in data.get("expenses", [])[:8]:
        lines.append(f"- {e.get('paid_at')}  {e.get('category')}  ¥{e.get('amount')}  {e.get('note') or ''}")
    if data.get("budget"):
        lines.append("预算执行情况：")
        for b in data["budget"]:
            lines.append(f"- {b.get('category') or '总预算'}: 预算¥{b.get('budget_amount')} "
                         f"已花¥{b.get('spent')} 剩余¥{b.get('remaining')} "
                         f"({b.get('used_percent')}%)")
    return "\n".join(lines)


class FinanceAgent(BaseAgent):
    name = "finance"
    display_name = "消费规划 Agent"
    description = "分析消费构成与预算使用，给出省支建议，支持记账。"
    role = prompts.FINANCE_ROLE

    def run(self, context: AgentRunContext, subtask: str,
            extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.on_start(context)

        # 1) 若为记账请求：尝试结构化写入
        if self._looks_like_recording(subtask):
            rec = self._try_record(subtask, context)
            if rec:
                self.on_end(context, ok=True)
                return {"agent": self.name, "display_name": self.display_name,
                        "ok": True,
                        "text": f"已记一笔消费：¥{rec['amount']}（{rec['category']}）{rec.get('note') or ''}",
                        "data": {"recorded": rec}}

        # 2) 否则做分析
        summary = _summarize(context)
        text = self.chat(context, subtask + "\n\n" + summary)
        if not text:
            text = self._fallback(summary)
        self.on_end(context, ok=bool(text))
        return {"agent": self.name, "display_name": self.display_name,
                "ok": True, "text": text, "data": tools.finance_context(context)}

    # -- 记账辅助 ------------------------------------------------------------
    @staticmethod
    def _looks_like_recording(text: str) -> bool:
        return any(k in text for k in ("记一笔", "记账", "花了", "消费了", "支出", "买了", "花了多少钱", "帮我记"))

    def _try_record(self, text: str, ctx: AgentRunContext) -> Dict[str, Any] | None:
        amount = self._extract_amount(text)
        if amount is None:
            return None
        from agents import tools as _tools
        cat = self._guess_category(text)
        res = _tools.record_expense(ctx, amount=amount, category=cat, note=text[:80])
        return res.get("expense") if res.get("ok") else None

    @staticmethod
    def _extract_amount(text: str) -> float | None:
        m = re.search(r"(?:¥|￥|花了|消费|支出|共)?\s*(\d+(?:\.\d{1,2})?)\s*元", text)
        if m:
            return float(m.group(1))
        m2 = re.search(r"[¥￥]\s*(\d+(?:\.\d{1,2})?)", text)
        return float(m2.group(1)) if m2 else None

    @staticmethod
    def _guess_category(text: str) -> str:
        table = {"餐": "餐饮", "饭": "餐饮", "吃": "餐饮", "书": "学习", "文具": "学习",
                 "课": "学习", "交通": "交通", "车": "交通", "地铁": "交通", "玩": "娱乐",
                 "电影": "娱乐", "游戏": "娱乐", "买": "生活", "超市": "生活"}
        for k, cat in table.items():
            if k in text:
                return cat
        return "other"

    @staticmethod
    def _fallback(summary: str) -> str:
        if "暂无" in summary:
            return "目前还没有消费或预算记录。可以告诉我本月预算或让我帮你记一笔账。"
        return summary + "\n（离线模式：以上为消费概览，联网后可由模型给出省支建议。）"


registry.register(FinanceAgent)
