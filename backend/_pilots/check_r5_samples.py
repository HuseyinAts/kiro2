#!/usr/bin/env python3
"""Quick: R5a/R5b sample inspection — write to file (stdout intercepted on Windows)."""

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUT = PROJECT_ROOT / "backend" / "_pilots" / "bug_5_sample_RESULT.md"

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

lines = []
lines.append("# Bug #5 R5a + R5b sample inspection\n")

for rule, pred in [
    ("R5a (repeated_char 7+)", "question_text ~ '(.)\\1{6,}'"),
    ("R5b (ends_with_ellipsis)", "question_text ~ '\\.\\.\\.\\s*$'"),
]:
    lines.append(f"## {rule}\n")
    lines.append("| id | source_book | preview |\n|---|---|---|")
    sql = f"""
        SELECT id::text, source_book, LEFT(question_text, 200) AS preview
        FROM question_bank
        WHERE is_active=true AND quality_review_status='auto_judged_high'
          AND {pred}
        ORDER BY md5(id::text)
        LIMIT 8
    """
    with eng.connect() as c:
        for row in c.execute(text(sql)).fetchall():
            pid, book, preview = row
            preview_clean = (preview or "").replace("\n", " ").replace("|", "\\|")[:180]
            book_clean = (book or "")[:40]
            lines.append(f"| `{pid[:8]}` | {book_clean} | {preview_clean} |")
    lines.append("")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Written: {OUT}")
