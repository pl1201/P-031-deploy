#!/usr/bin/env python3
"""Lấp các trường NIN 2017 còn trống (chủ yếu Na/K) bằng USDA analog do LLM CHỌN.

Ticket: DAT-25 (nối tiếp DAT-24). Hưng chấp nhận lấp ~314 dòng còn khuyết
(2026-08-09), với điều kiện làm theo cách an toàn nhất.

VÌ SAO KHÔNG ĐỂ LLM ĐOÁN SỐ (RULE-1)
------------------------------------
Các trường thiếu là Na/K/P — đúng ngưỡng chặn cứng của CKD/THA. Để LLM tự sinh
con số là vi phạm RULE-1 (LLM chọn, Python tính). Thay vào đó:

  1. Với mỗi thực phẩm chưa lấp, lấy `name_en` do chính NIN cung cấp + một danh
     sách ứng viên USDA THẬT (top-K theo độ tương đồng token).
  2. LLM chỉ được CHỌN một `fdc_id` TRONG danh sách đó (hoặc null nếu không có
     analog thật) — không được bịa id, không được sinh số. Id ngoài danh sách
     bị từ chối (giống UnknownFoodError).
  3. Lấy mẫu LLM 3 lần (ý tưởng repeated-sampling của Izzard et al. 2607.23273);
     chỉ chấp nhận khi ≥2/3 lần đồng thuận cùng một fdc_id.
  4. Python đọc GIÁ TRỊ THẬT (Na/K/P…) từ đúng dòng USDA đó. Con số luôn có
     nguồn; sự không chắc chắn nằm ở việc CHỌN analog, không ở con số.
  5. Đánh dấu `source=estimated`, `is_estimated=TRUE`, `source_ref` ghi rõ analog
     + mức đồng thuận + mã NIN. UI hiển thị "ước tính"; R2 vẫn phải duyệt trước
     khi tin dùng cho ngưỡng lâm sàng.

Không có analog thật / LLM trả null / không đồng thuận → GIỮ TRỐNG (đúng DEC-008).

Chạy:
  python scripts/fill_gaps_llm_analog.py --pilot 15      # thử, không ghi
  python scripts/fill_gaps_llm_analog.py --apply         # ghi vào food_items.csv
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import get_settings  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"
NIN_JSON = ROOT / "scripts" / "nin2017_extracted.json"
USDA_CACHE = ROOT / "data" / "cache" / "usda_generic.json"

TOP_K = 25
SAMPLES = 3  # ghi đè qua --samples; free-tier RPD/ngày thấp nên mặc định thực tế dùng 1
MIN_AGREE = 2  # cần ít nhất 2/3 lần chọn cùng fdc_id (tự hạ = 1 khi --samples 1)
# Sàn tin cậy: Na/K gate ngưỡng CKD/THA nên siết chặt. Dưới mức này → để R2
# quyết từ đầu thay vì tự lấp (dù đã đánh dấu estimated). VD Bánh đúc→Rice cake
# conf 0.53 bị đẩy sang R2 thay vì auto-fill.
MIN_CONF = 0.60

# Trường có thể lấy từ USDA analog. Macro (kcal/protein/carb) LUÔN từ NIN thật.
USDA_FIELDS = {"fat_g", "fiber_g", "na_mg", "k_mg", "p_mg"}

STOPWORDS = frozenset(
    {
        "raw",
        "fresh",
        "cooked",
        "boiled",
        "nfs",
        "ns",
        "as",
        "to",
        "the",
        "and",
        "with",
        "without",
        "type",
        "style",
        "commercial",
        "prepared",
        "dried",
        "of",
        "in",
    }
)


class AnalogPick(BaseModel):
    """LLM chỉ được chọn 1 id trong danh sách, hoặc null. Không có trường số nào."""

    fdc_id: int | None
    confidence: float
    reason: str


def _norm_en(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> set[str]:
    return {t for t in _norm_en(text).split() if t not in STOPWORDS and len(t) > 2}


def _score(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def load_targets() -> list[dict]:
    """Các dòng food_items còn trống, kèm mã NIN + danh sách trường thiếu."""
    nin_by_code = {d["code"]: d for d in json.loads(NIN_JSON.read_text(encoding="utf-8"))}
    out: list[dict] = []
    with open(SEEDS / "food_items.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("kcal_100g") or "").strip():
                continue
            ref = row.get("source_ref") or ""
            if "CHUA DU LIEU" not in ref:
                continue
            m_code = re.search(r"ma (\d+)", ref)
            m_miss = re.search(r"PDF thieu: (.+)$", ref)
            if not (m_code and m_miss):
                continue
            nin = nin_by_code.get(m_code.group(1))
            if nin is None or not (nin.get("name_en") or "").strip():
                continue
            missing = [x.strip() for x in m_miss.group(1).split(",")]
            out.append(
                {
                    "id": row["id"],
                    "name_vi": row["name_vi"],
                    "name_en": nin["name_en"].strip(),
                    "code": m_code.group(1),
                    "missing": missing,
                    "nin": nin,
                }
            )
    return out


def load_usda() -> list[dict]:
    return json.loads(USDA_CACHE.read_text(encoding="utf-8"))


def candidates_for(name_en: str, usda: list[dict], missing: list[str]) -> list[dict]:
    """Top-K ứng viên USDA có ĐỦ các trường cần lấp, xếp theo token score."""
    scored = []
    for u in usda:
        if any(u.get(fld) is None for fld in missing if fld in USDA_FIELDS):
            continue  # ứng viên thiếu đúng trường ta cần thì vô dụng
        s = _score(name_en, u["desc"])
        if s > 0:
            scored.append((s, u))
    scored.sort(key=lambda x: -x[0])
    return [u for _, u in scored[:TOP_K]]


_PROMPT = """Bạn là trợ lý dữ liệu dinh dưỡng cho một hệ thống lâm sàng Việt Nam.

