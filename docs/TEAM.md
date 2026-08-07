# TEAM — PHÂN VAI, PHÂN QUYỀN & TRÁCH NHIỆM (ĐỘI 4 NGƯỜI)

> Phiên bản 2.0 — vai trò R5 (DevOps/QA/PM) đã được chia lại cho 4 người.
> Bản 5 người lưu ở `TEAM_5p_backup.md` phòng khi có người tham gia thêm.
> Điền tên thật vào bảng dưới ngay buổi họp đầu rồi commit.

---

## 1. Bốn vai trò

| Mã | Vai trò | Thành viên | Sở hữu | Backup bởi |
|---|---|---|---|---|
| **R1** | Tech Lead / Agent Engineer **+ PM** | `…` | `src/agents/`, guardrails, prompt, LangGraph · theo dõi tiến độ & deliverables | R3 |
| **R2** | Clinical & Data Engineer **+ Eval** | `…` | `src/clinical/`, `src/rag/`, `data/`, bộ eval, liên hệ chuyên gia | R1 |
| **R3** | Backend Engineer **+ DevOps** | `…` | `src/api/`, `src/db/`, auth, audit · Docker, CI/CD, deploy, secrets | R1 |
| **R4** | Frontend Engineer **+ Deliverables** | `…` | `web/`, UI 2 vai trò, HITL dashboard · README, screenshot, video, pitch deck | R3 |

### Vai trò R5 cũ được chia thế nào

| Việc của R5 (bản 5 người) | Nay thuộc |
|---|---|
| Docker, CI/CD, deploy, secrets, chi phí API | **R3** |
| Bộ eval, RAGAS, báo cáo đánh giá | **R2** |
| Chạy eval runner trên graph | **R1** |
| README, video demo, pitch deck, screenshot | **R4** |
| Theo dõi 10 deliverables, nhắc DEVLOG, canh code freeze | **R1** |

> Với 4 người, **không ai là PM toàn thời gian**. R1 kiêm PM nghĩa là ~2 giờ/tuần cho theo dõi tiến độ, không phải nghỉ code.

---

## 2. Trách nhiệm chi tiết

### R1 — Tech Lead / Agent Engineer + PM
- **Chính:** LangGraph graph/node/tool, prompt, guardrails tầng 1–2, retry loop, LangSmith tracing, chạy eval runner.
- **Kiêm PM:** giữ bảng deliverables trong `DEVLOG.md` §6, nhắc standup, canh code freeze, chủ trì retro.
- **Quyền quyết:** chốt tranh luận kỹ thuật sau 15 phút. Review mọi PR chạm `src/agents/`.
- **Không làm:** logic tính toán dinh dưỡng (của R2) — tránh trộn LLM vào con số.
- **Cột mốc W3:** agent sinh thực đơn pass validator ≥70% ngay lần đầu.

### R2 — Clinical & Data Engineer + Eval
- **Chính:** bảng thực phẩm, món ăn, `clinical_rules`, drug–food, OOV estimator, RAG ingestion.
- **Kiêm Eval:** bộ 60 case, RAGAS, `eval/results/report.md`, mời chuyên gia review 20 thực đơn.
- **Quyền đặc biệt:** người **duy nhất** được thêm/sửa ngưỡng lâm sàng. Mọi PR chạm `src/clinical/` hoặc `data/seeds/` bắt buộc R2 duyệt.
- **Cũng chịu trách nhiệm:** verify từng số liệu y khoa trước khi lên slide → `docs/REFERENCES.md`.
- **Cột mốc W2:** 200 thực phẩm + 50 món + rules 4 nhóm bệnh, có nguồn từng dòng.

### R3 — Backend Engineer + DevOps
- **Chính:** FastAPI routes, Pydantic schemas, SQLAlchemy, Alembic, JWT auth, RBAC, audit log.
- **Kiêm DevOps:** Dockerfile, docker-compose, GitHub Actions, deploy Render+Vercel, secrets, theo dõi chi phí API hằng tuần.
- **Quyền đặc biệt:** được **chặn merge** nếu CI đỏ hoặc thiếu test, kể cả PR của Tech Lead.
- **Cột mốc W1:** Live URL hello-world + CI xanh. **W2:** auth + profile + targets API.

