#!/usr/bin/env python3
r"""
Download China Health and Nutrition Survey (CHNS) 2009 + 2015 biomarker data.

CHNS is a longitudinal survey tracking health and nutrition in China since 1989.
Biomarker data (HbA1c, glucose, lipids) available from 2009 and 2015 waves.

Data source: Carolina Population Center, UNC Chapel Hill
URL: https://data.cpc.unc.edu/projects/7
License: Public use, registration required, cite properly

This script:
1. Downloads CHNS biomarker + demographic + dietary files (2009, 2015)
2. Verifies checksums if available
3. Creates manifest with provenance metadata

Output: C:\Users\dinhl\data\research\chns_china\raw\

Usage:
    python scripts/download_chns_china_t2dm.py

Note: Manual download required - CHNS portal requires registration and
selecting specific files. This script documents the process.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# CHNS requires manual download - this script documents what to download
CHNS_FILES_2009 = {
    "biomarker": "chns_2009_biomarker.dta",  # HbA1c, glucose, lipids
    "demographic": "chns_2009_demographic.dta",
    "dietary": "chns_2009_dietary_day1.dta",
    "household": "chns_2009_household.dta",
}

CHNS_FILES_2015 = {
    "biomarker": "chns_2015_biomarker.dta",
    "demographic": "chns_2015_demographic.dta",
    "dietary": "chns_2015_dietary_day1.dta",
    "household": "chns_2015_household.dta",
}


def print_download_instructions() -> None:
    """Print manual download instructions for CHNS data."""
    print("=" * 70)
    print("CHNS China Download Instructions")
    print("=" * 70)
    print()
    print("CHNS requires manual download via their web portal.")
    print()
    print("Steps:")
    print("1. Register at: https://www.cpc.unc.edu/projects/china/data/datasets")
    print("2. Login and navigate to Data section")
    print("3. Download these files:")
    print()
    print("   [2009 Wave]")
    for key, filename in CHNS_FILES_2009.items():
        print(f"     - {key}: {filename}")
    print()
    print("   [2015 Wave]")
    for key, filename in CHNS_FILES_2015.items():
        print(f"     - {key}: {filename}")
    print()
    print("4. Save to: C:\\Users\\dinhl\\data\\research\\chns_china\\raw\\")
    print()
    print("Expected variables:")
    print("  - ID: ID code for merging")
    print("  - HbA1c: Glycated hemoglobin (2015 only)")
    print("  - Glucose: Fasting blood glucose")
    print("  - Age, Sex, Height, Weight, BMI")
    print("  - Dietary intake (3-day recall)")
    print()
    print("Citation:")
    print("  China Health and Nutrition Survey (CHNS). Carolina Population Center,")
    print("  University of North Carolina at Chapel Hill.")
    print("  https://www.cpc.unc.edu/projects/china")
    print()
    print("=" * 70)


def create_manifest_template() -> None:
    """Create manifest template for CHNS download."""
    output_dir = Path.home() / "data" / "research" / "chns_china"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "MANIFEST_TEMPLATE.json"

    manifest = {
        "dataset": "CHNS_China_2009_2015",
        "source": "Carolina Population Center, UNC Chapel Hill",
        "url": "https://data.cpc.unc.edu/projects/7",
        "license": "Public use with citation",
        "citation": "China Health and Nutrition Survey (CHNS). Carolina Population Center, University of North Carolina at Chapel Hill.",
        "download_date": datetime.now().isoformat(),
        "waves": ["2009", "2015"],
        "files_2009": CHNS_FILES_2009,
        "files_2015": CHNS_FILES_2015,
        "note": "Manual download required. Fill in checksums after download.",
        "checksums": {"2009": {}, "2015": {}},
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Manifest template created: {manifest_path}")
    print("     Fill in checksums after manual download")


def main() -> None:
    """Main execution."""
    print_download_instructions()
    create_manifest_template()

    print("\n" + "=" * 70)
    print("Next steps:")
    print("1. Complete manual download from CHNS portal")
    print("2. Run: python scripts/build_chns_t2dm_cohort.py")
    print("3. Run: python scripts/adapt_chns_to_vietnam.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
