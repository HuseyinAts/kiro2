#!/usr/bin/env python3
"""
Admin kullanıcı oluşturma - Direkt SQLite
"""
import sqlite3
from passlib.context import CryptContext
from datetime import datetime, timezone

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database path
DB_PATH = "kiro2_development.db"

# Admin credentials
ADMIN_EMAIL = "admin@turkiyesinav.com"
ADMIN_PASSWORD = "admin123"

def create_admin():
    """Create admin user"""
    print("Creating admin user...")

    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if admin exists
        cursor.execute("SELECT id, email, role FROM users WHERE email = ?", (ADMIN_EMAIL,))
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
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO users (
                id, email, username, password_hash,
                first_name, last_name, role,
                is_active, is_verified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin-001',
            ADMIN_EMAIL,
            'admin',
            password_hash,
            'Platform',
            'Yöneticisi',
            'admin',
            1,
            1,
            now,
            now
        ))

        conn.commit()

        # Verify
        cursor.execute("SELECT id, email, username, role FROM users WHERE email = ?", (ADMIN_EMAIL,))
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
        raise

if __name__ == "__main__":
    create_admin()
