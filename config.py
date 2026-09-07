"""项目配置：从 .env 加载 MySQL / Redis / DeepSeek(AI) 配置。

用法:
    from config import settings
    print(settings.mysql.host)
    print(settings.redis.port)
    print(settings.ai.model)
"""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# 加载项目根目录下的 .env（默认覆盖已有的环境变量）
load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class MySQLConfig:
    """MySQL 连接配置。"""
    host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    port: int = _int("MYSQL_PORT", 3307)
    user: str = os.getenv("MYSQL_USER", "campusops")
    password: str = os.getenv("MYSQL_PASSWORD", "")
    database: str = os.getenv("MYSQL_DATABASE", "campusops")

    @property
    def dsn(self) -> str:
        """返回 pymysql 可用的连接参数。"""
        return f"mysql+pymysql://{self.user}:***@{self.host}:{self.port}/{self.database}"


@dataclass(frozen=True)
class RedisConfig:
    """Redis 连接配置。"""
    host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    port: int = _int("REDIS_PORT", 6379)
    password: str = os.getenv("REDIS_PASSWORD", "")
    db: int = _int("REDIS_DB", 0)


@dataclass(frozen=True)
class AIConfig:
    """AI 模型配置（DeepSeek，OpenAI 兼容接口）。"""
    provider: str = "deepseek"
    api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    temperature: float = _float("AI_TEMPERATURE", 0.7)
    max_tokens: int = _int("AI_MAX_TOKENS", 4096)


@dataclass(frozen=True)
class Settings:
    mysql: MySQLConfig = field(default_factory=MySQLConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    ai: AIConfig = field(default_factory=AIConfig)


settings = Settings()
