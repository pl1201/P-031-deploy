#!/usr/bin/env python3
"""Phân loại 355 dòng trống trong `food_items.chua_co_so_lieu.csv` (DAT-13).

Chạy: python scripts/classify_food_gap_composite.py

Bối cảnh: 355 dòng này chỉ có tên, KHÔNG có bất kỳ số liệu hay `source_ref`
nào (xác nhận bằng tay 2026-08-10). Không thể tính bằng công thức Atwater
(cần biết trước protein/carb/fat) và không thể "phân rã thành nguyên liệu"
một cách tự động, vì đây không phải công thức món — phần lớn là NGUYÊN LIỆU
ĐƠN (rau, củ, cá, thịt) không có gì để phân rã.

Script này CHỈ PHÂN LOẠI theo từ khoá tên món — không tính, không đoán số,
không ghi `source`/`source_ref` nào — để R2 quyết định hướng xử lý cho từng
nhóm:

  - "nguyên liệu thô": không có công thức để tính. Đường duy nhất là tra lại
    NIN/USDA cho đúng thực phẩm đó.
  - "chế biến/tổng hợp": CÓ THỂ phân rã thành nguyên liệu + gram nếu có công
    thức tham khảo THẬT (sách nấu ăn định lượng, tiêu chuẩn NIN) — nhưng
    công thức phải có nguồn, không được suy đoán tỷ lệ (RULE-2). Chuẩn bị
    trước danh sách này để R2 xác nhận nguồn công thức, KHÔNG tự chạy phân
    rã ở đây.

Phân loại dựa trên từ khoá tên — là heuristic, không tuyệt đối. In danh sách
đầy đủ để R2 tự mắt kiểm tra, không âm thầm tin theo.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
GAP_FILE = ROOT / "data" / "quarantine" / "food_items.chua_co_so_lieu.csv"
OUT_FILE = ROOT / "docs" / "DAT-13-phan-loai-355-dong-trong.md"

# Từ khoá cho thấy đây là món ĐÃ chế biến/nhiều thành phần — có khả năng phân
# rã thành nguyên liệu+gram nếu tìm được công thức tham khảo thật. Danh sách
# rút ra từ đọc thủ công toàn bộ 355 tên (không suy đoán hàng loạt).
COMPOSITE_MARKERS: tuple[str, ...] = (
    "bánh chưng",
    "bánh giò",
    "bánh cuốn",
    "bánh bao",
    "bánh trôi",
    "bánh rán",
    "bánh tôm",
    "bánh tẻ",
    "bánh dẻo",
    "bánh nướng",
    "bánh khúc",
    "bánh gai",
    "bánh khoai",
    "bánh khoái",
    "bánh mì xíu mại",
    "bánh cốm",
    "bánh phu thê",
    "bánh chín tầng mây",
    "bánh bèo",
    "bánh bột lọc",
    "bánh chay",
    "bánh gio",
    "bún chả",
    "bún bò",
    "bún cua",
    "bún đậu",
    "bún ốc",
    "bún nem",
    "bún dọc mùng",
    "phở bò",
    "phở gà",
    "cháo lòng",
    "cháo sườn",
    "cháo trai",
    "chè ",
    "xôi ",
    "miến lươn",
    "miến ngan",
    "nem rán",
    "nem lụi",
    "cơm rang",
    "gà tần",
    "mỳ xào",
    "nộm",
    "giò lụa",
    "giò bò",
    "giò thủ",
    "chả quế",
    "chả lá lốt",
    "chả cá",
    "dồi lợn",
    "lạp xường",
    "dăm bông",
    "caramen",
    "mì ăn liền",
    "bánh phồng tôm",
    "kẹo ",
    "mứt ",
    "bánh bích",
    "bánh sô cô la",
    "bánh thỏi sô cô la",
    "bánh kem",
    "bánh quế",
    "bánh đậu xanh",
    "thịt bò hộp",
    "thịt gà hộp",
    "thịt lợn hộp",
    "cá thu hộp",
    "cá trích hộp",
    "hầm",
    "xiên nướng",
    "bánh bao nhân",
    "bánh đa nem",
    "bánh đúc",
    "thịt lợn, thịt bò xay hộp",
    "ruốc",
    "chả",
)


def classify(name: str) -> str:
    low = name.lower()
    return "che_bien" if any(marker in low for marker in COMPOSITE_MARKERS) else "nguyen_lieu_tho"


def main() -> int:
    with open(GAP_FILE, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    groups: dict[str, list[str]] = {"nguyen_lieu_tho": [], "che_bien": []}
    for row in rows:
        groups[classify(row["name_vi"])].append(row["name_vi"])

    print(f"Tổng: {len(rows)} dòng")
    print(f"  Nguyên liệu thô (không có công thức để tính): {len(groups['nguyen_lieu_tho'])}")
    print(f"  Chế biến/tổng hợp (có thể phân rã NẾU có công thức nguồn):  {len(groups['che_bien'])}")

    lines = [
        "# DAT-13 — Phân loại 355 dòng trống trong `food_items.csv`",
        "",
        "> Sinh tự động bởi `scripts/classify_food_gap_composite.py` — heuristic theo",
        "> từ khoá tên, KHÔNG tuyệt đối. R2 tự kiểm tra trước khi dùng để lên kế hoạch.",
        "",
        "Cả 355 dòng đều **trống hoàn toàn** (không số liệu, không `source_ref`) —",
        "xác nhận bằng tay 2026-08-10. Không tính được bằng công thức Atwater (cần",
        "biết trước protein/carb/fat) và không tự động phân rã được vì phần lớn là",
        "nguyên liệu đơn, không phải công thức món.",
        "",
        f"## Nhóm A — Nguyên liệu thô ({len(groups['nguyen_lieu_tho'])} dòng)",
        "",
        'Không có gì để "phân rã" — mỗi dòng là MỘT thực phẩm. Đường duy nhất là',
        "tra lại đúng thực phẩm đó trong NIN 2017 hoặc USDA FoodData Central.",
        "",
    ]
    lines += [f"- {name}" for name in groups["nguyen_lieu_tho"]]
    lines += [
        "",
        f"## Nhóm B — Chế biến/tổng hợp ({len(groups['che_bien'])} dòng)",
        "",
        "CÓ THỂ phân rã thành nguyên liệu + gram nếu R2 xác nhận được công thức",
        "tham khảo THẬT (sách nấu ăn định lượng, tiêu chuẩn NIN, hoặc nguồn tương",
        "đương). Không được để LLM tự suy đoán tỷ lệ nguyên liệu (RULE-1/RULE-2) —",
        "mọi công thức dùng để tính phải dẫn được nguồn, giống hệt cách `dishes.csv`",
        "hiện tại yêu cầu `source_ref` cho từng nguyên liệu.",
        "",
    ]
    lines += [f"- {name}" for name in groups["che_bien"]]
    lines.append("")

    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nĐã ghi báo cáo đầy đủ: {OUT_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
