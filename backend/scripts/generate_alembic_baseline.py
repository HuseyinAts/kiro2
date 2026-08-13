"""pg_dump ciktisini alembic baseline revizyonunun calistirabilecegi hale getir.

Tek seferlik yardimci (squash icin). Kaldirilan seyler:
  - psql meta-komutlari (PG17+ pg_dump: \\restrict / \\unrestrict) -- SQLAlchemy
    bunlari calistiramaz, sozdizimi hatasi verir.
Eklenen:
  - search_path geri yukleme; pg_dump onu '' yapiyor ve alembic sonrasinda
    alembic_version'a niteliksiz erisiyor.
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

BACKSLASH = chr(92)
META_PREFIXES = (BACKSLASH + "restrict", BACKSLASH + "unrestrict")

src = Path("backend/backups/schema_kiro2_20260813_baseline_src.sql")
dst = Path("backend/alembic/baseline/0001_baseline_schema.sql")

lines = src.read_text(encoding="utf-8").splitlines()
out: list[str] = []
dropped: list[str] = []
for ln in lines:
    if ln.startswith(META_PREFIXES):
        dropped.append(ln.split()[0])
        continue
    out.append(ln)

out += [
    "",
    "-- baseline sonrasi: alembic kendi oturumunda alembic_version'a niteliksiz",
    "-- erisiyor; pg_dump'in bosalttigi search_path'i geri ver.",
    "SELECT pg_catalog.set_config('search_path', 'public', false);",
]

dst.write_text("\n".join(out) + "\n", encoding="utf-8")

print(f"kaynak satir : {len(lines)}")
print(f"cikarilan    : {dropped}")
print(f"yazilan satir: {len(out)}")
print(f"CREATE TABLE : {sum(1 for x in out if x.startswith('CREATE TABLE'))}")
print(f"CREATE POLICY: {sum(1 for x in out if x.startswith('CREATE POLICY'))}")
print(f"ENABLE RLS   : {sum(1 for x in out if 'ENABLE ROW LEVEL SECURITY' in x)}")
_INDEX_PREFIXES = ("CREATE INDEX", "CREATE UNIQUE INDEX")
print(f"CREATE INDEX : {sum(1 for x in out if x.startswith(_INDEX_PREFIXES))}")
print(f"hedef        : {dst} ({dst.stat().st_size} bayt)")
