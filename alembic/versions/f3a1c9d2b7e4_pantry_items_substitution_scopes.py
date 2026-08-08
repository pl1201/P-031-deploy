"""Add pantry_items and substitution_scopes tables (P2/AGT-12).

Revision ID: f3a1c9d2b7e4
Revises: aedef0ff7743
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3a1c9d2b7e4"
down_revision: str | Sequence[str] | None = "aedef0ff7743"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pantry_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("profile_id", sa.String(length=36), sa.ForeignKey("patient_profiles.id"), nullable=False),
        sa.Column("food_id", sa.Integer(), sa.ForeignKey("food_items.id"), nullable=True),
        sa.Column("free_text_vi", sa.String(length=255), nullable=True),
        sa.Column("qty", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_pantry_items_profile_id", "pantry_items", ["profile_id"])

    op.create_table(
        "substitution_scopes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("profile_id", sa.String(length=36), sa.ForeignKey("patient_profiles.id"), nullable=False),
        sa.Column("base_plan_id", sa.String(length=36), sa.ForeignKey("meal_plans.id"), nullable=False),
        sa.Column("approved_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tolerance", sa.Float(), nullable=False, server_default="0.10"),
        sa.Column("max_auto_releases", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("release_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_substitution_scopes_profile_id", "substitution_scopes", ["profile_id"])
    op.create_index("ix_substitution_scopes_base_plan_id", "substitution_scopes", ["base_plan_id"])


def downgrade() -> None:
    op.drop_index("ix_substitution_scopes_base_plan_id", table_name="substitution_scopes")
    op.drop_index("ix_substitution_scopes_profile_id", table_name="substitution_scopes")
    op.drop_table("substitution_scopes")

    op.drop_index("ix_pantry_items_profile_id", table_name="pantry_items")
    op.drop_table("pantry_items")
