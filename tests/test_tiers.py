"""Test DAT-23 — ranh giới tầng dữ liệu (`src/clinical/tiers.py`).

Đây là NƠI DUY NHẤT test ranh giới tầng. Các loader chỉ cần một test hồi quy
khẳng định chúng gọi đúng hàm này, không lặp lại logic biên ở từng file.
"""

from __future__ import annotations

import pytest

from src.clinical.seeds import load_vn_dishes
from src.clinical.tiers import (
    REFERENCE_FOOD_ID_MAX,
    REFERENCE_FOOD_ID_MIN,
    is_patient_facing_dish,
    is_patient_facing_food,
)


@pytest.mark.parametrize("dish_id", ["PHO-BO", "BUN-CHA", "CANH-RAU-MUONG", "VN-PHO-GA"])
def test_mon_viet_curated_duoc_phep_toi_benh_nhan(dish_id):
    assert is_patient_facing_dish(dish_id) is True


@pytest.mark.parametrize(
    "dish_id",
    [
        "MENU-TĐ3+4-TD3-Sáng-1",  # mẫu bữa từ Excel — không phải món
        "MENU-",
        "FNDDS-2705384",  # khối khảo sát thực phẩm Mỹ
        "FNDDS-",
    ],
)
def test_mon_ngoai_tang_benh_nhan_bi_loai(dish_id):
    assert is_patient_facing_dish(dish_id) is False


@pytest.mark.parametrize("dish_id", [None, ""])
def test_dish_id_rong_fail_closed(dish_id):
    """Không có định danh thì không có căn cứ khẳng định đã curated — loại."""
    assert is_patient_facing_dish(dish_id) is False


@pytest.mark.parametrize(
    "food_id",
    [1, 152, 2000, 2166, 3000, 3047, 4000, 4077, 4115, REFERENCE_FOOD_ID_MIN - 1, -3],
)
def test_food_id_tang_viet_va_tong_hop_duoc_phep(food_id):
    assert is_patient_facing_food(food_id) is True


@pytest.mark.parametrize("food_id", [REFERENCE_FOOD_ID_MIN, 500000, REFERENCE_FOOD_ID_MAX])
def test_food_id_khoi_usda_bi_loai(food_id):
    assert is_patient_facing_food(food_id) is False


@pytest.mark.parametrize("food_id", [REFERENCE_FOOD_ID_MAX + 1, 1106327])
def test_nin2017_noi_tiep_sau_khoi_usda_van_duoc_giu(food_id):
    """430 dòng NIN 2017 tiếng Việt (1105898–1106327) nằm NGAY SAU khối USDA.

    Điều kiện kiểu `id >= 167516` sẽ xoá nhầm chúng — đây là bẫy thật, phát
    hiện khi kiểm chứng dữ liệu cho DAT-23 (xem docstring `tiers.py`).
    """
    assert is_patient_facing_food(food_id) is True


def test_khoang_usda_khop_chinh_xac_file_bulk():
    """Khoảng đóng phải trùng khít tập id của `food_items.usda_bulk.csv`."""
    import csv
    from pathlib import Path

    bulk_path = Path(__file__).resolve().parents[1] / "data" / "reference" / "food_items.usda_bulk.csv"
    with open(bulk_path, newline="", encoding="utf-8") as handle:
        ids = [int(row["id"]) for row in csv.DictReader(handle)]
    assert min(ids) == REFERENCE_FOOD_ID_MIN
    assert max(ids) == REFERENCE_FOOD_ID_MAX
    assert not any(is_patient_facing_food(food_id) for food_id in ids)


def test_food_id_none_fail_closed():
    assert is_patient_facing_food(None) is False


def test_load_vn_dishes_khong_tra_ve_mau_thuc_don_hay_khoi_my():
    """Hồi quy: `MENU-*` từng lọt qua `load_vn_dishes()` vì bộ lọc cũ dựa vào
    cột `verified_by` (các dòng MENU-* ghi "pending", không khớp "USDA FNDDS").
    Đó là nguyên nhân UI bệnh nhân hiện "Bữa sáng - Thực đơn 3 (TĐ 3+4)".

    Dùng `include_pending=True` vì toàn bộ 100 món hiện tại đều `pending`
    (DAT-27) — bài test này chỉ kiểm tra bộ lọc tầng (tiền tố dish_id), không
    kiểm tra gate `verified_by` (xem `test_load_vn_dishes_mac_dinh_*` bên dưới).
    """
    dish_ids = [dish.dish_id for dish in load_vn_dishes(include_pending=True)]
    assert dish_ids, "seed không còn món Việt nào dùng được — kiểm tra lại bộ lọc"
    assert not [d for d in dish_ids if d.startswith(("MENU-", "FNDDS-"))]


def test_load_vn_dishes_mac_dinh_loai_mon_chua_duyet():
    """DAT-27: `load_vn_dishes()` mặc định (`include_pending=False`) — dùng cho
    mọi luồng chạm bệnh nhân thật (`assembly.py`, `equivalent.py`) — PHẢI loại
    HẲN món `verified_by` rỗng hoặc "pending" khỏi kết quả, không chỉ gắn cờ
    cảnh báo. Trước fix này, món pending vẫn lọt vào ứng viên CP-SAT — an toàn
    thực tế chỉ dựa vào so khớp chuỗi con trong `note`, dễ bị bỏ lọt (đúng cơ
    chế đã gây bug MENU-*, DEC-022).

    Hiện toàn bộ 100 món trong seeds đều pending, nên assert này thực chất
    khẳng định "không có món pending nào lọt qua" bằng cách khẳng định KẾT QUẢ
    RỖNG — khẳng định mạnh hơn "không có phần tử X", đúng thực trạng dữ liệu.
    """
    assert load_vn_dishes() == []


def test_load_vn_dishes_include_pending_true_van_tra_ve_mon_cho_eval():
    """`include_pending=True` CHỈ dành cho eval/demo/nội bộ — không bao giờ
    dùng ở code path có khả năng tới bệnh nhân thật. Test khẳng định cờ này
    vẫn hoạt động (không bị gate chặn luôn, tách biệt với is_patient_facing_dish
    ở tầng khác)."""
    dishes = load_vn_dishes(include_pending=True)
    assert dishes, "include_pending=True phải trả về món pending cho eval/demo"
    assert all(d.is_reviewed is False for d in dishes), "toàn bộ 100 món hiện tại đều pending"
