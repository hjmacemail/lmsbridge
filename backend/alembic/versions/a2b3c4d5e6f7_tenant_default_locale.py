"""tenant default_locale (institution language)

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-07-14 04:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as b:
        b.add_column(sa.Column('default_locale', sa.String(length=8), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as b:
        b.drop_column('default_locale')
