"""BE test cho P1: /targets/{id}/explain và /targets/{id}/what-if.

`parse_what_if` gọi Gemini thật — mock lại để test chạy không cần API key và
không tốn quota. Trọng tâm: what-if không có side-effect lên DB, và phân
quyền đúng (bệnh nhân không gọi được).
"""

from __future__ import annotations

import pytest

from src.services import target_assistant


def _register_and_login(client, email, role, password="matkhau123"):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role, "full_name": "Test User"},
    )
    assert reg.status_code == 201, reg.text
    user_id = reg.json()["user_id"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return user_id, {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def dietitian(client):
    return _register_and_login(client, "dt_ta@example.com", "dietitian")


@pytest.fixture
def patient(client):
    return _register_and_login(client, "bn_ta@example.com", "patient")


@pytest.fixture
def profile_id(client, dietitian, patient):
    _, dt_headers = dietitian
    patient_user_id, _ = patient
    r = client.post(
        "/api/v1/patients",
        json={
            "user_id": patient_user_id,
            "age": 60,
            "sex": "male",
            "height_cm": 165,
            "weight_kg": 65,
            "activity_level": "light",
            "conditions": [{"code": "CKD", "stage": "G3b"}],
            "region": "north",
        },
        headers=dt_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --- /explain ----------------------------------------------------------------


def test_explain_tra_dung_rule_thang(client, dietitian, profile_id):
    _, headers = dietitian
    r = client.get(f"/api/v1/targets/{profile_id}/explain", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()

    protein = next(e for e in body if e["nutrient"] == "protein_g")
    applied_ids = {a["rule_id"] for a in protein["applied"]}
    assert applied_ids & {"CKD-PRO-01", "CKD-PRO-02", "CKD-PRO-05"}


def test_explain_benh_nhan_khong_goi_duoc(client, patient, profile_id):
    _, headers = patient
    r = client.get(f"/api/v1/targets/{profile_id}/explain", headers=headers)
    assert r.status_code == 403


def test_explain_khong_token_thi_401(client, profile_id):
    assert client.get(f"/api/v1/targets/{profile_id}/explain").status_code == 401


def test_explain_ho_so_khong_ton_tai_404(client, dietitian):
    _, headers = dietitian
    r = client.get("/api/v1/targets/khong-ton-tai/explain", headers=headers)
    assert r.status_code == 404


# --- /what-if ------------------------------------------------------------


def test_what_if_khong_sinh_so_ngoai_compute_targets(client, dietitian, profile_id, monkeypatch):
    """LLM chỉ trả delta, mọi số trong response phải khớp compute_targets() thật."""

    def _fake_parse(question_vi, *, settings=None):
        return target_assistant.ProfileDelta(condition_code=None, stage=None, flags=[])

    monkeypatch.setattr(target_assistant, "parse_what_if", _fake_parse)
    monkeypatch.setattr("src.api.routes.targets.parse_what_if", _fake_parse)

    _, headers = dietitian
    r = client.post(
        f"/api/v1/targets/{profile_id}/what-if",
        json={"question_vi": "không đổi gì cả"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()

    # delta rỗng -> before/after phải giống hệt nhau, không chất nào "changed".
    assert body["changed_nutrients"] == []
    assert body["explanations_before"] == body["explanations_after"]


def test_what_if_ckd_nang_len_thi_doi_ngưỡng(client, dietitian, profile_id, monkeypatch):
    def _fake_parse(question_vi, *, settings=None):
        return target_assistant.ProfileDelta(condition_code="CKD", stage="G4", flags=[])

    monkeypatch.setattr("src.api.routes.targets.parse_what_if", _fake_parse)

    _, headers = dietitian
    r = client.post(
        f"/api/v1/targets/{profile_id}/what-if",
        json={"question_vi": "nếu CKD sang G4 thì sao"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["changed_nutrients"], "G3b -> G4 phải làm ít nhất 1 ngưỡng đổi"
    assert body["delta"]["stage"] == "G4"


def test_what_if_khong_sua_ho_so_that_trong_db(client, dietitian, profile_id, monkeypatch):
    """Side-effect duy nhất được phép là AuditLog — profile trong DB không đổi."""

    def _fake_parse(question_vi, *, settings=None):
        return target_assistant.ProfileDelta(condition_code="CKD", stage="G5", flags=[])

    monkeypatch.setattr("src.api.routes.targets.parse_what_if", _fake_parse)

    _, headers = dietitian
    client.post(
        f"/api/v1/targets/{profile_id}/what-if",
        json={"question_vi": "nếu CKD sang G5 thì sao"},
        headers=headers,
    )

    r = client.get(f"/api/v1/patients/{profile_id}", headers=headers)
    assert r.status_code == 200
    ckd = next(c for c in r.json()["conditions"] if c["code"] == "CKD")
    assert ckd["stage"] == "G3b", "Hồ sơ thật trong DB không được đổi sau what-if"


def test_what_if_benh_nhan_khong_goi_duoc(client, patient, profile_id):
    _, headers = patient
    r = client.post(
        f"/api/v1/targets/{profile_id}/what-if",
        json={"question_vi": "test"},
        headers=headers,
    )
    assert r.status_code == 403
