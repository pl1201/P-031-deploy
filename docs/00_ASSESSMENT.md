# 00 — ĐÁNH GIÁ ĐỀ ÁN & NGHIÊN CỨU HIỆN TẠI

> Dự án: **VMEC-10 — AI Agent Dinh dưỡng Lâm sàng**
> Ngày đánh giá: 26/07/2026 · Người đánh giá: AI Tech Advisor (Claude)
> Đầu vào: `VMEC-10 - Đề bài ban đầu.txt`, `de_an_ai_agent_dinh_duong.md`, `nghien_cuu_dinh_duong_ai_agent.md`, template AI20K Build Cohort 2
>
> ⚠️ **Tài liệu lịch sử (26/07).** Phạm vi bệnh lý mô tả trong file này (đa bệnh lý) đã bị thu hẹp còn **ĐTĐ2** bởi `docs/PRD.md` v2.1 (05/08). Đọc `docs/PRD.md` để biết phạm vi hiện hành; file này giữ lại làm bối cảnh quyết định cắt scope kỹ thuật ban đầu (§9), vẫn còn giá trị tham khảo.

---

## 1. Tóm tắt điều hành (đọc phần này nếu chỉ có 2 phút)

| Hạng mục | Đánh giá | Ghi chú |
|---|---|---|
| Chất lượng nghiên cứu (research) | 🟢 8/10 | Rất tốt so với mặt bằng hackathon. Guideline lâm sàng, số liệu muối VN, phân tích 3 miền đều dùng được ngay |
| Độ bám đề bài VMEC-10 | 🟢 9/10 | Bao phủ đủ mọi yêu cầu "Cơ bản" và "Nâng cao" |
| Tính khả thi trong 6 tuần | 🔴 3/10 | **Vấn đề lớn nhất.** Scope hiện tại ≈ 3x năng lực đội 4–5 sinh viên |
| Kế hoạch triển khai (ai làm gì, khi nào) | 🔴 1/10 | Gần như chưa có. Roadmap mới ở mức liệt kê tính năng |
| Kế hoạch dữ liệu (lấy VNFCD/DDID ở đâu) | 🔴 2/10 | Đề án giả định "có sẵn" — thực tế đây là rủi ro chặn dự án |
| Kế hoạch đánh giá (Evaluation Evidence) | 🟡 4/10 | Có nhắc benchmark hoành tráng (MedQA, MedArena, M-LEAF) nhưng không khả thi; thiếu metric sản phẩm đơn giản mà BTC chấm |

**Kết luận:** Giữ nguyên phần *cơ sở khoa học* và *định vị sản phẩm* (đây là điểm mạnh cạnh tranh). **Cắt mạnh phần kỹ thuật**, dồn lực vào 1 thứ duy nhất tạo khác biệt: **tách bạch "LLM chọn món" khỏi "Python tính số" + HITL bắt buộc**. Đó là câu chuyện kỹ thuật đủ sâu để thắng, và đủ nhỏ để làm xong.

---

## 2. Đối chiếu đề bài gốc ↔ đề án mở rộng

| Yêu cầu đề bài VMEC-10 | Đề án hiện tại | Trạng thái |
|---|---|---|
| ≥2 vai trò (bệnh nhân / chuyên gia dinh dưỡng) | Có, thêm vai trò người nhà | ✅ Đủ (vai trò người nhà nên gộp vào bệnh nhân ở v1) |
| Nhập hồ sơ & ràng buộc ăn kiêng (mô phỏng) | Có + chỉ số xét nghiệm | ✅ |
| Gợi ý thực đơn/khẩu phần theo nguyên tắc lâm sàng | Có | ✅ |
| Ước tính năng lượng/đường/muối **có nguồn** | Có (NIN + USDA) | ⚠️ Phụ thuộc dữ liệu chưa có |
| Nhật ký ăn uống + phản hồi điều chỉnh | Có | ✅ |
| LangGraph điều phối 4 bước | Có | ✅ |
| RAG trên bảng TPTP VN + guideline | Có | ⚠️ Kiến trúc đang nhầm lẫn RAG vs tra cứu số liệu (xem §4.1) |
| 4 tool bắt buộc | Có đủ 4 | ✅ |
| Guardrails chống bịa + chặn chỉ định y khoa | Có | ✅ Điểm mạnh |
| HITL bắt buộc | Có | ✅ Điểm mạnh |
| FastAPI + Next.js + Postgres + deploy cloud | Có | ⚠️ Đề án thêm Qdrant/Milvus + K8s — thừa |
| Cảnh báo dị ứng & tương tác thuốc–thực phẩm | Có | ⚠️ Quy mô 23.950 bản ghi là bất khả thi |
| Bảo mật PII/PHI | Có (NĐ 13/2023) | ⚠️ Mới ở mức tuyên bố, chưa có thiết kế |

