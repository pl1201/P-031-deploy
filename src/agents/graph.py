"""LangGraph StateGraph cho luồng lập thực đơn.

Ticket: AGT-01, AGT-06, HIT-01

Luồng:
    load_profile → compute_targets → retrieve_context → generate_menu
      → compute_nutrition → validate ─┬─ PASS ──────────→ to_review → [HITL] → END
                                      ├─ FAIL & retry<3 → build_feedback ↺ generate_menu
                                      └─ FAIL & retry=3 → fallback → END

Graph dừng ở `to_review` (interrupt_before) và chỉ đi tiếp khi chuyên gia
duyệt — đây là chỗ RULE-3 được thực thi ở tầng orchestration.
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.nodes.core import (
    FallbackMenuProvider,
    MenuGenerator,
    ProfileRepository,
    build_feedback_node,
    make_compute_nutrition,
    make_compute_targets,
    make_fallback,
    make_generate_menu,
    make_load_profile,
    make_retrieve_context,
    make_validate,
    route_after_load,
    route_after_validate,
    to_review,
)
from src.agents.state import NutriState
from src.clinical.nutrition import FoodRepository
from src.clinical.rules import ClinicalRule


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

    builder.add_node("load_profile", make_load_profile(profiles))
    builder.add_node("compute_targets", make_compute_targets(rules))
    builder.add_node("retrieve_context", make_retrieve_context(foods))
    builder.add_node("generate_menu", make_generate_menu(generator))
    builder.add_node("compute_nutrition", make_compute_nutrition(foods))
    builder.add_node("validate", make_validate(foods, rules))
    builder.add_node("build_feedback", build_feedback_node)
    builder.add_node("fallback", make_fallback(fallback_provider, foods))
    builder.add_node("to_review", to_review)

    builder.add_edge(START, "load_profile")
    builder.add_conditional_edges(
        "load_profile",
        route_after_load,
        {"continue": "compute_targets", "end": END},
    )
    builder.add_edge("compute_targets", "retrieve_context")
    builder.add_edge("retrieve_context", "generate_menu")
    builder.add_edge("generate_menu", "compute_nutrition")
    builder.add_edge("compute_nutrition", "validate")

    builder.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "to_review": "to_review",
            "build_feedback": "build_feedback",
            "fallback": "fallback",
        },
    )
    builder.add_edge("build_feedback", "generate_menu")
    builder.add_edge("fallback", END)
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


# --- Backward compatibility wrapper for skeleton API routing and tests ---


class AgentState(TypedDict, total=False):
    query: str
    context: str
    analysis: str
    response: str
    error: str
    metadata: dict


def _analyze_node(state: AgentState) -> dict:
    query = state.get("query", "")
    if not query:
        return {"error": "Empty query"}
    return {"analysis": f"Analyzing query: {query}"}


def _respond_node(state: AgentState) -> dict:
    analysis = state.get("analysis", "")
    return {"response": f"Response based on analysis: {analysis}"}


def _should_continue(state: AgentState) -> str:
    if state.get("error"):
        return END
    return "respond"


_builder = StateGraph(AgentState)
_builder.add_node("analyze", _analyze_node)
_builder.add_node("respond", _respond_node)
_builder.set_entry_point("analyze")
_builder.add_conditional_edges("analyze", _should_continue)
_builder.add_edge("respond", END)
agent = _builder.compile()
