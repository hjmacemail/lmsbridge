"""instructor profile (user.title/bio), course.syllabus, material.kind/language

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-06-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a6b7c8d9e0f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as b:
        b.add_column(sa.Column('title', sa.String(length=160), nullable=True))
        b.add_column(sa.Column('bio', sa.Text(), nullable=True))
    with op.batch_alter_table('courses', schema=None) as b:
        b.add_column(sa.Column('syllabus', sa.Text(), nullable=True))
    with op.batch_alter_table('course_materials', schema=None) as b:
        b.add_column(sa.Column('kind', sa.String(length=16), nullable=False, server_default='file'))
        b.add_column(sa.Column('language', sa.String(length=32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('course_materials', schema=None) as b:
        b.drop_column('language')
        b.drop_column('kind')
    with op.batch_alter_table('courses', schema=None) as b:
        b.drop_column('syllabus')
    with op.batch_alter_table('users', schema=None) as b:
        b.drop_column('bio')
        b.drop_column('title')
