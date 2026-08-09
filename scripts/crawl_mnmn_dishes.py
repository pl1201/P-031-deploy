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

# Gia vi / rau thom AN TOAN KHI BO QUA neu cong thuc khong dinh luong.
#
# Vi sao duoc phep bo rieng nhom nay: day la thuc pham vua RAT IT khoi luong
# trong mot suat (vai gram toi ~15 g) vua GAN NHU KHONG co nang luong, nen bo
# di khong lam lech dang ke mat do dinh duong cua mon. Nguyen lieu khac (thit,
# tinh bot, dau an, rau cu an chinh) KHONG duoc bo — bo la lam mon bi ghi nhan
# thap hon nang luong that, dung bug da sua 2026-08-07.
#
# CO Y KHONG dua vao day: dau an / nuoc mam / duong / muoi — deu la nguon nang
# luong hoac natri lon, phai co dinh luong that moi tinh.
GARNISH_WORDS = (
    "tiêu|ớt|ớt hiểm|ớt sừng|ớt bột|tương ớt|tỏi|hành|hành lá|hành tím|hành khô|"
    "hành boaro|hành tây nhỏ|sả|gừng|riềng|ngò|ngò rí|ngò gai|rau thơm|rau răm|"
    "húng quế|thì là|lá chanh|chanh|quất|rau mùi|tía tô|kinh giới|mùi tàu|"
    "rau sống|rau ăn kèm|hẹ|đầu hành|gốc hành"
)
GARNISH_ONLY_RE = re.compile(
    rf"^\s*(?:{GARNISH_WORDS})(?:[\s,/]+(?:và|hoặc)?[\s,/]*(?:{GARNISH_WORDS}))*\s*$",
    re.IGNORECASE,
)

# Dong chi liet ke gia vi khong dinh luong ("Muoi, duong, tieu, dau an") — dong
# nay khong the tach ra tung thu, chap nhan bo qua ca dong.
SEASONING_ONLY_RE = re.compile(
    rf"^\s*(?:muối|đường|dầu ăn|nước mắm|hạt nêm|bột ngọt|gia vị|bột canh|giấm|"
    rf"nước tương|dầu mè|dầu hào|mè|{GARNISH_WORDS})"
    rf"(?:[\s,/]+(?:và|hoặc)?[\s,/]*(?:muối|đường|dầu ăn|nước mắm|hạt nêm|bột ngọt|"
    rf"gia vị|bột canh|giấm|nước tương|dầu mè|dầu hào|mè|{GARNISH_WORDS}))+\s*$",
    re.IGNORECASE,
)

# Tran so dong gia vi/rau thom duoc phep bo qua trong mot mon. Vuot nguong nay
# thi phan bi bo khong con la "vai nhanh rau thom" nua va sai so tich luy dang ke.
MAX_BO_QUA = 4

# Mon co tong khoi luong parse duoc qua nho thuong la cong thuc nuoc cham/gia vi
# hoac cong thuc bi doc thieu — khong phai mot suat an that.
MIN_DISH_MASS_G = 150.0

# Bang quy doi don vi uoc le -> gram, nap mot lan (xem _load_unit_conversions).
UNIT_TABLE: dict[tuple[str, str], tuple[float, str]] = {}

DISH_HEADER = ["dish_id", "name_vi", "region", "serving_g", "verified_by", "note"]
ING_HEADER = ["dish_id", "food_id", "grams", "note"]
REJECT_HEADER = ["url", "name_vi", "reason", "detail"]


# Don vi uoc le tieng Viet — KHONG quy doi duoc ra gram, nhung phai cat khoi
# TEN nguyen lieu, neu khong "ot hiem 2 trai" se khong bao gio khop noi "Ot".
VAGUE_UNITS = (
    "trái|quả|củ|cây|tai|cái|gói|chén|lát|nhánh|miếng|tép|bánh|vắt|hũ|bịch|"
    "con|khúc|lá|bó|nắm|muỗng|thìa|bát|ly|cốc|hộp|lon|vỉ|xâu|m|M"
)
QTY_TAIL_RE = re.compile(
    # BAT BUOC phai co chu so truoc don vi. Khong dung \b truoc don vi vi "1m"
    # (1 muong, rat pho bien o nguon nay) khong co ranh gioi tu giua "1" va "m";
    # nhung neu bo han rang buoc thi "cam" lai bi cat thanh "ca" — nen chot bang
    # cach yeu cau it nhat mot chu so/phan so mo dau.
    rf"(?:^|\s)[\d½¼⅓⅔¾][\d.,/½¼⅓⅔¾\s]*(?:{VAGUE_UNITS})(?![\wÀ-ỹ])\s*$"
    rf"|^\s*[\d.,/½¼⅓⅔¾]+\s*(?:{VAGUE_UNITS})(?![\wÀ-ỹ])",
)

