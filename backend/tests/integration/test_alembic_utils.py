"""`core/alembic_utils.py` -- defensif DDL introspection yardımcıları (30 Ağu 2026).

NEDEN VAR
---------
`core/alembic_utils.py` (idempotent migration yardımcıları: `table_exists`,
`column_exists`, `index_exists`, `constraint_exists`, `safe_create_table`,
`safe_drop_table`, `safe_add_column`, `safe_create_index`, `safe_drop_index`)
SS10.7 backlog grubundan untracked kalmıştı; hiçbir AKTİF migration onu
çağırmıyor (`alembic/versions/` içinde sıfır eşleşme -- yalnızca ARŞİVLENMİŞ
`versions_archive/20260517_student_question_flags.py` onu içe aktarıyordu).
Sıfır güncel çağıran olduğu için hiçbir test yoktu -- ama fonksiyonların
kendisi hâlâ mantıklı, genel amaçlı, canlı Postgres'e karşı doğrudan test
edilebilir.

KAPSAM: yalnızca 4 introspection fonksiyonu (`table_exists`, `column_exists`,
`index_exists`, `constraint_exists`) test ediliyor -- bunlar `bind`
parametresi kabul ediyor. `safe_create_table`/`safe_drop_table`/
`safe_add_column`/`safe_create_index`/`safe_drop_index` KASITLI OLARAK
DIŞARIDA: bunlar kayıtsız şartsız `op.get_bind()` çağırıyor (bkz.
`core/alembic_utils.py:81-114`), yani gerçek bir Alembic
`MigrationContext`/`op` bağlamı gerektiriyor -- bunu test için kurmak (context
stack'e sahte bir `op` push etmek) bu dar backlog-kurtarma PR'ının kapsamının
dışında ve fonksiyonların kendisi zaten sadece introspection sonucuna göre
dallanan tek satırlık sarmalayıcılar (asıl mantık, burada test edilen
fonksiyonlarda).

SENKRON MOTOR GEREKLİ: `get_inspector()` `sqlalchemy.inspect()` kullanıyor --
bu SENKRON reflection API'si, bir `AsyncConnection` ile çağrılamaz. Bu yüzden
bu dosya `canli_dsn_cozumle()`'nin verdiği asyncpg DSN'ini `alembic/env.py`
ile AYNI dönüşümle (`+asyncpg` -> `+psycopg`) senkron motora çeviriyor.

Kullanılan tablo/kolon/index/constraint adları 30 Ağu 2026'da canlı DB'ye
karşı ölçüldü (`information_schema.columns`, `pg_indexes`, `pg_constraint`)
-- varsayım değil.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from core.alembic_utils import (
    column_exists,
    constraint_exists,
    index_exists,
    table_exists,
)
from tests.integration.conftest import canli_dsn_cozumle

pytestmark = [pytest.mark.integration]


@pytest.fixture
def sync_conn():
    dsn = canli_dsn_cozumle()
    if not dsn:
        pytest.skip(
            "Canli DSN cozulemedi -- alembic_utils introspection'i test edilemez"
        )

    sync_dsn = dsn.replace("+asyncpg", "+psycopg")
    engine = create_engine(sync_dsn)
    try:
        with engine.connect() as conn:
            yield conn
    finally:
        engine.dispose()


def test_table_exists_gercek_tablo(sync_conn) -> None:
    assert table_exists("users", bind=sync_conn) is True


def test_table_exists_olmayan_tablo(sync_conn) -> None:
    assert table_exists("bu_tablo_hic_yok_kiro2_test", bind=sync_conn) is False


def test_column_exists_gercek_kolon(sync_conn) -> None:
    assert column_exists("users", "email", bind=sync_conn) is True


def test_column_exists_olmayan_kolon(sync_conn) -> None:
    assert column_exists("users", "bu_kolon_hic_yok", bind=sync_conn) is False


def test_column_exists_olmayan_tabloda_false_doner(sync_conn) -> None:
    """Tablo yoksa kolon kontrolü de sessizce False donmeli (exception degil)."""
    assert (
        column_exists("bu_tablo_hic_yok_kiro2_test", "email", bind=sync_conn) is False
    )


def test_index_exists_gercek_index(sync_conn) -> None:
    assert index_exists("users", "idx_user_email", bind=sync_conn) is True


def test_index_exists_olmayan_index(sync_conn) -> None:
    assert index_exists("users", "bu_index_hic_yok", bind=sync_conn) is False


def test_constraint_exists_gercek_fk(sync_conn) -> None:
    """`student_profiles.user_id` -> `users.id` FK'si (30 Agu 2026 olculdu)."""
    assert (
        constraint_exists(
            "student_profiles", "student_profiles_user_id_fkey", bind=sync_conn
        )
        is True
    )


def test_constraint_exists_olmayan_constraint(sync_conn) -> None:
    assert constraint_exists("users", "bu_constraint_hic_yok", bind=sync_conn) is False
