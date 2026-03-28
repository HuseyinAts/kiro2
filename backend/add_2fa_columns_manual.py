"""Manually add 2FA columns to users table"""

import os
import sys

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.exit(
        "ERROR: DATABASE_URL env var required. Example: postgresql://postgres:pass@localhost:5434/kiro2"
    )

engine = create_engine(DATABASE_URL)

try:
    with engine.begin() as conn:
        # Add secret_2fa column
        conn.execute(
            text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS secret_2fa VARCHAR(32)
        """)
        )
        print("[OK] Added secret_2fa column")

        # Add is_2fa_enabled column
        conn.execute(
            text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE
        """)
        )
        print("[OK] Added is_2fa_enabled column")

        # Add backup_codes_hashed column
        conn.execute(
            text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS backup_codes_hashed JSONB
        """)
        )
        print("[OK] Added backup_codes_hashed column")

        # Create index
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_users_2fa_enabled
            ON users(is_2fa_enabled)
        """)
        )
        print("[OK] Created idx_users_2fa_enabled index")

        print("\nSUCCESS: All 2FA fields added to users table!")

except Exception as e:
    print(f"ERROR: {e}")
