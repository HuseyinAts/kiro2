"""2019-2020 ACIL TYT Matematik: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0072_acl20t_eski_hat_pasif
Revises: 0071_acl20t_agac
Create Date: 2026-09-27

KARAR
-----
Sahip talimati (27 Eyl 2026): "sirada ki islenmemis kitabi isle" (tam
otonom kitap hatti, Faz 0-8). Emsal 0063 / 0066 / 0069. Bu migration
SILMEZ; yalniz is_active=FALSE yapar ve downgrade ile tam geri alinir.

NEDEN (Faz 5 olcumu, MAT_ACIL_1920_TYT_YONTEM.md bolum 5)
--------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    '2019-2020-ACIL-TYT-Soru Bankasi' (Turkce harfli)   9 satir, 9 aktif
    (MATEMATIK 8, GEOMETRI 1)
Yeni ithal (acil1920tyt_ithal.py, 1203 satir) ayni sorulari basili anahtar,
iki bagimsiz okuma ve gozle hakemli metinle tasir. Eski satirlardan 5'i
modern bir soruya GUCLU baglanir (govde 3-gram >= 0.9 VE bes sikkin >= 3'u
birebir); birinin (s424 -> T093_06) soru_hash'i modernle AYNI (eski id
farkli sema). 5 eslesmenin hicbirinde eski cevap basili anahtardan farkli
degil.

NE YAPAR
--------
Asagidaki (eski id, modern kirpim) ciftlerinde eski satir is_active=FALSE.
Guard: eski satir eski kaynak adini tasiyor, ithal_araci yok, hala aktif,
VE modern karsiligi bu kitabin ithal satiri olarak DB'de var (yoksa --
taze/CI DB -- eski satira dokunulmaz). GUCLU eslesmeyen 4 eski satir
AKTIF kalir.
Degisen her satirin onceki is_active degeri GUNLUK'e yazilir; downgrade
onu geri yukler. Konu sayaci ve beta gorunumu yenilenir.

Revizyon adi 26 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0072_acl20t_eski_hat_pasif"
down_revision: Union[str, None] = "0071_acl20t_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl20t_eski_hat_gunlugu_0072"
KAYNAK = "2019-2020 ACIL TYT Matematik Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/acil1920tyt_ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = ("2019-2020-AC\u0130L-TYT-Soru Bankas\u0131",)

# (eski satir id, modern kirpim adi -- ACL20T- oneksiz); kaynak:
# acil_1920_tyt_matematik_mukerrer_adaylari.json eski_hat, modern_karsilik=true.
# Yorum: eski satirin dersi ve basili sayfasi.
ESKI_MODERN: tuple[tuple[str, str], ...] = (
    ("9a8a5c36-1e3d-5311-9391-6378f054151d", "T006_06"),  # GEOMETRI s31
    ("7cc7c7e0-c392-592d-8fea-c0f9c85d7f79", "T031_11"),  # MATEMATIK s141
    ("f12e73be-e04f-59a9-bf3d-14e99fd2b4d0", "T082_07"),  # MATEMATIK s371
    ("4f7d6e20-fd59-58b5-95dc-1638d1b4d99e", "T088_10"),  # MATEMATIK s404
    ("5060d955-3bfd-5643-b4ba-5cc3f1ae4468", "T093_06"),  # MATEMATIK s424 (ayni hash)
)

_ESKI_SQL = """
SELECT qb.id::text, qb.is_active
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
 WHERE qb.id::text = ANY(:idler)
   AND qm.source_book = ANY(:kaynaklar)
   AND (qm.pipeline_metadata::jsonb ->> 'ithal_araci') IS NULL
   AND qb.is_active IS TRUE
"""

_MODERN_SQL = """
SELECT qm.pipeline_metadata::jsonb ->> 'kaynak_gorseli'
  FROM question_metadata qm
 WHERE qm.source_book = :kaynak
   AND qm.pipeline_metadata::jsonb ->> 'ithal_araci' = :arac
"""

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
        _log.info("[0072] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0072] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "topic_hierarchy")
    )


def hedef_idler(modern_var: set[str]) -> list[str]:
    """Modern karsiligi DB'de bulunan eski satir id'leri (saf fonksiyon, test edilir)."""
    return [e for e, m in ESKI_MODERN if f"ACL20T-{m}.png" in modern_var]


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0072] soru tablolari yok (taze DB?) -- atlandi")
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("islem", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    modern = {
        r[0]
        for r in b.execute(
            sa.text(_MODERN_SQL), {"kaynak": KAYNAK, "arac": ITHAL_ARACI}
        ).fetchall()
    }
    idler = hedef_idler(modern)
    eski = (
        b.execute(
            sa.text(_ESKI_SQL),
            {"idler": idler, "kaynaklar": list(ESKI_KAYNAKLAR)},
        ).fetchall()
        if idler
        else []
    )
    if eski:
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, islem, onceki_is_active)"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
                " VALUES (:id, 'eski_hat_pasif', :akt)"
            ),
            [{"id": r[0], "akt": r[1]} for r in eski],
        )
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = FALSE, updated_at = now()"
                " WHERE id::text = ANY(:idler)"
            ),
            {"idler": [r[0] for r in eski]},
        )
    _log.info("[0072] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0072] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(f"SELECT id, onceki_is_active FROM {GUNLUK}")  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
    ).fetchall()
    for sid, akt in kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = :akt, updated_at = now()"
                " WHERE id::text = :id"
            ),
            {"id": sid, "akt": akt},
        )
    _log.info("[0072] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
