"""Nạp seed CSV (food_items, dishes, dish_ingredients) thành object tầng lâm sàng.

LLM: NO — thuần dữ liệu. Ticket: DAT-02, DAT-04.

Món ăn được phân rã thành nguyên liệu (food_id + gram); dinh dưỡng của món tính
bằng compute_nutrition() — KHÔNG lưu con số dinh dưỡng của món (RULE-1).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from .models import DishCandidate, FoodItem, MealSlot, MenuDraft, MenuItem
from .nutrition import InMemoryFoodRepository
from .tiers import is_patient_facing_dish

SEEDS_DIR = Path(__file__).resolve().parents[2] / "data" / "seeds"

# Muối ăn (NaCl) = 39,3% natri → khối muối tương đương = Na(mg)/1000 / 0,393.
SALT_PER_NA_MG = 2.54 / 1000


def _split(raw: str | None) -> list[str]:
    return [s.strip() for s in (raw or "").split("|") if s.strip()]


def _opt_float(raw: str | None) -> float | None:
    raw = (raw or "").strip()
    return float(raw) if raw else None


def _opt_str(raw: str | None) -> str | None:
    raw = (raw or "").strip()
    return raw or None


def load_food_repository(path: Path | None = None) -> InMemoryFoodRepository:
    """Nạp các dòng ĐÃ có số liệu trong food_items.csv thành FoodItem."""
    path = path or SEEDS_DIR / "food_items.csv"
    items: list[FoodItem] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not (row.get("kcal_100g") or "").strip():
                continue  # dòng chưa nhập số liệu
            items.append(
                FoodItem(
                    id=int(row["id"]),
                    name_vi=row["name_vi"],
                    aliases=_split(row.get("aliases")),
                    kcal_100g=float(row["kcal_100g"]),
                    protein_g=float(row["protein_g"]),
                    carb_g=float(row["carb_g"]),
                    fat_g=float(row["fat_g"]),
                    fiber_g=float(row["fiber_g"]),
                    sugar_g=_opt_float(row.get("sugar_g")),
                    na_mg=float(row["na_mg"]),
                    k_mg=float(row["k_mg"]),
                    p_mg=float(row["p_mg"]),
                    purine_mg=_opt_float(row.get("purine_mg")),
                    purine_source_ref=_opt_str(row.get("purine_source_ref")),
                    gi_index=_opt_float(row.get("gi_index")),
                    gi_source=_opt_str(row.get("gi_source")),  # type: ignore[arg-type]
                    gi_source_ref=_opt_str(row.get("gi_source_ref")),
                    contains_allergens=_split(row.get("contains_allergens")),
                    source=row["source"],  # type: ignore[arg-type]
                    source_ref=row["source_ref"],
                    is_estimated=(row.get("is_estimated") or "").strip().upper() == "TRUE",
                )
            )
    return InMemoryFoodRepository(items)


def load_dish_menus(path: Path | None = None) -> dict[str, MenuDraft]:
    """Trả về {dish_id: MenuDraft} — mỗi món là tập nguyên liệu (food_id + gram)."""
    path = path or SEEDS_DIR / "dish_ingredients.csv"
    by_dish: dict[str, list[MenuItem]] = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_dish[row["dish_id"]].append(MenuItem(food_id=int(row["food_id"]), grams=float(row["grams"])))
    return {did: MenuDraft(items={MealSlot.LUNCH: items}) for did, items in by_dish.items()}


def load_vn_dishes(path: Path | None = None, ingredients_path: Path | None = None) -> list[DishCandidate]:
    """Nạp danh sách món ăn Việt Nam curated thật từ `dishes.csv`.

    `dishes.csv` hiện lẫn 2 nhóm dưới cùng file: ~2630 dòng `verified_by`=
    "USDA FNDDS (nguồn chính thức)" là khối import bulk khảo sát thực phẩm Mỹ
    (tên kiểu "Milk, whole", "Crackers, wheat (Wheat Thins)") — KHÔNG phải món
    Việt, bị loại ở đây. Chỉ ~45 dòng còn lại là món Việt curated thật, nhưng
    `verified_by="pending"` — R2 CHƯA rà công thức, nên trả về kèm
    `is_reviewed=False` để tầng trên cảnh báo, không tự ý coi là đã duyệt.
    Trong số đó, món tự ghi chú thiếu nguyên liệu (xem `incomplete_recipe_markers`
    bên dưới) bị loại hẳn — không đủ căn cứ dùng làm candidate CP-SAT (audit
    2026-08-08, xem DEVLOG). Số món dùng được thật hiện rất mỏng (~28/2678
    dòng file) — cần R2 mở rộng, xem `docs/TICKETS.md`.

    DAT-23/DEC-022: ranh giới tầng giờ lấy từ `clinical.tiers` thay vì tự suy ra
    từ cột `verified_by`. Bộ lọc cũ dựa vào `verified_by` bắt đầu bằng
    "USDA FNDDS" nên loại được `FNDDS-*` nhưng **bỏ lọt `MENU-*`** (các dòng này
    có `verified_by="pending"`, không khớp) — đó là nguyên nhân trực tiếp của bug
    tên món giả "Bữa sáng - Thực đơn 3 (TĐ 3+4)" hiện trên UI bệnh nhân.
    """
    path = path or SEEDS_DIR / "dishes.csv"
    ingredients_path = ingredients_path or SEEDS_DIR / "dish_ingredients.csv"

    ingredients_by_dish: dict[str, list[MenuItem]] = defaultdict(list)
    with open(ingredients_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ingredients_by_dish[row["dish_id"]].append(MenuItem(food_id=int(row["food_id"]), grams=float(row["grams"])))

    # Audit 2026-08-08: 17/45 món curated tự ghi chú trong cột `note` là thiếu
    # nguyên liệu quan trọng (VD PHO-BO thiếu gia vị/nước dùng, các món
    # "-VCB" thiếu nguyên liệu chính chưa ghép food_id — xem note gốc từng
    # dòng). Thiếu DÒNG nguyên liệu (không phải thiếu GIÁ TRỊ trên dòng đã
    # có) không bị RULE-2/`_eligible_dishes` bắt được — món vẫn "tính được"
    # nhưng mật độ dinh dưỡng bị pha loãng sai (gây bug thực đơn thiếu năng
    # lượng nghiêm trọng, xem DEVLOG 2026-08-07). Loại tạm cho tới khi R2 rà
    # xong (xem docs/TICKETS.md).
    incomplete_recipe_markers = ("THIẾU", "CHƯA GHÉP", "R2 cần rà")

    dishes: list[DishCandidate] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not is_patient_facing_dish(row["dish_id"]):
                continue  # FNDDS-* (bulk Mỹ) và MENU-* (mẫu bữa, không phải món)
            verified = (row.get("verified_by") or "").strip()
            note = row.get("note") or ""
            if any(marker in note for marker in incomplete_recipe_markers):
                continue  # công thức tự ghi nhận chưa đủ nguyên liệu — chờ R2 rà
            items = ingredients_by_dish.get(row["dish_id"], [])
            if not items:
                continue  # món chưa có nguyên liệu — không đủ căn cứ dùng làm candidate
            dishes.append(
                DishCandidate(
                    dish_id=row["dish_id"],
                    name_vi=row["name_vi"],
                    region=_opt_str(row.get("region")),
                    is_reviewed=bool(verified) and verified.lower() != "pending",
                    verified_by=_opt_str(row.get("verified_by")),
                    ingredients=items,
                )
            )
    return dishes


def salt_equiv_g(na_mg: float) -> float:
    """Khối muối tương đương (g) từ natri (mg). Dùng cho cảnh báo muối/bát."""
    return round(na_mg * SALT_PER_NA_MG, 2)
