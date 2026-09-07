"""初始化数据库：确保 database 存在并建全部表。

用法::

    python scripts/init_db.py
"""
from __future__ import annotations

import db.models  # noqa: F401  确保所有表注册进 metadata
from db.engine import create_all, ping


def main() -> None:
    if not ping():
        print("[init_db] MySQL 暂不可用，请先启动 docker-compose 的 mysql 服务。")
        return
    create_all()
    print("[init_db] 建表完成。")


if __name__ == "__main__":
    main()
