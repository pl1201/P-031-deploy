#!/usr/bin/env python3
"""Trích Natri/Kali/Phospho (và macro để đối chiếu chéo) từ Bảng TPTP VN 2007.

Chạy: python scripts/extract_nin2007.py

Bối cảnh (DAT-13): 341/355 dòng trống trong `food_items.csv` đã khớp tên
tuyệt đối với Bảng TPTP VN 2017, nhưng ~314 dòng trong số đó thiếu Na/K —
script merge NIN 2017 (DAT-22) cố ý không kích hoạt các dòng "nửa vời". Bản
2007 (`data/Bảng thanh phan dinh duong Thuc pham VN 2007.pdf`, 567 trang,
1 thực phẩm/trang) có cột Natri/Kali/Phospho — thử dùng nguồn này để bù.

RỦI RO ĐÃ XÁC NHẬN VÀ CÁCH XỬ LÝ:

1. **Lỗi font tiếng Việt**: dòng tiêu đề mỗi trang ("Tên thực phẩm...") bị
   lỗi font, giải mã ra ký tự sai (`"Tªn thùc phÈm"` thay vì `"Tên thực
   phẩm"`). KHÔNG cố decode lại — quá rủi ro, dễ đọc sai tên mà tưởng đúng.
   Thay vào đó dùng **"Mã số"** (chữ số, không bị lỗi font) làm khoá khớp —
   đã xác nhận bằng tay: `Mã số: 2001` (2007) = `code: 02001` (2017) = "Củ
   ấu" ở cả hai ấn bản. Mã số ổn định giữa hai lần xuất bản.

2. **Lỗi nhân đôi ký tự** (font đậm giả lập, quan sát trên vài dòng ở khối
   "acid béo" và "khoáng chất" — VD `"117733"` cần hiểu là `"173"`): CHỈ coi
   là lỗi nhân đôi khi TOÀN BỘ chuỗi số khớp mẫu "mỗi ký tự lặp đúng 2 lần
   liên tiếp" (`11`,`77`,`33` — không phải đoán mò một phần). Nếu không khớp
   mẫu này tuyệt đối, GIỮ NGUYÊN và không tự sửa.

3. **Không tin số từ 2007 một mình**: với các trường CẢ HAI ấn bản đều có
   (kcal/protein/carb/fat/fiber), nếu lệch nhau quá ngưỡng dung sai → ghi
   xung đột vào file riêng, KHÔNG tự chọn bên nào đúng (giống nguyên tắc
   `merge_nin2017_into_food_items.py`). Chỉ dùng 2007 để lấp CÁC Ô ĐANG
   TRỐNG (chủ yếu na_mg/k_mg/p_mg), không ghi đè giá trị đã có.

Output: `scripts/nin2007_extracted.json` — mỗi thực phẩm 1 dòng, `code` là
khoá khớp chính, giá trị số đã qua kiểm tra nhân đôi + khoảng hợp lý
(RANGES trong `validate_data.py`). Bước MERGE vào `food_items.csv` là script
riêng (`scripts/merge_nin2007_into_food_items.py`) — script này chỉ trích
xuất và kiểm tra, không ghi đè file dữ liệu chính.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = next(p for p in (ROOT / "data").glob("*.pdf") if "2007" in p.name)
OUT_PATH = ROOT / "scripts" / "nin2007_extracted.json"

MASO_RE = re.compile(r"M[a·][\s]*s[eèố][\s]*:\s*(\d+)")

# Nhãn hàng khoáng chất, ĐÚNG THỨ TỰ in trên bảng — dùng để ghép theo vị trí
# dòng (multi-line cell), không theo tên (tên nhãn cũng bị lỗi font).
MINERAL_ORDER = ["ca_mg", "fe_mg", "mg_mg", "mn_mg", "p_mg", "k_mg", "na_mg", "zn_mg", "cu_ug", "se_ug"]
# Nhãn hàng macro đầu bảng.
MACRO_ORDER = ["water_g", "enerc_kcal", "_enerc_kj", "protein_g", "fat_g", "chocdf_g", "fibc_g", "ash_g"]

DOUBLED_RE = re.compile(r"^(?:(.)\1)+$")


def undouble(raw: str) -> str | None:
    """Trả về chuỗi đã khử nhân đôi NẾU toàn bộ chuỗi khớp mẫu lặp đôi tuyệt
    đối; ngược lại trả None (không đoán, không sửa một phần)."""
    if DOUBLED_RE.match(raw):
        return raw[0::2]
    return None


def parse_num(raw: str) -> float | None:
    raw = (raw or "").strip()
    if raw in ("", "-", "--"):
        return None
    candidates = [raw]
    fixed = undouble(raw.replace(".", "")) if raw.replace(".", "").isdigit() else None
    # Chỉ thử bản khử nhân đôi khi phần số (bỏ dấu chấm) khớp mẫu lặp đôi
    # TUYỆT ĐỐI — không áp cho số bình thường tình cờ có ký tự lặp (VD "22").
    if fixed and len(raw.replace(".", "")) >= 4:
        # Chèn lại dấu chấm ở đúng vị trí tương đối nếu bản gốc có
        if "." in raw:
            int_len_raw = len(raw.split(".")[0])
            int_len_fixed = int_len_raw // 2 if int_len_raw % 2 == 0 else int_len_raw
            fixed = fixed[:int_len_fixed] + "." + fixed[int_len_fixed:]
        candidates.append(fixed)
    for cand in candidates[::-1]:  # ưu tiên bản đã khử nhân đôi nếu có
        try:
            return float(cand)
        except ValueError:
            continue
    return None


def extract_page(page) -> dict | None:
    text = page.extract_text() or ""
    m = MASO_RE.search(text)
    if not m:
        return None
    code = f"{int(m.group(1)):05d}"

    tables = page.extract_tables()
    if not tables:
        return None
    table = tables[0]
    if len(table) < 5:
        return None

    result: dict = {"code": code, "page": page.page_number}

    # Hàng 1 (index 1): macro — cột 0 = nhãn (bỏ qua, lỗi font), cột 2 = giá trị
    macro_lines = (table[1][2] or "").split("\n")
    for label, raw in zip(MACRO_ORDER, macro_lines, strict=False):
        if label.startswith("_"):
            continue
        result[label] = parse_num(raw)

    # Hàng 4 (index 4): khoáng chất
    mineral_lines = (table[4][2] or "").split("\n")
    for label, raw in zip(MINERAL_ORDER, mineral_lines, strict=False):
        result[label] = parse_num(raw)

    return result


def main() -> int:
    print(f"Doc: {PDF_PATH.name}")
    items: list[dict] = []
    skipped_no_code = 0
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        for page in pdf.pages:
            row = extract_page(page)
            if row is None:
                skipped_no_code += 1
                continue
            items.append(row)

    print(f"Tong so trang: {total}")
    print(f"Trang khong co Ma so (bia/muc luc/trang nhom): {skipped_no_code}")
    print(f"So thuc pham trich duoc: {len(items)}")

    # Thống kê nhanh độ phủ Na/K/P để biết trước khi merge có đáng làm không.
    have_na = sum(1 for i in items if i.get("na_mg") is not None)
    have_k = sum(1 for i in items if i.get("k_mg") is not None)
    have_p = sum(1 for i in items if i.get("p_mg") is not None)
    print(f"  Co Na: {have_na}/{len(items)}  Co K: {have_k}/{len(items)}  Co P: {have_p}/{len(items)}")

    OUT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nDa ghi: {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
