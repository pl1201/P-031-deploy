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

from .models import ActivityLevel, PatientProfile, Sex, WeightGoal

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


def compute_energy_target_kcal(profile: PatientProfile) -> float:
    """TDEE điều chỉnh theo mục tiêu cân nặng, có sàn an toàn."""
    target = compute_tdee(profile) + GOAL_DELTA_KCAL[profile.weight_goal]
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
