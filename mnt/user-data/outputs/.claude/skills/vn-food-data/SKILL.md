---
name: vn-food-data
description: Tra cứu, nhập, chuẩn hoá dữ liệu thực phẩm và món ăn Việt Nam vào cơ sở dữ liệu dinh dưỡng, kèm nguồn gốc bắt buộc. Dùng khi thêm dòng vào food_items hoặc dishes, khi xử lý tên món địa phương hoặc tên đồng nghĩa (OOV), khi phân rã một món ăn phức hợp như phở bò hay bún riêu thành nguyên liệu thô, hoặc khi cần ước tính dinh dưỡng cho món chưa có trong CSDL. Cũng dùng khi review PR chạm data/seeds.
---

# Dữ liệu thực phẩm & món ăn Việt Nam

## Nguyên tắc

- **Không dòng nào thiếu `source`.** CI sẽ đỏ.
- Thứ tự ưu tiên nguồn: `NIN` (Bảng thành phần thực phẩm Việt Nam) → `USDA` FoodData Central → `curated` (tự tổng hợp có ghi nguồn) → `estimated` (ước tính, phải kèm `confidence`).
- Dữ liệu thực phẩm truy vấn bằng **SQL**, không bao giờ đưa vào vector store.

## Schema `food_items`

```
id, name_vi, name_en, aliases[], unit_ref,
kcal_100g, protein_g, carb_g, fat_g, fiber_g,
na_mg, k_mg, p_mg, purine_mg, gi_index,
source, source_ref, is_estimated, confidence
```

`source_ref` phải đủ để người khác tra lại: tên tài liệu + trang, hoặc `USDA fdcId`.

## Quy trình thêm thực phẩm mới

1. Tra `aliases` trước — có thể đã tồn tại dưới tên khác
2. Tìm trong NIN → USDA → nếu không có, chuyển sang quy trình ước tính
3. Nhập vào `data/seeds/food_items.csv` kèm `source_ref`
4. Chạy `make validate-data`
5. PR → R2 review

### Kiểm tra khoảng hợp lý (chạy tự động, nhưng nên tự nhìn)

| Chất | Khoảng hợp lý /100g | Ghi chú |
|---|---|---|
| kcal | 0–900 | > 900 chỉ có ở dầu mỡ nguyên chất |
| Protein | 0–90 g | Bột đạm mới đạt mức cao |
| Natri | 0–20.000 mg | Nước mắm, bột canh rất mặn — trần cao là đúng |
| Kali | 0–4.000 mg | |
| GI | 0–110 | |

## Phân rã món ăn phức hợp

Món Việt hầu hết là món phức hợp. Quy trình:

1. LLM đề xuất danh sách nguyên liệu + gram cho 1 khẩu phần chuẩn
2. **Người rà soát và sửa** — không tin LLM về định lượng
3. Tra từng nguyên liệu bằng SQL
4. Cộng lại → so sánh với giá trị tham khảo đã biết
5. Lưu vào `dishes` + `dish_ingredients`, ghi `verified_by`

### Mốc kiểm chứng đã biết (dùng làm test hồi quy)

| Món | Giá trị tham chiếu | Nguồn |
|---|---|---|
| Phở bò (1 bát) | 3,3–4,0 g muối | Khảo sát tiêu thụ muối VN |
| Bún cá (1 bát) | ~6,2 g muối | như trên |
| Mì ăn liền (1 gói) | 4,2–5,0 g muối | như trên |

Nếu công thức nhập vào cho ra con số lệch xa các mốc này → công thức sai, không phải mốc sai.

**Nhớ:** 70–81% lượng muối của người Việt đến từ gia vị nêm nếm và nước chấm. Công thức món ăn **bắt buộc** phải kê riêng dòng nước mắm/bột canh/hạt nêm, và nước chấm ăn kèm phải là một `dish_ingredient` tách riêng để có thể khuyên bỏ.

## Xử lý OOV (món/nguyên liệu ngoài CSDL)

Thứ tự thử:
1. Tra bảng `aliases`
2. Tìm mờ theo tên (fuzzy)
3. Phân rã bằng LLM thành nguyên liệu → tra SQL từng nguyên liệu → cộng lại
4. Nếu vẫn không được → **nói không biết**, đừng gán bừa sang thực phẩm gần giống

Kết quả bước 3 luôn: `is_estimated=true`, có `confidence`, có `estimation_method`, và UI hiển thị nhãn "ước tính".

## Bảng đồng nghĩa vùng miền (mở rộng liên tục)

`dứa = thơm = khóm` · `lạc = đậu phộng` · `cá quả = cá lóc = cá chuối` · `mè = vừng` · `ngò = rau mùi` · `bắp = ngô` · `sắn = khoai mì` · `mướp đắng = khổ qua` · `heo = lợn` · `dứa dại ≠ dứa` (cẩn thận)

## Cảnh giác nguyên liệu ẩn (cho kiểm tra dị ứng)

nước mắm → cá · mắm tôm/mắm nêm → hải sản · chả/giò → thịt + bột · bánh phở → gạo · nước tương → đậu nành (thường cả lúa mì) · nem rán → trứng + thịt + bột

## Checklist

- [ ] Mọi dòng có `source` và `source_ref`
- [ ] Đã qua `make validate-data`
- [ ] Món phức hợp có kê riêng gia vị mặn và nước chấm
- [ ] Đã cập nhật `aliases` nếu tên có biến thể vùng miền
- [ ] Ước tính được gắn cờ đúng
- [ ] Tăng `data/VERSION` nếu thay đổi lớn
