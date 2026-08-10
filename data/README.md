# DATA — Nguồn, giấy phép và quy trình nhập liệu

> Owner: **R2** · Ticket: DAT-00 → DAT-06, DAT-23

---

## 📁 Ba tầng dữ liệu (DAT-23 / DEC-022)

Nguyên tắc một câu: **`data/seeds/` là thứ chạm tới bệnh nhân. Mọi thứ khác không nằm ở đó.**

| Thư mục | Nội dung | Được seed vào DB? | Loader đọc lúc chạy? |
|---|---|---|---|
| `data/seeds/` | Món Việt curated + NIN 2017 + rule lâm sàng + tương tác thuốc | ✅ có | ✅ có |
| `data/reference/` | Khối tham chiếu USDA/FNDDS tiếng Anh (6854 food, 2632 dish) | ❌ không | ❌ không |
| `data/quarantine/` | Nợ dữ liệu chờ R2 duyệt: mẫu thực đơn `MENU-*`, dòng chưa có số liệu | ❌ không | ❌ không |

**Vì sao tách:** trước DAT-23, cả bốn nguồn nằm chung trong `food_items.csv` (7745 dòng, 89% tên tiếng Anh) và `dishes.csv` (2677 dòng, 98% FNDDS). Mỗi loader tự lọc rác theo cách riêng, lọc lệch nhau, và mẫu thực đơn `MENU-*` đã lọt lên UI bệnh nhân dưới dạng tên món ("Bữa sáng - Thực đơn 3 (TĐ 3+4)").

**Ranh giới tầng** định nghĩa **một chỗ duy nhất** ở `src/clinical/tiers.py` — validator, loader và script tách đều dùng chung, không định nghĩa lại.

⚠️ Khối USDA là **khoảng đóng `id 167516–1105897`**, không phải "mọi id lớn hơn ngưỡng". 430 dòng NIN 2017 tiếng Việt (id 1105898–1106327) nằm **ngay sau** khối USDA — mọi điều kiện kiểu `id >= 167516` sẽ xoá nhầm chúng.

**Tách lại sau khi thêm dữ liệu mới:**

```bash
python scripts/split_data_tiers.py --dry-run   # xem bảng đối chiếu, chưa ghi
python scripts/split_data_tiers.py             # tách thật
python scripts/validate_data.py                # phải 0 lỗi
```

Script tất định, idempotent, và **từ chối chạy** nếu có dòng sai số cột hoặc món tầng `seeds` tham chiếu nguyên liệu ngoài tầng `seeds`.

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
| **Tương tác thuốc – thực phẩm** | `drug_food_interactions.csv` | 🟡 đã seed 30 cặp, chưa có `source_ref` | Xem mục "DDID" bên dưới, và **Dược thư Quốc gia VN 2022** ở mục nghiên cứu bổ sung |
| **Open Food Facts** | Thực phẩm đóng gói/công nghiệp (mì gói theo nhãn hiệu, nước chấm đóng gói) mà NIN/USDA không có | 🟢 xác nhận dùng được, chưa tích hợp | Free API, ODbL license. `source_ref` = `Open Food Facts, barcode:xxxxxxxxxxxxx` |

### Về DDID (23.950 bản ghi tương tác)

Đề án ban đầu định dùng trọn bộ DDID. **Quyết định đã đổi (ADR-005):** license chưa rõ ràng và 23.950 bản ghi là quá thừa cho 4 nhóm bệnh của đề bài. Thay bằng **80 cặp curated** — hiện đã seed 30 cặp phổ biến nhất, cần bổ sung thêm 50.

Nếu vẫn muốn dùng DDID: phải kiểm tra license **trước khi** import, và ghi kết quả kiểm tra vào `DEVLOG.md` §3.

---

## Nghiên cứu bổ sung nguồn dữ liệu (DAT-01, dựa trên `data/Dữ liệu dinh dưỡng Việt Nam.md`)

Tài liệu tổng quan `data/Dữ liệu dinh dưỡng Việt Nam.md` (57 trích dẫn, khảo sát hệ sinh thái dữ liệu dinh dưỡng VN + quốc tế) nêu 8 nguồn ngoài NIN/USDA. Đã tự xác minh từng nguồn qua web (không chép nguyên claim từ tài liệu — một số claim trong đó chưa kiểm chứng được, VD số liệu Open Food Facts luôn thay đổi theo thời gian thực). Kết quả:

