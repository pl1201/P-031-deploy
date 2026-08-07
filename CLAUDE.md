# CLAUDE.md — Quy tắc cho AI coding agent trên dự án này

> File này được Claude Code / Cursor / Codex / Gemini CLI đọc tự động ở mỗi phiên.
> Người cũng nên đọc. Đây là hợp đồng chung của cả đội.
> Rule chi tiết theo lĩnh vực nằm trong `docs/rules/`.

---

## 1. Dự án này là gì

**NutriCare Agent (VNutriCare)** — AI Agent dinh dưỡng lâm sàng, **trọng tâm MVP là bệnh nhân đái tháo đường type 2 (ĐTĐ2)** tại Việt Nam. Đề bài VMEC-10, chương trình AI20K Build Cohort 3, thời hạn 6 tuần.

> ⚠️ **Đổi phạm vi (2026-08-06):** MVP sử dụng dữ liệu thực tế NHANES 2021-2023 (de-identified, public-use) thay vì dữ liệu mô phỏng, theo `docs/PRD.md` v2.2. Dữ liệu tuân thủ NCHS Data User Agreement. Rule/code cho CKD, gout, tăng huyết áp **vẫn giữ nguyên và tiếp tục hoạt động** — cơ chế phát hiện xung đột đa bệnh lý (`compute_targets()`, DEC-007) **KHÔNG bị thu hẹp**. Khi viết ticket/code mới, ưu tiên đường găng ĐTĐ2 trước cho tính năng mới.

Stack: **FastAPI + LangGraph + PostgreSQL/pgvector + Next.js**, deploy Render + Vercel.

Đọc trước khi làm bất cứ việc gì: `docs/PRD.md` (nguồn phạm vi/tính năng chính thức), `docs/00_ASSESSMENT.md`, `docs/PLAN.md`, `docs/ARCHITECTURE.md`.

---

## 2. Ba quy tắc không bao giờ được vi phạm

### 🔴 RULE-1: LLM chọn món — Python tính số

LLM **chỉ** được trả về `food_id`/`dish_id` và số gram. Mọi giá trị kcal, protein, natri, kali, phospho, purine, đường **phải** được tính bằng truy vấn SQL vào `food_items`.

```python
# ❌ TUYỆT ĐỐI KHÔNG
menu = llm.invoke("Lập thực đơn 1800 kcal và cho biết tổng natri")

# ✅ ĐÚNG
selection = llm.with_structured_output(MenuSelection).invoke(prompt)  # chỉ food_id + grams
nutrition = compute_nutrition(selection)  # SQL, deterministic
```

Vi phạm rule này = PR bị từ chối, không thương lượng. CI có test tự động chặn (`EVL-03`).

### 🔴 RULE-2: Không con số nào không có nguồn

Mọi giá trị dinh dưỡng hiển thị cho người dùng phải kèm `source` (`NIN` / `USDA` / `estimated`) và `source_ref`. Món ước tính phải gắn `is_estimated=true` + `confidence`, và UI phải hiển thị nhãn "ước tính".

Nếu không tra được nguồn: **nói không biết**, đừng đoán.

### 🔴 RULE-3: Không có đường tắt tới bệnh nhân

Không viết bất kỳ code path nào cho phép thực đơn ở trạng thái khác `approved` đến được bệnh nhân — qua API, qua UI, qua email, qua export. Chuyên gia là chốt chặn cuối cùng và bắt buộc.

---

## 3. Ranh giới an toàn y tế

Hệ thống này **không được**:
- Chẩn đoán bệnh
- Kê đơn, gợi ý liều, hay khuyên ngừng/đổi thuốc
- Diễn giải kết quả xét nghiệm thành kết luận y khoa
- Nói "thay thế bác sĩ" ở bất kỳ đâu trong copy/UI

Khi người dùng hỏi những điều trên → guardrail tầng 1 trả về câu trả lời chuẩn (xem `docs/rules/10-clinical-safety.md`) và đề xuất chuyển câu hỏi cho chuyên gia.

**Dữ liệu:** Sử dụng dữ liệu thực tế đã được de-identified từ NHANES 2021-2023 cho phát triển và kiểm thử. Dữ liệu tuân thủ NCHS Data User Agreement và chỉ dùng cho mục đích nghiên cứu/phân tích thống kê. Không đưa SEQN hoặc thông tin định danh cá nhân vào prompt LLM.

**Prompt gửi LLM:** chỉ tuổi, giới, cân nặng, chiều cao, mã bệnh + giai đoạn, chỉ số xét nghiệm, danh sách thuốc. **Không** tên, email, số điện thoại, CCCD, địa chỉ.

---

## 4. Quy tắc code

| Chủ đề | Quy tắc |
|---|---|
| Python | 3.11+, type hints **bắt buộc** trên mọi hàm public |
| Format/Lint | `ruff` — chạy `make check` trước khi commit |
| Exception | **Cấm `except:` và `except Exception:` trần.** Bắt đúng loại lỗi, log, re-raise nếu không xử lý được |
| Secrets | Chỉ qua `src/core/config.py` (pydantic-settings). Cấm hardcode, cấm `os.getenv()` rải rác |
| Logging | Dùng logger có sẵn. **Cấm `print()`.** Không log PII/PHI |
| Validation | Pydantic cho mọi ranh giới vào/ra |
| Async | Route FastAPI dùng `async def`; I/O blocking đưa vào threadpool |
| Test | Logic mới phải có test. `src/clinical/` yêu cầu coverage ≥ 80% |
| Migration | Đổi schema → luôn kèm Alembic migration trong cùng PR |
| Docstring | Hàm lâm sàng phải ghi công thức + nguồn guideline |

