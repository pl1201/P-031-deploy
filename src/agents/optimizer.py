"""Node: generate_menu (bản CP-SAT)
LLM: NO — deterministic, dùng OR-Tools CP-SAT thay vì gọi LLM đoán món.

Ticket: AGT-09, AGT-10. Implement thẳng `Protocol MenuGenerator`
(src/agents/nodes/core.py) nên cắm được vào `generate_menu` node hiện có mà
không đổi graph.

⚠️ RULE-1 (còn chặt hơn `GeminiMenuGenerator`): ở đây không có bước "đoán" nào cả
— solver GIẢI trực tiếp bài toán ràng buộc trên số liệu đã có sẵn trong
`FoodItem` (đã qua RULE-2: mọi con số đều có `source_ref`). Không có lời gọi
mô hình ngôn ngữ nào trong file này.

Vì sao CP-SAT thay vì cho LLM đoán rồi validate-retry (AGT-06):
- Vòng lặp hiện tại tốn tới 3 lượt gọi LLM mà vẫn có thể rơi vào fallback nếu
  LLM không "đoán trúng" tổ hợp thoả ràng buộc.
- CP-SAT tìm được lời giải khả thi ngay lần đầu nếu có, và báo infeasible
  ngay nếu không có — không cần đoán lại.
- Ràng buộc "chọn hay không chọn" (biến bool) là điểm CP-SAT mạnh hơn hẳn LP
  thuần (MPSolver) — bài toán chọn thực đơn thuộc đúng lớp bài toán này.

Mô hình: MỘT model cho CẢ NGÀY (AGT-10).
Bản đầu (AGT-09) chia định mức ngày cho 4 bữa theo tỉ lệ cố định rồi giải từng
bữa riêng. Cách đó có lỗi hệ thống: mỗi bữa phải tự thoả `tỉ_lệ × min` cho MỌI
chất, nên bữa nhỏ (VD bữa phụ 10%) dễ vô nghiệm; slot đó trả rỗng → tổng ngày
hụt → `validate` báo vi phạm ngưỡng tối thiểu. Nay gộp lại: biến cho từng cặp
(bữa, món), ràng buộc dinh dưỡng đặt trên TỔNG cả ngày, chỉ ràng buộc số món là
còn theo từng bữa (để không dồn hết vào một bữa).

Hạn chế còn lại (ghi rõ để không đánh lừa người đọc sau):
- `FoodItem` chưa có trường `category` (đã bỏ khi nạp từ CSV, xem
  `src/clinical/seeds.py`) nên optimizer KHÔNG ép được ràng buộc kiểu "phải
  có món nhóm rau" — chỉ ràng buộc được trên các cột dinh dưỡng có trong
  targets. Muốn thêm ràng buộc nhóm thực phẩm cần đưa `category` vào
  `FoodItem` trước (việc khác, ngoài phạm vi AGT-09/AGT-10).
"""

from __future__ import annotations

import logging
import math

from ortools.sat.python import cp_model  # type: ignore[import-not-found]  # chưa có type stub

from src.clinical.models import (
    ClinicalTargets,
    DishCandidate,
    FoodItem,
    MealSlot,
    MenuDraft,
    MenuItem,
    PlannedDish,
    PatientProfile,
)
from src.clinical.nutrition import FoodRepository

logger = logging.getLogger(__name__)

# Các bữa được xếp món. Không còn tỉ lệ năng lượng cố định cho từng bữa —
# ràng buộc dinh dưỡng nay đặt trên tổng cả ngày (xem docstring module).
_SLOTS: tuple[MealSlot, ...] = (
    MealSlot.BREAKFAST,
    MealSlot.LUNCH,
    MealSlot.DINNER,
    MealSlot.SNACK,
)

# nutrient key trong ClinicalTargets.targets -> tên field tương ứng trên FoodItem.
_NUTRIENT_TO_FIELD: dict[str, str] = {
    "kcal": "kcal_100g",
    "protein_g": "protein_g",
    "carb_g": "carb_g",
    "fat_g": "fat_g",
    "fiber_g": "fiber_g",
    "sugar_g": "sugar_g",
    "na_mg": "na_mg",
    "k_mg": "k_mg",
    "p_mg": "p_mg",
    "purine_mg": "purine_mg",
}
# Field optional trên FoodItem (có thể None) — món thiếu số liệu này phải bị
# loại khỏi candidate cho LẦN GIẢI CÓ ràng buộc trên chính chất đó, không được
# coi None = 0 (sẽ làm sai ràng buộc, vi phạm tinh thần RULE-2/DEC-008).
_OPTIONAL_FIELDS = {"sugar_g", "purine_mg"}