| Nguồn | Xác minh được | Quyết định |
|---|---|---|
| **Open Food Facts** | ✅ API free, không cần key, giấy phép **ODbL** (Open Database License — cho phép dùng lại có ghi nguồn), endpoint `/api/v2/product/{barcode}.json`, giới hạn 15 req/phút/IP. Có sản phẩm Việt thật (VD mì Omachi — `world.openfoodfacts.org/product/8936221043064/mi-tomyum-omachi`), `vn.openfoodfacts.org` liệt kê 399 category cho VN | **Dùng được** cho nhóm thực phẩm đóng gói/công nghiệp mà NIN/USDA không có (mì gói theo nhãn hiệu, nước chấm/gia vị đóng gói cụ thể). `source_ref` đề xuất: `Open Food Facts, barcode:xxxxxxxxxxxxx` |
| **FAO/INFOODS uFiSh1.0** | 🟡 Xác nhận có thật: file Excel, 12 sheet, 78 loài cá/giáp xác/nhuyễn thể, bản 2016. Trang gốc `openknowledge.fao.org` không tải được lúc kiểm tra (lỗi kết nối, có thể tạm thời) — **chưa xác nhận được link tải + điều khoản license cụ thể** | **Cần thêm bước xác minh** trước khi seed — R2 tự thử tải link `openknowledge.fao.org/handle/20.500.14283/i6655en` trực tiếp (không qua tool fetch), nếu vào được thì license FAO nhìn chung cho phép dùng phi thương mại có trích dẫn |
| **FAO/INFOODS PhyFoodComp1.0** | ✅ Có thật (2018, hợp tác FAO/INFOODS/IZiNCG), dữ liệu phytate + tỷ lệ mol với Fe/Zn/Ca | ❌ **Không tích hợp.** Phytate phục vụ đánh giá sinh khả dụng khoáng chất (thiếu máu/thiếu kẽm) — ngoài phạm vi 4 bệnh mục tiêu (ĐTĐ2, THA, CKD, gout). Ghi nhận làm nguồn tương lai nếu dự án mở rộng sang thiếu vi chất |
| **EuroFIR eBASIS** | ⚠️ Trang chủ `eurofir.org` mô tả eBASIS là lợi ích dành cho **thành viên** (membership), không nêu rõ có gói truy cập miễn phí công khai hay không | ❌ **Không tích hợp** — rủi ro vi phạm giấy phép nếu dùng mà chưa xác nhận, đúng nguyên tắc "để trống còn hơn dùng sai nguồn". Có thể xác minh lại sau nếu cần polyphenol/phytosterol cho rau |
| **ASEANFOODS** | ✅ Có bản điện tử độc lập tại Viện Dinh dưỡng ĐH Mahidol, Thái Lan (`inmu.mahidol.ac.th/aseanfoods`, bản 2/2014) | ❌ **Không ưu tiên** — theo chính tài liệu gốc, VFCT 2017 **đã đối chiếu chéo** với ASEANFOODS khi biên soạn, nên phần lớn giá trị đã nằm sẵn trong VFCT 2017 (đã có trong repo). Dùng lại sẽ trùng lặp, không phải nguồn bổ sung độc lập |
| **WikiFCD / FoodOn / Wikidata SPARQL** | ✅ Dự án có thật (semantic web, ánh xạ food entity ↔ Wikidata) | ❌ **Không làm cho MVP** — cần hạ tầng SPARQL/ontology mapping, không phục vụ trực tiếp ngưỡng lâm sàng nào của 4 bệnh mục tiêu. Rủi ro over-engineering rõ ràng so với lợi ích |
| **Quyết định 5948/QĐ-BYT (2021)** | ✅ Có thật: 633 cặp theo hoạt chất + 68 cặp theo nhóm dược lý, ban hành 30/12/2021, tải được qua thuvienphapluat.vn/luatvietnam.vn. **Nhưng:** mọi mô tả tìm được đều gọi đây là danh mục tương tác **thuốc – thuốc** ("tương tác thuốc chống chỉ định"), không tìm thấy xác nhận cụ thể văn bản có phủ cặp **thuốc – thực phẩm** (warfarin–vitamin K, statin–bưởi...) hay không | ⚠️ **Không dùng làm `source_ref` cho `drug_food_interactions.csv`** cho tới khi ai đó mở file thật và xác nhận có mục thuốc-thực phẩm — đừng suy đoán. Ghi nhận là nguồn tiềm năng cho một bảng `drug_drug_interactions` (ngoài schema hiện tại) trong tương lai |
| **Dược thư Quốc gia Việt Nam** (bản 3, 2022, QĐ 3445/QĐ-BYT) | ✅ 743 chuyên luận + 25 chuyên luận hướng dẫn chung, tra cứu online miễn phí tại `trungtamthuoc.com/hoat-chat`, `duocdienvietnam.com`, `vnras.com` (có bản PDF). Theo tài liệu gốc, có Phụ lục Tương tác Thuốc riêng, biên soạn dựa trên Martindale/BNF/AHFS | ✅ **Nguồn `source_ref` ưu tiên cho DAT-05** — mỗi cặp thuốc-thực phẩm trong `drug_food_interactions.csv` nên tra chuyên luận thuốc tương ứng trong Dược thư, `source_ref` dạng: `Dược thư Quốc gia VN 2022 (QĐ 3445/QĐ-BYT), chuyên luận <tên thuốc>` |

