"""Ráp các thành phần cụ thể vào graph để có agent chạy được đầu-cuối.

Ticket: AGT-01..AGT-06. Đây là chỗ DUY NHẤT nối cổng (Protocol) với bản cài đặt
thật: repo thực phẩm (seed), LLM Gemini, thực đơn dự phòng.
"""

from __future__ import annotations

from src.agents.graph import build_graph
from src.agents.nodes.core import FallbackMenuProvider, MenuGenerator, ProfileRepository
from src.clinical.models import MealSlot, MenuDraft, MenuItem, PatientProfile
from src.clinical.nutrition import FoodRepository
from src.clinical.rules import ClinicalRule
from src.clinical.seeds import load_food_repository, load_vn_dishes
from src.config import get_settings


class InMemoryProfileRepository:
    """Repo hồ sơ bệnh nhân trong bộ nhớ (production sẽ là DB — ticket BE-03)."""

    def __init__(self, profiles: list[PatientProfile]) -> None:
        self._by_id = {p.patient_id: p for p in profiles}

    def get(self, patient_id: str) -> PatientProfile | None:
        return self._by_id.get(patient_id)


class SimpleFallbackProvider:
    """Thực đơn mẫu an toàn tối giản khi agent hết lượt retry.

    Chọn vài món ít natri có sẵn trong repo (cơm, rau, đậu phụ). Bản production
    sẽ là thực đơn do chuyên gia soạn theo từng bệnh lý.
    """

    _SAFE = ((2, 200.0), (65, 150.0), (55, 100.0))  # cơm tẻ, rau muống, đậu phụ

    def __init__(self, foods: FoodRepository) -> None:
        self._foods = foods

    def get(self, profile: PatientProfile) -> MenuDraft | None:
        items = [MenuItem(food_id=fid, grams=g) for fid, g in self._SAFE if self._foods.get(fid)]
        if not items:
            return None
        return MenuDraft(items={MealSlot.LUNCH: items})


def _generator_from_settings(foods: FoodRepository) -> MenuGenerator:
    """Dựng generator theo cấu hình (AGT-10). Import trễ để chỉ nạp thứ cần dùng.

    Riêng `gemini` mới bắt buộc có `GEMINI_API_KEY`; `cpsat` chạy được không cần
    key, còn `hybrid` chỉ cần key khi thực sự phải nhờ tới LLM.
    """
    choice = get_settings().menu_generator
    if choice == "gemini":
        from src.services.llm import GeminiMenuGenerator

        return GeminiMenuGenerator()
    if choice == "cpsat":
        from src.agents.optimizer import CPSATMenuOptimizer

        return CPSATMenuOptimizer(dishes=load_vn_dishes(), foods=foods)

    from src.agents.hybrid import HybridMenuGenerator
    from src.agents.optimizer import CPSATMenuOptimizer

    return HybridMenuGenerator(optimizer=CPSATMenuOptimizer(dishes=load_vn_dishes(), foods=foods))


def build_nutricare_graph(
    *,
    profiles: ProfileRepository,
    generator: MenuGenerator | None = None,
    foods: FoodRepository | None = None,
    fallback_provider: FallbackMenuProvider | None = None,
    rules: list[ClinicalRule] | None = None,
    interrupt_for_hitl: bool = False,
    checkpointer=None,
):
    """Dựng graph đầy đủ. `generator=None` → chọn theo `settings.menu_generator`."""
    foods = foods or load_food_repository()
    if generator is None:
        generator = _generator_from_settings(foods)
    return build_graph(
        profiles=profiles,
        foods=foods,
        generator=generator,
        fallback_provider=fallback_provider or SimpleFallbackProvider(foods),
        rules=rules,
        interrupt_for_hitl=interrupt_for_hitl,
        checkpointer=checkpointer,
    )
