"""2024 ACIL TYT Matematik Geometri Kitap-1: kesik kirpim duzeltmesi (T081_02 yeni satir, beta 1)

Revision ID: 0089_acl24mg_kesik_duzeltme
Revises: 0088_acl25pl_beta_onay
Create Date: 2026-09-28

NEDEN
-----
kitap_hat/kirp.py'ye eklenen KESIK kapisi (kutunun ust/alt seridinde murekkep)
birlesmis kitaplarda yeniden kosuldu: acl24mg'de profil SAYFA_ALTI 885 dort
soruda sik satirini kesmisti (sol sutun metni serit hizasina, y 886-895'e
iniyor; s29 / s104 / s113 / s183). SAYFA_ALTI 898 ile yeniden kirpildi; gozle:

* ACL24MG-T081_02 (s183): siklar kirpimda HIC yoktu, okuyucu bes sikki
  '[okunamadi]' yazmisti (bayrak sik_okunamadi, beta DISI kalmisti). Yeni
  kirpimda siklar: A) 7  B) 8  C) 9  D) 10  E) 11. Sik metni degisince
  soru_hash ve id (uuid5) degisir -> YENI satir eklenir (ithal formulu),
  eski satir pasif kalir ve yerine gecen id'yi tasir. Cevap anahtardan (D).
* ACL24MG-T012_03, T048_04: onceki okuma yeni kirpimla ayni (yalniz ust
  yarilari gorunen siklar dogru okunmustu); 'kaynak_kusuru' kesik notu ve
  bayragi kaldirilir. Metin / id degismez.
* ACL24MG-T053_03: kesik vardi, okuma ayni, notu yoktu; degisiklik yok.

BETA
----
Yeni satir 0085 ile ayni kapidan gecer (servis disi bayrak yok, `[??]` yok,
aktif hash ikizi yok) -> 0085 ile ayni durustluk: quality 'auto_judged_high',
review 'APPROVED', onay_turu 'toplu_beta_sahibi', bireysel_denetim_yapildi
false; is_ai_generated ve is_public'e DOKUNULMAZ. Soru cozulmedi.

GERI ALINABILIR
---------------
GUNLUK: dokunulan her satirin onceki degerleri. Downgrade eski satiri geri
yukler, yeni satiri PASIF'e alir (silmez), eklenen anahtarlari siler.
"""

import hashlib
import json
import logging
import unicodedata
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0089_acl24mg_kesik_duzeltme"
down_revision: Union[str, None] = "0088_acl25pl_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl24mg_kesik_duzeltme_gunlugu_0089"
KAYNAK = "2024 ACIL TYT Matematik Geometri Kitap-1"
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
ORTME_ISARETI = "%[??]%"
TARIH = "2026-09-28"
ACIKLAMA = "SAYFA_ALTI 885->898; kirp.py kesik kapisi; siklar yeni kirpimdan gozle"

# Eski (siklari okunamayan) satir: uuid5(hash(govde, 5x '[okunamadi]'))
ESKI_ID = "090a1bc2-08f3-515b-9d47-4c54269a26bd"
# Kesik notu kalkan satirlar (metin ayni)
KUSUR_NOTU_KALKAN = (
    "0c489b23-aad1-5882-8698-3d2c37ab9dd2",  # ACL24MG-T012_03
    "495f9314-6bb1-5ab8-9597-11f4578ebcd2",  # ACL24MG-T048_04
)

SERVIS_DISI_BAYRAKLAR = (
    "sik_bos",
    "gorsel_yok_sekilli",
    "gosterilemez_gorsel_sik_kirpimsiz",
    "sik_okunamadi",
)
SINYALLER: tuple[str, ...] = (
    "anahtar_iki_bagimsiz_okuma_505_505_hucre",
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
    "kesik_duzeltme",
)

