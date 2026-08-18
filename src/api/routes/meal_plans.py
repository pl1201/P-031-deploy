"""BE-06: sinh thực đơn — chạy `build_nutricare_graph()` NỀN (background task),
trả 202 ngay, không để request treo (AC gốc: không quá 60s).

LLM: đây là route DUY NHẤT trong `src/api/` được phép kéo theo đường LLM
(qua HybridMenuGenerator) — nhưng chính route/handler này KHÔNG tự gọi LLM,
chỉ ráp graph rồi giao việc cho background task.
"""

from __future__ import annotations

import logging
import traceback
from collections.abc import Callable
from datetime import date, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload

from src.agents.assembly import build_nutricare_graph
from src.api.clinical_bridge import to_clinical_profile
from src.api.security import CurrentUser, get_current_user
from src.clinical.dish_roles import parse_roles
from src.clinical.dishes import load_dish_food_repository
from src.clinical.models import DishCandidate, MenuItem
from src.clinical.models import PatientProfile as ClinicalPatientProfile
from src.clinical.nutrition import InMemoryFoodRepository
from src.clinical.seeds import load_food_repository
from src.clinical.tiers import is_patient_facing_dish
from src.config import get_settings
from src.db.base import get_db, get_session_factory
from src.db.models import Dish, DishIngredient, MealPlan, MealPlanItem
from src.db.models import FoodItem as DbFoodItem
from src.db.models import PatientProfile as DbPatientProfile

