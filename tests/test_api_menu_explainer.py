"""AGT-13 (B2): GET /meal-plans/{plan_id}/explain.

`explain_menu_naturally` gọi Gemini thật — mock lại để test không cần API key
và không tốn quota. Trọng tâm: guard chặn LLM bịa số (fallback template), và
gate RULE-3 đúng (409 chưa duyệt, 404 không phải chủ hồ sơ).
"""

from __future__ import annotations

import pytest

from src.config import get_settings


def _register_and_login(client, email, role, password="matkhau123"):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role, "full_name": "Test User"},
    )
    assert reg.status_code == 201, reg.text
    user_id = reg.json()["user_id"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _force_cpsat(monkeypatch):
    monkeypatch.setattr(get_settings(), "menu_generator", "cpsat")


@pytest.fixture
def dietitian(client):
    return _register_and_login(client, "dt_explain@example.com", "dietitian")


@pytest.fixture
def approved_plan(client, dietitian):
    """Sinh thực đơn thật (CP-SAT) rồi duyệt -> plan approved + patient headers chủ hồ sơ."""
    _, dt_headers = dietitian
    patient_user_id, patient_headers = _register_and_login(client, "bn_explain@example.com", "patient")
    profile = client.post(
        "/api/v1/patients",
        json={
            "user_id": patient_user_id,
            "age": 50,
            "sex": "female",
            "height_cm": 160,
            "weight_kg": 60,
            "activity_level": "light",
            "conditions": [{"code": "T2DM", "stage": None}],
            "region": "north",
        },
        headers=dt_headers,
    ).json()
    create = client.post(
        "/api/v1/meal-plans", json={"patient_id": profile["id"], "plan_date": "2026-08-12"}, headers=dt_headers
    )
    plan_id = create.json()["plan_id"]
    # Ngưỡng CKD/T2DM hiện chưa `verified` -> mọi lần duyệt đều dính P1 "unverified
    # rule", buộc phải ghi lý do override mới qua được (đúng thiết kế fail-safe).
    approve = client.post(
        f"/api/v1/reviews/{plan_id}/approve",
        json={"notes": "Test fixture: chấp nhận rule chưa xác minh để dựng dữ liệu cho test"},
        headers=dt_headers,
    )
    assert approve.status_code == 200, approve.text
    return plan_id, patient_headers


def _fake_explain_clean(facts):
    return f"Thực đơn ngày {facts.plan_date} có {len(facts.items)} món, cân đối dinh dưỡng."


def test_benh_nhan_chu_ho_so_xem_duoc(client, approved_plan, monkeypatch):
    plan_id, patient_headers = approved_plan
    monkeypatch.setattr("src.api.routes.menu_explainer.explain_menu_naturally", _fake_explain_clean)

    r = client.get(f"/api/v1/meal-plans/{plan_id}/explain", headers=patient_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "facts" in body and "text_vi" in body
    assert body["facts"]["plan_date"] == "2026-08-12"
    assert "cân đối dinh dưỡng" in body["text_vi"]


def test_dietitian_xem_duoc_thuc_don_khong_phai_cua_minh_quan_ly_truc_tiep(
    client, dietitian, approved_plan, monkeypatch
):
    plan_id, _ = approved_plan
    _, dt_headers = dietitian
    monkeypatch.setattr("src.api.routes.menu_explainer.explain_menu_naturally", _fake_explain_clean)

    r = client.get(f"/api/v1/meal-plans/{plan_id}/explain", headers=dt_headers)
    assert r.status_code == 200, r.text


def test_llm_bia_so_thi_bi_chan_dung_ban_mau(client, approved_plan, monkeypatch):
    """LLM chèn con số không có trong facts (VD 999999) -> guard chặn, route trả
    bản render mẫu tất định thay vì văn bản chưa qua kiểm."""

    def _fake_lie(facts):
        return "Thực đơn này có 999999 kcal cực kỳ vô lý."

    monkeypatch.setattr("src.api.routes.menu_explainer.explain_menu_naturally", _fake_lie)

    _, patient_headers = approved_plan
    plan_id, _ = approved_plan
    r = client.get(f"/api/v1/meal-plans/{plan_id}/explain", headers=patient_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "999999" not in body["text_vi"]
    # Bản mẫu luôn liệt kê tên món — khẳng định đây là fallback, không phải văn bản LLM gốc.
    assert any(item["name_vi"] in body["text_vi"] for item in body["facts"]["items"])


def test_thuc_don_chua_duyet_tra_409(client, dietitian):
    """pending_review (chưa approve) -> 409, không phải 404/200."""
    _, dt_headers = dietitian
    patient_user_id, _ = _register_and_login(client, "bn_pending_explain@example.com", "patient")
    profile = client.post(
        "/api/v1/patients",
        json={
            "user_id": patient_user_id,
            "age": 40,
            "sex": "male",
            "height_cm": 170,
            "weight_kg": 68,
            "activity_level": "light",
            "conditions": [{"code": "T2DM", "stage": None}],
            "region": "north",
        },
        headers=dt_headers,
    ).json()
    create = client.post(
        "/api/v1/meal-plans", json={"patient_id": profile["id"], "plan_date": "2026-08-13"}, headers=dt_headers
    )
    plan_id = create.json()["plan_id"]

    r = client.get(f"/api/v1/meal-plans/{plan_id}/explain", headers=dt_headers)
    assert r.status_code == 409, r.text


def test_benh_nhan_khac_khong_phai_chu_ho_so_tra_404(client, approved_plan):
    plan_id, _ = approved_plan
    _, other_patient_headers = _register_and_login(client, "khac_explain@example.com", "patient")

    r = client.get(f"/api/v1/meal-plans/{plan_id}/explain", headers=other_patient_headers)
    assert r.status_code == 404, r.text


def test_plan_khong_ton_tai_tra_404(client, dietitian):
    _, dt_headers = dietitian
    r = client.get("/api/v1/meal-plans/khong-ton-tai/explain", headers=dt_headers)
    assert r.status_code == 404
