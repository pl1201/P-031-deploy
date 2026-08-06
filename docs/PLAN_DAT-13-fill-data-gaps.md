# PLAN DAT-13 — Rà soát & làm giàu các khoảng trống dữ liệu hiện có

> Dành cho: agent/teammate khác tiếp nhận. Đọc `CLAUDE.md` §2 (3 rule đỏ) trước khi làm bất cứ dòng nào ở đây.
> Người viết: Claude (theo yêu cầu Hưng, 2026-08-06). Nhánh gốc: `feature/DAT-04-vn-dishes-batch1`.

---

## 0. Nguyên tắc bắt buộc (đọc trước khi code)

> **Nguyên tắc bị hiểu sai dễ nhất trong plan này:** "Trống có thể là không đáng kể" **KHÔNG có nghĩa là được phép tự đoán số 0 hay số nhỏ tùy ý.** DEC-008 vẫn áp dụng: *để trống còn hơn tích hợp sai*. Việc "làm giàu" ở đây nghĩa là **đi tìm số liệu THẬT cho những dòng đang trống**, không phải lấp trống bằng suy đoán.

Thứ tự ưu tiên bắt buộc khi lấp một ô trống (Na/K/P hoặc bất kỳ cột nào khác):

1. **Tra chéo nguồn chính thức đã có sẵn trong `data/`** cho đúng thực phẩm đó hoặc thực phẩm tương đồng nhất (cùng nhóm, cùng cách chế biến) — `Bang-thanh-phan-dinh-duong-Thuc-pham-VN-2017-27-4-17.pdf` (NIN 2017, 304 trang, đã có script `scripts/extract_nin2017_bulk.py` làm mẫu tra cứu theo tên/mã), `FoodData_Central_csv_2025-12-18/` (USDA bulk), `FoodData_Central_survey_food_json_2024-10-31/` (USDA Survey/FNDDS). Đây là nguồn THẬT, có mã tra cứu được — ưu tiên tuyệt đối.
2. **Chỉ khi (1) không tra được** (thực phẩm không có trong cả 2 bộ, hoặc không tìm được mục tương đồng đủ gần) mới cân nhắc gắn `source=estimated` + `is_estimated=TRUE`, và **bắt buộc** kèm `source_ref` giải thích rõ cơ sở suy luận (VD: "Ước tính theo nhóm 'ngũ cốc tinh bột không muối' — Na trace <5mg/100g, đối chiếu USDA FDC nhóm tương tự [FDC ID]", không được ghi chung chung "ước tính").
3. **Không có cơ sở nào ở (1) hoặc (2)** → giữ nguyên trống. Không thêm dòng vào `food_items.csv` chính (chỉ để trong file nháp/staging), không tự đặt `na_mg=0` chỉ vì "chắc là ít".

**Điểm mấu chốt về "không đáng kể":** điều này chỉ đúng cho MỘT SỐ nhóm thực phẩm cụ thể theo khoa học dinh dưỡng đã biết (VD: dầu ăn tinh luyện, đường tinh luyện, tinh bột nguyên chất không phụ gia → Na/K/P thực sự gần 0 và đã được y văn xác nhận rộng rãi). Nó **không đúng** cho rau củ, ngũ cốc nguyên hạt, thịt cá, sản phẩm chế biến — các nhóm này K/P thường đáng kể và biến thiên nhiều, tuyệt đối không suy đoán.

---

## 1. Bản đồ khoảng trống hiện tại (đã khảo sát 2026-08-06)

| File | Tổng dòng | Trống/thiếu | Cột thiếu | Ghi chú |
|---|---|---|---|---|
| `data/seeds/food_items.csv` | 7221 | 27 dòng chưa nhập số liệu (khác 7194 dòng đã đủ na/k/p — do `validate_data.py` chặn dòng thiếu na/k/p khi đã có kcal) | mọi cột số | Xem cột `assigned_to` |
| `data/seeds/food_items.template.csv` | 152 | **152/152** (100%) | mọi cột số | Chưa ai động vào — batch việc lớn nhất còn lại |
| `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` sheet "Bảng TP có phospho" | 397 | 309 dòng thiếu Na hoặc K (đã xác nhận 2026-08-06, xem DEVLOG cùng ngày) | na_mg và/hoặc k_mg | Đa số là ngũ cốc/tinh bột/bánh — ĐÚNG nhóm dễ tra chéo USDA/NIN2017 nhất |
| `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` sheet "Bảng TP" | 841 | 761 chưa từng đối chiếu (761 tên không có trong food_items.csv) | na_mg, k_mg, p_mg (sheet này không có 3 cột) | Chỉ dùng làm nguồn đối chiếu tên/kcal/protein/fat/carb/fiber, KHÔNG dùng trực tiếp để tạo dòng mới (thiếu na/k/p bắt buộc) |
| `data/seeds/drug_food_interactions.csv` | 30 | 13 cặp thiếu `source_ref` | source_ref | DAT-05 — cần Dược thư QGVN 2022 hoặc guideline gốc, không được để trống khi lên Demo |
| `data/seeds/gi_values.csv` | 28 | — | — | Phủ thưa nhưng đã trong `OPTIONAL_NUMERIC_COLS`, không phải lỗi |
| `data/seeds/purine_values.csv` | 19 | — | — | Tương tự, đã optional theo rule |

