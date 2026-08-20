"""API test — pantry_items + substitution_scopes + thực đơn tương đương (P2/AGT-12)."""

from __future__ import annotations

import pytest
from conftest import _create_user_directly

from src.config import get_settings


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
    token = login.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _force_cpsat(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "menu_generator", "cpsat")


@pytest.fixture
def dietitian(client):
    return _register_and_login(client, "dietitian@example.com", "dietitian")


@pytest.fixture
def patient(client):
    return _register_and_login(client, "patient@example.com", "patient")


@pytest.fixture
def profile_id(client, dietitian, patient):
    _, dt_headers = dietitian
    patient_id, _ = patient
    payload = {
        "user_id": patient_id,
        "age": 45,
        "sex": "male",
        "height_cm": 170,
        "weight_kg": 70,
        "activity_level": "light",
        "conditions": [{"code": "T2DM", "stage": None}],
        "region": "north",
    }
    r = client.post("/api/v1/patients", json=payload, headers=dt_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture
def approved_plan_id(client, dietitian, profile_id):
    """Thực đơn gốc thật, đã duyệt — điều kiện bắt buộc để tạo substitution scope."""
    _, dt_headers = dietitian
    create = client.post(
        "/api/v1/meal-plans", json={"patient_id": profile_id, "plan_date": "2026-08-10"}, headers=dt_headers
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
    return plan_id


def _fill_pantry_with_full_candidates(client, profile_id, headers):
    """Khai báo TOÀN BỘ ứng viên curated làm tủ lạnh — trường hợp tốt nhất để
    solve_equivalent chắc chắn giải được (không phụ thuộc bệnh nhân thật khai
    tay từng món)."""
    from src.agents.nodes.core import USDA_BULK_ID_THRESHOLD
    from src.clinical.seeds import load_food_repository

    foods = load_food_repository()
    for food in foods.all():
        if food.id >= USDA_BULK_ID_THRESHOLD:
            continue
        r = client.post(
            f"/api/v1/pantry/{profile_id}", json={"food_id": food.id, "qty": 1, "unit": "phần"}, headers=headers
        )
        assert r.status_code == 201, r.text


class TestPantry:
    def test_them_va_xem_pantry(self, client, dietitian, profile_id):
        _, dt_headers = dietitian
        add = client.post(
            f"/api/v1/pantry/{profile_id}", json={"food_id": 1, "qty": 500, "unit": "g"}, headers=dt_headers
        )
        assert add.status_code == 201, add.text
        assert add.json()["name_vi"]

        listed = client.get(f"/api/v1/pantry/{profile_id}", headers=dt_headers)
        assert listed.status_code == 200
        assert len(listed.json()) == 1

    def test_food_id_khong_ton_tai_bi_422(self, client, dietitian, profile_id):
        _, dt_headers = dietitian
        r = client.post(
            f"/api/v1/pantry/{profile_id}", json={"food_id": 999999, "qty": 1, "unit": "g"}, headers=dt_headers
        )
        assert r.status_code == 422

    def test_benh_nhan_khac_khong_xem_duoc_pantry(self, client, dietitian, profile_id):
        _, other_headers = _register_and_login(client, "other-pantry@example.com", "patient")
        r = client.get(f"/api/v1/pantry/{profile_id}", headers=other_headers)
        assert r.status_code == 404

    def test_xoa_pantry_item(self, client, dietitian, profile_id):
        _, dt_headers = dietitian
        add = client.post(
            f"/api/v1/pantry/{profile_id}", json={"food_id": 1, "qty": 500, "unit": "g"}, headers=dt_headers
        )
        item_id = add.json()["id"]
        deleted = client.delete(f"/api/v1/pantry/{profile_id}/{item_id}", headers=dt_headers)
        assert deleted.status_code == 204
        listed = client.get(f"/api/v1/pantry/{profile_id}", headers=dt_headers)
        assert listed.json() == []


class TestSubstitutionScope:
    def test_benh_nhan_khong_tao_duoc_scope(self, client, patient, approved_plan_id):
        _, patient_headers = patient
        r = client.post("/api/v1/substitution-scopes", json={"base_plan_id": approved_plan_id}, headers=patient_headers)
        assert r.status_code == 403

    def test_chua_approved_thi_khong_tao_duoc_scope(self, client, dietitian, profile_id):
        _, dt_headers = dietitian
        create = client.post(
            "/api/v1/meal-plans", json={"patient_id": profile_id, "plan_date": "2026-08-11"}, headers=dt_headers
        )
        pending_plan_id = create.json()["plan_id"]
        r = client.post("/api/v1/substitution-scopes", json={"base_plan_id": pending_plan_id}, headers=dt_headers)
        assert r.status_code == 409

    def test_dietitian_tao_scope_dung_default_dec018(self, client, dietitian, approved_plan_id):
        _, dt_headers = dietitian
        r = client.post("/api/v1/substitution-scopes", json={"base_plan_id": approved_plan_id}, headers=dt_headers)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["tolerance"] == pytest.approx(0.10)
        assert body["max_auto_releases"] == 5
        assert body["release_count"] == 0

    def test_revoke_scope(self, client, dietitian, approved_plan_id):
        _, dt_headers = dietitian
        create = client.post("/api/v1/substitution-scopes", json={"base_plan_id": approved_plan_id}, headers=dt_headers)
        scope_id = create.json()["id"]
        r = client.post(f"/api/v1/substitution-scopes/{scope_id}/revoke", headers=dt_headers)
        assert r.status_code == 200
        assert r.json()["revoked_at"] is not None


class TestEquivalentMenu:
    def test_khong_co_scope_thi_bi_403(self, client, dietitian, patient, profile_id, approved_plan_id):
        _, patient_headers = patient
        r = client.post(
            f"/api/v1/meal-plans/{approved_plan_id}/equivalent",
            json={"plan_date": "2026-08-12"},
            headers=patient_headers,
        )
        assert r.status_code == 403

    def test_co_scope_va_tu_lanh_day_du_thi_tu_phat_hanh(
        self, client, dietitian, patient, profile_id, approved_plan_id
    ):
        _, dt_headers = dietitian
        _, patient_headers = patient

        scope = client.post("/api/v1/substitution-scopes", json={"base_plan_id": approved_plan_id}, headers=dt_headers)
        assert scope.status_code == 201, scope.text

        _fill_pantry_with_full_candidates(client, profile_id, patient_headers)

        r = client.post(
            f"/api/v1/meal-plans/{approved_plan_id}/equivalent",
            json={"plan_date": "2026-08-12"},
            headers=patient_headers,
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["plan_id"]

        plan = client.get(f"/api/v1/meal-plans/{body['plan_id']}", headers=dt_headers)
        assert plan.status_code == 200
        assert plan.json()["status"] in ("approved", "pending_review")
        # RULE-1: mọi item vẫn có food_id + nguồn thật, không có số nào không nguồn.
        assert all(item["food_id"] and item["source_ref"] for item in plan.json()["items"])

        scope_after = client.get(f"/api/v1/pantry/{profile_id}", headers=patient_headers)
        assert scope_after.status_code == 200  # còn dùng được API khác sau khi phát hành

    def test_tu_lanh_ngheo_tra_ve_ly_do_khong_tao_plan_moi(
        self, client, dietitian, patient, profile_id, approved_plan_id
    ):
        _, dt_headers = dietitian
        _, patient_headers = patient
        client.post("/api/v1/substitution-scopes", json={"base_plan_id": approved_plan_id}, headers=dt_headers)

        client.post(
            f"/api/v1/pantry/{profile_id}", json={"food_id": 1, "qty": 100, "unit": "g"}, headers=patient_headers
        )

        r = client.post(
            f"/api/v1/meal-plans/{approved_plan_id}/equivalent",
            json={"plan_date": "2026-08-13"},
            headers=patient_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["released"] is False
        assert body["plan_id"] is None
        assert body["reason_vi"]

    def test_benh_nhan_khac_khong_goi_duoc(self, client, dietitian, approved_plan_id):
        _, other_headers = _register_and_login(client, "other-equiv@example.com", "patient")
        r = client.post(
            f"/api/v1/meal-plans/{approved_plan_id}/equivalent",
            json={"plan_date": "2026-08-12"},
            headers=other_headers,
        )
        assert r.status_code == 404
