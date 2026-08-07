"""Merge du lieu trich tu NIN 2017 (scripts/nin2017_extracted.json) vao
data/seeds/food_items.csv theo dung quy tac RULE-2 / DEC-008 cua du an:

- KHONG fuzzy-match ten mon tu dong. Chi ghep khi ten (sau khi strip
  khoang trang thua, ha chu) TRUNG KHOP TUYET DOI voi name_vi hoac mot
  trong cac alias hien co trong CSV. Cac cap ten gan giong nhung khong
  trung khop tuyet doi duoc liet ke rieng de nguoi review, KHONG tu ghep.
- Voi mon da co trong CSV va trung ten: chi DIEN vao cac o dang TRONG
  (na_mg/k_mg/p_mg va cac truong macro con trong). KHONG ghi de gia tri
  da co. Neu gia tri da co KHAC voi PDF 2017 cho cung 1 truong (numeric
  khac nhau ro), ghi nhan xung dot vao scripts/nin2017_conflicts.md,
  KHONG tu dong sua.
- Voi mon hoan toan moi (khong khop ten voi dong nao): them dong moi,
  id tang dan tu id lon nhat hien co. Cac truong PDF khong co (sugar_g,
  purine_mg, gi_index...) de TRONG, khong dien 0.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "seeds" / "food_items.csv"
JSON_PATH = ROOT / "scripts" / "nin2017_extracted.json"
CONFLICTS_PATH = ROOT / "scripts" / "nin2017_conflicts.md"

FIELDNAMES = [
    "id", "name_vi", "aliases", "category", "kcal_100g", "protein_g",
    "carb_g", "fat_g", "fiber_g", "sugar_g", "na_mg", "k_mg", "p_mg",
    "purine_mg", "purine_source_ref", "gi_index", "gi_source",
    "gi_source_ref", "contains_allergens", "source", "source_ref",
    "is_estimated",
]

# Map truong CSV -> truong JSON trich tu PDF, chi cac truong CSV co the
# dien tu khoi (a) macro+khoang chat.
FIELD_MAP = {
    "kcal_100g": "enerc_kcal",
    "protein_g": "procnt_g",
    "carb_g": "chocdf_g",
    "fat_g": "fat_g",
    "fiber_g": "fibc_g",
    "na_mg": "na_mg",
    "k_mg": "k_mg",
    "p_mg": "p_mg",
}


def norm(s: str | None) -> str:
    if not s:
        return ""
    return " ".join(s.strip().lower().split())


def fmt_num(v: float | None) -> str:
    if v is None:
        return ""
    if v == int(v):
        return str(int(v))
    return str(v)


def load_csv() -> list[dict]:
    with CSV_PATH.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(rows: list[dict]) -> None:
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in FIELDNAMES})


def build_name_index(rows: list[dict]) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = {}
    for r in rows:
        keys = {norm(r["name_vi"])}
        for a in (r.get("aliases") or "").split("|"):
            if a.strip():
                keys.add(norm(a))
        for k in keys:
            if k:
                idx.setdefault(k, []).append(r)
    return idx


# 8 truong "loi" ma src/clinical/seeds.py doi hoi PHAI co du (khong duoc
# thieu bat ky truong nao) neu kcal_100g da duoc dien - xac nhan qua kiem
# tra thuc te: CSV goc (152 dong) khong co dong nao "nua vay" (kcal co nhung
# na/k/p thieu). Vi vay CHI kich hoat (dien so) mot dong moi/duoc merge khi
# CA 8 TRUONG deu co gia tri trong PDF - neu thieu du 1 truong, GIU dong o
# dang "chua nhap so lieu" (tat ca 8 truong deu de trong, giong quy uoc
# hien co cua du an vd id 124/145/146/150), chi dien name/source_ref lam
# placeholder cho DAT-13 lap tiep sau.
CORE_FIELDS = ["kcal_100g", "protein_g", "carb_g", "fat_g", "fiber_g", "na_mg", "k_mg", "p_mg"]


def main() -> None:
    rows = load_csv()
    items = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    name_index = build_name_index(rows)
    max_id = max(int(r["id"]) for r in rows)

    filled_count = 0
    filled_field_count = 0
    new_count = 0
    new_incomplete_count = 0
    conflicts: list[str] = []
    unmatched_new: list[dict] = []

    for item in items:
        name = item["name_vi"]
        key = norm(name)
        matches = name_index.get(key)
        if matches and len(matches) == 1:
            row = matches[0]
            # Thu tinh trang neu dien: chi dien khi ket qua cuoi cung KHONG
            # con truong loi nao trong (tranh tao dong "nua vay" pha vo
            # invariant cua src/clinical/seeds.py).
            would_be = dict(row)
            candidate_fields: dict[str, str] = {}
            for csv_field, json_field in FIELD_MAP.items():
                pdf_val = item.get(json_field)
                existing_raw = (row.get(csv_field) or "").strip()
                if existing_raw == "" and pdf_val is not None:
                    candidate_fields[csv_field] = fmt_num(pdf_val)
                    would_be[csv_field] = candidate_fields[csv_field]
                elif existing_raw != "" and pdf_val is not None:
                    try:
                        existing_val = float(existing_raw)
                    except ValueError:
                        continue
                    if abs(existing_val - pdf_val) > max(0.05 * abs(existing_val), 0.5):
                        conflicts.append(
                            f"| {name} | {csv_field} | {existing_raw} | {fmt_num(pdf_val)} "
                            f"| CSV hien tai (source={row.get('source')}, "
                            f"source_ref={row.get('source_ref')}) vs NIN 2017 ma {item['code']} tr.{item['page']} |"
                        )
            core_complete = all((would_be.get(f) or "").strip() for f in CORE_FIELDS)
            if candidate_fields and core_complete:
                for csv_field, val in candidate_fields.items():
                    row[csv_field] = val
                    filled_field_count += 1
                filled_count += 1
                note = f"NIN 2017, ma {item['code']}, tr.{item['page']}"
                if row.get("source_ref"):
                    if "NIN 2017" not in row["source_ref"]:
                        row["source_ref"] = row["source_ref"] + f"; bo sung: {note}"
                else:
                    row["source_ref"] = note
                    row["source"] = row.get("source") or "NIN"
            # neu candidate_fields nhung khong core_complete: KHONG dien gi
            # ca (giu nguyen dong cu, tranh trang thai "nua vay")
        elif matches and len(matches) > 1:
            conflicts.append(
                f"| {name} | (nhieu dong trung ten) | - | - | Can review thu cong: "
                f"{len(matches)} dong CSV cung ten '{name}' - khong tu dong ghep |"
            )
        else:
            unmatched_new.append(item)

    # Them mon hoan toan moi
    new_rows: list[dict] = []
    for item in unmatched_new:
        max_id += 1
        row = {k: "" for k in FIELDNAMES}
        row["id"] = str(max_id)
        row["name_vi"] = item["name_vi"]
        row["aliases"] = ""
        row["category"] = ""  # can gan nhom thu cong sau, de trong thay vi doan

        core_vals = {}
        for csv_field, json_field in FIELD_MAP.items():
            v = item.get(json_field)
            if v is not None:
                core_vals[csv_field] = fmt_num(v)

        is_complete = all(f in core_vals for f in CORE_FIELDS)
        if is_complete:
            for csv_field, val in core_vals.items():
                row[csv_field] = val
            row["source"] = "NIN"
            row["source_ref"] = f"NIN 2017, ma {item['code']}, tr.{item['page']}"
            row["is_estimated"] = "FALSE"
        else:
            # Placeholder: chi ghi ten/nguon de tham chieu, KHONG dien so
            # lieu (tranh vi pham invariant "kcal co -> phai du 8 truong").
            row["source_ref"] = (
                f"[CHUA DU LIEU - can DAT-13] NIN 2017, ma {item['code']}, tr.{item['page']} "
                f"- PDF thieu: {', '.join(f for f in CORE_FIELDS if f not in core_vals)}"
            )
            row["is_estimated"] = "FALSE"
            new_incomplete_count += 1
        new_rows.append(row)
        new_count += 1

    rows.extend(new_rows)
    save_csv(rows)

    if conflicts:
        header = (
            "# Xung dot du lieu NIN 2017 vs food_items.csv hien tai\n\n"
            "Cac dong duoi day co gia tri KHAC nhau ro ret giua CSV hien tai va "
            "PDF NIN 2017. KHONG tu dong merge - can R2 xem xet va quyet dinh "
            "gia tri dung.\n\n"
            "| Ten mon | Cot | Gia tri cu (CSV) | Gia tri moi (NIN 2017) | Ghi chu |\n"
            "|---|---|---|---|---|\n"
        )
        CONFLICTS_PATH.write_text(header + "\n".join(conflicts) + "\n", encoding="utf-8")
    else:
        CONFLICTS_PATH.write_text(
            "# Xung dot du lieu NIN 2017 vs food_items.csv hien tai\n\n"
            "Khong phat hien xung dot so lieu ro ret nao giua CSV hien tai va "
            "PDF NIN 2017 trong lan merge nay.\n",
            encoding="utf-8",
        )

    print(f"Dong duoc dien them Na/K/P/macro: {filled_count} (tong {filled_field_count} o)")
    print(f"Dong hoan toan moi them vao: {new_count}")
    print(f"So xung dot ghi vao {CONFLICTS_PATH.name}: {len(conflicts)}")


if __name__ == "__main__":
    main()
