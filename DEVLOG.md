# DEVLOG — NHẬT KÝ PHÁT TRIỂN

> **Đây là file log duy nhất của dự án.** Nó phục vụ đồng thời Deliverable #8 (Development Journal) và #9 (Worklog).
> Quy tắc: **chỉ thêm, không sửa lịch sử.** Ghi sai thì thêm dòng đính chính, đừng xoá.
> Nhịp: mỗi người 1 entry sau mỗi buổi làm việc · cả đội 1 entry tổng kết mỗi cuối tuần.

---

## 0. Cách ghi

**Nhật ký cá nhân** — mất 2 phút, ghi vào §2:

```markdown
### [YYYY-MM-DD] · <Tên> · <Vai trò>
- **Làm:** CLN-04 bounds checker — xong phần Na/K, còn P
- **Kết quả:** 8 unit test pass, PR #23 đang chờ review
- **Vướng:** ngưỡng phospho cho CKD G4 chưa rõ đơn vị trong guideline → đang hỏi R2
- **Tiếp theo:** hoàn thiện P + viết test biên
- **Thời gian:** 3h
```

**Quyết định kỹ thuật** — ghi vào §3 khi có tranh luận đáng kể (bối cảnh → phương án → quyết định → hệ quả).

**Sự cố** — ghi vào §4. Bao gồm cả sự cố do chính mình gây ra. Không ai bị phạt vì ghi sự cố; ghi lại chính là thứ tạo ra slide "Challenges & Learnings".

**Tổng kết tuần** — R1 (kiêm PM) ghi vào §5 mỗi tối Chủ nhật.

> 💡 Tuần 6 sẽ cần đúng file này để dựng slide 9 và báo cáo. Ghi đều đặn từ tuần 1 rẻ hơn nhiều so với ngồi bịa lại lịch sử vào đêm trước Demo Day.

---

## 1. Thông tin dự án

| | |
|---|---|
| Tên dự án | NutriCare Agent — AI Agent Dinh dưỡng Lâm sàng |
| Đề bài | VMEC-10 |
| Repository | `https://github.com/AI20K-Build-Cohort-2/C2-App-XXX` |
| Live URL | *(cập nhật sau SET-05)* |
| Demo Day | 06/09/2026 *(giả định — cập nhật khi có lịch chính thức)* |
| Code freeze | 04/09/2026 23:59 |

| Vai trò | Thành viên | Email |
|---|---|---|
| R1 Tech Lead / Agent + PM | | |
| R2 Clinical & Data + Eval | | |
| R3 Backend + DevOps | | |
| R4 Frontend + Deliverables | | |

---

## 2. Nhật ký hằng ngày

<!-- Entry mới thêm vào CUỐI mục này, theo thứ tự thời gian -->

### [2026-07-26] · Cả đội · Dựng khung code + tổ chức lại cho đội 4 người
- **Làm:** Phân vai lại 4 người (R5 chia cho R1/R2/R3/R4); dựng khung clinical engine + LangGraph; seed clinical_rules (18) + drug_food (30) + template 152 thực phẩm; pitch deck outline
- **Kết quả:** 43 test xanh, graph compile và xuất được mermaid, `validate_data.py` bắt đúng 4/4 lỗi cài sẵn
- **Phát hiện:** test bắt được xung đột ADA vs KDIGO ở ca ĐTĐ+CKD → đã xử lý bằng rule precedence (DEC-007), đưa vào slide 9
- **Vướng:** vẫn chưa chốt được nguồn Bảng thành phần thực phẩm VN (DAT-01) — rủi ro RSK-01 còn nguyên
- **Tiếp theo:** SET-01→06 (R3), DAT-00 + DAT-01 (R2), nhập 152 dòng thực phẩm chia 4 người

### [2026-07-26] · Cả đội · Khởi động
- **Làm:** Đọc đề bài VMEC-10, rà soát đề án mở rộng và tài liệu nghiên cứu; nhận đánh giá kỹ thuật độc lập
- **Kết quả:** Bộ tài liệu `docs/` v1 (đánh giá, kế hoạch 6 tuần, kiến trúc, phân vai, 52 ticket, rules, skills)
- **Quyết định lớn:** cắt scope mạnh — bỏ vision/OCR, knowledge graph, K8s, benchmark y khoa; giữ trọng tâm ở nguyên tắc "LLM chọn món, Python tính số" + HITL (chi tiết ở §3, DEC-001)
- **Vướng:** chưa xác định nguồn Bảng thành phần thực phẩm Việt Nam dùng được → đây là rủi ro số 1
- **Tiếp theo:** SET-01 đến SET-06 và DAT-00, DAT-01 trong tuần 1
- **Thời gian:** —

