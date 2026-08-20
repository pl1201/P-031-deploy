"""food_items.thai_bo_pct — tỉ lệ thải bỏ khi sơ chế (DEC-062)

Vì sao: công thức nấu ăn ghi khối lượng nguyên liệu MUA Ở CHỢ (kể cả xương, vỏ,
mai, cuống, lá già), còn bảng thành phần thực phẩm cho số liệu trên PHẦN ĂN
ĐƯỢC. Nhân thẳng gram công thức với giá trị bảng là thổi phồng dinh dưỡng — đo
được tới −51 % kcal và −63 % đạm ở món canh cua sau khi hiệu chỉnh
(xem `docs/PHAT_HIEN_THAI_BO_2026-08-16.md`).

Trước đây bảng tỉ lệ này nằm rải trong `scripts/nap_mon_555.py`, chỉ áp cho một
nhóm món. Đưa lên cột dữ liệu để dùng chung và để CSV với DB không lệch nhau.

Nullable: không nguồn nào cho đủ. NIN có cột `Thải bỏ (%)`, FAO/INFOODS uFiSh có
hệ số `EDIBLE`, USDA có `refuse` — nhưng không phủ hết mọi thực phẩm.

Revision ID: c8f31d75a204
Revises: b7e2a91c4f08
Create Date: 2026-08-16
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "c8f31d75a204"
down_revision = "b7e2a91c4f08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("food_items") as batch:
        batch.add_column(sa.Column("thai_bo_pct", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("food_items") as batch:
        batch.drop_column("thai_bo_pct")
