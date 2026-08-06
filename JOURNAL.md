# JOURNAL — Nhật ký phát triển theo tuần

> ⚙️ File này được sinh tự động từ `DEVLOG.md` bằng `scripts/sync_devlog.py`.
> Đừng sửa trực tiếp — hãy sửa `DEVLOG.md` rồi chạy lại script.

> Cập nhật lần cuối: 06/08/2026 15:00

---

## Tổng kết theo tuần

### Tuần 1 (27/07 – 02/08) — Nền móng & Dữ liệu
- **Mục tiêu:** Repo + CI + Live URL hello-world + 150 thực phẩm + DEVLOG chạy
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:** ticket đóng __/10 · commit __ · test __ · coverage __%
- **Bài học:**
- **Điều chỉnh cho tuần sau:**

### Tuần 2 (03/08 – 09/08) — Clinical Engine
- **Mục tiêu:** API định mức đúng cho 4 bệnh lý + auth 2 role + schema DB
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 3 (10/08 – 16/08) — Agent & Guardrails
- **Mục tiêu:** Sinh thực đơn pass validator ≥70% lần đầu + chặn chỉ định y khoa ≥95%
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 4 (17/08 – 23/08) — HITL & Nhật ký
- **Mục tiêu:** Demo end-to-end 2 tài khoản trên Live URL
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 5 (24/08 – 30/08) — Nâng cao
- **Mục tiêu:** Mâm cơm gia đình + tương tác thuốc + thực đơn 7 ngày
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 6 (31/08 – 06/09) — Đóng gói
- **Mục tiêu:** Eval report + video + pitch + 10/10 deliverables
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

---

---

## Quyết định kỹ thuật

