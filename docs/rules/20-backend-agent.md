# RULE 20 — BACKEND & AGENT

> Owner: **R1** (agent) · **R3** (API/DB)

---

## A. LangGraph Agent

### R20.1 — Node phải khai báo rõ có gọi LLM hay không

Mỗi file node bắt đầu bằng docstring:

```python
"""Node: compute_nutrition
LLM: NO — deterministic, SQL only.
Input: state.draft_menu
Output: state.computed_nutrition, state.sources
"""
```

Node **không LLM**: `load_profile`, `compute_targets`, `compute_nutrition`, `validate`.
Node **có LLM**: `generate_menu`, `explain`, `decompose_dish` (OOV/mâm cơm).

### R20.2 — Structured output bắt buộc

Mọi lời gọi LLM sinh dữ liệu phải qua `with_structured_output(PydanticModel)`. Không parse JSON bằng regex, không `json.loads` trên free text.

Schema của `MenuSelection` **không được có** field nào chứa giá trị dinh dưỡng. Đây là ràng buộc thiết kế, có test kiểm tra.

### R20.3 — Retry có giới hạn và có thông tin

- Tối đa **3** lần regenerate.
- Mỗi lần retry phải đưa vào prompt **lỗi cụ thể**: chất nào, vượt bao nhiêu, do món nào.
- Hết 3 lần → fallback thực đơn mẫu theo bệnh lý + `needs_attention=true`, không được trả thực đơn vi phạm.

### R20.4 — State là nguồn sự thật duy nhất

Không dùng biến global, không cache ngoài state, không truyền dữ liệu ngầm giữa các node. Node đọc từ state và ghi vào state.

### R20.5 — Prompt sống trong file riêng, có version

`src/agents/prompts/*.py` hoặc `.md`. Mỗi prompt có comment ghi ngày sửa và lý do. Không nhúng prompt dài inline giữa logic.

### R20.6 — Prompt không chứa ngưỡng hardcode

Ngưỡng được **truyền vào** prompt từ `clinical_rules`, không viết cứng trong template. Sửa guideline không phải sửa prompt.

### R20.7 — Mọi lời gọi LLM có timeout và xử lý lỗi

Timeout 60s, retry 2 lần với backoff, lỗi cuối cùng → trả lỗi có nghĩa cho người dùng, ghi log kèm `trace_id`. Không để request treo.

### R20.8 — Tracing

Bật LangSmith với tag theo node. Mỗi lần sinh thực đơn có `trace_id` lưu vào `meal_plans` để đối chiếu khi debug.

---

## B. FastAPI

### R20.9 — Cấu trúc route

- Route chỉ làm: validate input → gọi service → format output. **Không logic nghiệp vụ trong route.**
- Nghiệp vụ ở `src/services/` hoặc `src/clinical/`.
- Truy vấn DB ở repository/service, không ở route.

### R20.10 — Phân quyền kiểm tra hai lần

Ở dependency (`require_role`) **và** ở tầng truy vấn (`WHERE patient_id = current_user.profile_id`). Không tin vào tham số từ client.

### R20.11 — Không rò rỉ sự tồn tại của bản ghi

Truy cập tài nguyên không thuộc về mình → **404**, không phải 403.

### R20.12 — Response envelope thống nhất

Mọi endpoint trả dữ liệu dinh dưỡng dùng cấu trúc `{data, sources, warnings, disclaimer}` (xem `ARCHITECTURE.md` §6). `sources` rỗng = bug, không phải trường hợp hợp lệ.

### R20.13 — Xử lý lỗi

- Exception handler toàn cục, trả JSON có `error_code`, `message`, `trace_id`.
- **Không bao giờ trả stack trace ra client.**
- Lỗi 5xx phải ghi log đầy đủ kèm `trace_id`.

### R20.14 — Bất đồng bộ

Route `async def`. Việc nặng (sinh thực đơn 7 ngày) trả `202 Accepted` + `plan_id`, client poll trạng thái. Không để request HTTP chạy quá 60 giây.

### R20.15 — Migration

Đổi model SQLAlchemy → luôn kèm Alembic migration trong cùng PR. Migration phải chạy được cả `upgrade` lẫn `downgrade`. Không sửa migration đã merge — tạo migration mới.

### R20.16 — Audit log

Ghi audit cho: sinh thực đơn, duyệt, sửa, từ chối, chuyên gia xem hồ sơ bệnh nhân, đổi `clinical_rules`. Bảng append-only, không có API xoá/sửa.

### R20.17 — Cấu hình

Mọi biến môi trường khai báo trong `src/core/config.py` với type + validation + default. Thêm biến mới → cập nhật `.env.example` trong cùng PR.

### R20.18 — Kiểm thử

- Unit test cho `src/clinical/` (coverage ≥ 80%).
- Integration test cho mọi endpoint có phân quyền.
- Test LLM dùng **mock**, không gọi API thật trong CI.
- Có ít nhất 1 test end-to-end: tạo hồ sơ → sinh thực đơn → duyệt → bệnh nhân đọc được.
