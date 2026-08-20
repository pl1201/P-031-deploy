# Biên bản ký duyệt release dữ liệu lâm sàng — 2026-08-18

**Người ký:** R2 (phụ trách tri thức lâm sàng · dữ liệu · eval)
**Phạm vi:** bộ dữ liệu nền dùng cho sinh thực đơn ĐTĐ2 — `data/seeds/`
**Trạng thái:** ✅ **KÝ**, kèm 4 giới hạn ghi rõ ở §6 và 1 việc treo ở §7

---

## 1. Nội dung được ký

| Tệp | Số dòng | Trạng thái |
|---|---:|---|
| `clinical_rules.csv` | 25 rule | 25/25 `verified` |
| `dishes.csv` | 211 món | **199 đã ký** · 12 thu hồi (§7) |
| `dish_ingredients.csv` | 935 dòng | — |
| `food_items.csv` | 564 dòng | `sugar_g` phủ 205 (36,3%) |
| `drug_food_interactions.csv` | 30 dòng | 30/30 `verified` — xem §5 về phạm vi tự rà |
| `drug_meal_timing.csv` | 6 dòng | 6/6 `verified` |
| `food_food_interactions.csv` | 9 dòng | 9/9 `verified` |
| `household_units.csv` | 12 đơn vị | — |
| `dish_unit_conversions.csv` | 405 dòng / 168 món | — |

**Bộ sinh thực đơn nạp được 199 món**, phủ đủ mọi vai trò bữa ăn:

| Vai trò | Số món |
|---|---:|
| canh (`soup`) | 39 |
| món một bát (`one_dish`) | 38 |
| rau (`vegetable`) | 38 |
| tráng miệng (`dessert`) | 34 |
| đạm (`protein`) | 30 |
| tinh bột (`staple`) | 6 |

Kiểm chứng tự động tại thời điểm ký: **`scripts/validate_data.py` 0 lỗi**, **846 test pass**.

---

## 2. Ba quyết định lâm sàng chốt trong đợt này

Căn cứ đầy đủ ở `R2_RESEARCH_TRUOC_KHI_CHOT_2026-08-18.md`.

### 2.1. Protein giữ 15–20 %E (QĐ 5481), không nâng lên 20–25 %E

Hội thảo t-DNA 16/08 đề xuất 20–25 %E. Sau khi tra cứu, **giữ nguyên**:

- **ADA Standards of Care 2026 không đặt %E chung** cho người lớn ĐTĐ2; mốc duy nhất họ nêu là cho người cao tuổi — *0,8–1,5 g/kg hoặc **15–20 %E***, trùng khít QĐ 5481. ADA/EASD 2019 Consensus tuyên bố không có tỷ lệ %E lý tưởng.
- Bằng chứng cho protein cao **không nhất quán ở đúng mục tiêu chính là đường huyết**: phân tích gộp 12 nghiên cứu (n = 1.138) không thấy khác biệt FPG/HbA1c. Lợi ích thật nằm ở cân nặng (−2,08 kg) và lipid.
- **Căn cứ quyết định — nguy cơ thận ở nhóm nhận ngưỡng mặc định.** ADD-CKD Study (Szczech LA et al., *PLoS One* 2014, n = 9.307 bệnh nhân ĐTĐ2): **54,1% có CKD giai đoạn 1–5 nhưng chỉ 12,1% được bác sĩ nhận biết** (giai đoạn 1: chỉ 1,1%). Một hồ sơ khai "chỉ có ĐTĐ2" có xác suất đáng kể thật ra có CKD chưa chẩn đoán, mà KDIGO 2024 giới hạn 0,8 g/kg.

Protein cao vẫn là lựa chọn **cá thể hoá của chuyên gia** cho bệnh nhân đã xác nhận chức năng thận bình thường — đúng tầng, không phải ngưỡng mặc định.

### 2.2. Ký 19 món chè/bánh ngọt, để rule đường quyết định việc chọn

ADA (*Nutrition Therapy Consensus Report*) **cho phép** thay thế thực phẩm chứa sucrose đẳng nhiệt lượng cho carbohydrate khác — khuyến nghị là *hạn chế để không lấn chỗ thực phẩm giàu vi chất*, **không phải cấm**.

Nguyên tắc phân tầng được áp dụng:

| Cột | Trả lời câu hỏi |
|---|---|
| `verified_by` | *Dữ liệu công thức này có đúng không?* |
| `clinical_rules` | *Bệnh nhân này có nên ăn món đó không?* |

Từ chối ký một món **vì nó ngọt** là đặt phán đoán lâm sàng sai tầng.