GRAM_STEP = 25
MAX_GRAMS_PER_ITEM = 300
MIN_ITEMS_PER_SLOT = 1
MAX_ITEMS_PER_SLOT = 5
SOLVE_TIME_LIMIT_SECONDS = 30.0

# Bug đã audit thực tế (2026-08-07): KHÔNG có ràng buộc này, cùng một nguyên
# liệu (VD gừng) có thể được chọn MAX_GRAMS_PER_ITEM ở CẢ 4 bữa/ngày = 1200 g/
# ngày — hợp lệ về toán ràng buộc dinh dưỡng nhưng vô lý lâm sàng/ẩm thực. Trần
# này áp cho NGUYÊN LIỆU THÔ được CP-SAT tự chọn (không áp cho gram bên trong
# một món `DishCandidate` — công thức món đã là tổ hợp cố định, tự nó không bị
# lỗi "chọn lặp" này).
MAX_GRAMS_PER_FOOD_PER_DAY = 400

# Tối đa 1 món hoàn chỉnh (DishCandidate) mỗi bữa — một bữa không ăn 2 tô phở.
MAX_DISHES_PER_SLOT = 1

# CP-SAT chỉ nhận hệ số nguyên, nên giá trị/100 g phải làm tròn về bội của
# 1/VALUE_SCALE. Nhân với VALUE_SCALE rồi làm tròn CÓ HƯỚNG (xem `_try_solve`)
# để đảm bảo TOÁN HỌC rằng tổng thật (do compute_nutrition tính bằng giá trị
# CHƯA làm tròn) không bao giờ vượt ngưỡng — dù chọn VALUE_SCALE bao nhiêu.
#
# Vì sao KHÔNG dùng round() đối xứng như bản đầu: giải khả thi thuần (không hàm
# mục tiêu) đặt tổng ĐÚNG SÁT ngưỡng, nên sai số round() (±0,5/VALUE_SCALE mỗi
# món) cộng dồn qua ~20 món đẩy tổng thật vượt ngưỡng — audit độc lập tìm được
# nhiều hồ sơ bị validate_menu gắn cờ, cả min lẫn max, gồm cả hard rule (chất
# xơ, carb, chất béo, đường). Làm tròn có hướng loại hẳn lỗi này.
#
# VALUE_SCALE lớn chỉ để thu hẹp độ "thận trọng thừa" (khả năng báo vô nghiệm ở
# sát biên), không ảnh hưởng tính đúng — nên đặt đủ lớn để gần như không bỏ sót
# lời giải hợp lệ ở biên.
VALUE_SCALE = 1000

# Dải hẹp quanh điểm giữa khoảng năng lượng, dùng cho pha 1 (xem `_solve_day`).
# Mục đích: thực đơn "vừa đủ" thay vì chạm sát biên trên/dưới của khoảng cho phép.
ENERGY_AIM_BAND = 0.03

# `compute_nutrition` làm tròn mọi tổng về 2 chữ số (round(v, 2)) trước khi
# `validate_menu` so với ngưỡng. Nên hợp đồng thực tế mà optimizer phải thoả là
# giá trị ĐÃ TRÒN, không phải tổng thật. round(x, 2) lệch tối đa 0,005 so với x,
# nên siết ngưỡng vào 0,005 mỗi phía để giá trị validate nhìn thấy chắc chắn
# nằm trong ngưỡng. Không có biên này, tổng thật hợp lệ (VD chất xơ 20,4849) vẫn
# bị gắn cờ vì round→20,48 < ngưỡng 20,482 (audit độc lập bắt được ở sát biên).
SUMMARY_ROUND_MARGIN = 0.005


