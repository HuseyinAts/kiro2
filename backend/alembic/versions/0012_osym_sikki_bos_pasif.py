"""OSYM sik_bos bayrakli 28 soruyu pasife al (0011'in kapsam hatasini duzeltir)

Revision ID: 0012_osym_sikki_bos_pasif
Revises: 0011_osym_aktiflestirme
Create Date: 2026-09-10

BAGLAM
------
0011 + D9, 291 OSYM sorusunun tumunu tek imzayla (osym_resmi_kaynak) kapidan
gecirdi. Push oncesi ders-zorlayici hook'u (test_icerik_gecerliligi.py::
test_k2_anahtar_dolu_bir_sikka_isaret_ediyor) 28 satirin cevap anahtarinin
GECERSIZ (dogru sikkin metni BOS) oldugunu buldu. Teshis (backend/_ci_art/
_r5_teshis.py, _bayrak_analiz.py): 28/28 satir kitapcik_ithal.py'nin ITHALAT
ANINDA kendi koydugu pipeline_metadata->'bayraklar' isaretinde 'sik_bos'
tasiyor -- dogru sik bir GORSEL/GRAFIK, metin degil. Birebir ortusme: havuzun
geri kalaninda (5250-28) SIFIR R5 hatasi var.

D10 (backend/migrations/D10_safe_for_beta_exclude_sik_bos.sql) kapiya bu
bayragi tasiyan satirlari geneli disari atan bir kural ekledi -- kapi zaten
bu 28'i disliyor. Bu migration ONA EK OLARAK is_active'i de false'a
cevirir: kapi tek basina yeterli olsa da, is_active=true birakmak DB'yi
DOGRUDAN okuyan baska araclara (admin panel, ileride yazilacak bir migration,
API disi raporlama) "bu soru servis icin hazir" gibi yanlis bilgi verir.
review_status'a DOKUNULMUYOR ('approved' kalir) -- cevap HARFININ dogrulugu
hala resmi kaynaktan dogrulanmis durumda, sorun harfin dogrulugu degil
sikkin metninin eksikligi (gorsel/grafik icerik icin metin sunumu yok).

Bu 28 soru gorsel sik destegi eklendiginde (ayri, daha buyuk bir urun/UI
isi) yeniden aktif hale getirilebilir -- bkz downgrade() ve D10_ROLLBACK.sql.

GUNLUK: sikki_bos_gunlugu_0012(id, alan, eski_deger). downgrade() is_active'i
eski degerine (TRUE) dondurur -- ANCAK D10'un kapi kurali ayri bir dosyada
oldugu icin, D10_ROLLBACK.sql elle calistirilmadan bu sorular kapidan yine
GECMEZ (bilerek boyle -- iki dosya bagimsiz, downgrade sirasi: once bu
dosyanin downgrade()'i, sonra istenirse D10_ROLLBACK.sql).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0012_osym_sikki_bos_pasif"
down_revision: Union[str, None] = "0011_osym_aktiflestirme"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "sikki_bos_gunlugu_0012"
_KAYNAKLAR = ("OSYM 2025 TYT", "OSYM 2025 AYT")
_BAYRAK = "sik_bos"

_SAYAC_SQL = """
UPDATE topic_hierarchy t
   SET total_questions = COALESCE(g.adet, 0), updated_at = now()
  FROM (SELECT th.id, count(qb.id) AS adet
          FROM topic_hierarchy th
          LEFT JOIN question_bank qb
                 ON qb.primary_topic_id = th.id AND qb.is_active IS TRUE
         GROUP BY th.id) g
 WHERE g.id = t.id
   AND t.total_questions IS DISTINCT FROM COALESCE(g.adet, 0)
"""


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0012] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0012] mv_safe_for_beta yenilendi")


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("question_bank"):
        _log.info("[0012] question_bank yok (taze DB?) -- atlandi")
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("alan", sa.String(), nullable=False),
        sa.Column("eski_deger", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", "alan"),
    )

    ids = (
        b.execute(
            sa.text(
                "SELECT b.id FROM question_bank b "
                "JOIN question_metadata m ON m.id = b.id "
                "WHERE m.source_book = ANY(:kaynaklar) "
                "AND (m.pipeline_metadata::jsonb -> 'bayraklar') ? :bayrak "
                "AND b.is_active IS TRUE"
            ),
            {"kaynaklar": list(_KAYNAKLAR), "bayrak": _BAYRAK},
        )
        .scalars()
        .all()
    )
    if not ids:
        _log.info("[0012] sik_bos bayrakli aktif OSYM sorusu yok -- atlandi")
        return

    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, alan, eski_deger) "  # noqa: S608  # nosec B608
            "VALUES (:id, 'is_active', 'true') ON CONFLICT DO NOTHING"
        ),
        [{"id": sid} for sid in ids],
    )
    b.execute(
        sa.text(
            "UPDATE question_bank SET is_active = FALSE, updated_at = now() "
            "WHERE id = ANY(:ids)"
        ),
        {"ids": list(ids)},
    )

    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    _log.info("[0012] %s sik_bos bayrakli soru pasife alindi", len(ids))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0012] %s yok -- geri alinacak bir sey yok", GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(f"SELECT id FROM {GUNLUK} WHERE alan = 'is_active'")  # noqa: S608  # nosec B608
    ).scalars().all()
    if kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = TRUE, updated_at = now() "
                "WHERE id = ANY(:ids)"
            ),
            {"ids": list(kayitlar)},
        )
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
    _log.info("[0012] %s kayit geri alindi, %s dusuruldu", len(kayitlar), GUNLUK)
