import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.routes import router
from src.config import get_settings
from src.db.base import get_engine

logger = logging.getLogger(__name__)


def _warm_database_pool() -> None:
    """Open the first pooled connection without blocking API startup."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection pool is warm")
    except Exception:
        logger.exception("Database warm-up failed; readiness will report the failure")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    warmup_task = (
        asyncio.create_task(asyncio.to_thread(_warm_database_pool)) if settings.app_env == "production" else None
    )
    yield
    if warmup_task is not None and not warmup_task.done():
        warmup_task.cancel()
    get_engine().dispose()
    logger.info("Shutting down...")


app = FastAPI(
    title="AI20K Agent",
    description="AI Agent built with LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
# `.strip()` từng dòng: biến môi trường trên Render/Vercel hay được viết có
# khoảng trắng sau dấu phẩy ("https://a.vercel.app, https://b.app"). Không cắt
# khoảng trắng thì origin thứ hai không bao giờ khớp và trình duyệt chặn với
# lỗi CORS khó truy — xem docs/DEPLOY.md (DAT-25).
allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    """Cheap liveness probe for Render; database readiness is separate."""
    return {"status": "ok", "env": settings.app_env}
