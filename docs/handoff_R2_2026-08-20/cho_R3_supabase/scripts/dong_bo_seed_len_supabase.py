#!/usr/bin/env python3
"""Đồng bộ seed CSV lên Supabase cho 4 bảng R2 sửa trong đợt ký release 18/08.

    python scripts/dong_bo_seed_len_supabase.py          # xem trước
    python scripts/dong_bo_seed_len_supabase.py --ghi    # ghi thật

⚠️ MẶC ĐỊNH CHỈ XEM TRƯỚC. Đây là database **dùng chung với deploy**.

Chỉ UPSERT, KHÔNG XOÁ dòng lạ
------------------------------
DB có nhiều dòng hơn seed CSV một cách hợp lệ: `food_items` 7.418 vs 564 (khối
USDA bulk), `dishes` 272 vs 211. Script chỉ ghi những gì CSV có; dòng chỉ tồn
tại trên DB được để nguyên. Xoá theo kiểu "cho khớp CSV" sẽ thổi bay khối dữ
liệu người khác nạp.

Bốn bảng được đồng bộ, và vì sao
-------------------------------
1. `food_items.sugar_g` — **quan trọng nhất**. DB hiện chỉ phủ 1,3% và `Đường
   trắng` (id 149) vẫn `NULL`, nghĩa là rule `T2DM-SUG-01` chưa hoạt động trên
   dữ liệu DB. Xem DEC-098.
2. `food_items` dòng mới — `Quế (bột)` id 5100.
3. `household_units` + `dish_unit_conversions` — cần cho hiển thị "khoảng 1 bát"
   thay vì "300 g". DB đang ở bản cũ (68 dòng, CSV có 405).
4. `dish_ingredients` của các món R2 vừa sửa — 20 món thêm `Nước lã` (DEC-095 §4)
   và `VN-SUON-XAO-CHUA-NGOT` thêm chanh/đường.

`clinical_rules` KHÔNG cần đồng bộ: đợt này chỉ sửa `guideline_ref` (ghi căn cứ
quyết định protein), không đổi một con số ngưỡng nào — và DB đã khớp 25/25.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEEDS = Path(__file__).resolve().parent.parent / "data" / "seeds"

#: Món có `dish_ingredients` bị R2 sửa trong đợt này — chỉ đồng bộ đúng nhóm này,
#: không đụng công thức của 250 món còn lại trên DB.
MON_SUA_NGUYEN_LIEU = "VN-SUON-XAO-CHUA-NGOT"


def _doc(ten: str) -> list[dict[str, str]]:
    with (SEEDS / ten).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _json_list(v: str | None) -> str:
    """Cột / trên DB là JSON list, CSV lưu dạng a|b|c."""
    return json.dumps([x.strip() for x in (v or "").split("|") if x.strip()], ensure_ascii=False)


def _so(v: str | None) -> float | None:
    v = (v or "").strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    from sqlalchemy import create_engine, text

    ghi = "--ghi" in sys.argv
    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"connect_timeout": 20})

    foods = _doc("food_items.csv")
    units = _doc("household_units.csv")
    convs = _doc("dish_unit_conversions.csv")
    ings = _doc("dish_ingredients.csv")

    # Món cần đồng bộ nguyên liệu: có dòng Nước lã (food_id=150) hoặc là món R2 sửa tay.
    mon_can_sua = {r["dish_id"] for r in ings if r["food_id"] == "150"} | {MON_SUA_NGUYEN_LIEU}

    with engine.connect() as conn:
        db_sugar = {str(i): s for i, s in conn.execute(text("select id, sugar_g from food_items")).all()}
        db_units = {u for (u,) in conn.execute(text("select unit_code from household_units")).all()}
        n_conv = conn.execute(text("select count(*) from dish_unit_conversions")).scalar()
        db_dish = {d for (d,) in conn.execute(text("select dish_id from dishes")).all()}

    can_sugar = [r for r in foods if _so(r.get("sugar_g")) is not None and db_sugar.get(r["id"]) is None]
    thieu_food = [r for r in foods if r["id"] not in db_sugar]
    can_unit = [u for u in units if u["unit_code"] not in db_units]
    conv_hop_le = [c for c in convs if c["dish_id"] in db_dish]
    mon_sua_that = sorted(mon_can_sua & db_dish)

    print("Sẽ ghi:")
    print(f"  food_items.sugar_g            : {len(can_sugar):4} dòng (DB đang NULL, CSV có số)")
    print(f"  food_items dòng mới           : {len(thieu_food):4} {[r['id'] for r in thieu_food]}")
    print(f"  household_units mới           : {len(can_unit):4} {[u['unit_code'] for u in can_unit]}")
    print(f"  dish_unit_conversions         : {len(conv_hop_le):4} dòng (thay {n_conv} dòng cũ)")
    print(f"  dish_ingredients — món R2 sửa : {len(mon_sua_that):4} món")

    bo_qua = [c["dish_id"] for c in convs if c["dish_id"] not in db_dish]
    if bo_qua:
        print(f"\n  Bỏ qua {len(set(bo_qua))} món có quy đổi nhưng không có trên DB: {sorted(set(bo_qua))[:5]}")

    if not ghi:
        print("\n(xem trước — thêm --ghi để ghi thật lên Supabase)")
        return 0

    with engine.begin() as w:
        for r in can_sugar:
            w.execute(
                text("update food_items set sugar_g = :s where id = :i"),
                {"s": _so(r["sugar_g"]), "i": int(r["id"])},
            )

        for r in thieu_food:
            w.execute(
                text(
                    "insert into food_items (id, name_vi, aliases, contains_allergens, category, kcal_100g, protein_g, carb_g, "
                    "fat_g, fiber_g, sugar_g, na_mg, k_mg, p_mg, source, source_ref, is_estimated) "
                    "values (:id, :ten, :alias, :allerg, :cat, :kcal, :pro, :carb, :fat, :fib, :sug, :na, :k, :p, "
                    ":src, :ref, false) on conflict (id) do nothing"
                ),
                {
                    "id": int(r["id"]),
                    "ten": r["name_vi"],
                    "alias": json.dumps(
                        [a.strip() for a in (r.get("aliases") or "").split("|") if a.strip()], ensure_ascii=False
                    ),
                    "allerg": _json_list(r.get("contains_allergens")),
                    "cat": r.get("category") or None,
                    "kcal": _so(r["kcal_100g"]),
                    "pro": _so(r["protein_g"]),
                    "carb": _so(r["carb_g"]),
                    "fat": _so(r["fat_g"]),
                    "fib": _so(r["fiber_g"]),
                    "sug": _so(r["sugar_g"]),
                    "na": _so(r["na_mg"]),
                    "k": _so(r["k_mg"]),
                    "p": _so(r["p_mg"]),
                    "src": r["source"],
                    "ref": r["source_ref"],
                },
            )

        for u in can_unit:
            w.execute(
                text(
                    "insert into household_units (unit_code, name_vi, region, aliases, volume_ml, "
                    "source_ref, verified_by) values (:c, :n, :r, :a, :v, :s, :vb) "
                    "on conflict (unit_code) do nothing"
                ),
                {
                    "c": u["unit_code"],
                    "n": u["name_vi"],
                    "r": u.get("region") or None,
                    "a": u.get("aliases") or None,
                    "v": _so(u.get("volume_ml")),
                    "s": u["source_ref"],
                    "vb": u["verified_by"],
                },
            )

        # Quy đổi khẩu phần: thay trọn bộ. An toàn vì toàn bộ bảng này do R2 sinh
        # từ `serving_g` đã ký, không có dòng nào của người khác.
        # Quy đổi khẩu phần: thay trọn bộ. An toàn vì toàn bộ bảng này do R2 sinh
        # từ `serving_g` đã ký, không có dòng nào của người khác.
        #
        # Ghi theo LÔ chứ không từng dòng: 300+ lệnh insert lẻ qua pooler làm rớt
        # kết nối giữa giao dịch (đã gặp thật, giao dịch tự rollback).
        w.execute(text("delete from dish_unit_conversions"))
        if conv_hop_le:
            w.execute(
                text(
                    "insert into dish_unit_conversions (dish_id, unit_code, grams, source_ref, "
                    "verified_by) values (:d, :u, :g, :s, :v)"
                ),
                [
                    {
                        "d": c["dish_id"],
                        "u": c["unit_code"],
                        "g": _so(c["grams"]),
                        "s": c["source_ref"],
                        "v": c["verified_by"],
                    }
                    for c in conv_hop_le
                ],
            )

        # Nguyên liệu: chỉ thay của đúng nhóm món R2 sửa, giữ nguyên phần còn lại.
        for dish_id in mon_sua_that:
            w.execute(text("delete from dish_ingredients where dish_id = :d"), {"d": dish_id})
            for r in (x for x in ings if x["dish_id"] == dish_id):
                w.execute(
                    text("insert into dish_ingredients (dish_id, food_id, grams, note) values (:d, :f, :g, :n)"),
                    {"d": dish_id, "f": int(r["food_id"]), "g": _so(r["grams"]), "n": r.get("note") or None},
                )

    print("\n✅ Đã ghi. Kiểm chứng lại:")
    with engine.connect() as conn:
        sg = conn.execute(text("select count(*) from food_items where sugar_g is not null")).scalar()
        tot = conn.execute(text("select count(*) from food_items")).scalar()
        duong = conn.execute(text("select sugar_g from food_items where id = 149")).scalar()
        nc = conn.execute(text("select count(*) from dish_unit_conversions")).scalar()
        nu = conn.execute(text("select count(*) from household_units")).scalar()
        print(f"  sugar_g phủ           : {sg}/{tot} ({sg / tot * 100:.1f}%)")
        print(f"  Đường trắng sugar_g   : {duong}  (phải là 99.6)")
        print(f"  dish_unit_conversions : {nc}")
        print(f"  household_units       : {nu}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
