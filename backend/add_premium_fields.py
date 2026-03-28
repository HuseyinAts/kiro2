"""Add premium tier fields to users table"""

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
        print("[1/2] Adding is_premium field...")
        conn.execute(
            text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_premium BOOLEAN NOT NULL DEFAULT FALSE
        """)
        )
        print("[OK] is_premium field added")

        print("[2/2] Adding premium_expires_at field...")
        conn.execute(
            text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMPTZ
        """)
        )
        print("[OK] premium_expires_at field added")

        print("\n[OK] SUCCESS: Premium tier fields added to users table!")
        print("\nFields added:")
        print("  - is_premium: Boolean (default: FALSE)")
        print("  - premium_expires_at: Timestamp with timezone (nullable)")

except Exception as e:
    print(f"[ERROR] {e}")