if TYPE_CHECKING:  # chỉ dùng cho annotation — giữ nguyên import trễ ở runtime
    from src.agents.nodes.core import MenuGenerator

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
    computed_nutrition: dict
    violations: list[dict]
    safety_findings: list[dict]
    review_packet: dict
    citations: list[dict]
    explanation_vi: str | None
    highest_risk: str
    menu_version: int
    menu_hash_ready: bool
    nutrition_hash_ready: bool
    retry_count: int
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
                cls._item_out(i)
                for i in sorted(
                    plan.items, key=lambda i: (i.slot, 0 if i.dish_id else 1, i.dish_id or "", i.food_id or 0)
                )
            ],
            targets=plan.targets or {},
            computed_nutrition=plan.computed_nutrition or {},
            violations=plan.violations or [],
            safety_findings=plan.safety_findings or [],
            review_packet=plan.review_packet or {},
            citations=plan.citations or [],
            explanation_vi=plan.explanation_vi,
            highest_risk=plan.highest_risk or "none",
            menu_version=plan.menu_version or 0,
            menu_hash_ready=bool(plan.menu_hash),
            nutrition_hash_ready=bool(plan.nutrition_hash),
            retry_count=plan.retry_count,
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
            return MealPlanItemOut(
                id=item.id,
                slot=item.slot,
                dish_id=item.dish_id,
                grams=item.grams,
                name_vi=item.dish.name_vi,
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


def _load_db_dish_candidates(session: Session) -> list[DishCandidate]:
    """Build optimizer candidates from the same Dish rows the API later persists."""
    rows = session.query(Dish).options(selectinload(Dish.ingredients)).all()
    return [
        DishCandidate(
            dish_id=row.dish_id,
            name_vi=row.name_vi,
            region=row.region,
            roles=parse_roles(row.roles),
            verified_by=row.verified_by,
            is_reviewed=bool(row.verified_by and row.verified_by.lower() not in {"pending", "todo"}),
            ingredients=[MenuItem(food_id=part.food_id, grams=part.grams) for part in row.ingredients],
        )
        for row in rows
        if row.ingredients and is_patient_facing_dish(row.dish_id)
    ]


def _load_db_aligned_food_repository(session: Session) -> InMemoryFoodRepository:
    """Keep deterministic seed nutrition only for food IDs that exist in this DB.

    The CSV can be newer than a deployed database. Returning the unfiltered
    repository lets the optimizer select an ID that cannot satisfy the
    `meal_plan_items.food_id` foreign key during persistence.
    """
    db_ids = {food_id for (food_id,) in session.query(DbFoodItem.id).all()}
    seed_foods = load_food_repository()
    return InMemoryFoodRepository([food for food in seed_foods.all() if food.id in db_ids])


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
        raw_foods = _load_db_aligned_food_repository(session)
        generator_choice = get_settings().menu_generator
        # All patient-facing generator modes now use real Dish rows.  Gemini is
        # a structured dish selector, never an unconstrained synthetic-food
        # generator, so persistence and nutrition share one catalog.
        uses_raw_candidates = generator_choice in ("cpsat", "hybrid", "gemini")
        foods = raw_foods if uses_raw_candidates else dish_foods
        # Annotate theo Protocol `MenuGenerator`, không theo lớp cụ thể: nhánh
        # dưới gán cả `CPSATMenuOptimizer` lẫn `HybridMenuGenerator`. Thiếu
        # annotation thì mypy chốt kiểu từ lần gán đầu rồi báo lỗi ở lần thứ hai.
        generator: MenuGenerator | None = None
        if uses_raw_candidates:
            from src.agents.hybrid import HybridMenuGenerator
            from src.agents.optimizer import CPSATMenuOptimizer
            from src.services.gemini_dish_selector import GeminiDishMenuGenerator

            db_dishes = _load_db_dish_candidates(session)
            optimizer = CPSATMenuOptimizer(dishes=db_dishes, foods=raw_foods)
            if generator_choice == "cpsat":
                generator = optimizer
            else:
                # ``gemini`` is intentionally routed through the same safe
                # CP-SAT-first policy as ``hybrid``.  A direct LLM selection of
                # fixed recipe servings can be culturally plausible yet wildly
                # miss clinical targets; Gemini is only allowed after the
                # deterministic solver has no feasible/validated answer.
                generator = HybridMenuGenerator(
                    optimizer=optimizer,
                    llm_factory=lambda: GeminiDishMenuGenerator(dishes=db_dishes, foods=raw_foods),
                )
        graph = build_nutricare_graph(
            profiles=_DbProfileRepository(session, clinical_profile),
            foods=foods,
            generator=generator,
            # Use the same reviewed catalog for solver, persistence and the
            # final Vietnamese-meal-structure gate.
            dishes=db_dishes,
        )
        result = graph.invoke({"patient_id": clinical_profile.patient_id, "trace_id": plan_id})

        plan.status = result.get("status") or "failed"
        plan.retry_count = result.get("retry_count") or 0
        targets = result.get("targets")
        if targets is not None:
            plan.targets = targets.model_dump(mode="json")
        nutrition = result.get("computed_nutrition")
        if nutrition is not None:
            plan.computed_nutrition = nutrition.model_dump(mode="json")
        plan.violations = [v.model_dump(mode="json") for v in result.get("violations") or []]
        plan.safety_findings = [v.model_dump(mode="json") for v in result.get("safety_findings") or []]
        packet = result.get("review_packet")
        plan.review_packet = packet.model_dump(mode="json") if packet is not None else {}
        plan.citations = [
            v.model_dump(mode="json") if hasattr(v, "model_dump") else v for v in result.get("citations") or []
        ]
        plan.explanation_vi = result.get("explanation_vi")
        plan.highest_risk = result.get("highest_risk") or "none"
        plan.menu_version = result.get("menu_version") or 0
        plan.menu_hash = result.get("menu_hash")
        plan.nutrition_hash = result.get("nutrition_hash")

        draft = result.get("draft_menu")
        if draft is not None:
            if uses_raw_candidates and not draft.planned_dishes:
                raise ValueError("Generator did not select any database dish; refusing ingredient-only patient draft")
            session.query(MealPlanItem).filter(MealPlanItem.plan_id == plan_id).delete()
            for slot, menu_items in draft.items.items():
                residual_grams = {menu_item.food_id: menu_item.grams for menu_item in menu_items}
                planned_dishes = draft.planned_dishes.get(slot, [])
                for planned_dish in planned_dishes:
                    dish_row = session.get(Dish, planned_dish.dish_id)
                    if dish_row is None:
                        raise ValueError(f"Không tìm thấy món đã chọn: {planned_dish.dish_id}")
                    recipe_grams = sum(part.grams for part in dish_row.ingredients)
                    if recipe_grams <= 0:
                        raise ValueError(f"Món không có định lượng công thức: {planned_dish.dish_id}")
                    session.add(
                        MealPlanItem(
                            plan_id=plan_id,
                            slot=slot.value,
                            dish_id=planned_dish.dish_id,
                            grams=planned_dish.serving_grams,
                        )
                    )
                    scale = planned_dish.serving_grams / recipe_grams
                    for part in dish_row.ingredients:
                        residual_grams[part.food_id] = residual_grams.get(part.food_id, 0.0) - part.grams * scale

                # CP-SAT vẫn có thể dùng một lượng thực phẩm bổ sung ngoài món
                # để đạt target. Chỉ lưu phần dư thật; nguyên liệu thuộc món đã
                # được biểu diễn bởi dish_id và không xuất hiện thành dòng UI.
                if planned_dishes:
                    for food_id, grams in residual_grams.items():
                        if grams > 0.1:
                            session.add(
                                MealPlanItem(plan_id=plan_id, slot=slot.value, food_id=food_id, grams=round(grams, 1))
                            )
                    continue
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
        session.commit()
    except Exception as exc:
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
            # Ghi luôn nguyên nhân vào `last_error`. Trước đây cột này tồn tại
            # trong schema nhưng KHÔNG BAO GIỜ được ghi, nên một `status=failed`
            # do crash và một `failed` do hết đường sinh thực đơn nhìn giống hệt
            # nhau từ DB lẫn từ UI — UI chỉ hiện "Không thể tạo phương án an
            # toàn với cấu hình này", đọc như kết luận lâm sàng chứ không phải
            # sự cố kỹ thuật. Hệ quả đo được: 43 plan `failed` trong DB dùng
            # chung mà không truy được một dòng nguyên nhân nào, phải suy ngược
            # từ log Render (đã xoay vòng mất) — xem docs/SET-05.
            #
            # Chỉ lưu loại lỗi + thông điệp + đuôi traceback: đủ để chẩn đoán,
            # không kèm hồ sơ bệnh nhân. Cột này chỉ chuyên gia/R1 đọc, KHÔNG
            # hiển thị cho bệnh nhân và KHÔNG đưa vào prompt LLM.
            plan.last_error = {
                "type": type(exc).__name__,
                "message": str(exc)[:2000],
                "traceback": "".join(traceback.format_exc()).strip()[-4000:],
            }
            session.commit()
    finally:
        session.close()


def _get_visible_plan(db: Session, plan_id: str, user: CurrentUser) -> MealPlan:
    query = db.query(MealPlan).options(*meal_plan_load_options()).filter(MealPlan.id == plan_id)
    if user.role == "patient":
        query = query.join(DbPatientProfile).filter(DbPatientProfile.user_id == user.id, MealPlan.status == "approved")
    plan = query.first()
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thực đơn")
    return plan


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
        query = query.join(DbPatientProfile).filter(DbPatientProfile.user_id == user.id, MealPlan.status == "approved")
    elif patient_id is not None:
        query = query.filter(MealPlan.profile_id == patient_id)
    if plan_status is not None:
        query = query.filter(MealPlan.status == plan_status)

    total = query.count()
    rows = query.order_by(MealPlan.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return MealPlanListOut(items=[MealPlanOut.from_model(p) for p in rows], total=total, page=page, page_size=page_size)
