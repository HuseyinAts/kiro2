"""Koçluk modülü ORM<->DB zaman sözleşmesini onar (gf25)

Revision ID: gf25_coaching_20260802
Revises: gfk2_diary_20260801
Create Date: 2026-08-02

NEDEN
-----
`POST /api/v1/coaching/signals` canlida 500 veriyordu:

    asyncpg.exceptions.NotNullViolationError: null value in column
    "recorded_at" of relation "student_engagement_signals"

`models/coaching.py:76` `recorded_at`'i `server_default=func.now()` diye
bildiriyor. Bu bildirim SQLAlchemy'ye "kolonu INSERT'e KOYMA, DB doldurur"
der; uretilen SQL gercekten de soyleydi:

    INSERT INTO student_engagement_signals (id, student_id, signal_type, value)
    VALUES (...) RETURNING organization_id, recorded_at

Canli kolonda ise DEFAULT **yoktu** ve NOT NULL'du -> ORM uzerinden yapilan
HER insert dustu.

KOKENI (ankraj)
---------------
`20260312_create_mega_feature_tables.py:234` tabloyu DOGRU kuruyordu
(`sa.DateTime(timezone=True), server_default=sa.func.now()`), ama ayni
dosyadaki `_table_exists()` kapisi tablo zaten varsa `create_table`'i atlar.
Ardindan `c555a10f4b93_sync_db_changes.py:1432-1435`:

    op.execute("UPDATE ... SET recorded_at = NOW() WHERE recorded_at IS NULL")
    op.alter_column('student_engagement_signals', 'recorded_at',
               existing_type=postgresql.TIMESTAMP(),   # <-- tz'siz
               nullable=False)                          # <-- DEFAULT eklemeden

`existing_type=postgresql.TIMESTAMP()` satiri kaymanin ikinci yarisini da
belgeliyor: autogenerate canli kolonu **naive** goruyordu, ORM ise tz-aware
bildiriyordu, ve fark "duzeltilecek kayma" degil "mevcut durum" diye yazildi.
Ayni migration GF-K1'deki 145 `DROP TABLE`'i da tasiyor — bu, o autogenerate
korlugunun kolon-duzeyi yuzu.

KACAN KARDES (bu turda olculdu)
-------------------------------
`coaching_events` ayni tz kaymasini tasiyor: `created_at` `shown_at`
`clicked_at` `dismissed_at` dordu de ORM'de `DateTime(timezone=True)`,
canlida `timestamp without time zone`. `created_at`'in DEFAULT'u VAR
(`now()`), bu yuzden gorunur bir 500 uretmiyordu — sessiz kalan kayma.
S202 karari geregi tablo/kolon isi **modul butunu** olarak yapilir.

TZ KAYMASI NEDEN ONEMLI (yalniz kozmetik degil)
-----------------------------------------------
`services/proactive_coaching_service.py:147,158` tukenmislik sinyalini
`recorded_at >= datetime.now(UTC) - 7 gun` ile ariyor — **aware** bir deger.
Naive kolona aware parametre asyncpg'de duser; blok :185'te
`except Exception: logger.debug(...)` ile YUTULUYOR. Yani tukenmislik
tespiti sessizce her zaman "risk yok" donebiliyordu.

VERI
----
student_engagement_signals: 28 satir · coaching_events: 102 satir (2 Agu olcumu).
Mevcut naive degerler UTC kabul edilir (`AT TIME ZONE 'UTC'`): iki yazar da
UTC uretiyordu — SQL tarafi `NOW()` (sunucu TZ'si UTC), uygulama tarafi
`datetime.now(UTC)`.

DOGRULAMA
---------
backend/tests/integration/test_coaching_schema_contract.py — modul butunu
sinif bekcisi (ORM `server_default` -> DB DEFAULT var mi; ORM tz-aware ->
DB timestamptz mi) + iki alet-dogrulama kolu.
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "gf25_coaching_20260802"
down_revision = "gfk2_diary_20260801"
branch_labels = None
depends_on = None


# (tablo, kolon) — ORM'de DateTime(timezone=True) bildirilen her kolon.
_TZ_KOLONLARI: tuple[tuple[str, str], ...] = (
    ("student_engagement_signals", "recorded_at"),
    ("coaching_events", "created_at"),
    ("coaching_events", "shown_at"),
    ("coaching_events", "clicked_at"),
    ("coaching_events", "dismissed_at"),
)


def upgrade() -> None:
    for tablo, kolon in _TZ_KOLONLARI:
        op.execute(
            f"ALTER TABLE {tablo} "
            f"ALTER COLUMN {kolon} TYPE timestamp with time zone "
            f"USING {kolon} AT TIME ZONE 'UTC'"
        )

    # Asil gf25 kusuru: ORM 'DB doldurur' diyor ama DB dolduramiyordu.
    op.execute(
        "ALTER TABLE student_engagement_signals "
        "ALTER COLUMN recorded_at SET DEFAULT now()"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE student_engagement_signals ALTER COLUMN recorded_at DROP DEFAULT"
    )

    for tablo, kolon in _TZ_KOLONLARI:
        op.execute(
            f"ALTER TABLE {tablo} "
            f"ALTER COLUMN {kolon} TYPE timestamp without time zone "
            f"USING {kolon} AT TIME ZONE 'UTC'"
        )
