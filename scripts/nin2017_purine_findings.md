# NIN 2017 — kết luận về dữ liệu Purine (khối "Thành phần các chất khác", trang 219-248)

## Kết luận

**CÓ** số liệu purine thật trong khối "Thành phần các chất khác trong 100g
thực phẩm ăn được" (bảng riêng, đánh số TT/trang độc lập với khối macro
23-152), cột cuối cùng của bảng (sau cột Phytosterol), đơn vị mg/100g.

Xác nhận bằng đối chiếu: các giá trị trích được cho nội tạng động vật khớp
rất sát với các bảng purine tham chiếu khác đã có trong dự án
(`data/seeds/purine_db_reference.csv`, từ `PURINEDATABASEANDDATASOURCES2025.xlsx`,
DAT-14) — ví dụ gan lợn ~515 mg, gan gà ~243 mg đều nằm trong nhóm
"purine rất cao" đúng như y văn mô tả cho nội tạng.

## Nhóm Thịt (mã 07xxx, trang PDF gốc macro 77-92, trong khối này ở trang
khoảng 230-236) — ví dụ purine trích được:

| Mã | Tên món | Purine (mg/100g) | Trang (khối 219-248) |
|---|---|---|---|
| 07010 | Thịt cừu, nạc | 182 | 231 |
| 07014 | Thịt gà tây | 110 | 231 |
| 07017 | Thịt lợn nạc | 166 | 231 |
| 07030 | Bầu dục lợn (thận lợn) | 334 | 232 |
| 07032 | Chân giò lợn (bỏ xương) | 160 | 232 |
| 07040 | Gan gà | 243 | 233 |
| 07041 | Gan lợn | 515 | 233 |
| 07045 | Lưỡi lợn | 136 | 233 |
| 07050 | Óc lợn | 83 | 233 |
| 07028 | Thịt vịt | 138 | 231 |

## Nhóm Thủy sản (mã 08xxx, trang PDF gốc macro 93-104, trong khối này ở
trang khoảng 236-240) — ví dụ purine trích được:

| Mã | Tên món | Purine (mg/100g) | Trang (khối 219-248) |
|---|---|---|---|
| 08003 | Cá chép | 160 | 237 |
| 08011 | Cá hồi | 170 | 237 |
| 08015 | Cá mòi (cá sardin) | 345 | 237 |
| 08026 | Cá thu | 145 | 238 |
| 08031 | Cá trích | 210 | 238 |
| 08048 | Sò | 90 | 239 |
| 08051 | Tôm biển | 147 | 239 |

## ⚠️ Vì sao KHÔNG merge tự động vào `purine_mg` trong phiên này

1. **Số cột mỗi dòng trong bảng PDF không cố định** — nhiều dòng bị cắt
   ngắn (thiếu hẳn một số cột giữa bảng khi giá trị = 0/trống), nên vị trí
   "cột cuối cùng" không đáng tin cậy 100% để suy ra đó luôn là Purine chứ
   không phải Phytosterol hay một cột khác bị dịch. Rủi ro lệch cột ở quy
   mô 620 dòng là có thật (đã có tiền lệ lệch dòng ở khối macro theo mô tả
   pilot).
2. Nhiều dòng thịt/cá tươi sống (VD `07083 Thịt lợn, nạc vai`,
   `07087-07090` các loại thịt gà công nghiệp/thịt ngan) hiển thị "0" ở vị
   trí cuối — về mặt sinh học, thịt sống nguyên miếng hiếm khi có purine
   bằng 0 thật (thường 100-200 mg/100g). Giá trị "0" này nhiều khả năng là
   Phytosterol=0 bị đọc nhầm thành Purine do dòng bị cắt cột, KHÔNG phải
   Purine=0 thật — merge nhầm sẽ vi phạm RULE-2/DEC-008 nghiêm trọng (điền
   sai giá trị nguy hiểm cho bệnh nhân gout).
3. Vì rủi ro sai lệch cột cao và hậu quả lâm sàng lớn nếu sai (bệnh nhân
   gout dựa vào `purine_mg` để né thực phẩm), quyết định **để trống**
   thay vì đoán, theo đúng tinh thần DEC-008.

## Đề xuất cho việc tiếp theo (không làm trong phiên này)

Cần một script trích xuất RIÊNG cho khối 219-248, xác định vị trí cột
Purine theo header thực tế của TỪNG bảng (không giả định cố định), đối
chiếu số lượng cột khớp với số nhãn cột trong header trước khi lấy giá
trị, và review thủ công toàn bộ trước khi merge — việc này nằm ngoài
phạm vi hoàn thành của DAT-22 lần merge này, nên tách thành ticket riêng
(gợi ý: DAT-23) nếu R2 muốn tiếp tục.
