#!/usr/bin/env python3
"""Trich cong thuc mon Viet tu monngonmoingay.com -> dishes/dish_ingredients.

Ticket: DAT-24 (nang so mon CP-SAT dung duoc len 500+).

NGUON & PHAP LY
---------------
- `robots.txt` cua site cho phep tuong minh `User-agent: ClaudeBot -> Allow: /`
  (kiem tra 2026-08-08). Crawl co delay, mot luot, khong tai lai anh.
- Chi trich SU KIEN dinh luong (ten nguyen lieu + so gram) + URL nguon. KHONG
  luu lai van ban cong thuc/huong dan nau (do la noi dung co ban quyen).
- Moi mon luu `source_ref` = URL goc de truy nguyen (RULE-2).

KHONG BIA SO (RULE-1/RULE-2/DEC-008)
-----------------------------------
Chi chap nhan nguyen lieu ghi ro don vi KHOI LUONG/THE TICH quy doi duoc:
g, gr, kg, ml, l. Cac don vi uoc le tieng Viet ("2 mieng", "1/2 cay",
"1 muong canh", "chut xiu") KHONG duoc quy doi thanh gram - quy doi la suy
doan, vi pham RULE-2. Nguyen lieu nhu vay bi danh dau `unparsed`.

Mot mon chi duoc coi la DUNG DUOC cho CP-SAT khi:
  1. Moi nguyen lieu co dinh luong parse duoc DEU khop food_id, va
  2. Ty le khoi luong khop >= `--min-mass-cover` (mac dinh 0.80) so voi tong
     khoi luong parse duoc, va
  3. Khong con nguyen lieu `unparsed` nao thuoc nhom nguyen lieu chinh
     (gia vi kho dinh luong nhu "muoi, duong, tieu, dau an" duoc bo qua co
     kiem soat - xem `SEASONING_ONLY_RE`).
Mon khong dat -> ghi vao file *.rejected.csv kem ly do, KHONG vao dishes.csv.

Chay:
  python scripts/crawl_mnmn_dishes.py --limit 40 --pilot     # do ty le khop
  python scripts/crawl_mnmn_dishes.py --limit 2600           # chay that
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"
CACHE = ROOT / "data" / "cache" / "mnmn"

SITEMAP_INDEX = "https://monngonmoingay.com/sitemap_index.xml"
UA = "ClaudeBot/1.0 (+VNutriCare academic nutrition research; contact via repo)"
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"}

# Don vi khoi luong/the tich quy doi duoc sang gram.
# ml/l: coi 1 ml ~ 1 g - dung cho nuoc/nuoc dung/sua/dau o muc chinh xac can
# thiet cho rang buoc dinh duong; ghi ro trong note de R2 biet gia dinh nay.
UNIT_TO_G: dict[str, float] = {"g": 1.0, "gr": 1.0, "gam": 1.0, "kg": 1000.0, "ml": 1.0, "l": 1000.0}

QTY_RE = re.compile(
    r"(?P<qty>\d+(?:[.,]\d+)?)\s*(?P<unit>kg|gr|gam|g|ml|l)\b",
    re.IGNORECASE,
)

# Dong chi liet ke gia vi khong dinh luong ("Muoi, duong, tieu, dau an").
SEASONING_ONLY_RE = re.compile(
    r"^\s*(muối|đường|tiêu|dầu ăn|nước mắm|hạt nêm|bột ngọt|gia vị|tương ớt|ớt|tỏi|hành|"
    r"bột canh|giấm|chanh|nước tương|dầu mè|mè|rau thơm|ngò|hành lá)"
    r"([\s,/và]+(muối|đường|tiêu|dầu ăn|nước mắm|hạt nêm|bột ngọt|gia vị|tương ớt|ớt|tỏi|"
    r"hành|bột canh|giấm|chanh|nước tương|dầu mè|mè|rau thơm|ngò|hành lá))*\s*$",
    re.IGNORECASE,
)

DISH_HEADER = ["dish_id", "name_vi", "region", "serving_g", "verified_by", "note"]
ING_HEADER = ["dish_id", "food_id", "grams", "note"]
REJECT_HEADER = ["url", "name_vi", "reason", "detail"]


def _norm(name: str) -> str:
    name = unicodedata.normalize("NFC", str(name)).strip().lower()
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"[^\w\sÀ-ỹ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


@dataclass
class Ingredient:
    raw: str
    name: str
    grams: float | None = None
    food_id: int | None = None


@dataclass
class Recipe:
    url: str
    name_vi: str
    servings: int | None
    ingredients: list[Ingredient] = field(default_factory=list)


# --------------------------------------------------------------------------
# Buoc 1 — lay danh sach URL mon an tu sitemap
# --------------------------------------------------------------------------
def fetch_recipe_urls(session: requests.Session) -> list[str]:
    idx = session.get(SITEMAP_INDEX, timeout=30).text
    submaps = [u for u in re.findall(r"<loc>(.*?)</loc>", idx) if "monan-sitemap" in u]
    urls: list[str] = []
    for sm in submaps:
        body = session.get(sm, timeout=30).text
        for u in re.findall(r"<loc>(.*?)</loc>", body):
            if u.rstrip("/").endswith("mon-an"):
                continue  # trang danh muc, khong phai mon
            urls.append(u)
        time.sleep(0.3)
    # de-dup giu thu tu
    return list(dict.fromkeys(urls))


# --------------------------------------------------------------------------
# Buoc 2 — doc JSON-LD schema.org/Recipe cua tung trang
# --------------------------------------------------------------------------
def parse_recipe_html(url: str, html: str) -> Recipe | None:
    for block in re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", html, re.S):
        try:
            # strict=False: JSON-LD cua site co xuong dong tho trong chuoi
            # (control character) — json chuan tu choi, bo qua se mat ~2/3 mon.
            data = json.loads(block, strict=False)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "@graph" in data:
            nodes = data["@graph"]
        elif isinstance(data, list):
            nodes = data
        else:
            nodes = [data]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            types = node.get("@type")
            types = types if isinstance(types, list) else [types]
            if "Recipe" not in types:
                continue
            raw_yield = str(node.get("recipeYield") or "")
            m = re.search(r"\d+", raw_yield)
            servings = int(m.group()) if m and int(m.group()) > 0 else None
            ings = [Ingredient(raw=s, name="") for s in (node.get("recipeIngredient") or []) if str(s).strip()]
            return Recipe(url=url, name_vi=str(node.get("name") or "").strip(), servings=servings, ingredients=ings)
    return None


# --------------------------------------------------------------------------
# Buoc 3 — tach dinh luong; KHONG doan don vi uoc le
# --------------------------------------------------------------------------
def parse_quantity(raw: str) -> tuple[str, float | None]:
    """Tra ve (ten nguyen lieu, so gram) — grams=None neu khong quy doi duoc."""
    m = QTY_RE.search(raw)
    if not m:
        return raw.strip(), None
    qty = float(m.group("qty").replace(",", "."))
    grams = qty * UNIT_TO_G[m.group("unit").lower()]
    name = (raw[: m.start()] + " " + raw[m.end() :]).strip(" ,.-")
    return name, grams


# --------------------------------------------------------------------------
# Buoc 4 — khop ten nguyen lieu -> food_id
# --------------------------------------------------------------------------
def load_food_index() -> dict[str, int]:
    """Chi lay ung vien CP-SAT that (id < 100000, da co so lieu)."""
    idx: dict[str, int] = {}
    with open(SEEDS / "food_items.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not (row.get("kcal_100g") or "").strip():
                continue
            if int(row["id"]) >= 100_000:
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
    # Khop tien to/hau to co kiem soat: chi chap nhan khi ten trong CSDL la mot
    # cum tu day du xuat hien tron ven trong ten nguyen lieu (VD "thit heo nac"
    # trong "thit heo nac xay"), va dai >= 4 ky tu de tranh khop bua ("ca").
    best: tuple[int, int] | None = None
    for cand, fid in idx.items():
        if len(cand) < 4:
            continue
        if re.search(rf"(?:^|\s){re.escape(cand)}(?:\s|$)", key):
            if best is None or len(cand) > best[1]:
                best = (fid, len(cand))
    return best[0] if best else None


# --------------------------------------------------------------------------
# Buoc 5 — quyet dinh mon co dung duoc khong
# --------------------------------------------------------------------------
def evaluate(recipe: Recipe, idx: dict[str, int], min_mass_cover: float) -> tuple[bool, str, str]:
    parsed_mass = 0.0
    matched_mass = 0.0
    unparsed_main: list[str] = []

    for ing in recipe.ingredients:
        name, grams = parse_quantity(ing.raw)
        ing.name, ing.grams = name, grams
        if grams is None:
            if not SEASONING_ONLY_RE.match(name.strip()):
                unparsed_main.append(ing.raw.strip())
            continue
        parsed_mass += grams
        ing.food_id = match_food_id(name, idx)
        if ing.food_id is not None:
            matched_mass += grams

    if parsed_mass <= 0:
        return False, "no_metric_qty", "khong co nguyen lieu nao ghi don vi g/kg/ml/l"
    if unparsed_main:
        return False, "unparsed_main_ingredient", "; ".join(unparsed_main[:4])
    cover = matched_mass / parsed_mass
    if cover < min_mass_cover:
        missing = [i.name for i in recipe.ingredients if i.grams is not None and i.food_id is None]
        return False, "low_food_id_cover", f"cover={cover:.2f} thieu: {', '.join(missing[:5])}"
    return True, "", f"cover={cover:.2f}"


def slugify_id(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1]
    return "MNMN-" + slug.upper()[:48]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--delay", type=float, default=1.0, help="giay nghi giua 2 request")
    ap.add_argument("--min-mass-cover", type=float, default=0.80)
    ap.add_argument("--pilot", action="store_true", help="chi in thong ke, khong ghi file seed")
    ap.add_argument("--out-prefix", default="mnmn")
    args = ap.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    print("Dang lay danh sach URL tu sitemap...")
    urls = fetch_recipe_urls(session)
    print(f"Tong URL mon an: {len(urls)} — se xu ly {min(args.limit, len(urls))}")

    idx = load_food_index()
    print(f"Chi muc food_id ung vien CP-SAT: {len(idx)} nhan")

    accepted: list[Recipe] = []
    rejected: list[dict[str, str]] = []
    stats = {"fetched": 0, "no_recipe_ldjson": 0, "accepted": 0}
    reasons: dict[str, int] = {}

    for url in urls[: args.limit]:
        cache_file = CACHE / (url.rstrip("/").split("/")[-1] + ".html")
        if cache_file.exists():
            html = cache_file.read_text(encoding="utf-8", errors="replace")
        else:
            try:
                resp = session.get(url, timeout=30)
            except requests.RequestException as exc:
                rejected.append({"url": url, "name_vi": "", "reason": "http_error", "detail": str(exc)[:120]})
                continue
            if resp.status_code != 200:
                rejected.append({"url": url, "name_vi": "", "reason": "http_error", "detail": str(resp.status_code)})
                continue
            html = resp.text
            cache_file.write_text(html, encoding="utf-8", errors="replace")
            time.sleep(args.delay)
        stats["fetched"] += 1

        recipe = parse_recipe_html(url, html)
        if recipe is None or not recipe.ingredients:
            stats["no_recipe_ldjson"] += 1
            rejected.append({"url": url, "name_vi": "", "reason": "no_recipe_ldjson", "detail": ""})
            continue

        ok, reason, detail = evaluate(recipe, idx, args.min_mass_cover)
        if ok:
            accepted.append(recipe)
            stats["accepted"] += 1
        else:
            reasons[reason] = reasons.get(reason, 0) + 1
            rejected.append({"url": url, "name_vi": recipe.name_vi, "reason": reason, "detail": detail})

    print("\n===== KET QUA =====")
    print(f"Tai ve            : {stats['fetched']}")
    print(f"Khong co Recipe LD: {stats['no_recipe_ldjson']}")
    print(f"DUNG DUOC         : {stats['accepted']} ({stats['accepted'] / max(stats['fetched'], 1):.1%})")
    print("Ly do loai:")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {k:28s} {v}")

    if args.pilot:
        print("\n(--pilot: khong ghi file seed)")
        for r in accepted[:8]:
            got = [f"{i.name}={i.grams:g}g#{i.food_id}" for i in r.ingredients if i.food_id]
            print(f"  ✓ {r.name_vi}: {', '.join(got[:6])}")
        return

    dish_path = SEEDS / f"dishes.{args.out_prefix}.csv"
    ing_path = SEEDS / f"dish_ingredients.{args.out_prefix}.csv"
    rej_path = SEEDS / f"dishes.{args.out_prefix}.rejected.csv"

    with open(dish_path, "w", newline="", encoding="utf-8") as fd, open(ing_path, "w", newline="", encoding="utf-8") as fi:
        wd = csv.DictWriter(fd, fieldnames=DISH_HEADER)
        wi = csv.DictWriter(fi, fieldnames=ING_HEADER)
        wd.writeheader()
        wi.writeheader()
        for r in accepted:
            did = slugify_id(r.url)
            total = sum(i.grams for i in r.ingredients if i.grams and i.food_id)
            serving = round(total / r.servings, 1) if r.servings else round(total, 1)
            wd.writerow({
                "dish_id": did,
                "name_vi": r.name_vi,
                "region": "",
                "serving_g": serving,
                "verified_by": "pending",
                "note": (
                    f"Trich JSON-LD schema.org/Recipe tu {r.url} (crawl 2026-08-08, robots.txt cho phep "
                    f"ClaudeBot). Chi lay nguyen lieu ghi ro g/kg/ml/l; ml quy doi 1ml=1g. "
                    f"R2 CAN DUYET gram truoc khi dung cho benh nhan."
                ),
            })
            for i in r.ingredients:
                if i.food_id and i.grams:
                    wi.writerow({"dish_id": did, "food_id": i.food_id, "grams": f"{i.grams:g}", "note": i.raw.strip()})

    with open(rej_path, "w", newline="", encoding="utf-8") as fr:
        wr = csv.DictWriter(fr, fieldnames=REJECT_HEADER)
        wr.writeheader()
        wr.writerows(rejected)

    print(f"\nDa ghi: {dish_path.name} ({len(accepted)} mon), {ing_path.name}, {rej_path.name} ({len(rejected)} bi loai)")


if __name__ == "__main__":
    main()
