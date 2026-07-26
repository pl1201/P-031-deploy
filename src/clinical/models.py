"""Domain models cho tầng lâm sàng.

LLM: NO — module này thuần dữ liệu, không import bất kỳ LLM client nào.
Ticket: CLN-01..CLN-05
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(StrEnum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"


ACTIVITY_FACTOR: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
}


class WeightGoal(StrEnum):
    LOSE = "lose"
    MAINTAIN = "maintain"
    GAIN = "gain"


class ConditionCode(StrEnum):
    """Mã bệnh lý hệ thống hỗ trợ ở v1."""

    T2DM = "T2DM"  # Đái tháo đường týp 2
    HTN = "HTN"  # Tăng huyết áp / tim mạch
    CKD = "CKD"  # Bệnh thận mạn
    GOUT = "GOUT"  # Gout / tăng acid uric


class Condition(BaseModel):
    code: ConditionCode
    stage: str | None = Field(
        default=None,
        description="Giai đoạn, ví dụ CKD: G1..G5. None nếu bệnh không phân giai đoạn.",
    )


class PatientProfile(BaseModel):
    """Hồ sơ bệnh nhân — KHÔNG chứa thông tin định danh (xem RULE R10.9)."""

    patient_id: str
    age: int = Field(ge=1, le=120)
    sex: Sex
    height_cm: float = Field(ge=80, le=250)
    weight_kg: float = Field(ge=20, le=300)
    activity_level: ActivityLevel = ActivityLevel.SEDENTARY
    weight_goal: WeightGoal = WeightGoal.MAINTAIN
    conditions: list[Condition] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    region: Literal["north", "central", "south"] | None = None
    dislikes: list[str] = Field(default_factory=list)

    @property
    def bmi(self) -> float:
        return self.weight_kg / (self.height_cm / 100) ** 2

    @field_validator("allergies", "medications", "dislikes", mode="after")
    @classmethod
    def _normalize(cls, v: list[str]) -> list[str]:
        return [s.strip().lower() for s in v if s.strip()]


class NutrientTarget(BaseModel):
    """Một định mức cho một chất, kèm dấu vết nguồn gốc."""

    nutrient: str
    min_value: float | None = None
    max_value: float | None = None
    unit: str
    rule_ids: list[str] = Field(default_factory=list)
    guideline_refs: list[str] = Field(default_factory=list)


class ClinicalTargets(BaseModel):
    """Kết quả của bộ tính định mức. Luôn kèm rule_ids để UI giải trình được."""

    patient_id: str
    bmr_kcal: float
    tdee_kcal: float
    targets: dict[str, NutrientTarget]
    applied_rule_ids: list[str] = Field(default_factory=list)
    needs_expert_review: bool = False
    conflict_notes: list[str] = Field(default_factory=list)

    def max_of(self, nutrient: str) -> float | None:
        t = self.targets.get(nutrient)
        return t.max_value if t else None

    def min_of(self, nutrient: str) -> float | None:
        t = self.targets.get(nutrient)
        return t.min_value if t else None


class FoodItem(BaseModel):
    """Một dòng trong bảng thành phần thực phẩm. `source` là bắt buộc (RULE R40.2)."""

    id: int
    name_vi: str
    aliases: list[str] = Field(default_factory=list)
    kcal_100g: float = Field(ge=0, le=900)
    protein_g: float = Field(ge=0, le=90)
    carb_g: float = Field(ge=0, le=100)
    fat_g: float = Field(ge=0, le=100)
    fiber_g: float = Field(ge=0, le=80)
    na_mg: float = Field(ge=0, le=25000)
    k_mg: float = Field(ge=0, le=5000)
    p_mg: float = Field(ge=0, le=2000)
    purine_mg: float = Field(ge=0, le=1000)
    gi_index: float | None = Field(default=None, ge=0, le=110)
    contains_allergens: list[str] = Field(default_factory=list)
    source: Literal["NIN", "USDA", "curated", "estimated"]
    source_ref: str = Field(min_length=1)
    is_estimated: bool = False

    @field_validator("source_ref")
    @classmethod
    def _source_ref_not_placeholder(cls, v: str) -> str:
        if v.strip().upper() in {"TODO", "N/A", "-", "?"}:
            raise ValueError("source_ref bắt buộc phải là nguồn thật, không được để TODO")
        return v


class MenuItem(BaseModel):
    """Một món trong thực đơn.

    LLM chỉ được sinh ra ĐÚNG hai field này (RULE-1). Mọi giá trị dinh dưỡng
    được tính ở tầng deterministic, không bao giờ do LLM cung cấp.
    """

    food_id: int
    grams: float = Field(gt=0, le=2000)


class MealSlot(StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class MenuDraft(BaseModel):
    """Bản nháp thực đơn do LLM chọn — CỐ Ý không có field dinh dưỡng nào."""

    items: dict[MealSlot, list[MenuItem]] = Field(default_factory=dict)

    def all_items(self) -> list[MenuItem]:
        return [i for items in self.items.values() for i in items]


class SourceRef(BaseModel):
    food_id: int
    name: str
    grams: float
    source: str
    source_ref: str
    is_estimated: bool = False


class NutritionSummary(BaseModel):
    """Kết quả tính bằng SQL/Python. `sources` rỗng là bug, không phải trường hợp hợp lệ."""

    kcal: float
    protein_g: float
    carb_g: float
    fat_g: float
    fiber_g: float
    na_mg: float
    k_mg: float
    p_mg: float
    purine_mg: float
    sources: list[SourceRef]
    has_estimated: bool = False

    def value_of(self, nutrient: str) -> float:
        return float(getattr(self, nutrient))


class Severity(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class Violation(BaseModel):
    nutrient: str
    actual: float
    limit: float
    unit: str
    kind: Literal["over", "under", "allergy", "drug_food"]
    severity: Severity
    message_vi: str
    suggestion: str | None = None
    rule_id: str | None = None

    @property
    def blocking(self) -> bool:
        return self.severity is Severity.HARD
