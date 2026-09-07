"""Agent 注册表：name -> Agent 工厂/实例。

便于按名字查找 Agent，并统一写入 agents 表（注册展示）。
"""
from __future__ import annotations

from typing import Dict, Type

from agents.base import BaseAgent


class AgentRegistry:
    """管理所有 Agent 类。"""

    def __init__(self) -> None:
        self._classes: Dict[str, Type[BaseAgent]] = {}

    def register(self, agent_cls: Type[BaseAgent]) -> Type[BaseAgent]:
        self._classes[agent_cls.name] = agent_cls
        return agent_cls

    def names(self) -> list[str]:
        return list(self._classes)

    def get(self, name: str) -> BaseAgent:
        cls = self._classes.get(name)
        if cls is None:
            raise KeyError(f"未知 Agent: {name}")
        return cls()

    def all(self) -> list[BaseAgent]:
        return [cls() for cls in self._classes.values()]

    def metadata(self) -> list[dict]:
        return [{"name": c.name, "display_name": c.display_name,
                 "description": c.description} for c in self._classes.values()]


#: 全局注册表
registry = AgentRegistry()
