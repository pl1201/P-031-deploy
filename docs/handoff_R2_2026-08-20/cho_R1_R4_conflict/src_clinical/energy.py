"""Tính năng lượng: BMR, TDEE, cân nặng lý tưởng.

LLM: NO — deterministic hoàn toàn.
Ticket: CLN-01, CLN-09

Công thức MẶC ĐỊNH (đổi 2026-08-06, quyết định của Hưng — "ưu tiên dùng từ
bản Excel, kể cả BMR và ActivityLevel", sau khi đã research bằng chứng về
BMR theo dân tộc/quần thể/bệnh lý — xem CLN-09 trong `docs/TICKETS.md` và
DEVLOG.md cùng ngày để biết đầy đủ trích dẫn/giới hạn bằng chứng):
  - BMR: **WHO/FAO/UNU (1985)**, đúng công thức chuyên gia dinh dưỡng dự án
    dùng thật trên Excel (`data/Bảng xác định nhu cầu dinh dưỡng + thực
    đơn.xlsx`, sheet "Bước 1+2", Bảng 1) — tuyến tính theo (nhóm tuổi × giới
    × cân nặng), KHÔNG có số hạng chiều cao.
  - PAL (hệ số lao động): Bảng 2 cùng file — 4 mức nhẹ/trung bình/nặng/rất
    nặng, khớp `ActivityLevel`.
  - IBW: BMI 22 (mức giữa khoảng bình thường của WHO cho người châu Á) — giữ
    nguyên, không đổi theo quyết định này.
  - Cân nặng hiệu chỉnh khi béo phì: ABW = IBW + 0.25*(W - IBW), dùng khi
    BMI >= 30. Excel gốc KHÔNG mô hình hoá bước này (chỉ dùng cân nặng thô ở
    Bảng 1), nhưng đây là ràng buộc an toàn lâm sàng riêng (tránh ước tính
    vượt nhu cầu thật ở bệnh nhân béo phì) — CỐ Ý giữ lại, không phải một
    phần "công thức BMR" nên không mâu thuẫn với quyết định ưu tiên Excel.

⚠️ Giới hạn bằng chứng (đọc trước khi đổi tiếp): research 2026-08-06 KHÔNG
tìm được nghiên cứu đo BMR trực tiếp trên người Việt Nam, và bằng chứng quốc
tế về công thức nào "đúng hơn" theo quần thể là TRÁI CHIỀU (không nhất quán).
Quyết định dùng WHO/FAO/UNU dựa trên: đây là công thức chuyên gia dinh dưỡng
DỰ ÁN đang dùng thật (nguồn thực hành trực tiếp, ưu tiên cao hơn tài liệu
quốc tế chưa xác nhận áp dụng được cho người Việt) — KHÔNG phải vì có bằng
chứng học thuật chứng minh WHO/FAO/UNU chính xác hơn Mifflin-St Jeor cho
người Việt. `bmr_mifflin_st_jeor()`/`compute_tdee_mifflin()` vẫn giữ lại làm
THAM KHẢO/so sánh, KHÔNG còn là mặc định.

⚠️ Ngưỡng năng lượng tối thiểu là ràng buộc an toàn, không phải tuỳ chọn:
không bao giờ trả về mục tiêu dưới 1200 kcal (nữ) / 1500 kcal (nam) khi giảm cân.
"""

from __future__ import annotations

from .models import ActivityLevel, ConditionCode, PatientProfile, Sex, WeightGoal

MIN_KCAL_FEMALE = 1200.0
MIN_KCAL_MALE = 1500.0
OBESITY_BMI = 30.0
GOAL_DELTA_KCAL: dict[WeightGoal, float] = {
    WeightGoal.LOSE: -500.0,
    WeightGoal.MAINTAIN: 0.0,
    WeightGoal.GAIN: +400.0,
}


def ideal_body_weight_kg(height_cm: float) -> float:
    """Cân nặng lý tưởng theo BMI 22."""
    return 22.0 * (height_cm / 100.0) ** 2