---

## 2. Việc cần làm — theo độ ưu tiên

### 2.1. [Ưu tiên 1] Lấp Na/K của 309 dòng "Bảng TP có phospho" bằng tra chéo NIN2017/USDA

- Với mỗi trong 309 tên thiếu Na hoặc K: thử tra theo tên chuẩn hoá (dùng lại hàm `_norm()` trong `scripts/extract_menu_xlsx_composition.py`) trong:
  - `data/Bang-thanh-phan-dinh-duong-Thuc-pham-VN-2017-27-4-17.pdf` (dùng lại logic toạ độ của `scripts/extract_nin2017_bulk.py`)
  - USDA bulk CSV/JSON (`data/FoodData_Central_csv_2025-12-18/`, `data/FoodData_Central_survey_food_json_2024-10-31/`) — khớp theo tên tiếng Anh gần nhất nếu không có tên Việt (rủi ro cao hơn, cần ghi rõ trong `source_ref` là khớp chéo ngôn ngữ, không phải khớp trực tiếp)
- Tìm được → điền `na_mg`/`k_mg` thật, `source` = NIN hoặc USDA tương ứng, `source_ref` trỏ đúng mã/trang.
- Không tìm được → xét nhóm thực phẩm có thuộc diện "trace theo y văn" (dầu, đường tinh luyện, tinh bột nguyên chất) không — nếu có, áp dụng bước 2 ở §0 với `source=estimated`. Nếu không thuộc nhóm này (đa số ngũ cốc/bánh trong danh sách 309 dòng **không** thuộc diện trace) → giữ trống, KHÔNG thêm vào `food_items.csv` (danh sách các dòng bị bỏ lại nên ghi vào `data/seeds/food_items.staging_incomplete.csv` để người sau biết đã thử và tại sao bỏ, tránh làm lại từ đầu).
- Chạy `python scripts/validate_data.py` sau mỗi batch.

### 2.2. [Ưu tiên 2] `food_items.template.csv` — 152 dòng chưa nhập số liệu

- Đây là batch lớn nhất còn "0% xong". Xem cột `assigned_to` (nếu có) để biết ai phụ trách trước khi bắt tay — tránh giẫm việc.
- Áp dụng đúng quy trình §0: tra NIN2017/USDA trước, không suy đoán.
- Nếu tên trong template trùng/gần với 761 tên "mới" ở sheet "Bảng TP" (xem §1) nhưng thiếu na/k/p ở đó — vẫn phải tự tra riêng cho na/k/p, không lấy "trace" làm mặc định.

### 2.3. [Ưu tiên 3] DAT-05 — 13 cặp `drug_food_interactions.csv` thiếu `source_ref`

- Tra Dược thư Quốc gia Việt Nam 2022 (đã xác nhận nguồn dùng được, xem `data/README.md` mục nghiên cứu nguồn bổ sung) cho từng cặp: Losartan, Simvastatin, Metformin (x2), Levothyroxine, và các cặp còn lại — liệt kê đủ trong file.
- Không tìm được trong Dược thư → thử Martindale/BNF (đã dẫn trong `data/README.md`) trước khi bỏ trống.

### 2.4. [Ưu tiên 4, có thể làm song song] Đối chiếu 21 dòng lệch kcal đã phát hiện

- 21 tên trùng giữa `food_items.csv` hiện có và sheet "Bảng TP"/"Bảng TP có phospho" có kcal lệch >2 (VD Cà rốt NIN=47 vs bảng nội bộ=43.65) — cần xác định ấn bản NIN nào đúng hơn (hỏi trực tiếp chuyên gia dinh dưỡng nếu có thể, vì họ là người biên soạn bảng nội bộ) trước khi quyết định sửa dữ liệu cũ hay giữ nguyên. Đây là quyết định ảnh hưởng dữ liệu đã qua CI — cần ghi DEVLOG dạng ADR khi chốt.

---

## 3. Không làm trong việc này

- Không tự gắn `na_mg=0`/`k_mg=0`/`p_mg=0` cho bất kỳ dòng nào chỉ vì "chắc là ít" mà không tra được nguồn — vi phạm RULE-2 trực tiếp, sẽ bị chặn ở review.
- Không đổi `OPTIONAL_NUMERIC_COLS` trong `scripts/validate_data.py` để né việc phải điền na/k/p — đây là quyết định phạm vi lâm sàng (na/k/p là ngưỡng chặn cứng cho CKD/THA), cần R1/R3 duyệt riêng nếu thực sự muốn nới, không tự ý đổi trong lúc làm giàu data.
- Không sửa số liệu cũ đã qua CI (21 dòng lệch ở §2.4) mà chưa có quyết định rõ ràng ghi vào DEVLOG.

## 4. Kiểm chứng khi xong mỗi batch

```bash
python scripts/validate_data.py
python -m pytest -q
```
Không lỗi mới, cảnh báo `còn N dòng chưa nhập số liệu` giảm dần theo từng batch đã làm.
