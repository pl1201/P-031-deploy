"""Merge heads: safety-chain+pantry chain with BE-07 food_logs migration.

Revision ID: 8546da42031c
Revises: 917bd9a5cef8, b7c214e93a08
"""

from collections.abc import Sequence

revision: str = "8546da42031c"
down_revision: str | Sequence[str] | None = ("917bd9a5cef8", "b7c214e93a08")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
