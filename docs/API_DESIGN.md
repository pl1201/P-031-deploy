# API DESIGN — NutriCare Agent Backend

> Owner: R3 (Backend) · Review: R1 · Deadline mentor: **08/08/2026**
> Khớp `docs/ARCHITECTURE.md` §5 (schema DB), `src/db/models.py` (ORM), `docs/TICKETS.md` EPIC 4 (BE-\*) + EPIC 5 (HIT-\*).
> Base URL: `/api/v1`. Toàn bộ response bọc theo envelope chuẩn ở §7.

---

## 0. Nguyên tắc thiết kế (bắt buộc theo `CLAUDE.md`)

1. **RULE-1**: Không endpoint nào nhận hoặc trả kcal/na_mg/protein... do client tự tính. Mọi giá trị dinh dưỡng đi qua `compute_nutrition`/`compute_targets` phía server.
2. **RULE-2**: Response chứa dữ liệu dinh dưỡng luôn kèm `source`/`source_ref` cho từng dòng.
3. **RULE-3**: Không endpoint nào trả nội dung `meal_plan` cho role `patient` khi `status != approved`. Route FastAPI `async def`; mọi truy vấn DB blocking chạy qua threadpool (`run_in_threadpool` hoặc session async).
4. Input/Output đều là Pydantic model (đã có phần lớn trong `src/clinical/models.py`, `src/models/schemas.py`) — không dict tự do.

---

## 1. Danh sách API

| # | Method | Path | Ticket | Role | Mô tả ngắn |
|---|---|---|---|---|---|
| 1 | POST | `/auth/register` | BE-02 | public | Đăng ký tài khoản (patient hoặc dietitian) |
| 2 | POST | `/auth/login` | BE-02 | public | Đăng nhập, trả access+refresh token |
| 3 | POST | `/auth/refresh` | BE-02 | authenticated | Cấp access token mới từ refresh token |
| 4 | POST | `/patients` | BE-03 | dietitian, admin | Tạo hồ sơ bệnh nhân mới |
| 5 | GET | `/patients/{id}` | BE-03 | patient(chính mình), dietitian, admin | Xem hồ sơ |
| 6 | PUT | `/patients/{id}` | BE-03 | patient(chính mình), dietitian, admin | Sửa hồ sơ |
| 7 | GET | `/patients` | BE-03 | dietitian, admin | Danh sách bệnh nhân (phân trang) |
| 8 | POST | `/targets/compute` | BE-04 | patient(chính mình), dietitian | Tính định mức lâm sàng từ hồ sơ |
| 9 | POST | `/meal-plans` | BE-06 | patient(chính mình), dietitian | Yêu cầu sinh thực đơn (chạy graph, async) |
| 10 | GET | `/meal-plans/{id}` | BE-06, HIT-04 | patient(chính mình, chỉ khi approved), dietitian | Xem 1 thực đơn |
| 11 | GET | `/meal-plans` | BE-06 | patient(chính mình, chỉ approved), dietitian | Danh sách thực đơn |
| 12 | GET | `/reviews/pending` | HIT-02 | dietitian | Hàng chờ duyệt, sắp theo mức cảnh báo |
| 13 | POST | `/reviews/{id}/approve` | HIT-02 | dietitian | Duyệt (kèm sửa gram tuỳ chọn) |
| 14 | POST | `/reviews/{id}/reject` | HIT-02 | dietitian | Từ chối (lý do bắt buộc) |
| 15 | POST | `/food-logs` | BE-07 | patient(chính mình) | Ghi món đã ăn |
| 16 | GET | `/food-logs/summary` | BE-07 | patient(chính mình), dietitian | Tổng hợp theo ngày/tuần so định mức |
| 17 | GET | `/audit` | BE-08 | admin | Xem audit log (không có API xoá/sửa) |
| 18 | GET | `/health`, `/status` | SET-05 | public | Đã có sẵn |

---

## 2. Chi tiết từng API

### 2.1 `POST /auth/register`
**Input** (`RegisterRequest`):
```
email: EmailStr
password: str (min_length=8, phải có chữ+số)
role: Literal["patient", "dietitian"]   # admin không tự đăng ký được, tạo tay qua DB
full_name: str (max_length=100)          # KHÔNG lưu vào PatientProfile/prompt LLM — chỉ users.email dùng để login
```
**Output** `201`: `{ user_id: str, email: str, role: str }`
**Lỗi**:
- `409` email đã tồn tại
- `422` password yếu / email sai định dạng (Pydantic tự chặn)

**Ràng buộc**: `password_hash` bằng **argon2id** (`passlib[argon2]`). Không log password ở bất kỳ mức nào (kể cả DEBUG).

