"""Test hồi quy cho lỗ hổng xác thực ở `POST /api/v1/chat`.

Bug gốc (phát hiện 2026-08-08): endpoint nhận văn bản tự do và có thể gọi
Gemini ở guardrail tầng 2, nhưng chữ ký hàm là `async def chat(payload)` —
KHÔNG có `Depends` nào. Bất kỳ ai cũng gọi được và mỗi lần gọi tiêu một lượt
API key của dự án.

Test này khoá cả hai mặt: phải có token, VÀ guardrail phải tiếp tục chặn chỉ
định y khoa sau khi thêm auth (thêm auth không được vô tình bỏ qua guardrail).
"""

from __future__ import annotations


def _register_and_login(client, email, role, password="matkhau123"):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role, "full_name": "Test User"},
    )
    assert reg.status_code == 201, reg.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_chat_khong_co_token_tra_401(client) -> None:
    resp = client.post("/api/v1/chat", json={"message": "ăn phở bò được không"})

    assert resp.status_code == 401, (
        "/chat phải yêu cầu đăng nhập — endpoint này nhận văn bản tự do và tiêu API key Gemini ở guardrail tầng 2."
    )


def test_chat_token_hong_tra_401(client) -> None:
    resp = client.post(
        "/api/v1/chat",
        json={"message": "ăn phở bò được không"},
        headers={"Authorization": "Bearer khong-phai-token-that"},
    )

    assert resp.status_code == 401


def test_chat_co_token_thi_qua_duoc(client) -> None:
    headers = _register_and_login(client, "benhnhan-chat@example.com", "patient")

    resp = client.post("/api/v1/chat", json={"message": "hôm nay ăn phở bò 1 bát"}, headers=headers)

    assert resp.status_code == 200
    assert resp.json()["blocked"] is False


def test_guardrail_van_chan_sau_khi_them_auth(client) -> None:
    """Thêm auth không được làm mất tầng chặn chỉ định y khoa (R10.1)."""
    headers = _register_and_login(client, "benhnhan-chat2@example.com", "patient")

    resp = client.post(
        "/api/v1/chat",
        json={"message": "tôi muốn ngừng uống metformin, ăn gì để thay thế?"},
        headers=headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["blocked"] is True
    assert "không có chức năng tư vấn" in body["reply"] or "bác sĩ" in body["reply"]
