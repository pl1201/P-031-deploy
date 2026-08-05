"""Nạp seed CSV (food_items, dishes, dish_ingredients) thành object tầng lâm sàng.

LLM: NO — thuần dữ liệu. Ticket: DAT-02, DAT-04.

Món ăn được phân rã thành nguyên liệu (food_id + gram); dinh dưỡng của món tính
bằng compute_nutrition() — KHÔNG lưu con số dinh dưỡng của món (RULE-1).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from .models import FoodItem, MealSlot, MenuDraft, MenuItem
from .nutrition import InMemoryFoodRepository

SEEDS_DIR = Path(__file__).resolve().parents[2] / "data" / "seeds"

# Muối ăn (NaCl) = 39,3% natri → khối muối tương đương = Na(mg)/1000 / 0,393.
SALT_PER_NA_MG = 2.54 / 1000


def _split(raw: str | None) -> list[str]:
    return [s.strip() for s in (raw or "").split("|") if s.strip()]


def _opt_float(raw: str | None) -> float | None:
    raw = (raw or "").strip()
    return float(raw) if raw else None


def _opt_str(raw: str | None) -> str | None:
    raw = (raw or "").strip()
    return raw or None


def load_food_repository(path: Path | None = None) -> InMemoryFoodRepository:
    """Nạp các dòng ĐÃ có số liệu trong food_items.csv thành FoodItem."""
    path = path or SEEDS_DIR / "food_items.csv"
    items: list[FoodItem] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not (row.get("kcal_100g") or "").strip():
                continue  # dòng chưa nhập số liệu
            items.append(
                FoodItem(
                    id=int(row["id"]),
                    name_vi=row["name_vi"],
                    aliases=_split(row.get("aliases")),
                    kcal_100g=float(row["kcal_100g"]),
                    protein_g=float(row["protein_g"]),
                    carb_g=float(row["carb_g"]),
                    fat_g=float(row["fat_g"]),
                    fiber_g=float(row["fiber_g"]),
                    sugar_g=_opt_float(row.get("sugar_g")),
                    na_mg=float(row["na_mg"]),
                    k_mg=float(row["k_mg"]),
                    p_mg=float(row["p_mg"]),
                    purine_mg=_opt_float(row.get("purine_mg")),
                    purine_source_ref=_opt_str(row.get("purine_source_ref")),
                    gi_index=_opt_float(row.get("gi_index")),
                    gi_source=_opt_str(row.get("gi_source")),  # type: ignore[arg-type]
                    gi_source_ref=_opt_str(row.get("gi_source_ref")),
                    contains_allergens=_split(row.get("contains_allergens")),
                    source=row["source"],  # type: ignore[arg-type]
                    source_ref=row["source_ref"],
                    is_estimated=(row.get("is_estimated") or "").strip().upper() == "TRUE",
                )
            )
    return InMemoryFoodRepository(items)


def load_dish_menus(path: Path | None = None) -> dict[str, MenuDraft]:
    """Trả về {dish_id: MenuDraft} — mỗi món là tập nguyên liệu (food_id + gram)."""
    path = path or SEEDS_DIR / "dish_ingredients.csv"
    by_dish: dict[str, list[MenuItem]] = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_dish[row["dish_id"]].append(MenuItem(food_id=int(row["food_id"]), grams=float(row["grams"])))
    return {did: MenuDraft(items={MealSlot.LUNCH: items}) for did, items in by_dish.items()}


def salt_equiv_g(na_mg: float) -> float:
    """Khối muối tương đương (g) từ natri (mg). Dùng cho cảnh báo muối/bát."""
    return round(na_mg * SALT_PER_NA_MG, 2)
