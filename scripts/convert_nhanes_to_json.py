#!/usr/bin/env python3
"""
Convert NHANES 2021-2023 probable T2DM cohort to JSON format.

Reads the processed CSV from ~/data/research/nhanes_2021_2023/processed/
and converts it to JSON format suitable for seeding the database.

This script is provided for local conversion only. The output should be
reviewed before any decision to include it in version control.

Usage:
    python scripts/convert_nhanes_to_json.py --output data/seeds/nhanes_t2dm_profiles.json

References:
- Input: ~/data/research/nhanes_2021_2023/processed/nhanes_probable_t2dm.csv
- NCHS Data User Agreement: https://www.cdc.gov/nchs/data_access/restrictions.htm
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


def convert_row_to_profile(row: pd.Series, index: int) -> dict[str, Any]:
    """
    Convert a single NHANES row to a patient profile dict.

    Args:
        row: DataFrame row with NHANES variables
        index: Row index for generating patient_id

    Returns:
        Patient profile dict
    """
    # Basic demographics
    age = int(row["RIDAGEYR"]) if pd.notna(row["RIDAGEYR"]) else None
    sex = "female" if row["RIAGENDR"] == 2 else "male" if row["RIAGENDR"] == 1 else None

    # Anthropometrics
    weight_kg = round(float(row["BMXWT"]), 1) if pd.notna(row["BMXWT"]) else None
    height_cm = round(float(row["BMXHT"]), 1) if pd.notna(row["BMXHT"]) else None
    bmi = round(float(row["BMXBMI"]), 1) if pd.notna(row["BMXBMI"]) else None

    # Lab values
    hba1c_pct = round(float(row["LBXGH"]), 1) if pd.notna(row["LBXGH"]) else None
    glucose_mg_dl = round(float(row["LBXGLU"]), 0) if pd.notna(row["LBXGLU"]) else None

    # Blood pressure
    sbp_mmhg = round(float(row["BPXOSY1"]), 0) if pd.notna(row["BPXOSY1"]) else None
    dbp_mmhg = round(float(row["BPXODI1"]), 0) if pd.notna(row["BPXODI1"]) else None

    # Build conditions
    conditions = []

    # T2DM condition
    if hba1c_pct is not None or glucose_mg_dl is not None:
        t2dm_condition = {
            "code": "E11",
            "name": "Type 2 Diabetes Mellitus",
            "stage": None,
            "lab_values": {}
        }
        if hba1c_pct is not None:
            t2dm_condition["lab_values"]["HbA1c_pct"] = hba1c_pct
        if glucose_mg_dl is not None:
            t2dm_condition["lab_values"]["glucose_fasting_mg_dl"] = glucose_mg_dl
        conditions.append(t2dm_condition)

    # Hypertension (if SBP >= 140 or DBP >= 90)
    if sbp_mmhg is not None and dbp_mmhg is not None:
        if sbp_mmhg >= 140 or dbp_mmhg >= 90:
            conditions.append({
                "code": "I10",
                "name": "Hypertension",
                "stage": None,
                "lab_values": {
                    "SBP_mmHg": sbp_mmhg,
                    "DBP_mmHg": dbp_mmhg
                }
            })

    profile = {
        "patient_id": f"nhanes_t2dm_{index:04d}",
        "age": age,
        "sex": sex,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "activity_level": None,  # Not available in NHANES
        "weight_goal": None,  # Not available in NHANES
        "conditions": conditions,
        "allergies": [],  # Not available in NHANES
        "medications": [],  # NHANES has medication count but not names
        "region": None,  # Vietnam-specific, not in NHANES
        "dislikes": [],  # Not available in NHANES
        "frailty_sarcopenia": False,
        "metabolically_unstable": False,
        "sodium_wasting": False,
        # Metadata
        "_source_dataset": "NHANES_2021_2023",
        "_source_type": "de_identified_public_use",
        "_diabetes_heuristic": "probable_type2",
        "_note": "Real de-identified patient data from NHANES 2021-2023"
    }

    return profile


def main() -> None:
    """Convert NHANES CSV to JSON format."""
    parser = argparse.ArgumentParser(description="Convert NHANES cohort to JSON")
    parser.add_argument(
        "--output",
        type=str,
        default="data/seeds/nhanes_t2dm_profiles.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of profiles (for testing)"
    )
    args = parser.parse_args()

    print("NHANES to JSON Converter")
    print("=" * 60)

    # Input file
    input_path = Path.home() / "data" / "research" / "nhanes_2021_2023" / "processed" / "nhanes_probable_t2dm.csv"

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        print("  Run: python scripts/build_nhanes_2021_2023_cohort.py")
        sys.exit(1)

    # Load data
    print(f"Loading: {input_path}")
    df = pd.read_csv(input_path)
    print(f"  Loaded {len(df):,} probable T2DM cases")

    # Limit if requested
    if args.limit:
        df = df.head(args.limit)
        print(f"  Limited to {len(df):,} profiles")

    # Convert
    print("\nConverting to JSON format...")
    profiles = []
    for idx, row in df.iterrows():
        profile = convert_row_to_profile(row, idx)
        profiles.append(profile)

    print(f"  [OK] Converted {len(profiles):,} profiles")

    # Output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save
    print(f"\nSaving to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    print(f"[OK] Saved {len(profiles):,} profiles")

    # Summary
    print(f"\n{'=' * 60}")
    print("Summary:")
    print(f"  Total profiles: {len(profiles):,}")
    print(f"  Source: NHANES 2021-2023 (de-identified, public-use)")
    print(f"  Heuristic: probable type 2 diabetes")
    print(f"\nIMPORTANT:")
    print(f"  This data is from NHANES and subject to NCHS Data User Agreement")
    print(f"  - May be used for research and statistical reporting")
    print(f"  - May NOT be used to re-identify participants")
    print(f"  - See: https://www.cdc.gov/nchs/data_access/restrictions.htm")


if __name__ == "__main__":
    main()
