"""MySQL Engine / Session 管理。

统一通过 ``from config import settings`` 读取连接配置，
对外暴露：

- ``engine``        : 全局 SQLAlchemy Engine（懒初始化）
- ``get_session()`` : 上下文管理器，业务代码内使用
- ``ensure_database()`` : 确保目标 database 存在
- ``create_all()``  : 按 db/models 元数据建表
- ``ping()``        : 连通性检查（healthcheck 用）
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings

# 连接到目标库前，先保证 database 存在（Docker 首次初始化数据库已建好，这里兜底）
_URL_WITHOUT_DB = (
    f"mysql+pymysql://{settings.mysql.user}:{settings.mysql.password}"
    f"@{settings.mysql.host}:{settings.mysql.port}"
)
_URL = f"{_URL_WITHOUT_DB}/{settings.mysql.database}?charset=utf8mb4"

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def _build_engine() -> Engine:
    """按需创建全局 Engine（mysql+pymysql）。"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            _URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )
    return _engine


def _build_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=_build_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _session_factory


def get_engine() -> Engine:
    return _build_engine()


def ensure_database() -> None:
    """若目标 database 不存在则创建（utf8mb4）。"""
    admin = create_engine(_URL_WITHOUT_DB, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(
            text(
                "CREATE DATABASE IF NOT EXISTS `%s` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci" % settings.mysql.database
            )
        )
    admin.dispose()


def create_all() -> None:
    """按 db/models 中登记的元数据创建全部表。"""
    from db.models.base import metadata  # 延迟导入，避免循环依赖

    ensure_database()
    metadata.create_all(bind=_build_engine())


def ping() -> bool:
    """连通性检查（healthcheck 用）。"""
    try:
        with _build_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@contextmanager
def get_session() -> Iterator[Session]:
    """业务代码内的统一事务边界：正常结束自动 commit，异常自动 rollback。"""
    session: Session = _build_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
