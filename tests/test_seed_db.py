"""Test scripts/seed_db.py — BE-10. LLM: NO.

Chạy trên SQLite tạm trong bộ nhớ, không đụng DB thật. Kiểm tra LOGIC merge/
idempotent/FK bằng dữ liệu tổng hợp nhỏ (nhanh) — không cần nạp toàn bộ CSV
thật (~10.000 dòng) để xác nhận cùng 1 hành vi. `test_seed_nap_dung_du_lieu_that`
là smoke test riêng trên dữ liệu THẬT, đánh dấu `slow` (xem `pyproject.toml`).
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from scripts.seed_db import (
    seed_all,
    seed_clinical_rules,
    seed_dish_ingredients,
    seed_dishes,
    seed_drug_food_interactions,
    seed_food_items,
    seed_serving_sizes,
)
from src.db.models import (
    Base,
    ClinicalRule,
    Dish,
    DishIngredient,
    DrugFoodInteraction,
    FoodItem,
    ServingSize,
)


def _engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


_FOOD_HEADER = (
    "id,name_vi,aliases,category,kcal_100g,protein_g,carb_g,fat_g,fiber_g,sugar_g,na_mg,k_mg,p_mg,"
    "purine_mg,purine_source_ref,gi_index,gi_source,gi_source_ref,contains_allergens,source,source_ref,"
    "is_estimated\n"
)


def _write_small_seed_set(tmp_path):
    """1 food_item đủ số liệu + 1 chưa nhập, 1 dish với 1 ingredient hợp lệ + 1
    ingredient trỏ tới food_id thiếu số liệu (đúng tình huống thật `dish_ingredients`
    phải bỏ qua) — đủ để kiểm merge/idempotent/FK mà không cần data thật."""
    (tmp_path / "food_items.csv").write_text(
        _FOOD_HEADER
        + "1,Gạo tẻ,,ngũ cốc,347,8.1,75.7,1.3,0.7,,5,202,108,,,,,,,NIN,NIN mã 1003,FALSE\n"
        + "2,Món chưa có số liệu,,ngũ cốc,,,,,,,,,,,,,,,,,,FALSE\n",
        encoding="utf-8",
    )
    (tmp_path / "dishes.csv").write_text(
        "dish_id,name_vi,region,serving_g,verified_by,note\nD1,Món test,any,100,pending,\n",
        encoding="utf-8",
    )
    (tmp_path / "dish_ingredients.csv").write_text(
        "dish_id,food_id,grams,note\nD1,1,100,\nD1,2,50,thiếu số liệu\n",
        encoding="utf-8",
    )
    (tmp_path / "clinical_rules.csv").write_text(
        "rule_id,condition_code,stages,nutrient,bound,value,unit,basis,severity,guideline_ref,"
        "guideline_grade,verify_status,overridden_by,disabled_by_flag,requires_flag\n"
        "R1,T2DM,,na_mg,max,2000,mg,absolute,hard,Test guideline,,to_verify,,,\n",
        encoding="utf-8",
    )
    (tmp_path / "drug_food_interactions.csv").write_text(
        "id,drug_name,drug_class,food_or_nutrient,severity,mechanism_vi,recommendation_vi,source_ref,"
        "verify_status\n1,Test Drug,test class,kali,high,test,test,Test source,to_verify\n",
        encoding="utf-8",
    )
    (tmp_path / "serving_sizes.csv").write_text(
        "category,serving_g,note,source\nbát phở,500,,test\n",
        encoding="utf-8",
    )


def _seed_all_from(session: Session, tmp_path) -> dict[str, int]:
    counts = {"food_items": seed_food_items(session, path=tmp_path / "food_items.csv")}
    counts["dishes"] = seed_dishes(session, path=tmp_path / "dishes.csv")
    counts["dish_ingredients"], counts["dish_ingredients_skipped"] = seed_dish_ingredients(
        session, path=tmp_path / "dish_ingredients.csv"
    )
    counts["clinical_rules"] = seed_clinical_rules(session, path=tmp_path / "clinical_rules.csv")
    counts["drug_food_interactions"] = seed_drug_food_interactions(
        session, path=tmp_path / "drug_food_interactions.csv"
    )
    counts["serving_sizes"] = seed_serving_sizes(session, path=tmp_path / "serving_sizes.csv")
    return counts


@pytest.mark.slow
def test_seed_nap_dung_du_lieu_that():
    """Smoke test trên `data/seeds/*.csv` THẬT — đắt (~6s, đọc ~10.000 dòng),
    chạy trong `make check`/CI đầy đủ nhưng bỏ qua ở vòng lặp nhanh (`pytest -m
    "not slow"`)."""
    engine = _engine()
    with Session(engine) as session:
        counts = seed_all(session)
        session.commit()

        assert counts["food_items"] > 100  # chỉ nạp dòng đã có số liệu, không nạp dòng trống
        assert counts["dishes"] == session.query(Dish).count()
        assert counts["clinical_rules"] == session.query(ClinicalRule).count()
        assert counts["drug_food_interactions"] == session.query(DrugFoodInteraction).count()
        assert counts["serving_sizes"] == session.query(ServingSize).count()
        assert counts["food_items"] == session.query(FoodItem).count()


def test_seed_khong_loi_fk_dish_ingredients(tmp_path):
    _write_small_seed_set(tmp_path)
    engine = _engine()
    with Session(engine) as session:
        _seed_all_from(session, tmp_path)
        session.commit()

        for ing in session.query(DishIngredient).all():
            assert session.get(FoodItem, ing.food_id) is not None
            assert session.get(Dish, ing.dish_id) is not None


def test_seed_idempotent_chay_lai_khong_tang_gap_doi(tmp_path):
    _write_small_seed_set(tmp_path)
    engine = _engine()
    with Session(engine) as session:
        first = _seed_all_from(session, tmp_path)
        session.commit()

        second = _seed_all_from(session, tmp_path)
        session.commit()

        assert second["food_items"] == first["food_items"]
        assert session.query(FoodItem).count() == first["food_items"]
        assert session.query(Dish).count() == first["dishes"]
        assert session.query(ClinicalRule).count() == first["clinical_rules"]
        assert session.query(DrugFoodInteraction).count() == first["drug_food_interactions"]
        assert session.query(ServingSize).count() == first["serving_sizes"]


def test_seed_bo_qua_dish_ingredient_thieu_food_item(tmp_path):
    """Dish_ingredient trỏ tới food_id chưa có số liệu phải bị bỏ qua, không crash."""
    _write_small_seed_set(tmp_path)
    engine = _engine()
    with Session(engine) as session:
        seed_food_items(session, path=tmp_path / "food_items.csv")
        seed_dishes(session, path=tmp_path / "dishes.csv")
        n, skipped = seed_dish_ingredients(session, path=tmp_path / "dish_ingredients.csv")
        session.commit()

        assert n == 1
        assert skipped == 1
