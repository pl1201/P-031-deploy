# Kế hoạch crawl và chuẩn hóa dữ liệu T2DM châu Á

**Ngày:** 2026-08-06  
**Mục tiêu:** Tải và chuẩn hóa 3 nguồn dữ liệu T2DM châu Á về chuẩn Việt Nam  
**Timeline:** 3-5 ngày  
**Output:** ~56,000 bệnh nhân T2DM sẵn sàng cho training/validation

---

## 1. Tổng quan

### 1.1. Nguồn đã có (✅ Completed)

| Nguồn | N | BMI | HbA1c | Status |
|---|---:|---:|---|---|
| NHANES VN-adapted | 840 | 24.0 | ✅ | ✅ Ready |
| Da Nang (VN) | 103 | 24.2 | ✅ | ✅ Ready |

**Total current:** 943 bệnh nhân

### 1.2. Nguồn cần tải (🔄 Priority targets)

| Nguồn | N (est.) | BMI | HbA1c | Priority | Timeline |
|---|---:|---:|---|---|---|
| **Bangladesh STEPS 2018** | 750 | 23.4 | ❌ | ⭐⭐⭐⭐⭐ | 1 ngày |
| **China CHNS 2009+2015** | 4,500 | 24-26 | ✅ (2015) | ⭐⭐⭐⭐⭐ | 2-3 ngày |
| **India NFHS-5 2019-21** | 55,000 | 23-25 | ❌ | ⭐⭐⭐⭐⭐ | 2-3 ngày |

**Total after crawl:** ~61,000 bệnh nhân T2DM

---

## 2. Chi tiết từng nguồn

### 2.1. Bangladesh STEPS 2018 (⭐⭐⭐⭐⭐ HIGHEST PRIORITY)

**Tại sao ưu tiên cao nhất:**
- BMI 23.4 kg/m² — GẦN VN NHẤT (VN: 24.0)
- Download NHANH NHẤT (instant approval)
- Sample size vừa phải (750) — dễ xử lý

**Steps:**

1. **Download (30 phút)**
   ```bash
   # Visit: https://extranet.who.int/ncdsmicrodata/index.php/catalog/770
   # Fill form → Download BGD_2018_STEPS_v01_M_stata.zip
   # Extract to: ~/data/research/bangladesh_steps_2018/raw/
   ```

2. **Build cohort (1 giờ)**
   ```bash
   python scripts/build_bangladesh_steps_t2dm_cohort.py
   # Input:  BGD_2018_STEPS_v01_M.dta
   # Filter: Glucose >= 7.0 mmol/L OR diabetes self-report
   # Output: ~/data/research/bangladesh_steps_2018/processed/bangladesh_t2dm.csv
   ```

3. **Convert to JSON (30 phút)**
   ```bash
   python scripts/convert_bangladesh_to_json.py
   # Output: data/.json/bangladesh_t2dm_profiles.json
   ```

4. **Adapt to VN norms (30 phút)**
   ```bash
   python scripts/adapt_bangladesh_to_vietnam.py
   # Adjustment: Minimal (BMI already 23.4, very close to VN 24.0)
   # Height: Male 163→165cm, Female 152→155cm (small shift)
   # Output: data/.json/bangladesh_t2dm_profiles_vn_adapted.json
   ```

**Expected output:**
- N: ~750 bệnh nhân
- BMI adapted: 23.4 → 24.0 kg/m²
- Height adapted: Match VN means
- Clinical: Glucose preserved

**Validation:**
- Compare glucose distribution with NHANES
- Check BMI-glucose correlation preserved
- Verify no outliers after adaptation

---

### 2.2. China CHNS 2009 + 2015 (⭐⭐⭐⭐⭐ HIGHEST PRIORITY)

**Tại sao quan trọng:**
- Sample lớn nhất có HbA1c (2015 wave)
- Longitudinal data (2009 → 2015 changes)
- Dietary data đầy đủ (3-day recall)
- BMI 24-26 — Gần VN hơn NHANES US

**Steps:**

1. **Register & Download (1-2 ngày)**
   ```bash
   # Register: https://www.cpc.unc.edu/projects/china/data/datasets
   # Wait for approval: Usually 1-2 business days
   # Download:
   #   - chns_2009_biomarker.dta
   #   - chns_2009_demographic.dta
   #   - chns_2015_biomarker.dta
   #   - chns_2015_demographic.dta
   # Extract to: ~/data/research/chns_china/raw/
   ```

