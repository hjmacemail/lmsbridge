"""drop unused Sage Q&A tables (pivoted to mini-LMS)

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-06-21 00:40:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a6b7c8d9e0f1'
down_revision: Union[str, None] = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ('sage_answers', 'sage_posts', 'sage_memberships', 'sage_classes'):
        op.drop_table(table)


def downgrade() -> None:
    # Recreate minimal structures (data is not restored).
    op.create_table(
        'sage_classes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=160), nullable=False),
        sa.Column('subject', sa.String(length=120)),
        sa.Column('join_code', sa.String(length=12), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_table(
        'sage_memberships',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=16)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_table(
        'sage_posts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text()),
        sa.Column('tags', sa.String(length=255)),
        sa.Column('anonymous', sa.Boolean()),
        sa.Column('resolved', sa.Boolean()),
        sa.Column('ai_misconception', sa.String(length=255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_table(
        'sage_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer()),
        sa.Column('is_ai', sa.Boolean()),
        sa.Column('is_instructor', sa.Boolean()),
        sa.Column('endorsed', sa.Boolean()),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
