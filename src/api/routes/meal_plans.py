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
from sqlalchemy.orm import Session

from src.agents.assembly import build_nutricare_graph
from src.api.clinical_bridge import to_clinical_profile
from src.api.security import CurrentUser, get_current_user
from src.clinical.models import PatientProfile as ClinicalPatientProfile
from src.db.base import get_db, get_session_factory
from src.db.models import MealPlan, MealPlanItem
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


class MealPlanItemOut(BaseModel):
    id: str
    slot: str
    food_id: int
    grams: float


class MealPlanOut(BaseModel):
    id: str
    patient_id: str
    plan_date: date
    status: str
    items: list[MealPlanItemOut]
    targets: dict
    computed_nutrition: dict
    violations: list[dict]
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
                MealPlanItemOut(id=i.id, slot=i.slot, food_id=i.food_id, grams=i.grams)
                for i in sorted(plan.items, key=lambda i: (i.slot, i.food_id))
            ],
            targets=plan.targets or {},
            computed_nutrition=plan.computed_nutrition or {},
            violations=plan.violations or [],
            retry_count=plan.retry_count,
            reviewer_id=plan.reviewer_id,
            reviewer_notes=plan.reviewer_notes,
            created_at=plan.created_at,
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

        graph = build_nutricare_graph(profiles=_DbProfileRepository(session, clinical_profile))
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

        draft = result.get("draft_menu")
        if draft is not None:
            session.query(MealPlanItem).filter(MealPlanItem.plan_id == plan_id).delete()
            for slot, menu_items in draft.items.items():
                for menu_item in menu_items:
                    session.add(
                        MealPlanItem(plan_id=plan_id, slot=slot.value, food_id=menu_item.food_id, grams=menu_item.grams)
                    )
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
    query = db.query(MealPlan).filter(MealPlan.id == plan_id)
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
    query = db.query(MealPlan)
    if user.role == "patient":
        query = query.join(DbPatientProfile).filter(DbPatientProfile.user_id == user.id, MealPlan.status == "approved")
    elif patient_id is not None:
        query = query.filter(MealPlan.profile_id == patient_id)
    if plan_status is not None:
        query = query.filter(MealPlan.status == plan_status)

    total = query.count()
    rows = query.order_by(MealPlan.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return MealPlanListOut(items=[MealPlanOut.from_model(p) for p in rows], total=total, page=page, page_size=page_size)
