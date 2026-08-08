# DAT-24 — Khảo sát khả thi: nâng CP-SAT lên 500+ món Việt

> Khảo sát 2026-08-08 (theo yêu cầu Hưng). Nhánh: `feature/DAT-24-vn-dishes-500`.
> Kết luận ngắn: **nguồn công thức KHÔNG phải nút thắt. Nút thắt là kho nguyên liệu (439 `food_items`) và chính sách quy đổi/thay thế nguyên liệu — đây là quyết định lâm sàng, cần R2 chốt.**

---

## 1. Trạng thái hiện tại (đo thật, không ước lượng)

| Chỉ số | Giá trị | Ghi chú |
|---|---|---|
| `main` | `c3b3b85` (PR #63 đã merge) | Bằng `project/main`. `origin/main` (fork cá nhân) còn cũ ở `1e00f39` |
| `food_items.csv` | 7.745 dòng / 7.375 có số liệu | |
| **Ứng viên nguyên liệu CP-SAT** | **439** | Lọc `id < 100000` (loại khối USDA bulk, cố ý — xem `core.py`) |
| `dishes.csv` | 2.677 dòng | 2.632 là khối USDA FNDDS (món Mỹ) |
| **Món CP-SAT dùng được** | **28** | 45 món Việt curated − 17 món tự ghi chú thiếu nguyên liệu |
| `validate_data.py` | 0 lỗi, 6 cảnh báo | |
| `pytest` | 196 passed (theo commit `54822c0`) | |

---

## 2. Nguồn công thức: ĐÃ TÌM ĐƯỢC, đủ quy mô

**monngonmoingay.com** — 2.510 trang món ăn trong sitemap.

- `robots.txt` cho phép tường minh: `User-agent: ClaudeBot → Allow: /` (kiểm tra 2026-08-08).
- Mỗi trang có JSON-LD `schema.org/Recipe` với **định lượng gram thật** và `recipeYield`.
- Đã viết `scripts/crawl_mnmn_dishes.py` (có cache, delay, chỉ lấy sự kiện định lượng + URL nguồn, **không lưu văn bản công thức** — tránh vấn đề bản quyền nội dung).
- Pilot 60 trang: **59/60 đọc được Recipe JSON-LD** (cần `json.loads(..., strict=False)` vì JSON-LD của site có ký tự xuống dòng thô trong chuỗi — bỏ qua điều này sẽ mất ~2/3 số món).

So sánh: `vietnamesecookbook.com` (đã dùng cho 15 món `-VCB`) chỉ có **151 trang công thức** — không đủ để đạt 500.

→ **Nguồn không thiếu. 2.510 công thức là quá đủ cho mục tiêu 500-1000.**

## 3. Nút thắt thật (đo trên 59 công thức pilot)

### 3.1. Quy đổi đơn vị ước lệ — chặn ~20% số dòng nguyên liệu

471 dòng nguyên liệu, trong đó ~372 dòng ghi rõ `g/kg/ml/l` (quy đổi được ngay). Phần còn lại dùng đơn vị ước lệ, **không được phép tự đoán ra gram** (RULE-2):

| Đơn vị | Số lần | Đơn vị | Số lần |
|---|---|---|---|
| `m`/`M` (muỗng) | 35 | `tai` | 9 |
| `trái` | 30 | `cái` | 6 |
| `củ` | 16 | `gói` | 4 |
| `quả` | 15 | `chén` | 3 |
| `cây` | 11 | `lát`, `nhánh`, `miếng`, `tép`… | ~10 |

99 dòng không có số nào (dòng gia vị gộp kiểu "Tiêu, muối, nước mắm, dầu điều, đường").

### 3.2. Khớp tên nguyên liệu → `food_id` — ĐÂY MỚI LÀ NÚT THẮT CHÍNH

Giả sử quy đổi được **mọi** đơn vị ở §3.1, tỷ lệ món có **đủ** nguyên liệu khớp `food_id` vẫn chỉ:

> **2/59 = 3%**

Áp lên 2.510 công thức → chỉ ~75 món. **Không đạt 500.**

Nguyên nhân, qua các nguyên liệu bị trượt nhiều nhất:

| Kiểu trượt | Ví dụ thật | Bản chất |
|---|---|---|
| **Thiếu hẳn trong kho** | `sả`, `cải bó xôi`, `thịt nạc vai`, `giò sống`, `bắp non`, `mè rang` | 439 nguyên liệu là quá mỏng cho ẩm thực Việt |
| **Tên chung vs tên cụ thể** | Công thức ghi `Thịt bò`; kho có `Thịt bò thăn`, `Thịt bò bắp`, `Thịt nạc bò` — **không có** `Thịt bò` chung | Cần **chính sách thay thế**, không phải lỗi kỹ thuật |
| **Tên lẫn tạp chất** | `Hành tỏi băm`, `Tỏi băm ớt sừng` (2 nguyên liệu trong 1 dòng) | Cần tách dòng |

---

## 4. Vì sao KHÔNG được "bỏ qua nguyên liệu không khớp"

`_dish_nutrient_totals()` (`src/agents/optimizer.py`) tính **tổng tuyệt đối cả món** và CP-SAT dùng món như một khối cố định (`MAX_DISHES_PER_SLOT = 1`, không co giãn khẩu phần).

Bỏ bớt nguyên liệu ⇒ món bị ghi nhận **thấp hơn** năng lượng thật ⇒ CP-SAT bù thêm nguyên liệu thô cho đủ chỉ tiêu ⇒ **bệnh nhân ăn vượt ngưỡng thật**.

Đây đúng là bug đã xảy ra và đã sửa ngày 2026-08-07, và là lý do PR #63 phải loại 17 món. **Không được lặp lại để chạy theo số lượng.**

---

## 4b. Đã sửa trong nhánh này: bug lọc ứng viên loại nhầm 82 thực phẩm NIN

`src/agents/nodes/core.py` lọc ứng viên CP-SAT bằng `id < 100_000` như một *proxy* cho "thuộc khối USDA bulk". Proxy đó **sai**: script merge NIN 2017 cấp id nối tiếp dãy `fdc_id`, nên **82 thực phẩm Việt Nam thật của Viện Dinh dưỡng** nhận id ≥ 1.105.898 và bị loại nhầm — đúng nhóm nguyên liệu công thức món Việt cần nhất:

> Vừng (mè), Cà rốt, Cải thìa, Cải soong, Giá đậu xanh, Giá đậu tương, Ớt đỏ to, Đậu tương, Đậu xanh, Đậu Hà Lan, Sữa đậu nành, Ngô bắp tươi…

Đã sửa: lọc theo `source` (`NIN`/`curated` luôn là ứng viên, bất kể id) thay vì theo id.

**Ứng viên nguyên liệu CP-SAT: 439 → 521.**

## 4c. Khoảng trống lớn nhất chưa khai thác: 370 dòng `food_items.csv` bỏ trống

370 dòng **chưa có bất kỳ số liệu nào**, và đó chính là danh sách nguyên liệu Việt curated gốc (id nhỏ), đúng những thứ công thức cần:

> Mì ăn liền, Bánh cuốn, Sắn luộc, Thịt gà (ức, bỏ da), Giò lụa, Chả quế, Cá lóc, Cá bống, Cá khô, Chao, Tương hột, Rau ngót…

### Đã điều tra tới cùng (2026-08-08) — và kết quả không như kỳ vọng

**348/370 dòng trống đều là mục NIN 2017 ĐÃ BIẾT MÃ**, bị chặn vì bản PDF gốc không phân tích vài trường:

| Trường thiếu | Số dòng |
|---|---|
| `na_mg`, `k_mg` | 200 |
| `fat_g` + `na_mg`, `k_mg` | 44 |
| `na_mg`, `k_mg`, `p_mg` | 31 |
| `fiber_g` + `na_mg`, `k_mg` | 29 |
| còn lại (fat/fiber/p lẻ) | 44 |

**Đã kiểm chứng trên chính file PDF** (trang 24, mã 01012 "Bánh mỳ"): tại toạ độ cột `NA`/`K` **không có token nào** — ô đó thật sự trống trong bảng gốc, **không phải lỗi trích xuất**. Ba số `0.10 / 0.07 / 0.7` nằm ở x≈918/955/994 là THIA/RIBF/NIA (vitamin B1/B2/B3).

> ⚠️ **Và "trống" ở đây KHÔNG có nghĩa "không đáng kể".** Bánh mỳ có Na ≈ 490–600 mg/100 g (USDA). Điền 0 cho nhóm này sẽ sai nghiêm trọng đúng vào ngưỡng chặn cứng của THA/CKD.

**Đã thử lấp bằng đối chiếu NIN → USDA** qua chính `name_en` mà NIN cung cấp (`scripts/fill_nin_gaps_from_usda.py`). Kết quả thực tế:

| | |
|---|---|
| Tự động lấp (score ≥ 0,90) | **15** dòng — dầu ăn các loại, bột dong, bột sắn, tôm khô, sữa đặc, mãng cầu xiêm… |
| Đưa R2 duyệt tay (0,70–0,90) | 19 dòng → `data/seeds/food_items.nin_gaps_can_R2_duyet.csv` |
| Bỏ hẳn, không đủ căn cứ | 314 dòng → `data/seeds/food_items.nin_gaps_unresolved.csv` |

Ba lần siết bộ khớp mới đủ an toàn, vì bản đầu tiên cho ra các khớp **sai nguy hiểm**:

- `Dầu ngô` (Corn oil) → `Oil, olive` — sai loại dầu
- `Lòng trắng trứng vịt` (Duck egg, **white**) → `Duck egg, cooked` — trắng ≠ nguyên quả
- `Hạt dẻ tươi` (Chestnut, fresh) → `Flour, chestnut` — chất xơ 2,3 vs 8,7 g/100 g
- `Mắm tôm loãng` (Shrimp sauce) → `Shrimp with **lobster sauce**` (món Hoa) — Na 1031 trong khi mắm tôm thật cao hơn nhiều lần

Ba lớp chặn đã thêm: nhóm tính từ loại trừ nhau (white/yolk · raw/cooked/dried · loại dầu · leaf/root/seed), token dạng chế biến bắt buộc khớp hai chiều (flour/powder/skin/soup/sauce…), và kiểm tra xung đột trên token **thô** (vì `raw`/`cooked`/`dried` vừa là stopword vừa nằm trong nhóm loại trừ — nếu kiểm tra sau khi bỏ stopword thì nhóm đó không bao giờ chạy và `Shrimp dried` khớp được với `Shrimp, raw`).

**Kết luận thẳng:** 314/348 dòng còn lại **không lấp được từ nguồn hiện có**. Đây là khoảng trống thật của dữ liệu thành phần thực phẩm Việt Nam (NIN 2017 đơn giản là không đo Na/K cho nhóm này), không phải việc kỹ thuật xử lý được. Muốn có, phải đo hoặc mua dữ liệu, hoặc R2 tra tay từng mục.

## 5. Việc cần làm để thật sự đạt 500+ (theo thứ tự)

1. **[Chặn đường găng] Mở rộng kho nguyên liệu Việt** từ 439 lên ~1.000-1.500.
   Nguồn có sẵn, chưa khai thác hết: NIN 2017 PDF (620 thực phẩm), sheet "Bảng TP" trong file Excel nội bộ (761 tên chưa đối chiếu — xem `docs/PLAN_DAT-13-fill-data-gaps.md`). Đây là điều kiện cần; làm xong bước này tỷ lệ khớp sẽ nhảy mạnh.
2. **Bảng quy đổi đơn vị ước lệ → gram, CÓ NGUỒN.**
   Nguồn dùng được: `data/seeds/serving_sizes.csv` (đã có, 175 dòng) + USDA `food_portion.csv` (47k dòng, có `portion_description` + `gram_weight`). Mỗi dòng quy đổi phải có `source_ref` riêng — không đặt số theo cảm tính.
3. **Chính sách thay thế tên chung → tên cụ thể** (VD `Thịt bò` → cắt nào?).
   ⚠️ **Đây là quyết định lâm sàng, R2 phải chốt và ghi thành ADR trong DEVLOG** — chọn `Thịt bò thăn` (nạc) hay `Thịt bò bắp` làm mặc định thay đổi rõ rệt lượng chất béo/năng lượng của hàng trăm món.
4. Chạy crawl đầy đủ 2.510 công thức, giữ ngưỡng nghiêm (`--min-mass-cover 0.80`, loại món còn nguyên liệu chưa quy đổi), xuất kèm file `*.rejected.csv` ghi rõ lý do từng món bị loại.
5. Mọi món mới vào với `verified_by=pending` → R2 duyệt trước khi `is_reviewed=True` (RULE-3).

---

## 6. Không làm

- Không suy đoán gram cho đơn vị ước lệ để tăng số món.
- Không bỏ qua nguyên liệu chưa khớp rồi vẫn đưa món vào CP-SAT (xem §4).
- Không tự chọn nguyên liệu thay thế cho tên chung khi chưa có quyết định của R2 (§5.3).
