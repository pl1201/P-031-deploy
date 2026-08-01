# NGHIÊN CỨU BỔ SUNG — BẢN 2.0 (ƯU TIÊN NGUỒN MỚI NHẤT)

> Dự án: **VNutriCare** — VMEC-10 · AI20K Build Cohort 3
> Ngày: 27/07/2026 · **Thay thế bản 1.0**
> Phạm vi rà soát: ưu tiên nguồn công bố **2025–2026**. Các nguồn cũ hơn chỉ giữ khi vẫn là chuẩn hiện hành hoặc chưa có bản thay thế.

---

## ⚠️ 0. BỐN THAY ĐỔI SO VỚI BẢN 1.0

Rà soát theo hướng "mới nhất" đã lật lại một số kết luận. Đọc mục này trước.

| # | Bản 1.0 nói | Bản 2.0 đính chính | Mức độ |
|---|---|---|---|
| 1 | Ngưỡng protein CKD **0,6–0,8 g/kg**, dẫn "KDIGO/KDOQI" | ❗ **KDIGO 2024 đã thay thế bản 2012**, khuyến nghị **duy trì 0,8 g/kg** (mức đơn, không phải khoảng 0,6–0,8). Ngưỡng 0,55–0,60 là của **KDOQI 2020** — một hướng dẫn khác, chặt hơn | 🔴 **Phải sửa `clinical_rules.csv`** |
| 2 | Không đề cập rule an toàn cho người cao tuổi | ❗ KDIGO 2024 có **Practice Point 3.3.1.5**: người cao tuổi có suy yếu/thiểu cơ cần **tăng** protein và năng lượng; và **PP 3.3.1.3**: **không** kê chế độ hạn chế protein cho người CKD chuyển hoá không ổn định | 🔴 **Thiếu 2 guardrail an toàn quan trọng** |
| 3 | "Bảng TPTP VN 2007 trên FAO" (ngụ ý là bản mới nhất) | ⚠️ **Có bản mới hơn**: bản 2017 gồm **628 thực phẩm**, và một bản cập nhật số liệu phân tích 2007–2014. Bản 2007 vẫn là bản **miễn phí, đầy đủ nhất theo từng thực phẩm** (86 chất, có purin) | 🟡 Điều chỉnh cách phát biểu |
| 4 | Đề xuất tự xây bộ eval, bỏ MedQA/MedArena | ✅ Vẫn đúng, **nhưng nay đã có benchmark đúng bài toán**: **FAM-Bench** (5/2026) và **NutriBench** — không cần tự xây từ số 0 | 🟢 Cơ hội mới |

---

## 1. CẬP NHẬT HƯỚNG DẪN LÂM SÀNG — ẢNH HƯỞNG TRỰC TIẾP ĐẾN BỘ RULE

### 1.1. KDIGO 2024 — bản thay thế cho KDIGO 2012

Đây là hướng dẫn hiện hành cho bệnh thận mạn chưa lọc máu, thay thế bản 2012, dựa trên tổng quan hệ thống các nghiên cứu đến tháng 7/2023.

| Mã | Nội dung | Ghi chú |
|---|---|---|
| **Rec 3.3.1.1** | Duy trì protein **0,8 g/kg cân nặng/ngày** ở người lớn CKD G3–G5 *(mức bằng chứng 2C)* | Mức khuyến nghị **yếu**; tương đương RDA của dân số chung |
| **PP 3.3.1.1** | Tránh protein cao **> 1,3 g/kg/ngày** ở người CKD có nguy cơ tiến triển | |
| **PP 3.3.1.2** | Chế độ rất thấp protein (0,3–0,4 g/kg) + ketoacid analog (tới 0,6 g/kg): chỉ cân nhắc cho người **sẵn sàng và có khả năng**, có nguy cơ suy thận, **dưới giám sát chặt** | ⚠️ Không phải mặc định |
| **PP 3.3.1.3** | **Không kê** chế độ thấp/rất thấp protein cho người CKD **chuyển hoá không ổn định** | 🔴 **Guardrail còn thiếu trong hệ thống** |
| **PP 3.3.1.5** | Người cao tuổi có **suy yếu (frailty) và thiểu cơ (sarcopenia)**: cân nhắc mục tiêu protein và năng lượng **CAO HƠN** | 🔴 **Guardrail còn thiếu — và đây đúng là nhóm bệnh nhân mục tiêu của dự án** |
| **Rec 3.3.2.1** | Natri **< 2 g/ngày** (< 90 mmol, < 5 g muối) | Khớp với rule hiện tại ✅ |
| PP 3.3.2.1 | Không hạn chế muối với bệnh thận mất muối (sodium-wasting nephropathy) | Trường hợp ngoại lệ cần biết |

