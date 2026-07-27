# NGHIÊN CỨU BỔ SUNG — BẰNG CHỨNG, DATASET, MÔ HÌNH VÀ PHƯƠNG ÁN AI

> Dự án: **VNutriCare** — VMEC-10 · AI20K Build Cohort 3
> Ngày: 27/07/2026 · Bổ sung cho `KeHoachDuAn_NutriCareAgent_VMEC10.docx`
> Mục đích: (1) kiểm chứng 4 nội dung vừa bổ sung, (2) cấp bằng chứng có nguồn cho từng RQ và mục tiêu, (3) kiểm kê dataset/mô hình có sẵn và chốt phương án xây dựng AI.

---

## 0. Phán quyết nhanh về 4 nội dung bạn vừa thêm

| # | Nội dung thêm | Phán quyết | Ghi chú |
|---|---|---|---|
| 1 | Đổi tên **VNutriCare**, Cohort 3 | ✅ Ghi nhận | Cần cập nhật đồng bộ trong repo, README, pitch deck |
| 2 | Biến **nghề nghiệp + tổng thu nhập gia đình** → điều chỉnh theo khả năng chi trả | ✅ **Có cơ sở mạnh** | Xem §1.5 — số liệu FAO/Cambridge cho thấy đây là ràng buộc thật, không phải tính năng phụ. Nhưng cách hỏi cần đổi (§1.5.3) |
| 3 | Bài báo **Epicure** (arXiv 2605.22391) | ✅ **Có thật, license CC BY 4.0, embedding tải được ngay** | Nhưng dùng đúng chỗ mới có giá trị — xem §3.1. **Không** dùng cho con số dinh dưỡng |
| 4 | **Dữ liệu app sức khoẻ trên smartphone** (Tầng 4) | 🟡 Đúng hướng, cần nói rõ hơn | Nên ghi cụ thể là qua **Apple HealthKit / Google Health Connect**, không phải "app nói chung" — xem §2.4 |

**Một lỗi soạn thảo nhỏ:** ô "Nhân khẩu học" trong bảng Tầng 1 hiện có chữ *"vùng miền"* xuất hiện **hai lần**. Cần sửa.

---

## 1. BẰNG CHỨNG CHO CÁC LUẬN ĐIỂM VÀ CÂU HỎI NGHIÊN CỨU

### 1.1. RQ1 — Kiến trúc lai có giảm sai lệch định lượng so với LLM tự tính không?

Đây là RQ trung tâm. Trước đây luận điểm "LLM lệch định lượng hệ thống" trong tài liệu nghiên cứu **không có nguồn cụ thể**. Nay đã có ba nguồn độc lập:

| Bằng chứng | Con số | Nguồn |
|---|---|---|
| LLM ước tính dinh dưỡng từ ảnh món ăn: sai số phần trăm tuyệt đối trung bình (MAPE) | ChatGPT-4o **35,8%** (năng lượng) · Claude 3.5 Sonnet **35,8%** · Gemini 1.5 Pro **64,2–109,9%** | *Performance Evaluation of 3 Large Language Models for Nutritional Content Estimation from Food Images*, Curr Dev Nutr (2025), PMID 41081011 |
| Hướng sai lệch | **Tất cả mô hình đều ước tính THẤP hơn thực tế**, và sai lệch **tăng dần theo kích thước khẩu phần** (độ dốc bias –0,23 đến –0,50) | như trên |
| LLM lập thực đơn ĐTĐ týp 2 theo chuẩn 1800 kcal | Gemini 2.5 Pro, ChatGPT-5 Auto, Gemini 2.5 Flash cho **tổng năng lượng thấp hơn có ý nghĩa thống kê** (p < 0,05) so với thực đơn tham chiếu do chuyên gia dinh dưỡng soạn | *LLMs as Clinical Nutrition Decision Tools: Quantitative Bias and Guideline Deviation in T2DM Meal Planning*, Healthcare (2026), doi 10.3390/healthcare14060739 |
| Tính lặp lại | Giá trị dinh dưỡng do cùng một AI trả về ở các ngày khác nhau lệch tới **45%** so với tính toán của chuyên gia | Nutrients (2025), PMC12526241 |
| Mô hình thị giác chuyên dụng tốt nhất (không phải LLM) | Nutrition5k: MAE **41,3 kcal** / MAPE **16,5%** (dùng thêm dữ liệu chiều sâu); chỉ ảnh 2D: MAPE **26,1%** | Thames et al., *Nutrition5k*, CVPR 2021, arXiv:2103.03375 |

