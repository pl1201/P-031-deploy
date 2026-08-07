"""food_food_interactions + drug_meal_timing (DAT-18/DAT-19)

Revision ID: 5394cb31dc4e
Revises: d027f9b06bd5
Create Date: 2026-08-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5394cb31dc4e'
down_revision: Union[str, Sequence[str], None] = 'd027f9b06bd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('food_food_interactions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('substance_a', sa.String(length=255), nullable=False),
    sa.Column('substance_b', sa.String(length=255), nullable=False),
    sa.Column('food_examples_vi', sa.Text(), nullable=False),
    sa.Column('mechanism_vi', sa.Text(), nullable=False),
    sa.Column('direction', sa.String(length=20), nullable=False),
    sa.Column('effect_size_vi', sa.Text(), nullable=True),
    sa.Column('clinical_significance', sa.String(length=10), nullable=False),
    sa.Column('applies_to_condition', sa.String(length=20), nullable=True),
    sa.Column('recommendation_vi', sa.Text(), nullable=False),
    sa.Column('source_ref', sa.Text(), nullable=False),
    sa.Column('pmid', sa.String(length=20), nullable=True),
    sa.Column('verify_status', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('drug_meal_timing',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('drug_name', sa.String(length=255), nullable=False),
    sa.Column('drug_class', sa.String(length=255), nullable=True),
    sa.Column('timing_rule', sa.String(length=20), nullable=False),
    sa.Column('offset_minutes', sa.Integer(), nullable=True),
    sa.Column('relative_to', sa.String(length=50), nullable=False),
    sa.Column('rationale_pk_vi', sa.Text(), nullable=False),
    sa.Column('condition', sa.String(length=20), nullable=True),
    sa.Column('source_ref', sa.Text(), nullable=False),
    sa.Column('page_ref', sa.String(length=50), nullable=True),
    sa.Column('verify_status', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drug_meal_timing_drug_name'), 'drug_meal_timing', ['drug_name'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_drug_meal_timing_drug_name'), table_name='drug_meal_timing')
    op.drop_table('drug_meal_timing')
    op.drop_table('food_food_interactions')
    # ### end Alembic commands ###
