"""enable pgvector extension (chuẩn bị DAT-06 — guideline_chunks.embedding)

Revision ID: 656fd0d62698
Revises: 5394cb31dc4e
Create Date: 2026-08-07 00:00:00.000000

Chỉ áp dụng trên Postgres (Supabase) — bỏ qua trên SQLite (dev/test/CI),
nơi vốn không có khái niệm extension và guideline_chunks.embedding vẫn ở
dạng JSON (xem TODO trong src/db/base.py). Theo ADR-008: bật extension qua
migration Alembic, không bật tay qua Supabase Studio UI.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '656fd0d62698'
down_revision: Union[str, Sequence[str], None] = '5394cb31dc4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP EXTENSION IF EXISTS vector")