class CPSATMenuOptimizer:
    """Bản cài đặt `Protocol MenuGenerator` dùng OR-Tools CP-SAT.

    `feedback` (lý do lần validate trước fail) KHÔNG được dùng để điều chỉnh
    model — khác `GeminiMenuGenerator` vốn đưa lỗi cụ thể vào prompt để LLM tự
    sửa. CP-SAT tự thoả mọi ràng buộc cứng đã đưa vào ngay từ đầu, nên giải lại
    với cùng input sẽ cho ra đúng kết quả cũ; retry là vô nghĩa. Nếu
    `validate()` vẫn fail thì nguyên nhân là một ràng buộc CHƯA được mô hình
    hoá (VD tương tác thuốc — thực phẩm), và cách xử lý đúng là chuyển sang
    generator biết đọc feedback: xem `HybridMenuGenerator` trong
    `src/agents/hybrid.py`. Tham số `feedback` giữ lại để tương thích Protocol,
    không phải bị bỏ sót.

    `dishes`/`foods` là optional (mặc định None = hành vi cũ hệt trước đây,
    chỉ ghép nguyên liệu thô) — dishes cần một `FoodRepository` ĐẦY ĐỦ (không
    phải `candidates` đã bị lọc còn ~150 dòng curated) vì nguyên liệu của món
    (`dish_ingredients.csv`) phần lớn tham chiếu khối USDA bulk (id ≥
    `USDA_BULK_ID_THRESHOLD`) bị `retrieve_context` loại khỏi `candidates`.
    """

    def __init__(
        self,
        dishes: list[DishCandidate] | None = None,
        foods: FoodRepository | None = None,
    ) -> None:
        self._dishes = dishes or []
        self._foods = foods

    def generate(
        self,
        profile: PatientProfile,
        targets: ClinicalTargets,
        candidates: list[FoodItem],
        feedback: str | None,
    ) -> MenuDraft:
        eligible_dishes = _eligible_dishes(self._dishes, self._foods, profile) if self._foods else []
        return _solve_day(candidates, targets, eligible_dishes, self._foods)


def _active_nutrient_bounds(targets: ClinicalTargets) -> dict[str, tuple[float | None, float | None]]:
    """Chỉ lấy các chất có ít nhất 1 ngưỡng. Ngưỡng giữ nguyên trị cho cả ngày."""
    bounds: dict[str, tuple[float | None, float | None]] = {}
    for nutrient, target in targets.targets.items():
        field = _NUTRIENT_TO_FIELD.get(nutrient)
        if field is None:
            continue  # nutrient không map được sang cột food_items (chưa hỗ trợ)
        if target.min_value is not None or target.max_value is not None:
            bounds[field] = (target.min_value, target.max_value)
    return bounds


def _eligible_candidates(
    candidates: list[FoodItem],
    bounds: dict[str, tuple[float | None, float | None]],
) -> list[FoodItem]:
    """Loại món thiếu số liệu của chất đang bị ràng buộc (không coi None = 0)."""
    eligible = list(candidates)
    for field in bounds:
        if field in _OPTIONAL_FIELDS:
            eligible = [f for f in eligible if getattr(f, field) is not None]
    return eligible


def _narrow_energy(
    bounds: dict[str, tuple[float | None, float | None]],
) -> dict[str, tuple[float | None, float | None]] | None:
    """Bản sao `bounds` với khoảng năng lượng bị siết vào dải hẹp quanh điểm giữa.

    Trả None khi không siết được (không có ngưỡng năng lượng, hoặc chỉ có một
    phía nên không xác định được điểm giữa).
    """
    lo, hi = bounds.get("kcal_100g", (None, None))
    if lo is None or hi is None:
        return None
    mid = (lo + hi) / 2
    narrowed = dict(bounds)
    narrowed["kcal_100g"] = (
        max(lo, mid * (1 - ENERGY_AIM_BAND)),
        min(hi, mid * (1 + ENERGY_AIM_BAND)),
    )
    return narrowed


