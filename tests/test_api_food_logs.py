"""BE-07: API nhật ký ăn uống + hàng chờ giải quyết OOV.

Bộ test này khoá lại lời hứa cốt lõi của sản phẩm: **thà nói không biết còn hơn
đoán**. Nếu ai đó "cho tiện" mà cộng món chưa tra được thành 0, hoặc để API trả
về kết luận "đạt ngưỡng" khi dữ liệu còn khuyết, các test dưới đây phải đỏ.
"""

from __future__ import annotations

import pytest


def _register_and_login(client, email, role, password="matkhau123"):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role, "full_name": "Test User"},
    )
    user_id = reg.json()["user_id"]
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return user_id, {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def dietitian(client):
    return _register_and_login(client, "dt_fl@example.com", "dietitian")


@pytest.fixture
def patient(client):
    return _register_and_login(client, "bn_fl@example.com", "patient")


@pytest.fixture
def profile_id(client, dietitian, patient):
    _, dt_headers = dietitian
    patient_user_id, _ = patient
    r = client.post(
        "/api/v1/patients",
        json={
            "user_id": patient_user_id,
            "age": 58,
            "sex": "male",
            "height_cm": 165,
            "weight_kg": 65,
            "activity_level": "light",
            "conditions": [{"code": "T2DM", "stage": None}],
            "region": "north",
        },
        headers=dt_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --- Ghi nhật ký -----------------------------------------------------------


def test_ghi_mon_tra_duoc_thi_tu_khop(client, patient, profile_id):
    _, headers = patient
    r = client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "Cà rốt", "grams": 100},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["match_status"] == "auto"
    assert body["food_id"] is not None
    assert body["food_name_vi"] is not None


def test_ghi_mon_la_thi_giu_nguyen_chu_nguoi_dung_go(client, patient, profile_id):
    """Món OOV: không đoán, không bắt bệnh nhân tự tra CSDL."""
    _, headers = patient
    r = client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "canh rau tập tàng bà Bảy", "grams": 200},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["match_status"] == "unmatched"
    assert body["food_id"] is None
    assert body["grams"] is None, "Không được giữ gram cho món chưa biết là gì"
    assert body["free_text_vi"] == "canh rau tập tàng bà Bảy"


def test_biet_mon_nhung_khong_ro_khau_phan_van_la_chua_du_du_lieu(client, patient, profile_id):
    """PRD FR-11: biết ăn gì mà không biết bao nhiêu thì không cộng được."""
    _, headers = patient
    r = client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "Cà rốt"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["match_status"] == "unmatched"


def test_ten_chung_khong_tu_chon_hang_cu_the_ma_goi_y_cho_nguoi_chon(client, patient, profile_id):
    """'thịt bò' chung chung: máy gợi ý, KHÔNG tự quyết cắt nào (quyết định lâm sàng)."""
    _, headers = patient
    r = client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "thịt bò", "grams": 100},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["match_status"] == "unmatched"
    assert len(body["suggestions"]) > 0, "Phải đưa ứng viên cho người chọn"


# --- Test vàng: không bịa số ----------------------------------------------


def test_mon_chua_tra_duoc_khong_bao_gio_thanh_so_0(client, patient, profile_id):
    """Test quan trọng nhất: OOV không được cộng vào tổng, và KHÔNG được kết luận 'đạt'."""
    _, headers = patient
    client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "Cà rốt", "grams": 100},
        headers=headers,
    )
    client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "canh rau tập tàng bà Bảy"},
        headers=headers,
    )

    r = client.get(f"/api/v1/food-logs/summary?profile_id={profile_id}", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["unmatched_count"] == 1
    assert body["coverage"] < 1.0
    assert body["is_complete"] is False

    kinds = {v["kind"] for v in body["violations"]}
    assert "unmatched_food" in kinds

    oov = next(v for v in body["violations"] if v["kind"] == "unmatched_food")
    assert oov["actual"] is None and oov["limit"] is None, (
        "Cảnh báo OOV không có con số — để None, tuyệt đối không nhồi 0"
    )

    # Không chất nào được kết luận "đạt" khi còn món chưa tra.
    assert "within" not in {v["verdict"] for v in body["verdicts"]}


def test_thieu_du_lieu_thi_khong_ket_luan_dat_nhung_van_bao_duoc_vuot(client, patient, profile_id):
    """Bất đối xứng kết luận: cận dưới đã vượt trần thì vẫn kết luận được."""
    _, headers = patient
    # Nước mắm rất mặn — đủ để vượt trần natri ngay cả khi còn món chưa tra.
    client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "Nước mắm", "grams": 100},
        headers=headers,
    )
    client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "món lạ chưa có tên"},
        headers=headers,
    )

    body = client.get(f"/api/v1/food-logs/summary?profile_id={profile_id}", headers=headers).json()
    na = next(v for v in body["verdicts"] if v["nutrient"] == "na_mg")
    assert na["verdict"] == "exceeded", f"Phải kết luận vượt natri, nhận {na}"