**Tóm lại:** 2 nguồn dùng ngay (Open Food Facts, Dược thư QGVN), 1 nguồn cần thêm bước xác minh (uFiSh1.0), 4 nguồn loại rõ lý do (PhyFoodComp, eBASIS, ASEANFOODS, WikiFCD/FoodOn), 1 nguồn cần đọc trực tiếp trước khi kết luận (5948/QĐ-BYT).

---

## Các file trong `data/seeds/`

> Cập nhật 2026-08-06. Số dòng không kể header.

| File | Dòng | Trạng thái | Ai phụ trách |
|---|---|---|---|
| `food_items.csv` | 7.315 | 🟢 file chính đang dùng — 7.293 có đủ số liệu, 22 còn trống. `category` phủ 96% (DAT-17), `purine_mg` phủ 51 món (DAT-14), `sugar_g` (đường tự do WHO) hầu như trống có chủ đích (DAT-15, xem lý do bên dưới) | R2 |
| `food_items.template.csv` | 152 | ⬜ trống phần số liệu — cần nhập | cả 4 người, xem cột `assigned_to` |
| `food_items.nin_draft.csv` | 152 | 🟡 **BẢN NHÁP** — 107 dòng có dữ liệu NIN thật, chờ R2 soát rồi promote (DAT-02) | R2 |
| `clinical_rules.csv` | 21 | 🔴 có ngưỡng + guideline_ref nhưng **100% `verify_status=to_verify`** — research 2026-08-06 phát hiện nhiều rule lệch/sai trích dẫn, 2 rule `hard` có rủi ro an toàn thật (xem `CLN-11`, ưu tiên P0) | R2 |
| `drug_food_interactions.csv` | 30 | 🟡 có cơ chế + khuyến nghị, 13/30 thiếu `source_ref`; research 2026-08-06 phát hiện thêm lỗi trích dẫn cụ thể ở các dòng đã có nguồn (xem `DAT-21`) | R2 |
| `food_food_interactions.csv` | 9 | 🆕 **MỚI 2026-08-06** — tương tác thực phẩm-thực phẩm hoá sinh, PMID thật cho cả 9 dòng, `verify_status=to_verify` (xem `DAT-18`) | R2 |
| `drug_meal_timing.csv` | 6 | 🆕 **MỚI 2026-08-06** — giờ dùng thuốc so với bữa ăn, `verify_status=to_verify` (xem `DAT-19`) | R2 |
| `gi_values.csv` | 28 | 🟡 7 món Việt (Chan 2001) + 21 staple/quả (Atkinson 2021 Suppl. Table 1, DAT-08/08b) — **~39 giá trị mới đã tìm được nguồn nhưng CHƯA merge** (xem `DAT-20`) | R2 |
| `purine_values.csv` | 19 | 🟡 bảng phụ trợ cũ (staging, không phải nguồn chính) — 32 món curated khác đã được gán `purine_mg` trực tiếp vào `food_items.csv` (không qua file này), xem `DAT-14` | R2 |
| `purine_db_reference.csv` | 475 | 🆕 **MỚI 2026-08-06** — bảng tra cứu purine thô trích từ `PURINEDATABASEANDDATASOURCES2025.xlsx` (nguồn USDA/ODS-NIH R2.0), dùng làm nguồn cho `DAT-14`, còn dư địa map thêm | (tham chiếu, không phải bảng DB) |
| `usda_sugar_coverage.csv` | 5.620 | 🆕 **MỚI 2026-08-06** — bảng tra cứu "Total Sugars" theo `fdc_id` từ USDA bulk, dùng nếu R2 chọn hướng thêm cột `total_sugar_g` (xem `DAT-15`) | (tham chiếu, không phải bảng DB) |
| `serving_sizes.csv` | 174 | 🟢 5 dòng khẩu phần món Việt cụ thể (gốc) + 169 dòng `wweia_*` (trung vị khẩu phần thật theo 172 nhóm USDA WWEIA — **khẩu phần kiểu Mỹ, không phải VN**, dùng tham chiếu/dự phòng, xem `DAT-16`) | R2 |

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
- **`FoodData_Central_csv_2025-12-18`** (bulk CSV toàn bộ database quan hệ, gồm `branded_food.csv` 950MB + `food_nutrient.csv` 1,78GB) — `branded_food.csv` (1.993.975 dòng, sản phẩm đóng gói thương hiệu Mỹ) **cố ý không khai thác** — chi phí xử lý cao, giá trị thấp cho mục tiêu dự án. Đã khai thác sâu **`sr_legacy_food.csv`** (7.793 món) + **`foundation_food.csv`** (436 món) + **`survey_fndds_food.csv`**/`input_food.csv` (món quốc tế phối hợp) — xem mục "DAT-12 — bỏ trần dữ liệu" bên dưới. Không commit các file gốc USDA — đã bị `.gitignore` (`data/*`) chặn sẵn.

