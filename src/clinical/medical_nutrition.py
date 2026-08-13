"""Thực phẩm cho mục đích y tế đặc biệt (FSMP) — chỉ dùng khi bệnh nhân KHAI BÁO.

LLM: NO — thuần Python, không I/O, không import LLM client.

Vấn đề
------
Sữa dinh dưỡng y tế (Glucerna, Nutren Diabetes...) là dữ liệu HỢP LỆ và có
nguồn thật (nhãn nhà sản xuất), nằm ở tầng B nên `is_patient_facing_food()`
cho qua. Nhưng "hợp lệ" không có nghĩa là "được tự do đưa vào thực đơn":

- Đây là sản phẩm thương mại có giá, bệnh nhân phải chủ động mua. Sinh thực
  đơn chứa "Sữa bột Glucerna 150 g" cho người không dùng sản phẩm đó là kê
  một thứ họ không có.
- Nói cho bệnh nhân dùng một sản phẩm y tế đặc biệt mà họ chưa dùng là tiến
  gần tới việc CHỈ ĐỊNH — vượt ranh giới an toàn ở `CLAUDE.md` §3.
- Mật độ dinh dưỡng của bột chưa pha (437-455 kcal/100 g) rất cao, nên bộ giải
  rất dễ chọn nó để "khớp số" thay vì soạn bữa ăn thật.

Cách chặn
---------
Loại HẲN khỏi tập ứng viên trừ khi tên sản phẩm khớp danh sách bệnh nhân đã
khai (`PatientProfile.medical_nutrition`). Fail closed: hồ sơ không khai gì thì
không sản phẩm nào lọt vào.

CỐ Ý **không** xoá các dòng này khỏi `food_items.csv`: bệnh nhân dùng thật thì
vẫn phải tính được kcal/kali/phospho của phần họ uống (đặc biệt quan trọng với
CKD — 100 g bột Glucerna có 710 mg kali). Vấn đề nằm ở việc TỰ ĐỘNG CHỌN, không
nằm ở việc lưu dữ liệu.

Ranh giới id
------------
Khối 5000-5099 dành riêng cho nhóm này (xem bảng tầng ở `src/clinical/tiers.py`).
Dùng khoảng id thay vì cột `category` vì `FoodItem` hiện KHÔNG nạp `category`
từ CSV — xem ghi chú hạn chế trong `src/agents/optimizer.py`. Khi `category`
được đưa vào `FoodItem`, nên đổi hàm này sang so theo category và bỏ khoảng id.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

#: Khoảng ĐÓNG dành cho thực phẩm y tế đặc biệt (sữa dinh dưỡng y tế, TPCN).
MEDICAL_NUTRITION_FOOD_ID_MIN = 5000
MEDICAL_NUTRITION_FOOD_ID_MAX = 5099


class _NamedFood(Protocol):
    """Chỉ cần đúng ba thuộc tính này — nhận cả `FoodItem` lẫn dòng CSV đã parse."""

    id: int
    name_vi: str
    aliases: list[str]


def is_medical_nutrition_food(food_id: int | None) -> bool:
    """True nếu `food_id` thuộc khối thực phẩm y tế đặc biệt."""
    if food_id is None:
        return False
    return MEDICAL_NUTRITION_FOOD_ID_MIN <= food_id <= MEDICAL_NUTRITION_FOOD_ID_MAX


def _tokens(food: _NamedFood) -> set[str]:
    return {food.name_vi.casefold().strip(), *(a.casefold().strip() for a in food.aliases)}


def is_declared(food: _NamedFood, declared: Iterable[str]) -> bool:
    """Bệnh nhân có khai đang dùng đúng sản phẩm này không.

    Khớp theo tên hoặc alias, không phân biệt hoa thường. So khớp CHỨA (một
    chiều: chuỗi khai báo nằm trong tên sản phẩm, hoặc ngược lại) vì bệnh nhân
    khai "glucerna" còn dữ liệu ghi "Sữa bột Glucerna (bột, chưa pha)".

    KHÔNG dùng fuzzy match: gán nhầm sản phẩm này sang sản phẩm khác thì mọi
    con số kcal/kali/phospho đều sai mà không ai thấy (RULE-2/DEC-008).
    """
    wanted = [d.casefold().strip() for d in declared if d and d.strip()]
    if not wanted:
        return False
    for token in _tokens(food):
        if not token:
            continue
        for w in wanted:
            if w in token or token in w:
                return True
    return False


def is_eligible_candidate(food: _NamedFood, declared: Iterable[str]) -> bool:
    """Món có được vào tập ứng viên sinh thực đơn không.

    Thực phẩm thường: luôn được. Thực phẩm y tế đặc biệt: chỉ khi đã khai báo.
    """
    if not is_medical_nutrition_food(food.id):
        return True
    return is_declared(food, declared)
