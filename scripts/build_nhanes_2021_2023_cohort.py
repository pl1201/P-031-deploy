#!/usr/bin/env python3
"""
Build NHANES 2021-2023 cohort and filter probable type 2 diabetes cases.

Reads XPT files from ~/data/research/nhanes_2021_2023/raw/, merges them by SEQN,
and applies heuristic to identify probable type 2 diabetes:
- Self-reported diabetes (DIQ010 = 1)
- Age >= 20 years
- Exclude likely type 1: insulin use + diagnosed <30y + started insulin ≤1 year

Outputs:
- nhanes_merged.csv: Full merged dataset
- nhanes_probable_t2dm.csv: Filtered probable T2DM cohort

Usage:
    python scripts/build_nhanes_2021_2023_cohort.py

References:
- NHANES 2021-2023 variable documentation: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023
"""

import sys
from pathlib import Path

import pandas as pd

# Expected NHANES files
REQUIRED_FILES = [
    "DEMO_L.xpt",  # Demographics
    "DIQ_L.xpt",  # Diabetes questionnaire
    "GHB_L.xpt",  # HbA1c
    "GLU_L.xpt",  # Glucose
    "BMX_L.xpt",  # Body measures
    "BPXO_L.xpt",  # Blood pressure
    "DR1TOT_L.xpt",  # Dietary day 1
    "DR2TOT_L.xpt",  # Dietary day 2
]

# Key columns to validate
EXPECTED_COLUMNS = {
    "DEMO_L": ["SEQN", "RIDAGEYR", "RIAGENDR", "RIDRETH3", "WTMEC2YR"],
    "DIQ_L": ["SEQN", "DIQ010", "DID040", "DIQ050", "DID060"],
    "GHB_L": ["SEQN", "LBXGH"],
    "GLU_L": ["SEQN", "LBXGLU"],
    "BMX_L": ["SEQN", "BMXWT", "BMXHT", "BMXBMI", "BMXWAIST"],
    "BPXO_L": ["SEQN", "BPXOSY1", "BPXODI1"],
    "DR1TOT_L": ["SEQN", "DR1TKCAL", "DR1TCARB", "DR1TPROT", "DR1TTFAT", "DR1TSODI"],
    "DR2TOT_L": ["SEQN", "DR2TKCAL", "DR2TCARB", "DR2TPROT", "DR2TTFAT", "DR2TSODI"],
}


def validate_columns(df: pd.DataFrame, file_name: str, expected: list[str]) -> None:
    """Validate that required columns exist in dataframe."""
    missing = set(expected) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {file_name}: {missing}")


def load_xpt_file(file_path: Path, file_key: str) -> pd.DataFrame:
    """Load XPT file and validate schema."""
    print(f"  Loading {file_path.name}...")
    df = pd.read_sas(file_path, format="xport")

    if file_key in EXPECTED_COLUMNS:
        validate_columns(df, file_path.name, EXPECTED_COLUMNS[file_key])

    print(f"    {len(df):,} rows, {len(df.columns)} columns")
    return df


def merge_nhanes_files(raw_dir: Path) -> pd.DataFrame:
    """Merge all NHANES component files by SEQN."""
    print("\n[1/4] Loading XPT files...")

    # Load demographics first (base table)
    demo = load_xpt_file(raw_dir / "DEMO_L.xpt", "DEMO_L")
    print(f"\n  Base: {len(demo):,} participants from demographics")

    # Load other components
    diq = load_xpt_file(raw_dir / "DIQ_L.xpt", "DIQ_L")
    ghb = load_xpt_file(raw_dir / "GHB_L.xpt", "GHB_L")
    glu = load_xpt_file(raw_dir / "GLU_L.xpt", "GLU_L")
    bmx = load_xpt_file(raw_dir / "BMX_L.xpt", "BMX_L")
    bpxo = load_xpt_file(raw_dir / "BPXO_L.xpt", "BPXO_L")
    dr1 = load_xpt_file(raw_dir / "DR1TOT_L.xpt", "DR1TOT_L")
    dr2 = load_xpt_file(raw_dir / "DR2TOT_L.xpt", "DR2TOT_L")

    print("\n[2/4] Merging files by SEQN...")

    # Merge with left join (keep all demographics records)
    merged = demo
    for name, df in [
        ("DIQ", diq),
        ("GHB", ghb),
        ("GLU", glu),
        ("BMX", bmx),
        ("BPXO", bpxo),
        ("DR1", dr1),
        ("DR2", dr2),
    ]:
        before_count = len(merged)
        merged = merged.merge(df, on="SEQN", how="left", validate="one_to_one", indicator=True)

        # Check for unmatched records on right side (data loss risk)
        right_only = (merged["_merge"] == "right_only").sum()
        if right_only > 0:
            raise RuntimeError(f"{right_only} records in {name} not found in demographics (data loss)")

        # Drop merge indicator
        merged = merged.drop(columns=["_merge"])
        print(f"  + {name}: {len(merged):,} rows (joined {len(df):,} records)")

        if len(merged) != before_count:
            raise RuntimeError(f"Row count changed from {before_count:,} to {len(merged):,} after merging {name}")

    return merged


