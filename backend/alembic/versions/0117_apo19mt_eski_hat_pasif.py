"""2019-2020 APOTEMI TYT Matematik Soru Bankasi: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0117_apo19mt_eski_hat_pasif
Revises: 0116_apo19mt_agac
Create Date: 2026-09-28

KARAR
-----
Sahip talimati: siradaki kitaplari ayni sekilde bastan sona isle. Emsal
0072 / 0075. Bu migration SILMEZ; yalniz is_active=FALSE yapar ve downgrade
ile tam geri alinir.

NEDEN (mukerrer olcumu, apotemi_2019_tyt_matematik_mukerrer_adaylari.json)
------------------------------------------------------------------
Ayni kitabin eski aktarimi aktif duruyor:
    2019-2020-Apotemi-Tyt Matematik Soru Bankas\u0131: 9 satir, 9 aktif, 6 modern karsilik
GUCLU esleme = govde 3-gram >= 0.9 VE bes sikkin >= 3'u birebir.

MODERN KARSILIK = MODERN ID
---------------------------
Guard kirpim adina degil MODERN ID'ye bakar: (eski id, modern kirpim, modern
id) ciftinde modern id question_bank'ta varsa eski satir is_active=FALSE.
Modern id = uuid5(NAMESPACE_OID, soru_hash(govde, sikler)) -- ithalin formulu.
Taze/CI DB'de modern id yoksa eski satira dokunulmaz.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0117_apo19mt_eski_hat_pasif"
down_revision: Union[str, None] = "0116_apo19mt_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "apo19mt_eski_hat_gunlugu_0117"
KAYNAK = "2019-2020 APOTEMI TYT Matematik Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = ("2019-2020-Apotemi-Tyt Matematik Soru Bankas\u0131",)

# (eski satir id, modern kirpim adi -- APO19MT- oneksiz, modern id); kaynak:
# mukerrer_adaylari.json eski_hat, modern_karsilik=true. Yorum: eski basili sayfa.
ESKI_MODERN: tuple[tuple[str, str, str], ...] = (
    (
        "09bbfb03-8fae-5b8c-a322-622165ae3195",
        "T011_07",
        "10cbd90b-6afc-5518-b3c6-0e3084c6c790",
    ),  # s31
    (
        "90034d49-874c-58b8-870f-e451b4bde0f5",
        "T059_03",
        "c928f4a6-ac99-56e8-a876-48f4847cc5fe",
    ),  # s158
    (
        "4452afd9-3774-5f8f-a4e7-d0d0d43b43c9",
        "T065_12",
        "ca13fc35-fa31-5c54-a1e7-4631b4efc129",
    ),  # s176
    (
        "07b0f1f9-46b2-5cfc-9b81-8216d92e4a14",
        "T081_04",
        "dc46952c-6527-5e6a-8e1c-7f26561ad956",
    ),  # s222
    (
        "8dd18241-8497-560c-bd85-c5a59fb23cad",
        "T094_01",
        "22417101-7ee0-557c-bb83-8422c4c7e10f",
    ),  # s252
    (
        "d413a13e-d209-541b-b40d-d3b645674885",
        "T102_08",
        "0c733fcf-2ce4-549d-bccb-1aa655cba29f",
    ),  # s271
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
        _log.info("[0117] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0117] mv_safe_for_beta yenilendi")


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
        _log.info("[0117] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0117] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0117] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0117] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
