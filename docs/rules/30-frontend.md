# RULE 30 — FRONTEND

> Owner: **R4** · Stack: Next.js (App Router) + TailwindCSS + shadcn/ui + Recharts

---

## R30.1 — Hai portal, hai trải nghiệm

Bệnh nhân và chuyên gia dùng chung codebase nhưng **không dùng chung layout**. Bệnh nhân thấy giao diện đơn giản, chữ to, ít số liệu kỹ thuật. Chuyên gia thấy dashboard mật độ thông tin cao, thao tác nhanh bằng phím.

## R30.2 — Con số phải bấm được để xem nguồn

Mọi giá trị dinh dưỡng hiển thị đều có thể bấm/hover để hiện: tên thực phẩm, khối lượng, nguồn, tham chiếu. Đây là tính năng bán hàng chính của sản phẩm — đừng giấu nó trong tooltip mờ nhạt.

## R30.3 — Phân cấp cảnh báo bằng thị giác

| Mức | Màu | Hành vi |
|---|---|---|
| `high` (dị ứng, tương tác thuốc nặng, vượt ngưỡng cứng) | Đỏ | Banner trên cùng, không thể bỏ qua, không tự ẩn |
| `moderate` | Cam | Badge cạnh món liên quan |
| `low` / gợi ý | Xanh dương | Text phụ |
| Ước tính (`is_estimated`) | Xám + icon | Nhãn "ước tính" cạnh con số |

Không bao giờ để cảnh báo `high` nằm dưới màn hình đầu tiên.

## R30.4 — Disclaimer luôn hiện diện

Ở mọi màn hình có thực đơn + footer app. Không giấu sau nút "xem thêm". Kèm tên chuyên gia đã duyệt và thời điểm duyệt.

## R30.5 — Bệnh nhân không được thấy bản nháp

Màn hình bệnh nhân khi plan đang `pending_review` chỉ hiện trạng thái chờ, **không hiện nội dung**, kể cả một phần. Đây là ràng buộc sản phẩm, không phải chi tiết UI.

## R30.6 — Ba trạng thái cho mọi màn hình

Loading (skeleton, không phải spinner toàn trang), Empty (có hướng dẫn hành động tiếp theo), Error (có thông điệp rõ và nút thử lại). Màn hình trắng là bug.

## R30.7 — Tốc độ ghi nhật ký

Ghi 1 bữa ăn phải xong trong ≤ 20 giây và ≤ 4 lần chạm. Tìm kiếm có gợi ý, món hay ăn hiện lên trước, có nút lặp lại bữa hôm qua.

## R30.8 — Dashboard chuyên gia tối ưu cho tốc độ

Mục tiêu: duyệt 1 thực đơn ≤ 2 phút. Nghĩa là: xem được toàn bộ thông tin quan trọng không cần cuộn, sửa gram tại chỗ (không mở modal), phím tắt cho Duyệt/Từ chối, và tổng dinh dưỡng cập nhật tức thì khi sửa.

## R30.9 — Không gọi LLM từ frontend

Mọi thứ đi qua backend. Không đặt API key LLM trong biến `NEXT_PUBLIC_*`.

## R30.10 — Không lưu PHI ở localStorage

Chỉ lưu token. Dữ liệu bệnh nhân lấy theo phiên, không cache dài hạn ở trình duyệt.

## R30.11 — Kỹ thuật

- TypeScript strict, không `any`
- Server Component mặc định; `"use client"` chỉ khi cần
- Gọi API qua một client tập trung có xử lý lỗi và refresh token
- Tailwind theo design token, tránh magic number
- Component > 200 dòng thì tách

## R30.12 — Accessibility & Dark mode

Tương phản WCAG AA, focus visible, nhãn cho mọi input, điều hướng được bằng bàn phím. Dark mode cho toàn app (BTC chấm mục UI/UX).

## R30.13 — Chụp màn hình khi làm xong mỗi màn hình

Lưu vào `docs/screenshots/`. Cuối kỳ cần cho README, pitch deck và video — đừng đợi tuần 6 mới đi chụp lại.

## R30.14 — Ngôn ngữ

Toàn bộ giao diện tiếng Việt. Thuật ngữ y khoa dùng từ phổ thông kèm chú thích (VD: "Natri (muối)"). Bệnh nhân mãn tính ở Việt Nam phần lớn là người lớn tuổi — cỡ chữ tối thiểu 16px trên portal bệnh nhân.