**Có bất đồng thật giữa các hiệp hội** — cần nêu rõ trong tài liệu thay vì giả vờ có một con số duy nhất:

| Hướng dẫn | Khuyến nghị protein cho CKD G3–5 |
|---|---|
| KDOQI 2020 | 0,55–0,60 g/kg (không ĐTĐ) · 0,6–0,8 g/kg (có ĐTĐ) — mức bằng chứng 1A |
| **KDIGO 2024** | **0,8 g/kg** — mức bằng chứng 2C |
| UKKA (Anh) | Không hạn chế |

→ **Đây là chất liệu tuyệt vời cho slide "Challenges & Learnings"**: ba hiệp hội quốc tế cho ba con số khác nhau trên cùng một nhóm bệnh nhân. Hệ thống phải chọn một và **ghi rõ đã chọn theo hướng dẫn nào** — đó chính là lý do trường `guideline_ref` tồn tại trong thiết kế.

### 1.2. Một nhận định lâm sàng quan trọng mà rule hiện tại bỏ sót

KDIGO 2024 nhấn mạnh chế độ ăn **thiên về thực vật**, và nêu: kali và phosphat từ **thực phẩm thực vật ít chế biến có sinh khả dụng thấp hơn nhiều** so với từ thực phẩm siêu chế biến.

Nghĩa là: **300 mg kali từ rau ≠ 300 mg kali từ nước ngọt có phụ gia phosphat.** Bộ kiểm tra hiện tại chỉ cộng tổng mg — sẽ phạt oan rau xanh và bỏ lọt thực phẩm siêu chế biến.

→ **Đề xuất ticket `CLN-09`:** thêm cột `bioavailability_class` (plant / animal / ultra-processed-additive) vào `food_items`, và áp hệ số khi kiểm tra ngưỡng K/P. Đây là cải tiến nhỏ về code nhưng đúng về lâm sàng, và là điểm rất dễ ghi điểm khi Q&A.

### 1.3. ADA Standards of Care in Diabetes — 2026

Công bố tháng 1/2026 (*Diabetes Care*, tập 49, Supplement 1). Cập nhật liên quan trực tiếp:

| Nội dung 2026 | Ảnh hưởng tới dự án |
|---|---|
| Người **cao tuổi** mắc ĐTĐ: protein **tối thiểu 0,8 g/kg/ngày** để duy trì khối nạc; có thể cao hơn nếu cần phục hồi khối cơ | ⚠️ Cộng với KDIGO PP 3.3.1.5 → với bệnh nhân **cao tuổi + ĐTĐ + CKD**, hạ protein xuống dưới 0,8 là **đi ngược cả hai hướng dẫn**. Rule hiện tại cho phép xuống 0,6 → cần sửa |
| Sàng lọc thừa cân/béo phì bằng **BMI kết hợp tỉ lệ eo–hông hoặc đo thành phần cơ thể** | ✅ **Xác nhận trực tiếp biến Tầng 2 bạn vừa thêm** (số đo vòng, InBody). Nay có căn cứ hướng dẫn 2026 để trích dẫn, không còn là suy luận của đội |
| Mục tiêu giảm cân **5–7%** để cải thiện đường huyết và nguy cơ tim mạch | Thay cho công thức giảm cân chung chung hiện tại |
| Nhấn mạnh nguồn carbohydrate **chất lượng cao, ít chế biến, giàu xơ** — bất kể tổng lượng carb | Củng cố rule chất xơ; nên thêm tiêu chí "ít chế biến" |
| Theo dõi dinh dưỡng liên tục để **bảo tồn khối nạc, phòng suy dinh dưỡng** khi dùng thuốc giảm cân | Liên quan nếu bệnh nhân dùng GLP-1 |
| Đánh giá **yếu tố xã hội quyết định sức khoẻ** để thiết kế can thiệp, tối đa hoá công bằng y tế | ✅ **Hậu thuẫn cho biến khả năng chi trả bạn thêm** |

**Lưu ý:** ADA cho biết sẽ có **báo cáo đồng thuận mới về dinh dưỡng trong năm 2026**. Nếu ra trước Demo Day, R2 cần rà lại.

### 1.4. Việc phải làm ngay với `clinical_rules.csv`

