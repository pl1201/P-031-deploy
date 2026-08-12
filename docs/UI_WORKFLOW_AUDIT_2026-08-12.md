# Audit workflow UI bệnh nhân và sinh thực đơn

Ngày kiểm tra: 2026-08-12
Phạm vi: `web-next`, API FastAPI, dữ liệu thực tế trên Supabase
Trạng thái tài liệu: ghi nhận vấn đề và đề xuất kiến trúc; **chưa triển khai sửa workflow**.

## 1. Kết luận

Workflow hiện tại chưa đúng ranh giới nghiệp vụ:

1. Trang **Bệnh nhân** vừa hiển thị hồ sơ vừa trực tiếp tạo meal plan, polling và chuyển trang. Trang này nên chỉ đọc/tìm kiếm/mở hồ sơ bệnh nhân. Nếu giữ CTA “Sinh thực đơn”, CTA chỉ được điều hướng tới màn hình tạo với `patient_id` đã chọn, không gọi API sinh ngay tại danh sách.
2. Trang **Tạo thực đơn** đang hiển thị nguyên liệu thô như một “thực đơn món Việt”. Đây không phải lỗi hiển thị đơn thuần; dữ liệu meal plan trong database thực sự đang được lưu dưới dạng `food_id + grams`, không phải `dish_id`.
3. Nút **Đổi món** không đổi món tại chỗ. Nó điều hướng sang trang review nên phá vỡ ngữ cảnh và sai nhãn hành động.
4. UI đánh dấu nhiều kiểm tra là “Đạt” chỉ vì backend không trả violation. Cách suy luận này không đủ để kết luận đạt lâm sàng.
5. Contract `targets` giữa frontend và backend không khớp, khiến UI vẫn hiện “Tính khi sinh” sau khi backend đã tính xong.
6. Meal plan mới sinh thiếu `review_packet`, `menu_hash` và `nutrition_hash`; vì vậy nút chuyển/duyệt có thể dẫn tới publish gate bị chặn.

## 2. Bằng chứng từ dữ liệu thực tế

Đã truy vấn chỉ đọc plan đang hiển thị trong ảnh:

- Plan: `4791a49b-2d40-4adf-8534-cd3d745a84a5`
- Trạng thái: `pending_review`
- Generator: `hybrid`
- Tổng năng lượng: `2564 kcal`
- Carbohydrate: `290.5 g`
- Protein: `130.34 g`
- Số item: `8`
- Số item có `dish_id`: `0`
- `review_packet`: rỗng
- `menu_hash`: chưa có
- `nutrition_hash`: chưa có
- `highest_risk`: `none`

Các item được lưu:

| Bữa | Dữ liệu lưu | Khối lượng |
|---|---|---:|
| Sáng | Dưa chuột | 25 g |
| Trưa | Dưa chuột | 25 g |
| Tối | Dưa chuột | 300 g |
| Phụ | Cà rốt | 300 g |
| Phụ | Lạc rang | 200 g |
| Phụ | Trứng cút | 50 g |
| Phụ | Củ cải trắng | 300 g |
| Phụ | Đậu đen | 300 g |

Bữa phụ có tổng khối lượng `1.150 g`. Kết quả có thể nằm trong dải macro do solver tính, nhưng không đạt yêu cầu sản phẩm về cấu trúc bữa ăn, món hoàn chỉnh, khẩu vị và tính khả dụng thực tế.

Targets trong database có cấu trúc lồng:

```text
targets
├── patient_id
├── bmr_kcal
├── tdee_kcal
├── applied_rule_ids
├── needs_expert_review
└── targets
    ├── kcal
    ├── carb_g
    ├── protein_g
    ├── fiber_g
    ├── sugar_g
    └── na_mg
```

Frontend hiện đọc `plan.targets['energy_kcal']` và `plan.targets['carb_g']`. Đường dẫn đúng theo response thực tế phải là `plan.targets.targets.kcal` và `plan.targets.targets.carb_g` sau khi đồng bộ type.

## 3. Ranh giới đúng của trang Bệnh nhân

### Trang danh sách bệnh nhân được phép làm

- Gọi `GET /patients`.
- Tìm kiếm/lọc hồ sơ.
- Hiển thị thông tin bệnh nhân đã có trong database.
- Mở `/dietitian/patients/{patient_id}`.
- Có thể có CTA “Tạo thực đơn”, nhưng CTA chỉ điều hướng:

```text
/dietitian/meal-plans/new?patient_id={patient_id}
```

### Trang danh sách bệnh nhân không nên làm

- Không gọi `POST /meal-plans`.
- Không polling trạng thái generation.
- Không tự chuyển sang review sau khi background task kết thúc.
- Không quản lý toast/trạng thái sinh thực đơn.

Vi phạm hiện tại nằm trong `handleGeneratePlan()` tại:

```text
web-next/src/app/dietitian/patients/page.tsx
```

