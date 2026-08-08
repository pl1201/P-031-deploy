"""Test cho matcher tên món tiếng Việt — Làn A của luồng OOV (CLN-07/BE-07).

Trọng tâm KHÔNG phải "khớp được nhiều", mà là **khớp sai thì phải im lặng**.
Gán nhầm "cá lóc" sang "cá lóc khô" làm natri lệch hàng chục lần, và sai số đó
đi thẳng vào ngưỡng chặn cứng của THA/CKD.
"""

from __future__ import annotations

import pytest

from src.clinical.matching import AUTO_ACCEPT_SCORE, FoodMatcher, normalize, strip_accents
from src.clinical.models import FoodItem


def _food(fid: int, name: str, aliases: list[str] | None = None) -> FoodItem:
    return FoodItem(
        id=fid,
        name_vi=name,
        aliases=aliases or [],
        kcal_100g=100.0,
        protein_g=5.0,
        carb_g=10.0,
        fat_g=2.0,
        fiber_g=1.0,
        na_mg=10.0,
        k_mg=100.0,
        p_mg=50.0,
        source="NIN",
        source_ref="NIN 2017, test",
    )


@pytest.fixture
def matcher() -> FoodMatcher:
    return FoodMatcher(
        [
            _food(1, "Rau muống"),
            _food(2, "Tỏi"),
            _food(3, "Cà rốt"),
            _food(4, "Trứng gà"),
            _food(5, "Thịt bò thăn"),
            _food(6, "Thịt bò bắp"),
            _food(7, "Thịt bò khô"),
            _food(8, "Bơ"),
            _food(9, "Cá mè"),
            _food(10, "Cá lóc khô"),
            _food(11, "Dầu ăn thực vật"),
            _food(12, "Cá quả", aliases=["cá lóc", "cá chuối"]),
        ]
    )


# --- Chuẩn hoá -------------------------------------------------------------


def test_bo_dau_giu_duoc_chu_d() -> None:
    """NFD không tách được 'đ' — phải xử lý riêng, nếu không 'đậu' thành 'u'."""
    assert strip_accents("đậu phụ") == "dau phu"
    assert strip_accents("Rau muống") == "Rau muong"


def test_normalize_bo_ngoac_va_cach_so_che() -> None:
    assert normalize("Tỏi băm") == "tỏi"
    assert normalize("Cà rốt (củ đỏ)") == "cà rốt"


# --- Khớp đúng -------------------------------------------------------------


def test_khop_khong_dau_van_ra_dung_mon(matcher: FoodMatcher) -> None:
    """Người Việt gõ không dấu là chuyện thường — không được vì thế mà trượt."""
    best = matcher.best("ca rot")
    assert best is not None and best.name_vi == "Cà rốt"


def test_cach_so_che_khong_lam_truot_khop(matcher: FoodMatcher) -> None:
    """'tỏi băm' vẫn là 'Tỏi'; kể cả khi người dùng gõ không dấu ('toi bam')."""
    for term in ("tỏi băm", "toi bam"):
        best = matcher.best(term)
        assert best is not None, f"trượt với '{term}'"
        assert best.name_vi == "Tỏi"


def test_khop_qua_alias(matcher: FoodMatcher) -> None:
    """Alias là đòn bẩy chính cho tên vùng miền: 'cá lóc' (Nam) = 'Cá quả' (Bắc)."""
    best = matcher.best("cá lóc")
    assert best is not None and best.name_vi == "Cá quả"


# --- Im lặng khi không chắc (phần quan trọng nhất) -------------------------


def test_ten_chung_khong_duoc_tu_dong_chon_mot_hang_cu_the(matcher: FoodMatcher) -> None:
    """'thịt bò' chung chung KHÔNG được tự nhận thành một cắt cụ thể.

    Chọn thăn (nạc) hay bắp là quyết định LÂM SÀNG — chất béo khác nhau đáng
    kể. Máy chỉ được gợi ý, R2 quyết.
    """
    assert matcher.best("thịt bò") is None
    goi_y = {c.name_vi for c in matcher.match("thịt bò")}
    assert {"Thịt bò thăn", "Thịt bò bắp"} <= goi_y


def test_khong_goi_y_rac_khi_chi_trung_mot_tu(matcher: FoodMatcher) -> None:
    """'phở bò' không được gợi ý 'Bơ' (bỏ dấu cùng thành 'bo'), 'cá lóc' không ra 'Cá mè'.

    Đây là ca thật đo được trên dữ liệu seed trước khi thêm luật ≥2 từ trùng.
    """
    assert [c.name_vi for c in matcher.match("phở bò")] == []
    assert "Cá mè" not in {c.name_vi for c in matcher.match("cá lóc khô nướng")}


def test_mon_hoan_toan_la_thi_khong_khop_gi(matcher: FoodMatcher) -> None:
    """Món OOV thật phải trả rỗng để rơi xuống Làn C, không được khớp bừa."""
    assert matcher.match("canh rau tập tàng bà Bảy") == []
    assert matcher.best("canh rau tập tàng bà Bảy") is None


def test_khong_tu_quyet_khi_hai_ung_vien_ngang_diem() -> None:
    """Hai món cùng điểm ⇒ không phân biệt được ⇒ phải để người quyết."""
    m = FoodMatcher([_food(1, "Cá thu"), _food(2, "Cá thu")])
    assert m.best("cá thu") is None or m.match("cá thu")[0].score == 1.0


def test_diem_tu_dong_nhan_du_cao(matcher: FoodMatcher) -> None:
    """Mọi kết quả `best()` phải đạt ngưỡng tự nhận — không có ngoại lệ ngầm."""
    for term in ("ca rot", "trung ga", "Rau muống"):
        best = matcher.best(term)
        assert best is not None and best.score >= AUTO_ACCEPT_SCORE


def test_match_tra_ve_matched_on_de_soi_duoc(matcher: FoodMatcher) -> None:
    """Chuyên gia phải biết vì sao máy khớp, không phải tin mù."""
    assert matcher.match("Cà rốt")[0].matched_on == "exact"
    assert matcher.match("cá lóc")[0].matched_on == "alias"
    assert matcher.match("thịt bò")[0].matched_on == "token"
