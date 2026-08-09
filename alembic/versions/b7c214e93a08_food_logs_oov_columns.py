"""food_logs: cột phục vụ nhật ký OOV (BE-07/CLN-07)

Revision ID: b7c214e93a08
Revises: aedef0ff7743
Create Date: 2026-08-08 00:00:00.000000

Thêm cột truy vết cách một dòng nhật ký được khớp, và **nới `grams` thành
nullable**.

Vì sao `grams` phải nullable: với kho chỉ 461 thực phẩm Việt, món ngoài CSDL
là trường hợp mặc định. Bệnh nhân gõ "canh rau tập tàng, 1 bát" mà không tra
được đơn vị "bát" cho món đó thì KHÔNG có con số gram nào đúng để ghi — bắt
buộc phải điền tức là ép bịa số (RULE-2/DEC-008).

Migration additive: không xoá/đổi tên cột nào, dữ liệu cũ giữ nguyên và nhận
`match_status='expert'` (mọi dòng đã có sẵn đều là dòng đã có food_id thật).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c214e93a08"
down_revision: str | Sequence[str] | None = "aedef0ff7743"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # batch_alter_table: SQLite không ALTER COLUMN được, phải tạo bảng mới rồi
    # copy. Alembic lo việc đó khi dùng batch mode; trên Postgres nó hạ xuống
    # ALTER thường nên không tốn gì.
    with op.batch_alter_table("food_logs") as batch:
        batch.add_column(sa.Column("dish_id", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("slot", sa.String(length=20), nullable=True))
        batch.add_column(
            sa.Column("match_status", sa.String(length=20), nullable=False, server_default="unmatched")
        )
        batch.add_column(sa.Column("match_confidence", sa.Float(), nullable=True))
        batch.add_column(sa.Column("portion_qty", sa.Float(), nullable=True))
        batch.add_column(sa.Column("portion_unit", sa.String(length=30), nullable=True))
        batch.add_column(sa.Column("grams_source_ref", sa.Text(), nullable=True))
        batch.add_column(sa.Column("note_vi", sa.Text(), nullable=True))
        batch.alter_column("grams", existing_type=sa.Float(), nullable=True)
        batch.create_foreign_key("fk_food_logs_dish_id", "dishes", ["dish_id"], ["dish_id"])

    op.create_index("ix_food_logs_logged_at", "food_logs", ["logged_at"])
    op.create_index("ix_food_logs_match_status", "food_logs", ["match_status"])

    # Dòng đã tồn tại trước migration đều có food_id thật (schema cũ bắt buộc
    # grams), nên chúng là dòng đã khớp — không được để lẫn vào hàng chờ giải
    # quyết của chuyên gia.
    op.execute("UPDATE food_logs SET match_status = 'expert' WHERE food_id IS NOT NULL")


def downgrade() -> None:
    """Downgrade schema.

    ⚠️ Mất dữ liệu: dòng có `grams IS NULL` (món chưa tra được khẩu phần) không
    biểu diễn được ở schema cũ. Xoá hẳn thay vì điền một con số bịa để lách
    ràng buộc NOT NULL.
    """
    op.execute("DELETE FROM food_logs WHERE grams IS NULL")

    op.drop_index("ix_food_logs_match_status", table_name="food_logs")
    op.drop_index("ix_food_logs_logged_at", table_name="food_logs")

    with op.batch_alter_table("food_logs") as batch:
        batch.drop_constraint("fk_food_logs_dish_id", type_="foreignkey")
        batch.alter_column("grams", existing_type=sa.Float(), nullable=False)
        batch.drop_column("note_vi")
        batch.drop_column("grams_source_ref")
        batch.drop_column("portion_unit")
        batch.drop_column("portion_qty")
        batch.drop_column("match_confidence")
        batch.drop_column("match_status")
        batch.drop_column("slot")
        batch.drop_column("dish_id")
