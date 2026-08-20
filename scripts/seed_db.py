#!/usr/bin/env python3
"""Nạp dữ liệu từ `data/seeds/*.csv` vào DB thật qua SQLAlchemy.

Ticket: BE-10 (tách từ BE-01). LLM: NO — thuần ETL, không có logic lâm sàng.
Chạy: python scripts/seed_db.py   (hoặc `make seed`)

Idempotent: dùng `session.merge()` theo khoá chính của từng bảng (id/dish_id/
rule_id...) — chạy lại nhiều lần không tạo dòng trùng, chỉ cập nhật giá trị
mới nhất từ CSV. Riêng `serving_sizes` không có khoá tự nhiên trong CSV nên
seed theo kiểu xoá-hết-rồi-nạp-lại (nội dung giống hệt sau mỗi lần chạy).

KHÔNG seed từ `gi_values.csv` / `purine_values.csv` / `usda_values.csv` —
đây là bảng phụ trợ dùng để MERGE số liệu vào `food_items.csv` lúc biên tập
dữ liệu (xem `data/README.md`), không phải bảng DB độc lập trong
`src/db/models.py`.

Dòng `food_items.csv` chưa nhập số liệu (còn trống `kcal_100g`) bị bỏ qua có
chủ đích — không seed dữ liệu rỗng/rác vào DB (RULE-2).
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

# CI runner có thể không đặt locale UTF-8 → in tiếng Việt sẽ UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # cho phép chạy trực tiếp `python scripts/seed_db.py`

from sqlalchemy.orm import Session  # noqa: E402

from src.db.base import get_engine  # noqa: E402
from src.db.models import (  # noqa: E402
    Base,
    ClinicalRule,
    Dish,
    DishIngredient,
    DrugFoodInteraction,
    DrugMealTiming,
    FoodFoodInteraction,
    FoodItem,
    ServingSize,
)

SEEDS = Path(__file__).resolve().parents[1] / "data" / "seeds"


def _split(raw: str | None) -> list[str]:
    return [s.strip() for s in (raw or "").split("|") if s.strip()]


def _opt_float(raw: str | None) -> float | None:
    raw = (raw or "").strip()
    return float(raw) if raw else None


def _opt_str(raw: str | None) -> str | None:
    raw = (raw or "").strip()
    return raw or None


def seed_food_items(session: Session, path: Path | None = None, commit_every: int = 500) -> int:
    """`commit_every`: commit theo lô để tránh 1 transaction quá dài bị
    connection pooler (VD Supabase Session Pooler) đóng kết nối giữa chừng
    trên bảng lớn (~7000+ dòng). merge() theo khoá chính nên idempotent,
    commit dở dang không gây trùng lặp khi chạy lại."""
    n = 0
    with open(path or SEEDS / "food_items.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not (row.get("kcal_100g") or "").strip():
                continue
            session.merge(
                FoodItem(
                    id=int(row["id"]),
                    name_vi=row["name_vi"],
                    aliases=_split(row.get("aliases")),
                    category=_opt_str(row.get("category")),
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
                    gi_source=_opt_str(row.get("gi_source")),
                    gi_source_ref=_opt_str(row.get("gi_source_ref")),
                    contains_allergens=_split(row.get("contains_allergens")),
                    source=row["source"],
                    source_ref=row["source_ref"],
                    is_estimated=(row.get("is_estimated") or "").strip().upper() == "TRUE",
                )
            )
            n += 1
            if commit_every and n % commit_every == 0:
                session.commit()
    session.flush()
    return n


def seed_dishes(session: Session, path: Path | None = None) -> int:
    n = 0
    with open(path or SEEDS / "dishes.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            session.merge(
                Dish(
                    dish_id=row["dish_id"],
                    name_vi=row["name_vi"],
                    region=_opt_str(row.get("region")),
                    origin=_opt_str(row.get("origin")),
                    roles=_opt_str(row.get("roles")),
                    serving_g=_opt_float(row.get("serving_g")),
                    verified_by=_opt_str(row.get("verified_by")),
                    note=_opt_str(row.get("note")),
                )
            )
            n += 1
    session.flush()
    return n


def seed_dish_ingredients(session: Session, path: Path | None = None) -> tuple[int, int]:
    """Trả về (số dòng đã nạp, số dòng bỏ qua vì food_id/dish_id chưa tồn tại)."""
    known_food_ids = {fid for (fid,) in session.query(FoodItem.id).all()}
    known_dish_ids = {did for (did,) in session.query(Dish.dish_id).all()}
    n, skipped = 0, 0
    with open(path or SEEDS / "dish_ingredients.csv", newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=1):
            dish_id, food_id = row["dish_id"], int(row["food_id"])
            if dish_id not in known_dish_ids or food_id not in known_food_ids:
                print(
                    f"  BỎ QUA dish_ingredients dòng {i}: {dish_id} × food_id={food_id} "
                    "— dish hoặc food_item chưa tồn tại/chưa có số liệu"
                )
                skipped += 1
                continue
            # Một số món ở lô crawl VCB có 2 dòng nguyên liệu trùng dish_id+food_id với gram
            # khác nhau (lỗi trích xuất công thức gốc, chưa được R2 rà) — .one_or_none() sẽ
            # crash toàn bộ seed vì việc này. Lấy dòng đầu (id nhỏ nhất) để không chặn seed,
            # nhưng cảnh báo rõ để không âm thầm bỏ qua mâu thuẫn dữ liệu.
            matches = session.query(DishIngredient).filter_by(dish_id=dish_id, food_id=food_id).order_by(DishIngredient.id).all()
            if len(matches) > 1:
                print(f"  CẢNH BÁO dish_ingredients: {dish_id} × food_id={food_id} có {len(matches)} dòng trùng trong DB — cần R2 rà công thức gốc")
            existing = matches[0] if matches else None
            if existing is not None:
                existing.grams = float(row["grams"])
                existing.note = _opt_str(row.get("note"))
            else:
                session.add(
                    DishIngredient(
                        dish_id=dish_id,
                        food_id=food_id,
                        grams=float(row["grams"]),
                        note=_opt_str(row.get("note")),
                    )
                )
            n += 1
    session.flush()
    return n, skipped


def seed_clinical_rules(session: Session, path: Path | None = None) -> int:
    n = 0
    with open(path or SEEDS / "clinical_rules.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("rule_id"):
                continue
            session.merge(
                ClinicalRule(
                    rule_id=row["rule_id"],
                    condition_code=row["condition_code"],
                    stages=_opt_str(row.get("stages")),
                    nutrient=row["nutrient"],
                    bound=row["bound"],
                    value=float(row["value"]),
                    unit=row["unit"],
                    basis=row["basis"],
                    severity=row["severity"],
                    guideline_ref=row["guideline_ref"],
                    guideline_grade=_opt_str(row.get("guideline_grade")),
                    verify_status=_opt_str(row.get("verify_status")) or "to_verify",
                    overridden_by=_opt_str(row.get("overridden_by")),
                    disabled_by_flag=_opt_str(row.get("disabled_by_flag")),
                    requires_flag=_opt_str(row.get("requires_flag")),
                )
            )
            n += 1
    session.flush()
    return n


def seed_drug_food_interactions(session: Session, path: Path | None = None) -> int:
    n = 0
    with open(path or SEEDS / "drug_food_interactions.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            session.merge(
                DrugFoodInteraction(
                    id=int(row["id"]),
                    drug_name=row["drug_name"],
                    drug_class=_opt_str(row.get("drug_class")),
                    food_or_nutrient=row["food_or_nutrient"],
                    severity=row["severity"],
                    mechanism_vi=row["mechanism_vi"],
                    recommendation_vi=row["recommendation_vi"],
                    source_ref=_opt_str(row.get("source_ref")),
                    verify_status=_opt_str(row.get("verify_status")) or "to_verify",
                )
            )
            n += 1
    session.flush()
    return n


def seed_food_food_interactions(session: Session, path: Path | None = None) -> int:
    n = 0
    with open(path or SEEDS / "food_food_interactions.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            session.merge(
                FoodFoodInteraction(
                    id=int(row["id"]),
                    substance_a=row["substance_a"],
                    substance_b=row["substance_b"],
                    food_examples_vi=row["food_examples_vi"],
                    mechanism_vi=row["mechanism_vi"],
                    direction=row["direction"],
                    effect_size_vi=_opt_str(row.get("effect_size_vi")),
                    clinical_significance=row["clinical_significance"],
                    applies_to_condition=_opt_str(row.get("applies_to_condition")),
                    recommendation_vi=row["recommendation_vi"],
                    source_ref=row["source_ref"],
                    pmid=_opt_str(row.get("pmid")),
                    verify_status=_opt_str(row.get("verify_status")) or "to_verify",
                )
            )
            n += 1
    session.flush()
    return n


def seed_drug_meal_timing(session: Session, path: Path | None = None) -> int:
    n = 0
    with open(path or SEEDS / "drug_meal_timing.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            offset_raw = (row.get("offset_minutes") or "").strip()
            session.merge(
                DrugMealTiming(
                    id=int(row["id"]),
                    drug_name=row["drug_name"],
                    drug_class=_opt_str(row.get("drug_class")),
                    timing_rule=row["timing_rule"],
                    offset_minutes=int(offset_raw) if offset_raw else None,
                    relative_to=row["relative_to"],
                    rationale_pk_vi=row["rationale_pk_vi"],
                    condition=_opt_str(row.get("condition")),
                    source_ref=row["source_ref"],
                    page_ref=_opt_str(row.get("page_ref")),
                    verify_status=_opt_str(row.get("verify_status")) or "to_verify",
                )
            )
            n += 1
    session.flush()
    return n


def seed_serving_sizes(session: Session, path: Path | None = None, preserve: bool = False) -> int:
    """Không có khoá tự nhiên trong CSV — xoá hết rồi nạp lại cho idempotent."""
    if not preserve:
        session.query(ServingSize).delete()
    n = 0
    with open(path or SEEDS / "serving_sizes.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            values = {
                "category": row["category"],
                "serving_g": float(row["serving_g"]),
                "note": _opt_str(row.get("note")),
                "source": _opt_str(row.get("source")),
            }
            existing = (
                session.query(ServingSize)
                .filter_by(category=values["category"], serving_g=values["serving_g"])
                .one_or_none()
            )
            if existing is None:
                session.add(ServingSize(**values))
            n += 1
    session.flush()
    return n


def seed_all(session: Session, preserve: bool = False) -> dict[str, int]:
    counts = {"food_items": seed_food_items(session)}
    counts["dishes"] = seed_dishes(session)
    counts["dish_ingredients"], skipped = seed_dish_ingredients(session)
    counts["dish_ingredients_skipped"] = skipped
    counts["clinical_rules"] = seed_clinical_rules(session)
    counts["drug_food_interactions"] = seed_drug_food_interactions(session)
    counts["food_food_interactions"] = seed_food_food_interactions(session)
    counts["drug_meal_timing"] = seed_drug_meal_timing(session)
    counts["serving_sizes"] = seed_serving_sizes(session, preserve=preserve)
    return counts


def main() -> int:
    """Nạp dữ liệu, commit sau MỖI bảng (không phải 1 transaction khổng lồ).

    Với Postgres qua connection pooler (VD Supabase Session Pooler), một
    transaction dài ~7000+ dòng dễ bị pooler đóng kết nối giữa chừng
    (`server closed the connection unexpectedly`) trước khi kịp commit,
    làm mất toàn bộ tiến trình. Commit theo từng bảng giới hạn thiệt hại
    khi rớt kết nối giữa chừng — vì mọi seed_* đều idempotent (merge() theo
    khoá chính), chạy lại kịch bản này nhiều lần là an toàn.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)  # no-op nếu bảng đã tồn tại (đã chạy alembic)
    counts: dict[str, int] = {}
    with Session(engine) as session:
        counts["food_items"] = seed_food_items(session)
        session.commit()
        counts["dishes"] = seed_dishes(session)
        session.commit()
        counts["dish_ingredients"], counts["dish_ingredients_skipped"] = seed_dish_ingredients(session)
        session.commit()
        counts["clinical_rules"] = seed_clinical_rules(session)
        session.commit()
        counts["drug_food_interactions"] = seed_drug_food_interactions(session)
        session.commit()
        counts["food_food_interactions"] = seed_food_food_interactions(session)
        session.commit()
        counts["drug_meal_timing"] = seed_drug_meal_timing(session)
        session.commit()
        counts["serving_sizes"] = seed_serving_sizes(session, preserve=os.getenv("PRESERVE_DATA", "0") == "1")
        session.commit()

    print("Đã nạp dữ liệu vào DB:")
    for table, n in counts.items():
        print(f"  {table}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