| Rule hiện tại | Vấn đề | Sửa thành |
|---|---|---|
| `CKD-PRO-01` max 0.8, ref "KDIGO/KDOQI" | Gộp hai hướng dẫn khác nhau vào một dòng | Tách rõ: `guideline_ref = "KDIGO 2024 Rec 3.3.1.1"` |
| `CKD-PRO-02` min 0.6 | Không phải khuyến nghị của KDIGO 2024 | Đổi thành `min 0.8` theo KDIGO 2024, **hoặc** giữ 0.6 nhưng ghi rõ ref là KDOQI 2020 và ghi nhận là lựa chọn có ý thức |
| *(chưa có)* | Thiếu chặn an toàn người cao tuổi | Thêm `CKD-PRO-03`: nếu tuổi ≥ 65 **và** có dấu hiệu suy yếu/thiểu cơ → **không** áp trần protein thấp, gắn cờ `needs_expert_review` |
| *(chưa có)* | Thiếu chặn "chuyển hoá không ổn định" | Thêm `CKD-PRO-04`: cờ `metabolically_unstable` → **không** áp chế độ hạn chế protein |
| *(chưa có)* | Thiếu trần trên | Thêm `CKD-PRO-05`: max 1.3 g/kg (PP 3.3.1.1) |

> Đây là loại chi tiết phân biệt một dự án "có tra hướng dẫn" với một dự án "đoán ngưỡng". Chi phí: khoảng 4 giờ.

---

## 2. BẰNG CHỨNG MỚI NHẤT CHO RQ1 — KIẾN TRÚC LAI

### 2.1. Nguồn mạnh nhất: Frontiers in Nutrition, tháng 7/2026

Nghiên cứu công bố **cách đây vài ngày** (doi 10.3389/fnut.2026.1894893) so sánh trực tiếp bộ khuyến nghị dựa trên tri thức với LLM cấu hình RAG và tinh chỉnh có giám sát (SFT), trên các hồ sơ người dùng tổng hợp.

Kết luận cốt lõi:

> Khi đánh giá đối đầu trên các hồ sơ bệnh không lây nhiễm, **hiệu năng của ChatGPT cải thiện rõ rệt khi được cung cấp sẵn mục tiêu năng lượng**, nhưng **hệ thống dựa trên tri thức vẫn cho ra kế hoạch chính xác nhất**.

**Đây gần như là mô tả chính xác kiến trúc của dự án:** bộ tính định mức xác định tính ra mục tiêu năng lượng → đưa cho LLM → LLM chọn món. Nghiên cứu này nói rằng đó đúng là cách làm cho kết quả tốt nhất.

Thêm một điểm về phương pháp: nghiên cứu dùng **hồ sơ người dùng tổng hợp** để đánh giá, với dung sai **±250 kcal** cho năng lượng. → Xác nhận phương pháp 60 ca mô phỏng của dự án là chuẩn mực được chấp nhận trong ngành, không phải giải pháp tạm.

### 2.2. Bảng bằng chứng tổng hợp (đã cập nhật)

| Bằng chứng | Con số | Nguồn | Năm |
|---|---|---|---|
| Hệ thống dựa trên tri thức > LLM thuần; LLM cải thiện rõ khi được cấp mục tiêu năng lượng | định tính, đối đầu | Front Nutr, doi 10.3389/fnut.2026.1894893 | **7/2026** |
| LLM lập thực đơn ĐTĐ2: nhiều mô hình cho năng lượng **thấp hơn có ý nghĩa** so với chuẩn chuyên gia | p < 0,05 | Healthcare, doi 10.3390/healthcare14060739 | **2026** |
| Cùng nghiên cứu: **mọi mô hình trừ Claude Sonnet 4.5** cho thực đơn **ít chất xơ hơn** chuẩn | — | như trên | **2026** |
| RAG lâm sàng trong thận học **giảm đáng kể ảo giác** khi trả lời câu hỏi phức tạp về chế độ ăn cho bệnh thận | — | Miao et al., dẫn trong Front AI 2026 | 2024 |
| Truy xuất dữ liệu **có cấu trúc** cải thiện độ chính xác so với LLM thường (NutriRAG) | — | Zhou et al., dẫn trong Front AI 2026 | **2026** |
| LLM hạn chế ở dinh dưỡng điều trị bệnh mạn, **tính toán dinh dưỡng**, và **độ chính xác khi dùng ngôn ngữ khác** | — | JMIR 2025;1:e78625 | 2025 |
| LLM ước tính từ ảnh: MAPE năng lượng | ChatGPT-4o **35,8%** · Claude 3.5 **35,8%** · Gemini 1.5 Pro **64–110%** | Curr Dev Nutr, PMID 41081011 | 2025 |
| Thị giác chuyên dụng tốt nhất | MAE 41,3 kcal / MAPE **16,5%** | Nutrition5k, CVPR | 2021 |

