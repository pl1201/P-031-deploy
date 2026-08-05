# DATA — Nguồn, giấy phép và quy trình nhập liệu

> Owner: **R2** · Ticket: DAT-00 → DAT-06

---

## ⚠️ Đọc trước: vì sao cột số liệu dinh dưỡng đang để trống

`food_items.template.csv` có đủ 152 dòng tên thực phẩm, alias, nhóm và dị nguyên — nhưng **các cột kcal/protein/natri… cố ý để trống**.

Lý do: điền sẵn 152 × 10 con số dinh dưỡng "từ trí nhớ" chính là **đúng cái lỗi mà toàn bộ kiến trúc dự án này sinh ra để chống**. Một bảng thực phẩm trông đầy đủ nhưng không truy được về NIN hay USDA còn nguy hiểm hơn một bảng trống, vì:

- Nó vượt qua được validator (số nằm trong khoảng hợp lý)
- Nó vượt qua được chuyên gia duyệt (nhìn không có gì bất thường)
- Nhưng nó làm sai định mức natri của bệnh nhân suy thận — và không ai phát hiện ra

Cột `source_ref` bỏ trống sẽ khiến `validate_data.py` báo lỗi và CI đỏ. Đó là thiết kế có chủ đích, không phải thiếu sót.

**Việc cần làm:** mỗi người nhập ~38 dòng theo cột `assigned_to`, tra từ nguồn thật, điền `source` + `source_ref`. Một buổi tối là xong.

---

## Nguồn dữ liệu

| Nguồn | Dùng cho | Tình trạng | Ghi chú |
|---|---|---|---|
| **NIN** — Bảng thành phần thực phẩm Việt Nam, Viện Dinh dưỡng | Thực phẩm và món ăn Việt | ⬜ cần chốt (DAT-01) | Là sách in / PDF, không có API. Ghi rõ số trang vào `source_ref` |
| **NIN 2017** — bản PDF đầy đủ (304 trang) | Bổ sung 17 dòng `food_items.csv` (DAT-09) | 🟢 đã trích | Không commit file gốc — xem mục "NIN 2017/2007" bên dưới |
| **USDA FoodData Central** | Vi chất chi tiết, nguyên liệu nhập khẩu | ⬜ cần đăng ký API key | Miễn phí. `source_ref` = `USDA fdcId:xxxxx` |
| **Guideline lâm sàng** (ADA, KDIGO, AHA/WHO, ACR, BYT) | `clinical_rules.csv` | 🟡 đã seed, chờ verify | Mỗi rule phải dẫn được tài liệu + năm |
| **Tương tác thuốc – thực phẩm** | `drug_food_interactions.csv` | 🟡 đã seed 30 cặp, chưa có `source_ref` | Xem mục "DDID" bên dưới |

### Về DDID (23.950 bản ghi tương tác)

Đề án ban đầu định dùng trọn bộ DDID. **Quyết định đã đổi (ADR-005):** license chưa rõ ràng và 23.950 bản ghi là quá thừa cho 4 nhóm bệnh của đề bài. Thay bằng **80 cặp curated** — hiện đã seed 30 cặp phổ biến nhất, cần bổ sung thêm 50.

Nếu vẫn muốn dùng DDID: phải kiểm tra license **trước khi** import, và ghi kết quả kiểm tra vào `DEVLOG.md` §3.

---

## Các file trong `data/seeds/`

| File | Dòng | Trạng thái | Ai phụ trách |
|---|---|---|---|
| `food_items.template.csv` | 152 | ⬜ trống phần số liệu — cần nhập | cả 4 người, xem cột `assigned_to` |
| `clinical_rules.csv` | 18 | 🟡 có ngưỡng + guideline_ref, `verify_status=to_verify` | R2 |
| `drug_food_interactions.csv` | 30 | 🟡 có cơ chế + khuyến nghị, thiếu `source_ref` | R2 |
| `gi_values.csv` | 28 | 🟢 7 món Việt (Chan 2001) + 21 staple/quả (Atkinson 2021 Suppl. Table 1, DAT-08/08b) | R2 |
| `food_items.nin_draft.csv` | 152 | 🟡 **BẢN NHÁP** — 107 dòng có dữ liệu NIN thật, chờ R2 soát rồi promote (DAT-02) | R2 |

