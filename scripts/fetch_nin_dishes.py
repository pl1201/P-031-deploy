#!/usr/bin/env python3
"""Tải dữ liệu MÓN ĂN từ API công khai Viện Dinh dưỡng (NIN) — ticket DAT-04.

Nguồn: https://viendinhduong.vn — công cụ "Giá trị dinh dưỡng của món ăn" (1250 món).
Mỗi món có dinh dưỡng/100 g phần ăn được: năng lượng, đạm, béo, carb, **Natri (kèm
tương đương muối)**, Kali, chất xơ, cholesterol. KHÔNG có purine; `dish_components`
(công thức nguyên liệu) hiện để trống trên API.

Bao gồm đúng nhóm món "nguy hiểm" natri cao của đề bài: bún riêu, bún bò Huế, cháo…

⚠️ Bản quyền: KHÔNG commit trọn bộ; chỉ subset đã dùng (đã map sang dishes), kèm mã NIN.

Dùng:
  python scripts/fetch_nin_dishes.py --search "bún riêu"     # tìm nhanh
  python scripts/fetch_nin_dishes.py --out data/cache/nin_dishes.json   # cache (gitignore)
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

import requests

API_URL = "https://viendinhduong.vn/api/fe/tool/getPageFoodData"

# Tên chất (name) NIN → khoá schema dishes.
COMPONENT_MAP: dict[str, str] = {
    "Năng lượng": "kcal",
    "Chất đạm": "protein_g",
    "Chất béo": "fat_g",
    "Chất bột đường": "carb_g",
    "Natri": "na_mg",
    "Kali": "k_mg",
    "Xơ": "fiber_g",
    "Cholesterol": "cholesterol_mg",
}


def fetch_all(timeout: int = 40) -> list[dict[str, Any]]:
    resp = requests.get(
        API_URL,
        params={"page": 1, "pageSize": 2000},
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def to_schema_row(dish: dict[str, Any]) -> dict[str, Any]:
    """Chuyển một món NIN sang các cột dinh dưỡng + tương đương muối (g)."""
    row: dict[str, Any] = {
        "name_vi": dish["name_vi"],
        "name_en": dish.get("name_en", ""),
        "category": dish.get("category_name", ""),
        "source": "NIN",
        "source_ref": f"NIN Giá trị dinh dưỡng món ăn (mã {dish['code']})",
    }
    for comp in dish.get("nutritional_components", []):
        col = COMPONENT_MAP.get(comp.get("name", ""))
        if col is not None:
            row[col] = comp.get("amount", "")
        if comp.get("name") == "Natri":
            for eq in comp.get("equivalenceComponents", []):
                if eq.get("key") == "tuong-duong-muoi":
                    row["salt_equiv_g"] = eq.get("amount", "")
    return row


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Ghi cache JSON thô (đừng commit)")
    parser.add_argument("--search", type=str, help="Lọc theo tên (không dấu)")
    args = parser.parse_args()

    dishes = fetch_all()
    print(f"Đã tải {len(dishes)} món ăn từ NIN.", file=sys.stderr)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        json.dump(dishes, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Đã ghi cache: {args.out}", file=sys.stderr)
    if args.search:
        needle = _norm(args.search)
        for dish in dishes:
            if needle in _norm(dish["name_vi"]):
                print(json.dumps(to_schema_row(dish), ensure_ascii=False))
    elif not args.out:
        for dish in dishes[:3]:
            print(json.dumps(to_schema_row(dish), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
