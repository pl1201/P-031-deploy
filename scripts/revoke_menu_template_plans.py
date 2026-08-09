#!/usr/bin/env python3
"""Thu hồi duyệt các thực đơn chứa mẫu `MENU-*` (DAT-25).

Chạy: python scripts/revoke_menu_template_plans.py [--apply]
Mặc định là DRY-RUN — không có `--apply` thì không ghi gì vào DB.

VÌ SAO THU HỒI CHỨ KHÔNG ĐỔI NHÃN HIỂN THỊ
------------------------------------------
Ban đầu tưởng đây là lỗi nhãn (UI hiện "Bữa sáng - Thực đơn 3 (TĐ 3+4)" thay vì
tên món). Kiểm tra dữ liệu thật cho thấy nội dung thực đơn SAI, không chỉ nhãn:

- Hệ số gram vô lý: `MENU-TĐ5+6+7-TD5-Sáng-1` có công thức 50 g (chỉ cà rốt)
  nhưng được phục vụ 300 g — hệ số 6.0x, tức "một bữa gồm 300 g cà rốt".
  `TD5-Trưa-2` (công thức 114 g) phục vụ 300 g — hệ số 2.63x.
  Dinh dưỡng được scale theo `grams` (RULE-1), nên con số đã tính cũng sai theo.
- Sai khung bữa: mẫu "Bữa tối" nằm trong slot `breakfast`, mẫu "Bữa trưa" nằm
  trong slot `dinner`.
- Trùng lặp: cùng một mẫu xuất hiện ở cả `lunch` lẫn `dinner`.

Đổi nhãn hiển thị trong trường hợp này là CHE một thực đơn sai, không phải sửa
nó — nên script này thu hồi trạng thái duyệt thay vì làm đẹp tên.

NGUYÊN TẮC AN TOÀN
------------------
- KHÔNG xoá dòng nào. `meal_plans` và `meal_plan_items` giữ nguyên để còn dấu
  vết kiểm toán: ai đã duyệt gì, vào lúc nào (RULE-3).
- Chỉ đổi `status` -> `rejected` và ghi lý do vào `reviewer_notes`.
- Chỉ đụng thực đơn ĐANG ở trạng thái `approved`. Thực đơn `rejected`/`failed`
  chưa bao giờ tới bệnh nhân, để nguyên.
- In toàn bộ thay đổi trước khi thực hiện; không có `--apply` thì không ghi.

Cả 3 hồ sơ bị ảnh hưởng đều đã có sẵn một thực đơn `pending_review` mới hơn,
nên chuyên gia có sẵn bản thay thế để duyệt — bệnh nhân không bị bỏ trống lâu.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from src.db.base import get_engine  # noqa: E402
from src.db.models import MealPlan, MealPlanItem  # noqa: E402

REVOKE_NOTE = (
    "[DAT-25 / tự động] Thu hồi duyệt: thực đơn chứa mẫu MENU-* (bữa mẫu trích từ "
    "file Excel), không phải món ăn. Nội dung sai chứ không chỉ sai nhãn — hệ số "
    "gram lệch tới 6x so với công thức gốc và mẫu bị đặt sai khung bữa, nên dinh "
    "dưỡng đã tính không dùng được. Cần chuyên gia duyệt lại thực đơn mới "
    "(mỗi hồ sơ đã có sẵn một bản pending_review). Xem DEVLOG DEC-022."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="ghi thật vào DB (mặc định là dry-run)")
    args = parser.parse_args()

    mode = "GHI THẬT" if args.apply else "DRY-RUN (không ghi gì)"
    print(f"Chế độ: {mode}\n")

    with Session(get_engine()) as session:
        plan_ids = set(session.scalars(select(MealPlanItem.plan_id).where(MealPlanItem.dish_id.like("MENU-%"))).all())
        plans = session.scalars(select(MealPlan).where(MealPlan.id.in_(plan_ids), MealPlan.status == "approved")).all()

        if not plans:
            print("✅ Không còn thực đơn `approved` nào chứa MENU-* — không có gì để thu hồi.")
            return 0

        print(f"Sẽ thu hồi duyệt {len(plans)} thực đơn:\n")
        for plan in plans:
            n_menu = sum(
                1
                for item in session.scalars(select(MealPlanItem).where(MealPlanItem.plan_id == plan.id)).all()
                if item.dish_id and item.dish_id.startswith("MENU-")
            )
            print(f"  {plan.id[:8]}  hồ sơ={plan.profile_id[:8]}  ngày={plan.plan_date}  {n_menu} item MENU-*")
            print("      status: approved -> rejected")
            if plan.reviewer_notes:
                print(f"      ghi chú cũ được giữ lại: {plan.reviewer_notes[:60]}...")

        if not args.apply:
            print("\n(dry-run — chưa ghi gì. Chạy lại với --apply để thực hiện.)")
            return 0

        for plan in plans:
            # Nối chứ không ghi đè: ghi chú cũ của chuyên gia là dấu vết kiểm toán.
            plan.reviewer_notes = f"{plan.reviewer_notes}\n\n{REVOKE_NOTE}" if plan.reviewer_notes else REVOKE_NOTE
            plan.status = "rejected"
        session.commit()

        print(f"\n✅ Đã thu hồi duyệt {len(plans)} thực đơn. Không dòng nào bị xoá.")
        print("   Bước tiếp theo: chuyên gia duyệt bản pending_review của từng hồ sơ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
