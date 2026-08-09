"""Ranh giới tầng dữ liệu — nguồn DUY NHẤT quyết định dòng nào chạm tới bệnh nhân.

LLM: NO — thuần Python, không I/O, không import LLM client. Ticket: DAT-23.

Bối cảnh (xem DEVLOG DEC-022): `data/seeds/food_items.csv` và `dishes.csv` từng
gộp bốn nguồn khác bản chất vào một file phẳng, và mỗi loader tự lọc rác theo
cách riêng — `src/clinical/dishes.py` lọc theo tiền tố `dish_id`, còn
`src/clinical/seeds.py::load_vn_dishes()` lọc theo cột `verified_by` + từ khoá
trong `note`. Hai bộ lọc lệch nhau khiến `MENU-*` lọt qua `load_vn_dishes()` và
hiện lên UI bệnh nhân dưới dạng "Bữa sáng - Thực đơn 3 (TĐ 3+4)".

Module này gom định nghĩa về một chỗ. Sau khi CSV đã được tách tầng
(`scripts/split_data_tiers.py`), các hàm ở đây là **lưới an toàn** cho dữ liệu
cũ chứ không còn là logic nghiệp vụ — nhưng vẫn giữ, vì DB production có thể
còn dòng cũ chưa dọn.

Các tầng id KHÔNG chồng lấn nhau (kiểm chứng trên seed 2026-08-09, 7745 dòng):

| Tầng | `food_items.id`     | n     | `dish_id`                       | Chạm bệnh nhân |
|------|---------------------|-------|---------------------------------|----------------|
| A    | 1–152               | 152   | `PHO-`, `BUN-`, `CANH-`, `VN-`… | CÓ             |
| B    | 2000–2166           | 167   | —                               | CÓ (NIN 2017)  |
| B    | 3000–3047           | 48    | —                               | CÓ (bảng nội bộ) |
| B    | 4000–4077, 4100–4115| 94    | —                               | CÓ (NIN 2017 + khớp chéo USDA) |
| C    | **167516–1105897**  | 6854  | `FNDDS-*`                       | KHÔNG (tham chiếu USDA) |
| B    | **≥ 1105898**       | 430   | —                               | CÓ (NIN 2017 nối tiếp) |
| D    | —                   | —     | `MENU-*`                        | KHÔNG (mẫu bữa, không phải món) |

⚠️ Khối tham chiếu USDA là **khoảng ĐÓNG**, không phải "mọi id lớn hơn ngưỡng".
430 dòng NIN 2017 tiếng Việt (id 1105898–1106327) được nối tiếp NGAY SAU khối
USDA khi merge, nên một điều kiện kiểu `id >= 167516` sẽ xoá nhầm dữ liệu Việt
thật. Đã kiểm chứng: tập id trong khoảng đóng khớp chính xác 6854 id của
`data/seeds/food_items.usda_bulk.csv`.
"""

from __future__ import annotations

# Khoảng đóng của khối USDA FoodData Central import bulk — xem cảnh báo ở trên.
REFERENCE_FOOD_ID_MIN = 167516
REFERENCE_FOOD_ID_MAX = 1105897

# `MENU-*` là một BỮA hoàn chỉnh trích từ file Excel thực đơn mẫu, không phải
# một món ăn. Không bao giờ được làm ứng viên cho generator, cũng không bao giờ
# được hiển thị như tên món cho bệnh nhân.
TEMPLATE_DISH_PREFIXES: tuple[str, ...] = ("MENU-",)

# `FNDDS-*` là khối khảo sát thực phẩm Mỹ (tên tiếng Anh: "Milk, NFS").
REFERENCE_DISH_PREFIXES: tuple[str, ...] = ("FNDDS-",)

NON_PATIENT_DISH_PREFIXES: tuple[str, ...] = TEMPLATE_DISH_PREFIXES + REFERENCE_DISH_PREFIXES


def is_patient_facing_dish(dish_id: str | None) -> bool:
    """True nếu `dish_id` được phép xuất hiện trong thực đơn của bệnh nhân.

    `None`/rỗng trả về False — không có định danh thì không có căn cứ khẳng định
    đây là món Việt đã curated, nên loại (fail closed).
    """
    if not dish_id:
        return False
    return not dish_id.startswith(NON_PATIENT_DISH_PREFIXES)


def is_patient_facing_food(food_id: int | None) -> bool:
    """True nếu `food_id` thuộc tầng A/B (món Việt curated, NIN 2017, nội bộ).

    Id âm là món tổng hợp sinh tại chỗ bởi `DishFoodRepository` (xem
    `src/clinical/dishes.py`) — luôn hợp lệ vì nguyên liệu của nó đã được lọc.

    Chỉ loại đúng khoảng ĐÓNG của khối USDA bulk: id ≥ 1105898 là dữ liệu NIN
    2017 tiếng Việt nối tiếp phía sau, phải giữ lại.
    """
    if food_id is None:
        return False
    return not (REFERENCE_FOOD_ID_MIN <= food_id <= REFERENCE_FOOD_ID_MAX)
