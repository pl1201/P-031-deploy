#!/usr/bin/env python3
"""Tách `data/seeds/` thành ba tầng theo bản chất dữ liệu (DAT-23 / DEC-022).

Chạy: python scripts/split_data_tiers.py [--dry-run]

Vấn đề: `food_items.csv` (7745 dòng) và `dishes.csv` (2677 dòng) đang gộp bốn
nguồn khác bản chất vào một file phẳng — món Việt curated, bảng NIN 2017, khối
tham chiếu USDA/FNDDS tiếng Anh, và mẫu thực đơn Excel. Hệ quả: mỗi loader tự
lọc rác theo cách riêng, lọc lệch nhau, và `MENU-*` từng lọt lên UI bệnh nhân.

Sau khi tách:

    data/seeds/       chỉ thứ được seed vào DB ứng dụng — CHẠM TỚI BỆNH NHÂN
    data/reference/   tra cứu/đối chiếu (USDA/FNDDS) — không seed, không load
    data/quarantine/  nợ dữ liệu chờ R2 duyệt — không seed, không load

Script này TẤT ĐỊNH và IDEMPOTENT: chạy lại trên kết quả đã tách cho cùng kết
quả (các tầng đã rỗng thì không có gì để chuyển). Ranh giới tầng lấy từ
`src/clinical/tiers.py` — không định nghĩa lại ở đây.

An toàn dữ liệu:
- Kiểm tra mọi dòng đúng số cột TRƯỚC khi ghi bất cứ thứ gì.
- In bảng đối chiếu vào/ra và khẳng định TỔNG SỐ DÒNG KHÔNG ĐỔI — không dòng
  nào bị mất im lặng.
- Từ chối chạy nếu có tham chiếu chéo tầng (món tầng seed dùng nguyên liệu
  thuộc tầng khác), vì tách trong trường hợp đó sẽ làm vỡ công thức món.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.clinical.tiers import (  # noqa: E402
    REFERENCE_DISH_PREFIXES,
    TEMPLATE_DISH_PREFIXES,
    is_patient_facing_food,
)

SEEDS = ROOT / "data" / "seeds"
REFERENCE = ROOT / "data" / "reference"
QUARANTINE = ROOT / "data" / "quarantine"

SEED, REF, QUAR = "seeds", "reference", "quarantine"


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Đọc CSV và khẳng định mọi dòng đúng số cột trước khi dùng."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        malformed = [i for i, row in enumerate(reader, start=2) if len(row) != len(header)]
    if malformed:
        raise SystemExit(
            f"❌ {path.name}: {len(malformed)} dòng sai số cột (dòng {malformed[:5]}) — dừng, không ghi gì"
        )
    with open(path, newline="", encoding="utf-8") as handle:
        return header, list(csv.DictReader(handle))


def _replace(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    """Ghi đè hoàn toàn — chỉ dùng cho `data/seeds/`, nguồn đầu vào của lần tách."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _merge(path: Path, header: list[str], rows: list[dict[str, str]], key: tuple[str, ...]) -> None:
    """HỢP NHẤT các dòng mới vào file tầng đích, không bao giờ thay thế nội dung cũ.

    Ghi đè là sai ở đây và đã suýt gây mất dữ liệu thật khi thử nghiệm: lần chạy
    thứ hai, `seeds/` đã sạch nên không còn dòng nào để chuyển — ghi đè sẽ xoá
    6854 dòng đã tách ở lần một, chỉ còn dòng header. Hợp nhất theo khoá cũng là
    thứ cho phép chạy lại sau khi đội thêm dữ liệu mới vào `seeds/` mà không mất
    những gì đã tách trước đó.
    """
    existing: list[dict[str, str]] = []
    if path.exists():
        _, existing = _read(path)
    seen = {tuple(row.get(k, "") for k in key) for row in existing}
    fresh = [row for row in rows if tuple(row.get(k, "") for k in key) not in seen]

    if not fresh:
        print(f"   giữ nguyên {path.name} ({len(existing)} dòng — không có dòng mới)")
        return

    merged_header = existing and _read(path)[0] or header
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=merged_header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows([*existing, *fresh])
    print(f"   {path.name}: {len(existing)} cũ + {len(fresh)} mới = {len(existing) + len(fresh)}")


def classify_food(row: dict[str, str]) -> str:
    """Tầng của một dòng `food_items`.

    Dòng chưa có số liệu dinh dưỡng đi `quarantine` chứ không ở `seeds`: loader
    vẫn bỏ qua chúng, nhưng để trong `seeds` khiến validator phải có nhánh
    "bỏ qua dòng rỗng" và nợ trở nên vô hình.
    """
    if not is_patient_facing_food(int(row["id"])):
        return REF
    if not (row.get("kcal_100g") or "").strip():
        return QUAR
    return SEED


def classify_dish(dish_id: str) -> str:
    if dish_id.startswith(REFERENCE_DISH_PREFIXES):
        return REF
    if dish_id.startswith(TEMPLATE_DISH_PREFIXES):
        return QUAR
    return SEED