# ithal.kayit_uret ciktisi (28 Eyl 2026, metin.json duzeltilmis); konu id eski
# satirdan alinir (ayni konu). Ters egik cizgi kacislari JSON'a aittir.
YENI_JSON = r"""
{
 "konu_kodu": "MAT-ACL24MG-B08-K01",
 "subject_area": "MATEMATIK",
 "exam_type": "TYT",
 "question_text": "\u015eekil 1'de bir kenar uzunlu\u011fu x birim olan bir kare g\u00f6sterilmi\u015ftir. Karenin bir kenar\u0131 a birim k\u00fc\u00e7\u00fclt\u00fcl\u00fcp di\u011fer kenar\u0131 b birim b\u00fcy\u00fct\u00fclerek \u015eekil 2'de g\u00f6sterilen mavi renkli dikd\u00f6rtgen olu\u015fturuluyor.\nOlu\u015fan EBFK dikd\u00f6rtgeninin alan\u0131 x^2 \u2212 4x \u2212 21 birimkare oldu\u011funa g\u00f6re, a + b toplam\u0131 ka\u00e7t\u0131r?",
 "secenekler": {
  "A": "7",
  "B": "8",
  "C": "9",
  "D": "10",
  "E": "11"
 },
 "correct_answer": "D",
 "question_image_url": "/static/crops/ACL24MG/ACL24MG-T081_02.png",
 "explanation": null,
 "source_page": 183,
 "word_count": 46,
 "unique_word_count": 37,
 "average_word_length": 5.369565217391305,
 "readability_score": 78.9,
 "morphology_complexity": 0.35,
 "bloom_level": 3,
 "bloom_category": "application",
 "osym_year": null,
 "osym_format_compliant": false,
 "pipeline_metadata": {
  "kaynak": "acl24mg",
  "profil": "ACL24MG",
  "konu_kodu": "MAT-ACL24MG-B08-K01",
  "konu_eslesme_duzeyi": "konu",
  "konu_kaynagi": "icindekiler_ve_test_ust_bandi",
  "ders": "MATEMATIK",
  "test_no": 81,
  "sayfa_dosya_no": 183,
  "basili_sayfa": 183,
  "sutun": "L",
  "sutun_sira": 1,
  "soru_no_basili": 2,
  "soru_no_kaynagi": "basili",
  "birim_kodu": "ACL24MG-T081",
  "birim_ici_sira": 2,
  "bolum_kodu": "MAT-ACL24MG-B08",
  "bolum_adi": "\u00c7ARPANLARA AYIRMA",
  "konu_adi": "\u00c7arpanlara Ay\u0131rma",
  "test_bandi": "\u00c7arpanlara Ay\u0131rma",
  "kaynak_gorseli": "ACL24MG-T081_02.png",
  "bayraklar": [
   "okuyucu_diski_ortme"
  ],
  "cevap_kaynagi": "testin_basili_cevap_anahtari",
  "cevap_okuma_kanali": "iki_okuma+goz(5x)",
  "anahtar_dogrulamasi": "basili_anahtar_iki_okuma_505_505_hucre_ayni__piksel_glif_loo_430_431_uyumsuz_goz__glif_disi_12_test_goz_5x__hucre_sayisi_esittir_numara_capasi_505",
  "cikmis_soru": false,
  "cikmis_etiketi": null,
  "sinav": null,
  "sinav_yili": null,
  "sekil_var": true,
  "sikler_gorsel": false,
  "kaynak_kusuru": null,
  "okuyucu_diski_ortme": [
   [
    731,
    361
   ]
  ],
  "mukerrer_aday": null,
  "modern_kitap_ikizi": null,
  "db_hash_carpismasi": null,
  "diger_kaynak_cevap_farki": null,
  "diger_kaynak_sik_sirasi_farkli": null,
  "kirpim_kutusu": [
   24,
   640,
   352,
   898
  ],
  "gorsel_boyu": [
   328,
   258
  ],
  "kirpim_capa_kanali": "okuyucu_simgesi+kirmizi_basili_numara",
  "kirpim_koordinat_sistemi": "sayfa_karti_589_43_1331_1022_numara_capasindan",
  "gorsel_kaynagi": "tam_soru_kirpimi_okuyucu_diski_beyazlatilmis",
  "metin_kaynagi": "soru_kirpimi_gorsel_okuma_duzeltme kesik goz (grup_09 yerine)_tam_ikinci_okuma",
  "metin_tavani": "kaynak_1920x1080_sayfa_karti",
  "bloom_kaynagi": "kural:sayisal_sonuc",
  "morfoloji_kaynagi": "heuristik_zemberek_yok_sabit",
  "okunabilirlik_kaynagi": "atesman_turkish_readability_service",
  "cozum_dogrulamasi": "yapilmadi_urun_karari",
  "telif": "ACIL Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar.",
  "uretim": "FERNUS okuyucu ekran goruntusunden okuma hatti (kitap_hat). Cevaplar testin basili cevap anahtarindan iki bagimsiz gorsel okumayla alindi (505/505 hucre ayni; piksel glif LOO ucuncu kanal 430/431, 1 uyumsuz 5x goz teyidi; bolutlenemeyen 12 test 5x goz). Sorular cozulmedi. Kirpim kutulari okuyucu simgesi + kirmizi basili numara capasindan. Transkripsiyon ayri okuyucularla kirpimdan; on kayitli TAM ikinci okuma; anahtar gosterilmedi. Detay: veriseti/zkitap/cikti/MAT_ACIL_2024_TYT_KITAP1_YONTEM.md",
  "ithal_araci": "scripts/kitap/kitap_hat/ithal.py"
 }
}
"""
YENI = json.loads(YENI_JSON)
# Yeni satirin id'si: uuid5(NAMESPACE_OID, soru_hash) -- ithal / metin_olcum.soru_hash
# formulu (metin NFC + kucuk harf, sikler NFC, '|' ile birlesik, md5). Hash kodda
# yazili degil, metinden turetilir; beklenen id sabiti dogrulama icindir.
YENI_ID = "cec01743-d95c-5255-a280-dadfb16433c1"


