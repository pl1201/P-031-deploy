"""Test HybridMenuGenerator — AGT-10. Không gọi mạng (dùng generator giả).

Trọng tâm: đúng nhánh nào gọi bên nào. CP-SAT tất định nên retry với cùng input
là vô nghĩa — hybrid phải chuyển sang LLM ngay khi có feedback, và cũng phải
chuyển khi CP-SAT vô nghiệm.
"""

from __future__ import annotations

import pytest

from src.agents.hybrid import HybridMenuGenerator
from src.clinical.models import (
    ActivityLevel,
    Condition,
    ConditionCode,
    MealSlot,
    MenuDraft,
    MenuItem,
    PatientProfile,
    Sex,
)
from src.clinical.rules import compute_targets


class _SpyGenerator:
    """Generator giả: ghi lại số lần được gọi và feedback nhận được."""

    def __init__(self, draft: MenuDraft) -> None:
        self._draft = draft
        self.calls = 0
        self.last_feedback: str | None = None

    def generate(self, profile, targets, candidates, feedback) -> MenuDraft:
        self.calls += 1
        self.last_feedback = feedback
        return self._draft


def _draft_with_items() -> MenuDraft:
    return MenuDraft(items={MealSlot.LUNCH: [MenuItem(food_id=1, grams=100)]})


@pytest.fixture
def profile() -> PatientProfile:
    return PatientProfile(
        patient_id="BN-HYBRID-01",
        age=58,
        sex=Sex.MALE,
        height_cm=165,
        weight_kg=70,
        activity_level=ActivityLevel.LIGHT,
        conditions=[Condition(code=ConditionCode.T2DM)],
    )


@pytest.fixture
def targets(profile):
    return compute_targets(profile)


def test_luot_dau_dung_cpsat_va_khong_dung_toi_llm(profile, targets):
    """CP-SAT giải được → trả luôn, KHÔNG được chạm tới LLM (không tốn token/key)."""
    cpsat = _SpyGenerator(_draft_with_items())
    llm = _SpyGenerator(_draft_with_items())

    draft = HybridMenuGenerator(optimizer=cpsat, llm_factory=lambda: llm).generate(
        profile, targets, candidates=[], feedback=None
    )

    assert cpsat.calls == 1
    assert llm.calls == 0, "CP-SAT đã giải được thì không được gọi LLM"
    assert draft.all_items()


def test_cpsat_vo_nghiem_thi_chuyen_sang_llm(profile, targets):
    """CP-SAT trả rỗng → hybrid phải nhờ LLM thay vì bỏ cuộc."""
    cpsat = _SpyGenerator(MenuDraft())
    llm = _SpyGenerator(_draft_with_items())

    draft = HybridMenuGenerator(optimizer=cpsat, llm_factory=lambda: llm).generate(
        profile, targets, candidates=[], feedback=None
    )

    assert cpsat.calls == 1
    assert llm.calls == 1
    assert draft.all_items()


def test_co_feedback_thi_di_thang_llm_khong_goi_lai_cpsat(profile, targets):
    """Đây là lý do tồn tại của hybrid: CP-SAT tất định, giải lại là vô nghĩa."""
    cpsat = _SpyGenerator(_draft_with_items())
    llm = _SpyGenerator(_draft_with_items())

    HybridMenuGenerator(optimizer=cpsat, llm_factory=lambda: llm).generate(
        profile, targets, candidates=[], feedback="Natri vượt 2100mg do nước mắm."
    )

    assert cpsat.calls == 0, "có feedback thì không được giải lại bằng CP-SAT"
    assert llm.calls == 1
    assert llm.last_feedback == "Natri vượt 2100mg do nước mắm."


def test_llm_chi_khoi_tao_khi_that_su_can(profile, targets):
    """llm_factory phải được gọi TRỄ — nếu không sẽ đòi GEMINI_API_KEY vô ích."""
    created = []

    def factory():
        created.append(1)
        return _SpyGenerator(_draft_with_items())

    generator = HybridMenuGenerator(optimizer=_SpyGenerator(_draft_with_items()), llm_factory=factory)
    assert created == [], "chưa gọi generate thì chưa được dựng LLM"

    generator.generate(profile, targets, candidates=[], feedback=None)
    assert created == [], "CP-SAT giải được thì vẫn không được dựng LLM"


def test_llm_chi_dung_mot_lan_du_goi_nhieu_luot(profile, targets):
    """Trên đường LLM, factory chỉ được gọi đúng 1 lần dù generate() nhiều lượt —
    nếu ai bỏ cache `self._llm`, mỗi lượt sẽ dựng client mới (tốn tài nguyên).
    """
    created: list[int] = []

    def factory():
        created.append(1)
        return _SpyGenerator(_draft_with_items())

    # CP-SAT luôn vô nghiệm → mọi lượt đều rơi sang LLM.
    generator = HybridMenuGenerator(optimizer=_SpyGenerator(MenuDraft()), llm_factory=factory)
    generator.generate(profile, targets, candidates=[], feedback=None)
    generator.generate(profile, targets, candidates=[], feedback="sửa natri")

    assert created == [1], "factory LLM phải chỉ chạy đúng 1 lần (được memoize)"