### [2026-07-27] · Claude (thay R3) · SET-01 bootstrap
- **Làm:** Rà lại toàn bộ EPIC 0 và phát hiện nhiều phần trước đó *chưa thực sự* đạt AC dù trông như đã xong. Sửa: thêm `pyproject.toml` (không tồn tại), thêm target `make run`/`lint`/`format` vào `Makefile` (AC "cả 5 người chạy `make run`" trước đó chắc chắn fail vì không có target), bổ sung biến thiếu trong `.env.example` (`APP_NAME`, `MODEL_NAME`, `LLM_TEMPERATURE`), redact `AI_LOG_API_KEY` thật khỏi `.env.example` (đã từng bị redact bởi Đinh Lê Quỳnh Phương rồi bị commit đè lại bằng key thật). Tạo branch `develop` trên repo đội thật (`AI20K-Build-Phase-Cohort-3/P-031`) — trước đó chỉ có `main`
- **Kết quả:** PR #3 (SET-01) + PR #2 (SET-03/SET-04, xem entry trước) mở trên repo đội thật
- **Phát hiện quan trọng:** repo đội thật là `AI20K-Build-Phase-Cohort-3/P-031`, không phải `hwngkm/VMEC10_P31` (repo cá nhân) — công việc trước đó (bao gồm cả PR đầu của phiên này) từng nhắm nhầm repo
- **Vướng:** tài khoản GitHub hiện dùng (`hwngkm`) không có quyền Admin trên repo đội thật (`permissions.admin=false` qua API) dù được xác nhận là admin — cần người thật kiểm tra lại trên GitHub UI để bật branch protection cho `main`/`develop` (AC SET-01 "main không push thẳng được" chưa đạt). TEAM.md/CODEOWNERS vẫn dùng handle placeholder vì chưa có tên GitHub thật của 4 thành viên
- **Tiếp theo:** merge PR #2 + PR #3, sau đó bật branch protection, điền tên thật vào TEAM.md/CODEOWNERS, xác nhận SET-02 đã chạy trên máy cả 4 người, viết lại README theo đúng AC SET-06 (hiện là README kỹ thuật cho khung code, thiếu phần giới thiệu dự án/Live URL/thành viên)
- **Thời gian:** ~1h

---

## 3. Quyết định kỹ thuật (Decision Log)

| ID | Ngày | Quyết định | Người quyết | Chi tiết |
|---|---|---|---|---|
| DEC-001 | 2026-07-26 | Cắt scope: bỏ vision/OCR, Neo4j, K8s, DDID full, benchmark MedQA | Cả đội | Xem `docs/00_ASSESSMENT.md` §9 |
| DEC-002 | 2026-07-26 | Postgres + pgvector, không dùng vector DB riêng | R1 | ADR-001 |
| DEC-003 | 2026-07-26 | LLM chỉ trả `food_id` + gram; số liệu tính bằng SQL | R1 | ADR-002 — nguyên tắc bất biến |
| DEC-004 | 2026-07-26 | Drug–food: curate 80 cặp thay vì import DDID | R2 | ADR-005 |
| DEC-005 | 2026-07-26 | Deploy Render + Vercel + Neon | R3 | ADR-006 |
| DEC-006 | 2026-07-26 | Đội 4 người: gộp DevOps vào R3, Eval vào R2, Deliverables vào R4, PM vào R1 | Cả đội | Xem `TEAM.md` §1 |
| DEC-007 | 2026-07-26 | Thêm cơ chế `overridden_by` cho clinical_rules | R2 | Bối cảnh: ADA (protein 15-20%E) xung đột KDIGO (0.6-0.8 g/kg) ở bệnh nhân ĐTĐ+CKD. Phương án: (A) để cơ chế conflict đẩy sang chuyên gia, (B) rule precedence. Chọn B vì ĐTĐ+CKD quá phổ biến, phương án A làm hỏng trải nghiệm. Hệ quả: giữ nguyên cơ chế conflict làm lưới an toàn cho trường hợp chưa lường trước |
| DEC-008 | 2026-07-26 | Không điền sẵn số liệu dinh dưỡng vào seed, để trống chờ tra nguồn thật | R2 | Bối cảnh: có thể sinh nhanh 152×10 con số trông hợp lý. Quyết định không làm, vì dữ liệu không truy vết được sẽ qua được cả validator lẫn mắt chuyên gia nhưng vẫn sai định mức bệnh nhân. Hệ quả: `validate_data.py` chặn merge nếu thiếu `source_ref` |