### Về nguồn NIN qua API (DAT-02)

Viện Dinh dưỡng có **API công khai**: `GET https://viendinhduong.vn/api/fe/foodNatunal/getPageFoodData` — 853 món, mỗi món kèm đủ chất (protein, fat, carb, **chất xơ**, **đường tổng**, Na, K, P). **Không có purine** (chỉ gout cần → `purine_mg` đã thành optional, bổ sung sau từ nguồn riêng).

- `scripts/fetch_nin_foods.py` — tải + map sang cột `food_items`, `source_ref = mã NIN`.
- `scripts/build_food_items_from_nin.py` — dựng `food_items.nin_draft.csv` (khớp tên tự động token-subset + neo đầu). **107/152 dòng** có dữ liệu; mỗi dòng có `match_confidence` (`exact`/`subset`/`MISS`) + `nin_name` để soát.
- ⚠️ **Quy trình:** R2 soát dòng `subset`/`MISS` (khớp tên tự động có thể sai, VD dạng khô/chế biến), sửa/bổ sung, rồi mới promote sang `food_items.csv`. Bản quyền: chỉ commit subset đã dùng, có dẫn mã NIN — không commit trọn bộ 853 món (`data/cache/` đã gitignore).

### Về NIN 2017/2007 (bản PDF đầy đủ — DAT-09)

Ngoài API 853 món, đã có 2 bản PDF sách in: **Bảng TPTP VN 2017** (304 trang, `ENERC`/`PROCNT`/`FAT`/`CHOCDF`/`FIBC`/`NA`/`K`/`P`... theo mã tag FAO/INFOOD) và **Bảng TPTP VN 2007** (567 trang, định dạng "1 món/trang" với nhãn tiếng Việt).

