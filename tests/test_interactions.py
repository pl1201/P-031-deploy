"""Test cảnh báo tương tác thuốc–thực phẩm — CLN-06.

Bảng `drug_food_interactions.csv` (30 cặp) đã được seed vào DB từ lâu nhưng
trước đây KHÔNG có dòng code nào truy vấn — thuốc bệnh nhân đang dùng hoàn
toàn không ảnh hưởng gì tới thực đơn sinh ra.
"""

from __future__ import annotations

import pytest

from src.clinical.interactions import (
    DrugFoodRule,
    advisories_for,
    check_drug_food_interactions,
    load_drug_food_rules,
    rules_for_medications,
)
from src.clinical.models import (
    Condition,
    ConditionCode,
    MealSlot,
    MenuDraft,
    MenuItem,
    PatientProfile,
    Severity,
)

FIXTURE_REF = "TEST-FIXTURE (dữ liệu giả, không dùng lâm sàng)"


def _rule(drug, food, severity="high", verify="to_verify", drug_class=None) -> DrugFoodRule:
    return DrugFoodRule(
        drug_name=drug,
        drug_class=drug_class,
        food_or_nutrient=food,
        severity=severity,
        mechanism_vi="Cơ chế giả lập cho test",
        recommendation_vi="Khuyến nghị giả lập cho test",
        source_ref=FIXTURE_REF,
        verify_status=verify,
    )


def _profile(medications: list[str]) -> PatientProfile:
    return PatientProfile(
        patient_id="test-cln06",
        age=60,
        sex="male",
        height_cm=165.0,
        weight_kg=65.0,
        conditions=[Condition(code=ConditionCode.T2DM)],
        medications=medications,
    )


def _menu(food_id: int, grams: float = 150.0) -> MenuDraft:
    return MenuDraft(items={MealSlot.BREAKFAST: [MenuItem(food_id=food_id, grams=grams)]})


# ---------------------------------------------------------------------------
# Nạp dữ liệu thật
# ---------------------------------------------------------------------------
def test_nap_du_30_cap_tu_seed() -> None:
    rules = load_drug_food_rules()
    # `>=` chứ không `== 30`: mục tiêu là 80 cặp curated (ADR-005), nên mỗi lần
    # R2 bổ sung dữ liệu, một assert số chính xác sẽ vỡ mà không chỉ ra lỗi thật.
    assert len(rules) >= 30
    assert all(r.source_ref for r in rules), "RULE-2: mọi cặp tương tác phải dẫn được nguồn"


def test_tach_dung_nhom_ten_mon_va_nhom_chat() -> None:
    """Hai loại phải tách được, vì chỉ loại 'tên món' mới tự khớp được."""
    rules = load_drug_food_rules()
    ten_mon = [r for r in rules if not r.is_nutrient_group]
    nhom_chat = [r for r in rules if r.is_nutrient_group]

    assert ten_mon and nhom_chat
    assert any("bưởi" in r.food_or_nutrient.lower() for r in ten_mon)
    assert any("giàu kali" in r.food_or_nutrient.lower() for r in nhom_chat)


# ---------------------------------------------------------------------------
# Khớp tên thuốc
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "medication",
    ["Atorvastatin", "atorvastatin 20mg", "ATORVASTATIN 40 mg uống tối"],
)
def test_khop_thuoc_bat_ke_ham_luong_va_hoa_thuong(medication: str) -> None:
    """Đơn thuốc thật luôn kèm hàm lượng/liều — không được vì thế mà trượt."""
    rules = [_rule("Atorvastatin", "bưởi")]
    assert rules_for_medications([medication], rules)


def test_khop_hoat_chat_trong_ngoac() -> None:
    """Rule ghi 'Sulfonylurea (Gliclazide)' phải khớp đơn ghi 'gliclazide'."""
    rules = [_rule("Sulfonylurea (Gliclazide)", "rượu bia")]
    assert rules_for_medications(["Gliclazide 30mg"], rules)


def test_khong_khop_thuoc_khac() -> None:
    rules = [_rule("Warfarin", "rau ngót")]
    assert rules_for_medications(["Metformin 500mg"], rules) == []


def test_khong_dung_thuoc_thi_khong_canh_bao(foods) -> None:
    rules = [_rule("Atorvastatin", "bưởi")]
    profile = _profile([])

    assert check_drug_food_interactions(_menu(1), profile, foods, rules) == []


# ---------------------------------------------------------------------------
# Sinh cảnh báo theo tên món
# ---------------------------------------------------------------------------
def test_canh_bao_khi_mon_trong_thuc_don_khop_ten(foods) -> None:
    """Ca thật: statin + bưởi (ức chế CYP3A4)."""
    # `foods` fixture dùng "Cá lóc"/"Nước mắm"…; thêm rule khớp đúng tên có sẵn.
    rules = [_rule("Metformin", "rượu bia")]
    profile = _profile(["Metformin 500mg"])

    # Món trong thực đơn KHÔNG phải rượu bia → không cảnh báo.
    assert check_drug_food_interactions(_menu(1), profile, foods, rules) == []