→ **Không thiếu gì so với đề bài.** Vấn đề nằm ở chiều ngược lại: thừa.

---

## 3. Điểm mạnh cần giữ bằng mọi giá

1. **Bài toán "mâm cơm gia đình"** — đây là insight bản địa hoá mà MyFitnessPal/Noom không có. Là *hook* của pitch deck. Giữ, nhưng làm bằng rule + LLM decomposition, **không cần computer vision**.
2. **Số liệu muối Việt Nam** (8,1–9,4 g/ngày vs khuyến cáo 5 g; 70–81% từ nêm nếm; phở bò 3,3–4,0 g; bún cá 6,2 g) — cực kỳ đắt giá cho slide 2 "Problem". Giữ nguyên, chỉ cần verify nguồn.
3. **Kiến trúc Hybrid: LLM linh hoạt + Deterministic Clinical Engine** — đây là câu trả lời cho câu hỏi BTC chắc chắn sẽ hỏi ("làm sao chống hallucination?"). Đây là **trục kỹ thuật chính** của toàn dự án.
4. **HITL bắt buộc** — vừa là ràng buộc đề bài, vừa là tính năng demo ấn tượng (2 màn hình, 2 tài khoản, 1 luồng duyệt).
5. **Phân tích 3 miền** — dùng làm chiến lược thay thế nguyên liệu, rất dễ demo và rất "Việt Nam".

---

## 4. Vấn đề kỹ thuật cần sửa

### 4.1. Nhầm lẫn giữa RAG và tra cứu số liệu ⚠️ NGHIÊM TRỌNG

Đề án viết "RAG trên bảng thành phần thực phẩm". **Sai về nguyên tắc.**

- Bảng thành phần thực phẩm là **dữ liệu có cấu trúc** → phải truy vấn bằng **SQL**, kết quả chính xác tuyệt đối.
- Nếu đưa vào vector DB rồi để LLM đọc snippet, ta vừa tự tạo ra đúng cái lỗi mà guardrail đang cố chống (sai số, bịa số).
- **RAG chỉ dùng cho văn bản không cấu trúc**: guideline BYT, ADA/KDIGO, tài liệu tư vấn — nơi ta cần *trích dẫn diễn giải*, không cần con số.

**Quy tắc bất biến của dự án (in đậm vào rules):**
> **LLM được chọn món và khẩu phần. LLM KHÔNG BAO GIỜ được sinh ra con số dinh dưỡng. Mọi con số đều đến từ truy vấn SQL vào bảng thực phẩm.**

### 4.2. Vector DB chọn thừa

Qdrant/Milvus + Postgres = 2 hệ thống phải vận hành, backup, deploy. Với < 5.000 chunks văn bản → **pgvector là đủ**, và giảm 1 service khỏi `docker-compose`. Bỏ Qdrant/Milvus.

### 4.3. Kubernetes là bẫy

Deploy K8s cho một demo 6 tuần chỉ tiêu tốn thời gian mà không được thêm điểm. **Render/Railway (backend) + Vercel (frontend) + Neon/Supabase (Postgres)** — free tier, 1 buổi là xong.

### 4.4. Multi-agent 5 con là over-engineering

Vision Agent, Ingredient Decomposition Agent, Clinical Guardrail Agent, Planning Agent, Verifier Agent (Med-PaLM)… Trong LangGraph, **node ≠ agent**. Ta cần **1 graph với ~7 node**, trong đó chỉ 2–3 node gọi LLM. Vẫn nói được là "multi-step agent" trong pitch mà không phải debug 5 vòng lặp lồng nhau.

### 4.5. Med-PaLM 2 làm Verifier — không khả thi

Med-PaLM 2 không mở API công khai cho dev thường. Thay bằng: **LLM-as-judge (cùng model, prompt khác) + rules engine**, và ghi rõ trong doc là "verifier tier-2".

### 4.6. Benchmark MedQA / MedArena / M-LEAF — không dùng được

Đây là benchmark cho *mô hình y khoa tổng quát*, không đo được sản phẩm dinh dưỡng. Đội sẽ tốn 1 tuần mà không ra được số. Thay bằng bộ eval tự xây (xem `PLAN.md` §7) — **60 case, 5 metric, chạy bằng pytest**. Đây mới là thứ BTC chấm ở Deliverable #10.

---

## 5. Rủi ro dữ liệu — rủi ro số 1 của dự án 🔴