Đo tại chỗ xác nhận rule đã tự làm việc — hồ sơ nữ 55 tuổi, trần đường tự do 34,3 g/ngày:

| Món | Đường/suất | % trần cả ngày |
|---|---:|---:|
| Chè hạt sen long nhãn | 35,6 g | **104%** |
| Bánh rán bọc đường | 30,0 g | 88% |

### 2.3. Xoá `PHO-BO-VCB`

Natri **10.506 mg/suất** (≈5 lần giới hạn cả ngày), 400 g hành tây + 100 g gừng **không có thịt bò, không có bánh phở**, thiếu `serving_g`. Đã bị lưới chặn của `ky_duyet_mon.py` từ chối. Có bản thay thế tốt hơn: `NIN-PHO-BO-CHIN`. Đã xoá ở cả CSV lẫn Supabase sau khi kiểm `food_logs` = 0 tham chiếu.

---

## 3. Sửa lỗi dữ liệu trong đợt này

### 3.1. 🔴 `sugar_g` của đường — lỗi nghiêm trọng nhất, đã vá

`Đường trắng` (id 149) và `Đường kính` (id 1106207) — **bản thân đường lại để trống `sugar_g`**. Được **47 món** dùng, nên mọi món ngọt báo ~0 g đường và rule `T2DM-SUG-01` (WHO 10 %E) **không bao giờ kích hoạt được**.

Sau khi vá: chè đỗ đen từ 2,3 g → **42,1 g đường**. Đã khoá bằng test hồi quy (`tests/test_r2_ca_nhan_hoa_oov.py::TestC22`), phá thử xác nhận đỏ đúng triệu chứng.

### 3.2. Phủ `sugar_g` từ 17,1% → 36,3%

| Nhóm | Dòng | Căn cứ |
|---|---:|---|
| `carb_g = 0` (thịt, cá, phủ tạng) | 101 | Suy ra tất yếu — đường là một phần của carb |
| Tra USDA FoodData Central | 5 | Gạo tẻ · Cải thảo · Hành củ · Cải ngọt · Khoai lang |
| Đường tinh luyện | 2 | id 149, 1106207 |

### 3.3. Hợp nhất quy ước nước dùng (20 món)

Việc `DEC-095 §④` ghi nhận là *"hai quy ước cùng tồn tại, chưa hợp nhất"*. Thêm dòng `Nước lã` cho 20 món canh/phở/chè. **Xác minh bằng so sánh với git HEAD: 0 món đổi kcal/natri**, đúng 20 món đổi khối lượng hiển thị — khớp đính chính `DEC-095 §②`.

### 3.4. Mở rộng quy đổi khẩu phần dân gian

17 → **168 món** có quy đổi; **154/199 món** quy đổi được khi truyền tổng nguyên liệu thật. Nguyên tắc: **không tạo số mới** — mỗi dòng lấy nguyên `serving_g` đã ký, chỉ đặt tên vật đựng.

---

## 4. Năng lực mới bổ sung cho tầng lâm sàng

| Module | Việc |
|---|---|
| `src/clinical/nutrition.py::compute_dish_nutrition()` | Dinh dưỡng **từng món** — trước đó chỉ tính được tổng cả thực đơn |
| `src/clinical/khau_phan.py` | Quy đổi gram ↔ bát/tô/thìa, phân biệt phương ngữ Bắc/Nam/Trung |
| `src/clinical/doc_khau_phan.py` | Đọc "2 bát cơm", "nửa tô phở" thành số — **tất định, không dùng LLM** |

Nguyên tắc kiến trúc được giữ: **LLM không bao giờ đoán số gram**. Số gram là con số dinh dưỡng, đi thẳng vào tổng carb của ngày (RULE-1).

---

## 5. Phạm vi tự rà của người ký — đọc kỹ

Biên bản này chỉ nhận phần **tôi tự đối chiếu trong đợt này**:

| Nhóm | Tôi tự rà | Ghi chú |
|---|---|---|
| `clinical_rules.csv` 25 rule | Rà lại toàn bộ; sửa/ghi căn cứ cho `T2DM-PRO-01/03` | Phần lớn đã `verified` từ các đợt 12–17/08 |
| `drug_food_interactions.csv` | **13 dòng** — 12 dòng severity `high` + viết lại Warfarin×rượu | 17 dòng còn lại mang chữ ký từ đợt trước hoặc phiên khác, **tôi không tự rà lại** |
| `drug_meal_timing.csv` 6 dòng | Có | |
| `food_food_interactions.csv` 9 dòng | Có — phát hiện và sửa **2 lỗi trích dẫn tạp chí** | Hurrell 1999 và Tuntawiroon 1990 bị ghi nhầm sang *Am J Clin Nutr* |
| `dishes.csv` | 19 món ngọt (ký) + 12 món (thu hồi) | 180 món còn lại mang chữ ký từ các đợt trước |

