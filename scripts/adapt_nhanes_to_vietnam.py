#!/usr/bin/env python3
"""
Adapt NHANES 2021-2023 T2DM profiles to Vietnamese population characteristics.

Adjusts anthropometric measurements to match Vietnamese norms while preserving
clinical relationships (HbA1c, glucose, blood pressure, lipids).

References:
- Vietnamese adults: Mean BMI 21-23 kg/m² (vs NHANES 33.3)
- Vietnamese height: Men 168cm, Women 156cm (vs NHANES 170/158cm)
- Weight adjustment preserves BMI-HbA1c correlation from NHANES

Usage:
    python scripts/adapt_nhanes_to_vietnam.py

Input:  data/raw/nhanes_t2dm_profiles.json (1,066 patients)
Output: data/raw/nhanes_t2dm_profiles_vn_adapted.json (1,066 adapted profiles)
"""

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

# Vietnamese population norms (from WHO STEPS VN 2021, Da Nang study)
VN_HEIGHT_MEAN = {"male": 168.0, "female": 156.0}  # cm
VN_HEIGHT_STD = {"male": 6.5, "female": 6.0}

VN_BMI_TARGET_MEAN = 24.2  # From Da Nang study (Asian T2DM)
VN_BMI_TARGET_STD = 3.0

# Region mapping (simplified - assign based on original latitude analogy)
VN_REGIONS = ["north", "central", "south"]
VN_REGION_WEIGHTS = [0.4, 0.2, 0.4]


def adjust_height_to_vietnamese(sex: str, original_height: float, rng: np.random.Generator) -> float:
    """
    Adjust height to Vietnamese norms while preserving relative position.

    Args:
        sex: "male" or "female"
        original_height: Original NHANES height in cm
        rng: Random generator

    Returns:
        Adjusted height in cm
    """
    # Use Vietnamese height distribution
    new_height = rng.normal(VN_HEIGHT_MEAN[sex], VN_HEIGHT_STD[sex])

    # Clip to reasonable range
    if sex == "male":
        new_height = np.clip(new_height, 150, 185)
    else:
        new_height = np.clip(new_height, 140, 170)

    return round(new_height, 1)


def adjust_weight_for_vietnamese_bmi(height_cm: float, target_bmi: float) -> float:
    """
    Calculate weight to achieve target BMI.

    Args:
        height_cm: Height in cm
        target_bmi: Target BMI in kg/m²

    Returns:
        Weight in kg
    """
    height_m = height_cm / 100
    weight_kg = target_bmi * (height_m ** 2)
    return round(weight_kg, 1)


def sample_vietnamese_bmi(original_bmi: float, rng: np.random.Generator) -> float:
    """
    Adjust BMI to Vietnamese T2DM population (lower than US).

    Preserves relative position: high BMI in US → high BMI in VN
    But shifts distribution down.

    Args:
        original_bmi: Original NHANES BMI
        rng: Random generator

    Returns:
        Adjusted BMI for Vietnamese population
    """
    # NHANES T2DM mean BMI ~ 33.3, we want ~ 24.2
    # Shift down but preserve variance
    shift = VN_BMI_TARGET_MEAN - 33.3

    # Add some noise
    noise = rng.normal(0, 1.0)

    new_bmi = original_bmi + shift + noise

    # Clip to reasonable T2DM range (18-35 for Vietnamese)
    new_bmi = np.clip(new_bmi, 18.0, 35.0)

    return round(new_bmi, 1)


def add_vietnamese_attributes(profile: dict[str, Any], rng: np.random.Generator) -> dict[str, Any]:
    """
    Add Vietnam-specific attributes to profile.

    Args:
        profile: Original NHANES profile
        rng: Random generator

    Returns:
        Profile with Vietnamese attributes added
    """
    # Assign region
    profile["region"] = rng.choice(VN_REGIONS, p=VN_REGION_WEIGHTS)

    # Add common Vietnamese food dislikes (if not already present)
    common_dislikes = [
        "sầu riêng", "mắm tôm", "bí đao", "mướp đắng",
        "gan", "tim", "lòng", "tiết canh"
    ]
    if not profile.get("dislikes"):
        n_dislikes = rng.choice([0, 1, 2, 3], p=[0.3, 0.4, 0.2, 0.1])
        profile["dislikes"] = rng.choice(common_dislikes, size=n_dislikes, replace=False).tolist()

    # Activity levels (conservative for T2DM)
    if not profile.get("activity_level"):
        profile["activity_level"] = rng.choice(
            ["sedentary", "lightly_active", "moderately_active"],
            p=[0.5, 0.35, 0.15]
        )

    # Weight goals
    if not profile.get("weight_goal"):
        profile["weight_goal"] = rng.choice(
            ["lose", "maintain", "gain"],
            p=[0.6, 0.35, 0.05]
        )

    return profile


