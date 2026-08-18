# SET-05 — Hướng dẫn tạo Supabase project (hosting Postgres/pgvector)

> Theo ADR-008 (`docs/ARCHITECTURE.md`): Supabase chỉ dùng làm **Postgres hosted thuần**.
> Alembic vẫn là công cụ ghi schema duy nhất — KHÔNG dùng Supabase CLI migrations,
> KHÔNG dùng Auth/RLS của Supabase.

## Các bước (người có quyền tạo project thực hiện)

1. Đăng nhập https://supabase.com, **New project**.
   - Database password: đặt mạnh, lưu vào password manager của team (không đưa vào chat/git).
2. Đợi project khởi tạo xong → **Connect** → chọn **Session pooler**.

   > 🔴 **BẮT BUỘC dùng Session pooler, KHÔNG dùng "Direct connection".**
   > Host direct `db.<project-ref>.supabase.co` chỉ có bản ghi **AAAA (IPv6)**, không có
   > A (IPv4). Máy/mạng không có IPv6 — rất phổ biến ở VN — sẽ báo `Network is unreachable`
   > hoặc timeout, và **Supabase không ghi log gì cả** vì TCP còn chưa dựng được, nên rất
   > dễ tưởng nhầm là "Supabase chết". Host pooler có IPv4 nên chạy được ở mọi mạng.

3. Bật extension `vector`: **Database → Extensions** → tìm `pgvector` → Enable.
4. Copy connection string, dạng:
   ```
   postgresql://postgres.[project-ref]:[password]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
   ```
   - Project hiện tại của đội ở region **`ap-northeast-1`** (Tokyo). Dán nhầm region khác
     (`ap-southeast-1`…) vẫn resolve được DNS nhưng sai tenant → `Tenant or user not found`.
   - Username pooler là `postgres.<project-ref>`, **không phải** `postgres` trần.
   - Mật khẩu có ký tự đặc biệt (`@ : / ? # &`) phải URL-encode, nếu không URL bị parse sai.
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

## Khi "không kết nối được Supabase / không sinh được thực đơn"

Chạy trước tiên, đừng đoán từ stack trace:

```bash
python scripts/check_db_connection.py
```

Script chỉ đọc, in ra đúng tầng nào hỏng (DNS → TCP → auth → dữ liệu). Ba nguyên nhân
đã gặp thật, xếp theo tần suất:

| Triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|
| `Network is unreachable`, timeout, **không có log nào trên Supabase Dashboard** | `DATABASE_URL` trỏ `db.<ref>.supabase.co` (IPv6-only) | Đổi sang Session pooler (bước 2 ở trên) |
| `Tenant or user not found` | Sai region trong host, hoặc username là `postgres` thay vì `postgres.<ref>` | Copy lại đúng chuỗi Session pooler |
| Kết nối OK nhưng `food_items = 0`, generator trả thực đơn rỗng | `.env` đang trỏ SQLite cục bộ chứ không phải Supabase | Sửa `DATABASE_URL` trong `.env` |

Trước khi nghi Supabase, kiểm tra trạng thái project trên Dashboard: nếu là `ACTIVE_HEALTHY`
và log pooler vẫn thấy `Connection authenticated` từ máy người khác thì lỗi nằm ở máy mình.

## Lưu ý Free tier

- Project tự **pause sau 7 ngày không hoạt động** — cần ping định kỳ (cron nhẹ hoặc chạy
  `alembic upgrade head` khi bắt đầu mỗi phiên làm việc) nếu muốn giữ project sống.
- Không có **branching** (PR preview DB) ở Free tier — mỗi PR vẫn test trên SQLite/CI như hiện tại.
- 500MB DB, đủ dùng cho quy mô dữ liệu hiện tại (`food_items` ~7300 dòng + seeds khác).

## Việc CẦN làm sau khi có DATABASE_URL thật (chưa làm được vì chưa có project)

- [ ] Chạy `alembic upgrade head` lên Supabase, xác nhận sạch.
- [ ] Cập nhật `.env.example` với comment trỏ về file này.
- [ ] Cập nhật `docs/TICKETS.md` SET-05: đánh dấu hoàn thành khi bước trên xong.
