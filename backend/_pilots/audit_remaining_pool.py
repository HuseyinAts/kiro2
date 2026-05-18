#!/usr/bin/env python3
"""
Random sample audit of v_safe_for_beta pool — visual-bound detection.
Goal: 'görseli eksik soru hiç kalmayana kadar' — find remaining patterns.
"""

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from sqlalchemy import create_engine, text

OUT = Path(__file__).parent / "audit_remaining_pool_RESULT.md"
eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

with eng.connect() as c:
    total = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()
    # 30 random sample — true random for re-audit iteration
    rows = c.execute(
        text(
            "SELECT id::text, subject_area, source_book, "
            "  LEFT(question_text, 350) AS qt, "
            "  LEFT(COALESCE(option_a,''), 60) AS a, "
            "  LEFT(COALESCE(option_b,''), 60) AS b "
            "FROM v_safe_for_beta "
            "ORDER BY RANDOM() LIMIT 30"
        )
    ).fetchall()

lines = [f"# v_safe_for_beta Audit — {len(rows)}/{total:,}\n"]
for r in rows:
    qt = (r.qt or "").replace("\n", " ")
    lines.append(f"\n## `{r.id[:8]}` [{r.subject_area}]")
    lines.append(f"- Book: {r.source_book[:50] if r.source_book else 'N/A'}")
    lines.append(f"- Text: {qt}")
    lines.append(f"- A: {r.a}  |  B: {r.b}")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Written: {OUT}")
print(f"Pool: {total:,}, Sampled: {len(rows)}")
