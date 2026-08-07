"""Kết nối DB thật (Postgres production, SQLite cho dev/test nhanh).

Ticket: BE-01. LLM: NO — thuần hạ tầng, không có logic lâm sàng ở đây.

`ARCHITECTURE.md` §9 chọn Postgres + pgvector cho production. `database_url`
mặc định SQLite (`src/config.py`) để chạy test/dev không cần cài Postgres —
bảng `guideline_chunks.embedding` vì vậy dùng `JSON` thay vì kiểu `Vector`
của pgvector (không cắm được vào SQLite). Khi deploy Postgres thật, đổi
`GuidelineChunk.embedding` sang `pgvector.sqlalchemy.Vector(1536)` — xem
TODO tại chỗ khai báo cột.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, connect_args=connect_args)


_SessionLocal: sessionmaker[Session] | None = None


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def get_db() -> Iterator[Session]:
    """FastAPI dependency: `db: Session = Depends(get_db)`."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
