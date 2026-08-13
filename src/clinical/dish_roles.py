"""Vai trò của món trong cấu trúc một bữa ăn — từ vựng DUY NHẤT của dự án.

LLM: NO — thuần Python, không I/O, không import LLM client.

Vì sao cần vai trò
------------------
`dishes.csv` trộn hai loại món khác bản chất: món **thành phần** (canh rau
muống, giò lụa — phải ghép nhiều món mới thành bữa) và món **một bát trọn
vẹn** (phở gà, bún chả — đã gồm cả tinh bột lẫn đạm trong một bát). Không có
nhãn vai trò thì mọi ràng buộc "bữa phải có tinh bột + đạm + rau" đều gán sai
cho nhóm thứ hai: phở gà vừa là tinh bột, vừa là đạm, vừa có rau — nhưng
KHÔNG phải ba món.

Ranh giới trách nhiệm (quan trọng)
----------------------------------
Đây là phân loại **ẩm thực/cấu trúc bữa**, KHÔNG phải ngưỡng lâm sàng:

- Vai trò KHÔNG bao giờ được dùng để suy ra con số dinh dưỡng. Mọi kcal/đạm/
  natri vẫn tính từ `dish_ingredients` × `food_items` bằng SQL (RULE-1).
- Vai trò KHÔNG được nhập vào `clinical_rules.csv`. Ngưỡng trong bảng đó có
  `guideline_ref` từ hướng dẫn y khoa; vai trò món ăn chỉ là quy ước thực
  hành, không có guideline nào định nghĩa. Trộn hai thứ vào cùng một bảng sẽ
  làm loãng RULE-2 và tạo ra "ngưỡng y tế" không nguồn.
- Mức tin cậy: `expert_default` — do R1 phân loại theo kinh nghiệm ẩm thực,
  **chưa** được R2 ký. Ràng buộc dựa trên vai trò vì vậy chỉ được ở mức
  CẢNH BÁO (soft), không chặn cứng, tới khi R2 rà xong.

Quy ước dữ liệu
---------------
Cột `roles` trong `dishes.csv` là danh sách phân tách bằng `|` (cùng quy ước
với `aliases` trong `food_items.csv`). Một món có thể giữ nhiều vai trò — xôi
lạc là `staple|one_dish` (ăn sáng đứng một mình được, nhưng trong mâm cơm đầy
đủ thì chỉ là tinh bột). Ép chọn một vai trò duy nhất sẽ sai ở cả hai ngữ cảnh.

`roles` RỖNG nghĩa là món KHÔNG đủ điều kiện làm một mục độc lập trong bữa —
fail closed, giống `is_patient_facing_dish("")`. Hai nhóm rơi vào đây:
nguyên liệu bị nhập lẫn thành "món" (bánh đa nem = vỏ cuốn nem), và toàn bộ
2632 dòng `FNDDS-*` tiếng Anh (`origin=foreign`) — không thể phân vai trò cho
chúng mà không suy đoán, và chúng vốn đã bị tầng C loại khỏi thực đơn bệnh
nhân (xem `src/clinical/tiers.py`).
"""

from __future__ import annotations

from enum import Enum


class DishRole(str, Enum):
    """Vai trò một món có thể đảm nhiệm trong bữa ăn."""

    STAPLE = "staple"  # nguồn tinh bột chính: cơm, xôi, bánh mì, bún/phở
    PROTEIN = "protein"  # nguồn đạm chính, động vật hoặc thực vật (đậu phụ)
    VEGETABLE = "vegetable"  # rau xào/luộc, nộm, gỏi
    SOUP = "soup"  # canh
    BEVERAGE = "beverage"  # đồ uống
    DESSERT = "dessert"  # tráng miệng, chè, bánh ngọt
    # Món một bát/một suất đã gồm cả tinh bột và đạm — phở, bún, cháo, cơm
    # rang, bánh mì kẹp. KHÔNG được đếm như nhiều món thành phần.
    ONE_DISH = "one_dish"
    # Nước chấm, gia vị ăn kèm. Không bao giờ đứng một mình thành một mục của
    # bữa; tách riêng để có thể khuyên bỏ khi cần giảm natri (xem rule "70-81%
    # natri của người Việt đến từ gia vị nêm và nước chấm").
    CONDIMENT = "condiment"


#: Vai trò tự nó đã tạo thành một bữa (không cần ghép thêm tinh bột/đạm).
SELF_SUFFICIENT_ROLES: frozenset[DishRole] = frozenset({DishRole.ONE_DISH})

#: Vai trò KHÔNG bao giờ được tính là một mục độc lập của bữa.
NON_STANDALONE_ROLES: frozenset[DishRole] = frozenset({DishRole.CONDIMENT})

ROLE_SEPARATOR = "|"


def parse_roles(raw: str | None) -> tuple[DishRole, ...]:
    """Đọc cột `roles` từ CSV/DB thành tuple `DishRole`.

    Bỏ qua giá trị lạ thay vì raise: dữ liệu seed do người biên tập bằng tay,
    một token gõ sai không được làm sập cả pipeline sinh thực đơn. Món có vai
    trò lạ sẽ hành xử như món không có vai trò (fail closed — không được chọn
    vào bữa), và `scripts/validate_data.py` là nơi báo lỗi để người sửa.
    """
    if not raw:
        return ()
    out: list[DishRole] = []
    for token in raw.split(ROLE_SEPARATOR):
        token = token.strip()
        if not token:
            continue
        try:
            role = DishRole(token)
        except ValueError:
            continue
        if role not in out:
            out.append(role)
    return tuple(out)


def unknown_role_tokens(raw: str | None) -> tuple[str, ...]:
    """Các token trong cột `roles` không thuộc từ vựng — dùng cho validate_data."""
    if not raw:
        return ()
    valid = {r.value for r in DishRole}
    return tuple(t.strip() for t in raw.split(ROLE_SEPARATOR) if t.strip() and t.strip() not in valid)


def is_standalone(roles: tuple[DishRole, ...]) -> bool:
    """Món có được phép là một mục độc lập trong bữa của bệnh nhân không.

    Rỗng → False (fail closed). Chỉ có vai trò ăn kèm → False.
    """
    if not roles:
        return False
    return any(r not in NON_STANDALONE_ROLES for r in roles)


def is_self_sufficient(roles: tuple[DishRole, ...]) -> bool:
    """Món tự nó đã đủ thành một bữa (không cần ghép tinh bột/đạm riêng)."""
    return any(r in SELF_SUFFICIENT_ROLES for r in roles)