- **Không commit 2 file PDF gốc** (3.8 MB + 4.7 MB) — đã bị `.gitignore` chặn qua rule `data/*` sẵn có (dòng 38), chỉ giữ trên máy cá nhân/Drive nhóm.
- **Phương pháp trích 2017:** dùng `pdfplumber` đọc toạ độ x của từng từ, khớp với vị trí cột trong header lặp lại mỗi trang (`EDIBLE ENERC WATER PROCNT FAT CHOCDF FIBC ASH CA P FE ZN NA K MG...`) — tin cậy hơn trích text tuần tự vì bảng có nhiều ô trống (matrix thưa) khiến thứ tự đọc bị lệch cột nếu không neo theo toạ độ.
- **Bản 2007 KHÔNG dùng được tự động:** phần nhãn cố định (label) của PDF này dùng font Việt hoá kiểu cũ (TCVN3/VNI) không có ToUnicode CMap đúng chuẩn — `pypdf`/`pdfplumber` giải mã ra ký tự Latin-1 sai (VD `BÇu` thay vì `Bầu`, `Th¶i bá` thay vì `Thải bỏ`). Tên món tiếng Việt trong file này **không đọc được đáng tin cậy** nếu không xây bảng giải mã riêng cho font — chưa làm vì lợi ích thấp (bản 2017 mới hơn, đã phủ đủ các món cần). Phần giá trị số (kcal, protein...) trong 2007 lại đọc đúng bình thường, chỉ tên món bị hỏng.
- **Kết quả (DAT-09):** đã lấp được **20/41 dòng trống** trong `food_items.csv` bằng dữ liệu 2017 sạch (có mã số + số trang, xem `source_ref`). Với các dòng thiếu Na/K/chất béo/chất xơ mà NIN 2017 không in (khoảng trống thật trong bảng gốc, không phải lỗi trích), đã tra bổ sung qua **USDA FoodData Central** — chỉ dùng khi khớp đúng loài (VD "Taro, raw" cho Khoai môn, "Mustard greens, raw" cho Cải ngọt, "Beans, snap, green, raw" cho Đậu cove); các trường hợp USDA trả về loài/sản phẩm khác (VD "Cranberries" cho Rau ngót, "Coriander" cho Rau răm, "Polish sausage" cho Giò lụa) đã **bị loại bỏ, để trống chứ không gán nhầm loài** (DEC-008).
- **Vòng 2 (dùng sheet "Bảng TP"/"Bảng TP có phospho" của file Excel làm từ điển tên/alias, KHÔNG dùng số liệu của sheet đó):** hai sheet này liệt kê ~841 tên món (bản chép lại danh mục NIN, không tự trích dẫn được số trang) — dùng để tìm đúng tên/alias rồi tra lại trực tiếp trong PDF NIN 2017, thêm được 3 dòng: Ngô luộc (mã 01023, tên gốc "Ngô nếp luộc"), Rau cải ngọt (mã 04108), Đậu cove (mã 04029, bản tươi chứ không phải hạt khô).
- **Còn trống (không tìm được nguồn đáng tin cậy cho đủ 8 cột bắt buộc):** Bánh mì (bánh mì trơn không có mục riêng trong NIN 2017), Mì ăn liền, Sắn luộc, Yến mạch, Thịt lợn ba chỉ, Thịt gà ức/đùi theo phần, Lòng lợn, Giò lụa, Chả quế (thiếu Na/K, USDA không có món tương đương), Cá lóc/bống/khô/Tôm sú, Đậu phụ chiên, Chao, Tương hột, Rau ngót/mồng tơi/má/răm/Tía tô/Kinh giới/Bí đao (thiếu chất béo — bảng gốc không in vì lượng quá nhỏ, không phải =0, và USDA không có loài tương ứng), Thanh long, Sữa tươi có đường, Nước cốt dừa, Mắm nêm, Mắm ruốc, Đường thốt nốt.
- **File "Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx"**: 2 sheet "Bảng TP"/"Bảng TP có phospho" chỉ dùng làm **từ điển tên món để tra lại NIN 2017**, không dùng số liệu trực tiếp của sheet — vì đây là file bài tập môn học của sinh viên (form "PHIẾU ĐÁNH GIÁ KHẨU PHẦN" chấm Đạt/Không đạt, công thức BMR theo WHO, số liệu tự chép từ NIN nhưng không dẫn số trang gốc) — không phải nguồn khoa học độc lập, vi phạm nguyên tắc truy vết của RULE R40.2/DEC-008 nếu dùng trực tiếp làm `source_ref`.

### Về `gi_values.csv` (bảng GI tách riêng — DAT-07)

GI có **nguồn riêng**, tách khỏi `source_ref` của NIN (RULE-2), nên để ở file riêng và merge vào `food_items` khi nạp. Cột: `food_id, name_vi, gi_index, gi_source, gi_source_ref, note`.

