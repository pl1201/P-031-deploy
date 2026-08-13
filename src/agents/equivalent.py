"""Thực đơn tương đương từ tủ lạnh (P2/AGT-12).

LLM: NO — tái dùng nguyên `_try_solve()` của `CPSATMenuOptimizer`
(src/agents/optimizer.py), chỉ đổi 2 input: tập ứng viên (giao giữa tủ lạnh
+ nguyên liệu chủ lực) và `bounds` (giao giữa ngưỡng lâm sàng gốc và dải
base±tolerance, lấy bên chặt hơn). Không có lời gọi mô hình ngôn ngữ nào.

"Tương đương" được định nghĩa bằng RÀNG BUỘC TOÁN HỌC, không phải độ tương tự
ngữ nghĩa: kết quả phải nằm trong CẢ ngưỡng lâm sàng gốc (`compute_targets()`)
LẪN dải base±tolerance. Vô nghiệm → trả `EquivalentMenuResult.reason_vi` giải
thích, KHÔNG bao giờ trả thực đơn một phần (RULE-2/RULE-3).

Chính sách phạm vi thay thế duyệt trước (RULE-3) — xem DEC-018 trong
DEVLOG.md §3: tolerance mặc định ±10% mọi chất, hạn dùng 7 ngày,
`max_auto_releases=5`, nguyên liệu chủ lực = {gạo, dầu ăn, nước mắm, muối,
đường, tỏi, hành lá}. Việc TỰ PHÁT HÀNH (không qua chuyên gia duyệt riêng lẻ)
không thuộc phạm vi module này — module này chỉ GIẢI bài toán tối ưu; quyết
định có phát hành tự động hay không thuộc tầng gọi (route), dựa trên bảng
`substitution_scopes` (còn hạn, `validate_menu()` sạch, chưa vượt
`max_auto_releases`, mọi nguyên liệu không `is_estimated`).
"""

from __future__ import annotations

from typing import NamedTuple

from src.agents.optimizer import (
    _NUTRIENT_TO_FIELD,
    _active_nutrient_bounds,
    _dish_nutrient_totals,
    _eligible_candidates,
    _try_solve,
)
from src.clinical.models import ClinicalTargets, DishCandidate, FoodItem, MenuDraft, NutritionSummary
from src.clinical.nutrition import FoodRepository

# DEC-018 (2026-08-09, Hưng xác nhận) — không tự đặt số, xem DEVLOG §3.
EQUIVALENT_TOLERANCE = 0.10
SUBSTITUTION_SCOPE_DAYS = 7
MAX_AUTO_RELEASES = 5

# Nguyên liệu chủ lực (DEC-018): luôn coi là có sẵn trong tủ lạnh, không cần
# bệnh nhân khai báo. Khớp CHÍNH XÁC theo `name_vi` của dòng curated đã xác
# nhận tồn tại trong `food_items.csv` (id thấp, nguồn NIN) — không suy đoán/
# fuzzy match sang biến thể khác (VD "Gạo nếp", "Dầu thực vật" là dòng KHÁC,
# cố ý không gộp vào để không mở rộng danh sách ngoài phạm vi đã duyệt).
STAPLE_NAMES_VI: tuple[str, ...] = (
    "Gạo tẻ (sống)",
    "Dầu ăn thực vật",
    "Nước mắm",
    "Muối ăn",
    "Đường trắng",
    "Tỏi",
    "Hành lá",
)

# food field (FoodItem/bounds key) -> nutrient key dùng bởi NutritionSummary.value_of().
_FIELD_TO_NUTRIENT: dict[str, str] = {field: nutrient for nutrient, field in _NUTRIENT_TO_FIELD.items()}

# Chất mà `NutritionSummary` chỉ cộng được TỪNG PHẦN (món thiếu số liệu bị bỏ
# qua khi cộng) -> tên cờ báo tổng đã đủ hay chưa. Xem docstring của
# `NutritionSummary.sugar_is_complete` / `purine_is_complete`.
_COMPLETENESS_FLAG_BY_NUTRIENT: dict[str, str] = {
    "sugar_g": "sugar_is_complete",
    "purine_mg": "purine_is_complete",
}


class EquivalentMenuResult(NamedTuple):
    """`draft` chỉ khác None khi giải được TRỌN VẸN. Không có kết quả một phần."""

    draft: MenuDraft | None
    reason_vi: str | None = None


def resolve_staple_food_ids(foods: FoodRepository) -> set[int]:
    """food_id của nhóm nguyên liệu chủ lực (DEC-018).

    Tên không khớp được (VD seed đổi tên) thì bỏ qua — không tự chọn món gần
    giống thay thế (RULE-2). Không có `search` cho khớp chính xác nên duyệt
    kết quả substring rồi lọc bằng so khớp tuyệt đối.
    """
    ids: set[int] = set()
    for name in STAPLE_NAMES_VI:
        for food in foods.search(name):
            if food.name_vi == name:
                ids.add(food.id)
                break
    return ids


