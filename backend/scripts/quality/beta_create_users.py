#!/usr/bin/env python3
"""
Faz 7.1 Manual Beta — bulk test user create.

10 öğrenci hesabı (beta01@kiro2.com … beta10@kiro2.com).
Şifre: Beta{n}!Kiro2026 (n=01-10).
Rol: ogrenci (STUDENT).

USAGE:
  python backend/scripts/quality/beta_create_users.py --dry-run
  python backend/scripts/quality/beta_create_users.py --apply
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BETA_COUNT = 10
BETA_DOMAIN = "kiro2.com"


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        print("[error] --dry-run veya --apply gerekli")
        return 2

    from passlib.context import CryptContext
    from sqlalchemy import text

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    eng = get_engine()
    mode = "apply" if args.apply else "dryrun"

    print(f"[mode] {mode}")
    print()

    users = []
    for i in range(1, BETA_COUNT + 1):
        email = f"beta{i:02d}@{BETA_DOMAIN}"
        password = f"Beta{i:02d}!Kiro2026"
        name = f"Beta User {i:02d}"
        users.append((email, password, name))

    print("[plan] 10 beta user oluşturulacak:")
    for email, pw, name in users:
        print(f"  {email} / {pw}  ({name})")
    print()

    if args.dry_run:
        print("[dry-run] DB UPDATE atlandı")
        return 0

    # Apply: DB UPDATE
    import uuid

    created = 0
    skipped = 0
    with eng.begin() as c:
        for email, password, name in users:
            # Existence check
            existing = c.execute(
                text("SELECT id FROM users WHERE email = :email"), {"email": email}
            ).scalar()
            if existing:
                skipped += 1
                print(f"  [skip] {email} zaten mevcut (id={existing[:8]})")
                continue

            uid = str(uuid.uuid4())
            hashed = pwd_context.hash(password)
            now = datetime.now()
            username = email.split("@")[0]
            first = "Beta"
            last = name.replace("Beta User ", "")

            c.execute(
                text("""
                    INSERT INTO users (id, email, username, password_hash, first_name, last_name, role, is_active, created_at, updated_at)
                    VALUES (:id, :email, :username, :pw, :first, :last, 'STUDENT', TRUE, :now, :now)
                """),
                {
                    "id": uid,
                    "email": email,
                    "username": username,
                    "pw": hashed,
                    "first": first,
                    "last": last,
                    "now": now,
                },
            )
            created += 1
            print(f"  [created] {email} id={uid[:8]}")

    print()
    print(f"[done] {created} user oluşturuldu, {skipped} skip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