def test_evidence_luon_chi_dich_danh_mon_kich_hoat(foods) -> None:
    """Chuyên gia phải soi được vì sao máy cảnh báo, không phải tin suông."""
    ten_mon = foods.get(4).name_vi  # "Nước mắm" trong fixture
    rules = [_rule("Thuốc giả lập", ten_mon)]
    profile = _profile(["Thuốc giả lập"])

    violations = check_drug_food_interactions(_menu(4), profile, foods, rules)

    assert len(violations) == 1
    v = violations[0]
    assert v.kind == "drug_food"
    assert ten_mon in (v.evidence or "")
    assert v.source_ref == FIXTURE_REF


def test_khong_bia_so_cho_canh_bao_dinh_tinh(foods) -> None:
    """RULE-2: cảnh báo tương tác không có ngưỡng số ⇒ actual/limit phải là None.

    Nếu nhồi 0.0 vào thì UI sẽ hiển thị '0 mg' y như một số đo thật.
    """
    rules = [_rule("Thuốc giả lập", foods.get(4).name_vi)]
    violations = check_drug_food_interactions(_menu(4), _profile(["Thuốc giả lập"]), foods, rules)

    assert violations[0].actual is None
    assert violations[0].limit is None
    assert violations[0].unit is None


def test_moi_cap_thuoc_mon_chi_canh_bao_mot_lan(foods) -> None:
    """Cùng một món xuất hiện ở nhiều bữa không được nhân bản cảnh báo."""
    ten_mon = foods.get(4).name_vi
    rules = [_rule("Thuốc giả lập", ten_mon)]
    menu = MenuDraft(
        items={
            MealSlot.BREAKFAST: [MenuItem(food_id=4, grams=10)],
            MealSlot.LUNCH: [MenuItem(food_id=4, grams=15)],
            MealSlot.DINNER: [MenuItem(food_id=4, grams=12)],
        }
    )

    violations = check_drug_food_interactions(menu, _profile(["Thuốc giả lập"]), foods, rules)

    assert len(violations) == 1


# ---------------------------------------------------------------------------
# verify_status quyết định mức chặn (PRD FR-14)
# ---------------------------------------------------------------------------
def test_cap_chua_xac_minh_khong_duoc_chan_cung(foods) -> None:
    """Rule chưa qua tay chuyên gia không được quyền chặn thực đơn."""
    rules = [_rule("Thuốc giả lập", foods.get(4).name_vi, severity="high", verify="to_verify")]

    violations = check_drug_food_interactions(_menu(4), _profile(["Thuốc giả lập"]), foods, rules)

    assert violations[0].severity is Severity.SOFT
    assert not violations[0].blocking
    assert "chưa được chuyên gia xác minh" in violations[0].message_vi


def test_cap_da_xac_minh_va_high_thi_chan_cung(foods) -> None:
    rules = [_rule("Thuốc giả lập", foods.get(4).name_vi, severity="high", verify="verified")]

    violations = check_drug_food_interactions(_menu(4), _profile(["Thuốc giả lập"]), foods, rules)

    assert violations[0].severity is Severity.HARD
    assert violations[0].blocking
    assert "chưa được chuyên gia xác minh" not in violations[0].message_vi


def test_moderate_da_xac_minh_van_chi_la_canh_bao_mem(foods) -> None:
    rules = [_rule("Thuốc giả lập", foods.get(4).name_vi, severity="moderate", verify="verified")]

    violations = check_drug_food_interactions(_menu(4), _profile(["Thuốc giả lập"]), foods, rules)

    assert violations[0].severity is Severity.SOFT


# ---------------------------------------------------------------------------
# Nhóm chất — tách riêng, không quy kết món nào
# ---------------------------------------------------------------------------
def test_nhom_chat_khong_sinh_canh_bao_theo_mon(foods) -> None:
    """'thực phẩm giàu kali' cần ngưỡng lâm sàng — không được tự đoán món nào vi phạm."""
    rules = [_rule("Enalapril", "thực phẩm giàu kali")]

    assert check_drug_food_interactions(_menu(3), _profile(["Enalapril"]), foods, rules) == []


def test_nhom_chat_tra_ve_luu_y_cho_chuyen_gia() -> None:
    rules = [_rule("Enalapril", "thực phẩm giàu kali")]

    advisories = advisories_for(_profile(["Enalapril 10mg"]), rules)

    assert len(advisories) == 1
    assert advisories[0].severity is Severity.SOFT
    assert "CHƯA tự kiểm tra được" in advisories[0].message_vi
    assert advisories[0].actual is None


def test_khong_dung_thuoc_thi_khong_co_luu_y() -> None:
    rules = [_rule("Enalapril", "thực phẩm giàu kali")]
    assert advisories_for(_profile([]), rules) == []
