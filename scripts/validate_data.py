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

# CI runner có thể không đặt locale UTF-8 → in tiếng Việt sẽ UnicodeEncodeError.
# Ép stdout/stderr về UTF-8 để script chạy được ở mọi môi trường.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.clinical.tiers import NON_PATIENT_DISH_PREFIXES  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"
SEEDS = DATA / "seeds"
QUARANTINE = DATA / "quarantine"  # nợ dữ liệu chờ R2, không seed (DAT-23)

# RULE R40.3 — khoảng hợp lý cho 100 g thực phẩm.
# Trần natri để cao vì nước mắm và bột canh thực sự rất mặn.
RANGES: dict[str, tuple[float, float]] = {
    "kcal_100g": (0, 920),
    "protein_g": (0, 90),
    "carb_g": (0, 100),
    "fat_g": (0, 100),
    "fiber_g": (0, 80),
    "sugar_g": (0, 100),
    "na_mg": (0, 40000),
    "k_mg": (0, 5000),
    "p_mg": (0, 2000),
    "purine_mg": (0, 1000),
    "gi_index": (0, 110),
}

# Cột số liệu được phép để trống (không phải mọi nguồn đều có).
# gi_index: GI phủ thưa. sugar_g: nhiều nguồn không tách đường khỏi carb tổng.
OPTIONAL_NUMERIC_COLS = {"gi_index", "sugar_g", "purine_mg"}

VALID_SOURCES = {"NIN", "USDA", "curated", "estimated"}
VALID_GI_SOURCES = {"Atkinson2021", "Chan2001_VN", "estimated"}
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
                if col not in OPTIONAL_NUMERIC_COLS:
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
        # LƯU Ý: fiber_g (chất xơ) trong NIN 2017 (CHOCDF) đã là carbohydrate
        # tổng, chất xơ là MỘT PHẦN của carb_g, không cộng dồn thêm — cộng
        # riêng fiber_g sẽ đếm hai lần với thực phẩm khô/nhiều xơ (VD Măng
        # khô, Hạt tiêu) và báo lỗi giả (DAT-22, phát hiện khi merge NIN 2017).
        try:
            macro = sum(float(row.get(c) or 0) for c in ("protein_g", "carb_g", "fat_g"))
            if macro > 105:
                err(f"{loc} tổng đa chất {macro:.1f} g/100 g — bất khả thi")
        except ValueError:
            pass

        # RULE-2 cho cột GI: có trị GI thì phải dẫn nguồn GI riêng (DAT-07).
        gi_raw = (row.get("gi_index") or "").strip()
        if gi_raw:
            gi_source = (row.get("gi_source") or "").strip()
            gi_ref = (row.get("gi_source_ref") or "").strip()
            if gi_source not in VALID_GI_SOURCES:
                err(
                    f"{loc} gi_index có trị nhưng gi_source='{gi_source}' không hợp lệ "
                    f"(phải là {sorted(VALID_GI_SOURCES)}) — RULE-2"
                )
            if gi_ref.lower() in PLACEHOLDER:
                err(f"{loc} gi_index có trị nhưng thiếu gi_source_ref — RULE-2")

        # RULE-2 cho purine: có trị purine thì phải dẫn nguồn purine riêng (USDA Purine DB).
        pur_raw = (row.get("purine_mg") or "").strip()
        if pur_raw and (row.get("purine_source_ref") or "").strip().lower() in PLACEHOLDER:
            err(f"{loc} purine_mg có trị nhưng thiếu purine_source_ref — RULE-2")

        # Đường là tập con của carb tổng.
        sugar_raw = (row.get("sugar_g") or "").strip()
        carb_raw = (row.get("carb_g") or "").strip()
        if sugar_raw and carb_raw:
            try:
                if float(sugar_raw) > float(carb_raw):
                    err(f"{loc} sugar_g={sugar_raw} > carb_g={carb_raw} — đường phải ≤ carb tổng")
            except ValueError:
                pass

    print(f"  {path.name}: {len(rows)} dòng, {filled} dòng đã nhập số liệu")
    if filled < len(rows):
        warn(f"{path.name}: còn {len(rows) - filled} dòng chưa nhập số liệu (xem cột assigned_to để biết ai phụ trách)")


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
        if not (row.get("guideline_grade") or "").strip():
            err(f"{loc} thiếu guideline_grade — cần mức bằng chứng để chọn severity")
        # Khuyến nghị yếu (2C/2D) không nên là ràng buộc chặn cứng
        if (row.get("guideline_grade") or "").strip() in {"2C", "2D"} and row.get("severity") == "hard":
            warn(
                f"{loc} mức bằng chứng {row.get('guideline_grade')} (yếu) nhưng severity=hard — cân nhắc hạ xuống soft"
            )
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


