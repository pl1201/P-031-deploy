# DAT-28 — Lỗ hổng dữ liệu `sugar_g` trong `food_items`

**Người nhận:** R2 (Clinical & Data Engineer + Eval)
**Người báo cáo:** phát hiện khi điều tra lỗi sinh thực đơn thất bại hàng loạt, 2026-08-18
**Mức độ:** P1 — đang được vá tạm bằng code (đã merge), nhưng gốc rễ vẫn là thiếu dữ liệu
**Liên quan:** `src/agents/optimizer.py`, `data/seeds/*.csv`, rule `T2DM-SUG-01`

---

## 1. Tóm tắt 1 dòng

`sugar_g` chỉ có ở **0.7% dòng** trong `food_items` (53/7.418), khiến CP-SAT gần như luôn vô nghiệm cho bệnh nhân ĐTĐ2 và đẩy hệ thống sang fallback LLM tốn kém/không ổn định. Đã vá phần **logic** (code), nhưng phần **dữ liệu** vẫn cần R2 xử lý.

## 2. Bối cảnh phát hiện

Điều tra 43 bản ghi `meal_plans.status='failed'` (đúng con số ghi trong comment cũ ở `meal_plans.py`), tái hiện bằng 1 bệnh nhân ĐTĐ2 thật trên DB dev (Supabase), lỗi:

```
ValueError: Generator did not select any database dish; refusing ingredient-only patient draft
```

Trạng thái `meal_plans` tại thời điểm điều tra:

| status | count |
|---|---|
| rejected | 72 |
| **failed** | **43** |
| approved | 4 |

## 3. Chuỗi nhân quả

1. `food_items.sugar_g` chỉ có dữ liệu ở **53/7.418 dòng (0.7%)**; `purine_mg` tương tự (50/7.418).
2. Rule `T2DM-SUG-01` (giới hạn đường tự do ≤ ~70g/ngày) áp cho **mọi bệnh nhân ĐTĐ2** → ràng buộc `sugar_g` gần như luôn "active" trong CP-SAT.
3. Theo đúng RULE-2 (CLAUDE.md), CP-SAT không được coi thiếu dữ liệu = 0 → loại **cả món** nếu bất kỳ nguyên liệu nào thiếu `sugar_g`. Với dữ liệu thưa như vậy, phần lớn món bị loại khỏi ứng viên.
4. **Điểm nghẽn nghiêm trọng nhất:** `Cơm tẻ` (food_id=2, nguồn `estimated`) là ứng viên **rice-food DUY NHẤT** trong toàn catalog để tạo bữa trưa/tối theo khuôn mẫu Việt Nam — và nó **không có `sugar_g`**. Hễ ràng buộc `sugar_g` còn hiệu lực, "vai trò phải có cơm" luôn thất bại, bất kể catalog còn bao nhiêu món khác đủ dữ liệu.
5. Cơ chế "degrade" (bỏ ràng buộc khi dữ liệu quá thưa) trong `optimizer.py` trước đây chỉ đếm **tổng số món có dữ liệu trên toàn catalog** (ngưỡng `< 4`) — không phát hiện được kiểu nghẽn 1-điểm này vì tổng vẫn ≥ 4 (dù phân bổ lệch hẳn, 0 món cho bữa sáng/bữa phụ).
6. CP-SAT vô nghiệm → chuyển sang Gemini → Gemini cũng bị ràng buộc tương tự ở bước validate, dùng hết 3 lượt retry mà không đạt → `status=failed`.

## 4. Đã vá (không cần R2 làm gì thêm ở phần này)

`src/agents/optimizer.py` — hàm `_optional_field_supports_blueprint` mới: thay đếm tổng bằng kiểm tra **từng vai trò bắt buộc riêng** (bữa sáng / cơm / đạm / rau-canh / bữa phụ). Chỉ giữ ràng buộc `sugar_g`/`purine_mg` nếu MỌI vai trò vẫn có ≥1 ứng viên đủ dữ liệu; nếu không, bỏ ràng buộc và để `validate` gắn cờ soft "thiếu dữ liệu đường" thay vì làm sập cả model.

**Đã kiểm chứng:**
- 489 test hiện có pass, `ruff`/`mypy` sạch.
- Chạy lại đúng bệnh nhân đã fail qua API thật: `status=pending_review`, 2849 kcal (đúng khoảng mục tiêu 2508–3066), đủ 4 bữa món Việt thật (bún chả, cơm, thịt bò xào ớt chuông, rau luộc, trái cây), chỉ còn 1 vi phạm **soft** (`sugar_g` thiếu dữ liệu — không chặn duyệt).

Bản vá này chỉ ngăn dữ liệu thưa **làm sập cả hệ thống**. Nó không làm dữ liệu `sugar_g` đầy đủ hơn — các thực đơn vẫn sẽ mang cờ "thiếu dữ liệu đường, không kết luận được có đạt ngưỡng hay không" cho tới khi dữ liệu được bổ sung.

## 5. Việc cần R2: backfill `sugar_g` (và `purine_mg`) có ưu tiên

Không cần bổ sung toàn bộ 7.418 dòng — chỉ **1.619 food_id thực sự được dùng làm nguyên liệu món ăn** (`dish_ingredients`), trong đó **1.577 dòng (97.4%) đang thiếu `sugar_g`**.