| Dataset đề án nêu | Thực tế | Hành động |
|---|---|---|
| VNFCD (Viện Dinh dưỡng, 500+ món) | Là **sách in / PDF**, không có API, không có file mở chính thức | Số hoá thủ công **150–200 thực phẩm phổ biến nhất** + trích PDF. Ghi rõ nguồn từng dòng |
| USDA FoodData Central | ✅ Có API mở, miễn phí, đăng ký key | Dùng để bổ sung vi chất. Ticket DAT-03 |
| DDID (23.950 tương tác) | Là dataset học thuật, **cần kiểm tra license** trước khi dùng | Nếu không dùng được: **curate thủ công 60–80 cặp thuốc–thực phẩm quan trọng nhất** (Warfarin–vitamin K, ACEi–kali, Statin–bưởi, Metformin–rượu, Levothyroxine–canxi/đậu nành, MAOI–tyramine…). 80 cặp là quá đủ để demo |
| Vietnamese Regional Recipe Dataset (1.000+ công thức) | **Không tồn tại công khai** | Tự xây 80–120 công thức, LLM sinh nháp + người rà soát. Ticket DAT-05 |
| Clinical Nutrition Ruleset | Phải tự viết | Đây là tài sản trí tuệ chính. Ticket CLN-01..05 |

> ⚠️ **Nếu tuần 1 không chốt xong nguồn dữ liệu, dự án sẽ trượt tiến độ toàn tập.** Đây là lý do DAT-01 là ticket P0 duy nhất phải xong trong 3 ngày đầu.

---

## 6. Vấn đề học thuật cần kiểm chứng trước khi lên pitch deck

Nghiên cứu trích dẫn nhiều số liệu ấn tượng. Trước khi đưa lên slide, cần **verify từng cái** (ticket DAT-00) — bị hỏi mà không dẫn được nguồn sẽ mất điểm nặng hơn là không nói:

- `arXiv:2601.04491` (Closed-Loop Multi-Agent, "2026") — kiểm tra ID có tồn tại thật không.
- `arXiv:2502.20601` (NutriGen) và con số sai lệch calo 1,55% / 3,68% / 10,45%.
- F1 = 0,894 (Llama-3 70B) và 0,842 (GPT-4o) cho phân rã món ăn.
- Hiệu lực hiện hành của **Thông tư 08/2024/TT-BYT**, **QĐ 2598/QĐ-BYT**, **QĐ 3777/QĐ-BYT**, **QĐ 9484/QĐ-BYT**.
- **Nghị định 13/2023/NĐ-CP** về bảo vệ dữ liệu cá nhân — kiểm tra đã có văn bản thay thế/bổ sung chưa.
- Con số ">70% bệnh nhân không tuân thủ sau 3 tháng" — trong đề án đang **không có nguồn**. Hoặc tìm được nguồn, hoặc bỏ.

**Nguyên tắc:** mỗi số liệu trên slide phải có 1 dòng nguồn trong `docs/REFERENCES.md`.

---

## 7. Rủi ro pháp lý & đạo đức (phải nói rõ trong demo)

1. **Dữ liệu bệnh nhân phải là dữ liệu mô phỏng 100%.** Không lấy hồ sơ thật, kể cả đã ẩn danh, kể cả từ người quen. Đề bài đã ghi "(mô phỏng)".
2. **Không chẩn đoán, không kê chế độ điều trị.** Agent phải từ chối các câu như "tôi bị gì?", "có nên bỏ thuốc không?", "liều insulin bao nhiêu?" → chuyển hướng sang chuyên gia. Đây là guardrail bắt buộc, cần test case riêng.
3. **Disclaimer hiển thị ở mọi nơi có thực đơn** (UI + PDF export + API response).
4. **Nếu có chuyên gia dinh dưỡng thật tham gia review** → là điểm cộng cực lớn cho pitch. Nên chủ động mời 1 người (giảng viên/bác sĩ quen) review 20 thực đơn và ký xác nhận. Ticket EVL-06.
5. **PII/PHI**: v1 chỉ cần — mã hoá mật khẩu (bcrypt/argon2), TLS, RBAC, audit log bất biến, không log PHI ra stdout, không gửi tên thật/CCCD vào prompt LLM (dùng ID + tuổi + giới + chỉ số). Đừng hứa HIPAA/GDPR compliance — không ai audit và cũng không đạt được.

---

## 8. Khoảng trống so với tiêu chí chấm của BTC

Đối chiếu với `docs/guide/chapter-09.md` của template (10 deliverables, 5 tiêu chí × 10 điểm, mục tiêu 35+/50):

