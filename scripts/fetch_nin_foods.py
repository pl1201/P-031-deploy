#!/usr/bin/env python3
"""Tải dữ liệu thành phần thực phẩm từ API công khai của Viện Dinh dưỡng (NIN).

Ticket: DAT-02 (nguồn NIN), DAT-03 (fetcher). Nguồn: Bảng thành phần thực phẩm
Việt Nam — Viện Dinh dưỡng, Bộ Y tế. https://viendinhduong.vn

⚠️ Bản quyền (xem data/README.md): KHÔNG commit trọn bộ 853 món vào repo. Script này
là công cụ tái lập; chỉ những dòng thực sự dùng (đã map sang food_items) mới được đưa
vào seed, kèm source_ref = mã NIN.

Dùng:
  python scripts/fetch_nin_foods.py --out data/cache/nin_foods.json      # cache thô (gitignore)
  python scripts/fetch_nin_foods.py --match data/seeds/food_items.template.csv  # báo cáo khớp

API trả mỗi món kèm mảng `nutrition` đầy đủ. Đơn vị: /100 g phần ăn được.
NIN có: protein, fat, carb, chất xơ, đường tổng, Na, K, P. KHÔNG có purine (gout) → USDA/khác.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import requests

API_URL = "https://viendinhduong.vn/api/fe/foodNatunal/getPageFoodData"

# Ánh xạ tên chất NIN (name_en) → cột schema food_items.
NUTRIENT_MAP: dict[str, str] = {
    "Protein": "protein_g",
    "Total lipid (Fat)": "fat_g",
    "Carbohydrate by difference": "carb_g",
    "Fibre, total dietary": "fiber_g",
    "Sugars, total": "sugar_g",
    "Na": "na_mg",
    "K": "k_mg",
    "P": "p_mg",
}


def fetch_all(timeout: int = 40) -> list[dict[str, Any]]:
    """Tải toàn bộ món trong một lần gọi (API hỗ trợ pageSize lớn)."""
    resp = requests.get(
        API_URL,
        params={"page": 1, "pageSize": 2000, "energy": 0},
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    payload = resp.json()
    return payload["data"]


def to_schema_row(food: dict[str, Any]) -> dict[str, Any]:
    """Chuyển một món NIN sang các cột food_items (chỉ chất có trong schema)."""
    row: dict[str, Any] = {
        "name_vi": food["name_vi"],
        "name_en": food.get("name_en", ""),
        "category": food.get("category", ""),
        "kcal_100g": food.get("energy"),
        "source": "NIN",
        "source_ref": f"NIN Bảng TPTP VN (mã {food['code']})",
    }
    for nutrient in food.get("nutrition", []):
        col = NUTRIENT_MAP.get(nutrient.get("name_en", ""))
        if col is not None:
            row[col] = nutrient.get("value")
    return row


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", text).strip()


def match_template(foods: list[dict[str, Any]], template_path: Path) -> None:
    """Báo cáo mức khớp giữa food_items.template.csv và NIN (chỉ báo cáo, KHÔNG ghi seed).

    Khớp bằng substring nên PHẢI có người kiểm (VD 'Cơm tẻ' nấu chín ≠ 'Gạo tẻ sống').
    """
    index = {_norm(f["name_vi"]): f for f in foods}
    with open(template_path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    matched = 0
    for row in rows:
        key = _norm(row["name_vi"])
        hit = index.get(key)
        confidence = "exact"
        if hit is None:
            cands = [f for k, f in index.items() if key and (key in k or k in key)]
            hit = cands[0] if cands else None
            confidence = "substring" if hit else "MISS"
        if hit is not None:
            matched += 1
        code = hit["code"] if hit else "-"
        nin_name = hit["name_vi"] if hit else "-"
        print(f"{confidence:9} | {row['name_vi']:32} | {code:7} | {nin_name}")
    print(f"\nKhớp {matched}/{len(rows)} món. Dòng 'substring'/'MISS' cần R2 kiểm tay.", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Ghi cache JSON thô (đừng commit)")
    parser.add_argument("--match", type=Path, help="Đối chiếu với template và in báo cáo khớp")
    args = parser.parse_args()

    foods = fetch_all()
    print(f"Đã tải {len(foods)} món từ NIN.", file=sys.stderr)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        json.dump(foods, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Đã ghi cache: {args.out}", file=sys.stderr)
    if args.match:
        match_template(foods, args.match)
    if not args.out and not args.match:
        # Mặc định: in vài dòng mẫu đã map sang schema để kiểm nhanh
        for food in foods[:3]:
            print(json.dumps(to_schema_row(food), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
