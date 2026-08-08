"""Add immutable snapshots used by the meal-plan publish gate.

Revision ID: c41f6a2d9e10
Revises: aedef0ff7743
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c41f6a2d9e10"
down_revision: str | Sequence[str] | None = "aedef0ff7743"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("meal_plans") as batch:
        batch.add_column(sa.Column("highest_risk", sa.String(length=4), nullable=False, server_default="none"))
        batch.add_column(sa.Column("menu_version", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("approved_menu_version", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("menu_hash", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("nutrition_hash", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("approved_menu_hash", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("approved_nutrition_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("meal_plans") as batch:
        batch.drop_column("approved_nutrition_hash")
        batch.drop_column("approved_menu_hash")
        batch.drop_column("nutrition_hash")
        batch.drop_column("menu_hash")
        batch.drop_column("approved_menu_version")
        batch.drop_column("menu_version")
        batch.drop_column("highest_risk")
