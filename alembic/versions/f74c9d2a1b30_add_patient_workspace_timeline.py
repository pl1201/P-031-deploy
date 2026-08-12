"""Add patient-centric observations, notes, and review events.

Revision ID: f74c9d2a1b30
Revises: e63b8c4f1a32
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f74c9d2a1b30"
down_revision: str | Sequence[str] | None = "e63b8c4f1a32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("profile_id", sa.String(length=36), sa.ForeignKey("patient_profiles.id"), nullable=False),
        sa.Column("observation_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="manual"),
        sa.Column("recorded_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_patient_observations_profile_type_measured", "patient_observations", ["profile_id", "observation_type", "measured_at"])

    op.create_table(
        "clinical_notes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("profile_id", sa.String(length=36), sa.ForeignKey("patient_profiles.id"), nullable=False),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("note_type", sa.String(length=30), nullable=False, server_default="follow_up"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="care_team"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_clinical_notes_profile_created", "clinical_notes", ["profile_id", "created_at"])

    op.create_table(
        "meal_plan_review_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("meal_plan_id", sa.String(length=36), sa.ForeignKey("meal_plans.id"), nullable=False),
        sa.Column("profile_id", sa.String(length=36), sa.ForeignKey("patient_profiles.id"), nullable=False),
        sa.Column("reviewer_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("menu_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("menu_hash", sa.String(length=64), nullable=True),
        sa.Column("nutrition_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_review_events_profile_created", "meal_plan_review_events", ["profile_id", "created_at"])
    op.create_index("ix_review_events_plan_created", "meal_plan_review_events", ["meal_plan_id", "created_at"])
    op.create_index("ix_review_events_decision_created", "meal_plan_review_events", ["decision", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_review_events_decision_created", table_name="meal_plan_review_events")
    op.drop_index("ix_review_events_plan_created", table_name="meal_plan_review_events")
    op.drop_index("ix_review_events_profile_created", table_name="meal_plan_review_events")
    op.drop_table("meal_plan_review_events")
    op.drop_index("ix_clinical_notes_profile_created", table_name="clinical_notes")
    op.drop_table("clinical_notes")
    op.drop_index("ix_patient_observations_profile_type_measured", table_name="patient_observations")
    op.drop_table("patient_observations")
