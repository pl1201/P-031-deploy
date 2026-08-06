#!/usr/bin/env python3
"""Trích xuất TOÀN BỘ bảng chính "Bảng thành phần thực phẩm Việt Nam 2017"
(304 trang, `data/Bang-thanh-phan-dinh-duong-Thuc-pham-VN-2017-27-4-17.pdf`,
không commit vào git — xem `data/README.md`) thành các dòng mới cho
`food_items.csv`.

Ticket: DAT-12. LLM: NO — thuần trích xuất toạ độ từ PDF chính thức của Viện
Dinh dưỡng, không suy đoán số liệu.

Phương pháp (đã xác nhận khớp 100% với dòng đã có: mã 01003 "Gạo tẻ giã" ra
đúng kcal=347/protein=8.1/carb=75.7/fat=1.3/fiber=0.7/na=5/k=202/p=108, khớp
dòng id=1 hiện có trong food_items.csv):

1. Mỗi trang lặp lại header tag-name (EDIBLE/ENERC/WATER/PROCNT/FAT/CHOCDF/
   FIBC/ASH/CA/P/FE/ZN/NA/K/MG...) ở toạ độ x cố định — dùng để neo cột.
2. Mỗi dòng thực phẩm có "Code" (5 chữ số, VD 01003) ở x≈65-100. Các từ khác
   cùng `top` (cùng dòng, dung sai ±2pt) được gán vào đúng cột theo x gần
   header tag-name nhất.
3. Tên tiếng Việt: các từ trong khoảng x∈[95, 270] trên CÙNG dòng với Code
   (một số tên dài xuống dòng tiếp theo — bản này CHƯA ráp phần xuống dòng,
   chấp nhận tên có thể cụt phần mô tả phụ; số liệu dinh dưỡng không bị ảnh
   hưởng vì luôn nằm trên dòng có Code).
4. **Bỏ qua mã đã có sẵn trong `food_items.csv`** (so khớp số mã NIN đã ghi
   trong `source_ref` hiện có, bỏ số 0 đứng đầu) — không tạo dòng trùng/xung
   đột với dữ liệu đã được người trước xác minh.
5. PDF có hiện tượng lặp trang (2 trang liên tiếp cùng nội dung, đúng như
   `data/README.md` mô tả "kéo dài hết 2 trang giấy để tiện tra cứu") — dedupe
   theo mã, giữ lần xuất hiện đầu.

Chạy: python scripts/extract_nin2017_bulk.py [--out PATH]
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "data" / "Bang-thanh-phan-dinh-duong-Thuc-pham-VN-2017-27-4-17.pdf"
SEEDS = ROOT / "data" / "seeds"
FOOD_ITEMS_CSV = SEEDS / "food_items.csv"

# Cột cần cho food_items.csv, theo tag name NIN 2017 (đã xác nhận toạ độ qua
# header lặp mỗi trang). Thứ tự khớp thứ tự xuất hiện trái→phải trên trang.
TAG_ORDER = [
    "EDIBLE",
    "ENERC",
    "WATER",
    "PROCNT",
    "FAT",
    "CHOCDF",
    "FIBC",
    "ASH",
    "CA",
    "P",
    "FE",
    "ZN",
    "NA",
    "K",
]
NEEDED_TAGS = {"ENERC", "PROCNT", "FAT", "CHOCDF", "FIBC", "NA", "K", "P"}

RANGES = {
    "kcal_100g": (0, 920),
    "protein_g": (0, 90),
    "carb_g": (0, 100),
    "fat_g": (0, 100),
    "fiber_g": (0, 80),
    "na_mg": (0, 40000),
    "k_mg": (0, 5000),
    "p_mg": (0, 2000),
}

CSV_HEADER = [
    "id",
    "name_vi",
    "aliases",
    "category",
    "kcal_100g",
    "protein_g",
    "carb_g",
    "fat_g",
    "fiber_g",
    "sugar_g",
    "na_mg",
    "k_mg",
    "p_mg",
    "purine_mg",
    "purine_source_ref",
    "gi_index",
    "gi_source",
    "gi_source_ref",
    "contains_allergens",
    "source",
    "source_ref",
    "is_estimated",
]

_NUM_RE = re.compile(r"^-?\d+([.,]\d+)?$")
_CODE_RE = re.compile(r"^\d{5}$")


def _existing_codes() -> set[str]:
    """Mã NIN (không số 0 đầu) đã dùng trong food_items.csv hiện có."""
    codes: set[str] = set()
    with open(FOOD_ITEMS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ref = row.get("source_ref") or ""
            for m in re.finditer(r"m[aã]\s*0*(\d{3,6})", ref, flags=re.IGNORECASE):
                codes.add(m.group(1))
    return codes


def _find_tag_anchors(words: list[dict]) -> dict[str, float]:
    """x0 của từng tag-name trên trang (header lặp mỗi trang, y~60-120)."""
    anchors: dict[str, float] = {}
    for w in words:
        if 55 < w["top"] < 130 and w["text"] in TAG_ORDER and w["text"] not in anchors:
            anchors[w["text"]] = w["x0"]
    return anchors


def _max_id(existing_max: int) -> int:
    return existing_max


def extract_rows() -> list[dict[str, str]]:
    import pdfplumber

    existing_codes = _existing_codes()
    print(f"Mã NIN đã có sẵn trong food_items.csv: {len(existing_codes)}")

    rows_by_code: dict[str, dict[str, str]] = {}

    with pdfplumber.open(PDF_PATH) as pdf:
        n_pages = len(pdf.pages)
        for page_idx in range(n_pages):
            page = pdf.pages[page_idx]
            words = page.extract_words()
            if not words:
                continue
            anchors = _find_tag_anchors(words)
            if not NEEDED_TAGS.issubset(anchors):
                continue  # trang không phải bảng dữ liệu (bìa, mục lục, phụ lục...)

            # Mỗi dòng thực phẩm neo bởi ô Code (x0<100, 5 chữ số). Tên món và
            # cột số liệu KHÔNG cùng `top` chính xác (lệch tới ~6pt — đã xác
            # nhận thực nghiệm trên mã 01002: code/số ở top=233.3, tên ở
            # top=227.9) — gán mỗi từ vào Code GẦN NHẤT theo top thay vì bin
            # cứng theo top, để không bỏ sót tên hay số liệu lệch dòng.
            body_words = [w for w in words if w["top"] > 165]
            code_words = [w for w in body_words if _CODE_RE.match(w["text"]) and w["x0"] < 100]
            if not code_words:
                continue
            code_tops = sorted(w["top"] for w in code_words)

            def _nearest_code_top(word_top: float) -> float | None:
                best, best_dist = None, 13.0  # nửa khoảng cách dòng (~25.6pt/dòng)
                for ct in code_tops:
                    d = abs(word_top - ct)
                    if d < best_dist:
                        best, best_dist = ct, d
                return best

            rows_words: dict[float, list[dict]] = {ct: [] for ct in code_tops}
            for w in body_words:
                nearest = _nearest_code_top(w["top"])
                if nearest is not None:
                    rows_words[nearest].append(w)

            for _top, line_words in rows_words.items():
                code_word = next((w for w in line_words if _CODE_RE.match(w["text"]) and w["x0"] < 100), None)
                if code_word is None:
                    continue
                code = code_word["text"]
                code_norm = code.lstrip("0") or "0"
                if code_norm in existing_codes or code in rows_by_code:
                    continue

                # Cột tên tiếng Việt kết thúc trước cột tên tiếng Anh (x≈174, xác
                # nhận thực nghiệm) — thu hẹp biên để không lẫn từ tiếng Anh vào
                # name_vi. Sắp theo (top, x0) để câu chữ đọc tự nhiên khi tên dài
                # xuống dòng.
                name_words = sorted(
                    (w for w in line_words if 95 <= w["x0"] < 172), key=lambda w: (round(w["top"]), w["x0"])
                )
                name_vi = " ".join(w["text"] for w in name_words).strip()
                if not name_vi:
                    continue

                values: dict[str, float] = {}
                for tag in NEEDED_TAGS:
                    anchor_x = anchors[tag]
                    # Từ số gần anchor nhất trong dòng (dung sai 25pt hai bên)
                    best = None
                    best_dist = 26.0
                    for w in line_words:
                        if not _NUM_RE.match(w["text"]):
                            continue
                        dist = abs(w["x0"] - anchor_x)
                        if dist < best_dist:
                            best = w
                            best_dist = dist
                    if best is not None:
                        values[tag] = float(best["text"].replace(",", "."))

                if not NEEDED_TAGS.issubset(values):
                    continue  # thiếu cột bắt buộc — bỏ, không suy đoán (RULE-2)

                mapped = {
                    "kcal_100g": values["ENERC"],
                    "protein_g": values["PROCNT"],
                    "fat_g": values["FAT"],
                    "carb_g": values["CHOCDF"],
                    "fiber_g": values["FIBC"],
                    "na_mg": values["NA"],
                    "k_mg": values["K"],
                    "p_mg": values["P"],
                }
                if any(not (lo <= mapped[f] <= hi) for f, (lo, hi) in RANGES.items()):
                    continue
                macro = mapped["protein_g"] + mapped["carb_g"] + mapped["fat_g"] + mapped["fiber_g"]
                if macro > 105:
                    continue

                rows_by_code[code] = {
                    "name_vi": name_vi,
                    "kcal_100g": f"{mapped['kcal_100g']:g}",
                    "protein_g": f"{mapped['protein_g']:g}",
                    "carb_g": f"{mapped['carb_g']:g}",
                    "fat_g": f"{mapped['fat_g']:g}",
                    "fiber_g": f"{mapped['fiber_g']:g}",
                    "na_mg": f"{mapped['na_mg']:g}",
                    "k_mg": f"{mapped['k_mg']:g}",
                    "p_mg": f"{mapped['p_mg']:g}",
                    "code": code,
                    "page": str(page_idx + 1),
                }
            if page_idx % 40 == 0:
                print(f"  ...trang {page_idx}/{n_pages}, đã thu {len(rows_by_code)} mã")

    print(f"Tổng mã mới thu được (đã loại trùng với dữ liệu có sẵn): {len(rows_by_code)}")
    return list(rows_by_code.values())


def to_csv_rows(raw_rows: list[dict[str, str]], start_id: int) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    next_id = start_id
    seen_names: set[str] = set()
    for r in raw_rows:
        name_key = r["name_vi"].strip().lower()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)
        out.append(
            {
                "id": str(next_id),
                "name_vi": r["name_vi"],
                "aliases": "",
                "category": "",
                "kcal_100g": r["kcal_100g"],
                "protein_g": r["protein_g"],
                "carb_g": r["carb_g"],
                "fat_g": r["fat_g"],
                "fiber_g": r["fiber_g"],
                "sugar_g": "",
                "na_mg": r["na_mg"],
                "k_mg": r["k_mg"],
                "p_mg": r["p_mg"],
                "purine_mg": "",
                "purine_source_ref": "",
                "gi_index": "",
                "gi_source": "",
                "gi_source_ref": "",
                "contains_allergens": "",
                "source": "NIN",
                "source_ref": f"Bảng TPTP VN 2017, mã {r['code']}, tr.{r['page']}",
                "is_estimated": "FALSE",
            }
        )
        next_id += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=SEEDS / "food_items.nin2017_bulk.csv")
    ap.add_argument("--start-id", type=int, default=2000, help="ID bắt đầu cấp cho dòng mới (tránh trùng fdc_id USDA)")
    args = ap.parse_args()

    raw_rows = extract_rows()
    csv_rows = to_csv_rows(raw_rows, args.start_id)
    print(f"Dòng sau khi loại trùng tên: {len(csv_rows)}")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Đã ghi {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