### DAT-12 — bỏ trần dữ liệu: USDA bulk (SR Legacy/Foundation) + NIN 2017 toàn bảng + FNDDS quốc tế (2026-08-05)

Ba script mới, chạy 1 lần lấy toàn bộ dữ liệu có nguồn thật từ tài nguyên đã có sẵn trong `data/` (không gọi API, không suy đoán):

**1. `scripts/extract_usda_bulk.py`** → `data/seeds/food_items.usda_bulk.csv` (**6.854 dòng**, đã merge vào `food_items.csv`)
- Trích từ `food.csv` + `food_nutrient.csv` (SR Legacy + Foundation Foods), chỉ giữ dòng có đủ 8 cột bắt buộc (RULE-2 — thiếu bất kỳ cột nào thì bỏ, không suy đoán = 0).
- Loại luôn các mục cô đặc thật nhưng vô nghĩa lâm sàng (bột nở, kem tartar, bột trà hoà tan — per-100g vượt khoảng "thực phẩm ăn được thông thường" dù số liệu USDA đúng, không ai ăn 100g bột nở).
- **Quy ước ID:** dùng thẳng `fdc_id` của USDA (luôn ≥ 100000) làm `id`, không cấp ID nội bộ mới — tránh trùng, giữ khả năng truy vết bằng chính con số.
- **Quan trọng — hồi quy hiệu năng đã phát hiện và sửa:** `retrieve_context` (node LangGraph, `src/agents/nodes/core.py`) trước đó đưa TOÀN BỘ `food_items` làm ứng viên cho CP-SAT/prompt Gemini. Với ~7000 dòng thay vì ~150, CP-SAT chậm **30-50 lần** (đo thực tế: 13 test từ ~1,5s → ~50s). Đã thêm hằng số `USDA_BULK_ID_THRESHOLD = 100_000`: khối USDA bulk chỉ là **kho tham chiếu** (tra cứu, OOV, mở rộng sau), bị loại khỏi ứng viên sinh thực đơn. Curated Việt Nam (id < 100000) không bị ảnh hưởng.

