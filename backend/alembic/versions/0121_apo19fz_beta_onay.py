"""2019-2020 Apotemi TYT-AYT Fizik Soru Bankasi: yeni ithal beta kapisindan gecer (2132/2180)

Revision ID: 0121_apo19fz_beta_onay
Revises: 0120_apo19fz_eski_hat_pasif
Create Date: 2026-09-28

SAHIP KARARI
------------
"siradaki kitaplari onay istemeden tam otonom isle" -- Faz 8 = aktiflestirme.
Bireysel insan denetimi yapilmadi; toplu beta sahibi onayi (0073 / 0076 emsali).

KAPI YUKU OLCULDU (yerel DB, agac + ithal + eski hat pasif sonrasi)
------------------------------------------------------------------
Kitap 2180 soru; ithalin yazdigi 2180 satirda:
    quality_review_status 'pending' ............ 2180/2180 (kilit)
    is_ai_generated=true, review 'PENDING' ..... 2180/2180 (kilit)
    bayrak sik_bos ...........................    0  -> DISLANIR
    bayrak gorsel_yok_sekilli ................    0  -> DISLANIR
    bayrak gosterilemez_gorsel_sik_kirpimsiz .    0  -> DISLANIR
    bayrak sik_okunamadi .....................    0  -> DISLANIR
    bayrak ortak_oncul_kirpimda_yok ..........    0  -> DISLANIR
    ogrenciye gorunen alti alanda `[??]` .......   46  -> DISLANIR
    aktif satirlarla soru_hash cakismasi .......    0  -> DISLANIR
    modern_kitap_ikizi, ikizi AKTIF ............    0  -> DISLANIR
    kitap ici ayni soru_hash (ilk id disi) .....    2  -> DISLANIR
HEDEF: 2132/2180

DISLAMA (0076 ile ayni kural + ortak oncul)
-------------------------------------------
Servis disi bayrak (sik_bos, gorsel_yok_sekilli,
gosterilemez_gorsel_sik_kirpimsiz, sik_okunamadi, ortak_oncul_kirpimda_yok),
ogrenciye gorunen alti alanda `[??]`, aktif hash ikizi, aktif modern kitap
ikizi.

KONSENSUS SINYALLERI (FIZ_APOTEMI_2019_TYT_AYT_YONTEM.md)
-------------------------------------------------
- anahtar_iki_bagimsiz_okuma_2180_2180_hucre: basili cevap anahtari iki
  bagimsiz gorsel okuma, fark yok.
- anahtar_glif_ucuncu_kanal_loo: piksel glif LOO 2180/2180; uyumsuzlar 5x
  goz teyidi; bolutlenemeyen 0 test 5x gozle.
- anahtar_hucre_sayisi_numara_capasina_esit: hucre sayisi == okuyucu simgesi +
  kirmizi numara capasi (2180).
- transkripsiyon_kapilari_yesil: harness kapilari yesil.
- metin_tam_ikinci_okuma_gozle_hukum: on kayitli TAM ikinci okuma,
  455 fark hakemle gozle hukum.

DURUSTLUK
---------
- quality_review_status 'pending' -> 'auto_judged_high'; 'human_verified'
  YAZILMAZ. review_status 'PENDING' -> 'APPROVED'; metadata'ya
  onay_turu='toplu_beta_sahibi', bireysel_denetim_yapildi=false.
- is_ai_generated'a ve is_public'e DOKUNULMAZ.
- Cevaplar dogrulanmadi (tek kaynak basili anahtar); sorular cozulmedi.

GERI ALINABILIR
---------------
Degisen her satirin onceki uc degeri GUNLUK'e yazilir; downgrade onlari geri
yukler ve eklenen metadata anahtarlarini siler.
"""

import json
import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0121_apo19fz_beta_onay"
down_revision: Union[str, None] = "0120_apo19fz_eski_hat_pasif"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "apo19fz_beta_onay_gunlugu_0121"
KAYNAK = "2019-2020 Apotemi TYT-AYT Fizik Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"

ORTME_ISARETI = "%[??]%"

SERVIS_DISI_BAYRAKLAR = (
    "sik_bos",
    "gorsel_yok_sekilli",
    "gosterilemez_gorsel_sik_kirpimsiz",
    "sik_okunamadi",
    "ortak_oncul_kirpimda_yok",
)

SINYALLER: tuple[str, ...] = (
    "anahtar_iki_bagimsiz_okuma_2180_2180_hucre",
    "anahtar_glif_ucuncu_kanal_loo",
    "anahtar_hucre_sayisi_numara_capasina_esit",
    "transkripsiyon_kapilari_yesil",
    "metin_tam_ikinci_okuma_gozle_hukum",
)

EK_ANAHTARLAR = (
    "consensus_2signal_run",
    "konsensus_sinyalleri",
    "onay_turu",
    "bireysel_denetim_yapildi",
)