**Ý nghĩa cho dự án — đây là lập luận mạnh nhất các bạn có:**

> Ngưỡng lâm sàng mà chính dự án đặt ra là **±10% năng lượng**. Mô hình thị giác chuyên dụng tốt nhất hiện nay đạt **16,5%**; LLM đa phương thức đạt **~36%**. Nghĩa là **không có mô hình nào hiện đủ chính xác để tự sinh con số dinh dưỡng cho bệnh nhân mãn tính**. Đó không phải ý kiến của đội — đó là số đo công bố.

Thêm nữa, hướng sai lệch là **ước tính thấp và càng khẩu phần lớn càng lệch nhiều**. Với bệnh nhân suy thận hạn chế đạm, sai theo hướng "thấp hơn thực tế" là hướng nguy hiểm nhất: hệ thống báo an toàn trong khi bệnh nhân đã vượt ngưỡng.

→ Đây là câu trả lời hoàn chỉnh cho câu hỏi giám khảo *"tại sao không để LLM làm hết cho nhanh?"*

### 1.2. RQ2 — HITL

Chưa tìm được nghiên cứu đo trực tiếp "HITL cải thiện an toàn thực đơn bao nhiêu %" — **đây là khoảng trống, và cũng là lý do RQ2 đáng làm**. Bằng chứng gián tiếp hiện có:

- Nghiên cứu Healthcare (2026) ở trên kết luận thẳng rằng độ an toàn lâm sàng và mức tuân thủ guideline của thực đơn do LLM sinh ra **vẫn còn chưa chắc chắn**, và đặt câu hỏi liệu LLM hiện tại có thể đóng vai trò công cụ hỗ trợ quyết định dinh dưỡng đáng tin cậy hay không.
- Thông tư 08/2024/TT-BYT đã quy định bác sĩ điều trị **bắt buộc hội chẩn khoa Dinh dưỡng** với bệnh nhân suy dinh dưỡng nặng — nghĩa là HITL không chỉ là lựa chọn thiết kế mà phù hợp với khung pháp lý hiện hành.

**Khuyến nghị:** giữ RQ2 nhưng đổi cách phát biểu cho khiêm tốn và đo được hơn:
> *"Chuyên gia dinh dưỡng phát hiện được những loại lỗi nào mà bộ kiểm tra tự động bỏ sót, với tần suất bao nhiêu?"*

Đây là câu hỏi trả lời được bằng 60 ca mô phỏng, và kết quả có giá trị công bố thật — vì hiện chưa ai đo.

### 1.3. RQ5 — Tương tác thuốc–thực phẩm

| Nguồn | Quy mô | Đánh giá |
|---|---|---|
| **FooDrugs** (IMDEA Food Institute) | **3.430.062** tương tác tiềm năng (1.108.429 từ khai phá văn bản; 2.321.633 suy ra từ dữ liệu biểu hiện gene). Công khai trên Zenodo | ⚠️ **Không dùng trực tiếp được.** Mô hình DistilBERT trích xuất đạt **F1 = 0,77** → khoảng 23% sai. Đây là tương tác *tiềm năng*, chưa được kiểm chứng lâm sàng |
| **DDID** | 23.950 tương tác, 1.338 thực phẩm/thảo dược, 1.516 thuốc | ⚠️ Vẫn cần kiểm license; quy mô thừa xa nhu cầu 4 nhóm bệnh |
| **DrugBank** 5.1.10 | 15.451 thuốc | ⚠️ Chú thích tương tác thực phẩm hạn chế và không đầy đủ |

**Kết luận quan trọng:** nghiên cứu FooDrugs tự nhận rằng các CSDL hiện có "chú thích tương tác thực phẩm–thuốc còn hạn chế, không đầy đủ và ít chồng lấp nhau". Nếu nạp thẳng 3,4 triệu cặp "tiềm năng" vào hệ thống cảnh báo, kết quả sẽ là **cảnh báo tràn lan** — đúng cái bẫy mà quy tắc R10.7 của dự án đã cảnh báo (cảnh báo phải hành động được, không được cảnh báo bừa).

