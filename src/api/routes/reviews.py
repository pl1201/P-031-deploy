"""HIT-02: hàng chờ duyệt + duyệt/từ chối thực đơn.

LLM: NO.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.routes.meal_plans import MealPlanOut, meal_plan_load_options
from src.api.security import CurrentUser, require_role
from src.clinical.models import ClinicalTargets, MealSlot, MenuDraft, MenuItem
from src.clinical.nutrition import compute_nutrition
from src.clinical.seeds import load_food_repository
from src.clinical.validator import has_blocking, validate_menu
from src.db.base import get_db
from src.db.models import AuditLog, MealPlan, MealPlanReviewEvent

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _severity_sort_key(plan: MealPlan) -> tuple[int, int]:
    violations = plan.violations or []
    n_hard = sum(1 for v in violations if v.get("severity") == "hard")
    n_soft = sum(1 for v in violations if v.get("severity") == "soft")
    return (-n_hard, -n_soft)


@router.get("/pending", response_model=list[MealPlanOut])
def list_pending_reviews(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("dietitian")),
) -> list[MealPlanOut]:
    plans = db.query(MealPlan).options(*meal_plan_load_options()).filter(MealPlan.status == "pending_review").all()
    plans.sort(key=_severity_sort_key)
    return [MealPlanOut.from_model(p) for p in plans]


class ItemEdit(BaseModel):
    item_id: str
    grams: float = Field(gt=0, le=2000)


class ApproveRequest(BaseModel):
    edits: list[ItemEdit] | None = None
    notes: str | None = None


class RejectRequest(BaseModel):
    reason: str = Field(min_length=10)


class ReviewEventOut(BaseModel):
    id: str
    meal_plan_id: str
    profile_id: str
    reviewer_id: str
    decision: str
    reason: str | None
    notes: str | None
    menu_version: int
    menu_hash: str | None
    nutrition_hash: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/history", response_model=list[ReviewEventOut])
def list_review_history(
    decision: str | None = Query(default=None),
    patient_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> list[MealPlanReviewEvent]:
    query = db.query(MealPlanReviewEvent)
    if decision:
        query = query.filter(MealPlanReviewEvent.decision == decision)
    if patient_id:
        query = query.filter(MealPlanReviewEvent.profile_id == patient_id)
    return query.order_by(MealPlanReviewEvent.created_at.desc()).limit(limit).all()


def _get_pending_plan(db: Session, plan_id: str) -> MealPlan:
    plan = db.get(MealPlan, plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thực đơn")
    if plan.status != "pending_review":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Thực đơn đang ở trạng thái '{plan.status}', không phải chờ duyệt"
        )
    return plan


@router.post("/{plan_id}/approve", response_model=MealPlanOut)
def approve_review(
    plan_id: str,
    payload: ApproveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian")),
) -> MealPlanOut:
    plan = _get_pending_plan(db, plan_id)
    before = {"items": [{"id": i.id, "grams": i.grams} for i in plan.items], "status": plan.status}

    if payload.edits:
        by_id = {i.item_id: i.grams for i in payload.edits}
        for item in plan.items:
            if item.id in by_id:
                item.grams = by_id[item.id]
        db.flush()

        # RULE-1: không tin số gram do reviewer gửi để tính lại dinh dưỡng — luôn
        # gọi lại compute_nutrition/validate_menu trên server từ food_id+grams.
        legacy_foods = load_food_repository()
        draft = MenuDraft()
        for item in plan.items:
            if item.dish is not None:
                recipe_grams = sum(part.grams for part in item.dish.ingredients)
                if recipe_grams <= 0:
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Món ăn không còn định lượng công thức")
                scale = item.grams / recipe_grams
                for part in item.dish.ingredients:
                    draft.items.setdefault(MealSlot(item.slot), []).append(
                        MenuItem(food_id=part.food_id, grams=part.grams * scale)
                    )
                continue
            if item.food_id is None:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Món ăn không còn trong dữ liệu công thức")
            draft.items.setdefault(MealSlot(item.slot), []).append(MenuItem(food_id=item.food_id, grams=item.grams))
        nutrition = compute_nutrition(draft, legacy_foods)
        targets = ClinicalTargets.model_validate(plan.targets)
        violations = validate_menu(nutrition, targets)

        if has_blocking(violations):
            db.rollback()
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Sau khi sửa vẫn còn vi phạm hard — không thể duyệt: "
                + "; ".join(v.message_vi for v in violations if v.blocking),
            )

        plan.computed_nutrition = nutrition.model_dump(mode="json")
        plan.violations = [v.model_dump(mode="json") for v in violations]

    plan.status = "approved"
    plan.reviewer_id = user.id
    plan.reviewer_notes = payload.notes
    plan.approved_menu_version = plan.menu_version
    plan.approved_menu_hash = plan.menu_hash
    plan.approved_nutrition_hash = plan.nutrition_hash

    after = {"items": [{"id": i.id, "grams": i.grams} for i in plan.items], "status": plan.status}
    db.add(AuditLog(at=datetime.now(UTC), actor_id=user.id, action="approve", before=before, after=after))
    db.add(
        MealPlanReviewEvent(
            meal_plan_id=plan.id,
            profile_id=plan.profile_id,
            reviewer_id=user.id,
            decision="approved",
            notes=payload.notes,
            menu_version=plan.menu_version,
            menu_hash=plan.menu_hash,
            nutrition_hash=plan.nutrition_hash,
            created_at=datetime.now(UTC),
        )
    )
    db.commit()
    db.refresh(plan)
    return MealPlanOut.from_model(plan)


@router.post("/{plan_id}/reject", response_model=MealPlanOut)
def reject_review(
    plan_id: str,
    payload: RejectRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian")),
) -> MealPlanOut:
    plan = _get_pending_plan(db, plan_id)
    before = {"status": plan.status}

    plan.status = "rejected"
    plan.reviewer_id = user.id
    plan.reviewer_notes = payload.reason

    db.add(
        AuditLog(
            at=datetime.now(UTC),
            actor_id=user.id,
            action="reject",
            before=before,
            after={"status": plan.status, "reason": payload.reason},
        )
    )
    db.add(
        MealPlanReviewEvent(
            meal_plan_id=plan.id,
            profile_id=plan.profile_id,
            reviewer_id=user.id,
            decision="rejected",
            reason=payload.reason,
            menu_version=plan.menu_version,
            menu_hash=plan.menu_hash,
            nutrition_hash=plan.nutrition_hash,
            created_at=datetime.now(UTC),
        )
    )
    db.commit()
    db.refresh(plan)
    return MealPlanOut.from_model(plan)
