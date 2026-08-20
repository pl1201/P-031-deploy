# Kế hoạch hoàn thiện module Sinh thực đơn theo bữa ăn Việt Nam

Ngày tổng hợp: 2026-08-12

> [!NOTE]
> Đây là đặc tả UX/domain cho module sinh thực đơn, không phải kế hoạch production độc lập. Thứ tự dependency, owner, migration, security, rollout và Go/No-Go nằm tại [Production Readiness Master Plan](./PRODUCTION_READINESS_MASTER_PLAN.md), mục 9.0. Khi có khác biệt, runtime production ưu tiên CP-SAT trước; LLM chỉ fallback/rank/diễn đạt và không quyết định safety.

## 1. Mục tiêu sản phẩm

Module Sinh thực đơn không chỉ tạo một danh sách `dish_id + grams` đạt tổng dinh dưỡng. Kết quả phải đồng thời:

- giống một ngày ăn thực tế của người Việt;
- đúng cấu trúc từng bữa;
- có định lượng chính xác để backend tính lâm sàng;
- có cách diễn đạt thân thuộc để người bệnh dễ thực hiện;
- truy xuất được nguồn của món, nguyên liệu và phép quy đổi;
- được chuyên gia duyệt trước khi người bệnh nhìn thấy.

Nguyên tắc kiến trúc:

```text
LLM chọn tổ hợp món có ý nghĩa ẩm thực
CP-SAT điều chỉnh khẩu phần và ràng buộc
Backend tính dinh dưỡng, kiểm tra an toàn và tạo hash
Chuyên gia phê duyệt
Người bệnh nhận hướng dẫn bằng đơn vị thân thuộc
```

LLM không tự tạo số dinh dưỡng và không tự quyết định an toàn.

## 2. Một ngày thực đơn Việt Nam kỳ vọng

### Bữa sáng — nhanh gọn

- Phở gà ít bánh — 380 g

### Bữa trưa — một mâm cơm đầy đủ

- Cơm gạo lứt — 150 g
- Cá nướng nghệ — 100 g
- Rau muống luộc — 150 g
- Canh bí xanh — 200 g

### Bữa phụ — nhỏ, đơn giản

- Ổi — 100 g
- Sữa chua không đường — 100 g

### Bữa tối — mâm cơm nhẹ hơn bữa trưa

- Cơm trắng — 120 g
- Đậu hũ sốt cà — 120 g
- Cải thìa luộc — 150 g
- Canh rau ngót — 200 g

Đây là ví dụ cấu trúc, không phải thực đơn cố định cho mọi bệnh nhân. Món và khẩu phần thực tế phải được tính từ hồ sơ, mục tiêu, dị ứng, thuốc và dữ liệu có nguồn.

## 3. Hai lớp định lượng

### 3.1. Lớp chuyên môn

Chuyên gia và backend tiếp tục dùng gram vì đây là đơn vị dùng để:

- tính năng lượng và chất dinh dưỡng;
- kiểm tra carbohydrate, natri, kali, phospho và purine;
- so sánh với mục tiêu;
- tạo nutrition hash;
- tái lập kết quả khi audit.

Ví dụ:

```text
Cơm gạo lứt — 150 g
Cá nướng nghệ — 100 g
Canh bí xanh — 200 g
```

### 3.2. Lớp thân thuộc cho người bệnh

Người bệnh được xem thêm đơn vị thường dùng trong gia đình:

```text
Cơm gạo lứt — 1 bát cơm vừa (150 g)
Cá nướng nghệ — 1 khúc/cỡ lòng bàn tay (100 g)
Rau muống luộc — khoảng 1 bát rau (150 g)
Canh bí xanh — 1 bát canh nhỏ (200 g)
Ổi — khoảng 1/2 quả vừa, phần ăn được (100 g)
Sữa chua không đường — 1 hũ (100 g)
```

Không được tự suy diễn `1 thìa`, `1 bát` hoặc `1 miếng` thành gram. Mỗi phép quy đổi phải tồn tại trong dữ liệu `serving_sizes` hoặc `unit_conversions` và có `source_ref`.

Ví dụ với thìa:

```text
Dầu ăn — 1 thìa cà phê (5 g)
Đậu phộng rang — 1 thìa canh gạt (10 g)
Nước mắm — 1 thìa cà phê (khối lượng theo bảng quy đổi có nguồn)
```