→ **Quyết định ADR-005 (curate thủ công ~80 cặp) là đúng, và giờ có lý do mạnh hơn để bảo vệ.** Cách dùng FooDrugs/DDID hợp lý: làm **nguồn sinh ứng viên** cho quá trình curate, không phải nguồn cảnh báo trực tiếp.

### 1.4. RQ6 — Phân rã mâm cơm / món phức hợp

Có nghiên cứu trực tiếp về đúng bài toán này: *Improving Personalized Meal Planning with Large Language Models: Identifying and Decomposing Compound Ingredients* (Nutrients, 2025, PMC12073434). Nghiên cứu nhấn mạnh việc nhận diện và phân rã nguyên liệu phức hợp là **thiết yếu để xác định và thay thế nguyên liệu gây dị ứng hoặc không dung nạp**, và để đánh giá dinh dưỡng chính xác.

→ Củng cố cho việc giữ RQ6, và liên kết trực tiếp phân rã món ăn với **an toàn dị ứng** chứ không chỉ tiện lợi.

### 1.5. Biến mới: thu nhập & khả năng chi trả — bằng chứng rất mạnh

Đây là bổ sung có giá trị nhất trong bản cập nhật của bạn.

| Bằng chứng | Con số |
|---|---|
| Chi phí một chế độ ăn lành mạnh (CoHD) tại Việt Nam, 2016–2020 | **3,08 đô la quốc tế PPP 2017/người/ngày ≈ 24.070 VND** |
| Nhóm thực phẩm giàu dinh dưỡng (đạm, rau, quả, sữa) chiếm | **~80%** tổng chi phí |
| Khả năng chi trả | Chế độ ăn lành mạnh rẻ nhất **không kham nổi với ~70% hộ thu nhập thấp**; tuân thủ khuyến nghị dinh dưỡng Việt Nam có thể **ngốn tới 70% thu nhập** của họ |
| Chênh lệch vùng | Trung du–miền núi phía Bắc thấp nhất; Đông Nam Bộ và Đồng bằng sông Hồng cao nhất |

*Nguồn: Cost and affordability of healthy diets in Vietnam, Public Health Nutrition (Cambridge), 2023, PMID 38037710.*

#### 1.5.1. Vì sao đây là bằng chứng quan trọng

Nó chuyển "khả năng chi trả" từ **tính năng tuỳ chọn** thành **ràng buộc thiết kế**. Một thực đơn đúng tuyệt đối về lâm sàng nhưng vượt khả năng chi trả thì tỉ lệ tuân thủ bằng không — và bệnh nhân mãn tính thu nhập thấp lại chính là nhóm đông nhất.

Điều này cũng bổ khuyết đúng chỗ yếu của Chương 1: phần pain point trước đây thiếu một điểm đau kinh tế, dù đó là rào cản thực tế lớn nhất.

#### 1.5.2. Đề xuất một RQ mới

> **RQ9 — Ràng buộc chi phí:** Khi bổ sung ràng buộc ngân sách vào bài toán sinh thực đơn, tỉ lệ thực đơn vừa đạt ngưỡng lâm sàng vừa nằm trong ngân sách là bao nhiêu, và mức ngân sách tối thiểu để còn tồn tại lời giải khả thi cho từng nhóm bệnh là bao nhiêu?

Đánh giá: **khả thi trung bình–cao**. Không cần bệnh nhân thật, không cần thiết bị. Chỉ cần thêm cột `price_per_100g` vào bảng thực phẩm và một ràng buộc trong bộ kiểm tra. Điểm mạnh: kết quả có ý nghĩa chính sách thật (mức ngân sách tối thiểu để ăn đúng bệnh) — hiếm dự án sinh viên nào đưa ra được con số kiểu này.

**Rủi ro cần nêu rõ:** giá thực phẩm biến động theo mùa và theo chợ. Không được trình bày con số chi phí như giá trị chính xác; phải ghi rõ ngày lấy giá và nguồn giá.

#### 1.5.3. ⚠️ Khuyến nghị quan trọng về cách hỏi thu nhập

**Không nên hỏi trực tiếp "tổng thu nhập gia đình" trong hồ sơ bệnh nhân.** Ba lý do:

