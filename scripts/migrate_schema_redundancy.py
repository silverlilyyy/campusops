"""对已存在的 MySQL 库做「冗余设计清理」的一次性迁移（保留数据）。

背景：本次代码审查删除了若干冗余/有问题的表结构，但项目没有 Alembic，
``create_all()`` 对已存在的表不会生效。本脚本用信息库动态定位外键名，
以 ALTER TABLE 方式原地迁移，不重建表、不丢数据。

改动清单（与 db/models 的修改一一对应）：
1. tasks.source_id          : 去掉自引用外键，改为普通 BIGINT 软引用列
2. action_plans.replan_of_id: 删除该「死字段」（及自引用外键）
3. agent_sessions           : 删除 current_agent / result 冗余列，新增 error 列
4. budgets.category         : NULL -> ''，并设为 NOT NULL DEFAULT ''（总预算用空串）
5. user_preferences         : 去掉代理主键 id，改用 user_id 作为主键

用法::

    python scripts/migrate_schema_redundancy.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from db.engine import get_engine  # noqa: E402


def column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
    ), {"t": table, "c": column}).scalar()
    return bool(row)


def fk_name(conn, table: str, column: str, ref_table: str) -> Optional[str]:
    row = conn.execute(text(
        "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t "
        "AND COLUMN_NAME = :c AND REFERENCED_TABLE_NAME = :r "
        "LIMIT 1"
    ), {"t": table, "c": column, "r": ref_table}).scalar()
    return row


def index_exists(conn, table: str, index_name: str) -> bool:
    row = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i"
    ), {"t": table, "i": index_name}).scalar()
    return bool(row)


def drop_fk_if_exists(conn, table: str, column: str, ref_table: str) -> None:
    name = fk_name(conn, table, column, ref_table)
    if name:
        conn.execute(text(f"ALTER TABLE `{table}` DROP FOREIGN KEY `{name}`"))
        print(f"  [ok] drop FK {name} on {table}.{column}")


def main() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        # 1. tasks.source_id：去自引用外键 -> 普通 BIGINT
        print("[1/5] tasks.source_id")
        drop_fk_if_exists(conn, "tasks", "source_id", "tasks")
        conn.execute(text(
            "ALTER TABLE `tasks` MODIFY COLUMN `source_id` BIGINT NULL "
            "COMMENT '来源对象ID(软引用，配合source_type指向业务表)'"
        ))
        print("  [ok] source_id -> BIGINT 软引用")

        # 2. action_plans.replan_of_id：删死字段
        print("[2/5] action_plans.replan_of_id")
        if column_exists(conn, "action_plans", "replan_of_id"):
            drop_fk_if_exists(conn, "action_plans", "replan_of_id", "action_plans")
            conn.execute(text("ALTER TABLE `action_plans` DROP COLUMN `replan_of_id`"))
            print("  [ok] 已删除 replan_of_id")
        else:
            print("  [skip] 列不存在")

        # 3. agent_sessions：删 current_agent / result，加 error
        print("[3/5] agent_sessions")
        for col in ("current_agent", "result"):
            if column_exists(conn, "agent_sessions", col):
                conn.execute(text(f"ALTER TABLE `agent_sessions` DROP COLUMN `{col}`"))
                print(f"  [ok] 已删除 {col}")
        if not column_exists(conn, "agent_sessions", "error"):
            conn.execute(text(
                "ALTER TABLE `agent_sessions` ADD COLUMN `error` TEXT "
                "COMMENT '失败原因(仅失败时写入)'"
            ))
            print("  [ok] 已新增 error")
        else:
            print("  [skip] error 已存在")

        # 4. budgets.category：NULL -> ''，NOT NULL DEFAULT ''
        print("[4/5] budgets.category")
        conn.execute(text("UPDATE `budgets` SET `category` = '' WHERE `category` IS NULL"))
        conn.execute(text(
            "ALTER TABLE `budgets` MODIFY COLUMN `category` VARCHAR(32) NOT NULL "
            "DEFAULT '' COMMENT '类别预算，''''=总预算'"
        ))
        print("  [ok] category -> NOT NULL DEFAULT ''")

        # 5. user_preferences：去 id 代理主键，改 user_id 主键
        print("[5/5] user_preferences")
        if column_exists(conn, "user_preferences", "id"):
            drop_fk_if_exists(conn, "user_preferences", "user_id", "users")
            # 先去掉 AUTO_INCREMENT，否则 DROP PRIMARY KEY 会因自增列无索引而报错
            conn.execute(text(
                "ALTER TABLE `user_preferences` MODIFY COLUMN `id` BIGINT NOT NULL"
            ))
            conn.execute(text("ALTER TABLE `user_preferences` DROP PRIMARY KEY"))
            if index_exists(conn, "user_preferences", "uk_pref_user"):
                conn.execute(text("ALTER TABLE `user_preferences` DROP INDEX `uk_pref_user`"))
            conn.execute(text("ALTER TABLE `user_preferences` DROP COLUMN `id`"))
            conn.execute(text("ALTER TABLE `user_preferences` ADD PRIMARY KEY (`user_id`)"))
            conn.execute(text(
                "ALTER TABLE `user_preferences` ADD CONSTRAINT `fk_pref_user` "
                "FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)"
            ))
            print("  [ok] user_id 已设为主键，id 已删除")
        else:
            print("  [skip] 已迁移（无 id 列）")

    print("\n迁移完成。可运行 python scripts/export_schema.py 校验结构一致性。")


if __name__ == "__main__":
    main()