def adjusted_body_weight_kg(weight_kg: float, height_cm: float) -> float:
    """Cân nặng dùng để tính nhu cầu.

    Trả về cân nặng thật nếu BMI < 30, ngược lại trả về cân nặng hiệu chỉnh.
    Đây cũng là cân nặng dùng cho định mức protein g/kg ở bệnh nhân CKD.
    """
    bmi = weight_kg / (height_cm / 100.0) ** 2
    if bmi < OBESITY_BMI:
        return weight_kg
    ibw = ideal_body_weight_kg(height_cm)
    return ibw + 0.25 * (weight_kg - ibw)


# --------------------------------------------------------------------------
# WHO/FAO/UNU (1985) — MẶC ĐỊNH từ 2026-08-06. Công thức thật chuyên gia
# dinh dưỡng dự án đang dùng trên Excel (xem docstring đầu file).
# --------------------------------------------------------------------------

# (hệ số W, hằng số cộng) theo (nhóm tuổi, giới) — trích nguyên văn "Bảng 1"
# trong file Excel chuyên gia. Nhóm tuổi lấy cận trên (age <= cận trên).
_WHO_FAO_BMR_TABLE: list[tuple[int, float, float, float, float]] = [
    # (tuổi tối đa của nhóm, hệ số nam, hằng số nam, hệ số nữ, hằng số nữ)
    (3, 60.9, -54.0, 61.0, -51.0),
    (10, 22.7, 495.0, 22.5, 499.0),
    (18, 17.5, 651.0, 12.2, 746.0),
    (30, 15.3, 679.0, 14.7, 496.0),
    (60, 11.6, 879.0, 8.7, 829.0),
]
_WHO_FAO_BMR_ELDERLY = (13.5, 487.0, 10.5, 596.0)  # >60 tuổi


def bmr_who_fao_unu(weight_kg: float, age: int, sex: Sex) -> float:
    """BMR theo công thức WHO/FAO/UNU (1985), phân theo nhóm tuổi — dùng cân
    nặng, KHÔNG dùng chiều cao (khác Mifflin-St Jeor). Đây là công thức thật
    trong file Excel chuyên gia dinh dưỡng dự án dùng (`Bước 1+2!I5:J10`).
    """
    for age_max, coef_m, const_m, coef_f, const_f in _WHO_FAO_BMR_TABLE:
        if age <= age_max:
            coef, const = (coef_m, const_m) if sex is Sex.MALE else (coef_f, const_f)
            return coef * weight_kg + const
    coef_m, const_m, coef_f, const_f = _WHO_FAO_BMR_ELDERLY
    coef, const = (coef_m, const_m) if sex is Sex.MALE else (coef_f, const_f)
    return coef * weight_kg + const


# Hệ số lao động (PAL) theo (mức lao động, giới) — "Bảng 2" trong Excel chuyên
# gia dinh dưỡng dự án (`Bước 1+2!H12:J17`). `ActivityLevel` đã đổi sang đúng
# 4 nhãn/4 mức này (LIGHT/MODERATE/HEAVY/VERY_HEAVY) nên khớp thẳng 1:1.
_PAL_WHO_FAO: dict[ActivityLevel, tuple[float, float]] = {  # (nam, nữ)
    ActivityLevel.LIGHT: (1.6, 1.5),  # "Lao động nhẹ"
    ActivityLevel.MODERATE: (1.7, 1.6),  # "Lao động trung bình"
    ActivityLevel.HEAVY: (2.1, 1.9),  # "Lao động nặng"
    ActivityLevel.VERY_HEAVY: (2.4, 2.2),  # "Lao động rất nặng"
}


def pal_who_fao(level: ActivityLevel, sex: Sex) -> float:
    """Hệ số chuyển hoá cơ sở (PAL) theo Bảng 2 Excel chuyên gia."""
    coef_m, coef_f = _PAL_WHO_FAO[level]
    return coef_m if sex is Sex.MALE else coef_f


def compute_bmr(profile: PatientProfile) -> float:
    """BMR mặc định của hệ thống — WHO/FAO/UNU, dùng cân nặng ĐÃ hiệu chỉnh
    béo phì (an toàn lâm sàng, xem `adjusted_body_weight_kg`)."""
    weight = adjusted_body_weight_kg(profile.weight_kg, profile.height_cm)
    return bmr_who_fao_unu(weight, profile.age, profile.sex)


