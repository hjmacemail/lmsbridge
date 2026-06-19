"""tenant licensing/subscription fields

Revision ID: a7c3licensing01
Revises: 4f91f26cce22
Create Date: 2026-06-17 19:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7c3licensing01'
down_revision: Union[str, None] = '4f91f26cce22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'subscription_status', sa.String(length=32),
            server_default='trial', nullable=False))
        batch_op.add_column(sa.Column(
            'plan', sa.String(length=32), server_default='pilot', nullable=False))
        batch_op.add_column(sa.Column('seat_limit', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column(
            'license_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_column('license_expires_at')
        batch_op.drop_column('seat_limit')
        batch_op.drop_column('plan')
        batch_op.drop_column('subscription_status')
