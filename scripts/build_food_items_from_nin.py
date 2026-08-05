#!/usr/bin/env python3
"""Dựng BẢN NHÁP food_items từ dữ liệu NIN (ticket DAT-02).

⚠️ Đây là BẢN NHÁP để R2 kiểm, KHÔNG phải food_items.csv sản xuất. Khớp tên tự động
(token-subset) có thể sai (VD dạng khô/chế biến) → mỗi dòng có cột `match_confidence`
và `nin_name` để soát. Chỉ dòng đã được R2 xác nhận mới được đưa vào food_items.csv.

Nguồn: Viện Dinh dưỡng (NIN) — https://viendinhduong.vn. Purine để trống (NIN không có).

Dùng:
  python scripts/build_food_items_from_nin.py --out data/seeds/food_items.nin_draft.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from fetch_nin_foods import NUTRIENT_MAP, fetch_all  # type: ignore[import-not-found]

SEEDS = Path(__file__).resolve().parents[1] / "data" / "seeds"

# Ánh xạ tay tên template → mã NIN cho món khớp tự động không ra (đã soát bằng tay
# từ danh sách NIN — R2 xác nhận trước khi coi là chuẩn).
# LƯU Ý: khoá phải ở dạng đã chuẩn hoá (_norm: bỏ dấu, thường) để khớp lookup.
OVERRIDES: dict[str, str] = {
    "ghe": "8035",  # Cua ghẹ, tươi
    "dau cove": "4029",  # Đậu cô ve, quả, tươi
    "thanh long": "5044",  # Quả thanh long, tươi
    "sua bot nguyen kem": "10006",  # Sữa bột toàn phần
    "muoi an": "13005",  # Muối
    "mi an lien": "1043",  # Mỳ ăn liền, lúa mì (dạng khô)
    "thit bo than": "7003",  # Thịt bò, loại I, tươi
    "dau phu chien": "3027",  # Đậu phụ, nướng (proxy cho chiên)
}

# Ước tính món NẤU CHÍN từ nguyên liệu sống × hệ số nở khi nấu (OOV Estimator, CLN-07).
# → source=estimated, is_estimated=TRUE. Khoá ở dạng _norm. (mã NIN, hệ số, ghi chú)
ESTIMATES: dict[str, tuple[str, float, str]] = {
    "com te": ("1003", 1 / 2.6, "Cơm chín ước tính từ gạo tẻ sống (NIN 1003) × 1/2.6 (hệ số nở khi nấu)"),
    "xoi trang": ("1001", 1 / 1.9, "Xôi ước tính từ gạo nếp sống (NIN 1001) × 1/1.9 (nở ít hơn cơm)"),
    "chao trang": ("1003", 1 / 7.0, "Cháo trắng ước tính từ gạo tẻ sống (NIN 1003) × 1/7 (loãng)"),
}

# Điền tay các nguyên liệu nền NIN thiếu nhưng công thức món ăn cần (DAT-04).
# Khoá ở dạng _norm. Mỗi giá trị là (dict cột dinh dưỡng, source, source_ref, is_estimated).
MANUAL_FILL: dict[str, tuple[dict[str, float], str, str, str]] = {
    "muoi an": (
        {
            "kcal_100g": 0,
            "protein_g": 0,
            "carb_g": 0,
            "fat_g": 0,
            "fiber_g": 0,
            "na_mg": 38758,
            "k_mg": 8,
            "p_mg": 0,
            "sugar_g": 0,
        },
        "curated",
        "USDA FDC 'Salt, table' — Na 38758 mg/100 g (NaCl)",
        "FALSE",
    ),
    "banh pho tuoi": (
        {
            "kcal_100g": 110,
            "protein_g": 2.0,
            "carb_g": 25.0,
            "fat_g": 0.2,
            "fiber_g": 0.5,
            "na_mg": 5,
            "k_mg": 10,
            "p_mg": 30,
        },
        "estimated",
        "Ước tính bánh phở gạo tươi (tham chiếu USDA 'Rice noodles, cooked')",
        "TRUE",
    ),
    "bun tuoi": (
        {
            "kcal_100g": 110,
            "protein_g": 2.0,
            "carb_g": 25.0,
            "fat_g": 0.2,
            "fiber_g": 0.5,
            "na_mg": 5,
            "k_mg": 10,
            "p_mg": 30,
        },
        "estimated",
        "Ước tính bún gạo tươi (tham chiếu USDA 'Rice noodles, cooked')",
        "TRUE",
    ),
    # --- Gia vị mặn (trục chính bài toán muối) ---
    "mi chinh": (
        {
            "kcal_100g": 0,
            "protein_g": 0,
            "carb_g": 0,
            "fat_g": 0,
            "fiber_g": 0,
            "na_mg": 12280,
            "k_mg": 0,
            "p_mg": 0,
            "sugar_g": 0,
        },
        "curated",
        "Mì chính = MSG (NaC5H8NO4) — natri hoá học 12,28% khối lượng",
        "FALSE",
    ),
    "bot canh": (
        {
            "kcal_100g": 0,
            "protein_g": 0,
            "carb_g": 0,
            "fat_g": 0,
            "fiber_g": 0,
            "na_mg": 33000,
            "k_mg": 0,
            "p_mg": 0,
            "sugar_g": 0,
        },
        "estimated",
        "Ước tính bột canh (~85% muối + MSG) — Na ~33.000 mg/100 g; cần đối chiếu nhãn",
        "TRUE",
    ),
    "hat nem": (
        {
            "kcal_100g": 5,
            "protein_g": 1.0,
            "carb_g": 1.0,
            "fat_g": 0,
            "fiber_g": 0,
            "na_mg": 17000,
            "k_mg": 20,
            "p_mg": 10,
        },
        "estimated",
        "Ước tính hạt nêm (muối + MSG + chiết xuất) — Na ~17.000 mg/100 g; cần đối chiếu nhãn",
        "TRUE",
    ),
    "nuoc mam giam man": (
        {
            "kcal_100g": 20,
            "protein_g": 4.0,
            "carb_g": 2.0,
            "fat_g": 0,
            "fiber_g": 0,
            "na_mg": 4000,
            "k_mg": 150,
            "p_mg": 20,
        },
        "estimated",
        "Ước tính nước mắm giảm mặn (~1/2 nước mắm thường) — Na ~4.000 mg/100 g",
        "TRUE",
    ),
    "mam tom": (
        {
            "kcal_100g": 73,
            "protein_g": 14.8,
            "carb_g": 3.6,
            "fat_g": 1.5,
            "fiber_g": 0,
            "na_mg": 4054,
            "k_mg": 200,
            "p_mg": 100,
        },
        "estimated",
        "Na 4054 từ NIN 'Mắm tôm đặc' (mã 13011); macro ước tính từ mắm tôm đặc",
        "TRUE",
    ),
}

OUT_COLS = [
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
    "match_confidence",
    "nin_name",
]


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", text).strip()


def _tokens(text: str) -> set[str]:
    return set(_norm(text).split())


def _has_minerals(food: dict[str, Any]) -> bool:
    """NIN có đủ Na/K/P cho món này không? (nhiều entry NIN thiếu khoáng)."""
    have = {n["name_en"] for n in food.get("nutrition", []) if n.get("value") not in (None, "")}
    return {"Na", "K", "P"} <= have


def _match_one(name: str, foods: list[dict[str, Any]], exact_idx: dict[str, dict]) -> tuple[dict | None, str]:
    hit = exact_idx.get(_norm(name))
    if hit is not None:
        return hit, "exact"
    want_list = _norm(name).split()
    if not want_list:
        return None, "MISS"
    want = set(want_list)
    head = want_list[0]  # danh từ chính, VD "đường" trong "đường trắng"
    # token-subset + neo đầu: mọi token nằm trong tên NIN VÀ token đầu NIN trùng token
    # đầu template (tránh "Đường trắng" khớp nhầm "Sữa ... có đường").
    cands = [f for f in foods if want <= _tokens(f["name_vi"]) and _norm(f["name_vi"]).split()[:1] == [head]]
    # Ưu tiên entry ĐỦ khoáng chất (nhiều biến thể NIN thiếu Na/K/P), rồi tới tên ngắn nhất.
    cands.sort(key=lambda f: (not _has_minerals(f), len(_tokens(f["name_vi"]))))
    return (cands[0], "subset") if cands else (None, "MISS")


def match_food(
    template_name: str, aliases: str, foods: list[dict[str, Any]], exact_idx: dict[str, dict]
) -> tuple[dict | None, str]:
    """Khớp tên chính rồi tới từng alias (VD cá lóc → cá quả). Trả (món, độ tin cậy)."""
    hit, conf = _match_one(template_name, foods, exact_idx)
    if hit is not None:
        return hit, conf
    for alias in (a.strip() for a in (aliases or "").split("|") if a.strip()):
        hit, conf = _match_one(alias, foods, exact_idx)
        if hit is not None:
            return hit, f"alias-{conf}"
    return None, "MISS"


PROD_COLS = [c for c in OUT_COLS if c not in ("match_confidence", "nin_name")]


def build(draft_path: Path, prod_path: Path | None = None) -> None:
    foods = fetch_all()
    exact_idx = {_norm(f["name_vi"]): f for f in foods}
    code_idx = {f["code"]: f for f in foods}
    gi_by_id = {r["food_id"]: r for r in csv.DictReader(open(SEEDS / "gi_values.csv", encoding="utf-8"))}
    purine_by_id = {r["food_id"]: r for r in csv.DictReader(open(SEEDS / "purine_values.csv", encoding="utf-8"))}
    usda_path = SEEDS / "usda_values.csv"
    usda_by_id = (
        {r["food_id"]: r for r in csv.DictReader(open(usda_path, encoding="utf-8"))} if usda_path.exists() else {}
    )
    template = list(csv.DictReader(open(SEEDS / "food_items.template.csv", encoding="utf-8")))

    built: list[dict[str, Any]] = []
    filled = 0
    for row in template:
        out = {c: "" for c in OUT_COLS}
        out.update(
            {
                "id": row["id"],
                "name_vi": row["name_vi"],
                "aliases": row.get("aliases", ""),
                "category": row.get("category", ""),
                "contains_allergens": row.get("contains_allergens", ""),
                "is_estimated": "FALSE",
            }
        )
        manual = MANUAL_FILL.get(_norm(row["name_vi"]))
        if manual is not None:
            nut_m, src_m, ref_m, est_m = manual
            filled += 1
            out["source"], out["source_ref"], out["is_estimated"] = src_m, ref_m, est_m
            out["match_confidence"] = "manual"
            for col, val in nut_m.items():
                out[col] = val
            hit = None
        else:
            override_code = OVERRIDES.get(_norm(row["name_vi"]))
            if override_code is not None:
                hit, conf = code_idx.get(override_code), "override"
            else:
                hit, conf = match_food(row["name_vi"], row.get("aliases", ""), foods, exact_idx)
            out["match_confidence"] = conf
        if manual is None and hit is not None:
            out["nin_name"] = hit["name_vi"]
            nut = {
                NUTRIENT_MAP[n["name_en"]]: n["value"] for n in hit.get("nutrition", []) if n["name_en"] in NUTRIENT_MAP
            }
            nut["kcal_100g"] = hit.get("energy")
            # NIN không liệt kê xơ/carb cho thực phẩm động vật/dầu → ~0 (thịt/cá/trứng không có carb).
            nut.setdefault("fiber_g", 0)
            nut.setdefault("carb_g", 0)
            # NIN đôi khi báo sugar > carb (carb tính by-difference vs đường đo trực tiếp
            # lệch nhau) → bỏ sugar mâu thuẫn, giữ carb (bắt buộc). Không bịa số.
            s, c = nut.get("sugar_g"), nut.get("carb_g")
            if s not in (None, "") and c not in (None, "") and s > c:
                nut.pop("sugar_g", None)
            required = ["kcal_100g", "protein_g", "carb_g", "fat_g", "fiber_g", "na_mg", "k_mg", "p_mg"]
            if all(nut.get(col) not in (None, "") for col in required):
                filled += 1
                out["source"] = "NIN"
                out["source_ref"] = f"NIN Bảng TPTP VN (mã {hit['code']})"
                for col, val in nut.items():
                    out[col] = val
            else:
                # NIN thiếu khoáng chất bắt buộc (Na/K/P) → không điền dở dang, để R2 tra tay.
                out["match_confidence"] = f"{conf}-nin-thiếu-khoáng"

        # Món nấu chín không có trong NIN → ước tính từ nguyên liệu sống × hệ số nở.
        est = ESTIMATES.get(_norm(row["name_vi"]))
        if manual is None and hit is None and est is not None:
            raw_code, factor, note = est
            raw = code_idx.get(raw_code)
            if raw is not None:
                nut = {
                    NUTRIENT_MAP[n["name_en"]]: n["value"]
                    for n in raw.get("nutrition", [])
                    if n["name_en"] in NUTRIENT_MAP and n["value"] not in (None, "")
                }
                nut["kcal_100g"] = raw.get("energy")
                nut.setdefault("fiber_g", 0)
                required = ["kcal_100g", "protein_g", "carb_g", "fat_g", "fiber_g", "na_mg", "k_mg", "p_mg"]
                if all(nut.get(col) not in (None, "") for col in required):
                    filled += 1
                    out["source"] = "estimated"
                    out["source_ref"] = note
                    out["is_estimated"] = "TRUE"
                    out["match_confidence"] = "estimated"
                    out["nin_name"] = f"(ước tính từ {raw['name_vi']})"
                    for col, val in nut.items():
                        out[col] = round(float(val) * factor, 2)

        # Fallback USDA FoodData Central cho món NIN không lấp được (DAT-03).
        if not out["source"]:
            u = usda_by_id.get(row["id"])
            if u is not None:
                filled += 1
                out["source"] = "USDA"
                out["source_ref"] = u["source_ref"]
                out["match_confidence"] = "usda"
                out["nin_name"] = u.get("usda_name", "")
                for c in ("kcal_100g", "protein_g", "carb_g", "fat_g", "fiber_g", "sugar_g", "na_mg", "k_mg", "p_mg"):
                    if u.get(c) not in (None, ""):
                        out[c] = u[c]

        gi = gi_by_id.get(row["id"])
        if gi is not None:
            out["gi_index"] = gi["gi_index"]
            out["gi_source"] = gi["gi_source"]
            out["gi_source_ref"] = gi["gi_source_ref"]
        pur = purine_by_id.get(row["id"])
        if pur is not None:
            out["purine_mg"] = pur["purine_mg"]
            out["purine_source_ref"] = pur["purine_source_ref"]
        built.append(out)

    with open(draft_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_COLS)
        writer.writeheader()
        writer.writerows(built)
    print(f"Đã ghi {draft_path}: {len(built)} dòng, {filled} dòng có dữ liệu NIN.", file=sys.stderr)

    if prod_path is not None:
        with open(prod_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=PROD_COLS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(built)
        print(f"Đã ghi {prod_path} (schema sản xuất, {filled} dòng có dữ liệu).", file=sys.stderr)
    print("Dòng match_confidence='subset'/'MISS' cần R2 soát trước khi lên food_items.csv.", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=SEEDS / "food_items.nin_draft.csv")
    parser.add_argument("--production", type=Path, help="Cũng ghi food_items.csv schema sản xuất (bỏ cột review)")
    args = parser.parse_args()
    build(args.out, args.production)
    return 0


if __name__ == "__main__":
    sys.exit(main())