**Không được import LLM client trong:** `src/clinical/**`, `src/agents/nodes/compute_*.py`, `src/agents/nodes/validate.py`. Có test kiểm tra điều này.

---

## 5. Git

- Branch: `feature/<mã-ticket>-mô-tả-ngắn` (VD `feature/AGT-04-generate-menu`)
- Commit: `type(scope): mô tả` — `feat|fix|docs|test|refactor|chore`, scope = `agent|api|clinical|web|data|ops`
- Mỗi commit nên tham chiếu mã ticket: `feat(clinical): thêm bounds checker (CLN-04)`
- PR: nhỏ (<400 dòng), có mô tả + cách test, ≥1 review
- **Không push thẳng `main`/`develop`. Không `--force`. Không `--no-verify`.**

---

## 6. Hướng dẫn cho AI agent khi được giao việc

Khi được yêu cầu implement một ticket:

1. **Đọc ticket trong `docs/TICKETS.md`** — dùng đúng mã ticket, đúng acceptance criteria.
2. **Kiểm tra 3 rule đỏ ở §2** có liên quan không. Nếu task đụng tới con số dinh dưỡng, dừng lại và xác nhận con số đến từ SQL.
3. **Xem `docs/rules/`** cho lĩnh vực tương ứng.
4. Viết code + test cùng lúc, không hứa "test sau".
5. Chạy `make check` trước khi báo xong.
6. **Đề xuất 1 dòng cho `DEVLOG.md`** cuối mỗi phiên làm việc.

Khi phát hiện yêu cầu mâu thuẫn với rule an toàn (VD: "cho LLM tự tính calo cho nhanh") → **nói thẳng là không nên và giải thích lý do**, đừng lặng lẽ làm theo.

Khi không chắc về một ngưỡng lâm sàng → **hỏi R2**, đừng tự đặt số. Ngưỡng sai trong hệ thống y tế không phải là bug thường.

---

## 7. Những gì KHÔNG làm ở phiên bản này

Đừng tự ý thêm (đã được quyết định cắt scope, xem `00_ASSESSMENT.md` §9):
- Computer vision / OCR nhận diện ảnh món ăn
- Neo4j / knowledge graph
- Kubernetes, Terraform
- Vector DB ngoài (Qdrant, Milvus, Pinecone)
- Fine-tuning
- Multi-tenant, tích hợp HIS/EMR
- Bất kỳ dependency mới nào không được thảo luận trong PR

Thêm dependency mới cần lý do trong PR description và được R1 hoặc R3 đồng ý.

**Ranh giới bệnh lý (từ `docs/PRD.md` v2.1 §4.2, đã làm rõ thêm — xem DEVLOG DEC-014):**
- Không xây **tính năng mới** chuyên biệt để điều trị CKD, gout, tăng huyết áp nặng trong phạm vi MVP — đây là "không mục tiêu" cho công sức phát triển mới, ưu tiên dồn vào ĐTĐ2.
- **Cơ chế đa bệnh lý hiện có (`compute_targets()`, DEC-007) giữ nguyên, không thu hẹp:** hồ sơ có bệnh đồng mắc vẫn được tính ngưỡng bình thường (lấy ngưỡng chặt hơn); chỉ gắn `needs_expert_review` khi rule thật sự **xung đột** (min > max, hoặc dải quá hẹp) hoặc rule bị vô hiệu bởi cờ an toàn — **không** gắn cờ cho mọi ca đồng mắc. Đã đối chiếu `KeHoachDuAn_VNutriCare_VMEC10_v3.docx` mục 6.4.1 và xác nhận đây đúng là đặc tả gốc.
- Không diễn giải "trọng tâm ĐTĐ2" thành "tắt/xoá code CKD/gout/THA" — cơ chế này là điểm khác biệt cạnh tranh, không phải nợ kỹ thuật cần dọn.

---

## 8. Tra cứu nhanh

| Cần gì | Xem đâu |
|---|---|
| Phạm vi sản phẩm, tính năng, không-mục-tiêu | `docs/PRD.md` (v2.2 — dữ liệu NHANES, trọng tâm ĐTĐ2) |
| Kiến trúc, luồng graph, schema DB, API | `docs/ARCHITECTURE.md` |
| Việc của tôi tuần này | `docs/TICKETS.md` + `docs/PLAN.md` §4 |
| Ai duyệt PR của tôi | `docs/TEAM.md` §4 + `.github/CODEOWNERS` |
| Rule an toàn lâm sàng | `docs/rules/10-clinical-safety.md` |
| Rule backend / agent | `docs/rules/20-backend-agent.md` |
| Rule frontend | `docs/rules/30-frontend.md` |
| Rule dữ liệu & RAG | `docs/rules/40-data-rag.md` |
| Quy trình làm việc | `docs/rules/50-workflow.md` |
| Ghi log hằng ngày | `DEVLOG.md` |
