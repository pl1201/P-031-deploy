#!/usr/bin/env python3
"""Quet TOAN BO "Bang thanh phan thuc pham Viet Nam 2017" (304 trang PDF,
`data/Bang-thanh-phan-dinh-duong-Thuc-pham-VN-2017-27-4-17.pdf`) thanh 1
bang tra cuu day du theo ten (KHONG loc theo ma da co trong food_items.csv
nhu `extract_nin2017_bulk.py`) - dung lam nguon doi chieu cho DAT-13 §2.1
(lap Na/K/P cho "Bang TP co phospho") va §2.2 (food_items.template.csv).

Tai su dung logic neo cot toa do da xac nhan dung 100% trong
`extract_nin2017_bulk.py` (khop mo 01003 "Gao te gia"). Khong loc trung
ma, chi dedupe theo ma NIN de giu moi ma 1 lan (giu lan xuat hien dau).

Chay: python scripts/build_nin2017_full_index.py
(uoc tinh ~40 phut do phai doc toan bo 304 trang PDF bang pdfplumber)
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "data" / "Bang-thanh-phan-dinh-duong-Thuc-pham-VN-2017-27-4-17.pdf"
OUT = ROOT / "data" / "seeds" / "nin2017_full_index.csv"

TAG_ORDER = ["EDIBLE", "ENERC", "WATER", "PROCNT", "FAT", "CHOCDF", "FIBC", "ASH", "CA", "P", "FE", "ZN", "NA", "K"]
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

_NUM_RE = re.compile(r"^-?\d+([.,]\d+)?$")
_CODE_RE = re.compile(r"^\d{5}$")


def _find_tag_anchors(words: list[dict]) -> dict[str, float]:
    anchors: dict[str, float] = {}
    for w in words:
        if 55 < w["top"] < 130 and w["text"] in TAG_ORDER and w["text"] not in anchors:
            anchors[w["text"]] = w["x0"]
    return anchors


def extract_rows() -> list[dict[str, str]]:
    import pdfplumber

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
                continue

            body_words = [w for w in words if w["top"] > 165]
            code_words = [w for w in body_words if _CODE_RE.match(w["text"]) and w["x0"] < 100]
            if not code_words:
                continue
            code_tops = sorted(w["top"] for w in code_words)

            def _nearest_code_top(word_top: float) -> float | None:
                best, best_dist = None, 13.0
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
                if code in rows_by_code:
                    continue

                name_words = sorted(
                    (w for w in line_words if 95 <= w["x0"] < 172), key=lambda w: (round(w["top"]), w["x0"])
                )
                name_vi = " ".join(w["text"] for w in name_words).strip()
                if not name_vi:
                    continue

                values: dict[str, float] = {}
                for tag in NEEDED_TAGS:
                    anchor_x = anchors[tag]
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
                    continue

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
                    "code": code,
                    "name_vi": name_vi,
                    "page": str(page_idx + 1),
                    "kcal_100g": f"{mapped['kcal_100g']:g}",
                    "protein_g": f"{mapped['protein_g']:g}",
                    "carb_g": f"{mapped['carb_g']:g}",
                    "fat_g": f"{mapped['fat_g']:g}",
                    "fiber_g": f"{mapped['fiber_g']:g}",
                    "na_mg": f"{mapped['na_mg']:g}",
                    "k_mg": f"{mapped['k_mg']:g}",
                    "p_mg": f"{mapped['p_mg']:g}",
                }
            if page_idx % 40 == 0:
                print(f"  ...trang {page_idx}/{n_pages}, da thu {len(rows_by_code)} ma")

    print(f"Tong ma thu duoc (toan bo, khong loc): {len(rows_by_code)}")
    return list(rows_by_code.values())


def main() -> int:
    rows = extract_rows()
    header = [
        "code",
        "name_vi",
        "page",
        "kcal_100g",
        "protein_g",
        "carb_g",
        "fat_g",
        "fiber_g",
        "na_mg",
        "k_mg",
        "p_mg",
    ]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"Da ghi {OUT} ({len(rows)} dong)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
