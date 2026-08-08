"""Giải thích ngưỡng dinh dưỡng đã tính — trợ lý ngưỡng cho chuyên gia (P1).

LLM: NO. Module này tự nó đã trả lời "vì sao ngưỡng chất X là Y" một cách
chính xác 100%, không cần LLM — mọi dữ kiện đã có sẵn trong `ClinicalTargets`
(do `compute_targets()` sinh ra) và `list[ClinicalRule]` (nạp từ CSV). Đây là
lớp tất định; lớp diễn đạt tự nhiên bằng LLM (chỉ văn phong hoá, không thêm
dữ kiện) nằm ở `src/services/target_assistant.py`.

Vì sao đáng làm: `applied_rule_ids` + `guideline_refs` + `conflict_notes` đã
tồn tại trong `ClinicalTargets` từ trước nhưng chưa ai từng render nó thành
câu trả lời "vì sao" cho chuyên gia — đây thuần tuý là lắp ráp lại dữ kiện đã
có, không tính toán gì mới, nên không có rủi ro sai số hay ảo giác.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .energy import adjusted_body_weight_kg, compute_energy_target_kcal
from .models import ClinicalTargets, PatientProfile
from .rules import ClinicalRule, _select_rules  # noqa: PLC2701 — tái dùng logic chọn rule, tránh chép lại 2 nơi
from .validator import NUTRIENT_LABELS_VI


class AppliedRuleExplanation(BaseModel):
    """Một rule đã THẮNG và góp phần tạo nên ngưỡng cuối cùng của một chất."""

    rule_id: str
    guideline_ref: str
    guideline_grade: str = ""
    bound: str  # "max" | "min"
    resolved_value: float
    unit: str


class ExcludedRuleExplanation(BaseModel):
    """Một rule ĐÁNG LẼ áp dụng nhưng bị loại — và vì sao.

    Đây thường là câu trả lời thật sự chuyên gia cần: không phải "ngưỡng là
    bao nhiêu" mà là "vì sao KHÔNG phải theo ADA mà lại theo KDIGO".
    """

    rule_id: str
    guideline_ref: str
    reason: str


class NutrientExplanation(BaseModel):
    nutrient: str
    label_vi: str
    min_value: float | None
    max_value: float | None
    unit: str | None
    applied: list[AppliedRuleExplanation] = Field(default_factory=list)
    excluded: list[ExcludedRuleExplanation] = Field(default_factory=list)
    conflict_notes: list[str] = Field(default_factory=list)


class NutrientDiff(BaseModel):
    """Khác biệt ngưỡng một chất giữa 2 lần tính — dùng cho luồng what-if."""

    nutrient: str
    label_vi: str
    before_min: float | None
    before_max: float | None
    after_min: float | None
    after_max: float | None
    changed: bool


def explain_targets(
    profile: PatientProfile,
    targets: ClinicalTargets,
    rules: list[ClinicalRule],
) -> list[NutrientExplanation]:
    """Với mỗi chất trong `targets`, liệt kê rule nào thắng, rule nào bị loại và vì sao."""
    weight = adjusted_body_weight_kg(profile.weight_kg, profile.height_cm)
    energy = compute_energy_target_kcal(profile)
    by_id = {r.rule_id: r for r in rules}

    selected, disabled = _select_rules(profile, rules)
    selected_ids = {r.rule_id for r in selected}
    disabled_ids = {r.rule_id for r in disabled}

    # Xây lại đúng tập "candidates" mà _select_rules dùng ở bước đầu (BASE +
    # rule khớp bệnh lý/giai đoạn), để suy ra rule nào bị loại và VÌ SAO —
    # _select_rules không trả riêng danh sách này nên phải tự tính lại.
    #
    # QUAN TRỌNG: _select_rules loại một rule khỏi `selected` vì MỘT TRONG HAI
    # lý do khác nhau — `not not_overridden(rule) or not flag_required_met(rule)`
    # — nên không được gộp chung thành "bị overridden". Bug thật đã bắt được khi
    # thử trên dữ liệu thật: T2DM-PRO-02 (`requires_flag=elderly`) bị loại vì
    # bệnh nhân 60 tuổi (<65) chưa đủ tuổi, KHÔNG phải vì bị CKD ghi đè — nếu
    # gộp chung sẽ in ra "Bị  thay thế" (rỗng, overridden_by của rule này rỗng).
    patient_conditions = {c.code.value for c in profile.conditions}
    flags = profile.clinical_flags
    candidates = [r for r in rules if r.condition_code == "BASE"]
    for cond in profile.conditions:
        candidates += [r for r in rules if r.applies_to(cond.code.value, cond.stage)]
    overridden_out: list[ClinicalRule] = []
    flag_unmet_out: list[ClinicalRule] = []
    for rule in candidates:
        if rule.rule_id in selected_ids or rule.rule_id in disabled_ids:
            continue
        if set(rule.overridden_by) & patient_conditions:
            overridden_out.append(rule)
        elif rule.requires_flag and not (set(rule.requires_flag) & flags):
            flag_unmet_out.append(rule)
        # Còn lại (không rơi vào 2 nhóm trên) là ca không nên xảy ra theo logic
        # hiện tại của `_select_rules` — bỏ qua thay vì báo sai lý do.

    explanations: list[NutrientExplanation] = []
    for nutrient, t in targets.targets.items():
        applied: list[AppliedRuleExplanation] = []
        for rid in t.rule_ids:
            rule = by_id.get(rid)
            if rule is None:
                if rid == "ENERGY-WHO-FAO-UNU":
                    applied.append(
                        AppliedRuleExplanation(
                            rule_id=rid,
                            guideline_ref=t.guideline_refs[0] if t.guideline_refs else "",
                            bound="range",
                            resolved_value=round(energy, 1),
                            unit="kcal",
                        )
                    )
                continue
            applied.append(
                AppliedRuleExplanation(
                    rule_id=rule.rule_id,
                    guideline_ref=rule.guideline_ref,
                    guideline_grade=rule.guideline_grade,
                    bound=rule.bound,
                    resolved_value=round(rule.resolve(weight_kg=weight, energy_kcal=energy), 2),
                    unit=rule.unit_for_target(),
                )
            )

        excluded: list[ExcludedRuleExplanation] = []
        for rule in overridden_out:
            if rule.nutrient != nutrient:
                continue
            excluded.append(
                ExcludedRuleExplanation(
                    rule_id=rule.rule_id,
                    guideline_ref=rule.guideline_ref,
                    reason=f"Bị {'/'.join(rule.overridden_by)} thay thế — guideline khác được ưu tiên hơn khi có bệnh lý này.",
                )
            )
        for rule in flag_unmet_out:
            if rule.nutrient != nutrient:
                continue
            excluded.append(
                ExcludedRuleExplanation(
                    rule_id=rule.rule_id,
                    guideline_ref=rule.guideline_ref,
                    reason=f"Chưa áp dụng — cần cờ {'/'.join(rule.requires_flag)} mà hồ sơ hiện chưa có.",
                )
            )
        for rule in disabled:
            if rule.nutrient != nutrient:
                continue
            excluded.append(
                ExcludedRuleExplanation(
                    rule_id=rule.rule_id,
                    guideline_ref=rule.guideline_ref,
                    reason=f"Vô hiệu do cờ an toàn: {'/'.join(rule.disabled_by_flag)}.",
                )
            )

        conflict_notes = [note for note in targets.conflict_notes if note.startswith(f"{nutrient}:")]

        explanations.append(
            NutrientExplanation(
                nutrient=nutrient,
                label_vi=NUTRIENT_LABELS_VI.get(nutrient, nutrient),
                min_value=t.min_value,
                max_value=t.max_value,
                unit=t.unit,
                applied=applied,
                excluded=excluded,
                conflict_notes=conflict_notes,
            )
        )
    return explanations


def diff_explanations(
    before: list[NutrientExplanation],
    after: list[NutrientExplanation],
) -> list[NutrientDiff]:
    """So sánh 2 lần giải thích — dùng cho what-if ("nếu CKD sang G4 thì sao")."""
    by_nutrient_before = {e.nutrient: e for e in before}
    by_nutrient_after = {e.nutrient: e for e in after}
    all_nutrients = sorted(set(by_nutrient_before) | set(by_nutrient_after))

    diffs: list[NutrientDiff] = []
    for nutrient in all_nutrients:
        b = by_nutrient_before.get(nutrient)
        a = by_nutrient_after.get(nutrient)
        b_min, b_max = (b.min_value, b.max_value) if b else (None, None)
        a_min, a_max = (a.min_value, a.max_value) if a else (None, None)
        diffs.append(
            NutrientDiff(
                nutrient=nutrient,
                label_vi=(a or b).label_vi if (a or b) else nutrient,
                before_min=b_min,
                before_max=b_max,
                after_min=a_min,
                after_max=a_max,
                changed=(b_min, b_max) != (a_min, a_max),
            )
        )
    return diffs
