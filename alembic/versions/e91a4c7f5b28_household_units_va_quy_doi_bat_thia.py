"""household_units + dish_unit_conversions — quy đổi bát/chén/thìa (DEC-027, Đợt B).

Revision ID: e91a4c7f5b28
Revises: c4e82b16d0f3

Bối cảnh
--------
`UI_UX_COMPETITIVE_UPGRADE_PLAN.md` §5.3 yêu cầu người bệnh nhìn thấy khẩu phần
bằng đơn vị quen thuộc ("1 bát nhỏ · 150 g"), và nói rõ: *"Nếu chưa có quy đổi
có nguồn, giao diện chỉ hiển thị gram"*.

Bảng `serving_sizes` sẵn có KHÔNG đáp ứng được: nó khoá theo `category` trừu
tượng (`rice_bowl_cooked`), không có từ vựng tiếng Việt người bệnh thật sự dùng,
không nối được tới `dish_id`, và chưa code nào đọc.

Vì sao `household_units` có cột `region`
---------------------------------------
Tên đơn vị KHÔNG thống nhất toàn quốc: miền Bắc "bát", miền Nam "chén", miền
Trung "đọi" — cùng một vật. Nghĩa là một chuỗi người bệnh gõ vào chỉ quy ra gram
được KHI BIẾT họ ở vùng nào. Đây là ràng buộc an toàn chứ không phải chi tiết
ngôn ngữ: hiểu sai vùng thì con số gram lệch, và gram là đầu vào của mọi tính
toán dinh dưỡng phía sau.

`region = NULL` chỉ dành cho đơn vị đã đo bằng DUNG TÍCH (ml) nên không phụ
thuộc cách gọi — ví dụ "muỗng canh nhỏ 5 ml" trong bảng ĐỊNH LƯỢNG của poster.

Vì sao quy đổi phải gắn theo TỪNG MÓN
-------------------------------------
Một bát cơm ~150 g nhưng một bát phở ~450-500 g. Cùng chữ "bát", khác gần 3 lần.
Không thể lưu quy đổi ở mức đơn vị.

Ranh giới RULE-2 (R2 chốt 2026-08-15)
-------------------------------------
`household_units` là TỪ VỰNG DÂN GIAN — cách gọi tương đối theo vùng, `source_ref`
để trống được. `dish_unit_conversions` thì BẮT BUỘC `source_ref`: con số gram mới
là thứ đi vào tính kcal/carb/natri, sai ở đó là sai quyết định lâm sàng.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e91a4c7f5b28"
down_revision: str | Sequence[str] | None = "c4e82b16d0f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "household_units",
        sa.Column("unit_code", sa.String(length=40), primary_key=True),
        sa.Column("name_vi", sa.String(length=60), nullable=False),
        sa.Column("region", sa.String(length=10), nullable=True),
        sa.Column("aliases", sa.String(length=255), nullable=True),
        sa.Column("volume_ml", sa.Float(), nullable=True),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_household_units_name_vi", "household_units", ["name_vi"])

    op.create_table(
        "dish_unit_conversions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dish_id", sa.String(length=64), sa.ForeignKey("dishes.dish_id"), nullable=False),
        sa.Column("unit_code", sa.String(length=40), sa.ForeignKey("household_units.unit_code"), nullable=False),
        sa.Column("grams", sa.Float(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=False),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_dish_unit_conversions_dish_id", "dish_unit_conversions", ["dish_id"])
    op.create_index("ix_dish_unit_conversions_unit_code", "dish_unit_conversions", ["unit_code"])
    op.create_index("ix_dish_unit_conv_dish", "dish_unit_conversions", ["dish_id", "unit_code"])


def downgrade() -> None:
    op.drop_index("ix_dish_unit_conv_dish", table_name="dish_unit_conversions")
    op.drop_index("ix_dish_unit_conversions_unit_code", table_name="dish_unit_conversions")
    op.drop_index("ix_dish_unit_conversions_dish_id", table_name="dish_unit_conversions")
    op.drop_table("dish_unit_conversions")
    op.drop_index("ix_household_units_name_vi", table_name="household_units")
    op.drop_table("household_units")
