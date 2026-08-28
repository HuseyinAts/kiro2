"""user_item_fsrs tablosunu AKTIF goc yoluna geri getir (S249 / I2)

Revision ID: 0003_restore_user_item_fsrs
Revises: 0002_is_active_default
Create Date: 2026-08-23

NEDEN BU MIGRATION VAR
----------------------
Tablo canli DB'de YOKTU (`to_regclass` -> None) ve bu IKINCI kayboluşuydu
(#461'de 1 Agu'da bir kez restore edilmisti). Depo kurali (verification.md):
2. kez gorulen sorun patch'lenmez, KOK NEDEN cozulur + enforcement eklenir.

KOK NEDEN (23 Agu 2026'da olculdu, uc katman)
---------------------------------------------
1. `alembic/env.py:84` koruma satiri yoruma alinmis + tablonun ORM modeli yok.
2. DROP: `versions_archive/c555a10f4b93_sync_db_changes.py:419`.
   NOT: uc ayri dokuman bu ankraji `:183` diye veriyor -- FANTOM ankraj;
   `:183` gercekte `khan_user_progress`.
3. **ASIL kalicilik sebebi: squash `e002f550b` (14 Agu 2026).**
   - `versions/0001_baseline_squash.py` govdesini
     `alembic/baseline/0001_baseline_schema.sql`'den okur. O dosya CANLI DB'nin
     `pg_dump --schema-only` ciktisi ve icinde `user_item_fsrs` **0 kez** geciyor
     (243 CREATE TABLE var). Yani YOKLUK kanonik semaya donduruldu.
   - Ayni commit `20260801_restore_user_item_fsrs.py`'yi R100 ile
     `versions/` -> `versions_archive/` tasidi.
   - Tabloya dokunan 6 alembic dosyasinin 6'si da arsivde; `down_revision`
     zincirleri (`mv_safe_for_beta_20260727`, `20260406_create_missing_tables`,
     `gf25_coaching_20260802`) aktif yoldaki **0** dosyada geciyor.
   - Sonuc: `alembic upgrade head` tabloyu BIR DAHA ASLA yaratmazdi.

IKI ARSIV MIGRATION'I BIRLESTIRILDI
-----------------------------------
`20260801_restore_user_item_fsrs.py` OLDUGU GIBI kopyalanmadi. O dosya
`question_id UUID` kuruyor ve `question_bank.id` **character varying** (olculdu,
information_schema). PostgreSQL'de `varchar = uuid` operatoru YOKTUR; bu yuzden
`_FETCH_DUE_SQL` / `_FETCH_DUE_MERCY_SQL` tablonun kuruldugu gunden beri hic
calismadi ve `20260802_fsrs_question_id_varchar.py` bunu sonradan duzeltti.
Burada tip **bastan VARCHAR** kuruluyor -- iki adimli kayma tekrarlanmiyor.

FK NEDEN NOT VALID DEGIL
------------------------
Arsivdeki tip-fix'i `NOT VALID` kullanmisti cunku o an tabloda bir YETIM satir
vardi (`question_id = 000...0`, question_bank'ta karsiligi yok) ve onaylanmamis
veri silinmedi. Burada tablo BOS dogar -> yetim yok -> kisit tam dogrulanabilir.
`question_bank.id` PRIMARY KEY olarak olculdu (information_schema, 3922 satir).

GRANT NEDEN ZORUNLU
-------------------
Uygulama `kiro2_app` non-superuser rolüyle baglaniyor (olculdu: `current_user`).
Bu satir olmadan tablo VAR ama uclar yine 500 verir -- `UndefinedTable` yerine
`InsufficientPrivilege`. Rol yoksa (test/CI) sessizce atlanir.

RLS
---
Tabloda `organization_id` kolonu YOK, dolayisiyla 73-tablo RLS deseni
uygulanamaz. Kapsam disi -- politika ICAT EDILMEDI (27 Tem restore'unun ayni
karari, arsivdeki 20260801 ayni gerekceyi tasiyor).

VERI
----
Tablo BOS gelir. DROP oncesi ~147 satir vardi (13 May 2026 olcumu); o veri icin
yedek YOK, kurtarilamaz.

BEKCI
-----
`backend/tests/db/test_user_item_fsrs_goc_yolunda.py` -- STATIK (DB istemez),
tablonun AKTIF goc yolunda tanimli oldugunu assert eder. Gelecekte bir squash
veya arsiv tasimasi onu yeniden dusurse test kirmiziya doner.
`tests/integration/test_fsrs_schema_contract.py` zaten canliya bakiyordu ve
KIRMIZIYDI -- sorun detektorun yoklugu degil, `integration` marker'i yuzunden
KOSULMAMASIYDI.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_restore_user_item_fsrs"
down_revision: str | None = "0002_is_active_default"
branch_labels: str | None = None
depends_on: str | None = None

_TABLO = "user_item_fsrs"
_INDEKS = "idx_uif_user_due"
_FK = "user_item_fsrs_question_id_fkey"


def upgrade() -> None:
    # Yeni tablo icin op.create_table + sa.Column ZORUNLU (CLAUDE.md Migration
    # Kurallari); ham SQL yalniz index/constraint/grant icin kullaniliyor.
    op.create_table(
        _TABLO,
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("stability", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("difficulty", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "due_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("last_review", sa.DateTime(timezone=True), nullable=True),
        sa.Column("state", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lapses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scheduled_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("elapsed_days", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("user_id", "question_id"),
    )

    op.create_index(_INDEKS, _TABLO, ["user_id", "due_date"])

    op.create_foreign_key(
        _FK,
        _TABLO,
        "question_bank",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # f-string KULLANILMIYOR: ruff S608 (SQL injection vektoru) f-string'li her
    # `op.execute` cagrisini isaretliyor. Burada yalnizca modul sabiti
    # enterpole edilecekti, yani gercek risk yok -- ama tablo adini duz yazmak
    # ayni sonucu uyarisiz veriyor. Kurali susturmak yerine ihtiyaci kaldirdik.
    op.execute("""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kiro2_app') THEN
            GRANT SELECT, INSERT, UPDATE, DELETE ON user_item_fsrs TO kiro2_app;
          END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_constraint(_FK, _TABLO, type_="foreignkey")
    op.drop_index(_INDEKS, table_name=_TABLO)
    op.drop_table(_TABLO)
