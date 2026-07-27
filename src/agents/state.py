"""State schema cho LangGraph agent.

Ticket: AGT-01

RULE R20.4: state là nguồn sự thật DUY NHẤT. Không biến global, không cache ngoài,
không truyền dữ liệu ngầm giữa các node.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from src.clinical.models import (
    ClinicalTargets,
    FoodItem,
    MenuDraft,
    NutritionSummary,
    PatientProfile,
    Violation,
)

PlanStatus = Literal[
    "drafting", "pending_review", "approved", "rejected", "published", "failed"
]

MAX_RETRIES = 3


class NutriState(TypedDict, total=False):
    # --- Đầu vào ---
    patient_id: str
    trace_id: str

    # --- Deterministic (không LLM) ---
    profile: PatientProfile
    targets: ClinicalTargets
    candidate_foods: list[FoodItem]

    # --- Vòng lặp agent ---
    draft_menu: MenuDraft | None
    computed_nutrition: NutritionSummary | None
    violations: list[Violation]
    retry_count: int
    feedback: str | None
    used_fallback: bool

    # --- HITL ---
    status: PlanStatus
    reviewer_id: str | None
    reviewer_notes: str | None
    needs_attention: bool
