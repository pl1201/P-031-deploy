# Data Synthesis — Hồ sơ bệnh nhân mô phỏng cho ĐTĐ2

> Tài liệu này mô tả cách hồ sơ bệnh nhân mô phỏng trong `data/seeds/synthetic_t2dm_profiles_*.json` được tạo ra từ dữ liệu nghiên cứu NHANES.

---

## Tổng quan

**Mục tiêu:** Tạo hồ sơ bệnh nhân đái tháo đường type 2 mô phỏng có đặc tính thống kê phản ánh quần thể thực tế, nhưng **100% synthetic** — không sao chép bất kỳ bản ghi bệnh nhân thật nào.

**Phương pháp:** Học phân bố thống kê từ dữ liệu công khai NHANES 2021-2023, sau đó sinh hồ sơ mới bằng cách lấy mẫu từ các phân bố đã học.

**Tuân thủ:** Cách tiếp cận này tuân thủ chính sách MVP "100% hồ sơ mô phỏng" (PRD v2.1 §4.1, CLAUDE.md §3) và NCHS Data User Agreement (không phát hành participant-level data).

---

## Nguồn dữ liệu: NHANES 2021-2023

### Thông tin nguồn

- **Dataset:** National Health and Nutrition Examination Survey (NHANES)
- **Cycle:** August 2021 – August 2023
- **URL:** https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023
- **Số người tham gia:** 11,933
- **Ngày phát hành:** September/October 2024
- **Giấy phép:** NCHS Data User Agreement (cho phép phân tích thống kê, cấm tái định danh)

### Files đã sử dụng

| Component | File | CDC Release | Variables chính |
|---|---|---|---|
| Demographics | DEMO_L.xpt | 2024-09 | SEQN, RIDAGEYR, RIAGENDR, RIDRETH3, WTMEC2YR |
| Diabetes | DIQ_L.xpt | 2024-09 | DIQ010, DIQ040, DIQ050, DID060 |
| HbA1c | GHB_L.xpt | 2024-10 | LBXGH |
| Glucose | GLU_L.xpt | 2024-10 | LBXGLU |
| Body Measures | BMX_L.xpt | 2024-09 | BMXWT, BMXHT, BMXBMI, BMXWAIST |
| Blood Pressure | BPXO_L.xpt | 2024-09 | BPXOSY1, BPXODI1 |
| Dietary Day 1 | DR1TOT_L.xpt | 2024-09 | DR1TKCAL, DR1TCARB, DR1TPROT, DR1TFAT, DR1TSODI |
| Dietary Day 2 | DR2TOT_L.xpt | 2024-09 | DR2TKCAL, DR2TCARB, DR2TPROT, DR2TFAT, DR2TSODI |

**Checksum và provenance:** Xem `~/data/research/nhanes_2021_2023/MANIFEST.json` (không commit vào repo)

---

## Heuristic xác định Probable Type 2 Diabetes

Do NHANES không có biến phân loại rõ ràng type 1 vs type 2, chúng tôi áp dụng heuristic sau để lọc **probable T2DM**:

### Tiêu chí bao gồm:
1. **Self-reported diabetes:** `DIQ010 = 1` (đã được nhân viên y tế báo có diabetes)
2. **Người trưởng thành:** `RIDAGEYR >= 20`

### Tiêu chí loại trừ (likely type 1):
- Đang dùng insulin (`DIQ050 = 1`)
- **VÀ** chẩn đoán khi < 30 tuổi (`DIQ040 < 30`)
- **VÀ** bắt đầu insulin ≤ 1 năm sau chẩn đoán (`DID060 <= 1` hoặc `DID060 = 666` [<1 năm])

### Kết quả:
- Từ 11,933 người tham gia NHANES 2021-2023
- Số ca probable T2DM sau lọc: **~700-900 ca** (số chính xác xem output script)

**Lưu ý quan trọng:** Đây là **probable** (có khả năng) type 2, không phải type 2 **đã xác nhận** bằng chẩn đoán y khoa. Heuristic này có thể bỏ sót một số T2DM thật và có thể bao gồm một số trường hợp biên.

---

## Pipeline sinh hồ sơ mô phỏng

### Bước 1: Tải dữ liệu NHANES

**Script:** `scripts/download_nhanes_2021_2023.py`

**Chức năng:**
- Tải 8 file XPT từ CDC qua HTTPS (TLS verification bật)
- Tính SHA-256 checksum
- Ghi provenance (URL, retrieval timestamp, file size, CDC release date)
- Lưu vào `~/data/research/nhanes_2021_2023/raw/` (ngoài repo)