⚠️ **Điểm cần trung thực:** dòng cuối bảng đã 5 năm tuổi. Xem §2.3.

### 2.3. Một bằng chứng ngược chiều — phải nêu, không được giấu

**NutriMLLM** (arXiv 2606.08948, **8/6/2026**): mô hình đa phương thức cho phân tích **vi chất** từ ảnh, phủ **65 chất dinh dưỡng**, đánh giá theo 4 thành phần (khả năng từ chối trả lời, ảo giác, tính khả dụng, độ chính xác số theo từng chất). Kết quả: biến thể lớn nhất **ngang hoặc vượt GPT-5, Gemini 3 và Claude Sonnet 4.5** ở đa số chất.

**Nghĩa là:** lĩnh vực đang tiến rất nhanh. Lập luận "thị giác chưa đủ chính xác" **vẫn đúng ở thời điểm hiện tại và với ngưỡng ±10%**, nhưng sẽ không đúng mãi.

→ **Cách phát biểu nên dùng trong pitch:**
> *"Tại thời điểm này, với ngưỡng lâm sàng ±10%, chưa có mô hình nào đủ chính xác để tự sinh con số. Kiến trúc của chúng em tách bạch phần chọn món và phần tính số — nên khi mô hình đủ tốt, chỉ cần thay một node, không phải viết lại hệ thống."*

Cách nói này vừa trung thực, vừa biến hạn chế của lĩnh vực thành ưu điểm kiến trúc. Nói vống "AI không bao giờ làm được" sẽ bị giám khảo có đọc arXiv bắt bài ngay.

---

## 3. BENCHMARK MỚI — KHÔNG CÒN PHẢI TỰ XÂY TỪ ĐẦU

Bản 1.0 khuyên bỏ MedQA/MedArena và tự xây 60 ca. Vẫn nên tự xây bộ ca tiếng Việt, **nhưng nay đã có hai benchmark đúng bài toán để đối chiếu và học phương pháp**.

### 3.1. FAM-Bench — sát bài toán của dự án nhất

*A Multimodal Benchmark for Condition-Aware Food-as-Medicine Reasoning* — arXiv 2605.31410, **5/2026**.

| Đặc điểm | Giá trị |
|---|---|
| Quy mô | **2.500 mẫu đã được chuyên gia dinh dưỡng thẩm định**, từ 3.859 công thức |
| Phạm vi | **13 tình trạng sức khoẻ liên quan chế độ ăn** |
| Câu hỏi cốt lõi | Không chỉ *"món này là gì?"* hay *"chứa gì?"* mà **"món này có phù hợp với tình trạng bệnh này không?"** |
| Mô hình đã đánh giá | GPT-5.4, Claude Sonnet 4.6, và 3 mô hình khác |
| Mã & dữ liệu | Đã công bố kèm bộ script đánh giá |

**Đây chính xác là câu hỏi mà VNutriCare phải trả lời.** Giá trị sử dụng:
1. **Học cấu trúc đánh giá** — không phải tự nghĩ ra tiêu chí
2. **Có mốc so sánh quốc tế** — kết quả của đội đặt cạnh GPT-5.4 và Claude Sonnet 4.6 trên cùng khung
3. **Tăng độ tin cậy học thuật** của phần Evaluation Evidence

→ **Ticket `EVL-07`: đọc FAM-Bench, áp dụng khung tiêu chí cho bộ 60 ca tiếng Việt.** 6 giờ. Ưu tiên cao — đây là cách rẻ nhất để nâng chất lượng deliverable #10.

### 3.2. NutriBench — khớp đúng phương thức đầu vào của dự án

*A dataset for evaluating large language models on nutrition estimation **from meal descriptions*** — arXiv 2407.12843.

Quan trọng: đánh giá từ **mô tả bằng chữ**, không phải từ ảnh. Dự án VNutriCare nhận đầu vào là **mô tả mâm cơm bằng text** → đây mới là benchmark đúng phương thức, chứ không phải các benchmark ảnh.

### 3.3. Các benchmark/dataset khác đáng biết (2025–2026)

