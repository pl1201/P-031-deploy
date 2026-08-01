"""Test tầng lâm sàng: năng lượng, định mức, tính dinh dưỡng, validator."""

from __future__ import annotations

import pytest

from src.clinical.energy import (
    adjusted_body_weight_kg,
    bmr_mifflin_st_jeor,
    compute_energy_target_kcal,
    ideal_body_weight_kg,
    kcal_per_kg,
)
from src.clinical.models import (
    ActivityLevel,
    Condition,
    ConditionCode,
    FoodItem,
    MealSlot,
    MenuDraft,
    MenuItem,
    PatientProfile,
    Severity,
    Sex,
    WeightGoal,
)
from src.clinical.nutrition import (
    InMemoryFoodRepository,
    UnknownFoodError,
    check_allergies,
    compute_nutrition,
)
from src.clinical.rules import compute_targets, load_rules
from src.clinical.validator import build_feedback, has_blocking, validate_menu


# ---------------------------------------------------------------- năng lượng
class TestEnergy:
    def test_bmr_nam_khop_cong_thuc_mifflin(self):
        # 10*65 + 6.25*165 - 5*58 + 5 = 650 + 1031.25 - 290 + 5
        assert bmr_mifflin_st_jeor(65, 165, 58, Sex.MALE) == pytest.approx(1396.25)

    def test_bmr_nu_thap_hon_nam_cung_thong_so(self):
        nam = bmr_mifflin_st_jeor(60, 160, 40, Sex.MALE)
        nu = bmr_mifflin_st_jeor(60, 160, 40, Sex.FEMALE)
        assert nu < nam
        assert nam - nu == pytest.approx(166.0)

    def test_ibw_theo_bmi_22(self):
        assert ideal_body_weight_kg(165) == pytest.approx(59.895, abs=0.01)

    def test_can_nang_hieu_chinh_chi_ap_dung_khi_beo_phi(self):
        assert adjusted_body_weight_kg(65, 165) == 65  # BMI ~23.9
        # BMI ~36.7 → phải hiệu chỉnh xuống
        adj = adjusted_body_weight_kg(100, 165)
        assert adj < 100
        assert adj > ideal_body_weight_kg(165)

    @pytest.mark.parametrize("sex,floor", [(Sex.FEMALE, 1200.0), (Sex.MALE, 1500.0)])
    def test_khong_bao_gio_xuong_duoi_san_an_toan(self, sex, floor):
        """Sàn năng lượng là ràng buộc an toàn, không phải tuỳ chọn."""
        p = PatientProfile(
            patient_id="X",
            age=80,
            sex=sex,
            height_cm=145,
            weight_kg=38,
            activity_level=ActivityLevel.SEDENTARY,
            weight_goal=WeightGoal.LOSE,
        )
        assert compute_energy_target_kcal(p) >= floor

    def test_kcal_tren_kg_nam_trong_khoang_lam_sang(self, profile_t2dm_ckd):
        """Kiểm tra chéo: bệnh nhân mãn tính ổn định thường 30–35 kcal/kg/ngày."""
        assert 25 <= kcal_per_kg(profile_t2dm_ckd) <= 40


