"""Persist versioned LangGraph state and operational audit metadata.

Revision ID: e63b8c4f1a32
Revises: d52a7b3e0f21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e63b8c4f1a32"
down_revision: str | Sequence[str] | None = "d52a7b3e0f21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("meal_plans") as batch:
        batch.add_column(sa.Column("run_id", sa.String(length=36), nullable=True))
        batch.add_column(sa.Column("profile_snapshot_hash", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("profile_version", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("rule_version", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("food_data_version", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("interaction_version", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("prompt_version", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("attempt_history", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("node_timings_ms", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("token_usage", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("last_error", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("audit_events", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    with op.batch_alter_table("meal_plans") as batch:
        batch.drop_column("audit_events")
        batch.drop_column("last_error")
        batch.drop_column("token_usage")
        batch.drop_column("node_timings_ms")
        batch.drop_column("attempt_history")
        batch.drop_column("prompt_version")
        batch.drop_column("interaction_version")
        batch.drop_column("food_data_version")
        batch.drop_column("rule_version")
        batch.drop_column("profile_version")
        batch.drop_column("profile_snapshot_hash")
        batch.drop_column("run_id")
