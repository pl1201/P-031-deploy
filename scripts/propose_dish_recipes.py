#!/usr/bin/env python3
"""LLM đề xuất công thức (nguyên liệu+gram) cho món chế biến — CHƯA R2 duyệt.

Chạy: python scripts/propose_dish_recipes.py [--apply]

Bối cảnh (DAT-13): 344 dòng `food_items.csv` còn trống, trong đó ~82 món là
"chế biến/tổng hợp" tại nhà (không tính 34 món công nghiệp — kẹo/bánh
quy/đồ hộp/mứt — vì bịa tỷ lệ nhà máy còn tệ hơn để trống). R2 xác nhận
(2026-08-10): dùng LLM đề xuất nguyên liệu+gram, R2 duyệt lại sau — đúng quy
trình đã áp dụng cho 30 món hiện có trong `dishes.csv`.

QUAN TRỌNG — đây là ĐỀ XUẤT, không phải dữ liệu đã duyệt:
- Mọi món sinh ra có `verified_by="pending"` và `note` ghi rõ "LLM đề xuất —
  CHƯA R2 duyệt, không dùng cho bệnh nhân thật cho tới khi rà xong".
- Gram là ước lượng theo khẩu phần chuẩn phổ biến (kiến thức nấu ăn phổ
  thông), KHÔNG dẫn được nguồn số liệu cụ thể — khác hẳn `food_items.csv`
  (luôn phải có `source_ref`). Đây là lý do món ở dạng "công thức" (RULE-1:
  dinh dưỡng tính từ nguyên liệu bằng Python) chứ không phải "số liệu"
  (RULE-2: số liệu phải có nguồn) — nhưng công thức vẫn cần R2 xác nhận
  gram trước khi tin.
- CHỈ dùng nguyên liệu đã có `food_id` thật trong `food_items.csv`. Món nào
  cần nguyên liệu chưa có trong CSDL bị BỎ QUA (không tự thêm food_item mới
  ở đây) — liệt kê riêng trong báo cáo để R2 quyết định có bổ sung không.
- KHÔNG kích hoạt vào `data/seeds/food_items.csv` (đó là dữ liệu ĐÃ có
  nguồn) — món mới nằm trong `dishes.csv`/`dish_ingredients.csv`, dinh
  dưỡng luôn được TÍNH LẠI từ nguyên liệu lúc cần (RULE-1), không lưu sẵn.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "seeds"
FOOD_ITEMS_PATH = SEEDS / "food_items.csv"
DISHES_PATH = SEEDS / "dishes.csv"
DISH_INGREDIENTS_PATH = SEEDS / "dish_ingredients.csv"

NOTE_PENDING = (
    "LLM de xuat nguyen lieu + gram cho khau phan chuan pho bien "
    "(khong dan duoc nguon so lieu cu the) - R2 CHUA DUYET, "
    "khong dung cho benh nhan that cho toi khi ra xong (DAT-13)"
)

# {dish_id: (ten_hien_thi, khau_phan_g, [(ten_nguyen_lieu_de_tra, gram), ...])}
# ten_nguyen_lieu_de_tra: khop theo name_vi hoac alias trong food_items.csv,
# khong phan biet hoa/thuong, khong dau cach thua.
PROPOSALS: dict[str, tuple[str, float, list[tuple[str, float]]]] = {
    "NIN-PHO-BO-CHIN": (
        "Phở bò chín",
        450,
        [
            ("Bánh phở tươi", 200),
            ("Thịt bò bắp", 70),
            ("Hành lá", 10),
            ("Rau mùi", 5),
            ("Nước mắm", 10),
            ("Muối ăn", 2),
            ("Gừng", 5),
        ],
    ),
    "NIN-PHO-BO-TAI": (
        "Phở bò tái",
        450,
        [
            ("Bánh phở tươi", 200),
            ("Thịt bò thăn", 70),
            ("Hành lá", 10),
            ("Rau mùi", 5),
            ("Nước mắm", 10),
            ("Muối ăn", 2),
            ("Gừng", 5),
        ],
    ),
    "NIN-PHO-GA": (
        "Phở gà",
        450,
        [
            ("Bánh phở tươi", 200),
            ("Thịt gà (đùi, có da)", 80),
            ("Hành lá", 10),
            ("Rau mùi", 5),
            ("Nước mắm", 10),
            ("Muối ăn", 2),
            ("Gừng", 5),
        ],
    ),
    "NIN-BUN-CHA": (
        "Bún chả",
        400,
        [
            ("Bún tươi", 200),
            ("Thịt lợn ba chỉ", 100),
            ("Nước mắm", 20),
            ("Đường trắng", 10),
            ("Tỏi", 5),
            ("Xà lách", 30),
        ],
    ),
    "NIN-BUN-DAU": (
        "Bún đậu",
        400,
        [("Bún tươi", 200), ("Đậu phụ chiên", 120), ("Mắm tôm", 15), ("Xà lách", 30), ("Rau mùi", 5)],
    ),
    "NIN-BUN-OC": (
        "Bún ốc",
        450,
        [("Bún tươi", 200), ("Cà chua", 60), ("Nước mắm", 15), ("Rau mùi", 5), ("Hành lá", 10)],
    ),
    "NIN-BUN-DOC-MUNG": (
        "Bún dọc mùng",
        450,
        [("Bún tươi", 200), ("Thịt lợn ba chỉ", 60), ("Cà chua", 40), ("Nước mắm", 15), ("Hành lá", 10)],
    ),
    "NIN-BUN-BO-NAM-BO": (
        "Bún bò Nam bộ",
        400,
        [
            ("Bún tươi", 200),
            ("Thịt bò thăn", 80),
            ("Giá đỗ", 30),
            ("Rau mùi", 5),
            ("Lạc rang", 10),
            ("Nước mắm", 15),
            ("Tỏi", 5),
        ],
    ),
    "NIN-CHAO-LONG": (
        "Cháo lòng",
        400,
        [("Cháo trắng", 300), ("Lòng lợn", 60), ("Tim lợn", 20), ("Hành lá", 10), ("Nước mắm", 5)],
    ),
    "NIN-CHAO-SUON": (
        "Cháo sườn",
        400,
        [("Cháo trắng", 320), ("Thịt lợn ba chỉ", 60), ("Hành lá", 8), ("Nước mắm", 5)],
    ),
    "NIN-COM-RANG": (
        "Cơm rang",
        350,
        [("Cơm tẻ", 250), ("Trứng gà", 55), ("Cà rốt", 30), ("Hành lá", 10), ("Dầu ăn thực vật", 10), ("Nước mắm", 5)],
    ),
    "NIN-XOI-DO-XANH": (
        "Xôi đỗ xanh",
        250,
        [("Xôi trắng", 200), ("Đậu xanh", 50)],
    ),
    "NIN-XOI-LAC": (
        "Xôi lạc",
        250,
        [("Xôi trắng", 220), ("Lạc rang", 30)],
    ),
    "NIN-XOI-NGO": (
        "Xôi ngô",
        250,
        [("Xôi trắng", 200), ("Ngô luộc", 50)],
    ),
    "NIN-NEM-RAN": (
        "Nem rán",
        200,
        [("Thịt lợn nạc", 100), ("Trứng gà", 30), ("Miến dong", 20), ("Cà rốt", 30), ("Hành lá", 10), ("Nước mắm", 10)],
    ),
    "NIN-NEM-LUI": (
        "Nem lụi",
        200,
        [("Thịt lợn nạc", 150), ("Tỏi", 5), ("Nước mắm", 10)],
    ),
    "NIN-CHA-LA-LOT": (
        "Chả lá lốt",
        200,
        [("Thịt lợn nạc", 120), ("Mỡ lợn", 20), ("Nước mắm", 10), ("Tỏi", 5)],
    ),
    "NIN-GIO-LUA": (
        "Giò lụa",
        100,
        [("Thịt lợn nạc", 95), ("Nước mắm", 5)],
    ),
    "NIN-GIO-BO": (
        "Giò bò",
        100,
        [("Thịt bò bắp", 95), ("Nước mắm", 5)],
    ),
    "NIN-CHA-QUE": (
        "Chả quế",
        100,
        [("Thịt lợn nạc", 90), ("Đường trắng", 5), ("Nước mắm", 5)],
    ),
    "NIN-CHA-QUE-LON": (
        "Chả quế lợn",
        100,
        [("Thịt lợn nạc", 90), ("Đường trắng", 5), ("Nước mắm", 5)],
    ),
    "NIN-CHA-CA-BASA": (
        "Chả cá basa",
        200,
        [("Cá basa", 180), ("Nước mắm", 10), ("Hành lá", 10)],
    ),
    "NIN-GA-TAN": (
        "Gà tần",
        400,
        [("Thịt gà (đùi, có da)", 200), ("Hạt sen", 30), ("Nấm hương", 10), ("Gừng", 5), ("Nước mắm", 10)],
    ),
    "NIN-THIT-VIT-HAM": (
        "Thịt vịt hầm",
        300,
        [("Thịt vịt", 200), ("Nước mắm", 10), ("Gừng", 5)],
    ),
    "NIN-THIT-XIEN-NUONG": (
        "Thịt xiên nướng",
        150,
        [("Thịt lợn nạc", 130), ("Tỏi", 5), ("Nước mắm", 10)],
    ),
    "NIN-NOM-TAI-LON": (
        "Nộm tai lợn",
        200,
        [("Rau mùi", 10), ("Lạc rang", 20), ("Nước mắm", 15), ("Tỏi", 3)],
    ),
    "NIN-MY-XAO": (
        "Mỳ xào",
        350,
        [("Bún tươi", 200), ("Thịt lợn nạc", 60), ("Cải bắp", 60), ("Cà rốt", 30), ("Nước mắm", 10)],
    ),
    "NIN-MIEN-LUON": (
        "Miến lươn",
        400,
        [("Miến dong", 200), ("Hành lá", 10), ("Nước mắm", 10)],
    ),
    "NIN-MIEN-NGAN": (
        "Miến ngan",
        400,
        [("Miến dong", 200), ("Thịt vịt", 100), ("Hành lá", 10), ("Nước mắm", 10)],
    ),
    "NIN-CHE-DO-DEN": (
        "Chè đỗ đen",
        250,
        [("Đậu đen", 60), ("Đường trắng", 40), ("Nước cốt dừa", 30)],
    ),
    "NIN-CHE-DO-DO": (
        "Chè đỗ đỏ",
        250,
        [("Đậu đỏ", 60), ("Đường trắng", 40), ("Nước cốt dừa", 30)],
    ),
    "NIN-CHE-DO-XANH": (
        "Chè đỗ xanh",
        250,
        [("Đậu xanh", 60), ("Đường trắng", 40), ("Nước cốt dừa", 30)],
    ),
    "NIN-CHE-HAT-SEN": (
        "Chè hạt sen",
        250,
        [("Hạt sen", 60), ("Đường trắng", 40)],
    ),
    "NIN-CHE-CHUOI": (
        "Chè chuối",
        250,
        [("Chuối tiêu", 100), ("Đường trắng", 30), ("Nước cốt dừa", 50)],
    ),
    "NIN-CHE-BUOI": (
        "Chè bưởi",
        250,
        [("Bưởi", 80), ("Đậu xanh", 40), ("Đường trắng", 40)],
    ),
    "NIN-XOI-GAC": (
        "Xôi gấc",
        250,
        [("Xôi trắng", 230), ("Đường trắng", 15)],
    ),
    "NIN-BANH-CUON": (
        "Bánh cuốn",
        200,
        [("Bột gạo tẻ Rice flour", 100), ("Thịt lợn nạc", 40), ("Nấm hương", 10), ("Nước mắm", 10)],
    ),
    "NIN-BANH-CUON-NONG-NHAN-THIT": (
        "Bánh cuốn nóng nhân thịt",
        200,
        [("Bột gạo tẻ Rice flour", 100), ("Thịt lợn nạc", 50), ("Nấm hương", 10), ("Nước mắm", 10)],
    ),
    "NIN-BANH-GIO": (
        "Bánh giò",
        200,
        [("Bột gạo tẻ Rice flour", 100), ("Thịt lợn nạc", 40), ("Nước mắm", 10)],
    ),
    "NIN-BANH-DUC": (
        "Bánh đúc",
        200,
        [("Bột gạo tẻ Rice flour", 150), ("Muối ăn", 3)],
    ),
    "NIN-BANH-DUC-NONG": (
        "Bánh đúc nóng",
        200,
        [("Bột gạo tẻ Rice flour", 150), ("Thịt lợn nạc", 30), ("Nước mắm", 5)],
    ),
    "NIN-BANH-DUC-NGUOI": (
        "Bánh đúc nguội",
        200,
        [("Bột gạo tẻ Rice flour", 150), ("Muối ăn", 3)],
    ),
    "NIN-BANH-BAO-NHAN-THIT": (
        "Bánh bao nhân thịt",
        150,
        [("Bột mì", 90), ("Thịt lợn nạc", 40), ("Trứng gà", 15)],
    ),
    "NIN-BANH-BAO-CHIEN-CO-NHAN": (
        "Bánh bao chiên có nhân",
        150,
        [("Bột mì", 90), ("Thịt lợn nạc", 40), ("Dầu ăn thực vật", 10)],
    ),
    "NIN-BANH-MI-XIU-MAI": (
        "Bánh mì xíu mại",
        250,
        [("Bánh mì", 100), ("Thịt lợn nạc", 100), ("Cà chua", 30), ("Nước mắm", 10)],
    ),
    "NIN-BANH-DA-NEM": (
        "Bánh đa nem",
        30,
        [("Bột gạo tẻ Rice flour", 30)],
    ),
    "NIN-BANH-TE": (
        "Bánh tẻ",
        150,
        [("Bột gạo tẻ Rice flour", 100), ("Thịt lợn nạc", 30), ("Nấm hương", 5)],
    ),
    "NIN-BANH-KHUC": (
        "Bánh khúc",
        150,
        [("Xôi trắng", 100), ("Đậu xanh", 30), ("Thịt lợn ba chỉ", 20)],
    ),
    "NIN-BANH-GIO-CHAY": (
        "Bánh chay",
        150,
        [("Bột mì", 80), ("Đậu xanh", 40), ("Đường trắng", 15)],
    ),
    "NIN-BANH-TROI": (
        "Bánh trôi",
        150,
        [("Bột mì", 100), ("Đường trắng", 20)],
    ),
    "NIN-BANH-RAN-BOC-DUONG": (
        "Bánh rán bọc đường",
        150,
        [("Bột mì", 80), ("Đậu xanh", 30), ("Đường trắng", 20), ("Dầu ăn thực vật", 15)],
    ),
    "NIN-BANH-KHOAI": (
        "Bánh khoai",
        200,
        [("Khoai lang", 150), ("Bột mì", 40), ("Dầu ăn thực vật", 10)],
    ),
    "NIN-BANH-KHOAI-SO-CHIEN": (
        "Bánh khoai sọ chiên",
        200,
        [("Khoai môn", 150), ("Bột mì", 40), ("Dầu ăn thực vật", 10)],
    ),
    "NIN-BANH-KHOAI-MIEN-TRUNG": (
        "Bánh khoái",
        200,
        [("Bột gạo tẻ Rice flour", 100), ("Thịt lợn nạc", 40), ("Trứng gà", 30), ("Giá đỗ", 30)],
    ),
    "NIN-BANH-BEO": (
        "Bánh bèo",
        150,
        [("Bột gạo tẻ Rice flour", 100), ("Tôm biển", 30), ("Nước mắm", 10)],
    ),
    "NIN-BANH-BOT-LOC": (
        "Bánh bột lọc",
        150,
        [("Bột sắn dây", 100), ("Tôm biển", 30), ("Thịt lợn ba chỉ", 20)],
    ),
    "NIN-BANH-TOM": (
        "Bánh tôm",
        150,
        [("Tôm biển", 60), ("Bột mì", 60), ("Khoai lang", 30), ("Dầu ăn thực vật", 15)],
    ),
    "NIN-BANH-CHUNG": (
        "Bánh chưng",
        300,
        [("Xôi trắng", 180), ("Đậu xanh", 60), ("Thịt lợn ba chỉ", 60)],
    ),
    "NIN-BANH-GIO-BANH": (
        "Bánh gio",
        150,
        [("Xôi trắng", 140), ("Đường trắng", 10)],
    ),
    "NIN-BANH-GAI": (
        "Bánh gai",
        150,
        [("Bột gạo nếp Glutinous rice flour", 90), ("Đậu xanh", 40), ("Đường trắng", 15)],
    ),
    "NIN-BANH-COM": (
        "Bánh cốm",
        100,
        [("Xôi trắng", 60), ("Đậu xanh", 35), ("Đường trắng", 5)],
    ),
    "NIN-BANH-DEO-NHAN-THAP-CAM": (
        "Bánh dẻo nhân thập cẩm",
        150,
        [("Bột gạo nếp Glutinous rice flour", 90), ("Lạc rang", 20), ("Vừng", 10), ("Đường trắng", 25)],
    ),
    "NIN-BANH-DEO-NHAN-TRUNG": (
        "Bánh dẻo nhân trứng",
        150,
        [("Bột gạo nếp Glutinous rice flour", 90), ("Trứng vịt", 30), ("Đường trắng", 25)],
    ),
    "NIN-BANH-NUONG-NHAN-THAP-CAM": (
        "Bánh nướng nhân thập cẩm",
        150,
        [("Bột mì", 80), ("Lạc rang", 20), ("Vừng", 10), ("Đường trắng", 25), ("Mỡ lợn", 10)],
    ),
    "NIN-BANH-NUONG-NHAN-TRUNG-DO-XANH": (
        "Bánh nướng nhân trứng đỗ xanh",
        150,
        [("Bột mì", 80), ("Đậu xanh", 30), ("Trứng vịt", 25), ("Đường trắng", 15)],
    ),
    "NIN-BANH-PHU-THE": (
        "Bánh phu thê (su sê, xu xuê)",
        100,
        [("Bột sắn dây", 60), ("Đậu xanh", 25), ("Đường trắng", 10)],
    ),
    "NIN-BANH-CHIN-TANG-MAY": (
        "Bánh chín tầng mây",
        100,
        [("Bột gạo tẻ Rice flour", 80), ("Đường trắng", 20)],
    ),
    "NIN-BANH-DAU-XANH": (
        "Bánh đậu xanh",
        50,
        [("Đậu xanh", 40), ("Đường trắng", 10)],
    ),
    "NIN-BANH-CHA": (
        "Bánh chả",
        100,
        [("Bột mì", 60), ("Thịt lợn ba chỉ", 30), ("Đường trắng", 10)],
    ),
    "NIN-CARAMEN": (
        "Caramen",
        100,
        [("Trứng gà", 50), ("Sữa tươi không đường", 40), ("Đường trắng", 10)],
    ),
    "NIN-GIO-THU-LON": (
        "Giò thủ lợn",
        100,
        [("Tim lợn", 40), ("Lòng lợn", 30), ("Nước mắm", 5), ("Mộc nhĩ", 10)],
    ),
    "NIN-DOI-LON": (
        "Dồi lợn",
        100,
        [("Lòng lợn", 60), ("Tiết lợn luộc", 35)],
    ),
}


def norm(s: str) -> str:
    return " ".join(s.strip().lower().split())


def main() -> int:
    apply = "--apply" in sys.argv

    with open(FOOD_ITEMS_PATH, newline="", encoding="utf-8") as handle:
        food_rows = list(csv.DictReader(handle))
    by_name: dict[str, str] = {}
    for row in food_rows:
        by_name[norm(row["name_vi"])] = row["id"]
        for alias in (row.get("aliases") or "").split("|"):
            if alias.strip():
                by_name[norm(alias)] = row["id"]

    with open(DISHES_PATH, encoding="utf-8") as handle:
        existing_dish_ids = {row[0] for row in csv.reader(handle)}

    resolved: list[tuple[str, str, float]] = []  # dish rows
    resolved_ings: list[tuple[str, str, float]] = []  # dish_id, food_id, grams
    blocked: list[tuple[str, list[str]]] = []

    for dish_id, (name_vi, _typed_serving_g, ingredients) in PROPOSALS.items():
        if dish_id in existing_dish_ids:
            continue
        missing = [n for n, _ in ingredients if norm(n) not in by_name]
        if missing:
            blocked.append((name_vi, missing))
            continue
        # serving_g PHẢI bằng tổng gram nguyên liệu thật, không gõ tay riêng —
        # lệch giữa hai số này chính là cơ chế đã gây bug thực đơn MENU-*
        # (hệ số scale sai khi grams phục vụ khác tổng công thức, DEC-022).
        serving_g = sum(g for _, g in ingredients)
        resolved.append((dish_id, name_vi, serving_g))
        for ing_name, grams in ingredients:
            resolved_ings.append((dish_id, by_name[norm(ing_name)], grams))

    print(f"Tong de xuat: {len(PROPOSALS)}")
    print(f"  Khop du nguyen lieu (san sang ghi): {len(resolved)}")
    print(f"  Bi chan vi thieu nguyen lieu trong food_items.csv: {len(blocked)}")
    if blocked:
        print("\nMon bi chan (can R2 bo sung food_item hoac sua ten khop):")
        for name, missing in blocked:
            print(f"   {name}: thieu {missing}")

    if not apply:
        print("\n(dry-run — chưa ghi gì. Chạy lại với --apply để ghi.)")
        return 0

    with open(DISHES_PATH, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for dish_id, name_vi, serving_g in resolved:
            writer.writerow([dish_id, name_vi, "", serving_g, "pending", NOTE_PENDING])

    with open(DISH_INGREDIENTS_PATH, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for dish_id, food_id, grams in resolved_ings:
            writer.writerow([dish_id, food_id, grams, ""])

    print(f"\nDa them {len(resolved)} mon vao {DISHES_PATH.relative_to(ROOT)}")
    print(f"Da them {len(resolved_ings)} dong nguyen lieu vao {DISH_INGREDIENTS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
