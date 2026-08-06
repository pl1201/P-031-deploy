#!/usr/bin/env python3
"""Ghép thủ công (có kiểm chứng từng dòng) dữ liệu từ `purine_db_reference.csv`
vào các món ăn Việt Nam curated (id 1-152) trong `food_items.csv` còn thiếu
`purine_mg`.

Ticket: DAT-14. LLM: NO — mapping do người review thủ công, KHÔNG suy đoán.

NGUYÊN TẮC CHỌN (RULE-2/DEC-008 — "để trống còn hơn tích hợp sai"):
  - CHỈ map khi cùng loài/loại thực phẩm rõ ràng, không đoán theo tên gần
    giống. VD: "cải xanh" (mustard greens, Brassica juncea) bị bỏ qua vì các
    dòng "mustard spinach"/"qing-geng-cai" trong bảng nguồn thực chất là loài
    khác (Brassica rapa var. perviridis / bok choy), dễ nhầm.
  - Ưu tiên nguồn Nhật/Trung Quốc (nonNAm) hơn Bắc Mỹ khi cả hai có, vì cách
    chế biến/loài gần thực phẩm Việt Nam hơn (cá, hải sản, rau, đậu, gia vị
    lên men) — nhưng LUÔN ghi rõ nước gốc, không giả vờ đây là số đo tại VN.
  - Khi lệch trạng thái sống/chín rõ rệt so với tên món (VD "luộc" nhưng
    nguồn chỉ có "raw") → BỎ QUA, vì luộc có thể làm giảm purine đáng kể
    (purine tan trong nước), không suy đoán mức giảm.
  - Khi 1 thực phẩm có nhiều biến thể purine dao động rộng (VD xúc xích công
    nghiệp 49.9-169.5 mg tuỳ loại) → vẫn ghi 1 giá trị đại diện (nguồn rõ
    ràng nhất) NHƯNG note nêu rõ dải dao động, không trình bày như số chắc
    chắn duy nhất.

Nguồn gốc bảng: "USDA and ODS-NIH Database for the Purine Content of Common
Foods" (Release 2.0, 2025) — xem `data/PURINEDATABASEANDDATASOURCES2025.xlsx`
và `scripts/extract_purine_db.py`.

Chạy: python scripts/map_purine_to_food_items.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOOD_ITEMS = ROOT / "data" / "seeds" / "food_items.csv"

SOURCE_TAG = "USDA/ODS-NIH Purine DB R2.0 (2025)"

# food_id -> (purine_mg_100g, mo_ta_nguon_goc, note)
# `note` LUÔN ghi rõ đây là proxy (loài/nước khác), không phải đo trên mẫu VN.
MAPPING: dict[str, tuple[float, str, str]] = {
    "11": (17.0, "Sweet potato, raw [Japan]", "Khoai lang. Đo trên mẫu Nhật Bản."),
    "12": (6.5, "Potato, raw [Japan]", "Khoai tây. Đo trên mẫu Nhật Bản."),
    "13": (1.8, "Taro [Japan]", "Khoai môn/khoai sọ. Đo trên mẫu Nhật Bản."),
    "22": (
        106.4,
        "Beef shin, raw [Japan]",
        "Thịt bò bắp (phần bắp/ống chân) — 'shin' là phần thịt tương đương trong butchery Anh. Đo trên mẫu Nhật Bản.",
    ),
    "28": (119.2, "Pork heart, raw [Japan]", "Tim lợn. Đo trên mẫu Nhật Bản."),
    "32": (
        49.9,
        "Frankfurter [Japan]",
        "Xúc xích — PROXY, dao động RỘNG tuỳ loại/thành phần: 49.9 (Nhật) đến 114.9-169.5 (Bắc Mỹ, bò/thịt hỗn hợp). Dùng giá trị thấp nhất tìm được, KHÔNG đại diện mọi loại xúc xích.",
    ),
    "33": (0.0, "Egg, chicken, raw [Japan]", "Trứng gà nguyên quả. Đo trên mẫu Nhật Bản."),
    "36": (0.0, "Egg, quail, raw [Japan]", "Trứng cút nguyên quả. Đo trên mẫu Nhật Bản."),
    "39": (103.2, "Carp, raw [Japan]", "Cá chép. Đo trên mẫu Nhật Bản."),
    "40": (
        205.2,
        "Catfish, farmed, raw [USA]",
        "Cá basa (Pangasius) — PROXY cùng bộ cá da trơn (Siluriformes) nhưng khác loài (catfish Mỹ = Ictalurus punctatus). Cần R2 xác nhận độ phù hợp.",
    ),
    "53": (
        145.4,
        "Clams, raw [Japan]",
        "Hến — PROXY nhóm ngao/hến nói chung (dải 110.2 Trung Quốc - 145.4 Nhật - 136.0 Bắc Mỹ), không phải đúng loài hến VN.",
    ),
    "57": (21.91, "Soy milk [Japan]", "Sữa đậu nành. Đo trên mẫu Nhật Bản."),
    "62": (
        57.4,
        "Bean sprouts, with bean, raw [Japan]",
        "Giá đỗ (kèm hạt đậu). Đo trên mẫu Nhật Bản — bản 'không hạt' thấp hơn (35.0).",
    ),
    "71": (3.2, "Cabbage, raw [Japan]", "Cải bắp/bắp cải thường. Đo trên mẫu Nhật Bản."),
    "72": (47.1, "Garland chrysanthemum [Japan]", "Cải cúc/tần ô — khớp tên trực tiếp. Đo trên mẫu Nhật Bản."),
    "78": (39.4, "Coriander [Japan]", "Rau mùi/ngò rí. Đo trên mẫu Nhật Bản."),
    "84": (70.0, "Broccoli, raw [Japan]", "Súp lơ xanh/bông cải xanh, dạng sống. Đo trên mẫu Nhật Bản."),
    "86": (2.1, "Carrots, raw [Japan]", "Cà rốt. Đo trên mẫu Nhật Bản."),
    "87": (1.7, "Radish root, Japanese [Japan]", "Củ cải trắng — daikon, khớp loại trực tiếp. Đo trên mẫu Nhật Bản."),
    "91": (56.7, "Pumpkin, raw [Japan]", "Bí đỏ/bí ngô. Đo trên mẫu Nhật Bản."),
    "95": (9.4, "Cucumber, raw [Japan]", "Dưa chuột/dưa leo. Đo trên mẫu Nhật Bản."),
    "96": (7.5, "Green beans [Japan]", "Đậu cove/đậu que. Đo trên mẫu Nhật Bản."),
    "102": (2.2, "Onions, raw [Japan]", "Hành tây. Đo trên mẫu Nhật Bản."),
    "103": (3.0, "Bananas, raw [Japan]", "Chuối tiêu/chuối già. Đo trên mẫu Nhật Bản."),
    "119": (18.4, "Avocado, raw [Japan]", "Bơ/trái bơ. Đo trên mẫu Nhật Bản."),
    "126": (
        5.2,
        "Yogurt (not further specified) [Japan]",
        "Sữa chua — PROXY loại không rõ chi tiết. Bản Bắc Mỹ 'plain' cho 7.0 (dải 5.2-7.0).",
    ),
    "133": (36.3, "Sesame [Japan]", "Vừng/mè. Đo trên mẫu Nhật Bản."),
    "137": (93.1, "Sauce, fish [Japan]", "Nước mắm — khớp loại trực tiếp (fish sauce). Đo trên mẫu Nhật Bản."),
    "143": (
        50.25,
        "Soy sauce made from soy and wheat (shoyu) [Japan]",
        "Nước tương/xì dầu. Đo trên mẫu Nhật Bản — shoyu (đậu nành+lúa mì) là loại phổ biến nhất, gần với nước tương VN.",
    ),
    "148": (134.4, "Sauce, oyster [Japan]", "Dầu hào — khớp loại trực tiếp. Đo trên mẫu Nhật Bản."),
    "151": (17.0, "Garlic, raw [Japan]", "Tỏi. Đo trên mẫu Nhật Bản."),
    "152": (2.3, "Ginger root, raw [Japan]", "Gừng. Đo trên mẫu Nhật Bản."),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(FOOD_ITEMS, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = 0
    skipped_already_filled = 0
    for row in rows:
        fid = row["id"]
        if fid not in MAPPING:
            continue
        if (row.get("purine_mg") or "").strip():
            skipped_already_filled += 1
            continue
        purine, source_desc, note = MAPPING[fid]
        row["purine_mg"] = str(purine)
        row["purine_source_ref"] = f"{SOURCE_TAG} — {source_desc}. {note}"
        updated += 1

    print(f"Se cap nhat: {updated} dong")
    if skipped_already_filled:
        print(f"Da bo qua (da co san purine_mg): {skipped_already_filled} dong")
    unmatched = set(MAPPING) - {r["id"] for r in rows}
    if unmatched:
        print(f"CANH BAO: {len(unmatched)} food_id trong MAPPING khong ton tai trong food_items.csv: {unmatched}")

    if args.dry_run:
        print("(--dry-run: chua ghi file)")
        return

    with open(FOOD_ITEMS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Da ghi {FOOD_ITEMS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
