"""Alembic zinciri BOŞ bir veritabanını kurabilmeli.

NEDEN VAR (13 Ağu 2026 ölçümü)
------------------------------
`backend/migrations/*.sql` klasörü "temizlenecek legacy borç" sanılıyordu.
Ölçünce tersi çıktı: **şemayı ayakta tutan tek yol o klasör.** Boş bir DB'de

    DATABASE_URL_SYNC=postgresql://...:5434/<bos_db> alembic upgrade head

şu hatayla ölüyor ve geriye **5 tablo** bırakıyor (canlıda 244):

    psycopg2.errors.UndefinedTable: relation "users" does not exist
    [SQL: CREATE TABLE student_goals (... FOREIGN KEY(user_id) REFERENCES users (id))]

Kök neden bir sıralama kusuru DEĞİL — **taban boş**:

    60e185cfcca9_unified_schema.py          (down_revision=None) -> upgrade(): pass
    f822e22c28c6_complete_schema_doc.py                          -> upgrade(): pass

Bu iki revizyon `alembic revision --autogenerate` ile **zaten dolu bir
veritabanına karşı** üretilmiş. Alembic "model ile DB arasında fark yok" görüp
gövdeyi boş yazmış; kimse fark etmemiş çünkü o DB'de tablolar zaten vardı.
Şemayı fiilen `backend/migrations/*.sql` kuruyor — yani o klasör temizlenecek
legacy borç değil, alembic tabanının **eksik parçası**.

Belirti olarak ayrıca: `users`'ı yaratan tek revizyon (`e73a8e0797c1`,
40 tablo) 5 yollu bir mergepoint'in ARDINDA; merge öncesi en az üç revizyon
(`20251117_032216`, `d7a10d07b648`, `3ec73c2c6d97`) `users`'a bel bağlıyor.
Ama sıralamayı düzeltmek yetmez — taban dolmadan yaratacak kimse yok.

Sonuç: taze deploy ve felaket kurtarma alembic ile İMKÂNSIZ. Canlı DB yalnızca
manuel SQL + snapshot restore sayesinde ayakta.

ÇÜRÜTME DENENDİ, DÜŞTÜ: `Base.metadata.create_all` kodda var ama zincirinin
(`DatabaseManager.create_tables()` <- `create_all_tables()`) **hiçbir canlı
çağıranı yok** — yalnızca `tests/unit/test_core_database_coverage.py:582`.
Yani startup otomatik tablo yaratmıyor.

Bu test o boşluğun bekçisi: zincir baştan kurabiliyorsa yeşil, kuramıyorsa
kırmızı. Yeşile döndüğünde `alembic upgrade head` gerçek bir kurulum aracıdır.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]

# Şemanın kurulduğunu söyleyebilmek için gereken minimum. Canlı DB 244 tablo
# taşıyor; eşiği oraya sabitlemek suite büyüdükçe kırılganlık üretir. Asıl
# ölçüm "çöktü mü" — tablo sayısı yalnızca ikinci bir kanıt.
MIN_TABLE_COUNT = 100

# Bu ada sahip olmayan hiçbir veritabanına dokunulmaz (teardown güvenliği).
SCRATCH_DB_NAME = "kiro2_alembic_scratch_test"
_SAFE_DB_NAME = re.compile(r"^kiro2_alembic_scratch_[a-z0-9_]+$")


def _sync_dsn() -> str | None:
    """CREATE DATABASE yetkisi olan gerçek bir psycopg2 DSN'i döndür.

    `DATABASE_URL` bilinçli olarak KULLANILMAZ: `backend/conftest.py:21` onu
    modül seviyesinde sqlite'a eziyor (bkz. `tests/e2e/pg_dsn.py`). Sahte bir
    motorla koşmak, testin ölçtüğünü sandığı şeyi ölçmemesi demektir.
    """
    dsn = os.environ.get("KVKK_VERIFY_DSN") or os.environ.get("DATABASE_URL_SYNC")
    if not dsn:
        return None
    lowered = dsn.lower()
    if "sqlite" in lowered or ":memory:" in lowered:
        return None
    if not lowered.startswith("postgresql"):
        return None
    # asyncpg sürücüsü alembic'te (psycopg2) kullanılamaz.
    return dsn.replace("postgresql+asyncpg://", "postgresql://", 1)


def _swap_database(dsn: str, db_name: str) -> str:
    """DSN'in yol kısmındaki veritabanı adını değiştir."""
    base, _, _ = dsn.rpartition("/")
    return f"{base}/{db_name}"


SKIP_REASON = (
    "Gerçek PostgreSQL yok. KVKK_VERIFY_DSN veya DATABASE_URL_SYNC ile "
    "CREATE DATABASE yetkisi olan bir postgresql:// DSN ver. NOT: DATABASE_URL "
    "tek başına yetmez — conftest onu sqlite'a eziyor."
)


@pytest.fixture
def scratch_db() -> str:
    """Boş bir veritabanı yarat, test sonunda kaldır."""
    psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 kurulu değil")

    dsn = _sync_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)

    assert _SAFE_DB_NAME.match(SCRATCH_DB_NAME), (
        f"Teardown güvenliği: {SCRATCH_DB_NAME!r} scratch adı kalıbına uymuyor. "
        "Bu test asla proje veritabanına dokunamaz."
    )

    admin_dsn = _swap_database(dsn, "postgres")

    def _run(sql: str) -> None:
        conn = psycopg2.connect(admin_dsn)
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql)
        finally:
            conn.close()

    try:
        _run(f'DROP DATABASE IF EXISTS "{SCRATCH_DB_NAME}"')
        _run(f'CREATE DATABASE "{SCRATCH_DB_NAME}"')
    except psycopg2.Error as exc:  # yetki yoksa test anlamsız
        pytest.skip(f"Scratch DB yaratılamadı ({exc.__class__.__name__}): {exc}")

    try:
        yield _swap_database(dsn, SCRATCH_DB_NAME)
    finally:
        _run(f'DROP DATABASE IF EXISTS "{SCRATCH_DB_NAME}"')


def test_alembic_upgrade_head_bos_veritabanini_kurar(scratch_db: str) -> None:
    """`alembic upgrade head` sıfırdan çalışabilir şema üretmeli."""
    psycopg2 = pytest.importorskip("psycopg2")

    env = {**os.environ, "DATABASE_URL_SYNC": scratch_db}
    # conftest'in sqlite ezmesi alt sürece sızmasın.
    env.pop("DATABASE_URL", None)

    result = subprocess.run(
        ["python", "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )

    assert result.returncode == 0, (
        "alembic upgrade head BOŞ veritabanında çöktü — taze deploy ve felaket "
        "kurtarma mümkün değil.\n"
        f"--- son stderr ---\n{result.stderr[-2000:]}"
    )

    conn = psycopg2.connect(scratch_db)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE'"
            )
            table_count = cur.fetchone()[0]
            cur.execute("SELECT to_regclass('public.users') IS NOT NULL")
            users_exists = cur.fetchone()[0]
    finally:
        conn.close()

    assert users_exists, (
        "`users` yok. Onu yaratan e73a8e0797c1 hâlâ kendisine bağımlı "
        "revizyonlardan SONRA koşuyor."
    )
    assert table_count >= MIN_TABLE_COUNT, (
        f"Yalnızca {table_count} tablo kuruldu (beklenen >= {MIN_TABLE_COUNT}). "
        "Zincir erken kesiliyor."
    )
