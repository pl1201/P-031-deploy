# NutriCare Agent Evaluation Report (EVL-05)

**Run ID:** 20260807_004844  
**Date:** 2026-08-07T00:48:44.189272  
**Git SHA:** 6f50794  
**Data Version:** unknown  
**Python Version:** 3.13.14  
**Cases Evaluated:** 60

---

## Executive Summary

Evaluation harness (EVL-02) ran 60 synthetic patient profiles through clinical target computation.

**Metrics Evaluated: 2/5**

| Metric | Status | Result | Notes |
|--------|--------|--------|-------|
| Guideline Compliance | evaluated | 20.0% (60 cases) | See Metric 1 below |
| Groundedness | evaluated | 100.0% (5 tests) | EVL-03 pytest suite |
| Safety Detection | not_evaluated | — | Input guardrails not implemented |
| RAG Faithfulness | not_evaluated | — | No RAG implementation |
| RAG Answer Relevancy | not_evaluated | — | No RAG implementation |
| Expert Agreement | not_evaluated | — | Pending real review data |

---

## Metric 1: Guideline Compliance

**Pass Rate:** 20.0% (12/60 cases)

### Interpretation

System achieved 20.0% accuracy comparing actual clinical target ranges (from `compute_targets()`) against oracle expected ranges.

**Key Finding:** 48/60 failures due to production bug — protein upper bound (`max_value`) not set for many cases, resulting in `actual_protein_max = 0.0`.

**Root Cause:** `src/clinical/rules.py` computes protein min correctly but does not populate protein max for some condition combinations.

### Sample Failures

```
T2DM-001: expected_protein 43.0-53.7 g, actual 83.7-0.0 g (max missing)
T2DM-002: expected_protein 50.9-63.6 g, actual 62.4-0.0 g (max missing)
T2DM-003: expected_protein 66.2-79.4 g, actual 79.3-0.0 g (max missing)
```

**Action Item:** Fix protein upper bound computation in `src/clinical/rules.py` before production.

---

## Metric 2: Groundedness (RULE-2 Enforcement)

**Pass Rate:** 100.0% (5/5 tests)

EVL-03 pytest suite (`eval/scripts/test_groundedness.py`) validates RULE-2: "Khong con so nao khong co nguon."

### Tests Passing

1. **test_food_repository_provenance:** 7293 food items all have `source` + `source_ref`
2. **test_no_null_provenance_in_db:** No placeholders ("TBD", "unknown") in loadable CSV rows
3. **test_compute_nutrition_all_sources:** `compute_nutrition()` generates `SourceRef` for every menu item
4. **test_unknown_food_raises:** Unknown food_id triggers `UnknownFoodError` (fail-closed)
5. **test_estimated_foods_flagged:** Estimated foods have `is_estimated=true` + method in `source_ref`

**Conclusion:** Groundedness infrastructure works correctly. All nutrition values have provenance.

---

## Metric 3: Safety Detection

**Status:** not_evaluated

**Blocker:** Safety evaluation requires input guardrail implementation (diagnosis refusal, medication advice refusal, PII detection, emergency escalation).

**Current Guardrails (implemented):**
- `validate_menu()` — bounds checking on nutrition targets (guardrail tier 3)
- `check_allergies()` — allergen detection in menu (hard constraint)

**Missing Guardrails (per docs/rules/10-clinical-safety.md R10.2-R10.3):**
- Diagnosis request refusal ("Toi bi benh gi?")
- Medication dosing refusal ("Toi nen uong metformin lieu bao nhieu?")
- Drug-food interaction warnings (warfarin + vitamin K)
- PII leak prevention (refuse queries for patient ID/name)
- Emergency escalation (chest pain → call 115)

**Safety Test Suite Ready:** `eval/datasets/safety_prompts_26.jsonl` (26 prompts, 8 categories) is prepared and waiting for guardrail implementation.

**Action Item:** Implement input guardrails in agent entry point before safety evaluation can run.

---

## Metric 4-5: RAG Quality & Expert Agreement

### RAG Faithfulness/Answer Relevancy (Metric 4)

**Status:** not_evaluated

**Blocker:** No RAG (Retrieval-Augmented Generation) implementation exists in codebase.

System uses deterministic rule engine (`src/clinical/rules.py`) + CP-SAT optimization (`src/agents/optimizer.py`), not retrieval from guideline corpus.

**Estimated Unblock Effort:** 16-20 hours (implement RAG module + RAGAS evaluation).

### Expert Agreement (Metric 5 / EVL-06)

**Status:** not_evaluated

**Infrastructure Ready:**
- `eval/scripts/prepare_evl06_export.py` — exports 20 meal plans for expert review
- `eval/scripts/import_evl06_reviews.py` — validates review data and computes agreement metrics
- `eval/datasets/expert_review_template.jsonl` — schema with 4 example reviews

**Pending:** Real expert review data collection (offline clinical process).

**Metrics to Compute (once data available):**
- Agreement rate: % approve + light_edit
- Reject rate: % rejected plans
- Edit distance: avg gram changes per edited plan
- Review time: avg minutes per plan

---

## Limitations

1. **Guideline Compliance (20%):** Production bug (protein max missing) inflates failure rate. True compliance likely higher after fix.
2. **Safety Not Evaluated:** Cannot measure safety detection without input guardrail implementation.
3. **No RAG:** System architecture does not use retrieval, so RAG metrics are N/A for current design.
4. **Expert Review Pending:** EVL-06 requires offline clinical review process.
5. **Oracle Review Status:** Current run used `--skip-review-check` for development. Production runs MUST have R1-reviewed oracle targets.

---

## Next Steps

1. **Fix protein upper bound bug** in `src/clinical/rules.py` (blocks guideline compliance metric)
2. **Implement input guardrails** for diagnosis/medication refusal (blocks safety metric)
3. **Collect expert review data** for 20 meal plans (blocks EVL-06 metric)
4. **Re-run evaluation** with oracle review status check (remove `--skip-review-check`)
5. **Decision on RAG:** If RAG is not part of MVP architecture, mark metric as "not_applicable" instead of "not_evaluated"

---

**Report Generated:** 2026-08-07T00:50:00.728108  
**Source Data:** 20260807_004844  
**Generator:** `eval/scripts/generate_evl05_report.py`