def compute_tdee(profile: PatientProfile) -> float:
    return compute_bmr(profile) * pal_who_fao(profile.activity_level, profile.sex)


QD5481_KCAL_PER_KG_IBW_MIN = 20.0
QD5481_KCAL_PER_KG_IBW_MAX = 30.0
QD5481_ENERGY_RULE_ID = "T2DM-ENERGY-QD5481"
QD5481_ENERGY_REF = (
    "Bộ Y tế, QĐ 5481/QĐ-BYT ngày 30/12/2020 'Hướng dẫn chẩn đoán và điều trị đái tháo đường "
    "típ 2', phần Dinh dưỡng: 'Có thể khởi đầu với mức năng lượng 20-30 kcal/kg cân nặng lý "
    "tưởng/ngày'; giảm cân ở thừa cân/béo phì trừ 250-500 kcal/ngày"
)


def qd5481_energy_band_kcal(height_cm: float) -> tuple[float, float]:
    """Dải năng lượng khởi đầu cho bệnh nhân ĐTĐ típ 2 theo QĐ 5481/QĐ-BYT.

    Tính trên CÂN NẶNG LÝ TƯỞNG (BMI 22), không phải cân nặng thực — đúng câu
    chữ phác đồ ("kcal/kg cân nặng lý tưởng/ngày").
    """
    ibw = ideal_body_weight_kg(height_cm)
    return QD5481_KCAL_PER_KG_IBW_MIN * ibw, QD5481_KCAL_PER_KG_IBW_MAX * ibw


# --------------------------------------------------------------------------
# Bảng nhu cầu năng lượng theo GIỚI × MỨC LAO ĐỘNG — hội thảo t-DNA/DSF 16/08/2026
#
# R2 CHỐT 2026-08-18: thay cách kẹp cứng vào dải QĐ 5481 bằng ĐỊNH VỊ theo bảng
# này. Lý do đo được (2.021 hồ sơ bệnh nhân thật):
#
#   * Cách cũ xoá sạch cá nhân hoá: 95/96 hồ sơ cùng chiều cao, giữ cân nhận
#     ĐÚNG một mức kcal dù cân 45-95 kg và lao động nhẹ đến rất nặng. Nguyên
#     nhân: trần QĐ 5481 tính trên cân nặng LÝ TƯỞNG (chỉ suy từ chiều cao), mà
#     phần lớn TDEE vượt trần nên bị dồn hết về trần.
#   * Áp bảng này KHÔNG phải nới lỏng đại trà — dân số thật gồm 54% lao động
#     nhẹ và 66% nữ, đúng nhóm bảng hội thảo SIẾT xuống (25 thay vì 30
#     kcal/kg). Đo thật: 35,0% hồ sơ chặt hơn trước, 39,9% không đổi, 23,4%
#     vượt trần QĐ 5481 cũ, 1,7% nới nhẹ. Chênh lệch TRUNG VỊ = 0 kcal.
#   * Cho ăn THIẾU cũng là rủi ro, không phải mặc định an toàn: ca lâm sàng 3
#     của chính hội thảo có HbA1c 9,1% nhưng glucose đói 3,6 mmol/L — hạ đường
#     huyết ở bệnh nhân dùng insulin/sulfonylurea (HR tử vong 1,8).
#
# Vì sao dùng được dù hội thảo bị xếp 🔴 KHÔNG ingest vào `guideline_chunks`:
# xung đột lợi ích (Glucerna/Abbott, grade C-D/LOE 3-4) chỉ thuộc phần DSF.
# Bảng này ở phần MNT — PGS.TS.BS Nguyễn Trọng Hưng, BV Nội tiết TW.
#
# ⚠️ `VERY_HEAVY` KHÔNG có trong bảng gốc (bảng chỉ tới "lao động nặng"). Tạm
# dùng chung mức HEAVY thay vì ngoại suy lên cao hơn — không hồ sơ thật nào
# hiện ở mức này (0/2.021), nên chưa cần R2 quyết gấp; nếu sau này có bệnh nhân
# lao động rất nặng thì phải hỏi R2 trước, không tự nâng số.
# --------------------------------------------------------------------------
TDNA_ENERGY_RULE_ID = "T2DM-ENERGY-TDNA-2026"
TDNA_ENERGY_REF = (
    "Hội thảo t-DNA/DSF 16/08/2026 (PGS.TS.BS Nguyễn Trọng Hưng, BV Nội tiết TW), Bước 2 "
    "'Nhu cầu năng lượng theo mức lao động': lao động nhẹ 30 (nam)/25 (nữ), trung bình 35/30, "
    "nặng 45/40 kcal/kg cân nặng lý tưởng/ngày. R2 chốt 2026-08-18 thay cách kẹp cứng dải "
    "QĐ 5481 (20-30 kcal/kg IBW) vốn xoá mất khác biệt theo giới và mức lao động. "
    "QĐ 5481 vẫn là căn cứ cho mọi ngưỡng ĐTĐ2 khác và cho chính khái niệm cân nặng lý tưởng; "
    "phác đồ ghi 20-30 là mức KHỞI ĐẦU điều trị, không phải trần sinh lý tuyệt đối"
)

