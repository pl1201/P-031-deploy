# Patient Data Directory Structure

## Organization

```
data/patients/
├── t2dm_vn_adapted_set1_840patients.csv
├── t2dm_vn_adapted_set2_700patients.csv
├── t2dm_vn_adapted_set3_372patients.csv
└── t2dm_vn_adapted_set4_108patients.csv
```

## Vietnamese-Adapted T2DM Datasets

**Local inventory: 2,020 source/derived rows.** Đây là các derivative được gắn thuộc tính Việt Nam để nghiên cứu, không phải cohort đại diện dân số Việt Nam và chưa phải tất cả đều được phép dùng trong product/eval path.

### Dataset Status

| Dataset | Rows | Status | Notes |
|---------|------|--------|-------|
| t2dm_vn_adapted_set1_840patients.csv | 840 | Verification pending | NHANES-derived; cần hoàn tất manifest/checksum/retrieval metadata |
| t2dm_vn_adapted_set2_700patients.csv | 700 | Quarantined | Chưa xác minh đầy đủ license và de-identification |
| t2dm_vn_adapted_set3_372patients.csv | 372 | Quarantined | Nguồn/DOI/license chưa xác minh |
| t2dm_vn_adapted_set4_108patients.csv | 108 | Quarantined | Có 5 bản ghi type 1 và schema nghiên cứu riêng; chỉ 103 T2DM sau chuẩn hóa |

### Adaptation Process

All VN-adapted datasets standardized to:
- **BMI target:** 24.2 ± 3.0 kg/m² (Vietnamese T2DM norm from Da Nang study)
- **Height norms:** Male 168±6.5cm, Female 156±6.0cm
- **Clinical values preserved:** Glucose, HbA1c, BP, medications (not recalculated)
- **Vietnamese attributes added:** Region (north/central/south), food dislikes, activity level

See [VN_ADAPTED_DATASETS_REPORT.md](../docs/VN_ADAPTED_DATASETS_REPORT.md) for full methodology and verification.

## Usage Guidelines

### For Development/Evaluation
- Generator chỉ được đọc dataset có trạng thái `enabled` trong manifest.
- Dataset `quarantined` không được dùng làm product seed hoặc benchmark input.
- `eval/datasets/` chỉ chứa hồ sơ synthetic; không sao chép trực tiếp row từ các CSV này.

### Dataset Selection Guide

| Research Question | Recommended Dataset |
|-------------------|-------------------|
| HbA1c-based analysis | `t2dm_vn_adapted_set1_840patients.csv` (795) + `t2dm_vn_adapted_set2_700patients.csv` (700) |
| Glucose-based analysis | `t2dm_vn_adapted_set1_840patients.csv` (435) + `t2dm_vn_adapted_set3_372patients.csv` (372) |
| Medication patterns | `t2dm_vn_adapted_set2_700patients.csv` (700, has medication data) |
| Early-onset T2DM | `t2dm_vn_adapted_set3_372patients.csv` (age 44.7y) |
| Elderly T2DM | `t2dm_vn_adapted_set1_840patients.csv` + `t2dm_vn_adapted_set2_700patients.csv` (age 63-65y) |
| Vietnamese reference | `t2dm_vn_adapted_set4_108patients.csv` |
| Maximum sample size | All 4 VN-adapted datasets combined (2,020 rows) |

## Data Provenance

| Dataset | Source | Provenance Status | Notes |
|---------|--------|-------------------|-------|
| NHANES 2021-2023 | CDC/NCHS | ⚠️ Metadata pending | Public-use, de-identified; cần manifest đầy đủ |
| MontiFinal | Mendeley Data (Thailand study) | ⚠️ Unverified | Cần dataset ID, license và bằng chứng de-identification |
| Type2_Diabetes | Probable Pima Indians | ⚠️ Unverified | No DOI found |
| Da Nang diabetes | PLOS ONE 2022 | ⚠️ Partial | n=108 nhưng gồm 5 type 1; cần DOI/license/extraction record |

## Policy Compliance

✅ **PRD v2.2:** Using de-identified public-use data (NHANES 2021-2023)  
✅ **CLAUDE.md:** No SEQN or PII in prompts, only age/sex/weight/height/labs/medications  
⚠️ **R40.9/R40.12:** Chưa đạt cho đến khi manifest và `data/VERSION` hoàn chỉnh  
✅ **NCHS Data User Agreement:** Statistical analysis only, no re-identification

---

**Last Updated:** 2026-08-06  
**Note:** Raw original files đã được loại khỏi repo; các derivative hiện chỉ là inventory local và phải qua provenance gate trước khi sử dụng.  
**See Also:** [VN_ADAPTED_DATASETS_REPORT.md](../docs/VN_ADAPTED_DATASETS_REPORT.md)

