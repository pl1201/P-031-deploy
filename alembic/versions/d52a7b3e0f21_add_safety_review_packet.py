"""Persist typed safety findings and the reviewer packet.

Revision ID: d52a7b3e0f21
Revises: c41f6a2d9e10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d52a7b3e0f21"
down_revision: str | Sequence[str] | None = "c41f6a2d9e10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("meal_plans") as batch:
        batch.add_column(sa.Column("safety_findings", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("review_packet", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("citations", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("explanation_vi", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("meal_plans") as batch:
        batch.drop_column("explanation_vi")
        batch.drop_column("citations")
        batch.drop_column("review_packet")
        batch.drop_column("safety_findings")
