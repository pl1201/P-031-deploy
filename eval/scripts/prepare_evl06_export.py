#!/usr/bin/env python3
"""EVL-06: Prepare meal plans for expert review.

Export 20 meal plans (draft status) với đầy đủ nutrition + warnings cho chuyên gia review.
Không gửi tới patient. Chỉ ghi reviewer_id ẩn danh, consent records giữ ngoài repo.

Usage:
    python eval/scripts/prepare_evl06_export.py --output eval/datasets/meal_plans_for_review.jsonl

Output format:
    {
        "meal_plan_id": "MP-001",
        "case_id": "T2DM-001",
        "patient_profile_summary": {...},  # Không có PII, chỉ demographics + conditions
        "menu": {...},  # MenuDraft với food_id + grams
        "nutrition_summary": {...},  # Computed nutrition với sources
        "warnings": [...],  # Safety warnings từ validators
        "status": "draft",
        "generated_at": "2026-08-07T...",
        "for_review_by": ["clinical_dietitian", "endocrinologist"]
    }

Review import format (từ chuyên gia):
    {
        "review_id": "REV-001",
        "meal_plan_id": "MP-001",
        "reviewer_id": "R2-001",  # Ẩn danh, mapping giữ ngoài repo
        "reviewer_role": "clinical_dietitian",
        "reviewed_at": "2026-08-07T...",
        "rating": "approve" | "light_edit" | "heavy_edit" | "reject",
        "gram_changes": {...},
        "dishes_added": [...],
        "dishes_removed": [...],
        "review_time_minutes": int,
        "comments": str,
        "reason_code": str | null
    }

CRITICAL:
- Meal plans phải ở trạng thái draft, CHƯA được gửi tới patient
- Reviewer identity + consent records giữ ngoài repo (TEAM.md references only)
- Import validator fail-closed nếu thiếu reviewer metadata hoặc rating không hợp lệ
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.clinical.models import FoodItem, MealSlot, MenuItem, MenuDraft, PatientProfile
from src.clinical.nutrition import InMemoryFoodRepository, compute_nutrition
from src.clinical.rules import compute_targets, load_rules


class MealPlanForReview(BaseModel):
    """Meal plan export for expert review."""

    meal_plan_id: str
    case_id: str
    patient_profile_summary: dict[str, Any]
    menu: dict[str, list[dict[str, Any]]]  # Serialized MenuDraft
    nutrition_summary: dict[str, Any]
    warnings: list[str]
    status: str = "draft"
    generated_at: str
    for_review_by: list[str]


def load_cases_sample(n: int = 20, seed: int = 42) -> list[dict[str, Any]]:
    """Load random sample of n cases for review export."""
    cases_path = Path("eval/datasets/cases_60_with_targets.jsonl")
    if not cases_path.exists():
        raise FileNotFoundError(f"Cases not found: {cases_path}")

    cases = []
    with open(cases_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    random.seed(seed)
    return random.sample(cases, min(n, len(cases)))


def generate_mock_menu(
    profile: PatientProfile, targets: dict[str, Any], food_repo: InMemoryFoodRepository
) -> MenuDraft:
    """Generate a mock menu for testing (placeholder for actual LLM generation).

    In production, this would call the LangGraph menu generation flow.
    For EVL-06 prep, we create simple deterministic menus using valid food IDs.
    """
    # Use food IDs that actually exist in the repository
    all_items = food_repo.all()

    # Find some common Vietnamese dishes (first 50 items should include basics)
    available_ids = [item.id for item in all_items[:100]]

    # Simple heuristic: pick first available items for each meal
    breakfast_items = [
        MenuItem(food_id=available_ids[0], grams=150),  # First item
        MenuItem(food_id=available_ids[1], grams=80),   # Second item
    ]
    lunch_items = [
        MenuItem(food_id=available_ids[0], grams=200),
        MenuItem(food_id=available_ids[2], grams=100),
        MenuItem(food_id=available_ids[3], grams=150),
    ]
    dinner_items = [
        MenuItem(food_id=available_ids[0], grams=150),
        MenuItem(food_id=available_ids[4], grams=100),
        MenuItem(food_id=available_ids[5], grams=150),
    ]

    return MenuDraft(
        items={
            MealSlot.BREAKFAST: breakfast_items,
            MealSlot.LUNCH: lunch_items,
            MealSlot.DINNER: dinner_items,
        }
    )


def main():
    parser = argparse.ArgumentParser(description="Prepare meal plans for EVL-06 expert review")
    parser.add_argument("--output", default="eval/datasets/meal_plans_for_review.jsonl")
    parser.add_argument("--count", type=int, default=20, help="Number of meal plans to export")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("=" * 70)
    print("EVL-06: MEAL PLAN EXPORT FOR EXPERT REVIEW")
    print("=" * 70)

    # Load dependencies
    cases = load_cases_sample(n=args.count, seed=args.seed)
    rules = load_rules()

    # Load food items from CSV (same as run_evaluation.py)
    import csv
    food_items = []
    with open("data/seeds/food_items.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("kcal_100g") or not row.get("protein_g"):
                continue
            food_items.append(
                FoodItem(
                    id=int(row["id"]),
                    name_vi=row["name_vi"],
                    aliases=row.get("aliases", "").split("|") if row.get("aliases") else [],
                    category=row.get("category", ""),
                    kcal_100g=float(row["kcal_100g"]),
                    protein_g=float(row["protein_g"]),
                    carb_g=float(row.get("carb_g", 0)),
                    fat_g=float(row.get("fat_g", 0)),
                    fiber_g=float(row.get("fiber_g", 0)),
                    na_mg=float(row.get("na_mg", 0)),
                    k_mg=float(row.get("k_mg", 0)),
                    p_mg=float(row.get("p_mg", 0)),
                    source=row.get("source", "unknown"),
                    source_ref=row.get("source_ref", ""),
                    is_estimated=row.get("is_estimated", "false").lower() == "true",
                )
            )
    food_repo = InMemoryFoodRepository(food_items)

    print(f"[OK] Loaded {len(cases)} cases for review")
    print(f"[OK] Loaded {len(food_repo.all())} food items")
    print(f"[OK] Loaded {len(rules)} clinical rules")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    meal_plans = []
    with open(output_path, "w", encoding="utf-8") as f:
        for i, case in enumerate(cases, start=1):
            case_id = case["case_id"]
            profile_dict = case["patient_profile"]

            # Build PatientProfile
            profile = PatientProfile(
                patient_id=case_id,
                age=profile_dict["age"],
                sex=profile_dict["sex"],
                weight_kg=profile_dict["weight_kg"],
                height_cm=profile_dict["height_cm"],
                conditions=profile_dict["conditions"],
                lab_values=profile_dict.get("lab_values", {}),
                activity_level=profile_dict["activity_level"],
                region=profile_dict.get("region", "north"),
                medications=profile_dict.get("medications", []),
                allergies=profile_dict.get("allergies", []),
            )

            # Compute targets
            targets = compute_targets(profile, rules)

            # Generate mock menu (in production: call LangGraph)
            menu = generate_mock_menu(profile, targets, food_repo)

            # Compute nutrition
            nutrition = compute_nutrition(menu, food_repo)

            # Collect warnings (placeholder)
            warnings = []
            if targets.needs_expert_review:
                warnings.extend(targets.conflict_notes)

            # Serialize
            meal_plan = MealPlanForReview(
                meal_plan_id=f"MP-{i:03d}",
                case_id=case_id,
                patient_profile_summary={
                    "age": profile.age,
                    "sex": profile.sex,
                    "bmi": profile.bmi,
                    "conditions": [c.code for c in profile.conditions],
                    "activity_level": profile.activity_level,
                },
                menu={
                    slot.value: [{"food_id": item.food_id, "grams": item.grams} for item in items]
                    for slot, items in menu.items.items()
                },
                nutrition_summary={
                    "kcal": nutrition.kcal,
                    "protein_g": nutrition.protein_g,
                    "carb_g": nutrition.carb_g,
                    "fat_g": nutrition.fat_g,
                    "fiber_g": nutrition.fiber_g,
                    "na_mg": nutrition.na_mg,
                    "k_mg": nutrition.k_mg,
                    "p_mg": nutrition.p_mg,
                    "sources": [
                        {"food_id": s.food_id, "name": s.name, "source": s.source, "source_ref": s.source_ref}
                        for s in nutrition.sources
                    ],
                },
                warnings=warnings,
                generated_at=datetime.now().isoformat(),
                for_review_by=["clinical_dietitian", "endocrinologist"],
            )

            f.write(meal_plan.model_dump_json() + "\n")
            meal_plans.append(meal_plan)

    print(f"\n[OK] Exported {len(meal_plans)} meal plans -> {output_path}")
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. Share meal plans with expert reviewers (offline process)")
    print("2. Collect review data in format: eval/datasets/expert_review_template.jsonl")
    print("3. Run: python eval/scripts/import_evl06_reviews.py")
    print("4. Compute EVL-06 metrics: agreement %, edit distance, time")
    print("\nREMINDER: Reviewer identity + consent records stay OUTSIDE repo")


if __name__ == "__main__":
    main()
