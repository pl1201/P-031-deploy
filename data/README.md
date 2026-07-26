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

Sau khi nhập xong, đổi tên `food_items.template.csv` → `food_items.csv`.

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
