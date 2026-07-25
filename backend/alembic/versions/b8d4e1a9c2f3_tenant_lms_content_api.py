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

    # Activate the one-click LMS import in the already-seeded public demo. The seeder only
    # runs on an empty DB, so wire the existing 'demo-university' tenant to the offline
    # 'sample' provider here and give its courses a course reference. No-op elsewhere.
    try:
        from app.core.crypto import encrypt_secret
        conn = op.get_bind()
        row = conn.execute(sa.text(
            "SELECT id FROM tenants WHERE slug = 'demo-university'"
        )).fetchone()
        if row is not None:
            tenant_id = row[0]
            conn.execute(
                sa.text(
                    "UPDATE tenants SET lms_provider='sample', "
                    "lms_base_url='sample://demo-university', "
                    "lms_api_key_encrypted=:k "
                    "WHERE id=:tid AND (lms_provider IS NULL OR lms_provider='')"
                ),
                {"k": encrypt_secret("demo-sample-token"), "tid": tenant_id},
            )
            conn.execute(
                sa.text(
                    "UPDATE courses SET lms_course_ref = brightspace_course_id "
                    "WHERE tenant_id=:tid AND (lms_course_ref IS NULL OR lms_course_ref='') "
                    "AND brightspace_course_id IS NOT NULL"
                ),
                {"tid": tenant_id},
            )
    except Exception:  # noqa: BLE001 — demo convenience only; never block the schema migration.
        pass


def downgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as b:
        b.drop_column('lms_api_key_encrypted')
        b.drop_column('lms_base_url')
        b.drop_column('lms_provider')
