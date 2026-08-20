"""food_items.fat_g cho phép NULL (DEC-061)

Vì sao: bảng thành phần thực phẩm của Viện Dinh dưỡng BỎ TRỐNG ô `Lipid (Fat)`
cho một loạt rau gia vị Việt — rau răm (mã 4088), rau húng (4094), dọc mùng
(4026). Bắt buộc cột này thì cả lớp rau ăn kèm cơ bản của bữa Việt nằm ngoài
kho vĩnh viễn, hoặc phải điền số mượn từ nguồn khác (vi phạm RULE-2).

Xử lý None-aware giống `sugar_g`/`purine_mg` đã làm: KHÔNG coi thiếu là 0, mà
cộng riêng rồi gắn cờ `NutritionSummary.fat_is_complete` để validator cảnh báo.

Revision ID: b7e2a91c4f08
Revises: 5103d1c0e654
Create Date: 2026-08-16
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "b7e2a91c4f08"
down_revision = "5103d1c0e654"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table để chạy được cả trên SQLite (test dùng SQLite).
    with op.batch_alter_table("food_items") as batch:
        batch.alter_column("fat_g", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    # Quay lại NOT NULL thì phải lấp các ô NULL trước, nếu không ALTER sẽ lỗi.
    # Điền 0 ở đây là CHẤP NHẬN ĐƯỢC vì đây là đường lùi khẩn cấp, và dữ liệu
    # đúng vẫn nằm nguyên trong `data/seeds/food_items.csv`.
    op.execute("UPDATE food_items SET fat_g = 0 WHERE fat_g IS NULL")
    with op.batch_alter_table("food_items") as batch:
        batch.alter_column("fat_g", existing_type=sa.Float(), nullable=False)
