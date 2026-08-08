"""Domain models cho tầng lâm sàng.

LLM: NO — module này thuần dữ liệu, không import bất kỳ LLM client nào.
Ticket: CLN-01..CLN-05
"""

from __future__ import annotations

from enum import Enum
from typing import ClassVar, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """4 mức "loại lao động" — khớp đúng nhãn/số lượng mức chuyên gia dinh
    dưỡng dự án dùng thật trên Excel (`Bước 1+2!H13:J17`, "Bảng 2: Hệ số tính
    chuyển hoá cơ sở"): nhẹ/trung bình/nặng/rất nặng. Đổi từ enum cũ
    (sedentary/light/moderate/active, 2026-08-05→08-06) — không có mức "tĩnh
    tại" riêng vì Bảng 2 gốc không có, và thêm mức "rất nặng" còn thiếu.
    Quyết định: `docs/TICKETS.md` đề xuất `CLN-09`."""

    LIGHT = "light"  # Lao động nhẹ
    MODERATE = "moderate"  # Lao động trung bình
    HEAVY = "heavy"  # Lao động nặng
    VERY_HEAVY = "very_heavy"  # Lao động rất nặng


class WeightGoal(str, Enum):
    LOSE = "lose"
    MAINTAIN = "maintain"
    GAIN = "gain"


class ConditionCode(str, Enum):
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
    activity_level: ActivityLevel = ActivityLevel.LIGHT
    weight_goal: WeightGoal = WeightGoal.MAINTAIN
    conditions: list[Condition] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    region: Literal["north", "central", "south"] | None = None
    dislikes: list[str] = Field(default_factory=list)

    # --- Cờ lâm sàng ảnh hưởng tới việc áp dụng ngưỡng ---
    # Nguồn: KDIGO 2024 Practice Point 3.3.1.3 và 3.3.1.5
    frailty_sarcopenia: bool = Field(
        default=False,
        description=(
            "Suy yếu và/hoặc thiểu cơ. KDIGO 2024 PP 3.3.1.5: người cao tuổi có "
            "frailty/sarcopenia cần cân nhắc mục tiêu protein và năng lượng CAO HƠN, "
            "nên KHÔNG áp trần protein thấp."
        ),
    )
    metabolically_unstable: bool = Field(
        default=False,
        description=(
            "Chuyển hoá không ổn định. KDIGO 2024 PP 3.3.1.3: KHÔNG kê chế độ thấp/rất thấp protein cho nhóm này."
        ),
    )
    sodium_wasting: bool = Field(
        default=False,
        description=("Bệnh thận mất muối. KDIGO 2024 PP 3.3.2.1: hạn chế natri thường KHÔNG phù hợp với nhóm này."),
    )

    ELDERLY_AGE_THRESHOLD: ClassVar[int] = 65

    @property
    def bmi(self) -> float:
        return self.weight_kg / (self.height_cm / 100) ** 2

    @property
    def clinical_flags(self) -> set[str]:
        """Tập cờ dùng để bật/tắt rule lâm sàng.

        `elderly` được suy ra từ tuổi thay vì nhập tay, để không phụ thuộc
        người nhập nhớ tích ô.
        """
        flags: set[str] = set()
        if self.age >= self.ELDERLY_AGE_THRESHOLD:
            flags.add("elderly")
        if self.frailty_sarcopenia:
            flags.add("frailty_sarcopenia")
        if self.metabolically_unstable:
            flags.add("metabolically_unstable")
        if self.sodium_wasting:
            flags.add("sodium_wasting")
        return flags

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
    category: str | None = None
    kcal_100g: float = Field(ge=0, le=920)  # mỡ/dầu tinh ~884-902 kcal/100 g
    protein_g: float = Field(ge=0, le=90)
    carb_g: float = Field(ge=0, le=100)
    fat_g: float = Field(ge=0, le=100)
    fiber_g: float = Field(ge=0, le=80)
    sugar_g: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "Tổng đường (thuộc carb_g). Cần cho ngưỡng đường tự do ĐTĐ2 (WHO <10%/<5% "
            "năng lượng). None khi nguồn không tách được đường ra khỏi carb tổng."
        ),
    )
    na_mg: float = Field(ge=0, le=40000)  # trần ~muối tinh (NaCl ≈ 38.758 mg Na/100 g)
    k_mg: float = Field(ge=0, le=5000)
    p_mg: float = Field(ge=0, le=2000)
    # Purine chỉ cần cho GOUT và KHÔNG có trong NIN → optional (giống sugar_g/gi).
    # None = chưa có nguồn purine; menu engine suy giảm mềm + cảnh báo cho ca gout.
    # purine đến từ nguồn RIÊNG (USDA/ODS-NIH Purine DB) nên có source_ref riêng (RULE-2).
    purine_mg: float | None = Field(default=None, ge=0, le=1000)
    purine_source_ref: str | None = None
    gi_index: float | None = Field(default=None, ge=0, le=110)
    # GI có nguồn RIÊNG, tách khỏi kcal/natri (thường là Atkinson 2021 hoặc Mai 2001
    # cho món Việt) — nên cần source_ref của chính nó để giữ RULE-2.
    gi_source: Literal["Atkinson2021", "Chan2001_VN", "estimated"] | None = None
    gi_source_ref: str | None = None
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

    @model_validator(mode="after")
    def _gi_and_sugar_consistency(self) -> FoodItem:
        # RULE-2 cho cột GI: có trị GI thì phải dẫn được nguồn GI, không mượn
        # source_ref của NIN (nguồn kcal khác nguồn GI). Ref chỉ có khoảng trắng
        # cũng bị coi là thiếu — nếu không, "   " sẽ lọt qua guard này.
        if self.gi_index is not None:
            ref = (self.gi_source_ref or "").strip()
            if not self.gi_source or not ref:
                raise ValueError(
                    f"[{self.name_vi}] gi_index={self.gi_index} nhưng thiếu gi_source/"
                    "gi_source_ref — mỗi con số hiển thị phải có nguồn riêng (RULE-2)"
                )
            if ref.upper() in {"TODO", "N/A", "-", "?"}:
                raise ValueError("gi_source_ref không được để placeholder (RULE-2)")
        # Đường là tập con của carbohydrate → không thể lớn hơn carb tổng.
        if self.sugar_g is not None and self.sugar_g > self.carb_g:
            raise ValueError(
                f"[{self.name_vi}] sugar_g={self.sugar_g} > carb_g={self.carb_g} — đường phải là tập con của carb tổng"
            )
        return self

    @property
    def available_carb_g(self) -> float:
        """Carbohydrate khả dụng trên 100 g = carb tổng − chất xơ.

        GI và GL được đo trên carb khả dụng chứ không phải carb tổng (ISO/Atkinson
        2021). Với 'carbohydrate by difference' của NIN/USDA, chất xơ nằm trong
        carb_g nên phải trừ ra. Kẹp sàn 0 để tránh trị âm do sai số nguồn.
        """
        return max(self.carb_g - self.fiber_g, 0.0)

    def glycemic_load(self, grams: float) -> float | None:
        """Tải đường huyết (GL) của một khẩu phần `grams`.

        GL = GI × (carb khả dụng của khẩu phần) / 100. Trả None khi chưa có GI —
        caller PHẢI suy giảm mềm (dựa vào lượng carb + nhóm thực phẩm), không được
        coi món thiếu GI là GL = 0.
        """
        if self.gi_index is None:
            return None
        portion_avail_carb = self.available_carb_g * grams / 100.0
        return self.gi_index * portion_avail_carb / 100.0


