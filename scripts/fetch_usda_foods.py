#!/usr/bin/env python3
"""Tra cứu thực phẩm từ USDA FoodData Central (DAT-03).

Dùng cho món nhập khẩu / vi chất mà NIN thiếu. Cần USDA_API_Key trong .env
(miễn phí: https://fdc.nal.usda.gov/api-key-signup). Trả về/100 g phần ăn được.

USDA KHÔNG có purine (purine dùng bảng USDA/ODS-NIH Purine DB riêng).

Dùng:
  python scripts/fetch_usda_foods.py "atlantic salmon raw"
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import requests

from src.config import get_settings

SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# nutrientId USDA → cột schema food_items (giá trị/100 g).
NUTRIENT_ID_MAP: dict[int, str] = {
    1008: "kcal_100g",  # Energy (kcal)
    1003: "protein_g",  # Protein
    1004: "fat_g",  # Total lipid (fat)
    1005: "carb_g",  # Carbohydrate, by difference
    1079: "fiber_g",  # Fiber, total dietary
    2000: "sugar_g",  # Sugars, total including NLEA
    1093: "na_mg",  # Sodium, Na
    1092: "k_mg",  # Potassium, K
    1091: "p_mg",  # Phosphorus, P
}


def search_food(query: str, api_key: str, timeout: int = 25) -> dict[str, Any] | None:
    """Trả về món khớp nhất (ưu tiên Foundation/SR Legacy — dữ liệu phân tích)."""
    resp = requests.get(
        SEARCH_URL,
        params={
            "query": query,
            "api_key": api_key,
            "pageSize": 5,
            "dataType": "Foundation,SR Legacy",
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    foods = resp.json().get("foods", [])
    return foods[0] if foods else None


def to_schema_row(food: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "name_en": food.get("description", ""),
        "fdc_id": food.get("fdcId"),
        "source": "USDA",
        "source_ref": f"USDA FDC fdcId:{food.get('fdcId')}",
    }
    for nutrient in food.get("foodNutrients", []):
        col = NUTRIENT_ID_MAP.get(nutrient.get("nutrientId"))
        if col is not None:
            row[col] = nutrient.get("value")
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Tên món cần tra (tiếng Anh)")
    args = parser.parse_args()

    api_key = get_settings().usda_api_key
    if not api_key:
        print("Chưa cấu hình USDA_API_Key trong .env", file=sys.stderr)
        return 1

    food = search_food(args.query, api_key)
    if food is None:
        print(f"Không tìm thấy: {args.query}", file=sys.stderr)
        return 2
    import json

    print(json.dumps(to_schema_row(food), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
