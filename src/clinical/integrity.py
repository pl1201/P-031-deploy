"""Deterministic integrity hashes and the patient publication gate.

LLM: NO. Hashes are calculated only from server-computed menu/nutrition data.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from src.clinical.models import MenuDraft, NutritionSummary


def _sha256(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def hash_menu(draft: MenuDraft) -> str:
    items = [
        {"slot": slot.value, "food_id": item.food_id, "grams": round(float(item.grams), 4)}
        for slot, menu_items in draft.items.items()
        for item in menu_items
    ]
    items.sort(key=lambda row: (row["slot"], row["food_id"], row["grams"]))
    return _sha256(items)


def hash_nutrition(nutrition: NutritionSummary | dict[str, Any]) -> str:
    payload = nutrition.model_dump(mode="json") if isinstance(nutrition, NutritionSummary) else nutrition
    return _sha256(payload)


def payload_has_p0(violations: list[dict[str, Any]] | None, highest_risk: str | None = None) -> bool:
    if highest_risk == "P0":
        return True
    return any(
        finding.get("risk_level") == "P0" or finding.get("severity") == "hard" or finding.get("blocking") is True
        for finding in (violations or [])
    )


def publish_gate_open(plan: Any) -> bool:
    """Return True only for an unchanged, approved and P0-free plan."""
    return bool(
        plan.status == "approved"
        and not payload_has_p0(plan.violations, getattr(plan, "highest_risk", None))
        and plan.menu_hash
        and plan.nutrition_hash
        and plan.menu_version == plan.approved_menu_version
        and plan.menu_hash == plan.approved_menu_hash
        and plan.nutrition_hash == plan.approved_nutrition_hash
    )


__all__ = ["hash_menu", "hash_nutrition", "payload_has_p0", "publish_gate_open"]