**2. `scripts/extract_nin2017_bulk.py`** → `data/seeds/food_items.nin2017_bulk.csv` (**167 dòng mới**, đã merge)
- Trích TOÀN BỘ bảng chính "Bảng TPTP VN 2017" (304 trang) bằng `pdfplumber`, neo cột theo toạ độ x của header tag-name (`EDIBLE ENERC WATER PROCNT FAT CHOCDF FIBC...`) lặp lại mỗi trang — đã xác nhận khớp 100% với dòng có sẵn (mã 01003 "Gạo tẻ giã" ra đúng kcal=347/protein=8,1/carb=75,7/fat=1,3/fiber=0,7/na=5/k=202/p=108, khớp hệt id=1 hiện có).
- **Phát hiện kỹ thuật:** tên món và số liệu trên cùng 1 "dòng" thực phẩm không cùng toạ độ `top` chính xác (lệch tới ~6pt) — bin cứng theo top ban đầu bỏ sót nhiều dòng; sửa bằng gán mỗi từ vào **mã gần nhất** theo khoảng cách top.
- Trong 621 mã có đủ cột dữ liệu trên trang hợp lệ, 87 mã đã có sẵn trong `food_items.csv` (từ DAT-02/09/10 trước), chỉ 167/534 mã còn lại có ĐỦ cả 8 cột bắt buộc — phần lớn còn lại thiếu Na/K/chất béo/chất xơ **thật sự không in trong bảng gốc** (khoảng trống thật, không phải lỗi trích — đúng phát hiện đã ghi ở DAT-09), bị loại đúng theo RULE-2/DEC-008, không suy đoán.
- ⚠️ **Chất lượng tên:** cột `name_vi` của lô này lấy theo toạ độ, có thể lẫn từ tiếng Anh/sai thứ tự với vài mục (số liệu dinh dưỡng không bị ảnh hưởng — luôn đọc đúng cột theo neo tag-name). Mỗi dòng có `source_ref` = trang + mã NIN chính xác để đối chiếu/sửa tên khi cần.

**3. `scripts/extract_fndds_dishes.py`** → `data/seeds/dishes.fndds_bulk.csv` + `dish_ingredients.fndds_bulk.csv` (**2.632 món quốc tế**, đã merge)
- USDA FNDDS ("What We Eat In America" survey, `survey_fndds_food.csv` 5.432 món) có sẵn phân rã nguyên liệu thật trong `input_food.csv` (18.585 dòng, nối qua `sr_code`/NDB number → `fdc_id` SR Legacy). Đây là **món quốc tế (chủ yếu Mỹ) có ĐỦ nguyên liệu quy đổi được** sang `food_id` đã tồn tại trong `food_items.csv` — đúng kiến trúc RULE-1 (món = tổng nguyên liệu × gram tính bằng SQL, KHÔNG lưu số dinh dưỡng trực tiếp trên `dishes`).
- Chỉ giữ món có **TOÀN BỘ** nguyên liệu quy đổi được (2.632/5.432) — bỏ món thiếu bất kỳ nguyên liệu nào (2.799 món, phần lớn dùng nguyên liệu ngoài SR Legacy như branded/survey food chưa nhập).
- **Bug đã tìm và sửa:** 1 món ("Bread, other white") có nguyên liệu là công thức quy mô lớn (bột mì 4.540g — mẻ bánh thương mại, không phải khẩu phần ăn), vượt `MenuItem.grams<=2000` — thêm bộ lọc loại nguyên liệu > 2000g VÀ tổng khẩu phần > 2000g thay vì nới trần hệ thống cho một nhóm nhỏ dữ liệu ngoại lệ.
- `verified_by = "USDA FNDDS (nguồn chính thức)"` — **khác** `pending` của món Việt Nam tự soạn: đây là bản ghi trực tiếp từ khảo sát dinh dưỡng chính thức, không phải công thức LLM nháp cần R2 duyệt độ chính xác ẩm thực.

**Xác nhận thật (`make seed` trên SQLite trắng, 2 lần liên tiếp để kiểm idempotent):** 7.146 `food_items` / 2.635 `dishes` / 5.369 `dish_ingredients`, 0 lỗi FK, số dòng không đổi giữa 2 lần chạy.

