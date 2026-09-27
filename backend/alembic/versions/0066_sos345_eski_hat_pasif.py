"""345 2025 TYT Sosyal Bilgiler: modern karsiligi olan eski hat satirlari pasif

Revision ID: 0066_sos345_eski_hat_pasif
Revises: 0065_sos345_agac
Create Date: 2026-09-27

KARAR
-----
Sahip talimati (26 Eyl 2026): "345 2025 TYT Kimya, Sosyal Bilgiler ve
Turkce; ucunu de sirayla onay istemeden kesintisiz tam otonom isle".
Emsal 0058 (STM345) ve 0063 (KMT345). Bu migration SILMEZ; yalniz
is_active=FALSE yapar ve downgrade ile tam geri alinir.

NEDEN (Faz 5 olcumu, SOS_345_YONTEM.md bolum 5)
----------------------------------------------
Ayni kitabin iki eski aktarimi aktif duruyor:
    '345 2025 Tyt Sosyal Bilgiler Soru Bankasi' (Turkce i)  26 satir, 26 aktif
    '345 Tyt Sosyal Bilgiler Soru Bankasi' (2024 baskisi)    12 satir, 12 aktif
Yeni ithal (sos345tyt_ithal.py, 1233 satir) ayni sorulari basili anahtar,
iki bagimsiz okuma ve gozle hakemli metinle tasir. Eski satirlardan
33'u modern bir soruya GUCLU baglanir (govde 3-gram >= 0.9 VE bes
sikkin >= 3'u birebir): 25 + 8. Bunlarin 1'i modern soruyla AYNI
soru_hash'i tasir; tekil aktif hash kurali geregi eski satir acikken
modern satir aktiflestirilemez. 33 eslesmenin 5'inde eski cevap basili
anahtardan farkli (sik sirasi ayni).

NE YAPAR
--------
Asagidaki (eski id, modern kirpim) ciftlerinde eski satir is_active=FALSE.
Guard: eski satir iki eski kaynak adindan birini tasiyor, ithal_araci yok,
hala aktif, VE modern karsiligi bu kitabin ithal satiri olarak DB'de var
(yoksa -- taze/CI DB -- eski satira dokunulmaz). GUCLU eslesmeyen
5 eski satir AKTIF kalir.
Degisen her satirin onceki is_active degeri GUNLUK'e yazilir; downgrade
onu geri yukler. Konu sayaci ve beta gorunumu yenilenir.

Revizyon adi 26 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0066_sos345_eski_hat_pasif"
down_revision: Union[str, None] = "0065_sos345_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "sos345_eski_hat_gunlugu_0066"
KAYNAK = "345 2025 TYT Sosyal Bilgiler Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/sos345tyt_ithal.py"
ESKI_KAYNAKLAR: tuple[str, ...] = (
    "345 2025 Tyt Sosyal Bilgiler Soru Bankas\u0131",
    "345 Tyt Sosyal Bilgiler Soru Bankas\u0131",
)

# (eski satir id, modern kirpim adi -- SOS345- oneksiz); kaynak:
# 345_2025_tyt_sosyal_mukerrer_adaylari.json eski_hat, modern_karsilik=true.
# Yorum: baski (25 = 2025, 24 = 2024) ve eski satirin basili sayfasi.
ESKI_MODERN: tuple[tuple[str, str], ...] = (
    ("8c634dcd-116a-5af0-a5ab-6546bd7acd37", "T004_06"),  # 25 s13
    ("12d45fb0-c35e-56bd-a3dd-c84c5de50bad", "T010_08"),  # 25 s25
    ("866dc21f-008c-51c2-9256-f6bcc1f9943d", "T010_05"),  # 25 s25
    ("cea09eea-f957-50f7-a8df-a0192820df75", "T025_01"),  # 25 s54
    ("97591f4e-eb06-5524-9e60-e73c8784b034", "T034_08"),  # 25 s73
    ("d262a544-3bd9-5665-b5b0-48ad3906e47a", "T034_06"),  # 25 s73
    ("1b3a0b35-c25b-51ec-bc3c-e418b91e180f", "T046_05"),  # 25 s97
    ("26ce5b19-50b1-5ffa-80b3-f8887e26e669", "T048_11"),  # 25 s101
    ("ae3f86cb-ae57-5b7b-a591-3e8045e69392", "T054_07"),  # 25 s113
    ("64f8466b-9477-5bc3-9c93-0a64f6b2ac2c", "T064_09"),  # 25 s133
    ("d54aee1b-4b4a-5995-af79-22af193b65cb", "T064_10"),  # 25 s133
    ("a8939410-5092-5e23-8b2c-021367155a52", "T066_04"),  # 25 s136
    ("4f540408-5562-546b-b20b-e9f78b1bd5ab", "T100_06"),  # 25 s205
    ("be3e3819-3926-5c6e-aeea-7bb8b17a9ccc", "T101_05"),  # 25 s207
    ("a449f090-e69b-5fb0-9a69-36a7f7128a50", "T107_06"),  # 25 s219
    ("6711e3ac-308d-5517-9acb-1993ab31fd9c", "T116_07"),  # 25 s237
    ("b2c5a261-1a22-52ef-8320-9397777023fc", "T116_08"),  # 25 s237
    ("299a7387-9df2-5134-9240-62ef35b44de0", "T128_08"),  # 25 s261
    ("2ebe5c78-8423-5936-ace7-d896141de720", "T131_08"),  # 25 s267
    ("d44db488-c908-5af2-af51-1252257d8088", "T131_10"),  # 25 s267
    ("61af6fff-22d4-5785-87c3-5336fe71f7a0", "T135_06"),  # 25 s275
    ("9ce0c73f-6f73-5621-86ac-ccd7ebd1bfe9", "T135_09"),  # 25 s275
    ("bbc9c08d-ee1e-5b15-9b35-53ec98958371", "T136_10"),  # 25 s277
    ("55499f14-f57c-59f9-8548-86cededb9d2c", "T142_05"),  # 25 s289
    ("62400c47-4231-563d-a338-aa52c0b96fe4", "T148_04"),  # 25 s300
    ("10e66d3d-e9a9-506d-89a3-9a1fbba5f1db", "T010_05"),  # 24 s25
    ("1c321c62-61a3-52e0-bba8-0fbe977519c9", "T058_06"),  # 24 s121
    ("4dfc5cc0-0cc6-533d-9036-1a6bc7d32e99", "T095_06"),  # 24 s195
    ("6b7ef97a-e894-57e0-bc72-308321ca441f", "T107_06"),  # 24 s219
    ("2099e02a-c4f5-5098-89f7-8a53c867fa4f", "T125_05"),  # 24 s255
    ("409be257-aeee-529c-a56c-5e49a18e12bf", "T131_08"),  # 24 s267
    ("bda2f411-b4fe-57f4-9e2d-60b2553e176e", "T131_10"),  # 24 s267
    ("72c539f1-666a-5096-9aa0-dbf79be6066f", "T136_09"),  # 24 s277
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
        _log.info("[0066] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0066] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in ("question_bank", "question_metadata", "topic_hierarchy")
    )


def hedef_idler(modern_var: set[str]) -> list[str]:
    """Modern karsiligi DB'de bulunan eski satir id'leri (saf fonksiyon, test edilir)."""
    return [e for e, m in ESKI_MODERN if f"SOS345-{m}.png" in modern_var]


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0066] soru tablolari yok (taze DB?) -- atlandi")
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
    _log.info("[0066] eski hat: %s aday, %s satir pasife alindi", len(idler), len(eski))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0066] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0066] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
