"""user profile avatar

Revision ID: e2b4d6f8a0c1
Revises: d1a3c5e7f9b2
Create Date: 2026-08-18 02:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e2b4d6f8a0c1'
down_revision: Union[str, None] = 'd1a3c5e7f9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar', sa.LargeBinary(), nullable=True))
    op.add_column('users', sa.Column('avatar_type', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('avatar_size', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'avatar_size')
    op.drop_column('users', 'avatar_type')
    op.drop_column('users', 'avatar')