**Output:**
- 8 files `.xpt`
- `MANIFEST.json` với metadata đầy đủ

### Bước 2: Ghép và lọc cohort

**Script:** `scripts/build_nhanes_2021_2023_cohort.py`

**Chức năng:**
- Đọc 8 XPT files, ghép bằng `SEQN` (participant ID)
- Validate schema (kiểm tra cột bắt buộc)
- Áp dụng heuristic probable T2DM
- Gắn nhãn `diabetes_source = self_report`, `diabetes_type = probable_type2`

**Output:**
- `nhanes_merged.csv` — toàn bộ cohort đã ghép
- `nhanes_probable_t2dm.csv` — chỉ probable T2DM cases

### Bước 3: Phân tích phân bố

**Script:** `scripts/analyze_nhanes_distributions.py`

**Chức năng:**
- Đọc `nhanes_probable_t2dm.csv`
- Tính thống kê **có trọng số** bằng survey weights (`WTMEC2YR`)
- Ước lượng phân bố (mean, std, percentiles) cho:
  - Demographics: age, sex
  - Anthropometrics: weight, height, BMI, waist
  - Labs: HbA1c, glucose
  - Blood pressure: SBP, DBP
  - Dietary: kcal, carb, protein, fat, sodium
- Tính ma trận correlation giữa các biến chính

**Output:**
- `distributions/t2dm_distributions.json` — chỉ chứa **tham số phân bố**, không chứa participant-level data

**Tầm quan trọng của survey weights:** NHANES sử dụng phương pháp lấy mẫu phức tạp (stratified, multi-stage). Survey weights (`WTMEC2YR`) điều chỉnh cho:
- Xác suất lựa chọn không đồng đều
- Non-response
- Post-stratification

→ Cho phép ước lượng **đại diện cho dân số Hoa Kỳ**, không chỉ mẫu NHANES.

### Bước 4: Sinh hồ sơ mô phỏng

**Script:** `scripts/generate_synthetic_t2dm_profiles.py`

**Chức năng:**
- Đọc `distributions/t2dm_distributions.json`
- Sinh N hồ sơ bằng cách lấy mẫu từ phân bố chuẩn `N(mean, std²)`
- Clip giá trị về khoảng [p5, p95] để tránh outlier vô lý
- Đảm bảo tính nhất quán: BMI tính từ weight/height phải gần BMI đã sinh
- **Thêm đặc tính Việt Nam** không có trong NHANES:
  - `region`: "north", "central", "south" (không có trong NHANES)
  - `dislikes`: danh sách món Việt không thích (không có trong NHANES)
- Gắn metadata:
  ```json
  {
    "_synthetic": true,
    "_source_dataset": "NHANES_2021_2023_derived",
    "_generation_method": "sample_from_distributions",
    "_generation_seed": 42
  }
  ```

**Output:**
- `data/seeds/synthetic_t2dm_profiles_v1.json` — **CÓ TRONG REPO**, vì đã 100% mô phỏng

**Đảm bảo không trùng:**
- Không sao chép `SEQN` hay bất kỳ ID thật nào
- Mỗi profile có `patient_id` mới dạng `synthetic_t2dm_<uuid>`
- Giá trị được sinh độc lập từ phân bố, không phải lookup từ NHANES

---

## Validation và kiểm tra

### Các bước đã thực hiện:

1. **Checksum verification:** SHA-256 của XPT files được ghi lại trong MANIFEST.json
2. **Schema validation:** Kiểm tra các cột bắt buộc có mặt trước khi merge
3. **Merge cardinality:** Sử dụng `pandas.merge(..., validate="one_to_one")` để đảm bảo không có duplicate
4. **Distribution sanity check:**
   - Mean age > 40 (T2DM thường phát triển ở người lớn tuổi)
   - Mean BMI > 25 (béo phì là yếu tố nguy cơ)
   - Mean HbA1c > 6% (ngưỡng chẩn đoán diabetes)
   - Không có outlier vô lý (VD: age > 120, BMI > 100)
5. **Synthetic independence:** Không có SEQN, tất cả profile có `_synthetic=true`

### Validation với PatientProfile schema:

Script sinh ra JSON conform với `src/clinical/models.py:PatientProfile`:
- ✅ Tất cả required fields có mặt
- ✅ Types đúng (`int`, `float`, `str`, `list`)
- ✅ Constraints: `age` ∈ [1, 120], `height_cm` ∈ [80, 250], `weight_kg` ∈ [20, 300]
- ✅ `conditions` có structure đúng với `code`, `name`, `stage`, `lab_values`

---

## Limitation và disclaimer

