"""Widen clinical_rules flag columns 50->255 chars (CLN-11 on_dialysis).

Revision ID: 5bbf9aaefecc
Revises: 8546da42031c

CLN-11 (2026-08-12) thêm cờ lâm sàng `on_dialysis` — CKD-PRO-01.disabled_by_flag
cần lưu 3 cờ nối chuỗi ("frailty_sarcopenia,metabolically_unstable,on_dialysis",
53 ký tự), vượt VARCHAR(50) cũ. Widening không mất dữ liệu (Postgres không cần
rewrite bảng khi tăng độ dài varchar).

LƯU Ý VẬN HÀNH: `alembic_version` trên DB Supabase dùng chung đang stamp ở
`f85d0e3b2c41` — revision đó KHÔNG tồn tại trong `alembic/versions/` của
nhánh này (lịch sử migration cục bộ và DB thật đã lệch từ trước, không phải do
migration này gây ra). Vì vậy 3 cột đã được ALTER TABLE trực tiếp trên DB thật
(2026-08-12) để không phá schema đang chạy, KHÔNG qua `alembic upgrade`. File
này tồn tại để: (1) DB mới tạo từ đầu (`alembic upgrade head`) có đúng schema,
(2) làm tài liệu cho lần đối chiếu/stamp lại lịch sử migration sau này. Linh
(owner E3/DB) cần xác nhận nguồn gốc `f85d0e3b2c41` trước khi chạy
`alembic stamp`/`upgrade` thật trên DB chung.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5bbf9aaefecc"
down_revision: str | Sequence[str] | None = "8546da42031c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("clinical_rules") as batch:
        batch.alter_column(
            "overridden_by", existing_type=sa.String(length=50), type_=sa.String(length=255)
        )
        batch.alter_column(
            "disabled_by_flag", existing_type=sa.String(length=50), type_=sa.String(length=255)
        )
        batch.alter_column(
            "requires_flag", existing_type=sa.String(length=50), type_=sa.String(length=255)
        )


def downgrade() -> None:
    with op.batch_alter_table("clinical_rules") as batch:
        batch.alter_column(
            "requires_flag", existing_type=sa.String(length=255), type_=sa.String(length=50)
        )
        batch.alter_column(
            "disabled_by_flag", existing_type=sa.String(length=255), type_=sa.String(length=50)
        )
        batch.alter_column(
            "overridden_by", existing_type=sa.String(length=255), type_=sa.String(length=50)
        )
