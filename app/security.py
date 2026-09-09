"""认证与密码工具：PBKDF2 密码哈希 + HMAC 签名令牌（零第三方依赖）。

课程设计场景下的"简单登录"：不引入 OAuth / JWT 库，
用标准库 ``hashlib`` + ``hmac`` 实现：

- ``hash_password`` / ``verify_password``：PBKDF2-SHA256 加盐哈希；
- ``create_token`` / ``verify_token``：HMAC-SHA256 签名的短期令牌。

注意：``AUTH_SECRET`` 是令牌签名密钥，生产环境请通过环境变量注入随机值。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Dict, Optional

#: 令牌签名密钥（可通过环境变量覆盖；演示环境提供默认值）
_SECRET = os.getenv("AUTH_SECRET", "campusops-dev-secret-change-me").encode()

#: 令牌有效期（秒），默认 7 天
TOKEN_TTL = int(os.getenv("AUTH_TOKEN_TTL", str(7 * 24 * 3600)))

#: PBKDF2 迭代次数
_PBKDF2_ITERATIONS = 120_000

#: 哈希存储格式前缀（用于识别新旧格式）
_HASH_PREFIX = "pbkdf2_sha256$"


def hash_password(password: str) -> str:
    """对明文密码做 PBKDF2-SHA256 加盐哈希，返回可存储的字符串。"""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"{_HASH_PREFIX}{_PBKDF2_ITERATIONS}${_b64e(salt).decode()}${_b64e(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    """校验明文密码是否匹配存储的哈希。

    兼容历史遗留的明文 ``password_hash``（例如 seed 早先写入的 ``demo``），
    一旦检测到 PBKDF2 格式则按格式校验。
    """
    if not stored:
        return False
    if stored.startswith(_HASH_PREFIX):
        try:
            _, iterations, salt_b64, dk_b64 = stored.split("$")
            salt = _b64d(salt_b64)
            expected = _b64d(dk_b64)
            dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
            return hmac.compare_digest(dk, expected)
        except Exception:  # noqa: BLE001 哈希串损坏时按不匹配处理
            return False
    # 历史明文密码（常量时间比较，避免时序侧信道）
    return hmac.compare_digest(password.encode(), stored.encode())


def create_token(user: Dict[str, Any]) -> str:
    """为指定用户签发令牌，格式：``base64url(payload).base64url(signature)``。"""
    payload = {
        "uid": user["id"],
        "username": user.get("username"),
        "exp": int(time.time()) + TOKEN_TTL,
    }
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64e(hmac.new(_SECRET, body, hashlib.sha256).digest())
    return f"{body.decode()}.{sig.decode()}"


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """校验令牌签名与有效期，合法则返回 payload，否则返回 None。"""
    try:
        body, sig = token.split(".", 1)
        expected = _b64e(hmac.new(_SECRET, body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected.decode()):
            return None
        payload = json.loads(_b64d(body))
        if int(payload.get("exp", 0)) < time.time():
            return None
        return payload
    except Exception:  # noqa: BLE001 任何解析失败均视为无效令牌
        return None


def _b64e(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