1. **Riêng tư:** thu nhập là thông tin nhạy cảm; hỏi thẳng làm giảm tỉ lệ hoàn thành hồ sơ và tăng nghĩa vụ bảo vệ dữ liệu theo Nghị định 13/2023/NĐ-CP.
2. **Không cần thiết về mặt kỹ thuật:** thứ hệ thống thực sự cần là **ngân sách cho bữa ăn**, không phải thu nhập.
3. **Rủi ro phân biệt đối xử:** hệ thống y tế gợi ý chế độ ăn khác nhau dựa trên thu nhập là vấn đề đạo đức cần cân nhắc rất kỹ, đặc biệt nếu bị hiểu là "người nghèo được tư vấn kém hơn".

**Thay bằng:** một câu hỏi tuỳ chọn, dễ trả lời, không định danh:

> *"Bạn muốn chi khoảng bao nhiêu cho tiền ăn mỗi ngày cho người bệnh?"*
> ◯ Dưới 50k ◯ 50–100k ◯ 100–150k ◯ Trên 150k ◯ Không giới hạn / bỏ qua

Cách này cho hệ thống đúng thông tin cần, mà không đụng vào dữ liệu thu nhập. **Nghề nghiệp** thì nên giữ nhưng đổi mục đích sử dụng: dùng để ước tính **mức độ hoạt động thể lực** (lao động chân tay và nhân viên văn phòng có TDEE khác nhau) — đây là công dụng lâm sàng chính đáng và dễ giải thích hơn.

---

## 2. KIỂM KÊ DATASET

### 2.1. Bảng thành phần thực phẩm — 🟢 Rủi ro đã giảm mạnh

**Phát hiện quan trọng nhất của đợt nghiên cứu này:** Bảng thành phần thực phẩm Việt Nam 2007 của Viện Dinh dưỡng **đang được host công khai trên máy chủ FAO**:

```
https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf
```

Nội dung đã kiểm chứng trực tiếp:

| Đặc điểm | Giá trị |
|---|---|
| Số thực phẩm | **526**, chia 14 nhóm |
| Số chất dinh dưỡng mỗi thực phẩm | **86** |
| Có **Purin** không? | ✅ Có (tham chiếu bảng thành phần Đức 2006) — thiết yếu cho gout |
| Có **Natri, Kali, Phospho**? | ✅ Có — thiết yếu cho CKD và tăng huyết áp |
| Có **tỷ lệ thải bỏ** (%)? | ✅ Có — cần cho quy đổi khẩu phần thực tế |
| Truy vết nguồn | ✅ **Mỗi giá trị có mã nguồn 1–7** (2000 / FAO 1972 / USDA v18 / Đức 2006 / Đan Mạch 2006 / ASEAN 2000 / nghiên cứu VDD 2000–2007) |
| Nhóm 13 "Gia vị, nước chấm" | 23 thực phẩm — gồm nước mắm loại I/II, mắm tôm, xì dầu, tương ớt… **đúng nhóm quan trọng nhất cho bài toán muối** |
| Định dạng | PDF **dạng text** (không phải ảnh scan) → trích xuất bằng script được |

**Đây là thay đổi lớn với RSK-01.** Trước đây rủi ro "không có dữ liệu dùng được" được đánh giá là *cao / chặn dự án*. Nay hạ xuống **trung bình**, và bản chất rủi ro đổi từ *"không có dữ liệu"* thành *"phải viết script trích xuất cho đúng"*.

⚠️ **Một cạm bẫy kỹ thuật cụ thể:** phần tiếng Việt trong PDF dùng **bảng mã font cũ (kiểu TCVN3/VNI)**, nên khi trích xuất sẽ ra dạng `G¹o tÎ m¸y` thay vì `Gạo tẻ máy`. Cần một bước chuyển bảng mã. Phần **số liệu thì trích xuất bình thường** (đã kiểm chứng: Gạo tẻ máy = 344 kcal, protein 7,9 g, Na 5 mg, K 241 mg, P 104 mg).

→ **Ticket mới `DAT-07`: viết script trích xuất bảng NIN 2007 từ PDF (bao gồm chuyển bảng mã tiếng Việt), xuất ra CSV kèm cột mã nguồn gốc.** Ước tính 8–12 giờ. Đây là công việc có giá trị cao nhất trên mỗi giờ bỏ ra trong toàn dự án.

