#!/usr/bin/env python3
"""
Independent oracle for computing expected_targets in EVL-01 benchmark.

CRITICAL: This oracle must NOT import src.clinical.compute_targets() or any
production clinical code. It uses frozen formulas and guideline snapshots
to produce expected outputs that are independent of the system under test.

All formulas must include:
- formula: mathematical expression or rule logic
- guideline_ref: source guideline (ADA 2023, KDIGO 2022, etc.)
- review_status: draft|reviewed|approved
- reviewed_by_role: R1|R2|R3|None
- reviewed_at: ISO date or None
- rule_version: semantic version of rule snapshot

Output: eval/datasets/cases_60_with_targets.jsonl

Usage:
    python scripts/compute_oracle_targets.py --input eval/datasets/cases_60.jsonl --output eval/datasets/cases_60_with_targets.jsonl
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

# ============================================================================
# ORACLE METADATA SCHEMAS
# ============================================================================


class OracleMetadata(BaseModel, extra="forbid"):
    """Metadata for oracle-computed target."""

    formula: str = Field(..., description="Mathematical expression or rule logic used")
    guideline_ref: str = Field(..., description="Source guideline (ADA 2023, KDIGO 2022, etc.)")
    rule_version: str = Field(..., description="Semantic version of rule snapshot (e.g., 1.0.0)")
    review_status: Literal["draft", "reviewed", "approved"] = Field(..., description="Review status of this target")
    reviewed_by_role: str | None = Field(None, description="R1|R2|R3 or None if unreviewed")
    reviewed_at: str | None = Field(None, description="ISO date of review or None")
    notes: str | None = Field(None, description="Additional context or caveats")


class ExpectedTargets(BaseModel, extra="forbid"):
    """Expected nutritional targets with oracle metadata."""

    kcal_min: int
    kcal_max: int
    protein_g_min: float
    protein_g_max: float
    carb_g_min: float
    carb_g_max: float
    fiber_g_min: float
    fat_g_max: float
    sodium_mg_max: int
    needs_expert_review: bool = Field(..., description="True if targets conflict or safety flags triggered")
    conflict_reason: str | None = Field(None, description="Why expert review needed")
    oracle_metadata: dict[str, OracleMetadata] = Field(
        ..., description="Per-target metadata with formulas and provenance"
    )


# ============================================================================
# FROZEN RULE SNAPSHOTS (v1.0.0 - 2026-08-07)
# ============================================================================

# These are snapshots of clinical guidelines as of 2026-08-07.
# They are INDEPENDENT of src/clinical/targets.py production code.


def compute_kcal_target_oracle(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
    activity_level: str,
    bmi: float,
    weight_goal: str = "maintain",
) -> tuple[int, int, OracleMetadata]:
    """
    Compute daily kcal target using Mifflin-St Jeor + activity factor.

    Frozen formula (v1.0.0):
    - BMR_male = 10*weight + 6.25*height - 5*age + 5
    - BMR_female = 10*weight + 6.25*height - 5*age - 161
    - TDEE = BMR * activity_factor
    - Range = TDEE * (0.9, 1.1) for maintain
    - Deficit 400-600 kcal/day for lose (centered on 500), surplus 200-400 for gain (centered on 300)

    FIX (PR review): Accept actual height_cm from patient profile instead of
    reverse-calculating from BMI, which introduced approximation errors.
    """
    # Guard against invalid inputs
    if bmi <= 0:
        raise ValueError(f"Invalid BMI: {bmi} (must be > 0)")
    if height_cm <= 0:
        raise ValueError(f"Invalid height_cm: {height_cm} (must be > 0)")

    # Mifflin-St Jeor BMR — uses actual height from patient profile (not approximated)
    if sex == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    # Activity factors (aligned with PatientProfile allowed values)
    activity_factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
    }
    factor = activity_factors.get(activity_level, 1.2)
    tdee = bmr * factor

    # Weight goal adjustments
    if weight_goal == "lose":
        kcal_min = int(tdee - 600)
        kcal_max = int(tdee - 400)
    elif weight_goal == "gain":
        kcal_min = int(tdee + 200)
        kcal_max = int(tdee + 400)
    else:  # maintain
        kcal_min = int(tdee * 0.9)
        kcal_max = int(tdee * 1.1)

    # Absolute floor and ceiling
    kcal_min = max(1200, kcal_min)
    kcal_max = min(3000, kcal_max)

    # Ensure min < max after clamping (avoid range collapse for low TDEE patients)
    if kcal_min >= kcal_max:
        kcal_max = kcal_min + 100

    metadata = OracleMetadata(
        formula=f"Mifflin-St Jeor: BMR={'10W+6.25H-5A+5' if sex == 'male' else '10W+6.25H-5A-161'}, H={height_cm}cm (actual), TDEE=BMR*{factor}, goal={weight_goal} ({'TDEE-[400,600]' if weight_goal == 'lose' else 'TDEE+[200,400]' if weight_goal == 'gain' else '±10%'})",
        guideline_ref="Academy of Nutrition and Dietetics 2020",
        rule_version="1.0.0",
        review_status="draft",
        reviewed_by_role=None,
        reviewed_at=None,
        notes=f"Weight goal: {weight_goal}. Height taken from patient profile (not reverse-calculated from BMI).",
    )

    return kcal_min, kcal_max, metadata


def compute_protein_target_oracle(
    weight_kg: float,
    age: int,
    ckd_stage: str | None,
    frailty_sarcopenia: bool,
) -> tuple[float, float, OracleMetadata]:
    """
    Compute daily protein target (grams).

    Frozen formula (v1.0.0):
    - Healthy adult: 0.8-1.0 g/kg/day
    - Elderly/frail/sarcopenia: 1.0-1.2 g/kg/day
    - CKD G3a-G4: 0.6-0.8 g/kg/day (KDIGO 2022)
    - CKD G5: 0.6 g/kg/day
    """
    if ckd_stage == "G4":
        # KDIGO 2022: CKD G4 — restrict to 0.6-0.8 g/kg/day to slow progression
        protein_min = 0.6 * weight_kg
        protein_max = 0.8 * weight_kg
        ref = "KDIGO 2022 CKD Nutrition Guideline"
        notes = (
            f"CKD G4: KDIGO 2022 recommends 0.6-0.8 g/kg/day "
            f"(= {protein_min:.1f}-{protein_max:.1f}g) to slow GFR decline. "
            "Protein restriction target is 0.8 g/kg/day (upper bound)."
        )
    elif ckd_stage == "G5":
        # KDIGO 2022: CKD G5 (pre-dialysis) — stricter restriction 0.6-0.7 g/kg/day
        protein_min = 0.6 * weight_kg
        protein_max = 0.7 * weight_kg
        ref = "KDIGO 2022 CKD Nutrition Guideline"
        notes = (
            f"CKD G5 (pre-dialysis): KDIGO 2022 recommends 0.6-0.7 g/kg/day "
            f"(= {protein_min:.1f}-{protein_max:.1f}g). Upper bound 0.7 g/kg/day "
            "is STRICTER than G4 (0.8 g/kg/day) to minimize uremic toxin load."
        )
    elif ckd_stage == "G3a" or ckd_stage == "G3b":
        protein_min = 0.6 * weight_kg
        protein_max = 0.8 * weight_kg
        ref = "KDIGO 2022 CKD Nutrition Guideline"
        notes = (
            f"CKD {ckd_stage}: moderate protein restriction 0.6-0.8 g/kg/day (= {protein_min:.1f}-{protein_max:.1f}g)"
        )
    elif frailty_sarcopenia or age >= 70:
        protein_min = 1.0 * weight_kg
        protein_max = 1.2 * weight_kg
        ref = "ESPEN Guideline on Nutrition in Older Adults 2019"
        notes = "Increased for sarcopenia/elderly"
    else:
        protein_min = 0.8 * weight_kg
        protein_max = 1.0 * weight_kg
        ref = "DRI (Dietary Reference Intakes) 2005"
        notes = "Standard adult requirement"

    metadata = OracleMetadata(
        formula=f"{protein_min / weight_kg:.1f}-{protein_max / weight_kg:.1f} g/kg/day",
        guideline_ref=ref,
        rule_version="1.0.0",
        review_status="draft",
        reviewed_by_role=None,
        reviewed_at=None,
        notes=notes,
    )

    return round(protein_min, 1), round(protein_max, 1), metadata


def compute_carb_target_oracle(
    kcal_min: int,
    kcal_max: int,
    has_t2dm: bool,
) -> tuple[float, float, OracleMetadata]:
    """
    Compute daily carbohydrate target (grams).

    Frozen formula (v1.0.0):
    - T2DM: 40-50% of total kcal from carbs (ADA 2023)
    - Non-T2DM: 45-65% of total kcal from carbs (DRI)
    - 1 g carb = 4 kcal
    """
    if has_t2dm:
        carb_min = (kcal_min * 0.40) / 4
        carb_max = (kcal_max * 0.50) / 4
        ref = "ADA Standards of Care 2023"
        notes = "T2DM: moderate carb intake"
    else:
        carb_min = (kcal_min * 0.45) / 4
        carb_max = (kcal_max * 0.65) / 4
        ref = "DRI (Dietary Reference Intakes) 2005"
        notes = "Standard adult carb range"

    metadata = OracleMetadata(
        formula=f"{'40-50%' if has_t2dm else '45-65%'} of kcal / 4",
        guideline_ref=ref,
        rule_version="1.0.0",
        review_status="draft",
        reviewed_by_role=None,
        reviewed_at=None,
        notes=notes,
    )

    return round(carb_min, 1), round(carb_max, 1), metadata


def compute_fiber_target_oracle(sex: str, age: int) -> tuple[float, OracleMetadata]:
    """
    Compute daily fiber minimum (grams).

    Frozen formula (v1.0.0):
    - Adult male: 30-38 g/day
    - Adult female: 21-25 g/day
    - Elderly (>70): lower end of range
    """
    if sex == "male":
        fiber_min = 30.0 if age < 70 else 28.0
        range_str = "30-38 g/day"
    else:
        fiber_min = 21.0 if age < 70 else 20.0
        range_str = "21-25 g/day"

    metadata = OracleMetadata(
        formula=range_str,
        guideline_ref="DRI (Dietary Reference Intakes) 2005",
        rule_version="1.0.0",
        review_status="draft",
        reviewed_by_role=None,
        reviewed_at=None,
        notes="Standard adult fiber requirement",
    )

    return fiber_min, metadata


def compute_fat_target_oracle(kcal_max: int) -> tuple[float, OracleMetadata]:
    """
    Compute daily fat maximum (grams).

    Frozen formula (v1.0.0):
    - Fat ≤ 30% of total kcal (ADA 2023, AHA 2021)
    - 1 g fat = 9 kcal
    """
    fat_max = (kcal_max * 0.30) / 9

    metadata = OracleMetadata(
        formula="≤30% of kcal / 9",
        guideline_ref="ADA Standards of Care 2023",
        rule_version="1.0.0",
        review_status="draft",
        reviewed_by_role=None,
        reviewed_at=None,
        notes="Standard fat limit for CVD/T2DM",
    )

    return round(fat_max, 1), metadata


def compute_sodium_target_oracle(
    has_htn: bool,
    has_ckd: bool,
    ckd_stage: str | None,
    sodium_wasting: bool,
) -> tuple[int, OracleMetadata]:
    """
    Compute daily sodium maximum (mg).

    Frozen formula (v1.0.0):
    - HTN or CKD: ≤2000 mg/day (AHA 2021, KDIGO 2022)
    - Healthy adult: ≤2300 mg/day (DRI)
    - Sodium wasting: relaxed to 2500-3000 mg/day
    """
    if sodium_wasting:
        sodium_max = 3000
        ref = "Clinical judgment for sodium-wasting conditions"
        notes = "Relaxed for sodium wasting"
    elif has_htn or has_ckd:
        sodium_max = 2000
        ref = "AHA 2021, KDIGO 2022"
        notes = f"Strict limit for {'HTN' if has_htn else 'CKD'}"
    else:
        sodium_max = 2300
        ref = "DRI (Dietary Reference Intakes) 2005"
        notes = "Standard adult upper limit"

    metadata = OracleMetadata(
        formula=f"≤{sodium_max} mg/day",
        guideline_ref=ref,
        rule_version="1.0.0",
        review_status="draft",
        reviewed_by_role=None,
        reviewed_at=None,
        notes=notes,
    )

    return sodium_max, metadata


# ============================================================================
# ORACLE COMPUTE FUNCTION
# ============================================================================


def compute_expected_targets_oracle(case: dict[str, Any]) -> ExpectedTargets:
    """
    Compute expected targets for a single evaluation case using frozen formulas.

    This function is INDEPENDENT of src.clinical.compute_targets() and uses
    only the frozen rule snapshots defined above.
    """
    profile = case["patient_profile"]
    conditions = {c["code"]: c for c in profile["conditions"]}

    # Extract key attributes
    weight_kg = profile["weight_kg"]
    height_cm = profile["height_cm"]
    age = profile["age"]
    sex = profile["sex"]
    activity = profile.get("activity_level", "sedentary")

    # Guard against invalid height before BMI calculation
    if height_cm <= 0:
        raise ValueError(f"Invalid height_cm: {height_cm} in case {case.get('case_id', 'unknown')}")

    bmi = case["clinical_context"].get("bmi", weight_kg / ((height_cm / 100) ** 2))
    frailty = profile.get("frailty_sarcopenia", False)
    sodium_wasting = profile.get("sodium_wasting", False)

    # Identify conditions
    has_t2dm = "T2DM" in conditions
    has_htn = "HTN" in conditions
    has_ckd = "CKD" in conditions
    ckd_stage = conditions["CKD"]["stage"] if has_ckd else None

    # Compute targets with oracle formulas
    # FIX: Pass actual height_cm from profile instead of letting oracle reverse-calculate from BMI
    height_cm = profile["height_cm"]
    kcal_min, kcal_max, kcal_meta = compute_kcal_target_oracle(
        weight_kg, height_cm, age, sex, activity, bmi, weight_goal="maintain"
    )

    protein_min, protein_max, protein_meta = compute_protein_target_oracle(weight_kg, age, ckd_stage, frailty)

    carb_min, carb_max, carb_meta = compute_carb_target_oracle(kcal_min, kcal_max, has_t2dm)

    fiber_min, fiber_meta = compute_fiber_target_oracle(sex, age)

    fat_max, fat_meta = compute_fat_target_oracle(kcal_max)

    sodium_max, sodium_meta = compute_sodium_target_oracle(has_htn, has_ckd, ckd_stage, sodium_wasting)

    # Check for conflicts
    needs_review = False
    conflict_reason = None

    # Protein-kcal conflict check
    protein_kcal_min = protein_min * 4  # rough lower bound for protein calories
    if protein_kcal_min > kcal_max:
        needs_review = True
        conflict_reason = (
            f"Protein minimum ({protein_min}g * 4 ≈ {int(protein_kcal_min)} kcal) exceeds kcal_max ({kcal_max})"
        )

    # CKD G5 + multi-morbidity
    if ckd_stage == "G5" and len(conditions) >= 3:
        needs_review = True
        conflict_reason = "CKD G5 with ≥3 conditions requires nephrologist + dietitian"

    # Frailty + severe restriction
    if frailty and kcal_min < 1200:
        needs_review = True
        conflict_reason = "Frail patient with very low kcal target"

    return ExpectedTargets(
        kcal_min=kcal_min,
        kcal_max=kcal_max,
        protein_g_min=protein_min,
        protein_g_max=protein_max,
        carb_g_min=carb_min,
        carb_g_max=carb_max,
        fiber_g_min=fiber_min,
        fat_g_max=fat_max,
        sodium_mg_max=sodium_max,
        needs_expert_review=needs_review,
        conflict_reason=conflict_reason,
        oracle_metadata={
            "kcal": kcal_meta.model_dump(),
            "protein": protein_meta.model_dump(),
            "carb": carb_meta.model_dump(),
            "fiber": fiber_meta.model_dump(),
            "fat": fat_meta.model_dump(),
            "sodium": sodium_meta.model_dump(),
        },
    )


# ============================================================================
# MAIN
# ============================================================================


def main() -> None:
    """Compute oracle targets for all evaluation cases."""
    parser = argparse.ArgumentParser(description="Compute oracle expected_targets for EVL-01")
    parser.add_argument(
        "--input",
        type=str,
        default="eval/datasets/cases_60.jsonl",
        help="Input cases JSONL file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="eval/datasets/cases_60_with_targets.jsonl",
        help="Output cases with targets JSONL file",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)

    print("=" * 70)
    print("ORACLE TARGET COMPUTATION (EVL-01)")
    print("=" * 70)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print("=" * 70)
    print("CRITICAL: This oracle does NOT import src.clinical.compute_targets()")
    print("All formulas are frozen snapshots (v1.0.0, 2026-08-07)")
    print("=" * 70)

    # Load cases
    cases = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))

    print(f"\n[OK] Loaded {len(cases)} cases")

    # Compute targets
    print("\nComputing expected targets...")
    for i, case in enumerate(cases, start=1):
        case_id = case["case_id"]
        try:
            targets = compute_expected_targets_oracle(case)
            case["expected_targets"] = targets.model_dump()
            status = "OK"
            if targets.needs_expert_review:
                status = "WARN"
            print(f"  [{i:02d}/60] {case_id}: {status}", flush=True)
        except Exception as e:
            print(f"  [{i:02d}/60] {case_id}: ERROR - {e}", flush=True)
            case["expected_targets"] = None

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nSaving: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"[OK] Saved {len(cases)} cases with expected_targets")

    # Summary
    with_targets = sum(1 for c in cases if c["expected_targets"] is not None)
    needs_review = sum(1 for c in cases if c["expected_targets"] and c["expected_targets"]["needs_expert_review"])

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total cases:           {len(cases)}")
    print(f"With expected_targets: {with_targets}")
    print(f"Needs expert review:   {needs_review}")
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. R1 must review oracle formulas and metadata")
    print("2. Update review_status -> 'reviewed' after R1 approval")
    print("3. EVL-02 runner will fail-closed if review_status != 'reviewed'")
    print("4. Do NOT use these targets until R1 has approved them")
    print("=" * 70)


if __name__ == "__main__":
    main()