def _soru_hash(metin: str, sec: dict[str, str]) -> str:
    nfc = lambda t: unicodedata.normalize("NFC", t)  # noqa: E731
    payload = "|".join([nfc(metin).lower()] + [nfc(sec.get(h, "")) for h in "ABCDE"])
    return hashlib.md5(payload.encode("utf-8"), usedforsecurity=False).hexdigest()


def _yeni_hash_ve_id() -> tuple[str, str]:
    h = _soru_hash(YENI["question_text"], YENI["secenekler"])
    i = str(uuid.uuid5(uuid.NAMESPACE_OID, h))
    if i != YENI_ID:
        raise RuntimeError(f"yeni satir id beklenen {YENI_ID} != turetilen {i}")
    return h, i


_QB = sa.text(
    """
    INSERT INTO question_bank (id, soru_hash, primary_topic_id, is_active, is_public, created_by,
        reviewed_by, created_at, updated_at, is_ai_generated, review_status, is_anchor)
    VALUES (:id, :soru_hash, :konu_id, FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE)
    """
)
_QC = sa.text(
    """
    INSERT INTO question_content (id, question_text, option_a, option_b, option_c, option_d,
        option_e, correct_answer, explanation, question_image_url, image_width, image_height)
    VALUES (:id, :question_text, :a, :b, :c, :d, :e, :correct_answer, NULL,
        :question_image_url, :image_width, :image_height)
    """
)
_QM = sa.text(
    """
    INSERT INTO question_metadata (id, bloom_level, bloom_category, exam_type, subject_area,
        grade_level, osym_format_compliant, osym_year, source_book, source_page,
        pipeline_metadata, morphology_complexity, word_count, unique_word_count,
        average_word_length, readability_score, pedagogical_status)
    VALUES (:id, :bloom_level, :bloom_category, :exam_type, :subject_area, :grade_level,
        :osym_format_compliant, :osym_year, :source_book, :source_page,
        CAST(:pipeline_metadata AS json), :morphology_complexity, :word_count,
        :unique_word_count, :average_word_length, :readability_score, 'PENDING')
    """
)
_QS = sa.text(
    """
    INSERT INTO question_statistics (id, difficulty_level, irt_based_difficulty,
        student_success_rate, difficulty_update_count, irt_discrimination, irt_difficulty,
        irt_guessing, irt_upper_asymptote, is_calibrated, calibration_sample_size,
        calibration_quality_score, times_asked, times_correct, times_wrong, times_skipped,
        average_response_time, median_response_time, exposure_rate, quality_score,
        quality_review_status)
    VALUES (:id, 'MEDIUM', 'medium', 0.5, 0, 1.0, 0.0, 0.2, 1.0, FALSE, 0, 0.0, 0, 0, 0, 0,
        0.0, 0.0, 0.0, 100.0, 'pending')
    """
)

