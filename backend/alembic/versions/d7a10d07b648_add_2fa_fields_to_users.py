"""add_2fa_fields_to_users

Revision ID: d7a10d07b648
Revises: 003_real_perf_idx
Create Date: 2025-11-11 18:43:51.775173

Sprint 4: Two-Factor Authentication (2FA)
Adds TOTP secret, 2FA enabled flag, and backup codes to users table
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd7a10d07b648'
down_revision: Union[str, None] = '003_real_perf_idx'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 2FA fields to users table (idempotent)"""
    conn = op.get_bind()

    def column_exists(table: str, column: str) -> bool:
        result = conn.execute(
            sa.text("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name=:t AND column_name=:c)"),
            {"t": table, "c": column}
        )
        return result.scalar()

    if not column_exists('users', 'secret_2fa'):
        op.add_column('users', sa.Column('secret_2fa', sa.String(32), nullable=True))

    if not column_exists('users', 'is_2fa_enabled'):
        op.add_column('users', sa.Column('is_2fa_enabled', sa.Boolean(), nullable=False, server_default='false'))

    if not column_exists('users', 'backup_codes_hashed'):
        op.add_column('users', sa.Column('backup_codes_hashed', JSON, nullable=True))

    try:
        op.create_index('idx_users_2fa_enabled', 'users', ['is_2fa_enabled'], if_not_exists=True)
    except Exception:
        pass


def downgrade() -> None:
    """Remove 2FA fields from users table"""

    # Drop index
    op.drop_index('idx_users_2fa_enabled', table_name='users')

    # Drop columns
    op.drop_column('users', 'backup_codes_hashed')
    op.drop_column('users', 'is_2fa_enabled')
    op.drop_column('users', 'secret_2fa')

    print("SUCCESS: 2FA fields removed from users table")
