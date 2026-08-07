"""Trích xuất khối (a) macro+khoang chat (khong lay vitamin - schema hien tai
khong co cot vitamin) tu Bang thanh phan dinh duong Thuc pham VN 2017,
trang 23-152 (15 nhom thuc pham chinh).

Chi dung pdfplumber.extract_tables() - khong OCR, khong doan.

Cau truc PDF: moi nhom di theo cap trang trai/phai. Trang trai chua
macro + khoang chat (bang co header chua "ENERC","WATER","PROCNT"...).
Trang phai chua vitamin (header chua "VITC","THIA"...) - BO QUA vi
schema food_items.csv hien tai khong co cot vitamin.

Output: data ghi ra scripts/nin2017_extracted.json - danh sach dict
moi thuc pham voi cac truong tho theo dung PDF (khong tinh toan/suy dien).
Cot trong PDF -> gia tri None neu o do trong that (khong suy doan).
"""

from __future__ import annotations

import json
from pathlib import Path

import pdfplumber

PDF_PATH = (
    Path(__file__).resolve().parent.parent / "data" / ("Bang-thanh-phan-dinh-duong-Thuc-pham-VN-2017-27-4-17.pdf")
)
OUT_PATH = Path(__file__).resolve().parent / "nin2017_extracted.json"

# Cot trong bang trang trai (22 cot khi co day du header):
# 0 TT | 1 Code | 2 name_vi | 3 name_en | 4 EDIBLE | 5 ENERC | 6 WATER
# 7 PROCNT | 8 FAT | 9 CHOCDF | 10 FIBC | 11 ASH | 12 CA | 13 P | 14 FE
# 15 ZN | 16 NA | 17 K | 18 MG | 19 MN | 20 CU | 21 SE
COL_MAP = {
    "code": 1,
    "name_vi": 2,
    "name_en": 3,
    "edible_pct": 4,
    "enerc_kcal": 5,
    "water_g": 6,
    "procnt_g": 7,
    "fat_g": 8,
    "chocdf_g": 9,
    "fibc_g": 10,
    "ash_g": 11,
    "ca_mg": 12,
    "p_mg": 13,
    "fe_mg": 14,
    "zn_mg": 15,
    "na_mg": 16,
    "k_mg": 17,
    "mg_mg": 18,
    "mn_mg": 19,
    "cu_ug": 20,
    "se_ug": 21,
}

FIRST_PAGE = 23  # 1-indexed, trang dau khoi (a)
LAST_PAGE = 152  # 1-indexed, trang cuoi khoi (a)


def is_left_macro_table(table: list[list[str | None]]) -> bool:
    """Header cua bang trai chua ENERC/WATER/PROCNT (khong phai vitamin)."""
    header_text = " ".join(str(c) for row in table[:4] for c in row if c)
    return "ENERC" in header_text and "WATER" in header_text


def clean_cell(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip().replace("\n", " ")
    return v if v else None


def to_float(v: str | None) -> float | None:
    v = clean_cell(v)
    if v is None:
        return None
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None


def extract_page(table: list[list[str | None]], page_no: int) -> list[dict]:
    """Trich cac dong thuc pham that (cot 0 la so TT dang so) tu 1 bang trai."""
    items = []
    for row in table:
        if not row:
            continue
        tt = clean_cell(row[0]) if len(row) > 0 else None
        if tt is None or not tt.replace(".", "", 1).isdigit():
            # bo qua dong header / dong tieu de nhom (I, II, III...) / dong trong
            continue
        code = clean_cell(row[COL_MAP["code"]]) if len(row) > COL_MAP["code"] else None
        name_vi = clean_cell(row[COL_MAP["name_vi"]]) if len(row) > COL_MAP["name_vi"] else None
        if not code or not name_vi:
            continue
        item = {
            "page": page_no,
            "tt": tt,
            "code": code,
            "name_vi": name_vi.replace("\n", " ").strip(),
            "name_en": clean_cell(row[COL_MAP["name_en"]]) if len(row) > COL_MAP["name_en"] else None,
        }
        for field, idx in COL_MAP.items():
            if field in ("code", "name_vi", "name_en"):
                continue
            item[field] = to_float(row[idx]) if len(row) > idx else None
        items.append(item)
    return items


def main() -> None:
    all_items: list[dict] = []
    skipped_pages: list[int] = []
    with pdfplumber.open(PDF_PATH) as pdf:
        for page_1idx in range(FIRST_PAGE, LAST_PAGE + 1):
            page = pdf.pages[page_1idx - 1]
            tables = page.extract_tables()
            found = False
            for table in tables:
                if is_left_macro_table(table):
                    found = True
                    all_items.extend(extract_page(table, page_1idx))
            if not found:
                skipped_pages.append(page_1idx)

    print(f"Tong so dong thuc pham trich duoc: {len(all_items)}")
    print(f"So trang khong tim thay bang macro (trang phai/vitamin/bia nhom): {len(skipped_pages)}")
    print(f"Danh sach trang bo qua: {skipped_pages}")

    OUT_PATH.write_text(json.dumps(all_items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Da ghi {OUT_PATH}")


if __name__ == "__main__":
    main()