2. **Build cohort (2 giờ)**
   ```bash
   python scripts/build_chns_t2dm_cohort.py
   # Merge 2009 + 2015 waves by ID
   # Filter T2DM: HbA1c >= 6.5% OR glucose >= 126 OR self-report
   # Handle longitudinal: Keep unique individuals (prefer 2015 if both)
   # Output: ~/data/research/chns_china/processed/chns_t2dm.csv
   ```

3. **Convert to JSON (1 giờ)**
   ```bash
   python scripts/convert_chns_to_json.py
   # Map to PatientProfile schema
   # Include dietary data if available
   # Output: data/.json/chns_t2dm_profiles.json
   ```

4. **Adapt to VN norms (1 giờ)**
   ```bash
   python scripts/adapt_chns_to_vietnam.py
   # BMI: 25.5 → 24.0 (shift -1.5)
   # Height: Male 168→168cm (already match), Female 158→156cm
   # Preserve: HbA1c, glucose, lipids, BP
   # Output: data/.json/chns_t2dm_profiles_vn_adapted.json
   ```

**Expected output:**
- N: ~4,500 bệnh nhân T2DM
- BMI adapted: 25.5 → 24.0 kg/m²
- HbA1c: Preserved (2015 wave)
- Dietary: Chinese → Vietnamese food mapping (future work)

**Validation:**
- Compare HbA1c distribution with NHANES
- Check BMI shift doesn't break clinical correlations
- Verify 2009 vs 2015 consistency

---

### 2.3. India NFHS-5 2019-2021 (⭐⭐⭐⭐⭐ LARGEST SAMPLE)

**Tại sao quan trọng:**
- Sample LỚN NHẤT: ~55,000 T2DM
- "Lean diabetes" phenotype (BMI 22-25) — Đặc thù châu Á
- Recent data (2019-2021)
- Free registration (DHS Program)

**Steps:**

1. **Register & Download (2-3 ngày)**
   ```bash
   # Register: https://dhsprogram.com/data/new-user-registration.cfm
   # Wait for approval: 24-48 hours (usually faster)
   # Download:
   #   - IABR7EDT.dta (Biomarker - CRITICAL)
   #   - IAHR7EDT.dta (Household)
   #   - IAIR7EDT.dta (Women)
   #   - IAMR7EDT.dta (Men)
   # Extract to: ~/data/research/nfhs5_india/raw/
   ```

2. **Build cohort (3 giờ - LARGE FILE)**
   ```bash
   python scripts/build_nfhs5_t2dm_cohort.py
   # Merge biomarker + demographic by HHID
   # Filter T2DM: Glucose >= 126 (fasting) OR >= 200 (random) OR self-report
   # Fasting vs random: Use SH20A (time since last ate)
   # Sample if needed: 10,000-15,000 random T2DM (too large otherwise)
   # Output: ~/data/research/nfhs5_india/processed/nfhs5_t2dm.csv
   ```

3. **Convert to JSON (2 giờ - LARGE)**
   ```bash
   python scripts/convert_nfhs5_to_json.py
   # Handle large N: Chunk processing
   # Output: data/.json/nfhs5_t2dm_profiles.json
   ```

4. **Adapt to VN norms (1 giờ)**
   ```bash
   python scripts/adapt_nfhs5_to_vietnam.py
   # BMI: 23.5 → 24.0 (small shift +0.5)
   # Height: Male 165→168cm, Female 153→156cm (increase slightly)
   # Preserve: Glucose, BP
   # Note: No HbA1c in NFHS-5
   # Output: data/.json/nfhs5_t2dm_profiles_vn_adapted.json
   ```

**Expected output:**
- N: 10,000-15,000 (sampled from ~55,000 to keep manageable)
- BMI adapted: 23.5 → 24.0 kg/m²
- Glucose: Preserved
- HbA1c: Not available (use glucose-only validation)

**Validation:**
- Stratified sampling: Preserve rural/urban, state distribution
- Compare glucose with NHANES (glucose-to-HbA1c correlation)
- Validate "lean diabetes" phenotype (BMI <25 but T2DM)

---

## 3. Adaptation methodology

### 3.1. Height adjustment

**Targets (Vietnamese norms):**
- Male: 168 ± 6.5 cm
- Female: 156 ± 6.0 cm

**Method:**
```python
def adjust_height(original_height, original_sex, source_country):
    # Shift distribution while preserving relative position
    shift = VN_HEIGHT_MEAN[sex] - SOURCE_HEIGHT_MEAN[country][sex]
    new_height = original_height + shift + noise
    return clip(new_height, min_height, max_height)
```

### 3.2. BMI adjustment

**Target:** 24.0 ± 3.0 kg/m² (from Da Nang study)

