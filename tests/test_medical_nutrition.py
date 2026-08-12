"""Thực phẩm y tế đặc biệt (FSMP) chỉ vào thực đơn khi bệnh nhân KHAI BÁO.

Bối cảnh: sữa dinh dưỡng y tế (id 5000-5099) là dữ liệu hợp lệ, có nguồn nhãn
nhà sản xuất, nằm ở tầng B nên `is_patient_facing_food()` cho qua — nhưng mật
độ 437-455 kcal/100 g bột khiến bộ giải rất dễ chọn nó để "khớp số", và kê một
sản phẩm thương mại bệnh nhân không dùng là tiến gần tới chỉ định
(CLAUDE.md §3). Các test dưới đây khoá hành vi fail-closed đó.
"""

from __future__ import annotations

from src.clinical.medical_nutrition import (
    is_declared,
    is_eligible_candidate,
    is_medical_nutrition_food,
)
from src.clinical.models import PatientProfile, Sex
from src.clinical.seeds import load_food_repository


def _profile(**kw) -> PatientProfile:
    base = dict(patient_id="P1", age=55, sex=Sex.MALE, height_cm=165, weight_kg=65)
    return PatientProfile(**{**base, **kw})


class TestIsMedicalNutritionFood:
    def test_khoi_5000_5099_la_thuc_pham_y_te(self):
        assert is_medical_nutrition_food(5000) is True
        assert is_medical_nutrition_food(5099) is True

    def test_ngoai_khoang_thi_khong(self):
        assert is_medical_nutrition_food(4999) is False
        assert is_medical_nutrition_food(5100) is False
        assert is_medical_nutrition_food(2) is False

    def test_none_khong_lam_sap(self):
        assert is_medical_nutrition_food(None) is False


class TestIsDeclared:
    """Bệnh nhân khai 'glucerna', dữ liệu ghi 'Sữa bột Glucerna (bột, chưa pha)'."""

    def test_khai_ten_ngan_khop_ten_day_du_trong_du_lieu(self):
        foods = load_food_repository()
        glucerna = foods.get(5000)
        assert glucerna is not None
        assert is_declared(glucerna, ["glucerna"]) is True

    def test_khop_qua_alias(self):
        foods = load_food_repository()
        nutren = foods.get(5001)
        assert nutren is not None
        assert is_declared(nutren, ["Nutren Diabetik"]) is True

    def test_khai_san_pham_khac_thi_khong_khop(self):
        """KHÔNG fuzzy match — gán nhầm sản phẩm làm mọi con số kcal/kali sai."""
        foods = load_food_repository()
        glucerna = foods.get(5000)
        assert is_declared(glucerna, ["nutren diabetes"]) is False

    def test_danh_sach_rong_hoac_toan_khoang_trang_thi_khong_khop(self):
        foods = load_food_repository()
        glucerna = foods.get(5000)
        assert is_declared(glucerna, []) is False
        assert is_declared(glucerna, ["", "   "]) is False


class TestIsEligibleCandidate:
    def test_thuc_pham_thuong_luon_duoc_vao_ung_vien(self):
        foods = load_food_repository()
        com = foods.get(2)  # Cơm tẻ
        assert com is not None
        assert is_eligible_candidate(com, []) is True

    def test_fsmp_khong_khai_thi_bi_loai(self):
        foods = load_food_repository()
        glucerna = foods.get(5000)
        assert is_eligible_candidate(glucerna, []) is False

    def test_fsmp_da_khai_thi_duoc_vao(self):
        foods = load_food_repository()
        glucerna = foods.get(5000)
        assert is_eligible_candidate(glucerna, ["glucerna"]) is True

    def test_khai_san_pham_A_khong_mo_cua_cho_san_pham_B(self):
        """Khai Glucerna KHÔNG được kéo theo Nutren Diabetes vào thực đơn."""
        foods = load_food_repository()
        nutren = foods.get(5001)
        assert is_eligible_candidate(nutren, ["glucerna"]) is False


class TestProfileDefault:
    def test_ho_so_mac_dinh_khong_khai_gi(self):
        """Fail closed — hồ sơ cũ (không có field này) không mở cửa cho FSMP."""
        assert _profile().medical_nutrition == []

    def test_chuan_hoa_ve_chu_thuong_bo_khoang_trang(self):
        p = _profile(medical_nutrition=["  Glucerna  ", ""])
        assert p.medical_nutrition == ["glucerna"]


class TestRetrieveContextGate:
    """Kiểm chứng ở đúng node dựng tập ứng viên, không chỉ ở hàm thuần.

    CỐ Ý dùng repo NHỎ (6 dòng) thay vì toàn bộ seed. Với seed thật, Glucerna
    xếp hạng ~43 theo kcal nên `_top_k_candidates` (quota 14/bảng xếp hạng) đã
    cắt nó khỏi ứng viên rồi — test trên seed đầy đủ sẽ XANH kể cả khi gate bị
    xoá, tức không kiểm được gì. Repo nhỏ (≤ RETRIEVAL_TOP_K) không bị cắt, nên
    hiệu lực của gate hiện ra thật.
    """

    def _small_repo(self):
        from src.clinical.nutrition import InMemoryFoodRepository

        seed = load_food_repository()
        ids = [2, 19, 65, 123, 5000, 5001]  # cơm, thịt lợn, rau muống, sữa tươi, 2 FSMP
        items = [f for fid in ids if (f := seed.get(fid)) is not None]
        assert len(items) == len(ids), "seed thiếu food_id dùng cho fixture"
        return InMemoryFoodRepository(items)

    def _candidate_ids(self, profile: PatientProfile) -> list[int]:
        from src.agents.nodes.core import make_retrieve_context

        node = make_retrieve_context(self._small_repo())
        return node({"profile": profile})["candidate_ids"]

    def test_fsmp_khong_lot_vao_ung_vien_khi_chua_khai(self):
        ids = self._candidate_ids(_profile())
        assert 5000 not in ids
        assert 5001 not in ids

    def test_fsmp_da_khai_thi_vao_duoc_ung_vien(self):
        """Chiều ngược lại — chứng minh chính gate quyết định, không phải top-k."""
        ids = self._candidate_ids(_profile(medical_nutrition=["glucerna"]))
        assert 5000 in ids
        assert 5001 not in ids, "khai Glucerna không được kéo theo Nutren"

    def test_thuc_pham_thuong_khong_bi_anh_huong(self):
        """Bộ lọc mới không được vô tình cắt thực phẩm thường."""
        ids = self._candidate_ids(_profile())
        assert {2, 19, 65, 123} <= set(ids)
