"""Bounds checker — guardrail tầng 3.

LLM: NO — deterministic.
Ticket: CLN-04

Nguyên tắc FAIL CLOSED (RULE R00.2): nghi ngờ thì chặn.
  - Vi phạm `hard` → chặn phát hành, agent phải sinh lại.
  - Vi phạm `soft` → cho qua nhưng ghi cảnh báo cho chuyên gia xem khi duyệt.

Năng lượng có quy tắc riêng: lệch > 10% là soft, lệch > 25% là hard.
"""

from __future__ import annotations

from .models import ClinicalTargets, NutritionSummary, Severity, Violation
from .rules import ENERGY_HARD_TOLERANCE, ENERGY_SOFT_TOLERANCE, ClinicalRule

NUTRIENT_LABELS_VI: dict[str, str] = {
    "kcal": "Năng lượng",
    "protein_g": "Chất đạm",
    "carb_g": "Tinh bột",
    "fat_g": "Chất béo",
    "fiber_g": "Chất xơ",
    "na_mg": "Natri (muối)",
    "k_mg": "Kali",
    "p_mg": "Phospho",
    "purine_mg": "Purin",
    "sugar_g": "Đường",
}

SUGGESTIONS_VI: dict[tuple[str, str], str] = {
    ("na_mg", "over"): (
        "Bỏ bát nước chấm dọn kèm, giảm một nửa lượng nước mắm/bột canh khi nêm, "
        "và chỉ ăn cái không húp nước canh/nước dùng."
    ),
    ("k_mg", "over"): (
        "Giảm rau lá xanh đậm và quả giàu kali (chuối, bơ, nước dừa). "
        "Rau củ nên chần qua nước sôi rồi đổ nước để giảm kali."
    ),
    ("p_mg", "over"): "Giảm nội tạng, phô mai, đậu hạt và nước ngọt có ga (chứa phụ gia phospho).",
    ("protein_g", "over"): "Giảm khẩu phần thịt/cá xuống khoảng 2/3 và bỏ phần đạm ở bữa phụ.",
    ("protein_g", "under"): "Thêm một nguồn đạm giá trị sinh học cao (trứng, cá, đậu phụ).",
    ("purine_mg", "over"): "Bỏ nội tạng, hải sản vỏ cứng và nước dùng hầm xương.",
    ("fiber_g", "under"): "Thêm rau xanh, đậu đỗ và ngũ cốc nguyên hạt vào bữa chính.",
    ("carb_g", "over"): "Giảm khoảng nửa bát cơm ở bữa tối, thay bằng rau.",
    ("sugar_g", "over"): (
        "Giảm đồ ngọt, nước ngọt, sữa đặc và chè; ưu tiên trái cây tươi ít ngọt "
        "thay cho đường tự do."
    ),
    ("kcal", "over"): "Giảm dầu mỡ khi chế biến và giảm khẩu phần tinh bột.",
    ("kcal", "under"): "Tăng khẩu phần tinh bột phức hợp hoặc thêm một bữa phụ.",
}


def _energy_severity(actual: float, bound: float, kind: str) -> Severity:
    """Mức độ vi phạm năng lượng, tính so với ĐỊNH MỨC GỐC chứ không so với biên.

    Định mức gốc E được suy ngược từ biên (biên = E * (1 ± 10%)).
    Lệch quá ±25% so với E là vi phạm cứng.
    """
    if kind == "over":
        base = bound / (1 + ENERGY_SOFT_TOLERANCE)
        return Severity.HARD if actual > base * (1 + ENERGY_HARD_TOLERANCE) else Severity.SOFT
    base = bound / (1 - ENERGY_SOFT_TOLERANCE)
    return Severity.HARD if actual < base * (1 - ENERGY_HARD_TOLERANCE) else Severity.SOFT


def _severity_for_rules(nutrient: str, rule_ids: list[str], all_rules: list[ClinicalRule] | None) -> Severity:
    """Mức độ của vi phạm lấy theo rule nghiêm ngặt nhất đã tạo ra ngưỡng đó."""
    if not all_rules:
        return Severity.HARD
    by_id = {r.rule_id: r for r in all_rules}
    for rid in rule_ids:
        rule = by_id.get(rid)
        if rule and rule.nutrient == nutrient and rule.severity == "hard":
            return Severity.HARD
    return Severity.SOFT


