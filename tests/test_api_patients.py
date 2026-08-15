"""BE-03: CRUD hồ sơ bệnh nhân + phân quyền (BE-09: A không xem được hồ sơ B)."""

from __future__ import annotations

import pytest
from sqlalchemy import event


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


def test_benh_nhan_lay_duoc_ho_so_cua_chinh_minh(client):
    """`/patients/me` — không có nó thì bệnh nhân không biết profile_id của mình.

    Phải khai báo TRƯỚC `/{profile_id}`; nếu sai thứ tự, "me" bị hiểu là một
    profile_id và endpoint luôn trả 404.
    """
    dt_id, dt_headers = _register_and_login(client, "dt_me@example.com", "dietitian")
    bn_id, bn_headers = _register_and_login(client, "bn_me@example.com", "patient")

    created = client.post(
        "/api/v1/patients",
        json={
            "user_id": bn_id,
            "age": 55,
            "sex": "female",
            "height_cm": 158,
            "weight_kg": 58,
            "activity_level": "light",
            "conditions": [{"code": "T2DM", "stage": None}],
        },
        headers=dt_headers,
    )
    assert created.status_code == 201, created.text

    r = client.get("/api/v1/patients/me", headers=bn_headers)
    assert r.status_code == 200, r.text
    assert r.json()["id"] == created.json()["id"]
    assert r.json()["user_id"] == bn_id


def test_chua_co_ho_so_thi_me_tra_404(client):
    _, headers = _register_and_login(client, "bn_chua_hs@example.com", "patient")
    assert client.get("/api/v1/patients/me", headers=headers).status_code == 404


def test_patient_profile_update_request_has_real_clinician_workflow(client, dietitian, patient_user):
    _, dietitian_headers = dietitian
    patient_id, patient_headers = patient_user
    profile = client.post("/api/v1/patients", json=_profile_payload(patient_id), headers=dietitian_headers).json()

    created = client.post(
        "/api/v1/patients/me/update-requests",
        json={"message": "Tôi vừa đổi thuốc và cần chuyên gia kiểm tra lại hồ sơ."},
        headers=patient_headers,
    )
    assert created.status_code == 201, created.text
    assert created.json()["profile_id"] == profile["id"]
    assert created.json()["status"] == "pending"

    duplicate = client.post(
        "/api/v1/patients/me/update-requests",
        json={"message": "Tạo thêm một yêu cầu khi yêu cầu cũ chưa xử lý."},
        headers=patient_headers,
    )
    assert duplicate.status_code == 409

    queue = client.get("/api/v1/patients/update-requests", headers=dietitian_headers)
    assert queue.status_code == 200
    assert [item["id"] for item in queue.json()] == [created.json()["id"]]

    forbidden = client.patch(
        f"/api/v1/patients/update-requests/{created.json()['id']}",
        json={"resolution_note": "Đã xử lý"},
        headers=patient_headers,
    )
    assert forbidden.status_code == 403

    resolved = client.patch(
        f"/api/v1/patients/update-requests/{created.json()['id']}",
        json={"resolution_note": "Đã liên hệ và cập nhật thuốc trong hồ sơ."},
        headers=dietitian_headers,
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "resolved"

    history = client.get("/api/v1/patients/me/update-requests", headers=patient_headers)
    assert history.status_code == 200
    assert history.json()[0]["resolution_note"] == "Đã liên hệ và cập nhật thuốc trong hồ sơ."


def test_patient_search_runs_on_server(client, dietitian):
    _, dietitian_headers = dietitian
    matching_id, _ = _register_and_login(client, "search-match@example.com", "patient")
    other_id, _ = _register_and_login(client, "search-other@example.com", "patient")
    matching = _profile_payload(matching_id)
    # Two matching medications must still return one profile.  This protects
    # the EXISTS-based search from regressing to a duplicate-producing join.
    matching["medications"] = ["losartan", "losartan potassium"]
    client.post("/api/v1/patients", json=matching, headers=dietitian_headers)
    client.post("/api/v1/patients", json=_profile_payload(other_id), headers=dietitian_headers)

    response = client.get("/api/v1/patients?search=losartan&page_size=1", headers=dietitian_headers)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["user_id"] == matching_id


def test_patient_list_loads_related_data_in_bounded_queries(client, dietitian, db_session):
    """A page of patients must not issue two relationship queries per patient."""
    _, dietitian_headers = dietitian
    for index in range(3):
        patient_id, _ = _register_and_login(client, f"eager-{index}@example.com", "patient")
        payload = _profile_payload(patient_id)
        payload["allergies"] = [f"allergy-{index}"]
        payload["medications"] = [f"medicine-{index}"]
        created = client.post("/api/v1/patients", json=payload, headers=dietitian_headers)
        assert created.status_code == 201, created.text

    db_session.expire_all()
    statements: list[str] = []

    def record_statement(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)

    event.listen(db_session.bind, "before_cursor_execute", record_statement)
    try:
        response = client.get("/api/v1/patients?page_size=20", headers=dietitian_headers)
    finally:
        event.remove(db_session.bind, "before_cursor_execute", record_statement)

    assert response.status_code == 200, response.text
    # Auth + count + profiles + batched allergies + batched medications.
    assert len(statements) <= 5