### 2.2. Dataset ảnh món ăn Việt Nam

| Dataset | Quy mô | Kết quả tốt nhất công bố | Dùng được cho dự án? |
|---|---|---|---|
| **30VNFoods** | 25.136 ảnh / **30 món** | ~95% (ConvNeXt V2-B) | 🟡 Chỉ để *nhận tên món*, không ước tính khẩu phần |
| **VinaFood21** | 13.950 ảnh / **21 món** | 94,9% (ConvNeXtV2-T + RoSE); baseline EfficientNet-B0 74,81% | 🟡 như trên |

**Đánh giá thẳng:** hai dataset này **không giải được bài toán của dự án**. Chúng phân loại được "đây là bát phở" nhưng không cho biết *bao nhiêu gram* và *bao nhiêu natri* — mà đó mới là thứ bệnh nhân CKD cần. Độ phủ 21–30 món cũng quá hẹp so với thực đơn hằng ngày.

→ Giữ nguyên quyết định **loại thị giác khỏi v1**. Nếu sau này làm, dùng chúng làm bước *gợi ý tên món* để người dùng xác nhận, không dùng để tính số.

### 2.3. Nutrition5k (Google)

| Đặc điểm | Giá trị |
|---|---|
| Quy mô | ~5.006 khay thức ăn, có RGB + **dữ liệu chiều sâu**, phân rã tới từng nguyên liệu kèm khối lượng |
| License | **CC BY 4.0** — dùng tự do, kể cả thương mại |
| Kết quả baseline | Ảnh 2D: MAE 70,6 kcal / MAPE 26,1% · Thêm depth: 47,6 / 18,8% · Volume scalar: **41,3 / 16,5%** |
| Hạn chế do chính tác giả nêu | Thu thập tại **một số căng tin ở California, Hoa Kỳ**; **không bao phủ mọi nền ẩm thực** |

**Dùng cho dự án:** không dùng làm dữ liệu huấn luyện (món Mỹ, không phải món Việt), nhưng **dùng làm bằng chứng đối chứng cho RQ1** thì rất giá trị — nó là mốc "tốt nhất mà thị giác chuyên dụng đạt được", và mốc đó vẫn kém ngưỡng lâm sàng ±10%.

### 2.4. Dữ liệu từ app sức khoẻ smartphone (Tầng 4, bạn vừa thêm)

Đề xuất hợp lý nhưng cần cụ thể hoá. Khuyến nghị ghi vào tài liệu là:

> Tiếp nhận qua lớp tổng hợp chuẩn — **Apple HealthKit** (iOS) và **Google Health Connect** (Android) — thay vì tích hợp riêng với từng hãng thiết bị.

Lý do: mỗi hãng wearable có định dạng và API riêng, một số không mở API công khai. Hai nền tảng trên đóng vai trò lớp trung gian, nên chỉ cần tích hợp một lần. Vẫn giữ nguyên kết luận: **ngoài phạm vi v1**.

### 2.5. Tổng kết: những gì KHÔNG tồn tại

Đã kiểm tra HuggingFace Hub — **không có dataset dinh dưỡng lâm sàng tiếng Việt nào dùng được**. Các dataset dinh dưỡng tìm thấy đều nhỏ (dưới 600 dòng), không nguồn gốc, không có vi chất (Na/K/P/purin).

Tương tự, **"Vietnamese Recipe & Allergy Dataset 1.000+ công thức"** nêu trong đề án ban đầu — không tìm thấy tồn tại công khai.

→ Xác nhận lại: phần **món ăn Việt + công thức nguyên liệu vẫn phải tự xây** (ticket DAT-04). Không có đường tắt.

---

## 3. KIỂM KÊ MÔ HÌNH

### 3.1. Epicure — bài báo bạn đề xuất

