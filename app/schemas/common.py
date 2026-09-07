"""通用 Schema：统一响应结构。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一响应包装：{ok, data, message}。"""

    ok: bool = True
    data: Optional[Any] = None
    message: str = ""

    @classmethod
    def success(cls, data: Any = None, message: str = "ok") -> "ApiResponse":
        return cls(ok=True, data=data, message=message)

    @classmethod
    def fail(cls, message: str, data: Any = None) -> "ApiResponse":
        return cls(ok=False, data=data, message=message)


class HealthInfo(BaseModel):
    mysql: bool
    redis: bool
    agents: list[Dict[str, str]] = []
