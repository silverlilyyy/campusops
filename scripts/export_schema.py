"""导出表结构 SQL 到 sql/schema.sql（数据库课程设计的 DDL 交付物）。

用法::

    python scripts/export_schema.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# 允许直接以 `python scripts/export_schema.py` 运行（把项目根目录加入 sys.path）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlalchemy
from sqlalchemy.dialects import mysql as mysql_dialect  # noqa: F401  方言需显式导入
from sqlalchemy.schema import CreateTable

import db.models  # noqa: F401
from db.models.base import metadata

OUT = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"


def main() -> None:
    lines = [
        "-- CampusOps 数据库结构（由 db/models 自动导出）",
        "-- 说明：仅供查阅与文档使用；建库请运行 python scripts/init_db.py",
        "",
        "CREATE DATABASE IF NOT EXISTS campusops DEFAULT CHARACTER SET utf8mb4 "
        "COLLATE utf8mb4_unicode_ci;",
        "USE campusops;",
        "",
    ]
    for table in metadata.sorted_tables:
        lines.append(str(
            CreateTable(table).compile(dialect=mysql_dialect.dialect())))
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[export_schema] 已写出 {len(metadata.sorted_tables)} 张表 -> {OUT}")


if __name__ == "__main__":
    main()
