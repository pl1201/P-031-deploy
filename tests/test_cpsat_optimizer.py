"""Test CPSATMenuOptimizer — AGT-09, AGT-10.

Trọng tâm: giải được bài toán thật trên dữ liệu seed thật (không mock), tổng
dinh dưỡng thực sự nằm trong định mức, và trả MenuDraft rỗng (không phải lỗi)
khi ràng buộc vô nghiệm — để route hiện có (route_after_validate) tự chuyển
sang fallback, đúng thiết kế graph.
"""

from __future__ import annotations

import pytest

from src.agents.nodes.core import USDA_BULK_ID_THRESHOLD
from src.agents.optimizer import CPSATMenuOptimizer
from src.clinical.models import (
    ActivityLevel,
    Condition,
    ConditionCode,
    DishCandidate,
    FoodItem,
    MealSlot,
    MenuDraft,
    MenuItem,
    PatientProfile,
    Sex,
)
from src.clinical.nutrition import compute_nutrition
from src.clinical.rules import compute_targets
from src.clinical.seeds import load_food_repository
from src.clinical.validator import validate_menu


@pytest.fixture(scope="module")
def foods():
    return load_food_repository()


@pytest.fixture(scope="module")
def menu_candidates(foods):
    """Ứng viên thật cho CP-SAT — khớp bộ lọc `retrieve_context` (DAT-12): loại
    khối USDA bulk (id ≥ `USDA_BULK_ID_THRESHOLD`), chỉ curated Việt Nam. Không
    dùng `foods.all()` trực tiếp cho CP-SAT trong test — ~7000 ứng viên (sau
    khi nhập USDA bulk) làm solver chậm 30-50 lần so với ~150 ứng viên curated.
    """
    return [f for f in foods.all() if f.id < USDA_BULK_ID_THRESHOLD]


def _profile(**overrides) -> PatientProfile:
    base = dict(
        patient_id="BN-CPSAT-01",
        age=58,
        sex=Sex.MALE,
        height_cm=165,
        weight_kg=70,
        activity_level=ActivityLevel.LIGHT,
        conditions=[Condition(code=ConditionCode.T2DM)],
    )
    base.update(overrides)
    return PatientProfile(**base)


def test_giai_duoc_thuc_don_kha_thi_tren_du_lieu_that(foods, menu_candidates):
    """Happy path: dữ liệu seed thật, định mức thật từ compute_targets()."""
    candidates = menu_candidates
    profile = _profile()
    targets = compute_targets(profile)

    draft = CPSATMenuOptimizer().generate(profile, targets, candidates, feedback=None)

    assert isinstance(draft, MenuDraft)
    all_items = draft.all_items()
    assert len(all_items) > 0, "phải tìm được lời giải trên tập ứng viên đầy đủ"

    # RULE-1: optimizer chỉ được sinh food_id + grams, không có field dinh dưỡng.
    # Món được chọn phải tồn tại thật trong repo (không bịa food_id).
    for item in all_items:
        assert item.grams > 0
        assert foods.get(item.food_id) is not None


# Các hồ sơ bên dưới đã được KIỂM CHỨNG: với bản làm tròn round() đối xứng cũ
# (VALUE_SCALE=10), mỗi hồ sơ cho ra thực đơn mà chính `validate_menu` gắn cờ
# vi phạm — tất cả đều rơi vào HARD rule (carb/xơ/béo/đường). Đây là test hồi
# quy thật: chạy trên bản cũ thì fail, trên bản đã sửa (làm tròn có hướng +
# biên bù round 2 chữ số) thì pass. (Quy trình tìm: quét không gian hồ sơ trên
# bản cũ, lọc đúng ca validate_menu trả violation.)
_AUDIT_PROFILES = [
    pytest.param(
        dict(age=45, sex=Sex.MALE, height_cm=155, weight_kg=60, conditions=[ConditionCode.T2DM]), id="carb-t2dm"
    ),
    pytest.param(
        dict(age=45, sex=Sex.MALE, height_cm=155, weight_kg=70, conditions=[ConditionCode.CKD]), id="fiber-ckd"
    ),
    pytest.param(dict(age=45, sex=Sex.MALE, height_cm=155, weight_kg=80, conditions=[]), id="fiber-none"),
    pytest.param(dict(age=45, sex=Sex.MALE, height_cm=160, weight_kg=60, conditions=[ConditionCode.HTN]), id="fat-htn"),
    pytest.param(
        dict(age=45, sex=Sex.MALE, height_cm=165, weight_kg=90, conditions=[ConditionCode.T2DM, ConditionCode.HTN]),
        id="sugar-t2dm+htn",
    ),
    pytest.param(
        dict(age=45, sex=Sex.MALE, height_cm=165, weight_kg=80, conditions=[ConditionCode.T2DM, ConditionCode.CKD]),
        id="carb-t2dm+ckd",
    ),
]