# 0085 ile ayni kapi, tek satira uygulanir (SQL duz yazilir; test dort bayragi dogrular).
_HEDEF_SQL = """
SELECT qb.id
  FROM question_bank qb
  JOIN question_metadata qm ON qm.id = qb.id
  JOIN question_content qc ON qc.id = qb.id
 WHERE qb.id = :id
   AND qm.source_book = :kaynak
   AND qm.pipeline_metadata::jsonb ->> 'ithal_araci' = :arac
   AND qb.is_active IS NOT TRUE
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos')
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'gorsel_yok_sekilli')
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar')
            ? 'gosterilemez_gorsel_sik_kirpimsiz')
   AND NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_okunamadi')
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

_DURUM_SQL = sa.text(
    """
    SELECT qb.is_active, qb.review_status, qs.quality_review_status,
           qm.pipeline_metadata::jsonb ->> 'kaynak_kusuru', qb.primary_topic_id
      FROM question_bank qb
      JOIN question_metadata qm ON qm.id = qb.id
      LEFT JOIN question_statistics qs ON qs.id = qb.id
     WHERE qb.id = :id
    """
)


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0089] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))


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


def _gunluk_yaz(b, sid: str, islem: str, durum) -> None:
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, islem, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
            " onceki_quality_review_status, onceki_kaynak_kusuru)"
            " VALUES (:id, :islem, :akt, :rs, :qrs, :kusur)"
        ),
        {
            "id": sid,
            "islem": islem,
            "akt": durum[0] if durum else None,
            "rs": durum[1] if durum else None,
            "qrs": durum[2] if durum else None,
            "kusur": durum[3] if durum else None,
        },
    )


def _meta_birlestir(b, sid: str, ek: dict) -> None:
    b.execute(
        sa.text(
            "UPDATE question_metadata"
            " SET pipeline_metadata = (pipeline_metadata::jsonb || CAST(:ek AS jsonb))::json"
            " WHERE id = :id"
        ),
        {"id": sid, "ek": json.dumps(ek, ensure_ascii=True)},
    )


def _meta_anahtar_sil(b, sid: str, anahtarlar) -> None:
    for a in anahtarlar:
        b.execute(
            sa.text(
                "UPDATE question_metadata"
                " SET pipeline_metadata = (pipeline_metadata::jsonb - :a)::json"
                " WHERE id = :id"
            ),
            {"a": a, "id": sid},
        )


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0089] soru tablolari yok (taze DB?) -- atlandi")
        return
    eski = b.execute(_DURUM_SQL, {"id": ESKI_ID}).first()
    if eski is None:
        _log.info("[0089] eski satir %s yok (ithal yapilmamis DB) -- atlandi", ESKI_ID)
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("islem", sa.String(), nullable=False),
        sa.Column("onceki_is_active", sa.Boolean(), nullable=True),
        sa.Column("onceki_review_status", sa.String(), nullable=True),
        sa.Column("onceki_quality_review_status", sa.String(), nullable=True),
        sa.Column("onceki_kaynak_kusuru", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    yeni_hash, yeni_id = _yeni_hash_ve_id()
    # 1) yeni satir (yoksa): ithal ile ayni dort tablo, PASIF; konu id eski satirdan
    var = b.execute(
        sa.text("SELECT 1 FROM question_bank WHERE id = :id"), {"id": yeni_id}
    ).first()
    if var is None:
        s = YENI["secenekler"]
        gen, boy = YENI["pipeline_metadata"]["gorsel_boyu"]
        b.execute(_QB, {"id": yeni_id, "soru_hash": yeni_hash, "konu_id": eski[4]})
        b.execute(
            _QC,
            {
                "id": yeni_id,
                "question_text": YENI["question_text"],
                "a": s["A"],
                "b": s["B"],
                "c": s["C"],
                "d": s["D"],
                "e": s["E"],
                "correct_answer": YENI["correct_answer"],
                "question_image_url": YENI["question_image_url"],
                "image_width": gen,
                "image_height": boy,
            },
        )
        meta_alanlar = (
            "bloom_level",
            "bloom_category",
            "exam_type",
            "subject_area",
            "osym_format_compliant",
            "osym_year",
            "source_page",
            "morphology_complexity",
            "word_count",
            "unique_word_count",
            "average_word_length",
            "readability_score",
        )
        b.execute(
            _QM,
            {
                "id": yeni_id,
                **{k: YENI[k] for k in meta_alanlar},
                "grade_level": 9,
                "source_book": KAYNAK,
                "pipeline_metadata": json.dumps(
                    YENI["pipeline_metadata"], ensure_ascii=True
                ),
            },
        )
        b.execute(_QS, {"id": yeni_id})
        _log.info("[0089] yeni satir eklendi: %s", yeni_id)
    _gunluk_yaz(b, yeni_id, "yeni_beta", b.execute(_DURUM_SQL, {"id": yeni_id}).first())
    # 2) eski satir: pasif kalir, yerine gecen id'yi tasir
    _gunluk_yaz(b, ESKI_ID, "eski_pasif", eski)
    b.execute(
        sa.text(
            "UPDATE question_bank SET is_active = FALSE, updated_at = now() WHERE id = :id"
        ),
        {"id": ESKI_ID},
    )
    _meta_birlestir(
        b,
        ESKI_ID,
        {
            "kesik_duzeltme_yerine": yeni_id,
            "kesik_duzeltme": ACIKLAMA,
            "kesik_duzeltme_tarihi": TARIH,
        },
    )
    # 3) yeni satir beta kapisi (0085 kurali)
    hedef = b.execute(
        sa.text(_HEDEF_SQL),
        {"id": yeni_id, "kaynak": KAYNAK, "arac": ITHAL_ARACI, "isaret": ORTME_ISARETI},
    ).first()
    if hedef is not None:
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = TRUE, review_status = 'APPROVED',"
                " updated_at = now() WHERE id = :id"
            ),
            {"id": yeni_id},
        )
        b.execute(
            sa.text(
                "UPDATE question_statistics SET quality_review_status = 'auto_judged_high'"
                " WHERE id = :id"
            ),
            {"id": yeni_id},
        )
        _meta_birlestir(
            b,
            yeni_id,
            {
                "consensus_2signal_run": True,
                "konsensus_sinyalleri": list(SINYALLER),
                "onay_turu": "toplu_beta_sahibi",
                "bireysel_denetim_yapildi": False,
                "kesik_duzeltme": ACIKLAMA,
            },
        )
        _log.info("[0089] beta kapisi: %s acildi", yeni_id)
    else:
        _log.info("[0089] beta kapisi: %s kapidan GECMEDI, pasif kaldi", yeni_id)
    # 4) kesik notu kalkan satirlar: kaynak_kusuru null, bayrak kaldirilir
    for sid in KUSUR_NOTU_KALKAN:
        durum = b.execute(_DURUM_SQL, {"id": sid}).first()
        if durum is None:
            continue
        _gunluk_yaz(b, sid, "kusur_notu", durum)
        b.execute(
            sa.text(
                "UPDATE question_metadata SET pipeline_metadata = ("
                " jsonb_set(pipeline_metadata::jsonb, '{kaynak_kusuru}', 'null'::jsonb)"
                " || jsonb_build_object('bayraklar', COALESCE((SELECT jsonb_agg(x)"
                "      FROM jsonb_array_elements_text(pipeline_metadata::jsonb -> 'bayraklar') AS x"
                "     WHERE x <> 'kaynak_kusuru'), '[]'::jsonb),"
                "    'kesik_duzeltme', CAST(:acik AS text)))::json"
                " WHERE id = :id"
            ),
            {"id": sid, "acik": ACIKLAMA},
        )
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0089] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(
            "SELECT id, islem, onceki_is_active, onceki_review_status,"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
            f" onceki_quality_review_status, onceki_kaynak_kusuru FROM {GUNLUK}"
        )
    ).fetchall()
    for sid, islem, akt, rs, qrs, kusur in kayitlar:
        if islem == "yeni_beta":
            # eklenen satir silinmez; ithal sonrasi haline (PASIF) doner
            b.execute(
                sa.text(
                    "UPDATE question_bank SET is_active = FALSE, review_status = 'PENDING',"
                    " updated_at = now() WHERE id = :id"
                ),
                {"id": sid},
            )
            b.execute(
                sa.text(
                    "UPDATE question_statistics SET quality_review_status = 'pending'"
                    " WHERE id = :id"
                ),
                {"id": sid},
            )
            _meta_anahtar_sil(b, sid, EK_ANAHTARLAR)
        elif islem == "eski_pasif":
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
            _meta_anahtar_sil(
                b,
                sid,
                ("kesik_duzeltme_yerine", "kesik_duzeltme", "kesik_duzeltme_tarihi"),
            )
        else:  # kusur_notu
            b.execute(
                sa.text(
                    "UPDATE question_metadata SET pipeline_metadata = ("
                    " jsonb_set(pipeline_metadata::jsonb, '{kaynak_kusuru}',"
                    "   to_jsonb(CAST(:kusur AS text)))"
                    " || jsonb_build_object('bayraklar',"
                    "      (pipeline_metadata::jsonb -> 'bayraklar') || '[\"kaynak_kusuru\"]'::jsonb)"
                    " )::json WHERE id = :id"
                ),
                {"id": sid, "kusur": kusur},
            )
            _meta_anahtar_sil(b, sid, ("kesik_duzeltme",))
    _log.info("[0089] geri alindi: %s kayit", len(kayitlar))
    b.execute(sa.text(_SAYAC_SQL))
    _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
