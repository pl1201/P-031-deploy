"""Test DAT-04 — phân rã món ăn thành nguyên liệu, tính dinh dưỡng bằng Python.

Mốc hồi quy: phở bò 1 bát ~3,3–4,0 g muối (khớp nghiên cứu). Nếu lệch xa →
công thức hoặc số liệu natri của nguyên liệu sai (thường là nước mắm/muối).
"""

from __future__ import annotations

import pytest

from src.clinical.nutrition import compute_nutrition
from src.clinical.seeds import load_dish_menus, load_food_repository, salt_equiv_g


@pytest.fixture(scope="module")
def repo():
    return load_food_repository()


@pytest.fixture(scope="module")
def dishes():
    return load_dish_menus()


def test_pho_bo_muoi_trong_khoang_nghien_cuu(repo, dishes):
    """Phở bò tính từ nguyên liệu phải cho ~3,3–4,0 g muối/bát."""
    nutrition = compute_nutrition(dishes["PHO-BO"], repo)
    salt = salt_equiv_g(nutrition.na_mg)
    assert 3.3 <= salt <= 4.0, f"Muối phở bò = {salt} g (Na={nutrition.na_mg} mg) — ngoài mốc 3,3–4,0 g"


def test_canh_rau_muong_it_muoi_hon_pho(repo, dishes):
    """Món canh phải ít muối hơn hẳn phở — kiểm tra tương quan hợp lý."""
    pho = salt_equiv_g(compute_nutrition(dishes["PHO-BO"], repo).na_mg)
    canh = salt_equiv_g(compute_nutrition(dishes["CANH-RAU-MUONG"], repo).na_mg)
    assert canh < pho


def test_moi_nguyen_lieu_deu_tra_duoc_nguon(repo, dishes):
    """RULE-2: mọi món dựng được đều có nguồn cho từng nguyên liệu."""
    for dish_id, menu in dishes.items():
        summary = compute_nutrition(menu, repo)
        assert summary.sources, f"{dish_id} không có nguồn"
        assert all(s.source_ref for s in summary.sources), f"{dish_id} có nguyên liệu thiếu nguồn"
