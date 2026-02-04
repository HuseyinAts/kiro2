"""Add premium tier fields to users table"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:changeme_strong_password_here@localhost/kiro2_db')

try:
    with engine.begin() as conn:
        print("[1/2] Adding is_premium field...")
        conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_premium BOOLEAN NOT NULL DEFAULT FALSE
        """))
        print("[OK] is_premium field added")

        print("[2/2] Adding premium_expires_at field...")
        conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMPTZ
        """))
        print("[OK] premium_expires_at field added")

        print("\n[OK] SUCCESS: Premium tier fields added to users table!")
        print("\nFields added:")
        print("  - is_premium: Boolean (default: FALSE)")
        print("  - premium_expires_at: Timestamp with timezone (nullable)")

except Exception as e:
    print(f'[ERROR] {e}')
