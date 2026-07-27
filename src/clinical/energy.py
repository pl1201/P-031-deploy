"""Tính năng lượng: BMR, TDEE, cân nặng lý tưởng.

LLM: NO — deterministic hoàn toàn.
Ticket: CLN-01

Công thức:
  - BMR: Mifflin-St Jeor (1990). Được ADA và ESPEN khuyến nghị cho người trưởng thành.
      Nam:  10*W + 6.25*H - 5*A + 5
      Nữ:   10*W + 6.25*H - 5*A - 161
  - IBW: BMI 22 (mức giữa khoảng bình thường của WHO cho người châu Á)
  - Cân nặng hiệu chỉnh khi béo phì: ABW = IBW + 0.25*(W - IBW)
      Dùng khi BMI >= 30 để tránh ước tính vượt nhu cầu thật.

⚠️ Ngưỡng năng lượng tối thiểu là ràng buộc an toàn, không phải tuỳ chọn:
không bao giờ trả về mục tiêu dưới 1200 kcal (nữ) / 1500 kcal (nam) khi giảm cân.
"""

from __future__ import annotations

from .models import ACTIVITY_FACTOR, PatientProfile, Sex, WeightGoal

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


def bmr_mifflin_st_jeor(
    weight_kg: float, height_cm: float, age: int, sex: Sex
) -> float:
    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age
    return base + 5.0 if sex is Sex.MALE else base - 161.0


def compute_bmr(profile: PatientProfile) -> float:
    weight = adjusted_body_weight_kg(profile.weight_kg, profile.height_cm)
    return bmr_mifflin_st_jeor(weight, profile.height_cm, profile.age, profile.sex)


def compute_tdee(profile: PatientProfile) -> float:
    return compute_bmr(profile) * ACTIVITY_FACTOR[profile.activity_level]


def compute_energy_target_kcal(profile: PatientProfile) -> float:
    """TDEE điều chỉnh theo mục tiêu cân nặng, có sàn an toàn."""
    target = compute_tdee(profile) + GOAL_DELTA_KCAL[profile.weight_goal]
    floor = MIN_KCAL_MALE if profile.sex is Sex.MALE else MIN_KCAL_FEMALE
    return max(target, floor)


def kcal_per_kg(profile: PatientProfile) -> float:
    """Kiểm tra chéo: bệnh nhân mãn tính ổn định thường nằm trong 30–35 kcal/kg/ngày."""
    return compute_energy_target_kcal(profile) / profile.weight_kg
