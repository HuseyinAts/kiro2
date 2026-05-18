import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)
with eng.connect() as c:
    r = c.execute(
        text(
            "SELECT id::text, quality_review_status, LEFT(question_text,80), "
            "  question_text ~ '^Bu fabrika' AS m1"
            " FROM question_bank WHERE id::text='c3256134-d74e-575c-ba7e-892d886b09c7'"
        )
    ).fetchone()
    print(r)
