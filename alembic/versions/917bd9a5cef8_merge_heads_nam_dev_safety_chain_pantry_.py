"""Merge heads: nam-dev safety chain + pantry_items/substitution_scopes.

Revision ID: 917bd9a5cef8
Revises: e63b8c4f1a32, f3a1c9d2b7e4
"""

from collections.abc import Sequence

revision: str = "917bd9a5cef8"
down_revision: str | Sequence[str] | None = ("e63b8c4f1a32", "f3a1c9d2b7e4")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
