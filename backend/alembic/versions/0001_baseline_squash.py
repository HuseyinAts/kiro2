"""baseline_squash: tum semayi tek revizyonda kur

Revision ID: 0001_baseline
Revises:
Create Date: 2026-08-14

NEDEN VAR (13-14 Agu 2026 olcumu)
---------------------------------
Onceki 117 revizyonluk zincir **iki yonden de kosulamiyordu**:

  bos DB'de   -> `alembic upgrade head` 6. revizyonda oldu, 5 tablo birakti
                 (20251117_032216: student_goals FK -> users, users YOK)
  dolu DB'de  -> 1. revizyonda oldu
                 (kvkk_compliance_001: DuplicateTable kvkk_consents)

Kok neden: taban bostu. `60e185cfcca9_unified_schema` (down_revision=None) ve
`f822e22c28c6` ikisi de `upgrade(): pass` idi -- `--autogenerate` ZATEN DOLU bir
veritabanina karsi kosturulmus, alembic "fark yok" gorup bos yazmisti. Semayi
fiilen `backend/migrations/*.sql` kuruyordu; alembic bir kurulum araci degil,
patch aracina donusmustu.

Iki onarim tasarimi da olcumle elendi:
  (i)  `migrations/001-009*.sql` porte et -> o dosyalar bayat. 001'in
       `users.id UUID`'i canliya uymuyor (canli: character varying) ve cöken
       FK'yi baska bir hatayla dusuruyor:
       "incompatible types: character varying and uuid"
  (ii) pg_dump tabani + mevcut zincir -> revizyonlar tutarsiz idempotent.
       `d7a10d07b648` savunmaci (column_exists), `kvkk_compliance_001` degil.

Kalan tek yol squash: bu revizyon canli semanin tamami. Eski 117 revizyon
`backend/alembic/versions_archive/` altina tasindi (silinmedi, git'te de duruyor).

BEDELI: eski surumlere `alembic downgrade` ile inilemez. Pratikte zaten
inilemiyordu -- zincir kosmuyordu.

SEMANIN KAYNAGI
---------------
`backend/alembic/baseline/0001_baseline_schema.sql`, su komutla uretildi:

    pg_dump --schema-only --no-owner --no-privileges \\
            --exclude-table=public.alembic_version \\
            -d postgresql://<host>:5434/kiro2

sonra iki duzeltme (`backend/scripts/generate_alembic_baseline.py`):
  - psql meta-komutlari (\\restrict / \\unrestrict, PG17+) cikarildi;
    SQLAlchemy bunlari calistiramaz.
  - sonuna search_path geri yukleme eklendi; pg_dump onu '' yapiyor ve alembic
    sonrasinda `alembic_version`'a niteliksiz erisiyor.
  - `alembic_version` dump DISINDA birakildi: alembic o tabloyu migration'dan
    ONCE kendisi yaratir, dump'taki CREATE onunla cakisirdi.

Icerik: 243 tablo, 637 index, 79 RLS policy + 79 ENABLE ROW LEVEL SECURITY.

Bekcisi: `backend/tests/db/test_alembic_from_scratch.py`
"""

from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None

BASELINE_SQL = (
    Path(__file__).resolve().parents[1] / "baseline" / "0001_baseline_schema.sql"
)

# Semanin kuruldugunu anlamak icin sondaj tablosu. `users` secildi cunku eski
# zincirin coktugu yer tam olarak onun yoklugu idi.
_PROBE_TABLE = "users"


def upgrade() -> None:
    conn = op.get_bind()

    already = conn.execute(
        sa.text("SELECT to_regclass('public.' || :t) IS NOT NULL"),
        {"t": _PROBE_TABLE},
    ).scalar()
    if already:
        # Dolu bir veritabaninda kosuldu (ornegin biri stamp'lemeyi atladi).
        # Baseline'i tekrar uygulamak DuplicateTable verirdi; atlamak dogru
        # davranis -- sema zaten burada.
        print(
            f"[0001_baseline] '{_PROBE_TABLE}' zaten var -> baseline ATLANDI. "
            "Mevcut veritabanlari `alembic stamp 0001_baseline` ile isaretlenir."
        )
        return

    if not BASELINE_SQL.is_file():
        raise RuntimeError(f"baseline SQL bulunamadi: {BASELINE_SQL}")

    conn.exec_driver_sql(BASELINE_SQL.read_text(encoding="utf-8"))


def downgrade() -> None:
    raise NotImplementedError(
        "0001_baseline bir squash tabanidir; asagi inilemez. "
        "Geri donmek icin veritabanini yedekten geri yukleyin."
    )