def validate_menu(
    nutrition: NutritionSummary,
    targets: ClinicalTargets,
    all_rules: list[ClinicalRule] | None = None,
) -> list[Violation]:
    violations: list[Violation] = []

    for nutrient, target in targets.targets.items():
        actual = nutrition.value_of(nutrient)
        label = NUTRIENT_LABELS_VI.get(nutrient, nutrient)

        if target.max_value is not None and actual > target.max_value:
            over = actual - target.max_value
            if nutrient == "kcal":
                severity = _energy_severity(actual, target.max_value, "over")
            else:
                severity = _severity_for_rules(nutrient, target.rule_ids, all_rules)
            violations.append(
                Violation(
                    nutrient=nutrient,
                    actual=round(actual, 1),
                    limit=round(target.max_value, 1),
                    unit=target.unit,
                    kind="over",
                    severity=severity,
                    message_vi=(
                        f"{label} vượt ngưỡng: {actual:.0f} {target.unit} "
                        f"(tối đa {target.max_value:.0f} {target.unit}, vượt {over:.0f})."
                    ),
                    suggestion=SUGGESTIONS_VI.get((nutrient, "over")),
                    rule_id=target.rule_ids[0] if target.rule_ids else None,
                )
            )

        if target.min_value is not None and actual < target.min_value:
            short = target.min_value - actual
            if nutrient == "kcal":
                severity = _energy_severity(actual, target.min_value, "under")
            else:
                severity = _severity_for_rules(nutrient, target.rule_ids, all_rules)
            violations.append(
                Violation(
                    nutrient=nutrient,
                    actual=round(actual, 1),
                    limit=round(target.min_value, 1),
                    unit=target.unit,
                    kind="under",
                    severity=severity,
                    message_vi=(
                        f"{label} thấp hơn mức tối thiểu: {actual:.0f} {target.unit} "
                        f"(tối thiểu {target.min_value:.0f} {target.unit}, thiếu {short:.0f})."
                    ),
                    suggestion=SUGGESTIONS_VI.get((nutrient, "under")),
                    rule_id=target.rule_ids[0] if target.rule_ids else None,
                )
            )

    # Có ngưỡng đường nhưng tổng đường thiếu số liệu → tổng bị thấp hơn thực tế,
    # không được coi việc "chưa vượt trần" là đạt. Cảnh báo mềm để chuyên gia biết.
    sugar_target = targets.targets.get("sugar_g")
    if sugar_target is not None and not nutrition.sugar_is_complete:
        violations.append(
            Violation(
                nutrient="sugar_g",
                actual=round(nutrition.sugar_g, 1),
                limit=round(sugar_target.max_value, 1) if sugar_target.max_value is not None else 0.0,
                unit=sugar_target.unit,
                kind="incomplete_data",
                severity=Severity.SOFT,
                message_vi=(
                    "Không đủ số liệu đường: một số món chưa có giá trị đường nên tổng "
                    f"đường ({nutrition.sugar_g:.0f} {sugar_target.unit}) đang THẤP hơn thực tế. "
                    "Không thể kết luận đạt ngưỡng đường tự do — cần bổ sung số liệu."
                ),
                suggestion="Bổ sung cột sugar_g cho các món còn thiếu trong CSDL thực phẩm.",
                rule_id=sugar_target.rule_ids[0] if sugar_target.rule_ids else None,
            )
        )

    return violations


def has_blocking(violations: list[Violation]) -> bool:
    return any(v.blocking for v in violations)


def build_feedback(violations: list[Violation], nutrition: NutritionSummary) -> str:
    """Sinh feedback CỤ THỂ cho lần regenerate kế tiếp.

    RULE R20.3: retry mà không nói rõ lỗi gì thì chỉ là cầu may.
    """
    if not violations:
        return ""

    lines = ["Bản thực đơn trước không đạt. Các vi phạm cụ thể:"]
    for v in sorted(violations, key=lambda x: (x.severity is not Severity.HARD, x.nutrient)):
        tag = "[CHẶN]" if v.blocking else "[cảnh báo]"
        lines.append(f"- {tag} {v.message_vi}")
        if v.suggestion:
            lines.append(f"  Hướng xử lý: {v.suggestion}")

    top = sorted(nutrition.sources, key=lambda s: s.grams, reverse=True)[:3]
    if top:
        lines.append(
            "Các món chiếm khối lượng lớn nhất: " + ", ".join(f"{s.name} ({s.grams:.0f} g)" for s in top) + "."
        )
    lines.append("Hãy giữ cấu trúc bữa ăn nhưng điều chỉnh đúng các điểm nêu trên.")
    return "\n".join(lines)