### 5.1. Ưu tiên cao nhất — nghịch lý dữ liệu cần sửa trước

| id | Tên | Nguồn | Vấn đề |
|---|---|---|---|
| 149 | Đường trắng | USDA | **Bản thân "đường" lại thiếu `sugar_g`** — sai logic rõ ràng, sửa trước tiên |
| 169655 | Sugars, granulated | USDA | Tương tự — nguyên liệu "đường hạt" không có giá trị đường |
| **2** | **Cơm tẻ** | estimated | **Điểm nghẽn tuyệt đối** đã nêu ở mục 3.4 — ứng viên cơm duy nhất, ưu tiên tuyệt đối dù chỉ 1 dòng |

### 5.2. Top 30 nguyên liệu theo mức ảnh hưởng (số món dùng nó, mất `sugar_g`)

Sắp theo `count(distinct dish_id)` — sửa các dòng đầu bảng lợi nhiều nhất vì 1 dòng dữ liệu gỡ ràng buộc cho hàng trăm món cùng lúc:

| id | Tên | Nguồn | Số món dùng |
|---|---|---|---|
| 173468 | Salt, table | USDA | 577 |
| 169655 | Sugars, granulated | USDA | 189 |
| 173647 | Beverages, water, tap, drinking | USDA | 122 |
| 137 | Nước mắm | NIN | 119 |
| 175103 | Beverages, water, tap, municipal | USDA | 89 |
| 170000 | Onions, raw | USDA | 63 |
| 169988 | Celery, raw | USDA | 61 |
| 19 | Thịt lợn nạc | NIN | 53 |
| 174815 | Alcoholic beverage, distilled (gin, rum, vodka, whiskey) 80 proof | USDA | 52 |
| 174924 | Bread, white, commercially prepared | USDA | 51 |
| 171287 | Egg, whole, raw, fresh | USDA | 43 |
| 149 | Đường trắng | USDA | 41 |
| 171009 | Salad dressing, mayonnaise, regular | USDA | 40 |
| 172237 | Vinegar, distilled | USDA | 40 |
| 168561 | Pickle relish, sweet | USDA | 38 |
| 79 | Hành lá | USDA | 37 |
| 173410 | Butter, salted | USDA | 35 |
| 172253 | Babyfood, water, bottled, GERBER | USDA | 33 |
| 171269 | Milk, nonfat, fluid, + vit A/D | USDA | 32 |
| 171267 | Milk, reduced fat 2%, + vit A/D | USDA | 31 |
| 4 | Bún tươi | estimated | 30 |
| 173424 | Egg, whole, cooked, hard-boiled | USDA | 28 |
| 172796 | Rolls, hamburger/hotdog, plain | USDA | 28 |
| 167747 | Lemon juice, raw | USDA | 27 |
| 170440 | Potatoes, boiled, no skin, no salt | USDA | 26 |
| 170859 | Cream, fluid, heavy whipping | USDA | 26 |
| 173414 | Cheese, cheddar | USDA | 26 |
| 171891 | Coffee, brewed, espresso | USDA | 24 |
| 174125 | Coffee, brewed, espresso, decaf | USDA | 24 |
| 168894 | Wheat flour, white, all-purpose, enriched | USDA | 23 |

Nhận xét nhanh (không phải kết luận thay R2, chỉ để tham khảo tốc độ xử lý): nhóm đầu bảng (muối, nước, nước mắm, hành, rượu mạnh, dấm) hợp lý là `sugar_g = 0` theo bảng thành phần chuẩn (USDA/NIN gốc) — có thể là lỗi **import/mapping** thiếu cột chứ không phải thật sự "chưa tra được", đáng kiểm tra script import trước khi tra cứu thủ công lại từ đầu.

### 5.3. Gợi ý acceptance criteria nếu mở ticket

- [ ] Toàn bộ ≥ 30 dòng ở mục 5.2 có `sugar_g` với `source`/`source_ref` hợp lệ (RULE-2)
- [ ] Riêng `id=2` (Cơm tẻ) và `id=149`/`169655` (đường) xử lý trước tiên, độc lập với phần còn lại
- [ ] Kiểm tra lại script import USDA/NIN — xác nhận `sugar_g=NULL` ở nhóm muối/nước/gia vị là "đúng 0 nhưng bị bỏ sót khi import" hay "nguồn gốc không có cột này"
- [ ] Sau backfill, chạy lại `pytest tests/test_cpsat_optimizer.py -k sugar` và kiểm tra tỉ lệ `meal_plans.status='failed'` giảm trên môi trường staging

## 6. Cách tái hiện / kiểm chứng độc lập

```sql
-- Độ phủ sugar_g toàn bảng
select count(*) filter (where sugar_g is not null) * 100.0 / count(*) as pct_covered
from food_items;

-- Nguyên liệu món ăn thực sự đang thiếu sugar_g, sắp theo mức ảnh hưởng
select fi.id, fi.name_vi, fi.source, count(distinct di.dish_id) as dish_count
from dish_ingredients di
join food_items fi on fi.id = di.food_id
where fi.sugar_g is null
group by fi.id, fi.name_vi, fi.source
order by dish_count desc;
```
