"""add_2fa_fields_to_users

Revision ID: d7a10d07b648
Revises: 003_real_perf_idx
Create Date: 2025-11-11 18:43:51.775173

Sprint 4: Two-Factor Authentication (2FA)
Adds TOTP secret, 2FA enabled flag, and backup codes to users table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = 'd7a10d07b648'
down_revision: Union[str, None] = '003_real_perf_idx'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 2FA fields to users table"""

    # Add secret_2fa column (TOTP secret key)
    op.add_column(
        'users',
        sa.Column(
            'secret_2fa',
            sa.String(32),
            nullable=True,
            comment='TOTP secret key for 2FA'
        )
    )

    # Add is_2fa_enabled column
    op.add_column(
        'users',
        sa.Column(
            'is_2fa_enabled',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='2FA enabled status'
        )
    )

    # Add backup_codes_hashed column (JSON array of hashed codes)
    op.add_column(
        'users',
        sa.Column(
            'backup_codes_hashed',
            JSON,
            nullable=True,
            comment='Hashed backup codes for 2FA recovery'
        )
    )

    # Create index on is_2fa_enabled for quick lookup
    op.create_index(
        'idx_users_2fa_enabled',
        'users',
        ['is_2fa_enabled']
    )

    print("SUCCESS: 2FA fields added to users table")


def downgrade() -> None:
    """Remove 2FA fields from users table"""

    # Drop index
    op.drop_index('idx_users_2fa_enabled', table_name='users')

    # Drop columns
    op.drop_column('users', 'backup_codes_hashed')
    op.drop_column('users', 'is_2fa_enabled')
    op.drop_column('users', 'secret_2fa')

    print("SUCCESS: 2FA fields removed from users table")