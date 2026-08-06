#!/usr/bin/env python3
"""
Analyze NHANES 2021-2023 probable T2DM cohort and extract distributions.

Computes population-weighted statistics for key clinical and dietary variables:
- Demographics: age, sex, race/ethnicity
- Anthropometrics: BMI, weight, height, waist circumference
- Labs: HbA1c, fasting glucose
- Blood pressure: systolic, diastolic
- Dietary: energy, macronutrients, sodium

Uses NHANES survey weights (WTMEC2YR) to produce population-representative estimates.

Outputs distributions/t2dm_distributions.json with means, standard deviations,
percentiles, and correlations for synthetic profile generation.

Usage:
    python scripts/analyze_nhanes_distributions.py

References:
- NHANES Analytic Guidelines: https://wwwn.cdc.gov/nchs/nhanes/analyticguidelines.aspx
"""

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def compute_weighted_stats(data: pd.Series, weights: pd.Series) -> dict[str, float]:
    """
    Compute weighted mean, std, and percentiles.

    Args:
        data: Variable values
        weights: Survey weights (WTMEC2YR, WTPH2YR, etc.)

    Returns:
        Dict with mean, std, p5, p25, p50, p75, p95
    """
    # Remove missing values
    valid = ~data.isna() & ~weights.isna()
    clean_data = data[valid]
    clean_weights = weights[valid]

    if len(clean_data) == 0:
        return {
            "mean": None,
            "std": None,
            "p5": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p95": None,
            "n": 0,
        }

    # Check for zero-sum weights
    weight_sum = clean_weights.sum()
    if weight_sum == 0:
        print("  ⚠ Warning: All weights are zero, returning unweighted stats")
        return {
            "mean": float(clean_data.mean()),
            "std": float(clean_data.std()),
            "p5": float(clean_data.quantile(0.05)),
            "p25": float(clean_data.quantile(0.25)),
            "p50": float(clean_data.quantile(0.50)),
            "p75": float(clean_data.quantile(0.75)),
            "p95": float(clean_data.quantile(0.95)),
            "n": int(len(clean_data)),
        }

    # Normalize weights
    norm_weights = clean_weights / weight_sum

    # Weighted mean
    mean = np.average(clean_data, weights=norm_weights)

    # Weighted variance
    variance = np.average((clean_data - mean) ** 2, weights=norm_weights)
    std = np.sqrt(variance)

    # Weighted percentiles (approximate via sorting)
    sorted_idx = np.argsort(clean_data)
    sorted_data = clean_data.iloc[sorted_idx].values
    sorted_weights = norm_weights.iloc[sorted_idx].values
    cumsum_weights = np.cumsum(sorted_weights)

    def find_percentile(p: float) -> float:
        # Use right-side search to handle edge case where cumsum never reaches 1.0
        idx = np.searchsorted(cumsum_weights, p / 100, side="right")
        # Clamp to valid range
        idx = max(0, min(idx, len(sorted_data) - 1))
        return float(sorted_data[idx])

    return {
        "mean": float(mean),
        "std": float(std),
        "p5": find_percentile(5),
        "p25": find_percentile(25),
        "p50": find_percentile(50),
        "p75": find_percentile(75),
        "p95": find_percentile(95),
        "n": int(len(clean_data)),
    }


def compute_correlation_matrix(
    df: pd.DataFrame, variables: list[str], weights: pd.Series
) -> dict[str, dict[str, float]]:
    """
    Compute weighted correlation matrix.

    Args:
        df: DataFrame with variables
        variables: List of variable names
        weights: Survey weights

    Returns:
        Dict of dict representing correlation matrix
    """
    # Filter to complete cases
    subset = df[variables + [weights.name]].dropna()
    if len(subset) < 2:
        return {}

    norm_weights = subset[weights.name] / subset[weights.name].sum()

    corr_matrix = {}
    for var1 in variables:
        corr_matrix[var1] = {}
        for var2 in variables:
            if var1 == var2:
                corr_matrix[var1][var2] = 1.0
            else:
                # Weighted Pearson correlation
                x = subset[var1]
                y = subset[var2]
                wx = x - np.average(x, weights=norm_weights)
                wy = y - np.average(y, weights=norm_weights)
                cov = np.average(wx * wy, weights=norm_weights)
                std_x = np.sqrt(np.average(wx**2, weights=norm_weights))
                std_y = np.sqrt(np.average(wy**2, weights=norm_weights))
                # Use epsilon threshold to avoid division by near-zero std
                epsilon = 1e-6
                r = cov / (std_x * std_y) if std_x > epsilon and std_y > epsilon else 0.0
                corr_matrix[var1][var2] = float(r)

    return corr_matrix


