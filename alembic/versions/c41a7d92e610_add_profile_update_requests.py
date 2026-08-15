"""Add durable patient profile update requests.

Revision ID: c41a7d92e610
Revises: 1778fd77cbec
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c41a7d92e610"
down_revision: str | Sequence[str] | None = "1778fd77cbec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profile_update_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("requester_id", sa.String(length=36), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("resolved_by", sa.String(length=36), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["patient_profiles.id"]),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_profile_update_requests_status_created", "profile_update_requests", ["status", "created_at"]
    )
    op.create_index(
        "ix_profile_update_requests_profile_created", "profile_update_requests", ["profile_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_profile_update_requests_profile_created", table_name="profile_update_requests")
    op.drop_index("ix_profile_update_requests_status_created", table_name="profile_update_requests")
    op.drop_table("profile_update_requests")
