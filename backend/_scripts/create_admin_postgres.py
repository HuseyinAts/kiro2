#!/usr/bin/env python3
"""
Admin kullanıcı oluşturma - PostgreSQL
"""
import psycopg2
from passlib.context import CryptContext
from datetime import datetime, timezone
import uuid

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "database": "turkiye_sinav_db",
    "user": "postgres",
    "password": "1470"
}

# Admin credentials
ADMIN_EMAIL = "admin@turkiyesinav.com"
ADMIN_PASSWORD = "admin123"

def create_admin():
    """Create admin user"""
    print("Creating admin user...")

    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Check if admin exists
        cursor.execute("SELECT id, email, role FROM users WHERE email = %s", (ADMIN_EMAIL,))
        existing = cursor.fetchone()

        if existing:
            print(f"\n[!] Admin user already exists!")
            print(f"    ID: {existing[0]}")
            print(f"    Email: {existing[1]}")
            print(f"    Role: {existing[2]}")
            conn.close()
            return

        # Hash password
        password_hash = pwd_context.hash(ADMIN_PASSWORD)

        # Create admin
        admin_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        cursor.execute("""
            INSERT INTO users (
                id, email, username, password_hash,
                first_name, last_name, role,
                is_active, is_verified, is_2fa_enabled, is_premium,
                total_xp, level,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            admin_id,
            ADMIN_EMAIL,
            'admin',
            password_hash,
            'Platform',
            'Yöneticisi',
            'ADMIN',
            True,
            True,
            False,
            False,
            0,
            1,
            now,
            now
        ))

        conn.commit()

        # Verify
        cursor.execute("SELECT id, email, username, role FROM users WHERE email = %s", (ADMIN_EMAIL,))
        admin = cursor.fetchone()

        print("\n" + "="*60)
        print("[OK] Admin user created successfully!")
        print("="*60)
        print(f"\nUser Details:")
        print(f"  ID: {admin[0]}")
        print(f"  Email: {admin[1]}")
        print(f"  Username: {admin[2]}")
        print(f"  Role: {admin[3]}")
        print(f"\nLogin Credentials:")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD}")
        print(f"\nLogin at: http://localhost:3001")
        print("="*60 + "\n")

        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Failed to create admin: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_admin()
