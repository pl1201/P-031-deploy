#!/usr/bin/env python3
"""Lấp Na/K/P cho các dòng trống bằng NIN 2007, chỉ kích hoạt khi đủ 8 trường lõi.

Chạy: python scripts/merge_nin2007_into_food_items.py

Đọc `data/quarantine/food_items.chua_co_so_lieu.csv` (355 dòng trống hoàn
toàn — xem `docs/DAT-13-phan-loai-355-dong-trong.md`). Với mỗi dòng:

1. Khớp tên tuyệt đối với `scripts/nin2017_extracted.json` (Bảng TPTP VN 2017)
   để lấy `code`.
2. Dùng `code` tra `scripts/nin2007_extracted.json` (Bảng TPTP VN 2007,
   `scripts/extract_nin2007.py`) — khớp theo MÃ SỐ, không theo tên (tên
   tiếng Việt trong PDF 2007 bị lỗi font, không đáng tin).
3. Với mỗi trường trong 8 trường lõi: ưu tiên giá trị 2017 nếu có, thiếu thì
   lấy 2007. Không có ở cả hai thì để trống.
4. **Chỉ kích hoạt dòng (chuyển từ `quarantine/` sang `seeds/`) khi CẢ 8
   TRƯỜNG đều có giá trị** — cùng nguyên tắc `merge_nin2017_into_food_items.py`
   dùng cho `food_items.csv`, tránh tạo dòng "nửa vời" vi phạm invariant của
   `src/clinical/seeds.py::load_food_repository()`.
5. Dòng còn thiếu ít nhất 1 trường: **giữ nguyên trong quarantine**, không
   ghi số nào — nhưng cập nhật `source_ref` để ghi lại đã thử 2007 và còn
   thiếu gì, tránh người sau tưởng chưa ai tra.

Không tự chọn giữa 2017/2007 khi họ CÓ CẢ HAI nhưng lệch nhau quá dung sai —
trường hợp đó chỉ xảy ra khi merge_nin2017 (chạy trước) đã sinh xung đột
riêng, không phải việc của script này.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"
QUARANTINE = ROOT / "data" / "quarantine"
GAP_PATH = QUARANTINE / "food_items.chua_co_so_lieu.csv"
FOOD_ITEMS_PATH = SEEDS / "food_items.csv"
NIN2017_PATH = ROOT / "scripts" / "nin2017_extracted.json"
NIN2007_PATH = ROOT / "scripts" / "nin2007_extracted.json"

CORE_FIELDS = ["kcal_100g", "protein_g", "carb_g", "fat_g", "fiber_g", "na_mg", "k_mg", "p_mg"]
FIELD_MAP_2017 = {
    "kcal_100g": "enerc_kcal",
    "protein_g": "procnt_g",
    "carb_g": "chocdf_g",
    "fat_g": "fat_g",
    "fiber_g": "fibc_g",
    "na_mg": "na_mg",
    "k_mg": "k_mg",
    "p_mg": "p_mg",
}
FIELD_MAP_2007 = {
    "kcal_100g": "enerc_kcal",
    "protein_g": "protein_g",
    "carb_g": "chocdf_g",
    "fat_g": "fat_g",
    "fiber_g": "fibc_g",
    "na_mg": "na_mg",
    "k_mg": "k_mg",
    "p_mg": "p_mg",
}


def norm(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def fmt_num(v: float | None) -> str:
    if v is None:
        return ""
    return str(int(v)) if v == int(v) else str(v)


def main() -> int:
    with open(GAP_PATH, newline="", encoding="utf-8") as handle:
        gap_header = handle.readline()
    with open(GAP_PATH, newline="", encoding="utf-8") as handle:
        gap_rows = list(csv.DictReader(handle))
    fieldnames = [c.strip() for c in gap_header.strip().split(",")]

    with open(FOOD_ITEMS_PATH, newline="", encoding="utf-8") as handle:
        food_items_rows = list(csv.DictReader(handle))
    food_items_fieldnames = list(food_items_rows[0].keys())

    nin2017 = json.loads(NIN2017_PATH.read_text(encoding="utf-8"))
    nin2017_by_name = {norm(r["name_vi"]): r for r in nin2017}
    nin2007 = {r["code"]: r for r in json.loads(NIN2007_PATH.read_text(encoding="utf-8"))}

    activated: list[dict] = []
    still_pending: list[dict] = []
    no_source_at_all: list[dict] = []

    for row in gap_rows:
        m2017 = nin2017_by_name.get(norm(row["name_vi"]))
        if not m2017:
            no_source_at_all.append(row)
            still_pending.append(row)
            continue

        code = m2017["code"]
        m2007 = nin2007.get(code)

        values: dict[str, float] = {}
        source_notes = [f"NIN 2017, ma {code}, tr.{m2017['page']}"]
        for field in CORE_FIELDS:
            v17 = m2017.get(FIELD_MAP_2017[field])
            if v17 is not None:
                values[field] = v17
                continue
            if m2007 is not None:
                v07 = m2007.get(FIELD_MAP_2007[field])
                if v07 is not None:
                    values[field] = v07

        if m2007 is not None:
            used_2007 = any(
                m2017.get(FIELD_MAP_2017[f]) is None and m2007.get(FIELD_MAP_2007[f]) is not None for f in CORE_FIELDS
            )
            if used_2007:
                source_notes.append(f"bo sung Na/K/P tu NIN 2007, ma {code}, tr.{m2007['page']}")

        missing = [f for f in CORE_FIELDS if f not in values]
        if not missing:
            new_row = {k: "" for k in food_items_fieldnames}
            new_row["id"] = row["id"]
            new_row["name_vi"] = row["name_vi"]
            new_row["aliases"] = row.get("aliases", "")
            new_row["category"] = row.get("category", "")
            for field, val in values.items():
                new_row[field] = fmt_num(val)
            new_row["source"] = "NIN"
            new_row["source_ref"] = "; ".join(source_notes)
            new_row["is_estimated"] = "FALSE"
            activated.append(new_row)
        else:
            updated = dict(row)
            updated["source_ref"] = (
                f"[CHUA DU LIEU - can DAT-13] {'; '.join(source_notes)} - con thieu: {', '.join(missing)}"
            )
            still_pending.append(updated)

    print(f"Tong dong dau vao: {len(gap_rows)}")
    print(f"  Kich hoat duoc (du 8 truong loi, chuyen sang seeds/): {len(activated)}")
    print(f"  Con thieu, giu lai quarantine/: {len(still_pending)}")
    print(f"  Khong khop ten NIN2017 nao (chua co manh moi): {len(no_source_at_all)}")

    if activated:
        food_items_rows.extend(activated)
        food_items_rows.sort(key=lambda r: int(r["id"]))
        with open(FOOD_ITEMS_PATH, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=food_items_fieldnames)
            writer.writeheader()
            writer.writerows(food_items_rows)

    with open(GAP_PATH, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(still_pending)

    print(f"\nDa ghi: {FOOD_ITEMS_PATH.relative_to(ROOT)} (+{len(activated)} dong)")
    print(f"Da ghi lai: {GAP_PATH.relative_to(ROOT)} ({len(still_pending)} dong con lai)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