# ----------------------------------------------------------------- định mức
class TestTargets:
    def test_ap_dung_dung_rule_theo_benh_ly(self, profile_htn):
        t = compute_targets(profile_htn, load_rules())
        assert t.max_of("na_mg") == 2000
        assert "HTN-NA-01" in t.applied_rule_ids

    def test_da_benh_ly_lay_nguong_nghiem_ngat_hon(self, profile_t2dm_ckd):
        """ĐTĐ2 + CKD G3b: protein phải theo CKD (chặt hơn), kali theo G3b."""
        t = compute_targets(profile_t2dm_ckd, load_rules())
        weight = 65
        # KDIGO thắng ADA về protein khi có CKD (rule precedence, xem _select_rules)
        assert t.max_of("protein_g") == pytest.approx(0.8 * weight)
        assert t.min_of("protein_g") == pytest.approx(0.6 * weight)
        assert t.needs_expert_review is False, "Ca ĐTĐ+CKD phổ biến, không được đẩy sang chuyên gia"
        assert t.max_of("k_mg") == 3000
        assert t.max_of("p_mg") == 1000

    def test_rule_bi_vo_hieu_khi_khong_co_benh_ghi_de(self):
        """Không có CKD thì rule protein của ADA vẫn áp dụng bình thường."""
        p = PatientProfile(
            patient_id="X",
            age=58,
            sex=Sex.MALE,
            height_cm=165,
            weight_kg=65,
            conditions=[Condition(code=ConditionCode.T2DM)],
        )
        t = compute_targets(p, load_rules())
        assert "T2DM-PRO-01" in t.applied_rule_ids
        assert t.min_of("protein_g") is not None

    def test_ckd_giai_doan_nang_hon_thi_nguong_kali_chat_hon(self):
        base = dict(patient_id="X", age=60, sex=Sex.MALE, height_cm=170, weight_kg=70)
        g3 = compute_targets(
            PatientProfile(**base, conditions=[Condition(code=ConditionCode.CKD, stage="G3a")]),
            load_rules(),
        )
        g5 = compute_targets(
            PatientProfile(**base, conditions=[Condition(code=ConditionCode.CKD, stage="G5")]),
            load_rules(),
        )
        assert g5.max_of("k_mg") < g3.max_of("k_mg")

    def test_luon_tra_ve_rule_ids_de_giai_trinh(self, profile_t2dm_ckd):
        t = compute_targets(profile_t2dm_ckd, load_rules())
        assert t.applied_rule_ids
        assert t.targets["na_mg"].guideline_refs, "Ngưỡng nào cũng phải dẫn được guideline"

    def test_gout_gioi_han_purin(self):
        p = PatientProfile(
            patient_id="X",
            age=50,
            sex=Sex.MALE,
            height_cm=170,
            weight_kg=80,
            conditions=[Condition(code=ConditionCode.GOUT)],
        )
        assert compute_targets(p, load_rules()).max_of("purine_mg") == 150

    def test_xung_dot_nguong_thi_chuyen_chuyen_gia_khong_tu_quyet(self, monkeypatch):
        """min > max sau hợp nhất → gắn cờ, không tự chọn bên nào."""
        rules = load_rules()
        conflicting = [r for r in rules if r.rule_id == "CKD-PRO-01"]
        assert conflicting, "fixture cần rule CKD-PRO-01"
        # Tạo xung đột nhân tạo: ép ngưỡng dưới cao hơn ngưỡng trên
        from dataclasses import replace

        bad = replace(conflicting[0], rule_id="TEST-CONFLICT", bound="min", value=2.0)
        t = compute_targets(
            PatientProfile(
                patient_id="X",
                age=60,
                sex=Sex.MALE,
                height_cm=170,
                weight_kg=70,
                conditions=[Condition(code=ConditionCode.CKD, stage="G4")],
            ),
            rules + [bad],
        )
        assert t.needs_expert_review is True
        assert t.conflict_notes


# ------------------------------------------------- tính dinh dưỡng (RULE-1)
class TestNutrition:
    def test_moi_con_so_deu_co_nguon(self, foods, modest_menu):
        """RULE-2: sources rỗng là bug, không phải trường hợp hợp lệ."""
        s = compute_nutrition(modest_menu, foods)
        assert s.sources
        assert len(s.sources) == len(modest_menu.all_items())
        assert all(x.source_ref for x in s.sources)

    def test_cong_dung_theo_khoi_luong(self, foods):
        menu = MenuDraft(items={MealSlot.LUNCH: [MenuItem(food_id=1, grams=200)]})
        s = compute_nutrition(menu, foods)
        assert s.kcal == pytest.approx(260.0)  # 130 kcal/100g * 2
        assert s.protein_g == pytest.approx(5.4)

    def test_food_id_khong_ton_tai_thi_bao_loi_khong_doan_bua(self, foods):
        menu = MenuDraft(items={MealSlot.LUNCH: [MenuItem(food_id=9999, grams=100)]})
        with pytest.raises(UnknownFoodError):
            compute_nutrition(menu, foods)

    def test_thuc_don_rong_tra_ve_0_khong_loi(self, foods):
        s = compute_nutrition(MenuDraft(), foods)
        assert s.kcal == 0 and s.sources == []


