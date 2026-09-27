"""2020-2021 ACIL TYT Matematik: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0075_acl21t_eski_hat_pasif
Revises: 0074_acl21t_agac
Create Date: 2026-09-27

KARAR
-----
Sahip talimati (27 Eyl 2026): "siradaki islenebilir kitabi ayni sekilde
bastan sona isle". Emsal 0063 / 0066 / 0069 / 0072. Bu migration SILMEZ;
yalniz is_active=FALSE yapar ve downgrade ile tam geri alinir.

NEDEN (Faz 5 olcumu, MAT_ACIL_2021_TYT_YONTEM.md bolum 5)
--------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    '2020-2021-ACIL-TYT Matematik Soru Bankasi' (Turkce harfli)  27 satir, 27 aktif
Eski satirlardan 16'si modern bir soruya GUCLU baglanir (govde 3-gram
>= 0.9 VE bes sikkin >= 3'u birebir); 16'sinin hicbirinde eski cevap
basili anahtardan farkli degil.

MODERN KARSILIK = MODERN ID
---------------------------
Bu kitabin sorularinin bir kismi onceki baskida (2019-2020, ACL20T, 0073)
ayni soru_hash ile zaten var: ayni id, acil2021tyt_ithal onlari YAZMADI.
Bu yuzden guard kirpim adina degil MODERN ID'ye bakar: (eski id, modern
kirpim, modern id) ciftinde modern id question_bank'ta varsa (ACL21T ya
da ayni hash ile ACL20T satiri) eski satir is_active=FALSE. Modern id =
uuid5(NAMESPACE_OID, soru_hash(govde, sikler)) -- ithalin kendi formulu.

NE YAPAR
--------
Guard: eski satir eski kaynak adini tasiyor, ithal_araci yok, hala aktif,
VE modern id DB'de var (yoksa -- taze/CI DB -- eski satira dokunulmaz).
GUCLU eslesmeyen 11 eski satir AKTIF kalir. Degisen her satirin onceki
is_active degeri GUNLUK'e yazilir; downgrade onu geri yukler.

Revizyon adi 26 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0075_acl21t_eski_hat_pasif"
down_revision: Union[str, None] = "0074_acl21t_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl21t_eski_hat_gunlugu_0075"
KAYNAK = "2020-2021 ACIL TYT Matematik Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/acil2021tyt_ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "2020-2021-AC\u0130L-TYT Matematik Soru Bankas\u0131",
)

# (eski satir id, modern kirpim adi -- ACL21T- oneksiz, modern id); kaynak:
# acil_2021_tyt_matematik_mukerrer_adaylari.json eski_hat, modern_karsilik=true.
# Yorum: eski satirin basili sayfasi.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "ade52a9f-e56a-5789-9bbb-f14c828ee434",
        "T003_12",
        "5235a84e-4b51-53ea-9bce-be0a408fc1b1",
    ),  # s14
    (
        "14ac595a-0f63-522b-8986-1f37b2dcf886",
        "T005_08",
        "aed69770-caa7-5d45-a18f-99b7c3082404",
    ),  # s19
    (
        "c8bd03a2-9aef-54c2-a822-421af69a8d7d",
        "T027_11",
        "bc9b5dc9-1acb-5ee9-8251-3ea52db50bf2",
    ),  # s81
    (
        "a741e59e-154a-5c5a-9894-9109c01e54c9",
        "T046_10",
        "8d3612c7-b04a-5efb-932d-bb4ed3ecc30d",
    ),  # s140
    (
        "d8d1289d-14e0-5c95-add7-71325fee8ded",
        "T062_07",
        "82b80a7c-64f7-5c57-a823-f17aed8b1e3c",
    ),  # s190
    (
        "21ebf43e-847b-51e8-8660-4542a2f6a6f7",
        "T064_14",
        "ed46cd23-2782-5c35-b767-a6255e17a409",
    ),  # s197
    (
        "3067ad21-9b1e-5850-bda3-cf6daf7e5fc7",
        "T113_12",
        "27161a6d-f9f8-58c2-b493-9b739a7b99c9",
    ),  # s340
    (
        "fe5cd755-c514-58e8-b12c-38f9acc880d8",
        "T125_01",
        "9e66101c-a991-5544-afcf-8b5e62f39f8d",
    ),  # s366
    (
        "3543e5dd-1027-5c48-8fc5-0970609f2e67",
        "T135_16",
        "413370d9-b370-534f-b530-b9085fbda042",
    ),  # s397
    (
        "6155be46-50f7-5282-8152-91173b2b065b",
        "T135_15",
        "47046db0-419e-55d4-b115-91dc971fddaa",
    ),  # s397
    (
        "cc2769e1-ce8e-5b08-925c-758ff113902b",
        "T135_14",
        "d19ec8b5-caab-5a17-84c5-4fa587548b87",
    ),  # s397
    (
        "04a598f7-efc9-5f37-b96a-24ad2fa7f69a",
        "T139_19",
        "7e8b4e79-2a75-5586-93a9-a21904d5324c",
    ),  # s411
    (
        "aee18d15-ab7b-5985-967b-ad26595390a3",
        "T139_18",
        "bb108416-206a-546a-9e1b-35191c0d15bd",
    ),  # s411
    (
        "1f4aecf7-1af3-51d8-b3c6-aef949f22eb2",
        "T140_16",
        "5efc4aac-512c-58b2-8a4c-b18926915353",
    ),  # s414
    (
        "73b16b61-a468-5dc1-a94a-3efa82b94a20",
        "T141_11",
        "6e662a0b-b158-54f9-a864-2385249c7dd0",
    ),  # s416
    (
        "a0224307-d413-5998-8b8a-3d8a9c7696f1",
        "T146_12",
        "dbc9a5e1-6dbf-59d3-9e8b-fe432e4d536c",
    ),  # s432
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
SELECT qb.id::text
  FROM question_bank qb
 WHERE qb.id::text = ANY(:idler)
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
        _log.info("[0075] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0075] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "topic_hierarchy")
    )


def hedef_idler(modern_var: set[str]) -> list[str]:
    """Modern id'si DB'de bulunan eski satir id'leri (saf fonksiyon, test edilir)."""
    return [e for e, _, mid in ESKI_MODERN if mid in modern_var]


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0075] soru tablolari yok (taze DB?) -- atlandi")
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
            sa.text(_MODERN_SQL), {"idler": [mid for _, _, mid in ESKI_MODERN]}
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
    _log.info("[0075] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0075] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0075] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
