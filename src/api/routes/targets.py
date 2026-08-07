"""BE-04: tính định mức lâm sàng — bọc `compute_targets()`, KHÔNG gọi LLM.

LLM: NO.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.clinical_bridge import to_clinical_profile
from src.api.security import CurrentUser, get_current_user
from src.clinical.rules import compute_targets
from src.db.base import get_db
from src.db.models import PatientProfile as DbPatientProfile

router = APIRouter(prefix="/targets", tags=["targets"])


class ComputeTargetsRequest(BaseModel):
    patient_id: str


class NutrientTargetOut(BaseModel):
    nutrient: str
    min_value: float | None
    max_value: float | None
    unit: str
    rule_ids: list[str]
    guideline_refs: list[str]


class ComputeTargetsResponse(BaseModel):
    patient_id: str
    bmr_kcal: float
    tdee_kcal: float
    targets: dict[str, NutrientTargetOut]
    applied_rule_ids: list[str]
    needs_expert_review: bool
    conflict_notes: list[str]


@router.post("/compute", response_model=ComputeTargetsResponse)
def compute_targets_route(
    payload: ComputeTargetsRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ComputeTargetsResponse:
    profile = db.get(DbPatientProfile, payload.patient_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")
    if user.role == "patient" and profile.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")

    result = compute_targets(to_clinical_profile(profile))

    return ComputeTargetsResponse(
        patient_id=payload.patient_id,
        bmr_kcal=result.bmr_kcal,
        tdee_kcal=result.tdee_kcal,
        targets={
            k: NutrientTargetOut(
                nutrient=v.nutrient,
                min_value=v.min_value,
                max_value=v.max_value,
                unit=v.unit,
                rule_ids=v.rule_ids,
                guideline_refs=v.guideline_refs,
            )
            for k, v in result.targets.items()
        },
        applied_rule_ids=result.applied_rule_ids,
        needs_expert_review=result.needs_expert_review,
        conflict_notes=result.conflict_notes,
    )
