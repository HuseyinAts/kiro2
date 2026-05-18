import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)
OUT = Path(__file__).parent / "check_2q_RESULT.md"

ids = ["92a19fd1-e255-5902-a816-f0e1fb13c3c8", "3742a515-ea3d-5ad6-baf2-9ff865e32fc4"]
lines = ["# 2 Question Status\n"]

with eng.connect() as c:
    for qid in ids:
        row = c.execute(
            text(
                "SELECT id::text, quality_review_status, LEFT(question_text,150) as qt, "
                "  question_text ~* 'şekil' AS matches_sekil "
                "FROM question_bank WHERE id::text=:qid"
            ),
            {"qid": qid},
        ).fetchone()
        if row:
            lines.append(f"\n## `{qid[:8]}`")
            lines.append(f"- status: {row.quality_review_status}")
            lines.append(f"- matches `şekil` regex: {row.matches_sekil}")
            lines.append(f"- text: {row.qt}")
        else:
            lines.append(f"\n## `{qid[:8]}` NOT FOUND")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Written: {OUT}")