### ⚠️ Người dùng phải biết:

1. **Nguồn gốc Hoa Kỳ:** Phân bố dựa trên dân số Hoa Kỳ (NHANES), không đại diện cho dân số Việt Nam. Có thể có khác biệt về:
   - Phân bố BMI (người Việt có ngưỡng béo phì thấp hơn)
   - Tỷ lệ bệnh đồng mắc
   - Dietary patterns (đã điều chỉnh một phần bằng cách thêm `region` và `dislikes` Việt Nam)

2. **Nhãn "probable":** Không phải T2DM đã xác nhận bằng chẩn đoán y khoa. Heuristic dựa trên self-report và age/insulin use có thể có sai sót.

3. **Thiếu medication chi tiết:** NHANES 2021-2023 cycle không có tên thuốc kê đơn chi tiết. Medications trong hồ sơ mô phỏng được sinh đơn giản dựa trên HbA1c (VD: nếu HbA1c > 7% → thêm "Metformin").

4. **Dietary data:** Dựa trên 2 ngày dietary recall 24h, không đại diện cho intake thường xuyên. Món ăn cụ thể không có trong NHANES → không thể map trực tiếp sang món Việt.

5. **Cross-sectional:** NHANES là dữ liệu cắt ngang, không có follow-up hay progression. Không thể mô phỏng diễn tiến bệnh theo thời gian.

6. **Sample size giới hạn:** ~700-900 probable T2DM cases từ NHANES. Khi sinh >1000 profiles, sẽ có nhiều profiles "giống nhau về mặt thống kê" hơn.

### 🔒 Tuân thủ:

- ✅ **NCHS Data User Agreement:** Không phát hành participant-level data. Chỉ phát hành thống kê tổng hợp (distributions) và hồ sơ mô phỏng độc lập.
- ✅ **Project policy (PRD v2.1, CLAUDE.md):** 100% hồ sơ mô phỏng trong product path. Dữ liệu thật chỉ dùng cho research, không vào repo/DB/prompt.
- ✅ **HIPAA N/A:** NHANES là public-use dataset, đã de-identified bởi NCHS.

---

## Files và đường dẫn

### Trong repo (commit được):
- `scripts/download_nhanes_2021_2023.py`
- `scripts/build_nhanes_2021_2023_cohort.py`
- `scripts/analyze_nhanes_distributions.py`
- `scripts/generate_synthetic_t2dm_profiles.py`
- `data/seeds/synthetic_t2dm_profiles_v1.json` ← **output cuối, 100% mô phỏng**
- `docs/DATA_SYNTHESIS.md` ← file này

### Ngoài repo (KHÔNG commit):
- `~/data/research/nhanes_2021_2023/raw/*.xpt` — XPT files gốc từ CDC
- `~/data/research/nhanes_2021_2023/processed/nhanes_merged.csv` — toàn bộ cohort
- `~/data/research/nhanes_2021_2023/processed/nhanes_probable_t2dm.csv` — T2DM cohort
- `~/data/research/nhanes_2021_2023/distributions/t2dm_distributions.json` — phân bố tổng hợp
- `~/data/research/nhanes_2021_2023/MANIFEST.json` — provenance

---

## Cách chạy pipeline

```bash
# Bước 1: Tải NHANES XPT files (cần pandas, requests)
python scripts/download_nhanes_2021_2023.py

# Bước 2: Ghép và lọc probable T2DM
python scripts/build_nhanes_2021_2023_cohort.py

# Bước 3: Phân tích phân bố
python scripts/analyze_nhanes_distributions.py

# Bước 4: Sinh 100 hồ sơ mô phỏng
python scripts/generate_synthetic_t2dm_profiles.py --count 100 --seed 42
```

**Dependencies:** Thêm vào `requirements.txt` hoặc `requirements-research.txt`:
```
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
requests>=2.31.0
```

---

## Tham khảo

### NHANES
- Cycle 2021-2023: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023
- Analytic Guidelines: https://wwwn.cdc.gov/nchs/nhanes/analyticguidelines.aspx
- Survey Weights Tutorial: https://wwwn.cdc.gov/nchs/nhanes/tutorials/weighting.aspx

### Project
- PRD v2.1: `docs/PRD.md` (MVP scope, 100% simulated data policy)
- CLAUDE.md §3: Data safety rules
- Clinical Safety: `docs/rules/10-clinical-safety.md` §10.9
- PatientProfile schema: `src/clinical/models.py:58-93`

---

**Người viết:** Claude Code (Opus 4.8)  
**Ngày:** 2026-08-06  
**Version:** 1.0
