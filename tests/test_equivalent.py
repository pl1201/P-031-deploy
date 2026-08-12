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


class TestChatThieuDuLieuKhongApDaiTuongDuong:
    """Chất có tổng KHÔNG ĐẦY ĐỦ thì chỉ giữ ngưỡng lâm sàng, bỏ dải ±tolerance.

    Bug gốc (phát hiện 2026-08-12 qua `test_co_scope_va_tu_lanh_day_du_thi_tu_phat_hanh`):
    `NutritionSummary` chỉ cộng món CÓ số liệu `sugar_g` rồi gắn
    `sugar_is_complete=False`, nhưng `_equivalent_bounds()` vẫn dựng dải ±10%
    quanh con số thiếu hụt đó. Đo trên ca thật: base `sugar_g=8.89` →
    dải 8.0–9.78 g cho CẢ NGÀY (rộng 1.78 g, so với 23–486 đơn vị ở chất khác)
    → bài toán vô nghiệm dù tủ lạnh khai báo TOÀN BỘ món curated.
    """

    @staticmethod
    def _summary(**kw):
        from src.clinical.models import NutritionSummary, SourceRef

        base = dict(
            kcal=2000.0, protein_g=90.0, carb_g=250.0, fat_g=60.0, fiber_g=30.0,
            na_mg=1500.0, k_mg=3000.0, p_mg=1000.0, purine_mg=100.0,
            sugar_g=8.89,
            sources=[
                SourceRef(food_id=1, name="Cơm tẻ", grams=100.0, source="NIN", source_ref="Bảng TPTP VN 2017")
            ],
        )
        return NutritionSummary(**{**base, **kw})

    @staticmethod
    def _targets(**targets):
        from src.clinical.models import ClinicalTargets

        return ClinicalTargets(patient_id="P", bmr_kcal=1600.0, tdee_kcal=2000.0, targets=targets)

    def _sugar_bounds(self, *, complete: bool):
        from src.clinical.models import NutrientTarget

        from src.agents.equivalent import _equivalent_bounds

        targets = self._targets(
            sugar_g=NutrientTarget(nutrient="sugar_g", min_value=None, max_value=67.64, unit="g")
        )
        bounds, reason = _equivalent_bounds(
            targets, self._summary(sugar_is_complete=complete), tolerance=0.10
        )
        assert reason is None, reason
        assert bounds is not None
        return bounds["sugar_g"]

    def test_sugar_thieu_du_lieu_thi_giu_nguyen_tran_lam_sang(self):
        lo, hi = self._sugar_bounds(complete=False)
        assert lo is None, "không được đặt sàn theo tổng đường thiếu hụt"
        assert hi == pytest.approx(67.64), "trần WHO cho đường tự do PHẢI giữ nguyên"

    def test_sugar_du_du_lieu_thi_van_ap_dai_tuong_duong(self):
        """Chiều ngược lại — dữ liệu đủ thì dải ±10% vẫn phải hoạt động, nếu
        không thì bản sửa đã vô hiệu hoá luôn khái niệm 'tương đương'."""
        lo, hi = self._sugar_bounds(complete=True)
        assert lo == pytest.approx(8.89 * 0.9)
        assert hi == pytest.approx(8.89 * 1.1)

    def test_khong_co_nguong_lam_sang_thi_chat_thieu_du_lieu_bi_bo_han(self):
        """Thiếu dữ liệu VÀ không có ngưỡng lâm sàng → không còn căn cứ nào,
        không được bịa ra ràng buộc."""
        from src.clinical.models import NutrientTarget

        from src.agents.equivalent import _equivalent_bounds

        targets = self._targets(
            sugar_g=NutrientTarget(nutrient="sugar_g", min_value=None, max_value=None, unit="g"),
            kcal=NutrientTarget(nutrient="kcal", min_value=1800.0, max_value=2200.0, unit="kcal"),
        )
        bounds, reason = _equivalent_bounds(
            targets, self._summary(sugar_is_complete=False), tolerance=0.10
        )
        assert reason is None
        assert "sugar_g" not in bounds
        # `bounds` khoá theo TÊN FIELD của FoodItem, không theo tên nutrient —
        # với kcal là `kcal_100g` (xem `_NUTRIENT_TO_FIELD` trong optimizer).
        assert "kcal_100g" in bounds, "chất có đủ dữ liệu vẫn phải được ràng buộc"