def check_food_food_interactions(path: Path) -> None:
    if not path.exists():
        warn(f"{path.name}: chưa có file")
        return

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    to_verify = 0
    for i, row in enumerate(rows, start=2):
        loc = f"{path.name}:{i} [{row.get('substance_a')} x {row.get('substance_b')}]"
        if row.get("direction") not in {"increases", "decreases"}:
            err(f"{loc} direction không hợp lệ")
        if row.get("clinical_significance") not in {"high", "moderate", "low"}:
            err(f"{loc} clinical_significance không hợp lệ")
        if not (row.get("source_ref") or "").strip():
            err(f"{loc} thiếu source_ref (RULE-2)")
        if (row.get("verify_status") or "to_verify") == "to_verify":
            to_verify += 1

    print(f"  {path.name}: {len(rows)} cặp tương tác thực phẩm-thực phẩm")
    if to_verify:
        warn(f"{path.name}: {to_verify} cặp ở trạng thái 'to_verify' — R2 cần đối chiếu trước Demo Day (DAT-18)")


def check_drug_meal_timing(path: Path) -> None:
    if not path.exists():
        warn(f"{path.name}: chưa có file")
        return

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    to_verify = 0
    for i, row in enumerate(rows, start=2):
        loc = f"{path.name}:{i} [{row.get('drug_name')}]"
        if row.get("timing_rule") not in {"before", "with", "after", "avoid_with"}:
            err(f"{loc} timing_rule không hợp lệ")
        if not (row.get("source_ref") or "").strip():
            err(f"{loc} thiếu source_ref (RULE-2)")
        if (row.get("verify_status") or "to_verify") == "to_verify":
            to_verify += 1

    print(f"  {path.name}: {len(rows)} quy tắc giờ dùng thuốc")
    if to_verify:
        warn(f"{path.name}: {to_verify} quy tắc ở trạng thái 'to_verify' — R2 cần đối chiếu trước Demo Day (DAT-19)")


def check_gi_values(path: Path) -> None:
    """Bảng GI tách riêng (DAT-07). GI có nguồn riêng, merge vào food_items khi nạp."""
    if not path.exists():
        warn(f"{path.name}: chưa có file")
        return

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    seen: set[str] = set()
    for i, row in enumerate(rows, start=2):
        loc = f"{path.name}:{i} [{row.get('name_vi') or '?'}]"
        fid = (row.get("food_id") or "").strip()
        if not fid.isdigit():
            err(f"{loc} food_id='{fid}' phải là số nguyên")
        if fid in seen:
            err(f"{loc} trùng food_id={fid} — mỗi thực phẩm chỉ một trị GI")
        seen.add(fid)

        gi_raw = (row.get("gi_index") or "").strip()
        try:
            gi = float(gi_raw)
            if not (0 <= gi <= 110):
                err(f"{loc} gi_index={gi} ngoài khoảng [0, 110]")
        except ValueError:
            err(f"{loc} gi_index không phải số: '{gi_raw}'")

        if (row.get("gi_source") or "").strip() not in VALID_GI_SOURCES:
            err(f"{loc} gi_source không hợp lệ (phải là {sorted(VALID_GI_SOURCES)}) — RULE-2")
        if (row.get("gi_source_ref") or "").strip().lower() in PLACEHOLDER:
            err(f"{loc} thiếu gi_source_ref — mỗi trị GI phải dẫn được nguồn (RULE-2)")

    print(f"  {path.name}: {len(rows)} trị GI")