# ------------------------------------------------------------------ dị ứng
class TestAllergy:
    def test_di_ung_luon_la_vi_pham_cung(self, foods, profile_allergy_seafood):
        menu = MenuDraft(items={MealSlot.LUNCH: [MenuItem(food_id=9, grams=100)]})  # tôm
        v = check_allergies(menu, profile_allergy_seafood, foods)
        assert len(v) == 1
        assert v[0].severity is Severity.HARD
        assert v[0].blocking is True
        assert "hải sản" in v[0].message_vi

    def test_khong_di_ung_thi_khong_canh_bao(self, foods, profile_htn):
        menu = MenuDraft(items={MealSlot.LUNCH: [MenuItem(food_id=9, grams=100)]})
        assert check_allergies(menu, profile_htn, foods) == []


# --------------------------------------------------------------- validator
class TestValidator:
    def test_chan_thuc_don_thua_muoi_cho_benh_nhan_tang_huyet_ap(self, foods, profile_htn, salty_menu):
        rules = load_rules()
        targets = compute_targets(profile_htn, rules)
        nutrition = compute_nutrition(salty_menu, foods)
        violations = validate_menu(nutrition, targets, rules)

        na = [v for v in violations if v.nutrient == "na_mg"]
        assert na, "Phải phát hiện vượt natri"
        assert na[0].severity is Severity.HARD
        assert has_blocking(violations) is True
        assert na[0].suggestion and "nước chấm" in na[0].suggestion

    def test_feedback_neu_ro_chat_nao_vuot_bao_nhieu(self, foods, profile_htn, salty_menu):
        rules = load_rules()
        targets = compute_targets(profile_htn, rules)
        nutrition = compute_nutrition(salty_menu, foods)
        fb = build_feedback(validate_menu(nutrition, targets, rules), nutrition)

        assert "Natri" in fb
        assert "[CHẶN]" in fb
        assert "Hướng xử lý" in fb
        # Feedback phải cụ thể, không được là câu chung chung
        assert "hãy thử lại" not in fb.lower()

    @pytest.mark.parametrize(
        "ratio,expected",
        [
            (1.15, Severity.SOFT),  # vượt 15% so với định mức → cảnh báo
            (1.40, Severity.HARD),  # vượt 40% → chặn
            (0.85, Severity.SOFT),  # thiếu 15% → cảnh báo
            (0.60, Severity.HARD),  # thiếu 40% → chặn
        ],
    )
    def test_muc_do_vi_pham_nang_luong_theo_do_lech(self, foods, profile_htn, ratio, expected):
        """±10% là bình thường, ±25% trở lên là chặn (RULE: fail closed)."""
        rules = load_rules()
        targets = compute_targets(profile_htn, rules)
        base_kcal = targets.max_of("kcal") / 1.10  # suy ngược định mức gốc

        # Cơm tẻ 1.3 kcal/g — dùng để đạt chính xác mức năng lượng cần test
        grams = base_kcal * ratio / 1.30
        nutrition = compute_nutrition(MenuDraft(items={MealSlot.LUNCH: [MenuItem(food_id=1, grams=grams)]}), foods)
        kcal_violations = [v for v in validate_menu(nutrition, targets, rules) if v.nutrient == "kcal"]
        assert len(kcal_violations) == 1
        assert kcal_violations[0].severity is expected

    def test_thuc_don_hop_le_khong_sinh_vi_pham_cung(self, foods, profile_htn, modest_menu):
        rules = load_rules()
        targets = compute_targets(profile_htn, rules)
        nutrition = compute_nutrition(modest_menu, foods)
        violations = validate_menu(nutrition, targets, rules)
        assert not has_blocking(violations)