| Đặc điểm | Giá trị |
|---|---|
| arXiv | **2605.22391**, nộp 21/05/2026 |
| Tác giả | Jakub Radzikowski, Josef Chen (KAIKAKU.AI) |
| License | **CC BY 4.0** ✅ |
| Nội dung | 3 embedding nguyên liệu (Cooc / Chem / Core) huấn luyện bằng Metapath2Vec |
| Dữ liệu | **4,14 triệu công thức** từ 11 nguồn, 7 ngôn ngữ — **có tiếng Việt** |
| Từ vựng | **1.790 nguyên liệu chuẩn hoá** qua pipeline có LLM hỗ trợ |
| Đồ thị | 203.508 cạnh đồng xuất hiện nguyên liệu + 80.019 cạnh nguyên liệu–hợp chất (FlavorDB), 2.247 nút hợp chất |
| **Tải về** | ✅ **Embedding có sẵn dạng CSV ngay trong ancillary files của arXiv**: `epicure_core.csv`, `epicure_cooc.csv`, `epicure_chem.csv`, `vocab.csv` |

#### Dùng được vào việc gì — và không được dùng vào việc gì

| ✅ Dùng được | ❌ Không được dùng |
|---|---|
| **Gợi ý thay thế nguyên liệu** (ADV-02): tìm nguyên liệu gần nhau trong không gian embedding để đề xuất thay thế khi cần giảm natri/kali | ❌ **Sinh giá trị dinh dưỡng** — đây là embedding hương vị/hoá học, không phải bảng thành phần |
| **Chuẩn hoá tên nguyên liệu / xử lý OOV** (CLN-07): `vocab.csv` 1.790 mục là điểm khởi đầu tốt cho ánh xạ tên món lạ | ❌ Thay thế cho bảng NIN |
| Nhóm nguyên liệu theo vùng ẩm thực để lọc ứng viên theo miền | ❌ Suy ra tính an toàn lâm sàng |

**Việc cần làm trước khi tin dùng:** tải `vocab.csv` và **đếm xem thực sự có bao nhiêu nguyên liệu Việt Nam** trong 1.790 mục. Bài báo nêu tiếng Việt là 1 trong 7 ngôn ngữ nhưng **không công bố tỉ lệ**. Nếu chỉ có vài chục nguyên liệu Việt thì giá trị thực tế thấp hơn nhiều so với kỳ vọng. Đây là kiểm tra 30 phút, phải làm trước khi đưa vào kế hoạch.

→ **Ticket mới `DAT-08`: tải và đánh giá độ phủ nguyên liệu Việt Nam của Epicure vocab.** 2 giờ.

### 3.2. Các mô hình khác đáng biết

| Mô hình | Mô tả | Liên quan |
|---|---|---|
| **FlavorGraph** (Park et al., 2021) | Embedding thực phẩm công khai toàn diện nhất trước Epicure, kết hợp hoá học FlavorDB với đồng xuất hiện Recipe1M+ | Nền tảng mà Epicure kế thừa |
| **FoodSky** | LLM chuyên ngành thực phẩm, được báo cáo là vượt qua kỳ thi đầu bếp và kỳ thi dinh dưỡng (Patterns, 2025) | 🟡 Đáng theo dõi, nhưng bối cảnh Trung Quốc; cần kiểm tra khả năng truy cập trước khi tính vào kế hoạch |
| **RoSENet / ConvNeXt V2** | Kiến trúc đạt SOTA trên 30VNFoods và VinaFood21 | Chỉ dùng nếu sau này làm nhận diện ảnh |

---

## 4. PHƯƠNG ÁN XÂY DỰNG AI — MUA, TÁI DÙNG HAY TỰ XÂY

Nguyên tắc: **tự xây phần quyết định an toàn lâm sàng; tái dùng phần còn lại.**

