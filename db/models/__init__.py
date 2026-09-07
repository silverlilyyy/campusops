"""模型包入口：导入全部表模块并登记到 metadata。

约定：所有模块在本文件被导入，从而把表注册进 ``db.models.base.metadata``，
供 ``db.engine.create_all`` 使用。

导入全部模型后可通过便捷映射 ``TABLES["users"]`` 取到对应 Table 对象。
"""
from db.models.base import metadata, pk, ts_columns  # noqa: F401

# 导入各域表（顺序即元数据注册顺序）
from db.models import user, academic, life, task_plan, conversation, agent_run  # noqa: F401

#: 表名 -> Table 对象 的便捷映射
TABLES: dict[str, object] = {}
for _tbl in metadata.tables.values():
    TABLES[_tbl.name] = _tbl

__all__ = [
    "metadata",
    "TABLES",
    "user",
    "academic",
    "life",
    "task_plan",
    "conversation",
    "agent_run",
]
