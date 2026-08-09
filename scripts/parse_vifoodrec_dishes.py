#!/usr/bin/env python3
"""Trich ten mon + nguyen lieu (gram that) tu dataset ViFoodRec -> dishes/dish_ingredients.

Ticket: DAT-26. Hung da duyet (2026-08-09): "neu la mon an thi khong can ra
soat qua chat... nhung can chuan hoa de phu hop".

CHI DUNG TEN MON + DANH SACH NGUYEN LIEU (VAN BAN). KHONG DUNG SO DINH DUONG
CUA VIFOODREC.
-----------------------------------------------------------------------------
Cot calories/fat/fiber/sugar/protein cua ViFoodRec la SO TONG DA SCRAPE SAN
tu trang web mon an — khong co nguon/khong tinh duoc tu nguyen lieu, vi pham
RULE-1 (LLM/nguon ngoai khong duoc tu sinh so dinh duong) va RULE-2 (moi so
phai co source/source_ref that). Script nay CHI doc `dish_name` + `ingredients`
(van ban tho) roi tu parse ra gram that + khop food_id trong food_items.csv,
dung y het co che da kiem chung o scripts/crawl_mnmn_dishes.py (DAT-24). Dinh
duong cuoi cung LUON duoc SQL tinh tu food_items.csv, khong bao gio lay tu
ViFoodRec.

GIAY PHEP — CHUA RO RANG, CAN R2/PHAP LY XAC NHAN
--------------------------------------------------
Repo goc (github.com/QuocAn55/DS300, ten day du
"A-New-Dataset-and-Empirical-Evaluation-for-Vietnamese-Food-Recommendation-System")
KHONG CO file LICENSE (license=null qua GitHub API, kiem tra 2026-08-09).
Paper PACLIC 2024 chi ghi "publicly available for free access by the
research community" trong van ban, khong phai license chinh thuc. Hung da
chap nhan dung cho muc dich phat trien/nghien cuu noi bo voi dieu kien nay
duoc ghi lai minh bach; MOI dish/note sinh ra deu neu ro nguon + tinh trang
license chua xac nhan de R2 / nguoi phu trach phap ly ra soat truoc khi dua
vao san pham that (deploy Render/Vercel).

File nguon `data/cache/vifoodrec/foods.csv` (7.3MB, tai tu
Data/Clean Dataset/foods.csv cua repo tren) CHI luu trong data/cache/ (da
gitignore) — KHONG commit vao repo, tranh phat tan lai toan bo dataset chua
ro license. Chi cac dish_id/ten mon/gram da chuan hoa (san pham phai sinh,
khong phai ban sao dataset goc) duoc ghi vao data/seeds/.

Chay:
  python scripts/parse_vifoodrec_dishes.py --limit 200 --pilot   # do ty le khop
  python scripts/parse_vifoodrec_dishes.py --limit 4000          # chay that
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"
SRC_CSV = ROOT / "data" / "cache" / "vifoodrec" / "foods.csv"

# Giong het mnmn (DAT-24): chi don vi khoi luong/the tich quy doi duoc that.
UNIT_TO_G: dict[str, float] = {"g": 1.0, "gr": 1.0, "gam": 1.0, "kg": 1000.0, "ml": 1.0, "l": 1000.0}

QTY_RE = re.compile(
    r"(?P<qty>\d+(?:[.,]\d+)?)\s*(?P<unit>kg|gr|gam|g|ml|l)\b",
    re.IGNORECASE,
)

# Danh sach goc tu crawl_mnmn_dishes.py — chi dung PREFIX-match (khong bat
# buoc khop tron ven ca cau) vi cau ViFoodRec hay co hau to lom xom
# ("dau me den", "bot ngot AJI-NO-MOTO"...). Nguyen lieu khop seasoning
# KHONG bi tinh la "unparsed_main_ingredient" (khong lam mon bi loai), nhung
# cung KHONG bao gio duoc cong gram (vi von khong co gram) — an toan ca 2 chieu.
SEASONING_ROOTS = (
    "muối", "đường", "tiêu", "dầu ăn", "nước mắm", "hạt nêm", "bột ngọt",
    "gia vị", "tương ớt", "ớt", "tỏi", "hành", "bột canh", "giấm", "chanh",
    "nước tương", "dầu mè", "mè", "rau thơm", "ngò", "hành lá", "dầu hào",
    "ăn kèm",
)

DISH_HEADER = ["dish_id", "name_vi", "region", "serving_g", "verified_by", "note"]
ING_HEADER = ["dish_id", "food_id", "grams", "note"]
REJECT_HEADER = ["vifoodrec_food_id", "name_vi", "reason", "detail"]

LICENSE_NOTE = (
    "Nguon: ViFoodRec (github.com/QuocAn55/DS300, PACLIC 2024, ViFoodRec food_id={vfid}). "
    "CHUA CO LICENSE CHINH THUC tren repo goc (kiem tra 2026-08-09) — CHI dung ten mon + "
    "danh sach nguyen lieu (van ban), R2/phap ly CAN XAC NHAN truoc khi dung cho san pham "
    "that. Gram tu parse tu van ban nguyen lieu goc, KHONG lay so dinh duong cua ViFoodRec "
    "(RULE-1/RULE-2). R2 CAN DUYET gram truoc khi dung cho benh nhan."
)


def _norm(name: str) -> str:
    name = unicodedata.normalize("NFC", str(name)).strip().lower()
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"[^\w\sÀ-ỹ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _is_seasoning(name: str) -> bool:
    n = _norm(name)
    return any(n == root or n.startswith(root + " ") for root in SEASONING_ROOTS)


@dataclass
class Ingredient:
    raw: str
    name: str = ""
    grams: float | None = None
    food_id: int | None = None


@dataclass
class Dish:
    vifoodrec_id: str
    name_vi: str
    ingredients: list[Ingredient] = field(default_factory=list)


# --------------------------------------------------------------------------
# Buoc 1 — tach chuoi nguyen lieu tho thanh tung nguyen lieu rieng
# --------------------------------------------------------------------------
def split_ingredients(raw: str) -> list[str]:
    """ViFoodRec khong co JSON-LD, nguyen lieu la 1 chuoi ngan cach bang dau ','.

    Hai dang gap trong du lieu:
      1. Co dau ':' — "Ten: dinh luong, ghi chu" — group cac phan ',' KHONG
         co ':' vao nguyen lieu truoc do (chung la ghi chu tiep noi, VD
         "Ot xiem xanh: 10 trai nho, dap dap").
      2. Khong co dau ':' o ca chuoi — moi phan tach boi ',' la 1 nguyen lieu
         doc lap (VD "Bot gao 200 Gr, Ca rot 1 Cu, ...").
    """
    parts = [p.strip() for p in raw.split(",")]
    if ":" not in raw:
        return [p for p in parts if p]
    out: list[str] = []
    cur: str | None = None
    for p in parts:
        if not p:
            continue
        if ":" in p:
            if cur:
                out.append(cur)
            cur = p
        elif cur is not None:
            cur = f"{cur}, {p}"
        else:
            cur = p
    if cur:
        out.append(cur)
    return out


def parse_fragment(frag: str) -> tuple[str, float | None]:
    """Tra ve (ten nguyen lieu, gram) — gram=None neu khong quy doi duoc that."""
    if ":" in frag:
        name, _, rest = frag.partition(":")
        name = name.strip()
        m = QTY_RE.search(rest)
    else:
        name = frag.strip()
        m = QTY_RE.search(frag)
    if not m:
        return name, None
    qty = float(m.group("qty").replace(",", "."))
    grams = qty * UNIT_TO_G[m.group("unit").lower()]
    if ":" not in frag:
        name = (frag[: m.start()] + " " + frag[m.end() :]).strip(" ,.-")
    return name.strip(), grams


# --------------------------------------------------------------------------
# Buoc 2 — khop ten nguyen lieu -> food_id (dung lai chi muc food_items.csv)
# --------------------------------------------------------------------------
def load_food_index() -> dict[str, int]:
    idx: dict[str, int] = {}
    with open(SEEDS / "food_items.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not (row.get("kcal_100g") or "").strip():
                continue
            if int(row["id"]) >= 100_000 and (row.get("source") or "") not in ("NIN", "curated"):
                continue
            for label in [row["name_vi"], *(row.get("aliases") or "").split("|")]:
                key = _norm(label)
                if key and key not in idx:
                    idx[key] = int(row["id"])
    return idx


def match_food_id(name: str, idx: dict[str, int]) -> int | None:
    key = _norm(name)
    if not key:
        return None
    if key in idx:
        return idx[key]
    best: tuple[int, int] | None = None
    for cand, fid in idx.items():
        if len(cand) < 4:
            continue
        if re.search(rf"(?:^|\s){re.escape(cand)}(?:\s|$)", key):
            if best is None or len(cand) > best[1]:
                best = (fid, len(cand))
    return best[0] if best else None


# --------------------------------------------------------------------------
# Buoc 3 — quyet dinh mon co dung duoc khong (giong het nguong mnmn)
# --------------------------------------------------------------------------
def evaluate(dish: Dish, idx: dict[str, int], min_mass_cover: float) -> tuple[bool, str, str]:
    parsed_mass = 0.0
    matched_mass = 0.0
    unparsed_main: list[str] = []

    for ing in dish.ingredients:
        name, grams = parse_fragment(ing.raw)
        ing.name, ing.grams = name, grams
        if grams is None:
            if not _is_seasoning(name):
                unparsed_main.append(ing.raw.strip())
            continue
        parsed_mass += grams
        ing.food_id = match_food_id(name, idx)
        if ing.food_id is not None:
            matched_mass += grams

    if parsed_mass <= 0:
        return False, "no_metric_qty", "khong co nguyen lieu nao ghi don vi g/kg/ml/l parse duoc"
    if unparsed_main:
        return False, "unparsed_main_ingredient", "; ".join(unparsed_main[:4])
    cover = matched_mass / parsed_mass
    if cover < min_mass_cover:
        missing = [i.name for i in dish.ingredients if i.grams is not None and i.food_id is None]
        return False, "low_food_id_cover", f"cover={cover:.2f} thieu: {', '.join(missing[:5])}"
    return True, "", f"cover={cover:.2f}"


def slugify_id(vifoodrec_id: str) -> str:
    return f"VFR-{vifoodrec_id}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--min-mass-cover", type=float, default=0.80)
    ap.add_argument("--pilot", action="store_true", help="chi in thong ke, khong ghi file seed")
    ap.add_argument("--out-prefix", default="vifoodrec")
    args = ap.parse_args()

    if not SRC_CSV.exists():
        print(f"Khong thay {SRC_CSV}. Can tai foods.csv (Clean Dataset) vao day truoc.")
        sys.exit(1)

    with open(SRC_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    batch = rows[args.offset : args.offset + args.limit] if args.limit else rows[args.offset :]
    print(f"ViFoodRec foods.csv: {len(rows)} dong | xu ly lo: offset={args.offset} so dong={len(batch)}")

    idx = load_food_index()
    print(f"Chi muc food_id ung vien: {len(idx)} nhan")

    accepted: list[Dish] = []
    rejected: list[dict[str, str]] = []
    reasons: dict[str, int] = {}

    for row in batch:
        name_vi = (row.get("dish_name") or "").strip()
        raw_ing = (row.get("ingredients") or "").strip()
        vfid = (row.get("food_id") or "").strip()
        if not name_vi or not raw_ing:
            rejected.append({"vifoodrec_food_id": vfid, "name_vi": name_vi, "reason": "empty_row", "detail": ""})
            continue

        dish = Dish(
            vifoodrec_id=vfid,
            name_vi=name_vi,
            ingredients=[Ingredient(raw=frag) for frag in split_ingredients(raw_ing)],
        )
        ok, reason, detail = evaluate(dish, idx, args.min_mass_cover)
        if ok:
            accepted.append(dish)
        else:
            reasons[reason] = reasons.get(reason, 0) + 1
            rejected.append({"vifoodrec_food_id": vfid, "name_vi": name_vi, "reason": reason, "detail": detail})

    print("\n===== KET QUA =====")
    print(f"Xu ly            : {len(batch)}")
    print(f"DUNG DUOC         : {len(accepted)} ({len(accepted) / max(len(batch), 1):.1%})")
    print("Ly do loai:")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {k:28s} {v}")

    if args.pilot:
        print("\n(--pilot: khong ghi file seed)")
        for d in accepted[:8]:
            got = [f"{i.name}={i.grams:g}g#{i.food_id}" for i in d.ingredients if i.food_id]
            print(f"  OK {d.name_vi}: {', '.join(got[:6])}")
        return

    dish_path = SEEDS / f"dishes.{args.out_prefix}.csv"
    ing_path = SEEDS / f"dish_ingredients.{args.out_prefix}.csv"
    rej_path = SEEDS / f"dishes.{args.out_prefix}.rejected.csv"
    dish_exists = dish_path.exists()

    with (
        open(dish_path, "a" if dish_exists else "w", newline="", encoding="utf-8") as fd,
        open(ing_path, "a" if dish_exists else "w", newline="", encoding="utf-8") as fi,
    ):
        wd = csv.DictWriter(fd, fieldnames=DISH_HEADER)
        wi = csv.DictWriter(fi, fieldnames=ING_HEADER)
        if not dish_exists:
            wd.writeheader()
            wi.writeheader()
        for d in accepted:
            did = slugify_id(d.vifoodrec_id)
            total = sum(i.grams for i in d.ingredients if i.grams and i.food_id)
            wd.writerow(
                {
                    "dish_id": did,
                    "name_vi": d.name_vi,
                    "region": "",
                    "serving_g": round(total, 1),
                    "verified_by": "pending",
                    "note": LICENSE_NOTE.format(vfid=d.vifoodrec_id),
                }
            )
            for i in d.ingredients:
                if i.food_id and i.grams:
                    wi.writerow({"dish_id": did, "food_id": i.food_id, "grams": f"{i.grams:g}", "note": i.raw.strip()})

    rej_exists = rej_path.exists()
    with open(rej_path, "a" if rej_exists else "w", newline="", encoding="utf-8") as fr:
        wr = csv.DictWriter(fr, fieldnames=REJECT_HEADER)
        if not rej_exists:
            wr.writeheader()
        wr.writerows(rejected)

    print(
        f"\nDa ghi: {dish_path.name} (+{len(accepted)} mon), {ing_path.name}, "
        f"{rej_path.name} (+{len(rejected)} bi loai)"
    )


if __name__ == "__main__":
    main()
