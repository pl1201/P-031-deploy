"""Test schema FoodItem — cột đường tự do + nguồn GI riêng (ticket DAT-07).

⚠️ Mọi số liệu ở đây là DỮ LIỆU GIẢ để test logic, không dùng lâm sàng.
"""

from __future__ import annotations

import pytest

from src.clinical.models import FoodItem

FAKE_REF = "TEST-FIXTURE (dữ liệu giả)"


def _rice(**overrides) -> FoodItem:
    """Một dòng thực phẩm hợp lệ (cơm tẻ giả) để chỉnh từng field trong test."""
    base = dict(
        id=1,
        name_vi="Cơm tẻ (giả)",
        kcal_100g=130,
        protein_g=2.7,
        carb_g=28.0,
        fat_g=0.3,
        fiber_g=0.4,
        na_mg=1,
        k_mg=35,
        p_mg=43,
        purine_mg=15,
        source="curated",
        source_ref=FAKE_REF,
    )
    base.update(overrides)
    return FoodItem(**base)


class TestAvailableCarb:
    def test_available_carb_la_carb_tru_xo(self):
        item = _rice(carb_g=28.0, fiber_g=0.4)
        assert item.available_carb_g == pytest.approx(27.6)

    def test_available_carb_khong_bao_gio_am(self):
        # Sai số nguồn: xơ ghi lớn hơn carb → phải kẹp về 0, không trả trị âm
        item = _rice(carb_g=2.0, fiber_g=5.0)
        assert item.available_carb_g == 0.0


class TestGlycemicLoad:
    def test_gl_tinh_dung_tren_carb_kha_dung(self):
        # GI 73, carb khả dụng 27.6 g/100 g, khẩu phần 150 g
        # portion = 27.6 * 1.5 = 41.4 g; GL = 73 * 41.4 / 100 = 30.222
        item = _rice(gi_index=73, gi_source="Atkinson2021", gi_source_ref="Atkinson 2021, mục 'rice, white'")
        assert item.glycemic_load(150) == pytest.approx(30.222)

    def test_gl_tra_none_khi_thieu_gi(self):
        """Hợp đồng suy-giảm-mềm: thiếu GI trả None, KHÔNG phải 0."""
        item = _rice()  # gi_index mặc định None
        assert item.gi_index is None
        assert item.glycemic_load(150) is None


class TestGiProvenanceRule2:
    def test_gi_khong_co_nguon_thi_bi_chan(self):
        """RULE-2: có trị GI mà không dẫn nguồn GI riêng → không tạo được."""
        with pytest.raises(ValueError, match="RULE-2"):
            _rice(gi_index=73)  # thiếu gi_source + gi_source_ref

    def test_gi_thieu_source_ref_bi_chan(self):
        with pytest.raises(ValueError, match="RULE-2"):
            _rice(gi_index=73, gi_source="Mai2001_VN")  # thiếu gi_source_ref

    def test_gi_source_ref_placeholder_bi_chan(self):
        with pytest.raises(ValueError):
            _rice(gi_index=73, gi_source="Mai2001_VN", gi_source_ref="TODO")

    def test_gi_day_du_nguon_thi_hop_le(self):
        item = _rice(
            gi_index=53,
            gi_source="Mai2001_VN",
            gi_source_ref="Mai et al. 2001, EJCN — phở bò",
        )
        assert item.gi_index == 53
        assert item.gi_source == "Mai2001_VN"


class TestSugar:
    def test_sugar_mac_dinh_none(self):
        assert _rice().sugar_g is None

    def test_sugar_khong_duoc_lon_hon_carb(self):
        with pytest.raises(ValueError, match="tập con"):
            _rice(carb_g=28.0, sugar_g=30.0)

    def test_sugar_hop_le_khi_nho_hon_carb(self):
        item = _rice(carb_g=28.0, sugar_g=0.1)
        assert item.sugar_g == pytest.approx(0.1)