Các mô tả phải chỉ rõ loại dụng cụ khi có khác biệt:

- thìa cà phê;
- thìa canh;
- thìa gạt;
- thìa vun;
- bát cơm;
- bát canh;
- cốc tiêu chuẩn.

Nếu chưa có phép quy đổi đáng tin cậy, UI phải giữ gram và ghi:

```text
Chưa có đơn vị gia đình được kiểm chứng cho món này.
```

Không được đoán một đơn vị chỉ để UI trông thân thiện hơn.

## 4. Cấu trúc dữ liệu đề xuất

```text
MealPlan
└── Meal
    ├── slot
    ├── template
    ├── nutrition_summary
    └── components[]
        ├── dish_id
        ├── role
        ├── grams
        ├── household_portion
        └── source_refs[]
```

Ví dụ response cho người bệnh:

```json
{
  "slot": "lunch",
  "template": "vietnamese_tray",
  "components": [
    {
      "dish_id": "COM-GAO-LUT",
      "role": "staple",
      "name_vi": "Cơm gạo lứt",
      "grams": 150,
      "household_portion": {
        "quantity": 1,
        "unit": "bát cơm vừa",
        "label_vi": "1 bát cơm vừa",
        "grams": 150,
        "source_ref": "serving_sizes:rice_bowl_cooked",
        "confidence": "verified"
      }
    }
  ]
}
```

`grams` luôn là giá trị chuẩn. `household_portion` là lớp biểu diễn có thể null.

## 5. Vai trò món

Mỗi món cần có một hoặc nhiều vai trò được kiểm soát:

| Role | Ý nghĩa | Ví dụ |
|---|---|---|
| `staple` | Tinh bột chính | cơm, bún, phở, khoai |
| `protein` | Đạm chính | cá, gà, thịt nạc, đậu hũ |
| `vegetable` | Rau | rau luộc, rau xào ít dầu |
| `soup` | Canh | canh bí, canh rau ngót |
| `fruit` | Trái cây | ổi, thanh long, bưởi |
| `dairy` | Sữa/chế phẩm sữa | sữa chua không đường |
| `beverage` | Đồ uống | sữa đậu nành không đường |
| `condiment` | Gia vị/nước chấm | nước mắm, dầu, hạt nêm |

Đổi món phải giữ nguyên role. Không được dùng cơm thay cá chỉ vì kcal gần nhau.

## 6. Template theo từng bữa

### `quick_breakfast`

- một món chính;
- tối đa một món hoặc đồ uống kèm;
- nhanh chuẩn bị;
- điều chỉnh lượng bún, bánh, phở hoặc xôi theo carbohydrate.

### `vietnamese_tray`

- bắt buộc có `staple`;
- bắt buộc có `protein`;
- bắt buộc có `vegetable`;
- khuyến nghị có `soup`;
- tránh quá nhiều món chiên hoặc món mặn trong cùng mâm.

### `light_vietnamese_tray`

- giữ cấu trúc mâm cơm;
- tinh bột thấp hơn bữa trưa theo mục tiêu phân bố;
- ưu tiên cá, đậu hũ, thịt nạc, rau và canh;
- hạn chế món nhiều dầu hoặc natri cao.

### `small_snack`

- một đến hai thành phần;
- chỉ dùng role phù hợp như `fruit`, `dairy`, `beverage` hoặc phần nhỏ `staple`;
- giới hạn gram riêng;
- không ghép nhiều nguyên liệu rời thành một bữa phụ lớn bất thường.

## 7. Dinh dưỡng theo từng bữa

Backend cần trả breakdown, không chỉ tổng ngày:

| Bữa | kcal | Carb | Protein | Khối lượng |
|---|---:|---:|---:|---:|
| Sáng | 450 | 48 g | 23 g | 380 g |
| Trưa | 720 | 82 g | 38 g | 600 g |
| Phụ | 180 | 20 g | 8 g | 200 g |
| Tối | 650 | 70 g | 35 g | 590 g |

Nhờ đó có thể phát hiện tổng ngày đạt nhưng carbohydrate tập trung quá nhiều ở một bữa.

## 8. Xử lý plan đã tồn tại

Khi API trả `409 Conflict`, backend nên kèm:

