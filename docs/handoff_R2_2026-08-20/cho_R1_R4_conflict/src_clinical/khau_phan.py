"""Quy đổi gram sang đơn vị dân gian (bát, tô, thìa, lòng bàn tay) để bệnh nhân hiểu.

LLM: NO — tra bảng tất định, không suy đoán.

Vì sao cần: "Cơm tẻ 180 g" là con số đúng nhưng không ai đong được ở nhà. Bệnh
nhân cần "khoảng 1 lưng bát cơm". Ngược lại, "1 bát" cũng phải quy về gram thì
Python mới tính được dinh dưỡng (RULE-1).

Nguyên tắc xuyên suốt: **KHÔNG ĐOÁN**. Món chưa có quy đổi đã được R2 ký thì trả
`None` và tầng hiển thị chỉ hiện gram — thà bắt bệnh nhân cân còn hơn nói sai
khẩu phần. Đoán "khoảng 1 bát" cho một món chưa đo là đoán cả lượng carb bệnh
nhân ĐTĐ2 sẽ nạp; sai một bát cơm là sai ~45-60 g glucid (hội thảo t-DNA §4.1).

Ba nguồn quy đổi, theo thứ tự ưu tiên:

1. `dish_unit_conversions.csv` — đo/duyệt cho ĐÚNG món đó, chính xác nhất.
2. `household_units.csv` — dụng cụ có dung tích xác định (thìa 15 ml, cốc 250 ml).
   Chỉ dùng được khi biết khối lượng riêng, nên hiện chỉ áp cho nước/dầu.
3. Khẩu phần chuẩn `serving_g` của món — cho ra "1 phần" chứ không phải "1 bát".

`QUY_TAC_BAN_TAY` là bảng THAM CHIẾU cho tầng hiển thị (nguồn: hội thảo t-DNA
16/08/2026 §7.4, ca 1 tr. 19) — dùng để chú thích trực quan, KHÔNG dùng để tính
dinh dưỡng ngược lại thành gram: "một lòng bàn tay" khác nhau giữa các bệnh nhân.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

SEEDS = Path(__file__).resolve().parent.parent.parent / "data" / "seeds"

#: Sai số cho phép khi khớp gram về bội số của một đơn vị. 12% là mức mà chênh
#: lệch vẫn nhỏ hơn sai số bản thân việc "ước lượng một bát" của người dùng.
DUNG_SAI = 0.12

#: Mô tả nửa phần — người Việt nói "lưng bát"/"nửa bát" chứ không nói "0,5 bát".
_NHAN_BOI: dict[float, str] = {
    0.5: "nửa",
    1.0: "1",
    1.5: "1 rưỡi",
    2.0: "2",
    3.0: "3",
}


@dataclass(frozen=True)
class QuyDoi:
    """Một cách diễn đạt khẩu phần bằng ngôn ngữ thường ngày."""

    mo_ta: str
    """VD 'khoảng 1 bát', 'nửa tô'. Luôn có chữ 'khoảng' — đây là ước lượng."""

    unit_code: str
    grams: float
    """Gram THẬT ứng với mô tả này — con số dùng để tính dinh dưỡng."""

    source_ref: str


#: Khẩu phần trực quan theo nhóm món — THAM CHIẾU để chú thích, không để tính.
#: Nguồn: hội thảo t-DNA/DSF 16/08/2026 §7.4 (ca 1, tr. 19), câu ghi nhớ gốc:
#: "Cơm bớt một nửa – rau gấp đôi – đạm đủ một lòng bàn tay".
QUY_TAC_BAN_TAY: dict[str, str] = {
    "staple": "khoảng 3/4 bát cơm, hoặc 1 bát phở/bún nhỏ",
    "protein": "khoảng 1 lòng bàn tay (cá, gà bỏ da, thịt nạc, tôm, đậu phụ)",
    "vegetable": "ít nhất 2 nắm tay lớn, ưu tiên luộc/hấp/canh",
    "soup": "khoảng 1 bát canh",
    "one_dish": "khoảng 1 bát/tô",
    "dessert": "1 phần nhỏ",
}


@lru_cache(maxsize=1)
def _bang_don_vi() -> dict[str, dict[str, str]]:
    with (SEEDS / "household_units.csv").open(encoding="utf-8") as fh:
        return {r["unit_code"]: r for r in csv.DictReader(fh)}


@lru_cache(maxsize=1)
def _bang_quy_doi_mon() -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    with (SEEDS / "dish_unit_conversions.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.setdefault(r["dish_id"], []).append(r)
    return out


def _nhan_boi(boi: float) -> str | None:
    for moc, nhan in _NHAN_BOI.items():
        if abs(boi - moc) <= moc * DUNG_SAI:
            return nhan
    return None


def quy_doi_mon(dish_id: str, grams: float, region: str | None = None) -> QuyDoi | None:
    """Diễn đạt `grams` của món `dish_id` bằng đơn vị dân gian, hoặc None.

    Trả `None` khi món chưa có quy đổi đã ký, hoặc khi số gram không rơi gần một
    bội số dễ nói (VD 137 g của một bát 450 g — nói "khoảng 0,3 bát" thì vô
    nghĩa với người dùng). Trả None là kết quả HỢP LỆ, không phải lỗi: tầng hiển
    thị hiện gram như cũ.

    `region` chọn đúng cách gọi theo vùng — cùng một vật, miền Bắc gọi 'bát',
    miền Nam 'chén', miền Trung 'đọi'. Không truyền thì lấy bản 'all' hoặc dòng
    đầu tiên, để hồ sơ NHANES (region=None) vẫn dùng được.
    """
    dong = _bang_quy_doi_mon().get(dish_id)
    if not dong or grams <= 0:
        return None

    don_vi = _bang_don_vi()
    uu_tien = (
        [d for d in dong if region and don_vi.get(d["unit_code"], {}).get("region") == region]
        or [d for d in dong if don_vi.get(d["unit_code"], {}).get("region") == "all"]
        or dong
    )

    for d in uu_tien:
        moc = float(d["grams"])
        if moc <= 0:
            continue
        nhan = _nhan_boi(grams / moc)
        if nhan:
            ten = don_vi.get(d["unit_code"], {}).get("name_vi", d["unit_code"])
            return QuyDoi(
                mo_ta=f"khoảng {nhan} {ten}",
                unit_code=d["unit_code"],
                grams=moc * (grams / moc),
                source_ref=d.get("source_ref", ""),
            )
    return None


def goi_y_truc_quan(roles: tuple[str, ...] | list[str]) -> str | None:
    """Chú thích khẩu phần theo nhóm món, khi không quy đổi được sang bát/tô.

    Đây là gợi ý ĐỊNH TÍNH cho người đọc dễ hình dung, KHÔNG phải con số tính
    được — không bao giờ dùng chiều ngược lại để suy ra gram.
    """
    for r in roles:
        if r in QUY_TAC_BAN_TAY:
            return QUY_TAC_BAN_TAY[r]
    return None


def don_vi_sang_gram(unit_code: str, so_luong: float, dish_id: str | None = None) -> float | None:
    """Chiều ngược lại: bệnh nhân nói "2 bát" thì bằng bao nhiêu gram.

    Chỉ trả số khi có quy đổi ĐÃ KÝ cho đúng món đó. Không có thì trả `None` —
    tầng gọi phải xử lý như dữ liệu thiếu (`unmatched`), tuyệt đối không tự quy
    ra gram trung bình rồi cộng vào tổng ngày (RULE-2).
    """
    if dish_id is None or so_luong <= 0:
        return None
    for d in _bang_quy_doi_mon().get(dish_id, []):
        if d["unit_code"] == unit_code:
            return float(d["grams"]) * so_luong
    return None
