#!/usr/bin/env python3
"""
MVP Beta Launch - Seed Data Script
Creates test users directly in PostgreSQL for MVP testing.

Uses bcrypt (passlib) for password hashing - compatible with auth system.
Idempotent: skips users that already exist.

Usage:
    cd backend
    python scripts/seed_mvp_data.py
"""

import os
import sys
import uuid

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from passlib.context import CryptContext

# Password hasher (must match auth system)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection - strip asyncpg driver for sync psycopg2
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:changeme_strong_password_here@localhost:5434/kiro2",
)
# Convert async URL to sync: remove +asyncpg
SYNC_URL = DATABASE_URL.replace("+asyncpg", "").replace("postgresql://", "")
# Parse: user:pass@host:port/dbname
try:
    auth_host, dbname = SYNC_URL.rsplit("/", 1)
    userpass, hostport = auth_host.rsplit("@", 1)
    db_user, db_pass = userpass.split(":", 1)
    db_host, db_port = hostport.split(":", 1)
except ValueError:
    print(f"ERROR: Cannot parse DATABASE_URL: {DATABASE_URL}")
    print("Expected format: postgresql+asyncpg://user:pass@host:port/dbname")
    sys.exit(1)

# MVP Test Users
MVP_USERS = [
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "mvp-student@kiro2.com")),
        "email": "test@kiro2.com",
        "username": "test_user",
        "password": "Kiro2Beta2026@x",
        "first_name": "Test",
        "last_name": "User",
        "role": "STUDENT",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "mvp-ogrenci@kiro2.com")),
        "email": "ogrenci@kiro2.com",
        "username": "ogrenci_mvp",
        "password": "Kiro2Beta2026@x",
        "first_name": "Demo",
        "last_name": "Ogrenci",
        "role": "STUDENT",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "mvp-ogretmen@kiro2.com")),
        "email": "ogretmen@kiro2.com",
        "username": "ogretmen_mvp",
        "password": "Kiro2Beta2026@x",
        "first_name": "Demo",
        "last_name": "Ogretmen",
        "role": "TEACHER",
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "mvp-admin@kiro2.com")),
        "email": "admin@kiro2.com",
        "username": "admin_mvp",
        "password": "Kiro2Beta2026@x",
        "first_name": "Demo",
        "last_name": "Admin",
        "role": "ADMIN",
    },
]

INSERT_SQL = """
INSERT INTO users (
    id, email, username, password_hash,
    first_name, last_name, role,
    is_active, is_verified,
    total_xp, level,
    is_premium, is_2fa_enabled
)
VALUES (
    %(id)s, %(email)s, %(username)s, %(password_hash)s,
    %(first_name)s, %(last_name)s, %(role)s::userrole,
    TRUE, TRUE,
    0, 1,
    FALSE, FALSE
)
ON CONFLICT (email) DO NOTHING
"""


def main():
    print(f"Connecting to PostgreSQL: {db_host}:{db_port}/{dbname}")
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=int(db_port),
            dbname=dbname,
            user=db_user,
            password=db_pass,
        )
    except psycopg2.OperationalError as e:
        print(f"ERROR: DB connection failed: {e}")
        print("Check DATABASE_URL in .env.mvp")
        sys.exit(1)
    conn.autocommit = False
    cur = conn.cursor()

    created = 0
    skipped = 0

    for user in MVP_USERS:
        # Check if already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (user["email"],))
        if cur.fetchone():
            print(f"  SKIP: {user['email']} (already exists)")
            skipped += 1
            continue

        # Hash password with bcrypt
        password_hash = pwd_context.hash(user["password"])

        cur.execute(
            INSERT_SQL,
            {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "password_hash": password_hash,
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user["role"],
            },
        )
        print(f"  CREATE: {user['email']} ({user['role']})")
        created += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nDone: {created} created, {skipped} skipped")
    print("\nMVP Login Credentials:")
    print("-" * 50)
    for user in MVP_USERS:
        print(f"  {user['role']:8s} | {user['email']} | {user['password']}")


if __name__ == "__main__":
    main()