def _eligible_dishes(
    dishes: list[DishCandidate],
    foods: FoodRepository | None,
    profile: PatientProfile,
) -> list[DishCandidate]:
    """Loại món có nguyên liệu không tra được, chứa dị ứng, hoặc bị dislike.

    Không đoán thay: nguyên liệu không tra được trong `foods` → loại cả món
    (RULE-2), không coi thiếu số liệu = 0.
    """
    if foods is None or not dishes:
        return []
    eligible: list[DishCandidate] = []
    for dish in dishes:
        if dish.name_vi.strip().lower() in profile.dislikes:
            continue
        resolved = [foods.get(ing.food_id) for ing in dish.ingredients]
        if any(r is None for r in resolved):
            continue
        if any(a.lower() in profile.allergies for r in resolved for a in r.contains_allergens):  # type: ignore[union-attr]
            continue
        eligible.append(dish)
    return eligible


def _dish_nutrient_totals(
    dish: DishCandidate,
    foods: FoodRepository,
    bounds: dict[str, tuple[float | None, float | None]],
) -> dict[str, float] | None:
    """Tổng dinh dưỡng CẢ MÓN (không phải /100g) cho các field đang bị ràng buộc.

    Trả None khi một nguyên liệu thiếu số liệu của field optional đang bị ràng
    buộc (RULE-2/DEC-008, giống `_eligible_candidates`) — món đó bị loại khỏi
    lần giải có ràng buộc trên chính chất đó.
    """
    totals: dict[str, float] = dict.fromkeys(bounds, 0.0)
    for ing in dish.ingredients:
        food = foods.get(ing.food_id)
        if food is None:
            return None
        factor = ing.grams / 100.0
        for field in bounds:
            value = getattr(food, field)
            if field in _OPTIONAL_FIELDS and value is None:
                return None
            totals[field] += (value or 0.0) * factor
    return totals


def _solve_day(
    candidates: list[FoodItem],
    targets: ClinicalTargets,
    dishes: list[DishCandidate] | None = None,
    foods: FoodRepository | None = None,
) -> MenuDraft:
    """Giải cả 4 bữa trong MỘT model; ràng buộc dinh dưỡng đặt trên tổng ngày.

    Giải theo HAI PHA, cả hai đều là bài toán *khả thi* (feasibility) thuần —
    cố ý KHÔNG dùng hàm mục tiêu `Minimize`:
      1. Siết năng lượng vào dải hẹp quanh điểm giữa khoảng cho phép, để thực
         đơn "vừa đủ" thay vì chạm sát biên.
      2. Nếu pha 1 vô nghiệm (dải hẹp quá chặt với tập ứng viên hiện có) thì
         giải lại với khoảng năng lượng gốc.

    Vì sao không dùng `Minimize(|kcal − điểm giữa|)` như trực giác ban đầu: đo
    thực tế trên seed hiện tại (43 ứng viên đủ số liệu × 4 bữa) cho thấy bản
    khả thi thuần xong trong **0,1 s (OPTIMAL)**, còn bản có hàm mục tiêu chạy
    **105 s vẫn trả UNKNOWN** — tức không tìm nổi một lời giải khả thi nào, vì
    hàm mục tiêu lái tìm kiếm sang nhánh xấu. Hai pha khả thi đạt cùng ý định
    lâm sàng mà nhanh hơn ~1000 lần và tất định.
    """
    bounds = _active_nutrient_bounds(targets)
    # A bound on an optional nutrient is not solvable when the repository has
    # too few complete candidates to compose a varied day. Degrade to the
    # validator's incomplete-data warning instead of making the whole menu
    # infeasible or treating unknown values as zero.
    for field in _OPTIONAL_FIELDS:
        if field in bounds and sum(getattr(food, field) is not None for food in candidates) < len(_SLOTS):
            bounds.pop(field)
    if not bounds:
        # Không ràng buộc nào áp dụng được — không đủ căn cứ để chọn món.
        return MenuDraft()

    eligible = _eligible_candidates(candidates, bounds)
    if not eligible:
        return MenuDraft()

    # Tổng dinh dưỡng mỗi món hoàn chỉnh — tính MỘT LẦN (không đổi giữa 2 pha,
    # vì `_narrow_energy` chỉ siết khoảng kcal, không đổi tập field bị ràng buộc).
    dish_totals: list[tuple[DishCandidate, dict[str, float]]] = []
    if foods is not None:
        for dish in dishes or []:
            totals = _dish_nutrient_totals(dish, foods, bounds)
            if totals is not None:
                dish_totals.append((dish, totals))

    attempts: list[dict[str, tuple[float | None, float | None]]] = []
    narrowed = _narrow_energy(bounds)
    if narrowed is not None:
        attempts.append(narrowed)
    attempts.append(bounds)

    for attempt in attempts:
        draft = _try_solve(eligible, attempt, dish_totals)
        if draft is not None:
            return draft
    return MenuDraft()


