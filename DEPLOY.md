# Hướng dẫn Deploy — NutriCare Agent

Tài liệu này hướng dẫn từng bước deploy hệ thống lên Cloud:
- **Backend (API FastAPI):** Render.com (Docker)
- **Database (Postgres + pgvector):** Neon.tech
- **Frontend (Next.js App Router):** Vercel.com

---

## 🟢 PHẦN 1: Deploy Database lên Neon.tech (2 phút)

1. Truy cập [Neon.tech](https://neon.tech) và tạo tài khoản miễn phí.
2. Tạo project mới đặt tên: `nutricare-db`.
3. Sau khi tạo xong, copy chuỗi **Connection String** (dạng Postgres URL), ví dụ:
   ```
   postgresql://alex:Abc123xyz@ep-cool-name-123456.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
4. Lưu chuỗi này lại để dùng ở Phần 2.

---

## 🔵 PHẦN 2: Deploy Backend lên Render.com (5 phút)

1. Push toàn bộ code dự án lên GitHub của bạn.
2. Truy cập [Render.com](https://render.com) -> chọn **New +** -> **Blueprint**.
3. Kết nối với repo GitHub `P-031`. Render sẽ tự đọc file `render.yaml`.
4. Điền các biến môi trường (Environment Variables) trên Render:
   - `DATABASE_URL`: dán chuỗi Connection String ở **Phần 1**.
   - `GEMINI_API_KEY`: API Key của Google Gemini.
   - `JWT_SECRET`: Nhập 1 chuỗi ngẫu nhiên dài 32+ ký tự (VD: `my-super-secret-jwt-key-nutricare-2026`).
   - `CORS_ORIGINS`: `https://nutricare-agent.vercel.app,http://localhost:3000` (sửa lại theo domain Vercel ở Phần 3).
5. Bấm **Deploy**. Render sẽ tự build Dockerfile và chạy service.
6. Sau khi Render deploy xong, lấy URL backend (VD: `https://nutricare-agent-api.onrender.com`).
7. **Khởi tạo dữ liệu trên DB thật (chạy 1 lần duy nhất trên máy bạn):**
   Thay `DATABASE_URL` trong file `.env` bằng URL Neon ở Phần 1, sau đó chạy:
   ```powershell
   .venv\Scripts\python -m scripts.seed_db; .venv\Scripts\python -m scripts.seed_demo_users
   ```

---

## ⚡ PHẦN 3: Deploy Frontend Next.js lên Vercel.com

Có 2 cách đơn giản để đẩy lên Vercel:

### Cách A: Deploy qua Vercel CLI (Dòng lệnh — Nhanh nhất)

1. Cài đặt Vercel CLI nếu chưa có:
   ```powershell
   npm install -g vercel
   ```
2. Di chuyển vào thư mục `web-next`:
   ```powershell
   cd web-next
   ```
3. Chạy lệnh deploy:
   ```powershell
   vercel
   ```
   * Trả lời `Y` để xác nhận deploy.
   * Chọn account và project name.
   * Thư mục code chọn `./`.
4. Thiết lập biến môi trường API URL trên Vercel:
   ```powershell
   vercel env add NEXT_PUBLIC_API_BASE_URL
   ```
   * Nhập value: `https://nutricare-agent-api.onrender.com/api/v1` (URL backend Render ở Phần 2).
   * Chọn áp dụng cho: `Production`, `Preview`, `Development`.
5. Đẩy bản Production chính thức:
   ```powershell
   vercel --prod
   ```

---

### Cách B: Deploy qua Vercel Dashboard (Giao diện web)

1. Đăng nhập vào [Vercel.com](https://vercel.com).
2. Bấm **Add New...** -> **Project**.
3. Import repository GitHub `P-031`.
4. Trong phần cấu hình Project:
   - **Root Directory:** Bấm Edit -> Chọn thư mục `web-next`.
   - **Framework Preset:** Next.js (tự động nhận diện).
   - **Environment Variables:**
     - Key: `NEXT_PUBLIC_API_BASE_URL`
     - Value: `https://nutricare-agent-api.onrender.com/api/v1` (URL backend Render ở Phần 2).
5. Bấm **Deploy**. Vercel sẽ tự build và cấp đường link domain miễn phí (VD: `https://web-next-five.vercel.app`).
