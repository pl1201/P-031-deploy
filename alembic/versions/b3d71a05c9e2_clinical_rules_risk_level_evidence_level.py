"""clinical_rules: thêm risk_level + evidence_level (DEC-023).

Revision ID: b3d71a05c9e2
Revises: 1778fd77cbec

Bối cảnh
--------
Trước đây quyền CHẶN PHÁT HÀNH (P0) được suy ra từ cột `severity`: mọi rule
`severity=hard` đều sinh finding P0. Hệ quả là hệ thống chặn thực đơn dựa trên
cả những ngưỡng mà chính file dữ liệu ghi là không truy được nguồn
(`CKD-P-02`, `GOUT-PUR-01` — `guideline_grade=unverified`) hoặc những ngưỡng mà
guideline gốc yêu cầu đánh giá cá thể trước khi hạn chế (`CKD-K-01/02/03` —
KDOQI 2020 grade OPINION).

`risk_level` tách quyền chặn khỏi mức độ lâm sàng:
    P0 = chặn phát hành · P1 = cần chuyên gia xác nhận · P2 = tham khảo

`evidence_level` ghi mức xác minh nguồn (primary_verified | secondary |
project_convention | unsourced) — chỉ để R2 truy vết, KHÔNG tham gia tính toán.

Cả hai cột đều nullable: dòng cũ để NULL vẫn chạy đúng như trước (code suy ra
từ `severity`), nên migration này tương thích ngược và không cần backfill bắt
buộc trước khi deploy code mới.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b3d71a05c9e2"
down_revision: str | Sequence[str] | None = "1778fd77cbec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clinical_rules", sa.Column("risk_level", sa.String(length=2), nullable=True))
    op.add_column("clinical_rules", sa.Column("evidence_level", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("clinical_rules", "evidence_level")
    op.drop_column("clinical_rules", "risk_level")