@pytest.mark.parametrize("spec", _AUDIT_PROFILES)
def test_thuc_don_thoa_validate_that(foods, menu_candidates, spec):
    """Thực đơn CP-SAT phải QUA được đúng `validate_menu` mà graph dùng.

    Đây là hợp đồng thật: `compute_nutrition` làm tròn tổng về 2 chữ số rồi
    `validate_menu` so với ngưỡng. Kiểm qua chính validator (không tự cộng/so
    lại) nên bắt được cả sai số làm tròn hệ số của model LẪN sai số làm tròn 2
    chữ số của summary — hai thứ mà audit độc lập chỉ ra bản cũ vi phạm.
    """
    fields = {k: v for k, v in spec.items() if k != "conditions"}
    conditions = [Condition(code=c) for c in spec["conditions"]]
    profile = _profile(conditions=conditions, **fields)
    targets = compute_targets(profile)

    draft = CPSATMenuOptimizer().generate(profile, targets, menu_candidates, feedback=None)
    assert draft.all_items(), "các hồ sơ này đều khả thi — phải có lời giải để kiểm tra ngưỡng"

    summary = compute_nutrition(draft, foods)
    violations = validate_menu(summary, targets)
    assert violations == [], f"thực đơn vi phạm ngưỡng: {[str(v) for v in violations]}"


def test_xep_du_bon_bua(menu_candidates):
    """Model ép MIN_ITEMS_PER_SLOT=1 cho cả 4 bữa → lời giải khả thi phải đủ 4 bữa.

    Assert đúng con số 4 (không phải '>=2' lỏng lẻo): nếu ai bỏ ràng buộc số món
    tối thiểu trên một bữa, bữa đó có thể rỗng và test này bắt được.
    """
    profile = _profile()
    targets = compute_targets(profile)

    draft = CPSATMenuOptimizer().generate(profile, targets, menu_candidates, feedback=None)

    assert len(draft.items) == 4, f"phải xếp món cho đủ 4 bữa, nhận {sorted(s.value for s in draft.items)}"
    for slot, items in draft.items.items():
        assert items, f"bữa {slot.value} bị rỗng"


def test_tra_menu_rong_khi_khong_co_ung_vien():
    """Không có ứng viên nào (VD lọc dị ứng loại hết) → MenuDraft rỗng, không lỗi."""
    profile = _profile()
    targets = compute_targets(profile)

    draft = CPSATMenuOptimizer().generate(profile, targets, candidates=[], feedback=None)

    assert isinstance(draft, MenuDraft)
    assert draft.all_items() == []


def test_tra_menu_rong_khi_khong_co_muc_tieu_kha_thi(foods):
    """Ứng viên chỉ có món cực ít calo nhưng định mức đòi calo rất cao → infeasible."""
    # Lọc ra vài món ít kcal nhất — không đủ để chạm định mức năng lượng cả ngày dù
    # chọn hết mức cho phép (MAX_GRAMS_PER_ITEM x MAX_ITEMS_PER_SLOT).
    low_kcal_candidates = sorted(foods.all(), key=lambda f: f.kcal_100g)[:2]
    profile = _profile()
    targets = compute_targets(profile)

    draft = CPSATMenuOptimizer().generate(profile, targets, low_kcal_candidates, feedback=None)

    assert isinstance(draft, MenuDraft)
    assert draft.all_items() == []


