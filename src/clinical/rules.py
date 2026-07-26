"""Nạp và áp dụng quy tắc lâm sàng.

LLM: NO — deterministic.
Ticket: CLN-02, CLN-03

Nguyên tắc (RULE R10.4): ngưỡng KHÔNG BAO GIỜ hardcode trong code hay prompt.
Nguồn duy nhất là `data/seeds/clinical_rules.csv` → bảng `clinical_rules`.

Nguyên tắc (RULE R10.5): đa bệnh lý luôn lấy ngưỡng NGHIÊM NGẶT hơn.
  - Giới hạn trên (max) → lấy min(các ngưỡng)
  - Giới hạn dưới (min) → lấy max(các ngưỡng)
  - Nếu min > max sau khi hợp nhất → KHÔNG tự quyết, gắn cờ needs_expert_review.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .energy import adjusted_body_weight_kg, compute_bmr, compute_energy_target_kcal, compute_tdee
from .models import ClinicalTargets, NutrientTarget, PatientProfile

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[2] / "data" / "seeds" / "clinical_rules.csv"

# Hệ số quy đổi năng lượng cho basis = pct_energy
KCAL_PER_GRAM: dict[str, float] = {"protein_g": 4.0, "carb_g": 4.0, "fat_g": 9.0}

# Dung sai năng lượng so với định mức
ENERGY_SOFT_TOLERANCE = 0.10
ENERGY_HARD_TOLERANCE = 0.25

Bound = Literal["max", "min"]
Basis = Literal["absolute", "per_kg", "pct_energy", "per_1000kcal"]


@dataclass(frozen=True)
class ClinicalRule:
    rule_id: str
    condition_code: str
    stages: tuple[str, ...]
    nutrient: str
    bound: Bound
    value: float
    unit: str
    basis: Basis
    severity: str
    guideline_ref: str
    overridden_by: tuple[str, ...] = ()

    def applies_to(self, condition_code: str, stage: str | None) -> bool:
        if self.condition_code != condition_code:
            return False
        if not self.stages:
            return True
        return stage is not None and stage in self.stages

    def unit_for_target(self) -> str:
        """Đơn vị hiển thị sau khi quy đổi ngưỡng về giá trị tuyệt đối/ngày."""
        if self.basis in ("per_kg", "pct_energy", "per_1000kcal"):
            return "g" if self.nutrient.endswith("_g") else "mg"
        return self.unit

    def resolve(self, weight_kg: float, energy_kcal: float) -> float:
        """Quy đổi ngưỡng tương đối thành giá trị tuyệt đối theo ngày."""
        if self.basis == "absolute":
            return self.value
        if self.basis == "per_kg":
            return self.value * weight_kg
        if self.basis == "per_1000kcal":
            return self.value * energy_kcal / 1000.0
        if self.basis == "pct_energy":
            kcal_g = KCAL_PER_GRAM.get(self.nutrient)
            if kcal_g is None:
                raise ValueError(f"Rule {self.rule_id}: basis=pct_energy không áp dụng cho {self.nutrient}")
            return energy_kcal * (self.value / 100.0) / kcal_g
        raise ValueError(f"Rule {self.rule_id}: basis không hợp lệ: {self.basis}")


def load_rules(path: Path | None = None) -> list[ClinicalRule]:
    path = path or DEFAULT_RULES_PATH
    rules: list[ClinicalRule] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("rule_id"):
                continue
            stages = tuple(s.strip() for s in (row["stages"] or "").split(",") if s.strip())
            rules.append(
                ClinicalRule(
                    rule_id=row["rule_id"].strip(),
                    condition_code=row["condition_code"].strip(),
                    stages=stages,
                    nutrient=row["nutrient"].strip(),
                    bound=row["bound"].strip(),  # type: ignore[arg-type]
                    value=float(row["value"]),
                    unit=row["unit"].strip(),
                    basis=row["basis"].strip(),  # type: ignore[arg-type]
                    severity=row["severity"].strip(),
                    guideline_ref=row["guideline_ref"].strip(),
                    overridden_by=tuple(c.strip() for c in (row.get("overridden_by") or "").split(",") if c.strip()),
                )
            )
    if not rules:
        raise ValueError(f"Không nạp được rule nào từ {path}")
    return rules


def _select_rules(profile: PatientProfile, rules: list[ClinicalRule]) -> list[ClinicalRule]:
    """Chọn rule áp dụng cho bệnh nhân, có xét quyền ưu tiên giữa các guideline.

    Một số rule bị vô hiệu khi bệnh nhân mắc kèm bệnh khác. Ví dụ thực tế:
    ADA khuyến nghị protein 15-20% năng lượng cho bệnh nhân ĐTĐ, nhưng khi có
    kèm CKD thì KDIGO thắng — protein bị hạn chế 0.6-0.8 g/kg. Nếu không xử lý
    precedence, hai rule sẽ mâu thuẫn và toàn bộ ca ĐTĐ+CKD (rất phổ biến) sẽ
    bị đẩy sang chuyên gia một cách không cần thiết.
    """
    patient_conditions = {c.code.value for c in profile.conditions}

    def not_overridden(rule: ClinicalRule) -> bool:
        return not (set(rule.overridden_by) & patient_conditions)

    selected = [r for r in rules if r.condition_code == "BASE" and not_overridden(r)]
    for cond in profile.conditions:
        selected += [r for r in rules if r.applies_to(cond.code.value, cond.stage) and not_overridden(r)]
    return selected


def compute_targets(profile: PatientProfile, rules: list[ClinicalRule] | None = None) -> ClinicalTargets:
    """Tính định mức cá thể hoá. Luôn trả về kèm applied_rule_ids để UI giải trình."""
    rules = rules if rules is not None else load_rules()
    energy = compute_energy_target_kcal(profile)
    weight = adjusted_body_weight_kg(profile.weight_kg, profile.height_cm)

    targets: dict[str, NutrientTarget] = {
        "kcal": NutrientTarget(
            nutrient="kcal",
            min_value=energy * (1 - ENERGY_SOFT_TOLERANCE),
            max_value=energy * (1 + ENERGY_SOFT_TOLERANCE),
            unit="kcal",
            rule_ids=["ENERGY-MSJ"],
            guideline_refs=["Mifflin-St Jeor 1990; điều chỉnh theo mục tiêu cân nặng"],
        )
    }

    applied: list[str] = ["ENERGY-MSJ"]
    conflicts: list[str] = []

    for rule in _select_rules(profile, rules):
        value = rule.resolve(weight_kg=weight, energy_kcal=energy)
        t = targets.get(rule.nutrient)
        if t is None:
            t = NutrientTarget(nutrient=rule.nutrient, unit=rule.unit_for_target())
            targets[rule.nutrient] = t

        if rule.bound == "max":
            # Ngưỡng trên: lấy chặt hơn = nhỏ hơn
            t.max_value = value if t.max_value is None else min(t.max_value, value)
        else:
            # Ngưỡng dưới: lấy chặt hơn = lớn hơn
            t.min_value = value if t.min_value is None else max(t.min_value, value)

        t.rule_ids.append(rule.rule_id)
        if rule.guideline_ref not in t.guideline_refs:
            t.guideline_refs.append(rule.guideline_ref)
        applied.append(rule.rule_id)

    # Phát hiện xung đột không giải được — KHÔNG tự chọn, chuyển chuyên gia
    for name, t in targets.items():
        if t.min_value is not None and t.max_value is not None and t.min_value > t.max_value:
            conflicts.append(
                f"{name}: ngưỡng tối thiểu {t.min_value:.1f} lớn hơn tối đa {t.max_value:.1f} "
                f"(rules: {', '.join(t.rule_ids)})"
            )

    return ClinicalTargets(
        patient_id=profile.patient_id,
        bmr_kcal=round(compute_bmr(profile), 1),
        tdee_kcal=round(compute_tdee(profile), 1),
        targets=targets,
        applied_rule_ids=applied,
        needs_expert_review=bool(conflicts),
        conflict_notes=conflicts,
    )
