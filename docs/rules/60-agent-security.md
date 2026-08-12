# Rule 60 — Kiểm soát quyền hạn agent (Controlled Agent Security)

> Ticket: SEC-01. Code: `src/agents/security.py`. Red-team: `tests/test_agent_security.py`.
> Đọc cùng: `10-clinical-safety.md` (guardrail y khoa), `CLAUDE.md` §2 (ba rule đỏ).

---

## R60.0 — Điều quan trọng nhất phải hiểu trước

**RULE-1 mới là hàng rào thật, không phải prompt.**

Kể cả khi prompt injection thành công tuyệt đối, LLM ở hệ này cũng chỉ trả được
`food_id + grams` qua structured output `_LLMSelection`, và **mọi** con số dinh
dưỡng đều do Python tính lại từ SQL (`compute_nutrition()`). Injection không đổi
được một con số lâm sàng nào — nó chỉ khiến agent chọn món kém, và
`validate_menu()` chặn tiếp, rồi RULE-3 chặn lần cuối.

Vì thế: **đừng bao giờ coi câu chữ trong system prompt là cơ chế an toàn.** Nó
chỉ giúp mô hình hợp tác. Mọi ràng buộc thật phải nằm ở tầng code, kiểm được
bằng test.

Hệ quả thực tế: gặp injection thì **ghi log và chạy tiếp**, không chặn — vì hậu
quả đã bị chặn ở nơi khác, còn chặn cứng theo mẫu chuỗi sẽ tạo false positive
làm hỏng luồng. Riêng **rò rỉ secret/PII thì chặn cứng**, vì đó là loại hậu quả
không có hàng rào nào phía sau.

---

## R60.1 — Ranh giới tin cậy: cái gì là dữ liệu, cái gì là mệnh lệnh

Mọi thứ dưới đây là **DỮ LIỆU NGOÀI**, không bao giờ là mệnh lệnh:

| Nguồn | Vì sao không tin được |
|---|---|
| `food_items.name_vi`, `aliases` | ~6.900 dòng import bulk USDA + nội dung crawl web (`scripts/crawl_mnmn_dishes.py`) |
| `dishes.note` | Ghi chú crawl từ monngonmoingay.com / vietnamesecookbook.com |
| `food_logs.free_text_vi` | Bệnh nhân gõ tay |
| `guideline_chunks` (RAG, DAT-06) | Nội dung PDF ingest từ ngoài |
| Ghi chú duyệt/từ chối của chuyên gia | Người thật, nhưng vẫn là free text |

**Bắt buộc** khi đưa các nguồn trên vào prompt:
1. `sanitize_untrusted()` — làm phẳng xuống dòng/ký tự điều khiển, chuẩn hoá
   NFKC, cắt độ dài.
2. `fence(label, content)` — bọc trong khối có nhãn kèm lời dặn đây là dữ liệu.
3. `scan_for_injection()` — ghi log nếu thấy dấu hiệu.

> ⚠️ Xuống dòng là công cụ tấn công chính. Trong một prompt phẳng, `\n\n` +
> "QUY TẮC MỚI:" đọc y hệt một khối chỉ thị của hệ thống. Đây là lỗ hổng **có
> thật đã dựng lại được** ở `_candidates_text()` trước SEC-01 — xem
> `tests/test_agent_security.py::test_prompt_that_khong_con_xuong_dong_tu_ten_mon`.

---

## R60.2 — Chặn rò rỉ (secret egress) — fail closed

`assert_no_egress(prompt)` **bắt buộc** gọi trước mọi lần gửi text ra dịch vụ
ngoài. Chặn hai nhóm:

- **Secret**: Google API key, JWT, chuỗi kết nối DB, và trùng nguyên văn giá trị
  trong `Settings` (`jwt_secret`, `database_url`, `gemini_api_key`).
- **PII/PHI**: email, số điện thoại VN, CCCD/CMND, thẻ BHYT — theo `CLAUDE.md`
  §3, prompt **chỉ** được chứa tuổi, giới, cân nặng, chiều cao, mã bệnh + giai
  đoạn, chỉ số xét nghiệm, danh sách thuốc.

Hai quy tắc phụ dễ bị quên:
- **Thông điệp lỗi không được chứa chính giá trị bị phát hiện.** Lỗi đi vào log
  và trả về client — nó sẽ tự trở thành đường rò rỉ.
- **Log mẫu phải cắt ngắn.** Nội dung gây nghi ngờ có thể chính là payload chứa
  số CCCD.

---

## R60.3 — Hành động rủi ro bắt buộc có người duyệt

