"""BE-02: đăng ký / đăng nhập / refresh token."""

from __future__ import annotations


def _register(client, email="user@example.com", password="matkhau123", role="patient"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role, "full_name": "Nguyễn Văn A"},
    )


def test_dang_ky_thanh_cong(client):
    r = _register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "user@example.com"
    assert body["role"] == "patient"
    assert "user_id" in body


def test_dang_ky_email_trung_bi_tu_choi(client):
    _register(client)
    r2 = _register(client)
    assert r2.status_code == 409


def test_dang_ky_mat_khau_yeu_bi_tu_choi(client):
    r = _register(client, password="short")
    assert r.status_code == 422


def test_dang_ky_role_khong_hop_le_bi_tu_choi(client):
    r = _register(client, role="admin")
    assert r.status_code == 422


def test_dang_ky_cong_khai_voi_role_dietitian_phuc_vu_demo(client):
    r = _register(client, role="dietitian")
    assert r.status_code == 201
    assert r.json()["role"] == "dietitian"


def test_dang_nhap_thanh_cong_tra_ca_2_token(client):
    _register(client)
    r = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "matkhau123"})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_dang_nhap_sai_mat_khau_tra_401(client):
    _register(client)
    r = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "sai-mat-khau"})
    assert r.status_code == 401


def test_dang_nhap_email_khong_ton_tai_tra_401_khong_lo_thong_tin(client):
    """Thông báo lỗi phải GIỐNG HỆT trường hợp sai mật khẩu — chống user-enumeration."""
    _register(client)
    login_wrong_pw = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "sai-mat-khau"})
    login_no_such_email = client.post(
        "/api/v1/auth/login", json={"email": "khong-ton-tai@example.com", "password": "bat-ky"}
    )
    assert login_no_such_email.status_code == 401
    assert login_wrong_pw.json()["detail"] == login_no_such_email.json()["detail"]


def test_refresh_token_cap_access_token_moi(client):
    _register(client)
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "matkhau123"})
    refresh_token = login.json()["refresh_token"]

    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_refresh_bang_access_token_bi_tu_choi(client):
    """Không được dùng access token thay refresh token — kiểm tra `type` claim."""
    _register(client)
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "matkhau123"})
    access_token = login.json()["access_token"]

    r = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert r.status_code == 401


def test_goi_route_can_dang_nhap_khong_co_token_tra_401(client):
    r = client.get("/api/v1/patients/khong-quan-trong")
    assert r.status_code == 401