#: kcal/kg cân nặng LÝ TƯỞNG theo (nam, nữ).
_TDNA_KCAL_PER_KG_IBW: dict[ActivityLevel, tuple[float, float]] = {
    ActivityLevel.LIGHT: (30.0, 25.0),
    ActivityLevel.MODERATE: (35.0, 30.0),
    ActivityLevel.HEAVY: (45.0, 40.0),
    ActivityLevel.VERY_HEAVY: (45.0, 40.0),  # không có trong bảng gốc — xem ghi chú trên
}


def tdna_energy_kcal(height_cm: float, sex: Sex, activity_level: ActivityLevel) -> float:
    """Nhu cầu năng lượng theo bảng hội thảo t-DNA, tính trên cân nặng lý tưởng."""
    nam, nu = _TDNA_KCAL_PER_KG_IBW[activity_level]
    return ideal_body_weight_kg(height_cm) * (nam if sex is Sex.MALE else nu)


KDOQI_KCAL_PER_KG_IBW_MIN = 25.0
KDOQI_KCAL_PER_KG_IBW_MAX = 35.0
KDOQI_ENERGY_RULE_ID = "CKD-ENERGY-KDOQI"
KDOQI_ENERGY_REF = (
    "KDOQI Clinical Practice Guideline for Nutrition in CKD: 2020 Update, khuyến cáo năng "
    "lượng 25-35 kcal/kg/ngày cho người lớn CKD G3-G5 (kể cả lọc máu), điều chỉnh theo tuổi, "
    "giới, mức hoạt động và tình trạng dinh dưỡng"
)


def kdoqi_energy_band_kcal(height_cm: float) -> tuple[float, float]:
    """Dải năng lượng cho bệnh nhân CKD theo KDOQI 2020.

    Dùng cân nặng LÝ TƯỞNG như dải QĐ 5481 để hai mốc so được với nhau, và vì
    KDOQI cũng khuyến cáo tính trên cân nặng lý tưởng/hiệu chỉnh chứ không phải
    cân nặng thực ở người thừa cân hoặc phù.
    """
    ibw = ideal_body_weight_kg(height_cm)
    return KDOQI_KCAL_PER_KG_IBW_MIN * ibw, KDOQI_KCAL_PER_KG_IBW_MAX * ibw


def _has_t2dm(profile: PatientProfile) -> bool:
    return any(c.code is ConditionCode.T2DM for c in profile.conditions)


def _has_ckd(profile: PatientProfile) -> bool:
    return any(c.code is ConditionCode.CKD for c in profile.conditions)


