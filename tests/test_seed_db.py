"""Test scripts/seed_db.py — BE-10. LLM: NO.

Chạy trên SQLite tạm trong bộ nhớ, không đụng DB thật. Trọng tâm: nạp đúng số
dòng thật từ `data/seeds/*.csv`, không lỗi FK, và idempotent (chạy 2 lần
không tăng gấp đôi).
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from scripts.seed_db import seed_all
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


def test_seed_nap_dung_du_lieu_that():
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


def test_seed_khong_loi_fk_dish_ingredients():
    engine = _engine()
    with Session(engine) as session:
        seed_all(session)
        session.commit()

        for ing in session.query(DishIngredient).all():
            assert session.get(FoodItem, ing.food_id) is not None
            assert session.get(Dish, ing.dish_id) is not None


def test_seed_idempotent_chay_lai_khong_tang_gap_doi():
    engine = _engine()
    with Session(engine) as session:
        first = seed_all(session)
        session.commit()

        second = seed_all(session)
        session.commit()

        assert second["food_items"] == first["food_items"]
        assert session.query(FoodItem).count() == first["food_items"]
        assert session.query(Dish).count() == first["dishes"]
        assert session.query(ClinicalRule).count() == first["clinical_rules"]
        assert session.query(DrugFoodInteraction).count() == first["drug_food_interactions"]
        assert session.query(ServingSize).count() == first["serving_sizes"]


def test_seed_bo_qua_dish_ingredient_thieu_food_item(tmp_path):
    """Dish_ingredient trỏ tới food_id chưa có số liệu phải bị bỏ qua, không crash."""
    food_csv = tmp_path / "food_items.csv"
    food_csv.write_text(
        "id,name_vi,aliases,category,kcal_100g,protein_g,carb_g,fat_g,fiber_g,sugar_g,na_mg,k_mg,p_mg,"
        "purine_mg,purine_source_ref,gi_index,gi_source,gi_source_ref,contains_allergens,source,source_ref,"
        "is_estimated\n"
        "1,Gạo tẻ,,ngũ cốc,347,8.1,75.7,1.3,0.7,,5,202,108,,,,,,,NIN,NIN mã 1003,FALSE\n"
        "2,Món chưa có số liệu,,ngũ cốc,,,,,,,,,,,,,,,,,,FALSE\n",
        encoding="utf-8",
    )
    dish_csv = tmp_path / "dishes.csv"
    dish_csv.write_text(
        "dish_id,name_vi,region,serving_g,verified_by,note\nD1,Món test,any,100,pending,\n",
        encoding="utf-8",
    )
    ing_csv = tmp_path / "dish_ingredients.csv"
    ing_csv.write_text(
        "dish_id,food_id,grams,note\nD1,1,100,\nD1,2,50,thiếu số liệu\n",
        encoding="utf-8",
    )

    from scripts.seed_db import seed_dish_ingredients, seed_dishes, seed_food_items

    engine = _engine()
    with Session(engine) as session:
        seed_food_items(session, path=food_csv)
        seed_dishes(session, path=dish_csv)
        n, skipped = seed_dish_ingredients(session, path=ing_csv)
        session.commit()

        assert n == 1
        assert skipped == 1
