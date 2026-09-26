"""345 Start Matematik: yeni ithal beta kapisindan gecer (365/371)

Revision ID: 0059_stm345_beta_onay
Revises: 0058_stm345_eski_hat_pasif
Create Date: 2026-09-26

SAHIP KARARI (26 Eyl 2026)
--------------------------
"FAZ 7 VE FAZ 8 I TAMAMLA" -- Faz 8 = aktiflestirme (plan
STM_345_KESIF_VE_PLAN.md). Bireysel insan denetimi yapilmadi; toplu beta
sahibi onayi (0014/0016/0018/0023/0027/0037/0039/0056 emsali).

KAPI YUKU OLCULDU (26 Eyl, yerel DB, 0058 + stm345_ithal sonrasi)
----------------------------------------------------------------
`v_safe_for_beta` tanimi pg_get_viewdef ile okundu. 371 yeni satirda:
    quality_review_status 'pending' ............  371/371 (kilit)
    uyum sinyali (consensus_2signal_run vb.) ...    0/371 (kilit)
    is_ai_generated=true, review 'PENDING' .....  371/371 (kilit)
    sik_bos / gorsel_yok_sekilli /
      gosterilemez_gorsel_sik_kirpimsiz ........    0
    ogrenciye gorunen alti alanda `[??]` .......    6
    bos sik / cevap ............................    0
    gorselsiz satir ............................    0
    aktif satirlarla soru_hash cakismasi .......    0
Uc kilit acilir, is_active acilir.

HEDEF 365 (371 DEGIL)
--------------------
Dislama kurali 0039/0056 ile ayni: servis edilemez bayrak ya da gorunen
alanda `[??]`. `[??]` tasiyan 6 soru (T005_05, T011_07, T012_02, T035_08,
T036_02, T038_04: goruntude render edilmemis isaret, tahmin edilmedi)
PASIF kalir.

ACILANLAR ARASINDA GORUNUR BIRAKILANLAR (dislanmadi)
----------------------------------------------------
- `kaynak_kusuru` (okuma notu): gorunen alanda `[??]` yok; ogrenci tam
  soru kirpimini gorur.
- `okuyucu_diski_ortme` 6: ortme suphesi olculdu; gorunen alanda `[??]` 0.
- `sikler_gorsel` 3: sikler kirpimda, kirpim var.

KONSENSUS SINYALLERI (bu kitaba ait, STM_345_YONTEM.md)
-------------------------------------------------------
- anahtar_iki_bagimsiz_okuma_harf_farki_0: sayfa alti serit iki bagimsiz
  gorsel okuma (A 5x sirali, B 7x ters), 371 girdi, 0 harf farki.
- anahtar_serit_glif_ucuncu_kanal_loo: piksel glif en-yakin-komsu LOO
  358/359; tutmayan ve kapsam disi girdiler goz ile 10x.
- anahtar_girdi_sayisi_basili_numaraya_esit: 90 sutun, serit girdi sayisi
  == basili soru numarasi sayisi.
- transkripsiyon_kapilari_yesil: harness kapilari yesil (371 kirpim, bir
  kez; basili no == sira; bes sik dolu).
- metin_tam_ikinci_okuma_gozle_hukum: on kayitli TAM ikinci okuma, farklar
  piksel/6x ile hukum; soluk '+' piksel taramasi.

DURUSTLUK
---------
- quality_review_status 'pending' -> 'auto_judged_high'; 'human_verified'
  YAZILMAZ. review_status 'PENDING' -> 'APPROVED'; metadata'ya
  onay_turu='toplu_beta_sahibi', bireysel_denetim_yapildi=false.
- is_ai_generated'a DOKUNULMAZ; is_public'e DOKUNULMAZ.
- Cevaplar dogrulanmadi (tek kaynak basili anahtar); sorular cozulmedi.

TELIF
-----
Satirlarin `pipeline_metadata.telif` notu "aktiflestirme ayri karar" der;
bu migration o ayri kararin (urun sahibi) uygulanmasidir.

GERI ALINABILIR
---------------
Degisen her satirin onceki uc degeri GUNLUK'e yazilir; downgrade onlari
geri yukler ve eklenen metadata anahtarlarini siler. Konu sayaci ve beta
gorunumu yenilenir.

Revizyon adi 21 karakter (sinir 32).
"""

import json
import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0059_stm345_beta_onay"
down_revision: Union[str, None] = "0058_stm345_eski_hat_pasif"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "stm345_beta_onay_gunlugu_0059"
KAYNAK = "345 2025 Start Matematik"
ITHAL_ARACI = "scripts/kitap/stm345_ithal.py"

ORTME_ISARETI = "%[??]%"

SERVIS_DISI_BAYRAKLAR = (
    "sik_bos",
    "gorsel_yok_sekilli",
    "gosterilemez_gorsel_sik_kirpimsiz",
)

SINYALLER: tuple[str, ...] = (
    "anahtar_iki_bagimsiz_okuma_harf_farki_0",
    "anahtar_serit_glif_ucuncu_kanal_loo",
    "anahtar_girdi_sayisi_basili_numaraya_esit",
    "transkripsiyon_kapilari_yesil",
    "metin_tam_ikinci_okuma_gozle_hukum",
)

EK_ANAHTARLAR = (
    "consensus_2signal_run",
    "konsensus_sinyalleri",
    "onay_turu",
    "bireysel_denetim_yapildi",
)

# SQL DUZ YAZILIR (interpolasyon yok); SERVIS_DISI_BAYRAKLAR ile ayni uc
# bayragi tasidigini test dogrular.
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
   AND qc.question_text NOT LIKE :isaret
   AND qc.option_a NOT LIKE :isaret
   AND qc.option_b NOT LIKE :isaret
   AND qc.option_c NOT LIKE :isaret
   AND qc.option_d NOT LIKE :isaret
   AND qc.option_e NOT LIKE :isaret
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
        _log.info("[0059] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0059] mv_safe_for_beta yenilendi")


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
        _log.info("[0059] soru tablolari yok (taze DB?) -- atlandi")
        return
    var_mi = b.execute(
        sa.text(
            "SELECT 1 FROM question_metadata WHERE source_book = :k"
            " AND pipeline_metadata::jsonb ->> 'ithal_araci' = :a LIMIT 1"
        ),
        {"k": KAYNAK, "a": ITHAL_ARACI},
    ).first()
    if not var_mi:
        _log.info("[0059] %s ithal satiri yok -- atlandi", KAYNAK)
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
    _log.info("[0059] beta kapisi: %s satir acildi", len(idler))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0059] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0059] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
