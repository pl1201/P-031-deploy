import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.api.routes import router
from src.config import get_settings
from src.db.base import get_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    yield
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
async def health():
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
            orphan_count = conn.execute(
                text(
                    """
                    SELECT count(*)
                    FROM meal_plan_items m
                    LEFT JOIN food_items f ON f.id = m.food_id
                    LEFT JOIN dishes d ON d.dish_id = m.dish_id
                    WHERE (m.food_id IS NOT NULL AND f.id IS NULL)
                       OR (m.dish_id IS NOT NULL AND d.dish_id IS NULL)
                       OR (m.food_id IS NULL AND m.dish_id IS NULL)
                    """
                )
            ).scalar_one()
        if orphan_count:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "degraded",
                    "env": settings.app_env,
                    "reason": "Dữ liệu thực phẩm tham chiếu bị thiếu",
                },
            )
        return {"status": "ok", "env": settings.app_env}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "env": settings.app_env, "reason": "Không kết nối được cơ sở dữ liệu"},
        )