**Chưa làm trong đợt này (còn để ngỏ):**
- `PURINEDATABASEANDDATASOURCES2025.xlsx` (608 dòng purine North America + non-NAm) — có sẵn trong `data/`, chưa khai thác. Cần ghép tên món với `food_items.csv` (fuzzy match), không đơn giản như 3 việc trên vì không có khoá chung (id/fdc_id) sẵn.
- NIN 2007 (526 món) — theo `data/README.md` mục DAT-09, tên món không đọc được đáng tin cậy (font TCVN3/VNI cũ). Bản 2017 đã phủ hầu hết, lợi ích thấp so với công sức xây bảng giải mã font riêng.
- 27 dòng `food_items.csv` gốc còn trống, `dishes.csv` gốc (3 món Việt tự soạn, `pending`), `clinical_rules.csv`, `drug_food_interactions.csv` (13/30 thiếu `source_ref`) — cần R2 chuyên môn lâm sàng thật, không tự ý làm (xem `docs/PLAN_DAT-12-uncap-data-and-db.md`).

### DAT-12 tiếp — bắt đầu lấp món Việt (2026-08-06, vẫn `pending`)

Trước đợt này `dishes.csv` chỉ có 3 món Việt gốc — toàn bộ 2.632 món thêm ngày 05/08 là USDA FNDDS (Mỹ), không giải quyết nhu cầu món Việt. Đã thêm 27 món/bữa ăn Việt mới, **tất cả vẫn `verified_by=pending`** — chưa qua R2, không dùng cho bệnh nhân:

- **15 "bữa ăn" trích từ nguồn thật:** `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` (file thực đơn nội bộ dự án, sẵn có trong `data/`, chưa từng khai thác) — 4 sheet thực đơn mẫu Sáng/Trưa/Tối với cột "KL sống sạch" (gram thật). Script `scripts/extract_menu_xlsx_dishes.py` parse theo state machine, khớp `food_id` bằng tên đã chuẩn hoá (bỏ ngoặc, hạ chữ thường) — **không fuzzy-match rộng** (để tránh gán nhầm loại thực phẩm, VD không tự suy "Dầu ăn" ≈ "Dầu ăn thực vật") nên tỷ lệ khớp chỉ ~37% (67/180 dòng nguyên liệu), 2 sheet đầu không có nhãn bữa ăn nên 0 kết quả. Dish_id dạng `MENU-<sheet>-TD<n>-<bữa>-<idx>`.
- **12 món Việt tự soạn qua LLM** (`data/seeds/dishes.vn_llm_draft.csv`): phở gà, bún chả, canh chua cá, rau muống xào tỏi, đậu phụ sốt cà chua, cá kho tộ, gà kho gừng, canh cải nấu tôm, sườn xào chua ngọt, trứng chiên hành, canh su hào cà rốt thịt băm, nấm hương xào thịt bò — nguyên liệu là `food_id` thật đã có trong hệ thống, nhưng **gram theo kinh nghiệm ẩm thực phổ thông, chưa đối chiếu nguồn định lượng nào** (khác 3 món gốc đã đối chiếu Na với nghiên cứu). Vài món thiếu gia vị (đường, dấm, nước dùng) vì chưa có `food_item` tương ứng.
- Đã kiểm tra 1 nguồn Hưng gợi ý (paper Epicure, arXiv 2605.22391 — Hugging Face `Kaikaku/epicure-*`): đây là model embedding nguyên liệu (Gemini embedding trên RecipeNLG/Recipe1M+/Xiachufang/ChefKoch/SOMOS/USDA), có công thức định lượng thật nhưng **không có món Việt Nam** trong bất kỳ dataset liệt kê — không dùng được cho mục tiêu này.
- **Xác nhận thật:** `validate_data.py` 0 lỗi mới, `pytest -q` 112/112, `make seed` (SQLite trắng, 2 lần) → `dishes` 2.635→**2.662**, `dish_ingredients` 5.369→**5.479**, 0 skip FK.
- Vẫn còn 30/2.662 món Việt (3 gốc + 27 mới) cần R2 duyệt tay — **không có bulk source Việt Nam nào tương đương FNDDS** để lấp nhanh tới mục tiêu 500 món; đường đi khả thi là R2 duyệt dần + LLM soạn thêm theo lô.

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

## Đợt 2026-08-06 — khai thác dữ liệu local + research bổ sung (DAT-14 → DAT-21)

