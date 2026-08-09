"""Schema DB thật — SQLAlchemy ORM, khớp `docs/ARCHITECTURE.md` §5.

Ticket: BE-01. LLM: NO — thuần định nghĩa bảng, không có logic lâm sàng.

Đây là bản build ra từ ERD trong ARCHITECTURE.md §5, có MỞ RỘNG thêm các bảng
đã tồn tại thật trong `data/seeds/` nhưng ERD cũ (viết lúc S1, trước khi có
dữ liệu thật) chưa vẽ: `dishes`, `dish_ingredients`, `patient_medications`,
`patient_allergies`, `food_logs`, `guideline_chunks`, `serving_sizes`. ERD
mermaid trong ARCHITECTURE.md đã cập nhật lại cho khớp file này — sửa 1 bên
thì phải sửa bên kia (2 bản mô tả cùng 1 sự thật, không được lệch nhau).

Quy ước:
- Bảng bắt buộc có cột `source`/`source_ref` theo RULE-2: `food_items`,
  `dishes`, `clinical_rules`, `drug_food_interactions`, `guideline_chunks`.
  KHÔNG có `nullable=False` cứng ở tầng cột cho `source_ref` vì một số dòng
  hợp lệ chưa nhập xong (seed CSV đang import) — validate ở tầng ứng dụng
  (`scripts/validate_data.py`) trước khi promote sang production DB, không
  chặn ở tầng DDL để tránh phá `alembic upgrade` khi có dữ liệu nháp.
- `id` các bảng nghiệp vụ chính dùng UUID (đúng ERD gốc); bảng seed từ CSV
  (`food_items`, `dishes`, `clinical_rules`, `drug_food_interactions`,
  `gi_values`... đã merge vào `food_items`) giữ nguyên kiểu khoá đang dùng
  trong CSV (int/string) để import thẳng không phải đổi kiểu.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# --------------------------------------------------------------------------
# Người dùng & hồ sơ bệnh nhân
# --------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # patient|dietitian|admin

    profile: Mapped[PatientProfile | None] = relationship(back_populates="user", uselist=False)


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    age: Mapped[int] = mapped_column(Integer)
    sex: Mapped[str] = mapped_column(String(10))
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    conditions: Mapped[list] = mapped_column(JSON, default=list)  # [{code, stage}] ICD10 + giai đoạn
    lab_values: Mapped[dict] = mapped_column(JSON, default=dict)  # {eGFR, HbA1c, K, uric...}
    activity_level: Mapped[str] = mapped_column(String(20), default="light")
    region: Mapped[str | None] = mapped_column(String(10), nullable=True)  # north|central|south

    user: Mapped[User] = relationship(back_populates="profile")
    medications: Mapped[list[PatientMedication]] = relationship(back_populates="profile")
    allergies: Mapped[list[PatientAllergy]] = relationship(back_populates="profile")
    meal_plans: Mapped[list[MealPlan]] = relationship(back_populates="profile")
    food_logs: Mapped[list[FoodLog]] = relationship(back_populates="profile")
    pantry_items: Mapped[list[PantryItem]] = relationship(back_populates="profile")


class PatientMedication(Base):
    """Thuốc bệnh nhân đang dùng — đầu vào cho CLN-06 (kiểm tra tương tác thuốc-thực phẩm)."""

    __tablename__ = "patient_medications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    drug_name: Mapped[str] = mapped_column(String(255))
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    profile: Mapped[PatientProfile] = relationship(back_populates="medications")


class PatientAllergy(Base):
    """Dị ứng bệnh nhân — đầu vào cho CLN-05 (chặn cứng, không bao giờ chỉ cảnh báo)."""

    __tablename__ = "patient_allergies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    allergen: Mapped[str] = mapped_column(String(100))  # VD "hải sản", "đậu phộng"

    profile: Mapped[PatientProfile] = relationship(back_populates="allergies")


# --------------------------------------------------------------------------
# Thực phẩm & món ăn (RULE-2: bắt buộc source/source_ref)
# --------------------------------------------------------------------------
class FoodItem(Base):
    """Khớp `data/seeds/food_items.csv`. `id` giữ nguyên kiểu int từ CSV để import thẳng."""

    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_vi: Mapped[str] = mapped_column(String(255), index=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    kcal_100g: Mapped[float] = mapped_column(Float)
    protein_g: Mapped[float] = mapped_column(Float)
    carb_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)
    fiber_g: Mapped[float] = mapped_column(Float)
    sugar_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    na_mg: Mapped[float] = mapped_column(Float)
    k_mg: Mapped[float] = mapped_column(Float)
    p_mg: Mapped[float] = mapped_column(Float)
    purine_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    purine_source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    gi_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    gi_source: Mapped[str | None] = mapped_column(String(30), nullable=True)
    gi_source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    contains_allergens: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(20))  # NIN|USDA|curated|estimated — RULE-2
    source_ref: Mapped[str] = mapped_column(Text)  # RULE-2: bắt buộc truy vết được
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)

    dish_ingredients: Mapped[list[DishIngredient]] = relationship(back_populates="food")
    meal_plan_items: Mapped[list[MealPlanItem]] = relationship(back_populates="food")


class Dish(Base):
    """Khớp `data/seeds/dishes.csv`. `dish_id` là string (VD 'pho-bo') theo CSV hiện có."""

    __tablename__ = "dishes"

    dish_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name_vi: Mapped[str] = mapped_column(String(255), index=True)
    region: Mapped[str | None] = mapped_column(String(20), nullable=True)  # north|central|south
    serving_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(100), nullable=True)  # RULE-2 cho món (DAT-04)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    ingredients: Mapped[list[DishIngredient]] = relationship(back_populates="dish")
    meal_plan_items: Mapped[list[MealPlanItem]] = relationship(back_populates="dish")


class DishIngredient(Base):
    """Khớp `data/seeds/dish_ingredients.csv`. Món = tổng nguyên liệu × gram, tính bằng SQL (RULE-1)."""

    __tablename__ = "dish_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dish_id: Mapped[str] = mapped_column(ForeignKey("dishes.dish_id"), index=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"), index=True)
    grams: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    dish: Mapped[Dish] = relationship(back_populates="ingredients")
    food: Mapped[FoodItem] = relationship(back_populates="dish_ingredients")


class ServingSize(Base):
    """Khớp `data/seeds/serving_sizes.csv` — khẩu phần chuẩn theo nhóm món (bát phở ~500g...)."""

    __tablename__ = "serving_sizes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    serving_g: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)


# --------------------------------------------------------------------------
# Luật lâm sàng & tương tác
# --------------------------------------------------------------------------
class ClinicalRule(Base):
    """Khớp `data/seeds/clinical_rules.csv`. `rule_id` string (VD 'CKD-NA-01')."""

    __tablename__ = "clinical_rules"

    rule_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    condition_code: Mapped[str] = mapped_column(String(20), index=True)
    stages: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nutrient: Mapped[str] = mapped_column(String(30))
    bound: Mapped[str] = mapped_column(String(10))  # min|max
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))
    basis: Mapped[str] = mapped_column(String(20))  # absolute|per_kg|pct_energy|per_1000kcal
    severity: Mapped[str] = mapped_column(String(10))  # hard|soft
    guideline_ref: Mapped[str] = mapped_column(Text)  # RULE-2
    guideline_grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    verify_status: Mapped[str] = mapped_column(String(20), default="to_verify")
    overridden_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    disabled_by_flag: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requires_flag: Mapped[str | None] = mapped_column(String(50), nullable=True)


class DrugFoodInteraction(Base):
    """Khớp `data/seeds/drug_food_interactions.csv`."""

    __tablename__ = "drug_food_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drug_name: Mapped[str] = mapped_column(String(255), index=True)
    drug_class: Mapped[str | None] = mapped_column(String(255), nullable=True)
    food_or_nutrient: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(10))  # high|moderate|low
    mechanism_vi: Mapped[str] = mapped_column(Text)
    recommendation_vi: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)  # RULE-2 — xem DAT-05
    verify_status: Mapped[str] = mapped_column(String(20), default="to_verify")


class FoodFoodInteraction(Base):
    """Tương tác thực phẩm–thực phẩm (cơ chế hoá sinh, VD phytate/tannin ức
    chế hấp thu sắt, canxi ăn cùng bữa giảm oxalat niệu...). Khớp
    `data/seeds/food_food_interactions.csv`. Ticket: DAT-18.
    """

    __tablename__ = "food_food_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    substance_a: Mapped[str] = mapped_column(String(255))
    substance_b: Mapped[str] = mapped_column(String(255))
    food_examples_vi: Mapped[str] = mapped_column(Text)
    mechanism_vi: Mapped[str] = mapped_column(Text)
    direction: Mapped[str] = mapped_column(String(20))  # increases|decreases
    effect_size_vi: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_significance: Mapped[str] = mapped_column(String(10))  # high|moderate|low
    applies_to_condition: Mapped[str | None] = mapped_column(String(20), nullable=True)  # T2DM|HTN|CKD|GOUT|None
    recommendation_vi: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str] = mapped_column(Text)  # RULE-2
    pmid: Mapped[str | None] = mapped_column(String(20), nullable=True)
    verify_status: Mapped[str] = mapped_column(String(20), default="to_verify")


class DrugMealTiming(Base):
    """Thời điểm dùng thuốc so với bữa ăn (dược động học). KHÔNG được diễn
    giải thành chỉ định điều trị/khuyên đổi liều (ranh giới an toàn CLAUDE.md
    §3) — chỉ mô tả khuyến nghị chế độ ăn/thời điểm uống theo nguồn dược thư.
    Khớp `data/seeds/drug_meal_timing.csv`. Ticket: DAT-19.
    """

    __tablename__ = "drug_meal_timing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drug_name: Mapped[str] = mapped_column(String(255), index=True)
    drug_class: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timing_rule: Mapped[str] = mapped_column(String(20))  # before|with|after|avoid_with
    offset_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relative_to: Mapped[str] = mapped_column(String(50))  # VD "bữa ăn", "cà phê"
    rationale_pk_vi: Mapped[str] = mapped_column(Text)
    condition: Mapped[str | None] = mapped_column(String(20), nullable=True)  # T2DM|HTN|CKD|GOUT|None
    source_ref: Mapped[str] = mapped_column(Text)  # RULE-2
    page_ref: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verify_status: Mapped[str] = mapped_column(String(20), default="to_verify")


class GuidelineChunk(Base):
    """Khớp DAT-06 (ingest RAG). `embedding` = JSON trên SQLite, đổi sang
    `pgvector.sqlalchemy.Vector(1536)` khi deploy Postgres thật — xem docstring
    module `src/db/base.py`.
    """

    __tablename__ = "guideline_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(100))  # VD "ADA 2025", "KDIGO 2024"
    title: Mapped[str] = mapped_column(String(255))
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    condition_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)  # TODO: pgvector.Vector khi có Postgres


# --------------------------------------------------------------------------
# Thực đơn & nhật ký ăn uống
# --------------------------------------------------------------------------
class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    plan_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="drafting")
    targets: Mapped[dict] = mapped_column(JSON, default=dict)
    computed_nutrition: Mapped[dict] = mapped_column(JSON, default=dict)
    violations: Mapped[list] = mapped_column(JSON, default=list)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped[PatientProfile] = relationship(back_populates="meal_plans")
    items: Mapped[list[MealPlanItem]] = relationship(back_populates="plan")


class MealPlanItem(Base):
    """RULE-1: chỉ `food_id` + `grams` + `slot` — không cột dinh dưỡng nào ở đây."""

    __tablename__ = "meal_plan_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(ForeignKey("meal_plans.id"), index=True)
    slot: Mapped[str] = mapped_column(String(20))  # breakfast|lunch|dinner|snack
    # New rows point to a prepared dish. food_id remains nullable so existing
    # development databases and historical ingredient-level plans still load.
    food_id: Mapped[int | None] = mapped_column(ForeignKey("food_items.id"), nullable=True)
    dish_id: Mapped[str | None] = mapped_column(ForeignKey("dishes.dish_id"), nullable=True, index=True)
    grams: Mapped[float] = mapped_column(Float)

    plan: Mapped[MealPlan] = relationship(back_populates="items")
    food: Mapped[FoodItem | None] = relationship(back_populates="meal_plan_items")
    dish: Mapped[Dish | None] = relationship(back_populates="meal_plan_items")


class FoodLog(Base):
    """Nhật ký ăn uống thật (BE-07) — khác `meal_plan_items` (thực đơn ĐỀ XUẤT).
    `food_id` có thể null khi bệnh nhân gõ tự do món chưa có trong DB (OOV, CLN-07).
    """

    __tablename__ = "food_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    food_id: Mapped[int | None] = mapped_column(ForeignKey("food_items.id"), nullable=True)
    free_text_vi: Mapped[str | None] = mapped_column(String(255), nullable=True)  # OOV: tên gõ tay
    grams: Mapped[float] = mapped_column(Float)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)  # true nếu qua OOV Estimator

    profile: Mapped[PatientProfile] = relationship(back_populates="food_logs")


class PantryItem(Base):
    """Nguyên liệu bệnh nhân khai báo có sẵn — đầu vào cho thực đơn tương đương
    (P2/AGT-12, `src/agents/equivalent.py`).

    `free_text_vi` giữ chỗ cho nhập tự do (VD "còn nửa con gà") nhưng KHÔNG có
    cơ chế tự khớp sang `food_id` trong lượt này — phụ thuộc `FoodMatcher`
    (BE-07, chưa merge vào `main`). Dòng chỉ `free_text_vi` (food_id=None) bị
    `solve_equivalent()` bỏ qua, không suy đoán (RULE-2).
    """

    __tablename__ = "pantry_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    food_id: Mapped[int | None] = mapped_column(ForeignKey("food_items.id"), nullable=True)
    free_text_vi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qty: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped[PatientProfile] = relationship(back_populates="pantry_items")
    food: Mapped[FoodItem | None] = relationship()


class SubstitutionScope(Base):
    """Phạm vi thay thế duyệt trước (RULE-3, DEC-018 — DEVLOG.md §3).

    Chuyên gia duyệt MỘT CHÍNH SÁCH áp cho nhiều lần phát hành tự động, không
    phải từng bản riêng lẻ. Thực đơn tương đương chỉ được tự phát hành (không
    qua duyệt tay) khi ĐỒNG THỜI: còn hạn (`expires_at`), `validate_menu()`
    không có vi phạm nào (kể cả soft), mọi nguyên liệu `is_estimated=False`,
    nằm trong `tolerance`, `release_count < max_auto_releases`. Trượt bất kỳ
    điều kiện nào → rơi về `pending_review`. Bảng này chỉ LƯU chính sách —
    việc enforce nằm ở route gọi `solve_equivalent()`, không phải ở đây.
    """

    __tablename__ = "substitution_scopes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    base_plan_id: Mapped[str] = mapped_column(ForeignKey("meal_plans.id"), index=True)
    approved_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    tolerance: Mapped[float] = mapped_column(Float, default=0.10)
    max_auto_releases: Mapped[int] = mapped_column(Integer, default=5)
    release_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    profile: Mapped[PatientProfile] = relationship()
    base_plan: Mapped[MealPlan] = relationship()


class AuditLog(Base):
    """Append-only theo R20.16/BE-08 — KHÔNG có API xoá/sửa ở tầng ứng dụng."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    actor_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(50))  # generate|approve|edit|reject|view_patient|edit_rule
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)


__all__ = [
    "AuditLog",
    "Dish",
    "DishIngredient",
    "ClinicalRule",
    "DrugFoodInteraction",
    "FoodItem",
    "FoodLog",
    "GuidelineChunk",
    "MealPlan",
    "MealPlanItem",
    "PantryItem",
    "PatientAllergy",
    "PatientMedication",
    "PatientProfile",
    "ServingSize",
    "SubstitutionScope",
    "User",
]
