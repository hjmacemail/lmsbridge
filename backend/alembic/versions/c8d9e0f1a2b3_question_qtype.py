"""question qtype (Sage question types: mcq/true_false/multi/short)

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-06-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('questions', schema=None) as b:
        b.add_column(sa.Column('qtype', sa.String(length=16), nullable=False, server_default='mcq'))


def downgrade() -> None:
    with op.batch_alter_table('questions', schema=None) as b:
        b.drop_column('qtype')
