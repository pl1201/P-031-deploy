#!/usr/bin/env python3
"""Mở rộng `serving_sizes.csv` bằng khẩu phần trung vị theo nhóm thực phẩm
WWEIA ("What We Eat In America" — hệ phân loại chính thức của USDA dùng
trong khảo sát NHANES/FNDDS), tính trực tiếp từ dữ liệu khẩu phần thật trong
`data/FoodData_Central_csv_2025-12-18/`.

Ticket: DAT-16. LLM: NO — thuần thống kê (trung vị) trên dữ liệu CSV chính
thức USDA, không suy đoán/không tự đặt số.

VÌ SAO DÙNG WWEIA THAY VÌ TỰ ĐẶT DANH MỤC MÓN VIỆT:
`serving_sizes.csv` (5 dòng cũ) do đội tự tổng hợp thủ công cho vài nhóm món
Việt cụ thể (bát phở, bát cơm...) — cách làm đúng nhưng không mở rộng nhanh
được tới 100-200 dòng mà vẫn giữ nguồn thật, vì không có khảo sát khẩu phần
món Việt quy mô lớn công khai. WWEIA là hệ 172 nhóm thực phẩm CHÍNH THỨC của
USDA (dùng trong khảo sát tiêu thụ thực phẩm quốc gia Mỹ NHANES), mỗi nhóm có
hàng trăm bản ghi khẩu phần thật (`food_portion.csv`, đơn vị "1 cup", "1
slice"...) — đủ dữ liệu để tính trung vị có ý nghĩa thống kê.

⚠️ GIỚI HẠN THẬT (phải đọc trước khi dùng): đây là khẩu phần theo THÓI QUEN
ĂN UỐNG MỸ (khảo sát NHANES), KHÔNG PHẢI khẩu phần người Việt. Dùng làm
THAM CHIẾU/dự phòng khi không có nguồn khẩu phần Việt Nam cụ thể — không thay
thế 5 dòng khẩu phần món Việt đã có (giữ nguyên, không ghi đè).

Phương pháp: với mỗi mã WWEIA, lấy toàn bộ `fdc_id` thuộc nhóm đó
(`survey_fndds_food.csv`), gộp mọi `gram_weight` trong `food_portion.csv` của
các fdc_id này, tính TRUNG VỊ (median, ít nhạy với outlier hơn trung bình).
Nhóm có < 5 bản ghi khẩu phần bị loại (không đủ ý nghĩa thống kê).

Chạy: python scripts/build_serving_sizes_wweia.py
"""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FDC = ROOT / "data" / "FoodData_Central_csv_2025-12-18" / "FoodData_Central_csv_2025-12-18"
OUT = ROOT / "data" / "seeds" / "serving_sizes.wweia_reference.csv"

MIN_SAMPLES = 5


def load_category_names() -> dict[str, str]:
    out: dict[str, str] = {}
    with open(FDC / "wweia_food_category.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["wweia_food_category"]] = row["wweia_food_category_description"]
    return out


def load_fdc_to_category() -> dict[str, str]:
    out: dict[str, str] = {}
    with open(FDC / "survey_fndds_food.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["fdc_id"]] = row["wweia_category_code"]
    return out


def collect_gram_weights_by_category(fdc_to_cat: dict[str, str]) -> dict[str, list[float]]:
    by_cat: dict[str, list[float]] = defaultdict(list)
    with open(FDC / "food_portion.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fdc_id = row["fdc_id"]
            cat = fdc_to_cat.get(fdc_id)
            if cat is None:
                continue
            try:
                grams = float(row["gram_weight"])
            except (ValueError, KeyError):
                continue
            if grams <= 0 or grams > 2000:  # loại giá trị vô lý (lỗi nhập liệu nguồn)
                continue
            by_cat[cat].append(grams)
    return by_cat


def main() -> None:
    names = load_category_names()
    fdc_to_cat = load_fdc_to_category()
    print(f"WWEIA categories: {len(names)}; fdc_id da gan category: {len(fdc_to_cat)}")

    by_cat = collect_gram_weights_by_category(fdc_to_cat)

    rows = []
    for cat, grams_list in by_cat.items():
        if len(grams_list) < MIN_SAMPLES:
            continue
        median_g = round(statistics.median(grams_list), 1)
        rows.append(
            {
                "category": f"wweia_{cat}",
                "serving_g": median_g,
                "note": names.get(cat, "(khong ro ten nhom)"),
                "source": (
                    f"USDA FNDDS/WWEIA (khao sat NHANES) — trung vi {len(grams_list)} ban ghi khau phan that, "
                    f"nhom '{names.get(cat, cat)}' (ma WWEIA {cat}). "
                    "Khau phan theo thoi quen an uong My, dung tham chieu/du phong, KHONG phai khau phan VN."
                ),
            }
        )

    rows.sort(key=lambda r: r["category"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "serving_g", "note", "source"])
        writer.writeheader()
        writer.writerows(rows)

    skipped = len(names) - len(rows)
    print(f"\nDa ghi {OUT.relative_to(ROOT)}: {len(rows)} nhom (>= {MIN_SAMPLES} mau)")
    print(f"Bo qua {skipped} nhom WWEIA khong du du lieu khau phan that (< {MIN_SAMPLES} mau hoac khong co)")


if __name__ == "__main__":
    main()
