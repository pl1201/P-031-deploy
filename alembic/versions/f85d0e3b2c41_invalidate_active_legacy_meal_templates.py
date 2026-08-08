"""Invalidate active plans that stored whole meal templates as dishes.

Revision ID: f85d0e3b2c41
Revises: f74c9d2a1b30

`MENU-*` rows came from spreadsheet meal bundles and are not concrete dishes.
They cannot be renamed safely, so active plans must be regenerated. Approved
history is deliberately left untouched.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f85d0e3b2c41"
down_revision: str | Sequence[str] | None = "f74c9d2a1b30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE meal_plans
        SET status = 'failed',
            reviewer_notes = 'SYSTEM: Legacy MENU-* meal bundle detected; regenerate this plan to use concrete dishes.'
        WHERE status IN ('drafting', 'pending_review')
          AND EXISTS (
              SELECT 1
              FROM meal_plan_items
              WHERE meal_plan_items.plan_id = meal_plans.id
                AND meal_plan_items.dish_id LIKE 'MENU-%'
          )
        """
    )


def downgrade() -> None:
    # The original drafting/pending_review state cannot be inferred safely.
    pass
