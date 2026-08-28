"""Canli DB'de OLMAYAN tablolarin kod tuketicilerini bul.

S206 dersi: ORM modeli olmayan bir tablo da canli 500 uretebilir (Celery ham SQL).
Bu yuzden tuketici taramasi ORM ile sinirli DEGIL -- ham SQL dizeleri de aranir.

Kullanim:
    python backend/scripts/audit_missing_table_consumers.py <tablo1> <tablo2> ...
    python backend/scripts/audit_missing_table_consumers.py --file <liste.txt>
"""

import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

# Sadece CANLI kod yollari. migrations/ ve alembic/ haric -- orada gecmesi
# "kullaniliyor" demek degil, zaten tablonun kaynagi orasi.
SCAN_DIRS = ["api", "services", "models", "core", "tasks", "algorithms", "schemas"]
SKIP_PARTS = {"__pycache__", "_deprecated", "migrations", "alembic", "tests", "scripts"}


def iter_files():
    for d in SCAN_DIRS:
        base = BACKEND / d
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            if SKIP_PARTS & set(p.parts):
                continue
            yield p


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--file":
        tables = [
            ln.split("|")[0].strip()
            for ln in Path(args[1]).read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    else:
        tables = args
    if not tables:
        print("kullanim: audit_missing_table_consumers.py <tablo...> | --file <liste>")
        return 2

    files = list(iter_files())
    texts = [(p, p.read_text(encoding="utf-8", errors="replace")) for p in files]

    print(f"taranan canli kod dosyasi: {len(files)}")
    print()
    print("tablo\torm_model\tham_sql\tdiger_referans\tornek_yerler")

    for t in tables:
        orm_re = re.compile(rf'__tablename__\s*=\s*[\'"]{re.escape(t)}[\'"]')
        # FROM/JOIN/INTO/UPDATE <tablo>  -- ham SQL dizesi icinde
        sql_re = re.compile(
            rf'\b(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+(?:public\.)?"?{re.escape(t)}"?\b',
            re.IGNORECASE,
        )
        word_re = re.compile(rf"\b{re.escape(t)}\b")

        orm_hits: list[str] = []
        sql_hits: list[str] = []
        other_hits: list[str] = []
        for p, text in texts:
            rel = p.relative_to(ROOT).as_posix()
            if orm_re.search(text):
                orm_hits.append(rel)
            if sql_re.search(text):
                sql_hits.append(rel)
            elif word_re.search(text) and not orm_re.search(text):
                other_hits.append(rel)

        sample = ",".join((orm_hits + sql_hits + other_hits)[:3]) or "-"
        print(f"{t}\t{len(orm_hits)}\t{len(sql_hits)}\t{len(other_hits)}\t{sample}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