```json
{
  "detail": "Đã có thực đơn đang xử lý cho ngày này",
  "existing_plan_id": "...",
  "existing_status": "pending_review"
}
```

UI hiển thị:

```text
Đã có thực đơn đang chờ duyệt cho ngày này.

[Mở thực đơn hiện có] [Chọn ngày khác]
```

## 9. Sinh lại có versioning

```text
Bản nháp v1
  ↓ Sinh lại
Bản nháp v2
  ↓ Đổi món/chỉnh khẩu phần
Bản nháp v3
  ↓ Phê duyệt
Approved version = v3
```

Mỗi phiên bản cần lưu người thực hiện, thời gian, cấu hình đầu vào, lý do, menu hash và nutrition hash. Không ghi đè âm thầm bản cũ.

## 10. Preview trước khi đổi món

Trước khi xác nhận thay món, UI hiển thị tác động:

| Chỉ số | Hiện tại | Sau thay | Chênh lệch |
|---|---:|---:|---:|
| Năng lượng | 220 kcal | 185 kcal | -35 |
| Carb | 4 g | 12 g | +8 |
| Protein | 28 g | 16 g | -12 |
| Natri | 260 mg | 410 mg | +150 |

Backend phải chạy preview deterministic và trả safety delta. Chỉ sau khi người dùng xác nhận mới tạo version mới.

## 11. Metadata LLM

Với chế độ hybrid cần lưu:

```json
{
  "generator": "hybrid",
  "initial_engine": "cpsat",
  "llm_used": true,
  "llm_model": "gemini-2.5-flash",
  "llm_call_count": 1,
  "fallback_used": false
}
```

UI chuyên gia chỉ hiển thị metadata cần thiết; không hiển thị prompt nội bộ hoặc API key.

## 12. Điểm chất lượng ẩm thực

Ngoài safety gate, optimizer cần đánh giá:

- `meal_structure_score`;
- `variety_score`;
- `regional_fit_score`;
- `preparation_score`;
- `repetition_penalty`;
- `portion_plausibility_score`.

Safety là điều kiện bắt buộc. Điểm ẩm thực dùng để xếp hạng giữa các phương án đều an toàn, không được thay thế kiểm tra lâm sàng.

## 13. Dashboard và nhật ký

Dashboard chuyên gia cần API tổng hợp thật cho số lượng chờ duyệt, cảnh báo theo risk, số plan đã duyệt và thời gian duyệt trung bình.

Dashboard người bệnh cần nối nhật ký thật để so sánh kế hoạch và thực tế. Khi một món chưa map được hoặc chưa quy đổi được khẩu phần, UI phải hiển thị `chưa đủ dữ liệu`, không coi là 0.

## 14. Thứ tự triển khai

1. Thêm role món và template bữa.
2. Sinh cấu trúc bữa Việt theo slot.
3. Tính dinh dưỡng theo từng bữa.
4. Thêm household portion có nguồn cho UI người bệnh.
5. Xử lý `409` bằng nút mở plan hiện có.
6. Preview và thay món theo cùng role.
7. Sinh lại có versioning.
8. Thêm điểm chất lượng ẩm thực.
9. Lưu metadata LLM/hybrid.
10. Hoàn thiện dashboard và nhật ký từ API thật.

## 15. Tiêu chí nghiệm thu

- Bữa sáng không bị sinh thành một mâm cơm đầy đủ.
- Bữa trưa và tối có đủ vai trò bắt buộc theo template.
- Bữa phụ tối đa hai thành phần và nằm trong giới hạn khẩu phần.
- Mỗi thành phần có `dish_id`, role và gram.
- Đổi món chỉ đưa ứng viên cùng role.
- Backend trả tổng dinh dưỡng theo bữa và theo ngày.
- Người bệnh thấy cả gram và đơn vị thân thuộc khi có phép quy đổi đã kiểm chứng.
- Mọi đơn vị bát, thìa, miếng, quả hoặc hũ đều có `source_ref`.
- Không có phép quy đổi thì giữ gram và nói rõ chưa đủ dữ liệu.
- LLM không sinh số dinh dưỡng, không duyệt plan và không tự tạo ID ngoài database.
- Mọi chỉnh sửa làm tăng version và tạo lại integrity hashes.