# SQL DUZ YAZILIR (interpolasyon yok); SERVIS_DISI_BAYRAKLAR ile ayni bes
# bayragi tasidigini test dogrular. Son NOT EXISTS: aktif modern kitap ikizi.
_HEDEF_SQL = """
SELECT qb.id, qb.is_active, qb.review_status, qs.quality_review_status
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
  JOIN question_content qc ON qc.id = qb.id
  LEFT JOIN question_statistics qs ON qs.id = qb.id
 WHERE qm.source_book = :kaynak
   AND qm.pipeline_metadata::jsonb ->> 'ithal_araci' = :arac
   AND qb.is_active IS NOT TRUE
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos')
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'gorsel_yok_sekilli')
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar')
            ? 'gosterilemez_gorsel_sik_kirpimsiz')
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_okunamadi')
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar')
            ? 'ortak_oncul_kirpimda_yok')
   AND qc.question_text NOT LIKE :isaret
   AND qc.option_a NOT LIKE :isaret
   AND qc.option_b NOT LIKE :isaret
   AND qc.option_c NOT LIKE :isaret
   AND qc.option_d NOT LIKE :isaret
   AND qc.option_e NOT LIKE :isaret
   AND NOT EXISTS (SELECT 1 FROM question_bank o
                    WHERE o.soru_hash = qb.soru_hash
                      AND o.is_active IS TRUE AND o.id <> qb.id)
   AND NOT EXISTS (SELECT 1 FROM question_bank o
                     JOIN question_metadata om ON om.id = o.id
                    WHERE o.soru_hash = qb.soru_hash AND o.id <> qb.id
                      AND om.source_book = qm.source_book
                      AND o.id::text < qb.id::text)
   AND NOT EXISTS (
         SELECT 1
           FROM jsonb_array_elements_text(
                  CASE WHEN jsonb_typeof(qm.pipeline_metadata::jsonb -> 'modern_kitap_ikizi')
                            = 'array'
                       THEN qm.pipeline_metadata::jsonb -> 'modern_kitap_ikizi'
                       ELSE '[]'::jsonb END) AS ikiz(id)
           JOIN question_bank o ON o.id::text = ikiz.id
          WHERE o.is_active IS TRUE)
"""

_META_EKLE = sa.text(
    """
    UPDATE question_metadata
       SET pipeline_metadata = (
             pipeline_metadata::jsonb
             || jsonb_build_object(
                  'consensus_2signal_run', true,
                  'konsensus_sinyalleri', CAST(:sinyaller AS jsonb),
                  'onay_turu', 'toplu_beta_sahibi',
                  'bireysel_denetim_yapildi', false)
           )::json
     WHERE id = ANY(:idler)
    """
)

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
        _log.info("[0121] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0121] mv_safe_for_beta yenilendi")


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(
        denetci.has_table(t)
        for t in (
            "question_bank",
            "question_metadata",
            "question_content",
            "question_statistics",
        )
    )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0121] soru tablolari yok (taze DB?) -- atlandi")
        return
    var_mi = b.execute(
        sa.text(
            "SELECT 1 FROM question_metadata WHERE source_book = :k"
            " AND pipeline_metadata::jsonb ->> 'ithal_araci' = :a LIMIT 1"
        ),
        {"k": KAYNAK, "a": ITHAL_ARACI},
    ).first()
    if not var_mi:
        _log.info("[0121] %s ithal satiri yok -- atlandi", KAYNAK)
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("islem", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.Column("onceki_review_status", sa.String(), nullable=True),
        sa.Column("onceki_quality_review_status", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    hedef = b.execute(
        sa.text(_HEDEF_SQL),
        {"kaynak": KAYNAK, "arac": ITHAL_ARACI, "isaret": ORTME_ISARETI},
    ).fetchall()
    idler = [r[0] for r in hedef]
    if idler:
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, islem, onceki_is_active,"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
                " onceki_review_status, onceki_quality_review_status)"
                " VALUES (:id, 'beta_ac', :akt, :rs, :qrs)"
            ),
            [{"id": str(r[0]), "akt": r[1], "rs": r[2], "qrs": r[3]} for r in hedef],
        )
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = TRUE, review_status = 'APPROVED',"
                " updated_at = now() WHERE id = ANY(:idler)"
            ),
            {"idler": idler},
        )
        b.execute(
            sa.text(
                "UPDATE question_statistics SET quality_review_status = 'auto_judged_high'"
                " WHERE id = ANY(:idler)"
            ),
            {"idler": idler},
        )
        b.execute(
            _META_EKLE, {"idler": idler, "sinyaller": json.dumps(list(SINYALLER))}
        )
    _log.info("[0121] beta kapisi: %s satir acildi", len(idler))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0121] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(
            "SELECT id, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
            f" onceki_quality_review_status FROM {GUNLUK}"
        )
    ).fetchall()
    for sid, akt, rs, qrs in kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = :akt, review_status = :rs,"
                " updated_at = now() WHERE id = :id"
            ),
            {"id": sid, "akt": akt, "rs": rs},
        )
        b.execute(
            sa.text(
                "UPDATE question_statistics SET quality_review_status = :qrs"
                " WHERE id = :id"
            ),
            {"id": sid, "qrs": qrs},
        )
    acilan = [r[0] for r in kayitlar]
    for anahtar in EK_ANAHTARLAR:
        b.execute(
            sa.text(
                "UPDATE question_metadata"
                " SET pipeline_metadata = (pipeline_metadata::jsonb - :a)::json"
                " WHERE id = ANY(:idler)"
            ),
            {"a": anahtar, "idler": acilan},
        )
    _log.info("[0121] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
