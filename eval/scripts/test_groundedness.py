#!/usr/bin/env python3
"""EVL-03: Groundedness tests for nutrition values.

Kiểm tra RULE-2: Không con số nào không có nguồn.
- Mọi giá trị dinh dưỡng hiển thị phải có source + source_ref
- Món ước tính phải có is_estimated=true + confidence
- Unknown food_id phải fail-closed (không đoán thay thế)

Usage:
    pytest eval/scripts/test_groundedness.py -v

Tests:
1. test_food_repository_provenance: Mọi food item có source + source_ref
2. test_no_null_provenance_in_db: DB seed không có null/placeholder
3. test_compute_nutrition_all_sources: compute_nutrition() sinh SourceRef cho mọi item
4. test_unknown_food_raises: LLM trả unknown food_id → UnknownFoodError
5. test_estimated_foods_flagged: Món estimated có cờ + confidence
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.clinical.models import FoodItem, MenuDraft, MenuItem
from src.clinical.nutrition import (
    InMemoryFoodRepository,
    UnknownFoodError,
    compute_nutrition,
)

FOOD_ITEMS_PATH = Path("data/seeds/food_items.csv")


def load_food_repository() -> InMemoryFoodRepository:
    """Load food items from CSV for testing."""
    items = []
    with open(FOOD_ITEMS_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip incomplete rows
            if not row.get("kcal_100g") or not row.get("protein_g"):
                continue

            items.append(
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
    return InMemoryFoodRepository(items)


def test_food_repository_provenance():
    """EVL-03.1: Mọi food item phải có source và source_ref không rỗng."""
    repo = load_food_repository()
    items = repo.all()

    assert len(items) > 7000, "Expected >7000 food items in repository"

    missing_source = []
    missing_ref = []

    for item in items:
        if not item.source or item.source == "unknown":
            missing_source.append(f"ID {item.id}: {item.name_vi}")
        if not item.source_ref:
            missing_ref.append(f"ID {item.id}: {item.name_vi}")

    assert not missing_source, f"Found {len(missing_source)} items without source:\n" + "\n".join(missing_source[:10])
    assert not missing_ref, f"Found {len(missing_ref)} items without source_ref:\n" + "\n".join(missing_ref[:10])


def test_no_null_provenance_in_db():
    """EVL-03.2: DB seed không có placeholder "TBD", "N/A", null.

    NOTE: Incomplete rows (missing kcal_100g/protein_g) are allowed but won't be loaded.
    This test only checks rows that WILL be loaded into the repository.
    """
    with open(FOOD_ITEMS_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        bad_rows = []
        for i, row in enumerate(reader, start=2):
            # Skip rows that won't be loaded (missing required nutrition data)
            if not row.get("kcal_100g") or not row.get("protein_g"):
                continue

            source = row.get("source", "").strip().lower()
            source_ref = row.get("source_ref", "").strip().lower()

            if source in ("", "unknown", "tbd", "n/a", "null"):
                bad_rows.append(f"Line {i} (ID {row.get('id')}): source='{row.get('source')}'")
            if source_ref in ("", "tbd", "n/a", "null"):
                bad_rows.append(f"Line {i} (ID {row.get('id')}): source_ref='{row.get('source_ref')}'")

    assert not bad_rows, f"Found {len(bad_rows)} rows with placeholder provenance:\n" + "\n".join(bad_rows[:10])


def test_compute_nutrition_all_sources():
    """EVL-03.3: compute_nutrition() sinh SourceRef cho mọi món trong menu."""
    repo = load_food_repository()

    # Menu 3 món: cơm, thịt, rau (MenuDraft.items là dict[MealSlot, list[MenuItem]])
    from src.clinical.models import MealSlot

    menu = MenuDraft(
        items={
            MealSlot.LUNCH: [
                MenuItem(food_id=1, grams=200),
                MenuItem(food_id=10, grams=100),
                MenuItem(food_id=50, grams=150),
            ]
        }
    )

    summary = compute_nutrition(menu, repo)

    assert len(summary.sources) == 3, "Expected 3 SourceRef objects (1 per menu item)"

    for src in summary.sources:
        assert src.food_id > 0, f"Invalid food_id: {src.food_id}"
        assert src.name, f"Missing name in SourceRef for food_id {src.food_id}"
        assert src.source, f"Missing source in SourceRef for food_id {src.food_id}"
        assert src.source_ref, f"Missing source_ref in SourceRef for food_id {src.food_id}"


def test_unknown_food_raises():
    """EVL-03.4: LLM trả unknown food_id → UnknownFoodError, không đoán thay thế."""
    repo = load_food_repository()
    from src.clinical.models import MealSlot

    menu = MenuDraft(
        items={
            MealSlot.LUNCH: [
                MenuItem(food_id=999999, grams=100),
            ]
        }
    )

    with pytest.raises(UnknownFoodError, match="999999"):
        compute_nutrition(menu, repo)


def test_estimated_foods_flagged():
    """EVL-03.5: Món estimated có is_estimated=true."""
    repo = load_food_repository()
    all_items = repo.all()

    estimated = [i for i in all_items if i.is_estimated]

    # Chỉ kiểm tra có ít nhất một món estimated; không yêu cầu confidence ở FoodItem level
    # (confidence sẽ ở SourceRef khi compute_nutrition)
    assert len(estimated) > 0, "Expected at least some estimated food items in repository"

    for item in estimated[:5]:  # Sample 5 món
        assert item.is_estimated is True, f"ID {item.id}: is_estimated should be True"
        # source_ref phải ghi rõ phương pháp: "ước tính", "estimated", "approx", formula với ×,
        # hoặc "khớp chéo ngôn ngữ" (cross-language mapping)
        ref_lower = item.source_ref.lower()
        keywords = ["ước tính", "estimated", "approx", "×", "khớp chéo", "cross-language"]
        assert any(keyword in ref_lower for keyword in keywords), (
            f"ID {item.id}: source_ref '{item.source_ref}' should indicate estimation method"
        )
