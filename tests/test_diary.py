"""Test cho tổng hợp nhật ký ăn uống — BE-07.

Đây là bộ test QUAN TRỌNG NHẤT của luồng nhật ký: nó khoá lại lời hứa "thà nói
không biết còn hơn đoán". Nếu một ngày nào đó ai đó "cho tiện" mà điền 0 cho
món chưa tra được, hoặc báo "đạt ngưỡng" khi còn món chưa tra, các test này
phải đỏ.
"""

from __future__ import annotations

import pytest

from src.clinical.diary import LoggedFood, Verdict, summarize_day
from src.clinical.models import (
    ClinicalTargets,
    FoodItem,
    MealSlot,
    NutrientTarget,
)
from src.clinical.nutrition import InMemoryFoodRepository


def _food(fid: int, name: str, *, na_mg: float, kcal: float = 100.0) -> FoodItem:
    return FoodItem(
        id=fid,
        name_vi=name,
        kcal_100g=kcal,
        protein_g=5.0,
        carb_g=10.0,
        fat_g=2.0,
        fiber_g=1.0,
        na_mg=na_mg,
        k_mg=100.0,
        p_mg=50.0,
        source="NIN",
        source_ref="NIN 2017, test",
    )


@pytest.fixture
def repo() -> InMemoryFoodRepository:
    # Nước mắm rất mặn (Na thật ~7720 mg/100 g) để dựng ca vượt trần dễ đọc.
    return InMemoryFoodRepository(
        [
            _food(1, "Cơm tẻ", na_mg=1.0),
            _food(2, "Nước mắm", na_mg=7720.0),
        ]
    )


@pytest.fixture
def targets() -> ClinicalTargets:
    return ClinicalTargets(
        patient_id="test-diary",
        bmr_kcal=1400.0,
        tdee_kcal=1900.0,
        targets={
            "na_mg": NutrientTarget(nutrient="na_mg", max_value=2000.0, unit="mg", rule_ids=["BASE-NA-01"]),
            "protein_g": NutrientTarget(nutrient="protein_g", min_value=60.0, unit="g", rule_ids=["BASE-PRO-01"]),
        },
    )


def _na_verdict(summary) -> Verdict:
    return next(v.verdict for v in summary.verdicts if v.nutrient == "na_mg")


def _protein_verdict(summary) -> Verdict:
    return next(v.verdict for v in summary.verdicts if v.nutrient == "protein_g")


# --- Bất đối xứng kết luận (lõi của thiết kế) ------------------------------


def test_vuot_tran_thi_van_ket_luan_duoc_du_con_mon_chua_tra(repo, targets) -> None:
    """Cận dưới đã vượt trần ⇒ ăn thêm chỉ vượt nhiều hơn ⇒ kết luận hợp lệ."""
    logs = [
        LoggedFood("l1", food_id=2, grams=50.0, slot=MealSlot.LUNCH),  # Na = 3860 mg
        LoggedFood("l2", food_id=None, grams=None, free_text_vi="canh rau tập tàng"),
    ]
    summary = summarize_day(logs, targets, repo)

    assert _na_verdict(summary) is Verdict.EXCEEDED
    assert any(v.kind == "over" and v.nutrient == "na_mg" for v in summary.violations)


def test_chua_vuot_tran_nhung_thieu_du_lieu_thi_cam_ket_luan_dat(repo, targets) -> None:
    """Ca dễ sai nhất: tổng còn thấp KHÔNG có nghĩa là đạt — phần chưa tra có thể đủ để vượt."""
    logs = [
        LoggedFood("l1", food_id=1, grams=200.0, slot=MealSlot.LUNCH),  # Na = 2 mg
        LoggedFood("l2", food_id=None, grams=None, free_text_vi="cá kho tộ của mẹ"),
    ]
    summary = summarize_day(logs, targets, repo)

    assert _na_verdict(summary) is Verdict.INSUFFICIENT_DATA
    assert _na_verdict(summary) is not Verdict.WITHIN


def test_thieu_du_lieu_thi_khong_bao_thieu_chat(repo, targets) -> None:
    """Đối xứng cho ngưỡng min: chưa đạt min mà còn món chưa tra ⇒ không kết luận 'thiếu'."""
    logs = [
        LoggedFood("l1", food_id=1, grams=100.0, slot=MealSlot.LUNCH),  # protein = 5 g
        LoggedFood("l2", food_id=None, grams=None, free_text_vi="thịt gì đó kho"),
    ]
    summary = summarize_day(logs, targets, repo)

    assert _protein_verdict(summary) is Verdict.INSUFFICIENT_DATA
    assert not any(v.kind == "under" for v in summary.violations), (
        "Báo 'thiếu protein' khi chưa biết món còn lại là kết luận sai — món đó có thể là thịt."
    )


