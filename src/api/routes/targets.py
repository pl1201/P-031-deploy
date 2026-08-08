"""BE-04: tính định mức lâm sàng — bọc `compute_targets()`, KHÔNG gọi LLM.

LLM: NO.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.clinical_bridge import to_clinical_profile
from src.api.security import CurrentUser, get_current_user, require_role
from src.clinical.rules import compute_targets, load_rules
from src.clinical.target_explainer import diff_explanations, explain_targets
from src.db.base import get_db
from src.db.models import AuditLog
from src.db.models import PatientProfile as DbPatientProfile
from src.services.target_assistant import apply_delta, parse_what_if

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


# ---------------------------------------------------------------------------
# P1 — Trợ lý ngưỡng cho chuyên gia (trả lời "vì sao ngưỡng này")
#
# LLM: NO cho /explain (thuần lắp ráp lại dữ kiện đã có, xem target_explainer.py).
# `explain_naturally()` (LLM: YES, target_assistant.py) CHƯA nối vào route này —
# route trả structured facts, để FE tự chọn hiện raw hay gọi thêm bước diễn đạt
# tự nhiên riêng nếu cần (tránh mỗi lần xem ngưỡng đều tốn 1 lượt Gemini).
#
# Chỉ role dietitian/admin — bệnh nhân không cần "vì sao", chỉ cần con số đã
# duyệt (RULE-3), và đây không phải chat tự do nên không qua guard_free_text().
# ---------------------------------------------------------------------------
class AppliedRuleOut(BaseModel):
    rule_id: str
    guideline_ref: str
    guideline_grade: str
    bound: str
    resolved_value: float
    unit: str


class ExcludedRuleOut(BaseModel):
    rule_id: str
    guideline_ref: str
    reason: str


class NutrientExplanationOut(BaseModel):
    nutrient: str
    label_vi: str
    min_value: float | None
    max_value: float | None
    unit: str | None
    applied: list[AppliedRuleOut]
    excluded: list[ExcludedRuleOut]
    conflict_notes: list[str]


@router.get("/{patient_id}/explain", response_model=list[NutrientExplanationOut])
def explain_targets_route(
    patient_id: str,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> list[NutrientExplanationOut]:
    profile_row = db.get(DbPatientProfile, patient_id)
    if profile_row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")

    profile = to_clinical_profile(profile_row)
    rules = load_rules()
    targets = compute_targets(profile, rules)
    explanations = explain_targets(profile, targets, rules)

    return [
        NutrientExplanationOut(
            nutrient=e.nutrient,
            label_vi=e.label_vi,
            min_value=e.min_value,
            max_value=e.max_value,
            unit=e.unit,
            applied=[AppliedRuleOut(**a.model_dump()) for a in e.applied],
            excluded=[ExcludedRuleOut(**x.model_dump()) for x in e.excluded],
            conflict_notes=e.conflict_notes,
        )
        for e in explanations
    ]


class WhatIfRequest(BaseModel):
    question_vi: str


class WhatIfResponse(BaseModel):
    delta: dict
    explanations_before: list[NutrientExplanationOut]
    explanations_after: list[NutrientExplanationOut]
    changed_nutrients: list[str]


@router.post("/{patient_id}/what-if", response_model=WhatIfResponse)
def what_if_targets_route(
    patient_id: str,
    payload: WhatIfRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> WhatIfResponse:
    """"Nếu CKD sang G4 thì ngưỡng đổi thế nào?" — không sửa gì trong DB.

    LLM (target_assistant.parse_what_if) chỉ trả về `ProfileDelta` — không có
    field số nào (xem docstring `ProfileDelta`). Ngưỡng luôn tính LẠI bằng
    `compute_targets()` trên bản sao hồ sơ, không bao giờ do LLM sinh ra.
    """
    profile_row = db.get(DbPatientProfile, patient_id)
    if profile_row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")

    profile = to_clinical_profile(profile_row)
    rules = load_rules()

    targets_before = compute_targets(profile, rules)
    explanations_before = explain_targets(profile, targets_before, rules)

    delta = parse_what_if(payload.question_vi)
    profile_after = apply_delta(profile, delta)
    targets_after = compute_targets(profile_after, rules)
    explanations_after = explain_targets(profile_after, targets_after, rules)

    diffs = diff_explanations(explanations_before, explanations_after)

    db.add(
        AuditLog(
            at=datetime.now(UTC),
            actor_id=user.id,
            action="targets_what_if",
            before={"patient_id": patient_id, "question_vi": payload.question_vi},
            after={"delta": delta.model_dump(mode="json")},
        )
    )
    db.commit()

    def _to_out(explanations):
        return [
            NutrientExplanationOut(
                nutrient=e.nutrient,
                label_vi=e.label_vi,
                min_value=e.min_value,
                max_value=e.max_value,
                unit=e.unit,
                applied=[AppliedRuleOut(**a.model_dump()) for a in e.applied],
                excluded=[ExcludedRuleOut(**x.model_dump()) for x in e.excluded],
                conflict_notes=e.conflict_notes,
            )
            for e in explanations
        ]

    return WhatIfResponse(
        delta=delta.model_dump(mode="json"),
        explanations_before=_to_out(explanations_before),
        explanations_after=_to_out(explanations_after),
        changed_nutrients=[d.nutrient for d in diffs if d.changed],
    )
