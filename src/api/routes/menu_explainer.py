"""Menu Explainer & Coaching (`AGT-13`, ticket B2) — endpoint gọi theo yêu cầu.

Không phải node trong LangGraph — mọi node hiện tại chạy TRƯỚC khi duyệt
(`to_review`/HITL), còn duyệt (`POST /reviews/{planId}/approve`) chỉ đổi
`status` trên DB, không resume graph. Endpoint này diễn giải một thực đơn ĐÃ
`approved` cho chính bệnh nhân (hoặc chuyên gia/admin xem lại).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.routes.meal_plans import MealPlanOut, meal_plan_load_options
from src.api.security import CurrentUser, get_current_user
from src.clinical.menu_explainer import MenuFacts, assemble_menu_facts
from src.db.base import get_db
from src.db.models import MealPlan
from src.db.models import PatientProfile as DbPatientProfile
from src.services.menu_coach import explain_menu_naturally
from src.services.menu_explanation_guard import check_grounded

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])

_FALLBACK_TEMPLATE_HEADER = "Thực đơn ngày {plan_date} gồm các món sau:"
_STATUS_LABEL_VI = {"over": "vượt ngưỡng", "under": "dưới ngưỡng", "within": "trong ngưỡng an toàn"}


class MenuExplainResponse(BaseModel):
    facts: MenuFacts
    text_vi: str


def _render_template(facts: MenuFacts) -> str:
    """Bản render mẫu tất định — dùng khi LLM bịa số (guard `ok=False`).

    KHÔNG gọi LLM, chỉ lắp câu từ dữ kiện đã có, đảm bảo luôn có một phản hồi
    an toàn để phục vụ người dùng thay vì lỗi 500 hay im lặng.
    """
    lines = [_FALLBACK_TEMPLATE_HEADER.format(plan_date=facts.plan_date)]
    for item in facts.items:
        lines.append(f"- [{item.slot}] {item.name_vi}: {item.grams} g")
    for nutrient in facts.nutrients:
        if nutrient.status != "within":
            lines.append(f"Lưu ý: {nutrient.label_vi} đang {_STATUS_LABEL_VI[nutrient.status]}.")
    for note in facts.soft_notes:
        lines.append(f"Ghi chú: {note}")
    return "\n".join(lines)


def _get_plan_for_explain(db: Session, plan_id: str, user: CurrentUser) -> MealPlan:
    """404 nếu không tồn tại hoặc bệnh nhân không phải chủ hồ sơ; 409 nếu chưa
    `approved`. Thứ tự kiểm tra CỐ Ý: ownership trước status, để một bệnh nhân
    không sở hữu thực đơn không bao giờ học được (qua mã lỗi 409 so với 404)
    rằng thực đơn đó tồn tại nhưng chưa duyệt — chỉ nhận được 404 duy nhất.
    """
    plan = db.query(MealPlan).options(*meal_plan_load_options()).filter(MealPlan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thực đơn")

    if user.role == "patient":
        profile = db.get(DbPatientProfile, plan.profile_id)
        if profile is None or profile.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thực đơn")

    if plan.status != "approved":
        raise HTTPException(status.HTTP_409_CONFLICT, "Thực đơn chưa được chuyên gia duyệt")

    return plan


@router.get("/{plan_id}/explain", response_model=MenuExplainResponse)
def explain_meal_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> MenuExplainResponse:
    plan = _get_plan_for_explain(db, plan_id, user)

    out = MealPlanOut.from_model(plan)
    facts = assemble_menu_facts(
        plan_date=out.plan_date.isoformat(),
        items=[{"name_vi": i.name_vi, "slot": i.slot, "grams": i.grams} for i in out.items],
        targets=out.targets,
        nutrition=out.computed_nutrition or {},
        violations=out.violations,
    )

    text_vi = explain_menu_naturally(facts)
    guard = check_grounded(text_vi, facts)
    if not guard.ok:
        text_vi = _render_template(facts)

    return MenuExplainResponse(facts=facts, text_vi=text_vi)


__all__ = ["router", "MenuExplainResponse"]