def test_rang_buoc_purine_loai_mon_thieu_du_lieu(foods):
    """RULE-2/DEC-008: có ngưỡng purine thì món thiếu purine_mg phải bị loại,
    KHÔNG được coi None = 0 (sẽ chọn nhầm món không rõ purine cho bệnh nhân gout).
    """
    from src.agents.optimizer import _eligible_candidates

    all_foods = foods.all()
    have_purine = [f for f in all_foods if f.purine_mg is not None]
    missing_purine = [f for f in all_foods if f.purine_mg is None]
    assert missing_purine, "seed cần có ít nhất vài món chưa có purine để test có nghĩa"

    # Có ràng buộc purine → mọi món thiếu purine_mg bị loại.
    with_purine_bound = _eligible_candidates(all_foods, {"purine_mg": (None, 400.0)})
    assert {f.id for f in with_purine_bound} == {f.id for f in have_purine}
    assert all(f.purine_mg is not None for f in with_purine_bound)

    # Không có ràng buộc purine → không loại vì thiếu purine.
    no_purine_bound = _eligible_candidates(all_foods, {"na_mg": (None, 2000.0)})
    assert {f.id for f in no_purine_bound} == {f.id for f in all_foods}


def test_narrow_energy_siet_dung_dai_quanh_diem_giua():
    """Pha 1 phải siết kcal vào dải ±ENERGY_AIM_BAND quanh điểm giữa, không đụng
    chất khác; và trả None khi kcal chỉ có một phía (không có điểm giữa)."""
    from src.agents.optimizer import ENERGY_AIM_BAND, _narrow_energy

    narrowed = _narrow_energy({"kcal_100g": (1000.0, 2000.0), "na_mg": (None, 2000.0)})
    assert narrowed is not None
    lo, hi = narrowed["kcal_100g"]
    mid = 1500.0
    assert lo == pytest.approx(mid * (1 - ENERGY_AIM_BAND))
    assert hi == pytest.approx(mid * (1 + ENERGY_AIM_BAND))
    assert narrowed["na_mg"] == (None, 2000.0), "chỉ được siết kcal, không đụng chất khác"

    # kcal chỉ có trần (không có sàn) → không xác định được điểm giữa → None.
    assert _narrow_energy({"kcal_100g": (None, 2000.0)}) is None
    assert _narrow_energy({"na_mg": (None, 2000.0)}) is None


def test_pha_2_duoc_goi_khi_pha_1_vo_nghiem(foods, monkeypatch):
    """Hai pha: nếu pha 1 (dải hẹp) vô nghiệm, pha 2 (khoảng gốc) PHẢI được thử.

    Ép `_try_solve` trả None ở lần gọi đầu (pha 1) và một draft ở lần sau (pha
    2), rồi xác nhận `_solve_day` trả draft đó. Nếu ai xoá pha 2, lần gọi thứ
    hai không xảy ra và hàm trả rỗng → test fail.
    """
    import src.agents.optimizer as opt

    profile = _profile()
    targets = compute_targets(profile)
    sentinel = MenuDraft(items={list(opt._SLOTS)[0]: []})  # draft phân biệt được
    calls: list[dict] = []

    def fake_try_solve(eligible, bounds, dish_totals=None):
        calls.append(bounds)
        return None if len(calls) == 1 else sentinel

    monkeypatch.setattr(opt, "_try_solve", fake_try_solve)
    result = opt._solve_day(foods.all(), targets)

    assert len(calls) == 2, "pha 1 vô nghiệm thì phải gọi pha 2"
    assert result is sentinel
    # Pha 1 dùng bounds đã siết kcal, pha 2 dùng bounds gốc (trần kcal rộng hơn).
    assert calls[0]["kcal_100g"][1] < calls[1]["kcal_100g"][1]


# --------------------------------------------------------------------------
# Trần gram/ngày mỗi nguyên liệu (bug audit 2026-08-07, xem DEVLOG)
# --------------------------------------------------------------------------


