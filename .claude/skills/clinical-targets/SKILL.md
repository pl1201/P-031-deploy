---
name: clinical-targets
description: Tính hoặc kiểm tra định mức dinh dưỡng lâm sàng (BMR, TDEE, kcal, protein, natri, kali, phospho, purine, chất xơ) cho bệnh nhân mãn tính Việt Nam. Dùng khi làm việc với src/clinical/, khi thêm hoặc sửa clinical_rules, khi cần xác minh một ngưỡng cho ĐTĐ týp 2, tăng huyết áp, bệnh thận mạn CKD, gout, hoặc khi xử lý bệnh nhân đa bệnh lý. Cũng dùng khi review PR chạm tới bất kỳ con số ngưỡng nào.
---

# Tính định mức dinh dưỡng lâm sàng

## Nguyên tắc trước khi làm bất cứ điều gì

1. **Ngưỡng không bao giờ hardcode trong code hay prompt.** Nguồn duy nhất là bảng `clinical_rules` trong DB (seed từ `data/seeds/clinical_rules.csv`).
2. **Module này không được import LLM client.** Toàn bộ là Python thuần + SQL.
3. Mỗi ngưỡng phải có `guideline_ref`. Không có nguồn thì không thêm.

## Quy trình

### Bước 1 — Tính năng lượng cơ bản

Mifflin-St Jeor:
```
Nam:  BMR = 10×W + 6.25×H − 5×A + 5
Nữ:   BMR = 10×W + 6.25×H − 5×A − 161
```
W = kg, H = cm, A = tuổi.

Nếu BMI > 30 → dùng cân nặng điều chỉnh: `W_adj = IBW + 0.25 × (W − IBW)`, với IBW theo Devine hoặc BMI 22 × (H/100)².

TDEE = BMR × hệ số hoạt động (nằm 1.2 · nhẹ 1.375 · vừa 1.55 · nặng 1.725).
Mục tiêu cân nặng: giảm −500 kcal/ngày (không dưới 1200 nữ / 1500 nam), tăng +300–500.

**Kiểm tra chéo:** kết quả nên nằm trong 30–35 kcal/kg/ngày cho bệnh nhân mãn tính ổn định. Lệch nhiều → xem lại đầu vào.

### Bước 2 — Nạp rule theo bệnh lý

Query `clinical_rules` theo `condition_code` + `stage`. Mỗi rule cho biết: chất nào, toán tử, ngưỡng, đơn vị, tính theo ngày hay theo kg cân nặng, mức `hard` hay `soft`.

### Bước 3 — Xử lý đa bệnh lý (quan trọng nhất)

Khi nhiều rule cùng tác động lên một chất:
- Giới hạn **trên** → lấy `min(threshold)` (chặt hơn)
- Giới hạn **dưới** → lấy `max(threshold)`
- Xung đột cứng không giải được (VD: protein tối thiểu của một bệnh cao hơn tối đa của bệnh khác) → **không tự chọn**, gắn cờ `needs_expert_review` và chuyển cho chuyên gia.

Ví dụ ĐTĐ2 + CKD G4:
- Protein: theo CKD (0,6–0,8 g/kg) — chặt hơn
- Carbohydrate %: theo ĐTĐ
- Natri: cả hai đều < 2000 mg → lấy 2000
- Kali, Phospho: theo CKD

### Bước 4 — Trả kết quả kèm giải trình

Output luôn gồm `targets` + `applied_rule_ids` + `guideline_refs`, để UI hiển thị được "vì sao ra con số này".

## Bảng tham chiếu nhanh (xác nhận lại với `clinical_rules` trước khi dùng)

| Bệnh lý | Chất | Ngưỡng | Nguồn |
|---|---|---|---|
| ĐTĐ týp 2 | Carb | 45–55% năng lượng, GI thấp/TB | ADA/EASD |
| ĐTĐ týp 2 | Chất xơ | ≥ 14 g/1000 kcal | ADA |
| THA / tim mạch | Natri | < 2000 mg/ngày | WHO/AHA |
| THA / tim mạch | Béo bão hoà | < 7% năng lượng | AHA |
| CKD G3–G5 chưa lọc | Protein | 0,6–0,8 g/kg/ngày | KDIGO/KDOQI |
| CKD | Kali, Phospho | theo giai đoạn | KDIGO |
| Gout | Purine | < 150 mg/ngày | ACR |
| Chung | Năng lượng | 30–35 kcal/kg/ngày | BYT / Viện Dinh dưỡng |

## Checklist trước khi kết thúc

- [ ] Không hardcode ngưỡng nào
- [ ] Có unit test cho: 1 bệnh đơn lẻ, 1 ca đa bệnh lý, 2 case biên (tuổi/BMI cực trị)
- [ ] Output có `applied_rule_ids`
- [ ] Docstring ghi công thức + nguồn
- [ ] Không import LLM
- [ ] R2 đã review nếu có thay đổi ngưỡng

## Khi không chắc

Không tự đặt số. Hỏi R2 (Clinical & Data Engineer). Ngưỡng sai trong hệ thống dinh dưỡng lâm sàng gây hại thật, không phải là bug thẩm mỹ.
