#!/usr/bin/env python3
"""Trích xuất SR Legacy + Foundation Foods từ USDA FoodData Central bulk CSV
(`data/FoodData_Central_csv_2025-12-18/`) thành các dòng mới cho `food_items.csv`.

Ticket: DAT-12 (bỏ trần dữ liệu). LLM: NO — thuần ETL từ file CSV chính thức
của USDA, mọi giá trị đi thẳng từ nguồn, không suy đoán.

Vì sao SR Legacy + Foundation Foods (không dùng branded_food — 1.993.975 dòng,
sản phẩm đóng gói thương hiệu Mỹ, đã đánh giá là chi phí cao/giá trị thấp cho
mục tiêu dự án, xem `data/README.md` mục "Về bộ FoodData Central bulk
download"):
- **SR Legacy** (7.793 món): bảng tham chiếu dinh dưỡng cổ điển của USDA, phủ
  rộng nguyên liệu thô + một phần món đã chế biến, đa số có đủ 7 chất cốt lõi.
- **Foundation Foods** (436 món): nguyên liệu phân tích phòng thí nghiệm mới
  hơn, dùng bổ sung khi SR Legacy không có.

Quy ước ID: dùng thẳng `fdc_id` của USDA làm `id` trong `food_items.csv` (thay
vì cấp ID nội bộ tuần tự) — `fdc_id` là số nguyên duy nhất toàn cục, không bao
giờ trùng với ID nội bộ hiện có (1–152, đều < 1000), và giữ nguyên khả năng
truy vết ngược về USDA chỉ bằng con số. Xem `data/README.md`.

Chỉ giữ dòng có ĐỦ 7 cột bắt buộc theo `scripts/validate_data.py`
(kcal/protein/carb/fat/fiber/na/k/p) — thiếu bất kỳ cột nào thì bỏ, không suy
đoán = 0 (RULE-2/DEC-008). `purine_mg`/`gi_index`/`sugar_g` để trống (USDA
SR/Foundation không có purine; sugar "Total Sugars" có nhưng không tách biệt
đủ tin cậy theo tinh thần DAT-07 nên để trống, không suy đoán).

Chạy: python scripts/extract_usda_bulk.py [--limit N] [--out PATH]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

USDA_DIR = (
    Path(__file__).resolve().parents[1] / "data" / "FoodData_Central_csv_2025-12-18" / "FoodData_Central_csv_2025-12-18"
)
SEEDS = Path(__file__).resolve().parents[1] / "data" / "seeds"

NUTRIENT_IDS = {
    "kcal_100g": "1008",
    "protein_g": "1003",
    "fat_g": "1004",
    "carb_g": "1005",
    "fiber_g": "1079",
    "na_mg": "1093",
    "k_mg": "1092",
    "p_mg": "1091",
}
REQUIRED_FIELDS = ("kcal_100g", "protein_g", "fat_g", "carb_g", "fiber_g", "na_mg", "k_mg", "p_mg")

# Khớp RANGES trong scripts/validate_data.py — lọc trước ở đây để không sinh lỗi
# validate. Vài mục cô đặc thật (bột nở, kem tartar, bột trà hoà tan) có giá trị
# per-100g thật nhưng vượt khoảng "thực phẩm ăn được thông thường" — không ai ăn
# 100g bột nở, loại khỏi tập ứng viên thay vì nới khoảng hợp lý dùng chung.
RANGES = {
    "kcal_100g": (0, 920),
    "protein_g": (0, 90),
    "carb_g": (0, 100),
    "fat_g": (0, 100),
    "fiber_g": (0, 80),
    "na_mg": (0, 40000),
    "k_mg": (0, 5000),
    "p_mg": (0, 2000),
}

CSV_HEADER = [
    "id",
    "name_vi",
    "aliases",
    "category",
    "kcal_100g",
    "protein_g",
    "carb_g",
    "fat_g",
    "fiber_g",
    "sugar_g",
    "na_mg",
    "k_mg",
    "p_mg",
    "purine_mg",
    "purine_source_ref",
    "gi_index",
    "gi_source",
    "gi_source_ref",
    "contains_allergens",
    "source",
    "source_ref",
    "is_estimated",
]


def _load_target_foods() -> dict[str, tuple[str, str]]:
    """fdc_id -> (data_type, description) cho sr_legacy_food + foundation_food."""
    targets: dict[str, tuple[str, str]] = {}
    with open(USDA_DIR / "food.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["data_type"] in ("sr_legacy_food", "foundation_food"):
                targets[row["fdc_id"]] = (row["data_type"], row["description"])
    return targets


def _load_nutrients(target_ids: set[str]) -> dict[str, dict[str, float]]:
    """fdc_id -> {kcal_100g: value, ...} — chỉ giữ nutrient cần, stream 1 lượt qua file 1.78GB."""
    wanted_nutrient_ids = set(NUTRIENT_IDS.values())
    out: dict[str, dict[str, float]] = {}
    with open(USDA_DIR / "food_nutrient.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fdc_id = row["fdc_id"]
            if fdc_id not in target_ids or row["nutrient_id"] not in wanted_nutrient_ids:
                continue
            amount = (row.get("amount") or "").strip()
            if not amount:
                continue
            field = next(k for k, v in NUTRIENT_IDS.items() if v == row["nutrient_id"])
            out.setdefault(fdc_id, {})[field] = float(amount)
    return out


def build_rows(limit: int | None = None) -> list[dict[str, str]]:
    foods = _load_target_foods()
    print(f"Foods (SR Legacy + Foundation) trong food.csv: {len(foods)}")
    nutrients = _load_nutrients(set(foods))
    print(f"Foods có ít nhất 1 giá trị dinh dưỡng cần: {len(nutrients)}")

    rows: list[dict[str, str]] = []
    seen_names: set[str] = set()
    for fdc_id, (data_type, description) in foods.items():
        vals = nutrients.get(fdc_id)
        if not vals or not all(f in vals for f in REQUIRED_FIELDS):
            continue
        macro = vals["protein_g"] + vals["carb_g"] + vals["fat_g"] + vals["fiber_g"]
        if macro > 105:
            continue  # bất khả thi, khớp kiểm tra chéo của validate_data.py — bỏ, không sửa số
        if any(not (lo <= vals[f] <= hi) for f, (lo, hi) in RANGES.items()):
            continue  # ngoài khoảng hợp lý (VD bột nở, kem tartar) — bỏ, không nới khoảng dùng chung
        name_key = description.strip().lower()
        if name_key in seen_names:
            continue  # SR Legacy có vài mô tả trùng chữ giữa các fdc_id khác nhau (mẫu đo khác năm) — giữ mục đầu tiên
        seen_names.add(name_key)
        source_tag = "SR Legacy" if data_type == "sr_legacy_food" else "Foundation Foods"
        row = {
            "id": fdc_id,
            "name_vi": description,
            "aliases": "",
            "category": "",
            "kcal_100g": f"{vals['kcal_100g']:g}",
            "protein_g": f"{vals['protein_g']:g}",
            "carb_g": f"{vals['carb_g']:g}",
            "fat_g": f"{vals['fat_g']:g}",
            "fiber_g": f"{vals['fiber_g']:g}",
            "sugar_g": "",
            "na_mg": f"{vals['na_mg']:g}",
            "k_mg": f"{vals['k_mg']:g}",
            "p_mg": f"{vals['p_mg']:g}",
            "purine_mg": "",
            "purine_source_ref": "",
            "gi_index": "",
            "gi_source": "",
            "gi_source_ref": "",
            "contains_allergens": "",
            "source": "USDA",
            "source_ref": f"USDA FoodData Central ({source_tag}), fdcId:{fdc_id}",
            "is_estimated": "FALSE",
        }
        rows.append(row)
        if limit and len(rows) >= limit:
            break
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Giới hạn số dòng (debug)")
    ap.add_argument("--out", type=Path, default=SEEDS / "food_items.usda_bulk.csv")
    args = ap.parse_args()

    rows = build_rows(limit=args.limit)
    print(f"Dòng đủ 7 chất bắt buộc, sẵn sàng ghi: {len(rows)}")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Đã ghi {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
