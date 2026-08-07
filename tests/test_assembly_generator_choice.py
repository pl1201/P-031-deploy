"""Test `_generator_from_settings` — AGT-10.

Trước đây mọi test graph đều inject `generator=` trực tiếp nên nhánh chọn
generator theo config (`settings.menu_generator`) không được chạy dòng nào. Test
này phủ cả ba nhánh, dùng monkeypatch để không cần API key thật.
"""

from __future__ import annotations

import src.agents.assembly as assembly
from src.agents.hybrid import HybridMenuGenerator
from src.agents.optimizer import CPSATMenuOptimizer


class _FakeSettings:
    def __init__(self, choice: str) -> None:
        self.menu_generator = choice


def _patch_choice(monkeypatch, choice: str) -> None:
    monkeypatch.setattr(assembly, "get_settings", lambda: _FakeSettings(choice))


def test_config_cpsat_tra_ve_cpsat(monkeypatch):
    _patch_choice(monkeypatch, "cpsat")
    assert isinstance(assembly._generator_from_settings(), CPSATMenuOptimizer)


def test_config_hybrid_tra_ve_hybrid(monkeypatch):
    _patch_choice(monkeypatch, "hybrid")
    assert isinstance(assembly._generator_from_settings(), HybridMenuGenerator)


def test_config_gemini_tra_ve_gemini(monkeypatch):
    """Nhánh gemini phải dựng đúng GeminiMenuGenerator — dùng key giả để ctor qua."""
    _patch_choice(monkeypatch, "gemini")

    import src.services.llm as llm_mod

    class _FakeGeminiSettings:
        gemini_model = "gemini-2.5-flash"
        llm_temperature = 0.7

        def gemini_keys(self):
            return ["fake-key-for-ctor"]

    monkeypatch.setattr(llm_mod, "get_settings", lambda: _FakeGeminiSettings())

    from src.services.llm import GeminiMenuGenerator

    gen = assembly._generator_from_settings()
    assert isinstance(gen, GeminiMenuGenerator)


def test_config_mac_dinh_la_hybrid():
    """Mặc định của Settings (không đụng .env) phải là hybrid — an toàn không cần key."""
    from src.config import Settings

    assert Settings(_env_file=None).menu_generator == "hybrid"
