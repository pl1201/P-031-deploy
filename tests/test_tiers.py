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

    Sau đợt duyệt thủ công 2026-08-12 (R2 gửi ghi chú qua text vì giao diện
    duyệt tạm bị lỗi, xem DEVLOG), 31/100 món đã có `verified_by` thực (không
    còn "pending"), số còn lại vẫn pending. Assert không còn có thể khẳng
    định KẾT QUẢ RỖNG — thay vào đó khẳng định trực tiếp điều gate thực sự
    phải đảm bảo: không món nào trong kết quả còn `is_reviewed=False`.
    """
    dishes = load_vn_dishes()
    assert dishes, "phải có ít nhất 1 món đã duyệt lọt qua gate include_pending=False"
    assert all(d.is_reviewed for d in dishes), "gate mặc định lọt món chưa duyệt"


def test_load_vn_dishes_include_pending_true_van_tra_ve_mon_cho_eval(tmp_path):
    """`include_pending=True` CHỈ dành cho eval/demo/nội bộ — không bao giờ
    dùng ở code path có khả năng tới bệnh nhân thật.

    Sau đợt duyệt 2026-08-13 (R2 xử lý dứt điểm toàn bộ dishes.csv: món đủ
    nguyên liệu → duyệt, món thiếu thành phần định danh → loại hẳn qua
    `incomplete_recipe_markers`), seed thật hiện KHÔNG còn món nào vừa qua
    được bộ lọc marker vừa còn `pending` — `include_pending=True` và mặc
    định giờ trả kết quả GIỐNG HỆT nhau trên dữ liệu thật. Đó là điều tốt
    (không còn nợ dữ liệu), không phải bug, nhưng khiến test cũ dựa vào seed
    thật để phân biệt hai nhánh không còn ý nghĩa.

    Dùng CSV giả lập cố định (độc lập trạng thái duyệt thật) để kiểm chứng
    đúng HỢP ĐỒNG của tham số — không phụ thuộc seed đã duyệt tới đâu.
    """
    dishes_csv = tmp_path / "dishes.csv"
    dishes_csv.write_text(
        "dish_id,name_vi,region,serving_g,verified_by,note\n"
        'VN-DA-DUYET,Món đã duyệt,,200,"Chuyên gia duyệt 2026-08-13",\n'
        'VN-CHUA-DUYET,Món chưa duyệt,,200,pending,\n',
        encoding="utf-8",
    )
    ingredients_csv = tmp_path / "dish_ingredients.csv"
    ingredients_csv.write_text(
        "dish_id,food_id,grams,note\nVN-DA-DUYET,1,150,\nVN-CHUA-DUYET,1,150,\n",
        encoding="utf-8",
    )

    only_reviewed = load_vn_dishes(dishes_csv, ingredients_csv, include_pending=False)
    all_dishes = load_vn_dishes(dishes_csv, ingredients_csv, include_pending=True)

    assert [d.dish_id for d in only_reviewed] == ["VN-DA-DUYET"]
    assert {d.dish_id for d in all_dishes} == {"VN-DA-DUYET", "VN-CHUA-DUYET"}
    assert any(d.is_reviewed for d in all_dishes) and any(not d.is_reviewed for d in all_dishes)
