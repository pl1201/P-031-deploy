"""Add notifications, patient_preferences, and onboarding/terms flags on users.

Revision ID: 53f37213ed57
Revises: c41a7d92e610
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "53f37213ed57"
down_revision: str | Sequence[str] | None = "c41a7d92e610"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("terms_accepted_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("onboarding_completed_at", sa.DateTime(), nullable=True))

    op.create_table(
        "patient_preferences",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("patient_profiles.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("disliked_foods", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("usual_meal_times", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("meal_reminders_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "related_meal_plan_id",
            sa.String(length=36),
            sa.ForeignKey("meal_plans.id"),
            nullable=True,
        ),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notifications_user_read_created", "notifications", ["user_id", "read_at", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("patient_preferences")
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "terms_accepted_at")
