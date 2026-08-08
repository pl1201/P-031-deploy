"""Tổng hợp nhật ký ăn uống một ngày + kết luận có kiểm soát — BE-07.

LLM: **NO** (module nằm trong `src/clinical/`, có test `DETERMINISTIC_FILES`).

Bài toán riêng của nhật ký so với thực đơn
------------------------------------------
Thực đơn do hệ thống sinh ra nên mọi món đều tra được. Nhật ký thì không: bệnh
nhân ăn gì thì ghi nấy, mà kho chỉ có 461 thực phẩm Việt — **món chưa tra được
là mặc định, không phải ngoại lệ**. Nên tổng dinh dưỡng ngày gần như luôn là
một **tổng thiếu**.

Nguyên lý bất đối xứng kết luận
-------------------------------
Nếu còn món chưa tra được, con số tính ra là **cận dưới** của sự thật:

* Cận dưới **đã vượt trần** → "ĐÃ VƯỢT" là kết luận hợp lệ về logic (ăn thêm
  chỉ làm vượt nhiều hơn). Cảnh báo bình thường.
* Cận dưới **chưa vượt trần** → **CẤM** kết luận "đạt". Phần chưa tra được có
  thể đủ để vượt.
* Ngưỡng `min` thì ngược lại: cận dưới **đã đạt min** → kết luận được; **chưa
  đạt min** → cấm kết luận "thiếu".

Nhờ vậy vẫn cảnh báo được khi dữ liệu khuyết mà **không bịa một con số nào** —
giữ nguyên RULE-2 và DEC-008. Đây là tổng quát hoá của `sugar_is_complete` /
`purine_is_complete` đã có sẵn trong `validator.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .models import (
    ClinicalTargets,
    MealSlot,
    MenuDraft,
    MenuItem,
    NutritionSummary,
    Severity,
    Violation,
)
from .nutrition import FoodRepository, compute_nutrition
from .rules import ClinicalRule
from .validator import NUTRIENT_LABELS_VI, validate_menu


@dataclass(frozen=True)
class LoggedFood:
    """Một dòng nhật ký, đã tách khỏi tầng DB để `clinical/` không phụ thuộc ORM.

    `food_id is None` nghĩa là chưa tra được (OOV) — khi đó `grams` có thể cũng
    None nếu người dùng không mô tả được khẩu phần.
    """

    log_id: str
    food_id: int | None
    grams: float | None
    free_text_vi: str | None = None
    slot: MealSlot = MealSlot.LUNCH


class Verdict(str, Enum):
    """Kết luận cho MỘT chất trong ngày."""

    EXCEEDED = "exceeded"  # đã vượt trần — kết luận được kể cả khi thiếu dữ liệu
    BELOW_MIN = "below_min"  # chưa đạt tối thiểu — chỉ kết luận khi dữ liệu đủ
    WITHIN = "within"  # trong ngưỡng — chỉ kết luận khi dữ liệu đủ
    INSUFFICIENT_DATA = "insufficient_data"  # KHÔNG kết luận được


@dataclass(frozen=True)
class NutrientVerdict:
    nutrient: str
    label_vi: str
    verdict: Verdict
    counted: float | None  # tổng tính được từ phần ĐÃ tra được; None nếu không có gì
    min_value: float | None
    max_value: float | None
    unit: str | None


@dataclass
class DaySummary:
    """Kết quả tổng hợp một ngày.

    `nutrition` chỉ cộng phần đã tra được — **không bao giờ** ước lượng phần
    thiếu. `unmatched` giữ nguyên chữ người dùng gõ để chuyên gia xử lý.
    """

    nutrition: NutritionSummary | None
    verdicts: list[NutrientVerdict] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)
    matched_count: int = 0
    unmatched_count: int = 0
    unmatched: list[LoggedFood] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return self.matched_count + self.unmatched_count

    @property
    def coverage(self) -> float:
        """Tỉ lệ món tra được. 1.0 = đủ dữ liệu để kết luận cả hai chiều."""
        return self.matched_count / self.total_count if self.total_count else 0.0

    @property
    def is_complete(self) -> bool:
        return self.unmatched_count == 0 and self.total_count > 0


def _unmatched_violation(log: LoggedFood) -> Violation:
    """Cảnh báo cho món chưa tra được — CỐ Ý không có `actual`/`limit`.

    Không có số thì để None; nhồi 0.0 vào sẽ hiển thị "0 mg" y như một số đo
    thật (xem docstring `Violation`).
    """
    ten = (log.free_text_vi or "").strip() or "món không rõ tên"
    return Violation(
        nutrient="__unmatched__",
        kind="unmatched_food",
        severity=Severity.SOFT,
        message_vi=(
            f"Chưa tra được '{ten}' trong cơ sở dữ liệu nên KHÔNG tính vào tổng ngày. "
            f"Tổng dưới đây là mức tối thiểu, thực tế có thể cao hơn."
        ),
        suggestion="Chuyên gia dinh dưỡng sẽ đối chiếu và bổ sung món này.",
        evidence=ten,
        food_log_id=log.log_id,
    )


def summarize_day(
    logs: list[LoggedFood],
    targets: ClinicalTargets,
    repo: FoodRepository,
    all_rules: list[ClinicalRule] | None = None,
) -> DaySummary:
    """Tổng hợp một ngày nhật ký thành số + kết luận có kiểm soát.

    Tái dùng nguyên si `compute_nutrition()` và `validate_menu()` — nhật ký và
    thực đơn phải dùng CÙNG một bộ ngưỡng và cùng một cách tính, nếu không
    bệnh nhân sẽ thấy hai con số khác nhau cho cùng một bữa ăn.
    """
    matched = [x for x in logs if x.food_id is not None and x.grams is not None]
    # Món tra được tên nhưng không rõ khẩu phần vẫn là "chưa đủ dữ liệu": biết
    # ăn gì mà không biết bao nhiêu thì không cộng được.
    unmatched = [x for x in logs if x.food_id is None or x.grams is None]

    summary = DaySummary(
        nutrition=None,
        matched_count=len(matched),
        unmatched_count=len(unmatched),
        unmatched=unmatched,
    )
    summary.violations.extend(_unmatched_violation(x) for x in unmatched)

    if not matched:
        summary.verdicts = [
            NutrientVerdict(
                nutrient=n,
                label_vi=NUTRIENT_LABELS_VI.get(n, n),
                verdict=Verdict.INSUFFICIENT_DATA,
                counted=None,
                min_value=t.min_value,
                max_value=t.max_value,
                unit=t.unit,
            )
            for n, t in targets.targets.items()
        ]
        return summary

    items: dict[MealSlot, list[MenuItem]] = {}
    for log in matched:
        assert log.food_id is not None and log.grams is not None  # đã lọc ở trên
        items.setdefault(log.slot, []).append(MenuItem(food_id=log.food_id, grams=log.grams))

    nutrition = compute_nutrition(MenuDraft(items=items), repo)
    summary.nutrition = nutrition

    du_lieu_du = summary.is_complete
    raw_violations = validate_menu(nutrition, targets, all_rules)

    # Lọc theo nguyên lý bất đối xứng: khi dữ liệu chưa đủ, vi phạm "under"
    # KHÔNG còn giá trị kết luận (phần chưa tra được có thể bù đủ), nhưng vi
    # phạm "over" thì vẫn đúng.
    for v in raw_violations:
        if not du_lieu_du and v.kind == "under":
            continue
        summary.violations.append(v)

    summary.verdicts = _build_verdicts(nutrition, targets, du_lieu_du)
    return summary


def _build_verdicts(
    nutrition: NutritionSummary,
    targets: ClinicalTargets,
    du_lieu_du: bool,
) -> list[NutrientVerdict]:
    out: list[NutrientVerdict] = []
    for nutrient, target in targets.targets.items():
        counted = nutrition.value_of(nutrient)

        if target.max_value is not None and counted > target.max_value:
            # Cận dưới đã vượt trần ⇒ kết luận hợp lệ dù thiếu dữ liệu.
            verdict = Verdict.EXCEEDED
        elif du_lieu_du and target.min_value is not None and counted < target.min_value:
            verdict = Verdict.BELOW_MIN
        elif du_lieu_du:
            verdict = Verdict.WITHIN
        else:
            # Chưa vượt trần NHƯNG còn món chưa tra được ⇒ KHÔNG kết luận "đạt".
            verdict = Verdict.INSUFFICIENT_DATA

        out.append(
            NutrientVerdict(
                nutrient=nutrient,
                label_vi=NUTRIENT_LABELS_VI.get(nutrient, nutrient),
                verdict=verdict,
                counted=round(counted, 1),
                min_value=target.min_value,
                max_value=target.max_value,
                unit=target.unit,
            )
        )
    return out