class MenuItem(BaseModel):
    """Một món trong thực đơn.

    LLM chỉ được sinh ra ĐÚNG hai field này (RULE-1). Mọi giá trị dinh dưỡng
    được tính ở tầng deterministic, không bao giờ do LLM cung cấp.
    """

    food_id: int
    grams: float = Field(gt=0, le=2000)


class MealSlot(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class PlannedDish(BaseModel):
    """Món hoàn chỉnh được optimizer chọn; ingredients chỉ dùng để tính số."""

    dish_id: str
    serving_grams: float = Field(gt=0, le=2000)


class MenuDraft(BaseModel):
    """Bản nháp thực đơn do LLM chọn — CỐ Ý không có field dinh dưỡng nào."""

    items: dict[MealSlot, list[MenuItem]] = Field(default_factory=dict)
    planned_dishes: dict[MealSlot, list[PlannedDish]] = Field(default_factory=dict)

    def all_items(self) -> list[MenuItem]:
        return [i for items in self.items.values() for i in items]


class DishCandidate(BaseModel):
    """Một món ăn Việt Nam hoàn chỉnh (công thức = nguyên liệu cố định), dùng làm
    khung cho generator thay vì luôn ghép rời từng nguyên liệu thô (CLN-*, xem
    quyết định "hybrid: dish làm khung" trong DEVLOG).

    CỐ Ý không tự sinh MenuItem mới — `ingredients` là food_id + gram THẬT lấy
    từ `dish_ingredients.csv`, generator chỉ chọn "dùng món này hay không",
    Python vẫn là nơi duy nhất tính dinh dưỡng (RULE-1 giữ nguyên qua lớp này).
    """

    dish_id: str
    name_vi: str
    region: str | None = None
    # `data/seeds/dishes.csv` hiện có 2 nhóm hoàn toàn khác nhau dưới cùng cột
    # verified_by: ~2600 dòng "USDA FNDDS" (khối bulk thực phẩm Mỹ lẫn vào,
    # KHÔNG phải món Việt — bị loại ở load_vn_dishes()) và 30 món Việt thật
    # (Phở bò, Bún đậu mắm...) nhưng verified_by="pending" — R2 CHƯA rà công
    # thức. is_reviewed=False cho toàn bộ 30 món này hiện tại; downstream (API/
    # UI) phải hiển thị cảnh báo "công thức chưa qua chuyên gia rà" khi dùng.
    is_reviewed: bool = False
    verified_by: str | None = None
    ingredients: list[MenuItem] = Field(default_factory=list)


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
    # Chỉ cộng các món có purine_mg. False = có món thiếu số liệu purine → tổng bị
    # thiếu hụt, rule gout KHÔNG được coi đây là "đạt ngưỡng".
    purine_is_complete: bool = True
    # Tổng đường (đường tự do WHO cho ĐTĐ2). Chỉ cộng các món có sugar_g.
    # `sugar_is_complete=False` nghĩa là có món thiếu số liệu đường → tổng bị
    # thiếu hụt, rule đường tự do KHÔNG được coi đây là "đạt ngưỡng".
    sugar_g: float = 0.0
    sugar_is_complete: bool = True
    sources: list[SourceRef]
    has_estimated: bool = False

    def value_of(self, nutrient: str) -> float:
        return float(getattr(self, nutrient))


class Severity(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class Violation(BaseModel):
    nutrient: str
    actual: float
    limit: float
    unit: str
    kind: Literal["over", "under", "allergy", "drug_food", "incomplete_data"]
    severity: Severity
    message_vi: str
    suggestion: str | None = None
    rule_id: str | None = None

    @property
    def blocking(self) -> bool:
        return self.severity is Severity.HARD
