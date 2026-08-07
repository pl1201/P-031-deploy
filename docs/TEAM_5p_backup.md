# TEAM — PHÂN VAI, PHÂN QUYỀN & TRÁCH NHIỆM

> Điền tên thật vào cột "Thành viên" ngay buổi họp đầu tiên rồi commit file này.

---

## 1. Bảng phân vai

| Mã | Vai trò | Thành viên | Sở hữu module | Backup bởi |
|---|---|---|---|---|
| **R1** | Tech Lead / Agent Engineer | `…` | `src/agents/`, guardrails, prompt, LangGraph | R3 |
| **R2** | Clinical & Data Engineer | `…` | `src/clinical/`, `src/rag/`, `data/`, seeds | R1 |
| **R3** | Backend Engineer | `…` | `src/api/`, `src/db/`, auth, RBAC, audit | R1 |
| **R4** | Frontend Engineer | `…` | `web/`, UI 2 vai trò, HITL dashboard | R5 |
| **R5** | DevOps / QA / PM | `…` | Docker, CI/CD, deploy, tests, eval, deliverables | R3 |

### Nếu đội ít hơn 5 người

| Số người | Gộp vai |
|---|---|
| 4 | R5 chia đôi: DevOps→R3, QA/PM→R1 |
| 3 | R1+R2 (một người lo AI+dữ liệu), R3+R5, R4 giữ nguyên |
| 6 | Tách R2 thành R2a (clinical rules) và R2b (data ETL + RAG) |

> Mỗi module phải có **đúng 1 owner**. "Cả nhóm cùng làm" = không ai làm.

---

## 2. Mô tả trách nhiệm chi tiết

### R1 — Tech Lead / Agent Engineer
**Trách nhiệm chính:** LangGraph graph, node, tool, prompt, guardrails tầng 1–2, retry loop, LangSmith tracing.
**Cũng chịu trách nhiệm:** chốt tranh luận kỹ thuật (sau 15 phút bàn không xong thì R1 quyết), review mọi PR chạm `src/agents/`, giữ `ARCHITECTURE.md` cập nhật.
**Không được làm:** viết logic tính toán dinh dưỡng (đó là của R2) — để tránh trộn LLM vào con số.
**Đầu ra tuần 3:** agent sinh được thực đơn pass validator ≥70% lần đầu.

### R2 — Clinical & Data Engineer
**Trách nhiệm chính:** bảng thực phẩm, món ăn, `clinical_rules`, drug–food, OOV estimator, RAG ingestion, bộ eval 60 case.
**Cũng chịu trách nhiệm:** **verify từng số liệu y khoa** trước khi lên slide (`REFERENCES.md`); liên hệ chuyên gia dinh dưỡng để review.
**Vai trò đặc biệt:** R2 là người duy nhất được quyền thêm/sửa ngưỡng lâm sàng. Mọi PR chạm `src/clinical/` hoặc `data/seeds/` **bắt buộc** R2 review.
**Đầu ra tuần 2:** 200 thực phẩm + 50 món + rules cho 4 nhóm bệnh, có nguồn từng dòng.

### R3 — Backend Engineer
**Trách nhiệm chính:** FastAPI routes, Pydantic schemas, SQLAlchemy models, Alembic, JWT auth, RBAC, audit log, error handling.
**Cũng chịu trách nhiệm:** hợp đồng API (giữ `ARCHITECTURE.md` §6 đúng thực tế), Swagger sạch, không endpoint nào rò dữ liệu chéo bệnh nhân.
**Đầu ra tuần 2:** auth + profile + targets API chạy, có integration test.

### R4 — Frontend Engineer
**Trách nhiệm chính:** Next.js, 2 portal riêng biệt, form hồ sơ, hiển thị thực đơn kèm nguồn, dashboard duyệt, nhật ký ăn uống, biểu đồ, dark mode, responsive.
**Cũng chịu trách nhiệm:** disclaimer hiển thị đúng chỗ; cảnh báo dị ứng/tương tác phải nổi bật (badge đỏ, không phải chữ nhỏ); **screenshot mọi màn hình** cho README và pitch.
**Đầu ra tuần 4:** demo 2 tài khoản chạy trên Live URL.