def test_du_du_lieu_thi_ket_luan_binh_thuong_ca_hai_chieu(repo, targets) -> None:
    logs = [LoggedFood("l1", food_id=1, grams=100.0, slot=MealSlot.LUNCH)]
    summary = summarize_day(logs, targets, repo)

    assert summary.is_complete
    assert _na_verdict(summary) is Verdict.WITHIN
    assert _protein_verdict(summary) is Verdict.BELOW_MIN
    assert any(v.kind == "under" and v.nutrient == "protein_g" for v in summary.violations)


# --- Không bịa số ----------------------------------------------------------


def test_mon_chua_tra_duoc_khong_duoc_cong_thanh_0(repo, targets) -> None:
    """Món OOV phải nằm ngoài phép cộng, không phải cộng vào với giá trị 0."""
    chi_com = summarize_day([LoggedFood("l1", food_id=1, grams=100.0, slot=MealSlot.LUNCH)], targets, repo)
    them_oov = summarize_day(
        [
            LoggedFood("l1", food_id=1, grams=100.0, slot=MealSlot.LUNCH),
            LoggedFood("l2", food_id=None, grams=None, free_text_vi="món lạ"),
        ],
        targets,
        repo,
    )
    # Con số giống hệt nhau — nhưng KẾT LUẬN thì khác.
    assert chi_com.nutrition.na_mg == them_oov.nutrition.na_mg
    assert chi_com.is_complete and not them_oov.is_complete


def test_canh_bao_oov_khong_co_con_so(repo, targets) -> None:
    """`actual`/`limit` phải là None — không được nhồi 0.0 để lấp chỗ trống."""
    logs = [LoggedFood("l1", food_id=None, grams=None, free_text_vi="canh rau tập tàng bà Bảy")]
    summary = summarize_day(logs, targets, repo)

    oov = [v for v in summary.violations if v.kind == "unmatched_food"]
    assert len(oov) == 1
    assert oov[0].actual is None and oov[0].limit is None and oov[0].unit is None
    assert "canh rau tập tàng bà Bảy" in oov[0].message_vi
    assert oov[0].food_log_id == "l1"


def test_biet_mon_nhung_khong_ro_khau_phan_van_la_chua_du_du_lieu(repo, targets) -> None:
    """Biết ăn gì mà không biết bao nhiêu thì không cộng được — PRD FR-11."""
    logs = [LoggedFood("l1", food_id=2, grams=None, free_text_vi="nước mắm, không rõ bao nhiêu")]
    summary = summarize_day(logs, targets, repo)

    assert summary.unmatched_count == 1
    assert summary.nutrition is None
    assert all(v.verdict is Verdict.INSUFFICIENT_DATA for v in summary.verdicts)


def test_khong_co_mon_nao_tra_duoc_thi_moi_chat_deu_khong_ket_luan(repo, targets) -> None:
    logs = [LoggedFood("l1", food_id=None, grams=None, free_text_vi="bún gì đó")]
    summary = summarize_day(logs, targets, repo)

    assert summary.nutrition is None
    assert summary.coverage == 0.0
    assert {v.verdict for v in summary.verdicts} == {Verdict.INSUFFICIENT_DATA}


def test_coverage_phan_anh_dung_ty_le(repo, targets) -> None:
    logs = [
        LoggedFood("l1", food_id=1, grams=100.0, slot=MealSlot.BREAKFAST),
        LoggedFood("l2", food_id=1, grams=100.0, slot=MealSlot.LUNCH),
        LoggedFood("l3", food_id=None, grams=None, free_text_vi="chè"),
        LoggedFood("l4", food_id=None, grams=None, free_text_vi="bánh"),
    ]
    summary = summarize_day(logs, targets, repo)

    assert summary.matched_count == 2
    assert summary.unmatched_count == 2
    assert summary.coverage == 0.5
    assert len([v for v in summary.violations if v.kind == "unmatched_food"]) == 2


def test_nhat_ky_rong_khong_no(repo, targets) -> None:
    summary = summarize_day([], targets, repo)
    assert summary.total_count == 0
    assert summary.coverage == 0.0
    assert not summary.is_complete
