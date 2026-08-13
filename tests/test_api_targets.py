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
    """ĐTĐ2 + CKD G3b — phải áp cả 2 nhóm rule, không phải chỉ 1 bệnh.

    Lịch sử field này (đọc trước khi sửa lại lần nữa): bản gốc assert thẳng
    `applied_rule_ids` có T2DM/CKD. Khi CLN-11 (PR #107) mới xong mà
    fix/CLN-11-remaining-rules (PR #109) chưa merge, 23/23 rule vẫn
    `to_verify`, nên `compute_targets_with_rule_gate()` (fail-closed theo
    DEC-021) chặn hết — bản assert tạm thời khi đó kiểm `needs_expert_review`
    + `conflict_notes` thay vì `applied_rule_ids`.

    Sau khi hợp nhất #107+#109 (2 PR sửa đúng 2 tập rule KHÔNG giao nhau:
    CKD-PRO/CKD-K/CKD-NA vs BASE/T2DM/HTN/CKD-P/GOUT), toàn bộ 23/23 rule đã
    `verified` — quay lại đúng ý định gốc của ticket: `applied_rule_ids`
    phải có rule của CẢ HAI bệnh, không bỏ sót một bệnh nào, và KHÔNG cần
    `needs_expert_review` nữa vì không còn rule chưa xác minh áp dụng được
    cho ca này.
    """
    _, dt_headers = dietitian
    r = client.post("/api/v1/targets/compute", json={"patient_id": profile_id}, headers=dt_headers)
    body = r.json()

    assert body["needs_expert_review"] is False, "không còn rule chưa xác minh — không cần chuyên gia rà lại"
    assert body["conflict_notes"] == []

    rule_ids = " ".join(body["applied_rule_ids"])
    assert "T2DM" in rule_ids, "không áp rule ĐTĐ2 — nguy cơ bỏ sót một bệnh"
    assert "CKD" in rule_ids, "không áp rule CKD — nguy cơ bỏ sót một bệnh"
    assert "CKD-PRO-01" in body["applied_rule_ids"]
    assert "T2DM-CARB-01" in body["applied_rule_ids"]


def test_patient_id_khong_ton_tai_tra_404(client, dietitian):
    _, dt_headers = dietitian
    r = client.post("/api/v1/targets/compute", json={"patient_id": "khong-ton-tai"}, headers=dt_headers)
    assert r.status_code == 404


def test_benh_nhan_khac_khong_tinh_duoc_dinh_muc_ho_so_nguoi_khac(client, dietitian, profile_id):
    _, other_headers = _register_and_login(client, "other-patient@example.com", "patient")
    r = client.post("/api/v1/targets/compute", json={"patient_id": profile_id}, headers=other_headers)
    assert r.status_code == 404