Hàm này đang tạo plan, polling mỗi 2 giây và `router.push()` sang review. Toàn bộ trách nhiệm đó thuộc màn hình tạo thực đơn.

## 4. Nguyên nhân thực đơn không giống database món

Trong `src/api/routes/meal_plans.py`:

```python
uses_raw_candidates = get_settings().menu_generator in ("cpsat", "hybrid")
foods = raw_foods if uses_raw_candidates else dish_foods
```

Với cấu hình hiện tại là `hybrid`, graph nhận kho `raw_foods`. Kết quả không có `planned_dishes` sẽ được lưu trực tiếp thành:

```text
MealPlanItem(food_id=..., grams=...)
```

Do đó frontend đang hiển thị đúng bản ghi database, nhưng database chứa **nguyên liệu rời**, không phải **món ăn hoàn chỉnh**.

Đây là vấn đề kiến trúc candidate/optimizer, không nên sửa bằng cách đổi tên hoặc ghép chuỗi ở frontend.

### Quy tắc dữ liệu cần thống nhất

- Một hàng chính trên UI phải đại diện cho một `Dish` có `dish_id`, tên món, serving size và danh sách nguyên liệu.
- `food_id` chỉ nên xuất hiện bên trong thành phần món hoặc phần bổ sung có nhãn rõ ràng.
- Không được gộp tùy ý nhiều nguyên liệu thô thành tên món ở frontend.
- Mỗi slot phải có rule về số món, tổng gram và loại món phù hợp.
- Bữa phụ phải có giới hạn gram riêng; không thể dùng cùng trần với tổng bữa chính.
- Cần kiểm tra trùng món/nguyên liệu giữa các slot.

## 5. Nút “Đổi món” hiện tại sai workflow

Hiện tại nút này thực hiện:

```tsx
router.push(`/dietitian/reviews/${plan.id}`)
```

Đây là hành vi “Mở trang review”, không phải “Đổi món”.

Endpoint `POST /meal-plans/{base_plan_id}/equivalent` đang có không phù hợp cho nút này vì:

- Nó thay thế/tạo **toàn bộ plan tương đương**, không thay một item.
- Nó yêu cầu substitution scope.
- Base plan phải qua điều kiện phê duyệt/phạm vi thay thế.
- Nó phục vụ luồng thực đơn tương đương sau phê duyệt, không phải biên tập draft trước review.

## 6. Workflow UI đề xuất

```text
Danh sách bệnh nhân
  → Mở màn tạo với patient_id
  → Xác nhận hồ sơ và mục tiêu
  → Chọn cấu hình thật sự được backend hỗ trợ
  → Sinh draft
  → Hiển thị dish + serving + dinh dưỡng từng bữa
  → Đổi món/chỉnh gram ngay tại draft
  → Backend tính lại nutrition + safety
  → Người dùng kiểm tra thay đổi
  → Lưu draft
  → Chủ động chuyển sang hàng chờ duyệt
  → Review/phê duyệt
```

### Hành vi “Đổi món” đúng

1. Nhấn “Đổi món” không rời trang.
2. Mở drawer/modal bên phải cho đúng meal item.
3. Hiển thị candidate từ kho `Dish`, đã lọc theo:
   - vùng miền;
   - dị ứng;
   - thuốc–thực phẩm;
   - bệnh nền;
   - slot;
   - nguồn dữ liệu;
   - mức tương đương dinh dưỡng.
4. Chọn candidate.
5. Backend thay item trong transaction.
6. Backend tính lại toàn bộ nutrition, violations, safety findings và hashes.
7. UI cập nhật tại chỗ từ response mới.
8. Nếu không đạt, hiển thị cảnh báo và cho hoàn tác; không tự chuyển review.

## 7. API còn thiếu cho workflow

Đề xuất contract tối thiểu:

### Lấy candidate thay món

```http
GET /meal-plans/{plan_id}/items/{item_id}/replacement-candidates
```

Response cần có `dish_id`, `name_vi`, `serving_g`, nutrition delta, nguồn và lý do phù hợp.

### Thay một món

```http
POST /meal-plans/{plan_id}/items/{item_id}/replace
```

```json
{
  "dish_id": "...",
  "serving_g": 320
}
```

Response phải trả toàn bộ plan phiên bản mới sau recompute.

### Chỉnh gram

Có thể dùng endpoint recompute hiện tại, nhưng cần trả đủ:

- `menu_version`;
- `computed_nutrition`;
- `violations`;
- `safety_findings`;
- `review_packet`;
- `citations`;
- `menu_hash`/trạng thái integrity phù hợp cho UI.

### Sinh lại

```http
POST /meal-plans/{plan_id}/regenerate
```

Không nên tạo plan thứ hai cùng ngày rồi gặp `409`.

## 8. Sai lệch trạng thái kiểm tra lâm sàng

Frontend hiện dùng logic gần như:

```text
không có violation → Đạt
```

Điều này không an toàn. Không có violation có thể do:

