"""345 2025 TYT Turkce: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0069_trt345_eski_hat_pasif
Revises: 0068_trt345_agac
Create Date: 2026-09-27

KARAR
-----
Sahip talimati (26 Eyl 2026): "345 2025 TYT Kimya, Sosyal Bilgiler ve
Turkce; ucunu de sirayla onay istemeden kesintisiz tam otonom isle".
Emsal 0063 (KMT345) ve 0066 (SOS345). Bu migration SILMEZ; yalniz
is_active=FALSE yapar ve downgrade ile tam geri alinir.

NEDEN (Faz 5 olcumu, TRT_345_YONTEM.md bolum 5)
----------------------------------------------
Ayni kitabin uc eski aktarimi aktif duruyor:
    '345 2025 Tyt Turkce Soru Bankasi' (Turkce harfli)   18 satir, 18 aktif
    '345 Tyt Turkce Soru Bankasi' (Turkce harfli)        11 satir, 11 aktif
    '345 Yayinevi TYT Turkce Soru Bankasi 2025'           2 satir, 2 aktif
Yeni ithal (tur345tyt_ithal.py, 2066 satir; 4 soru Paragraf kitabinda ayni
hash ile zaten var) ayni sorulari basili anahtar, iki bagimsiz okuma ve
gozle hakemli metinle tasir. Eski satirlardan 17'si modern bir
soruya GUCLU baglanir (govde 3-gram >= 0.9 VE bes sikkin >= 3'u birebir):
10 + 5 + 2. Hicbiri modern soruyla ayni soru_hash'i tasimaz.
17 eslesmenin 4'unde eski cevap basili anahtardan farkli.

NE YAPAR
--------
Asagidaki (eski id, modern kirpim) ciftlerinde eski satir is_active=FALSE.
Guard: eski satir uc eski kaynak adindan birini tasiyor, ithal_araci yok,
hala aktif, VE modern karsiligi bu kitabin ithal satiri olarak DB'de var
(yoksa -- taze/CI DB -- eski satira dokunulmaz). GUCLU eslesmeyen
14 eski satir AKTIF kalir.
Degisen her satirin onceki is_active degeri GUNLUK'e yazilir; downgrade
onu geri yukler. Konu sayaci ve beta gorunumu yenilenir.

Revizyon adi 26 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0069_trt345_eski_hat_pasif"
down_revision: Union[str, None] = "0068_trt345_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "trt345_eski_hat_gunlugu_0069"
KAYNAK = "345 2025 TYT Turkce Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/tur345tyt_ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "345 2025 Tyt T\u00fcrk\u00e7e Soru Bankas\u0131",
    "345 Tyt T\u00fcrk\u00e7e Soru Bankas\u0131",
    "345 Yayinevi TYT Turkce Soru Bankasi 2025",
)

# (eski satir id, modern kirpim adi -- TRT345- oneksiz); kaynak:
# 345_2025_tyt_turkce_mukerrer_adaylari.json eski_hat, modern_karsilik=true.
# Yorum: eski aktarim (25 / 24 / YE = Yayinevi adi) ve eski satirin basili sayfasi.
ESKI_MODERN: tuple[tuple[str, str], ...] = (
    ("00f54306-dc88-597c-9180-63bf9678a100", "T015_07"),  # 25 s35
    ("0439fa0a-6c65-585c-ab21-cc59a59a977f", "T018_06"),  # 25 s41
    ("2dcbccc5-523a-543f-93e1-688de98720c0", "T019_07"),  # 25 s43
    ("19af0508-6182-59b5-b8a7-5b109ed7679a", "T020_09"),  # 25 s45
    ("6586c1af-3de5-5457-ae6a-6e4b8e1a13fa", "T050_07"),  # 25 s105
    ("42622ee5-a20e-5130-991a-42e05c7be6cd", "T068_07"),  # 25 s141
    ("eba716c9-f856-510b-acdf-f4b63d37756d", "T068_08"),  # 25 s141
    ("dcca7e90-8522-5710-8839-4a9ddc5273cf", "T080_04"),  # 25 s166
    ("b4575caf-1caa-5d0a-aae4-f7049eedef1b", "T125_05"),  # 25 s261
    ("97634057-adb5-5a62-b305-b63438c05f9e", "T199_01"),  # 25 s414
    ("79561f83-bacb-52e3-8279-c2b8e0a38c4a", "T016_05"),  # 24 s36
    ("3d2dd00a-c88a-522c-acef-8e9eb34000b9", "T043_01"),  # 24 s90
    ("ab726d37-97f6-5ba6-a961-67ec5b62b5d2", "T060_04"),  # 24 s125
    ("b180fe28-9904-5bb1-8df1-1d333442a983", "T068_08"),  # 24 s141
    ("b2e014d3-f5aa-5e55-94d9-81bc01894727", "T068_07"),  # 24 s141
    ("f8ae35a1-1f98-437c-8deb-d9976fda62b7", "T004_04"),  # YE s12
    ("87dbe4eb-b10e-4bd2-a8da-c26befa1d4d1", "T007_01"),  # YE s18
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
        _log.info("[0069] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0069] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "topic_hierarchy")
    )


def hedef_idler(modern_var: set[str]) -> list[str]:
    """Modern karsiligi DB'de bulunan eski satir id'leri (saf fonksiyon, test edilir)."""
    return [e for e, m in ESKI_MODERN if f"TRT345-{m}.png" in modern_var]


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0069] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0069] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0069] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0069] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
