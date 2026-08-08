"""merge heads: pgvector + meal_plan_items_use_dishes

Revision ID: aedef0ff7743
Revises: 656fd0d62698, a82f7c11d912
Create Date: 2026-08-07 19:06:23.797959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aedef0ff7743'
down_revision: Union[str, Sequence[str], None] = ('656fd0d62698', 'a82f7c11d912')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
