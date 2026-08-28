"""add reduced_motion/no_animations/no_shadows to osb_settings

Revision ID: osb_access_001
Revises: xp_source_len_001
Create Date: 2026-04-12

GF115 fix — Session 149 flagged `osb_settings` as schema-drifted because
the ORM (`models/osb_settings.py:61-63`) declared `reduced_motion`,
`no_animations`, and `no_shadows` as NOT NULL Boolean columns but the
live table was missing them. Session 149 shimmed the three write
handlers with a 503 `_degrade_schema_error()` fallback; Session 152
removes that shim after this migration lands.

server_default is required because the columns are NOT NULL and the
table already has rows — Postgres needs a value to backfill.
"""

import sqlalchemy as sa

from alembic import op

revision = "osb_access_001"
down_revision = "xp_source_len_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "osb_settings",
        sa.Column(
            "reduced_motion",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "osb_settings",
        sa.Column(
            "no_animations",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "osb_settings",
        sa.Column(
            "no_shadows",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("osb_settings", "no_shadows")
    op.drop_column("osb_settings", "no_animations")
    op.drop_column("osb_settings", "reduced_motion")
