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
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return one process-wide engine and reuse its connection pool."""
    settings = get_settings()
    is_sqlite = settings.database_url.startswith("sqlite")
    if is_sqlite:
        engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout_sec,
            pool_recycle=settings.db_pool_recycle_sec,
            connect_args={
                "connect_timeout": settings.db_connect_timeout_sec,
                "application_name": "vnutricare-api",
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 3,
            },
        )
    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


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
