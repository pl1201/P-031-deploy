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


def test_da_benh_ly_phat_hien_ca_hai_nhom_rule_nhung_gate_chan_vi_chua_verified(client, dietitian, profile_id):
    """ĐTĐ2 + CKD G3b — phải phát hiện rule của CẢ HAI bệnh, không bỏ sót một bệnh.

    Ý định gốc của ticket giữ nguyên. Chỗ đổi là hợp đồng phía trên nó:
    `/targets/compute` đi qua `compute_targets_with_rule_gate()`, và hàm này
    tính định mức bằng `load_rules(verified_only=True)` — fail-closed theo
    DEC-021. Toàn bộ 23 rule trong seed hiện còn `verify_status=to_verify`
    (R2 chưa ký), nên `applied_rule_ids` CHỈ có rule năng lượng tính trong
    code; không rule lâm sàng nào từ CSV được áp.

    Vì vậy test khẳng định đúng thứ gate phải bảo đảm, thay vì khẳng định
    một hành vi mà thiết kế an toàn cố ý không cho phép:
      1. Không im lặng bỏ qua — hồ sơ bị gắn `needs_expert_review`.
      2. Rule của CẢ HAI bệnh phải xuất hiện trong danh sách chưa xác minh
         (đây là phần bắt "bỏ sót một bệnh" của ticket gốc).

    Khi R2 ký `verify_status=verified` cho tập rule T2DM/CKD, test này sẽ đỏ
    và PHẢI được sửa lại thành khẳng định `applied_rule_ids` có cả hai nhóm —
    đó là tín hiệu đúng, không phải hồi quy.
    """
    _, dt_headers = dietitian
    r = client.post("/api/v1/targets/compute", json={"patient_id": profile_id}, headers=dt_headers)
    body = r.json()

    assert body["needs_expert_review"] is True, "gate không được im lặng thả qua khi rule chưa xác minh"

    notes = " ".join(body["conflict_notes"])
    assert "T2DM" in notes, "không phát hiện rule ĐTĐ2 — nguy cơ bỏ sót một bệnh"
    assert "CKD" in notes, "không phát hiện rule CKD — nguy cơ bỏ sót một bệnh"


def test_patient_id_khong_ton_tai_tra_404(client, dietitian):
    _, dt_headers = dietitian
    r = client.post("/api/v1/targets/compute", json={"patient_id": "khong-ton-tai"}, headers=dt_headers)
    assert r.status_code == 404


def test_benh_nhan_khac_khong_tinh_duoc_dinh_muc_ho_so_nguoi_khac(client, dietitian, profile_id):
    _, other_headers = _register_and_login(client, "other-patient@example.com", "patient")
    r = client.post("/api/v1/targets/compute", json={"patient_id": profile_id}, headers=other_headers)
    assert r.status_code == 404
