# Kế hoạch DAT-12 — Bỏ trần dữ liệu EPIC 1/2, fill full data, hoàn thiện DB/ERD

> Dành cho cả người thật lẫn AI agent khác cùng theo dõi. Nhánh làm việc: `feature/DAT-12-uncap-data-and-db` (tách từ `main`, hiện tại `main` đã có toàn bộ dữ liệu/DB build của các PR trước — xem mục 1). Owner tổng: R2 (data) + R3 (DB) phối hợp, R1 review.

---

## 0. Việc cần làm (yêu cầu gốc)

1. Bỏ trần số lượng cứng (150 thực phẩm / 80 món / 80 cặp thuốc-thực phẩm / ~15 tài liệu / 40 rule) trong **EPIC 1 (DATA)** và **EPIC 2 (CLINICAL ENGINE)** của `docs/TICKETS.md` — chuyển từ "đủ N là xong" sang "không giới hạn trên, càng nhiều nguồn thật càng tốt", giữ lại **sàn tối thiểu** để vẫn có AC đo được cho MVP.
2. Fill dữ liệu thật nhiều nhất có thể — mọi nguồn đã xác minh dùng được (NIN, USDA, Open Food Facts, Dược thư QGVN — xem `data/README.md` mục "Nghiên cứu bổ sung nguồn dữ liệu").
3. Xây dựng database thật (schema, ERD) — **CẦN KIỂM TRA TRƯỚC KHI LÀM LẠI: phần này đã được làm một phần đáng kể trong PR gần nhất trên `main` (BE-01, ngày 2026-08-05) — xem mục 1 để không làm trùng.**
4. Bổ sung ticket mới cho các phần việc phát sinh.

---

## 1. Trạng thái thật tính đến 2026-08-05 (đọc kỹ trước khi bắt tay, tránh làm trùng)

### 1.1 Dữ liệu (CSV seed)

| File | Số dòng | Ghi chú |
|---|---|---|
| `food_items.csv` | 152 | Đã điền phần lớn qua nhiều đợt (DAT-02, DAT-09 NIN 2017, DAT-10 FDC Survey) — **còn khoảng 27 dòng trống** (kiểm tra lại bằng `python scripts/validate_data.py`) |
| `dishes.csv` | **chỉ 3 dòng** | Mục tiêu gốc DAT-04 là ≥80 món — **đây là khoảng trống lớn nhất trong toàn bộ EPIC 1**, cả 3 dòng hiện có đều `verified_by=pending` (chưa R2 duyệt) |
| `dish_ingredients.csv` | 11 | Tương ứng 3 món trên, phân rã nguyên liệu |
| `clinical_rules.csv` | 21 | Mục tiêu gốc CLN-02 là ≥40 rule — còn thiếu nhiều, đa số `verify_status=to_verify` |
| `drug_food_interactions.csv` | 30 | Mục tiêu gốc DAT-05 là ≥80 cặp — **`source_ref` toàn bộ đang rỗng**, xem mục 1.3 để biết nguồn nên dùng |
| `gi_values.csv` | 28 | Nguồn riêng (Atkinson 2021, Chan 2001) — phủ thưa là bình thường (GI hiếm dữ liệu), không phải lỗi |
| `purine_values.csv` | 19 | Nguồn riêng (USDA/ODS-NIH Purine DB) — chỉ cần cho ca gout |
| `usda_values.csv` | 23 | Bảng phụ trợ merge vào `food_items.csv`, không phải bảng DB độc lập |
| `serving_sizes.csv` | 5 | Khẩu phần chuẩn (phở/bún/cơm...) — rất mỏng so với số món cần |

**Chạy lệnh sau trước khi bắt đầu để có số chính xác lúc bạn đọc file này** (số ở trên có thể đã đổi):
```bash
python scripts/validate_data.py
```

### 1.2 Database (SQLAlchemy + Alembic) — ĐÃ LÀM MỘT PHẦN, đừng làm lại từ đầu

Ticket `BE-01` trong `docs/TICKETS.md` đã được cập nhật trạng thái **"✅ (khung đã build, còn phần tích hợp)"** ngày 2026-08-05:

- `src/db/models.py` — **15 bảng SQLAlchemy đã viết**: `User`, `PatientProfile`, `PatientMedication`, `PatientAllergy`, `FoodItem`, `Dish`, `DishIngredient`, `ServingSize`, `ClinicalRule`, `DrugFoodInteraction`, `GuidelineChunk`, `MealPlan`, `MealPlanItem`, `FoodLog`, `AuditLog`.
- `src/db/base.py` — `Base` (DeclarativeBase) + session factory + FastAPI dependency `get_db()`.
- `alembic/` + `alembic.ini` — đã init, migration đầu tiên `d027f9b06bd5_initial_schema_be_01.py`, test `upgrade head` / `downgrade base` sạch trên SQLite trắng.
- `tests/test_db_models.py` — 6 test (tạo bảng, insert/round-trip, quan hệ dish↔ingredient không lưu dinh dưỡng — đúng RULE-1).
- `docs/ARCHITECTURE.md` §5 — ERD mermaid **đã cập nhật khớp `src/db/models.py`**, bổ sung 6 bảng ERD bản cũ còn thiếu (`dishes`, `dish_ingredients`, `serving_sizes`, `patient_medications`, `patient_allergies`, `food_logs`, `guideline_chunks`).

