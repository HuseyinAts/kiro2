"""question_bank.is_active: DDL varsayilanini gercek yap

Revision ID: 0002_is_active_default
Revises: 0001_baseline
Create Date: 2026-08-18

NEDEN VAR (18 Agu 2026 olcumu, S229 / #485)
-------------------------------------------
`models/question_bank.py` yillardir `server_default="true"` beyan ediyordu, ama
canli DB'de o varsayilan HIC YOKTU. Olculdu:

    SELECT column_default FROM information_schema.columns
     WHERE table_name='question_bank' AND column_name='is_active';
    -> NULL

Yani beyan **fantomdu**: `server_default` yalnizca DDL uretilirken (create_all
veya migration) kullanilir; tablo onu icermeyen bir yoldan olusmus. Davranis
uzerinden de dogrulandi -- kolonu atlayan ham INSERT patliyordu:

    NotNullViolationError: null value in column "is_active"
                           of relation "question_bank"

Bu, ORM'i atlayan her yazma yolunu (ham SQL, COPY, disaridan arac) kiriyordu.
Kardes fix ORM tarafinda: `default=False` -> `default=True` (Python-side default
INSERT'e kolonu dahil ettigi icin server_default'u zaten hic atesLetmiyordu).

NE DEGISMIYOR
-------------
Mevcut 36.967 satirin hicbiri etkilenmez: `SET DEFAULT` yalnizca BUNDAN SONRAKI
INSERT'lere uygulanir, mevcut satirlari yeniden yazmaz. Olcum: fix oncesi
`is_active` dagilimi 36.967/36.967 = true, yani geri doldurulacak satir da yok.

`op.execute` kullanimi Migration Kurallari'na uygun: yeni tablo DEGIL, mevcut
kolon uzerinde ALTER. Dogrulama information_schema ile ZORUNLU ve testle civili:
`tests/integration/test_question_bank_defaults.py::test_ddl_server_default_exists`
"""

from alembic import op

revision: str = "0002_is_active_default"
down_revision: str | None = "0001_baseline"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE question_bank ALTER COLUMN is_active SET DEFAULT true")


def downgrade() -> None:
    # Geri alim varsayilani KALDIRIR (baslangic hali: varsayilan yok).
    # NOT NULL kisiti yerinde kaldigi icin, geri alim sonrasi kolonu atlayan
    # INSERT'ler yeniden NotNullViolation alir — bu bilincli: down() tam olarak
    # onceki (kusurlu) hale dondurur, daha iyisine degil.
    op.execute("ALTER TABLE question_bank ALTER COLUMN is_active DROP DEFAULT")
