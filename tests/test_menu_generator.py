"""Test GeminiMenuGenerator — AGT-04. Không gọi mạng (mock lời gọi LLM).

Trọng tâm: RULE-1 — schema LLM chỉ có slot/food_id/grams, và pipeline chuyển
kết quả LLM thành MenuDraft đúng.
"""

from __future__ import annotations

from src.clinical.rules import compute_targets, load_rules
from src.config import Settings
from src.services.llm import GeminiMenuGenerator, _LLMItem, _LLMSelection, _to_menu_draft


def test_schema_llm_khong_co_truong_dinh_duong():
    """RULE-1: LLM không được có đường ghi giá trị dinh dưỡng."""
    nutri = {
        "kcal",
        "calorie",
        "calories",
        "protein",
        "carb",
        "fat",
        "fiber",
        "na",
        "sodium",
        "k",
        "potassium",
        "p",
        "phosphorus",
        "purine",
        "sugar",
        "gi",
    }
    for model in (_LLMItem, _LLMSelection):
        for field in model.model_fields:
            assert field.split("_")[0].lower() not in nutri, f"{model.__name__}.{field} vi phạm RULE-1"


def test_chuyen_ket_qua_llm_thanh_menudraft():
    sel = _LLMSelection(
        items=[
            _LLMItem(slot="breakfast", food_id=5, grams=150),
            _LLMItem(slot="lunch", food_id=21, grams=50),
            _LLMItem(slot="lunch", food_id=137, grams=10),
        ]
    )
    draft = _to_menu_draft(sel)
    assert len(draft.all_items()) == 3
    lunch_ids = {i.food_id for i in draft.items[list(draft.items)[1]]}
    assert {21, 137} <= {i.food_id for i in draft.all_items()}
    assert 21 in lunch_ids


def test_generate_goi_llm_va_tra_menudraft(monkeypatch, profile_t2dm_ckd):
    """generate() phải trả MenuDraft; LLM được mock để không gọi mạng."""
    settings = Settings(gemini_api_key="fake-key-for-test")
    gen = GeminiMenuGenerator(settings)
    fixed = _LLMSelection(items=[_LLMItem(slot="lunch", food_id=5, grams=200)])
    monkeypatch.setattr(gen, "_call_with_rotation", lambda prompt, config: fixed)

    targets = compute_targets(profile_t2dm_ckd, load_rules())
    draft = gen.generate(profile_t2dm_ckd, targets, candidates=[], feedback=None)
    assert draft.all_items()[0].food_id == 5
    assert draft.all_items()[0].grams == 200