def test_khong_nguyen_lieu_nao_vuot_tran_gram_moi_ngay(menu_candidates):
    """Trước khi sửa: CP-SAT có thể chọn cùng 1 nguyên liệu ở cả 4 bữa (VD
    gừng 300g×4=1200g/ngày) — hợp lệ toán ràng buộc nhưng vô lý lâm sàng/ẩm
    thực. Test trên dữ liệu thật (~150 ứng viên curated), không mock."""
    import src.agents.optimizer as opt

    profile = _profile()
    targets = compute_targets(profile)

    draft = CPSATMenuOptimizer().generate(profile, targets, menu_candidates, feedback=None)
    totals: dict[int, float] = {}
    for item in draft.all_items():
        totals[item.food_id] = totals.get(item.food_id, 0.0) + item.grams
    assert totals, "cần có lời giải thật để kiểm tra trần"
    for food_id, grams in totals.items():
        assert grams <= opt.MAX_GRAMS_PER_FOOD_PER_DAY, (
            f"food_id={food_id} có {grams} g/ngày, vượt trần {opt.MAX_GRAMS_PER_FOOD_PER_DAY} g "
            "— đúng bug đã audit (gừng 300g×4 bữa)"
        )


def test_tran_gram_ngay_thuc_su_duoc_ap_vao_model(menu_candidates):
    """Hạ trần xuống rất thấp (50 g) — nếu ràng buộc thực sự nằm trong model
    CP-SAT (không phải lọc hậu kỳ), solver phải tự tìm cách khác (dùng nhiều
    nguyên liệu hơn thay vì lặp lại) hoặc báo vô nghiệm; không bao giờ trả về
    một food_id vượt 50 g/ngày."""
    import src.agents.optimizer as opt

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(opt, "MAX_GRAMS_PER_FOOD_PER_DAY", 50)
        profile = _profile()
        targets = compute_targets(profile)
        draft = opt.CPSATMenuOptimizer().generate(profile, targets, menu_candidates, feedback=None)

    totals: dict[int, float] = {}
    for item in draft.all_items():
        totals[item.food_id] = totals.get(item.food_id, 0.0) + item.grams
    for food_id, grams in totals.items():
        assert grams <= 50, f"food_id={food_id} có {grams} g — trần 50g đã ép không có hiệu lực trong model"


# --------------------------------------------------------------------------
# Món ăn hoàn chỉnh (DishCandidate) làm khung — hybrid dish + nguyên liệu thô
# --------------------------------------------------------------------------


def _dish(dish_id: str, name_vi: str, ingredients: list[MenuItem]) -> DishCandidate:
    return DishCandidate(dish_id=dish_id, name_vi=name_vi, is_reviewed=False, ingredients=ingredients)


def test_loader_loai_bo_bua_mau_khoi_catalog_mon():
    from src.clinical.seeds import load_vn_dishes

    dishes = load_vn_dishes()
    assert dishes
    assert all(not dish.dish_id.upper().startswith("MENU-") for dish in dishes)
    assert all(not dish.name_vi.lower().startswith(("bữa sáng", "bữa trưa", "bữa tối")) for dish in dishes)


def test_t2dm_van_co_mon_cu_the_khi_du_lieu_duong_chua_day_du(foods):
    """Thiếu sugar_g là cảnh báo dữ liệu, không được làm catalog món thành rỗng."""
    from src.clinical.seeds import load_vn_dishes

    profile = _profile(conditions=[Condition(code=ConditionCode.T2DM)])
    targets = compute_targets(profile)
    candidates = [food for food in foods.all() if food.id < USDA_BULK_ID_THRESHOLD]

    draft = CPSATMenuOptimizer(dishes=load_vn_dishes(), foods=foods).generate(
        profile, targets, candidates, feedback=None
    )

    assert set(draft.planned_dishes) == set(MealSlot)
    assert all(len(draft.planned_dishes[slot]) == 1 for slot in MealSlot)