def test_nhat_ky_rong_khong_no(client, patient, profile_id):
    _, headers = patient
    body = client.get(f"/api/v1/food-logs/summary?profile_id={profile_id}", headers=headers).json()
    assert body["matched_count"] == 0
    assert body["coverage"] == 0.0
    assert {v["verdict"] for v in body["verdicts"]} == {"insufficient_data"}


# --- Chuyên gia giải quyết -------------------------------------------------


def test_chuyen_gia_gan_mon_thi_duoc_tinh_vao_tong(client, patient, dietitian, profile_id):
    _, p_headers = patient
    _, dt_headers = dietitian

    client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "canh rau tập tàng"},
        headers=p_headers,
    )
    unresolved = client.get("/api/v1/food-logs/unresolved", headers=dt_headers).json()
    assert len(unresolved) == 1
    log_id = unresolved[0]["id"]

    # Chuyên gia chọn một food_id thật.
    logs = client.get(f"/api/v1/food-logs?profile_id={profile_id}", headers=dt_headers).json()
    assert logs

    r = client.post(
        f"/api/v1/food-logs/{log_id}/resolve",
        json={"action": "map_to_existing", "food_id": 1, "grams": 150},
        headers=dt_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["match_status"] == "expert"

    body = client.get(f"/api/v1/food-logs/summary?profile_id={profile_id}", headers=p_headers).json()
    assert body["is_complete"] is True
    assert body["unmatched_count"] == 0


def test_chuyen_gia_duoc_phep_noi_khong_du_du_lieu(client, patient, dietitian, profile_id):
    """`mark_no_data` là lựa chọn HỢP LỆ — đúng DEC-008, không phải đường cùng."""
    _, p_headers = patient
    _, dt_headers = dietitian
    client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "món bà ngoại nấu"},
        headers=p_headers,
    )
    log_id = client.get("/api/v1/food-logs/unresolved", headers=dt_headers).json()[0]["id"]

    r = client.post(
        f"/api/v1/food-logs/{log_id}/resolve",
        json={"action": "mark_no_data", "note_vi": "không đủ thông tin để tra"},
        headers=dt_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["match_status"] == "no_data"

    # Vẫn KHÔNG được tính vào tổng, và ngày vẫn là "chưa đủ dữ liệu".
    body = client.get(f"/api/v1/food-logs/summary?profile_id={profile_id}", headers=p_headers).json()
    assert body["is_complete"] is False


def test_khong_tin_food_id_client_gui(client, patient, dietitian, profile_id):
    _, p_headers = patient
    _, dt_headers = dietitian
    client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "món lạ"},
        headers=p_headers,
    )
    log_id = client.get("/api/v1/food-logs/unresolved", headers=dt_headers).json()[0]["id"]

    r = client.post(
        f"/api/v1/food-logs/{log_id}/resolve",
        json={"action": "map_to_existing", "food_id": 999999, "grams": 100},
        headers=dt_headers,
    )
    assert r.status_code == 422


def test_gan_mon_ma_thieu_gram_thi_bi_tu_choi(client, patient, dietitian, profile_id):
    _, p_headers = patient
    _, dt_headers = dietitian
    client.post(
        "/api/v1/food-logs",
        json={"profile_id": profile_id, "free_text_vi": "món lạ"},
        headers=p_headers,
    )
    log_id = client.get("/api/v1/food-logs/unresolved", headers=dt_headers).json()[0]["id"]

    r = client.post(
        f"/api/v1/food-logs/{log_id}/resolve",
        json={"action": "map_to_existing", "food_id": 1},
        headers=dt_headers,
    )
    assert r.status_code == 422, "Không có gram thì không tính vào tổng được"


# --- Phân quyền ------------------------------------------------------------


def test_benh_nhan_khong_doc_duoc_nhat_ky_nguoi_khac(client, dietitian, profile_id):
    """404 chứ không phải 403 — 403 sẽ xác nhận hồ sơ đó tồn tại."""
    _, other_headers = _register_and_login(client, "bn_khac@example.com", "patient")
    r = client.get(f"/api/v1/food-logs?profile_id={profile_id}", headers=other_headers)
    assert r.status_code == 404


def test_benh_nhan_khong_vao_duoc_hang_cho_giai_quyet(client, patient):
    _, headers = patient
    assert client.get("/api/v1/food-logs/unresolved", headers=headers).status_code == 403


def test_khong_token_thi_401(client, profile_id):
    assert client.get(f"/api/v1/food-logs?profile_id={profile_id}").status_code == 401
    assert client.post("/api/v1/food-logs", json={"profile_id": profile_id, "free_text_vi": "x"}).status_code == 401
