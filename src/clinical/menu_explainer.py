"""Lớp Explainer & Coaching (lớp 4, đề xuất kiến trúc lai) — tầng tất định.

LLM: NO. Module này CHỈ lắp lại dữ kiện ĐÃ TÍNH SẴN (tên món/gram từ
`MealPlanItem`, ngưỡng từ `ClinicalTargets`, tổng dinh dưỡng từ
`NutritionSummary`, vi phạm còn sót từ `Violation`) thành `MenuFacts` — không
tính toán gì mới, không gọi LLM. Lớp diễn đạt tự nhiên bằng LLM (chỉ văn
phong hoá, không thêm dữ kiện) nằm ở `src/services/menu_coach.py`, đúng mô
hình đã dùng cho `target_explainer.py`/`target_assistant.py` (P1).

RULE-3: hàm này chỉ có ý nghĩa dùng cho thực đơn đã `approved` — bản thân
module không tự kiểm tra trạng thái (không có DB access ở đây), caller
(route) phải gate trạng thái trước khi gọi.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .validator import NUTRIENT_LABELS_VI


class MenuFactItem(BaseModel):
    name_vi: str
    slot: str
    grams: float


class NutrientFact(BaseModel):
    nutrient: str
    label_vi: str
    value: float
    min_value: float | None
    max_value: float | None
    unit: str
    status: Literal["within", "over", "under"]


class MenuFacts(BaseModel):
    """Toàn bộ dữ kiện đã tính sẵn cho một thực đơn — nguồn sự thật duy nhất
    mà LLM (`menu_coach.py`) được phép văn phong hoá."""

    plan_date: str
    items: list[MenuFactItem]
    nutrients: list[NutrientFact]
    soft_notes: list[str] = Field(default_factory=list)


def _nutrient_status(
    value: float, min_value: float | None, max_value: float | None
) -> Literal["within", "over", "under"]:
    if max_value is not None and value > max_value:
        return "over"
    if min_value is not None and value < min_value:
        return "under"
    return "within"


def assemble_menu_facts(
    plan_date: str,
    items: list[dict],
    targets: dict,
    nutrition: dict,
    violations: list[dict],
) -> MenuFacts:
    """Lắp `MenuFacts` từ dữ kiện đã tính sẵn của một `MealPlan`.

    `items`: mỗi phần tử có `name_vi`/`slot`/`grams` (VD từ
    `MealPlanOut.items`, đã resolve tên món/nguyên liệu).
    `targets`: dict thô của `ClinicalTargets.targets` (`{nutrient: {min_value,
    max_value, unit, ...}}`, VD `plan.targets` trên `MealPlan` DB row).
    `nutrition`: dict thô của `NutritionSummary` (`{nutrient: value, ...}`,
    VD `plan.computed_nutrition`).
    `violations`: dict thô của `list[Violation]` còn sót lại trên thực đơn đã
    duyệt — trên một plan `approved` chỉ nên còn vi phạm `soft` (severity
    `hard` phải chặn duyệt từ trước), nhưng hàm này không tự giả định, chỉ
    lắp lại message_vi đã có sẵn.
    """
    menu_items = [MenuFactItem(name_vi=i["name_vi"], slot=i["slot"], grams=i["grams"]) for i in items]

    nutrient_facts: list[NutrientFact] = []
    for nutrient, value in nutrition.items():
        # `bool` là subclass của `int` trong Python — `isinstance(True, int)` là
        # True, nên phải loại bool TRƯỚC kiểm tra số, nếu không các cờ
        # `purine_is_complete`/`sugar_is_complete`/`has_estimated` của
        # `NutritionSummary.model_dump()` sẽ bị hiểu nhầm thành chất dinh dưỡng
        # (phát hiện khi AGT-13 lần đầu gọi hàm này với dữ liệu thật, không
        # phải dict tay trong test — xem tests/test_menu_explainer.py).
        if isinstance(value, bool) or not isinstance(value, int | float):
            continue
        target = targets.get(nutrient) or {}
        min_value = target.get("min_value")
        max_value = target.get("max_value")
        unit = target.get("unit") or ""
        nutrient_facts.append(
            NutrientFact(
                nutrient=nutrient,
                label_vi=NUTRIENT_LABELS_VI.get(nutrient, nutrient),
                value=float(value),
                min_value=min_value,
                max_value=max_value,
                unit=unit,
                status=_nutrient_status(float(value), min_value, max_value),
            )
        )

    soft_notes = [v["message_vi"] for v in violations if v.get("message_vi")]

    return MenuFacts(plan_date=plan_date, items=menu_items, nutrients=nutrient_facts, soft_notes=soft_notes)