### 2.2 `POST /auth/login`
**Input**: `{ email: EmailStr, password: str }`
**Output** `200`: `{ access_token: str, refresh_token: str, token_type: "bearer", expires_in: int }`
**Lỗi**: `401` sai email/password (thông báo chung, không tiết lộ email có tồn tại hay không — chống user-enumeration).
**Ràng buộc**: access token TTL 15 phút, refresh TTL 7 ngày. JWT payload: `{sub: user_id, role, exp}`. Rate limit: 5 lần sai/15 phút/IP → `429`.

### 2.3 `POST /auth/refresh`
**Input**: `{ refresh_token: str }` → **Output**: access token mới. Refresh token cũ bị revoke (rotate).

### 2.4 `POST /patients`
**Input** (`PatientProfileCreate`, tái dùng `src/clinical/models.PatientProfile` + `user_id`):
```
user_id: str (UUID, phải role=patient, chưa có profile)
age: int (1-120) · sex: "male"|"female" · height_cm: float (80-250) · weight_kg: float (20-300)
activity_level: enum · conditions: [{code, stage}] · allergies: [str] · medications: [str]
region: "north"|"central"|"south"|null
```
**Output** `201`: `PatientProfile` đầy đủ + `id`.
**Lỗi**: `422` (validation Pydantic, khớp `src/clinical/models.py`) · `404` user_id không tồn tại · `409` user đã có profile.
**Ràng buộc**: cân nặng 20–300kg, tuổi 1–120 (đã có sẵn trong model) · `eGFR` (trong `lab_values`) ngoài khoảng hợp lệ → `422`.

### 2.5/2.6 `GET/PUT /patients/{id}`
**Output GET** `200`: `PatientProfile` (+ `medications`, `allergies` nối bảng).
**Ràng buộc phân quyền (RULE-3 mở rộng)**: `require_role()` — bệnh nhân A gọi hồ sơ B → `404` (không phải `403`, để không lộ sự tồn tại của hồ sơ khác — xem BE-09 AC).
PUT dùng cùng schema Create nhưng toàn bộ field optional (partial update).

### 2.7 `GET /patients?page=&page_size=&condition=`
Chỉ dietitian/admin. **Output**: `{ items: [...], total, page, page_size }` (đúng "API Response Format" chuẩn của dự án).

### 2.8 `POST /targets/compute`
**Input**: `{ patient_id: str }` (hoặc toàn bộ `PatientProfile` inline nếu chưa lưu DB — hỗ trợ preview trước khi tạo hồ sơ).
**Output** `200` (`ClinicalTargets`, nguyên trạng từ `compute_targets()`):
```
patient_id, bmr_kcal, tdee_kcal,
targets: { "kcal_100g": {min,max,unit,rule_ids,guideline_refs}, "na_mg": {...}, ... },
applied_rule_ids: [str], needs_expert_review: bool, conflict_notes: [str]
```
**Ràng buộc**: **Không gọi LLM** (đúng AC gốc BE-04). Trả `<200ms` (thuần Python/SQL). `needs_expert_review=true` → UI phải hiển thị rõ, không im lặng.
**Lỗi**: `404` patient_id không có hồ sơ.

### 2.9 `POST /meal-plans`
**Input**: `{ patient_id: str, plan_date: date, preferences: {dislikes: [str]}? }`
**Output** `202 Accepted`: `{ plan_id: str, status: "drafting" }` — **không đợi graph chạy xong trong request** (BE-06 AC: không để request treo > 60s). Chạy graph qua background task/queue, cập nhật `MealPlan.status` khi xong (`pending_review` hoặc `failed`).
**Ràng buộc**:
- Bệnh nhân chỉ gọi được cho `patient_id` = chính mình.
- Timeout graph nội bộ: nếu LLM (nhánh Gemini của Hybrid) không phản hồi sau 60s → node fail có kiểm soát, `status="failed"`, không crash request gốc.
- `retry_count <= 3` (đúng `MAX_RETRIES` trong `state.py`).
**Lỗi**: `404` patient chưa có hồ sơ (phải gọi `/targets/compute` gián tiếp trước, tức phải có `PatientProfile`) · `409` đã có plan `drafting`/`pending_review` cùng `plan_date` (không sinh trùng).

