"""P2/AGT-12: thực đơn tương đương từ tủ lạnh + phạm vi thay thế duyệt trước (RULE-3).

LLM: NO — `solve_equivalent()` (src/agents/equivalent.py) là CP-SAT thuần.

Luồng: chuyên gia duyệt TRƯỚC một `SubstitutionScope` cho một thực đơn gốc đã
`approved` (chính sách, không phải từng bản riêng lẻ — DEC-018, DEVLOG.md §3).
Không có scope còn hiệu lực thì KHÔNG sinh được thực đơn tương đương, kể cả
bản nháp xem trước — chuyên gia luôn là chốt chặn đầu tiên trước khi tính
năng này hoạt động cho một bệnh nhân, không chỉ chốt chặn cho từng lần dùng.

Khi giải được: RULE-1 buộc tính lại `compute_nutrition`/`validate_menu` trên
server (không tin thẳng nội bộ solver). Tự phát hành (status=approved ngay,
không qua hàng chờ chuyên gia) CHỈ khi ĐỒNG THỜI — còn hạn, không vi phạm nào
(kể cả soft), không nguyên liệu nào `is_estimated`, chưa vượt
`max_auto_releases`. Trượt bất kỳ điều kiện nào → `pending_review`, vào đúng
hàng chờ duyệt hiện có (`/reviews`), KHÔNG có code path nào khác đưa thực đơn
chưa qua điều kiện trên tới bệnh nhân (RULE-3).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.agents.equivalent import (
    EQUIVALENT_TOLERANCE,
    MAX_AUTO_RELEASES,
    SUBSTITUTION_SCOPE_DAYS,
    resolve_staple_food_ids,
    solve_equivalent,
)
from src.agents.nodes.core import USDA_BULK_ID_THRESHOLD, VN_CURATED_SOURCES
from src.agents.optimizer import _eligible_dishes
from src.api.clinical_bridge import to_clinical_profile
from src.api.security import CurrentUser, get_current_user, require_role
from src.clinical.models import ClinicalTargets, NutritionSummary
from src.clinical.nutrition import compute_nutrition
from src.clinical.seeds import load_food_repository, load_vn_dishes
from src.clinical.validator import validate_menu
from src.db.base import get_db
from src.db.models import AuditLog, MealPlan, MealPlanItem, SubstitutionScope
from src.db.models import PantryItem as DbPantryItem
from src.db.models import PatientProfile as DbPatientProfile

router = APIRouter(tags=["equivalent-menu"])


class CreateScopeRequest(BaseModel):
    base_plan_id: str
    tolerance: float = Field(default=EQUIVALENT_TOLERANCE, gt=0, le=0.5)
    expires_in_days: int = Field(default=SUBSTITUTION_SCOPE_DAYS, gt=0, le=30)
    max_auto_releases: int = Field(default=MAX_AUTO_RELEASES, gt=0, le=50)


class ScopeOut(BaseModel):
    id: str
    profile_id: str
    base_plan_id: str
    tolerance: float
    max_auto_releases: int
    release_count: int
    expires_at: datetime
    revoked_at: datetime | None

    model_config = {"from_attributes": True}


@router.post("/substitution-scopes", response_model=ScopeOut, status_code=status.HTTP_201_CREATED)
def create_substitution_scope(
    payload: CreateScopeRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> SubstitutionScope:
    plan = db.get(MealPlan, payload.base_plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thực đơn gốc")
    if plan.status != "approved":
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ tạo được phạm vi thay thế cho thực đơn đã 'approved'")

    scope = SubstitutionScope(
        profile_id=plan.profile_id,
        base_plan_id=plan.id,
        approved_by=user.id,
        tolerance=payload.tolerance,
        max_auto_releases=payload.max_auto_releases,
        expires_at=datetime.utcnow() + timedelta(days=payload.expires_in_days),
    )
    db.add(scope)
    db.add(
        AuditLog(
            at=datetime.utcnow(),
            actor_id=user.id,
            action="substitution_scope_create",
            before=None,
            after={
                "base_plan_id": plan.id,
                "tolerance": payload.tolerance,
                "max_auto_releases": payload.max_auto_releases,
            },
        )
    )
    db.commit()
    db.refresh(scope)
    return scope


@router.post("/substitution-scopes/{scope_id}/revoke", response_model=ScopeOut)
def revoke_substitution_scope(
    scope_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> SubstitutionScope:
    scope = db.get(SubstitutionScope, scope_id)
    if scope is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phạm vi thay thế")
    scope.revoked_at = datetime.utcnow()
    db.add(
        AuditLog(
            at=datetime.utcnow(),
            actor_id=user.id,
            action="substitution_scope_revoke",
            before=None,
            after={"scope_id": scope_id},
        )
    )
    db.commit()
    db.refresh(scope)
    return scope


def _active_scope(db: Session, base_plan_id: str) -> SubstitutionScope | None:
    now = datetime.utcnow()
    return (
        db.query(SubstitutionScope)
        .filter(
            SubstitutionScope.base_plan_id == base_plan_id,
            SubstitutionScope.revoked_at.is_(None),
            SubstitutionScope.expires_at > now,
            SubstitutionScope.release_count < SubstitutionScope.max_auto_releases,
        )
        .order_by(SubstitutionScope.created_at.desc())
        .first()
    )


class EquivalentMenuRequest(BaseModel):
    plan_date: date


class EquivalentMenuResponse(BaseModel):
    released: bool
    plan_id: str | None = None
    plan_status: str | None = None
    reason_vi: str | None = None


@router.post(
    "/meal-plans/{base_plan_id}/equivalent", response_model=EquivalentMenuResponse, status_code=status.HTTP_201_CREATED
)
def generate_equivalent_menu(
    base_plan_id: str,
    payload: EquivalentMenuRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> EquivalentMenuResponse:
    plan = db.get(MealPlan, base_plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thực đơn gốc")
    profile = db.get(DbPatientProfile, plan.profile_id)
    if profile is None or (user.role == "patient" and profile.user_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thực đơn gốc")

    scope = _active_scope(db, base_plan_id)
    if scope is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Chưa có phạm vi thay thế nào còn hiệu lực cho thực đơn này — cần chuyên gia duyệt trước (RULE-3)",
        )

    clinical_profile = to_clinical_profile(profile)
    targets = ClinicalTargets.model_validate(plan.targets)
    base_nutrition = NutritionSummary.model_validate(plan.computed_nutrition)

    pantry_food_ids = {
        row.food_id
        for row in db.query(DbPantryItem).filter(DbPantryItem.profile_id == profile.id).all()
        if row.food_id is not None
    }

    foods = load_food_repository()
    pantry_food_ids |= resolve_staple_food_ids(foods)

    candidates = [
        f
        for f in foods.all()
        if (f.id < USDA_BULK_ID_THRESHOLD or f.source in VN_CURATED_SOURCES)
        and not any(a in clinical_profile.allergies for a in map(str.lower, f.contains_allergens))
        and f.name_vi.lower() not in clinical_profile.dislikes
    ]
    dishes = _eligible_dishes(load_vn_dishes(), foods, clinical_profile)

    result = solve_equivalent(
        base_nutrition, targets, pantry_food_ids, candidates, dishes, foods, tolerance=scope.tolerance
    )
    if result.draft is None:
        return EquivalentMenuResponse(released=False, reason_vi=result.reason_vi)

    # RULE-1: không tin thẳng nội bộ solver — tính lại từ food_id+grams.
    nutrition = compute_nutrition(result.draft, foods)
    violations = validate_menu(nutrition, targets)

    now = datetime.utcnow()
    scope_still_valid = (
        scope.expires_at > now and scope.revoked_at is None and scope.release_count < scope.max_auto_releases
    )
    auto_release = scope_still_valid and not violations and not nutrition.has_estimated

    new_plan = MealPlan(
        profile_id=profile.id,
        plan_date=payload.plan_date,
        status="approved" if auto_release else "pending_review",
        targets=plan.targets,
        computed_nutrition=nutrition.model_dump(mode="json"),
        violations=[v.model_dump(mode="json") for v in violations],
        reviewer_id=scope.approved_by if auto_release else None,
        reviewer_notes=(f"Tự động phát hành theo phạm vi thay thế {scope.id} (DEC-018)" if auto_release else None),
    )
    db.add(new_plan)
    db.flush()
    for slot, menu_items in result.draft.items.items():
        for menu_item in menu_items:
            db.add(MealPlanItem(plan_id=new_plan.id, slot=slot.value, food_id=menu_item.food_id, grams=menu_item.grams))

    if auto_release:
        scope.release_count += 1
    action = "equivalent_auto_release" if auto_release else "equivalent_pending_review"
    db.add(
        AuditLog(
            at=now,
            actor_id=user.id,
            action=action,
            before={"base_plan_id": base_plan_id, "scope_id": scope.id},
            after={"plan_id": new_plan.id, "status": new_plan.status},
        )
    )
    db.commit()
    return EquivalentMenuResponse(released=auto_release, plan_id=new_plan.id, plan_status=new_plan.status)
