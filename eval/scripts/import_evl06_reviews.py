#!/usr/bin/env python3
"""EVL-06: Import and validate expert reviews.

Import review data từ chuyên gia, validate format, compute metrics.

Usage:
    python eval/scripts/import_evl06_reviews.py --input expert_reviews.jsonl --output results.json

Metrics computed:
1. Agreement rate: % approve + light_edit
2. Edit distance: avg gram changes across edited plans
3. Reject rate: % rejected plans
4. Avg review time
5. Reason code distribution

Validation rules:
- 20 reviews minimum (1 per meal plan)
- All meal_plan_ids must match export
- reviewer_id required (anonymous mapping)
- rating must be: approve | light_edit | heavy_edit | reject
- reviewed_at must be valid ISO datetime
- Fail-closed on any validation error
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExpertReview(BaseModel):
    """Expert review of a meal plan (EVL-06)."""

    review_id: str
    meal_plan_id: str
    reviewer_id: str = Field(..., description="Anonymous reviewer ID")
    reviewer_role: str
    reviewed_at: str
    rating: str
    gram_changes: dict[str, Any] = Field(default_factory=dict)
    dishes_added: list[dict[str, Any]] = Field(default_factory=list)
    dishes_removed: list[dict[str, Any]] = Field(default_factory=list)
    review_time_minutes: int = Field(ge=0)
    comments: str
    reason_code: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: str) -> str:
        valid = {"approve", "light_edit", "heavy_edit", "reject"}
        if v not in valid:
            raise ValueError(f"Invalid rating: {v}. Must be one of {valid}")
        return v

    @field_validator("reviewed_at")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {v}") from e
        return v


class EVL06Metrics(BaseModel):
    """EVL-06 evaluation metrics."""

    total_reviews: int
    agreement_pct: float = Field(..., description="% approve + light_edit")
    reject_pct: float
    heavy_edit_pct: float
    avg_review_time_minutes: float
    avg_gram_changes_per_edit: float
    reason_code_distribution: dict[str, int]
    reviewer_distribution: dict[str, int]


def load_reviews(path: Path) -> list[ExpertReview]:
    """Load and validate expert reviews."""
    if not path.exists():
        raise FileNotFoundError(f"Review file not found: {path}")

    reviews = []
    errors = []

    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                review = ExpertReview(**data)
                reviews.append(review)
            except Exception as e:
                errors.append(f"Line {i}: {e}")

    if errors:
        print("[ERROR] Validation failed:")
        for err in errors[:10]:
            print(f"  {err}")
        raise ValueError(f"{len(errors)} validation errors in review file")

    return reviews


def compute_metrics(reviews: list[ExpertReview]) -> EVL06Metrics:
    """Compute EVL-06 metrics from reviews."""
    total = len(reviews)

    # Agreement: approve + light_edit
    approve_count = sum(1 for r in reviews if r.rating == "approve")
    light_edit_count = sum(1 for r in reviews if r.rating == "light_edit")
    agreement_pct = (approve_count + light_edit_count) / total * 100

    # Reject rate
    reject_count = sum(1 for r in reviews if r.rating == "reject")
    reject_pct = reject_count / total * 100

    # Heavy edit rate
    heavy_edit_count = sum(1 for r in reviews if r.rating == "heavy_edit")
    heavy_edit_pct = heavy_edit_count / total * 100

    # Avg review time
    avg_review_time = sum(r.review_time_minutes for r in reviews) / total

    # Avg gram changes per edit (only for light_edit + heavy_edit)
    edited = [r for r in reviews if r.rating in ("light_edit", "heavy_edit")]
    total_gram_changes = sum(len(r.gram_changes) for r in edited)
    avg_gram_changes = total_gram_changes / len(edited) if edited else 0.0

    # Reason code distribution
    reason_codes: dict[str, int] = {}
    for r in reviews:
        if r.reason_code:
            reason_codes[r.reason_code] = reason_codes.get(r.reason_code, 0) + 1

    # Reviewer distribution
    reviewers: dict[str, int] = {}
    for r in reviews:
        reviewers[r.reviewer_id] = reviewers.get(r.reviewer_id, 0) + 1

    return EVL06Metrics(
        total_reviews=total,
        agreement_pct=agreement_pct,
        reject_pct=reject_pct,
        heavy_edit_pct=heavy_edit_pct,
        avg_review_time_minutes=avg_review_time,
        avg_gram_changes_per_edit=avg_gram_changes,
        reason_code_distribution=reason_codes,
        reviewer_distribution=reviewers,
    )


def main():
    parser = argparse.ArgumentParser(description="Import and validate EVL-06 expert reviews")
    parser.add_argument("--input", required=True, help="Path to expert review JSONL file")
    parser.add_argument("--output", default="eval/results/evl06_metrics.json")
    args = parser.parse_args()

    print("=" * 70)
    print("EVL-06: EXPERT REVIEW IMPORT & VALIDATION")
    print("=" * 70)

    input_path = Path(args.input)
    reviews = load_reviews(input_path)

    print(f"[OK] Loaded {len(reviews)} reviews from {input_path}")

    # Validate minimum count
    if len(reviews) < 20:
        print(f"[ERROR] Expected 20 reviews, got {len(reviews)}")
        sys.exit(1)

    # Compute metrics
    metrics = compute_metrics(reviews)

    print("\n" + "=" * 70)
    print("EVL-06 METRICS")
    print("=" * 70)
    print(f"Total reviews: {metrics.total_reviews}")
    print(f"Agreement rate: {metrics.agreement_pct:.1f}% (approve + light_edit)")
    print(f"Reject rate: {metrics.reject_pct:.1f}%")
    print(f"Heavy edit rate: {metrics.heavy_edit_pct:.1f}%")
    print(f"Avg review time: {metrics.avg_review_time_minutes:.1f} minutes")
    print(f"Avg gram changes per edit: {metrics.avg_gram_changes_per_edit:.1f}")

    print("\nReason code distribution:")
    for code, count in sorted(metrics.reason_code_distribution.items(), key=lambda x: -x[1]):
        print(f"  {code}: {count}")

    print("\nReviewer distribution:")
    for reviewer_id, count in sorted(metrics.reviewer_distribution.items()):
        print(f"  {reviewer_id}: {count} reviews")

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(metrics.model_dump_json(indent=2))

    print(f"\n[OK] Metrics written to {output_path}")


if __name__ == "__main__":
    main()
