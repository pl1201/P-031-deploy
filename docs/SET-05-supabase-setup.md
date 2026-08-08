# SET-05 — Hướng dẫn tạo Supabase project (hosting Postgres/pgvector)

> Theo ADR-008 (`docs/ARCHITECTURE.md`): Supabase chỉ dùng làm **Postgres hosted thuần**.
> Alembic vẫn là công cụ ghi schema duy nhất — KHÔNG dùng Supabase CLI migrations,
> KHÔNG dùng Auth/RLS của Supabase.

## Các bước (người có quyền tạo project thực hiện)

1. Đăng nhập https://supabase.com, **New project**.
   - Region: chọn gần Việt Nam nhất (Singapore).
   - Database password: đặt mạnh, lưu vào password manager của team (không đưa vào chat/git).
2. Đợi project khởi tạo xong → **Project Settings → Database → Connection string** → chọn
   **URI** (chế độ "Session pooler" hoặc "Direct connection" đều được cho Alembic).
3. Bật extension `vector`: **Database → Extensions** → tìm `pgvector` → Enable.
4. Copy connection string, dạng:
   ```
   postgresql://postgres.[project-ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```
5. Gửi connection string cho tôi qua kênh an toàn (không paste vào chat công khai) hoặc tự điền
   trực tiếp vào `.env` cục bộ:
   ```
   DATABASE_URL=postgresql://...  # connection string ở bước 4
   ```
6. Sau khi có `DATABASE_URL`, chạy:
   ```bash
   alembic upgrade head
   ```
   Xác nhận chạy sạch, không lỗi — đây là toàn bộ những gì cần để "dùng Supabase": Alembic tự
   tạo schema đúng như SQLite hiện tại, không cần thao tác gì thêm trên Supabase Studio.
7. **Không** chỉnh sửa bảng qua Supabase Studio UI trực tiếp — mọi thay đổi schema phải qua
   Alembic migration mới trong PR (CLAUDE.md §4), nếu không sẽ gây lệch schema âm thầm.

## Lưu ý Free tier

- Project tự **pause sau 7 ngày không hoạt động** — cần ping định kỳ (cron nhẹ hoặc chạy
  `alembic upgrade head` khi bắt đầu mỗi phiên làm việc) nếu muốn giữ project sống.
- Không có **branching** (PR preview DB) ở Free tier — mỗi PR vẫn test trên SQLite/CI như hiện tại.
- 500MB DB, đủ dùng cho quy mô dữ liệu hiện tại (`food_items` ~7300 dòng + seeds khác).

## Việc CẦN làm sau khi có DATABASE_URL thật (chưa làm được vì chưa có project)

- [ ] Chạy `alembic upgrade head` lên Supabase, xác nhận sạch.
- [ ] Cập nhật `.env.example` với comment trỏ về file này.
- [ ] Cập nhật `docs/TICKETS.md` SET-05: đánh dấu hoàn thành khi bước trên xong.
