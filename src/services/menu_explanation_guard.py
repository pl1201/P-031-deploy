"""Chặn bịa số cho lớp Explainer & Coaching — tất định, không LLM.

RULE-1/RULE-2 ở tầng service: `src/services/menu_coach.py` cấm LLM thêm số
qua system prompt, nhưng prompt suông không đủ tin cậy (LLM vẫn có thể bịa).
Module này là lớp chặn cứng SAU khi LLM sinh văn bản: mọi chuỗi số xuất hiện
trong văn bản phải khớp với một con số đã có sẵn trong `MenuFacts` — số nào
không khớp bị coi là bịa, và caller phải dùng bản render mẫu (template)
thay vì phục vụ văn bản đó cho người dùng.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from src.clinical.menu_explainer import MenuFacts

_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")


class GuardResult(BaseModel):
    ok: bool
    ungrounded_numbers: list[str] = Field(default_factory=list)


def extract_digit_sequences(text: str) -> set[str]:
    """Chuẩn hoá dấu thập phân (`,`/`.`) để '1,5' và '1.5' coi là cùng 1 số."""
    return {m.replace(",", ".") for m in _NUMBER_RE.findall(text)}


def _allowed_numbers(facts: MenuFacts) -> set[str]:
    allowed: set[str] = set()

    # Ngày trong `facts.plan_date` (VD "2026-08-12") là dữ kiện thật, không phải
    # số bịa — văn bản tự nhiên (mẫu render hay LLM) hay nhắc lại ngày. Không
    # thêm riêng thì mọi văn bản nói tới ngày đều bị guard chặn nhầm (phát hiện
    # khi AGT-13 lần đầu gọi guard với văn bản thật, không phải chuỗi tay
    # trong test cũ vốn không nhắc ngày).
    for part in facts.plan_date.replace("/", "-").split("-"):
        part = part.strip()
        if part:
            allowed.add(part)  # dạng có số 0 đứng đầu, VD "08"
            allowed.add(part.lstrip("0") or "0")  # dạng đã bỏ số 0 đứng đầu, VD "8"

    def _add(value: float | int | None) -> None:
        if value is None:
            return
        allowed.add(str(value).replace(",", "."))
        # Cho phép cả dạng làm tròn số nguyên khi giá trị gốc là số thực
        # (VD 450.0 gram thường được viết là "450" trong văn xuôi).
        if float(value).is_integer():
            allowed.add(str(int(value)))
        else:
            allowed.add(f"{float(value):.1f}")
            allowed.add(f"{float(value):.0f}")

    for item in facts.items:
        _add(item.grams)

    for nutrient in facts.nutrients:
        _add(nutrient.value)
        _add(nutrient.min_value)
        _add(nutrient.max_value)

    # Số lượng món/bữa là điều LLM có thể tự đếm từ input mà không phải bịa.
    allowed.add(str(len(facts.items)))

    return allowed


def check_grounded(text_vi: str, facts: MenuFacts) -> GuardResult:
    """Trả `ok=False` nếu văn bản chứa số không xuất hiện trong `MenuFacts`."""
    found = extract_digit_sequences(text_vi)
    allowed = _allowed_numbers(facts)
    ungrounded = sorted(found - allowed)
    return GuardResult(ok=not ungrounded, ungrounded_numbers=ungrounded)
