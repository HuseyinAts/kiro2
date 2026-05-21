#!/usr/bin/env python3
"""Verify beta users exist + are active."""

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import create_engine, text

OUT = Path(__file__).parent / "beta_users_verify_RESULT.md"
eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

lines = [
    "# Beta Users — DB doğrulama\n",
    "| email | username | role | is_active | created |\n|---|---|---|---|---|",
]

with eng.connect() as c:
    rows = c.execute(
        text(
            "SELECT email, username, role, is_active, created_at "
            "FROM users WHERE email LIKE 'beta%@kiro2.com' "
            "ORDER BY email"
        )
    ).fetchall()

for email, uname, role, active, created in rows:
    lines.append(
        f"| {email} | {uname} | {role} | {active} | {created.strftime('%Y-%m-%d %H:%M')} |"
    )

lines.append(f"\n**Total beta users:** {len(rows)}")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Written: {OUT}")