### 2.10/2.11 `GET /meal-plans/{id}`, `GET /meal-plans?patient_id=&status=`
**Output** (`MealPlanResponse`):
```
id, patient_id, plan_date, status,
items: { breakfast: [{food_id, name_vi, grams, source, source_ref}], lunch: [...], ... },
computed_nutrition: { kcal, na_mg, k_mg, p_mg, protein_g, carb_g, fat_g, fiber_g, sugar_g, sources: [SourceRef] },
targets_snapshot: ClinicalTargets,
violations: [{nutrient, actual, limit, severity, message_vi, suggestion}],
reviewer_id, reviewer_notes, created_at
```
**Ràng buộc RULE-3 (chặn cứng ở tầng query, không phải ở tầng serialize)**:
```python
# WRONG — lọc sau khi đã query hết, rò rỉ nội dung vào log/trace
if plan.status != "approved" and role == "patient": strip_content(plan)
# ĐÚNG — WHERE ngay trong câu query
query.where(MealPlan.status == "approved") if role == "patient" else query
```
Bệnh nhân gọi `GET /meal-plans` khi plan đang `drafting`/`pending_review` → **không xuất hiện trong danh sách**, gọi thẳng `GET /meal-plans/{id}` của plan đó → `404` (không phải `403`).

### 2.12 `GET /reviews/pending?sort=severity`
Chỉ role `dietitian`. **Output**: danh sách `MealPlan` có `status="pending_review"`, sort theo mức vi phạm nặng nhất trong `violations[]` trước (`hard` > `soft`).

### 2.13 `POST /reviews/{id}/approve`
**Input**: `{ edits: [{item_id, grams}]?, notes: str? }` — `edits` optional, cho phép chuyên gia sửa gram trước khi duyệt.
**Xử lý**: nếu có `edits` → ghi đè `MealPlanItem.grams` → **gọi lại `compute_nutrition` + `validate_menu` trên server** (không tin số client gửi, RULE-1) → nếu vẫn còn `hard` violation sau khi sửa → `422`, không cho duyệt. Ghi `AuditLog(action="approve", before=<bản trước sửa>, after=<bản sau>)`.
**Output** `200`: `MealPlan` với `status="approved"`, `reviewer_id`, `reviewed_at`.

### 2.14 `POST /reviews/{id}/reject`
**Input**: `{ reason: str (min_length=10) }` — thiếu/rỗng → `422` (đúng AC gốc HIT-02).
**Output** `200`: `status="rejected"`. Ghi `AuditLog`. (HIT-05, P2, có thể làm sau: đưa `reason` vào `feedback` để agent sinh lại tự động — ở bản tối thiểu chỉ cần set trạng thái, dietitian tự yêu cầu sinh lại qua `POST /meal-plans` mới.)

### 2.15 `POST /food-logs`
**Input**: `{ patient_id, food_id: int? , free_text_vi: str?, grams: float(0,2000], logged_at: datetime? }` — đúng 1 trong 2 (`food_id` XOR `free_text_vi`) bắt buộc.
**Xử lý**: `food_id` có sẵn → tra thẳng `food_items`. `free_text_vi` (gõ tự do, không có trong DB) → route qua OOV Estimator (CLN-07, nếu đã có) → `is_estimated=true`. **Nếu CLN-07 chưa xong**: trả `422` với message rõ ràng "chưa hỗ trợ món tự do, chọn từ danh sách" — **không âm thầm coi is_estimated=false / gán 0 dinh dưỡng** (RULE-2).
**Output** `201`: `FoodLog` đã lưu.

### 2.16 `GET /food-logs/summary?patient_id=&from=&to=`
**Output**: `{ days: [{date, kcal, na_mg, ..., pct_of_target: {...}}], warnings: [{nutrient, date, message_vi}] }`. Vượt ngưỡng Na → `warnings[]` chỉ rõ log nào đóng góp nhiều nhất (join `food_logs`→`food_items` sort theo `na_mg*grams/100` giảm dần).

### 2.17 `GET /audit?actor_id=&action=&from=&to=`
Chỉ `admin`. Không có `POST/PUT/DELETE` nào cho resource này ở tầng route (chặn cả ở router, không chỉ ở permission check).

---

## 3. Auth & phân quyền (BE-02, dùng chung mọi route)

```python
# Dependency chuẩn, áp cho toàn bộ route trừ /auth/*, /health, /status
def require_role(*roles: str):
    def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(403, "Không đủ quyền")
        return user
    return _dep
```
- Token hết hạn/không hợp lệ → `401` (không phải `403`).
- `patient` chỉ thao tác được resource gắn với `user_id` của chính mình — kiểm tra **ở tầng query** (`WHERE patient_profiles.user_id = current_user.id`), không kiểm tra sau khi đã lấy dữ liệu.

---

## 4. Ràng buộc chung (áp dụng mọi endpoint)