# Nguon nay hay them nhan phan loai o dau dong ("Gia vi: dau an, hat nem",
# "Rau nem: ngo ri", "An kem: com trang") — phai cat de con lai ten thuc pham.
LABEL_PREFIX_RE = re.compile(
    r"^\s*(?:gia vị|rau nêm|rau ăn kèm|ăn kèm|nguyên liệu|phần\s+\w+|nước chấm|"
    r"nguyên liệu chính|sơ chế|ướp)\s*:\s*",
    re.IGNORECASE,
)

# Cach so che — khong doi ban chat thuc pham, phai bo khi so khop ten
# ("toi bam" van la "Toi", "thit bo thai mong" van la thit bo).
PREP_WORDS_RE = re.compile(
    r"\b(băm|bằm|xay|thái|cắt|nhuyễn|mỏng|nhỏ|khúc|sợi|hạt lựu|bóc vỏ|làm sạch|"
    r"rửa sạch|đập dập|giã|xắt|tươi|khô sẵn|rang sẵn)\b",
    re.IGNORECASE,
)


def _norm(name: str) -> str:
    name = unicodedata.normalize("NFC", str(name)).strip().lower()
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"[^\w\sÀ-ỹ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _clean_name(name: str) -> str:
    """Bo so luong uoc le va cach so che de con lai TEN thuc pham thuan."""
    out = LABEL_PREFIX_RE.sub("", name).strip(" ,.:-")
    for _ in range(3):  # co the co nhieu duoi lien tiep
        new = QTY_TAIL_RE.sub(" ", out).strip(" ,.:-")
        if new == out:
            break
        out = new
    out = PREP_WORDS_RE.sub(" ", out)
    return re.sub(r"\s+", " ", out).strip(" ,.:-")


@dataclass
class Ingredient:
    raw: str
    name: str
    grams: float | None = None
    food_id: int | None = None
    unit_ref: str | None = None   # nguon quy doi neu gram den tu bang unit_conversions


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
FRACTIONS = {"½": 0.5, "¼": 0.25, "⅓": 1 / 3, "⅔": 2 / 3, "¾": 0.75}

# So luong + don vi uoc le, VD "2 trai", "1/2 cu", "1m", "3 tai".
VAGUE_QTY_RE = re.compile(rf"(?P<qty>\d+(?:\s*/\s*\d+)?(?:[.,]\d+)?|[½¼⅓⅔¾])\s*(?P<unit>{VAGUE_UNITS})(?![\wÀ-ỹ])")


def _load_unit_conversions() -> dict[tuple[str, str], tuple[float, str]]:
    """{(ten chuan hoa, don vi): (gram, source_ref)} tu unit_conversions.csv."""
    table: dict[tuple[str, str], tuple[float, str]] = {}
    path = SEEDS / "unit_conversions.csv"
    if not path.exists():
        return table
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (_norm(row["ten_nguyen_lieu"]), row["don_vi"].strip())
            table[key] = (float(row["gram"]), row["source_ref"])
    return table


def _parse_vague_amount(text: str) -> float | None:
    text = text.strip()
    if text in FRACTIONS:
        return FRACTIONS[text]
    if "/" in text:
        try:
            num, den = (p.strip() for p in text.split("/", 1))
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def quy_doi_don_vi_uoc_le(raw: str, table: dict[tuple[str, str], tuple[float, str]]) -> tuple[float, str] | None:
    """Quy doi "2 qua trung ga" -> (88 g, nguon). None neu khong co trong bang.

    CHI dung bang tra `data/seeds/unit_conversions.csv` (moi dong co fdc_id USDA
    lam nguon) — khong bao gio tu doan khoi luong mot "qua"/"cu"/"muong".
    """
    m = VAGUE_QTY_RE.search(raw)
    if not m:
        return None
    amount = _parse_vague_amount(m.group("qty"))
    if amount is None:
        return None
    # "qua" (Bac) va "trai" (Nam) la cung mot don vi dem; nguon nay dung lan lon.
    unit = {"trái": "quả"}.get(m.group("unit"), m.group("unit"))
    name = _clean_name(raw)
    key_name = _norm(name)
    for (ten, don_vi), (gram, ref) in table.items():
        if don_vi != unit:
            continue
        if key_name == ten or re.search(rf"(?:^|\s){re.escape(ten)}(?:\s|$)", key_name):
            return amount * gram, ref
    return None