def compute_energy_target_kcal(profile: PatientProfile) -> float:
    """TDEE điều chỉnh theo mục tiêu cân nặng, kẹp theo phác đồ ĐTĐ2, có sàn an toàn.

    Với hồ sơ ĐTĐ típ 2, mục tiêu năng lượng được kẹp vào dải 20-30 kcal/kg cân
    nặng lý tưởng của QĐ 5481/QĐ-BYT (DEC-024, R2 chốt 2026-08-15).

    Vì sao phải kẹp thay vì thêm rule vào `clinical_rules.csv`: `compute_targets()`
    dựng dải kcal từ chính giá trị này (energy ± 10%) TRƯỚC khi hợp nhất rule, nên
    một rule trần 30 kcal/kg IBW sẽ cho `min > max` và đẩy MỌI hồ sơ ĐTĐ2 sang
    `needs_expert_review` — chặn hệ thống chứ không sửa được sai lệch.

    Đo trước khi sửa (nam 58t, 165cm, 65kg, lao động nhẹ): TDEE cho ra 39-48
    kcal/kg IBW ở chế độ giữ cân và 32-39 ở chế độ giảm cân — tức ngay cả khi
    giảm cân, SÀN của dự án vẫn cao hơn TRẦN của phác đồ. Đây là lý do gốc khiến
    thực đơn ĐTĐ do Viện Dinh dưỡng công bố (1.210-1.277 kcal) lệch hẳn so với
    định mức hệ thống tự tính (~2.600 kcal).

    ⚠️ Đọc kỹ trước khi đổi: phác đồ ghi "có thể KHỞI ĐẦU với mức 20-30
    kcal/kg" — đây là mức kê điều trị lúc bắt đầu, không phải trần sinh lý tuyệt
    đối. Bệnh nhân lao động nặng thật sự có thể cần hơn; khi đó là quyết định
    lâm sàng của chuyên gia, không phải việc nới hằng số ở đây.

    Sàn an toàn tuyệt đối (1200 nữ / 1500 nam) vẫn được áp SAU CÙNG, nên với
    người thấp bé mà cận dưới 20 kcal/kg rơi xuống dưới sàn thì sàn vẫn thắng.
    """
    target = compute_tdee(profile) + GOAL_DELTA_KCAL[profile.weight_goal]
    if _has_t2dm(profile):
        # R2 CHỐT 2026-08-18: ĐỊNH VỊ theo bảng t-DNA (giới x mức lao động) thay
        # vì kẹp cứng vào dải QĐ 5481. Xem khối ghi chú ở `TDNA_ENERGY_RULE_ID`
        # để biết số đo trên 2.021 hồ sơ thật và lý do đổi.
        #
        # Đây KHÔNG phải "nới trần": 35,0% hồ sơ thật nhận mức CHẶT HƠN trước
        # (dân số 54% lao động nhẹ, 66% nữ — nhóm bảng t-DNA siết xuống 25
        # kcal/kg), 39,9% không đổi, chênh lệch trung vị 0 kcal.
        #
        # Mục tiêu giảm cân vẫn trừ `GOAL_DELTA_KCAL` như cũ, và sàn an toàn
        # tuyệt đối phía dưới vẫn thắng.
        target = tdna_energy_kcal(profile.height_cm, profile.sex, profile.activity_level)
        target += GOAL_DELTA_KCAL[profile.weight_goal]
        if _has_ckd(profile):
            # DEC-007: đồng mắc thì lấy ngưỡng CHẶT HƠN. Trước 18/08 nhánh này
            # không cần thiết vì trần QĐ 5481 (30 kcal/kg IBW) luôn thấp hơn
            # trần KDOQI (35), nên đi đường T2DM đã tự khắc chặt hơn.
            #
            # Bảng t-DNA nới cận trên lên 45 kcal/kg nên điều đó KHÔNG còn đúng:
            # đo được ca nam 178,7 cm lao động nặng, T2DM + CKD G5 nhận 3.161
            # kcal = 45 kcal/kg, vượt 28% trần KDOQI 2.459 kcal. Với bệnh nhân
            # suy thận, nạp năng lượng vượt guideline thận không phải chuyện nhỏ.
            _, kdoqi_max = kdoqi_energy_band_kcal(profile.height_cm)
            target = min(target, kdoqi_max)
    elif _has_ckd(profile):
        # CKD KHÔNG đồng mắc ĐTĐ2: kẹp theo KDOQI 2020 (DEC-033, R2 chốt
        # 2026-08-15). Không dùng dải QĐ 5481 vì đó là phác đồ ĐTĐ típ 2 — cùng
        # lý do đã ghi ở DEC-024, không lặng lẽ áp phác đồ bệnh này cho bệnh kia.
        #
        # Đo trước khi sửa (bộ 60 ca, nhóm CKD+HTN): hệ thống ra 2.420-2.958
        # kcal trong khi oracle theo chuẩn quốc tế ra 1.838-2.246 — đúng hiện
        # tượng đã sửa cho ĐTĐ2 ở DEC-024, nhưng ở nhóm chưa ai kẹp. 2.958 kcal
        # cho một bệnh nhân CKD là mức không có guideline nào đỡ.
        #
        # Dải KDOQI (25-35) RỘNG HƠN QĐ 5481 (20-30) là có chủ đích của guideline:
        # bệnh nhân CKD hạn chế đạm cần đủ năng lượng từ nguồn khác để không đốt
        # cơ, nên sàn năng lượng cao hơn. Ca CKD + ĐTĐ2 đồng mắc vẫn đi nhánh
        # trên (QĐ 5481, chặt hơn) — lấy ngưỡng chặt hơn khi đa bệnh lý, đúng
        # nguyên tắc DEC-007.
        lo, hi = kdoqi_energy_band_kcal(profile.height_cm)
        target = min(max(target, lo), hi)
    floor = MIN_KCAL_MALE if profile.sex is Sex.MALE else MIN_KCAL_FEMALE
    return max(target, floor)


