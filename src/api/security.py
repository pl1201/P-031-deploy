"""Băm mật khẩu, JWT, và dependency phân quyền — BE-02.

LLM: NO. Không import LLM client trong module này (đúng CLAUDE.md §4:
danh sách cấm chỉ liệt kê src/clinical/**, src/agents/nodes/compute_*.py,
src/agents/nodes/validate.py, nhưng auth cũng không có lý do gì cần LLM).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

UTC = timezone.utc

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from src.config import get_settings

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def _encode_token(*, user_id: str, role: str, token_type: str, ttl: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(*, user_id: str, role: str) -> str:
    settings = get_settings()
    return _encode_token(
        user_id=user_id, role=role, token_type=TOKEN_TYPE_ACCESS, ttl=timedelta(minutes=settings.jwt_access_ttl_min)
    )


def create_refresh_token(*, user_id: str, role: str) -> str:
    settings = get_settings()
    return _encode_token(
        user_id=user_id, role=role, token_type=TOKEN_TYPE_REFRESH, ttl=timedelta(days=settings.jwt_refresh_ttl_days)
    )


class InvalidTokenError(Exception):
    """Token hết hạn, sai chữ ký, hoặc sai loại (access/refresh)."""


def decode_token(token: str, *, expected_type: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Cần token loại '{expected_type}', nhận '{payload.get('type')}'")
    return payload


@dataclass(frozen=True)
class CurrentUser:
    id: str
    role: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    """Dependency chuẩn cho mọi route cần đăng nhập — raise 401 nếu thiếu/hỏng token."""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Thiếu token xác thực")
    try:
        payload = decode_token(credentials.credentials, expected_type=TOKEN_TYPE_ACCESS)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token không hợp lệ hoặc đã hết hạn") from exc
    return CurrentUser(id=payload["sub"], role=payload["role"])


def require_role(*roles: str):
    """Dependency factory: `Depends(require_role("dietitian", "admin"))`."""

    def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Không đủ quyền cho hành động này")
        return user

    return _dep
