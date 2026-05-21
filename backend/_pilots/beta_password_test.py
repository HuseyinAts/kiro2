#!/usr/bin/env python3
"""Verify beta01 password hash matches Beta01!Kiro2026."""

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from passlib.context import CryptContext
from sqlalchemy import create_engine, text

OUT = Path(__file__).parent / "beta_password_test_RESULT.md"
eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

lines = [
    "# Beta password hash verification\n",
    "| email | hash prefix | verify(Beta0X!Kiro2026) |\n|---|---|---|",
]

with eng.connect() as c:
    rows = c.execute(
        text(
            "SELECT email, password_hash FROM users "
            "WHERE email LIKE 'beta%@kiro2.com' ORDER BY email"
        )
    ).fetchall()

for email, hash_val in rows:
    # extract NN from beta01@kiro2.com -> 01
    nn = email.replace("beta", "").split("@")[0]
    expected_pw = f"Beta{nn}!Kiro2026"
    try:
        ok = pwd.verify(expected_pw, hash_val)
    except Exception as e:
        ok = f"ERR: {e}"
    lines.append(
        f"| {email} | `{hash_val[:30]}...` | {ok} (expected: `{expected_pw}`) |"
    )

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Written: {OUT}")
