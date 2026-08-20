"""Bệnh nhân tự ghi cân nặng, sở thích, onboarding, và trung tâm thông báo.

Bao phủ các route mới: POST/GET /patients/me/observations (chặn cứng
observation_type="weight", source="patient_reported"), /patients/me/preferences,
/auth/me/accept-terms, /auth/me/onboarding-complete, /notifications/*.
"""

from __future__ import annotations

import pytest
from conftest import _create_user_directly


def _register_and_login(client, email, role, password="matkhau123"):
    if role != "patient":
        user_id = _create_user_directly(client, email, role, password)
        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return user_id, {"Authorization": f"Bearer {login.json()['access_token']}"}
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


@pytest.fixture
def patient_with_profile(client, dietitian, patient_user):
    _, dt_headers = dietitian
    patient_id, headers = patient_user
    payload = {
        "user_id": patient_id,
        "age": 58,
        "sex": "male",
        "height_cm": 165,
        "weight_kg": 65,
        "activity_level": "light",
        "conditions": [],
        "allergies": [],
        "medications": [],
    }
    r = client.post("/api/v1/patients", json=payload, headers=dt_headers)
    assert r.status_code == 201, r.text
    return headers


def test_benh_nhan_tu_ghi_can_nang_thanh_cong(client, patient_with_profile):
    headers = patient_with_profile
    r = client.post(
        "/api/v1/patients/me/observations",
        json={"value": 64.5, "measured_at": "2026-08-19T08:00:00", "note": "Trước ăn sáng"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["observation_type"] == "weight"
    assert body["unit"] == "kg"
    assert body["source"] == "patient_reported"

    listed = client.get("/api/v1/patients/me/observations", headers=headers)
    assert listed.status_code == 200
    # +1 vì tạo hồ sơ đã tự ghi 1 quan sát cân nặng khởi tạo (xem patients.py create_patient).
    rows = listed.json()
    assert len(rows) == 2
    assert any(row["source"] == "patient_reported" for row in rows)


def test_can_nang_ngoai_khoang_hop_le_bi_422(client, patient_with_profile):
    headers = patient_with_profile
    r = client.post(
        "/api/v1/patients/me/observations",
        json={"value": 5, "measured_at": "2026-08-19T08:00:00"},
        headers=headers,
    )
    assert r.status_code == 422


def test_chua_co_ho_so_thi_tu_ghi_can_nang_tra_404(client, patient_user):
    _, headers = patient_user
    r = client.post(
        "/api/v1/patients/me/observations",
        json={"value": 60, "measured_at": "2026-08-19T08:00:00"},
        headers=headers,
    )
    assert r.status_code == 404


def test_dietitian_khong_goi_duoc_route_tu_ghi_cua_benh_nhan(client, dietitian, patient_with_profile):
    _, dt_headers = dietitian
    r = client.post(
        "/api/v1/patients/me/observations",
        json={"value": 60, "measured_at": "2026-08-19T08:00:00"},
        headers=dt_headers,
    )
    assert r.status_code == 403


def test_so_thich_doc_ghi(client, patient_with_profile):
    headers = patient_with_profile
    empty = client.get("/api/v1/patients/me/preferences", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["disliked_foods"] == []

    updated = client.put(
        "/api/v1/patients/me/preferences",
        json={
            "disliked_foods": ["mắm tôm"],
            "usual_meal_times": {"breakfast": "07:00"},
            "meal_reminders_enabled": False,
        },
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["disliked_foods"] == ["mắm tôm"]
    assert updated.json()["meal_reminders_enabled"] is False


def test_dong_y_dieu_khoan_va_hoan_tat_onboarding(client, patient_user):
    _, headers = patient_user
    r1 = client.post("/api/v1/auth/me/accept-terms", headers=headers)
    assert r1.status_code == 200
    assert r1.json()["terms_accepted_at"] is not None
    assert r1.json()["onboarding_completed_at"] is None

    r2 = client.post("/api/v1/auth/me/onboarding-complete", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["onboarding_completed_at"] is not None


def test_thong_bao_rong_khi_chua_co_gi(client, patient_user):
    _, headers = patient_user
    r = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert r.status_code == 200
    assert r.json()["unread"] == 0


def test_duyet_thuc_don_tao_thong_bao_cho_benh_nhan(client, dietitian, patient_with_profile, db_session):
    """Hook trong reviews.py: approve/reject phải tạo Notification cho đúng bệnh nhân."""
    from datetime import date

    from src.db.models import MealPlan, PatientProfile, User

    patient_headers = patient_with_profile
    patient_row = db_session.query(User).filter(User.email == "patient@example.com").first()
    profile = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient_row.id).first()

    plan = MealPlan(
        profile_id=profile.id,
        plan_date=date(2026, 8, 19),
        status="pending_review",
        highest_risk="none",
        menu_hash="h" * 16,
        nutrition_hash="n" * 16,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    _, dt_headers = dietitian
    r = client.post(f"/api/v1/reviews/{plan.id}/approve", json={"notes": None}, headers=dt_headers)
    assert r.status_code == 200, r.text

    notified = client.get("/api/v1/notifications", headers=patient_headers)
    assert notified.status_code == 200
    types = [item["type"] for item in notified.json()]
    assert "review_decision" in types

    notification_id = notified.json()[0]["id"]
    marked = client.patch(f"/api/v1/notifications/{notification_id}/read", headers=patient_headers)
    assert marked.status_code == 200
    assert marked.json()["read_at"] is not None
