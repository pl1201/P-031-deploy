# API Reference — VNutriCare

## Base URL & xác thực

Base URL production:

```text
https://<backend-render>.onrender.com/api/v1
```

Mọi API cần header dưới đây, trừ `auth/*`, `health` và `status`:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

Tài liệu OpenAPI khi backend đang chạy: `https://<backend-render>.onrender.com/docs`.

---

## 1. Authentication

### `POST /auth/register`

Tạo tài khoản bệnh nhân hoặc chuyên gia.

**Input**

```json
{
  "email": "user@example.com",
  "password": "matkhau123",
  "role": "patient",
  "full_name": "Nguyễn Văn A"
}
```

- `role`: `patient` hoặc `dietitian`.
- Password: tối thiểu 8 ký tự, có cả chữ và số.

**Output — 201**

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "patient"
}
```

### `POST /auth/login`

Đăng nhập, trả về JWT để frontend gọi các API bảo vệ.

**Input**

```json
{ "email": "user@example.com", "password": "matkhau123" }
```

**Output — 200**

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### `POST /auth/refresh`

Gia hạn access token.

**Input**

```json
{ "refresh_token": "<jwt-refresh-token>" }
```

**Output:** cùng cấu trúc `/auth/login`.

---

## 2. Patient profiles

### `GET /patients?page=1&page_size=20`

Lấy danh sách bệnh nhân, dùng tại tab **Hồ sơ bệnh nhân** và **Nhật ký phê duyệt**.

- **Quyền:** `dietitian`, `admin`.
- **Input:** query `page` (mặc định 1), `page_size` (1–100).

**Output — 200**

```json
{
  "items": ["<PatientProfile>"],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

### `GET /patients/{profile_id}`

Lấy một hồ sơ bệnh nhân.

- **Quyền:** bệnh nhân chỉ xem hồ sơ của mình; chuyên gia/admin xem được hồ sơ hợp lệ.
- **Output:** một `<PatientProfile>`.

### `POST /patients`

Tạo hồ sơ bệnh nhân.

- **Quyền:** `dietitian`, `admin`.

**Input**

```json
{
  "user_id": "uuid-user",
  "age": 45,
  "sex": "male",
  "height_cm": 170,
  "weight_kg": 70,
  "activity_level": "light",
  "conditions": [{ "code": "T2DM", "stage": null }],
  "lab_values": { "hba1c": 7.2 },
  "allergies": ["tôm"],
  "medications": ["metformin"],
  "region": "north"
}
```

**Output — 201:** `<PatientProfile>`.

### `PUT /patients/{profile_id}`

Cập nhật một phần hoặc toàn bộ thông tin hồ sơ.

- **Input:** các trường của payload tạo hồ sơ, trừ `user_id`; tất cả đều tùy chọn.
- **Output — 200:** `<PatientProfile>` sau cập nhật.

### Cấu trúc `<PatientProfile>`

```json
{
  "id": "uuid-profile",
  "user_id": "uuid-user",
  "age": 45,
  "sex": "male",
  "height_cm": 170,
  "weight_kg": 70,
  "activity_level": "light",
  "conditions": [{ "code": "T2DM", "stage": null }],
  "lab_values": { "hba1c": 7.2 },
  "allergies": ["tôm"],
  "medications": ["metformin"],
  "region": "north"
}
```

---

## 3. Clinical targets

### `POST /targets/compute`

Tính BMR, TDEE và các định mức dinh dưỡng bằng Python/clinical rules, không dùng LLM.

**Input**

```json
{ "patient_id": "uuid-profile" }
```

**Output — 200**

```json
{
  "patient_id": "uuid-profile",
  "bmr_kcal": 1540,
  "tdee_kcal": 1848,
  "targets": {
    "kcal": {
      "nutrient": "kcal",
      "min_value": 1663,
      "max_value": 1848,
      "unit": "kcal",
      "rule_ids": ["..."],
      "guideline_refs": ["..."]
    }
  },
  "applied_rule_ids": ["..."],
  "needs_expert_review": true,
  "conflict_notes": []
}
```

---

## 4. Meal plans

### `POST /meal-plans`

Khởi tạo luồng sinh thực đơn. Agent chạy nền; API trả `202` ngay, sau đó frontend polling bằng `GET /meal-plans/{plan_id}`.

**Input**

```json
{
  "patient_id": "uuid-profile",
  "plan_date": "2026-08-08",
  "preferences": {
    "dislikes": ["khổ qua"]
  }
}
```

**Output — 202**

```json
{ "plan_id": "uuid-plan", "status": "drafting" }
```

### `GET /meal-plans/{plan_id}`

Lấy chi tiết một thực đơn để polling trạng thái, xem chi tiết và duyệt.

- **Bệnh nhân:** chỉ xem thực đơn đã `approved` và vượt qua publish gate.
- **Chuyên gia/admin:** xem được các trạng thái liên quan.

**Output:** `<MealPlan>`.

### `GET /meal-plans?patient_id=&status=&page=1`

Lấy lịch sử thực đơn.

- `patient_id`: tùy chọn, dùng cho trang chi tiết hồ sơ chuyên gia.
- `status`: `drafting`, `pending_review`, `approved`, `rejected`, hoặc `failed`.
- `page`: phân trang, mặc định 1.
- **Bệnh nhân:** backend tự áp publish gate; không thể dùng query để xem bản chưa duyệt.

**Output — 200**

```json
{
  "items": ["<MealPlan>"],
  "total": 3,
  "page": 1,
  "page_size": 20
}
```

### Cấu trúc rút gọn `<MealPlan>`

```json
{
  "id": "uuid-plan",
  "patient_id": "uuid-profile",
  "plan_date": "2026-08-08",
  "status": "pending_review",
  "items": [
    {
      "id": "uuid-item",
      "slot": "lunch",
      "dish_id": "pho-bo",
      "grams": 400,
      "name_vi": "Phở bò",
      "source": "recipe",
      "source_ref": "dish:pho-bo",
      "ingredients": []
    }
  ],
  "computed_nutrition": {},
  "violations": [],
  "safety_findings": [],
  "review_packet": {},
  "citations": [],
  "explanation_vi": null,
  "highest_risk": "none",
  "retry_count": 0,
  "menu_version": 1,
  "reviewer_id": null,
  "reviewer_notes": null,
  "created_at": "2026-08-08T12:00:00"
}
```

---

## 5. Human-in-the-loop review

### `GET /reviews/pending`

Lấy hàng chờ duyệt, ưu tiên thực đơn có rủi ro cao.

- **Quyền:** `dietitian`.
- **Output — 200:** mảng `<MealPlan>` trạng thái `pending_review`.

### `POST /reviews/{plan_id}/recompute`

Chuyên gia sửa gram của món; server tính lại dinh dưỡng, safety findings, review packet và risk trước khi duyệt.

- **Quyền:** `dietitian`.
- Chỉ hoạt động khi thực đơn đang `pending_review`.

**Input**

```json
{
  "edits": [
    { "item_id": "uuid-item", "grams": 120 }
  ]
}
```

**Output — 200:** `<MealPlan>` đã tính lại.

### `POST /reviews/{plan_id}/approve`

Duyệt và phát hành thực đơn cho bệnh nhân.

**Input**

```json
{
  "edits": [{ "item_id": "uuid-item", "grams": 120 }],
  "notes": "Theo dõi đường huyết sau ăn trong tuần đầu."
}
```

- `edits` và `notes` đều tùy chọn.
- Publish gate chặn nếu còn P0, thiếu hash do server tính hoặc menu bị thay đổi sau khi tính.
- Nếu có P1, `notes` là bắt buộc để ghi nhận lý do override.

**Output — 200:** `<MealPlan>` với `status: "approved"`.

### `POST /reviews/{plan_id}/reject`

Từ chối thực đơn và lưu lý do.

**Input**

```json
{ "reason": "Quá nhiều carbohydrate vào bữa tối, cần sinh lại." }
```

- `reason`: ít nhất 10 ký tự.
- **Output — 200:** `<MealPlan>` với `status: "rejected"`.

---

## 6. System & chat

### `GET /health`

Kiểm tra backend và database.

**Output — 200 / 503**

```json
{ "status": "ok", "env": "production" }
```

### `GET /status`

Trả trạng thái cơ bản của agent.

```json
{ "status": "ready", "agent": "LangGraph Agent v1.0" }
```

### `POST /chat`

Chat MVP có guardrail y khoa. Endpoint không đưa ra chỉ định thuốc/chẩn đoán.

**Input**

```json
{ "message": "Tôi có nên tự đổi liều insulin không?" }
```

**Output**

```json
{
  "reply": "...",
  "blocked": true,
  "method": "regex"
}
```

`method` có thể là `regex`, `llm` hoặc `safe_pattern`.

---

## Luồng API mà frontend đang sử dụng

```text
POST /auth/login
  → GET /patients
  → POST /meal-plans
  → GET /meal-plans/{plan_id}  (polling khi sinh)
  → GET /reviews/pending
  → POST /reviews/{plan_id}/recompute
  → POST /reviews/{plan_id}/approve hoặc /reject
  → GET /meal-plans?status=approved
```

Frontend gọi API tập trung tại `web-next/src/lib/api.ts`.
