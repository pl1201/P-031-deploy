"""Test LangGraph agent: vòng lặp retry, fallback, HITL, và các ràng buộc kiến trúc."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver

from src.agents.graph import build_graph
from src.clinical.models import MealSlot, MenuDraft, MenuItem, PatientProfile
from src.clinical.rules import load_rules

SRC = Path(__file__).resolve().parents[1] / "src"


# ------------------------------------------------------------------ doubles
class FakeProfiles:
    def __init__(self, profile: PatientProfile) -> None:
        self._p = profile

    def get(self, patient_id: str) -> PatientProfile | None:
        return self._p if patient_id == self._p.patient_id else None


class ScriptedGenerator:
    """LLM giả: trả về lần lượt các thực đơn đã kịch bản hoá, đếm số lần được gọi."""

    def __init__(self, menus: list[MenuDraft]) -> None:
        self.menus = menus
        self.calls = 0
        self.feedbacks: list[str | None] = []

    def generate(self, profile, targets, candidates, feedback) -> MenuDraft:
        self.feedbacks.append(feedback)
        menu = self.menus[min(self.calls, len(self.menus) - 1)]
        self.calls += 1
        return menu


class StaticFallback:
    def __init__(self, menu: MenuDraft | None) -> None:
        self._menu = menu

    def get(self, profile) -> MenuDraft | None:
        return self._menu


def _run(graph, patient_id="BN-DEMO-02"):
    return graph.invoke({"patient_id": patient_id, "trace_id": "t-1"})


# ------------------------------------------------------------------- luồng
class TestAgentFlow:
    def test_thuc_don_dat_ngay_lan_dau_thi_khong_retry(
        self, foods, profile_htn, modest_menu
    ):
        gen = ScriptedGenerator([modest_menu])
        graph = build_graph(
            profiles=FakeProfiles(profile_htn),
            foods=foods,
            generator=gen,
            fallback_provider=StaticFallback(None),
            rules=load_rules(),
        )
        out = _run(graph)

        assert gen.calls == 1
        assert out["status"] == "pending_review"
        assert out["computed_nutrition"].sources
        assert out.get("used_fallback") is not True

    def test_thuc_don_sai_thi_sinh_lai_kem_feedback_cu_the(
        self, foods, profile_htn, salty_menu, modest_menu
    ):
        """Lần 1 thừa muối → phải retry, và feedback phải nêu đúng chất vi phạm."""
        gen = ScriptedGenerator([salty_menu, modest_menu])
        graph = build_graph(
            profiles=FakeProfiles(profile_htn),
            foods=foods,
            generator=gen,
            fallback_provider=StaticFallback(None),
            rules=load_rules(),
        )
        out = _run(graph)

        assert gen.calls == 2
        assert gen.feedbacks[0] is None
        assert "Natri" in gen.feedbacks[1]
        assert out["status"] == "pending_review"

    def test_het_luot_retry_thi_dung_fallback_va_gan_co_can_chu_y(
        self, foods, profile_htn, salty_menu, modest_menu
    ):
        gen = ScriptedGenerator([salty_menu])  # luôn trả thực đơn sai
        graph = build_graph(
            profiles=FakeProfiles(profile_htn),
            foods=foods,
            generator=gen,
            fallback_provider=StaticFallback(modest_menu),
            rules=load_rules(),
        )
        out = _run(graph)

        assert gen.calls == 3, "Đúng 3 lần thử, không vòng lặp vô hạn"
        assert out["used_fallback"] is True
        assert out["needs_attention"] is True
        assert out["status"] == "pending_review"

    def test_khong_co_fallback_thi_that_bai_chu_khong_phat_hanh_thuc_don_sai(
        self, foods, profile_htn, salty_menu
    ):
        """Fail closed: thà không có thực đơn còn hơn có thực đơn vi phạm."""
        graph = build_graph(
            profiles=FakeProfiles(profile_htn),
            foods=foods,
            generator=ScriptedGenerator([salty_menu]),
            fallback_provider=StaticFallback(None),
            rules=load_rules(),
        )
        out = _run(graph)
        assert out["status"] == "failed"
        assert out["needs_attention"] is True

    def test_llm_bia_food_id_thi_bi_ep_sinh_lai(self, foods, profile_htn, modest_menu):
        bogus = MenuDraft(items={MealSlot.LUNCH: [MenuItem(food_id=99999, grams=100)]})
        gen = ScriptedGenerator([bogus, modest_menu])
        graph = build_graph(
            profiles=FakeProfiles(profile_htn),
            foods=foods,
            generator=gen,
            fallback_provider=StaticFallback(None),
            rules=load_rules(),
        )
        out = _run(graph)

        assert gen.calls == 2
        assert "99999" in gen.feedbacks[1]
        assert out["status"] == "pending_review"

    def test_di_ung_chan_cung_du_cac_chi_so_khac_dat(
        self, foods, profile_allergy_seafood, modest_menu
    ):
        shrimp = MenuDraft(
            items={
                MealSlot.LUNCH: [MenuItem(food_id=1, grams=300), MenuItem(food_id=9, grams=100)]
            }
        )
        gen = ScriptedGenerator([shrimp, modest_menu])
        graph = build_graph(
            profiles=FakeProfiles(profile_allergy_seafood),
            foods=foods,
            generator=gen,
            fallback_provider=StaticFallback(None),
            rules=load_rules(),
        )
        out = _run(graph, patient_id="BN-DEMO-03")
        assert gen.calls >= 2, "Thực đơn có tôm phải bị chặn và sinh lại"
        assert out["status"] == "pending_review"

    def test_khong_co_ho_so_thi_dung_lai(self, foods, profile_htn, modest_menu):
        graph = build_graph(
            profiles=FakeProfiles(profile_htn),
            foods=foods,
            generator=ScriptedGenerator([modest_menu]),
            fallback_provider=StaticFallback(None),
            rules=load_rules(),
        )
        out = _run(graph, patient_id="KHONG-TON-TAI")
        assert out["status"] == "failed"


# --------------------------------------------------------------------- HITL
class TestHITL:
    def test_graph_dung_truoc_khi_phat_hanh_va_giu_duoc_state(
        self, foods, profile_htn, modest_menu
    ):
        """RULE-3: không có đường nào đi thẳng từ agent tới bệnh nhân."""
        graph = build_graph(
            profiles=FakeProfiles(profile_htn),
            foods=foods,
            generator=ScriptedGenerator([modest_menu]),
            fallback_provider=StaticFallback(None),
            rules=load_rules(),
            checkpointer=MemorySaver(),
            interrupt_for_hitl=True,
        )
        config = {"configurable": {"thread_id": "plan-001"}}
        graph.invoke({"patient_id": "BN-DEMO-02", "trace_id": "t-1"}, config)

        state = graph.get_state(config)
        assert state.next == ("to_review",), "Phải dừng trước bước đưa vào hàng chờ"
        assert state.values["status"] != "approved"
        assert state.values["computed_nutrition"] is not None

        # Chuyên gia xử lý xong → resume
        graph.invoke(None, config)
        assert graph.get_state(config).values["status"] == "pending_review"

    def test_khong_bao_gio_tu_dat_trang_thai_approved(
        self, foods, profile_htn, modest_menu
    ):
        graph = build_graph(
            profiles=FakeProfiles(profile_htn),
            foods=foods,
            generator=ScriptedGenerator([modest_menu]),
            fallback_provider=StaticFallback(None),
            rules=load_rules(),
        )
        assert _run(graph)["status"] != "approved"


# --------------------------------------------------- ràng buộc kiến trúc
FORBIDDEN_LLM_MODULES = {
    "openai", "anthropic", "langchain_openai", "langchain_anthropic",
    "langchain_core.language_models", "litellm", "google.generativeai",
}

DETERMINISTIC_FILES = [
    "clinical/energy.py",
    "clinical/rules.py",
    "clinical/nutrition.py",
    "clinical/validator.py",
    "clinical/models.py",
]


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
    return mods


class TestArchitectureInvariants:
    """Các test này biến nguyên tắc thiết kế thành ràng buộc kỹ thuật thật.

    Ticket EVL-03 — CI phải đỏ nếu ai đó vô tình để LLM sinh ra con số.
    """

    @pytest.mark.parametrize("rel", DETERMINISTIC_FILES)
    def test_tang_deterministic_khong_duoc_import_llm(self, rel):
        mods = _imported_modules(SRC / rel)
        leaked = {m for m in mods if any(m.startswith(f) for f in FORBIDDEN_LLM_MODULES)}
        assert not leaked, f"{rel} import LLM client: {leaked} — vi phạm RULE-1"

    def test_schema_llm_khong_co_field_dinh_duong(self):
        """MenuItem là thứ DUY NHẤT LLM được sinh ra: chỉ food_id + grams."""
        assert set(MenuItem.model_fields) == {"food_id", "grams"}

        nutrition_like = {
            "kcal", "calorie", "calories", "protein", "carb", "fat",
            "fiber", "na", "sodium", "k", "potassium", "p", "phosphorus", "purine",
        }
        for model in (MenuItem, MenuDraft):
            for field in model.model_fields:
                assert field.split("_")[0].lower() not in nutrition_like, (
                    f"{model.__name__}.{field} cho phép LLM sinh giá trị dinh dưỡng — vi phạm RULE-1"
                )

    def test_moi_thuc_pham_deu_phai_khai_bao_nguon(self):
        """RULE-2 ở tầng schema: không tạo được FoodItem thiếu nguồn."""
        from src.clinical.models import FoodItem

        base = dict(
            id=1, name_vi="X", kcal_100g=100, protein_g=1, carb_g=1, fat_g=1,
            fiber_g=1, na_mg=1, k_mg=1, p_mg=1, purine_mg=1,
        )
        with pytest.raises(Exception):
            FoodItem(**base, source="NIN", source_ref="")
        with pytest.raises(Exception):
            FoodItem(**base, source="NIN", source_ref="TODO")
