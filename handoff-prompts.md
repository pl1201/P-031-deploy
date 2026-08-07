# Handoff prompts — R1 / R3 / R4 (sau đợt API stack BE-02..HIT-02, 2026-08-06)

> Copy nguyên khối markdown của từng role, dán làm prompt đầu tiên cho agent của người đó.
> Base branch: `main` (đã đồng bộ toàn bộ tới PR #43). Không ai push thẳng `main`/`develop`.

---

## Prompt cho R1 — Tech Lead / Agent Engineer + PM

```
Bạn là R1 (Tech Lead / Agent Engineer + PM) trong đội NutriCare Agent (VMEC-10, AI20K Build Phase Cohort 3, P-031). Một phiên trước (Claude, theo yêu cầu Hưng) vừa hoàn thành toàn bộ tầng API backend (BE-02..BE-06, HIT-02) và merge vào `main`. Bạn tiếp quản phần AGENT còn thiếu.

## Bước 1 — Setup
1. `git fetch origin main && git checkout main && git pull` (repo: AI20K-Build-Phase-Cohort-3/P-031, branch chính `main`).
2. `python3.11 -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`), `pip install -r requirements.txt`.
3. `cp .env.example .env` nếu chưa có, điền `GEMINI_API_KEY` của bạn (không commit).
4. Chạy `bash scripts/setup_hooks.sh` (bắt buộc — Deliverable #4 AI Usage Logging).
5. Verify: `python3 -m pytest -q` phải ra 157/1u-cuối bằng CP-SAT (không cần LLM) lẫn Gemini thật.
5. `docs/TICKETS.md` mục EPIC 3 (AGT-01..AGT-10, đã đọc xong hầu hết) và EPIC 5 (HIT-01, HIT-05).
6. `DEVLOG.md` — đọc entry cuối cùng "[2026-08-06] · Claude · Thiết kế API stack..." để biết chính xác BE-06 đã nối graph vào API như thế nào (background task, không dùng `interrupt()` thật của LangGraph — status quản ở tầng DB).
57 pass. Nếu không, dừng lại và báo — đừng code tiếp trên nền chưa xanh.

## Bước 2 — Đọc trước khi code (bắt buộc, theo đúng thứ tự)
1. `CLAUDE.md` §1-§6 — đặc biệt 3 RULE đỏ (§2): LLM chỉ chọn món, mọi số tính bằng Python; không số nào thiếu nguồn; không đường tắt tới bệnh nhân.
2. `docs/ARCHITECTURE.md` — luồng graph 8 node, ERD.
3. `docs/API_DESIGN.md` — API stack vừa xây, đặc biệt mục `POST /meal-plans` (BE-06) và cách nó gọi `build_nutricare_graph()` qua background task — bạn sẽ sửa/mở rộng đúng chỗ này.
4. `src/agents/graph.py`, `src/agents/nodes/core.py`, `src/agents/assembly.py`, `src/agents/state.py` — code hiện có, đã chạy được đầ
## Bước 3 — Skill có sẵn nên dùng
- Skill `langgraph-node` — khi thêm/sửa node, tool, edge trong graph.
- Skill `menu-safety-check` — BẮT BUỘC chạy trước khi coi bất kỳ thay đổi nào ở guardrail/validator/agent là xong, kể cả chỉ để tự kiểm tra.
- Skill `ticket-workflow` — quy trình chuẩn: branch → code+test → PR → DEVLOG.

## Bước 4 — Nhiệm vụ (theo thứ tự ưu tiên, xem AC gốc trong docs/TICKETS.md)
1. **AGT-07 — Guardrail chặn chỉ định y khoa (P0, chưa có code nào, ưu tiên cao nhất).** Regex tiếng Việt + LLM classifier tầng 2. Route `POST /api/v1/chat` hiện đang trả 501 stub — đây là chỗ AC yêu cầu nối vào. ≥95% chặn đúng trên 20 câu red-team, false positive <10%. Test riêng `tests/unit/test_guardrail.py`.
2. **HIT-01 — Đánh giá lại quyết định "không dùng interrupt() thật".** Graph hiện HỖ TRỢ `interrupt_before=["to_review"]` qua checkpointer (đã build sẵn trong `build_graph()`), nhưng API (BE-06) đang bỏ qua cơ chế này, tự quản trạng thái `pending_review`/`approved` ở tầng DB (đơn giản hơn, không cần Postgres checkpointer). Bạn quyết định: giữ nguyên cách này (ghi ADR vào DEVLOG giải thích tại sao đủ tốt) HAY chuyển sang dùng `interrupt()` thật + `PostgresSaver` (phức tạp hơn, cần deploy Postgres — phối hợp với R3). Đừng tự đổi khi chưa cân nhắc kỹ, đây là quyết định kiến trúc.
3. **AGT-08 — LangSmith tracing (P2, làm sau nếu còn thời gian).** Bật tracing, gắn tag theo node, log chi phí — cần cho Deliverable #4 và slide Q&A "chi phí trung bình/thực đơn".
4. **AGT-03 phần RAG còn thiếu:** `retrieve_context` hiện chỉ lọc SQL theo dị ứng/bệnh lý (đã xong), CHƯA có phần Hybrid RAG (BM25 + vector) vì `DAT-06` (ingest guideline vào `guideline_chunks`) chưa làm — đây là việc của R2, không phải bạn, nhưng nếu ai đó làm DAT-06 xong thì bạn nối tiếp phần retrieval.

## Bước 5 — Trước khi code: brainstorm/phản biện với đội
Đừng tự quyết một mình các điểm sau — nêu ra trong group/standup trước khi code:
- Guardrail dùng LLM classifier nào (Gemini có sẵn, hay model nhỏ hơn cho rẻ/nhanh)? Ai cũng nên xem qua bộ 20 câu red-team trước khi chốt regex.
- Quyết định HIT-01 (giữ đơn giản vs. interrupt thật) ảnh hưởng trực tiếp tới việc R3 có cần deploy Postgres checkpointer hay không — bàn với R3 trước khi chốt.
- Sau khi xong AGT-07/HIT-01, đề xuất kế hoạch tuần tới (EPIC 7 — ADV-01 "phân rã mâm cơm gia đình" là tính năng khác biệt nhất dự án, nên bàn sớm về scope) cho cả đội duyệt, không tự ý mở rộng phạm vi một mình.

## Quy tắc git (bắt buộc)
Branch `feature/AGT-07-guardrail` (hoặc mã ticket tương ứng) từ `main`. PR nhỏ <400 dòng, có test, `ruff check`+`mypy src/`+`pytest -q` xanh trước khi mở PR. Không `--force`, không `--no-verify`. Ghi 1 dòng DEVLOG cuối phiên.
```

---

## Prompt cho R3 — Backend Engineer + DevOps

```
Bạn là R3 (Backend Engineer + DevOps) trong đội NutriCare Agent (VMEC-10, AI20K Build Phase Cohort 3, P-031). Một phiên trước (Claude, theo yêu cầu Hưng) vừa xây xong tầng API core (BE-02..BE-06, HIT-02) và merge vào `main`, ĐÃ verify Docker build+run local thành công nhưng CHƯA deploy lên Render/Vercel/Neon thật (không có credential). Bạn tiếp quản đúng chỗ này.

## Bước 1 — Setup
1. `git fetch origin main && git checkout main && git pull`.
2. `python3.11 -m venv .venv && source .venv/bin/activate`, `pip install -r requirements.txt`.
3. `cp .env.example .env`, điền key của bạn.
4. `bash scripts/setup_hooks.sh`.
5. `python3 -m pytest -q` → phải 157/157 pass trước khi động tay vào gì.
6. `python3 scripts/seed_demo_users.py` sau `python3 scripts/seed_db.py` (hoặc `make seed && make seed-demo-users`) để có sẵn 2 chuyên gia + 6 bệnh nhân demo test API (bảng tài khoản trong README.md mục "Tài khoản demo", mật khẩu chung `Demo1234`).

## Bước 2 — Đọc trước khi code
1. `CLAUDE.md` §2 (3 rule đỏ), §4 (quy tắc code — cấm `except:` trần, cấm `print()`, secret chỉ qua `src/config.py`).
2. `docs/API_DESIGN.md` — đọc TOÀN BỘ, đây là hợp đồng API bạn phải tuân theo khi thêm BE-07/08/09.
3. `src/api/routes/` (đã tách thành package theo resource: `auth.py`, `patients.py`, `targets.py`, `meal_plans.py`, `reviews.py`, `misc.py`) và `src/api/security.py` (JWT+argon2id), `src/api/clinical_bridge.py` — hiểu pattern trước khi thêm route mới, đi đúng convention đã có (chặn quyền ở TẦNG QUERY, không lọc sau khi query — xem `_get_owned_profile` trong `patients.py` làm mẫu).
4. `tests/conftest.py` — fixture `client`/`db_session` (SQLite in-memory qua `StaticPool`, override `get_db`). Dùng lại đúng pattern này cho test mới, đừng tự nghĩ ra cách khác.
5. `Dockerfile`, `render.yaml`, `DEVLOG.md` entry cuối cùng — mục "Docker: build local thành công... /health trả 200" để biết đã verify tới đâu.
6. `docs/TICKETS.md` EPIC 4 (BE-07/08/09) và §5 (`SET-05` deploy — đã có `render.yaml` sẵn, chưa từng connect thật).

## Bước 3 — Nhiệm vụ (theo thứ tự ưu tiên)
1. **Deploy thật lên Render + Vercel + Neon (ưu tiên cao nhất — chưa ai làm được vì thiếu credential).**
   - Backend: Render, Docker, dùng `render.yaml` có sẵn. Set secrets thật trên dashboard Render (không commit): `DATABASE_URL` (Neon Postgres), `GEMINI_API_KEY`, `JWT_SECRET` (đổi khỏi giá trị dev mặc định trong `src/config.py`!), `CORS_ORIGINS`.
   - DB: Neon/Supabase Postgres + `pgvector`. Chạy `alembic upgrade head` rồi `make seed && make seed-demo-users` trên DB thật.
   - Verify: `GET /health` trả 200 công khai, cập nhật README mục "Live URL".
2. **BE-09 — Security test tự động (P0).** Test cho MỌI endpoint có dữ liệu bệnh nhân: bệnh nhân A gọi tài nguyên B → 404 (pattern đã có sẵn ở `_get_owned_profile`/`_get_visible_plan`, viết test bao phủ đủ, thêm `gitleaks` vào CI).
3. **BE-08 phần còn thiếu — `GET /audit` (admin only).** `AuditLog` đã được ghi tự động trong `reviews.py` (approve/reject) — chỉ thiếu route đọc. Không có API sửa/xoá (đã đúng theo thiết kế, đừng thêm).
4. **BE-07 — API nhật ký ăn uống (`food_logs`).** Bảng `FoodLog` đã có sẵn trong `src/db/models.py`. `food_id` có thể null khi bệnh nhân gõ tự do (OOV, CLN-07 — CLN-07 CHƯA làm, nên tạm thời route này nên trả lỗi rõ ràng khi thiếu `food_id`, đừng tự suy đoán dinh dưỡng — xem cách `reviews.py` xử lý tương tự).

## Bước 4 — Trước khi code: brainstorm/phản biện với đội
- Deploy Postgres schema thật: bàn với R1 trước — nếu R1 quyết định dùng `interrupt()` thật cho HIT-01 thì bạn cần `PostgresSaver` checkpointer, ảnh hưởng cấu hình DB. Đừng deploy xong rồi mới biết phải đổi.
- `JWT_SECRET` production: đề xuất cách generate/lưu an toàn (Render env var, không hardcode) — thông báo cho cả đội biết secret ở đâu để không ai tự ý đổi.
- Sau khi deploy xong, đề xuất checklist DEL-06 (kiểm tra cuối trước nộp) cho cả đội cùng rà, không tự ý coi là xong một mình.

## Quy tắc git (bắt buộc)
Branch theo mã ticket từ `main`. PR nhỏ, có test, `ruff check`+`mypy src/`+`pytest -q` xanh. Không `--force`/`--no-verify`. Deploy secrets KHÔNG BAO GIỜ commit vào repo dù là `.env.example`. Ghi DEVLOG cuối phiên + cập nhật README Live URL khi deploy xong.
```

---

## Prompt cho R4 — Frontend Engineer + Deliverables

```
Bạn là R4 (Frontend Engineer + Deliverables) trong đội NutriCare Agent (VMEC-10, AI20K Build Phase Cohort 3, P-031). Toàn bộ backend (auth, hồ sơ bệnh nhân, tính định mức, sinh thực đơn, hàng chờ duyệt chuyên gia) đã xong và deploy-ready trên `main` — bạn là người XÂY GIAO DIỆN ĐẦU TIÊN cho dự án này, EPIC 6 hiện là 0%.

## Bước 1 — Setup
1. `git fetch origin main && git checkout main && git pull`.
2. Backend: `python3.11 -m venv .venv && source .venv/bin/activate`, `pip install -r requirements.txt`, `cp .env.example .env` (điền key), `bash scripts/setup_hooks.sh`.
3. `python3 -m pytest -q` → 157/157 pass.
4. `make seed && make seed-demo-users`, `make run` (hoặc `uvicorn src.main:app --reload --port 8000`) → Swagger UI tại `http://localhost:8000/docs`, thử đăng nhập bằng tài khoản demo trong README (`dietitian1@nutricare.demo` / `Demo1234`, `patient1@nutricare.demo` / `Demo1234`...) để hiểu luồng API thật trước khi code UI.
5. Frontend: tạo mới `web/` (Next.js App Router) — CHƯA có sẵn, bạn là người khởi tạo.

## Bước 2 — Đọc trước khi code
1. `CLAUDE.md` §2 (RULE-2 đặc biệt quan trọng cho UI: mọi số dinh dưỡng hiển thị phải kèm nguồn `source`/`source_ref` — xem AC gốc FE-03 "Bấm vào món hiện popup 'Gạo tẻ · NIN · Bảng TPTP VN, tr.42'"), §3 (ranh giới an toàn y tế — copy/UI không bao giờ được viết "thay thế bác sĩ").
2. `docs/API_DESIGN.md` — TOÀN BỘ, đây là hợp đồng bạn gọi từ frontend. Đặc biệt §3 (auth: Bearer JWT, access token 15 phút — cần xử lý refresh), §7 (chưa áp dụng envelope response chuẩn thực tế, response hiện tại là Pydantic model trực tiếp — kiểm tra qua Swagger `/docs` để biết đúng shape thật).
3. `docs/TEAM.md` §2 (mô tả vai trò R4), `docs/TICKETS.md` EPIC 6 (FE-01..FE-08) — đọc kỹ AC từng ticket.
4. `README.md` — bảng tài khoản demo, mục "Tech Stack" (Next.js, chưa chọn UI library — bạn tự quyết, đề xuất trong PR đầu).
5. Gọi thử API thật qua Swagger (`/docs`) hoặc `curl` để hiểu response thật của `POST /meal-plans` (trả `202` ngay, phải poll `GET /meal-plans/{id}` để biết khi nào xong — đây là điểm dễ làm sai nếu chỉ đọc doc mà không thử thật).

## Bước 3 — Nhiệm vụ (theo thứ tự ưu tiên, đường găng dự án)
1. **FE-01 — Khung app + Auth UI (P0, chặn mọi FE khác).** Next.js App Router, layout theo role (patient/dietitian), login/logout, lưu token an toàn (không localStorage cho refresh token nếu tránh được XSS — cân nhắc httpOnly cookie qua BFF route của Next.js), route guard.
2. **FE-02 — Form hồ sơ bệnh nhân**, gọi `POST/PUT /api/v1/patients`.
3. **FE-03 — Màn hình thực đơn**, gọi `POST /meal-plans` + poll `GET /meal-plans/{id}`. Chip nguồn bấm được cho từng món (RULE-2 — dữ liệu `source`/`source_ref` đã có sẵn trong response, không phải tự bịa).
4. **HIT-03 — Dashboard duyệt thực đơn (P0, phụ thuộc FE-01+HIT-02 đã có API)**, gọi `GET /reviews/pending`, `POST /reviews/{id}/approve` (kèm sửa gram — UI cần cho chuyên gia sửa số trực tiếp, gọi lại API để lấy dinh dưỡng tính lại từ server, KHÔNG tự tính ở client).
5. FE-04..FE-08 làm sau theo thời gian còn lại.

## Bước 4 — Trước khi code: brainstorm/phản biện với đội
- Chọn UI library (shadcn/ui, MUI, Tailwind thuần...) — đề xuất trong group trước khi cài, tránh phải đổi giữa chừng.
- Cách xử lý polling cho `POST /meal-plans` (202 async) — bàn với R1/R3 xem có nên thêm WebSocket/SSE không, hay polling đơn giản là đủ cho demo (khuyến nghị: polling đủ cho MVP, đừng over-engineer).
- Sau FE-01/FE-03/HIT-03 xong (đủ để demo full luồng), đề xuất với cả đội việc tiếp theo — DEL-03 (video demo) cần chính bạn dựng kịch bản, nên bàn sớm ai đóng vai bệnh nhân/chuyên gia trong video.

## Quy tắc git (bắt buộc)
Branch `feature/FE-01-...` từ `main`. Frontend code trong `web/`. PR nhỏ, README/screenshot cập nhật khi có UI chạy được. Không `--force`/`--no-verify`. Ghi DEVLOG cuối phiên.
```
