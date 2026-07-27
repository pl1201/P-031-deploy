"""Tính dinh dưỡng từ thực đơn.

LLM: NO — đây là nơi RULE-1 được thực thi.
Ticket: AGT-05, CLN-05

⚠️ RULE-1: LLM chọn món, Python tính số.
Mọi giá trị dinh dưỡng trong hệ thống đi qua đúng hàm compute_nutrition() dưới đây.
Nếu bạn thấy một con số dinh dưỡng được sinh ở chỗ khác — đó là bug kiến trúc.

Test tests/test_no_llm_import.py chặn việc import LLM client vào module này.
"""

from __future__ import annotations

from typing import Protocol

from .models import (
    FoodItem,
    MenuDraft,
    NutritionSummary,
    PatientProfile,
    Severity,
    SourceRef,
    Violation,
)

NUTRIENT_FIELDS = (
    "kcal",
    "protein_g",
    "carb_g",
    "fat_g",
    "fiber_g",
    "na_mg",
    "k_mg",
    "p_mg",
    "purine_mg",
)


class FoodRepository(Protocol):
    """Cổng truy cập bảng thành phần thực phẩm.

    Ở production là truy vấn SQL vào Postgres; trong test là bản in-memory.
    Dù ở đâu, đây là nguồn DUY NHẤT của mọi con số dinh dưỡng.
    """

    def get(self, food_id: int) -> FoodItem | None: ...

    def search(self, term: str) -> list[FoodItem]: ...


class InMemoryFoodRepository:
    """Bản cài đặt dùng cho test và seed. Tra cả theo tên chính lẫn alias."""

    def __init__(self, items: list[FoodItem]) -> None:
        self._by_id = {i.id: i for i in items}

    def get(self, food_id: int) -> FoodItem | None:
        return self._by_id.get(food_id)

    def search(self, term: str) -> list[FoodItem]:
        t = term.strip().lower()
        return [
            i
            for i in self._by_id.values()
            if t in i.name_vi.lower() or any(t in a.lower() for a in i.aliases)
        ]

    def all(self) -> list[FoodItem]:
        return list(self._by_id.values())


class UnknownFoodError(ValueError):
    """LLM trả về food_id không tồn tại — reject, tuyệt đối không suy đoán thay thế."""


def compute_nutrition(menu: MenuDraft, repo: FoodRepository) -> NutritionSummary:
    """Cộng dinh dưỡng của thực đơn bằng dữ liệu tra từ repository.

    Mọi item đều sinh ra một SourceRef — `sources` rỗng nghĩa là thực đơn rỗng,
    không bao giờ là "không tra được nguồn".
    """
    totals = dict.fromkeys(NUTRIENT_FIELDS, 0.0)
    sources: list[SourceRef] = []
    has_estimated = False

    for item in menu.all_items():
        food = repo.get(item.food_id)
        if food is None:
            raise UnknownFoodError(
                f"food_id={item.food_id} không có trong CSDL. "
                "Không được đoán sang thực phẩm gần giống (RULE R40.4)."
            )
        factor = item.grams / 100.0
        totals["kcal"] += food.kcal_100g * factor
        totals["protein_g"] += food.protein_g * factor
        totals["carb_g"] += food.carb_g * factor
        totals["fat_g"] += food.fat_g * factor
        totals["fiber_g"] += food.fiber_g * factor
        totals["na_mg"] += food.na_mg * factor
        totals["k_mg"] += food.k_mg * factor
        totals["p_mg"] += food.p_mg * factor
        totals["purine_mg"] += food.purine_mg * factor

        has_estimated = has_estimated or food.is_estimated
        sources.append(
            SourceRef(
                food_id=food.id,
                name=food.name_vi,
                grams=item.grams,
                source=food.source,
                source_ref=food.source_ref,
                is_estimated=food.is_estimated,
            )
        )

    return NutritionSummary(
        **{k: round(v, 2) for k, v in totals.items()},
        sources=sources,
        has_estimated=has_estimated,
    )


def check_allergies(
    menu: MenuDraft, profile: PatientProfile, repo: FoodRepository
) -> list[Violation]:
    """Dị ứng là ràng buộc CỨNG tuyệt đối (RULE R10.6) — không bao giờ hạ xuống cảnh báo."""
    if not profile.allergies:
        return []

    violations: list[Violation] = []
    for item in menu.all_items():
        food = repo.get(item.food_id)
        if food is None:
            continue
        for allergen in food.contains_allergens:
            if allergen.lower() in profile.allergies:
                violations.append(
                    Violation(
                        nutrient=allergen,
                        actual=item.grams,
                        limit=0.0,
                        unit="g",
                        kind="allergy",
                        severity=Severity.HARD,
                        message_vi=(
                            f"Bệnh nhân dị ứng {allergen}, nhưng thực đơn có "
                            f"{food.name_vi} ({item.grams:.0f} g) chứa {allergen}."
                        ),
                        suggestion=f"Loại bỏ hoàn toàn {food.name_vi} khỏi thực đơn.",
                    )
                )
    return violations
