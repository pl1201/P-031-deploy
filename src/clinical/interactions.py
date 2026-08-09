"""Verified-only drug-food interaction seed loader.

LLM: NO. Unverified rows may be inventoried for reviewer warnings but are never
converted into automatic clinical constraints.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DEFAULT_INTERACTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "seeds" / "drug_food_interactions.csv"


@dataclass(frozen=True)
class DrugFoodInteraction:
    interaction_id: str
    drug_name: str
    food_or_nutrient: str
    severity: str
    recommendation_vi: str
    source_ref: str
    verify_status: str

    def applies_to(self, medication: str) -> bool:
        medication = medication.casefold()
        drug = self.drug_name.casefold()
        return drug in medication or medication in drug


def load_drug_food_interactions(path: Path | None = None, *, verified_only: bool = True) -> list[DrugFoodInteraction]:
    rows: list[DrugFoodInteraction] = []
    with open(path or DEFAULT_INTERACTIONS_PATH, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            status = (row.get("verify_status") or "to_verify").strip().lower()
            if verified_only and status != "verified":
                continue
            rows.append(
                DrugFoodInteraction(
                    interaction_id=(row.get("id") or "").strip(),
                    drug_name=row["drug_name"].strip(),
                    food_or_nutrient=row["food_or_nutrient"].strip(),
                    severity=row["severity"].strip().lower(),
                    recommendation_vi=row["recommendation_vi"].strip(),
                    source_ref=(row.get("source_ref") or "").strip(),
                    verify_status=status,
                )
            )
    return rows


__all__ = ["DrugFoodInteraction", "load_drug_food_interactions"]
