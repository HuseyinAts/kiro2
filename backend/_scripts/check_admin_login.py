#!/usr/bin/env python3
"""
Admin login kontrolü
"""
import psycopg2
from passlib.context import CryptContext

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

ADMIN_EMAIL = "admin@turkiyesinav.com"
ADMIN_PASSWORD = "admin123"

def check_admin():
    """Check admin user and test password"""
    print("Checking admin user...")

    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Get admin user
        cursor.execute("""
            SELECT id, email, username, password_hash, role, is_active, is_verified
            FROM users WHERE email = %s
        """, (ADMIN_EMAIL,))

        user = cursor.fetchone()

        if not user:
            print("\n[ERROR] Admin user not found in database!")
            return

        user_id, email, username, password_hash, role, is_active, is_verified = user

        print("\n" + "="*60)
        print("Admin User Details:")
        print("="*60)
        print(f"ID: {user_id}")
        print(f"Email: {email}")
        print(f"Username: {username}")
        print(f"Role: {role}")
        print(f"Active: {is_active}")
        print(f"Verified: {is_verified}")
        print(f"Password Hash (first 50 chars): {password_hash[:50]}...")
        print("="*60)

        # Test password
        print("\nTesting password verification...")
        is_valid = pwd_context.verify(ADMIN_PASSWORD, password_hash)

        if is_valid:
            print("[OK] Password verification SUCCESSFUL!")
            print(f"    Password '{ADMIN_PASSWORD}' matches the stored hash")
        else:
            print("[ERROR] Password verification FAILED!")
            print(f"    Password '{ADMIN_PASSWORD}' does NOT match the stored hash")

            # Generate new hash for comparison
            new_hash = pwd_context.hash(ADMIN_PASSWORD)
            print(f"\nNew hash generated: {new_hash[:50]}...")
            print("\nYou may need to update the password hash in database")

        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_admin()
