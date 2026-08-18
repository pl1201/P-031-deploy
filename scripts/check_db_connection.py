#!/usr/bin/env python3
"""Chẩn đoán nhanh vì sao không kết nối được Supabase (không sinh được thực đơn).

Chạy:  python scripts/check_db_connection.py

⚠️ SCRIPT NÀY CHỈ ĐỌC. Chỉ chạy `SELECT`, không ghi gì vào DB dùng chung.

Vì sao cần script này: lỗi "không kết nối được Supabase" hầu như luôn là lỗi
CẤU HÌNH PHÍA CLIENT, không phải Supabase chết. Hai cái bẫy đã gặp thật:

1. **Dùng "Direct connection"** — host `db.<ref>.supabase.co` chỉ có bản ghi
   AAAA (IPv6), KHÔNG có A (IPv4). Máy/mạng không có IPv6 (rất phổ biến ở VN)
   sẽ báo `Network is unreachable` / `connection timeout`, và Supabase KHÔNG
   ghi log nào cả vì TCP còn chưa dựng được. Phải dùng **Session pooler**.

2. **Sai region trong host pooler** — project ở `ap-northeast-1` (Tokyo).
   Dán nhầm `ap-southeast-1` vẫn resolve DNS được nhưng sai tenant, báo
   `Tenant or user not found`.

Script in ra đúng chỗ hỏng thay vì để người đọc đoán từ stack trace SQLAlchemy.
"""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPECTED_REGION = "ap-northeast-1"


def _redact(url: str) -> str:
    """Che mật khẩu trước khi in — tuyệt đối không để lộ ra log/chat."""
    parts = urlsplit(url)
    if parts.password is None:
        return url
    return url.replace(f":{parts.password}@", ":***@", 1)


def _address_families(host: str, port: int) -> list[str]:
    """Trả về ['IPv4'] / ['IPv6'] / cả hai mà host phân giải ra được."""
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SystemExit(f"❌ Không phân giải được DNS cho {host}: {exc}") from exc
    return sorted({"IPv4" if info[0] == socket.AF_INET else "IPv6" for info in infos})


def _check_host(url: str) -> None:
    """Bắt hai cái bẫy cấu hình trước khi thử kết nối thật."""
    parts = urlsplit(url)
    host, port = parts.hostname, parts.port or 5432
    if host is None:
        raise SystemExit("❌ DATABASE_URL không có hostname.")

    print(f"Host      : {host}:{port}")
    families = _address_families(host, port)
    print(f"DNS       : {', '.join(families)}")

    if ".pooler.supabase.com" not in host:
        print(
            "\n❌ Đang dùng DIRECT CONNECTION, không phải pooler.\n"
            f"   {host} chỉ có IPv6 — mạng không hỗ trợ IPv6 sẽ không kết nối được.\n"
            "   Sửa: Supabase Dashboard → Connect → chọn **Session pooler**, dạng\n"
            f"   postgresql://postgres.<ref>:<mật-khẩu>@aws-0-{EXPECTED_REGION}"
            ".pooler.supabase.com:5432/postgres"
        )
        raise SystemExit(1)

    if EXPECTED_REGION not in host:
        print(
            f"\n❌ Sai region trong host pooler: cần `{EXPECTED_REGION}` (project ở Tokyo).\n"
            "   Region sai vẫn resolve DNS nhưng sẽ báo `Tenant or user not found`."
        )
        raise SystemExit(1)

    if "IPv4" not in families:
        print("\n⚠️  Host không có IPv4 — mạng thiếu IPv6 sẽ hỏng.")

    try:
        socket.create_connection((host, port), timeout=10).close()
    except OSError as exc:
        print(
            f"\n❌ Không mở được TCP tới {host}:{port} — {type(exc).__name__}: {exc}\n"
            "   Nguyên nhân thường gặp: firewall/proxy công ty chặn cổng 5432,\n"
            "   hoặc mạng đang dùng chặn outbound Postgres. Thử mạng khác (4G) để loại trừ."
        )
        raise SystemExit(1) from exc
    print("TCP       : OK")


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("❌ Chưa có DATABASE_URL (kiểm tra file .env ở gốc repo).")

    print(f"DATABASE_URL: {_redact(url)}\n")

    if url.startswith("sqlite"):
        print("ℹ️  Đang trỏ SQLite cục bộ, không phải Supabase — đây có thể chính là lý do")
        print("   dữ liệu món ăn trống và generator không sinh được thực đơn.")
        return 1

    _check_host(url)

    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError

    engine = create_engine(url, connect_args={"connect_timeout": 10})
    try:
        with engine.connect() as conn:
            print("Auth      : OK")
            print(f"alembic   : {conn.execute(text('select version_num from alembic_version')).scalar()}")
            foods = conn.execute(text("select count(*) from food_items")).scalar()
            dishes = conn.execute(text("select count(*) from dishes")).scalar()
            print(f"food_items: {foods}")
            print(f"dishes    : {dishes}")
    except OperationalError as exc:
        message = str(exc.orig) if exc.orig else str(exc)
        print(f"\n❌ Kết nối/xác thực thất bại: {message.strip()}")
        if "Tenant or user not found" in message:
            print("   → Sai username hoặc sai region. Username pooler phải là `postgres.<project-ref>`.")
        elif "password authentication failed" in message:
            print("   → Sai mật khẩu, hoặc mật khẩu có ký tự đặc biệt chưa URL-encode (@ : / ? # &).")
        return 1

    print("\n✅ Kết nối Supabase bình thường.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
