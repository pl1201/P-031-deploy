"""Health check, status, và endpoint chat stub — di chuyển nguyên trạng từ
`src/api/routes.py` khi tách route theo resource (BE-02..BE-09)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from pydantic import BaseModel, Field

from src.config import get_settings
from src.db.base import get_engine

router = APIRouter(tags=["misc"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check dưới prefix /api/v1 (AC của ticket SET-05)."""
    settings = get_settings()
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
            orphan_count = conn.execute(text("SELECT count(*) FROM meal_plan_items m LEFT JOIN food_items f ON f.id=m.food_id WHERE f.id IS NULL")).scalar_one()
        if orphan_count:
            return JSONResponse(status_code=503, content={"status": "degraded", "env": settings.app_env, "reason": "Dữ liệu thực phẩm tham chiếu bị thiếu"})
        return {"status": "ok", "env": settings.app_env}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "env": settings.app_env, "reason": "Không kết nối được cơ sở dữ liệu"})


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    blocked: bool
    method: str  # "regex" | "llm" | "safe_pattern"


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Chat với AI agent — AGT-07: guardrail chặn chỉ định y khoa tầng 1 (regex).

    LLM: Tầng 2 (Gemini classifier) tuỳ cấu hình GEMINI_API_KEY.
    RULE-3: Endpoint này không trả thông tin y khoa trực tiếp cho bệnh nhân.
    """
    from src.agents.guardrail import check_guardrail

    result = check_guardrail(payload.message)
    if result.blocked:
        return ChatResponse(reply=result.safe_response, blocked=True, method=result.method)

    # Placeholder dinh dưỡng — RAG sẽ thay thế khi ADV-01..ADV-03 xong
    return ChatResponse(
        reply=(
            "Câu hỏi của bạn liên quan đến dinh dưỡng. Hiện tại hệ thống đang "
            "trong giai đoạn MVP — vui lòng xem thực đơn đã được chuyên gia duyệt "
            "trong mục 'Thực đơn của tôi' để có thông tin dinh dưỡng cá thể hóa. "
            "Nếu có câu hỏi cụ thể, hãy liên hệ trực tiếp với chuyên gia dinh dưỡng."
        ),
        blocked=False,
        method=result.method,
    )


@router.get("/status")
async def agent_status() -> dict[str, str]:
    """Kiểm tra trạng thái agent."""
    return {"status": "ready", "agent": "LangGraph Agent v1.0"}
