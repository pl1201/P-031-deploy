#!/usr/bin/env python3
"""Lap cac truong NIN 2017 BO TRONG (chu yeu Na/K, it fat/fiber/P) bang cach
doi chieu sang USDA FoodData Central qua TEN TIENG ANH do chinh NIN cung cap.

Ticket: DAT-24 / DAT-13.

BOI CANH (da kiem chung, khong suy doan)
----------------------------------------
348/370 dong `food_items.csv` con bo trong deu la muc NIN 2017 DA BIET MA, bi
chan vi ban PDF goc khong phan tich mot vai truong. Da kiem chung tren PDF
(trang 24, ma 01012 "Banh my"): KHONG co token nao o toa do cot NA/K -> o do
that su trong trong bang goc, KHONG phai loi trich xuat.

=> Khong the lay tu NIN. Va KHONG duoc dien 0: banh my co Na ~490 mg/100g
(USDA), "trong" o day KHONG dong nghia "khong dang ke".

CACH LAM
--------
NIN 2017 tu cung cap `name_en` cho tung muc (VD 01012 -> "Bread, French style").
Dung chinh ten do doi chieu sang mo ta USDA (sr_legacy/foundation/survey) -
day la anh xa do NGUON GOC dua ra, khong phai do minh doan.

Chi nhan khop khi diem tuong dong du cao VA thuoc cung nhom thuc pham; moi
dong duoc lap deu bi danh dau:
    source        = "estimated"
    is_estimated  = TRUE
    source_ref    = ghi ro CA HAI nguon (macro tu NIN ma X; Na/K tu USDA fdc_id Y)
vi gia tri muon tu he thuc pham khac chi la XAP XI (RULE-2). UI phai hien
nhan "uoc tinh". R2 duyet lai truoc khi tin dung cho nguong lam sang.

Dong khong tim duoc khop dat nguong -> GIU NGUYEN trong, ghi vao file
*.unresolved.csv de nguoi sau biet da thu va vi sao bo.

Chay:
  python scripts/fill_nin_gaps_from_usda.py --pilot          # xem thu 30 cap khop
  python scripts/fill_nin_gaps_from_usda.py --apply          # ghi vao food_items.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

csv.field_size_limit(10**7)

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"
USDA = ROOT / "data" / "FoodData_Central_csv_2025-12-18" / "FoodData_Central_csv_2025-12-18"
NIN_JSON = ROOT / "scripts" / "nin2017_extracted.json"
CACHE = ROOT / "data" / "cache" / "usda_generic.json"

# Chi dung nhom generic; bo qua ~2 trieu dong branded_food (ten thuong mai,
# khong phai thuc pham co ban, gay khop nham nghiem trong).
GENERIC_TYPES = {"sr_legacy_food", "foundation_food", "survey_fndds_food"}

# Ma chat dinh duong USDA.
NUTRIENT_IDS = {"fat_g": 1004, "fiber_g": 1079, "p_mg": 1091, "k_mg": 1092, "na_mg": 1093}

FIELD_FROM_NIN = {
    "kcal_100g": "enerc_kcal",
    "protein_g": "procnt_g",
    "carb_g": "chocdf_g",
    "fat_g": "fat_g",
    "fiber_g": "fibc_g",
    "na_mg": "na_mg",
    "k_mg": "k_mg",
    "p_mg": "p_mg",
}

MIN_SCORE = 0.70   # duoi muc nay: bo han, khong dua ra ca de xuat
AUTO_SCORE = 0.90  # tu muc nay tro len moi TU DONG ap vao food_items.csv


# NIN va USDA viet khac nhau cung mot thu ("Arrow root" vs "Arrowroot").
COMPOUND_FIXES = {"arrow root": "arrowroot", "buck wheat": "buckwheat", "water melon": "watermelon"}


def _norm_en(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for src, dst in COMPOUND_FIXES.items():
        text = text.replace(src, dst)
    return text


# Tu bi loai khi so khop: chi la trang thai che bien/mo ta, khong phan biet
# duoc thuc pham nay voi thuc pham khac.
STOPWORDS = {
    "raw", "fresh", "cooked", "boiled", "nfs", "ns", "as", "to", "the", "and",
    "with", "without", "type", "style", "commercial", "prepared", "unprepared",
}


def _tokens(text: str) -> set[str]:
    return {t for t in _norm_en(text).split() if t not in STOPWORDS and len(t) > 2}


# Cac nhom tinh tu LOAI TRU NHAU. Neu ten NIN mang mot gia tri trong nhom va
# mo ta USDA mang gia tri KHAC cung nhom -> khac thuc pham, tu choi khop.
#
# Ly do bat buoc phai co: chi dua vao diem tuong dong chuoi, "Long trang trung
# vit" (Duck egg, white) khop nham "Duck egg, cooked" va "Dau ngo" (Corn oil)
# khop nham "Oil, olive" — sai hoan toan ve thanh phan, ma Na/K/P lai la
# nguong chan cung cho CKD/THA.
EXCLUSIVE_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"white", "yolk", "whole"}),
    frozenset({"raw", "cooked", "dried", "fried", "pickled", "boiled", "roasted", "smoked", "canned"}),
    frozenset({"corn", "olive", "peanut", "sesame", "soybean", "palm", "coconut", "sunflower", "cottonseed", "canola"}),
    frozenset({"skim", "nonfat", "lowfat", "whole"}),
    frozenset({"leaf", "leaves", "root", "seed", "flower", "stem", "fruit"}),
)


# Tu chi DANG che bien: neu mot ben co ma ben kia khong -> khac han thuc pham,
# du diem chuoi cao. VD "Chestnut, fresh" vs "Flour, chestnut" (hat de tuoi vs
# bot hat de: chat xo 2,3 vs 8,7 g/100g); "Chicken, thighs" vs "Chicken, skin";
# "Chicken, canned" vs "Soup, chicken, canned" (sup da pha loang).
FORM_TOKENS = frozenset({
    "flour", "powder", "skin", "soup", "stew", "salad", "substitute",
    "juice", "sauce", "paste", "chips", "rinds", "crepe", "candies", "bran",
})


def _conflicts(a: set[str], b: set[str]) -> bool:
    for group in EXCLUSIVE_GROUPS:
        ga, gb = a & group, b & group
        if ga and gb and not (ga & gb):
            return True
    return (a & FORM_TOKENS) != (b & FORM_TOKENS)


def score(nin_en: str, usda_desc: str) -> float:
    a, b = _tokens(nin_en), _tokens(usda_desc)
    if not a or not b:
        return 0.0
    # Kiem tra xung dot tren token THO (truoc khi bo stopword): "raw"/"cooked"/
    # "dried" vua nam trong STOPWORDS vua nam trong nhom loai tru — neu kiem tra
    # sau khi da bo stopword thi nhom do khong bao gio chay, va "Shrimp dried"
    # se khop duoc voi "Shrimp, raw" (natri lech hang chuc lan).
    if _conflicts(set(_norm_en(nin_en).split()), set(_norm_en(usda_desc).split())):
        return 0.0
    jaccard = len(a & b) / len(a | b)
    # Phai co it nhat 1 tu chung THAT — chan truong hop diem cao chi nho
    # chuoi ky tu giong nhau ("Arrow root" vs "Burdock root" khong duoc tinh
    # la khop chi vi cung co chu "root").
    if not (a & b):
        return 0.0
    # Bao phu phia NIN: bao nhieu phan y nghia cua ten NIN duoc USDA nhac lai.
    coverage = len(a & b) / len(a)
    ratio = SequenceMatcher(None, _norm_en(nin_en), _norm_en(usda_desc)).ratio()
    return 0.40 * jaccard + 0.40 * coverage + 0.20 * ratio


def build_usda_index() -> list[dict]:
    """Doc USDA bulk -> [{fdc_id, desc, <nutrients>}]. Cache lai vi file rat lon."""
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))

    print("Doc food.csv (2M dong, chi giu nhom generic)...")
    foods: dict[str, str] = {}
    with open(USDA / "food.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["data_type"] in GENERIC_TYPES:
                foods[row["fdc_id"]] = row["description"]
    print(f"  giu {len(foods)} thuc pham generic")

    wanted = {str(v): k for k, v in NUTRIENT_IDS.items()}
    values: dict[str, dict[str, float]] = {}
    print("Doc food_nutrient.csv (rat lon, mat mot luc)...")
    with open(USDA / "food_nutrient.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            fid = row["fdc_id"]
            if fid not in foods:
                continue
            col = wanted.get(row["nutrient_id"])
            if col is None:
                continue
            raw = (row.get("amount") or "").strip()
            if raw:
                try:
                    values.setdefault(fid, {})[col] = float(raw)
                except ValueError:
                    pass

    index = [{"fdc_id": fid, "desc": desc, **values.get(fid, {})} for fid, desc in foods.items() if fid in values]
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"  cache {len(index)} muc -> {CACHE}")
    return index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--min-score", type=float, default=MIN_SCORE, help="duoi nguong nay: bo han")
    ap.add_argument("--auto-score", type=float, default=AUTO_SCORE, help="tu dong ap; giua 2 nguong -> file cho R2 duyet")
    args = ap.parse_args()

    nin_by_code = {d["code"]: d for d in json.loads(NIN_JSON.read_text(encoding="utf-8"))}
    usda = build_usda_index()

    rows = list(csv.DictReader(open(SEEDS / "food_items.csv", encoding="utf-8", newline="")))
    targets = [
        r for r in rows
        if not (r.get("kcal_100g") or "").strip() and "CHUA DU LIEU" in (r.get("source_ref") or "")
    ]
    print(f"\nDong can lap: {len(targets)}")

    filled, unresolved, review = [], [], []
    for row in targets:
        m = re.search(r"ma (\d+)", row.get("source_ref") or "")
        nin = nin_by_code.get(m.group(1)) if m else None
        if nin is None:
            unresolved.append({"id": row["id"], "name_vi": row["name_vi"], "reason": "khong tra duoc ma NIN", "detail": ""})
            continue

        missing = [f for f, src in FIELD_FROM_NIN.items() if nin.get(src) is None]
        name_en = (nin.get("name_en") or "").strip()
        if not name_en:
            unresolved.append({"id": row["id"], "name_vi": row["name_vi"], "reason": "NIN khong co name_en", "detail": ""})
            continue

        best = max(usda, key=lambda u: score(name_en, u["desc"]))
        best_score = score(name_en, best["desc"])
        if best_score < args.auto_score:
            # Vung "co ve khop nhung khong chac" -> KHONG tu dong ap, day sang
            # file cho R2 duyet tay. Ly do bat buoc phai co vung nay: "Mam tom
            # loang" (Shrimp sauce) khop 0.80 vao "Shrimp with lobster sauce"
            # (mot mon Hoa) — natri 1031 mg/100g trong khi mam tom that cao hon
            # nhieu lan. Sai kieu nay di thang vao nguong chan cung cua THA/CKD.
            if best_score >= args.min_score and not any(best.get(f) is None for f in missing):
                review.append({
                    "id": row["id"], "name_vi": row["name_vi"], "name_en": name_en,
                    "usda_desc": best["desc"], "fdc_id": best["fdc_id"],
                    "score": f"{best_score:.2f}", "truong_can_lap": ", ".join(missing),
                    "gia_tri_de_xuat": " ".join(f"{f}={best[f]:g}" for f in missing),
                })
                continue
            unresolved.append({
                "id": row["id"], "name_vi": row["name_vi"], "reason": "khong khop du nguong",
                "detail": f"en='{name_en}' gan nhat='{best['desc']}' score={best_score:.2f}",
            })
            continue
        if any(best.get(f) is None for f in missing):
            unresolved.append({
                "id": row["id"], "name_vi": row["name_vi"], "reason": "USDA cung thieu truong can lap",
                "detail": f"can {missing}, USDA co {[k for k in NUTRIENT_IDS if best.get(k) is not None]}",
            })
            continue

        for field, nin_key in FIELD_FROM_NIN.items():
            row[field] = f"{nin[nin_key]:g}" if nin.get(nin_key) is not None else f"{best[field]:g}"
        row["source"] = "estimated"
        row["is_estimated"] = "TRUE"
        row["source_ref"] = (
            f"NIN 2017 mã {nin['code']} (năng lượng/đa chất); "
            f"{', '.join(missing)} lấy từ USDA FDC #{best['fdc_id']} '{best['desc']}' "
            f"do NIN 2017 không phân tích các trường này — khớp theo name_en NIN "
            f"'{name_en}', score={best_score:.2f}. ƯỚC TÍNH, R2 cần duyệt."
        )
        filled.append((row, name_en, best, best_score, missing))

    print(f"Tu dong lap (score >= {args.auto_score}) : {len(filled)}")
    print(f"Cho R2 duyet tay ({args.min_score}-{args.auto_score}) : {len(review)}")
    print(f"Bo han (khong du can cu)             : {len(unresolved)}")

    if args.pilot:
        print("\n--- 30 cap khop dau tien ---")
        for row, en, best, sc, missing in filled[:30]:
            vals = " ".join(f"{f}={row[f]}" for f in missing)
            print(f"  {sc:.2f} {row['name_vi']:28s} | {en:38s} -> {best['desc'][:46]:46s} | {vals}")
        print("\n--- 15 dong bo lai ---")
        for u in unresolved[:15]:
            print(f"  {u['name_vi'][:26]:26s} {u['reason']:26s} {u['detail'][:70]}")
        return

    if not args.apply:
        print("\n(chua --apply nen khong ghi gi)")
        return

    header = list(rows[0].keys())
    with open(SEEDS / "food_items.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)

    review_path = SEEDS / "food_items.nin_gaps_can_R2_duyet.csv"
    with open(review_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name_vi", "name_en", "usda_desc", "fdc_id", "score", "truong_can_lap", "gia_tri_de_xuat"])
        w.writeheader()
        w.writerows(review)

    unresolved_path = SEEDS / "food_items.nin_gaps_unresolved.csv"
    with open(unresolved_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name_vi", "reason", "detail"])
        w.writeheader()
        w.writerows(unresolved)
    print(f"\nDa ghi food_items.csv (+{len(filled)} dong co so lieu) va {unresolved_path.name}")


if __name__ == "__main__":
    main()
