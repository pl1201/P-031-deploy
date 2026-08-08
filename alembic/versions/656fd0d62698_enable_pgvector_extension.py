"""Enable pgvector extension for PostgreSQL deployments.

Revision ID: 656fd0d62698
Revises: 5394cb31dc4e
"""
from collections.abc import Sequence

from alembic import op

revision: str = "656fd0d62698"
down_revision: str | Sequence[str] | None = "5394cb31dc4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP EXTENSION IF EXISTS vector")