def _try_solve(
    eligible: list[FoodItem],
    bounds: dict[str, tuple[float | None, float | None]],
    dish_totals: list[tuple[DishCandidate, dict[str, float]]] | None = None,
) -> MenuDraft | None:
    """Một lần giải khả thi. Trả None khi vô nghiệm (để caller thử pha kế tiếp)."""
    dish_totals = dish_totals or []
    model = cp_model.CpModel()
    max_units = MAX_GRAMS_PER_ITEM // GRAM_STEP

    # Biến cho từng cặp (bữa, món): số đơn vị GRAM_STEP gram + cờ có chọn không.
    units: dict[tuple[MealSlot, int], cp_model.IntVar] = {}
    chosen: dict[tuple[MealSlot, int], cp_model.BoolVarT] = {}
    for slot in _SLOTS:
        for food in eligible:
            key = (slot, food.id)
            units[key] = model.new_int_var(0, max_units, f"units_{slot.value}_{food.id}")
            chosen[key] = model.new_bool_var(f"chosen_{slot.value}_{food.id}")
            model.add(units[key] > 0).only_enforce_if(chosen[key])
            model.add(units[key] == 0).only_enforce_if(chosen[key].negated())

    # Biến cho từng cặp (bữa, món hoàn chỉnh): chọn cả món hay không — món là tổ
    # hợp nguyên liệu CỐ ĐỊNH (không stepping theo GRAM_STEP như nguyên liệu thô).
    dish_chosen: dict[tuple[MealSlot, str], cp_model.BoolVarT] = {}
    for slot in _SLOTS:
        for dish, _totals in dish_totals:
            dish_chosen[(slot, dish.dish_id)] = model.new_bool_var(f"dish_{slot.value}_{dish.dish_id}")

    # Số món mỗi bữa (nguyên liệu rời + món hoàn chỉnh cùng tính) — ràng buộc
    # DUY NHẤT còn theo bữa, để không dồn hết một chỗ.
    for slot in _SLOTS:
        in_slot = [chosen[(slot, f.id)] for f in eligible]
        in_slot += [dish_chosen[(slot, d.dish_id)] for d, _t in dish_totals]
        model.add(sum(in_slot) >= MIN_ITEMS_PER_SLOT)
        model.add(sum(in_slot) <= MAX_ITEMS_PER_SLOT)

    # Tối đa 1 món hoàn chỉnh mỗi bữa — một bữa không ăn 2 tô phở.
    for slot in _SLOTS:
        if dish_totals:
            model.add(sum(dish_chosen[(slot, d.dish_id)] for d, _t in dish_totals) <= MAX_DISHES_PER_SLOT)

    # Trần tổng gram/ngày cho MỖI nguyên liệu thô (audit 2026-08-07: thiếu ràng
    # buộc này khiến CP-SAT có thể chọn cùng 1 nguyên liệu ở cả 4 bữa, VD gừng
    # 300g×4 = 1200g/ngày — hợp lệ về toán nhưng vô lý lâm sàng/ẩm thực). KHÔNG
    # áp cho gram bên trong món hoàn chỉnh — công thức món đã là tổ hợp cố định.
    max_food_units_per_day = MAX_GRAMS_PER_FOOD_PER_DAY // GRAM_STEP
    for food in eligible:
        model.add(sum(units[(slot, food.id)] for slot in _SLOTS) <= max_food_units_per_day)

    # Ràng buộc dinh dưỡng trên TỔNG cả ngày.
    # Tổng thật = Σ gram × (giá trị/100 g) / 100. Nhân cả hai vế với
    # 100 × VALUE_SCALE để mọi hệ số là số nguyên.
    #
    # LÀM TRÒN CÓ HƯỚNG để tổng THẬT được đảm bảo nằm trong ngưỡng:
    #   - Ngưỡng MAX: dùng hệ số ceil (mô hình ước lượng TỔNG CAO hơn thật) và
    #     ngưỡng floor. Model ép tổng-ước-lượng ≤ ngưỡng ⇒ tổng thật ≤ ngưỡng.
    #   - Ngưỡng MIN: dùng hệ số floor (mô hình ước lượng TỔNG THẤP hơn thật) và
    #     ngưỡng ceil. Model ép tổng-ước-lượng ≥ ngưỡng ⇒ tổng thật ≥ ngưỡng.
    # Ngưỡng còn siết thêm SUMMARY_ROUND_MARGIN để bù việc compute_nutrition làm
    # tròn tổng về 2 chữ số. Nutrient có cả min lẫn max (carb, kcal) cần hai biểu
    # thức riêng vì hai hướng làm tròn khác nhau.
    #
    # Món hoàn chỉnh đóng góp CẢ TỔNG (không nhân gram/GRAM_STEP như nguyên
    # liệu thô) vì `dish_chosen` là biến 0/1 trên toàn bộ công thức món.
    scale = 100 * VALUE_SCALE
    for field, (lo, hi) in bounds.items():
        if hi is not None:
            total_ceil = sum(
                units[(slot, f.id)] * GRAM_STEP * math.ceil(getattr(f, field) * VALUE_SCALE)
                for slot in _SLOTS
                for f in eligible
            )
            total_ceil += sum(
                dish_chosen[(slot, d.dish_id)] * math.ceil(totals[field] * scale)
                for slot in _SLOTS
                for d, totals in dish_totals
            )
            model.add(total_ceil <= math.floor((hi - SUMMARY_ROUND_MARGIN) * scale))
        if lo is not None:
            total_floor = sum(
                units[(slot, f.id)] * GRAM_STEP * math.floor(getattr(f, field) * VALUE_SCALE)
                for slot in _SLOTS
                for f in eligible
            )
            total_floor += sum(
                dish_chosen[(slot, d.dish_id)] * math.floor(totals[field] * scale)
                for slot in _SLOTS
                for d, totals in dish_totals
            )
            model.add(total_floor >= math.ceil((lo + SUMMARY_ROUND_MARGIN) * scale))

    solver = cp_model.CpSolver()
    # Bài toán nhỏ nên việc TÌM LỜI GIẢI gần như tức thì (deterministic_time đo
    # được chỉ ~0,003 s). Nhưng lần đầu native library của OR-Tools (~24 MB)
    # được nạp vào tiến trình tốn cỡ 8 s cố định, không liên quan tới độ khó bài
    # toán — nên cần trần thời gian đủ rộng để không bị cắt giữa chừng
    # (production giữ process sống lâu, không trả giá nạp thư viện mỗi lần giải).
    solver.parameters.max_time_in_seconds = SOLVE_TIME_LIMIT_SECONDS
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        logger.info(
            "CPSATMenuOptimizer: không tìm được thực đơn khả thi (status=%s)",
            solver.StatusName(status),
        )
        return None

    items: dict[MealSlot, list[MenuItem]] = {}
    planned_dishes: dict[MealSlot, list[PlannedDish]] = {}
    for slot in _SLOTS:
        # gram theo food_id — gộp nguyên liệu thô + nguyên liệu bên trong món
        # hoàn chỉnh cùng food_id (hiếm nhưng có thể xảy ra) thành một dòng.
        grams_by_food: dict[int, float] = {}
        for f in eligible:
            g = solver.Value(units[(slot, f.id)]) * GRAM_STEP
            if g > 0:
                grams_by_food[f.id] = grams_by_food.get(f.id, 0.0) + g
        for dish, _totals in dish_totals:
            if solver.Value(dish_chosen[(slot, dish.dish_id)]):
                planned_dishes.setdefault(slot, []).append(
                    PlannedDish(dish_id=dish.dish_id, serving_grams=sum(ingredient.grams for ingredient in dish.ingredients))
                )
                for ing in dish.ingredients:
                    grams_by_food[ing.food_id] = grams_by_food.get(ing.food_id, 0.0) + ing.grams
        if grams_by_food:
            items[slot] = [MenuItem(food_id=fid, grams=g) for fid, g in grams_by_food.items()]
    return MenuDraft(items=items, planned_dishes=planned_dishes)
