"""数据库模型的公共基础设施。

本项目以 SQLAlchemy 2.0 **Core** 方式定义表结构，所有业务表共享同一个
``metadata``，便于 ``create_all`` 一键建表、以及后续导出 DDL。

约定：
- 主键统一为 ``id`` BIGINT 自增；
- 记录创建/更新时间由 MySQL ``CURRENT_TIMESTAMP`` 生成（默认列默认值在 repos 层维护）；
- 业务枚举统一使用 VARCHAR 长度 16~32 的字符串（语义清晰、便于扩展）；
- 全库 utf8mb4 字符集（docker-compose 已配置）。
"""
from __future__ import annotations

from datetime import date, datetime, time as dtime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    MetaData,
    SmallInteger,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.sql import func

#: 全局元数据（所有表登记于此）
metadata = MetaData()


def pk() -> Column:
    """通用主键列：BIGINT 自增。"""
    return Column("id", BigInteger, primary_key=True, autoincrement=True)


def ts_columns() -> list[Column]:
    """通用时间戳列：created_at / updated_at（created_at 由 DB 生成）。"""
    return [
        Column(
            "created_at",
            DateTime,
            nullable=False,
            server_default=func.now(),
            comment="创建时间",
        ),
        Column(
            "updated_at",
            DateTime,
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
            comment="更新时间",
        ),
    ]
