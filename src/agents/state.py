"""State schema cho LangGraph agent.

Ticket: AGT-01

RULE R20.4: state là nguồn sự thật DUY NHẤT. Không biến global, không cache ngoài,
không truyền dữ liệu ngầm giữa các node.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field, model_validator

from src.clinical.models import (
    ClinicalTargets,
    MenuDraft,
    NutritionSummary,
    PatientProfile,
    Violation,
)

PlanStatus = Literal[
    "drafting",
    "manual_review_required",
    "pending_review",
    "approved",
    "rejected",
    "published",
    "failed",
]

MAX_RETRIES = 3


class RiskSeverity(str, Enum):
    P0 = "P0"  # blocking, never reviewer-overridable
    P1 = "P1"  # reviewer override requires a reason
    P2 = "P2"  # warning only


class SafetyFinding(BaseModel):
    """Typed clinical finding shared by graph, API and reviewer UI."""

    code: str
    risk_level: RiskSeverity
    category: Literal[
        "target_conflict",
        "unverified_rule",
        "nutrient",
        "allergy",
        "drug_food",
        "medication_timing",
        "incomplete_data",
        "generation",
        "culinary",
    ]
    message_vi: str
    suggestion: str | None = None
    rule_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    reviewer_override_allowed: bool = False

    @model_validator(mode="after")
    def enforce_override_policy(self) -> SafetyFinding:
        if self.risk_level is RiskSeverity.P0 and self.reviewer_override_allowed:
            raise ValueError("P0 findings can never be reviewer-overridden")
        if self.risk_level is RiskSeverity.P1:
            self.reviewer_override_allowed = True
        return self

    @property
    def blocking(self) -> bool:
        return self.risk_level is RiskSeverity.P0


class ReviewPacket(BaseModel):
    highest_risk: Literal["P0", "P1", "P2", "none"] = "none"
    can_approve: bool = False
    used_fallback: bool = False
    target_gate_reasons: list[str] = Field(default_factory=list)
    findings: list[SafetyFinding] = Field(default_factory=list)
    summary: str = ""


class Citation(BaseModel):
    source_ref: str
    title: str | None = None
    rule_ids: list[str] = Field(default_factory=list)


class ProfileCompleteness(BaseModel):
    is_complete: bool = True
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TargetConflict(BaseModel):
    code: str = "TARGET_CONFLICT"
    message: str
    rule_ids: list[str] = Field(default_factory=list)


class GenerationAttempt(BaseModel):
    attempt_no: int
    source: Literal["cpsat", "gemini", "fallback"]
    status: Literal["generated", "failed", "fallback"]
    at: datetime
    feedback_used: bool = False
    error: str | None = None


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class StructuredError(BaseModel):
    code: str
    message: str
    node: str
    retriable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    at: datetime
    node: str
    action: str
    duration_ms: int | None = None
    output_fields: list[str] = Field(default_factory=list)


class SafetyConstraints(BaseModel):
    schema_version: str = "1.0"
    excluded_food_ids: list[int] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    hard_nutrient_bounds: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    medication_interactions: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_medications: list[str] = Field(default_factory=list)


class NutriState(TypedDict, total=False):
    # Identity/version
    run_id: str
    trace_id: str
    plan_id: str
    patient_id: str  # backward-compatible graph input alias
    profile_id: str
    profile_version: str
    rule_version: str
    food_data_version: str
    interaction_version: str
    prompt_version: str

    # Clinical
    profile: PatientProfile
    profile_snapshot_hash: str
    completeness: ProfileCompleteness
    targets: ClinicalTargets
    target_conflicts: list[TargetConflict]
    unverified_rule_ids: list[str]
    target_gate_reasons: list[str]
    safety_constraints: SafetyConstraints

    # Retrieval — checkpoint IDs, never large candidate objects
    candidate_ids: list[int]
    guideline_chunk_ids: list[str]

    # Generation
    draft_menu: MenuDraft | None
    menu_version: int
    menu_hash: str | None
    generation_source: Literal["cpsat", "gemini", "fallback"]
    attempt_count: int
    attempt_history: list[GenerationAttempt]
    retry_count: int  # compatibility alias for existing routing/tests
    feedback: str | None
    used_fallback: bool

    # Deterministic results
    computed_nutrition: NutritionSummary | None
    nutrition_hash: str | None
    violations: list[Violation]
    safety_findings: list[SafetyFinding]
    highest_risk: Literal["P0", "P1", "P2", "none"]

    # Explainability
    citations: list[Citation]
    expert_explanation: str | None
    patient_explanation: str | None

    # HITL
    status: PlanStatus
    review_packet: ReviewPacket
    reviewer_id: str | None
    review_decision: str | None
    reviewer_notes: str | None
    approved_menu_version: int | None
    needs_attention: bool

    # Operations
    node_timings_ms: dict[str, int]
    token_usage: TokenUsage
    last_error: StructuredError | None
    audit_events: list[AuditEvent]
