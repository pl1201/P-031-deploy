#!/usr/bin/env python3
"""Đếm dữ liệu bệnh nhân còn trỏ tới tầng KHÔNG dành cho bệnh nhân (DAT-23).

Chạy: DATABASE_URL=<...> python scripts/audit_menu_dish_refs.py

⚠️ SCRIPT NÀY CHỈ ĐỌC. Không UPDATE, không DELETE, không tạo transaction ghi.
Đây là chủ ý, không phải thiếu sót: `meal_plans` ở trạng thái `approved` là
thực đơn ĐÃ TỚI TAY BỆNH NHÂN (RULE-3). Quyết định làm gì với chúng là của R2
và chuyên gia, không phải của script.

Bối cảnh: trước DAT-23, `data/seeds/dishes.csv` lẫn 15 dòng `MENU-*` (mẫu bữa
trích từ Excel, không phải món ăn) và 2632 dòng `FNDDS-*` (khối khảo sát Mỹ).
`load_vn_dishes()` không lọc `MENU-*`, nên chúng lọt thành ứng viên cho
generator và hiện lên UI bệnh nhân dưới dạng tên món:

    "Bữa sáng - Thực đơn 3 (TĐ 3+4) — 300 g"

Code đã vá (PR-1) và dữ liệu seed đã tách tầng (PR-2), nhưng các dòng
`meal_plan_items` ĐÃ ĐƯỢC GHI trước đó vẫn nằm trong DB. Script này trả lời:
còn bao nhiêu, thuộc thực đơn ở trạng thái nào, và có bao nhiêu bệnh nhân bị
ảnh hưởng — để R2 quyết định trên số liệu thật thay vì phỏng đoán.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from src.clinical.tiers import (  # noqa: E402
    NON_PATIENT_DISH_PREFIXES,
    is_patient_facing_dish,
    is_patient_facing_food,
)
from src.config import get_settings  # noqa: E402
from src.db.base import get_engine  # noqa: E402
from src.db.models import MealPlan, MealPlanItem  # noqa: E402


def _print_breakdown(title: str, rows: list[tuple[str, str]], total_items: int) -> None:
    """In phân rã theo trạng thái thực đơn — `approved` là dòng cần chú ý nhất."""
    print(f"\n{title}: {len(rows)} dòng / {total_items} dòng tổng")
    if not rows:
        print("   (không có — sạch)")
        return
    by_status = Counter(status for status, _ in rows)
    for status, count in by_status.most_common():
        flag = "  ⚠️ ĐÃ TỚI BỆNH NHÂN (RULE-3)" if status == "approved" else ""
        print(f"   {count:>6}  status={status}{flag}")
    examples = sorted({value for _, value in rows})[:5]
    print(f"   ví dụ: {examples}")


def main() -> int:
    settings = get_settings()
    # Không in nguyên chuỗi kết nối — có mật khẩu trong đó.
    backend = settings.database_url.split("://", 1)[0]
    print(f"DB backend: {backend}")
    print("Chế độ: CHỈ ĐỌC — script này không ghi gì vào DB.\n")

    with Session(get_engine()) as session:
        stmt = select(MealPlanItem.dish_id, MealPlanItem.food_id, MealPlan.status, MealPlan.profile_id).join(
            MealPlan, MealPlanItem.plan_id == MealPlan.id
        )
        rows = session.execute(stmt).all()

    total = len(rows)
    print(f"Tổng số dòng meal_plan_items: {total}")
    if total == 0:
        print("DB chưa có thực đơn nào — không có gì để dọn.")
        return 0

    # `food_id IS NULL` nghĩa là dòng này dùng `dish_id` — hợp lệ, không phải vi
    # phạm. `is_patient_facing_food(None)` trả False theo ngữ nghĩa fail-closed
    # của tầng lọc, nên phải loại NULL ra trước khi đếm, nếu không mọi dòng
    # dùng món đều bị đếm nhầm thành vi phạm.
    bad_dish = [(status, dish_id) for dish_id, _, status, _ in rows if dish_id and not is_patient_facing_dish(dish_id)]
    bad_food = [
        (status, str(food_id))
        for _, food_id, status, _ in rows
        if food_id is not None and not is_patient_facing_food(food_id)
    ]

    _print_breakdown(f"dish_id thuộc tầng {NON_PATIENT_DISH_PREFIXES}", bad_dish, total)
    _print_breakdown("food_id thuộc khối tham chiếu USDA", bad_food, total)

    affected = {
        profile_id
        for dish_id, food_id, _, profile_id in rows
        if (dish_id and not is_patient_facing_dish(dish_id))
        or (food_id is not None and not is_patient_facing_food(food_id))
    }
    approved = sum(1 for status, _ in (*bad_dish, *bad_food) if status == "approved")

    print(f"\nSố hồ sơ bệnh nhân bị ảnh hưởng: {len(affected)}")
    print(f"Số dòng thuộc thực đơn đã duyệt (approved): {approved}")

    if not bad_dish and not bad_food:
        print("\n✅ DB sạch — không dòng nào trỏ ra ngoài tầng dành cho bệnh nhân.")
        return 0

    print(
        "\n⚠️ Còn dữ liệu cũ cần xử lý. KHÔNG tự xoá.\n"
        "   Shim hiển thị ở src/api/routes/meal_plans.py::_item_out() vẫn đang che\n"
        "   tên MENU-* bằng danh sách nguyên liệu, nên UI không lộ tên mẫu nữa.\n"
        "   Bước tiếp theo là quyết định của R2 + chuyên gia, dựa trên số liệu trên:\n"
        "   thực đơn approved đã tới tay bệnh nhân — sửa hay thu hồi đều là quyết định\n"
        "   lâm sàng, không phải thao tác kỹ thuật (RULE-3)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
