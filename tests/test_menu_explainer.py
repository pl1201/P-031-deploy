"""Test lớp Explainer & Coaching — assembler tất định + guard chống bịa số."""

from __future__ import annotations

from src.clinical.menu_explainer import MenuFacts, assemble_menu_facts
from src.services.menu_explanation_guard import check_grounded


def _sample_items() -> list[dict]:
    return [
        {"name_vi": "Phở bò", "slot": "breakfast", "grams": 450.0},
        {"name_vi": "Cơm gạo lứt", "slot": "lunch", "grams": 200.0},
    ]


def _sample_targets() -> dict:
    return {
        "kcal": {"min_value": 1600.0, "max_value": 1800.0, "unit": "kcal"},
        "na_mg": {"min_value": None, "max_value": 2000.0, "unit": "mg"},
    }


def _sample_nutrition() -> dict:
    return {"kcal": 1750.0, "na_mg": 2200.0}


def _sample_violations() -> list[dict]:
    return [{"nutrient": "na_mg", "message_vi": "Natri hơi vượt ngưỡng, nên giảm nước chấm."}]


class TestAssembleMenuFacts:
    def test_lap_dung_ten_mon_va_gram(self):
        facts = assemble_menu_facts("2026-08-10", _sample_items(), _sample_targets(), _sample_nutrition(), [])
        assert [i.name_vi for i in facts.items] == ["Phở bò", "Cơm gạo lứt"]
        assert facts.items[0].grams == 450.0

    def test_gan_dung_trang_thai_over_within(self):
        facts = assemble_menu_facts("2026-08-10", _sample_items(), _sample_targets(), _sample_nutrition(), [])
        by_nutrient = {n.nutrient: n for n in facts.nutrients}
        assert by_nutrient["kcal"].status == "within"
        assert by_nutrient["na_mg"].status == "over"

    def test_lay_dung_nhan_tieng_viet(self):
        facts = assemble_menu_facts("2026-08-10", _sample_items(), _sample_targets(), _sample_nutrition(), [])
        by_nutrient = {n.nutrient: n for n in facts.nutrients}
        assert by_nutrient["na_mg"].label_vi == "Natri (muối)"

    def test_soft_notes_lay_tu_violations(self):
        facts = assemble_menu_facts(
            "2026-08-10", _sample_items(), _sample_targets(), _sample_nutrition(), _sample_violations()
        )
        assert facts.soft_notes == ["Natri hơi vượt ngưỡng, nên giảm nước chấm."]

    def test_bo_qua_field_khong_phai_so_trong_nutrition(self):
        nutrition = {**_sample_nutrition(), "sources": [{"food_id": 1}]}
        facts = assemble_menu_facts("2026-08-10", _sample_items(), _sample_targets(), nutrition, [])
        assert {n.nutrient for n in facts.nutrients} == {"kcal", "na_mg"}


class TestCheckGrounded:
    def _facts(self) -> MenuFacts:
        return assemble_menu_facts("2026-08-10", _sample_items(), _sample_targets(), _sample_nutrition(), [])

    def test_van_ban_chi_dung_so_that_thi_qua(self):
        text = "Bữa sáng có Phở bò 450 gram, năng lượng cả ngày khoảng 1750 kcal."
        result = check_grounded(text, self._facts())
        assert result.ok is True
        assert result.ungrounded_numbers == []

    def test_van_ban_bia_so_thi_bi_chan(self):
        text = "Hôm nay bạn đã giảm được 500mg natri so với hôm qua, tuyệt vời!"
        result = check_grounded(text, self._facts())
        assert result.ok is False
        assert "500" in result.ungrounded_numbers

    def test_so_luong_mon_duoc_coi_la_hop_le(self):
        text = f"Thực đơn hôm nay gồm {len(self._facts().items)} món."
        result = check_grounded(text, self._facts())
        assert result.ok is True

    def test_khop_so_thap_phan_du_viet_bang_dau_phay_hay_cham(self):
        facts = assemble_menu_facts(
            "2026-08-10",
            _sample_items(),
            {"kcal": {"min_value": None, "max_value": None, "unit": "kcal"}},
            {"kcal": 1234.5},
            [],
        )
        text = "Năng lượng thực đơn khoảng 1234,5 kcal."
        result = check_grounded(text, facts)
        assert result.ok is True
