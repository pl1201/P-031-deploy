"""BE-03: CRUD hồ sơ bệnh nhân.

LLM: NO.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.security import CurrentUser, get_current_user, require_role
from src.db.base import get_db
from src.db.models import PatientAllergy, PatientMedication, PatientProfile, User

router = APIRouter(prefix="/patients", tags=["patients"])


class ConditionIn(BaseModel):
    code: str
    stage: str | None = None


class PatientProfileCreate(BaseModel):
    user_id: str
    age: int = Field(ge=1, le=120)
    sex: Literal["male", "female"]
    height_cm: float = Field(ge=80, le=250)
    weight_kg: float = Field(ge=20, le=300)
    # 4 mức "loại lao động" đúng nhãn chuyên gia dinh dưỡng dự án dùng thật
    # (Bảng 2, `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx`) — khớp
    # `src.clinical.models.ActivityLevel`.
    activity_level: Literal["light", "moderate", "heavy", "very_heavy"] = "light"
    conditions: list[ConditionIn] = Field(default_factory=list)
    lab_values: dict[str, float] = Field(default_factory=dict)
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    region: Literal["north", "central", "south"] | None = None


class PatientProfileUpdate(BaseModel):
    age: int | None = Field(default=None, ge=1, le=120)
    sex: Literal["male", "female"] | None = None
    height_cm: float | None = Field(default=None, ge=80, le=250)
    weight_kg: float | None = Field(default=None, ge=20, le=300)
    activity_level: Literal["light", "moderate", "heavy", "very_heavy"] | None = None
    conditions: list[ConditionIn] | None = None
    lab_values: dict[str, float] | None = None
    allergies: list[str] | None = None
    medications: list[str] | None = None
    region: Literal["north", "central", "south"] | None = None


class PatientProfileOut(BaseModel):
    id: str
    user_id: str
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    activity_level: str
    conditions: list[dict]
    lab_values: dict
    allergies: list[str]
    medications: list[str]
    region: str | None

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, profile: PatientProfile) -> PatientProfileOut:
        return cls(
            id=profile.id,
            user_id=profile.user_id,
            age=profile.age,
            sex=profile.sex,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            activity_level=profile.activity_level,
            conditions=profile.conditions or [],
            lab_values=profile.lab_values or {},
            allergies=[a.allergen for a in profile.allergies],
            medications=[m.drug_name for m in profile.medications],
            region=profile.region,
        )


class PatientListOut(BaseModel):
    items: list[PatientProfileOut]
    total: int
    page: int
    page_size: int


def _sync_allergies_and_medications(
    db: Session, profile: PatientProfile, allergies: list[str], medications: list[str]
) -> None:
    db.query(PatientAllergy).filter(PatientAllergy.profile_id == profile.id).delete()
    db.query(PatientMedication).filter(PatientMedication.profile_id == profile.id).delete()
    for allergen in allergies:
        db.add(PatientAllergy(profile_id=profile.id, allergen=allergen))
    for drug_name in medications:
        db.add(PatientMedication(profile_id=profile.id, drug_name=drug_name))


def _get_owned_profile(db: Session, profile_id: str, user: CurrentUser) -> PatientProfile:
    """404 (không phải 403) khi hồ sơ không tồn tại HOẶC thuộc user khác — chống rò rỉ (BE-09)."""
    query = db.query(PatientProfile).filter(PatientProfile.id == profile_id)
    if user.role == "patient":
        query = query.filter(PatientProfile.user_id == user.id)
    profile = query.first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ")
    return profile


@router.post("", response_model=PatientProfileOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientProfileCreate,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> PatientProfileOut:
    target_user = db.get(User, payload.user_id)
    if target_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user_id không tồn tại")
    if target_user.role != "patient":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "user_id phải có role=patient")
    if target_user.profile is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "User này đã có hồ sơ bệnh nhân")

    profile = PatientProfile(
        user_id=payload.user_id,
        age=payload.age,
        sex=payload.sex,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        activity_level=payload.activity_level,
        conditions=[c.model_dump() for c in payload.conditions],
        lab_values=payload.lab_values,
        region=payload.region,
    )
    db.add(profile)
    db.flush()  # cần profile.id trước khi tạo allergy/medication con
    _sync_allergies_and_medications(db, profile, payload.allergies, payload.medications)
    db.commit()
    db.refresh(profile)
    return PatientProfileOut.from_model(profile)


# ⚠️ Phải khai báo TRƯỚC `/{profile_id}` — FastAPI khớp theo thứ tự khai báo,
# đặt sau thì "me" bị hiểu là một profile_id và luôn trả 404.
@router.get("/me", response_model=PatientProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> PatientProfileOut:
    """Hồ sơ của chính người đang đăng nhập.

    Cần cho mọi màn hình bệnh nhân: session chỉ có `user_id`, trong khi các API
    dinh dưỡng đều khoá theo `profile_id`. Không có endpoint này thì bệnh nhân
    không có cách nào biết `profile_id` của mình (`GET /patients` yêu cầu quyền
    dietitian) — tức là không ghi được nhật ký.
    """
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bạn chưa có hồ sơ bệnh nhân")
    return PatientProfileOut.from_model(profile)


@router.get("/{profile_id}", response_model=PatientProfileOut)
def get_patient(
    profile_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> PatientProfileOut:
    profile = _get_owned_profile(db, profile_id, user)
    return PatientProfileOut.from_model(profile)


@router.put("/{profile_id}", response_model=PatientProfileOut)
def update_patient(
    profile_id: str,
    payload: PatientProfileUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> PatientProfileOut:
    profile = _get_owned_profile(db, profile_id, user)

    updates = payload.model_dump(exclude_unset=True)
    if "conditions" in updates:
        profile.conditions = [c.model_dump() if hasattr(c, "model_dump") else c for c in payload.conditions or []]
        del updates["conditions"]
    allergies = updates.pop("allergies", None)
    medications = updates.pop("medications", None)
    for field, value in updates.items():
        setattr(profile, field, value)
    if allergies is not None or medications is not None:
        _sync_allergies_and_medications(
            db,
            profile,
            allergies if allergies is not None else [a.allergen for a in profile.allergies],
            medications if medications is not None else [m.drug_name for m in profile.medications],
        )
    db.commit()
    db.refresh(profile)
    return PatientProfileOut.from_model(profile)


@router.get("", response_model=PatientListOut)
def list_patients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> PatientListOut:
    query = db.query(PatientProfile)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PatientListOut(
        items=[PatientProfileOut.from_model(p) for p in items], total=total, page=page, page_size=page_size
    )