| Tên | Năm | Nội dung |
|---|---|---|
| **DiningBench** | 4/2026 | Benchmark phân cấp, đa góc nhìn cho nhận thức và suy luận trong lĩnh vực ăn uống |
| **January Food Benchmark (JFB)** | 2025 | Benchmark công khai + bộ đánh giá cho phân tích thực phẩm đa phương thức |
| **ACETADA** | 2025 | Ảnh bữa ăn có dinh dưỡng **do chuyên gia thẩm định**, kèm GPS và mốc thời gian |
| **MetaFood3D** | 2024 | Dataset 3D thực phẩm có chú thích dinh dưỡng |
| **Food2K / ISIA Food-500 / VIREO Food-172** | 2020–2023 | Phân loại ảnh quy mô lớn |
| **Recipe1M+ / RecipeQA** | 2018–2019 | Truy hồi ảnh ↔ công thức |

→ Đưa bảng này vào tài liệu để chứng minh đội **đã khảo sát bối cảnh nghiên cứu**, không chỉ ghép thư viện.

---

## 4. SỐ LIỆU VIỆT NAM — CẬP NHẬT VÀ ĐÍNH CHÍNH

### 4.1. ⚠️ Đính chính con số muối

Bản 1.0 và tài liệu Word hiện ghi **"8,1–9,4 g muối/ngày"**. Đây là **gộp hai cuộc điều tra khác nhau** — không nên viết như một khoảng.

| Con số | Nguồn | Tình trạng |
|---|---|---|
| **8,1 g/ngày** | **Điều tra STEPS 2021** — được chính Viện Dinh dưỡng dẫn lại trong bài đăng **12/3/2026** | ✅ **Dùng con số này** |
| 9,4 g/ngày (nam 10,5 · nữ 8,3) | Điều tra trước đó | Chỉ dùng khi nói về xu hướng giảm theo thời gian |

→ **Sửa slide và tài liệu thành: "8,1 g muối/ngày (STEPS 2021), gần gấp đôi khuyến nghị 5 g của WHO"** — một con số, một nguồn, một năm.

### 4.2. Số liệu và văn bản mới bổ sung

| Nội dung | Chi tiết | Nguồn |
|---|---|---|
| Gánh nặng bệnh không lây nhiễm | Chiếm **gần 3/4 tổng gánh nặng bệnh tật** tại Việt Nam | Bài đăng 6/2026, dẫn nghiên cứu gánh nặng bệnh tật toàn cầu |
| Chiến lược Quốc gia về Dinh dưỡng | Giai đoạn **2021–2030, tầm nhìn 2045** — Quyết định **02/QĐ-TTg** (2022) | Thủ tướng Chính phủ |
| Kế hoạch quốc gia phòng chống bệnh không lây nhiễm | Giai đoạn **2022–2025** — Quyết định **155/QĐ-TTg** (29/1/2022) | Thủ tướng Chính phủ |
| Mục tiêu quốc gia về muối | Giảm tiêu thụ trung bình còn **< 7 g/người/ngày vào 2030** | Chương trình Sức khỏe Việt Nam |
| Tạp chí trong nước đang hoạt động | **Tạp chí Dinh dưỡng và Thực phẩm** (số 21(4)−2025) | Có bài về kiến thức–thực hành sử dụng muối |

→ Việc dẫn được **Quyết định 02/QĐ-TTg** và mục tiêu **< 7 g muối vào 2030** cho thấy dự án gắn với chính sách quốc gia đang hiệu lực — mạnh hơn nhiều so với chỉ dẫn khuyến nghị của WHO.

### 4.3. ⚠️ Đính chính về bảng thành phần thực phẩm

Bản 1.0 nói bảng 2007 trên FAO như thể là bản mới nhất. **Không đúng.**

| Phiên bản | Số thực phẩm | Số chất dinh dưỡng | Truy cập |
|---|---|---|---|
| 1972 | 200 (bản Đông Dương 1941) → bản VN | — | Lịch sử |
| 2000 | 501 | 15 chất chính | Sách in |
| **2007** | **526** | **86 chất/thực phẩm** (có purin, K, P, Na, tỉ lệ thải bỏ) | ✅ **PDF miễn phí trên FAO** |
| Bản sau 2007 | — | Cập nhật số liệu phân tích 2007–2014 | Sách in |
| **2017** | **628** | 15 chất chính + bảng riêng cho acid amin/béo/khoáng. Kèm **"Bảng thành phần thức ăn Việt Nam 2017"** tra cứu **theo món ăn** | Sách in / phần mềm thương mại |

**Khuyến nghị cập nhật:**

