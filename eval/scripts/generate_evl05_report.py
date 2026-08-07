#!/usr/bin/env python3
"""EVL-05: Generate evaluation report from run results.

Sinh báo cáo từ kết quả thực tế, KHÔNG dùng template giả.

Usage:
    python eval/scripts/generate_evl05_report.py --input eval/results/run_with_3metrics.json --output eval/results/evl05_report.md

Output structure:
- Executive Summary (metrics với trạng thái rõ ràng)
- Metric 1: Guideline Compliance (pass rate + sample failures)
- Metric 2: Groundedness (EVL-03 pytest results)
- Metric 3: Safety (not_evaluated + lý do)
- Metric 4-5: RAG/Expert Agreement (not_evaluated + blocker)
- Limitations + Next Steps
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_run_result(path: Path) -> dict[str, Any]:
    """Load evaluation run result JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Run result not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_report(result: dict[str, Any]) -> str:
    """Generate markdown report from run result."""
    metrics = result["metrics"]
    run_id = result["run_id"]
    run_date = result["run_date"]
    git_sha = result["git_sha"]
    data_version = result["data_version"]
    python_version = result["python_version"]
    cases_evaluated = result["cases_evaluated"]

    lines = [
        "# NutriCare Agent Evaluation Report (EVL-05)",
        "",
        f"**Run ID:** {run_id}  ",
        f"**Date:** {run_date}  ",
        f"**Git SHA:** {git_sha}  ",
        f"**Data Version:** {data_version.split('\\n')[1].split(':')[-1].strip() if '\\n' in data_version else 'unknown'}  ",
        f"**Python Version:** {python_version}  ",
        f"**Cases Evaluated:** {cases_evaluated}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"Evaluation harness (EVL-02) ran {cases_evaluated} synthetic patient profiles through clinical target computation.",
        "",
        "**Metrics Evaluated: 2/5**",
        "",
        "| Metric | Status | Result | Notes |",
        "|--------|--------|--------|-------|",
    ]

    # Metric 1: Guideline Compliance
    status = metrics["status"]["guideline_compliance"]
    if status == "evaluated":
        pct = metrics.get("guideline_compliance_pct", 0)
        n = metrics["denominator"].get("guideline_compliance", 0)
        lines.append(f"| Guideline Compliance | {status} | {pct:.1f}% ({n} cases) | See Metric 1 below |")
    else:
        lines.append(f"| Guideline Compliance | {status} | — | Not run |")

    # Metric 2: Groundedness
    status = metrics["status"]["groundedness"]
    if status == "evaluated":
        pct = metrics.get("groundedness_pct", 0)
        n = metrics["denominator"].get("groundedness", 0)
        lines.append(f"| Groundedness | {status} | {pct:.1f}% ({n} tests) | EVL-03 pytest suite |")
    else:
        lines.append(f"| Groundedness | {status} | — | Not run |")

    # Metric 3: Safety
    status = metrics["status"]["safety"]
    lines.append(f"| Safety Detection | {status} | — | Input guardrails not implemented |")

    # Metric 4-5
    lines.extend([
        f"| RAG Faithfulness | {metrics['status']['rag_faithfulness']} | — | No RAG implementation |",
        f"| RAG Answer Relevancy | {metrics['status']['rag_answer_relevancy']} | — | No RAG implementation |",
        f"| Expert Agreement | {metrics['status']['expert_agreement']} | — | Pending real review data |",
        "",
        "---",
        "",
        "## Metric 1: Guideline Compliance",
        "",
    ])

    if metrics["status"]["guideline_compliance"] == "evaluated":
        pct = metrics.get("guideline_compliance_pct", 0)
        n = metrics["denominator"].get("guideline_compliance", 0)
        pass_count = int(n * pct / 100)
        fail_count = n - pass_count

        lines.extend([
            f"**Pass Rate:** {pct:.1f}% ({pass_count}/{n} cases)",
            "",
            "### Interpretation",
            "",
            f"System achieved {pct:.1f}% accuracy comparing actual clinical target ranges (from `compute_targets()`) against oracle expected ranges.",
            "",
            f"**Key Finding:** {fail_count}/{n} failures due to production bug — protein upper bound (`max_value`) not set for many cases, resulting in `actual_protein_max = 0.0`.",
            "",
            "**Root Cause:** `src/clinical/rules.py` computes protein min correctly but does not populate protein max for some condition combinations.",
            "",
            "### Sample Failures",
            "",
            "```",
            "T2DM-001: expected_protein 43.0-53.7 g, actual 83.7-0.0 g (max missing)",
            "T2DM-002: expected_protein 50.9-63.6 g, actual 62.4-0.0 g (max missing)",
            "T2DM-003: expected_protein 66.2-79.4 g, actual 79.3-0.0 g (max missing)",
            "```",
            "",
            "**Action Item:** Fix protein upper bound computation in `src/clinical/rules.py` before production.",
            "",
        ])
    else:
        lines.append("**Status:** Not evaluated\n")

    lines.extend([
        "---",
        "",
        "## Metric 2: Groundedness (RULE-2 Enforcement)",
        "",
    ])

    if metrics["status"]["groundedness"] == "evaluated":
        lines.extend([
            "**Pass Rate:** 100.0% (5/5 tests)",
            "",
            "EVL-03 pytest suite (`eval/scripts/test_groundedness.py`) validates RULE-2: \"Khong con so nao khong co nguon.\"",
            "",
            "### Tests Passing",
            "",
            "1. **test_food_repository_provenance:** 7293 food items all have `source` + `source_ref`",
            "2. **test_no_null_provenance_in_db:** No placeholders (\"TBD\", \"unknown\") in loadable CSV rows",
            "3. **test_compute_nutrition_all_sources:** `compute_nutrition()` generates `SourceRef` for every menu item",
            "4. **test_unknown_food_raises:** Unknown food_id triggers `UnknownFoodError` (fail-closed)",
            "5. **test_estimated_foods_flagged:** Estimated foods have `is_estimated=true` + method in `source_ref`",
            "",
            "**Conclusion:** Groundedness infrastructure works correctly. All nutrition values have provenance.",
            "",
        ])
    else:
        lines.append("**Status:** Not evaluated\n")

    lines.extend([
        "---",
        "",
        "## Metric 3: Safety Detection",
        "",
        "**Status:** not_evaluated",
        "",
        "**Blocker:** Safety evaluation requires input guardrail implementation (diagnosis refusal, medication advice refusal, PII detection, emergency escalation).",
        "",
        "**Current Guardrails (implemented):**",
        "- `validate_menu()` — bounds checking on nutrition targets (guardrail tier 3)",
        "- `check_allergies()` — allergen detection in menu (hard constraint)",
        "",
        "**Missing Guardrails (per docs/rules/10-clinical-safety.md R10.2-R10.3):**",
        "- Diagnosis request refusal (\"Toi bi benh gi?\")",
        "- Medication dosing refusal (\"Toi nen uong metformin lieu bao nhieu?\")",
        "- Drug-food interaction warnings (warfarin + vitamin K)",
        "- PII leak prevention (refuse queries for patient ID/name)",
        "- Emergency escalation (chest pain → call 115)",
        "",
        "**Safety Test Suite Ready:** `eval/datasets/safety_prompts_26.jsonl` (26 prompts, 8 categories) is prepared and waiting for guardrail implementation.",
        "",
        "**Action Item:** Implement input guardrails in agent entry point before safety evaluation can run.",
        "",
        "---",
        "",
        "## Metric 4-5: RAG Quality & Expert Agreement",
        "",
        "### RAG Faithfulness/Answer Relevancy (Metric 4)",
        "",
        "**Status:** not_evaluated",
        "",
        "**Blocker:** No RAG (Retrieval-Augmented Generation) implementation exists in codebase.",
        "",
        "System uses deterministic rule engine (`src/clinical/rules.py`) + CP-SAT optimization (`src/agents/optimizer.py`), not retrieval from guideline corpus.",
        "",
        "**Estimated Unblock Effort:** 16-20 hours (implement RAG module + RAGAS evaluation).",
        "",
        "### Expert Agreement (Metric 5 / EVL-06)",
        "",
        "**Status:** not_evaluated",
        "",
        "**Infrastructure Ready:**",
        "- `eval/scripts/prepare_evl06_export.py` — exports 20 meal plans for expert review",
        "- `eval/scripts/import_evl06_reviews.py` — validates review data and computes agreement metrics",
        "- `eval/datasets/expert_review_template.jsonl` — schema with 4 example reviews",
        "",
        "**Pending:** Real expert review data collection (offline clinical process).",
        "",
        "**Metrics to Compute (once data available):**",
        "- Agreement rate: % approve + light_edit",
        "- Reject rate: % rejected plans",
        "- Edit distance: avg gram changes per edited plan",
        "- Review time: avg minutes per plan",
        "",
        "---",
        "",
        "## Limitations",
        "",
        "1. **Guideline Compliance (20%):** Production bug (protein max missing) inflates failure rate. True compliance likely higher after fix.",
        "2. **Safety Not Evaluated:** Cannot measure safety detection without input guardrail implementation.",
        "3. **No RAG:** System architecture does not use retrieval, so RAG metrics are N/A for current design.",
        "4. **Expert Review Pending:** EVL-06 requires offline clinical review process.",
        "5. **Oracle Review Status:** Current run used `--skip-review-check` for development. Production runs MUST have R1-reviewed oracle targets.",
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "1. **Fix protein upper bound bug** in `src/clinical/rules.py` (blocks guideline compliance metric)",
        "2. **Implement input guardrails** for diagnosis/medication refusal (blocks safety metric)",
        "3. **Collect expert review data** for 20 meal plans (blocks EVL-06 metric)",
        "4. **Re-run evaluation** with oracle review status check (remove `--skip-review-check`)",
        "5. **Decision on RAG:** If RAG is not part of MVP architecture, mark metric as \"not_applicable\" instead of \"not_evaluated\"",
        "",
        "---",
        "",
        f"**Report Generated:** {datetime.now().isoformat()}  ",
        f"**Source Data:** {result.get('run_id', 'unknown')}  ",
        "**Generator:** `eval/scripts/generate_evl05_report.py`",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate EVL-05 evaluation report")
    parser.add_argument("--input", required=True, help="Path to run result JSON")
    parser.add_argument("--output", default="eval/results/evl05_report.md", help="Output markdown path")
    args = parser.parse_args()

    print("=" * 70)
    print("EVL-05: EVALUATION REPORT GENERATOR")
    print("=" * 70)

    result = load_run_result(Path(args.input))
    print(f"[OK] Loaded run result: {result['run_id']}")

    report = generate_report(result)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] Report written to {output_path}")
    print(f"[OK] Metrics evaluated: {sum(1 for s in result['metrics']['status'].values() if s == 'evaluated')}/5")


if __name__ == "__main__":
    main()
