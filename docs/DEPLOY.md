# DEPLOY — Nối backend (Render) với frontend (Vercel)

> Ticket: DAT-25 · Owner: R1/R3 (hạ tầng) + R2 (dữ liệu)

---

## Vì sao có tài liệu này

Ngày 2026-08-09, R2 chụp màn hình trang "Thực đơn của tôi" trên bản deploy và thấy tên món sai. Điều tra ra hai chuyện tách biệt:

1. Dữ liệu có mẫu `MENU-*` lọt vào thực đơn — đã sửa (DAT-25, DEVLOG DEC-022).
2. **Backend và frontend chưa thật sự nối với nhau.** Trang trên Vercel gọi về `http://localhost:8000` trên máy người dùng, không gọi Render. Nghĩa là bản "deploy" đang chạy backend cũ trên máy cá nhân — code mới merge vào `main` không có tác dụng gì trên đó.

Điểm 2 nguy hiểm hơn điểm 1 vì nó âm thầm: mọi bản vá backend sẽ trông như "đã deploy" mà thực tế không tới người dùng.

---

## Cách nhận ra vấn đề đang xảy ra

| Triệu chứng | Nguyên nhân |
|---|---|
| Trang tải được, có dữ liệu, nhưng **không phản ánh code mới nhất** | Frontend đang gọi `localhost:8000` — backend cũ trên máy cá nhân |
| Trang trắng / "Failed to fetch" khi mở từ máy khác | Frontend gọi `localhost` nhưng máy đó không chạy backend |
| Console báo lỗi CORS | Domain Vercel chưa có trong `CORS_ORIGINS` của Render |

**Cách kiểm tra nhanh:** mở DevTools → tab Network trên trang Vercel, xem request đi tới host nào. Nếu là `localhost` thì chưa nối.

---

## Biến môi trường cần đặt

Cả hai đều đặt **trên dashboard**, không nằm trong repo (`render.yaml` khai báo `sync: false` cho các biến bí mật, nghĩa là giá trị phải nhập tay trên Render).

### Vercel — Project Settings → Environment Variables

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://<tên-service>.onrender.com/api/v1` | **Bắt buộc.** Không đặt thì mặc định về `http://localhost:8000/api/v1` (xem `web-next/src/lib/api.ts`) — đây chính là lỗi đang gặp. |

Tiền tố `NEXT_PUBLIC_` là bắt buộc để Next.js nhúng biến vào bundle chạy ở trình duyệt. Sau khi đặt phải **redeploy** — Next.js nhúng giá trị lúc build, không đọc lúc chạy.

### Render — Service → Environment

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `CORS_ORIGINS` | `https://<dự-án>.vercel.app` | **Bắt buộc.** Nhiều domain thì ngăn bằng dấu phẩy. |
| `DATABASE_URL` | chuỗi kết nối Supabase | Dùng chung với dev hiện tại |
| `OPENAI_API_KEY`, `LANGCHAIN_API_KEY` | khoá thật | |

**Về `CORS_ORIGINS`:** phải là **origin**, không phải URL đầy đủ — `https://abc.vercel.app`, không có dấu `/` ở cuối, không có đường dẫn. Khoảng trắng sau dấu phẩy được tự cắt (`src/main.py`), nhưng dấu `/` thừa thì không — trình duyệt so khớp origin theo chuỗi chính xác.

**Về preview deployment của Vercel:** mỗi nhánh sinh một domain riêng (`<dự-án>-<hash>.vercel.app`) và sẽ **không** khớp `CORS_ORIGINS` của production. Nếu cần test preview, thêm domain đó vào danh sách hoặc dùng domain cố định của Vercel.

---

## Kiểm tra sau khi đặt

```bash
# 1. Backend sống
curl https://<tên-service>.onrender.com/health

# 2. CORS cho đúng domain Vercel (phải thấy access-control-allow-origin)
curl -I -H "Origin: https://<dự-án>.vercel.app" \
  https://<tên-service>.onrender.com/api/v1/health
```

3. Mở trang Vercel → DevTools → Network → xác nhận request đi tới `onrender.com`, **không phải** `localhost`.

---

## Lưu ý gói free của Render

Service ở gói `free` (`render.yaml`) **ngủ sau ~15 phút không có request**. Lần gọi đầu sau khi ngủ mất 30–60 giây để dậy — dễ bị hiểu nhầm là backend chết hoặc frontend hỏng. Nếu cần demo, gọi `/health` trước vài phút để đánh thức.
