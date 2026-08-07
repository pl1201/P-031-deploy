#!/usr/bin/env python3
r"""
Download India NFHS-5 (2019-2021) biomarker data for T2DM analysis.

NFHS-5 (National Family Health Survey) is part of the DHS Program.
Contains glucose, HbA1c, BMI, and demographic data for ~724,000 adults.

Data source: DHS Program (USAID)
URL: https://dhsprogram.com/data/available-datasets.cfm
License: Free registration required, research use

This script documents the download process and expected files.

Output: C:\Users\dinhl\data\research\nfhs5_india\raw\

Usage:
    python scripts/download_india_nfhs5_t2dm.py

Note: Manual registration and approval required (24-48h).
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def print_download_instructions() -> None:
    """Print registration and download instructions."""
    print("=" * 70)
    print("India NFHS-5 Download Instructions")
    print("=" * 70)
    print()
    print("NFHS-5 requires DHS Program registration (free, 24-48h approval).")
    print()
    print("Steps:")
    print("1. Register at: https://dhsprogram.com/data/new-user-registration.cfm")
    print("   - Provide institution, research purpose")
    print("   - Agree to DHS data use terms")
    print()
    print("2. After approval, login and search for 'India NFHS-5'")
    print()
    print("3. Request these datasets:")
    print("   - Household Recode (IAHR7EDT.zip)")
    print("   - Individual Recode - Women (IAIR7EDT.zip)")
    print("   - Individual Recode - Men (IAMR7EDT.zip)")
    print("   - Biomarker/Blood Recode (IABR7EDT.zip) **CRITICAL**")
    print()
    print("4. Download formats:")
    print("   - Stata (.dta) - Recommended")
    print("   - SPSS (.sav)")
    print("   - Flat ASCII (.dat + .dct)")
    print()
    print("5. Save to: C:\\Users\\dinhl\\data\\research\\nfhs5_india\\raw\\")
    print()
    print("Expected variables (Biomarker file):")
    print("  - HHID: Household ID (for merging)")
    print("  - HVIDX: Line number")
    print("  - HV105: Age")
    print("  - HV104: Sex")
    print("  - SH20B: Blood glucose level (mg/dL)")
    print("  - SH20A: Time since last ate/drank (for fasting status)")
    print("  - HB40: BMI")
    print("  - HB40A: Weight (kg)")
    print("  - HB40B: Height (cm)")
    print("  - SH130: Has diabetes (self-reported)")
    print("  - SH131: Taking diabetes medication")
    print()
    print("Sample size:")
    print("  - Total tested: ~724,000 adults")
    print("  - Estimated T2DM (glucose >=126 OR self-report): ~50,000-70,000")
    print()
    print("Citation:")
    print("  International Institute for Population Sciences (IIPS) and ICF. 2021.")
    print("  National Family Health Survey (NFHS-5), 2019-21: India.")
    print("  Mumbai: IIPS. http://rchiips.org/nfhs/")
    print()
    print("=" * 70)


def create_manifest_template() -> None:
    """Create manifest template for NFHS-5."""
    output_dir = Path.home() / "data" / "research" / "nfhs5_india"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "MANIFEST_TEMPLATE.json"

    manifest = {
        "dataset": "NFHS5_India_2019_2021",
        "source": "DHS Program (USAID) / IIPS",
        "url": "https://dhsprogram.com/data/",
        "license": "DHS Standard - Free registration, research use only",
        "citation": "International Institute for Population Sciences (IIPS) and ICF. 2021. National Family Health Survey (NFHS-5), 2019-21: India. Mumbai: IIPS.",
        "download_date": datetime.now().isoformat(),
        "survey_period": "2019-06 to 2021-04",
        "files_expected": {
            "biomarker": "IABR7EDT.dta",
            "household": "IAHR7EDT.dta",
            "women": "IAIR7EDT.dta",
            "men": "IAMR7EDT.dta",
        },
        "key_variables": {
            "glucose": "SH20B",
            "fasting_status": "SH20A",
            "bmi": "HB40",
            "weight_kg": "HB40A",
            "height_cm": "HB40B",
            "age": "HV105",
            "sex": "HV104",
            "diabetes_self_report": "SH130",
            "diabetes_meds": "SH131",
        },
        "sample_size": {"total_tested": 724000, "estimated_t2dm": "50000-70000"},
        "note": "Manual download after DHS registration approval (24-48h)",
        "checksums": {},
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Manifest template created: {manifest_path}")


def print_t2dm_filter_heuristic() -> None:
    """Print T2DM identification heuristic for NFHS-5."""
    print("\n" + "=" * 70)
    print("T2DM Identification Heuristic (NFHS-5)")
    print("=" * 70)
    print()
    print("Probable T2DM if:")
    print("  (1) Fasting glucose >= 126 mg/dL")
    print("  OR (2) Random glucose >= 200 mg/dL")
    print("  OR (3) Self-reported diabetes (SH130=1) AND age >= 20")
    print()
    print("Exclude likely Type 1:")
    print("  - Diagnosed age < 30 AND BMI < 18.5")
    print("  (Note: NFHS-5 doesn't have insulin start date)")
    print()
    print("Fasting status:")
    print("  - SH20A <= 8 hours: Fasting glucose")
    print("  - SH20A > 8 hours: Random glucose")
    print()
    print("Expected T2DM prevalence: ~10-12% of tested adults")
    print("Estimated N: 50,000-70,000 T2DM cases")
    print()
    print("Phenotype notes:")
    print("  - 'Lean diabetes' common in India (BMI 22-25)")
    print("  - Rural/urban differences significant")
    print("  - State-level variation (Kerala highest ~25%, Bihar lowest ~5%)")
    print("=" * 70)


def main() -> None:
    """Main execution."""
    print_download_instructions()
    create_manifest_template()
    print_t2dm_filter_heuristic()

    print("\n" + "=" * 70)
    print("Next steps:")
    print("1. Complete DHS registration and wait for approval")
    print("2. Download biomarker + demographic files")
    print("3. Run: python scripts/build_nfhs5_t2dm_cohort.py")
    print("4. Run: python scripts/adapt_nfhs5_to_vietnam.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
