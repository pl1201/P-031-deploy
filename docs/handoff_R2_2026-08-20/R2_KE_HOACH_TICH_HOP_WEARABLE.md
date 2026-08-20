# R2 — Kế hoạch tích hợp Wearable (Google Fit / Apple HealthKit)

> 2026-08-20 · R2 (tri thức lâm sàng · dữ liệu · eval)
> Trả lời câu hỏi: "có nên tích hợp Google Fit/Apple Health/wearable để cạnh tranh?"
> Kèm market research, đánh giá rủi ro, và prototype luồng UI/UX dự kiến (`prototype_uiux_wearable.html`).

---

## 0. Kết luận trước

**Nên làm, nhưng không phải như một app thể dục.** Thị trường quản lý ĐTĐ số ở
Châu Á-TBD đạt ~4,33 tỷ USD năm 2025, **wearable chiếm 54,9% doanh thu nhóm này** — bỏ
qua hướng này thực sự mất lợi thế cạnh tranh. Nhưng **ba phát hiện dưới đây đổi hẳn cách
làm**:

1. Calo tiêu hao ước lượng từ wearable tiêu dùng sai **20–90%** tuỳ thiết bị/cường độ —
   không đạt chuẩn "có nguồn" của RULE-2.
2. **Google Fit API đã ngừng nhận đăng ký mới từ 1/5/2024** và đang bị khai tử — xây trên
   nền tảng này bây giờ là xây trên nền sắp sập.
3. Không app ĐTĐ nào đứng đắn trong nhóm khảo sát (Glooko, One Drop, WellDoc BlueStar,
   Nutrisense) dùng dữ liệu wearable để **tự động** tính lại khẩu phần hay liều thuốc —
   tất cả dừng ở **hiển thị/tương quan**, quyết định vẫn do người.

Nên hướng đúng không phải "kết nối càng nhiều chỉ số càng tốt", mà là **wearable làm
quan sát tham khảo cho chuyên gia đọc**, giữ đúng khuôn đã dùng cho cân nặng (C1–C7) và
kcal-out (K1–K5): không tự động nối vào chỉ định.

---

## 1. Market research

### 1.1. Ai đã làm, làm tới đâu

| Sản phẩm | Nguồn wearable | Dùng để làm gì |
|---|---|---|
| **One Drop** | Apple HealthKit, Google Fit, Fitbit, Dexcom | Hợp nhất hiển thị trên 1 dashboard, không công bố công thức tự động điều chỉnh |
| **Glooko** (FDA-cleared) | Apple Health, Fitbit, Strava + 200+ thiết bị BGM/CGM/bơm | Dữ liệu hoạt động vào **báo cáo cho bác sĩ xem lại**, không tự tính khuyến nghị |
| **mySugr** | Apple Health (không có Dexcom trực tiếp) | Chủ yếu hiển thị log |
| **WellDoc BlueStar** (FDA-cleared digital therapeutic) | Dexcom G6 + activity tracker | Tích hợp sâu nhất nhóm khảo sát: sinh **insight liên hệ hoạt động–đường huyết** cho cả bệnh nhân và bác sĩ điều chỉnh phác đồ — nhưng vẫn qua bác sĩ, không tự động |
| **Nutrisense** | Apple Watch/Fitbit/Garmin/Oura | Overlay giấc ngủ/vận động lên biểu đồ glucose — chỉ hiển thị |

**Không sản phẩm nào trong nhóm dùng calo tiêu hao từ wearable để tự động tính lại khẩu
phần hay liều insulin.** Đây là tín hiệu ngành, không phải riêng thận trọng của R2.

### 1.2. Độ chính xác calo tiêu hao — số liệu thật

- Stanford (Ferguson et al. 2017, *J Pers Med*, 60 người, 7 thiết bị gồm Apple Watch,
  Fitbit Surge, Microsoft Band): **không thiết bị nào đạt sai số ước lượng năng lượng
  tiêu hao dưới 20%**; thấp nhất ~27,4%, tệ nhất (Fitbit Surge) tới **92,6%**.
- Nghiên cứu treadmill (PMC6843350): Apple Watch Series 1 MAPE ~10,7% ở tốc độ trung
  bình nhưng Garmin Forerunner 920XT **âm 21,6% đến âm 49,3%** ở cường độ cao (đo thấp
  hẳn so với thực tế).
- Sai số phụ thuộc thiết bị, cường độ vận động, và cả tông da/tỷ lệ mỡ cơ thể (ảnh hưởng
  cảm biến quang PPG đo nhịp tim).

