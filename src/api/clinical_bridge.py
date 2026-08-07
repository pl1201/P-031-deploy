"""Chuyển đổi ORM (`src/db/models.py`) <-> Pydantic model của tầng lâm sàng
(`src/clinical/models.py`) — dùng chung cho `targets.py` và `meal_plans.py`.

LLM: NO.
"""

from __future__ import annotations

from typing import Literal, cast

from src.clinical.models import ActivityLevel, Condition, Sex
from src.clinical.models import PatientProfile as ClinicalPatientProfile
from src.db.models import PatientProfile as DbPatientProfile


def to_clinical_profile(db_profile: DbPatientProfile) -> ClinicalPatientProfile:
    """`compute_targets()`/`build_graph()` (RULE-1, thuần Python) chỉ nhận Pydantic model này."""
    conditions = [Condition(code=c["code"], stage=c.get("stage")) for c in (db_profile.conditions or [])]
    return ClinicalPatientProfile(
        patient_id=db_profile.id,
        age=db_profile.age,
        sex=Sex(db_profile.sex),
        height_cm=db_profile.height_cm,
        weight_kg=db_profile.weight_kg,
        activity_level=ActivityLevel(db_profile.activity_level),
        conditions=conditions,
        allergies=[a.allergen for a in db_profile.allergies],
        medications=[m.drug_name for m in db_profile.medications],
        # region đã được validate là Literal["north","central","south"]|None ở
        # PatientProfileCreate/Update (BE-03) trước khi ghi DB — cột ORM chỉ khai
        # String(10) nên mypy không tự suy ra được.
        region=cast("Literal['north', 'central', 'south'] | None", db_profile.region),
    )