### R4 — Frontend Engineer + Deliverables
- **Chính:** Next.js 2 portal, form hồ sơ, thực đơn kèm nguồn, dashboard duyệt, nhật ký, biểu đồ, dark mode.
- **Kiêm Deliverables:** README, chụp màn hình liên tục (không dồn tuần 6), video demo, pitch deck.
- **Cũng chịu trách nhiệm:** disclaimer đúng chỗ; cảnh báo dị ứng/tương tác phải nổi bật, không phải chữ nhỏ.
- **Cột mốc W4:** demo 2 tài khoản chạy trên Live URL.

---

## 3. Ma trận RACI

`R` = làm · `A` = chịu trách nhiệm cuối · `C` = hỏi ý kiến · `I` = thông báo

| Hạng mục | R1 | R2 | R3 | R4 |
|---|:-:|:-:|:-:|:-:|
| Kiến trúc hệ thống | **A/R** | C | C | I |
| Ngưỡng & quy tắc lâm sàng | C | **A/R** | I | I |
| Dữ liệu thực phẩm & nguồn | I | **A/R** | C | I |
| LangGraph, prompt, guardrails 1–2 | **A/R** | C | C | I |
| Validator (guardrail tầng 3) | C | **A/R** | C | I |
| HITL — backend | C | I | **A/R** | C |
| HITL — giao diện | C | C | C | **A/R** |
| Auth / RBAC / bảo mật | C | I | **A/R** | C |
| Schema DB & migration | C | C | **A/R** | I |
| Frontend & UX | I | I | C | **A/R** |
| Docker / CI / Deploy | C | I | **A/R** | I |
| Bộ eval & báo cáo | R | **A/R** | I | I |
| Theo dõi 10 deliverables | **A** | I | I | R |
| README, video, pitch deck | C | C | C | **A/R** |
| DEVLOG | **A** | R | R | R |

Không ô nào có hai chữ **A**. Cột có **A** là người bị hỏi khi hạng mục đó hỏng.

---

## 4. Phân quyền kỹ thuật

### GitHub

| Quyền | Ai |
|---|---|
| Admin repo | R1, R3 |
| Write | tất cả |
| Merge vào `main` | R3 (sau khi R1 duyệt) |
| Merge vào `develop` | bất kỳ ai, sau ≥1 review |
| Force push | **không ai** |

Branch protection `main` + `develop`: require PR · ≥1 approval · status checks `lint`/`test`/`build` · không cho bypass.

### `.github/CODEOWNERS`

```
*                       @r1-tech-lead

# Lâm sàng — nơi sai sót gây hại thật
/src/clinical/          @r2-clinical @r1-tech-lead
/data/seeds/            @r2-clinical
/eval/                  @r2-clinical

/src/agents/            @r1-tech-lead
/src/api/               @r3-backend
/src/db/                @r3-backend
/.github/               @r3-backend
/Dockerfile             @r3-backend
/web/                   @r4-frontend
/docs/                  @r1-tech-lead
README.md               @r4-frontend
```

### Secrets

| Bí mật | Ai giữ | Ở đâu |
|---|---|---|
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | R3 | Render env + GitHub Secrets |
| `DATABASE_URL` (prod) | R3 | Render env |
| `JWT_SECRET` | R3 | Render env |
| `LANGSMITH_API_KEY` | R1, R3 | Render env |
| `AI_LOG_API_KEY` | mỗi người | `.env` local |

> Ai lỡ commit secret: revoke key ngay → `git filter-repo` → ghi vào DEVLOG §4 như một sự cố. Không giấu.

### RBAC trong sản phẩm