1. **Vẫn dùng bản 2007 (FAO) làm nền** — vì là bản duy nhất miễn phí, đầy đủ 86 chất/thực phẩm, và **có purin** (thiết yếu cho gout, các bản mô tả 15 chất chính không chắc có).
2. **Nhưng phải ghi rõ trong tài liệu là "bản 2007"**, không được viết "bản mới nhất".
3. **Nếu tiếp cận được bản 2017 qua thư viện trường** (628 thực phẩm, và đặc biệt là bảng **tra cứu theo món ăn**) → đối chiếu và cập nhật những mục lệch. Bảng theo món ăn 2017 có thể tiết kiệm phần lớn công việc của ticket `DAT-04`.
4. Ghi `source_ref` chính xác đến phiên bản: `NIN 2007, tr.X` chứ không phải `NIN`.

→ **Bổ sung vào `DAT-07`:** thêm bước hỏi thư viện trường/khoa Dinh dưỡng về bản 2017.

---

## 5. TỔNG HỢP VIỆC PHẢI LÀM

### 5.1. Ticket mới và ticket sửa

| Mã | Nội dung | Owner | Giờ | Ưu tiên |
|---|---|---|---|---|
| `CLN-10` | **Sửa `clinical_rules.csv` theo KDIGO 2024 + ADA 2026**: tách guideline_ref, thêm CKD-PRO-03/04/05 (người cao tuổi, chuyển hoá không ổn định, trần 1,3 g/kg) | R2 | 4h | 🔴 **P0** |
| `EVL-07` | Đọc FAM-Bench, áp khung tiêu chí cho bộ 60 ca tiếng Việt | R2 + R1 | 6h | 🔴 P0 |
| `DAT-08` *(đổi số từ DAT-07)* | Trích xuất bảng NIN 2007 từ PDF FAO **+ hỏi thư viện về bản 2017** | R2 | 10–14h | 🔴 P0 |
| `DAT-07` *(đã làm)* | Mở rộng schema `food_items`: `sugar_g` + nguồn GI riêng + helper GL. Xem §8 | R2 | 3h | ✅ P1 |
| `CLN-09` | Thêm `bioavailability_class` cho K/P (thực vật vs siêu chế biến) | R2 | 5h | 🟡 P2 |
| `DAT-10` | Rà NutriBench để tham chiếu cách đánh giá ước tính từ mô tả text | R1 | 3h | 🟡 P2 |
| `DAT-00` *(sửa)* | Bổ sung: đổi "8,1–9,4 g muối" thành **"8,1 g (STEPS 2021)"** trong mọi tài liệu | R2 | 1h | 🔴 P0 |

### 5.2. Sửa trong tài liệu Word

| Vị trí | Sửa gì |
|---|---|
| Ch.1, bảng dịch tễ | Thêm dòng "NCD chiếm ~3/4 gánh nặng bệnh tật (2026)" |
| Ch.1, mọi chỗ nhắc muối | **8,1 g (STEPS 2021)** — bỏ khoảng 8,1–9,4 |
| Ch.1, pain point | Thêm điểm đau kinh tế + dẫn Quyết định 02/QĐ-TTg và mục tiêu <7 g muối/2030 |
| Ch.2, bảng dữ liệu nền | Ghi rõ "Bảng TPTP VN **2007**"; ghi chú tồn tại bản 2017 (628 thực phẩm) |
| Ch.2, Tầng 2 | Thêm dẫn **ADA 2026** cho việc dùng BMI + tỉ lệ eo–hông + đo thành phần cơ thể |
| Ch.3, RQ1 | Thay bằng chứng bằng nguồn Front Nutr 7/2026 (mới nhất, đúng bài toán nhất) |
| Ch.3, mục eval | Thêm FAM-Bench và NutriBench làm khung tham chiếu |
| Ch.3 | Thêm **RQ9** (ràng buộc chi phí) như bản 1.0 đã đề xuất |
| Phụ lục | Thay toàn bộ danh mục nguồn bằng §6 dưới đây |

---

## 6. DANH MỤC NGUỒN — SẮP THEO ĐỘ MỚI

