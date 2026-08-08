
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
