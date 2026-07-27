"""Các node của LangGraph agent.

Mỗi node khai báo rõ có gọi LLM hay không (RULE R20.1).

| Node                | LLM |
|---------------------|-----|
| load_profile        | NO  |
| compute_targets     | NO  |
| retrieve_context    | NO  |
| generate_menu       | YES |
| compute_nutrition   | NO  |
| validate            | NO  |
| build_feedback      | NO  |
| fallback            | NO  |

Ticket: AGT-02..AGT-06
"""

from __future__ import annotations

from typing import Protocol

from src.agents.state import MAX_RETRIES, NutriState
from src.clinical.models import (
    ClinicalTargets,
    MenuDraft,
    PatientProfile,
)
from src.clinical.nutrition import (
    FoodRepository,
    UnknownFoodError,
    check_allergies,
    compute_nutrition,
)
from src.clinical.rules import ClinicalRule, compute_targets, load_rules
from src.clinical.validator import build_feedback, has_blocking, validate_menu


# --------------------------------------------------------------------------
# Cổng ra ngoài — cho phép test inject bản giả, và cho phép đổi LLM provider
# mà không đụng vào tầng deterministic.
# --------------------------------------------------------------------------
class ProfileRepository(Protocol):
    def get(self, patient_id: str) -> PatientProfile | None: ...


class MenuGenerator(Protocol):
    """Cổng gọi LLM.

    ⚠️ RULE-1: bản cài đặt thật PHẢI dùng structured output trả về MenuDraft,
    tức là CHỈ food_id + grams. Không bao giờ nhận giá trị dinh dưỡng từ LLM.
    """

    def generate(
        self,
        profile: PatientProfile,
        targets: ClinicalTargets,
        candidates: list,
        feedback: str | None,
    ) -> MenuDraft: ...


class FallbackMenuProvider(Protocol):
    """Thực đơn mẫu theo bệnh lý, dùng khi agent hết lượt retry."""

    def get(self, profile: PatientProfile) -> MenuDraft | None: ...


# --------------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------------
def make_load_profile(profiles: ProfileRepository):
    """Node: load_profile — LLM: NO."""

    def load_profile(state: NutriState) -> dict:
        profile = profiles.get(state["patient_id"])
        if profile is None:
            return {"status": "failed", "feedback": "Không tìm thấy hồ sơ bệnh nhân."}
        return {"profile": profile, "status": "drafting", "retry_count": 0}

    return load_profile


def make_compute_targets(rules: list[ClinicalRule] | None = None):
    """Node: compute_targets — LLM: NO. Deterministic hoàn toàn."""
    rules = rules if rules is not None else load_rules()

    def compute_targets_node(state: NutriState) -> dict:
        targets = compute_targets(state["profile"], rules)
        out: dict = {"targets": targets}
        if targets.needs_expert_review:
            # Xung đột ngưỡng không giải được → không tự quyết (RULE R10.5)
            out["status"] = "pending_review"
            out["needs_attention"] = True
        return out

    return compute_targets_node


def make_retrieve_context(foods: FoodRepository):
    """Node: retrieve_context — LLM: NO.

    Lọc sẵn danh sách ứng viên theo dị ứng và bệnh lý, để LLM không bao giờ
    nhìn thấy thực phẩm cấm. Chặn ở đầu vào rẻ hơn chặn ở đầu ra.
    """

    def retrieve_context(state: NutriState) -> dict:
        profile: PatientProfile = state["profile"]
        all_items = foods.all() if hasattr(foods, "all") else []
        candidates = [
            f
            for f in all_items
            if not any(a in profile.allergies for a in map(str.lower, f.contains_allergens))
            and f.name_vi.lower() not in profile.dislikes
        ]
        return {"candidate_foods": candidates}

    return retrieve_context


def make_generate_menu(generator: MenuGenerator):
    """Node: generate_menu — LLM: YES.

    Đây là node DUY NHẤT trong luồng sinh thực đơn được phép gọi LLM.
    Output đi qua schema MenuDraft, tức chỉ có food_id + grams.
    """

    def generate_menu(state: NutriState) -> dict:
        draft = generator.generate(
            profile=state["profile"],
            targets=state["targets"],
            candidates=state.get("candidate_foods", []),
            feedback=state.get("feedback"),
        )
        return {"draft_menu": draft, "retry_count": state.get("retry_count", 0) + 1}

    return generate_menu


def make_compute_nutrition(foods: FoodRepository):
    """Node: compute_nutrition — LLM: NO. Nơi RULE-1 được thực thi."""

    def compute_nutrition_node(state: NutriState) -> dict:
        try:
            summary = compute_nutrition(state["draft_menu"], foods)
        except UnknownFoodError as exc:
            # LLM bịa food_id → không đoán thay thế, ép sinh lại
            return {
                "computed_nutrition": None,
                "violations": [],
                "feedback": (
                    f"{exc} Chỉ được chọn food_id có trong danh sách ứng viên được cung cấp."
                ),
            }
        return {"computed_nutrition": summary}

    return compute_nutrition_node


def make_validate(foods: FoodRepository, rules: list[ClinicalRule] | None = None):
    """Node: validate — LLM: NO. Guardrail tầng 3, fail closed."""
    rules = rules if rules is not None else load_rules()

    def validate_node(state: NutriState) -> dict:
        nutrition = state.get("computed_nutrition")
        if nutrition is None:
            return {"violations": []}
        violations = validate_menu(nutrition, state["targets"], rules)
        violations += check_allergies(state["draft_menu"], state["profile"], foods)
        return {"violations": violations}

    return validate_node


def build_feedback_node(state: NutriState) -> dict:
    """Node: build_feedback — LLM: NO."""
    nutrition = state.get("computed_nutrition")
    if nutrition is None:
        return {"feedback": state.get("feedback") or "Thực đơn không hợp lệ, hãy chọn lại món."}
    return {"feedback": build_feedback(state["violations"], nutrition)}


def make_fallback(provider: FallbackMenuProvider, foods: FoodRepository):
    """Node: fallback — LLM: NO.

    Hết lượt retry thì dùng thực đơn mẫu đã được chuyên gia soạn sẵn cho từng
    bệnh lý, gắn cờ needs_attention. Không bao giờ phát hành thực đơn vi phạm.
    """

    def fallback(state: NutriState) -> dict:
        draft = provider.get(state["profile"])
        if draft is None:
            return {
                "status": "failed",
                "needs_attention": True,
                "used_fallback": True,
            }
        nutrition = compute_nutrition(draft, foods)
        return {
            "draft_menu": draft,
            "computed_nutrition": nutrition,
            "used_fallback": True,
            "needs_attention": True,
            "status": "pending_review",
        }

    return fallback


def to_review(state: NutriState) -> dict:
    """Node: to_review — LLM: NO. Đưa vào hàng chờ HITL.

    RULE-3: không có đường nào đi thẳng từ đây tới bệnh nhân.
    """
    return {"status": "pending_review"}


# --------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------
def route_after_load(state: NutriState) -> str:
    """Thoát sớm nếu không nạp được hồ sơ — không chạy tiếp với state khuyết."""
    return "end" if state.get("status") == "failed" else "continue"


def route_after_validate(state: NutriState) -> str:
    """Conditional edge sau node validate."""
    nutrition = state.get("computed_nutrition")
    violations = state.get("violations", [])
    retry = state.get("retry_count", 0)

    if nutrition is not None and not has_blocking(violations):
        return "to_review"
    if retry >= MAX_RETRIES:
        return "fallback"
    return "build_feedback"
