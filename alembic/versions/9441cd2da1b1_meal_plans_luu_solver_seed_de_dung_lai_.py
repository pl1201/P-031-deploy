"""meal_plans: lưu `solver_seed` để dựng lại được thực đơn đã duyệt.

DEC-030 đã ép CP-SAT giải tất định THEO một hạt giống, nhưng hạt giống lúc đó là
hằng số 42 và không được lưu ở đâu. Nên lời hứa truy vết chỉ đúng trên lý
thuyết: chuyên gia duyệt một thực đơn rồi hỏi "vì sao ca này ra thế" thì không
dựng lại được, vì không ai biết đã giải bằng seed nào.

Cột này lưu đúng hạt giống đã dùng cho chính thực đơn đó. Nullable vì mọi thực
đơn sinh trước 16/08/2026 không có thông tin này — điền số vào đó sẽ là bịa.

Revision ID: 9441cd2da1b1
Revises: 2475767dbf06
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9441cd2da1b1"
down_revision: str | Sequence[str] | None = "2475767dbf06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("meal_plans", sa.Column("solver_seed", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("meal_plans", "solver_seed")
