"""tenant LMS content API (admin-configured, tokenless instructor import)

Revision ID: b8d4e1a9c2f3
Revises: a2b3c4d5e6f7
Create Date: 2026-07-25 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8d4e1a9c2f3'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as b:
        b.add_column(sa.Column('lms_provider', sa.String(length=32), nullable=True))
        b.add_column(sa.Column('lms_base_url', sa.String(length=512), nullable=True))
        b.add_column(sa.Column('lms_api_key_encrypted', sa.String(length=2048), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as b:
        b.drop_column('lms_api_key_encrypted')
        b.drop_column('lms_base_url')
        b.drop_column('lms_provider')