def analyze_cohort(cohort_path: Path) -> dict[str, Any]:
    """
    Analyze probable T2DM cohort and extract distributions.

    Args:
        cohort_path: Path to nhanes_probable_t2dm.csv

    Returns:
        Distribution metadata dict
    """
    print("\n[1/3] Loading cohort...")
    df = pd.read_csv(cohort_path)
    print(f"  Loaded {len(df):,} probable T2DM cases")

    # Use MEC exam weights (WTMEC2YR) - covers lab and anthropometry
    weights = df["WTMEC2YR"]

    print("\n[2/3] Computing distributions...")

    distributions = {}

    # Demographics
    print("  - Demographics")
    distributions["age"] = compute_weighted_stats(df["RIDAGEYR"], weights)
    distributions["sex_female_pct"] = float(100 * np.average((df["RIAGENDR"] == 2), weights=weights / weights.sum()))

    # Anthropometrics
    print("  - Anthropometrics")
    distributions["weight_kg"] = compute_weighted_stats(df["BMXWT"], weights)
    distributions["height_cm"] = compute_weighted_stats(df["BMXHT"], weights)
    distributions["bmi"] = compute_weighted_stats(df["BMXBMI"], weights)
    distributions["waist_cm"] = compute_weighted_stats(df["BMXWAIST"], weights)

    # Labs
    print("  - Laboratory")
    distributions["hba1c_pct"] = compute_weighted_stats(df["LBXGH"], weights)
    distributions["glucose_mg_dl"] = compute_weighted_stats(df["LBXGLU"], weights)

    # Blood pressure
    print("  - Blood pressure")
    distributions["sbp_mmhg"] = compute_weighted_stats(df["BPXOSY1"], weights)
    distributions["dbp_mmhg"] = compute_weighted_stats(df["BPXODI1"], weights)

    # Dietary (average of day 1 and day 2)
    print("  - Dietary")
    df["avg_kcal"] = (df["DR1TKCAL"] + df["DR2TKCAL"]) / 2
    df["avg_carb_g"] = (df["DR1TCARB"] + df["DR2TCARB"]) / 2
    df["avg_protein_g"] = (df["DR1TPROT"] + df["DR2TPROT"]) / 2
    df["avg_fat_g"] = (df["DR1TTFAT"] + df["DR2TTFAT"]) / 2
    df["avg_sodium_mg"] = (df["DR1TSODI"] + df["DR2TSODI"]) / 2

    distributions["kcal_per_day"] = compute_weighted_stats(df["avg_kcal"], weights)
    distributions["carb_g_per_day"] = compute_weighted_stats(df["avg_carb_g"], weights)
    distributions["protein_g_per_day"] = compute_weighted_stats(df["avg_protein_g"], weights)
    distributions["fat_g_per_day"] = compute_weighted_stats(df["avg_fat_g"], weights)
    distributions["sodium_mg_per_day"] = compute_weighted_stats(df["avg_sodium_mg"], weights)

    # Correlations
    print("\n[3/3] Computing correlations...")
    key_variables = ["RIDAGEYR", "BMXBMI", "LBXGH", "LBXGLU", "BPXOSY1", "BPXODI1"]
    correlations = compute_correlation_matrix(df, key_variables, weights)

    return {
        "dataset": "NHANES 2021-2023 Probable Type 2 Diabetes",
        "n_cases": len(df),
        "heuristic": "self_report + age>=20 + exclude_likely_type1",
        "survey_weights": "WTMEC2YR",
        "distributions": distributions,
        "correlations": correlations,
        "variable_mapping": {
            "RIDAGEYR": "age",
            "BMXBMI": "bmi",
            "LBXGH": "hba1c_pct",
            "LBXGLU": "glucose_mg_dl",
            "BPXOSY1": "sbp_mmhg",
            "BPXODI1": "dbp_mmhg",
        },
        "notes": [
            "Distributions are population-weighted using NHANES survey weights",
            "Probable T2DM identified by heuristic, not confirmed diagnosis",
            "Dietary data averaged across two 24-hour recalls",
            "Missing values excluded from each distribution calculation",
        ],
    }


def main() -> None:
    """Analyze NHANES cohort and save distributions."""
    print("NHANES 2021-2023 Distribution Analyzer")
    print("=" * 60)

    # Check input file
    processed_dir = Path.home() / "data" / "research" / "nhanes_2021_2023" / "processed"
    cohort_path = processed_dir / "nhanes_probable_t2dm.csv"

    if not cohort_path.exists():
        print(f"[ERROR] Input file not found: {cohort_path}")
        print("  Run: python scripts/build_nhanes_2021_2023_cohort.py")
        sys.exit(1)

    # Analyze
    result = analyze_cohort(cohort_path)

    # Save distributions
    output_dir = processed_dir.parent / "distributions"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "t2dm_distributions.json"

    print(f"\n{'=' * 60}")
    print(f"Saving distributions: {output_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[OK] Saved distributions for {result['n_cases']:,} T2DM cases")
    print("\nKey statistics:")
    print(f"  Age: {result['distributions']['age']['mean']:.1f} +/- {result['distributions']['age']['std']:.1f} years")
    print(f"  BMI: {result['distributions']['bmi']['mean']:.1f} +/- {result['distributions']['bmi']['std']:.1f} kg/m^2")
    print(
        f"  HbA1c: {result['distributions']['hba1c_pct']['mean']:.1f} +/- {result['distributions']['hba1c_pct']['std']:.1f}%"
    )
    print(
        f"  Daily kcal: {result['distributions']['kcal_per_day']['mean']:.0f} +/- {result['distributions']['kcal_per_day']['std']:.0f}"
    )
    print("\nNext step: python scripts/generate_synthetic_t2dm_profiles.py")


if __name__ == "__main__":
    main()
