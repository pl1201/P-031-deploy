from __future__ import annotations

from src.db import base


def test_get_engine_reuses_one_process_wide_pool() -> None:
    base.get_engine.cache_clear()
    first = base.get_engine()
    second = base.get_engine()

    try:
        assert first is second
    finally:
        first.dispose()
        base.get_engine.cache_clear()
