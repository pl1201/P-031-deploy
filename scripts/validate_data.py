#!/usr/bin/env python3
"""Kiểm tra chất lượng dữ liệu seed trước khi nạp vào DB.

Ticket: DAT-02, DAT-05, EVL-03
Chạy: python scripts/validate_data.py   (hoặc `make validate-data`)

ERROR  → CI đỏ, không được merge.
WARN   → cho qua nhưng phải xử lý trước Demo Day.

Ba thứ script này bảo vệ:
  1. RULE R40.2 — không dòng nào thiếu nguồn
  2. RULE R40.3 — giá trị dinh dưỡng nằm trong khoảng hợp lý
  3. Tính nhất quán — không trùng id, không trùng tên
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

SEEDS = Path(__file__).resolve().parents[1] / "data" / "seeds"

# RULE R40.3 — khoảng hợp lý cho 100 g thực phẩm.
# Trần natri để cao vì nước mắm và bột canh thực sự rất mặn.
RANGES: dict[str, tuple[float, float]] = {
    "kcal_100g": (0, 900),
    "protein_g": (0, 90),
    "carb_g": (0, 100),
    "fat_g": (0, 100),
    "fiber_g": (0, 80),
    "na_mg": (0, 25000),
    "k_mg": (0, 5000),
    "p_mg": (0, 2000),
    "purine_mg": (0, 1000),
    "gi_index": (0, 110),
}

VALID_SOURCES = {"NIN", "USDA", "curated", "estimated"}
PLACEHOLDER = {"", "todo", "tbd", "n/a", "-", "?", "x"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def check_food_items(path: Path) -> None:
    if not path.exists():
        warn(f"{path.name}: chưa có file (đang dùng template?)")
        return

    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    filled = 0

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for i, row in enumerate(rows, start=2):
        name = (row.get("name_vi") or "").strip()
        rid = (row.get("id") or "").strip()
        loc = f"{path.name}:{i} [{name or '?'}]"

        if not name:
            err(f"{loc} thiếu name_vi")
        if rid in seen_ids:
            err(f"{loc} trùng id={rid}")
        seen_ids.add(rid)
        if name.lower() in seen_names:
            err(f"{loc} trùng tên với dòng trước")
        seen_names.add(name.lower())

        # Dòng chưa nhập số liệu thì bỏ qua phần kiểm tra giá trị
        if not (row.get("kcal_100g") or "").strip():
            continue
        filled += 1

        source = (row.get("source") or "").strip()
        source_ref = (row.get("source_ref") or "").strip()

        # RULE R40.2 — không dòng nào thiếu nguồn
        if source not in VALID_SOURCES:
            err(f"{loc} source='{source}' không hợp lệ (phải là {sorted(VALID_SOURCES)})")
        if source_ref.lower() in PLACEHOLDER:
            err(f"{loc} source_ref rỗng hoặc placeholder — vi phạm RULE R40.2")
        if source == "estimated" and (row.get("is_estimated") or "").upper() != "TRUE":
            err(f"{loc} source=estimated nhưng is_estimated không phải TRUE")

        # RULE R40.3 — khoảng hợp lý
        for col, (lo, hi) in RANGES.items():
            raw = (row.get(col) or "").strip()
            if not raw:
                if col != "gi_index":
                    err(f"{loc} thiếu giá trị cột {col}")
                continue
            try:
                val = float(raw)
            except ValueError:
                err(f"{loc} cột {col} không phải số: '{raw}'")
                continue
            if not (lo <= val <= hi):
                err(f"{loc} {col}={val} ngoài khoảng hợp lý [{lo}, {hi}]")

        # Kiểm tra chéo: tổng đa chất không được vượt quá 100 g / 100 g thực phẩm
        try:
            macro = sum(
                float(row.get(c) or 0) for c in ("protein_g", "carb_g", "fat_g", "fiber_g")
            )
            if macro > 105:
                err(f"{loc} tổng đa chất {macro:.1f} g/100 g — bất khả thi")
        except ValueError:
            pass

    print(f"  {path.name}: {len(rows)} dòng, {filled} dòng đã nhập số liệu")
    if filled < len(rows):
        warn(
            f"{path.name}: còn {len(rows) - filled} dòng chưa nhập số liệu "
            "(xem cột assigned_to để biết ai phụ trách)"
        )


def check_clinical_rules(path: Path) -> None:
    if not path.exists():
        err(f"Thiếu {path.name} — không có ngưỡng lâm sàng thì hệ thống không chạy được")
        return

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    to_verify = 0
    for i, row in enumerate(rows, start=2):
        loc = f"{path.name}:{i} [{row.get('rule_id')}]"
        if not (row.get("guideline_ref") or "").strip():
            err(f"{loc} thiếu guideline_ref — mọi ngưỡng phải dẫn được nguồn (RULE R10.4)")
        if row.get("bound") not in {"max", "min"}:
            err(f"{loc} bound phải là max hoặc min")
        if row.get("severity") not in {"hard", "soft"}:
            err(f"{loc} severity phải là hard hoặc soft")
        if row.get("basis") not in {"absolute", "per_kg", "pct_energy", "per_1000kcal"}:
            err(f"{loc} basis không hợp lệ")
        if (row.get("verify_status") or "").strip() == "to_verify":
            to_verify += 1

    print(f"  {path.name}: {len(rows)} rule")
    if to_verify:
        warn(
            f"{path.name}: {to_verify} rule ở trạng thái 'to_verify' — "
            "R2 phải đối chiếu guideline gốc trước Demo Day (ticket DAT-00)"
        )


def check_drug_food(path: Path) -> None:
    if not path.exists():
        warn(f"{path.name}: chưa có file")
        return

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    missing_ref = 0
    for i, row in enumerate(rows, start=2):
        loc = f"{path.name}:{i} [{row.get('drug_name')}]"
        if row.get("severity") not in {"high", "moderate", "low"}:
            err(f"{loc} severity không hợp lệ")
        if not (row.get("recommendation_vi") or "").strip():
            err(f"{loc} thiếu khuyến nghị — cảnh báo phải hành động được (RULE R10.7)")
        if not (row.get("source_ref") or "").strip():
            missing_ref += 1

    print(f"  {path.name}: {len(rows)} cặp tương tác")
    if missing_ref:
        warn(f"{path.name}: {missing_ref} cặp chưa có source_ref — phải điền trước khi lên slide")


def main() -> int:
    print("Kiểm tra dữ liệu seed...")
    check_food_items(SEEDS / "food_items.csv")
    check_food_items(SEEDS / "food_items.template.csv")
    check_clinical_rules(SEEDS / "clinical_rules.csv")
    check_drug_food(SEEDS / "drug_food_interactions.csv")

    print()
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")

    print()
    if errors:
        print(f"❌ {len(errors)} lỗi, {len(warnings)} cảnh báo — KHÔNG được merge")
        return 1
    print(f"✅ Không có lỗi. {len(warnings)} cảnh báo cần xử lý trước Demo Day.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
