"""BE-06: sinh thực đơn — chạy `build_nutricare_graph()` NỀN (background task),
trả 202 ngay, không để request treo (AC gốc: không quá 60s).

LLM: đây là route DUY NHẤT trong `src/api/` được phép kéo theo đường LLM
(qua HybridMenuGenerator) — nhưng chính route/handler này KHÔNG tự gọi LLM,
chỉ ráp graph rồi giao việc cho background task.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload

from src.agents.assembly import build_nutricare_graph
from src.api.clinical_bridge import to_clinical_profile
from src.api.security import CurrentUser, get_current_user
from src.clinical.dishes import load_dish_food_repository
from src.clinical.integrity import hash_menu, hash_nutrition, publish_gate_open
from src.clinical.models import PatientProfile as ClinicalPatientProfile
from src.clinical.seeds import load_food_repository
from src.config import get_settings
from src.db.base import get_db, get_session_factory
from src.db.models import Dish, DishIngredient, MealPlan, MealPlanItem
from src.db.models import PatientProfile as DbPatientProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])

_ACTIVE_STATUSES = ("drafting", "pending_review")


class MealPlanPreferences(BaseModel):
    dislikes: list[str] = Field(default_factory=list)


class CreateMealPlanRequest(BaseModel):
    patient_id: str
    plan_date: date
    preferences: MealPlanPreferences | None = None


class CreateMealPlanResponse(BaseModel):
    plan_id: str
    status: str


class MealPlanIngredientOut(BaseModel):
    food_id: int
    name_vi: str
    grams: float
    source: str
    source_ref: str


class MealPlanItemOut(BaseModel):
    id: str
    slot: str
    dish_id: str | None = None
    food_id: int | None = None
    grams: float
    name_vi: str
    source: str
    source_ref: str
    is_estimated: bool
    ingredients: list[MealPlanIngredientOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


def meal_plan_load_options():
    """Eager-load both new dish rows and legacy food rows."""
    return (
        selectinload(MealPlan.items).selectinload(MealPlanItem.food),
        selectinload(MealPlan.items)
        .selectinload(MealPlanItem.dish)
        .selectinload(Dish.ingredients)
        .selectinload(DishIngredient.food),
    )


class MealPlanOut(BaseModel):
    id: str
    patient_id: str
    plan_date: date
    status: str
    items: list[MealPlanItemOut]
    targets: dict
    computed_nutrition: dict | None
    violations: list[dict]
    safety_findings: list[dict]
    review_packet: dict
    citations: list[dict]
    explanation_vi: str | None
    highest_risk: str
    retry_count: int
    menu_version: int
    reviewer_id: str | None
    reviewer_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, plan: MealPlan) -> MealPlanOut:
        return cls(
            id=plan.id,
            patient_id=plan.profile_id,
            plan_date=plan.plan_date,
            status=plan.status,
            items=[
                cls._item_out(i) for i in sorted(plan.items, key=lambda i: (i.slot, i.dish_id or "", i.food_id or 0))
            ],
            targets=plan.targets or {},
            # An empty mapping means the graph stopped before nutrition was
            # computed (for example, at the fail-closed target gate).  Expose
            # that state as JSON null so clients cannot mistake it for a
            # complete ComputedNutrition payload.
            computed_nutrition=plan.computed_nutrition or None,
            violations=plan.violations or [],
            safety_findings=plan.safety_findings or [],
            review_packet=plan.review_packet or {},
            citations=plan.citations or [],
            explanation_vi=plan.explanation_vi,
            highest_risk=plan.highest_risk,
            retry_count=plan.retry_count,
            menu_version=plan.menu_version,
            reviewer_id=plan.reviewer_id,
            reviewer_notes=plan.reviewer_notes,
            created_at=plan.created_at,
        )

    @staticmethod
    def _item_out(item: MealPlanItem) -> MealPlanItemOut:
        if item.dish is not None:
            recipe_g = sum(part.grams for part in item.dish.ingredients) or item.dish.serving_g or item.grams
            scale = item.grams / recipe_g
            ingredients = [
                MealPlanIngredientOut(
                    food_id=part.food_id,
                    name_vi=part.food.name_vi,
                    grams=round(part.grams * scale, 1),
                    source=part.food.source,
                    source_ref=part.food.source_ref,
                )
                for part in item.dish.ingredients
            ]
            display_name = item.dish.name_vi
            if item.dish_id and item.dish_id.startswith("MENU-"):
                # Compatibility for plans generated before MENU-* aggregate
                # rows were removed from the optimizer candidate set.
                ingredient_names = [part.food.name_vi for part in item.dish.ingredients]
                display_name = " + ".join(ingredient_names[:3]) or "Món tổng hợp"
            return MealPlanItemOut(
                id=item.id,
                slot=item.slot,
                dish_id=item.dish_id,
                grams=item.grams,
                name_vi=display_name,
                source="recipe",
                source_ref=f"dish:{item.dish_id}",
                is_estimated=False,
                ingredients=ingredients,
            )
        assert item.food is not None
        return MealPlanItemOut(
            id=item.id,
            slot=item.slot,
            food_id=item.food_id,
            grams=item.grams,
            name_vi=item.food.name_vi,
            source=item.food.source,
            source_ref=item.food.source_ref,
            is_estimated=item.food.is_estimated,
        )


class MealPlanListOut(BaseModel):
    items: list[MealPlanOut]
    total: int
    page: int
    page_size: int


class _DbProfileRepository:
    """`ProfileRepository` Protocol (`src/agents/nodes/core.py`) đọc từ DB thật.

    Chỉ cần đúng 1 hồ sơ cho graph run này — không preload toàn bộ bảng.
    """

    def __init__(self, session: Session, clinical_profile: ClinicalPatientProfile) -> None:
        self._session = session
        self._profile = clinical_profile

    def get(self, patient_id: str) -> ClinicalPatientProfile | None:
        return self._profile if patient_id == self._profile.patient_id else None


def _run_graph_and_persist(
    plan_id: str,
    dislikes: list[str],
    session_factory: Callable[[], Session] | None = None,
) -> None:
    """Chạy graph thật trong threadpool (Starlette tự đưa hàm sync vào threadpool
    khi add qua `BackgroundTasks`) rồi ghi kết quả — mở SESSION RIÊNG vì session
    của request gốc đã đóng khi background task chạy.

    `session_factory` cho phép test trỏ vào DB tạm cùng engine với `client`
    fixture thay vì `DATABASE_URL` thật (mặc định `None` -> factory production)."""
    session = (session_factory or get_session_factory())()
    try:
        plan = session.get(MealPlan, plan_id)
        if plan is None:
            return
        profile_row = session.get(DbPatientProfile, plan.profile_id)
        if profile_row is None:
            plan.status = "failed"
            session.commit()
            return

        clinical_profile = to_clinical_profile(profile_row)
        if dislikes:
            clinical_profile = clinical_profile.model_copy(update={"dislikes": dislikes})

        # CP-SAT (và hybrid, dùng CP-SAT ở lượt đầu) có cơ chế "dish" RIÊNG
        # (DishCandidate + dish_chosen trong optimizer.py) — món hoàn chỉnh
        # được chọn NGUYÊN KHỐI rồi tự khai triển thành food_id+grams nguyên
        # liệu thô thật trong MenuDraft (RULE-1). Kho "food" tổng hợp theo
        # món (`load_dish_food_repository`, mỗi món = 1 "food" mật độ pha
        # loãng cả công thức) chỉ đúng cho generator chọn NGUYÊN món qua LLM
        # (`gemini` thuần). Trộn lẫn 2 kho — dùng kho món-tổng-hợp làm nguồn
        # "nguyên liệu thô" cho CP-SAT — khiến CP-SAT chọn lượng nhỏ của một
        # "food" có mật độ đã pha loãng như thể là nguyên liệu rời, ra thực
        # đơn thiếu năng lượng nghiêm trọng dù CP-SAT báo khả thi (phát hiện
        # audit 2026-08-07 khi merge PR#57 dish-day-cap với PR#59 dish-repo).
        dish_foods = load_dish_food_repository()
        raw_foods = load_food_repository()
        uses_raw_candidates = get_settings().menu_generator in ("cpsat", "hybrid")
        foods = raw_foods if uses_raw_candidates else dish_foods
        graph = build_nutricare_graph(profiles=_DbProfileRepository(session, clinical_profile), foods=foods)
        result = graph.invoke({"patient_id": clinical_profile.patient_id, "trace_id": plan_id})

        plan.status = result.get("status") or "failed"
        plan.run_id = result.get("run_id")
        plan.profile_snapshot_hash = result.get("profile_snapshot_hash")
        plan.profile_version = result.get("profile_version")
        plan.rule_version = result.get("rule_version")
        plan.food_data_version = result.get("food_data_version")
        plan.interaction_version = result.get("interaction_version")
        plan.prompt_version = result.get("prompt_version")
        plan.attempt_history = [attempt.model_dump(mode="json") for attempt in result.get("attempt_history") or []]
        plan.node_timings_ms = result.get("node_timings_ms") or {}
        token_usage = result.get("token_usage")
        plan.token_usage = token_usage.model_dump(mode="json") if token_usage is not None else {}
        last_error = result.get("last_error")
        plan.last_error = last_error.model_dump(mode="json") if last_error is not None else None
        plan.audit_events = [event.model_dump(mode="json") for event in result.get("audit_events") or []]
        plan.retry_count = result.get("retry_count") or 0
        targets = result.get("targets")
        if targets is not None:
            plan.targets = targets.model_dump(mode="json")
        nutrition = result.get("computed_nutrition")
        if nutrition is not None:
            plan.computed_nutrition = nutrition.model_dump(mode="json")
            plan.nutrition_hash = hash_nutrition(nutrition)
        else:
            plan.computed_nutrition = {}
            plan.nutrition_hash = None
        plan.violations = [v.model_dump(mode="json") for v in result.get("violations") or []]
        plan.safety_findings = [finding.model_dump(mode="json") for finding in result.get("safety_findings") or []]
        review_packet = result.get("review_packet")
        plan.review_packet = review_packet.model_dump(mode="json") if review_packet is not None else {}
        plan.citations = [citation.model_dump(mode="json") for citation in result.get("citations") or []]
        plan.explanation_vi = result.get("expert_explanation")
        plan.highest_risk = result.get("highest_risk") or "none"

        draft = result.get("draft_menu")
        if draft is not None:
            plan.menu_version = (plan.menu_version or 0) + 1
            plan.menu_hash = hash_menu(draft)
            session.query(MealPlanItem).filter(MealPlanItem.plan_id == plan_id).delete()
            for slot, menu_items in draft.items.items():
                for menu_item in menu_items:
                    # `dish_foods` chỉ khớp khi generator thật sự chọn NGUYÊN
                    # món qua kho món-tổng-hợp (gemini thuần); CP-SAT/hybrid
                    # trả food_id nguyên liệu thô thật (xem ghi chú ở trên) —
                    # KHÔNG cưỡng ép map dish, lưu thẳng food_id khi không map
                    # được thay vì raise (raise chỉ đúng khi foods=dish_foods).
                    dish = dish_foods.dish_for_food_id(menu_item.food_id) if not uses_raw_candidates else None
                    if dish is not None:
                        session.add(
                            MealPlanItem(plan_id=plan_id, slot=slot.value, dish_id=dish.dish_id, grams=menu_item.grams)
                        )
                    else:
                        session.add(
                            MealPlanItem(
                                plan_id=plan_id, slot=slot.value, food_id=menu_item.food_id, grams=menu_item.grams
                            )
                        )
        else:
            plan.menu_hash = None
        session.commit()
    except Exception:
        # Biên ngoài cùng của 1 background task fire-and-forget: không có request
        # nào đang chờ để propagate lỗi tới. Log đầy đủ + đánh dấu failed thay vì
        # để tiến trình chết lặng lẽ — đây LÀ cách "xử lý" ở biên này, không phải
        # nuốt lỗi (CLAUDE.md §4 cấm except trần khi có nơi xử lý cụ thể hơn; ở
        # đây không có).
        logger.exception("Sinh thực đơn thất bại cho plan_id=%s", plan_id)
        session.rollback()
        plan = session.get(MealPlan, plan_id)
        if plan is not None:
            plan.status = "failed"
            session.commit()
    finally:
        session.close()


def _get_visible_plan(db: Session, plan_id: str, user: CurrentUser) -> MealPlan:
    query = db.query(MealPlan).options(*meal_plan_load_options()).filter(MealPlan.id == plan_id)
    if user.role == "patient":
        query = _apply_patient_publish_gate(query.join(DbPatientProfile)).filter(DbPatientProfile.user_id == user.id)
    plan = query.first()
    if plan is None or (user.role == "patient" and not publish_gate_open(plan)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thực đơn")
    return plan


def _apply_patient_publish_gate(query):
    """SQL half of the publish gate; ``publish_gate_open`` is the defence-in-depth check."""
    return query.filter(
        MealPlan.status == "approved",
        MealPlan.highest_risk != "P0",
        MealPlan.menu_hash.is_not(None),
        MealPlan.nutrition_hash.is_not(None),
        MealPlan.menu_version == MealPlan.approved_menu_version,
        MealPlan.menu_hash == MealPlan.approved_menu_hash,
        MealPlan.nutrition_hash == MealPlan.approved_nutrition_hash,
    )


@router.post("", response_model=CreateMealPlanResponse, status_code=status.HTTP_202_ACCEPTED)
def request_meal_plan(
    payload: CreateMealPlanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> CreateMealPlanResponse:
    profile = db.get(DbPatientProfile, payload.patient_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")
    if user.role == "patient" and profile.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")

    existing = (
        db.query(MealPlan)
        .filter(
            MealPlan.profile_id == payload.patient_id,
            MealPlan.plan_date == payload.plan_date,
            MealPlan.status.in_(_ACTIVE_STATUSES),
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Đã có thực đơn đang xử lý/chờ duyệt cho ngày này")

    plan = MealPlan(profile_id=payload.patient_id, plan_date=payload.plan_date, status="drafting")
    db.add(plan)
    db.commit()
    db.refresh(plan)

    dislikes = payload.preferences.dislikes if payload.preferences else []
    # Trỏ background task vào CÙNG engine với session request này đang dùng —
    # tự động đúng cả khi test override `get_db` sang SQLite tạm, không cần
    # wiring riêng cho test.
    bind = db.get_bind()
    background_tasks.add_task(
        _run_graph_and_persist, plan.id, dislikes, lambda: Session(bind=bind, expire_on_commit=False)
    )

    return CreateMealPlanResponse(plan_id=plan.id, status=plan.status)


@router.get("/{plan_id}", response_model=MealPlanOut)
def get_meal_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> MealPlanOut:
    return MealPlanOut.from_model(_get_visible_plan(db, plan_id, user))


@router.get("", response_model=MealPlanListOut)
def list_meal_plans(
    patient_id: str | None = Query(default=None),
    plan_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> MealPlanListOut:
    query = db.query(MealPlan).options(*meal_plan_load_options())
    if user.role == "patient":
        query = _apply_patient_publish_gate(query.join(DbPatientProfile)).filter(DbPatientProfile.user_id == user.id)
    elif patient_id is not None:
        query = query.filter(MealPlan.profile_id == patient_id)
    if plan_status is not None:
        query = query.filter(MealPlan.status == plan_status)

    total = query.count()
    rows = query.order_by(MealPlan.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return MealPlanListOut(items=[MealPlanOut.from_model(p) for p in rows], total=total, page=page, page_size=page_size)
