"""backend/migrations/*.sql <-> alembic <-> canli DB uc yonlu drift olcumu.

Gerekce (13 Agu 2026, S206): `daily_plans` / `yks_exam_goals` /
`learning_progress_daily` tablolari SADECE backend/migrations/*.sql icinde
tanimliydi, hicbir alembic surumunde yoktu ve canli DB'de de yoktu.
Canli Celery beat + 2 API ucu bu yuzden kalici 500 veriyordu (cdea871deea9
ile kapandi). Bu script o hatanin KARDESLERINI arar.

Cikti: her tablo icin (sql_var, alembic_var, db_var) uclusu.
KRITIK sinif = sql_var AND NOT db_var  -> kod bagimliysa canli 500 riski.

Salt-okunur. Hicbir DDL calistirmaz.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

REPO = Path(__file__).resolve().parents[2]
SQL_DIR = REPO / "backend" / "migrations"
ALEMBIC_DIR = REPO / "backend" / "alembic" / "versions"

# "CREATE TABLE [IF NOT EXISTS] [schema.]name" -- tirnakli/tirnaksiz
CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"']?(?:(\w+)\.)?[\"']?(\w+)[\"']?",
    re.IGNORECASE,
)
# alembic: op.create_table("name", ...)
OP_CREATE_RE = re.compile(r"""op\.create_table\(\s*["'](\w+)["']""")


def _dsn() -> str:
    """DSN'i ortamdan veya backend/.env'den al. ASLA yazdirma."""
    for key in ("DATABASE_URL", "KVKK_VERIFY_DSN", "POSTGRES_DSN"):
        if os.environ.get(key):
            return os.environ[key]
    env = REPO / "backend" / ".env"
    if not env.exists():
        env = REPO / ".env"
    if env.exists():
        for ham in env.read_text(encoding="utf-8", errors="replace").splitlines():
            satir = ham.strip()
            if satir.startswith("DATABASE_URL="):
                return satir.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("DSN bulunamadi (DATABASE_URL / backend/.env)")


def _psycopg_dsn(url: str) -> str:
    """SQLAlchemy surucu ekini soy: postgresql+asyncpg:// -> postgresql://"""
    return re.sub(r"^postgresql\+\w+://", "postgresql://", url)


def tables_from_sql() -> dict[str, set[str]]:
    """tablo -> onu tanimlayan .sql dosyalarinin adlari."""
    out: dict[str, set[str]] = {}
    for f in sorted(SQL_DIR.glob("*.sql")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for schema, name in CREATE_TABLE_RE.findall(text):
            if schema and schema.lower() != "public":
                continue
            out.setdefault(name.lower(), set()).add(f.name)
    return out


def tables_from_alembic() -> set[str]:
    out: set[str] = set()
    for f in sorted(ALEMBIC_DIR.glob("*.py")):
        text = f.read_text(encoding="utf-8", errors="replace")
        out.update(n.lower() for n in OP_CREATE_RE.findall(text))
        # op.execute("CREATE TABLE ...") ham SQL yolu da sayilir
        for schema, name in CREATE_TABLE_RE.findall(text):
            if schema and schema.lower() != "public":
                continue
            out.add(name.lower())
    return out


def tables_from_db() -> set[str]:
    import psycopg2

    conn = psycopg2.connect(_psycopg_dsn(_dsn()))
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
            return {r[0].lower() for r in cur.fetchall()}
    finally:
        conn.close()


TABLENAME_RE = "__tablename__\\s*=\\s*[\"']{t}[\"']"
RAWSQL_RE = "(?:FROM|INTO|UPDATE|JOIN)\\s+{t}\\b"

# Canli uygulama yolu: buradaki bir referans = canli 500 riski.
LIVE_DIRS = ("api", "services", "models", "core", "tasks", "algorithms")


_CORPUS: list[tuple[str, str]] = []


def _corpus() -> list[tuple[str, str]]:
    """Canli uygulama .py dosyalarini bir kez oku (yol, icerik)."""
    if not _CORPUS:
        for d in LIVE_DIRS:
            for f in (REPO / "backend" / d).rglob("*.py"):
                _CORPUS.append(
                    (
                        str(f.relative_to(REPO)).replace("\\", "/"),
                        f.read_text(encoding="utf-8", errors="replace"),
                    )
                )
    return _CORPUS


def scan_usage(table: str) -> dict[str, list[str]]:
    """Tablonun ORM modeli / ham SQL referansi var mi? Salt-okunur."""
    orm_re = re.compile(TABLENAME_RE.format(t=re.escape(table)))
    sql_re = re.compile(RAWSQL_RE.format(t=re.escape(table)), re.IGNORECASE)
    hits: dict[str, list[str]] = {"orm": [], "sql": []}
    for path, text in _corpus():
        if orm_re.search(text):
            hits["orm"].append(path)
        elif sql_re.search(text):
            hits["sql"].append(path)
    return hits


def main() -> int:
    sql = tables_from_sql()
    alembic = tables_from_alembic()
    try:
        db = tables_from_db()
        db_ok = True
    except Exception as exc:
        print(f"[UYARI] DB'ye baglanilamadi: {type(exc).__name__}: {exc}")
        db, db_ok = set(), False

    print(f"backend/migrations/*.sql  : {len(sql)} farkli tablo")
    print(f"alembic/versions/*.py     : {len(alembic)} farkli tablo")
    print(f"canli DB (public)         : {len(db) if db_ok else 'OLCULEMEDI'}")
    print()

    if not db_ok:
        return 2

    # KONTROL KOLU: bilinen-canli tablo bol referans vermeli; 0 ise tarayici arizali.
    ctrl = scan_usage("users")
    if len(ctrl["orm"]) + len(ctrl["sql"]) == 0:
        print(
            "[HATA] Kontrol kolu ('users') 0 dondu -> tarayici arizali, bulgular GECERSIZ."
        )
        return 3
    print(
        f"[kontrol kolu] 'users': orm={len(ctrl['orm'])} dosya, "
        f"sql={len(ctrl['sql'])} dosya -> tarayici saglam\n"
    )

    # ASIL SINIF: .sql'de var, canli DB'de YOK
    missing = sorted(t for t in sql if t not in db)
    print(f"=== .sql'de TANIMLI ama canli DB'de YOK: {len(missing)} ===")
    load_bearing: list[tuple[str, dict[str, list[str]]]] = []
    for t in missing:
        flag = (
            "alembic'te de YOK"
            if t not in alembic
            else "alembic'te VAR (uygulanmamis?)"
        )
        u = scan_usage(t)
        if u["orm"] or u["sql"]:
            load_bearing.append((t, u))
            print(f"  {t:<38} [{flag}]  !! KOD BAGIMLI")
        else:
            print(f"  {t:<38} [{flag}]  (referanssiz)")

    print()
    print(f"=== CANLI 500 RISKI: kod bagimli + DB'de YOK -> {len(load_bearing)} ===")
    for t, u in load_bearing:
        print(f"\n  {t}")
        for f in u["orm"]:
            print(f"      ORM  {f}")
        for f in u["sql"][:6]:
            print(f"      SQL  {f}")

    print()
    orphan = sorted(t for t in sql if t not in alembic and t in db)
    print(f"=== .sql'de var, DB'de var, alembic'te YOK (izlenmeyen): {len(orphan)} ===")
    for t in orphan:
        print(f"  {t}")

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
