"""question distractor_misconceptions (per-wrong-choice misconception tags for Sage quizzes)

Revision ID: f2c4e6a8b0d1
Revises: e2b4d6f8a0c1
Create Date: 2026-10-31 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2c4e6a8b0d1'
down_revision: Union[str, None] = 'e2b4d6f8a0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('questions', schema=None) as b:
        b.add_column(sa.Column('distractor_misconceptions', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('questions', schema=None) as b:
        b.drop_column('distractor_misconceptions')