def kcal_per_kg(profile: PatientProfile) -> float:
    """Kiểm tra chéo: bệnh nhân mãn tính ổn định thường nằm trong 30–35 kcal/kg/ngày."""
    return compute_energy_target_kcal(profile) / profile.weight_kg


# --------------------------------------------------------------------------
# Mifflin-St Jeor (1990) — THAM KHẢO/so sánh từ 2026-08-06 (không còn mặc
# định). Vẫn đúng công thức, chỉ đổi vai trò.
# --------------------------------------------------------------------------

_ACTIVITY_FACTOR_MIFFLIN: dict[ActivityLevel, float] = {
    # Quy ước phổ biến trong công cụ tính calo trực tuyến — KHÔNG truy được
    # về 1 nguồn học thuật/lâm sàng đơn nhất (không phải từ bài Mifflin-St
    # Jeor 1990 gốc, cũng không phải IOM/NAM DRI 2005 — xem research CLN-09).
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.HEAVY: 1.725,
    ActivityLevel.VERY_HEAVY: 1.9,
}


def bmr_mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
    """Nam:  10*W + 6.25*H - 5*A + 5 · Nữ: 10*W + 6.25*H - 5*A - 161."""
    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age
    return base + 5.0 if sex is Sex.MALE else base - 161.0


def compute_bmr_mifflin(profile: PatientProfile) -> float:
    weight = adjusted_body_weight_kg(profile.weight_kg, profile.height_cm)
    return bmr_mifflin_st_jeor(weight, profile.height_cm, profile.age, profile.sex)


def compute_tdee_mifflin(profile: PatientProfile) -> float:
    """TDEE theo Mifflin-St Jeor — hàm THAM KHẢO/so sánh, không dùng trong
    `compute_targets()`. Xem `_ACTIVITY_FACTOR_MIFFLIN` về giới hạn nguồn."""
    return compute_bmr_mifflin(profile) * _ACTIVITY_FACTOR_MIFFLIN[profile.activity_level]


def compute_tdee_who_fao(profile: PatientProfile) -> float:
    """TDEE theo WHO/FAO/UNU dùng cân nặng THÔ (khớp đúng cách Excel chuyên
    gia tính — không hiệu chỉnh béo phì), khác `compute_tdee()` (mặc định hệ
    thống, có hiệu chỉnh béo phì). Dùng để đối chiếu/so sánh."""
    bmr = bmr_who_fao_unu(profile.weight_kg, profile.age, profile.sex)
    return bmr * pal_who_fao(profile.activity_level, profile.sex)