### R5 — DevOps / QA / PM
**Trách nhiệm chính:** Dockerfile, docker-compose, GitHub Actions, deploy Render+Vercel, quản lý secrets, structured logging.
**Cũng chịu trách nhiệm:** theo dõi 10 deliverables (chủ sở hữu bảng checklist), nhắc DEVLOG, chạy eval, quay video, ghép pitch deck, canh code freeze.
**Quyền đặc biệt:** R5 được quyền **chặn merge** nếu CI đỏ hoặc thiếu test, kể cả PR của Tech Lead.
**Đầu ra tuần 1:** Live URL hello-world + CI xanh + hooks AI logging đã cài.

---

## 3. Ma trận RACI

`R` = Người làm · `A` = Người chịu trách nhiệm cuối · `C` = Được hỏi ý kiến · `I` = Được thông báo

| Hạng mục | R1 | R2 | R3 | R4 | R5 |
|---|:-:|:-:|:-:|:-:|:-:|
| Kiến trúc hệ thống | **A/R** | C | C | I | C |
| Ngưỡng & quy tắc lâm sàng | C | **A/R** | I | I | I |
| Dữ liệu thực phẩm & nguồn | I | **A/R** | C | I | I |
| LangGraph & prompt | **A/R** | C | C | I | I |
| Guardrails tầng 1–2 | **A/R** | C | C | I | C |
| Guardrails tầng 3 (validator) | C | **A/R** | C | I | C |
| Luồng HITL (backend) | C | I | **A/R** | C | I |
| Luồng HITL (UI) | C | C | C | **A/R** | I |
| Auth / RBAC / bảo mật | C | I | **A/R** | C | C |
| Schema DB & migration | C | C | **A/R** | I | I |
| Frontend & UX | I | I | C | **A/R** | C |
| Docker / CI / Deploy | I | I | C | C | **A/R** |
| Bộ eval & báo cáo | C | **R** | I | I | **A** |
| 10 Deliverables | I | I | I | C | **A/R** |
| Pitch deck & video | C | C | C | **R** | **A** |
| DEVLOG | R | R | R | R | **A** |

**Đọc bảng:** cột có **A** là người bị hỏi khi hạng mục đó hỏng. Không có ô nào hai chữ A.

---

## 4. Phân quyền kỹ thuật (thực thi bằng công cụ, không bằng lời hứa)

### GitHub

| Quyền | Ai |
|---|---|
| Admin repo | R1, R5 |
| Write | tất cả |
| Merge vào `main` | chỉ R5 (sau khi R1 duyệt) |
| Merge vào `develop` | bất kỳ ai, sau ≥1 review |
| Force push | **không ai** |

**Branch protection cho `main` và `develop`:**
- [x] Require pull request before merging
- [x] Require ≥ 1 approval
- [x] Require status checks: `lint`, `test`, `build`
- [x] Do not allow bypassing

### CODEOWNERS

Tạo file `.github/CODEOWNERS`:

```
# Mặc định
*                       @tech-lead

# Lâm sàng — bắt buộc R2 duyệt, đây là nơi sai sót gây hại thật
/src/clinical/          @clinical-eng @tech-lead
/data/seeds/            @clinical-eng
/eval/datasets/         @clinical-eng

/src/agents/            @tech-lead
/src/api/  /src/db/     @backend-eng
/web/                   @frontend-eng
/.github/  /Dockerfile  @devops-qa
/docs/                  @devops-qa @tech-lead
```

### Secrets & môi trường

| Bí mật | Ai giữ | Lưu ở đâu |
|---|---|---|
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | R5 | Render env + GitHub Secrets |
| `DATABASE_URL` (prod) | R5, R3 | Render env |
| `JWT_SECRET` | R5 | Render env |
| `AI_LOG_API_KEY` | R5 | `.env` local từng người |
| `LANGSMITH_API_KEY` | R1, R5 | Render env |

> ⚠️ Ai commit secret vào repo: revoke key ngay, `git filter-repo`, và ghi vào DEVLOG như một sự cố. Không giấu.

### Quyền trong sản phẩm (RBAC ứng dụng)

