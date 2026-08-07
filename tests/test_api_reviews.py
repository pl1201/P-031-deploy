"""HIT-02: hàng chờ duyệt + duyệt/từ chối thực đơn."""

from __future__ import annotations

import pytest

from src.config import get_settings
from src.db.models import AuditLog


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
    return _register_and_login(client, "dietitian@example.com", "dietitian")


@pytest.fixture
def pending_plan(client, dietitian):
    """Tạo hồ sơ + gọi sinh thực đơn thật (CP-SAT) -> trả về plan pending_review."""
    _, dt_headers = dietitian
    patient_id, _ = _register_and_login(client, "patient@example.com", "patient")
    profile = client.post(
        "/api/v1/patients",
        json={
            "user_id": patient_id,
            "age": 45,
            "sex": "male",
            "height_cm": 170,
            "weight_kg": 70,
            "activity_level": "light",
            "conditions": [{"code": "T2DM", "stage": None}],
            "region": "north",
        },
        headers=dt_headers,
    ).json()
    create = client.post(
        "/api/v1/meal-plans", json={"patient_id": profile["id"], "plan_date": "2026-08-11"}, headers=dt_headers
    )
    plan_id = create.json()["plan_id"]
    detail = client.get(f"/api/v1/meal-plans/{plan_id}", headers=dt_headers).json()
    assert detail["status"] == "pending_review"
    return plan_id, detail


def test_danh_sach_cho_duyet_chi_dietitian_goi_duoc(client, dietitian, pending_plan):
    plan_id, _ = pending_plan
    _, dt_headers = dietitian
    r = client.get("/api/v1/reviews/pending", headers=dt_headers)
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()]
    assert plan_id in ids


def test_patient_khong_goi_duoc_danh_sach_cho_duyet(client, pending_plan):
    _, patient_headers = _register_and_login(client, "someone@example.com", "patient")
    r = client.get("/api/v1/reviews/pending", headers=patient_headers)
    assert r.status_code == 403


def test_duyet_khong_sua_gi_thanh_cong(client, dietitian, pending_plan):
    plan_id, _ = pending_plan
    _, dt_headers = dietitian
    r = client.post(f"/api/v1/reviews/{plan_id}/approve", json={"notes": "OK, đúng định mức"}, headers=dt_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "approved"
    assert body["reviewer_notes"] == "OK, đúng định mức"


def test_duyet_ghi_audit_log(client, dietitian, pending_plan, db_session):
    plan_id, _ = pending_plan
    _, dt_headers = dietitian
    client.post(f"/api/v1/reviews/{plan_id}/approve", json={}, headers=dt_headers)

    logs = db_session.query(AuditLog).filter(AuditLog.action == "approve").all()
    assert len(logs) == 1
    assert logs[0].after["status"] == "approved"


def test_duyet_sua_gram_tinh_lai_dinh_duong(client, dietitian, pending_plan):
    plan_id, detail = pending_plan
    _, dt_headers = dietitian
    first_item = detail["items"][0]
    # Giảm gram (không tăng): tăng có thể đẩy thực đơn vượt hard rule (carb/sugar)
    # nếu bản gốc đã sát ngưỡng trên — đúng hành vi RULE-3 (API phải chặn), không
    # phải bug, nhưng làm test flaky vì phụ thuộc thực đơn cụ thể được sinh ra.
    # Giảm gram không bao giờ tự tạo vi phạm MAX mới nên an toàn cho mục đích
    # test này (xác nhận approve+edit tính lại dinh dưỡng, không phải test biên).
    new_grams = max(first_item["grams"] - 20, 1)

    r = client.post(
        f"/api/v1/reviews/{plan_id}/approve",
        json={"edits": [{"item_id": first_item["id"], "grams": new_grams}]},
        headers=dt_headers,
    )
    assert r.status_code == 200, r.text
    approved = r.json()
    assert approved["status"] == "approved"
    edited = next(i for i in approved["items"] if i["id"] == first_item["id"])
    assert edited["grams"] == new_grams
    # dinh dưỡng phải đổi theo gram mới, không phải giữ nguyên số cũ (RULE-1: server
    # tự tính lại, không tin số client gửi kèm)
    assert approved["computed_nutrition"] != detail["computed_nutrition"]


def test_duyet_bi_tu_choi_neu_lan_2(client, dietitian, pending_plan):
    plan_id, _ = pending_plan
    _, dt_headers = dietitian
    r1 = client.post(f"/api/v1/reviews/{plan_id}/approve", json={}, headers=dt_headers)
    assert r1.status_code == 200
    r2 = client.post(f"/api/v1/reviews/{plan_id}/approve", json={}, headers=dt_headers)
    assert r2.status_code == 409


def test_tu_choi_thieu_ly_do_bi_422(client, dietitian, pending_plan):
    plan_id, _ = pending_plan
    _, dt_headers = dietitian
    r = client.post(f"/api/v1/reviews/{plan_id}/reject", json={"reason": "ngắn"}, headers=dt_headers)
    assert r.status_code == 422


def test_tu_choi_thanh_cong(client, dietitian, pending_plan):
    plan_id, _ = pending_plan
    _, dt_headers = dietitian
    r = client.post(
        f"/api/v1/reviews/{plan_id}/reject",
        json={"reason": "Quá nhiều tinh bột buổi tối, cần sinh lại"},
        headers=dt_headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_benh_nhan_khong_duyet_duoc(client, pending_plan):
    plan_id, _ = pending_plan
    _, patient_headers = _register_and_login(client, "notdietitian@example.com", "patient")
    r = client.post(f"/api/v1/reviews/{plan_id}/approve", json={}, headers=patient_headers)
    assert r.status_code == 403


def test_plan_khong_ton_tai_tra_404(client, dietitian):
    _, dt_headers = dietitian
    r = client.post("/api/v1/reviews/khong-ton-tai/approve", json={}, headers=dt_headers)
    assert r.status_code == 404