| Deliverable | Đề án hiện có? | Ghi chú |
|---|---|---|
| 1. Source Code | ❌ chưa bắt đầu | — |
| 2. README.md | ❌ | Copy `README_boilerplate.md` |
| 3. Architecture Diagram | 🟡 có sơ đồ ASCII | Cần Mermaid → xem `ARCHITECTURE.md` |
| 4. AI Logs | ❌ | Template đã có hook sẵn, chỉ cần `bash scripts/setup_hooks.sh` — **làm ngay ngày đầu** |
| 5. Live URL | ❌ | Deploy hello-world ở tuần 1, không đợi tuần 6 |
| 6. Video Demo | ❌ | Hiếm đội có → lợi thế lớn |
| 7. Pitch Deck | ❌ | 10 slide theo template chương 9 |
| 8. Journal | ❌ | → `DEVLOG.md` |
| 9. Worklog | ❌ | → `DEVLOG.md` + git log |
| 10. Evaluation Evidence | 🟡 nhắc benchmark sai hướng | Hiếm đội có → lợi thế lớn nhất. Xem `PLAN.md` §7 |

**Chiến lược ăn điểm:** 3 deliverable mà đa số đội bỏ (Video, Pitch, Evaluation) chính là 3 thứ tốn ít công nhất nếu làm sớm và đều tay.

---

## 9. Quyết định scope — MoSCoW

### ✅ MUST (không có = không nộp được bài)
- Auth + 2 role (patient / dietitian), RBAC
- Hồ sơ bệnh nhân: bệnh lý (ĐTĐ2, THA, CKD G3–G4, Gout), cân nặng/chiều cao/tuổi/giới, dị ứng, thuốc đang dùng
- Deterministic Clinical Engine: BMR/TDEE + định mức kcal, protein, Na, K, P, purine, chất xơ
- Food DB (≥150 thực phẩm + ≥80 món ăn VN) truy vấn bằng SQL, có cột `source`
- LangGraph agent sinh thực đơn 1 ngày → validate → regenerate (tối đa 3 lần)
- Guardrails: bounds checker + chặn chỉ định y khoa + cảnh báo dị ứng
- HITL: hàng chờ duyệt, chuyên gia approve/edit/reject, chỉ thực đơn approved mới đến bệnh nhân
- Nhật ký ăn uống + tổng hợp ngày, cảnh báo vượt ngưỡng Na/đường
- Disclaimer, audit log
- Deploy cloud + README + Architecture + DEVLOG

### 🟨 SHOULD (làm nếu MUST xong đúng hạn — đây là phần ghi điểm)
- Thực đơn 7 ngày + Smart Shopping List
- Phân rã mâm cơm gia đình (rule + LLM, nhập bằng text)
- Drug–food interaction (80 cặp curated)
- OOV Estimator (ước tính món lạ từ nguyên liệu, có gắn nhãn `estimated` + độ tin cậy)
- Biểu đồ xu hướng 7/30 ngày
- RAG guideline có trích dẫn (pgvector + BM25)
- Bộ eval 60 case + báo cáo

### 🟦 COULD (chỉ khi dư thời gian tuần 6)
- Memory sở thích / nguyên liệu sẵn có
- Gợi ý thay thế theo vùng miền
- Export PDF thực đơn
- Streaming response

### 🟥 WON'T (v1 — nói rõ trong slide "Next Steps" để thể hiện có suy nghĩ)
- Nhận diện ảnh mâm cơm (OCR/Vision)
- Knowledge Graph Neo4j, DDID full 23.950 bản ghi
- Kubernetes, multi-tenant bệnh viện
- Fine-tuning, Med-PaLM verifier
- Benchmark MedQA / MedArena / M-LEAF
- Mobile app native
- Đồng bộ HIS/EMR bệnh viện

---

## 10. Ba khuyến nghị chốt

1. **Đổi trục kể chuyện từ "AI làm được nhiều thứ" sang "AI an toàn để bác sĩ dám dùng".** Một hệ thống nhỏ mà không bịa số, có người duyệt, có audit trail sẽ thắng một hệ thống to mà không ai kiểm chứng được.
2. **Tuần 1 phải có: repo chạy + deploy hello-world + 150 dòng dữ liệu thực phẩm.** Không có dữ liệu thì mọi thứ phía sau là giả.
3. **Viết `DEVLOG.md` mỗi ngày từ hôm nay.** 2 deliverable (#8, #9) được hoàn thành miễn phí, và tuần 6 sẽ không phải bịa lại lịch sử dự án.

---

*Tài liệu tiếp theo: `PLAN.md` (kế hoạch 6 tuần) → `ARCHITECTURE.md` → `TEAM.md` → `TICKETS.md`*
