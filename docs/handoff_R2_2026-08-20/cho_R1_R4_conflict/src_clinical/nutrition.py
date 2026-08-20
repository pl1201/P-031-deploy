"""Tính dinh dưỡng từ thực đơn.

LLM: NO — đây là nơi RULE-1 được thực thi.
Ticket: AGT-05, CLN-05

⚠️ RULE-1: LLM chọn món, Python tính số.
Mọi giá trị dinh dưỡng trong hệ thống đi qua đúng hàm compute_nutrition() dưới đây.
Nếu bạn thấy một con số dinh dưỡng được sinh ở chỗ khác — đó là bug kiến trúc.

Test tests/test_no_llm_import.py chặn việc import LLM client vào module này.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .gia_vi import la_nguon_man
from .models import (
    FoodItem,
    MealSlot,
    MenuDraft,
    MenuItem,
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
        return [i for i in self._by_id.values() if t in i.name_vi.lower() or any(t in a.lower() for a in i.aliases)]

    def all(self) -> list[FoodItem]:
        return list(self._by_id.values())


class UnknownFoodError(ValueError):
    """LLM trả về food_id không tồn tại — reject, tuyệt đối không suy đoán thay thế."""


def compute_nutrition(menu: MenuDraft, repo: FoodRepository) -> NutritionSummary:
    """Cộng dinh dưỡng của thực đơn bằng dữ liệu tra từ repository.

    Mọi item đều sinh ra một SourceRef — `sources` rỗng nghĩa là thực đơn rỗng,
    không bao giờ là "không tra được nguồn".
    """
    # `fat_g` cố ý KHÔNG nằm trong `totals`: nó là Optional (DEC-061) nên được
    # cộng riêng None-aware như sugar/purine, rồi truyền vào NutritionSummary
    # bằng tham số riêng bên dưới.
    totals = {k: 0.0 for k in NUTRIENT_FIELDS if k != "fat_g"}
    sources: list[SourceRef] = []
    has_estimated = False
    # Đường xử lý riêng vì sugar_g là Optional: chỉ cộng món có số liệu, và
    # đánh dấu không đầy đủ nếu có món thiếu — để rule đường tự do không bị
    # đánh lừa bởi một tổng bị thiếu hụt.
    sugar_total = 0.0
    sugar_is_complete = True
    # Purine cũng Optional (không có trong NIN/USDA) — xử lý None-aware như sugar.
    purine_total = 0.0
    purine_is_complete = True
    # Chất béo: một số rau gia vị Việt không có số liệu trong NIN (DEC-061).
    fat_total = 0.0
    fat_is_complete = True

    for item in menu.all_items():
        food = repo.get(item.food_id)
        if food is None:
            raise UnknownFoodError(
                f"food_id={item.food_id} không có trong CSDL. Không được đoán sang thực phẩm gần giống (RULE R40.4)."
            )
        factor = item.grams / 100.0
        totals["kcal"] += food.kcal_100g * factor
        totals["protein_g"] += food.protein_g * factor
        totals["carb_g"] += food.carb_g * factor
        totals["fiber_g"] += food.fiber_g * factor
        totals["na_mg"] += food.na_mg * factor
        totals["k_mg"] += food.k_mg * factor
        totals["p_mg"] += food.p_mg * factor

        if food.fat_g is None:
            fat_is_complete = False
        else:
            fat_total += food.fat_g * factor

        if food.purine_mg is None:
            purine_is_complete = False
        else:
            purine_total += food.purine_mg * factor

        if food.sugar_g is None:
            sugar_is_complete = False
        else:
            sugar_total += food.sugar_g * factor

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
        fat_g=round(fat_total, 2),
        fat_is_complete=fat_is_complete,
        purine_mg=round(purine_total, 2),
        purine_is_complete=purine_is_complete,
        sugar_g=round(sugar_total, 2),
        sugar_is_complete=sugar_is_complete,
        sources=sources,
        has_estimated=has_estimated,
    )


def compute_dish_nutrition(ingredients: Iterable[MenuItem], repo: FoodRepository) -> NutritionSummary:
    """Dinh dưỡng của MỘT món, tính từ danh sách nguyên liệu của chính nó.

    Dùng để hiển thị cho bệnh nhân: "Bánh mì thịt · 180 g · 420 kcal" thay vì chỉ
    có tổng cả ngày. Tầng API/UI cần con số này (xem
    `HANDOFF_R4_HIEN_THI_MON_CHO_BENH_NHAN.md`), nhưng `src/clinical/` mới là nơi
    được phép tính nó — RULE-1: Python tính số, không phải LLM, và cũng không
    phải JavaScript ở tầng hiển thị.

    CỐ Ý gọi thẳng `compute_nutrition()` thay vì chép lại vòng cộng: nếu viết
    công thức thứ hai thì tổng từng món và tổng cả ngày sẽ trôi khỏi nhau khi một
    bên được sửa mà bên kia quên — đúng loại lệch mà bệnh nhân nhìn thấy ngay
    (cộng 4 món ra một số, thẻ tổng ngày ra số khác) và không ai giải thích được.

    Ràng buộc None-aware của `sugar_g`/`purine_mg`/`fat_g` được giữ nguyên: món
    có nguyên liệu thiếu số liệu sẽ trả về `*_is_complete=False` chứ không lặng lẽ
    cộng 0 (RULE-2). Tầng hiển thị phải đọc cờ đó, đừng in thẳng con số thiếu.

    Lưu ý khi cộng lại: mỗi `NutritionSummary` đã làm tròn 2 chữ số thập phân, nên
    cộng tay các món có thể lệch tổng ngày vài phần trăm gram. Muốn khớp tuyệt đối
    thì lấy `computed_nutrition` của cả kế hoạch, đừng tự cộng ở tầng hiển thị.
    """
    return compute_nutrition(MenuDraft(items={MealSlot.LUNCH: list(ingredients)}), repo)


def check_allergies(
    menu: MenuDraft,
    profile: PatientProfile,
    repo: FoodRepository,
    *,
    sua_duoc: frozenset[int] = frozenset(),
) -> list[Violation]:
    """Dị ứng là ràng buộc CỨNG (RULE R10.6) — trừ nguyên liệu SỬA ĐƯỢC (DEC-092).

    Ngoại lệ duy nhất, do R2 chốt 17/08/2026: dị nguyên đến từ GIA VỊ (nguồn mặn
    đổi nhau được) hoặc từ nguyên liệu công thức khai TUỲ CHỌN thì không loại bỏ
    thực đơn — nó thành cảnh báo kèm chỉ dẫn sửa, và đi tiếp ra `safety_findings`
    để bệnh nhân lẫn chuyên gia duyệt đều đọc được.

    Đây KHÔNG phải nới ngưỡng: nguyên liệu định danh (cá trong canh chua cá) vẫn
    HARD như cũ. Phần nới đúng bằng phần mà ngoài đời người ta thật sự đổi được —
    xem `src/clinical/di_ung_nguyen_lieu.py`.

    `sua_duoc` là tập `food_id` được miễn chặn cho ĐÚNG thực đơn này — tính bằng
    `di_ung_nguyen_lieu.tap_sua_duoc()`, không tự suy ra ở đây. Bỏ trống thì mọi
    dị nguyên đều HARD như trước (fail closed): hàm này không được tự nới cho
    chính mình, nơi gọi phải nói rõ đã cân nhắc.
    """
    if not profile.allergies:
        return []

    violations: list[Violation] = []
    for item in menu.all_items():
        food = repo.get(item.food_id)
        if food is None:
            continue
        for allergen in food.contains_allergens:
            if allergen.lower() not in profile.allergies:
                continue
            if item.food_id in sua_duoc:
                violations.append(
                    Violation(
                        nutrient=allergen,
                        actual=item.grams,
                        limit=0.0,
                        unit="g",
                        kind="allergy_advisory",
                        severity=Severity.SOFT,
                        message_vi=(
                            f"Bệnh nhân dị ứng {allergen}. Thực đơn có {food.name_vi} "
                            f"({item.grams:.1f} g) — nguyên liệu SỬA ĐƯỢC, không phải "
                            f"thành phần định danh của món."
                        ),
                        suggestion=(
                            f"Thay {food.name_vi} bằng gia vị không chứa {allergen} "
                            f"(giữ nguyên độ mặn), hoặc bỏ nguyên liệu này khi chế biến."
                            if la_nguon_man(item.food_id)
                            else f"Bỏ {food.name_vi} khi chế biến — món vẫn đúng công thức."
                        ),
                    )
                )
                continue
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