**Method:**
```python
def adjust_bmi(original_bmi, source_mean_bmi):
    # Shift distribution down to VN target
    shift = VN_BMI_TARGET - source_mean_bmi
    new_bmi = original_bmi + shift + noise
    return clip(new_bmi, 18.0, 35.0)  # Reasonable T2DM range
```

**Weight recalculation:**
```python
weight_kg = new_bmi * (new_height_m ** 2)
```

### 3.3. Clinical values preservation

**KHÔNG điều chỉnh:**
- HbA1c (%)
- Fasting glucose (mg/dL)
- Blood pressure (mmHg)
- Lipids (mg/dL)

**Lý do:** Clinical values assumed independent of anthropometric adjustments
(supported by literature — glucose metabolism similar across ethnicities)

### 3.4. Vietnamese-specific additions

**Add to all adapted profiles:**
```python
profile["region"] = random.choice(["north", "central", "south"], p=[0.4, 0.2, 0.4])
profile["dislikes"] = random.choice(VIETNAMESE_DISLIKES, n=0-3)
profile["activity_level"] = random.choice(["sedentary", "lightly_active", "moderately_active"])
profile["weight_goal"] = random.choice(["lose", "maintain", "gain"], p=[0.6, 0.35, 0.05])
```

---

## 4. Scripts cần tạo

### 4.1. Bangladesh (3 scripts)

- ✅ `scripts/download_bangladesh_steps_t2dm.py` (instructions)
- ⏳ `scripts/build_bangladesh_steps_t2dm_cohort.py` (cần tạo)
- ⏳ `scripts/convert_bangladesh_to_json.py` (cần tạo)
- ⏳ `scripts/adapt_bangladesh_to_vietnam.py` (cần tạo)

### 4.2. China (3 scripts)

- ✅ `scripts/download_chns_china_t2dm.py` (instructions)
- ⏳ `scripts/build_chns_t2dm_cohort.py` (cần tạo)
- ⏳ `scripts/convert_chns_to_json.py` (cần tạo)
- ⏳ `scripts/adapt_chns_to_vietnam.py` (cần tạo)

### 4.3. India (3 scripts)

- ✅ `scripts/download_india_nfhs5_t2dm.py` (instructions)
- ⏳ `scripts/build_nfhs5_t2dm_cohort.py` (cần tạo)
- ⏳ `scripts/convert_nfhs5_to_json.py` (cần tạo)
- ⏳ `scripts/adapt_nfhs5_to_vietnam.py` (cần tạo)

**Pattern:** Mỗi nguồn 3 scripts (build → convert → adapt), tái sử dụng logic từ NHANES pipeline

---

## 5. Timeline & Dependencies

```
Day 1: Bangladesh (FASTEST)
├── Morning: Download + build cohort (1.5h)
├── Afternoon: Convert + adapt (1h)
└── Evening: Validate + commit (0.5h)

Day 2-3: China CHNS (WAIT FOR APPROVAL)
├── Day 2 AM: Submit registration
├── Day 2 PM: [Wait] Write build/convert/adapt scripts
├── Day 3 AM: [Approval] Download data
├── Day 3 PM: Process + validate
└── Evening: Commit

Day 2-3: India NFHS-5 (PARALLEL WITH CHINA)
├── Day 2 AM: Submit DHS registration
├── Day 2 PM: [Wait] Write build/convert/adapt scripts
├── Day 3 AM: [Approval] Download biomarker file
├── Day 3-4: Process large file (chunked)
└── Day 4: Sample + validate + commit

Day 5: Integration & Validation
├── Merge all adapted datasets
├── Cross-validate distributions
├── Update DATA_RESEARCH_REPORT.md
└── Final commit
```

---

## 6. Validation checklist

### 6.1. Per-source validation

**For each adapted dataset:**

- [ ] BMI distribution: Mean ~24.0 ± 3.0
- [ ] Height distribution: Match VN norms (M: 168, F: 156)
- [ ] HbA1c preserved (if available): Same mean/SD as original
- [ ] Glucose preserved: Same mean/SD as original
- [ ] No outliers: BMI 18-35, height reasonable, glucose/HbA1c realistic
- [ ] Clinical correlations: BMI-HbA1c, BMI-glucose correlations weakened <10%

### 6.2. Cross-source validation

**Compare adapted datasets:**

- [ ] BMI convergence: All adapted sources ~24.0 ± 0.5
- [ ] HbA1c consistency: NHANES vs CHNS HbA1c distributions similar
- [ ] Glucose consistency: Bangladesh/India/NHANES glucose align
- [ ] Comorbidity rates: Hypertension prevalence comparable

