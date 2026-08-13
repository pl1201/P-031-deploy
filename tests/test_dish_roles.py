"""Vai trò món trong cấu trúc bữa (`src/clinical/dish_roles.py`).

Trọng tâm: hành vi FAIL CLOSED. Món không có vai trò, hoặc chỉ có vai trò ăn
kèm, không được lọt vào bữa của bệnh nhân như một mục độc lập.
"""

from __future__ import annotations

import csv

from src.clinical.dish_roles import (
    DishRole,
    is_self_sufficient,
    is_standalone,
    parse_roles,
    unknown_role_tokens,
)
from src.clinical.seeds import SEEDS_DIR, load_vn_dishes


class TestParseRoles:
    def test_doc_nhieu_vai_tro_phan_tach_bang_gach_doc(self):
        assert parse_roles("staple|one_dish") == (DishRole.STAPLE, DishRole.ONE_DISH)

    def test_rong_va_none_tra_ve_tuple_rong(self):
        assert parse_roles("") == ()
        assert parse_roles(None) == ()

    def test_token_la_bi_bo_qua_khong_raise(self):
        """Một token gõ sai trong seed KHÔNG được làm sập pipeline sinh thực đơn.

        Món đó hành xử như món không có vai trò (fail closed);
        `scripts/validate_data.py` là nơi báo lỗi cho người sửa.
        """
        assert parse_roles("staple|khong_ton_tai") == (DishRole.STAPLE,)
        assert parse_roles("khong_ton_tai") == ()

    def test_khong_lap_vai_tro_trung(self):
        assert parse_roles("soup|soup") == (DishRole.SOUP,)

    def test_bo_khoang_trang_thua(self):
        assert parse_roles(" staple | protein ") == (DishRole.STAPLE, DishRole.PROTEIN)


class TestUnknownRoleTokens:
    def test_bao_dung_token_la_cho_validator(self):
        assert unknown_role_tokens("staple|sai_be_bet") == ("sai_be_bet",)

    def test_khong_bao_gi_khi_moi_token_hop_le(self):
        assert unknown_role_tokens("staple|protein") == ()
        assert unknown_role_tokens("") == ()


class TestIsStandalone:
    def test_khong_co_vai_tro_thi_khong_duoc_dung_doc_lap(self):
        """Fail closed — không có nhãn thì không có căn cứ khẳng định là món."""
        assert is_standalone(()) is False

    def test_chi_co_vai_tro_an_kem_thi_khong_doc_lap(self):
        """Nước chấm không bao giờ là một mục của bữa."""
        assert is_standalone((DishRole.CONDIMENT,)) is False

    def test_mon_thuong_va_mon_mot_bat_deu_doc_lap(self):
        assert is_standalone((DishRole.SOUP,)) is True
        assert is_standalone((DishRole.ONE_DISH,)) is True


class TestIsSelfSufficient:
    def test_mon_mot_bat_tu_no_da_du_thanh_bua(self):
        assert is_self_sufficient((DishRole.ONE_DISH,)) is True

    def test_mon_thanh_phan_khong_tu_du(self):
        """Canh/giò lụa phải ghép thêm mới thành bữa."""
        assert is_self_sufficient((DishRole.SOUP,)) is False
        assert is_self_sufficient((DishRole.PROTEIN,)) is False
        assert is_self_sufficient(()) is False

    def test_da_vai_tro_co_one_dish_thi_van_tu_du(self):
        """Xôi lạc = staple|one_dish: ăn sáng đứng một mình được."""
        assert is_self_sufficient((DishRole.STAPLE, DishRole.ONE_DISH)) is True


class TestSeedDataRoles:
    """Kiểm chứng trên dữ liệu seed thật, không phải fixture tay."""

    def test_moi_mon_trong_dishes_csv_co_role_hop_le(self):
        with open(SEEDS_DIR / "dishes.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert rows, "dishes.csv rỗng"
        for row in rows:
            bad = unknown_role_tokens(row.get("roles"))
            assert not bad, f"{row['dish_id']} có token vai trò lạ: {bad}"

    def test_banh_da_nem_co_y_khong_co_vai_tro(self):
        """Bánh đa nem là VỎ CUỐN (nguyên liệu), bị nhập lẫn thành 'món'.

        Để trống `roles` là cố ý — nếu sau này ai gán vai trò cho nó thì test
        này đỏ, buộc người sửa phải giải thích vì sao một tấm vỏ bánh lại là
        một mục độc lập trong bữa của bệnh nhân.
        """
        with open(SEEDS_DIR / "dishes.csv", newline="", encoding="utf-8") as f:
            rows = {r["dish_id"]: r for r in csv.DictReader(f)}
        assert parse_roles(rows["NIN-BANH-DA-NEM"].get("roles")) == ()

    def test_load_vn_dishes_mang_theo_vai_tro(self):
        """Vai trò phải đi được từ CSV tới DishCandidate — nếu loader bỏ rơi
        cột này thì mọi ràng buộc cấu trúc bữa ở tầng trên đều thấy tuple rỗng
        và âm thầm không áp dụng gì."""
        dishes = load_vn_dishes(include_pending=True)
        assert dishes, "không nạp được món nào"
        assert any(d.roles for d in dishes), "không món nào có vai trò — loader đã bỏ rơi cột roles"

    def test_moi_mon_foreign_deu_khong_co_vai_tro(self):
        """2632 dòng FNDDS (`origin=foreign`) là khối tham chiếu USDA tiếng Anh.

        Không thể phân vai trò cho chúng mà không suy đoán, và tầng C vốn đã
        loại chúng khỏi thực đơn bệnh nhân — `roles` phải rỗng toàn bộ.
        """
        path = SEEDS_DIR.parent / "reference" / "dishes.fndds_bulk.csv"
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert rows, "file tham chiếu rỗng"
        assert all(r.get("origin") == "foreign" for r in rows)
        assert all(parse_roles(r.get("roles")) == () for r in rows)
