"""数据访问层公共工具。

提供统一的 行 -> dict 转换、原生 SQL 辅助等。
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from sqlalchemy import select, text
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import Table


def row_to_dict(row: Row) -> Dict[str, Any]:
    """单行结果 -> dict。"""
    return dict(row._mapping)


def insert_and_fetch(session: Session, table: Table, values: Dict[str, Any]) -> Dict[str, Any]:
    """插入并回读整行（跨方言：MySQL 不支持 ``INSERT ... RETURNING``）。

    流程：执行 INSERT -> 取自增主键 -> 再按主键 SELECT 该行。
    要求表使用单一自增主键列（本项目统一为 ``id``）。
    """
    result = session.execute(table.insert().values(**values))
    pk = result.inserted_primary_key
    if not pk:
        raise RuntimeError(f"插入 {table.name} 后无法获取自增主键")
    row = session.execute(select(table).where(table.c.id == pk[0])).first()
    return row_to_dict(row)


def rows_to_dicts(rows: Sequence[Row]) -> List[Dict[str, Any]]:
    """多行结果 -> list[dict]。"""
    return [dict(r._mapping) for r in rows]


def scalar(session: Session, sql: str, **params: Any):
    """执行原生 SQL 并返回首行首列（如 count/sum）。"""
    return session.execute(text(sql), params).scalar()


def fetch_all(session: Session, sql: str, **params: Any) -> List[Dict[str, Any]]:
    """执行原生 SQL 并返回 dict 列表（适合写业务报表 SQL）。"""
    return rows_to_dicts(session.execute(text(sql), params).fetchall())


def fetch_one(session: Session, sql: str, **params: Any) -> Dict[str, Any] | None:
    row = session.execute(text(sql), params).first()
    return row_to_dict(row) if row else None