**Về phiên song song — đã đối chiếu, KHÔNG mất việc.** Trong lúc kiểm kê tôi thấy hai dấu hiệu đáng ngờ: 9 dòng `drug_food_interactions.csv` mang ghi chú `verified` với văn bản khác của tôi, và `git status` báo 3 tệp tương tác không có thay đổi dù tôi vừa sửa. Đã đối chiếu trực tiếp với `git show HEAD`:

* Toàn bộ thay đổi của tôi **có trong HEAD** — 2 sửa trích dẫn tạp chí, bản viết lại Warfarin×rượu, 12 dòng ghi chú ký, 6/6 `drug_meal_timing`.
* Nội dung HEAD và cây làm việc **giống hệt nhau**; khác biệt duy nhất là ký tự xuống dòng, do `core.autocrlf = true`.

Kết luận: phiên song song đã **commit kèm** công việc của tôi (commit `8f980c8`) chứ không ghi đè. Nghi vấn ban đầu là báo động nhầm — nguyên nhân kỹ thuật, không phải xung đột. 9 dòng `moderate` mang ghi chú của phiên kia thì tôi vẫn **không nhận là mình rà**.

---

## 6. Bốn giới hạn đã biết, ký kèm chứ không giấu

1. **`sugar_g` mới phủ 36,3%.** Món chứa nguyên liệu thiếu `sugar_g` **bị loại khỏi ràng buộc đường** (`_dish_nutrient_totals` trả `None`) chứ không bị tính là 0 — đúng RULE-2, nhưng nghĩa là rule đường chưa áp được cho mọi món.
2. **`carb_g` từ NIN, `sugar_g` từ USDA** ở 5 dòng vừa tra — hai bảng đo giống/điều kiện khác nhau nên tỷ lệ đường/carb có thể lệch so với tỷ lệ nội bộ của USDA. Ràng buộc `sugar_g ≤ carb_g` vẫn được kiểm.
3. **31 món chưa quy đổi được khẩu phần** — hiển thị gram, không bịa "khoảng 1 phần".
4. **Chưa có HbA1c trong hồ sơ** — đây là **bước 1** của thuật toán t-DNA. Đã đặc tả, chờ R4 làm schema.

---

## 7. Việc treo — 12 món bị thu hồi chữ ký

Chi tiết ở `R2_12_MON_CAN_DUNG_LAI_CONG_THUC.md`.

Phát hiện một **lỗi hệ thống**: chuỗi ký vòng tròn — LLM soạn nháp không nguồn → sinh biến thể gia vị → ký biến thể → ký bản gốc *vì biến thể đã ký*. Bản gốc chưa từng được đọc.

Để lọt những món như **"Nộm tai lợn" không có tai lợn**, **"Chả quế" không có quế**, **"Nem rán" không có vỏ**. Lưới `_ly_do_chan` không bắt được vì chỉ kiểm tỷ lệ nguyên liệu chính và trần natri.

Đã khoá bằng `tests/test_r2_nguyen_lieu_dinh_danh.py` — điền lại `verified_by` mà công thức vẫn thiếu thì CI đỏ.

**Không chặn release:** 12 món này `verified_by` trống nên `load_vn_dishes()` không nạp, không lọt tới bệnh nhân (RULE-3). Chỉ mất đa dạng ở nhóm chả/giò/bánh mặn.

**Nút thắt để ký lại:** cần **số gram có nguồn**. Sách 555 trong repo là **ảnh scan, 0 ký tự text** — không trích được. Việc này cần người đọc bản in, không tự động hoá được.

---

## 8. Điều kiện hiệu lực

Biên bản này có hiệu lực với **nội dung dữ liệu tại thời điểm ký**. Cần làm trước khi coi là chốt:

- [x] ~~Đối chiếu 3 tệp tương tác với `HEAD`~~ — **đã làm, không mất việc** (§5)
- [ ] Commit toàn bộ thay đổi `data/seeds/` kèm biên bản này
- [ ] Đồng bộ Supabase (đã làm cho `dishes.verified_by`; các bảng khác cần R3 xác nhận)

Rule hoặc dữ liệu đổi giá trị sau ngày ký → **biên bản hết hiệu lực với phần đó**, phải ký lại. Sửa `guideline_ref`/ghi chú mà không đổi số thì không cần (`R2_AUDIT_EXCEPTION_BASED_CARE_RULES.md` §5.2).

---

**Ký ngày 2026-08-18 — R2**