**Kết luận kỹ thuật:** calo tiêu hao từ wearable **không đạt chuẩn RULE-2** ("mọi con số
hiển thị phải kèm nguồn đáng tin"). Bước chân và nhịp tim đáng tin hơn nhiều — đây là
điểm quan trọng cho §3.

### 1.3. Rào cản pháp lý-kỹ thuật

| Nền tảng | Tình trạng |
|---|---|
| **Google Fit API** | Ngừng đăng ký mới từ 1/5/2024, đang khai tử. Google khuyến nghị chuyển sang **Health Connect** (chỉ Android, dữ liệu on-device, không có cloud sync sẵn) hoặc Fitbit Web API |
| **Apple HealthKit** | Không tự động = HIPAA-compliant — chỉ phát sinh nghĩa vụ khi chia sẻ với "covered entity" (bệnh viện/bảo hiểm Mỹ). VNutriCare ở Việt Nam không thuộc phạm vi HIPAA trực tiếp, nhưng Apple áp policy riêng toàn cầu: **cấm dùng dữ liệu sức khỏe cho quảng cáo**, bắt buộc consent rõ theo từng loại dữ liệu, khuyến nghị mã hoá AES-256 + TLS 1.2+. Vi phạm policy này = rủi ro bị gỡ app, không phải rủi ro pháp lý VN |

**Hệ quả cho lộ trình:** Google Fit **không nên đầu tư lúc này**. Ưu tiên Apple HealthKit
trước (nền tảng ổn định hơn), và cân nhắc **Health Connect** cho Android về sau khi hạ
tầng ổn định hơn — không nên coi hai nền tảng ngang hàng trong roadmap.

### 1.4. Xu hướng thị trường

- Thị trường quản lý ĐTĐ số Châu Á-TBD: ~3,76 tỷ USD (2024) → 4,33 tỷ USD (2025), CAGR
  ~15%/năm; wearable chiếm 54,9% doanh thu nhóm 2025 (Mordor Intelligence).
- WHO Đông Nam Á: ~246 triệu người lớn mắc ĐTĐ (2022), nhưng nhiều bệnh nhân ở các nước
  thu nhập thấp/trung bình vẫn dùng test strip thủ công — hạ tầng wearable **chưa phổ cập
  đồng đều**.
- **Khoảng trống dữ liệu thật, không suy đoán:** không tìm được số liệu tỷ lệ dùng/churn
  wearable riêng cho Việt Nam hay Đông Nam Á qua đợt research này. Bất kỳ giả định về "X%
  người dùng VN có Apple Watch" trong pitch/demo đều **không có nguồn** — nên nói rõ đây
  là giả định, không phải số đo được.

### 1.5. Case cảnh báo — vì sao không tự động hoá

- **FDA (2/2025)**: cảnh báo chính thức về thiết bị ĐTĐ kết nối smartphone (CGM, bơm
  insulin, automated insulin dosing) — cài đặt điện thoại (chế độ im lặng, tối ưu pin)
  khiến cảnh báo an toàn quan trọng không tới người dùng, góp phần gây hạ đường huyết
  nặng, tăng đường huyết nặng, nhiễm toan ceton, có ca tử vong.
- Đây không phải lỗi thuật toán tính từ wearable, mà lỗi **chuỗi cảnh báo** — nhưng minh
  chứng thật cho rủi ro khi để thiết bị tiêu dùng nằm trong chuỗi quyết định lâm sàng mà
  không có lớp xác nhận của người.

---

## 2. Ranh giới sở hữu — theo đúng khuôn đã dùng cho C1–C7 / K1–K5

| Việc | Ai |
|---|---|
| OAuth, đồng bộ API, lưu trữ dữ liệu thô | R1 (backend) |
| Giao diện kết nối, hiển thị biểu đồ | R4 (frontend) |
| **Chỉ số nào được tin, chỉ số nào chỉ tham khảo** | **R2** |
| **Ngưỡng red flag phát sinh từ dữ liệu wearable** | **R2** |
| **Quy tắc: dữ liệu wearable KHÔNG được tự động làm gì** | **R2** — xem §3 |
| Chính sách quyền riêng tư, consent theo policy Apple/Google | R1 (pháp lý dữ liệu thuộc R1 theo phân công hiện tại) |

---

## 3. Ba quy tắc R2 chốt trước khi R1/R4 code

### 3.1. Phân tầng độ tin cậy theo loại chỉ số — KHÔNG đối xử như nhau

| Chỉ số | Độ tin cậy | Dùng được cho gì |
|---|---|---|
| **Bước chân** | Cao — cảm biến gia tốc kế ổn định | Hiển thị tham khảo, có thể liên hệ với hoạt động đã ghi tay (K1–K5) |
| **Nhịp tim** | Trung bình-cao lúc nghỉ, giảm khi vận động mạnh (PPG bị nhiễu) | Hiển thị tham khảo, KHÔNG dùng tính MET/cường độ tự động |
| **Calo tiêu hao (EE)** | **Thấp — sai 20-90%** | **CHỈ hiển thị nguyên trạng từ thiết bị, gắn nhãn rõ "ước tính của [tên thiết bị], có thể sai lệch đáng kể"**. KHÔNG đưa vào bất kỳ công thức nào của hệ thống (không thay `compute_tdee`, không cộng vào mục tiêu kcal) |
| **Giấc ngủ** | Trung bình | Hiển thị tham khảo cho chuyên gia — giấc ngủ kém liên quan kháng insulin, nhưng diễn giải là việc của chuyên gia, không phải hệ thống tự kết luận |

Nguyên tắc chung: **nguồn "wearable" là một loại `source` mới trong `patient_observations`,
ngang hàng với "tự khai"** — không phải nguồn cao cấp hơn chỉ vì đến từ thiết bị. Việc
"đo bằng máy" không tự động nghĩa là "đáng tin hơn con người nhập tay", nhất là với EE.

### 3.2. Không nối vòng — mở rộng nguyên tắc K5 đã chốt

Giữ nguyên lý do đã dùng cho năng lượng vận động tự ghi (K5): **không chỉ số nào từ
wearable được tự động điều chỉnh mục tiêu kcal, khẩu phần, hay bất kỳ khuyến nghị nào**.
Case FDA §1.5 là bằng chứng cho đúng nguyên tắc này ở quy mô lớn hơn.

### 3.3. Red flag mới cần thêm vào `R2_AUDIT_EXCEPTION_BASED_CARE_RULES.md` §5.4 khi triển khai

Đề xuất sơ bộ (chưa chốt, cần bạn duyệt khi tới lúc code):

> **Red flag #6 (dự kiến):** nhịp tim nghỉ từ wearable liên tục > 100 bpm hoặc < 50 bpm
> trong ≥3 ngày liên tiếp ở bệnh nhân ĐTĐ2 — đẩy chuyên gia xem, hệ thống không diễn giải
> nguyên nhân (giữ đúng "không chẩn đoán" — CLAUDE.md §3).

---

## 4. Lộ trình đề xuất

| Đợt | Việc | Vì sao |
|---|---|---|
| **1** | Apple HealthKit — chỉ đọc **bước chân + nhịp tim nghỉ**, hiển thị tham khảo | Hai chỉ số tin cậy nhất, giá trị demo cao, rủi ro thấp nhất |
| **2** | Thêm **giấc ngủ**, hiển thị cho chuyên gia (không diễn giải) | Liên quan kháng insulin nhưng cần chuyên gia đọc |
| **3** | Thêm **calo tiêu hao**, nhãn rõ "ước tính thiết bị, có thể sai 20-90%" | Chỉ hiển thị nguyên trạng, không tính lại gì |
| **—** | **Google Fit / Android** | Hoãn tới khi Health Connect ổn định hoặc có nhu cầu Android rõ ràng — không đầu tư vào API đang bị khai tử |

**Không làm ở MVP:** đồng bộ CGM (Dexcom/Libre) — đây là thiết bị y tế, không phải
wearable tiêu dùng, đặt ra loạt câu hỏi về schema/độ trễ dữ liệu/red flag khác hẳn, nên
tách thành đề xuất riêng nếu cần.

---

## 5. Xem thêm

- Prototype luồng UI/UX: [`prototype_uiux_wearable.html`](prototype_uiux_wearable.html) —
  mockup 4 màn hình (kết nối → xem tham khảo → chuyên gia đọc → red flag), do R2 phác thảo
  nội dung/nhãn dữ liệu, R4 quyết định thiết kế thật.
- Ranh giới đã chốt cho cân nặng/kcal-out (cùng nguyên tắc không nối vòng):
  `R2_KE_HOACH_KCAL_OUT_VA_THEO_DOI_CAN_NANG.md`
- Danh sách red flag hiện có: `R2_AUDIT_EXCEPTION_BASED_CARE_RULES.md` §5.4