| ID | Ngày | Quyết định | Người quyết | Chi tiết |
|---|---|---|---|---|
| DEC-001 | 2026-07-26 | Cắt scope: bỏ vision/OCR, Neo4j, K8s, DDID full, benchmark MedQA | Cả đội | Xem `docs/00_ASSESSMENT.md` §9 |
| DEC-002 | 2026-07-26 | Postgres + pgvector, không dùng vector DB riêng | R1 | ADR-001 |
| DEC-003 | 2026-07-26 | LLM chỉ trả `food_id` + gram; số liệu tính bằng SQL | R1 | ADR-002 — nguyên tắc bất biến |
| DEC-004 | 2026-07-26 | Drug–food: curate 80 cặp thay vì import DDID | R2 | ADR-005 |
| DEC-005 | 2026-07-26 | Deploy Render + Vercel + Neon | R3 | ADR-006 |
| DEC-006 | 2026-07-26 | Đội 4 người: gộp DevOps vào R3, Eval vào R2, Deliverables vào R4, PM vào R1 | Cả đội | Xem `TEAM.md` §1 |
| DEC-007 | 2026-07-26 | Thêm cơ chế `overridden_by` cho clinical_rules | R2 | Bối cảnh: ADA (protein 15-20%E) xung đột KDIGO (0.6-0.8 g/kg) ở bệnh nhân ĐTĐ+CKD. Phương án: (A) để cơ chế conflict đẩy sang chuyên gia, (B) rule precedence. Chọn B vì ĐTĐ+CKD quá phổ biến, phương án A làm hỏng trải nghiệm. Hệ quả: giữ nguyên cơ chế conflict làm lưới an toàn cho trường hợp chưa lường trước |
| DEC-008 | 2026-07-26 | Không điền sẵn số liệu dinh dưỡng vào seed, để trống chờ tra nguồn thật | R2 | Bối cảnh: có thể sinh nhanh 152×10 con số trông hợp lý. Quyết định không làm, vì dữ liệu không truy vết được sẽ qua được cả validator lẫn mắt chuyên gia nhưng vẫn sai định mức bệnh nhân. Hệ quả: `validate_data.py` chặn merge nếu thiếu `source_ref` |
| DEC-009 | 2026-08-01 | Chọn ĐTĐ2 làm bệnh chính (anchor tim-chuyển hoá), THA + CKD sớm là comorbidity modifier | R2 | Bối cảnh: cần 1 bệnh chính cho MVP dinh dưỡng dù bệnh nhân đa bệnh. Phương án: A) làm cả 4 bệnh song song, B) anchor 1 bệnh. Chọn B/ĐTĐ2 vì: luật dinh dưỡng ĐTĐ2 tính được bằng SQL hợp RULE-1 nhất, ĐTĐ2 là hub kéo theo THA/CKD, dataset & guideline phong phú nhất, và purine (cột khó nguồn nhất) không cần cho anchor. Hệ quả: DAT-07 mở rộng schema cho đường tự do + GI |
| DEC-010 | 2026-08-01 | GI có nguồn riêng (`gi_source`/`gi_source_ref`), tách khỏi `source_ref` của NIN | R2 | Bối cảnh: GI đến từ Atkinson 2021 / Mai 2001, khác nguồn kcal (NIN). Dùng chung 1 source_ref là vi phạm tinh thần RULE-2. Hệ quả: model + validate_data chặn `gi_index` không có nguồn GI; `glycemic_load` None-safe để menu engine suy giảm mềm khi thiếu GI |
| DEC-011 | 2026-07-27 | Dockerfile cài dependency system-wide thay vì `pip install --user` | R3 (SET-04) | Bối cảnh: image 2-stage copy `/root/.local` từ builder sang runtime rồi chạy bằng `appuser` không phải root; `/root` có mode 0700 nên `appuser` không traverse được dù đã `chown -R` các file bên trong → container luôn crash `Permission denied` khi khởi động, kể cả khi build thành công. Phương án cân nhắc: (A) `chmod o+x /root` — mở quyền lên thư mục home của root, chấp nhận được vì rỗng nhưng vẫn xấu; (B) cài system-wide (bỏ `--user`), copy `/usr/local/lib/python3.11/site-packages` + `/usr/local/bin`. Chọn B vì không cần nới quyền `/root`. Hệ quả: `docker build` xanh không đủ để coi là "deploy được" — phải thực sự chạy container và gọi healthcheck (đã làm khi verify SET-04). *(đổi số từ DEC-009 khi merge develop→main để tránh trùng)* |
| DEC-013 | 2026-08-03 | Không dùng số per-món của API NIN cho dishes; phân rã nguyên liệu (DAT-04 gốc) | R2 | Bối cảnh: API món ăn NIN có kcal/muối per-100g dao động phi lý (phở 276–826 kcal/100g, muối 0,01–6,7 g/100g). Phương án: A) seed dishes.csv từ NIN, B) phân rã món → nguyên liệu → tính SQL từ food_items. Chọn B vì số món NIN không đáng tin cho ngưỡng lâm sàng; food_items có nguồn NIN/USDA truy được. Hệ quả: test hồi quy muối (phở 3,3–4,0g/bát) tính từ nguyên liệu + khẩu phần (serving_sizes.csv) |
| DEC-012 | 2026-08-02 | `purine_mg` thành optional (None) trong FoodItem/NutritionSummary | R2 | Bối cảnh: điền food_items từ NIN nhưng NIN (và USDA) KHÔNG có purine; purine chỉ cần cho gout. Phương án: A) tìm nguồn purine riêng cho cả 152 món rồi mới điền, B) purine optional + None-aware giống sugar/gi. Chọn B: gỡ được đường găng DAT-02 ngay, purine bổ sung sau từ nguồn riêng (bảng purine Nhật). Hệ quả: compute_nutrition cộng purine None-aware + cờ `purine_is_complete`; validator sinh cảnh báo `incomplete_data` cho ca gout khi thiếu → an toàn không bị đánh lừa bởi tổng thiếu hụt |
| DEC-014 | 2026-08-05 | Giữ nguyên `compute_targets()`/DEC-007 (chỉ gắn `needs_expert_review` khi rule xung đột) dù PRD v2.1 §2.2 đọc thoáng qua có vẻ yêu cầu gắn cờ cho MỌI ca đồng mắc ngoài ĐTĐ2 | Hưng (xác nhận) | Bối cảnh: PRD v2.1 (Phương) thu hẹp trọng tâm MVP về ĐTĐ2, §2.2 dễ đọc thành "mọi bệnh đồng mắc → bắt buộc chuyên gia duyệt", ngược DEC-007. Phương án cân nhắc: A) sửa code theo nghĩa đen PRD mới; B) chỉ flag khi thật sự không xác định được ngưỡng an toàn (giữ DEC-007); C) hỏi R2 trước. Đã research `KeHoachDuAn_VNutriCare_VMEC10_v3.docx` (nguồn yêu cầu chính của chính PRD.md) mục 6.4.1 "Bốn tình huống kiểm chứng" — đặc tả gốc khớp chính xác hành vi hiện tại, kể cả ca ĐTĐ2+CKD chỉ chuyển chuyên gia khi dải ngưỡng hẹp bằng 0. `docs/NGHIEN_CUU_DAI_THAO_DUONG_2026.md` xác nhận cơ chế này là điểm khác biệt cạnh tranh. Chọn B. Hệ quả: không đổi code/test; sửa lại các note đã lỡ ghi "cần sửa code" trong `CLAUDE.md`/`TICKETS.md`/`docs/rules/10-clinical-safety.md` cho khớp kết luận |
| DEC-015 | 2026-08-05 | Chỉ nhận Open Food Facts + Dược thư QGVN trong số 8 nguồn nghiên cứu bổ sung; loại PhyFoodComp/eBASIS/ASEANFOODS/WikiFCD-FoodOn | R2 (Claude) | Bối cảnh: tài liệu tổng quan `data/Dữ liệu dinh dưỡng Việt Nam.md` đề xuất 8 nguồn ngoài NIN/USDA. Phương án cân nhắc: chấp nhận cả 8 theo tài liệu, hoặc tự xác minh từng nguồn trước khi quyết. Chọn tự xác minh (WebSearch/WebFetch) vì tài liệu chỉ là gợi ý, không phải nguồn đã kiểm chứng. Hệ quả: PhyFoodComp bị loại vì ngoài phạm vi 4 bệnh mục tiêu (phytate phục vụ thiếu máu/thiếu kẽm); eBASIS bị loại vì trang chủ mô tả truy cập theo membership, không xác nhận được gói miễn phí; ASEANFOODS bị loại vì VFCT 2017 đã đối chiếu chéo sẵn (trùng lặp); WikiFCD/FoodOn bị loại vì cần hạ tầng SPARQL/ontology không tương xứng lợi ích cho MVP. QĐ 5948/QĐ-BYT KHÔNG được dùng làm nguồn cho DAT-05 vì chỉ xác nhận được là danh mục thuốc-thuốc, không có bằng chứng phủ thuốc-thực phẩm — tránh suy đoán sai như DEC-008 cảnh báo |
| DEC-016 | 2026-08-05 | Bỏ trần số lượng ở EPIC 1/2 nhưng KHÔNG đổi ngưỡng validate_data.py; chỉ điền source_ref cho dược chất xác nhận được có chuyên luận riêng (17/30), để trống 13/30 còn lại | Hưng (yêu cầu) | Bối cảnh: yêu cầu "nâng trần → không giới hạn" cho EPIC 1/2 + "fill full data với mọi data tìm được". Phương án cân nhắc: A) đổi AC ticket thành số lớn tuỳ ý (VD 500 món) để nhìn "đầy tham vọng"; B) đổi AC thành "sàn, không phải trần" — không đặt trần trên nhưng cũng không bịa số lớn hơn hiện có; C) với drug_food_interactions, điền source_ref cho TẤT CẢ 30 dòng bằng cách suy luận chuyên luận Dược thư "chắc là có" cho các dược chất phổ biến. Chọn B (không đặt số trần tuỳ ý — số lượng là biến phụ thuộc, có nguồn thật hay không mới là biến chính, đúng RULE-2/DEC-008) và từ chối C (chỉ điền 17/30 đã xác nhận qua tìm kiếm thực tế có trang chuyên luận riêng, 13 dược chất còn lại — kể cả rất phổ biến như Metformin/Simvastatin — để trống vì KHÔNG tự xác nhận được, dù nhiều khả năng có thật). Hệ quả: "không giới hạn" trong ticket nghĩa là "không dừng lại vì đã đạt con số ban đầu", không phải "báo đã xong 100%" — validate_data.py vẫn coi 13 dòng thiếu source_ref là cảnh báo cần R2 xử lý tiếp, không tự ý tắt cảnh báo đó |
| DEC-017 | 2026-08-05 | Khối USDA bulk (~7000 dòng food_items, id≥100000) chỉ dùng làm kho tham chiếu, loại khỏi ứng viên sinh thực đơn qua `USDA_BULK_ID_THRESHOLD` trong `retrieve_context` | Hưng (xác nhận) | Bối cảnh: thêm 6.854 dòng USDA bulk để đạt mục tiêu "1000+ food_items" khiến CP-SAT chậm 30-50 lần (đo thật: 1,5s→50s) vì `retrieve_context` đưa toàn bộ `food_items` làm ứng viên. Phương án cân nhắc: A) lọc candidate — chỉ dùng ~150 dòng Việt curated cho sinh thực đơn, giữ 7000 dòng USDA làm tham chiếu; B) giữ nguyên, chấp nhận chậm hơn; C) giảm quy mô nhập USDA xuống ~1000 dòng thay vì 6854. Chọn A vì không đánh đổi hiệu năng tính năng đã kiểm chứng (CP-SAT) lấy số lượng dữ liệu thô, đồng thời vẫn giữ được toàn bộ 7000+ dòng cho mục đích tra cứu/OOV/mở rộng sau. Hệ quả: `id` ≥100000 (fdc_id USDA) là quy ước phân tách "tham chiếu" vs "ứng viên sinh thực đơn" — mọi dữ liệu USDA bulk nhập sau này (kể cả mở rộng purine) nên tuân theo cùng quy ước ID để không cần sửa lại filter |

**Mẫu ghi quyết định mới:**

```markdown
| DEC-0XX | YYYY-MM-DD | <quyết định 1 dòng> | <ai> | Bối cảnh: … · Phương án cân nhắc: A/B/C · Chọn B vì … · Hệ quả: … |
```

---

---

## Sự cố & bài học

| ID | Ngày | Sự cố | Tác động | Nguyên nhân gốc | Đã làm gì | Phòng ngừa |
|---|---|---|---|---|---|---|
| | | | | | | |

*(Ghi cả sự cố nhỏ: CI hỏng 2 tiếng, mất 1 buổi vì merge conflict, LLM ngốn hết credit… Đây là nguyên liệu tốt nhất cho slide "Challenges & Learnings".)*

---