| Hành động | patient | dietitian | admin |
|---|:-:|:-:|:-:|
| Xem hồ sơ của mình | ✅ | ✅ | ✅ |
| Xem hồ sơ bệnh nhân khác | ❌ | ✅ | ✅ |
| Yêu cầu sinh thực đơn | ✅ | ✅ | ✅ |
| Xem thực đơn `pending_review` | ❌ | ✅ | ✅ |
| Duyệt / sửa / từ chối | ❌ | ✅ | ✅ |
| Ghi nhật ký ăn uống | ✅ | ❌ | ✅ |
| Sửa `clinical_rules` | ❌ | ❌ | ✅ |

**Test bắt buộc (BE-09):** bệnh nhân A gọi tài nguyên của B → **404**, không phải 403.

---

## 5. Phân bổ tải

| Vai trò | Giờ ước tính | Giờ/tuần |
|---|---|---|
| R1 Tech Lead / Agent + PM | ~118h | ~20h |
| R2 Clinical & Data + Eval | ~130h | ~22h |
| R3 Backend + DevOps | ~98h | ~16h |
| R4 Frontend + Deliverables | ~102h | ~17h |

⚠️ **R2 quá tải ở tuần 1–2** vì việc nhập dữ liệu. Bắt buộc cả 4 người cùng làm `DAT-02` (chia 4 × ~38 dòng, một buổi tối là xong). Để R2 gánh một mình thì đường găng vỡ ngay tuần đầu.

**Điều chỉnh giữa kỳ:** R3 rảnh hơn từ tuần 5 → chuyển sang hỗ trợ `ADV-01` (mâm cơm gia đình) và `EVL-02`.

---

## 6. Nhịp làm việc

| Khi nào | Việc | Bao lâu |
|---|---|---|
| Hằng ngày 21:00 | Standup async — 3 dòng/người: hôm qua / hôm nay / vướng | 5 phút |
| Thứ 2 20:00 | Sprint planning, chốt ticket tuần | 45 phút |
| Thứ 7 20:00 | Demo nội bộ — mỗi người demo phần mình trên `develop` | 30 phút |
| Thứ 7 sau demo | Retro — 1 điều giữ, 1 điều bỏ | 15 phút |
| Cuối mỗi buổi | Ghi DEVLOG | 2 phút |

Quy tắc: chỉ **1 ticket In Progress** mỗi người · vướng > 90 phút phải kêu · tranh luận tối đa 15 phút rồi R1 quyết.

---

## 7. Demo Day — ai nói phần nào

| Phần | Slide | Người nói | Thời lượng |
|---|---|---|---|
| Vấn đề & thị trường | 1–3 | R2 (nắm số liệu y khoa chắc nhất) | 2 phút |
| Demo sản phẩm live | 4 | R4 | 3 phút |
| Kiến trúc & cách chống bịa số | 5–7 | R1 | 3 phút |
| Evaluation & DevOps | 8 | R3 | 1,5 phút |
| Bài học & bước tiếp | 9–10 | R4 | 1 phút |

### Q&A — ai trả lời câu nào

| Câu hỏi | Người | Ý chính |
|---|---|---|
| "Làm sao chống hallucination?" | R1 | Kiến trúc 4 tầng; LLM không sinh số |
| "Số liệu dinh dưỡng lấy đâu?" | R2 | NIN + USDA, mỗi dòng có nguồn, món lạ gắn nhãn ước tính |
| "Nếu AI sai thì sao?" | R1/R2 | Fail closed + HITL + audit log; nói rõ hệ thống KHÔNG làm gì |
| "Dùng dữ liệu bệnh nhân thật không?" | R3 | Dev/test dùng NHANES public-use đã de-identify; eval là synthetic; không dùng dữ liệu định danh hay SEQN |
| "Chi phí mỗi request?" | R3 | Số đo thật từ LangSmith |
| "Scale 1000 user?" | R3 | Trả lời thật: chưa scale, nêu hướng (queue, cache, batch) |
| "Sao chọn LangGraph mà không CrewAI?" | R1 | Cần state machine có interrupt để làm HITL |

> Trả lời thật khi chưa làm được ghi điểm cao hơn nói vống. Giám khảo phân biệt được.
