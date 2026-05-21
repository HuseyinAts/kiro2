#!/usr/bin/env python3
"""
Faz 7.1 fix — beta user'lara student_profiles satırı yarat.

Bug: beta_create_users.py sadece users tablosuna INSERT etti.
exam_sessions.student_id → student_profiles.id FK, beta user'lar
profile olmadan sınav başlatamıyor (HTTP 500 ForeignKeyViolationError).

Bu script idempotent — varsa atlar, yoksa yaratır.

USAGE:
  python backend/scripts/quality/beta_create_profiles.py --dry-run
  python backend/scripts/quality/beta_create_profiles.py --apply
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        print("[error] --dry-run veya --apply gerekli")
        return 2

    from sqlalchemy import text

    eng = get_engine()

    # Mevcut beta users (profile YOKSA)
    with eng.connect() as c:
        rows = c.execute(
            text("""
                SELECT u.id, u.email
                FROM users u
                LEFT JOIN student_profiles sp ON sp.user_id::text = u.id::text
                WHERE u.email LIKE 'beta%@kiro2.com'
                  AND sp.id IS NULL
                ORDER BY u.email
            """)
        ).fetchall()

    if not rows:
        print("[done] Tüm beta user'ların student_profiles satırı var")
        return 0

    print(f"[plan] {len(rows)} beta user için profile yaratılacak:")
    for r in rows:
        print(f"  {r.email}  (user_id={r.id[:8]})")
    print()

    if args.dry_run:
        print("[dry-run] DB INSERT atlandı")
        return 0

    # CONVENTION: student_profiles.id MUST EQUAL users.id
    # Reason: api/sinav.py line 396 calls create_exam_session(student_id=current_user.id);
    # exam_sessions.student_id → student_profiles.id FK. Mismatch = HTTP 500.
    created = 0
    with eng.begin() as c:
        for r in rows:
            c.execute(
                text("""
                    INSERT INTO student_profiles (
                        id, user_id, grade_level, hedef_sinav, veli_onay,
                        current_level, total_study_hours, total_questions_solved,
                        correct_answers, irt_ability, created_at, updated_at
                    )
                    VALUES (
                        :uid, :uid, 12, 'TYT', TRUE,
                        0.5, 0, 0,
                        0, 0.0, :now, :now
                    )
                """),
                {"uid": r.id, "now": datetime.now()},
            )
            created += 1
            print(f"  [created] {r.email}  profile_id={r.id[:8]} (== user_id)")

    print(f"\n[done] {created} profile yaratıldı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
