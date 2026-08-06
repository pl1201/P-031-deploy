#!/usr/bin/env python3
"""Đo độ phủ thực tế của các chỉ số đường trong USDA FDC bulk cho những dòng
`food_items.csv` đang có nguồn USDA.

Ticket: DAT-15 (khảo sát trước khi quyết). LLM: NO — thuần đếm từ file CSV
chính thức của USDA.

VÌ SAO CHỈ ĐẾM, CHƯA GHI:
`sugar_g` trong schema dự án được DAT-07 định nghĩa theo ngưỡng **đường tự do
(free sugars)** của WHO. WHO loại trừ đường có sẵn trong trái cây nguyên quả
và sữa khỏi "đường tự do". USDA "Total Sugars" (nutrient 2000/1063) thì BAO
GỒM các loại đường đó — hai khái niệm KHÁC NHAU. Đổ Total Sugars vào `sugar_g`
rồi áp ngưỡng WHO sẽ gắn cờ sai cho bệnh nhân ăn trái cây nguyên quả.
`scripts/extract_usda_bulk.py` đã cố ý để trống cột này vì lý do đó.

"Sugars, added" (nutrient 1235) gần với free sugars hơn nhưng vẫn không đồng
nhất (free sugars của WHO = added sugars + đường trong mật ong, siro, nước ép
trái cây). Script này đo xem 1235 phủ được bao nhiêu dòng để R2 quyết định
dựa trên số thật thay vì phỏng đoán.

Chạy: python scripts/scan_usda_sugar_coverage.py
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"
FDC = ROOT / "data" / "FoodData_Central_csv_2025-12-18" / "FoodData_Central_csv_2025-12-18"

# Xem `nutrient.csv` của USDA
NUTRIENT_TOTAL_SUGAR_NEW = "2000"  # "Total Sugars"
NUTRIENT_TOTAL_SUGAR_LEGACY = "1063"  # "Sugars, Total"
NUTRIENT_ADDED_SUGAR = "1235"  # "Sugars, added"
WANTED = {NUTRIENT_TOTAL_SUGAR_NEW, NUTRIENT_TOTAL_SUGAR_LEGACY, NUTRIENT_ADDED_SUGAR}

FDC_ID_RE = re.compile(r"fdcId[:\s]*(\d+)")


def load_usda_fdc_ids() -> dict[str, list[dict[str, str]]]:
    """fdc_id -> các dòng food_items.csv tham chiếu tới nó."""
    by_fdc: dict[str, list[dict[str, str]]] = defaultdict(list)
    with open(SEEDS / "food_items.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("source") != "USDA":
                continue
            m = FDC_ID_RE.search(row.get("source_ref", ""))
            if m:
                by_fdc[m.group(1)].append(row)
    return by_fdc


def scan(by_fdc: dict[str, list[dict[str, str]]]) -> dict[str, dict[str, float]]:
    """Quét food_nutrient.csv (~1,8 GB) 1 lượt, chỉ giữ chất đường cần đếm."""
    found: dict[str, dict[str, float]] = defaultdict(dict)
    path = FDC / "food_nutrient.csv"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for i, rec in enumerate(reader):
            if i % 5_000_000 == 0 and i:
                print(f"  ...{i:,} dòng", file=sys.stderr, flush=True)
            # cột: id, fdc_id, nutrient_id, amount, ...
            if len(rec) < 4:
                continue
            nutrient_id = rec[2]
            if nutrient_id not in WANTED:
                continue
            fdc_id = rec[1]
            if fdc_id not in by_fdc:
                continue
            try:
                found[fdc_id][nutrient_id] = float(rec[3])
            except ValueError:
                continue
    return found


def main() -> None:
    by_fdc = load_usda_fdc_ids()
    print(f"food_items.csv: {len(by_fdc):,} fdcId nguồn USDA cần tra", flush=True)
    print("Đang quét food_nutrient.csv (~1,8 GB, chạy 1 lượt)...", flush=True)
    found = scan(by_fdc)

    has_total = sum(1 for v in found.values() if NUTRIENT_TOTAL_SUGAR_NEW in v or NUTRIENT_TOTAL_SUGAR_LEGACY in v)
    has_added = sum(1 for v in found.values() if NUTRIENT_ADDED_SUGAR in v)
    has_both = sum(
        1
        for v in found.values()
        if NUTRIENT_ADDED_SUGAR in v and (NUTRIENT_TOTAL_SUGAR_NEW in v or NUTRIENT_TOTAL_SUGAR_LEGACY in v)
    )

    total = len(by_fdc)
    print()
    print("KET QUA DO PHU (tren tong fdcId nguon USDA cua du an):")
    print(f"  Tong fdcId                     : {total:,}")
    print(f"  Co 'Total Sugars' (2000/1063)  : {has_total:,} ({has_total / total:.1%})")
    print(f"  Co 'Sugars, added' (1235)      : {has_added:,} ({has_added / total:.1%})")
    print(f"  Co ca hai                      : {has_both:,} ({has_both / total:.1%})")
    print()
    print("LUU Y: 'Total Sugars' KHONG dong nghia 'free sugars' cua WHO (DAT-07).")
    print("Chi 'Sugars, added' moi gan free sugars — va van khong dong nhat.")

    out = SEEDS / "usda_sugar_coverage.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fdc_id", "total_sugar_g", "added_sugar_g"])
        for fdc_id, vals in sorted(found.items(), key=lambda kv: int(kv[0])):
            total_sugar = vals.get(NUTRIENT_TOTAL_SUGAR_NEW, vals.get(NUTRIENT_TOTAL_SUGAR_LEGACY))
            w.writerow(
                [
                    fdc_id,
                    "" if total_sugar is None else total_sugar,
                    vals.get(NUTRIENT_ADDED_SUGAR, ""),
                ]
            )
    print(f"\nDa ghi bang tra cuu: {out.relative_to(ROOT)} ({len(found):,} dong)")


if __name__ == "__main__":
    main()
