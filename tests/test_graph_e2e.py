"""Test luồng agent đầu-cuối qua graph — dùng generator GIẢ (không cần Gemini key).

Chứng minh 8 node chạy thông: load → targets → retrieve → generate → compute →
validate → (to_review | fallback). RULE-1 vẫn giữ: generator giả cũng chỉ trả
MenuDraft (food_id + grams).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.agents.assembly import InMemoryProfileRepository, build_nutricare_graph
from src.agents.optimizer import CPSATMenuOptimizer
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
from src.clinical.rules import load_rules
from src.clinical.seeds import load_food_repository


class _FakeGenerator:
    """Generator giả: trả thực đơn cố định từ vài food_id có thật trong repo."""

    def __init__(self, food_ids: list[int]) -> None:
        self._ids = food_ids

    def generate(self, profile, targets, candidates, feedback) -> MenuDraft:
        items = [MenuItem(food_id=fid, grams=150) for fid in self._ids]
        return MenuDraft(items={MealSlot.LUNCH: items})


@pytest.fixture(scope="module")
def foods():
    return load_food_repository()


@pytest.fixture
def profiles():
    p = PatientProfile(
        patient_id="BN-E2E",
        age=58,
        sex=Sex.MALE,
        height_cm=165,
        weight_kg=70,
        activity_level=ActivityLevel.LIGHT,
        conditions=[Condition(code=ConditionCode.T2DM)],
    )
    return InMemoryProfileRepository([p])


@pytest.fixture(scope="module")
def verified_rules():
    return [replace(rule, verify_status="verified") for rule in load_rules(verified_only=False)]


def test_graph_fake_khong_dat_thi_retry_roi_fallback(foods, profiles, verified_rules):
    """Fake trả thực đơn cố định 4 món → validate fail → retry đủ 3 lượt →
    fallback. Kết quả tất định: pending_review + used_fallback + retry_count=3.

    Assert đúng con số (không dùng disjunction 'pending_review hoặc failed' lỏng
    lẻo): nếu vòng lặp retry hỏng hoặc fallback không kích hoạt, test này bắt được.
    """
    some_ids = [f.id for f in foods.all()[:4]]
    graph = build_nutricare_graph(
        profiles=profiles, generator=_FakeGenerator(some_ids), foods=foods, rules=verified_rules
    )
    final = graph.invoke({"patient_id": "BN-E2E", "trace_id": "t1"})

    assert final["status"] == "pending_review"
    assert final["used_fallback"] is True
    assert final["retry_count"] == 3
    assert final["computed_nutrition"] is not None
    assert final["computed_nutrition"].kcal > 0


def test_graph_khong_tim_thay_ho_so_thi_dung_som(foods, profiles, verified_rules):
    graph = build_nutricare_graph(profiles=profiles, generator=_FakeGenerator([1]), foods=foods, rules=verified_rules)
    final = graph.invoke({"patient_id": "KHONG-TON-TAI", "trace_id": "t2"})
    assert final["status"] == "failed"


def test_graph_chay_voi_cpsat_that_khong_can_api_key(foods, profiles, verified_rules):
    """Generator THẬT chạy hết graph — trước AGT-10 chỉ làm được với generator giả.

    CP-SAT không cần API key nên CI chạy được luồng thật. Kỳ vọng đi tới bước
    duyệt HITL ngay lượt đầu, KHÔNG rơi vào fallback (đó mới là điểm ăn tiền so
    với vòng lặp đoán-rồi-thử của LLM).
    """
    graph = build_nutricare_graph(profiles=profiles, generator=CPSATMenuOptimizer(), foods=foods, rules=verified_rules)
    final = graph.invoke({"patient_id": "BN-E2E", "trace_id": "t3"})

    assert final["status"] == "pending_review"
    assert not final.get("used_fallback"), "CP-SAT phải giải được, không được rơi vào fallback"
    assert final["retry_count"] == 1, "phải xong ngay lượt đầu, không cần vòng lặp retry"
    assert final["computed_nutrition"].kcal > 0


class _AlwaysEmptyGenerator:
    """Mô phỏng CP-SAT vô nghiệm: luôn trả MenuDraft RỖNG (không phải None)."""

    def generate(self, profile, targets, candidates, feedback) -> MenuDraft:
        return MenuDraft()


def test_cpsat_vo_nghiem_di_qua_graph_that_toi_fallback(foods, profiles, verified_rules):
    """Đóng lỗ hổng audit chỉ ra: CP-SAT trả draft RỖNG (khác None) phải trôi qua
    compute_nutrition → validate → retry → fallback end-to-end, không kẹt hay
    crash. Trước đây chỉ test optimizer trả rỗng ở mức đơn vị, chưa qua graph.
    """
    graph = build_nutricare_graph(
        profiles=profiles, generator=_AlwaysEmptyGenerator(), foods=foods, rules=verified_rules
    )
    final = graph.invoke({"patient_id": "BN-E2E", "trace_id": "t4"})

    # Draft rỗng không bao giờ đạt validate → cạn retry → fallback (fallback repo
    # đầy đủ nên dựng được thực đơn mẫu) → pending_review + used_fallback.
    assert final["status"] == "pending_review"
    assert final["used_fallback"] is True
    assert final["retry_count"] == 3