| Loại | Quy tắc |
|---|---|
| **Validation** | 100% qua Pydantic model ở boundary (request body + query param), không tự parse dict. Field ngoài khoảng hợp lệ → `422` kèm chi tiết field nào sai (FastAPI mặc định đã làm việc này qua `RequestValidationError`). |
| **Authentication** | Bearer JWT, header `Authorization: Bearer <token>`. `/auth/*`, `/health`, `/status` là public, còn lại bắt buộc. |
| **Giới hạn dữ liệu** | Phân trang bắt buộc cho mọi endpoint trả list (`page`, `page_size`, mặc định 20, tối đa 100). `grams` mọi nơi giới hạn `(0, 2000]` (khớp `MenuItem` hiện có). |
| **Rate limit** | `/auth/login` 5 lần/15 phút/IP. Các endpoint sinh thực đơn (`POST /meal-plans`) giới hạn 10 lần/giờ/patient — tốn LLM token thật. |
| **Xử lý lỗi** | Envelope lỗi thống nhất (xem §7). Không bao giờ trả stack trace ra ngoài (`APP_ENV=production` tắt `debug`). Log lỗi chi tiết ở server (không PII/PHI trong log — đúng `CLAUDE.md` §3). |
| **Timeout** | Mọi I/O blocking (DB sync driver, gọi LLM) chạy trong threadpool hoặc dùng driver async. Request tổng không quá 60s (BE-06 AC) — sinh thực đơn phải là `202 Accepted` + polling/webhook, không đồng bộ. |
| **CORS** | Đã cấu hình qua `settings.cors_origins` (`src/config.py`) — chỉ origin frontend thật, không dùng `*` ở production. |

---

## 5. Bảng lỗi chuẩn (HTTP status)

| Status | Khi nào |
|---|---|
| `400` | Request sai cấu trúc chung (hiếm, thường bị `422` bắt trước) |
| `401` | Thiếu/hết hạn token |
| `403` | Có token hợp lệ nhưng role không đủ quyền cho HÀNH ĐỘNG (không phải để che giấu tài nguyên — dùng `404` cho trường hợp đó) |
| `404` | Resource không tồn tại, HOẶC tồn tại nhưng thuộc user khác (chống rò rỉ thông tin — BE-09) |
| `409` | Xung đột trạng thái (email trùng, plan trùng ngày, user đã có profile) |
| `422` | Validation Pydantic thất bại, hoặc nghiệp vụ chặn (VD duyệt thực đơn còn hard violation) |
| `429` | Rate limit |
| `500` | Lỗi hệ thống không lường trước — log đầy đủ server-side, response ra ngoài chỉ có `request_id` để tra log |

---

## 6. Mapping API ↔ schema DB (`src/db/models.py`)

`User` ↔ auth · `PatientProfile`+`PatientMedication`+`PatientAllergy` ↔ `/patients/*` · `ClinicalRule` (đọc only qua `compute_targets`, không có API sửa — R2 sửa trực tiếp CSV/DB) · `MealPlan`+`MealPlanItem` ↔ `/meal-plans/*`, `/reviews/*` · `FoodLog` ↔ `/food-logs/*` · `AuditLog` ↔ `/audit` (ghi tự động trong middleware/dependency của các route approve/reject/edit, không phải route riêng để ghi).

---

## 7. Envelope response chuẩn (theo `common/patterns.md` — API Response Format)

```jsonc
// Thành công
{ "success": true, "data": { ... }, "error": null, "meta": {"total": 42, "page": 1, "page_size": 20} }
// Lỗi
{ "success": false, "data": null, "error": {"code": "VALIDATION_ERROR", "message": "...", "fields": {"age": "phải 1-120"}}, "meta": null }
```
Áp dụng qua `FastAPI` exception handler chung (`@app.exception_handler(RequestValidationError)` + `@app.exception_handler(HTTPException)`), không lặp lại ở từng route.

---

## 8. Thứ tự triển khai đề xuất (bám đường găng `docs/TICKETS.md` Phụ lục A)

1. BE-02 Auth (chặn mọi thứ sau) → 2. BE-03 Patient CRUD → 3. BE-04 Targets compute (đã có clinical engine, chỉ cần bọc route) → 4. BE-05 Seed demo (2 chuyên gia + 6 bệnh nhân) → 5. BE-06 Meal-plans (nối `build_graph()` thật) → 6. HIT-02 Reviews → 7. BE-07 Food logs (nếu còn thời gian) → 8. BE-08 Audit, BE-09 Security test.

**Phạm vi thực tế cho hạn 08/08 (2 ngày)**: ưu tiên 1→6 (đủ để demo full vòng đời "đăng ký → hồ sơ → tính định mức → sinh thực đơn → chuyên gia duyệt") — đây là *đúng lát cắt Demo Day cần*. 7-8 làm được tới đâu hay tới đó, không phải đường găng của demo.