def check_purine_values(path: Path) -> None:
    """Bảng purine tách riêng (nguồn USDA/ODS-NIH, khác NIN). Merge vào food_items khi nạp."""
    if not path.exists():
        warn(f"{path.name}: chưa có file")
        return
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    seen: set[str] = set()
    for i, row in enumerate(rows, start=2):
        loc = f"{path.name}:{i} [{row.get('name_vi') or '?'}]"
        fid = (row.get("food_id") or "").strip()
        if not fid.isdigit():
            err(f"{loc} food_id='{fid}' phải là số nguyên")
        if fid in seen:
            err(f"{loc} trùng food_id={fid}")
        seen.add(fid)
        try:
            val = float((row.get("purine_mg") or "").strip())
            if not (0 <= val <= 1000):
                err(f"{loc} purine_mg={val} ngoài khoảng [0, 1000]")
        except ValueError:
            err(f"{loc} purine_mg không phải số")
        if (row.get("purine_source_ref") or "").strip().lower() in PLACEHOLDER:
            err(f"{loc} thiếu purine_source_ref — mỗi trị purine phải dẫn nguồn (RULE-2)")
    print(f"  {path.name}: {len(rows)} trị purine")


def check_usda_values(path: Path) -> None:
    """Bảng USDA FDC tách riêng (nguồn USDA, lấp món NIN thiếu). Merge vào food_items."""
    if not path.exists():
        warn(f"{path.name}: chưa có file")
        return
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for i, row in enumerate(rows, start=2):
        loc = f"{path.name}:{i} [{row.get('name_vi') or '?'}]"
        if not (row.get("food_id") or "").strip().isdigit():
            err(f"{loc} food_id phải là số nguyên")
        if "fdcid" not in (row.get("source_ref") or "").lower():
            err(f"{loc} source_ref phải dẫn fdcId USDA (RULE-2)")
        for col in ("kcal_100g", "na_mg", "k_mg", "p_mg"):
            if not (row.get(col) or "").strip():
                err(f"{loc} thiếu {col}")
    print(f"  {path.name}: {len(rows)} món USDA")


def check_dishes(path: Path) -> None:
    """Món ăn (DAT-23). Trước đây validator KHÔNG đụng tới file này dòng nào —
    đúng chỗ nợ `MENU-*` / `FNDDS-*` / `pending` đang nằm.

    `dishes.csv` là dữ liệu chạm tới bệnh nhân: tên món hiện thẳng lên UI. Mọi
    dòng không phải món Việt thật (mẫu bữa Excel `MENU-*`, khối khảo sát Mỹ
    `FNDDS-*`) phải nằm ở `data/reference/` hoặc `data/quarantine/`, không phải
    ở đây.
    """
    if not path.exists():
        warn(f"{path.name}: chưa có file")
        return

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    seen: set[str] = set()
    pending = 0
    for i, row in enumerate(rows, start=2):
        dish_id = (row.get("dish_id") or "").strip()
        loc = f"{path.name}:{i} [{dish_id or '?'}]"

        if not dish_id:
            err(f"{loc} thiếu dish_id")
        elif dish_id in seen:
            err(f"{loc} trùng dish_id — mỗi món chỉ một dòng")
        seen.add(dish_id)

        if dish_id.startswith(NON_PATIENT_DISH_PREFIXES):
            err(
                f"{loc} không phải món ăn cho bệnh nhân — MENU-* là mẫu bữa, "
                f"FNDDS-* là khối khảo sát Mỹ. Chuyển sang data/reference/ "
                f"hoặc data/quarantine/ (DAT-23)"
            )

        if not (row.get("name_vi") or "").strip():
            err(f"{loc} thiếu name_vi — tên món hiện thẳng lên UI bệnh nhân")

        serving_raw = (row.get("serving_g") or "").strip()
        if serving_raw:
            try:
                if float(serving_raw) <= 0:
                    err(f"{loc} serving_g={serving_raw} phải > 0")
            except ValueError:
                err(f"{loc} serving_g không phải số: '{serving_raw}'")
        else:
            warn(f"{loc} chưa có serving_g")

        if (row.get("verified_by") or "").strip().lower() in {"", "pending"}:
            pending += 1

    if pending:
        warn(f"{path.name}: {pending}/{len(rows)} món chưa được R2 rà công thức (verified_by=pending)")
    print(f"  {path.name}: {len(rows)} món")


