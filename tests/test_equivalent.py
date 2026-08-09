"""Test thực đơn tương đương từ tủ lạnh (P2/AGT-12) — src/agents/equivalent.py.

LLM: NO — dữ liệu seed thật, không mock, giống tests/test_cpsat_optimizer.py.
"""

from __future__ import annotations

import pytest

from src.agents.equivalent import (
    EQUIVALENT_TOLERANCE,
    STAPLE_NAMES_VI,
    resolve_staple_food_ids,
    solve_equivalent,
)
from src.agents.nodes.core import USDA_BULK_ID_THRESHOLD
from src.agents.optimizer import CPSATMenuOptimizer, _eligible_dishes
from src.clinical.models import ActivityLevel, Condition, ConditionCode, PatientProfile, Sex
from src.clinical.nutrition import compute_nutrition
from src.clinical.rules import compute_targets
from src.clinical.seeds import load_food_repository, load_vn_dishes
from src.clinical.validator import validate_menu


@pytest.fixture(scope="module")
def foods():
    return load_food_repository()


@pytest.fixture(scope="module")
def menu_candidates(foods):
    return [f for f in foods.all() if f.id < USDA_BULK_ID_THRESHOLD]


@pytest.fixture(scope="module")
def profile() -> PatientProfile:
    return PatientProfile(
        patient_id="BN-EQUIV-01",
        age=55,
        sex=Sex.MALE,
        height_cm=165,
        weight_kg=70,
        activity_level=ActivityLevel.LIGHT,
        conditions=[Condition(code=ConditionCode.T2DM)],
    )


@pytest.fixture(scope="module")
def base_plan(foods, menu_candidates, profile):
    """Thực đơn gốc thật — dùng làm điểm tựa cho dải base±tolerance."""
    targets = compute_targets(profile)
    draft = CPSATMenuOptimizer().generate(profile, targets, menu_candidates, feedback=None)
    assert draft.all_items(), "cần thực đơn gốc giải được để test thực đơn tương đương"
    nutrition = compute_nutrition(draft, foods)
    return targets, nutrition


def test_resolve_staple_food_ids_khop_dung_ten_curated(foods):
    """Mỗi tên trong STAPLE_NAMES_VI (DEC-018) phải khớp CHÍNH XÁC 1 dòng thật."""
    ids = resolve_staple_food_ids(foods)
    assert len(ids) == len(STAPLE_NAMES_VI), "thiếu ít nhất 1 nguyên liệu chủ lực trong seed hiện tại"
    for food_id in ids:
        assert foods.get(food_id) is not None


def test_giai_duoc_khi_tu_lanh_du_nguyen_lieu(foods, menu_candidates, profile, base_plan):
    """Tủ lạnh = TOÀN BỘ ứng viên (trường hợp tốt nhất) — phải giải được, và kết
    quả nằm trong CẢ ngưỡng lâm sàng lẫn dải base±tolerance."""
    targets, (base_nutrition) = base_plan
    pantry_ids = {f.id for f in menu_candidates}
    dishes = _eligible_dishes(load_vn_dishes(), foods, profile)

    result = solve_equivalent(base_nutrition, targets, pantry_ids, menu_candidates, dishes, foods)

    assert result.draft is not None, result.reason_vi
    nutrition = compute_nutrition(result.draft, foods)
    violations = validate_menu(nutrition, targets)
    assert not any(v.blocking for v in violations), "thực đơn tương đương không được vi phạm hard rule"

    for field in ("kcal", "carb_g", "na_mg"):
        base_value = base_nutrition.value_of(field)
        actual = nutrition.value_of(field)
        lo, hi = base_value * (1 - EQUIVALENT_TOLERANCE), base_value * (1 + EQUIVALENT_TOLERANCE)
        # so_sánh nới biên nhỏ cho sai số làm tròn 2 chữ số của compute_nutrition.
        assert lo - 1 <= actual <= hi + 1, f"{field}: {actual} ngoài dải ±{EQUIVALENT_TOLERANCE:.0%} quanh {base_value}"


def test_vo_nghiem_khi_tu_lanh_qua_ngheo(foods, profile, base_plan):
    """Tủ lạnh chỉ có 1 món (không đủ đa dạng) — PHẢI trả None + lý do tường
    minh, KHÔNG được trả một phần thực đơn."""
    targets, base_nutrition = base_plan
    one_food = next(f for f in foods.all() if f.id < USDA_BULK_ID_THRESHOLD)
    pantry_ids = {one_food.id}

    result = solve_equivalent(base_nutrition, targets, pantry_ids, [one_food], [], foods)

    assert result.draft is None
    assert result.reason_vi is not None and result.reason_vi.strip()


def test_tu_lanh_rong_tra_ve_ly_do_khong_du_nguyen_lieu(foods, profile, base_plan):
    targets, base_nutrition = base_plan
    result = solve_equivalent(base_nutrition, targets, set(), [], [], foods)
    assert result.draft is None
    assert result.reason_vi is not None


def test_khong_giao_nhau_giua_tolerance_va_nguong_lam_sang(foods, profile, base_plan):
    """tolerance=0 ép dải trùng khít thực đơn gốc — với dữ liệu rời rạc theo
    GRAM_STEP gần như chắc chắn không giải được đúng khít, nhưng KHÔNG được
    trả thực đơn một phần: hoặc None+lý do, hoặc một lời giải hợp lệ thật."""
    targets, base_nutrition = base_plan
    pantry_ids = {f.id for f in foods.all() if f.id < USDA_BULK_ID_THRESHOLD}
    dishes = _eligible_dishes(load_vn_dishes(), foods, profile)
    candidates = [f for f in foods.all() if f.id < USDA_BULK_ID_THRESHOLD]

    result = solve_equivalent(base_nutrition, targets, pantry_ids, candidates, dishes, foods, tolerance=0.0)

    if result.draft is not None:
        nutrition = compute_nutrition(result.draft, foods)
        violations = validate_menu(nutrition, targets)
        assert not any(v.blocking for v in violations)
    else:
        assert result.reason_vi