Theo yêu cầu Hưng ("nghiên cứu trên tạp chí y khoa, dinh dưỡng VN, thực đơn vùng miền, tương tác dược-thực phẩm, GI/purine, serving_sizes, USDA, viết lại README"). Chi tiết đầy đủ từng ticket ở `docs/TICKETS.md` (`DAT-14` đến `DAT-21`, `CLN-11`), quyết định + rationale đầy đủ ở `DEVLOG.md` các entry ngày 2026-08-06. Tóm tắt ở đây để người mới đọc nắm nhanh mà không phải lục cả DEVLOG.

### Đã khai thác xong (từ file local sẵn có trong repo, không cần internet)

| Việc | Nguồn | Kết quả | Ticket |
|---|---|---|---|
| Purine 32 món curated | `PURINEDATABASEANDDATASOURCES2025.xlsx` (USDA/ODS-NIH Purine DB R2.0, 2025) → `purine_db_reference.csv` (475 dòng) | `purine_mg` phủ 19 → 51 món; chỉ map khi chắc chắn cùng loài (bỏ qua match mơ hồ) | `DAT-14` |
| `serving_sizes` 5 → 174 dòng | `food_portion.csv` (47.446 bản ghi USDA FNDDS) theo 172 nhóm **WWEIA** (NHANES) | 169 dòng mới = trung vị khẩu phần thật, ghi rõ là chuẩn Mỹ không phải VN | `DAT-16` |
| `category` 2% → 96% | `food_category.csv` chính thức USDA (28 nhóm), dịch sang tiếng Việt | 6.870/7.315 dòng được gán nhãn | `DAT-17` |
| `sugar_g` — khảo sát khả thi | `food_nutrient.csv` USDA bulk (1,78GB) | "Sugars, added" = 0% dữ liệu; "Total Sugars" = 81,9% nhưng khác nghĩa free-sugar WHO → KHÔNG lấp, ghi ticket cho R2 quyết schema | `DAT-15` |

### Đã research xong, có nguồn thật (PMID/DOI), CHƯA merge vào CSV — cần R2 xác nhận trước

| Việc | Kết quả chính | Ticket |
|---|---|---|
| Verify 21 `clinical_rules` | Chỉ 7/21 khớp đúng nguồn gốc (KDIGO 2024, KDOQI 2020, NIN 2016, ADA 2026 — đọc toàn văn). **2 rule `hard` có rủi ro an toàn thật**: `CKD-PRO-01` không phân biệt bệnh nhân lọc máu (G5D cần 1.0-1.2 g/kg, không phải trần 0.8 g/kg); 3 rule kali `CKD-K-01/02/03` trích dẫn sai mức chứng cứ KDOQI (thực tế chỉ ở mức OPINION) | `CLN-11` (P0) |
| GI món Việt — 39 giá trị mới | Chan 2001 (PMID 11781674, đọc toàn văn), Atkinson 2008 (PMC2584181), Henry 2021 compendium 940 món châu Á (PMID 33414403). Phát hiện: Việt Nam KHÔNG có trong danh sách quốc gia của compendium — chưa có nghiên cứu GI đo trực tiếp trên người tại VN đạt chuẩn quốc tế | `DAT-20` |
| Tương tác thực phẩm-thực phẩm | 9 cặp PMID thật — **đã seed** vào bảng DB mới `food_food_interactions` (xem dưới) | `DAT-18` |
| Giờ dùng thuốc so với bữa ăn | 6 thuốc — **đã seed** vào bảng DB mới `drug_meal_timing` (xem dưới) | `DAT-19` |
| Verify `drug_food_interactions.csv` hiện có | Phát hiện lỗi trích dẫn cụ thể ở 6+ dòng (gán sai chuyên luận, sai tên tác giả, severity không khớp mức bằng chứng) — CHƯA sửa, chờ R2 | `DAT-21` |
| Thực đơn/mâm cơm 3 miền | Không có nghiên cứu ẩm thực học định lượng (chỉ nguồn báo/blog phổ thông). Đề xuất 20 món theo vùng. **Cảnh báo an toàn:** món đề xuất dùng khế (carambola) — y văn ghi nhận khế chứa caramboxin, chống chỉ định CKD | `DAT-04` (cập nhật) |

