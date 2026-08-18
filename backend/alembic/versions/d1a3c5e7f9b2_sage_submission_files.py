"""sage submission file attachments

Revision ID: d1a3c5e7f9b2
Revises: c9e2f4a7b1d6
Create Date: 2026-08-18 01:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd1a3c5e7f9b2'
down_revision: Union[str, None] = 'c9e2f4a7b1d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sage_submissions', sa.Column('file_name', sa.String(length=255), nullable=True))
    op.add_column('sage_submissions', sa.Column('content_type', sa.String(length=128), nullable=True))
    op.add_column('sage_submissions', sa.Column('size_bytes', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('sage_submissions', sa.Column('file_content', sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column('sage_submissions', 'file_content')
    op.drop_column('sage_submissions', 'size_bytes')
    op.drop_column('sage_submissions', 'content_type')
    op.drop_column('sage_submissions', 'file_name')