### 2026
1. *An AI-driven multivariate approach for personalized healthy eating recommendations…* Frontiers in Nutrition, **7/2026**. doi:10.3389/fnut.2026.1894893
2. *NutriMLLM: Multimodal Large Language Models for Dietary Micronutrient Analysis.* arXiv:2606.08948, **6/2026**
3. *FAM-Bench: A Multimodal Benchmark for Condition-Aware Food-as-Medicine Reasoning.* arXiv:2605.31410, **5/2026**
4. *Epicure: Navigating the Emergent Geometry of Food Ingredient Embeddings.* arXiv:2605.22391, **5/2026**. CC BY 4.0
5. *An LLM-RAG Approach for Healthy Eating Index-Informed Personalized Food Recommendations.* arXiv:2605.15213, **5/2026**
6. *An explainable graph retrieval augmented generation framework for personalized nutrition recommendation.* Frontiers in AI, **4/2026**
7. *DiningBench: A Hierarchical Multi-view Benchmark…* arXiv:2604.10425, **4/2026**
8. *Evaluation of LLMs in retrieving food and nutritional context for RAG systems.* arXiv:2603.09704, **3/2026**
9. *LLMs as Clinical Nutrition Decision Tools: Quantitative Bias and Guideline Deviation in T2DM Meal Planning.* Healthcare, **3/2026**. doi:10.3390/healthcare14060739
10. **ADA Standards of Care in Diabetes—2026.** Diabetes Care, tập 49, Supplement 1, **1/2026**
11. Viện Dinh dưỡng — bài đăng Ngày Thận Thế giới, **12/3/2026** (dẫn STEPS 2021: 8,1 g muối/ngày)

### 2025
12. *Performance Evaluation of 3 Large Language Models for Nutritional Content Estimation from Food Images.* Curr Dev Nutr, 2025. PMID 41081011
13. *Comparison of Accuracy… Between Professional Nutritionists and Chatbots.* Nutrients, 2025. PMC12526241
14. *Improving Personalized Meal Planning with LLMs: Identifying and Decomposing Compound Ingredients.* Nutrients, 2025. PMC12073434
15. *Evaluating LLMs and RAG Enhancement for Delivering Guideline-Adherent Nutrition Information for CVD Prevention.* JMIR 2025;1:e78625
16. *Comprehensive Evaluation of Large Multimodal Models for Nutrition Analysis (ACETADA).* arXiv:2507.07048
17. *January Food Benchmark (JFB).* arXiv:2508.09966
18. Tạp chí Dinh dưỡng và Thực phẩm, **21(4)−2025**

### 2024 và trước — vẫn là chuẩn hiện hành
19. **KDIGO 2024 Clinical Practice Guideline for the Evaluation and Management of CKD** (thay thế bản 2012)
20. *NutriBench: a dataset for evaluating LLMs on nutrition estimation from meal descriptions.* arXiv:2407.12843
21. *DDID: diet–drug interactions.* Briefings in Bioinformatics, 2024
22. *FooDrugs.* Database (Oxford), 2023. PMID 37951712
23. *Cost and affordability of healthy diets in Vietnam.* Public Health Nutrition, 2023. PMID 38037710 *(dữ liệu 2016–2020 — cũ nhưng chưa có bản thay thế cho Việt Nam)*
24. **Viện Dinh dưỡng – Bộ Y tế. Bảng thành phần thực phẩm Việt Nam, NXB Y học, 2007.** 526 thực phẩm, 86 chất. PDF: `fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf`
25. Thames Q. et al. *Nutrition5k.* CVPR 2021. arXiv:2103.03375. CC BY 4.0
26. Điều tra STEPS 2021, Bộ Y tế
27. Quyết định 02/QĐ-TTg (2022) — Chiến lược Quốc gia về Dinh dưỡng 2021–2030
28. Quyết định 155/QĐ-TTg (2022) — Kế hoạch phòng chống bệnh không lây nhiễm 2022–2025
29. Thông tư 08/2024/TT-BYT — sàng lọc dinh dưỡng cho người bệnh

---

## 7. BA ĐIỀU QUAN TRỌNG NHẤT

1. **Sửa bộ rule CKD theo KDIGO 2024 trước khi làm bất cứ việc gì khác** (`CLN-10`, 4 giờ). Hệ thống hiện đang dùng ngưỡng của một hướng dẫn đã bị thay thế, và **thiếu hai chốt an toàn cho người cao tuổi** — đúng nhóm bệnh nhân mục tiêu.

2. **Dùng FAM-Bench làm khung đánh giá.** Một benchmark 5/2026, 2.500 mẫu do chuyên gia thẩm định, hỏi đúng câu hỏi của dự án. Rẻ hơn và uy tín hơn nhiều so với tự nghĩ tiêu chí.

3. **Đổi cách phát biểu về thị giác trong pitch.** Bằng chứng 6/2026 cho thấy mô hình đa phương thức đang tiến rất nhanh. Nói *"hiện chưa đủ chính xác cho ngưỡng ±10%, và kiến trúc của chúng em cho phép thay thế khi nó đủ tốt"* — trung thực, và biến hạn chế thành ưu điểm thiết kế.

---

## 8. CHỌN BỆNH CHÍNH & TÍNH KHẢ THI DỮ LIỆU ĐTĐ2 (deep-dive 01/08/2026)