### 6.3. Integration validation

**Merged dataset:**

- [ ] Total N: 56,000-61,000 T2DM patients
- [ ] Source distribution: NHANES 840, Da Nang 103, Bangladesh 750, CHNS 4500, NFHS-5 50000+
- [ ] No duplicates: Unique patient_id across sources
- [ ] Schema compliance: All load into PatientProfile without errors
- [ ] Train/val/test split: Stratified by source + demographics

---

## 7. Output files

### 7.1. Raw data (Outside repo)

```
C:\Users\dinhl\data\research\
├── bangladesh_steps_2018\
│   ├── raw\
│   │   └── BGD_2018_STEPS_v01_M.dta
│   ├── processed\
│   │   └── bangladesh_t2dm.csv (750 rows)
│   └── MANIFEST.json
├── chns_china\
│   ├── raw\
│   │   ├── chns_2009_biomarker.dta
│   │   ├── chns_2015_biomarker.dta
│   │   └── ...
│   ├── processed\
│   │   └── chns_t2dm.csv (4,500 rows)
│   └── MANIFEST.json
└── nfhs5_india\
    ├── raw\
    │   └── IABR7EDT.dta (LARGE)
    ├── processed\
    │   └── nfhs5_t2dm_sampled.csv (15,000 rows)
    └── MANIFEST.json
```

### 7.2. Processed data (In repo)

```
d:\P-031\data\
├── .json\
│   ├── bangladesh_t2dm_profiles_vn_adapted.json (750, ~800 KB)
│   ├── chns_t2dm_profiles_vn_adapted.json (4,500, ~5 MB)
│   ├── nfhs5_t2dm_profiles_vn_adapted.json (15,000, ~18 MB)
│   └── merged_asian_t2dm_vn_adapted.json (21,193, ~25 MB)
└── patients\
    └── asian_t2dm_vn_adapted.csv (21,193 rows, flattened)
```

---

## 8. Documentation updates

### 8.1. Files to update

- `docs/DATA_RESEARCH_REPORT.md` — Add Section 14: Asian datasets
- `data/README.md` — Add Asian sources table
- `DEVLOG.md` — Daily progress entries
- `docs/ASIAN_T2DM_CRAWL_PLAN.md` — This file (update status)

### 8.2. New documentation

- `docs/ASIAN_ADAPTATION_METHODOLOGY.md` — Chi tiết phương pháp adaptation
- `docs/CROSS_POPULATION_VALIDATION.md` — So sánh US vs Asian vs VN phenotypes

---

## 9. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| CHNS/NFHS-5 approval delay | Timeline +2-5 days | Medium | Start with Bangladesh first (instant) |
| File too large (NFHS-5) | Memory error | High | Chunk processing, sample 15k instead of 55k |
| Missing variables | Incomplete profiles | Low | Document in limitations, use available variables only |
| Adaptation breaks correlations | Invalid profiles | Medium | Validate correlations before/after, limit shift magnitude |
| Different glucose units | Conversion error | Low | Careful mmol/L ↔ mg/dL conversion (×18 or ÷18) |

---

## 10. Success criteria

✅ **Minimum viable (MVP):**
- Bangladesh + CHNS downloaded & adapted
- Total Asian T2DM: 5,250 (750 + 4,500)
- BMI adapted to ~24.0
- Clinical values validated

✅ **Full success:**
- All 3 sources (Bangladesh + CHNS + NFHS-5)
- Total: 21,000+ T2DM patients
- Cross-validated with NHANES and Da Nang
- Documentation complete

---

## 11. Next immediate steps

**Today (2026-08-06):**

1. ✅ Create download instruction scripts (DONE)
2. ✅ Create this plan document (DONE)
3. ⏳ Commit scripts + plan
4. ⏳ Start Bangladesh download (30 min)
5. ⏳ Submit CHNS + NFHS-5 registrations (while Bangladesh processes)

**Tomorrow (2026-08-07):**

1. ⏳ Complete Bangladesh pipeline
2. ⏳ Write build/convert/adapt scripts for CHNS and NFHS-5
3. ⏳ Wait for approvals

**Day 3-4:**

1. ⏳ Download approved datasets
2. ⏳ Process CHNS and NFHS-5
3. ⏳ Validate all adapted datasets

**Day 5:**

1. ⏳ Merge datasets
2. ⏳ Final validation
3. ⏳ Update documentation
4. ⏳ Final commit

---

**Người lập:** Claude Sonnet 5  
**Review:** Pending R2 (Clinical/Data)  
**Status:** Draft - Ready to execute
