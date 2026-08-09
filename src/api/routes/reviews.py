"""HIT-02: hàng chờ duyệt + duyệt/từ chối thực đơn.

LLM: NO.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.agents.graph import build_review_recompute_graph
from src.api.clinical_bridge import to_clinical_profile
from src.api.routes.meal_plans import MealPlanOut, meal_plan_load_options
from src.api.security import CurrentUser, require_role
from src.clinical.dishes import load_dish_food_repository
from src.clinical.integrity import hash_menu, hash_nutrition, payload_has_p0
from src.clinical.models import ClinicalTargets, MealSlot, MenuDraft, MenuItem
from src.clinical.seeds import load_food_repository
from src.db.base import get_db
from src.db.models import AuditLog, MealPlan

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _severity_sort_key(plan: MealPlan) -> tuple[int, int]:
    risk_rank = {"P0": 3, "P1": 2, "P2": 1, "none": 0}
    violations = plan.violations or []
    n_hard = sum(1 for v in violations if v.get("severity") == "hard")
    return (-risk_rank.get(plan.highest_risk, 0), -n_hard)


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


class RecomputeRequest(BaseModel):
    edits: list[ItemEdit] = Field(min_length=1)


def _get_pending_plan(db: Session, plan_id: str) -> MealPlan:
    plan = db.get(MealPlan, plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thực đơn")
    if plan.status != "pending_review":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Thực đơn đang ở trạng thái '{plan.status}', không phải chờ duyệt"
        )
    return plan


def _apply_edits(plan: MealPlan, edits: list[ItemEdit]) -> None:
    by_id = {item.id: item for item in plan.items}
    unknown = sorted({edit.item_id for edit in edits} - set(by_id))
    if unknown:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown meal-plan item(s): {', '.join(unknown)}")
    for edit in edits:
        by_id[edit.item_id].grams = edit.grams


def _draft_and_repository(plan: MealPlan):
    dish_foods = load_dish_food_repository()
    legacy_foods = load_food_repository()
    uses_dishes = all(item.dish_id for item in plan.items)
    if any(item.dish_id for item in plan.items) and not uses_dishes:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Mixed dish/ingredient plans cannot be recomputed safely"
        )
    foods = dish_foods if uses_dishes else legacy_foods
    draft = MenuDraft()
    for item in plan.items:
        candidate_id = dish_foods.food_id_for_dish(item.dish_id) if item.dish_id else item.food_id
        if candidate_id is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Meal item no longer exists in the food database")
        draft.items.setdefault(MealSlot(item.slot), []).append(MenuItem(food_id=candidate_id, grams=item.grams))
    return draft, foods


def _recompute_downstream(plan: MealPlan, edits: list[ItemEdit], db: Session) -> dict:
    """Run only compute -> safety -> triage -> explain after a reviewer edit."""
    _apply_edits(plan, edits)
    db.flush()
    draft, foods = _draft_and_repository(plan)
    graph = build_review_recompute_graph(foods=foods)
    result = graph.invoke(
        {
            "patient_id": plan.profile_id,
            "profile": to_clinical_profile(plan.profile),
            "targets": ClinicalTargets.model_validate(plan.targets),
            "draft_menu": draft,
            "status": "pending_review",
            "retry_count": plan.retry_count,
            "used_fallback": bool((plan.review_packet or {}).get("used_fallback")),
        }
    )
    nutrition = result["computed_nutrition"]
    plan.computed_nutrition = nutrition.model_dump(mode="json")
    plan.violations = [violation.model_dump(mode="json") for violation in result.get("violations", [])]
    plan.safety_findings = [finding.model_dump(mode="json") for finding in result.get("safety_findings", [])]
    packet = result["review_packet"]
    plan.review_packet = packet.model_dump(mode="json")
    plan.highest_risk = result.get("highest_risk", "none")
    plan.citations = [citation.model_dump(mode="json") for citation in result.get("citations", [])]
    plan.explanation_vi = result.get("expert_explanation")
    new_timings = result.get("node_timings_ms") or {}
    existing_timings = plan.node_timings_ms or {}
    plan.node_timings_ms = {
        node: existing_timings.get(node, 0) + new_timings.get(node, 0)
        for node in set(existing_timings) | set(new_timings)
    }
    plan.audit_events = (plan.audit_events or []) + [
        event.model_dump(mode="json") for event in result.get("audit_events") or []
    ]
    plan.menu_version = (plan.menu_version or 0) + 1
    plan.menu_hash = hash_menu(draft)
    plan.nutrition_hash = hash_nutrition(nutrition)
    return result


@router.post("/{plan_id}/recompute", response_model=MealPlanOut)
def recompute_review_edit(
    plan_id: str,
    payload: RecomputeRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian")),
) -> MealPlanOut:
    plan = _get_pending_plan(db, plan_id)
    before = {"items": [{"id": item.id, "grams": item.grams} for item in plan.items], "version": plan.menu_version}
    _recompute_downstream(plan, payload.edits, db)
    after = {
        "items": [{"id": item.id, "grams": item.grams} for item in plan.items],
        "version": plan.menu_version,
        "highest_risk": plan.highest_risk,
    }
    db.add(AuditLog(at=datetime.now(UTC), actor_id=user.id, action="recompute_review_edit", before=before, after=after))
    db.commit()
    db.refresh(plan)
    return MealPlanOut.from_model(plan)


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
        _recompute_downstream(plan, payload.edits, db)

    if payload_has_p0(plan.violations, plan.highest_risk) or not plan.menu_hash or not plan.nutrition_hash:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Publish gate blocked: plan must have unchanged server-computed hashes and no P0 finding.",
        )
    if plan.highest_risk == "P1" and not (payload.notes or "").strip():
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "P1 findings require an explicit reviewer override reason.",
        )

    plan.status = "approved"
    plan.approved_menu_version = plan.menu_version
    plan.approved_menu_hash = plan.menu_hash
    plan.approved_nutrition_hash = plan.nutrition_hash
    plan.reviewer_id = user.id
    plan.reviewer_notes = payload.notes

    after = {"items": [{"id": i.id, "grams": i.grams} for i in plan.items], "status": plan.status}
    db.add(AuditLog(at=datetime.now(UTC), actor_id=user.id, action="approve", before=before, after=after))
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
    db.commit()
    db.refresh(plan)
    return MealPlanOut.from_model(plan)
