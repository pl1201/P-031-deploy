#!/usr/bin/env python3
"""Trích xuất món ăn quốc tế (Mỹ/phối hợp, USDA FNDDS "What We Eat In America")
từ USDA FoodData Central bulk CSV thành `dishes.csv` + `dish_ingredients.csv`
bổ sung — có phân rã nguyên liệu thật (RULE-1), không phải số dinh dưỡng trực
tiếp trên món.

Ticket: DAT-12 (bỏ trần dữ liệu, thêm món quốc tế). LLM: NO — thuần ETL.

Nguồn:
- `survey_fndds_food.csv` (5.432 món "as consumed" trong khảo sát WWEIA) —
  danh sách món.
- `input_food.csv` (18.585 dòng) — phân rã từng món thành nguyên liệu SR
  Legacy (`sr_code` = NDB number) + khối lượng gram thật (`gram_weight`).
- `sr_legacy_food.csv` — map NDB number → fdc_id, để nối sang food_items đã
  nhập từ `scripts/extract_usda_bulk.py`.

Chỉ giữ món có TOÀN BỘ nguyên liệu quy đổi được sang food_id đã tồn tại trong
`food_items.csv` (đã nhập đủ 8 cột bắt buộc) — không tạo dish_ingredients trỏ
tới food_id không tồn tại/thiếu số liệu (RULE-1 + toàn vẹn FK).

`verified_by` = "USDA FNDDS (nguồn chính thức)" — khác `pending` của món Việt
tự soạn: đây không phải công thức do LLM nháp cần R2 duyệt lại độ chính xác
ẩm thực, mà là bản ghi trực tiếp từ khảo sát dinh dưỡng chính thức của USDA.

Chạy: python scripts/extract_fndds_dishes.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

USDA_DIR = (
    Path(__file__).resolve().parents[1] / "data" / "FoodData_Central_csv_2025-12-18" / "FoodData_Central_csv_2025-12-18"
)
SEEDS = Path(__file__).resolve().parents[1] / "data" / "seeds"

DISH_HEADER = ["dish_id", "name_vi", "region", "serving_g", "verified_by", "note"]
ING_HEADER = ["dish_id", "food_id", "grams", "note"]

VERIFIED_BY = "USDA FNDDS (nguồn chính thức)"


def _known_food_ids() -> set[str]:
    ids: set[str] = set()
    with open(SEEDS / "food_items.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("kcal_100g") or "").strip():
                ids.add(row["id"])
    return ids


def _known_dish_ids() -> set[str]:
    ids: set[str] = set()
    with open(SEEDS / "dishes.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ids.add(row["dish_id"])
    return ids


def _ndb_to_fdc() -> dict[str, str]:
    mapping: dict[str, str] = {}
    with open(USDA_DIR / "sr_legacy_food.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mapping[row["NDB_number"]] = row["fdc_id"]
    return mapping


def _dish_descriptions(dish_fdc_ids: set[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    with open(USDA_DIR / "food.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["fdc_id"] in dish_fdc_ids:
                out[row["fdc_id"]] = row["description"]
    return out


def build() -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    known_food_ids = _known_food_ids()
    known_dish_ids = _known_dish_ids()
    ndb_to_fdc = _ndb_to_fdc()

    survey_fdc_ids: set[str] = set()
    with open(USDA_DIR / "survey_fndds_food.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            survey_fdc_ids.add(row["fdc_id"])
    print(f"Món trong survey_fndds_food.csv: {len(survey_fdc_ids)}")

    ingredients_by_dish: dict[str, list[dict]] = {}
    with open(USDA_DIR / "input_food.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["fdc_id"] not in survey_fdc_ids:
                continue
            ingredients_by_dish.setdefault(row["fdc_id"], []).append(row)

    descriptions = _dish_descriptions(set(ingredients_by_dish))

    dish_rows: list[dict[str, str]] = []
    ing_rows: list[dict[str, str]] = []
    skipped_partial = 0

    for dish_fdc, ings in ingredients_by_dish.items():
        resolved: list[tuple[str, float, str]] = []  # (food_id, grams, ingredient_desc)
        ok = True
        for row in ings:
            food_fdc = ndb_to_fdc.get(row["sr_code"])
            if food_fdc is None or food_fdc not in known_food_ids:
                ok = False
                break
            try:
                grams = float(row["gram_weight"])
            except ValueError:
                ok = False
                break
            # MenuItem.grams giới hạn le=2000 (src/clinical/models.py) — vài mục
            # FNDDS là công thức quy mô lớn (VD bột mì 4540g cho 1 mẻ bánh
            # thương mại), không phải "1 khẩu phần ăn". Loại thay vì nới trần
            # hệ thống cho một nhóm nhỏ dữ liệu ngoại lệ.
            if not (0 < grams <= 2000):
                ok = False
                break
            resolved.append((food_fdc, grams, row.get("sr_description") or ""))
        if not ok or not resolved:
            skipped_partial += 1
            continue
        if sum(g for _, g, _ in resolved) > 2000:
            skipped_partial += 1
            continue  # tổng khẩu phần bất thường (>2kg) — không phải "1 lần ăn" thật

        dish_id = f"FNDDS-{dish_fdc}"
        if dish_id in known_dish_ids:
            continue

        name = descriptions.get(dish_fdc, "").strip()
        if not name:
            continue

        total_grams = sum(g for _, g, _ in resolved)
        dish_rows.append(
            {
                "dish_id": dish_id,
                "name_vi": name,
                "region": "",
                "serving_g": f"{total_grams:g}",
                "verified_by": VERIFIED_BY,
                "note": f"USDA FoodData Central (FNDDS/WWEIA Survey Foods), fdcId:{dish_fdc}",
            }
        )
        for food_id, grams, desc in resolved:
            ing_rows.append(
                {
                    "dish_id": dish_id,
                    "food_id": food_id,
                    "grams": f"{grams:g}",
                    "note": desc,
                }
            )

    print(f"Món đủ TOÀN BỘ nguyên liệu quy đổi được: {len(dish_rows)}")
    print(f"Món bị bỏ (thiếu ≥1 nguyên liệu chưa có trong food_items.csv): {skipped_partial}")
    return dish_rows, ing_rows, skipped_partial


def main() -> int:
    dish_rows, ing_rows, _ = build()

    dish_out = SEEDS / "dishes.fndds_bulk.csv"
    ing_out = SEEDS / "dish_ingredients.fndds_bulk.csv"

    with open(dish_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=DISH_HEADER)
        w.writeheader()
        w.writerows(dish_rows)
    with open(ing_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ING_HEADER)
        w.writeheader()
        w.writerows(ing_rows)

    print(f"Đã ghi {dish_out} ({len(dish_rows)} món)")
    print(f"Đã ghi {ing_out} ({len(ing_rows)} dòng nguyên liệu)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
