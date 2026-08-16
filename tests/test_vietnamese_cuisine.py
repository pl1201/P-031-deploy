"""Vietnamese meal-structure guardrails stay separate from clinical rules."""

from __future__ import annotations

from src.agents.nodes.core import make_culinary_validate
from src.agents.vietnamese_cuisine import allowed_in_slot, preferred_in_slot, slot_candidates
from src.clinical.dish_roles import DishRole
from src.clinical.models import DishCandidate, MealSlot, MenuDraft, MenuItem, PlannedDish


def _dish(dish_id: str, name: str, *roles: DishRole) -> DishCandidate:
    return DishCandidate(
        dish_id=dish_id,
        name_vi=name,
        roles=roles,
        ingredients=[MenuItem(food_id=1, grams=100)],
    )


def _draft(**slots: str) -> MenuDraft:
    return MenuDraft(
        planned_dishes={
            MealSlot(slot): [PlannedDish(dish_id=dish_id, serving_grams=100)] for slot, dish_id in slots.items()
        }
    )


def test_slot_policy_uu_tien_mon_nuoc_sang_va_com_trua_toi():
    pho = _dish("PHO", "Phở gà", DishRole.ONE_DISH)
    com = _dish("COM", "Cơm tấm", DishRole.ONE_DISH)
    banh_mi = _dish("BANH-MI", "Bánh mì thịt", DishRole.ONE_DISH)

    selected = slot_candidates([pho, com, banh_mi], prefer=True)

    assert selected[MealSlot.BREAKFAST] == [pho]
    assert selected[MealSlot.LUNCH] == [com]
    assert selected[MealSlot.DINNER] == [com]


def test_do_uong_trang_mieng_va_mon_nuoc_toi_bi_chan():
    coffee = _dish("CA-PHE", "Cà phê sữa đá", DishRole.BEVERAGE)
    che = _dish("CHE", "Chè đỗ đen", DishRole.DESSERT)
    bun = _dish("BUN", "Bún bò Huế", DishRole.ONE_DISH)

    assert not allowed_in_slot(coffee, MealSlot.BREAKFAST)
    assert not allowed_in_slot(che, MealSlot.LUNCH)
    assert allowed_in_slot(bun, MealSlot.BREAKFAST)
    assert not allowed_in_slot(bun, MealSlot.DINNER)
    assert preferred_in_slot(bun, MealSlot.BREAKFAST)


def test_banh_chung_banh_chien_va_xoi_khong_vao_slot_hang_ngay_sai():
    banh_chung = _dish("CHUNG", "Bánh chưng", DishRole.ONE_DISH)
    banh_bao_chien = _dish("BAO", "Bánh bao chiên", DishRole.ONE_DISH)
    xoi = _dish("XOI", "Xôi đỗ xanh", DishRole.STAPLE, DishRole.ONE_DISH)

    assert not allowed_in_slot(banh_chung, MealSlot.LUNCH)
    assert not allowed_in_slot(banh_bao_chien, MealSlot.BREAKFAST)
    assert not allowed_in_slot(xoi, MealSlot.SNACK)


def test_culinary_gate_chan_mon_nuoc_lap_va_bua_toi_khong_phai_com():
    pho = _dish("PHO", "Phở gà", DishRole.ONE_DISH)
    bun = _dish("BUN", "Bún bò Huế", DishRole.ONE_DISH)
    banh_mi = _dish("BANH-MI", "Bánh mì thịt", DishRole.ONE_DISH)
    gate = make_culinary_validate([pho, bun, banh_mi])

    result = gate(
        {
            "draft_menu": _draft(breakfast="PHO", lunch="BANH-MI", dinner="BUN"),
            "safety_findings": [],
        }
    )

    codes = {finding.code for finding in result["safety_findings"]}
    assert "CULINARY_SLOT_MISMATCH" in codes  # món nước không được làm bữa tối
    assert "CULINARY_WATER_DISH_OVERUSE" in codes
    assert "CULINARY_DINNER_NOT_RICE_PRIORITY" in codes


def test_culinary_gate_chan_lap_lai_mot_mon_chinh():
    com = _dish("COM", "Cơm tấm", DishRole.ONE_DISH)
    pho = _dish("PHO", "Phở gà", DishRole.ONE_DISH)
    gate = make_culinary_validate([com, pho])

    result = gate(
        {
            "draft_menu": _draft(breakfast="PHO", lunch="COM", dinner="COM"),
            "safety_findings": [],
        }
    )

    assert "CULINARY_REPEATED_DISH" in {finding.code for finding in result["safety_findings"]}


def test_culinary_gate_chan_nguyen_lieu_roi_o_bua_chinh():
    pho = _dish("PHO", "Phở gà", DishRole.ONE_DISH)
    gate = make_culinary_validate([pho])
    draft = MenuDraft(
        items={MealSlot.BREAKFAST: [MenuItem(food_id=1, grams=100), MenuItem(food_id=2, grams=150)]},
        planned_dishes={MealSlot.BREAKFAST: [PlannedDish(dish_id="PHO", serving_grams=100)]},
    )

    result = gate({"draft_menu": draft, "safety_findings": []})

    assert "CULINARY_RAW_MAIN_FOOD" in {finding.code for finding in result["safety_findings"]}


def test_culinary_gate_khong_anh_huong_graph_khong_co_catalog_mon():
    gate = make_culinary_validate()
    assert gate({"safety_findings": []}) == {}
