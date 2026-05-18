import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)
tests = [
    ("LOWER('Ş')", "SELECT LOWER('Ş')"),
    ("'Şekilde' ~* 'şekil'", "SELECT 'Şekilde' ~* 'şekil'"),
    ("'Şekilde' ILIKE '%şekil%'", "SELECT 'Şekilde' ILIKE '%şekil%'"),
    ("LOWER('Şekilde') ~ 'şekil'", "SELECT LOWER('Şekilde') ~ 'şekil'"),
    ("'Şekilde' ~* '[şŞ]ekil'", "SELECT 'Şekilde' ~* '[şŞ]ekil'"),
    ("Database locale", "SHOW lc_collate"),
]
with eng.connect() as c:
    for label, sql in tests:
        try:
            r = c.execute(text(sql)).scalar()
            print(f"  {label}: {r}")
        except Exception as e:
            print(f"  {label}: ERR {e}")
