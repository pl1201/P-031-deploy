"""Test hồi quy cho bộ lọc ứng viên nguyên liệu của `retrieve_context`.

Ticket: DAT-24. Bug gốc (phát hiện 2026-08-08): bộ lọc dùng `id < 100_000` làm
proxy cho "thuộc khối USDA bulk". Script merge NIN 2017 cấp id nối tiếp dãy
`fdc_id` nên 82 thực phẩm Việt Nam THẬT của Viện Dinh dưỡng nhận id ≥ 1.105.898
và bị loại nhầm khỏi ứng viên CP-SAT — đúng nhóm nguyên liệu (vừng, cà rốt,
giá đậu, cải thìa…) mà công thức món Việt cần nhất.
"""

from __future__ import annotations

from src.agents.nodes.core import (
    USDA_BULK_ID_THRESHOLD,
    USDA_BULK_SOURCE,
    make_retrieve_context,
)
from src.clinical.models import Condition, ConditionCode, PatientProfile
from src.clinical.seeds import load_food_repository


def _candidates(profile: PatientProfile) -> list:
    foods = load_food_repository()
    node = make_retrieve_context(foods)
    return node({"profile": profile})["candidate_foods"]


def _profile(**kwargs) -> PatientProfile:
    base: dict = dict(
        patient_id="test-dat24",
        age=55,
        sex="male",
        weight_kg=65.0,
        height_cm=165.0,
        conditions=[Condition(code=ConditionCode.T2DM)],
    )
    base.update(kwargs)
    return PatientProfile(**base)


def test_thuc_pham_nin_id_lon_van_la_ung_vien() -> None:
    """NIN id ≥ ngưỡng bulk PHẢI nằm trong ứng viên — chính là bug đã sửa."""
    got = _candidates(_profile())
    nin_id_lon = [f for f in got if f.id >= USDA_BULK_ID_THRESHOLD and f.source == "NIN"]

    assert nin_id_lon, (
        "Không có thực phẩm NIN nào với id ≥ ngưỡng bulk trong ứng viên — "
        "bộ lọc đã quay lại lọc theo id và loại nhầm thực phẩm Việt Nam."
    )
    # Vừng/mè (NIN 2017 mã 03020) là ca thật làm trượt công thức món Việt.
    assert any("Vừng" in f.name_vi for f in nin_id_lon)


def test_khoi_usda_bulk_van_bi_loai() -> None:
    """Sửa bug không được kéo theo cả ~6.850 dòng USDA bulk vào (CP-SAT chậm 30-50x)."""
    got = _candidates(_profile())
    bulk = [f for f in got if f.id >= USDA_BULK_ID_THRESHOLD and f.source == USDA_BULK_SOURCE]

    assert bulk == [], f"{len(bulk)} dòng USDA bulk lọt vào ứng viên, VD: {[f.name_vi for f in bulk[:3]]}"


def test_ung_vien_khong_it_hon_truoc_khi_sua() -> None:
    """Số ứng viên phải ≥ mức cũ (439) — sửa bug chỉ được thêm, không được bớt."""
    got = _candidates(_profile())
    chi_theo_id = [f for f in load_food_repository().all() if f.id < USDA_BULK_ID_THRESHOLD]

    assert len(got) > len(chi_theo_id)


def test_van_loai_di_ung_va_mon_khong_thich() -> None:
    """Bộ lọc mới không được làm hỏng chặn dị ứng/không thích (an toàn > số lượng)."""
    khong_loc = _candidates(_profile())
    ten_dau = khong_loc[0].name_vi

    co_loc = _candidates(_profile(dislikes=[ten_dau.lower()]))
    assert all(f.name_vi != ten_dau for f in co_loc)

    di_ung = _candidates(_profile(allergies=["sữa"]))
    assert all("sữa" not in map(str.lower, f.contains_allergens) for f in di_ung)