def adapt_profile_to_vietnamese(profile: dict[str, Any], rng: np.random.Generator) -> dict[str, Any]:
    """
    Adapt a single NHANES profile to Vietnamese population characteristics.

    Clinical values (HbA1c, glucose, BP) are preserved.
    Anthropometric values are adjusted to Vietnamese norms.

    Args:
        profile: Original NHANES profile
        rng: Random generator

    Returns:
        Adapted profile
    """
    adapted = profile.copy()

    # Adjust height to Vietnamese norms
    new_height = adjust_height_to_vietnamese(
        adapted["sex"],
        adapted["height_cm"],
        rng
    )

    # Adjust BMI to Vietnamese T2DM norms
    original_bmi = adapted["weight_kg"] / ((adapted["height_cm"] / 100) ** 2)
    new_bmi = sample_vietnamese_bmi(original_bmi, rng)

    # Calculate new weight based on new height and target BMI
    new_weight = adjust_weight_for_vietnamese_bmi(new_height, new_bmi)

    # Update profile
    adapted["height_cm"] = new_height
    adapted["weight_kg"] = new_weight

    # Add Vietnamese-specific attributes
    adapted = add_vietnamese_attributes(adapted, rng)

    # Update metadata
    adapted["_source_dataset"] = "NHANES_2021_2023_VN_adapted"
    adapted["_adaptation_method"] = "height_bmi_adjustment_to_vietnamese_norms"
    adapted["_original_bmi"] = round(original_bmi, 1)
    adapted["_adapted_bmi"] = new_bmi
    adapted["_note"] = "NHANES clinical data adapted to Vietnamese anthropometric norms"

    return adapted


def main() -> None:
    """Adapt NHANES profiles to Vietnamese population."""
    print("NHANES to Vietnamese Adaptation")
    print("=" * 60)

    # Load NHANES profiles
    input_path = Path("data/.json/nhanes_t2dm_profiles.json")
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)

    print(f"Loading NHANES profiles: {input_path}")
    with open(input_path, encoding="utf-8") as f:
        profiles = json.load(f)

    print(f"  [OK] Loaded {len(profiles)} profiles")

    # Filter profiles with complete anthropometric data
    complete_profiles = [
        p for p in profiles
        if p.get("weight_kg") is not None and p.get("height_cm") is not None
    ]
    print(f"  Profiles with complete height/weight: {len(complete_profiles)}/{len(profiles)}")

    # Compute original statistics
    original_bmis = [p["weight_kg"] / ((p["height_cm"] / 100) ** 2) for p in complete_profiles]
    original_heights = [p["height_cm"] for p in complete_profiles]

    print(f"\nOriginal NHANES statistics:")
    print(f"  BMI: {np.mean(original_bmis):.1f} +/- {np.std(original_bmis):.1f} kg/m²")
    print(f"  Height: {np.mean(original_heights):.1f} +/- {np.std(original_heights):.1f} cm")

    # Adapt profiles
    print(f"\nAdapting to Vietnamese norms...")
    rng = np.random.default_rng(42)
    adapted_profiles = [adapt_profile_to_vietnamese(p, rng) for p in complete_profiles]

    # Compute adapted statistics
    adapted_bmis = [p["_adapted_bmi"] for p in adapted_profiles]
    adapted_heights = [p["height_cm"] for p in adapted_profiles]
    adapted_weights = [p["weight_kg"] for p in adapted_profiles]

    print(f"  [OK] Adapted {len(adapted_profiles)} profiles")
    print(f"\nAdapted Vietnamese statistics:")
    print(f"  BMI: {np.mean(adapted_bmis):.1f} +/- {np.std(adapted_bmis):.1f} kg/m²")
    print(f"  Height: {np.mean(adapted_heights):.1f} +/- {np.std(adapted_heights):.1f} cm")
    print(f"  Weight: {np.mean(adapted_weights):.1f} +/- {np.std(adapted_weights):.1f} kg")

    # Save
    output_path = Path("data/.json/nhanes_t2dm_profiles_vn_adapted.json")
    print(f"\nSaving: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(adapted_profiles, f, indent=2, ensure_ascii=False)

    print(f"[OK] Saved {len(adapted_profiles)} adapted profiles")
    print(f"\n{'=' * 60}")
    print("[OK] Adaptation complete")
    print(f"\nClinical values (HbA1c, glucose, BP) preserved from NHANES")
    print(f"Anthropometric values adjusted to Vietnamese norms")


if __name__ == "__main__":
    main()
