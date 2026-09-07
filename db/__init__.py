"""db 包：MySQL 数据模型（SQLAlchemy Core）与数据访问层（repos）。

- db/models : 18 张核心业务表的 SQLAlchemy Core 定义（单一事实来源，可 create_all）
- db/repos  : 数据访问层，使用 SQLAlchemy Core / 原生 SQL 编写
- db/engine : MySQL Engine / Session 管理
- db/cache  : Redis 客户端封装（对话上下文、Agent 状态、任务队列）
"""