# ------------------------------------------- KDIGO 2024 / ADA 2026 safety flags
class TestKdigo2024SafetyFlags:
    """Các chốt an toàn theo KDIGO 2024 Practice Point 3.3.1.3 và 3.3.1.5.

    Bối cảnh: KDIGO 2024 thay thế bản 2012. Khuyến nghị 3.3.1.1 là *duy trì*
    0,8 g/kg (mức 2C - yếu), không phải khoảng 0,6-0,8. Quan trọng hơn, có hai
    tình huống mà việc hạn chế protein là CHỐNG CHỈ ĐỊNH.
    """

    BASE = dict(patient_id="X", sex=Sex.MALE, height_cm=165, weight_kg=65)
    CKD_G4 = [Condition(code=ConditionCode.CKD, stage="G4")]

    def test_ca_on_dinh_van_ap_tran_protein_binh_thuong(self):
        p = PatientProfile(**self.BASE, age=58, conditions=self.CKD_G4)
        t = compute_targets(p, load_rules())
        assert t.max_of("protein_g") == pytest.approx(0.8 * 65)
        assert t.min_of("protein_g") == pytest.approx(0.6 * 65)
        assert t.needs_expert_review is False

    def test_suy_yeu_thieu_co_thi_go_tran_protein_thap(self):
        """PP 3.3.1.5: người cao tuổi có frailty/sarcopenia cần protein CAO HƠN."""
        p = PatientProfile(**self.BASE, age=72, conditions=self.CKD_G4, frailty_sarcopenia=True)
        t = compute_targets(p, load_rules())

        assert "CKD-PRO-01" not in t.targets["protein_g"].rule_ids
        # Trần an toàn tuyệt đối 1.3 g/kg vẫn còn hiệu lực
        assert t.max_of("protein_g") == pytest.approx(1.3 * 65)
        assert t.needs_expert_review is True
        assert any("CKD-PRO-01" in c for c in t.conflict_notes)

    def test_chuyen_hoa_khong_on_dinh_thi_khong_han_che_protein(self):
        """PP 3.3.1.3: không kê chế độ thấp protein cho người chuyển hoá không ổn định."""
        p = PatientProfile(**self.BASE, age=58, conditions=self.CKD_G4, metabolically_unstable=True)
        t = compute_targets(p, load_rules())

        ids = t.targets["protein_g"].rule_ids
        assert "CKD-PRO-01" not in ids and "CKD-PRO-02" not in ids
        assert t.needs_expert_review is True

    def test_tran_an_toan_1_3_khong_bao_gio_bi_vo_hieu(self):
        """CKD-PRO-05 là trần tuyệt đối, mọi cờ đều không gỡ được."""
        p = PatientProfile(
            **self.BASE,
            age=80,
            conditions=self.CKD_G4,
            frailty_sarcopenia=True,
            metabolically_unstable=True,
        )
        t = compute_targets(p, load_rules())
        assert "CKD-PRO-05" in t.targets["protein_g"].rule_ids
        assert t.max_of("protein_g") == pytest.approx(1.3 * 65)

    def test_nguoi_cao_tuoi_dtd_ckd_thi_hai_guideline_gap_nhau_mot_diem(self):
        """ADA 2026 đặt sàn 0,8 g/kg cho người cao tuổi ĐTĐ; KDIGO 2024 đặt trần 0,8.

        Dải rộng bằng 0 -> không thực đơn nào thoả. Hệ thống phải phát hiện và
        chuyển chuyên gia, KHÔNG tự chọn bên nào.
        """
        p = PatientProfile(
            **self.BASE,
            age=72,
            conditions=[
                Condition(code=ConditionCode.T2DM),
                Condition(code=ConditionCode.CKD, stage="G4"),
            ],
        )
        t = compute_targets(p, load_rules())

        assert "T2DM-PRO-02" in t.targets["protein_g"].rule_ids
        assert t.min_of("protein_g") == pytest.approx(t.max_of("protein_g"))
        assert t.needs_expert_review is True
        assert any("quá hẹp" in c for c in t.conflict_notes)

    def test_rule_theo_tuoi_khong_ap_cho_nguoi_tre(self):
        """T2DM-PRO-02 chỉ áp cho người cao tuổi (requires_flag=elderly)."""
        young = PatientProfile(**self.BASE, age=45, conditions=[Condition(code=ConditionCode.T2DM)])
        t = compute_targets(young, load_rules())
        assert "T2DM-PRO-02" not in t.applied_rule_ids

    def test_moi_rule_deu_dan_duoc_guideline_va_muc_bang_chung(self):
        for rule in load_rules():
            assert rule.guideline_ref, f"{rule.rule_id} thiếu guideline_ref"
            assert rule.guideline_grade, f"{rule.rule_id} thiếu guideline_grade"

    def test_khuyen_nghi_yeu_2c_khong_duoc_la_rang_buoc_cung(self):
        """Mức bằng chứng phải khớp severity: khuyến nghị yếu không nên chặn cứng."""
        for rule in load_rules():
            if rule.guideline_grade == "2C" and rule.rule_id.endswith("PRO-01"):
                assert rule.severity == "soft", f"{rule.rule_id} là khuyến nghị 2C (yếu) nhưng đang đặt severity=hard"


