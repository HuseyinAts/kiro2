"""ORM __tablename__ ile CANLI DB'yi karsilastir (S206 hayalet-tablo sinifi).

S206: daily_plans / yks_exam_goals / learning_progress_daily -- kod bekliyordu,
hicbir migration yaratmiyordu, DB'de yoktu -> canli 500 + kalici Celery fail.
Bu script o hatanin KALANINI olcer: "kod bekliyor ama DB'de yok".

Yon onemli: migration'in NEREDE oldugu (alembic mi manuel SQL mi) ikincil.
Birincil olcum "ORM bekliyor mu" + "DB'de var mi".

Kullanim:
    python backend/scripts/audit_orm_vs_livedb.py            # canli DB'ye baglanir
"""

import os
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "backend" / "models"
DSN = os.getenv("KIRO2_DSN", "postgresql://postgres@localhost:5434/kiro2")

TABLENAME_RE = re.compile(r'__tablename__\s*=\s*[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]')
# Kendi Base'ini kuran dosya ortak metadata'da DEGIL -> create_all/migration disi
OWN_BASE_RE = re.compile(r"^\s*Base\s*=\s*declarative_base\(\)", re.MULTILINE)
ABSTRACT_RE = re.compile(r"__abstract__\s*=\s*True")


def orm_tables() -> dict[str, tuple[str, bool]]:
    """tablo -> (dosya, kendi_base_mi)"""
    out: dict[str, tuple[str, bool]] = {}
    for p in sorted(MODELS_DIR.rglob("*.py")):
        if "__pycache__" in p.parts or "_deprecated" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if ABSTRACT_RE.search(text) and not TABLENAME_RE.search(text):
            continue
        own_base = bool(OWN_BASE_RE.search(text))
        for m in TABLENAME_RE.finditer(text):
            out.setdefault(
                m.group(1).lower(), (p.relative_to(ROOT).as_posix(), own_base)
            )
    return out


def live_relations() -> set[str]:
    """Tablo + view + matview -- ORM bir view'a da map edilebilir."""
    sql = (
        "select relname from pg_class "
        "where relkind in ('r','v','m','p','f') "
        "and relnamespace='public'::regnamespace;"
    )
    try:
        import psycopg2
    except ImportError:
        print(
            "[HATA] psycopg2 kurulu degil: pip install psycopg2-binary", file=sys.stderr
        )
        raise SystemExit(1) from None

    try:
        conn = psycopg2.connect(DSN)
    except psycopg2.Error as exc:
        print(f"[HATA] DB baglantisi: {exc}", file=sys.stderr)
        raise SystemExit(1) from None

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return {row[0].strip().lower() for row in cur.fetchall() if row[0]}
    finally:
        conn.close()


def main() -> int:
    orm = orm_tables()
    live = live_relations()
    missing = sorted(set(orm) - live)

    print(f"ORM __tablename__ : {len(orm)}")
    print(f"Canli iliski      : {len(live)} (tablo+view+matview)")
    print(f"KOD BEKLIYOR/DB'DE YOK: {len(missing)}")
    print()
    print("tablo\tkendi_base\tmodel_dosyasi")
    for t in missing:
        src, own = orm[t]
        print(f"{t}\t{'IZOLE' if own else 'ORTAK'}\t{src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
