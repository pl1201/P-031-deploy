"""Các node của LangGraph agent.

Mỗi node khai báo rõ có gọi LLM hay không (RULE R20.1).

| Node                | LLM |
|---------------------|-----|
| load_profile        | NO  |
| compute_targets     | NO  |
| retrieve_context_bundle | NO |
| build_safety_constraints | NO |
| generate_menu       | YES |
| compute_nutrition   | NO  |
| safety_validate     | NO  |
| risk_triage         | NO  |
| build_feedback      | NO  |
| fallback_template   | NO  |
| explain_with_citations | NO |
| prepare_review_packet | NO |

Ticket: AGT-02..AGT-06
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol
from uuid import uuid4

from src.agents.state import (
    MAX_RETRIES,
    Citation,
    GenerationAttempt,
    NutriState,
    ProfileCompleteness,
    ReviewPacket,
    RiskSeverity,
    SafetyConstraints,
    SafetyFinding,
    StructuredError,
    TargetConflict,
    TokenUsage,
)
from src.clinical.integrity import hash_menu, hash_nutrition
from src.clinical.medical_nutrition import is_eligible_candidate
from src.clinical.interactions import (
    advisories_for,
    check_drug_food_interactions,
    load_drug_food_rules,
)
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
from src.clinical.rules import ClinicalRule, _select_rules, compute_targets, load_rules
from src.clinical.validator import build_feedback, validate_menu


def _stable_hash(payload) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _version_for_rules(rules: list[ClinicalRule]) -> str:
    return _stable_hash([(rule.rule_id, rule.verify_status) for rule in rules])[:16]


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
        profile_hash = _stable_hash(profile.model_dump(mode="json"))
        warnings: list[str] = []
        if any(condition.code.value == "CKD" and not condition.stage for condition in profile.conditions):
            warnings.append("CKD profile is missing a stage/eGFR-derived classification.")
        return {
            "run_id": state.get("run_id") or str(uuid4()),
            "trace_id": state.get("trace_id") or str(uuid4()),
            "plan_id": state.get("plan_id") or state.get("trace_id") or str(uuid4()),
            "profile_id": profile.patient_id,
            "profile": profile,
            "profile_snapshot_hash": profile_hash,
            "profile_version": profile_hash[:16],
            "completeness": ProfileCompleteness(is_complete=not warnings, warnings=warnings),
            "status": "drafting",
            "retry_count": 0,
            "attempt_count": 0,
            "attempt_history": [],
            "menu_version": 0,
            "guideline_chunk_ids": [],
            "node_timings_ms": {},
            "token_usage": TokenUsage(),
            "last_error": None,
            "audit_events": [],
        }

    return load_profile


def make_compute_targets(rules: list[ClinicalRule] | None = None):
    """Node: compute_targets — LLM: NO. Deterministic hoàn toàn.

    DEC-014/DEC-020 (DEVLOG.md §3): dùng CẢ rule `to_verify` để tính ngưỡng —
    không fail-closed tuyệt đối trên verify_status. Đối chiếu tài liệu kế
    hoạch gốc (`KeHoachDuAn_VNutriCare_VMEC10_v3.docx` §6.4.1) xác nhận
    `needs_expert_review` chỉ kích hoạt khi rule THẬT SỰ xung đột (min>max
    sau hợp nhất), không phải cho mọi rule chưa verified — giữ fail-closed
    tuyệt đối (bản trước) khiến `compute_targets()` chỉ còn tính được ngưỡng
    năng lượng vì toàn bộ 21 rule trong seed hiện tại đều `to_verify`.
    """
    rule_inventory = rules if rules is not None else load_rules(verified_only=False)

    def compute_targets_node(state: NutriState) -> dict:
        targets = compute_targets(state["profile"], rule_inventory)
        applicable, disabled = _select_rules(state["profile"], rule_inventory)
        unverified = sorted(rule.rule_id for rule in (*applicable, *disabled) if rule.verify_status != "verified")
        out: dict = {
            "targets": targets,
            "target_conflicts": [TargetConflict(message=note) for note in targets.conflict_notes],
            "unverified_rule_ids": unverified,
            "rule_version": _version_for_rules(rule_inventory),
        }
        if targets.needs_expert_review:
            # Xung đột ngưỡng không giải được → không tự quyết (RULE R10.5)
            out["status"] = "pending_review"
            out["needs_attention"] = True
        return out

    return compute_targets_node


def target_gate(state: NutriState) -> dict:
    """Fail closed CHỈ khi ngưỡng có xung đột thật (DEC-014/DEC-020) — rule
    `to_verify` không chặn, chỉ được ghi lại thành `SafetyFinding` P1 để
    chuyên gia soát (`reviewer_override_allowed`), không phải lý do dừng
    generator. Trước đây coi mọi `unverified_rule_ids` là lý do
    `manual_review_required` — với seed hiện tại (21/21 rule `to_verify`)
    nghĩa là MỌI thực đơn đều bị chặn trước generator, mâu thuẫn với DEC-020.
    """
    targets = state["targets"]
    unverified = state.get("unverified_rule_ids", [])
    unverified_findings = [
        SafetyFinding(
            code="UNVERIFIED_RULE",
            risk_level=RiskSeverity.P1,
            category="unverified_rule",
            message_vi=f"Quy tắc {rule_id} chưa được xác minh.",
            rule_id=rule_id,
            reviewer_override_allowed=True,
        )
        for rule_id in unverified
    ]
    if targets.conflict_notes or targets.needs_expert_review:
        findings = [
            SafetyFinding(
                code="TARGET_CONFLICT",
                risk_level=RiskSeverity.P0,
                category="target_conflict",
                message_vi=reason,
            )
            for reason in targets.conflict_notes
        ] + unverified_findings
        return {
            "status": "manual_review_required",
            "needs_attention": True,
            "target_gate_reasons": list(targets.conflict_notes),
            "safety_findings": findings,
        }
    return {"target_gate_reasons": [], "safety_findings": unverified_findings}


# `food_items.csv` từ DAT-12 gồm ~150 dòng curated (id nội bộ tuần tự, nhỏ) +
# ~6.850 dòng USDA FoodData Central bulk (SR Legacy/Foundation, id = fdc_id
# gốc, luôn ≥ 100000 — xem `data/README.md`). Khối bulk là KHO THAM CHIẾU
# (tra cứu, OOV, mở rộng sau), KHÔNG dùng làm ứng viên sinh thực đơn: đưa cả
# ~7000 dòng vào CP-SAT/prompt LLM làm chậm CP-SAT ~30-50 lần (đo thực tế:
# 13 test từ ~1,5s lên ~50s) và làm prompt Gemini phình to vô ích — phần lớn
# là thực phẩm Mỹ/quốc tế không phù hợp bối cảnh bệnh nhân Việt Nam.
USDA_BULK_ID_THRESHOLD = 100_000

# Khối tham chiếu cần loại = ĐÚNG những dòng import bulk từ USDA (source="USDA"
# VÀ id là fdc_id gốc ≥ ngưỡng). Mọi dòng khác — NIN, curated, estimated — đều
# là thực phẩm Việt Nam do đội biên soạn và LÀ ứng viên, bất kể id.
#
# Sửa 2026-08-08 (DAT-24): ngưỡng id một mình là proxy cho "thuộc khối USDA
# bulk", và proxy đó sai. Script merge NIN 2017 cấp id nối tiếp dãy fdc_id nên
# 82 thực phẩm Việt Nam THẬT của Viện Dinh dưỡng (Vừng, Cà rốt, Cải thìa, Giá
# đậu xanh, Ớt đỏ, Đậu tương…) nhận id ≥ 1.105.898 và bị loại nhầm khỏi ứng
# viên CP-SAT — đúng nhóm nguyên liệu mà công thức món Việt cần nhất.
USDA_BULK_SOURCE = "USDA"


def _la_khoi_usda_bulk(food) -> bool:
    """True khi dòng thuộc khối import bulk USDA (kho tham chiếu, không phải ứng viên)."""
    return food.source == USDA_BULK_SOURCE and food.id >= USDA_BULK_ID_THRESHOLD


# Sửa 2026-08-08 (DAT-24): ngưỡng id ở trên là proxy cho "thuộc khối USDA bulk",
# và proxy đó đã sai. Script merge NIN 2017 cấp id nối tiếp dãy fdc_id nên 82
# thực phẩm Việt Nam THẬT của Viện Dinh dưỡng (Vừng, Cà rốt, Cải thìa, Giá đậu
# xanh, Ớt đỏ, Đậu tương…) nhận id ≥ 1.105.898 và bị loại nhầm khỏi ứng viên
# CP-SAT — đúng nhóm nguyên liệu mà công thức món Việt cần nhất. Lọc theo
# `source` là đúng ý định ban đầu ("loại khối bulk Mỹ"), không phải theo id.
VN_CURATED_SOURCES = frozenset({"NIN", "curated"})
RETRIEVAL_TOP_K = 100


def _top_k_candidates(candidates: list, limit: int = RETRIEVAL_TOP_K) -> list:
    """Deterministic multi-objective shortlist that preserves food diversity."""
    if len(candidates) <= limit:
        return candidates
    selected: dict[int, object] = {}
    quota = max(12, limit // 7)
    rankings = (
        lambda food: (not (food.source == "NIN" and food.id >= USDA_BULK_ID_THRESHOLD), -food.kcal_100g, food.id),
        lambda food: (-food.kcal_100g, food.id),
        lambda food: (-food.protein_g, food.id),
        lambda food: (-food.fiber_g, food.id),
        lambda food: (-food.carb_g, food.id),
        lambda food: (-food.fat_g, food.id),
        lambda food: (food.na_mg, -food.kcal_100g, food.id),
        lambda food: (food.purine_mg is None, food.purine_mg or 0, food.id),
    )
    for key in rankings:
        for food in sorted(candidates, key=key)[:quota]:
            selected.setdefault(food.id, food)
            if len(selected) >= limit:
                break
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        for food in sorted(candidates, key=lambda item: (item.source != "NIN", item.name_vi.casefold(), item.id)):
            selected.setdefault(food.id, food)
            if len(selected) >= limit:
                break
    return list(selected.values())


def make_retrieve_context(foods: FoodRepository):
    """Node: retrieve_context — LLM: NO.

    Lọc sẵn danh sách ứng viên theo dị ứng và bệnh lý, để LLM không bao giờ
    nhìn thấy thực phẩm cấm. Chặn ở đầu vào rẻ hơn chặn ở đầu ra. Đồng thời
    loại khối USDA bulk khỏi ứng viên — xem ghi chú ở trên.

    Cũng loại thực phẩm y tế đặc biệt (sữa dinh dưỡng y tế) mà bệnh nhân KHÔNG
    khai đang dùng: dữ liệu hợp lệ nhưng tự ý đưa vào thực đơn là kê một sản
    phẩm thương mại họ không có, và tiến gần tới chỉ định (CLAUDE.md §3). Chi
    tiết ở `src/clinical/medical_nutrition.py`.
    """

    def retrieve_context(state: NutriState) -> dict:
        profile: PatientProfile = state["profile"]
        all_items = foods.all() if hasattr(foods, "all") else []
        candidates = [
            f
            for f in all_items
            if not _la_khoi_usda_bulk(f)
            and is_eligible_candidate(f, profile.medical_nutrition)
            and not any(a in profile.allergies for a in map(str.lower, f.contains_allergens))
            and f.name_vi.lower() not in profile.dislikes
        ]
        version_path = Path(__file__).resolve().parents[3] / "data" / "VERSION"
        data_version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else "unknown"
        return {
            "candidate_ids": [food.id for food in _top_k_candidates(candidates)],
            "food_data_version": data_version,
        }

    return retrieve_context


def make_build_safety_constraints(foods: FoodRepository):
    """Build hard, structured exclusions before either CP-SAT or Gemini sees candidates."""
    inventory = load_drug_food_rules()
    verified = [rule for rule in inventory if rule.verify_status == "verified"]

    def build_safety_constraints(state: NutriState) -> dict:
        profile = state["profile"]
        allergy_set = {value.casefold() for value in profile.allergies}
        dislike_set = {value.casefold() for value in profile.dislikes}
        all_foods = foods.all() if hasattr(foods, "all") else []
        excluded = sorted(
            food.id
            for food in all_foods
            if food.name_vi.casefold() in dislike_set
            or bool({value.casefold() for value in food.contains_allergens} & allergy_set)
        )
        matched_verified = [
            interaction
            for interaction in verified
            if any(interaction.applies_to(medication) for medication in profile.medications)
        ]
        matched_unverified = [
            interaction
            for interaction in inventory
            if interaction.verify_status != "verified"
            and any(interaction.applies_to(medication) for medication in profile.medications)
        ]
        unresolved = sorted(
            {
                medication
                for medication in profile.medications
                if any(interaction.applies_to(medication) for interaction in matched_unverified)
                and not any(interaction.applies_to(medication) for interaction in matched_verified)
            }
        )
        findings = list(state.get("safety_findings", []))
        findings.extend(
            SafetyFinding(
                code="UNVERIFIED_DRUG_FOOD_COVERAGE",
                risk_level=RiskSeverity.P1,
                category="drug_food",
                message_vi=f"Tương tác thực phẩm của thuốc {medication} chưa có rule đã xác minh.",
                reviewer_override_allowed=True,
            )
            for medication in unresolved
        )
        constraints = SafetyConstraints(
            excluded_food_ids=excluded,
            allergens=sorted(allergy_set),
            dislikes=sorted(dislike_set),
            hard_nutrient_bounds={
                nutrient: {"min": target.min_value, "max": target.max_value}
                for nutrient, target in state["targets"].targets.items()
            },
            medication_interactions=[interaction.__dict__ for interaction in matched_verified],
            unresolved_medications=unresolved,
        )
        allowed_ids = [food_id for food_id in state.get("candidate_ids", []) if food_id not in set(excluded)]
        return {
            "safety_constraints": constraints,
            "candidate_ids": allowed_ids,
            "safety_findings": findings,
            "interaction_version": _stable_hash([(item.interaction_id, item.verify_status) for item in inventory])[:16],
        }

    return build_safety_constraints


def make_generate_menu(generator: MenuGenerator, foods: FoodRepository):
    """Node: generate_menu — LLM: YES.

    Đây là node DUY NHẤT trong luồng sinh thực đơn được phép gọi LLM.
    Output đi qua schema MenuDraft, tức chỉ có food_id + grams.
    """

    def generate_menu(state: NutriState) -> dict:
        candidates = [food for food_id in state.get("candidate_ids", []) if (food := foods.get(food_id)) is not None]
        attempt_no = state.get("attempt_count", 0) + 1
        generator_name = type(generator).__name__.casefold()
        source: Literal["gemini", "cpsat"] = (
            "gemini"
            if "gemini" in generator_name or ("hybrid" in generator_name and state.get("feedback"))
            else "cpsat"
        )
        history = list(state.get("attempt_history", []))
        try:
            draft = generator.generate(
                profile=state["profile"],
                targets=state["targets"],
                candidates=candidates,
                feedback=state.get("feedback"),
            )
        except Exception as exc:
            history.append(
                GenerationAttempt(
                    attempt_no=attempt_no,
                    source=source,
                    status="failed",
                    at=datetime.now(UTC),
                    feedback_used=bool(state.get("feedback")),
                    error=str(exc),
                )
            )
            return {
                "draft_menu": None,
                "menu_version": state.get("menu_version", 0) + 1,
                "menu_hash": None,
                "generation_source": source,
                "attempt_count": attempt_no,
                "attempt_history": history,
                "retry_count": state.get("retry_count", 0) + 1,
                "computed_nutrition": None,
                "nutrition_hash": None,
                "violations": [],
                "last_error": StructuredError(
                    code="GENERATOR_ERROR", message=str(exc), node="generate_menu", retriable=True
                ),
                "feedback": "Generator failed; retry with the safe routing policy.",
            }
        history.append(
            GenerationAttempt(
                attempt_no=attempt_no,
                source=source,
                status="generated",
                at=datetime.now(UTC),
                feedback_used=bool(state.get("feedback")),
            )
        )
        return {
            "draft_menu": draft,
            "menu_version": state.get("menu_version", 0) + 1,
            "menu_hash": hash_menu(draft),
            "generation_source": source,
            "prompt_version": _stable_hash({"generator": type(generator).__name__})[:16],
            "attempt_count": attempt_no,
            "attempt_history": history,
            "retry_count": attempt_no,
            "last_error": None,
            # A new draft invalidates every downstream artefact from the old one.
            "computed_nutrition": None,
            "nutrition_hash": None,
            "violations": [],
            "feedback": None,
        }

    return generate_menu


def make_compute_nutrition(foods: FoodRepository):
    """Node: compute_nutrition — LLM: NO. Nơi RULE-1 được thực thi."""

    def compute_nutrition_node(state: NutriState) -> dict:
        draft = state["draft_menu"]
        if draft is None:
            return {
                "computed_nutrition": None,
                "nutrition_hash": None,
                "violations": [],
                "feedback": "Chưa có thực đơn nháp để tính dinh dưỡng.",
            }
        try:
            summary = compute_nutrition(draft, foods)
        except UnknownFoodError as exc:
            # LLM bịa food_id → không đoán thay thế, ép sinh lại
            return {
                "computed_nutrition": None,
                "nutrition_hash": None,
                "violations": [],
                "feedback": (f"{exc} Chỉ được chọn food_id có trong danh sách ứng viên được cung cấp."),
            }
        return {"computed_nutrition": summary, "nutrition_hash": hash_nutrition(summary)}

    return compute_nutrition_node


def _finding_from_violation(violation) -> SafetyFinding:
    category: Literal["incomplete_data", "allergy", "drug_food", "nutrient"]
    if violation.kind == "incomplete_data":
        level = RiskSeverity.P1
        category = "incomplete_data"
    elif violation.kind == "allergy":
        level = RiskSeverity.P0
        category = "allergy"
    elif violation.kind == "drug_food":
        level = RiskSeverity.P0 if violation.blocking else RiskSeverity.P1
        category = "drug_food"
    else:
        level = RiskSeverity.P0 if violation.blocking else RiskSeverity.P2
        category = "nutrient"
    return SafetyFinding(
        code=f"{violation.kind.upper()}_{violation.nutrient.upper()}",
        risk_level=level,
        category=category,
        message_vi=violation.message_vi,
        suggestion=violation.suggestion,
        rule_id=violation.rule_id,
        metadata=violation.model_dump(mode="json"),
    )


def make_validate(foods: FoodRepository, rules: list[ClinicalRule] | None = None):
    """Node: validate — LLM: NO. Guardrail tầng 3, fail closed."""
    rules = [rule for rule in rules if rule.verify_status == "verified"] if rules is not None else load_rules()
    # Nạp một lần khi dựng graph, không đọc CSV lại mỗi lần validate (CLN-06).
    drug_food_rules = load_drug_food_rules()

    def validate_node(state: NutriState) -> dict:
        nutrition = state.get("computed_nutrition")
        draft = state["draft_menu"]
        persistent_findings = [
            finding
            for finding in state.get("safety_findings", [])
            if finding.category in {"drug_food", "medication_timing", "unverified_rule", "target_conflict"}
        ]
        if nutrition is None or draft is None:
            return {
                "violations": [],
                "safety_findings": persistent_findings
                + [
                    SafetyFinding(
                        code="INVALID_DRAFT",
                        risk_level=RiskSeverity.P0,
                        category="generation",
                        message_vi=state.get("feedback") or "Không có thực đơn hợp lệ để kiểm định.",
                    )
                ],
            }
        profile = state["profile"]
        violations = validate_menu(nutrition, state["targets"], rules)
        violations += check_allergies(draft, profile, foods)
        # CLN-06: bảng 30 cặp tương tác đã seed từ lâu nhưng trước đây không có
        # dòng code nào truy vấn — thuốc bệnh nhân đang dùng hoàn toàn không ảnh
        # hưởng gì tới thực đơn sinh ra.
        violations += check_drug_food_interactions(draft, profile, foods, drug_food_rules)
        violations += advisories_for(profile, drug_food_rules)
        return {
            "violations": violations,
            "safety_findings": persistent_findings + [_finding_from_violation(v) for v in violations],
        }

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
        attempt_no = state.get("attempt_count", 0) + 1
        history = list(state.get("attempt_history", []))
        history.append(
            GenerationAttempt(
                attempt_no=attempt_no,
                source="fallback",
                status="fallback" if draft is not None else "failed",
                at=datetime.now(UTC),
                error=None if draft is not None else "No fallback template available",
            )
        )
        if draft is None:
            return {
                "draft_menu": None,
                "menu_version": state.get("menu_version", 0) + 1,
                "menu_hash": None,
                "generation_source": "fallback",
                "attempt_count": attempt_no,
                "attempt_history": history,
                "computed_nutrition": None,
                "nutrition_hash": None,
                "violations": [],
                "feedback": "No safe fallback template is available; manual review is required.",
                "status": "manual_review_required",
                "needs_attention": True,
                "used_fallback": True,
            }
        return {
            "draft_menu": draft,
            "menu_version": state.get("menu_version", 0) + 1,
            "menu_hash": hash_menu(draft),
            "generation_source": "fallback",
            "attempt_count": attempt_no,
            "attempt_history": history,
            "computed_nutrition": None,
            "nutrition_hash": None,
            "violations": [],
            "feedback": None,
            "used_fallback": True,
            "needs_attention": True,
            "status": "manual_review_required",
        }

    return fallback


def prepare_manual_review(state: NutriState) -> dict:
    """Prepare a fail-closed state without invoking an optimizer or LLM."""
    return {"status": "manual_review_required", "needs_attention": True, "highest_risk": "P0"}


def risk_triage(state: NutriState) -> dict:
    """Assign P0/P1/P2 with strict P0 > P1 > P2 precedence."""
    levels = {finding.risk_level.value for finding in state.get("safety_findings", [])}
    highest = next((level for level in ("P0", "P1", "P2") if level in levels), "none")
    return {"highest_risk": highest}


def prepare_review_packet(state: NutriState) -> dict:
    """Return a P0-first packet so the reviewer can decide with minimal clicks."""
    order = {RiskSeverity.P0: 0, RiskSeverity.P1: 1, RiskSeverity.P2: 2}
    findings = sorted(state.get("safety_findings", []), key=lambda finding: (order[finding.risk_level], finding.code))
    highest = state.get("highest_risk", "none")
    return {
        "review_packet": ReviewPacket(
            highest_risk=highest,
            can_approve=highest != "P0" and state.get("computed_nutrition") is not None,
            used_fallback=state.get("used_fallback", False),
            target_gate_reasons=state.get("target_gate_reasons", []),
            findings=findings,
            summary=f"{len(findings)} safety finding(s); highest risk: {highest}.",
        )
    }


def explain_with_citations(state: NutriState) -> dict:
    """Deterministic evidence bundle; never fabricates a guideline citation."""
    by_ref: dict[str, set[str]] = {}
    for target in state["targets"].targets.values():
        for ref in target.guideline_refs:
            by_ref.setdefault(ref, set()).update(target.rule_ids)
    for finding in state.get("safety_findings", []):
        for ref in finding.evidence_refs:
            by_ref.setdefault(ref, set()).update([finding.rule_id] if finding.rule_id else [])
    citations = [Citation(source_ref=ref, rule_ids=sorted(rule_ids)) for ref, rule_ids in sorted(by_ref.items())]
    highest = state.get("highest_risk", "none")
    return {
        "citations": citations,
        "expert_explanation": f"Thực đơn được tính lại trên server; mức rủi ro cao nhất: {highest}.",
        "patient_explanation": None,
    }


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


def route_after_target_gate(state: NutriState) -> str:
    return "manual_review" if state.get("status") == "manual_review_required" else "continue"


def route_after_validate(state: NutriState) -> str:
    """Conditional edge sau node validate."""
    nutrition = state.get("computed_nutrition")
    has_p0 = any(finding.risk_level is RiskSeverity.P0 for finding in state.get("safety_findings", []))
    retry = state.get("retry_count", 0)

    if nutrition is not None and not has_p0:
        return "prepare_review"
    if state.get("used_fallback"):
        return "prepare_review"
    if retry >= MAX_RETRIES:
        return "fallback"
    return "build_feedback"
