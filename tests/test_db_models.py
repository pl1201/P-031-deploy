"""Test schema DB thật — BE-01. LLM: NO.

Trọng tâm: models import sạch, tạo được đủ bảng trên SQLite trắng (không cần
Postgres thật để chạy CI), và insert/round-trip được record cơ bản qua vài
bảng đại diện — chứng minh model không chỉ "import được" mà còn dùng được.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.models import (
    Base,
    ClinicalRule,
    Dish,
    DishIngredient,
    DrugFoodInteraction,
    FoodItem,
    PatientProfile,
    User,
)


def _engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_tao_du_19_bang():
    """15 bảng BE-01 + food_food_interactions + drug_meal_timing (DAT-18/19)
    + pantry_items + substitution_scopes (P2/AGT-12) — tối thiểu 19 bảng.

    `>=` chứ không `==`: bảng mới được thêm liên tục (clinical_notes,
    patient_observations, meal_plan_review_events...); một assert số chính
    xác sẽ vỡ mà không chỉ ra lỗi thật, giống cách `test_nap_du_30_cap_tu_seed`
    (tests/test_interactions.py) đã xử lý cho drug_food_interactions.csv."""
    assert len(Base.metadata.tables) >= 19


def test_tao_bang_tren_sqlite_trang():
    engine = _engine()
    with engine.connect() as conn:
        names = {row[0] for row in conn.exec_driver_sql("select name from sqlite_master where type='table'")}
    for expected in ("users", "food_items", "dishes", "clinical_rules", "drug_food_interactions"):
        assert expected in names


def test_insert_va_doc_lai_food_item():
    engine = _engine()
    with Session(engine) as session:
        food = FoodItem(
            id=1,
            name_vi="Cơm tẻ",
            kcal_100g=130.0,
            protein_g=2.7,
            carb_g=28.2,
            fat_g=0.3,
            fiber_g=0.4,
            na_mg=1.0,
            k_mg=35.0,
            p_mg=43.0,
            source="NIN",
            source_ref="Bảng TPTP VN 2017, mã 01001",
        )
        session.add(food)
        session.commit()

        loaded = session.get(FoodItem, 1)
        assert loaded is not None
        assert loaded.name_vi == "Cơm tẻ"
        assert loaded.source_ref == "Bảng TPTP VN 2017, mã 01001"


def test_dish_ingredient_lien_ket_dung_food_item():
    """RULE-1: dish_ingredients chỉ lưu food_id + gram, không lưu dinh dưỡng."""
    engine = _engine()
    with Session(engine) as session:
        session.add(
            FoodItem(
                id=1,
                name_vi="Bún tươi",
                kcal_100g=110.0,
                protein_g=1.7,
                carb_g=25.0,
                fat_g=0.2,
                fiber_g=0.5,
                na_mg=5.0,
                k_mg=20.0,
                p_mg=15.0,
                source="NIN",
                source_ref="Bảng TPTP VN 2017, mã 01010",
            )
        )
        session.add(Dish(dish_id="pho-bo", name_vi="Phở bò", serving_g=500.0, verified_by="R2"))
        session.commit()

        session.add(DishIngredient(dish_id="pho-bo", food_id=1, grams=150.0))
        session.commit()

        dish = session.get(Dish, "pho-bo")
        assert dish is not None
        assert len(dish.ingredients) == 1
        assert dish.ingredients[0].grams == 150.0
        # Không có cột nào trên DishIngredient lưu kcal/Na — phải join sang FoodItem.
        assert not hasattr(DishIngredient, "kcal_100g")


def test_clinical_rule_va_drug_food_interaction_co_the_insert():
    engine = _engine()
    with Session(engine) as session:
        session.add(
            ClinicalRule(
                rule_id="BASE-NA-01",
                condition_code="BASE",
                nutrient="na_mg",
                bound="max",
                value=2000,
                unit="mg",
                basis="absolute",
                severity="soft",
                guideline_ref="WHO 2012",
            )
        )
        session.add(
            DrugFoodInteraction(
                drug_name="Warfarin",
                food_or_nutrient="vitamin K",
                severity="high",
                mechanism_vi="Đối kháng tác dụng chống đông",
                recommendation_vi="Giữ lượng ổn định",
                source_ref="Dược thư Quốc gia Việt Nam 2022, chuyên luận Warfarin",
            )
        )
        session.commit()

        rule = session.get(ClinicalRule, "BASE-NA-01")
        assert rule is not None
        assert rule.severity == "soft"


def test_patient_profile_gan_voi_user():
    engine = _engine()
    with Session(engine) as session:
        user = User(email="bn-demo-01@example.com", password_hash="x", role="patient")
        session.add(user)
        session.commit()

        profile = PatientProfile(
            user_id=user.id,
            age=58,
            sex="male",
            height_cm=165,
            weight_kg=70,
            conditions=[{"code": "T2DM", "stage": None}],
        )
        session.add(profile)
        session.commit()

        assert user.profile is not None
        assert user.profile.age == 58
