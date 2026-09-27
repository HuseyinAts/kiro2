"""345 2025 TYT Turkce: yeni ithal beta kapisindan gecer (2066/2066)

Revision ID: 0070_trt345_beta_onay
Revises: 0069_trt345_eski_hat_pasif
Create Date: 2026-09-27

SAHIP KARARI (26 Eyl 2026)
--------------------------
"345 2025 TYT Kimya, Sosyal Bilgiler ve Turkce; ucunu de sirayla onay
istemeden kesintisiz tam otonom isle" -- Faz 8 = aktiflestirme. Bireysel
insan denetimi yapilmadi; toplu beta sahibi onayi
(0014/0016/0018/0023/0027/0037/0039/0056/0059/0061/0064/0067 emsali).

KAPI YUKU OLCULDU (27 Eyl, yerel DB, 0068 + tur345tyt_ithal + 0069 sonrasi)
-------------------------------------------------------------------------
Kitap 2070 soru; 4'u (T041_07, T044_07, T045_08, T069_06: cikmis sorular)
'345 2025 Paragraf Sifir Risk' kitabinda ayni soru_hash ile zaten aktif --
ayni id, ithal onlari YAZMADI. `v_safe_for_beta` quality_review_status'a
bakar. 2066 yeni satirda:
    quality_review_status 'pending' ............ 2066/2066 (kilit)
    uyum sinyali (consensus_2signal_run) .......    0/2066 (kilit)
    is_ai_generated=true, review 'PENDING' ..... 2066/2066 (kilit)
    sik_bos / gorsel_yok_sekilli /
      gosterilemez_gorsel_sik_kirpimsiz ........    0
    ogrenciye gorunen alti alanda `[??]` .......    0
    bos sik / cevap ............................    0
    gorselsiz satir ............................    0
    '[okunamadi]' sik ..........................    0
    konu dugumu bos ............................    0
    aktif satirlarla soru_hash cakismasi .......    0
Uc kilit acilir, is_active acilir.

HEDEF 2066
----------
Dislama kurali 0039/0056/0059/0061/0064/0067 ile ayni: servis edilemez
bayrak ya da gorunen alanda `[??]` (bu kitapta 0). Aktif bir satirla ayni
soru_hash tasiyan satir acilmaz (tekil aktif hash indeksi); olculen 0.

ACILANLAR ARASINDA GORUNUR BIRAKILANLAR (dislanmadi)
----------------------------------------------------
- `kaynak_kusuru` (okuma notu, 371): cogu dusuk cozunurlukte iki adayli
  isaret (tirnak tipi, virgul / nokta); gorunen alanda `[??]` yok; ogrenci
  tam soru kirpimini gorur.
- `okuyucu_diski_ortme` (260): disk numara kenarini ortuyor, soru metni
  ortulmuyor (ikinci okumada ortme listesindeki her soru gozle bakildi).
- `mukerrer_aday` (24): eski hat (0069 ile pasif), OSYM 2025 TYT ya da
  yayinevinin diger kitaplari (ayri hash).
- `diger_kaynak_sik_sirasi_farkli` (3): DB'nin dogru sikkinin metni bizde
  basili anahtarin harfinde; celiski yok.
- `diger_kaynak_cevap_farki` (4): eski hat satirlari (0069 ile pasif);
  bizim cevap basili tablodan (iki bagimsiz okuma + glif).
- `sikler_gorsel` (3): sikler kirpimda, kirpim var.

KONSENSUS SINYALLERI (bu kitaba ait, TRT_345_YONTEM.md)
------------------------------------------------------
- anahtar_iki_bagimsiz_okuma_2067_2070_hucre: kitap sonu tablo iki
  bagimsiz gorsel okuma; 3 fark 5-6x goz.
- anahtar_tablo_glif_ucuncu_kanal_loo: piksel glif en-yakin-komsu LOO
  2066/2070; uyumsuzlar goz karari ya da goz teyidi.
- anahtar_hucre_sayisi_basili_numaraya_esit: tablo hucre sayisi ==
  basili soru numarasi sayisi (2070).
- transkripsiyon_kapilari_yesil: harness kapilari yesil (2070 kirpim, bir
  kez; basili no == sira; bes sik dolu).
- metin_tam_ikinci_okuma_gozle_hukum: on kayitli TAM ikinci okuma (43
  bagimsiz okuyucu), 164 fark 6 hakemle gozle hukum.

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

revision: str = "0070_trt345_beta_onay"
down_revision: Union[str, None] = "0069_trt345_eski_hat_pasif"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "trt345_beta_onay_gunlugu_0070"
KAYNAK = "345 2025 TYT Turkce Soru Bankasi"
ITHAL_ARACI = "scripts/kitap/tur345tyt_ithal.py"

ORTME_ISARETI = "%[??]%"

SERVIS_DISI_BAYRAKLAR = (
    "sik_bos",
    "gorsel_yok_sekilli",
    "gosterilemez_gorsel_sik_kirpimsiz",
)

SINYALLER: tuple[str, ...] = (
    "anahtar_iki_bagimsiz_okuma_2067_2070_hucre",
    "anahtar_tablo_glif_ucuncu_kanal_loo",
    "anahtar_hucre_sayisi_basili_numaraya_esit",
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
   AND NOT EXISTS (SELECT 1 FROM question_bank o
                    WHERE o.soru_hash = qb.soru_hash
                      AND o.is_active IS TRUE AND o.id <> qb.id)
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
        _log.info("[0070] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0070] mv_safe_for_beta yenilendi")


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
        _log.info("[0070] soru tablolari yok (taze DB?) -- atlandi")
        return
    var_mi = b.execute(
        sa.text(
            "SELECT 1 FROM question_metadata WHERE source_book = :k"
            " AND pipeline_metadata::jsonb ->> 'ithal_araci' = :a LIMIT 1"
        ),
        {"k": KAYNAK, "a": ITHAL_ARACI},
    ).first()
    if not var_mi:
        _log.info("[0070] %s ithal satiri yok -- atlandi", KAYNAK)
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
    _log.info("[0070] beta kapisi: %s satir acildi", len(idler))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0070] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0070] geri alindi: %s satir eski haline dondu", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