def to_name_en(header: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
    """Chuyển `name_vi` (đang chứa tiếng Anh) sang `name_en` cho tầng tham chiếu.

    KHÔNG dịch máy, KHÔNG bịa tên Việt — `name_vi` để rỗng cho tới khi có nguồn
    thật (RULE-2). Chỉ áp dụng cho `data/reference/`.
    """
    new_header = [*header]
    if "name_en" not in new_header:
        new_header.insert(new_header.index("name_vi") + 1, "name_en")
    moved = [{**row, "name_en": row.get("name_vi", ""), "name_vi": ""} for row in rows]
    return new_header, moved


def normalize_reference_names(path: Path) -> None:
    """Đảm bảo file tầng tham chiếu có cột `name_en` và tên tiếng Anh nằm đúng chỗ.

    Chạy độc lập với bước hợp nhất, vì các dòng đã có sẵn trong file gốc sẽ bị
    `_merge()` bỏ qua và do đó không bao giờ được chuyển cột. Idempotent: file
    đã chuẩn hoá rồi thì không đụng tới.
    """
    if not path.exists():
        return
    header, rows = _read(path)
    if "name_en" in header:
        return
    new_header, moved = to_name_en(header, rows)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=new_header)
        writer.writeheader()
        writer.writerows(moved)
    print(f"   {path.name}: chuyển {len(moved)} tên tiếng Anh sang cột name_en")


def assert_no_cross_tier_refs(
    ingredients: list[dict[str, str]],
    food_tier: dict[str, str],
) -> None:
    """Món ở tầng `seeds` chỉ được dùng nguyên liệu cũng ở tầng `seeds`.

    Nếu vi phạm, tách sẽ làm món mất nguyên liệu và mật độ dinh dưỡng sai —
    đúng cơ chế đã gây bug thực đơn thiếu năng lượng (DEVLOG 2026-08-07).
    """
    broken = [
        (row["dish_id"], row["food_id"], food_tier.get(row["food_id"], "MISSING"))
        for row in ingredients
        if classify_dish(row["dish_id"]) == SEED and food_tier.get(row["food_id"]) != SEED
    ]
    if broken:
        raise SystemExit(
            f"❌ {len(broken)} nguyên liệu của món tầng seeds trỏ ra ngoài tầng seeds — "
            f"tách sẽ làm vỡ công thức. Ví dụ: {broken[:5]}"
        )


def report(title: str, counts: Counter[str], total_in: int) -> None:
    print(f"\n{title}")
    for tier in (SEED, REF, QUAR):
        print(f"   {counts[tier]:>6}  data/{tier}/")
    total_out = sum(counts.values())
    mark = "✅" if total_out == total_in else "❌"
    print(f"   {'-' * 30}\n   {total_out:>6}  tổng ra / {total_in} vào  {mark}")
    if total_out != total_in:
        raise SystemExit("❌ Số dòng ra khác số dòng vào — dừng, không ghi gì")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="chỉ in bảng đối chiếu, không ghi file")
    args = parser.parse_args()

    food_header, foods = _read(SEEDS / "food_items.csv")
    dish_header, dishes = _read(SEEDS / "dishes.csv")
    ing_header, ingredients = _read(SEEDS / "dish_ingredients.csv")

    food_tier = {row["id"]: classify_food(row) for row in foods}
    assert_no_cross_tier_refs(ingredients, food_tier)

    foods_by: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in foods:
        foods_by[food_tier[row["id"]]].append(row)

    dish_tier = {row["dish_id"]: classify_dish(row["dish_id"]) for row in dishes}
    dishes_by: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in dishes:
        dishes_by[dish_tier[row["dish_id"]]].append(row)

    # Nguyên liệu đi theo món của nó — không bao giờ tách rời công thức.
    ings_by: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ingredients:
        ings_by[classify_dish(row["dish_id"])].append(row)

    report("food_items.csv", Counter({k: len(v) for k, v in foods_by.items()}), len(foods))
    report("dishes.csv", Counter({k: len(v) for k, v in dishes_by.items()}), len(dishes))
    report("dish_ingredients.csv", Counter({k: len(v) for k, v in ings_by.items()}), len(ingredients))

    if args.dry_run:
        print("\n(--dry-run: không ghi file nào)")
        return 0

    ref_food_header, ref_foods = to_name_en(food_header, foods_by[REF])
    ref_dish_header, ref_dishes = to_name_en(dish_header, dishes_by[REF])

    print("\nGhi kết quả:")
    _replace(SEEDS / "food_items.csv", food_header, foods_by[SEED])
    _replace(SEEDS / "dishes.csv", dish_header, dishes_by[SEED])
    _replace(SEEDS / "dish_ingredients.csv", ing_header, ings_by[SEED])

    # Ghi vào chính các file bulk gốc (đã có git history) thay vì tạo bản sao —
    # nội dung trùng khít, giữ hai bản chỉ làm `data/` phình thêm lần nữa.
    _merge(REFERENCE / "food_items.usda_bulk.csv", ref_food_header, ref_foods, ("id",))
    _merge(REFERENCE / "dishes.fndds_bulk.csv", ref_dish_header, ref_dishes, ("dish_id",))
    _merge(REFERENCE / "dish_ingredients.fndds_bulk.csv", ing_header, ings_by[REF], ("dish_id", "food_id"))

    _merge(QUARANTINE / "food_items.chua_co_so_lieu.csv", food_header, foods_by[QUAR], ("id",))
    _merge(QUARANTINE / "dishes.menu_xlsx.csv", dish_header, dishes_by[QUAR], ("dish_id",))
    _merge(QUARANTINE / "dish_ingredients.menu_xlsx.csv", ing_header, ings_by[QUAR], ("dish_id", "food_id"))

    # Việt hoá tầng tham chiếu: tên tiếng Anh về đúng cột `name_en`, `name_vi`
    # để rỗng cho tới khi có nguồn thật — không dịch máy, không bịa (RULE-2).
    normalize_reference_names(REFERENCE / "food_items.usda_bulk.csv")
    normalize_reference_names(REFERENCE / "dishes.fndds_bulk.csv")

    print("\n✅ Đã tách. Chạy tiếp: python scripts/validate_data.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
