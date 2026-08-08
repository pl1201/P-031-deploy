"""LangGraph StateGraph cho luồng lập thực đơn.

Ticket: AGT-01, AGT-06, HIT-01

Luồng chính:
    load_profile → compute_targets → target_gate → retrieve_context_bundle
      → build_safety_constraints → generate_menu → compute_nutrition
      → safety_validate → risk_triage ─┬─ safe/P1/P2 → explain → review_packet → HITL
                                       ├─ P0 & retry<3 → feedback ↺ generate_menu
                                       └─ P0 & retry=3 → fallback_template ↺ compute_nutrition

Target conflict/rule chưa verified đi thẳng tới manual review. Fallback không
có edge tới END; mọi fallback đều phải được tính lại và kiểm định trước HITL.

Graph dừng ở `to_review` (interrupt_before) và chỉ đi tiếp khi chuyên gia
duyệt — đây là chỗ RULE-3 được thực thi ở tầng orchestration.
"""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.nodes.core import (
    FallbackMenuProvider,
    MenuGenerator,
    ProfileRepository,
    build_feedback_node,
    explain_with_citations,
    make_build_safety_constraints,
    make_compute_nutrition,
    make_compute_targets,
    make_fallback,
    make_generate_menu,
    make_load_profile,
    make_retrieve_context,
    make_validate,
    prepare_manual_review,
    prepare_review_packet,
    risk_triage,
    route_after_load,
    route_after_target_gate,
    route_after_validate,
    target_gate,
    to_review,
)
from src.agents.state import AuditEvent, NutriState
from src.clinical.nutrition import FoodRepository
from src.clinical.rules import ClinicalRule


def _instrument(node_name, node):
    """Record per-node latency and an append-only, PHI-minimal audit event."""

    def instrumented(state: NutriState) -> dict:
        started = perf_counter()
        update = node(state)
        duration_ms = max(0, round((perf_counter() - started) * 1000))
        timings = dict(state.get("node_timings_ms", {}))
        timings[node_name] = timings.get(node_name, 0) + duration_ms
        events = list(state.get("audit_events", []))
        events.append(
            AuditEvent(
                at=datetime.now(UTC),
                node=node_name,
                action="node_completed",
                duration_ms=duration_ms,
                output_fields=sorted(update),
            )
        )
        return {**update, "node_timings_ms": timings, "audit_events": events}

    return instrumented


def build_graph(
    *,
    profiles: ProfileRepository,
    foods: FoodRepository,
    generator: MenuGenerator,
    fallback_provider: FallbackMenuProvider,
    rules: list[ClinicalRule] | None = None,
    checkpointer=None,
    interrupt_for_hitl: bool = True,
):
    """Dựng và compile graph.

    `interrupt_for_hitl=True` khiến graph dừng TRƯỚC node to_review, để backend
    lưu bản nháp và chờ chuyên gia. Đặt False trong test tự động.
    """
    builder = StateGraph(NutriState)

    builder.add_node("load_profile", _instrument("load_profile", make_load_profile(profiles)))
    builder.add_node("compute_targets", _instrument("compute_targets", make_compute_targets(rules)))
    builder.add_node("target_gate", _instrument("target_gate", target_gate))
    builder.add_node("retrieve_context_bundle", _instrument("retrieve_context_bundle", make_retrieve_context(foods)))
    builder.add_node(
        "build_safety_constraints", _instrument("build_safety_constraints", make_build_safety_constraints(foods))
    )
    builder.add_node("generate_menu", _instrument("generate_menu", make_generate_menu(generator, foods)))
    builder.add_node("compute_nutrition", _instrument("compute_nutrition", make_compute_nutrition(foods)))
    builder.add_node("safety_validate", _instrument("safety_validate", make_validate(foods, rules)))
    builder.add_node("build_feedback", _instrument("build_feedback", build_feedback_node))
    builder.add_node("fallback_template", _instrument("fallback_template", make_fallback(fallback_provider, foods)))
    builder.add_node("risk_triage", _instrument("risk_triage", risk_triage))
    builder.add_node("prepare_manual_review", _instrument("prepare_manual_review", prepare_manual_review))
    builder.add_node("prepare_review_packet", _instrument("prepare_review_packet", prepare_review_packet))
    builder.add_node("explain_with_citations", _instrument("explain_with_citations", explain_with_citations))
    builder.add_node("to_review", _instrument("to_review", to_review))

    builder.add_edge(START, "load_profile")
    builder.add_conditional_edges(
        "load_profile",
        route_after_load,
        {"continue": "compute_targets", "end": END},
    )
    builder.add_edge("compute_targets", "target_gate")
    builder.add_conditional_edges(
        "target_gate",
        route_after_target_gate,
        {"continue": "retrieve_context_bundle", "manual_review": "prepare_manual_review"},
    )
    builder.add_edge("prepare_manual_review", "explain_with_citations")
    builder.add_edge("retrieve_context_bundle", "build_safety_constraints")
    builder.add_edge("build_safety_constraints", "generate_menu")
    builder.add_edge("generate_menu", "compute_nutrition")
    builder.add_edge("compute_nutrition", "safety_validate")
    builder.add_edge("safety_validate", "risk_triage")

    builder.add_conditional_edges(
        "risk_triage",
        route_after_validate,
        {
            "prepare_review": "explain_with_citations",
            "build_feedback": "build_feedback",
            "fallback": "fallback_template",
        },
    )
    builder.add_edge("build_feedback", "generate_menu")
    builder.add_edge("fallback_template", "compute_nutrition")
    builder.add_edge("explain_with_citations", "prepare_review_packet")
    builder.add_edge("prepare_review_packet", "to_review")
    builder.add_edge("to_review", END)

    kwargs = {}
    if checkpointer is not None:
        kwargs["checkpointer"] = checkpointer
        if interrupt_for_hitl:
            kwargs["interrupt_before"] = ["to_review"]

    return builder.compile(**kwargs)


def build_graph_with_memory(**kwargs):
    """Tiện ích cho dev/test: checkpointer in-memory.

    Production dùng PostgresSaver — xem ADR-004 trong ARCHITECTURE.md.
    """
    return build_graph(checkpointer=MemorySaver(), **kwargs)


def build_review_recompute_graph(*, foods: FoodRepository, rules: list[ClinicalRule] | None = None):
    """Downstream-only graph used after a reviewer edits menu grams.

    It deliberately contains no retrieval, optimizer, fallback or LLM generation
    node, so a UI edit cannot silently replace the reviewer's menu.
    """
    builder = StateGraph(NutriState)
    builder.add_node("compute_nutrition", _instrument("compute_nutrition", make_compute_nutrition(foods)))
    builder.add_node("safety_validate", _instrument("safety_validate", make_validate(foods, rules)))
    builder.add_node("risk_triage", _instrument("risk_triage", risk_triage))
    builder.add_node("explain_with_citations", _instrument("explain_with_citations", explain_with_citations))
    builder.add_node("prepare_review_packet", _instrument("prepare_review_packet", prepare_review_packet))
    builder.add_edge(START, "compute_nutrition")
    builder.add_edge("compute_nutrition", "safety_validate")
    builder.add_edge("safety_validate", "risk_triage")
    builder.add_edge("risk_triage", "explain_with_citations")
    builder.add_edge("explain_with_citations", "prepare_review_packet")
    builder.add_edge("prepare_review_packet", END)
    return builder.compile()
