"""Test cho src/services/target_assistant.py — LLM chỉ diễn đạt/parse tham số.

Trọng tâm: chứng minh LLM KHÔNG THỂ sinh ra một con số ngưỡng, dù có cố tình.
"""

from __future__ import annotations

import pydantic
import pytest

from src.clinical.models import Condition, ConditionCode, PatientProfile
from src.clinical.target_explainer import AppliedRuleExplanation, NutrientExplanation
from src.services.target_assistant import ProfileDelta, apply_delta


def _profile(**kwargs) -> PatientProfile:
    base = dict(patient_id="t1", age=60, sex="male", height_cm=165, weight_kg=65)
    base.update(kwargs)
    return PatientProfile(**base)


# --- Schema ProfileDelta: không có field số nào -----------------------------


def test_profile_delta_khong_co_field_so_nao():
    """Đây là hàng rào cứng nhất: dù prompt bị injection cách nào, Pydantic
    schema vật lý không có chỗ để LLM nhét một con số ngưỡng vào."""
    fields = ProfileDelta.model_fields
    for name, field in fields.items():
        ann = str(field.annotation)
        assert "float" not in ann.lower() and "int" not in ann.lower(), (
            f"Field '{name}' có kiểu số ({ann}) — vi phạm nguyên tắc LLM không sinh số"
        )


def test_profile_delta_reject_enum_sai():
    with pytest.raises(pydantic.ValidationError):
        ProfileDelta(condition_code="KHONG_TON_TAI")


def test_profile_delta_reject_co_la():
    with pytest.raises(pydantic.ValidationError):
        ProfileDelta(flags=["co_bia_dat"])


def test_profile_delta_chap_nhan_input_hop_le():
    d = ProfileDelta(condition_code=ConditionCode.CKD, stage="G4", flags=["frailty_sarcopenia"])
    assert d.condition_code is ConditionCode.CKD
    assert d.stage == "G4"
    assert d.flags == ["frailty_sarcopenia"]


def test_profile_delta_rong_hop_le():
    """Câu hỏi không đề cập bệnh lý mới vẫn phải parse được (mọi field optional)."""
    d = ProfileDelta()
    assert d.condition_code is None
    assert d.flags == []


# --- apply_delta: không sửa profile gốc, không đụng số liệu ----------------


def test_apply_delta_khong_sua_profile_goc():
    p = _profile(conditions=[Condition(code=ConditionCode.CKD, stage="G3b")])
    delta = ProfileDelta(condition_code=ConditionCode.CKD, stage="G4")
    p2 = apply_delta(p, delta)

    assert p.conditions[0].stage == "G3b", "Profile gốc bị sửa — what-if không được có side-effect"
    assert p2.conditions[0].stage == "G4"
    assert p2 is not p


def test_apply_delta_them_benh_ly_moi_giu_nguyen_benh_cu():
    p = _profile(conditions=[Condition(code=ConditionCode.T2DM)])
    p2 = apply_delta(p, ProfileDelta(condition_code=ConditionCode.CKD, stage="G3a"))

    codes = {c.code for c in p2.conditions}
    assert codes == {ConditionCode.T2DM, ConditionCode.CKD}


def test_apply_delta_khong_dong_cham_can_nang_chieu_cao_tuoi():
    """apply_delta chỉ được đổi conditions/flags — không có đường nào chạm số nhân trắc."""
    p = _profile(weight_kg=65.0, height_cm=165.0, age=60)
    p2 = apply_delta(p, ProfileDelta(condition_code=ConditionCode.HTN))
    assert p2.weight_kg == 65.0
    assert p2.height_cm == 165.0
    assert p2.age == 60


def test_apply_delta_them_co_an_toan():
    p = _profile()
    assert p.frailty_sarcopenia is False
    p2 = apply_delta(p, ProfileDelta(flags=["frailty_sarcopenia"]))
    assert p2.frailty_sarcopenia is True
    assert p.frailty_sarcopenia is False


# --- explain_naturally: chỉ được văn phong hoá, test qua mock ---------------


def test_explain_naturally_rong_khong_goi_llm(monkeypatch):
    """Không có gì để giải thích thì không cần gọi Gemini (tiết kiệm quota, tránh lỗi khi thiếu key)."""
    from src.services import target_assistant

    def _boom(*a, **k):
        raise AssertionError("Không được gọi Gemini khi danh sách rỗng")

    monkeypatch.setattr(target_assistant, "_call_gemini", _boom)
    result = target_assistant.explain_naturally([])
    assert "Chưa có" in result


def test_explain_naturally_dua_du_kien_that_vao_prompt(monkeypatch):
    """Kiểm tra prompt gửi cho LLM chứa đúng số đã tính — không phải chỗ nào khác bịa ra."""
    from src.services import target_assistant

    captured = {}

    class _FakeOutput:
        text_vi = "đoạn văn giả lập"

    def _fake_call(prompt, system_prompt, schema, settings):
        captured["prompt"] = prompt
        return _FakeOutput()

    monkeypatch.setattr(target_assistant, "_call_gemini", _fake_call)

    explanations = [
        NutrientExplanation(
            nutrient="protein_g",
            label_vi="Chất đạm",
            min_value=39.0,
            max_value=52.0,
            unit="g",
            applied=[
                AppliedRuleExplanation(
                    rule_id="CKD-PRO-01", guideline_ref="KDIGO 2024", bound="max", resolved_value=52.0, unit="g"
                )
            ],
        )
    ]
    result = target_assistant.explain_naturally(explanations)

    assert result == "đoạn văn giả lập"
    assert "52.0" in captured["prompt"]
    assert "39.0" in captured["prompt"]
    assert "CKD-PRO-01" in captured["prompt"]
