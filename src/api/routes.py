from fastapi import APIRouter, HTTPException

from src.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check dưới prefix /api/v1 (AC của ticket SET-05)."""
    settings = get_settings()
    return {"status": "ok", "env": settings.app_env}


@router.post("/chat")
async def chat() -> None:
    """Chat với AI agent.

    Chưa triển khai: cần ProfileRepository/FoodRepository/MenuGenerator thật
    để dựng graph qua `build_graph()` (xem BE-06 trong docs/TICKETS.md).
    """
    raise HTTPException(status_code=501, detail="Chưa triển khai — xem ticket BE-06")


@router.get("/status")
async def agent_status() -> dict[str, str]:
    """Kiểm tra trạng thái agent."""
    return {"status": "ready", "agent": "LangGraph Agent v1.0"}
