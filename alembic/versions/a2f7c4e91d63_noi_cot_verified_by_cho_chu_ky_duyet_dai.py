"""Nới cột verified_by: varchar(100) -> Text

Vì sao: chữ ký duyệt của chuyên gia là câu văn có bối cảnh, không phải mã ngắn.
Chuỗi thật đang dùng trong `dishes.csv` dài tới 158 ký tự, ví dụ:

    "Chuyên gia duyệt 2026-08-13 (R2 xác nhận duyệt đợt rà 53 món pending còn
     lại — số liệu công thức từ nguồn crawl có ghi chú, thiếu gia vị phụ không
     chặn duyệt)"

Với `varchar(100)`, `scripts/seed_db.py` ném `StringDataRightTruncation` và
**dừng giữa chừng**, nên toàn bộ đợt đồng bộ seed lên Supabase thất bại (phát
hiện 2026-08-15 khi đồng bộ theo chỉ thị R2). Cắt bớt chữ ký để vừa cột là
KHÔNG chấp nhận được: đó chính là dấu vết ai duyệt và duyệt với điều kiện gì —
cắt đi là mất căn cứ truy vết của RULE-2/RULE-3.

Đổi sang `Text` thay vì nới lên một con số lớn hơn: mọi giới hạn độ dài ở đây
đều là con số tuỳ tiện, và Postgres không tối ưu hơn khi biết trước độ dài.

Áp cho cả ba bảng có cùng cột này để không phải sửa lại lần nữa.

Revision ID: a2f7c4e91d63
Revises: e91a4c7f5b28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a2f7c4e91d63"
down_revision = "e91a4c7f5b28"
branch_labels = None
depends_on = None

_BANG = ("dishes", "household_units", "dish_unit_conversions")


def upgrade() -> None:
    # `batch_alter_table` thay vì `op.alter_column` trực tiếp: SQLite KHÔNG có
    # `ALTER TABLE ... ALTER COLUMN`, nên bản cũ làm `alembic upgrade head` chết
    # ngay tại đây với "near ALTER: syntax error" — không ai dựng lại được schema
    # từ con số 0 để đối chiếu, dù production (Postgres) vẫn chạy bình thường.
    # Phát hiện 16/08/2026 khi chạy thử chuỗi migration sau lúc merge main.
    #
    # Chế độ batch cho Alembic tự dựng bảng mới rồi chép dữ liệu sang trên
    # SQLite; với Postgres nó vẫn phát đúng `ALTER COLUMN` như trước.
    for bang in _BANG:
        with op.batch_alter_table(bang) as batch:
            batch.alter_column(
                "verified_by",
                existing_type=sa.String(length=100),
                type_=sa.Text(),
                existing_nullable=True,
            )


def downgrade() -> None:
    # Cảnh báo: hạ về varchar(100) sẽ CẮT MẤT phần đuôi của mọi chữ ký dài hơn
    # 100 ký tự — chạy downgrade này đồng nghĩa mất dấu vết duyệt.
    for bang in _BANG:
        with op.batch_alter_table(bang) as batch:
            batch.alter_column(
                "verified_by",
                existing_type=sa.Text(),
                type_=sa.String(length=100),
                existing_nullable=True,
            )