Khai báo trong `AGENT_ACTIONS` (`src/agents/security.py`). Ba mức:

| Mức | Nghĩa | Ví dụ |
|---|---|---|
| `LOW` | Chỉ đọc | `read_food_items`, `compute_targets` |
| `MEDIUM` | Ghi dữ liệu của chính người dùng, có audit | `generate_menu_draft`, `create_food_log` |
| `HIGH` | Ảnh hưởng lâm sàng hoặc ra ngoài hệ thống — **bắt buộc người duyệt** | `publish_meal_plan`, `resolve_food_log`, `create_food_item`, `edit_clinical_rule`, `send_external_message` |

**Hành động chưa khai báo mặc định là HIGH** (fail closed). Thêm tính năng mà
quên khai báo thì nó bị chặn, chứ không lặng lẽ chạy với quyền cao nhất.

Mọi hành động `HIGH` **phải** ghi `requires_role` — HIGH mà không nói ai được
duyệt thì cổng duyệt vô nghĩa (có test ép điều này).

---

## R60.4 — Trace để điều tra sự cố

- `SecurityIncident` ghi: lớp tấn công, nguồn, chi tiết, mẫu (**cắt 60 ký tự**),
  `trace_id`.
- Hành động `MEDIUM`/`HIGH` phải ghi `AuditLog(actor_id, action, before, after)`
  — bảng đã có sẵn ở `src/db/models.py`.
- `MealPlan.trace_id` nối ngược về LangSmith trace của lượt sinh thực đơn.

Câu hỏi phải trả lời được sau một sự cố: *ai* làm, *lúc nào*, *dữ liệu trước và
sau*, và *dòng dữ liệu ngoài nào* đã đi vào prompt.

---

## R60.5 — Attack taxonomy (dùng cho red-team)

Mỗi lớp trong `AttackClass` **phải** có ít nhất một test tấn công thật. Có test
`test_moi_lop_tan_cong_deu_co_test` ép điều đó — thêm lớp mới mà quên test thì
CI đỏ.

| Lớp | Mô tả | Kiểm ở đâu |
|---|---|---|
| `INSTRUCTION_OVERRIDE` | "bỏ qua hướng dẫn phía trên", "ignore previous instructions" | `test_agent_security.py` |
| `ROLE_HIJACK` | "bạn giờ là bác sĩ", chèn thẻ `</system>` | `test_agent_security.py` |
| `SCHEMA_ESCAPE` | Ép trả field ngoài schema (kcal, natri) | `test_agent_security.py` |
| `SECRET_EXFILTRATION` | Moi API key / JWT / chuỗi kết nối DB | `test_agent_security.py` |
| `PII_EXFILTRATION` | Moi email/CCCD/điện thoại bệnh nhân | `test_agent_security.py` |
| `CLINICAL_BOUNDARY` | Ép kê đơn/chẩn đoán/đổi thuốc | `test_guardrail.py` (AGT-07) |
| `APPROVAL_BYPASS` | Ép phát hành thực đơn chưa duyệt | `test_agent_security.py` + test RULE-3 |

**Yêu cầu chất lượng cho test red-team:** phải tấn công vào *đường đi thật của
dữ liệu*, không phải gọi hàm phòng thủ rồi tự khen. Và phải chứng minh được test
đỏ khi gỡ lớp phòng thủ ra (đã làm với `_candidates_text`).

Đối trọng bắt buộc: mỗi bộ test tấn công phải đi kèm bộ **không được báo động
giả** (`test_ten_mon_binh_thuong_khong_bi_bao_dong_gia`). False positive làm
chuyên gia mất niềm tin nhanh hơn là không cảnh báo.

---

## R60.6 — Chưa làm (ghi ra để không tưởng là đã có)

- **RAG chưa tồn tại** (DAT-06 chưa xong) — khi ingest guideline, mọi chunk phải
  đi qua R60.1 trước khi vào prompt. Đây sẽ là bề mặt injection lớn nhất.
- **Chưa có rate limit** cho `/chat` và các endpoint gọi LLM.
- **Làn B (LLM mapper cho OOV)** khi làm phải áp cùng R60.1 cho `free_text_vi`.
- **Chưa có cổng duyệt tự động hoá** — `AGENT_ACTIONS` mới là bảng khai báo;
  việc ép mọi call-site đi qua nó vẫn phải làm thủ công khi thêm endpoint.
- Ảnh đính kèm nhật ký (nếu làm) là kênh dữ liệu ngoài mới, cần rule riêng.
