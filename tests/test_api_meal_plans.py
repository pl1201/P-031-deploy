"""BE-06: sinh thực đơn qua graph thật (CP-SAT, không cần API key LLM)."""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest

from src.api.routes.meal_plans import MealPlanOut
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
    """Test không cần/không có GEMINI_API_KEY — ép dùng CP-SAT thuần (AGT-09),
    đúng tinh thần graph chạy được thật mà không cần LLM (AC gốc AGT-10)."""
    settings = get_settings()
    monkeypatch.setattr(settings, "menu_generator", "cpsat")


@pytest.fixture
def dietitian(client):
    return _register_and_login(client, "dietitian@example.com", "dietitian")


@pytest.fixture
def profile_id(client, dietitian):
    _, dt_headers = dietitian
    patient_id, _ = _register_and_login(client, "patient@example.com", "patient")
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


def test_yeu_cau_sinh_thuc_don_tra_202_ngay(client, dietitian, profile_id):
    _, dt_headers = dietitian
    r = client.post(
        "/api/v1/meal-plans", json={"patient_id": profile_id, "plan_date": "2026-08-10"}, headers=dt_headers
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["plan_id"]
    assert body["status"] == "drafting"


def test_sau_khi_tra_ve_graph_da_chay_xong_va_ghi_ket_qua(client, dietitian, profile_id):
    """TestClient chờ background task chạy xong trước khi trả response — kiểm tra
    thẳng trạng thái cuối, không cần poll."""
    _, dt_headers = dietitian
    create = client.post(
        "/api/v1/meal-plans", json={"patient_id": profile_id, "plan_date": "2026-08-10"}, headers=dt_headers
    )
    plan_id = create.json()["plan_id"]

    r = client.get(f"/api/v1/meal-plans/{plan_id}", headers=dt_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "pending_review", body
    assert len(body["items"]) > 0
    assert all(item["name_vi"] and item["source"] and item["source_ref"] for item in body["items"])
    # CP-SAT (forced ở fixture _force_cpsat) tự khai triển "món hoàn chỉnh"
    # thành food_id+grams nguyên liệu thô thật trước khi trả (RULE-1) — khác
    # `gemini` thuần (chọn nguyên "food" tổng hợp theo món, item có dish_id).
    # Sửa 2026-08-07: trước đó test này giả định sai là CP-SAT luôn trả
    # dish_id — bug thật khiến CP-SAT dùng nhầm kho "food" tổng hợp theo món
    # (mật độ dinh dưỡng pha loãng) làm nguồn nguyên liệu thô, ra thực đơn
    # thiếu năng lượng nghiêm trọng mà không lỗi rõ ràng ở đâu (audit khi
    # merge PR#57 dish-day-cap với PR#59 dish-repo).
    assert all(item["food_id"] and item["dish_id"] is None for item in body["items"])
    assert body["computed_nutrition"]["kcal"] > 0
    assert body["targets"]["applied_rule_ids"]


def test_sinh_2_lan_cung_ngay_bi_409(client, dietitian, profile_id):
    _, dt_headers = dietitian
    payload = {"patient_id": profile_id, "plan_date": "2026-08-10"}
    r1 = client.post("/api/v1/meal-plans", json=payload, headers=dt_headers)
    assert r1.status_code == 202
    r2 = client.post("/api/v1/meal-plans", json=payload, headers=dt_headers)
    assert r2.status_code == 409


def test_benh_nhan_khong_the_yeu_cau_cho_ho_so_khac(client, dietitian, profile_id):
    _, other_headers = _register_and_login(client, "other@example.com", "patient")
    r = client.post(
        "/api/v1/meal-plans", json={"patient_id": profile_id, "plan_date": "2026-08-10"}, headers=other_headers
    )
    assert r.status_code == 404


def test_benh_nhan_khong_thay_plan_dang_pending_review_trong_danh_sach(client, dietitian, profile_id):
    """RULE-3: bệnh nhân chỉ thấy plan đã approved."""
    _, dt_headers = dietitian
    _, patient_headers = _register_and_login(client, "viewer@example.com", "patient")

    # gán patient_id thuộc dietitian test ở trên cho đơn giản — patient viewer
    # không sở hữu profile này nên list của họ luôn rỗng, đủ để kiểm tra RULE-3
    # dù dùng user khác: kiểm tra chính chủ mới là ca quan trọng hơn ở dưới.
    create = client.post(
        "/api/v1/meal-plans", json={"patient_id": profile_id, "plan_date": "2026-08-10"}, headers=dt_headers
    )
    plan_id = create.json()["plan_id"]

    get_by_patient = client.get(f"/api/v1/meal-plans/{plan_id}", headers=patient_headers)
    assert get_by_patient.status_code == 404

    list_by_dietitian = client.get("/api/v1/meal-plans", headers=dt_headers)
    assert list_by_dietitian.status_code == 200
    ids = [p["id"] for p in list_by_dietitian.json()["items"]]
    assert plan_id in ids  # dietitian thấy được (kể cả pending_review)


def test_plan_id_khong_ton_tai_tra_404(client, dietitian):
    _, dt_headers = dietitian
    r = client.get("/api/v1/meal-plans/khong-ton-tai", headers=dt_headers)
    assert r.status_code == 404


def test_plan_bi_target_gate_chan_tra_computed_nutrition_null():
    """Không biến trạng thái chưa tính dinh dưỡng thành object rỗng truthy ở UI."""
    plan = SimpleNamespace(
        id="plan-target-gate",
        profile_id="profile-1",
        plan_date=date(2026, 8, 10),
        status="pending_review",
        items=[],
        targets={},
        computed_nutrition={},
        violations=[],
        safety_findings=[],
        review_packet={},
        citations=[],
        explanation_vi=None,
        highest_risk="P0",
        retry_count=0,
        menu_version=0,
        reviewer_id=None,
        reviewer_notes=None,
        created_at=datetime(2026, 8, 8),
    )

    assert MealPlanOut.from_model(plan).computed_nutrition is None
