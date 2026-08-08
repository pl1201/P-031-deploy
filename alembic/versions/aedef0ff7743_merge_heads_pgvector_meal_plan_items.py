"""Merge pgvector and dish meal-plan migration heads.

Revision ID: aedef0ff7743
Revises: 656fd0d62698, a82f7c11d912
"""
from collections.abc import Sequence

revision: str = "aedef0ff7743"
down_revision: str | Sequence[str] | None = ("656fd0d62698", "a82f7c11d912")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