### Bảng DB mới (schema + migration + seed — đã code xong 2026-08-06)

- **`food_food_interactions`** — tương tác hoá sinh thực phẩm-thực phẩm (VD phytate/tannin ức chế hấp thu sắt, canxi ăn cùng bữa giảm nguy cơ sỏi thận do oxalat, fructose/rượu tăng acid uric liên quan gout). Model: `src/db/models.py::FoodFoodInteraction`.
- **`drug_meal_timing`** — thời điểm uống thuốc so với bữa ăn theo dược động học (KHÔNG phải khuyên liều — chỉ mô tả timing theo dược thư). Model: `src/db/models.py::DrugMealTiming`.
- Migration: `alembic/versions/5394cb31dc4e_food_food_interactions_drug_meal_.py`. ERD cập nhật trong `docs/ARCHITECTURE.md`.
- **Chưa wiring vào agent/API/UI** — mới dừng ở tầng dữ liệu, cả 2 bảng 100% `verify_status=to_verify`.

### Cách tái tạo (mọi bước đều có script, không sửa tay CSV)

```
python scripts/extract_purine_db.py              # DAT-14 bước 1: trích bảng purine thô
python scripts/map_purine_to_food_items.py        # DAT-14 bước 2: map vào food_items.csv
python scripts/scan_usda_sugar_coverage.py        # DAT-15: khảo sát độ phủ sugar (chỉ đọc, không ghi food_items.csv)
python scripts/build_serving_sizes_wweia.py       # DAT-16: sinh bảng WWEIA reference
python scripts/fill_category_from_usda.py         # DAT-17: lấp category
python scripts/validate_data.py                   # kiểm tra tất cả — phải 0 lỗi trước khi commit
```

Mọi script đều có `--dry-run` và idempotent (chạy lại nhiều lần không nhân đôi dữ liệu).

---

## Bản quyền

- Ghi rõ nguồn cho mọi dữ liệu sử dụng.
- Với tài liệu có bản quyền: **chỉ trích dẫn có dẫn nguồn, không sao chép nguyên khối vào repo.**
- Dự án học thuật vẫn phải tôn trọng quyền tác giả.

## Dữ liệu bệnh nhân

PRD v2.2 cho phép dùng NHANES 2021–2023 public-use, de-identified cho phát triển và kiểm thử theo NCHS Data User Agreement. Không được tái định danh, không đưa SEQN/PII/PHI vào UI, DB ứng dụng, prompt hoặc log, và không tuyên bố NHANES đại diện dân số Việt Nam.

Bộ benchmark trong `eval/datasets/` và demo seed bệnh nhân vẫn phải là dữ liệu mô phỏng, được đánh dấu rõ (`synthetic=true` hoặc ID `BN-DEMO-*`). Expected output của benchmark phải được tính và review độc lập với system under test.

### Nguồn nghiên cứu cho hồ sơ mô phỏng ĐTĐ2

Các hồ sơ mô phỏng trong `seeds/synthetic_t2dm_profiles_*.json` được sinh dựa trên **phân bố thống kê** học từ:

- **NHANES August 2021–August 2023** (CDC/NCHS)
- Phương pháp: Tải dữ liệu thật về máy local (ngoài repo) → phân tích phân bố có survey weights → sinh hồ sơ mô phỏng độc lập
- Dữ liệu cấp bản ghi chỉ được lưu/commit khi nguồn, license, de-identification và phạm vi sử dụng đã được xác minh; SEQN và mã định danh nguồn không được phát hành. Eval chỉ lưu hồ sơ mô phỏng có `synthetic=true`.

**Pipeline chi tiết:**
1. `scripts/download_nhanes_2021_2023.py` — tải 8 file XPT với checksum
2. `scripts/build_nhanes_2021_2023_cohort.py` — ghép files, lọc probable T2DM
3. `scripts/analyze_nhanes_distributions.py` — tính phân bố có survey weights
4. `scripts/generate_synthetic_t2dm_profiles.py` — sinh hồ sơ mô phỏng

Xem `docs/DATA_SYNTHESIS.md` để biết chi tiết về nguồn dữ liệu, heuristic lọc T2DM, phương pháp sinh mô phỏng, và limitation.
