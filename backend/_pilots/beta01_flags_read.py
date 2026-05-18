#!/usr/bin/env python3
"""Read beta01's flagged questions (Faz 7.2 student feedback flag mechanism)."""

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import create_engine, text

OUT = Path(__file__).parent / "beta01_flags_RESULT.md"
eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

lines = ["# Beta01 Flag Reports — Karışık Pratik\n"]

# First identify beta01 user_id
with eng.connect() as c:
    user_id = c.execute(
        text("SELECT id FROM users WHERE email='beta01@kiro2.com'")
    ).scalar()
    if not user_id:
        print("beta01 not found")
        OUT.write_text("# beta01 user not found\n", encoding="utf-8")
        sys.exit(1)

lines.append(f"**Beta01 user_id:** `{user_id}`\n")

# Check table existence
with eng.connect() as c:
    tables = c.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name LIKE '%flag%'"
        )
    ).fetchall()
    flag_tables = [t[0] for t in tables]

lines.append(f"**Flag tables in DB:** {flag_tables}\n")

# Query all flags by this user
for table in flag_tables:
    try:
        with eng.connect() as c:
            cols = c.execute(
                text(
                    f"SELECT column_name FROM information_schema.columns "
                    f"WHERE table_name='{table}' ORDER BY ordinal_position"
                )
            ).fetchall()
            col_names = [c[0] for c in cols]
            lines.append(f"\n## Table `{table}`\n")
            lines.append(f"Columns: {col_names}\n")

            # Find user_id column
            uid_col = None
            for c_name in col_names:
                if "user" in c_name.lower() or "student" in c_name.lower():
                    uid_col = c_name
                    break

            if not uid_col:
                lines.append(f"No user_id column found in {table}\n")
                continue

            rows = c.execute(
                text(f"SELECT * FROM {table} WHERE {uid_col}=:uid ORDER BY 1 DESC"),
                {"uid": str(user_id)},
            ).fetchall()
            lines.append(f"**Rows for beta01:** {len(rows)}\n")
            for i, row in enumerate(rows, 1):
                lines.append(f"### Flag #{i}")
                for col_name, val in zip(col_names, row):
                    if isinstance(val, str) and len(val) > 200:
                        val = val[:200] + "..."
                    lines.append(f"- **{col_name}:** {val}")
                lines.append("")
    except Exception as e:
        lines.append(f"Error reading {table}: {e}\n")

# Also check generic feedback tables
for table in ["student_feedback", "question_feedback", "feedback"]:
    try:
        with eng.connect() as c:
            count = c.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            lines.append(f"\n## `{table}` total rows: {count}\n")
            if count > 0 and count < 100:
                cols = c.execute(
                    text(
                        f"SELECT column_name FROM information_schema.columns "
                        f"WHERE table_name='{table}'"
                    )
                ).fetchall()
                col_names = [c[0] for c in cols]
                # Find user column
                uid_col = next(
                    (
                        c
                        for c in col_names
                        if "user" in c.lower() or "student" in c.lower()
                    ),
                    None,
                )
                if uid_col:
                    rows = c.execute(
                        text(f"SELECT * FROM {table} WHERE {uid_col}=:uid"),
                        {"uid": str(user_id)},
                    ).fetchall()
                    lines.append(f"**Rows for beta01:** {len(rows)}\n")
                    for i, row in enumerate(rows, 1):
                        lines.append(f"### {table} #{i}")
                        for col_name, val in zip(col_names, row):
                            if isinstance(val, str) and len(val) > 200:
                                val = val[:200] + "..."
                            lines.append(f"- {col_name}: {val}")
                        lines.append("")
    except Exception:
        pass

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Written: {OUT}")