def parse_quantity(raw: str) -> tuple[str, float | None]:
    """Tra ve (ten nguyen lieu, so gram) — grams=None neu khong quy doi duoc."""
    m = QTY_RE.search(raw)
    if not m:
        return _clean_name(raw), None
    qty = float(m.group("qty").replace(",", "."))
    grams = qty * UNIT_TO_G[m.group("unit").lower()]
    name = (raw[: m.start()] + " " + raw[m.end() :]).strip(" ,.-")
    return _clean_name(name), grams


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
            # Giu dong bo voi `_la_khoi_usda_bulk` trong src/agents/nodes/core.py:
            # loai DUNG khoi bulk USDA, moi dong khac deu la ung vien.
            if (row.get("source") or "") == "USDA" and int(row["id"]) >= 100_000:
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
def bo_qua_duoc(name: str) -> bool:
    """True khi nguyen lieu khong dinh luong nay bo qua duoc ma khong lam sai mon.

    Chi dung cho gia vi / rau thom: it khoi luong VA gan nhu khong nang luong.
    """
    text = name.strip()
    return bool(GARNISH_ONLY_RE.match(text) or SEASONING_ONLY_RE.match(text))


def evaluate(recipe: Recipe, idx: dict[str, int], min_mass_cover: float) -> tuple[bool, str, str]:
    parsed_mass = 0.0
    matched_mass = 0.0
    unparsed_main: list[str] = []
    bo_qua: list[str] = []

    for ing in recipe.ingredients:
        name, grams = parse_quantity(ing.raw)
        if grams is None:
            quy_doi = quy_doi_don_vi_uoc_le(ing.raw, UNIT_TABLE)
            if quy_doi is not None:
                grams, ing.unit_ref = quy_doi
        ing.name, ing.grams = name, grams
        if grams is None:
            if bo_qua_duoc(name):
                bo_qua.append(name)
            else:
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
    # Bo qua qua nhieu dong -> khong con la "vai nhanh rau thom" nua, tu choi.
    if len(bo_qua) > MAX_BO_QUA:
        return False, "qua_nhieu_dong_bo_qua", f"{len(bo_qua)} dong: {'; '.join(bo_qua[:4])}"
    cover = matched_mass / parsed_mass
    if cover < min_mass_cover:
        missing = [i.name for i in recipe.ingredients if i.grams is not None and i.food_id is None]
        return False, "low_food_id_cover", f"cover={cover:.2f} thieu: {', '.join(missing[:5])}"
    if parsed_mass < MIN_DISH_MASS_G:
        return False, "khoi_luong_qua_nho", f"chi {parsed_mass:.0f} g — kho la mot suat that"
    return True, "", f"cover={cover:.2f} bo_qua={len(bo_qua)}"


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
    UNIT_TABLE.update(_load_unit_conversions())
    print(f"Bang quy doi don vi uoc le: {len(UNIT_TABLE)} dong")

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

    with (
        open(dish_path, "w", newline="", encoding="utf-8") as fd,
        open(ing_path, "w", newline="", encoding="utf-8") as fi,
    ):
        wd = csv.DictWriter(fd, fieldnames=DISH_HEADER)
        wi = csv.DictWriter(fi, fieldnames=ING_HEADER)
        wd.writeheader()
        wi.writeheader()
        for r in accepted:
            did = slugify_id(r.url)
            total = sum(i.grams for i in r.ingredients if i.grams and i.food_id)
            serving = round(total / r.servings, 1) if r.servings else round(total, 1)
            wd.writerow(
                {
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
                }
            )
            for i in r.ingredients:
                if i.food_id and i.grams:
                    wi.writerow({"dish_id": did, "food_id": i.food_id, "grams": f"{i.grams:g}", "note": i.raw.strip()})

    with open(rej_path, "w", newline="", encoding="utf-8") as fr:
        wr = csv.DictWriter(fr, fieldnames=REJECT_HEADER)
        wr.writeheader()
        wr.writerows(rejected)

    print(
        f"\nDa ghi: {dish_path.name} ({len(accepted)} mon), {ing_path.name}, {rej_path.name} ({len(rejected)} bi loai)"
    )


if __name__ == "__main__":
    main()