# ---------------------------------------------- đường tự do WHO (CLN-08)
class TestFreeSugarRule:
    FIXTURE_REF = "TEST-FIXTURE (dữ liệu giả)"

    def _t2dm(self) -> PatientProfile:
        return PatientProfile(
            patient_id="BN-SUG",
            age=50,
            sex=Sex.MALE,
            height_cm=165,
            weight_kg=65,
            conditions=[Condition(code=ConditionCode.T2DM)],
        )

    def _food(self, fid, name, kcal, carb, sugar):
        return FoodItem(
            id=fid,
            name_vi=name,
            kcal_100g=kcal,
            protein_g=1.0,
            carb_g=carb,
            fat_g=0.5,
            fiber_g=0.5,
            sugar_g=sugar,
            na_mg=1,
            k_mg=50,
            p_mg=30,
            purine_mg=10,
            source="curated",
            source_ref=self.FIXTURE_REF,
        )

    def test_t2dm_co_nguong_duong_tu_do(self):
        """WHO: đường tự do < 10% năng lượng → trần sugar_g = E * 0.10 / 4."""
        t = compute_targets(self._t2dm(), load_rules())
        assert "T2DM-SUG-01" in t.applied_rule_ids
        # kcal target = E*(1±10%) → suy ngược định mức năng lượng E rồi tính trần đường
        energy = t.targets["kcal"].max_value / 1.10
        assert t.max_of("sugar_g") == pytest.approx(energy * 0.10 / 4.0)

    def test_thua_duong_sinh_canh_bao_mem(self):
        rules = load_rules()
        repo = InMemoryFoodRepository(
            [self._food(1, "Chè đặc", 300, 60.0, 55.0)]  # 200 g → 110 g đường
        )
        menu = MenuDraft(items={MealSlot.SNACK: [MenuItem(food_id=1, grams=200)]})
        nutrition = compute_nutrition(menu, repo)
        assert nutrition.sugar_is_complete is True
        v = validate_menu(nutrition, compute_targets(self._t2dm(), rules), rules)
        sugar_over = [x for x in v if x.nutrient == "sugar_g" and x.kind == "over"]
        assert len(sugar_over) == 1
        assert sugar_over[0].severity is Severity.SOFT  # WHO strong nhưng đặt soft

    def test_thieu_so_lieu_duong_thi_canh_bao_incomplete(self):
        """Món thiếu sugar_g → không được coi là đạt ngưỡng đường."""
        rules = load_rules()
        repo = InMemoryFoodRepository(
            [
                self._food(1, "Có đường", 100, 20.0, 5.0),
                FoodItem(  # sugar_g=None
                    id=2,
                    name_vi="Chưa rõ đường",
                    kcal_100g=130,
                    protein_g=2.7,
                    carb_g=28.0,
                    fat_g=0.3,
                    fiber_g=0.4,
                    na_mg=1,
                    k_mg=35,
                    p_mg=43,
                    purine_mg=15,
                    source="curated",
                    source_ref=self.FIXTURE_REF,
                ),
            ]
        )
        menu = MenuDraft(items={MealSlot.LUNCH: [MenuItem(food_id=1, grams=100), MenuItem(food_id=2, grams=200)]})
        nutrition = compute_nutrition(menu, repo)
        assert nutrition.sugar_is_complete is False
        v = validate_menu(nutrition, compute_targets(self._t2dm(), rules), rules)
        incomplete = [x for x in v if x.kind == "incomplete_data"]
        assert len(incomplete) == 1
        assert incomplete[0].severity is Severity.SOFT
