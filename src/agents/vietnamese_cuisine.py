"""Deterministic structure rules for patient-facing Vietnamese meals.

This module owns *culinary structure*, never clinical thresholds or nutrition
math.  The core contract is deliberately narrow:

* breakfast is one familiar, complete Vietnamese breakfast, preferably a soup;
* lunch and dinner are a rice plate: rice + one protein + vegetable and/or soup;
* a snack is fruit, plain dairy, or a small nut portion.

The database currently stores cooked rice and fruit as ``FoodItem`` rows rather
than prepared ``Dish`` rows.  They are explicitly allow-listed here, so they
remain recognisable patient-facing components instead of optimiser residuals.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable

from src.clinical.dish_roles import DishRole, is_self_sufficient
from src.clinical.models import DishCandidate, FoodItem, MealSlot

_WATER_DISH_TOKENS = ("phở", "bún", "miến", "hủ tiếu", "cháo", "mì quảng", "mì nước")
_RICE_DISH_TOKENS = ("cơm", "cơm tấm")
_FESTIVAL_DISH_TOKENS = ("bánh chưng", "bánh tét")
_FRIED_DISH_TOKENS = ("chiên", "rán", "rang")
_OCCASIONAL_DISH_TOKENS = ("cháo lòng", "bún đậu")
_HEAVY_SNACK_TOKENS = _WATER_DISH_TOKENS + ("xôi", "bánh chưng", "bánh tét", "cơm", "bánh mì")
_UNSUITABLE_DAILY_COMPONENT_TOKENS = ("giò", "dồi", "nộm tai", "nem", "thịt xiên")
_NON_MEAL_ROLES = frozenset({DishRole.BEVERAGE, DishRole.DESSERT, DishRole.CONDIMENT})
_MAIN_SLOTS = frozenset({MealSlot.BREAKFAST, MealSlot.LUNCH, MealSlot.DINNER})
_SIMPLE_SNACK_CATEGORIES = frozenset({"trái cây", "hạt", "sữa", "sữa & trứng"})
_SNACK_NAME_TOKENS = ("cam", "bưởi", "ổi", "táo", "chuối", "thanh long", "sữa chua", "hạnh nhân", "óc chó")
_RICE_FOOD_NAMES = frozenset({"cơm tẻ", "cơm trắng", "cơm gạo lứt"})


def _text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()


def _name(dish: DishCandidate) -> str:
    return _text(dish.name_vi)


def _food_name(food: FoodItem) -> str:
    return _text(food.name_vi)


def is_water_dish(dish: DishCandidate) -> bool:
    """Whether a dish is a Vietnamese noodle/soup/porridge meal."""
    return any(token in _name(dish) for token in _WATER_DISH_TOKENS)


def is_rice_dish(dish: DishCandidate) -> bool:
    """Whether a complete dish is rice-centred for lunch/dinner."""
    return any(token in _name(dish) for token in _RICE_DISH_TOKENS)


def is_festival_dish(dish: DishCandidate) -> bool:
    return any(token in _name(dish) for token in _FESTIVAL_DISH_TOKENS)


def is_fried_dish(dish: DishCandidate) -> bool:
    return any(token in _name(dish) for token in _FRIED_DISH_TOKENS)


def is_rice_food(food: FoodItem) -> bool:
    """Only cooked rice may be a raw ``FoodItem`` in a main meal."""
    return _food_name(food) in _RICE_FOOD_NAMES


def is_simple_snack_food(food: FoodItem) -> bool:
    """Allow only displayable fruit, plain dairy or nuts for a snack."""
    category = _text(food.category or "")
    return category in _SIMPLE_SNACK_CATEGORIES or any(token in _food_name(food) for token in _SNACK_NAME_TOKENS)


def raw_food_allowed_in_slot(food: FoodItem, slot: MealSlot) -> bool:
    """Explicit food components allowed in patient-facing meal cards."""
    if slot in {MealSlot.LUNCH, MealSlot.DINNER}:
        return is_rice_food(food)
    return slot is MealSlot.SNACK and is_simple_snack_food(food)


def is_patient_meal_dish(dish: DishCandidate) -> bool:
    """Complete dish fit for a standalone Vietnamese meal."""
    roles = set(dish.roles)
    return bool(roles) and not bool(roles & _NON_MEAL_ROLES) and is_self_sufficient(dish.roles)


def is_main_component(dish: DishCandidate) -> bool:
    """Reviewed protein/vegetable/soup component suitable for a rice plate."""
    roles = set(dish.roles)
    component_roles = {DishRole.PROTEIN, DishRole.VEGETABLE, DishRole.SOUP}
    return (
        bool(roles & component_roles)
        and not bool(roles & {DishRole.STAPLE, DishRole.ONE_DISH})
        and not bool(roles & _NON_MEAL_ROLES)
        and not is_festival_dish(dish)
        and not is_fried_dish(dish)
        and not any(token in _name(dish) for token in _UNSUITABLE_DAILY_COMPONENT_TOKENS)
    )


def is_primary_dish(dish: DishCandidate) -> bool:
    return is_patient_meal_dish(dish) or DishRole.STAPLE in dish.roles


def allowed_in_slot(dish: DishCandidate, slot: MealSlot) -> bool:
    """Hard compatibility for one complete prepared dish."""
    if not is_patient_meal_dish(dish) or is_festival_dish(dish) or is_fried_dish(dish):
        return False
    if any(token in _name(dish) for token in _OCCASIONAL_DISH_TOKENS):
        return False
    if slot is MealSlot.SNACK:
        return not any(token in _name(dish) for token in _HEAVY_SNACK_TOKENS)
    if slot not in _MAIN_SLOTS:
        return False
    return not (slot is MealSlot.DINNER and is_water_dish(dish))


def allowed_component_in_slot(dish: DishCandidate, slot: MealSlot) -> bool:
    """A protein/vegetable/soup component belongs only on lunch/dinner trays."""
    return slot in {MealSlot.LUNCH, MealSlot.DINNER} and is_main_component(dish) and not is_fried_dish(dish)


def preferred_in_slot(dish: DishCandidate, slot: MealSlot) -> bool:
    if not allowed_in_slot(dish, slot):
        return False
    if slot is MealSlot.BREAKFAST:
        return is_water_dish(dish)
    if slot in {MealSlot.LUNCH, MealSlot.DINNER}:
        return is_rice_dish(dish)
    return False


def has_meal_blueprint_catalog(dishes: Iterable[DishCandidate], foods: Iterable[FoodItem]) -> bool:
    """Whether the catalog can form a safe everyday Vietnamese meal pattern."""
    dish_list = list(dishes)
    return (
        any(allowed_in_slot(dish, MealSlot.BREAKFAST) for dish in dish_list)
        and any(
            DishRole.PROTEIN in dish.roles and allowed_component_in_slot(dish, MealSlot.LUNCH) for dish in dish_list
        )
        and any(
            (DishRole.VEGETABLE in dish.roles or DishRole.SOUP in dish.roles)
            and allowed_component_in_slot(dish, MealSlot.LUNCH)
            for dish in dish_list
        )
        and any(is_rice_food(food) for food in foods)
        and any(is_simple_snack_food(food) for food in foods)
    )


def slot_candidates(
    dishes: Iterable[DishCandidate], *, prefer: bool, include_components: bool = False
) -> dict[MealSlot, list[DishCandidate]]:
    """Return role-filtered candidates for legacy selector paths.

    The CP-SAT blueprint path uses role-specific constraints in ``optimizer``;
    this helper remains the catalog boundary for Gemini and focused tests.
    """
    all_dishes = list(dishes)
    out: dict[MealSlot, list[DishCandidate]] = {}
    for slot in _MAIN_SLOTS:
        primary = [dish for dish in all_dishes if allowed_in_slot(dish, slot)]
        components = [
            dish
            for dish in all_dishes
            if include_components and allowed_component_in_slot(dish, slot) and not is_patient_meal_dish(dish)
        ]
        preferred = [dish for dish in primary if preferred_in_slot(dish, slot)]
        out[slot] = (preferred if prefer and preferred else primary) + components
    out[MealSlot.SNACK] = [dish for dish in all_dishes if allowed_in_slot(dish, MealSlot.SNACK)]
    return out