def _equivalent_bounds(
    targets: ClinicalTargets,
    base_nutrition: NutritionSummary,
    tolerance: float,
) -> tuple[dict[str, tuple[float | None, float | None]] | None, str | None]:
    """Giao giữa ngưỡng lâm sàng gốc và dải base±tolerance, bên chặt hơn thắng.

    Trả (None, lý do) khi một chất có dải rỗng (không giao nhau) — cả ngày
    coi là vô nghiệm ngay từ bước ràng buộc, không cần gọi solver.

    Chất có tổng KHÔNG ĐẦY ĐỦ thì KHÔNG áp dải tương đương
    ---------------------------------------------------------
    `NutritionSummary` chỉ cộng những món CÓ số liệu cho `sugar_g`/`purine_mg`
    và gắn cờ `*_is_complete=False` khi có món bị bỏ qua — tổng khi đó là con
    số THIẾU HỤT, không phải lượng thật (xem docstring của chính hai field đó:
    "rule ... KHÔNG được coi đây là đạt ngưỡng").

    Dựng dải ±tolerance quanh một tổng thiếu hụt là sai hai lần:

    1. Nó ghim thực đơn mới vào artefact của dữ liệu khuyết, không phải vào
       thực đơn gốc. Thực đơn mới cộng đường trên một TẬP MÓN KHÁC, nên hai
       con số không so được với nhau.
    2. Với tổng nhỏ, dải trở nên vô nghĩa về mặt thực hành. Đo trên ca thật
       (2026-08-12): base `sugar_g=8.89` và `sugar_is_complete=False` → dải
       ±10% chỉ còn **8.0–9.78 g cho CẢ NGÀY** (rộng 1.78 g), trong khi các
       chất khác rộng 23–486 đơn vị. Chính ràng buộc này làm bài toán vô
       nghiệm dù tủ lạnh đã khai báo TOÀN BỘ món curated.

    Vì vậy chất thiếu dữ liệu chỉ giữ NGƯỠNG LÂM SÀNG, bỏ dải tương đương.
    Đây KHÔNG phải nới lỏng an toàn: trần WHO cho đường tự do vẫn áp nguyên
    (`T2DM-SUG-01`), chỉ bỏ đi một ràng buộc chưa bao giờ đo được thật.
    """
    active = _active_nutrient_bounds(targets)
    bounds: dict[str, tuple[float | None, float | None]] = {}
    for field, (lo, hi) in active.items():
        nutrient = _FIELD_TO_NUTRIENT.get(field)
        if nutrient is None:
            continue

        flag = _COMPLETENESS_FLAG_BY_NUTRIENT.get(nutrient)
        if flag is not None and not getattr(base_nutrition, flag):
            if lo is not None or hi is not None:
                bounds[field] = (lo, hi)
            continue

        base_value = base_nutrition.value_of(nutrient)
        band_lo, band_hi = base_value * (1 - tolerance), base_value * (1 + tolerance)
        new_lo = band_lo if lo is None else max(lo, band_lo)
        new_hi = band_hi if hi is None else min(hi, band_hi)
        if new_lo > new_hi:
            return None, (
                f"Dải ±{tolerance:.0%} quanh thực đơn gốc không giao với ngưỡng lâm sàng cho "
                f"'{nutrient}' — không có thực đơn tương đương nào vừa an toàn vừa gần thực đơn gốc."
            )
        bounds[field] = (new_lo, new_hi)
    if not bounds:
        return (
            None,
            "Thực đơn gốc không có ngưỡng dinh dưỡng nào áp dụng được — không đủ căn cứ để tìm thực đơn tương đương.",
        )
    return bounds, None


def solve_equivalent(
    base_nutrition: NutritionSummary,
    targets: ClinicalTargets,
    pantry_food_ids: set[int],
    candidates: list[FoodItem],
    dishes: list[DishCandidate],
    foods: FoodRepository,
    tolerance: float = EQUIVALENT_TOLERANCE,
) -> EquivalentMenuResult:
    """Giải thực đơn tương đương chỉ từ nguyên liệu có sẵn (tủ lạnh + chủ lực).

    `candidates`/`dishes` PHẢI đã qua cùng bước lọc dị ứng/dislike như thực
    đơn gốc (đúng hợp đồng của `CPSATMenuOptimizer.generate()`) — module này
    không lọc lại profile, chỉ thu hẹp thêm theo tủ lạnh + ngưỡng.
    """
    bounds, reason = _equivalent_bounds(targets, base_nutrition, tolerance)
    if bounds is None:
        return EquivalentMenuResult(draft=None, reason_vi=reason)

    pantry_candidates = [f for f in candidates if f.id in pantry_food_ids]
    eligible = _eligible_candidates(pantry_candidates, bounds)

    pantry_dishes = [d for d in dishes if all(ing.food_id in pantry_food_ids for ing in d.ingredients)]
    dish_totals: list[tuple[DishCandidate, dict[str, float]]] = []
    for dish in pantry_dishes:
        totals = _dish_nutrient_totals(dish, foods, bounds)
        if totals is not None:
            dish_totals.append((dish, totals))

    if not eligible and not dish_totals:
        return EquivalentMenuResult(
            draft=None,
            reason_vi="Tủ lạnh (kể cả nguyên liệu chủ lực) không đủ nguyên liệu đạt yêu cầu dinh dưỡng — gợi ý mua thêm rau/đạm/chất xơ.",
        )

    draft = _try_solve(eligible, bounds, dish_totals)
    if draft is None:
        return EquivalentMenuResult(
            draft=None,
            reason_vi="Không tìm được tổ hợp món nào trong tủ lạnh hiện có thoả đồng thời ngưỡng lâm sàng và dải tương đương — gợi ý mua thêm nguyên liệu đa dạng hơn.",
        )
    return EquivalentMenuResult(draft=draft)
