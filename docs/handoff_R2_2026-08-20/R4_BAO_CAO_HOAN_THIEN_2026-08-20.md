# Báo cáo hoàn thiện phần việc R4 — 2026-08-20

## Kết quả

R4 đã hoàn thiện các phần có thể triển khai an toàn trên trạng thái repo hiện tại:

1. **Giữ luồng đăng ký tài khoản demo**
   - Theo yêu cầu vận hành demo, `POST /auth/register` tiếp tục chấp nhận `patient` và `dietitian` như ban đầu.
   - `admin` vẫn không được tạo qua public API.
   - Có test hồi quy xác nhận tài khoản demo `dietitian` vẫn đăng ký và đăng nhập được.
   - Trước khi phát hành production, cần thay đăng ký `dietitian` bằng invitation/admin provisioning.

2. **Guardrail cho nhật ký ăn tự do**
   - `POST /food-logs` dùng dependency `guard_free_text("free_text_vi")`.
   - Văn bản mang chỉ định y khoa bị chặn trước khi đi vào matcher/lưu DB.
   - Có test hồi quy cho tình huống yêu cầu ngừng metformin.

3. **Dinh dưỡng từng món qua API**
   - `MealPlanItemOut` bổ sung kcal, protein, carb, fat, fiber, sugar, purine.
   - Đường và purine có cờ completeness; thiếu dữ liệu trả `null`, không trả 0.
   - Món dạng recipe được tính từ nguyên liệu đã eager-load và scale theo gram thực tế.
   - Món legacy dạng food được tính từ mật độ dinh dưỡng của chính food item.

4. **UI bệnh nhân**
   - Drawer chi tiết bữa hiển thị gram, kcal và tên/gram từng nguyên liệu.
   - Khi dữ liệu đường chưa đầy đủ, UI hiện rõ “chưa đủ số liệu để kết luận”.
   - TypeScript interface đã khớp response backend.
   - Tinh giản dashboard cho người dùng không chuyên: bỏ banner nhắc bữa và toàn bộ thanh “Thực đơn đang áp dụng”.
   - Gộp kcal đã ăn, kcal/macros kế hoạch vào cùng khung “Kế hoạch trong ngày”.
   - Thêm một lời mời đơn giản ở cuối danh sách bữa để báo ăn món khác hoặc bỏ bữa.
   - Lời nhắc bữa được chuyển vào chuông thông báo với câu chữ nhẹ nhàng theo thời điểm trong ngày.
   - Sửa lỗi vòng kcal không cập nhật: sau khi ghi bữa, frontend tải lại cả food-log và `DaySummary` ngay lập tức.
   - Thay hai card phụ bên phải bằng “Bản tin chăm sóc”: cung cấp các lối tắt thiết thực tới tổng hợp tuần, nhật ký dinh dưỡng và thiết bị sức khỏe.
   - Thay lời chào chung bằng welcome card có thông điệp theo thời điểm trong ngày và hiệu ứng nền nhẹ; hiệu ứng tự tắt khi người dùng bật reduced-motion.
   - Hoàn thiện khung “Việc tiếp theo” trên Patient Home: tự chọn bữa có trong kế hoạch nhưng chưa ghi gần nhất, hiển thị tiến độ ngày và chuyển sang trạng thái hoàn tất khi đủ bữa.
   - Chuẩn hóa typography theo thang 12/14/16/18/24/30px; tiêu đề trang dùng `clamp(30px, 4vw, 38px)`, giữ Plus Jakarta Sans cho nội dung và IBM Plex Mono ở dữ liệu kỹ thuật cần thiết.
   - Hai badge đếm thông báo trên desktop/mobile được tăng từ 10px lên 12px và vùng hiển thị từ 16px lên 20px; số kcal chính giảm độ đậm từ 800 xuống 700.
   - Màu chữ phụ `--c-muted` được hiệu chỉnh thành `#565453`, đo được 7,13:1 trên nền `#f7f9f9`, đạt WCAG AAA cho chữ thường.

5. **Risk badge**
   - Repo hiện tại đã có badge `P0/P1/P2/none` trên hàng chờ duyệt và trang chi tiết.
   - R4 giữ nguyên implementation đang có; không viết đè phần UI đang phát triển.

6. **UI wearable**
   - Thêm trang `/patient/activity` và mục điều hướng “Thiết bị sức khỏe”.
   - Consent tách theo bước chân, nhịp tim nghỉ, giấc ngủ và calo tiêu hao.
   - Mỗi chỉ số có nhãn độ tin cậy bằng cả màu và chữ.
   - Nêu rõ calo wearable không được đưa vào TDEE/khẩu phần.
   - Trang không tạo dữ liệu giả và không giả vờ đã kết nối HealthKit.

## Quyết định fail-closed

`khau_phan_mo_ta` đã có trong API nhưng hiện trả `null`. Repo chưa có model runtime và seed canonical cho `household_units`/`dish_unit_conversions`; artifact bàn giao còn lệch 318 so với 405 dòng trong biên bản. R4 không dùng snapshot không nhất quán để sinh con số bệnh nhân nhìn thấy.

Khi R2/R3 hợp nhất migration + model + seed canonical, R4 chỉ cần nối lookup đã ký vào field này. Trong thời gian chờ, UI hiển thị gram — đúng nguyên tắc không đoán.

## Phần còn phụ thuộc role khác

- **R1:** backend native bridge/OAuth cho Apple HealthKit và persistence observation.
- **R2:** ký ngưỡng red flag wearable; duyệt loại chỉ số và nội dung cảnh báo cuối.
- **R3:** hợp nhất và đồng bộ `household_units`, `dish_unit_conversions`; xác nhận bộ 318/405 dòng nào là canonical.
- **Pháp lý/dữ liệu:** privacy policy, retention và consent wording trước khi phát hành kết nối thật.

## Kiểm thử

- `108 passed` trên nhóm API auth, food-log, meal-plan, review, patient, target, pantry, explainer, workspace và self-service.
- `npx tsc --noEmit`: pass.
- `npm run lint`: 0 error; còn 1 warning có sẵn ở `dietitian/meal-plans/new/page.tsx` (`formatTargetValue` chưa dùng), không thuộc thay đổi này.

## Lưu ý tích hợp

Working tree vốn có nhiều thay đổi chưa commit. Các thay đổi R4 trong báo cáo này không nên được commit bằng `git add .`; cần stage đúng file và review diff trước khi tạo commit/PR.