> Bối cảnh: rà soát dataset bệnh mãn tính (HuggingFace, Kaggle, NIN, NHANES, GI tables) để chốt **một bệnh chính** cho MVP dinh dưỡng, dù bệnh nhân đa bệnh. Kết quả đã đưa vào code (DAT-07) và Decision Log (DEC-009, DEC-010).

### 8.1. Kết luận: chọn **ĐTĐ2 làm bệnh chính** (anchor tim-chuyển hoá)

THA và CKD-sớm là **comorbidity modifier** chồng lên, không phải bệnh riêng lẻ. Lý do:

| Tiêu chí | Vì sao ĐTĐ2 thắng |
|---|---|
| Hợp RULE-1 | Luật dinh dưỡng ĐTĐ2 (kcal, %carb, GI/GL, đường tự do) **tính được bằng SQL** — LLM chỉ chọn món, Python tính số |
| Trung tâm đa bệnh | ĐTĐ2 là hub kéo theo THA + rối loạn lipid + CKD sớm → chọn nó cho phép layer các modifier |
| Dữ liệu & guideline | Phong phú nhất; ADA 2026 + WHO + FAO/WHO 1998 |
| Giảm gánh nguồn khó | **Purine** (cột khó nguồn nhất, không có trong NIN/USDA) là chuyện của gout, **không cần cho anchor ĐTĐ2** |

### 8.2. Phát hiện then chốt về dataset

**Hầu hết dataset "diabetes/heart" trên HF/Kaggle là dữ liệu DỰ ĐOÁN bệnh** (Pima, Cleveland 303 dòng, BRFSS 253k, Diabetes 130-US) — **không phải dữ liệu dinh dưỡng** và không dùng được cho engine tính món. Nguồn thật cho engine vẫn là: **NIN 2017/2007 + USDA** (thành phần) và **GI tables** (Atkinson 2021 + Chan 2001) — đúng như bản 2.0 đã xác định. Các dataset dự đoán chỉ dùng làm **bối cảnh dân số / validate**, không phải lõi.

### 8.3. Thay đổi schema đã áp (DAT-07)

`FoodItem` ([src/clinical/models.py](../src/clinical/models.py)) được bổ sung:
- `sugar_g` — cho ngưỡng **đường tự do WHO** (<10%, lý tưởng <5% năng lượng). Ràng buộc `sugar_g ≤ carb_g`.
- `gi_source` + `gi_source_ref` — GI có **nguồn riêng**, tách khỏi `source_ref` của NIN (RULE-2). Model chặn `gi_index` không có nguồn GI.
- `available_carb_g` (= carb − xơ) và `glycemic_load(grams)` — GL tính trên carb khả dụng, **None-safe** khi thiếu GI.

### 8.4. Nguồn GI và rủi ro (đã seed `data/seeds/gi_values.csv`)

- **[Chan HMS et al. 2001, Eur J Clin Nutr 55:1076–1083](https://www.nature.com/articles/1601265)** (glucose=100, n=12): nguồn duy nhất đo **GI món Việt** mà bảng quốc tế thiếu. Đã trích 7 trị: bún/bánh phở tươi **40**, cơm tẻ jasmine **109**, xôi **94**, na **58**, sữa đặc **61**, miến (proxy) **39**.
- **[Atkinson 2021](https://ajcn.nutrition.org/article/S0002-9165(22)00494-4/fulltext)** (ISO, >4000 món): dùng cho staple/quả quốc tế còn thiếu — **chưa transcribe**, thuộc DAT-08. **Không điền GI từ trí nhớ** (DEC-008).
- **Rủi ro GI:** phủ thưa + mâu thuẫn giữa nguồn (VD phở GI 53 vs "cao"). GI món Việt cực cao ngoài dự đoán (gạo tẻ 109 > glucose) — **lật lại giả định "cơm ta GI thấp"**. → Menu engine **phải** suy giảm mềm theo lượng carb + nhóm thực phẩm khi thiếu GI, không coi thiếu GI là GL=0.

### 8.5. Việc tiếp theo

1. **DAT-08**: transcribe GI staple/quả quốc tế từ Atkinson 2021 (gạo lứt, khoai, ngô, yến mạch, bánh mì, các loại quả).
2. **CLN-02/CLN-10**: thêm rule ĐTĐ2 dùng `sugar_g` (đường tự do WHO) và GL/ngày (khi đủ phủ GI).
3. Cân nhắc đo riêng GI **miến dong** để thay trị proxy 39 bằng số đo thật.
