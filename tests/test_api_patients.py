"""BE-03: CRUD hồ sơ bệnh nhân + phân quyền (BE-09: A không xem được hồ sơ B)."""

from __future__ import annotations

import pytest


def _register_and_login(client, email, role, password="matkhau123"):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role, "full_name": "Test User"},
    )
    assert reg.status_code == 201, reg.text
    user_id = reg.json()["user_id"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def dietitian(client):
    return _register_and_login(client, "dietitian@example.com", "dietitian")


@pytest.fixture
def patient_user(client):
    return _register_and_login(client, "patient@example.com", "patient")


def _profile_payload(user_id):
    return {
        "user_id": user_id,
        "age": 58,
        "sex": "male",
        "height_cm": 165,
        "weight_kg": 65,
        "activity_level": "light",
        "conditions": [{"code": "T2DM", "stage": None}],
        "allergies": ["hải sản"],
        "medications": ["metformin"],
        "region": "north",
    }


def test_dietitian_tao_ho_so_thanh_cong(client, dietitian, patient_user):
    _, dt_headers = dietitian
    patient_id, _ = patient_user

    r = client.post("/api/v1/patients", json=_profile_payload(patient_id), headers=dt_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["age"] == 58
    assert body["allergies"] == ["hải sản"]
    assert body["medications"] == ["metformin"]


def test_patient_tu_tao_ho_so_bi_tu_choi_403(client, patient_user):
    patient_id, headers = patient_user
    r = client.post("/api/v1/patients", json=_profile_payload(patient_id), headers=headers)
    assert r.status_code == 403


def test_tao_ho_so_cho_user_id_khong_ton_tai_bi_404(client, dietitian):
    _, dt_headers = dietitian
    r = client.post("/api/v1/patients", json=_profile_payload("khong-ton-tai"), headers=dt_headers)
    assert r.status_code == 404


def test_tao_ho_so_cho_user_role_dietitian_bi_422(client, dietitian):
    """user_id phải trỏ tới role=patient — không tạo hồ sơ bệnh nhân cho tài khoản dietitian."""
    dietitian_user_id, dt_headers = dietitian
    r = client.post("/api/v1/patients", json=_profile_payload(dietitian_user_id), headers=dt_headers)
    assert r.status_code == 422


def test_tao_2_lan_cho_cung_user_bi_409(client, dietitian, patient_user):
    _, dt_headers = dietitian
    patient_id, _ = patient_user
    r1 = client.post("/api/v1/patients", json=_profile_payload(patient_id), headers=dt_headers)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/patients", json=_profile_payload(patient_id), headers=dt_headers)
    assert r2.status_code == 409


def test_benh_nhan_a_khong_xem_duoc_ho_so_benh_nhan_b_tra_404(client, dietitian):
    """BE-09 AC: bệnh nhân A gọi tài nguyên của B → 404 (không phải 403 — không lộ thông tin)."""
    _, dt_headers = dietitian
    a_id, a_headers = _register_and_login(client, "a@example.com", "patient")
    b_id, b_headers = _register_and_login(client, "b@example.com", "patient")

    profile_b = client.post("/api/v1/patients", json=_profile_payload(b_id), headers=dt_headers).json()

    r = client.get(f"/api/v1/patients/{profile_b['id']}", headers=a_headers)
    assert r.status_code == 404


def test_benh_nhan_xem_duoc_ho_so_chinh_minh(client, dietitian, patient_user):
    _, dt_headers = dietitian
    patient_id, patient_headers = patient_user
    profile = client.post("/api/v1/patients", json=_profile_payload(patient_id), headers=dt_headers).json()

    r = client.get(f"/api/v1/patients/{profile['id']}", headers=patient_headers)
    assert r.status_code == 200
    assert r.json()["id"] == profile["id"]


def test_sua_ho_so_partial_update_khong_mat_field_khac(client, dietitian, patient_user):
    _, dt_headers = dietitian
    patient_id, patient_headers = patient_user
    profile = client.post("/api/v1/patients", json=_profile_payload(patient_id), headers=dt_headers).json()

    r = client.put(f"/api/v1/patients/{profile['id']}", json={"weight_kg": 70}, headers=patient_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["weight_kg"] == 70
    assert body["age"] == 58  # không đổi
    assert body["allergies"] == ["hải sản"]  # không đổi vì không gửi field này


def test_can_nang_ngoai_khoang_hop_le_bi_422(client, dietitian, patient_user):
    _, dt_headers = dietitian
    patient_id, _ = patient_user
    payload = _profile_payload(patient_id)
    payload["weight_kg"] = 500  # ngoài khoảng 20-300
    r = client.post("/api/v1/patients", json=payload, headers=dt_headers)
    assert r.status_code == 422


def test_danh_sach_benh_nhan_chi_dietitian_goi_duoc(client, dietitian, patient_user):
    _, dt_headers = dietitian
    _, patient_headers = patient_user

    r_patient = client.get("/api/v1/patients", headers=patient_headers)
    assert r_patient.status_code == 403

    r_dietitian = client.get("/api/v1/patients", headers=dt_headers)
    assert r_dietitian.status_code == 200
    assert "items" in r_dietitian.json()
    assert "total" in r_dietitian.json()
