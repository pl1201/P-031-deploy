"""Khớp tên món/thực phẩm người dùng gõ tự do sang `food_id` — Làn A (tất định).

Ticket: CLN-07 / BE-07. LLM: **NO** — module này nằm trong `src/clinical/`, tuyệt
đối không import LLM client (có test `DETERMINISTIC_FILES` kiểm tra).

Vì sao cần module riêng thay vì dùng `InMemoryFoodRepository.search()`:
`search()` chỉ là substring thô (`nutrition.py:60`) — gõ "canh rau muong" không
dấu là trượt, gõ "tỏi băm" không khớp "Tỏi", và nó không xếp hạng nên không có
cách nào biết kết quả nào đáng tin. Với kho chỉ 461 thực phẩm Việt và 44/7.745
dòng có alias, khớp trượt là mặc định chứ không phải ngoại lệ.

**Ranh giới trách nhiệm:** module này CHỈ trả ứng viên kèm điểm. Nó KHÔNG quyết
định "đây chắc chắn là món X" và KHÔNG bao giờ suy ra con số dinh dưỡng. Quyết
định cuối cùng thuộc về tầng trên (ngưỡng tin cậy) hoặc về chuyên gia — đúng
DEC-008: thà để trống còn hơn gán sai.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .models import FoodItem

# Ngưỡng mặc định. Cố ý đặt cao: gán nhầm "cá lóc" thành "cá lóc khô" làm natri
# lệch hàng chục lần, mà lỗi đó lại đi thẳng vào ngưỡng chặn cứng của THA/CKD.
# Thà rơi xuống Làn B/C (LLM hoặc chuyên gia) còn hơn khớp bừa.
AUTO_ACCEPT_SCORE = 0.90
SUGGEST_SCORE = 0.45
TOP_K = 8

# Cách sơ chế — không đổi bản chất thực phẩm nên phải bỏ khi so khớp
# ("tỏi băm" vẫn là "Tỏi", "thịt bò thái mỏng" vẫn là thịt bò).
_PREP_WORDS = (
    "băm|bằm|xay|thái|cắt|nhuyễn|mỏng|nhỏ|khúc|sợi|hạt lựu|bóc vỏ|làm sạch|"
    "rửa sạch|đập dập|giã|xắt|lát|miếng|vụn|đông lạnh|hấp|luộc sẵn"
)
_PREP_RE = re.compile(rf"\b(?:{_PREP_WORDS})\b", re.IGNORECASE)

# Từ nối/đơn vị đếm mơ hồ — không mang thông tin phân biệt thực phẩm.
#
# CỐ Ý KHÔNG đưa vào đây: "loại" và "ăn". Đo được lỗi thật khi từng đưa vào:
# bỏ "loại" làm "Thịt bò loại I" rút gọn còn {thịt, bò}, nên truy vấn chung
# "thịt bò" KHỚP CHÍNH XÁC và tự động nhận đúng một hạng thịt cụ thể — chính
# là kiểu thay thế ngầm mà chỉ R2 mới được quyết (hạng thịt khác nhau đáng kể
# về chất béo). Tương tự "ăn" là phần phân biệt của "Dầu ăn".
_STOPWORDS = frozenset(
    {
        "và",
        "hoặc",
        "với",
        "của",
        "cái",
        "con",
        "quả",
        "trái",
        "củ",
        "cây",
        "chút",
        "ít",
        "nhiều",
        "một",
        "hai",
        "ba",
        "kèm",
    }
)


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt. Giữ 'đ' → 'd' (NFD không tách được 'đ')."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def normalize(text: str) -> str:
    """Chuẩn hoá để so khớp: NFC → thường → bỏ ngoặc → bỏ ký tự lạ → gọn khoảng trắng."""
    text = unicodedata.normalize("NFC", str(text)).strip().lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = _PREP_RE.sub(" ", text)
    text = re.sub(r"[^\w\sÀ-ỹ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# Người dùng gõ không dấu là chuyện thường ("toi bam", "ca rot"), mà `_PREP_RE`
# chỉ khớp dạng CÓ dấu — nên phải lọc lại một lần nữa trên dạng đã bỏ dấu, nếu
# không "toi bam" giữ nguyên token "bam" và trượt khỏi "Tỏi".
_PREP_STRIPPED = frozenset(strip_accents(w) for w in _PREP_WORDS.split("|"))
_STOPWORDS_STRIPPED = frozenset(strip_accents(w) for w in _STOPWORDS)


def _tokens(text: str) -> set[str]:
    """Token đã bỏ dấu, bỏ stopword và từ chỉ cách sơ chế."""
    out: set[str] = set()
    for raw in normalize(text).split():
        token = strip_accents(raw)
        if len(token) <= 1 or token in _PREP_STRIPPED or token in _STOPWORDS_STRIPPED:
            continue
        out.add(token)
    return out


@dataclass(frozen=True)
class MatchCandidate:
    """Một ứng viên khớp. `score` ∈ [0, 1] — càng cao càng chắc."""

    food_id: int
    name_vi: str
    score: float
    matched_on: str  # "exact" | "alias" | "token" — để chuyên gia soi được vì sao khớp


class FoodMatcher:
    """Chỉ mục tra cứu tên → food_id. Dựng một lần, tra nhiều lần.

    Chỉ nhận thực phẩm ĐÃ có số liệu và ĐÃ là ứng viên hợp lệ; việc lọc khối
    USDA bulk do tầng gọi quyết định (xem `src/agents/nodes/core.py`), module
    này không tự đoán phạm vi.
    """

    def __init__(self, items: list[FoodItem]) -> None:
        self._items = items
        self._exact: dict[str, int] = {}
        self._alias: dict[str, int] = {}
        self._tokens: dict[int, set[str]] = {}
        self._name: dict[int, str] = {}

        for item in items:
            self._name[item.id] = item.name_vi
            key = " ".join(sorted(_tokens(item.name_vi)))
            if key:
                self._exact.setdefault(key, item.id)
            for alias in item.aliases:
                akey = " ".join(sorted(_tokens(alias)))
                if akey:
                    self._alias.setdefault(akey, item.id)
            self._tokens[item.id] = _tokens(item.name_vi) | {t for alias in item.aliases for t in _tokens(alias)}

    def match(self, term: str, *, top_k: int = TOP_K) -> list[MatchCandidate]:
        """Trả danh sách ứng viên đã xếp hạng giảm dần. Rỗng nếu không có gì đáng gợi ý."""
        # Khớp exact phải dùng CÙNG bộ token với khớp mờ, nếu không "toi bam"
        # (đã bỏ token sơ chế "bam") sẽ không khớp nổi "Tỏi".
        key = " ".join(sorted(_tokens(term)))
        if not key:
            return []

        # Khớp chính xác (đã bỏ dấu) — tin cậy tuyệt đối.
        if key in self._exact:
            fid = self._exact[key]
            return [MatchCandidate(fid, self._name[fid], 1.0, "exact")]
        if key in self._alias:
            fid = self._alias[key]
            return [MatchCandidate(fid, self._name[fid], 1.0, "alias")]

        query = _tokens(term)
        if not query:
            return []

        scored: list[MatchCandidate] = []
        for fid, cand_tokens in self._tokens.items():
            if not cand_tokens:
                continue
            overlap = query & cand_tokens
            if not overlap:
                continue
            # Truy vấn nhiều từ mà chỉ trùng đúng 1 từ ⇒ gần như luôn là khớp
            # rác. Ca thật đo được: "phở bò" trùng {bo} với "Bơ" (bỏ dấu cũng
            # thành "bo") được 0,667 vì ứng viên chỉ có 1 token nên bao phủ
            # phía ứng viên = 1,0; "cá lóc" trùng {ca} với "Cá mè"/"Cá thu".
            # Gợi ý sai kiểu này làm chuyên gia mất niềm tin nhanh hơn là
            # không gợi ý gì.
            if len(query) >= 2 and len(overlap) < 2:
                continue
            # Hai chiều bao phủ: phần truy vấn được giải thích, VÀ phần ứng viên
            # được dùng tới. Chỉ dùng một chiều thì "phở" sẽ khớp 1.0 vào "Phở bò
            # tái nạm gầu" — nuốt trọn truy vấn nhưng bỏ qua toàn bộ phần còn lại
            # của ứng viên, tức là đang đoán thay người dùng.
            cover_q = len(overlap) / len(query)
            cover_c = len(overlap) / len(cand_tokens)
            score = 2 * cover_q * cover_c / (cover_q + cover_c)  # trung bình điều hoà
            if score >= SUGGEST_SCORE:
                scored.append(MatchCandidate(fid, self._name[fid], round(score, 3), "token"))

        scored.sort(key=lambda c: (-c.score, len(self._name[c.food_id])))
        return scored[:top_k]

    def best(self, term: str) -> MatchCandidate | None:
        """Ứng viên tốt nhất nếu ĐỦ CHẮC để tự động nhận; ngược lại None.

        Trả None KHÔNG có nghĩa là "không tìm thấy gì" — nó có nghĩa là "không
        đủ chắc để tự quyết". Tầng gọi phải đưa `match()` cho người dùng/chuyên
        gia chọn, chứ không được lấy đại phần tử đầu.
        """
        cands = self.match(term, top_k=2)
        if not cands or cands[0].score < AUTO_ACCEPT_SCORE:
            return None
        # Hai ứng viên ngang điểm nhau ⇒ không phân biệt được ⇒ không tự quyết.
        if len(cands) > 1 and abs(cands[0].score - cands[1].score) < 1e-9:
            return None
        return cands[0]
