#!/usr/bin/env python3
"""Lấp cột `category` còn trống trong `food_items.csv` cho các dòng nguồn
USDA, dùng phân loại CHÍNH THỨC `food_category` của USDA FoodData Central
(28 nhóm, `data/FoodData_Central_csv_2025-12-18/.../food_category.csv`),
dịch sang nhãn tiếng Việt.

Ticket: DAT-17. LLM: NO — thuần tra cứu + dịch nhãn phân loại chính thức,
không suy đoán nội dung dinh dưỡng.

Đây là gán NHÃN PHÂN LOẠI (metadata tổ chức dữ liệu), không phải giá trị
lâm sàng — rủi ro thấp hơn nhiều so với các trường kcal/Na/K/P. Không cần
`source_ref` riêng cho `category` (cột này không nằm trong phạm vi RULE-2 —
`validate_data.py` không kiểm tra nguồn cho `category`).

Với 21 dòng thiếu Na/kcal/... (không phải 22, xem README) vẫn giữ `category`
rỗng nếu không tra được fdc_id — không suy đoán nhóm từ tên món.

Chạy: python scripts/fill_category_from_usda.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOOD_ITEMS = ROOT / "data" / "seeds" / "food_items.csv"
FDC = ROOT / "data" / "FoodData_Central_csv_2025-12-18" / "FoodData_Central_csv_2025-12-18"

FDC_ID_RE = re.compile(r"fdcId[:\s]*(\d+)")

# USDA food_category.id -> nhãn tiếng Việt. Dịch trực tiếp mô tả chính thức
# USDA (`food_category.csv`), không tự sáng tạo nhóm mới ngoài phạm vi 28
# nhóm gốc. id=27 "Quality Control Materials" không phải thực phẩm thật nên
# CỐ Ý không map (giữ trống nếu gặp).
CATEGORY_VI: dict[str, str] = {
    "1": "sữa & trứng",
    "2": "gia vị",
    "3": "thực phẩm trẻ em",
    "4": "dầu mỡ",
    "5": "thịt gia cầm",
    "6": "súp & nước sốt",
    "7": "thịt chế biến",
    "8": "ngũ cốc ăn sáng",
    "9": "trái cây",
    "10": "thịt lợn",
    "11": "rau củ",
    "12": "hạt",
    "13": "thịt bò",
    "14": "đồ uống",
    "15": "thủy sản",
    "16": "đậu",
    "17": "thịt cừu/thú rừng",
    "18": "bánh nướng",
    "19": "đồ ngọt",
    "20": "ngũ cốc",
    "21": "đồ ăn nhanh (Mỹ)",
    "22": "món ăn chế biến sẵn",
    "23": "đồ ăn vặt",
    "24": "thực phẩm bản địa Mỹ",
    "25": "món nhà hàng (Mỹ)",
    "26": "thực phẩm đóng gói thương hiệu",
    "28": "đồ uống có cồn",
}


def load_fdc_categories() -> dict[str, str]:
    """fdc_id -> USDA category id, chỉ cho SR Legacy/Foundation (loại dùng
    trong food_items.csv nguồn USDA của dự án — xem extract_usda_bulk.py)."""
    out: dict[str, str] = {}
    with open(FDC / "food.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["data_type"] not in ("sr_legacy_food", "foundation_food"):
                continue
            cat_id = row.get("food_category_id", "")
            if cat_id:
                out[row["fdc_id"]] = cat_id
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    fdc_to_cat = load_fdc_categories()
    print(f"food.csv: {len(fdc_to_cat):,} fdc_id co category (SR Legacy/Foundation)")

    with open(FOOD_ITEMS, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = 0
    no_fdc_match = 0
    qc_skipped = 0
    for row in rows:
        if (row.get("category") or "").strip():
            continue
        if row.get("source") != "USDA":
            continue
        m = FDC_ID_RE.search(row.get("source_ref", ""))
        if not m:
            no_fdc_match += 1
            continue
        cat_id = fdc_to_cat.get(m.group(1))
        if cat_id is None:
            no_fdc_match += 1
            continue
        vi_label = CATEGORY_VI.get(cat_id)
        if vi_label is None:
            qc_skipped += 1
            continue
        row["category"] = vi_label
        updated += 1

    print(f"Se cap nhat: {updated:,} dong")
    print(f"Khong tim duoc fdc_id/category: {no_fdc_match:,} dong (giu trong)")
    if qc_skipped:
        print(f"Bo qua (Quality Control Materials, khong phai thuc pham that): {qc_skipped:,} dong")

    if args.dry_run:
        print("(--dry-run: chua ghi file)")
        return

    with open(FOOD_ITEMS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Da ghi {FOOD_ITEMS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
