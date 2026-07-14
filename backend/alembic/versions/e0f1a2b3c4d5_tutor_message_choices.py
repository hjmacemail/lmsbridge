"""tutor message choices (multiple-choice checks)

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-07-14 03:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e0f1a2b3c4d5'
down_revision: Union[str, None] = 'd9e0f1a2b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('tutor_messages', schema=None) as b:
        b.add_column(sa.Column('choices', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('tutor_messages', schema=None) as b:
        b.drop_column('choices')