| Thành phần | Phương án | Lý do |
|---|---|---|
| **Bộ tính định mức lâm sàng** (BMR/TDEE, ngưỡng theo bệnh) | 🔨 **Tự xây** — đã xong, 43 test xanh | Là tài sản trí tuệ chính; phải xác định và kiểm chứng được; không có sản phẩm sẵn nào phù hợp guideline Việt Nam |
| **Bảng thành phần thực phẩm** | 📥 **Trích xuất từ NIN 2007 (FAO)** + USDA bổ sung | Nguồn chính thống, có mã nguồn từng giá trị |
| **Công thức món ăn Việt** | 🔨 **Tự xây, LLM sinh nháp + người rà soát** | Không tồn tại nguồn công khai |
| **Chuẩn hoá tên / OOV** | 📥 **Epicure vocab** + bảng alias tự xây | Có sẵn, license mở |
| **Gợi ý thay thế nguyên liệu** | 📥 **Epicure embedding** | Có sẵn, đúng mục đích |
| **Sinh thực đơn** | 🔌 **LLM qua API** + structured output | Không cần và không nên tự huấn luyện |
| **Bộ kiểm tra ngưỡng (validator)** | 🔨 **Tự xây** — đã xong | Phải xác định; đây là chốt an toàn |
| **Tương tác thuốc–thực phẩm** | 🔨 **Curate ~80 cặp**, dùng FooDrugs/DDID làm nguồn sinh ứng viên | Dữ liệu sẵn có có tỉ lệ sai cao (F1 0,77), không dùng thẳng được |
| **RAG guideline** | 📥 pgvector + BM25 | Công nghệ trưởng thành |
| **Nhận diện ảnh món ăn** | ⛔ **Không làm ở v1** | Bằng chứng §1.1 cho thấy chưa đủ chính xác cho mục đích lâm sàng |
| **Ràng buộc chi phí** (mới) | 🔨 Tự xây — thêm cột giá + ràng buộc trong validator | Đơn giản, giá trị cao (§1.5) |

### Không cần huấn luyện mô hình nào từ đầu

Toàn bộ kiến trúc chạy được với: **1 LLM qua API + embedding có sẵn + code Python xác định + SQL**. Đây là điểm mạnh cần nói rõ trong pitch — nó có nghĩa là hệ thống **rẻ để vận hành, dễ kiểm toán, và cập nhật guideline không cần huấn luyện lại**.

---

## 5. TÁC ĐỘNG LÊN KẾ HOẠCH HIỆN TẠI

### 5.1. Thay đổi đánh giá rủi ro

| Mã | Trước | Sau | Lý do |
|---|---|---|---|
| RSK-01 (không có dữ liệu thực phẩm) | 🔴 Cao / chặn dự án | 🟡 **Trung bình** | Bảng NIN 2007 có trên FAO, 526 món, 86 chất, dạng text. Rủi ro còn lại là kỹ thuật trích xuất, không phải thiếu nguồn |

### 5.2. Ticket mới đề xuất

| Mã | Nội dung | Owner | Ước tính | Ưu tiên |
|---|---|---|---|---|
| `DAT-07` | Script trích xuất bảng NIN 2007 từ PDF FAO (kèm chuyển bảng mã tiếng Việt) → CSV có cột nguồn | R2 | 8–12h | **P0** |
| `DAT-08` | Tải Epicure vocab, đánh giá độ phủ nguyên liệu Việt Nam | R2 | 2h | P1 |
| `DAT-09` | Thu thập giá thực phẩm (chợ/siêu thị, ghi rõ ngày và nguồn) cho ~50 nguyên liệu chính | R2 + cả đội | 6h | P2 |
| `CLN-08` | Thêm ràng buộc ngân sách vào bộ kiểm tra ngưỡng | R2 | 6h | P2 |
| `FE-09` | Câu hỏi ngân sách bữa ăn dạng khoảng, tuỳ chọn (§1.5.3) | R4 | 3h | P2 |

`DAT-07` nên chen lên đầu Sprint 1 — nó có thể **thay thế phần lớn công việc nhập tay 152 dòng** trong ticket DAT-02.

### 5.3. Cập nhật tài liệu Word

Cần bổ sung vào các chương:

- **Chương 1** — thêm pain point kinh tế (§1.5), kèm số liệu CoHD 24.070 VND và 70% hộ thu nhập thấp
- **Chương 2** — sửa ô "Nhân khẩu học" (bỏ "vùng miền" trùng), đổi cách hỏi thu nhập thành khoảng ngân sách, ghi rõ HealthKit/Health Connect ở Tầng 4, cập nhật trạng thái bảng thành phần thực phẩm thành "đã có nguồn"
- **Chương 3** — thêm **RQ9 (ràng buộc chi phí)** vào danh sách và ma trận ưu tiên; bổ sung bằng chứng §1.1 vào phần mô tả RQ1; đổi cách phát biểu RQ2 (§1.2)
- **Phụ lục** — thêm toàn bộ nguồn ở §6 vào mục A.2

