"""Đọc định lượng bệnh nhân gõ bằng tiếng Việt tự nhiên: "2 bát cơm", "nửa tô phở".

Ticket: CLN-14. LLM: **NO** — module nằm trong `src/clinical/`, tuyệt đối không
import LLM client (có test `DETERMINISTIC_FILES` kiểm tra).

Vì sao KHÔNG để LLM làm việc này
---------------------------------
Nghe thì hợp lý: "đưa câu bệnh nhân gõ cho LLM, bảo nó trả về số gram". Nhưng
số gram là **con số dinh dưỡng** — nó đi thẳng vào tổng carb/natri của ngày.
RULE-1 nói rõ: LLM chỉ được chọn `food_id`, mọi con số phải do Python tính.
Một LLM đoán "2 bát cơm ≈ 400 g" là một LLM đang tính khẩu phần cho bệnh nhân
ĐTĐ2 — sai 1 bát cơm là sai 45–60 g glucid (hội thảo t-DNA §4.1).

Phân vai đúng:

* **Module này (tất định):** tách SỐ LƯỢNG và ĐƠN VỊ ra khỏi câu. "2" và "bát".
* **`khau_phan.don_vi_sang_gram()` (tra bảng đã ký):** "2 bát của món X" = ? gram.
* **LLM (nếu cần, Làn B):** chỉ đoán TÊN MÓN là gì, không bao giờ đoán số.

Nguyên tắc mơ hồ thì dừng
--------------------------
Câu không tách được rõ ràng thì trả `None`, và tầng gọi phải xử lý như dữ liệu
thiếu (`unmatched`) — đúng đường đã có sẵn ở `src/clinical/diary.py`. Đoán bừa
để "cho có số" là cách nhanh nhất tạo ra một tổng ngày sai mà không ai biết.

Văn bản vào đây là **dữ liệu người dùng gõ, không đáng tin**. Module này chỉ
đọc số và đơn vị; nó không nội suy văn bản vào prompt nào. Khi nào Làn B (LLM
mapper) được xây, phần tên món còn lại PHẢI đi qua `src/agents/security.py`
(`sanitize_untrusted` → `fence` → `scan_for_injection`) trước khi vào prompt —
xem `HANDOFF_NLP_KHAU_PHAN_VA_GUARDRAIL.md`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .matching import strip_accents

#: Số đếm tiếng Việt viết chữ. Chỉ tới 10 — quá 10 bát thì gần như chắc chắn là
#: gõ nhầm hoặc đùa, để `None` cho người xử lý còn hơn nhận bừa.
_SO_CHU: dict[str, float] = {
    "khong": 0.0,
    "mot": 1.0,
    "hai": 2.0,
    "ba": 3.0,
    "bon": 4.0,
    "nam": 5.0,
    "sau": 6.0,
    "bay": 7.0,
    "tam": 8.0,
    "chin": 9.0,
    "muoi": 10.0,
}

#: Từ chỉ phần lẻ. "lưng bát"/"lưng chén" = bát vơi, hội thảo t-DNA quy ước
#: 3/4 bát cơm cho bệnh nhân ĐTĐ2 (§7.4) nên lấy đúng con số đó, không tự đặt.
_PHAN_LE: dict[str, float] = {
    "nua": 0.5,
    "ruoi": 0.5,  # cộng thêm, xử lý riêng: "1 rưỡi" = 1.5
    "lung": 0.75,
    "voi": 0.75,
}

#: Đơn vị bệnh nhân hay nói -> `unit_code` trong `household_units.csv`.
#: CỐ Ý không nhận "muỗng"/"thìa" trần: thìa canh 15 ml và thìa cà phê 5 ml
#: chênh nhau 3 lần, đoán sai là sai gấp ba lượng dầu/đường.
_DON_VI: dict[str, str] = {
    "bat": "bat_an",
    "chen": "chen_an",
    "doi": "doi_an",
    "to": "to_an",
    "coc": "coc_250ml",
    "ly": "coc_250ml",
    "thia canh": "thia_canh_chuan",
    "muong canh": "thia_canh_chuan",
    "thia ca phe": "thia_ca_phe_chuan",
    "muong ca phe": "thia_ca_phe_chuan",
}

#: Đơn vị khối lượng trực tiếp — không cần tra bảng quy đổi.
_DON_VI_GRAM = {"g": 1.0, "gam": 1.0, "gram": 1.0, "kg": 1000.0, "lang": 100.0}

_TRAN_SO_LUONG = 10.0


@dataclass(frozen=True)
class KhauPhanDoc:
    """Kết quả tách một câu định lượng. `unit_code=None` nghĩa là đơn vị gram."""

    so_luong: float
    unit_code: str | None
    grams: float | None
    """Có số ngay khi bệnh nhân gõ thẳng gram; None thì phải tra `dish_unit_conversions`."""

    phan_con_lai: str
    """Phần chữ còn lại sau khi bóc số và đơn vị — ứng viên cho tên món."""


def _doc_so(cum: str) -> float | None:
    """Đọc '2', '2,5', 'hai', 'nửa', '1 rưỡi' thành số. None nếu không phải số."""
    cum = cum.strip()
    if not cum:
        return None

    tu = cum.split()
    tong = 0.0
    thay_so = False
    for t in tu:
        t = t.strip(".,")
        if not t:
            continue
        if re.fullmatch(r"\d+([.,]\d+)?", t):
            tong += float(t.replace(",", "."))
            thay_so = True
        elif t in _SO_CHU:
            tong += _SO_CHU[t]
            thay_so = True
        elif t == "ruoi":
            if not thay_so:
                return None  # "rưỡi" đứng một mình không có nghĩa
            tong += 0.5
        elif t in _PHAN_LE:
            # "nửa"/"lưng" đứng trước đơn vị: nếu đã có số nguyên thì đây là
            # cách nói lạ ("2 nửa bát") — không đoán.
            if thay_so:
                return None
            tong += _PHAN_LE[t]
            thay_so = True
        else:
            return None
    return tong if thay_so else None


def doc_khau_phan(text: str) -> KhauPhanDoc | None:
    """Tách số lượng + đơn vị khỏi câu bệnh nhân gõ. `None` nếu không chắc chắn.

    Trả `None` là kết quả HỢP LỆ và là mặc định an toàn — tầng gọi xử lý như
    `unmatched`, đúng đường đã có ở `diary.summarize_day()`.

    >>> doc_khau_phan("2 bát cơm").so_luong
    2.0
    >>> doc_khau_phan("nửa tô phở bò").unit_code
    'to_an'
    >>> doc_khau_phan("150g thịt lợn").grams
    150.0
    >>> doc_khau_phan("ăn nhiều lắm") is None
    True
    """
    if not text or not text.strip():
        return None

    goc = text.strip()
    phang = strip_accents(goc.lower())
    phang = re.sub(r"\s+", " ", phang)

    # Gram viết liền: "150g", "1.5kg"
    m = re.match(r"^\s*(\d+([.,]\d+)?)\s*(kg|g|gam|gram|lang)\b(.*)$", phang)
    if m:
        so = float(m.group(1).replace(",", "."))
        he_so = _DON_VI_GRAM[m.group(3)]
        gram = so * he_so
        if gram <= 0 or gram > 5000:
            return None
        return KhauPhanDoc(so_luong=so, unit_code=None, grams=gram, phan_con_lai=m.group(4).strip())

    # Đơn vị dân gian: bắt cụm đơn vị DÀI TRƯỚC ("thìa canh" trước "thìa").
    for cum, code in sorted(_DON_VI.items(), key=lambda kv: -len(kv[0])):
        m = re.search(rf"\b{re.escape(cum)}\b", phang)
        if not m:
            continue
        so = _doc_so(phang[: m.start()])
        if so is None or so <= 0 or so > _TRAN_SO_LUONG:
            return None
        return KhauPhanDoc(
            so_luong=so,
            unit_code=code,
            grams=None,  # phải tra `khau_phan.don_vi_sang_gram()` theo đúng món
            phan_con_lai=phang[m.end() :].strip(),
        )

    return None