def test_gia_vi_va_hat_co_tran_khau_phan_nho(foods):
    from src.agents.optimizer import _max_grams_per_day, _max_grams_per_slot

    spice = foods.all()[0].model_copy(update={"category": "gia vị"})
    nut = foods.all()[0].model_copy(update={"category": "hạt"})
    assert _max_grams_per_slot(spice) == 25
    assert _max_grams_per_day(spice) == 50
    assert _max_grams_per_slot(nut) == 50
    assert _max_grams_per_day(nut) == 100


def test_mon_hoan_chinh_duoc_chon_nguyen_ca_cong_thuc(foods):
    """Khi optimizer chọn một `DishCandidate`, TOÀN BỘ nguyên liệu của món phải
    xuất hiện trong draft — không được chọn nửa công thức."""
    # Cơm tẻ (2) + Rau muống (65) + Đậu phụ (55) — id thật trong seed, dùng làm
    # "món" tự chế để test không phụ thuộc nội dung dishes.csv có thể đổi.
    dish = _dish(
        "TEST-COM-RAU-DAUPHU",
        "Cơm rau đậu phụ (test)",
        [MenuItem(food_id=2, grams=150), MenuItem(food_id=65, grams=100), MenuItem(food_id=55, grams=80)],
    )

    profile = _profile()
    targets = compute_targets(profile)
    candidates = [f for f in foods.all() if f.id < USDA_BULK_ID_THRESHOLD]

    draft = CPSATMenuOptimizer(dishes=[dish], foods=foods).generate(profile, targets, candidates, feedback=None)
    assert draft.all_items(), "phải giải được với cả nguyên liệu thô lẫn 1 món hoàn chỉnh làm ứng viên"

    all_food_ids = {item.food_id for item in draft.all_items()}
    dish_food_ids = {ing.food_id for ing in dish.ingredients}
    # Nếu món được chọn ở BẤT KỲ bữa nào, cả 3 nguyên liệu phải có mặt cùng nhau.
    if dish_food_ids & all_food_ids:
        assert dish_food_ids <= all_food_ids, "món hoàn chỉnh bị chọn nửa vời — vi phạm tính toàn vẹn công thức"


def test_mon_co_di_ung_bi_loai_khoi_ung_vien(foods):
    """Món chứa nguyên liệu dị ứng của bệnh nhân phải bị loại hoàn toàn, không
    bao giờ được optimizer chọn (RULE R10.6 — dị ứng là ràng buộc cứng)."""
    from src.clinical.nutrition import InMemoryFoodRepository

    peanut_food = FoodItem(
        id=999001,
        name_vi="Lạc rang (test)",
        kcal_100g=567.0,
        protein_g=25.0,
        carb_g=16.0,
        fat_g=49.0,
        fiber_g=8.0,
        na_mg=5.0,
        k_mg=700.0,
        p_mg=380.0,
        contains_allergens=["đậu phộng"],
        source="curated",
        source_ref="test",
    )
    fake_foods = InMemoryFoodRepository([*foods.all(), peanut_food])
    dish = _dish("TEST-MON-DI-UNG", "Món có lạc (test)", [MenuItem(food_id=999001, grams=50)])

    profile = _profile(allergies=["đậu phộng"])
    eligible = _eligible_dishes_for_test(dishes=[dish], fake_foods=fake_foods, profile=profile)
    assert eligible == [], "món có nguyên liệu dị ứng phải bị loại khỏi candidate ngay từ đầu"


def _eligible_dishes_for_test(dishes, fake_foods, profile):
    from src.agents.optimizer import _eligible_dishes

    return _eligible_dishes(dishes, fake_foods, profile)


def test_mon_bi_dislike_bi_loai_khoi_ung_vien(foods):
    """Món trùng tên với `dislikes` của bệnh nhân phải bị loại — cùng cơ chế
    lọc dislike đã áp cho nguyên liệu thô ở `retrieve_context`."""
    dish = _dish("TEST-MON-GHET", "Món test không thích", [MenuItem(food_id=2, grams=100)])
    profile = _profile(dislikes=["món test không thích"])

    eligible = _eligible_dishes_for_test(dishes=[dish], fake_foods=foods, profile=profile)
    assert eligible == [], "món trùng dislikes phải bị loại khỏi candidate"
