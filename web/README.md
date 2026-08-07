# NutriCare web MVP

Prototype UI thuần HTML/CSS/JavaScript, chỉ dùng mock data và chưa gọi backend.

## Chạy local

Mở `index.html` trực tiếp, hoặc từ thư mục gốc chạy:

```powershell
python -m http.server 5173 --directory web
```

Sau đó truy cập `http://localhost:5173`.

## Luồng tương tác

1. Chọn một trong ba hồ sơ mô phỏng.
2. Xem chỉ số lâm sàng và mục tiêu dinh dưỡng.
3. Nhấn **Sinh lại** để mô phỏng agent tạo phương án mới.
4. Nhấn **Duyệt thực đơn** để mở hộp thoại xác nhận.

Các mock data trong `app.js` được tách khỏi markup để có thể thay bằng API client sau này.
