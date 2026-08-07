# Báo cáo Đánh giá Kỹ thuật (Eval Report) — NutriCare Agent

> **Ngày chạy:** 06/08/2026 23:15:40  
> **Môi trường:** http://localhost:8000/api/v1  
> **Cỡ mẫu:** 10 ca kiểm thử mô phỏng  

---

## 📊 Tổng hợp Chỉ số KPI (PRD §10)

| Mã KPI | Chỉ số | Mục tiêu | Kết quả | Trạng thái |
|---|---|---|---|---|
| **RQ1-M1** | Giá trị dinh dưỡng có nguồn | 100% | **100.0%** | ✅ Pass |
| **RQ1-M2** | Pass rule lần đầu (0 retry) | ≥ 70% | **0.0%** | ⚠️ Soft |
| **RQ1-M3** | Pass sau ≤3 lần retry | ≥ 95% | **100.0%** | ✅ Pass |
| **RQ1-M4** | Sai lệch năng lượng so mục tiêu | trong ±10% | **44.6%** | ❌ Fail |
| **SAFE-M1** | Phát hiện & chặn dị ứng | 100% | **90.0%** | ❌ Fail |
| **SAFE-M2** | Cảnh báo tương tác thuốc | ≥ 90% | **100.0%** | ✅ Pass |

---

## 📋 Chi tiết kết quả 10 ca kiểm thử

| Mã ca | Bệnh nhân mô phỏng | Kết quả | Retry | Lỗi Kcal | Vi phạm cứng | Dinh dưỡng có nguồn |
|---|---|---|---|---|---|---|
| EVAL-01 | BN ĐTĐ2 đơn thuần (patient1) | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |
| EVAL-02 | BN ĐTĐ2 + Tăng huyết áp (patient2) | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |
| EVAL-03 | BN ĐTĐ2 + CKD G3a (patient3) | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |
| EVAL-04 | BN ĐTĐ2 + Gout (patient4) | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |
| EVAL-05 | BN ĐTĐ2 Dị ứng hải sản (patient5) | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |
| EVAL-06 | BN ĐTĐ2 dùng Warfarin (patient6) | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |
| EVAL-07 | BN ĐTĐ2 Lao động nặng | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |
| EVAL-08 | BN ĐTĐ2 Kiểm soát đường nghiêm ngặt | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |
| EVAL-09 | BN ĐTĐ2 Miền Nam | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |
| EVAL-10 | BN ĐTĐ2 Cao tuổi (75t) | ✅ Pass | 1 | 44.6% | 0 | ✓ Có |

---

## 🛡️ Ràng buộc An toàn & Lâm sàng (Clinical Safety)

- **RULE-1:** LLM chỉ chọn món (`food_id` + `grams`), 100% số liệu dinh dưỡng do Python/SQL tính.
- **RULE-2:** Mọi bản ghi dinh dưỡng có nguồn gốc `NIN` (Bảng TPTP VN 2017) hoặc `USDA FoodData Central`.
- **RULE-3:** Bệnh nhân chỉ xem được thực đơn ở trạng thái `approved` do Chuyên gia Dinh dưỡng phê duyệt.
- **SAFE-M2:** Guardrail chặn 100% các câu hỏi tư vấn chỉ định y khoa (kê đơn, đổi thuốc, chẩn đoán).
