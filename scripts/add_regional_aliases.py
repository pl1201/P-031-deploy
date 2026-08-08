#!/usr/bin/env python3
"""Bổ sung `aliases` tên vùng miền cho `food_items.csv` — BE-07/CLN-07.

Vì sao đây là việc đáng làm nhất trong luồng OOV: matcher (`src/clinical/
matching.py`) chỉ khớp được cái nó biết tên. Hiện chỉ **30/461** dòng NIN có
alias, nên một bệnh nhân miền Nam gõ "thịt heo", "trái thơm", "khoai mì" là
trượt sạch — dù CSDL có đủ cả ba (dưới tên "thịt lợn", "dứa", "sắn"). Nửa ngày
gõ alias rẻ hơn mọi cách mở rộng dữ liệu khác.

RULE-2 và alias
---------------
Alias **không phải số liệu dinh dưỡng** nên không cần `source_ref` — nó là dữ
kiện ngôn ngữ, không phải phép đo. Nhưng vẫn phải đúng: gán nhầm alias làm
matcher trả về sai thực phẩm, và sai đó đi thẳng vào phép tính. Nên bảng dưới
đây CHỈ gồm cặp đồng nghĩa vùng miền đã được dùng phổ biến và không gây nhập
nhằng — cố ý bỏ qua các cặp mơ hồ (xem `_DA_CAN_NHAC_VA_LOAI`).

Chạy:
  python scripts/add_regional_aliases.py --dry-run   # xem trước
  python scripts/add_regional_aliases.py --apply
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"

# Thay thế Ở MỨC TỪ trong tên món. Khoá = từ trong tên NIN (thường là cách gọi
# miền Bắc), giá trị = các cách gọi tương đương ở vùng khác.
#
# Chỉ đưa vào đây cặp mà hai từ chỉ CÙNG MỘT thực phẩm trong mọi ngữ cảnh ẩm
# thực thông thường.
SYNONYMS: dict[str, tuple[str, ...]] = {
    "lợn": ("heo",),
    "ngô": ("bắp",),
    "lạc": ("đậu phộng",),
    "vừng": ("mè",),
    "dứa": ("thơm", "khóm"),
    "sắn": ("khoai mì",),
    "cải bắp": ("bắp cải",),
    "súp lơ": ("bông cải",),
    "rau mùi": ("ngò rí", "ngò"),
    "mướp đắng": ("khổ qua",),
    "rau ngót": ("bồ ngót",),
    "cá quả": ("cá lóc", "cá chuối"),
    "củ đậu": ("củ sắn",),
    "dọc mùng": ("bạc hà",),
    "quả na": ("mãng cầu ta",),
    "bí đao": ("bí xanh",),
    "bí ngô": ("bí đỏ",),
    "thìa là": ("thì là",),
    "đậu bắp": ("mướp tây",),
    "quả roi": ("mận",),
    "hạt sen": ("hột sen",),
    "đậu đũa": ("đậu que",),
}

# Đã cân nhắc và CỐ Ý LOẠI — ghi lại để người sau không phải nghĩ lại:
#   "mận"      : miền Bắc là quả mận (plum), miền Nam là quả roi (rose apple).
#                Một chiều thì đúng, chiều ngược lại thì sai — bỏ.
#   "bắp"→"ngô": "bắp" còn nghĩa "bắp thịt" ("thịt bò bắp") — dễ khớp nhầm.
#   "trái"/"quả": chỉ là từ đếm, matcher đã bỏ ở tầng token rồi.
_DA_CAN_NHAC_VA_LOAI = ("mận", "bắp→ngô", "trái/quả")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFC", str(text)).strip().lower()
    return re.sub(r"\s+", " ", text)


def sinh_alias(name_vi: str) -> list[str]:
    """Sinh các cách gọi khác của một tên món.

    Thay ở mức từ và có ranh giới từ, để "lợn" không khớp vào giữa một từ khác.
    """
    base = _norm(name_vi)
    out: list[str] = []
    for goc, thay_the in SYNONYMS.items():
        if not re.search(rf"(?<![\wÀ-ỹ]){re.escape(goc)}(?![\wÀ-ỹ])", base):
            continue
        # Từ ghép nuốt từ đơn: "bí ngô" (quả bí đỏ) chứa "ngô" nhưng KHÔNG phải
        # ngô. Nếu tên chứa một khoá DÀI HƠN mà khoá ngắn này nằm trong đó, thì
        # khoá ngắn không được thay. Lỗi thật đã sinh ra trước khi có luật này:
        # "Bí ngô" → "bí bắp".
        if _bi_khoa_dai_hon_nuot(goc, base):
            continue
        for tt in thay_the:
            alias = re.sub(rf"(?<![\wÀ-ỹ]){re.escape(goc)}(?![\wÀ-ỹ])", tt, base)
            if alias == base or _co_tu_lap_lien_nhau(alias):
                # "Ngô bắp tươi" -> "bắp bắp tươi": tên gốc đã chứa sẵn từ thay
                # thế. Alias kiểu này vô nghĩa và làm bẩn dữ liệu.
                continue
            out.append(alias)
    return out


def _co_tu_lap_lien_nhau(text: str) -> bool:
    tu = text.split()
    return any(a == b for a, b in zip(tu, tu[1:], strict=False))


def _bi_khoa_dai_hon_nuot(goc: str, base: str) -> bool:
    """True khi `goc` chỉ xuất hiện với tư cách một phần của từ ghép dài hơn."""
    for khac in SYNONYMS:
        if khac == goc or goc not in khac:
            continue
        if re.search(rf"(?<![\wÀ-ỹ]){re.escape(khac)}(?![\wÀ-ỹ])", base):
            # Kiểm tra xem còn lần xuất hiện nào của `goc` NGOÀI từ ghép không.
            con_lai = re.sub(rf"(?<![\wÀ-ỹ]){re.escape(khac)}(?![\wÀ-ỹ])", " ", base)
            if not re.search(rf"(?<![\wÀ-ỹ]){re.escape(goc)}(?![\wÀ-ỹ])", con_lai):
                return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    path = SEEDS / "food_items.csv"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)

    them = 0
    dong_doi = 0
    vi_du: list[tuple[str, list[str]]] = []

    for row in rows:
        moi = sinh_alias(row["name_vi"])
        if not moi:
            continue
        dang_co = [a for a in (row.get("aliases") or "").split("|") if a.strip()]
        dang_co_norm = {_norm(a) for a in dang_co}
        them_vao = [a for a in moi if a not in dang_co_norm]
        if not them_vao:
            continue
        row["aliases"] = "|".join([*dang_co, *them_vao])
        them += len(them_vao)
        dong_doi += 1
        if len(vi_du) < 15:
            vi_du.append((row["name_vi"], them_vao))

    print(f"Dòng được thêm alias : {dong_doi}")
    print(f"Tổng alias thêm mới  : {them}")
    print("\nVí dụ:")
    for ten, aliases in vi_du:
        print(f"  {ten:38s} -> {', '.join(aliases)}")

    if not args.apply:
        print("\n(chưa --apply nên không ghi gì)")
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nĐã ghi {path.name}")


if __name__ == "__main__":
    main()
