"""Dish candidates whose nutrition is derived from recipe ingredients."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.clinical.models import FoodItem
from src.clinical.nutrition import InMemoryFoodRepository
from src.clinical.seeds import SEEDS_DIR, load_food_repository


@dataclass(frozen=True)
class DishIngredientView:
    food_id: int
    name_vi: str
    grams: float
    source: str
    source_ref: str


@dataclass(frozen=True)
class DishView:
    dish_id: str
    name_vi: str
    region: str | None
    serving_g: float
    ingredients: tuple[DishIngredientView, ...]


class DishFoodRepository(InMemoryFoodRepository):
    """Adapt prepared dishes to the existing deterministic FoodRepository port."""

    def __init__(self, items: list[FoodItem], dishes: dict[int, DishView]) -> None:
        super().__init__(items)
        self._dishes = dishes
        self._food_id_by_dish = {dish.dish_id: food_id for food_id, dish in dishes.items()}

    def dish_for_food_id(self, food_id: int) -> DishView | None:
        return self._dishes.get(food_id)

    def food_id_for_dish(self, dish_id: str) -> int | None:
        return self._food_id_by_dish.get(dish_id)


def load_dish_food_repository(
    dishes_path: Path | None = None,
    ingredients_path: Path | None = None,
) -> DishFoodRepository:
    """Aggregate each non-FNDDS recipe into a per-100-g dish candidate."""
    foods = load_food_repository()
    dishes_path = dishes_path or SEEDS_DIR / "dishes.csv"
    ingredients_path = ingredients_path or SEEDS_DIR / "dish_ingredients.csv"
    recipes: dict[str, list[tuple[int, float]]] = {}
    with open(ingredients_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            recipes.setdefault(row["dish_id"], []).append((int(row["food_id"]), float(row["grams"])))

    with open(dishes_path, newline="", encoding="utf-8") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            # MENU-* rows imported from spreadsheets describe an entire meal,
            # not a prepared dish. Letting the optimizer select them creates
            # labels such as "Bữa trưa" inside the dinner slot.
            if not row["dish_id"].startswith(("FNDDS-", "MENU-"))
        ]

    items: list[FoodItem] = []
    dish_views: dict[int, DishView] = {}
    for index, row in enumerate(rows, start=1):
        resolved = [(foods.get(food_id), grams) for food_id, grams in recipes.get(row["dish_id"], [])]
        if not resolved or any(food is None for food, _ in resolved):
            continue
        typed = [(food, grams) for food, grams in resolved if food is not None]
        total_g = sum(grams for _, grams in typed)
        if total_g <= 0:
            continue

        def per_100(field: str) -> float:
            return sum(float(getattr(food, field)) * grams / 100 for food, grams in typed) * 100 / total_g

        sugar_complete = all(food.sugar_g is not None for food, _ in typed)
        purine_complete = all(food.purine_mg is not None for food, _ in typed)
        synthetic_id = -index
        dish_views[synthetic_id] = DishView(
            dish_id=row["dish_id"],
            name_vi=row["name_vi"],
            region=(row.get("region") or "").strip() or None,
            serving_g=float(row.get("serving_g") or total_g),
            ingredients=tuple(
                DishIngredientView(food.id, food.name_vi, grams, food.source, food.source_ref) for food, grams in typed
            ),
        )
        items.append(
            FoodItem(
                id=synthetic_id,
                name_vi=row["name_vi"],
                kcal_100g=per_100("kcal_100g"),
                protein_g=per_100("protein_g"),
                carb_g=per_100("carb_g"),
                fat_g=per_100("fat_g"),
                fiber_g=per_100("fiber_g"),
                sugar_g=per_100("sugar_g") if sugar_complete else None,
                na_mg=per_100("na_mg"),
                k_mg=per_100("k_mg"),
                p_mg=per_100("p_mg"),
                purine_mg=per_100("purine_mg") if purine_complete else None,
                contains_allergens=sorted({a for food, _ in typed for a in food.contains_allergens}),
                source="curated",
                source_ref=f"recipe:{row['dish_id']};ingredients:" + ",".join(str(food.id) for food, _ in typed),
                is_estimated=any(food.is_estimated for food, _ in typed),
            )
        )
    return DishFoodRepository(items, dish_views)