| Hành động | patient | dietitian | admin |
|---|:-:|:-:|:-:|
| Xem hồ sơ của mình | ✅ | ✅ | ✅ |
| Xem hồ sơ bệnh nhân khác | ❌ | ✅ (được phân công) | ✅ |
| Yêu cầu sinh thực đơn | ✅ | ✅ | ✅ |
| Xem thực đơn `pending_review` | ❌ | ✅ | ✅ |
| Duyệt / sửa / từ chối thực đơn | ❌ | ✅ | ✅ |
| Ghi nhật ký ăn uống | ✅ | ❌ | ✅ |
| Sửa `clinical_rules` | ❌ | ❌ | ✅ |
| Xem audit log | ❌ | phần liên quan | ✅ |

**Test bảo mật bắt buộc (ticket BE-09):** đăng nhập bằng bệnh nhân A, gọi `GET /meal-plans/{id_của_B}` → phải trả **404** (không phải 403, để không lộ sự tồn tại của bản ghi).

---

## 5. Quy tắc làm việc nhóm

1. **Không push thẳng lên `main`/`develop`.** Không ngoại lệ, kể cả "sửa 1 dòng".
2. **PR nhỏ.** Trên 400 dòng thay đổi thì tách. PR to không ai review thật, chỉ bấm Approve cho xong.
3. **Review trong 12 giờ.** Nếu quá 12 giờ chưa ai review, tag trực tiếp trong nhóm chat.
4. **Không sửa file của người khác mà không báo.** Nếu cần, comment trong PR hoặc nhắn owner.
5. **Vướng quá 90 phút phải kêu cứu.** Ngồi im 2 ngày với 1 bug là thiệt hại của cả đội, không phải chuyện cá nhân.
6. **Ghi DEVLOG cuối mỗi buổi làm.** Không có ngoại lệ — đây là 2 deliverable.
7. **Tranh luận kỹ thuật tối đa 15 phút.** Sau đó R1 quyết, ghi lý do vào DEVLOG dạng ADR. Có thể quay lại xem xét sau, nhưng không tranh luận tiếp trong hôm nay.
8. **Ai làm phần nào thì demo phần đó** ở buổi demo nội bộ tối thứ 7.

---

## 6. Ai thuyết trình Demo Day

| Phần | Slide | Người nói | Thời lượng |
|---|---|---|---|
| Vấn đề & thị trường | 1–3 | R2 (nắm số liệu y khoa chắc nhất) | 2 phút |
| Demo sản phẩm live | 4 | R4 | 3 phút |
| Kiến trúc & cách chống bịa số | 5–7 | R1 | 3 phút |
| Evaluation & DevOps | 8 | R5 | 1,5 phút |
| Bài học & bước tiếp | 9–10 | R3 | 1 phút |
| Q&A | — | R1 chủ trì, phân câu cho đúng người | — |

### Câu hỏi giám khảo chắc chắn hỏi — ai trả lời

| Câu hỏi | Người trả lời | Ý chính |
|---|---|---|
| "Làm sao chống hallucination?" | R1 | Kiến trúc 4 tầng; LLM không sinh số |
| "Số liệu dinh dưỡng lấy ở đâu?" | R2 | NIN + USDA, mỗi dòng có nguồn, món lạ gắn nhãn ước tính |
| "Nếu AI sai thì sao?" | R1 hoặc R2 | Fail closed + HITL + audit log; và nói thẳng những gì hệ thống không làm |
| "Có dùng dữ liệu bệnh nhân thật không?" | R3 | Dev/test dùng NHANES public-use đã de-identify; eval là synthetic; không dùng dữ liệu định danh hay SEQN |
| "Chi phí mỗi request?" | R5 | Có số đo thật từ LangSmith |
| "Scale 1000 user thì sao?" | R5 | Trả lời thật: hiện chưa scale, và nêu hướng (queue, cache targets, batch) |
| "Tại sao LangGraph mà không CrewAI?" | R1 | Cần state machine có interrupt để làm HITL — đây đúng là điểm mạnh của LangGraph |

> Trả lời thật khi chưa làm được sẽ ghi điểm cao hơn là nói vống. Giám khảo phân biệt được.
