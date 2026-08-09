"""Test cho src/clinical/target_explainer.py — trợ lý ngưỡng cho chuyên gia (P1).

Toàn bộ test chạy trên `clinical_rules.csv` THẬT (không fixture giả), vì mục
đích của module là giải thích đúng dữ liệu thật — sai một ca ở đây là chuyên
gia nhận lời giải thích sai về vì sao một ngưỡng được áp.
"""

from __future__ import annotations

import pytest

from src.clinical.models import Condition, ConditionCode, PatientProfile
from src.clinical.rules import compute_targets, load_rules
from src.clinical.target_explainer import diff_explanations, explain_targets


@pytest.fixture(scope="module")
def rules():
    return load_rules()


def _profile(**kwargs) -> PatientProfile:
    base = dict(patient_id="t1", age=60, sex="male", height_cm=165, weight_kg=65)
    base.update(kwargs)
    return PatientProfile(**base)


def _find(explanations, nutrient):
    return next(e for e in explanations if e.nutrient == nutrient)


# --- Rule thắng được giải thích đúng ---------------------------------------


def test_ckd_thang_t2dm_cho_protein(rules):
    """T2DM+CKD: protein phải theo KDIGO (CKD), không phải ADA (T2DM) — DEC-007."""
    p = _profile(conditions=[Condition(code=ConditionCode.T2DM), Condition(code=ConditionCode.CKD, stage="G3b")])
    targets = compute_targets(p, rules)
    ex = _find(explain_targets(p, targets, rules), "protein_g")

    applied_ids = {a.rule_id for a in ex.applied}
    assert applied_ids & {"CKD-PRO-01", "CKD-PRO-02", "CKD-PRO-05"}
    assert not (applied_ids & {"T2DM-PRO-01"})


def test_rule_bi_ghi_de_co_ly_do_dung_la_overridden(rules):
    p = _profile(conditions=[Condition(code=ConditionCode.T2DM), Condition(code=ConditionCode.CKD, stage="G3b")])
    targets = compute_targets(p, rules)
    ex = _find(explain_targets(p, targets, rules), "protein_g")

    excluded_by_id = {x.rule_id: x for x in ex.excluded}
    assert "T2DM-PRO-01" in excluded_by_id
    assert "CKD" in excluded_by_id["T2DM-PRO-01"].reason
    assert excluded_by_id["T2DM-PRO-01"].reason.strip(), "Lý do không được rỗng"


def test_rule_thieu_flag_co_ly_do_dung_la_thieu_flag_khong_phai_overridden(rules):
    """Bug thật đã bắt được: T2DM-PRO-02 (requires_flag=elderly) bị loại vì
    bệnh nhân chưa đủ tuổi — KHÔNG phải vì bị CKD ghi đè (overridden_by rỗng
    trên chính rule này). Gộp chung 2 lý do sẽ in ra "Bị  thay thế" (rỗng)."""
    p = _profile(
        age=60, conditions=[Condition(code=ConditionCode.T2DM), Condition(code=ConditionCode.CKD, stage="G3b")]
    )
    targets = compute_targets(p, rules)
    ex = _find(explain_targets(p, targets, rules), "protein_g")

    excluded_by_id = {x.rule_id: x for x in ex.excluded}
    assert "T2DM-PRO-02" in excluded_by_id
    reason = excluded_by_id["T2DM-PRO-02"].reason
    assert "elderly" in reason
    assert "thay thế" not in reason, "Lý do phải là thiếu cờ, không phải bị ghi đè"


def test_du_tuoi_thi_rule_yeu_cau_elderly_duoc_ap(rules):
    p = _profile(age=70, conditions=[Condition(code=ConditionCode.T2DM)])
    targets = compute_targets(p, rules)
    ex = _find(explain_targets(p, targets, rules), "protein_g")

    applied_ids = {a.rule_id for a in ex.applied}
    assert "T2DM-PRO-02" in applied_ids
    assert not any(x.rule_id == "T2DM-PRO-02" for x in ex.excluded)


def test_moi_con_so_trong_applied_deu_lay_tu_targets_khong_bia(rules):
    """resolved_value của rule applied phải khớp đúng min/max cuối cùng đã chọn."""
    p = _profile(conditions=[Condition(code=ConditionCode.CKD, stage="G3b")])
    targets = compute_targets(p, rules)
    ex = _find(explain_targets(p, targets, rules), "k_mg")

    max_values = [a.resolved_value for a in ex.applied if a.bound == "max"]
    if max_values:
        assert min(max_values) == ex.max_value


def test_rule_disabled_boi_co_an_toan_co_ly_do_dung(rules):
    """Frailty/sarcopenia vô hiệu trần protein thấp của CKD (KDIGO PP 3.3.1.5)."""
    p = _profile(conditions=[Condition(code=ConditionCode.CKD, stage="G3b")], frailty_sarcopenia=True)
    targets = compute_targets(p, rules)
    ex = _find(explain_targets(p, targets, rules), "protein_g")

    if ex.excluded:
        disabled = [x for x in ex.excluded if "cờ an toàn" in x.reason]
        assert all("frailty_sarcopenia" in x.reason for x in disabled)


def test_conflict_note_gan_dung_chat(rules):
    """Ca hẹp dải đã biết: người cao tuổi ĐTĐ+CKD — ADA sàn 0.8 g/kg, KDIGO trần 0.8 g/kg."""
    p = _profile(
        age=70, conditions=[Condition(code=ConditionCode.T2DM), Condition(code=ConditionCode.CKD, stage="G3b")]
    )
    targets = compute_targets(p, rules)
    if targets.needs_expert_review:
        ex = _find(explain_targets(p, targets, rules), "protein_g")
        assert ex.conflict_notes
        assert all(note.startswith("protein_g:") for note in ex.conflict_notes)


def test_nang_luong_co_giai_thich_du_khong_co_trong_csv(rules):
    """kcal không nằm trong clinical_rules.csv (rule ENERGY-WHO-FAO-UNU hardcode ở rules.py) — vẫn phải giải thích được."""
    p = _profile()
    targets = compute_targets(p, rules)
    ex = _find(explain_targets(p, targets, rules), "kcal")

    assert len(ex.applied) == 1
    assert ex.applied[0].rule_id == "ENERGY-WHO-FAO-UNU"
    assert ex.applied[0].unit == "kcal"


# --- diff_explanations cho what-if -----------------------------------------


def test_diff_bat_dung_thay_doi_khi_ckd_nang_len(rules):
    p_g3b = _profile(conditions=[Condition(code=ConditionCode.CKD, stage="G3b")])
    p_g4 = _profile(conditions=[Condition(code=ConditionCode.CKD, stage="G4")])

    ex_before = explain_targets(p_g3b, compute_targets(p_g3b, rules), rules)
    ex_after = explain_targets(p_g4, compute_targets(p_g4, rules), rules)
    diffs = diff_explanations(ex_before, ex_after)

    changed = {d.nutrient for d in diffs if d.changed}
    assert changed, "G3b -> G4 phải làm ít nhất 1 ngưỡng đổi (kali/phospho thường siết thêm)"
    for d in diffs:
        if d.changed:
            assert (d.before_min, d.before_max) != (d.after_min, d.after_max)


def test_diff_khong_doi_gi_khi_ho_so_khong_doi(rules):
    p = _profile(conditions=[Condition(code=ConditionCode.T2DM)])
    ex = explain_targets(p, compute_targets(p, rules), rules)
    diffs = diff_explanations(ex, ex)
    assert all(not d.changed for d in diffs)
