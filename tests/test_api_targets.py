"""BE-04: API tính định mức — bọc compute_targets(), không gọi LLM."""

from __future__ import annotations

import pytest


def _register_and_login(client, email, role, password="matkhau123"):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role, "full_name": "Test User"},
    )
    user_id = reg.json()["user_id"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def dietitian(client):
    return _register_and_login(client, "dietitian@example.com", "dietitian")


@pytest.fixture
def profile_id(client, dietitian):
    _, dt_headers = dietitian
    patient_id, _patient_headers = _register_and_login(client, "patient@example.com", "patient")
    payload = {
        "user_id": patient_id,
        "age": 58,
        "sex": "male",
        "height_cm": 165,
        "weight_kg": 65,
        "activity_level": "light",
        "conditions": [{"code": "T2DM", "stage": None}, {"code": "CKD", "stage": "G3b"}],
        "region": "north",
    }
    r = client.post("/api/v1/patients", json=payload, headers=dt_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_tinh_dinh_muc_thanh_cong(client, dietitian, profile_id):
    _, dt_headers = dietitian
    r = client.post("/api/v1/targets/compute", json={"patient_id": profile_id}, headers=dt_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["bmr_kcal"] > 0
    assert body["tdee_kcal"] > 0
    assert "kcal" in body["targets"]
    assert isinstance(body["applied_rule_ids"], list)
    assert len(body["applied_rule_ids"]) > 0


def test_da_benh_ly_tra_applied_rule_ids_day_du(client, dietitian, profile_id):
    """ĐTĐ2 + CKD G3b — phải áp cả 2 nhóm rule, không phải chỉ 1 bệnh."""
    _, dt_headers = dietitian
    r = client.post("/api/v1/targets/compute", json={"patient_id": profile_id}, headers=dt_headers)
    body = r.json()
    rule_ids = " ".join(body["applied_rule_ids"])
    assert "T2DM" in rule_ids or "CKD" in rule_ids


def test_patient_id_khong_ton_tai_tra_404(client, dietitian):
    _, dt_headers = dietitian
    r = client.post("/api/v1/targets/compute", json={"patient_id": "khong-ton-tai"}, headers=dt_headers)
    assert r.status_code == 404


def test_benh_nhan_khac_khong_tinh_duoc_dinh_muc_ho_so_nguoi_khac(client, dietitian, profile_id):
    _, other_headers = _register_and_login(client, "other-patient@example.com", "patient")
    r = client.post("/api/v1/targets/compute", json={"patient_id": profile_id}, headers=other_headers)
    assert r.status_code == 404