def filter_probable_t2dm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply heuristic to identify probable type 2 diabetes cases.

    Criteria:
    - Self-reported diabetes (DIQ010 = 1)
    - Age >= 20 years
    - Exclude likely type 1:
      * Currently using insulin (DIQ050 = 1)
      * Diagnosed age < 30 (DIQ040 < 30)
      * Started insulin ≤ 1 year after diagnosis (DID060 <= 1 or DID060 = 365 days)

    Returns:
        DataFrame with probable T2DM cases and new columns:
        - diabetes_source: 'self_report'
        - diabetes_type: 'probable_type2'
    """
    print("\n[3/4] Filtering probable type 2 diabetes cases...")

    # Start with self-reported diabetes
    has_diabetes = df["DIQ010"] == 1
    print(f"  Self-reported diabetes (DIQ010=1): {has_diabetes.sum():,}")

    # Adult population
    is_adult = df["RIDAGEYR"] >= 20
    print(f"  Age >= 20: {(has_diabetes & is_adult).sum():,}")

    # Identify likely type 1 (to exclude)
    using_insulin = df["DIQ050"] == 1
    diagnosed_young = df["DID040"] < 30

    # DID060: How long taking insulin (years, or 666 for <1 year)
    # Treat 666 as 0.5 years, and missing as unknown (don't exclude)
    insulin_duration = df["DID060"].fillna(999)  # Use 999 for missing
    started_insulin_early = (insulin_duration <= 1) | (insulin_duration == 666)

    likely_type1 = using_insulin & diagnosed_young & started_insulin_early
    print(f"  Likely type 1 (insulin + dx<30y + early insulin): {likely_type1.sum():,}")

    # Final filter
    probable_t2dm = has_diabetes & is_adult & ~likely_type1
    print(f"  [OK] Probable type 2 diabetes: {probable_t2dm.sum():,}")

    # Extract and label
    t2dm_cohort = df[probable_t2dm].copy()
    t2dm_cohort["diabetes_source"] = "self_report"
    t2dm_cohort["diabetes_type"] = "probable_type2"

    return t2dm_cohort


def main() -> None:
    """Build NHANES 2021-2023 cohort and filter probable T2DM."""
    print("NHANES 2021-2023 Cohort Builder")
    print("=" * 60)

    # Check input directory
    raw_dir = Path.home() / "data" / "research" / "nhanes_2021_2023" / "raw"
    if not raw_dir.exists():
        print(f"[ERROR] Input directory not found: {raw_dir}")
        print("  Run: python scripts/download_nhanes_2021_2023.py")
        sys.exit(1)

    # Check all files exist
    missing = [f for f in REQUIRED_FILES if not (raw_dir / f).exists()]
    if missing:
        print(f"[ERROR] Missing XPT files: {missing}")
        sys.exit(1)

    # Output directory
    processed_dir = raw_dir.parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Merge files
    merged = merge_nhanes_files(raw_dir)

    # Save full merged dataset
    merged_path = processed_dir / "nhanes_merged.csv"
    print(f"\n  Saving merged dataset: {merged_path}")
    merged.to_csv(merged_path, index=False)
    print(f"  [OK] Saved {len(merged):,} rows, {len(merged.columns)} columns")

    # Filter probable T2DM
    t2dm_cohort = filter_probable_t2dm(merged)

    # Save T2DM cohort
    t2dm_path = processed_dir / "nhanes_probable_t2dm.csv"
    print(f"\n[4/4] Saving probable T2DM cohort: {t2dm_path}")
    t2dm_cohort.to_csv(t2dm_path, index=False)
    print(f"  [OK] Saved {len(t2dm_cohort):,} rows, {len(t2dm_cohort.columns)} columns")

    # Summary statistics
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total participants: {len(merged):,}")
    print(f"  Probable T2DM: {len(t2dm_cohort):,} ({100 * len(t2dm_cohort) / len(merged):.1f}%)")
    print(f"  Mean age (T2DM): {t2dm_cohort['RIDAGEYR'].mean():.1f} years")
    print(f"  Mean BMI (T2DM): {t2dm_cohort['BMXBMI'].mean():.1f} kg/m²")
    print(f"  Mean HbA1c (T2DM): {t2dm_cohort['LBXGH'].mean():.1f}%")
    print("\nNext step: python scripts/analyze_nhanes_distributions.py")


if __name__ == "__main__":
    main()