- rule chưa chạy;
- dữ liệu thiếu;
- review packet chưa được tạo;
- category đó chưa được validator kiểm tra;
- contract response thiếu trường.

UI chỉ được hiển thị “Đạt” khi backend trả verdict tường minh. Trạng thái cần tách:

- `pending`: chưa chạy;
- `pass`: đã kiểm tra và đạt;
- `warning`: cần chuyên gia xem;
- `blocked`: không được chuyển review/phát hành;
- `insufficient_data`: thiếu dữ liệu, không được coi là đạt.

Plan `4791a49b` hiện có `violations=[]` nhưng đồng thời `review_packet={}`, không có hashes. UI đang hiển thị “Đạt” là kết luận quá mức so với dữ liệu backend.

## 9. Các file liên quan

### Frontend

- `web-next/src/app/dietitian/patients/page.tsx`
- `web-next/src/app/dietitian/meal-plans/new/page.tsx`
- `web-next/src/app/dietitian/reviews/[id]/page.tsx`
- `web-next/src/lib/api.ts`

### Backend

- `src/api/routes/meal_plans.py`
- `src/api/routes/reviews.py`
- `src/api/routes/equivalent.py`
- `src/agents/assembly.py`
- `src/agents/optimizer.py`
- `src/clinical/dishes.py`
- `src/db/models.py`

## 10. Thứ tự sửa đề xuất

1. Chốt schema response `MealPlan` và sửa type frontend.
2. Tách hành động sinh plan khỏi trang danh sách bệnh nhân.
3. Đảm bảo generator tạo cấu trúc dựa trên `Dish`, không phát hành danh sách nguyên liệu rời như một thực đơn.
4. Thêm rule phân bố bữa, giới hạn gram theo slot và chống lặp.
5. Bổ sung endpoint replacement candidate và replace item.
6. Sửa “Đổi món” thành drawer/modal tại chỗ.
7. Recompute nutrition/safety/hashes sau mọi chỉnh sửa.
8. Chỉ cho chuyển review khi backend trả gate hợp lệ.
9. Bổ sung integration test cho toàn workflow.

## 11. Tiêu chí nghiệm thu

- Trang bệnh nhân không gọi API sinh thực đơn.
- CTA từ bệnh nhân chỉ mở màn tạo với đúng `patient_id`.
- Mỗi bữa hiển thị ít nhất một món có `dish_id` hoặc được đánh dấu rõ là nguyên liệu bổ sung.
- Không lặp cùng một nguyên liệu làm món chính ở nhiều bữa nếu không có chủ ý được giải thích.
- Bữa phụ không vượt giới hạn gram đã định.
- “Đổi món” không điều hướng sang review.
- Sau thay món, nutrition và safety được tính lại từ backend.
- UI không suy `Đạt` từ mảng violation rỗng.
- Plan không thể chuyển review/approve nếu thiếu review packet hoặc integrity hashes.
- Tất cả con số dinh dưỡng hiển thị đều đến từ response backend và có trạng thái nguồn.

## 12. Trạng thái triển khai ngày 2026-08-12

Đã triển khai:

- Trang bệnh nhân không còn gọi API sinh thực đơn; CTA chỉ mở màn tạo với `patient_id`.
- Backend trả đầy đủ safety findings, review packet, citations, risk, version và trạng thái integrity hash.
- Generator lấy ứng viên món từ chính bảng `dishes` và `dish_ingredients` trong database. Nếu không chọn được món database, background job thất bại rõ ràng thay vì phát hành draft chỉ gồm nguyên liệu rời.
- Mỗi slot sinh mới phải có ít nhất một `dish_id`; nguyên liệu rời còn lại chỉ là phần cân chỉnh do optimizer tạo.
- Mục tiêu dinh dưỡng frontend đọc đúng từ `targets.targets`.
- UI chỉ hiện “Đạt” khi có review packet cùng menu/nutrition hash; không còn suy từ `violations=[]`.
- “Đổi món” mở drawer tại chỗ, lấy danh sách món từ database và không điều hướng sang review.
- Thay món gọi API riêng, thay đúng một item, rồi tính lại nutrition, safety, version và hashes.
- Recompute hỗ trợ plan có cả món hoàn chỉnh và phần nguyên liệu cân chỉnh bằng cách khai triển công thức món từ database.
- Quyết định approve/reject được ghi thêm vào lịch sử `meal_plan_review_events`.
- Frontend production build đã hoàn tất thành công.

Còn cần làm ở vòng tiếp theo:

- Endpoint “Sinh lại” riêng và chính sách lưu/so sánh nhiều bản nháp.
- Tối ưu objective để giảm tối đa nguyên liệu cân chỉnh rời và tăng chất lượng ẩm thực.
- Bổ sung delta dinh dưỡng ngay trong danh sách món thay thế trước khi người dùng xác nhận.
- Bổ sung integration test riêng cho candidate/replace và kiểm thử trình duyệt toàn workflow.
