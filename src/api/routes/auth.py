"""BE-02: đăng ký / đăng nhập / refresh token.

LLM: NO.
"""

from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from src.api.security import (
    TOKEN_TYPE_REFRESH,
    CurrentUser,
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from src.config import get_settings
from src.db.base import get_db
from src.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    # Giữ luồng demo hiện tại: public API có thể tạo patient hoặc dietitian.
    # Trước production cần thay bằng invitation/admin provisioning cho dietitian.
    role: str = Field(pattern="^(patient|dietitian)$")
    full_name: str = Field(min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError("Mật khẩu phải có ít nhất 8 ký tự, gồm cả chữ và số")
        return v


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được đăng ký")

    user = User(email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return RegisterResponse(user_id=user.id, email=user.email, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    # Thông báo lỗi CHUNG cho cả 2 trường hợp (email không tồn tại / sai mật khẩu)
    # để không lộ email nào đã đăng ký (chống user-enumeration).
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email hoặc mật khẩu không đúng")

    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user_id=user.id, role=user.role),
        refresh_token=create_refresh_token(user_id=user.id, role=user.role),
        expires_in=settings.jwt_access_ttl_min * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        claims = decode_token(payload.refresh_token, expected_type=TOKEN_TYPE_REFRESH)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token không hợp lệ hoặc đã hết hạn") from exc

    user = db.get(User, claims["sub"])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không còn tồn tại")

    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user_id=user.id, role=user.role),
        refresh_token=create_refresh_token(user_id=user.id, role=user.role),
        expires_in=settings.jwt_access_ttl_min * 60,
    )


class MeStatusOut(BaseModel):
    terms_accepted_at: datetime | None
    onboarding_completed_at: datetime | None


def _get_self(db: Session, user: CurrentUser) -> User:
    account = db.get(User, user.id)
    if account is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không còn tồn tại")
    return account


@router.get("/me/status", response_model=MeStatusOut)
def get_me_status(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> User:
    return _get_self(db, user)


@router.post("/me/accept-terms", response_model=MeStatusOut)
def accept_terms(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> User:
    account = _get_self(db, user)
    account.terms_accepted_at = datetime.utcnow()
    db.commit()
    db.refresh(account)
    return account


@router.post("/me/onboarding-complete", response_model=MeStatusOut)
def complete_onboarding(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> User:
    account = _get_self(db, user)
    account.onboarding_completed_at = datetime.utcnow()
    db.commit()
    db.refresh(account)
    return account
