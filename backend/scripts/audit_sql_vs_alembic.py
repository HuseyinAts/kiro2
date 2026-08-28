"""backend/migrations/*.sql ile alembic revizyonlarinin yarattigi tablolari karsilastir.

S206'da uc tablo (daily_plans, yks_exam_goals, learning_progress_daily) yalnizca
manuel SQL'de bulundu, hicbir alembic revizyonunda yoktu -> taze DB'de yoklar ->
canli 500. Bu script o sinifin KALANINI olcer.

Kullanim:
    python backend/scripts/audit_sql_vs_alembic.py
"""

import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "backend" / "migrations"
ALEMBIC_DIR = ROOT / "backend" / "alembic" / "versions"
MODELS_DIR = ROOT / "backend" / "models"

# CREATE TABLE [IF NOT EXISTS] [schema.]name  -- tirnakli veya tirnaksiz
CREATE_TABLE_RE = re.compile(
    r"CREATE\s+(?:UNLOGGED\s+|TEMP\s+|TEMPORARY\s+)?TABLE\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?"
    r'(?:"?public"?\.)?"?([a-zA-Z_][a-zA-Z0-9_]*)"?',
    re.IGNORECASE,
)
OP_CREATE_TABLE_RE = re.compile(
    r'op\.create_table\(\s*[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]'
)
TABLENAME_RE = re.compile(r'__tablename__\s*=\s*[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]')


def scan(paths, *patterns) -> dict[str, set[str]]:
    """tablo adi -> onu yaratan dosya adlari"""
    out: dict[str, set[str]] = {}
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pat in patterns:
            for m in pat.finditer(text):
                out.setdefault(m.group(1).lower(), set()).add(p.name)
    return out


def main() -> int:
    sql_files = sorted(SQL_DIR.glob("*.sql"))
    alembic_files = sorted(ALEMBIC_DIR.glob("*.py"))
    model_files = sorted(MODELS_DIR.rglob("*.py"))

    sql_tables = scan(sql_files, CREATE_TABLE_RE)
    # alembic hem op.create_table hem op.execute("CREATE TABLE ...") kullaniyor
    alembic_tables = scan(alembic_files, OP_CREATE_TABLE_RE, CREATE_TABLE_RE)
    orm_tables = scan(model_files, TABLENAME_RE)

    only_sql = sorted(set(sql_tables) - set(alembic_tables))

    print(f"SQL dosyasi        : {len(sql_files)}")
    print(f"Alembic revizyonu  : {len(alembic_files)}")
    print(f"SQL'in yarattigi   : {len(sql_tables)} tablo")
    print(f"Alembic'in         : {len(alembic_tables)} tablo")
    print(f"ORM __tablename__  : {len(orm_tables)} tablo")
    print()
    print(f"=== YALNIZCA MANUEL SQL'DE ({len(only_sql)}) ===")
    print("tablo\tORM_var_mi\tkaynak_sql")
    for t in only_sql:
        orm = "ORM" if t in orm_tables else "-"
        src = ",".join(sorted(sql_tables[t]))
        print(f"{t}\t{orm}\t{src}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