- **7 dòng hiện có** trích từ [Chan HMS et al. 2001, *Eur J Clin Nutr* 55:1076–1083](https://www.nature.com/articles/1601265), Table 2 (glucose=100, n=12) — đây là các món Việt mà bảng quốc tế **không có**: bún/bánh phở tươi (40), cơm tẻ jasmine (109), xôi (94), na (58), sữa đặc (61). Một dòng (miến dong 39) là `estimated` proxy từ miến đậu xanh — đã ghi rõ trong `note`.
- **4 dòng bổ sung (DAT-08)** trích từ [Atkinson FS et al. 2021, *Am J Clin Nutr* 114:1625–1632](https://academic.oup.com/ajcn/article/114/5/1625/6320814): gạo lứt **65**, khoai tây luộc **73**, yến mạch **55**, cà chua **22** — đều là **trị nêu rõ trong phần Results/Discussion** của bài (không phải trung bình nhóm).
- **DAT-08b (đã làm):** đã trích **Supplemental Table 1 của Atkinson 2021** (bản PDF `docs/TLTK/SupplementalTable1.pdf`) cho 17 món per-food: chuối 47, cam 45, quýt 52, táo 44, lê 33, xoài 48, đu đủ 38, dứa 82, dưa hấu 51, vải 57 (tươi), ổi 29, nho 54, khoai lang 77, ngô 52, bánh mì 59 (proxy), đậu xanh 42, giá đỗ 25. Mỗi trị dẫn số hiệu mục trong bảng.
- **Cố ý để trống (không có mục sạch trong Suppl. Table 1):** đậu đen, đậu đỏ (chỉ có "red bean paste" đã chế biến), thanh long, sầu riêng, bơ (quá ít carb để đo). Để None còn hơn gán sai (DEC-008).
- Trị GI phủ thưa là bình thường; menu engine đã thiết kế suy giảm mềm khi `gi_index` = None.

Sau khi nhập xong, đổi tên `food_items.template.csv` → `food_items.csv`.

### Về bộ FoodData Central bulk download (DAT-10)

Ngoài API USDA gọi từng món, đã tải 3 bộ **bulk download** chính thức từ [fdc.nal.usda.gov/download-datasets](https://fdc.nal.usda.gov/download-datasets.html) để đối chiếu offline:

- **`FoodData_Central_foundation_food_json_2025-12-18`** (365 món, nguyên liệu thô phân tích phòng thí nghiệm) — đã khảo sát, hầu như không có món Việt/châu Á cụ thể, không dùng để lấp `food_items.csv`. **Phát hiện kỹ thuật quan trọng nếu dùng sau này:** nutrient id năng lượng KHÔNG đồng nhất — phần lớn món (226/365 và 199/365) dùng `id=2047`/`2048` ("Energy Atwater General/Specific Factors") thay vì `id=1008` ("Energy") mà `scripts/fetch_usda_foods.py` hiện chỉ map — cần sửa `NUTRIENT_ID_MAP` nếu tích hợp file này, nếu không sẽ hụt kcal ở phần lớn dòng.
- **`FoodData_Central_survey_food_json_2024-10-31`** (`surveyDownload.json`, FNDDS/"What We Eat In America" — món **đã chế biến/phối hợp**, không phải nguyên liệu thô) — **5.432 món, 5431/5432 có đủ 9 chất cốt lõi** (tỷ lệ đầy đủ cao hơn hẳn Foundation Foods). Đây là nguồn đã dùng để lấp thêm 5 dòng còn trống trong `food_items.csv` (DAT-10):
  - **Bánh mì** (id 7) ← "Bread, white", `fdcId 2707598`
  - **Thanh long** (id 116) ← "Dragon fruit", `fdcId 2709234`
  - **Nước cốt dừa** (id 136) ← "Coconut milk, used in cooking" (KHÔNG dùng biến thể "Coconut milk" — đó là loại pha loãng dạng thức uống, kcal chỉ 31/100g, sai bản chất nước cốt dừa nấu ăn), `fdcId 2705413`
  - **Tôm sú** (id 48) ← "Shrimp, steamed or boiled", `fdcId 2706363` — tôm chung, **không phân biệt loài** cụ thể là tôm sú, ghi rõ trong `source_ref`
  - **Lòng lợn** (id 27) ← "Chitterlings", `fdcId 2706163`, `source=estimated` — đây là món lòng chế biến kiểu phương Tây (thường chiên/nấu nhiều mỡ, 20,2 g béo/100g), khác lòng luộc kiểu Việt, dùng tạm làm proxy có ghi rõ hạn chế
  - Đã **cố ý bỏ qua** "Soup, ramen noodles, water added" cho **Mì ăn liền**: mì ramen Nhật pha loãng (66 kcal/100g) khác quá xa mì gói Việt Nam (thường đặc/nhiều dầu hơn) — để trống còn hơn gán sai (DEC-008)
  - Không tìm được mục phù hợp cho: Cá lóc, Cá khô, Đậu phụ chiên, Chao, Tương hột (miso khác bản chất), Rau răm/Tía tô/Kinh giới/Rau má (thảo mộc Việt không có trong khảo sát Mỹ), Đường thốt nốt
- **`FoodData_Central_csv_2025-12-18`** (bulk CSV toàn bộ database quan hệ, gồm `branded_food.csv` 950MB + `food_nutrient.csv` 1,78GB) — đã xem cấu trúc bảng (`branded_food.csv` chỉ có metadata sản phẩm đóng gói Mỹ, không có giá trị dinh dưỡng trực tiếp, phải JOIN qua `food_nutrient.csv`). **Chưa khai thác sâu** — chi phí xử lý cao (phải join 2 file rất lớn) trong khi giá trị thấp cho mục tiêu "thực phẩm Việt phổ thông" của dự án (branded food chủ yếu là sản phẩm đóng gói thương hiệu Mỹ). Không commit các file gốc — đã bị `.gitignore` (`data/*`) chặn sẵn.

---

## Quy trình nhập một dòng thực phẩm

1. **Tra alias trước** — có thể món đã tồn tại dưới tên khác (`dứa` = `thơm` = `khóm`)
2. Tìm trong **NIN** → nếu không có, tìm **USDA** → nếu vẫn không có, dùng OOV Estimator và đặt `source=estimated`, `is_estimated=TRUE`
3. Điền `source_ref` đủ để người khác tra lại được:
   - `NIN` → `Bảng TPTP VN 2007, tr.42`
   - `USDA` → `USDA fdcId:169756`
   - `estimated` → `Ước tính từ công thức: 60g gạo + 40g thịt`
4. Chạy `python scripts/validate_data.py`
5. PR → **R2 review** (bắt buộc, theo CODEOWNERS)

### Ưu tiên khi nhập

Cột `priority_note` đánh dấu các dòng quan trọng nhất. Nhóm **gia vị và nước chấm** phải nhập trước tiên và chính xác nhất — 70–81% lượng natri của người Việt đến từ nhóm này, và đây là trục chính của bài toán. Nước mắm, bột canh, hạt nêm, mắm nêm, mắm tôm sai số liệu thì toàn bộ tính năng cảnh báo muối trở nên vô nghĩa.

---

## Quy tắc kiểm tra tự động

`scripts/validate_data.py` chặn merge khi:

- Thiếu `source` hoặc `source_ref` (hoặc để `TODO`)
- Giá trị ngoài khoảng hợp lý (kcal 0–900; protein 0–90 g; natri 0–25.000 mg — trần cao vì nước mắm thật sự rất mặn)
- Tổng đa chất > 105 g trên 100 g thực phẩm
- `source=estimated` nhưng `is_estimated` không phải `TRUE`
- Trùng `id` hoặc trùng tên

Cảnh báo (không chặn merge, nhưng phải xử lý trước Demo Day): dòng chưa nhập, rule còn `to_verify`, tương tác thuốc thiếu `source_ref`.

---

## Mốc kiểm chứng (dùng làm test hồi quy)

Sau khi nhập xong nhóm gia vị và món ăn, các con số sau phải tái lập được:

| Món | Giá trị tham chiếu | Ý nghĩa |
|---|---|---|
| Phở bò 1 bát | 3,3–4,0 g muối | Nếu tính ra 1 g → công thức thiếu nước dùng/gia vị |
| Bún cá 1 bát | ~6,2 g muối | |
| Mì ăn liền 1 gói | 4,2–5,0 g muối | |

Lệch xa các mốc này nghĩa là **công thức sai, không phải mốc sai**.

---

## Bản quyền

- Ghi rõ nguồn cho mọi dữ liệu sử dụng.
- Với tài liệu có bản quyền: **chỉ trích dẫn có dẫn nguồn, không sao chép nguyên khối vào repo.**
- Dự án học thuật vẫn phải tôn trọng quyền tác giả.

## Dữ liệu bệnh nhân

**100% mô phỏng.** Không đưa dữ liệu bệnh nhân thật vào repo, DB hay prompt — kể cả đã ẩn danh, kể cả trong file test. Seed bệnh nhân dùng tên rõ ràng là giả (`BN-DEMO-01`) nhưng chỉ số lâm sàng phải hợp lý để demo thuyết phục. R2 chịu trách nhiệm về tính hợp lý này.
