"""mastery snapshots (class-average mastery over time -> trends)

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-07-14 03:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e0f1a2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mastery_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(),
                  sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', sa.Integer(),
                  sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('avg_mastery', sa.Float(), nullable=False, server_default='0'),
        sa.Column('at_risk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('taken_on', sa.Date(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('course_id', 'concept_id', 'taken_on', name='uq_snapshot_day'),
    )


def downgrade() -> None:
    op.drop_table('mastery_snapshots')
