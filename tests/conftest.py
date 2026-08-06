"""Fixtures dùng chung cho test.

⚠️ TOÀN BỘ số liệu dinh dưỡng trong file này là DỮ LIỆU GIẢ dùng để test logic.
KHÔNG dùng cho mục đích lâm sàng và KHÔNG được copy sang data/seeds/.
Dữ liệu thật phải đến từ NIN hoặc USDA kèm source_ref có thật (ticket DAT-02).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.clinical.models import (
    ActivityLevel,
    Condition,
    ConditionCode,
    FoodItem,
    MealSlot,
    MenuDraft,
    MenuItem,
    PatientProfile,
    Sex,
)
from src.clinical.nutrition import InMemoryFoodRepository

FIXTURE_REF = "TEST-FIXTURE (dữ liệu giả, không dùng lâm sàng)"


def _food(fid, name, kcal, pro, carb, fat, fib, na, k, p, purine, allergens=(), aliases=()):
    return FoodItem(
        id=fid,
        name_vi=name,
        aliases=list(aliases),
        kcal_100g=kcal,
        protein_g=pro,
        carb_g=carb,
        fat_g=fat,
        fiber_g=fib,
        na_mg=na,
        k_mg=k,
        p_mg=p,
        purine_mg=purine,
        contains_allergens=list(allergens),
        source="curated",
        source_ref=FIXTURE_REF,
    )


@pytest.fixture
def foods() -> InMemoryFoodRepository:
    return InMemoryFoodRepository(
        [
            _food(1, "Cơm tẻ", 130, 2.7, 28.0, 0.3, 0.4, 1, 35, 43, 15),
            _food(2, "Thịt lợn nạc", 143, 19.0, 0.0, 7.0, 0.0, 55, 340, 190, 145),
            _food(3, "Rau muống luộc", 23, 2.6, 2.5, 0.2, 1.0, 25, 320, 40, 30),
            _food(4, "Nước mắm", 35, 5.0, 3.6, 0.0, 0.0, 7800, 250, 40, 60),
            _food(5, "Cá lóc", 97, 18.2, 0.0, 2.7, 0.0, 60, 300, 200, 110, aliases=["cá quả"]),
            _food(6, "Đậu phụ", 95, 10.9, 0.7, 5.4, 0.4, 8, 120, 130, 68, allergens=["đậu nành"]),
            _food(7, "Dầu ăn", 900, 0.0, 0.0, 100.0, 0.0, 0, 0, 0, 0),
            _food(8, "Chuối tiêu", 88, 1.5, 22.2, 0.2, 0.8, 1, 329, 28, 20),
            _food(9, "Tôm biển", 82, 17.6, 0.9, 0.9, 0.0, 418, 185, 200, 235, allergens=["hải sản"]),
        ]
    )


@pytest.fixture
def profile_t2dm_ckd() -> PatientProfile:
    """Nam 58 tuổi, ĐTĐ týp 2 + CKD G3b — ca đa bệnh lý điển hình."""
    return PatientProfile(
        patient_id="BN-DEMO-01",
        age=58,
        sex=Sex.MALE,
        height_cm=165,
        weight_kg=65,
        activity_level=ActivityLevel.LIGHT,
        conditions=[
            Condition(code=ConditionCode.T2DM),
            Condition(code=ConditionCode.CKD, stage="G3b"),
        ],
        medications=["metformin"],
        region="north",
    )


@pytest.fixture
def profile_htn() -> PatientProfile:
    return PatientProfile(
        patient_id="BN-DEMO-02",
        age=45,
        sex=Sex.FEMALE,
        height_cm=158,
        weight_kg=62,
        conditions=[Condition(code=ConditionCode.HTN)],
    )


@pytest.fixture
def profile_allergy_seafood() -> PatientProfile:
    return PatientProfile(
        patient_id="BN-DEMO-03",
        age=40,
        sex=Sex.FEMALE,
        height_cm=160,
        weight_kg=55,
        conditions=[Condition(code=ConditionCode.HTN)],
        allergies=["hải sản"],
    )


@pytest.fixture
def salty_menu() -> MenuDraft:
    """Thực đơn cố tình thừa muối — dùng để kiểm tra validator có chặn không."""
    return MenuDraft(
        items={
            MealSlot.LUNCH: [
                MenuItem(food_id=1, grams=300),
                MenuItem(food_id=2, grams=150),
                MenuItem(food_id=4, grams=40),  # 40 g nước mắm ~ 3120 mg natri
            ]
        }
    )


@pytest.fixture
def db_session():
    """DB SQLite in-memory riêng cho mỗi test — không đụng `.env`/DATABASE_URL thật
    (đúng testing.md: 'integration test dùng DB thật', ở mức API layer đây là
    SQLite thật (không mock ORM), chỉ khác Postgres production ở driver)."""
    from src.db import models  # noqa: F401  — đăng ký toàn bộ table với Base.metadata
    from src.db.base import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, expire_on_commit=False)
    session: Session = session_local()
    try:
        # API graph dùng kho thực phẩm seed thật để chọn food_id. Seed cùng dữ
        # liệu vào SQLite test để response có thể truy vết nguồn (RULE-2), thay
        # vì để MealPlanItem trỏ tới một bản ghi thực phẩm không tồn tại.
        from scripts.seed_db import seed_food_items

        seed_food_items(session)
        session.commit()
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    """`TestClient` với `get_db` override sang `db_session` — không chạm DB thật."""
    from src.db.base import get_db
    from src.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def modest_menu() -> MenuDraft:
    """Định lượng đã tăng 2026-08-06 (CLN-09: đổi BMR mặc định sang WHO/FAO/UNU
    — định mức kcal/chất xơ cao hơn Mifflin-St Jeor trước đó, cần nhiều thức
    ăn hơn để không rơi vào vi phạm 'thiếu')."""
    return MenuDraft(
        items={
            MealSlot.BREAKFAST: [MenuItem(food_id=1, grams=260), MenuItem(food_id=8, grams=120)],
            MealSlot.LUNCH: [
                MenuItem(food_id=1, grams=380),
                MenuItem(food_id=5, grams=150),
                MenuItem(food_id=3, grams=280),
                MenuItem(food_id=7, grams=10),
            ],
            MealSlot.DINNER: [
                MenuItem(food_id=1, grams=320),
                MenuItem(food_id=6, grams=180),
                MenuItem(food_id=3, grams=220),
                MenuItem(food_id=7, grams=7),
            ],
        }
    )