**Còn thiếu (phần này mới thật sự cần làm tiếp — xem mục 2.3):**
- Index cho các truy vấn nóng theo pattern thật của BE-03→BE-07 (mới có index mặc định theo FK/unique).
- `psycopg2-binary` chưa cài (chỉ cần khi deploy Postgres thật — hiện dev/test dùng SQLite).
- **Script `seed_db.py`/`make seed` migrate dữ liệu từ `data/seeds/*.csv` sang DB thật — CHƯA VIẾT.** Đây là việc quan trọng nhất còn lại để DB thật sự "sống" thay vì chỉ có schema rỗng.
- `src/api/routes.py` vẫn đọc CSV trực tiếp, chưa nối qua `get_db()` — việc của BE-03 trở đi, không phải BE-01.

→ **Kết luận mục 1.2:** Task "xây dựng database, ERD" của yêu cầu này phần lớn đã xong. Việc còn lại tập trung vào: (a) viết `seed_db.py` để đổ dữ liệu CSV vào DB thật, (b) thêm index theo truy vấn thật, (c) sau đó mới tới việc wire API — nhưng đó là scope của BE-03+ (ngoài EPIC 1/2).

### 1.3 Nguồn dữ liệu đã xác minh dùng được (không suy đoán thêm)

Xem đầy đủ tại `data/README.md` mục "Nghiên cứu bổ sung nguồn dữ liệu":

| Nguồn | Trạng thái | Dùng cho |
|---|---|---|
| NIN (Bảng TPTP VN 2007/2017) | ✅ Đã dùng nhiều | `food_items.csv` |
| USDA FoodData Central | ✅ Đã dùng nhiều | `food_items.csv` |
| **Open Food Facts** | ✅ Xác nhận dùng được (free API, ODbL), **chưa tích hợp** | Sản phẩm đóng gói/công nghiệp (mì gói theo nhãn hiệu, nước chấm đóng gói) — ticket `DAT-11` |
| **Dược thư Quốc gia VN 2022** | ✅ Xác nhận dùng được (743 chuyên luận, tra cứu online miễn phí), **chưa dùng** | `source_ref` cho `drug_food_interactions.csv` — đang là khoảng trống lớn nhất về nguồn |
| FAO uFiSh1.0 (cá/thủy sản) | 🟡 Cần R2 tự thử tải link trực tiếp | `food_items.csv` nhóm thủy sản |
| PhyFoodComp/eBASIS/ASEANFOODS/WikiFCD-FoodOn | ❌ Đã loại, có lý do ghi trong `data/README.md` | — |
| QĐ 5948/QĐ-BYT | ⚠️ Không dùng cho `drug_food_interactions.csv` (chỉ xác nhận là danh mục thuốc-thuốc) | — |

---

## 2. Việc cần làm cụ thể (chia theo người/agent có thể nhận)

### 2.1 Sửa `docs/TICKETS.md` — bỏ trần EPIC 1/2

Đổi các ticket sau từ "đủ N là xong" sang "không giới hạn trên, sàn tối thiểu M":

| Ticket | Trần cũ | Đề xuất |
|---|---|---|
| `DAT-02` | ≥150 dòng food_items | Sàn ≥150 (đã đạt), **không trần trên** — mọi món Việt tìm được nguồn thật đều nên vào |
| `DAT-04` | ≥80 món | Sàn ≥80 (mới đạt 3!), **không trần trên** — càng nhiều món phổ biến có nguồn càng tốt |
| `DAT-05` | ≥80 cặp | Sàn ≥80 (mới đạt 30), **không trần trên** |
| `DAT-06` | ~15 tài liệu | Sàn ~15, **không trần trên** — mọi guideline liên quan 4 bệnh mục tiêu đều nên ingest |
| `CLN-02` | ≥40 rule | Sàn ≥40 (mới đạt 21), **không trần trên** |

**Nguyên tắc khi sửa:** giữ nguyên AC về chất lượng (mỗi dòng phải có `source`/`source_ref`, RULE-2/DEC-008 không đổi) — chỉ bỏ trần *số lượng*, không bỏ trần *chất lượng*. "Không giới hạn" không có nghĩa là được nới lỏng yêu cầu nguồn gốc.

**Ai làm:** bất kỳ agent/thành viên nào — chỉ sửa file markdown, không rủi ro, làm trước tiên.

### 2.2 Fill dữ liệu thật — ưu tiên theo độ hụt

