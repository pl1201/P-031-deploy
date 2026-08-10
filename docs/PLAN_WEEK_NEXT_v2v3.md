# KẾ HOẠCH TUẦN TỚI (10/08–16/08) + ĐỊNH HƯỚNG V2/V3

> File đồng bộ cho **AI coding agent** và **thành viên team** — đọc file này trước khi nhận bất kỳ việc nào dưới đây, có thể làm độc lập không cần đọc lại lịch sử chat/session trước.
> Cập nhật lần cuối: 2026-08-09. Sprint hiện tại theo `docs/TICKETS.md`: **S3 (10/08–16/08)**.
> Không thay thế `docs/TICKETS.md`/`docs/PRD.md` — file này là lớp điều phối tuần, trỏ tới ticket gốc thay vì chép lại nội dung dài.

---

## 1. Trạng thái hiện tại (snapshot 2026-08-09)

| Tính năng | Trạng thái | Nhánh/PR | Ghi chú |
|---|---|---|---|
| CP-SAT / `HybridMenuGenerator` | ✅ Đã ở `main` | — | `src/agents/hybrid.py`, wired vào `generate_menu` (AGT-10) |
| Target Assistant (giải thích ngưỡng cho chuyên gia, P1) | ✅ Đã ở `main` | — | `src/services/target_assistant.py` + `src/clinical/target_explainer.py` + `src/api/routes/targets.py` |
| Thực đơn tương đương (equivalent menu, P2/AGT-12) | ✅ Đã ở `main` | — | `src/agents/equivalent.py` + `src/api/routes/equivalent.py` |
| Nhật ký ăn uống (food log, BE-07) | ✅ Đã ở `main` | — | `src/api/routes/food_logs.py` |
| DAT-26 — ViFoodRec ingest (263 món) | ⏳ Chờ review | [PR #76](https://github.com/AI20K-Build-Phase-Cohort-3/P-031/pull/76) | Chưa merge — license nguồn chưa xác nhận, `verified_by=pending` |
| Menu Explainer & Coaching — B1 (deterministic) | ⏳ Chờ review | [PR #77](https://github.com/AI20K-Build-Phase-Cohort-3/P-031/pull/77) | Chỉ phần không-LLM; B2 (LLM+route) chưa bắt đầu |
| Nghiên cứu LLM+CP-SAT (đã audit citation + TokMem/Gemma-4/VLM) | ✅ Trên `main` | — | `docs/Nghiên cứu ứng dụng LLM và CP-SAT tạo thực đơn cho người đái tháo đường.md` |

**Nếu bạn là agent/người mới nhận việc:** trước khi bắt đầu, `git fetch project main` và kiểm tra 2 PR trên đã merge chưa — nếu đã merge, bỏ bước "chờ" trong AC bên dưới.

---

## 2. Việc tuần tới — làm được ngay, độc lập

### `AGT-13` Ticket B2 — Menu Explainer LLM wording + API route
**Owner đề xuất:** R1 (LLM/agent) · **P1** · **Deps:** PR #77 merge trước
Hoàn thiện lớp Explainer & Coaching sau khi B1 (assembler + guard, PR #77) đã có: `src/services/menu_coach.py` (Gemini, theo mẫu `target_assistant.explain_naturally()`) — `explain_menu_naturally(facts: MenuFacts) -> str`, schema output không field số nào. Gọi `check_grounded()` ngay sau khi sinh; `ok=False` → dùng bản render mẫu (template) từ `MenuFacts`, không phục vụ văn bản LLM, log lại để theo dõi.
`src/api/routes/menu_explainer.py`: `GET /meal-plans/{plan_id}/explain` — role bệnh nhân (chủ hồ sơ) + chuyên gia/admin. Gate RULE-3: 409 nếu `plan.status != "approved"`, 404 nếu bệnh nhân không phải chủ hồ sơ (theo mẫu `_get_pending_plan`/`targets.py`). Response luôn có cả `facts` (structured) lẫn `text_vi` (văn xuôi).
**AC:** Test LLM "nói dối" (chèn số không có trong facts) → guard chặn + route trả fallback · Test 409/404/200 theo trạng thái plan · `pytest`/`ruff` xanh · **KHÔNG** làm coaching hỏi-đáp tự do (free-text Q&A) trong ticket này — để dành ticket sau nếu cần (CLAUDE.md §7).

### `DAT-27` Sửa lỗ hổng `load_vn_dishes()` không gate `verified_by`
**Owner đề xuất:** R2 · **P1** · **Deps:** —
Phát hiện từ DAT-26 (PR #76): `src/clinical/seeds.py::load_vn_dishes()` hiện KHÔNG gate theo `verified_by` — món `pending` vẫn được CP-SAT dùng ngay nếu đã nằm trong `dishes.csv`. Safety net thực tế chỉ dựa vào so khớp chuỗi con `"R2 cần rà"`/`"THIẾU"`/`"CHƯA GHÉP"` trong `note`, và note của cả `dishes.mnmn.csv` lẫn `dishes.vifoodrec.csv` hiện KHÔNG chứa đúng các chuỗi đó.
**AC:** `load_vn_dishes()` loại món `verified_by == "pending"` khỏi tập ứng viên CP-SAT (trừ khi có cờ rõ ràng khác đánh dấu đã duyệt) · Test hồi quy: món pending không xuất hiện trong kết quả CP-SAT · **PHẢI xong trước khi** bất kỳ nguồn `pending` nào (mnmn hiện có, vifoodrec ở PR #76) được merge vào `dishes.csv` chính.

### `DAT-26-merge` R2 rà + merge `dishes.vifoodrec.csv` vào `dishes.csv` chính
**Owner:** R2 · **P2** · **Deps:** PR #76 (đã merge), `DAT-27` (đã xong), xác nhận license ViFoodRec
Rà 263 món trong PR #76, xác nhận license repo nguồn (`github.com/QuocAn55/DS300` hiện không có LICENSE — cần liên hệ tác giả qua GitHub issue hoặc xin xác nhận pháp lý khác trước bước này). Sau khi cả 2 điều kiện đạt: merge có kiểm soát vào `dishes.csv`/`dish_ingredients.csv`, đổi `verified_by` từng món đã rà.
**AC:** Không merge hàng loạt không kiểm — mỗi món R2 xác nhận công thức hợp lý trước khi đổi `verified_by` · License đã có xác nhận bằng văn bản/email/issue link, không suy đoán.

### Đồng bộ 9 tài liệu (đang làm cùng phiên với file này)
**Owner:** R1 (điều phối) · **P2** · Xem PR "docs sync" đi kèm — không lặp lại chi tiết ở đây, chỉ liệt kê để không ai làm trùng: `ARCHITECTURE.md`, `PRD.md`, `TICKETS.md`, `LANGGRAPH_ARCHITECTURE_COMPARISON.md`, `LANGGRAPH_FLOW_OPTIMIZATION.md`, `UI_flow.md`, `JIRA_PLAN_3_WEEKS.md`+`TEAM.md`, `00_ASSESSMENT.md`, `brief.md`.

---

## 3. Định hướng V2/V3 (đặc tả trước, chưa code)

Chi tiết đầy đủ nằm ở `docs/Nghiên cứu ứng dụng LLM và CP-SAT tạo thực đơn cho người đái tháo đường.md`, mục **"Lộ Trình Model Nền & TokMem"** và mục **"Tầng thị giác/VLM"** (đã cập nhật 2026-08-09) — đây chỉ là tóm tắt điều hướng, không lặp lại nội dung.

- **Model nền local + TokMem** — R2 xác nhận dự án sẽ cần tự host local model. Bước 1 (trước): bench chọn model nền chạy được trên mobile, ứng viên hàng đầu **Gemma 4 E2B** (Apache 2.0, <1,5GB RAM, train qua Unsloth 8GB VRAM) so với Vistral/SeaLLM/PhoGPT (chuyên biệt tiếng Việt hơn nhưng không chạy mobile). Bước 2 (sau): áp **TokMem** nén các "procedure" lặp lại của Orchestrator — cần hạ tầng GPU tự host, **chưa có hạ tầng tại thời điểm này**, không bắt đầu code cho tới khi có.
- **VLM ảnh món ăn — đang đánh giá lại có điều kiện.** R2 chủ động mở lại câu hỏi "ước tính dinh dưỡng từ ảnh" (hiện ngoài MVP, CLAUDE.md §7/PRD §4.2, do MAPE đo được 35,8–110%) vì Gemma 4 E2B đa phương thức thật (nhận ảnh). Điều kiện: bench lại đúng phương pháp đo MAPE cũ với Gemma 4 E2B trước, định ngưỡng đạt/không-đạt TRƯỚC khi bench, chỉ sửa `CLAUDE.md`/`PRD` nếu đạt. **Chưa có kết quả bench — chưa đổi quyết định phạm vi.**
- **Menu Explainer & Coaching** (`AGT-13` ở trên) là bước đầu tiên khả thi ngay của "lớp 4" kiến trúc lai — không phụ thuộc hạ tầng mới, dùng Gemini hiện có.

---

## 4. Quy tắc chung khi làm việc độc lập

- **3 RULE đỏ** (chi tiết: `CLAUDE.md` §2) — RULE-1: LLM chỉ chọn `food_id`+gram, Python tính mọi số. RULE-2: mọi số hiển thị phải có `source`/`source_ref` thật. RULE-3: không có đường tắt nào đưa thực đơn chưa `approved` tới bệnh nhân.
- **Nhánh/PR:** `feature/<mã-ticket>-mô-tả-ngắn`, commit `type(scope): mô tả`, PR nhỏ (<400 dòng), ≥1 review, không push thẳng `main`/`develop`, không `--force`, không `--no-verify` (CLAUDE.md §5).
- **⚠️ Bài học phiên 2026-08-09 — xung đột nhánh đồng thời:** nhiều agent/người cùng sửa trực tiếp thư mục chính (`D:/VMEC10_P31`) gây mất đồng bộ (branch bị đổi giữa chừng bởi tiến trình khác, uncommitted changes của người khác bị đụng). **Khuyến nghị bắt buộc:** mỗi người/agent làm việc trong `git worktree` riêng (`git worktree add ../<tên> <branch>`), không sửa trực tiếp thư mục dùng chung. Trước khi rebase/push, luôn `git fetch` lại `main` mới nhất — đừng dùng ref đã cache từ đầu phiên.
- **`gh pr create` cần `--repo AI20K-Build-Phase-Cohort-3/P-031` tường minh** nếu remote `origin` của bạn trỏ tới fork cá nhân (không phải repo đội) — nếu không, lệnh báo lỗi khó hiểu ("Head sha can't be blank").

---

## 5. Bảng phân công đề xuất

| Việc | Role | Ưu tiên |
|---|---|---|
| `AGT-13` Menu Explainer B2 | R1 | P1 |
| `DAT-27` Gate `verified_by` | R2 | P1 |
| Review PR #76, #77 | R1 (agent/AGT), R2 (data/clinical) | P1 |
| `DAT-26-merge` (sau khi DAT-27 xong + license) | R2 | P2 |
| Đồng bộ 9 tài liệu | R1 điều phối, R4 review UI_flow | P2 |
| Bench Gemma 4 E2B (khi có hạ tầng GPU) | R1 + R2 (đánh giá kết quả lâm sàng) | P3, chưa có hạ tầng |