def check_dish_ingredients(path: Path, dishes_path: Path, foods_path: Path) -> None:
    """Nguyên liệu của món (DAT-23) — kiểm tra toàn vẹn tham chiếu.

    Thiếu DÒNG nguyên liệu không bị RULE-2 bắt được (khác thiếu GIÁ TRỊ trên
    dòng đã có): món vẫn "tính được" nhưng mật độ dinh dưỡng bị pha loãng sai.
    Đây chính là cơ chế đã gây bug thực đơn thiếu năng lượng (DEVLOG 2026-08-07),
    nên kiểm ở đây thay vì phát hiện muộn lúc chạy.
    """
    if not path.exists():
        warn(f"{path.name}: chưa có file")
        return

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    known_dishes: set[str] = set()
    if dishes_path.exists():
        with open(dishes_path, newline="", encoding="utf-8") as f:
            known_dishes = {(r.get("dish_id") or "").strip() for r in csv.DictReader(f)}

    known_foods: set[str] = set()
    if foods_path.exists():
        with open(foods_path, newline="", encoding="utf-8") as f:
            known_foods = {(r.get("id") or "").strip() for r in csv.DictReader(f)}

    dishes_with_items: set[str] = set()
    for i, row in enumerate(rows, start=2):
        dish_id = (row.get("dish_id") or "").strip()
        food_id = (row.get("food_id") or "").strip()
        loc = f"{path.name}:{i} [{dish_id or '?'}]"
        dishes_with_items.add(dish_id)

        if known_dishes and dish_id not in known_dishes:
            err(f"{loc} dish_id không tồn tại trong {dishes_path.name}")
        if not food_id.isdigit():
            err(f"{loc} food_id='{food_id}' phải là số nguyên")
        elif known_foods and food_id not in known_foods:
            err(f"{loc} food_id={food_id} không tồn tại trong {foods_path.name}")

        grams_raw = (row.get("grams") or "").strip()
        try:
            if float(grams_raw) <= 0:
                err(f"{loc} grams={grams_raw} phải > 0")
        except ValueError:
            err(f"{loc} grams không phải số: '{grams_raw}'")

    orphans = sorted(known_dishes - dishes_with_items - {""})
    if orphans:
        err(
            f"{dishes_path.name}: {len(orphans)} món không có nguyên liệu nào — "
            f"không tính được dinh dưỡng (RULE-1): {orphans[:5]}"
        )
    print(f"  {path.name}: {len(rows)} dòng nguyên liệu cho {len(dishes_with_items)} món")


def main() -> int:
    print("Kiểm tra dữ liệu seed...")
    check_food_items(SEEDS / "food_items.csv")
    check_food_items(QUARANTINE / "food_items.template.csv")
    check_dishes(SEEDS / "dishes.csv")
    check_dish_ingredients(
        SEEDS / "dish_ingredients.csv",
        SEEDS / "dishes.csv",
        SEEDS / "food_items.csv",
    )
    check_clinical_rules(SEEDS / "clinical_rules.csv")
    check_drug_food(SEEDS / "drug_food_interactions.csv")
    check_food_food_interactions(SEEDS / "food_food_interactions.csv")
    check_drug_meal_timing(SEEDS / "drug_meal_timing.csv")
    check_gi_values(SEEDS / "gi_values.csv")
    check_purine_values(SEEDS / "purine_values.csv")
    check_usda_values(SEEDS / "usda_values.csv")

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
