"""Redis 客户端封装。

Redis 定位（见需求 4.2）：只保存 Agent 运行过程中的**高频 / 实时**数据，
不作为核心业务数据的唯一存储。主要职责：

- 当前对话上下文（conversation context）
- Agent 实时运行状态（manager/academic/... -> running/completed）
- Agent 任务队列（任务调度中间产物）
- 通用缓存 / 会话缓存

使用示例::

    from db.cache import get_redis, agent_status, context_cache

    agent_status("session:1").set("manager", "completed")
    context_cache(1).push("user", "...")
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from redis import Redis
from redis.exceptions import RedisError

from config import settings

_redis: Optional[Redis] = None
#: Redis 健康状态缓存：None=未知 / True=可用 / False=不可用。
#: 一旦判定不可用，后续调用快速短路（不反复尝试连接，避免拖慢主流程）。
_redis_ok: Optional[bool] = None

# Redis key 前缀（便于统一清理与区分业务）
PREFIX_STATUS = "campusops:agent:status"   # Agent 实时状态
PREFIX_QUEUE = "campusops:agent:queue"     # Agent 任务队列
PREFIX_CTX = "campusops:ctx"               # 对话上下文
PREFIX_CACHE = "campusops:cache"           # 通用缓存

#: 内存降级默认值（Redis 不可用时对各类读操作的返回值）
_DEFAULTS: Dict[str, Any] = {
    "none": None,
    "dict": {},
    "list": [],
    "bool": False,
    "int": 0,
}


def get_redis() -> Redis:
    """返回全局 Redis 客户端（decode_responses=True，带连接超时）。"""
    global _redis
    if _redis is None:
        kwargs = dict(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            decode_responses=True,
            socket_connect_timeout=1.5,
            socket_timeout=2.0,
            retry_on_timeout=False,
        )
        if settings.redis.password:
            kwargs["password"] = settings.redis.password
        _redis = Redis(**kwargs)
    return _redis


def _run(kind: str, op: Any) -> Any:
    """执行一次 Redis 操作；Redis 不可用时返回该类型的降级默认值。

    kind 取值对应 _DEFAULTS（none/dict/list/bool/int）。
    """
    global _redis_ok
    if _redis_ok is False:
        return _DEFAULTS[kind]
    try:
        result = op()
        _redis_ok = True
        return result
    except RedisError:
        _redis_ok = False
        return _DEFAULTS[kind]


def ping() -> bool:
    """探测 Redis 连通性（失败返回 False，不抛异常）。"""
    def _p() -> bool:
        return bool(get_redis().ping())
    return bool(_run("bool", _p))


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


class AgentStatusStore:
    """Agent 实时运行状态（hash：agent_name -> status）。"""

    def __init__(self, run_key: str):
        # run_key 形如 session:{id}，用于区分不同轮次执行
        self._key = f"{PREFIX_STATUS}:{run_key}"

    def set(self, agent_name: str, status: str) -> None:
        _run("none", lambda: _pipe(
            lambda: get_redis().hset(self._key, agent_name, status),
            lambda: get_redis().expire(self._key, 3600),
        ))

    def get(self, agent_name: str) -> Optional[str]:
        return _run("none", lambda: get_redis().hget(self._key, agent_name))

    def all(self) -> Dict[str, str]:
        return _run("dict", lambda: get_redis().hgetall(self._key) or {})

    def delete(self) -> None:
        _run("none", lambda: get_redis().delete(self._key))


class ContextStore:
    """当前对话上下文（list，逐条消息追加；带过期时间）。"""

    def __init__(self, conversation_id: int, ttl: int = 7200):
        self._key = f"{PREFIX_CTX}:conv:{conversation_id}"
        self._ttl = ttl

    def push(self, role: str, content: str, **extra: Any) -> None:
        item = {"role": role, "content": content, "ts": time.time(), **extra}
        _run("none", lambda: _pipe(
            lambda: get_redis().rpush(self._key, _json(item)),
            lambda: get_redis().expire(self._key, self._ttl),
        ))

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        def _recent() -> List[Dict[str, Any]]:
            raw_list = get_redis().lrange(self._key, -limit, -1) or []
            return [json.loads(x) for x in raw_list]
        return _run("list", _recent)

    def clear(self) -> None:
        _run("none", lambda: get_redis().delete(self._key))


class TaskQueue:
    """Agent 任务队列：并行任务分组入队，便于编排器消费。"""

    def __init__(self, run_key: str):
        self._key = f"{PREFIX_QUEUE}:{run_key}"

    def push(self, task: Dict[str, Any]) -> None:
        _run("none", lambda: get_redis().rpush(self._key, _json(task)))

    def pop(self) -> Optional[Dict[str, Any]]:
        def _pop() -> Optional[Dict[str, Any]]:
            item = get_redis().lpop(self._key)
            return json.loads(item) if item else None
        return _run("none", _pop)

    def size(self) -> int:
        return _run("int", lambda: get_redis().llen(self._key) or 0)

    def drain(self) -> None:
        _run("none", lambda: get_redis().delete(self._key))


def cache_set(key: str, value: Any, ttl: int = 600) -> None:
    """通用缓存写入。"""
    _run("none", lambda: get_redis().set(
        f"{PREFIX_CACHE}:{key}", _json(value), ex=ttl))


def cache_get(key: str) -> Optional[Any]:
    """通用缓存读取。"""
    def _get() -> Optional[Any]:
        raw_val = get_redis().get(f"{PREFIX_CACHE}:{key}")
        return json.loads(raw_val) if raw_val else None
    return _run("none", _get)


def _pipe(*ops: Any) -> None:
    """顺序执行多次 Redis 命令（Redis 不可用时由 _run 统一降级）。"""
    for op in ops:
        op()