Nhiệm vụ: cho một thực phẩm Việt Nam (thiếu số liệu natri/kali), chọn MỘT thực phẩm USDA trong danh sách dưới đây là món TƯƠNG ĐƯƠNG DINH DƯỠNG gần nhất — cùng loại thực phẩm, cùng cách chế biến — để mượn giá trị khoáng chất của nó.

Thực phẩm cần tra:
- Tên Việt: {name_vi}
- Tên Anh (do Viện Dinh dưỡng cung cấp): {name_en}

Danh sách ứng viên USDA (chỉ được chọn fdc_id trong đây):
{candidates}

QUY TẮC:
- Chỉ trả về `fdc_id` CÓ trong danh sách trên, hoặc `null`.
- Đây là dữ liệu y tế: chọn sai analog → sai natri → nguy hiểm cho bệnh nhân thận/huyết áp. THÀ TRẢ null CÒN HƠN đoán một analog yếu.
- Trả null nếu danh sách chỉ có sản phẩm thương mại không liên quan, hoặc không món nào thật sự cùng loại.
- `confidence`: 0-1, mức bạn tin đây đúng là analog cùng loại."""


class QuotaExhaustedError(Exception):
    """Toàn bộ key đều 429 — dừng cả script, KHÔNG mất kết quả đã tính được."""


def pick_analog(
    client_keys: list[str], model: str, name_vi: str, name_en: str,
    candidates: list[dict], samples: int, min_agree: int,
) -> tuple[int | None, float, str]:
    cand_text = "\n".join(f"- fdc_id={u['fdc_id']}: {u['desc']}" for u in candidates)
    prompt = _PROMPT.format(name_vi=name_vi, name_en=name_en, candidates=cand_text)
    valid_ids = {int(u["fdc_id"]) for u in candidates}
    config = types.GenerateContentConfig(
        temperature=0.4, response_mime_type="application/json", response_schema=AnalogPick
    )
    picks: list[int | None] = []
    confs: list[float] = []
    reasons: list[str] = []
    for _ in range(samples):
        pick = _call(client_keys, model, prompt, config)
        if pick is None:
            picks.append(None)
            continue
        # LLM bịa id ngoài danh sách → coi như null (RULE-1: không nhận id lạ).
        fid = pick.fdc_id if (pick.fdc_id in valid_ids) else None
        picks.append(fid)
        confs.append(pick.confidence)
        reasons.append(pick.reason)
    # Đồng thuận: fdc_id không-null xuất hiện nhiều nhất. samples=1 -> min_agree=1,
    # tức chỉ còn dựa vào MIN_CONF tự báo cáo của chính lần gọi đó.
    non_null = [p for p in picks if p is not None]
    if not non_null:
        return None, 0.0, "; ".join(reasons[:1])
    top, count = collections.Counter(non_null).most_common(1)[0]
    if count < min_agree:
        return None, 0.0, f"không đồng thuận (picks={picks})"
    avg_conf = sum(confs) / len(confs) if confs else 0.0
    if avg_conf < MIN_CONF:
        return None, round(avg_conf, 2), f"đồng thuận nhưng conf {avg_conf:.2f} < {MIN_CONF}"
    return top, round(avg_conf, 2), f"{count}/{samples} đồng thuận; {reasons[0] if reasons else ''}"


def _call(keys: list[str], model: str, prompt: str, config) -> AnalogPick | None:
    exhausted = 0
    for key in keys:
        try:
            client = genai.Client(api_key=key)
            resp = client.models.generate_content(model=model, contents=prompt, config=config)
        except errors.ClientError as exc:
            if getattr(exc, "code", None) == 429:
                exhausted += 1
                continue
            raise
        parsed = resp.parsed
        if isinstance(parsed, AnalogPick):
            return parsed
        try:
            return AnalogPick.model_validate_json(resp.text or "{}")
        except (ValueError, TypeError):
            return None
    if exhausted == len(keys):
        # Free-tier RPD (requests/ngày/project/model) là quota NGÀY, không phải
        # phút — retry ngay trong phiên này vô ích nếu tất cả key dùng chung
        # project. Dừng sạch để không mất phần đã lấp được của batch hiện tại.
        raise QuotaExhaustedError(f"Cả {len(keys)} key đều 429 (hết quota/ngày).")
    return None


HEADER_ORDER = None  # giữ đúng thứ tự cột file gốc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=0, help="chỉ chạy N dòng đầu, không ghi")
    ap.add_argument("--offset", type=int, default=0, help="bỏ qua N dòng đầu (chạy theo lô)")
    ap.add_argument("--limit", type=int, default=0, help="chỉ xử lý N dòng từ offset (0 = hết)")
    ap.add_argument("--samples", type=int, default=1,
                     help="số lần lấy mẫu LLM/dòng (mặc định 1 — free-tier RPD/ngày quá thấp cho 3)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    min_agree = 2 if args.samples >= 3 else 1

    settings = get_settings()
    keys = settings.gemini_keys()
    if not keys:
        print("Chưa cấu hình GEMINI_API_KEY.")
        sys.exit(1)
    model = settings.gemini_model

    targets = load_targets()
    usda = load_usda()
    print(f"Dòng còn trống cần lấp: {len(targets)} | USDA cache: {len(usda)}")

    if args.pilot:
        batch = targets[: args.pilot]
    else:
        end = args.offset + args.limit if args.limit else len(targets)
        batch = targets[args.offset : end]
    print(f"Xử lý lô: offset={args.offset} số dòng={len(batch)}")
    filled: dict[str, dict] = {}  # id -> {field: value, source_ref}
    remain: list[dict] = []
    untouched: list[dict] = []

    for i, t in enumerate(batch):
        cands = candidates_for(t["name_en"], usda, t["missing"])
        if not cands:
            remain.append({**_r(t), "reason": "không ứng viên USDA nào đủ trường cần"})
            continue
        try:
            fid, conf, note = pick_analog(
                keys, model, t["name_vi"], t["name_en"], cands, args.samples, min_agree
            )
        except QuotaExhaustedError as exc:
            untouched = batch[i:]
            print(
                f"\n⚠️ {exc} Dừng batch tại đây, GHI LẠI phần đã lấp được — không mất việc.\n"
                f"   Chưa kịp thử: {len(untouched)} dòng (sẽ tự động nằm trong lần chạy kế tiếp, "
                "vì load_targets() đọc lại food_items.csv mỗi lần)."
            )
            break
        if fid is None:
            remain.append({**_r(t), "reason": f"LLM trả null / {note}"})
            print(f"  ⊘ {t['name_vi'][:26]:26s} → null ({note[:40]})")
            continue
        src = next(u for u in cands if int(u["fdc_id"]) == fid)
        vals = {fld: src.get(fld) for fld in t["missing"] if fld in USDA_FIELDS}
        if any(v is None for v in vals.values()):
            remain.append({**_r(t), "reason": "analog thiếu trường sau khi chọn"})
            continue
        filled[t["id"]] = {
            "vals": vals,
            "source_ref": (
                f"Ước tính: {', '.join(vals)} lấy từ món tương tự USDA #{fid} "
                f"'{src['desc']}' (LLM chọn analog theo nghĩa, {note}); "
                f"NIN 2017 mã {t['code']} không đo các trường này. R2 cần duyệt."
            ),
        }
        print(
            f"  ✓ {t['name_vi'][:26]:26s} → #{fid} {src['desc'][:34]:34s} | "
            + " ".join(f"{k}={v:g}" for k, v in vals.items())
            + f" (conf {conf})"
        )

    print(
        f"\nLấp được: {len(filled)} | Còn lại (LLM null/thiếu ứng viên): {len(remain)}"
        + (f" | Chưa thử (hết quota): {len(untouched)}" if untouched else "")
    )

    if not args.apply:
        print("(--pilot: không ghi)")
        return

    _write(filled, remain)


def _r(t: dict) -> dict:
    return {"id": t["id"], "name_vi": t["name_vi"], "name_en": t["name_en"], "code": t["code"]}


def _write(filled: dict[str, dict], remain: list[dict]) -> None:
    path = SEEDS / "food_items.csv"
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    header = list(rows[0].keys())
    nin_by_code = {d["code"]: d for d in json.loads(NIN_JSON.read_text(encoding="utf-8"))}

    for row in rows:
        info = filled.get(row["id"])
        if info is None:
            continue
        code_m = re.search(r"ma (\d+)", row.get("source_ref") or "")
        nin = nin_by_code.get(code_m.group(1)) if code_m else None
        if nin is None:
            continue
        # Macro/khoáng có sẵn trong NIN → điền từ NIN (số thật của NIN).
        nin_map = {
            "kcal_100g": "enerc_kcal",
            "protein_g": "procnt_g",
            "carb_g": "chocdf_g",
            "fat_g": "fat_g",
            "fiber_g": "fibc_g",
            "na_mg": "na_mg",
            "k_mg": "k_mg",
            "p_mg": "p_mg",
        }
        for col, ninkey in nin_map.items():
            if (row.get(col) or "").strip():
                continue
            if col in info["vals"]:
                row[col] = f"{info['vals'][col]:g}"  # từ USDA analog
            elif nin.get(ninkey) is not None:
                row[col] = f"{nin[ninkey]:g}"  # từ NIN thật
        row["source"] = "estimated"
        row["is_estimated"] = "TRUE"
        row["source_ref"] = info["source_ref"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)

    # Append để chạy theo lô không ghi đè lô trước.
    rem_path = SEEDS / "food_items.llm_analog_unresolved.csv"
    fields = ["id", "name_vi", "name_en", "code", "reason"]
    new_file = not rem_path.exists()
    with open(rem_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        w.writerows(remain)
    print(f"Đã ghi food_items.csv (+{len(filled)} dòng) và append {rem_path.name} (+{len(remain)} còn lại)")


if __name__ == "__main__":
    main()