---

## 6. DANH MỤC NGUỒN ĐÃ KIỂM CHỨNG

Tất cả các nguồn dưới đây đã được truy cập và xác minh trực tiếp trong quá trình nghiên cứu này (27/07/2026).

**Về độ chính xác của AI trong ước tính dinh dưỡng**
1. *Performance Evaluation of 3 Large Language Models for Nutritional Content Estimation from Food Images.* Current Developments in Nutrition, 2025. PMID 41081011 / PMC12513282.
2. *Large Language Models as Clinical Nutrition Decision Tools: Quantitative Bias and Guideline Deviation in Type 2 Diabetes Meal Planning.* Healthcare, 2026. doi:10.3390/healthcare14060739.
3. *Comparison of Accuracy in the Evaluation of Nutritional Labels… Between Professional Nutritionists and Chatbots.* Nutrients, 2025. PMC12526241.
4. Thames Q. et al. *Nutrition5k: Towards Automatic Nutritional Understanding of Generic Food.* CVPR 2021. arXiv:2103.03375. Dataset: github.com/google-research-datasets/Nutrition5k (CC BY 4.0).
5. *Improving Personalized Meal Planning with Large Language Models: Identifying and Decomposing Compound Ingredients.* Nutrients, 2025. PMC12073434.

**Về embedding và mô hình thực phẩm**
6. Radzikowski J., Chen J. *Epicure: Navigating the Emergent Geometry of Food Ingredient Embeddings.* arXiv:2605.22391, 21/05/2026. CC BY 4.0.
7. Park D. et al. *FlavorGraph*, 2021.

**Về dataset món ăn Việt Nam**
8. Nguyen T.T. et al. *VinaFood21: A Novel Dataset for Evaluating Vietnamese Food Recognition.* RIVF 2021. arXiv:2108.02929.
9. *30VNFoods: A Dataset for Vietnamese Foods Recognition.* IEEE, 2021.

**Về tương tác thuốc–thực phẩm**
10. *FooDrugs: a comprehensive food–drug interactions database…* Database (Oxford), 2023. PMID 37951712 / PMC10640380.
11. *DDID: a comprehensive resource for visualization and analysis of diet–drug interactions.* Briefings in Bioinformatics, 2024.

**Về chi phí và khả năng chi trả**
12. *Cost and affordability of healthy diets in Vietnam.* Public Health Nutrition (Cambridge), 2023. PMID 38037710 / PMC10830355.
13. FAO. *Cost and Affordability of a Healthy Diet (CoAHD)*, FAOSTAT.

**Về dữ liệu thành phần thực phẩm**
14. Viện Dinh dưỡng – Bộ Y tế. *Bảng thành phần thực phẩm Việt Nam / Vietnamese Food Composition Table.* NXB Y học, 2007. 526 thực phẩm, 86 chất dinh dưỡng. Bản PDF: `fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf`
15. USDA FoodData Central.

**Về dịch tễ Việt Nam** *(đã dùng trong Chương 1)*
16. Điều tra STEPS 2021 và 2015, Bộ Y tế.
17. Bộ Y tế – Cục Phòng bệnh, hội thảo về bệnh thận mạn.
18. Tạp chí Y học Việt Nam, 2023 — khảo sát acid uric và gout tại BV ĐH Y Dược TP.HCM.

---

## 7. BA ĐIỀU NÊN LÀM NGAY

1. **Chạy `DAT-07` trước mọi thứ khác.** Bảng NIN 2007 nằm sẵn trên FAO là món quà lớn nhất của đợt nghiên cứu này — nó rút ngắn đáng kể con đường tới dữ liệu có nguồn, và giảm rủi ro lớn nhất của dự án.

2. **Đưa số liệu §1.1 vào slide 6 của pitch deck.** "Mô hình thị giác tốt nhất đạt sai số 16,5%, LLM đa phương thức 36%, trong khi ngưỡng lâm sàng là 10%" — một câu, ba con số có nguồn, trả lời trọn vẹn câu hỏi khó nhất mà giám khảo sẽ hỏi.

3. **Đổi cách hỏi thu nhập thành khoảng ngân sách bữa ăn.** Giữ được toàn bộ giá trị của biến mới, bỏ được rủi ro riêng tư và đạo đức.
