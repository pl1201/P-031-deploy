#!/usr/bin/env python3
"""Áp kết quả duyệt từ giao diện tạm (`duyet-mon-an.html`) vào `dishes.csv`.

Chạy: python scripts/apply_dish_review.py <file_json_tai_ve> [--apply]

Đọc file JSON chuyên gia dinh dưỡng tải về từ giao diện duyệt (mỗi dòng có
`dish_id`, `status`, `note`, `edited_grams_by_food_id`). Với mỗi món:

- `status="approved"`: đổi `verified_by` sang mô tả có ngày duyệt (bất kỳ giá
  trị nào khác rỗng/`"pending"` đều đủ để `load_vn_dishes()` (DAT-27) coi là
  đã duyệt — xem `src/clinical/seeds.py`). Áp gram đã sửa (nếu có) vào
  `dish_ingredients.csv`.
- `status="needs_edit"`: GIỮ `verified_by="pending"` (chưa đủ điều kiện dùng
  cho bệnh nhân thật), áp gram đã sửa, nối ghi chú chuyên gia vào cột `note`
  để R2 xử lý tiếp.
- `status="rejected"`: giữ `verified_by="pending"` (đã bị `DAT-27` loại khỏi
  ứng viên CP-SAT nên an toàn), nối ghi chú lý do từ chối vào `note` — không
  tự xoá dòng, để R2 quyết định.
- `status="pending"` (chưa xem): bỏ qua, không đổi gì.

KHÔNG tự động làm gì với món "approved" ngoài đổi `verified_by`/gram — không
đẩy thẳng vào thực đơn bệnh nhân (đó là việc của HITL/CP-SAT sau này).
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DISHES_PATH = ROOT / "data" / "seeds" / "dishes.csv"
DISH_INGREDIENTS_PATH = ROOT / "data" / "seeds" / "dish_ingredients.csv"


def main() -> int:
    if len(sys.argv) < 2:
        print("Dùng: python scripts/apply_dish_review.py <file_json_tai_ve> [--apply]")
        return 1
    review_path = Path(sys.argv[1])
    apply = "--apply" in sys.argv

    reviews = {r["dish_id"]: r for r in json.loads(review_path.read_text(encoding="utf-8"))["reviews"]}

    with open(DISHES_PATH, newline="", encoding="utf-8") as f:
        dish_rows = list(csv.DictReader(f))
        dish_fieldnames = list(dish_rows[0].keys())
    with open(DISH_INGREDIENTS_PATH, newline="", encoding="utf-8") as f:
        ing_rows = list(csv.DictReader(f))
        ing_fieldnames = list(ing_rows[0].keys())

    today = date.today().isoformat() if apply else "YYYY-MM-DD"
    verified_note = f"Chuyên gia duyệt {today} (qua giao diện duyệt tạm)"

    counts = {"approved": 0, "needs_edit": 0, "rejected": 0, "pending": 0, "khong_co_trong_review": 0}
    grams_changed = 0

    for row in dish_rows:
        review = reviews.get(row["dish_id"])
        if review is None:
            counts["khong_co_trong_review"] += 1
            continue
        status = review.get("status", "pending")
        counts[status] = counts.get(status, 0) + 1

        if status == "approved":
            row["verified_by"] = verified_note
        elif status in ("needs_edit", "rejected"):
            prefix = "[CẦN SỬA]" if status == "needs_edit" else "[TỪ CHỐI]"
            note = review.get("note", "").strip()
            extra = f"{prefix} {note}".strip() if note else prefix
            row["note"] = f"{row.get('note', '').strip()} {extra}".strip()

        edited = review.get("edited_grams_by_food_id") or {}
        for ing in ing_rows:
            if ing["dish_id"] != row["dish_id"]:
                continue
            new_g = edited.get(ing["food_id"])
            if new_g is not None and float(ing["grams"]) != float(new_g):
                ing["grams"] = str(new_g)
                grams_changed += 1

    print("Phân loại theo file duyệt:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"Số dòng nguyên liệu bị sửa gram: {grams_changed}")

    if not apply:
        print("\n(dry-run — chưa ghi gì. Chạy lại với --apply để ghi.)")
        return 0

    with open(DISHES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=dish_fieldnames)
        writer.writeheader()
        writer.writerows(dish_rows)
    with open(DISH_INGREDIENTS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ing_fieldnames)
        writer.writeheader()
        writer.writerows(ing_rows)

    print(f"\nĐã ghi {DISHES_PATH.relative_to(ROOT)} và {DISH_INGREDIENTS_PATH.relative_to(ROOT)}")
    print("Chạy tiếp: python scripts/validate_data.py && pytest -q")
    return 0


if __name__ == "__main__":
    sys.exit(main())
