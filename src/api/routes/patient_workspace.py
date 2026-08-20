"""Patient-centric workspace: overview, observations, notes, and review history.

LLM: NO. Các endpoint chỉ đọc/ghi dữ liệu nghiệp vụ đã được xác thực.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.routes.patients import PatientProfileOut, _get_owned_profile
from src.api.security import CurrentUser, get_current_user, require_role
from src.db.base import get_db
from src.db.models import (
    ClinicalNote,
    MealPlan,
    MealPlanReviewEvent,
    PatientObservation,
    PatientPreferences,
    PatientProfile,
)

router = APIRouter(prefix="/patients", tags=["patient-workspace"])


def _get_my_profile(db: Session, user: CurrentUser) -> PatientProfile:
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bạn chưa có hồ sơ bệnh nhân")
    return profile


class ObservationCreate(BaseModel):
    observation_type: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9_]+$")
    value: float
    unit: str = Field(min_length=1, max_length=30)
    measured_at: datetime
    source: Literal["manual", "device", "lab", "imported"] = "manual"
    note: str | None = Field(default=None, max_length=1000)


class ObservationOut(BaseModel):
    id: str
    profile_id: str
    observation_type: str
    value: float
    unit: str
    measured_at: datetime
    source: str
    recorded_by: str
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClinicalNoteCreate(BaseModel):
    note_type: Literal["assessment", "follow_up", "goal", "care_plan"] = "follow_up"
    content: str = Field(min_length=1, max_length=10000)
    visibility: Literal["internal", "care_team", "patient_visible"] = "care_team"


class ClinicalNoteOut(BaseModel):
    id: str
    profile_id: str
    author_id: str
    note_type: str
    content: str
    visibility: str
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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


class MealPlanSummary(BaseModel):
    total: int
    approved: int
    pending_review: int
    rejected: int
    latest_plan_id: str | None
    latest_plan_date: str | None
    latest_status: str | None


class PatientOverviewOut(BaseModel):
    patient: PatientProfileOut
    latest_observations: dict[str, ObservationOut]
    meal_plans: MealPlanSummary
    last_review: ReviewEventOut | None
    notes_count: int


@router.get("/{profile_id}/overview", response_model=PatientOverviewOut)
def get_patient_overview(
    profile_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> PatientOverviewOut:
    profile = _get_owned_profile(db, profile_id, user)
    observation_rows = (
        db.query(PatientObservation)
        .filter(PatientObservation.profile_id == profile_id)
        .order_by(PatientObservation.measured_at.desc())
        .all()
    )
    latest_observations: dict[str, ObservationOut] = {}
    for row in observation_rows:
        latest_observations.setdefault(row.observation_type, ObservationOut.model_validate(row))

    status_counts: dict[str, int] = dict(
        db.query(MealPlan.status, func.count(MealPlan.id))
        .filter(MealPlan.profile_id == profile_id)
        .group_by(MealPlan.status)
        .all()  # type: ignore[arg-type]
    )
    latest_plan = (
        db.query(MealPlan).filter(MealPlan.profile_id == profile_id).order_by(MealPlan.created_at.desc()).first()
    )
    last_review = (
        db.query(MealPlanReviewEvent)
        .filter(MealPlanReviewEvent.profile_id == profile_id)
        .order_by(MealPlanReviewEvent.created_at.desc())
        .first()
    )
    notes_query = db.query(ClinicalNote).filter(ClinicalNote.profile_id == profile_id)
    if user.role == "patient":
        notes_query = notes_query.filter(ClinicalNote.visibility == "patient_visible")

    return PatientOverviewOut(
        patient=PatientProfileOut.from_model(profile),
        latest_observations=latest_observations,
        meal_plans=MealPlanSummary(
            total=sum(status_counts.values()),
            approved=status_counts.get("approved", 0),
            pending_review=status_counts.get("pending_review", 0),
            rejected=status_counts.get("rejected", 0),
            latest_plan_id=latest_plan.id if latest_plan else None,
            latest_plan_date=latest_plan.plan_date.isoformat() if latest_plan else None,
            latest_status=latest_plan.status if latest_plan else None,
        ),
        last_review=ReviewEventOut.model_validate(last_review) if last_review else None,
        notes_count=notes_query.count(),
    )


class SelfWeightObservationCreate(BaseModel):
    """Cân nặng bệnh nhân tự ghi — KHÔNG dùng field `observation_type`/`source` tuỳ ý
    như route dietitian-only ở dưới: chặn cứng loại = "weight", nguồn =
    "patient_reported" để tách biệt với số đo do chuyên gia ghi nhận (RULE-3: hồ sơ
    lâm sàng gốc `patient_profiles.weight_kg` vẫn chỉ chuyên gia sửa được)."""

    value: float = Field(ge=20, le=300)
    measured_at: datetime = Field(default_factory=datetime.utcnow)
    note: str | None = Field(default=None, max_length=1000)


@router.get("/me/observations", response_model=list[ObservationOut])
def list_my_observations(
    observation_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("patient")),
) -> list[PatientObservation]:
    profile = _get_my_profile(db, user)
    query = db.query(PatientObservation).filter(PatientObservation.profile_id == profile.id)
    if observation_type:
        query = query.filter(PatientObservation.observation_type == observation_type)
    return query.order_by(PatientObservation.measured_at.desc()).limit(limit).all()


@router.post("/me/observations", response_model=ObservationOut, status_code=status.HTTP_201_CREATED)
def create_my_weight_observation(
    payload: SelfWeightObservationCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("patient")),
) -> PatientObservation:
    profile = _get_my_profile(db, user)
    observation = PatientObservation(
        profile_id=profile.id,
        observation_type="weight",
        value=payload.value,
        unit="kg",
        measured_at=payload.measured_at,
        source="patient_reported",
        recorded_by=user.id,
        note=payload.note,
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


class PreferencesIn(BaseModel):
    disliked_foods: list[str] = Field(default_factory=list)
    usual_meal_times: dict[str, str] = Field(default_factory=dict)
    meal_reminders_enabled: bool = True


class PreferencesOut(PreferencesIn):
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("/me/preferences", response_model=PreferencesOut)
def get_my_preferences(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("patient")),
) -> PatientPreferences:
    profile = _get_my_profile(db, user)
    prefs = db.query(PatientPreferences).filter(PatientPreferences.profile_id == profile.id).first()
    if prefs is None:
        prefs = PatientPreferences(profile_id=profile.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.put("/me/preferences", response_model=PreferencesOut)
def update_my_preferences(
    payload: PreferencesIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("patient")),
) -> PatientPreferences:
    profile = _get_my_profile(db, user)
    prefs = db.query(PatientPreferences).filter(PatientPreferences.profile_id == profile.id).first()
    if prefs is None:
        prefs = PatientPreferences(profile_id=profile.id)
        db.add(prefs)
    prefs.disliked_foods = payload.disliked_foods
    prefs.usual_meal_times = payload.usual_meal_times
    prefs.meal_reminders_enabled = payload.meal_reminders_enabled
    prefs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs


@router.get("/{profile_id}/observations", response_model=list[ObservationOut])
def list_observations(
    profile_id: str,
    observation_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[PatientObservation]:
    _get_owned_profile(db, profile_id, user)
    query = db.query(PatientObservation).filter(PatientObservation.profile_id == profile_id)
    if observation_type:
        query = query.filter(PatientObservation.observation_type == observation_type)
    return query.order_by(PatientObservation.measured_at.desc()).limit(limit).all()


@router.post("/{profile_id}/observations", response_model=ObservationOut, status_code=status.HTTP_201_CREATED)
def create_observation(
    profile_id: str,
    payload: ObservationCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> PatientObservation:
    _get_owned_profile(db, profile_id, user)
    observation = PatientObservation(profile_id=profile_id, recorded_by=user.id, **payload.model_dump())
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


@router.get("/{profile_id}/notes", response_model=list[ClinicalNoteOut])
def list_clinical_notes(
    profile_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[ClinicalNote]:
    _get_owned_profile(db, profile_id, user)
    query = db.query(ClinicalNote).filter(ClinicalNote.profile_id == profile_id)
    if user.role == "patient":
        query = query.filter(ClinicalNote.visibility == "patient_visible")
    return query.order_by(ClinicalNote.created_at.desc()).all()


@router.post("/{profile_id}/notes", response_model=ClinicalNoteOut, status_code=status.HTTP_201_CREATED)
def create_clinical_note(
    profile_id: str,
    payload: ClinicalNoteCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> ClinicalNote:
    _get_owned_profile(db, profile_id, user)
    now = datetime.utcnow()
    note = ClinicalNote(
        profile_id=profile_id, author_id=user.id, created_at=now, updated_at=now, **payload.model_dump()
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{profile_id}/review-events", response_model=list[ReviewEventOut])
def list_patient_review_events(
    profile_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> list[MealPlanReviewEvent]:
    _get_owned_profile(db, profile_id, user)
    return (
        db.query(MealPlanReviewEvent)
        .filter(MealPlanReviewEvent.profile_id == profile_id)
        .order_by(MealPlanReviewEvent.created_at.desc())
        .limit(limit)
        .all()
    )