**Mẫu ghi quyết định mới:**

```markdown
| DEC-0XX | YYYY-MM-DD | <quyết định 1 dòng> | <ai> | Bối cảnh: … · Phương án cân nhắc: A/B/C · Chọn B vì … · Hệ quả: … |
```

---

## 4. Sự cố & bài học

| ID | Ngày | Sự cố | Tác động | Nguyên nhân gốc | Đã làm gì | Phòng ngừa |
|---|---|---|---|---|---|---|
| | | | | | | |

*(Ghi cả sự cố nhỏ: CI hỏng 2 tiếng, mất 1 buổi vì merge conflict, LLM ngốn hết credit… Đây là nguyên liệu tốt nhất cho slide "Challenges & Learnings".)*

---

## 5. Tổng kết tuần

### Tuần 1 (27/07 – 02/08) — Nền móng & Dữ liệu
- **Mục tiêu:** Repo + CI + Live URL hello-world + 150 thực phẩm + DEVLOG chạy
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:** ticket đóng __/10 · commit __ · test __ · coverage __%
- **Bài học:**
- **Điều chỉnh cho tuần sau:**

### Tuần 2 (03/08 – 09/08) — Clinical Engine
- **Mục tiêu:** API định mức đúng cho 4 bệnh lý + auth 2 role + schema DB
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 3 (10/08 – 16/08) — Agent & Guardrails
- **Mục tiêu:** Sinh thực đơn pass validator ≥70% lần đầu + chặn chỉ định y khoa ≥95%
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 4 (17/08 – 23/08) — HITL & Nhật ký
- **Mục tiêu:** Demo end-to-end 2 tài khoản trên Live URL
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 5 (24/08 – 30/08) — Nâng cao
- **Mục tiêu:** Mâm cơm gia đình + tương tác thuốc + thực đơn 7 ngày
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 6 (31/08 – 06/09) — Đóng gói
- **Mục tiêu:** Eval report + video + pitch + 10/10 deliverables
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

---

## 6. Theo dõi Deliverables

| # | Deliverable | Owner | Trạng thái | Vị trí | Ghi chú |
|---|---|---|---|---|---|
| 1 | Source Code | R1 | ⬜ | `src/` | |
| 2 | README.md | R4 | ⬜ | `README.md` | |
| 3 | Architecture Diagram | R1 | ⬜ | `docs/architecture_diagram.md` | |
| 4 | AI Logs | R3 | ⬜ | `.ai-log/` + LangSmith | Xong ngay tuần 1 nhờ hooks |
| 5 | Live URL | R3 | ⬜ | Render + Vercel | Deploy từ tuần 1 |
| 6 | Video Demo | R4 | ⬜ | YouTube unlisted | Hiếm đội có → ưu tiên |
| 7 | Pitch Deck | R4 | ⬜ | `presentation/` | |
| 8 | Development Journal | Cả đội | 🟡 | **file này** §2, §5 | Đang chạy |
| 9 | Worklog | R1 | 🟡 | **file này** + `docs/worklog.md` | `git log` xuất cuối kỳ |
| 10 | Evaluation Evidence | R2 | ⬜ | `eval/results/report.md` | Hiếm đội có → ưu tiên |

Trạng thái: ⬜ chưa bắt đầu · 🟡 đang làm · ✅ xong

---

## 7. Theo dõi chỉ số

| Tuần | Ticket đóng | Commit | Test | Coverage | Chi phí LLM | Live URL | Ghi chú |
|---|---|---|---|---|---|---|---|
| W1 | | | | | | | |
| W2 | | | | | | | |
| W3 | | | | | | | |
| W4 | | | | | | | |
| W5 | | | | | | | |
| W6 | | | | | | | |

---

## 8. Xuất worklog cuối kỳ

```bash
git log --oneline --date=short --pretty=format:'%ad | %an | %s' --since="2026-07-27" > docs/worklog.md
```
