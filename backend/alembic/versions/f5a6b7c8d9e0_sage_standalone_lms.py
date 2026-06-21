"""sage standalone mini-LMS (course join code/owner, authored MCQ questions)

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-06-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f5a6b7c8d9e0'
down_revision: Union[str, None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('join_code', sa.String(length=12), nullable=True))
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_courses_join_code', ['join_code'], unique=True)
        batch_op.create_foreign_key(
            'fk_courses_owner', 'users', ['owner_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('choices', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('correct_answer', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_column('correct_answer')
        batch_op.drop_column('choices')

    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_courses_owner', type_='foreignkey')
        batch_op.drop_index('ix_courses_join_code')
        batch_op.drop_column('owner_id')
        batch_op.drop_column('join_code')
