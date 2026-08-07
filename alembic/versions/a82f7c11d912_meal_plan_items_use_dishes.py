"""Store prepared dishes in meal plans.

Revision ID: a82f7c11d912
Revises: 5394cb31dc4e
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a82f7c11d912"
down_revision: str | Sequence[str] | None = "5394cb31dc4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("meal_plan_items") as batch:
        batch.alter_column("food_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column("dish_id", sa.String(length=64), nullable=True))
        batch.create_foreign_key("fk_meal_plan_items_dish_id", "dishes", ["dish_id"], ["dish_id"])
        batch.create_index("ix_meal_plan_items_dish_id", ["dish_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("meal_plan_items") as batch:
        batch.drop_index("ix_meal_plan_items_dish_id")
        batch.drop_constraint("fk_meal_plan_items_dish_id", type_="foreignkey")
        batch.drop_column("dish_id")
        batch.alter_column("food_id", existing_type=sa.Integer(), nullable=False)