1. **`dishes.csv` (3→80+)** — khoảng trống lớn nhất. Cần: chọn món phổ biến/nguy hiểm (phở, bún, canh chua, thịt kho, cá kho, lẩu...), phân rã nguyên liệu + gram, đối chiếu muối với mốc nghiên cứu (`data/README.md` mục "Mốc kiểm chứng"). 3 món hiện có đều `verified_by=pending` — cần R2 duyệt trước khi coi là xong, không chỉ thêm dòng mới.
2. **`drug_food_interactions.csv` (30→80+, source_ref rỗng→điền đủ)** — dùng Dược thư QGVN 2022 tra từng chuyên luận thuốc.
3. **`food_items.csv` (~27 dòng còn trống)** — tiếp tục kiểu DAT-09/DAT-10: NIN 2017 còn sót + USDA + Open Food Facts cho nhóm đóng gói (ticket `DAT-11`).
4. **`clinical_rules.csv` (21→40+)** — cần R2 đọc thêm guideline (ADA/KDIGO/AHA/ACR) cho các ngưỡng chưa có rule.

**Ai làm:** R2 (chuyên môn lâm sàng/dinh dưỡng) là chính; agent AI có thể hỗ trợ tra cứu + soạn nháp nhưng **món ăn/rule lâm sàng bắt buộc người có chuyên môn duyệt** trước khi đổi `verified_by`/`verify_status` sang đã duyệt.

### 2.3 Hoàn thiện DB (phần thật sự còn thiếu — không làm lại từ đầu)

1. ✅ **[2026-08-05, Claude]** Viết `scripts/seed_db.py` + target `make seed`: đọc `data/seeds/*.csv` → insert vào DB qua `src/db/models.py`, idempotent (`session.merge()` theo khoá chính; `serving_sizes` xoá-hết-rồi-nạp-lại vì không có khoá tự nhiên trong CSV). `dish_ingredients` tự bỏ qua dòng thiếu `food_id`/`dish_id` (kèm log), không crash FK. 4 test mới (`tests/test_seed_db.py`, SQLite in-memory) + verify tay trên SQLite trắng, chạy lại lần 2 số dòng không đổi. Chi tiết xem `BE-10` trong `docs/TICKETS.md`.
2. ⬜ Rà index theo truy vấn thật sẽ dùng ở BE-03..BE-07 (khi các ticket đó bắt đầu) — chưa làm, đúng như kế hoạch (chỉ làm khi có truy vấn thật để rà theo).
3. ⬜ Cài `psycopg2-binary` khi thật sự deploy Postgres (đang comment sẵn trong `requirements.txt`) — chưa cần, dev/test vẫn dùng SQLite.

**Ai làm:** R3 (backend/DevOps) hoặc agent quen SQLAlchemy/Alembic.

### 2.4 Ticket mới cần thêm vào `docs/TICKETS.md`

- **`DAT-11`** (đã có sẵn từ phiên trước) — tích hợp Open Food Facts. Xác nhận vẫn còn nguyên trong TICKETS.md, không cần tạo lại.
- **`DAT-12`** (ticket mới, ứng với nhánh này) — "Bỏ trần số lượng EPIC 1/2 + fill dữ liệu thật không giới hạn". Owner R2, P1.
- **`BE-05b`** (ticket mới, tách từ ghi chú "còn lại" của BE-01) — "Script `seed_db.py`: nạp `data/seeds/*.csv` vào DB thật qua SQLAlchemy". Owner R3, Deps: `BE-01`.

---

## 3. Cách theo dõi tiến độ

- Mỗi người/agent nhận 1 mục ở §2, cập nhật trực tiếp vào file này (đánh dấu ✅ kèm tên + ngày) hoặc ghi vào `DEVLOG.md` §2 theo đúng skill `ticket-workflow`.
- Trước khi mở PR: chạy `python scripts/validate_data.py` (chặn nếu thiếu `source`) + `pytest tests/ -q` + `ruff check` + `mypy src/`.
- Không tự ý gộp `dishes.csv`/`clinical_rules.csv` mới vào `verified_by=<tên bạn>` nếu bạn không phải người có chuyên môn lâm sàng thật — giữ `pending` và nhờ R2 duyệt, đúng RULE-3 (không có đường tắt tới bệnh nhân, áp dụng cả cho dữ liệu chưa duyệt).

---

## 4. Việc KHÔNG làm trong phạm vi này

- Không viết lại `src/db/models.py`/`alembic/` từ đầu — đã có, chỉ bổ sung theo mục 2.3.
- Không tự nới lỏng RULE-2/DEC-008 để đạt số lượng nhanh hơn — "không giới hạn" là bỏ trần trên, không phải hạ chuẩn nguồn gốc.
- Không đổi `verify_status`/`verified_by` sang đã duyệt nếu không phải người có thẩm quyền lâm sàng.
