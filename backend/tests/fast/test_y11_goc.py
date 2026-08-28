"""Y11 göç dönüşümü — `kaynak_satiri_donustur` bekçisi (FAZ B, 20 Ağu 2026).

Bu dosya `backend/scripts/quality/y11_goc.py` YAZILMADAN önce yazıldı ve
o modül yokken **kırmızı** düşer (RED hâli). Ölçtüğü şey tek bir saf
fonksiyondur: `kiro2_temp.question_bank`'ın (pre-split, 78 kolon) tek bir
satırını, canlı `kiro2`'nun 4-tablo split'ine ait dört satır sözlüğüne
çeviren dönüşüm.

NEDEN BU KADAR ÇOK BEKÇİ
------------------------
Göçün her kuralı, ya canlı DB'den ölçülmüş bir kanona ya da bu depoda
bedeli ödenmiş bir derse dayanıyor. Sessizce ihlal edilebilen kuralların
listesi (hepsi ölçüldü):

* `review_status` **lowercase 'approved'** — canlı 36.967/36.967 böyle, ama
  hedef kolonun `server_default`'ı `'APPROVED'`. Kolonu boş bırakmak
  sürükleme yazar ve hiçbir kısıt bunu durdurmaz (varchar, CHECK yok).
* `bloom_category` **varchar** — yanlış değer INSERT'i DÜŞÜRMEZ, tüketici
  `empirical_irt_calibrator.BLOOM_A_MAP`'te bulamayınca sessizce `a=1.05`
  yapar. Kaynaktaki Türkçe etiketler ("kavrama", "sentez") haritada YOK.
* `correct_answer` bir DEĞER değil, şık listesine **konumsal referanstır**
  (`L-s232-cevap-harfi-sik-listesi-olmadan-anlamsizdir`). Şıkları normalize
  etmek/yeniden sıralamak anahtarı sessizce yanlış cevaba bağlar.
* 17 kuralın adıyla andığı kolon sayısı 26; hedefte **NOT NULL + defaultsuz**
  23 kolon daha var. Kurallara harfiyen uyan bir uygulama onları atlar ve
  her INSERT `NotNullViolationError` ile düşer. Bu yüzden burada geçiş
  (`pass-through`) da ayrıca çivilenmiştir.
* Üç yavru tablonun PK'sı `question_bank.id` ile **AYNI** olmalı
  (`L-s230-yavru-tablonun-pk-si-id`); ayrı bir `question_id` kolonu YOKTUR.

Kardeş bekçi: `backend/tests/fast/test_y11_dedup.py` (kimlik/mükerrer katmanı).
Dedup KÜME düzeyi bir iştir; bu saf satır-dönüştürücünün işi DEĞİLDİR.
"""

from __future__ import annotations

import copy
from datetime import UTC, datetime

import pytest

from services.empirical_irt_calibrator import BLOOM_A_MAP

try:
    from scripts.quality.y11_goc import kaynak_satiri_donustur as _donustur
except ImportError as _hata:  # FAZ B: modül henüz YAZILMADI -> RED
    _IMPORT_HATASI: ImportError | None = _hata
    _donustur = None
else:
    _IMPORT_HATASI = None


def kaynak_satiri_donustur(satir, *, topic_kod_haritasi, damga):
    """İnce sarmalayıcı — modül yokken GERÇEK `ImportError`'ı test gövdesinde fırlatır.

    Modül-düzeyi çıplak import, tüm dosyayı tek bir *collection error*'a
    çevirirdi; o zaman "hangi test hangi sebeple düştü" ölçülemezdi.
    Sarmalayıcı ayrıca **imza sözleşmesini** de sabitler: gerçek fonksiyonun
    anahtar-kelime adları farklıysa `TypeError` yüzeye çıkar.
    """
    if _IMPORT_HATASI is not None:
        raise _IMPORT_HATASI
    return _donustur(satir, topic_kod_haritasi=topic_kod_haritasi, damga=damga)


# ---------------------------------------------------------------------------
# HEDEF ŞEMA — canlı `kiro2` information_schema'sından ölçüldü (20 Ağu 2026)
# ---------------------------------------------------------------------------

HEDEF_BANK = frozenset(
    {
        "id",
        "soru_hash",
        "primary_topic_id",
        "is_active",
        "is_public",
        "created_by",
        "reviewed_by",
        "created_at",
        "updated_at",
        "is_ai_generated",
        "review_status",
        "is_anchor",
    }
)

HEDEF_CONTENT = frozenset(
    {
        "id",
        "question_text",
        "question_html",
        "question_latex",
        "question_image_url",
        "image_ocr_text",
        "image_width",
        "image_height",
        "question_audio_url",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "option_e",
        "correct_answer",
        "explanation",
        "explanation_video_url",
        "alternative_solutions",
        "structured_explanation",
    }
)

HEDEF_METADATA = frozenset(
    {
        "id",
        "secondary_topics",
        "bloom_level",
        "bloom_category",
        "exam_type",
        "subject_area",
        "grade_level",
        "osym_format_compliant",
        "osym_year",
        "source_book",
        "source_page",
        "pipeline_metadata",
        "misconception_tags",
        "solution_steps",
        "similar_question_ids",
        "morphology_complexity",
        "word_count",
        "unique_word_count",
        "average_word_length",
        "readability_score",
        "pedagogical_status",
    }
)

HEDEF_STATISTICS = frozenset(
    {
        "id",
        "difficulty_level",
        "irt_based_difficulty",
        "student_success_rate",
        "last_difficulty_update",
        "difficulty_update_count",
        "irt_discrimination",
        "irt_difficulty",
        "irt_guessing",
        "irt_upper_asymptote",
        "is_calibrated",
        "calibration_sample_size",
        "last_calibration_date",
        "calibration_quality_score",
        "irt_a",
        "irt_b",
        "irt_c",
        "irt_calibrated",
        "irt_calibrated_at",
        "irt_n_responses",
        "irt_method",
        "is_calib_pool",
        "embedding",
        "times_asked",
        "times_correct",
        "times_wrong",
        "times_skipped",
        "average_response_time",
        "median_response_time",
        "exposure_rate",
        "last_used_date",
        "quality_score",
        "quality_review_status",
        "reviewed_at",
    }
)

# Kaynakta KARŞILIĞI OLMAYAN 5 kolon (kural 17 + kural 6).
HEDEF_OZEL = frozenset(
    {
        "is_ai_generated",
        "review_status",
        "is_anchor",
        "structured_explanation",
        "pedagogical_status",
    }
)

# Kural 1: `embedding` çıktıya HİÇ konmaz (kaynak vector(768) / hedef vector(1536)).
BEKLENEN_STATISTICS = HEDEF_STATISTICS - {"embedding"}

# ---------------------------------------------------------------------------
# TOPIC HARİTASI — iki DB'den ölçüldü (20 Ağu 2026)
# KIM/FIZ/GEN canlıda FARKLI id taşıyor; KIM.DEN/KIM.ASI BİREBİR aynı.
# ---------------------------------------------------------------------------

KAYNAK_TOPIC = {
    "KIM": "dcd3211c-58e3-5cf9-bc37-9a33daa1a0c4",
    "FIZ": "93140aa9-15ad-54fe-9d09-afc2c9626c93",
    "GEN": "0c6a66f8-b007-5b88-9d0b-cc49fba3d7b8",
    "KIM.DEN": "6ef2025f-a1e3-428e-9dfd-1c4c62cbcb37",
    "KIM.ASI": "b70e7141-a707-4354-9158-647518c0f2d7",
}

CANLI_TOPIC = {
    "KIM": "72e79276-4795-424c-a262-0edf9a77a23f",
    "FIZ": "c6c72669-267e-47ce-a3d2-8392de050bc7",
    "GEN": "9928457b-b653-46d4-8bc1-a0937b1d9836",
    "KIM.DEN": "6ef2025f-a1e3-428e-9dfd-1c4c62cbcb37",
    "KIM.ASI": "b70e7141-a707-4354-9158-647518c0f2d7",
}

DAMGA = "y11-kimya-2026-08"

# Kaynak bloom_level -> kaynaktaki TÜRKÇE etiket (ölçüldü: 4.419 satırın dağılımı)
KAYNAK_BLOOM_ETIKETI = {
    1: "bilgi",
    2: "kavrama",
    3: "uygulama",
    4: "analiz",
    5: "sentez",
    6: "degerlendirme",
}

# Kural 8: seviye -> canlı kanon (lowercase İngilizce).
# DİKKAT: kaynak ESKİ Bloom (5=sentez, 6=değerlendirme); kullanıcı kararı
# SAYIYI kanon kabul eder, kelimeyi değil.
BEKLENEN_BLOOM = {
    1: "knowledge",
    2: "comprehension",
    3: "application",
    4: "analysis",
    5: "evaluation",
    6: "creation",
}

APOTEMI = "Apotemi 2024 Ayt Kimya Soru Bankasi"
DIGER_KITAP = "Bilgi Sarmal 2024 Ayt Kimya Sopru Bankasi"

PAGE_GORSEL = (
    "/static/crops/Apotemi_2024_Ayt_Kimya_Soru_Bankasi/"
    "Apotemi_2024_Ayt_Kimya_Soru_Bankasi_p0018_PAGE.png"
)
APOTEMI_CROP = (
    "/static/crops/Apotemi_2024_Ayt_Kimya_Soru_Bankasi/"
    "Apotemi_2024_Ayt_Kimya_Soru_Bankasi_p0094_q02.png"
)
TEMIZ_CROP = (
    "/static/crops/Bilgi_Sarmal_2024_Ayt_Kimya_Sopru_Bankasi/"
    "Bilgi_Sarmal_2024_Ayt_Kimya_Sopru_Bankasi_p0015_q06.png"
)


# ---------------------------------------------------------------------------
# FIXTURE — gerçek bir kaynak satırı (78 kolon + JOIN'den gelen `topic_code`)
# ---------------------------------------------------------------------------


def kaynak_satiri(**degisiklikler) -> dict:
    """78 kaynak kolonu + `topic_code` taşıyan taze bir sözlük üretir.

    Değerler bilerek **varsayılan-DIŞI** seçildi: geçişi (`pass-through`)
    ölçen bir assert, kaynak değeri hedefin varsayılanıyla aynıysa hiçbir şey
    ölçmez. Örn. `times_asked=7` olmasaydı kural 9 (sayaçları sıfırla)
    çivilenemezdi; `is_public=False` olmasaydı kural 4 çivilenemezdi.

    AYNI GEREKÇENİN İKİNCİ YÜZÜ — **hiçbir iki alan aynı değeri taşımaz**.
    Kaynakta altı IRT çifti (`irt_a`/`irt_discrimination`,
    `irt_b`/`irt_difficulty`, `irt_c`/`irt_guessing`,
    `irt_calibrated`/`is_calibrated`, `irt_n_responses`/
    `calibration_sample_size`, `irt_calibrated_at`/`last_calibration_date`)
    birbirine karıştırılmaya açık. Fixture onlara AYNI değeri verirse her
    çapraz kablolama bir no-op gibi görünür; ölçüldü: `irt_a` kaynakta
    19.360/19.360 NULL, `irt_discrimination` ise 19.360/19.360 DOLU — yani
    ikisini eşit tutmak gerçek dağılıma da aykırıydı. Tüketici
    `services/irt_service_3pl.py:104,147` `irt_a`'yı okuyor.

    Aynı sebeple `None` taşıyan geçiş alanı BIRAKILMADI: `assert cikti == None`
    bir mutasyonu (alanı koşulsuz `None`'a çekmek) öldüremez.
    """
    satir: dict = {
        # --- question_bank tarafı (9 kaynak kolonu) ---
        "id": "3f1a2b7c-1111-4111-8111-aaaaaaaaaaa1",
        "soru_hash": "0123456789abcdef0123456789abcdef",
        "primary_topic_id": KAYNAK_TOPIC["KIM"],
        "is_active": False,
        "is_public": False,
        "created_by": "eski-editor-42",
        # Kaynakta 19.360/19.360 NULL; DOLU verilmesi bilinçli — kural 3'ün
        # kardeşi `reviewed_by` de None basmalı ve bu ancak kaynak doluyken
        # ölçülebilir. Hedefte FK var: question_bank_reviewed_by_fkey ->
        # users(id) ON DELETE CASCADE (canlı `users` 3 satır, bu kimlik YOK).
        "reviewed_by": "eski-reviewer-7",
        "created_at": datetime(2026, 5, 12, 6, 31, 43, tzinfo=UTC),
        "updated_at": datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
        # --- question_content tarafı (17 kaynak kolonu) ---
        "question_text": "Asagidakilerden hangisi bir asit-baz tepkimesidir?",
        "question_html": "<p>Asagidakilerden hangisi bir asit-baz tepkimesidir?</p>",
        "question_latex": r"\ce{HCl + NaOH -> NaCl + H2O}",
        "question_image_url": TEMIZ_CROP,
        "image_ocr_text": "HCl + NaOH tepkimesi",
        "image_width": 620,
        "image_height": 410,
        "question_audio_url": "/static/audio/kim_p0015_q06.mp3",
        "option_a": "HCl + NaOH",
        "option_b": "H2 + O2",
        "option_c": "NaCl + AgNO3",
        "option_d": "CH4 + O2",
        "option_e": "Fe + CuSO4",
        "correct_answer": "A",
        "explanation": "Asit ile bazin tuz ve su vermesi notrallesmedir.",
        "explanation_video_url": "https://video.ornek/kim-notrallesme",
        "alternative_solutions": ["Iyonik denklem uzerinden de cozulur."],
        # --- question_metadata tarafı (19 kaynak kolonu) ---
        "secondary_topics": ["KIM.ASI"],
        "bloom_level": 2,
        "bloom_category": KAYNAK_BLOOM_ETIKETI[2],
        "exam_type": "AYT",
        "subject_area": "KIMYA",
        "grade_level": 12,
        "osym_format_compliant": True,
        "osym_year": 2019,
        "source_book": DIGER_KITAP,
        "source_page": 15,
        "pipeline_metadata": {
            "source": "kiro2_batch_v4.14e",
            "blind_seen": True,
            "book_key_match": {"status": "agree", "qbank_answer": "A"},
        },
        "misconception_tags": ["tuz-olusumunu-yanlis-eslestirme"],
        "solution_steps": ["1) Asit ve bazi belirle", "2) Urunleri yaz"],
        "similar_question_ids": ["3f1a2b7c-1111-4111-8111-aaaaaaaaaaa2"],
        "morphology_complexity": 0.42,
        "word_count": 12,
        "unique_word_count": 11,
        "average_word_length": 5.8,
        "readability_score": 61.3,
        # --- question_statistics tarafı (33 kaynak kolonu) ---
        "difficulty_level": "MEDIUM",
        "irt_based_difficulty": "medium",
        "student_success_rate": 0.42,
        "last_difficulty_update": datetime(2026, 6, 1, 9, 0, 0, tzinfo=UTC),
        "difficulty_update_count": 3,
        # ALTI IKIZ CIFT — her biri AYRISTIRILDI (bkz. fixture docstring'i).
        # Eşit tutulsalardı `irt_a = satir["irt_discrimination"]` gibi bir
        # çapraz kablolama hiçbir testi düşürmezdi (ölçüldü: 101/101 PASS).
        "irt_discrimination": 1.35,
        "irt_difficulty": -0.4,
        "irt_guessing": 0.2,
        "irt_upper_asymptote": 0.98,
        "is_calibrated": True,
        "calibration_sample_size": 120,
        "last_calibration_date": datetime(2026, 6, 2, 10, 0, 0, tzinfo=UTC),
        "calibration_quality_score": 0.77,
        "irt_a": 0.77,
        "irt_b": 1.9,
        "irt_c": 0.05,
        "irt_calibrated": False,
        "irt_calibrated_at": datetime(2026, 6, 3, 11, 30, 0, tzinfo=UTC),
        "irt_n_responses": 31,
        "irt_method": "empirical",
        # Kaynakta TRUE yalnız 136/19.360 satırda; tüketici api/admin.py:253
        # `SUM(CASE WHEN qs.is_calib_pool THEN 1 ELSE 0 END)`. Koşulsuz True
        # basmak tüm partiyi kalibrasyon havuzuna sokar.
        "is_calib_pool": False,
        "embedding": [0.01] * 768,
        "times_asked": 7,
        "times_correct": 3,
        "times_wrong": 4,
        "times_skipped": 1,
        "average_response_time": 48.5,
        "median_response_time": 44.0,
        "exposure_rate": 0.03,
        "last_used_date": datetime(2026, 7, 1, 8, 0, 0, tzinfo=UTC),
        "quality_score": 0.85,
        "quality_review_status": "auto_judged_high",
        "reviewed_at": datetime(2026, 7, 4, 15, 45, 0, tzinfo=UTC),
        # --- JOIN'den gelen ---
        "topic_code": "KIM",
    }
    bilinmeyen = set(degisiklikler) - set(satir)
    if bilinmeyen:
        raise AssertionError(
            f"fixture'da olmayan alan ezilmeye calisildi: {sorted(bilinmeyen)}"
        )
    satir.update(degisiklikler)
    return satir


def donustur(**degisiklikler) -> dict[str, dict]:
    """Fixture + varsayılan harita/damga ile tek çağrılık kısayol."""
    return kaynak_satiri_donustur(
        kaynak_satiri(**degisiklikler),
        topic_kod_haritasi=dict(CANLI_TOPIC),
        damga=DAMGA,
    )


# ---------------------------------------------------------------------------
# YAPI ve KOLON TAMLIĞI — tek testte çok sayıda sessiz kusuru yakalar
# ---------------------------------------------------------------------------


def test_dort_hedef_tablo_dondurulur():
    cikti = donustur()
    assert set(cikti) == {
        "question_bank",
        "question_content",
        "question_metadata",
        "question_statistics",
    }


def test_question_bank_kolon_kumesi_birebir():
    assert set(donustur()["question_bank"]) == set(HEDEF_BANK)


def test_question_content_kolon_kumesi_birebir():
    assert set(donustur()["question_content"]) == set(HEDEF_CONTENT)


def test_question_metadata_kolon_kumesi_birebir():
    assert set(donustur()["question_metadata"]) == set(HEDEF_METADATA)


def test_question_statistics_kolon_kumesi_embedding_haric_birebir():
    """Eksik kolon `NotNullViolation`, FAZLA kolon `CompileError` üretir.

    İkisi de INSERT anında patlar; burada satır bile yazılmadan yakalanır.
    """
    assert set(donustur()["question_statistics"]) == set(BEKLENEN_STATISTICS)


def test_kolon_muhasebesi_78_kaynak_arti_5_hedef_ozel():
    """Ölçüm ALETİNİ doğrula: fixture gerçekten 78 kaynak kolonu taşıyor mu?

    Kontrol kolu olmadan yukarıdaki dört küme testi "hedef şemayı doğru
    yazdım" demekten öteye gitmez.
    """
    satir = kaynak_satiri()
    kaynak_kolonlari = set(satir) - {"topic_code"}
    beklenen_kaynak = (
        HEDEF_BANK | HEDEF_CONTENT | HEDEF_METADATA | HEDEF_STATISTICS
    ) - HEDEF_OZEL
    assert len(beklenen_kaynak) == 78
    assert kaynak_kolonlari == beklenen_kaynak

    cikti = donustur()
    uretilen = set().union(*(set(d) for d in cikti.values()))
    # 83 distinct hedef kolon - `embedding` = 82
    assert len(uretilen) == 82
    assert uretilen == (beklenen_kaynak | HEDEF_OZEL) - {"embedding"}


# Kaynakta birbirine karıştırılmaya açık ikiz alanlar. Fixture'ın onlara
# FARKLI değer vermesi bir ÖLÇÜM ALETİ özelliğidir, süs değil.
IKIZ_ALANLAR = [
    ("irt_a", "irt_discrimination"),
    ("irt_b", "irt_difficulty"),
    ("irt_c", "irt_guessing"),
    ("irt_calibrated", "is_calibrated"),
    ("irt_n_responses", "calibration_sample_size"),
    ("irt_calibrated_at", "last_calibration_date"),
]


@pytest.mark.parametrize("sol,sag", IKIZ_ALANLAR)
def test_fixture_ikiz_alanlari_ayristirir(sol, sag):
    """ÖLÇÜM ALETİNİ doğrula — fixture ayırt edici mi?

    Bu testin yokluğunda fixture'ı "sadeleştirip" ikizlere aynı değeri
    vermek hiçbir testi düşürmezdi, ama geçiş testlerinin çapraz-kablolama
    duyarlılığını SESSİZCE sıfırlardı. Ölçüldü: altı çift eşitken
    `irt_a = satir["irt_discrimination"]` mutasyonu 101/101 PASS alıyordu.

    Tüketici: `services/irt_service_3pl.py:104,147` → `q.get("irt_a", 1.0)`
    (CAT motoru `irt_a`'ya bakıyor, `irt_discrimination`'a değil).
    """
    satir = kaynak_satiri()
    assert satir[sol] != satir[sag], (
        f"fixture'da {sol} == {sag}: bu ikisi arasindaki capraz kablolama "
        "hicbir testle olculemez hale gelir"
    )


def test_embedding_hicbir_sozlukte_yok():
    """Kural 1. `None` olması YETMEZ — anahtarın kendisi bulunmamalı.

    KAPSANDI: `test_question_statistics_kolon_kumesi_embedding_haric_birebir`
    ve `test_kolon_muhasebesi_...` (ikisi de TAM küme eşitliği iddia eder).
    Ölçüldü — `embedding` sızdıran mutasyon üçünü birden düşürüyor. Bu test
    kuralın GEREKÇESİNİ (vector(768) vs vector(1536)) taşıdığı için tutuldu;
    yeni test yazarken ÖRNEK ALINMAMALI.

    Kaynak vector(768), hedef vector(1536). Anahtar `None` değeriyle bile
    konsa INSERT'e girer ve boyut uyuşmazlığı üretir; hedef kolon nullable
    olduğu için ATLAMAK güvenlidir.
    """
    cikti = donustur()
    for tablo, sozluk in cikti.items():
        assert "embedding" not in sozluk, f"{tablo} sozlugunde embedding var"


def test_topic_code_cikti_kolonu_degildir():
    """`topic_code` JOIN'den gelir, hedefte KOLON DEĞİLDİR.

    KAPSANDI: `test_question_bank_kolon_kumesi_birebir` +
    `test_kolon_muhasebesi_...`. Ölçüldü — `topic_code` sızdıran mutasyon
    üçünü birden düşürüyor; bu testi TEK BAŞINA öldüren mutasyon YOK.
    Kuralın adını taşıdığı için tutuldu, örnek alınmamalı.
    """
    cikti = donustur()
    for tablo, sozluk in cikti.items():
        assert "topic_code" not in sozluk, f"{tablo} sozlugunde topic_code sizdi"


def test_id_dort_sozlukte_de_ayni():
    """Üç yavru tablonun PK'sı `question_bank.id`'nin KENDİSİ.

    Ayrı bir `question_id` kolonu YOKTUR; JOIN anahtarı `qc.id = qb.id`.
    Farklı id üretmek 4-tablo parity bekçisini kırar.
    """
    cikti = donustur()
    idler = {tablo: sozluk["id"] for tablo, sozluk in cikti.items()}
    assert len(set(idler.values())) == 1, idler
    assert idler["question_bank"] == kaynak_satiri()["id"]


# ---------------------------------------------------------------------------
# KURAL 2 — topic remap KOD üzerinden, sessiz varsayılan YOK
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kod,degisir_mi",
    [
        ("KIM", True),  # 852 soru — canlıda v4 id
        ("FIZ", True),  # 12 soru
        ("GEN", True),  # 1 soru
        ("KIM.DEN", False),  # 1361 soru — id BİREBİR aynı
        ("KIM.ASI", False),  # 507 soru
    ],
)
def test_topic_remap_kod_uzerinden(kod, degisir_mi):
    """Hem DEĞİŞEN hem DEĞİŞMEYEN kod ölçülür.

    Yalnız değişenle test etmek "id eşitliği tesadüfen tutuyor" hâlini
    göremez; yalnız değişmeyenle test etmek remap'in hiç çalışmadığı hâli
    göremez.
    """
    cikti = donustur(topic_code=kod, primary_topic_id=KAYNAK_TOPIC[kod])
    assert cikti["question_bank"]["primary_topic_id"] == CANLI_TOPIC[kod]
    assert (CANLI_TOPIC[kod] != KAYNAK_TOPIC[kod]) is degisir_mi


def test_kaynak_topic_id_asla_gecirilmez():
    """Kaynağın id'si canlıda YOK — geçirmek FK ihlali üretir.

    KAPSANDI: `test_topic_remap_kod_uzerinden` (o zaten `== CANLI_TOPIC[kod]`
    diyor ve `CANLI_TOPIC['KIM'] != KAYNAK_TOPIC['KIM']` ölçüldü). Kaynak
    id'yi geçiren mutasyon üç testi birden düşürüyor. FK gerekçesini
    taşıdığı için tutuldu, örnek alınmamalı.
    """
    cikti = donustur(topic_code="KIM", primary_topic_id=KAYNAK_TOPIC["KIM"])
    assert cikti["question_bank"]["primary_topic_id"] != KAYNAK_TOPIC["KIM"]


def test_bilinmeyen_topic_kodu_gurultulu_hata():
    """Yanlış-sıfır tek kabul edilemez hata türü: eksik kod SESSİZ geçmemeli.

    Sessiz varsayılan (`None`, kaynak id'yi geçirme, ilk konuya bağlama)
    yerine hata; eksik konuyu kopyalamak da YASAK
    (`topic_hierarchy_code_key` UNIQUE ihlali).

    `pytest.raises` BİLEREK dar (`ValueError`): `(KeyError, ValueError)`
    kabul edilseydi, açık `raise` bloğunu tamamen silmek de testi geçerdi —
    `topic_kod_haritasi[topic_kodu]` zaten çıplak `KeyError` atıyor ve
    `str(KeyError)` de kodu içeriyor (ölçüldü: bekçiyi `if False:` yapmak
    101/101 PASS veriyordu). Ölçülen şey artık YOL GÖSTERİCİ mesajın kendisi.
    """
    with pytest.raises(ValueError) as hata:
        donustur(topic_code="KIM.YOK.OLAN")
    assert "KIM.YOK.OLAN" in str(hata.value)
    assert "haritada YOK" in str(hata.value)


def test_topic_code_alani_eksikse_gurultulu_hata():
    """Eksik JOIN alanı: `_zorunlu` bekçisi ADIYLA bildirmeli, çıplak
    `KeyError` ile değil (`.get()`'e çevrilirse hiç hata olmazdı)."""
    satir = kaynak_satiri()
    del satir["topic_code"]
    with pytest.raises(ValueError) as hata:
        kaynak_satiri_donustur(satir, topic_kod_haritasi=dict(CANLI_TOPIC), damga=DAMGA)
    assert "topic_code" in str(hata.value)


# ---------------------------------------------------------------------------
# KURAL 3/4/5/6 — question_bank'ın açıkça yazılan alanları
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("alan", ["created_by", "reviewed_by"])
def test_kullanici_kimlikleri_none_basilir(alan):
    """Kural 3 ve KARDEŞİ. Kaynak İKİSİNİ DE dolu verir; geçirilirse yetim FK.

    `reviewed_by` 17 kuralın anmadığı ama aynı FK'ya bağlı kolon:
    `question_bank_reviewed_by_fkey -> users(id) ON DELETE CASCADE`
    (canlı şemadan ölçüldü; canlı `users` 3 satır, bu kimlikler YOK).
    Yalnız `created_by` test edilseydi `reviewed_by`'a kaynağın kimliğini
    geçirmek 101/101 PASS verirdi — ölçüldü.
    """
    cikti = donustur(created_by="eski-editor-42", reviewed_by="eski-reviewer-7")
    assert cikti["question_bank"][alan] is None


def test_is_public_acikca_true():
    """Kural 4 gerçek bir DÖNÜŞÜM, geçiş değil: kaynak 4.419/4.419 FALSE,
    canlı kanon 36.967/36.967 TRUE."""
    cikti = donustur(is_public=False)
    assert cikti["question_bank"]["is_public"] is True


def test_is_active_acikca_true():
    """Kural 5. `server_default` var ama ORM default False (S225 dersi):
    varsayılana bırakmak satırı kapının DIŞINDA bırakırdı."""
    cikti = donustur(is_active=False)
    assert cikti["question_bank"]["is_active"] is True


def test_review_status_kucuk_harf_approved():
    """Kural 6. Canlı kanon 36.967/36.967 **'approved'**; hedef kolonun
    `server_default`'ı ise `'APPROVED'`. Kolonu yazmamak sürükleme üretir
    ve varchar olduğu için hiçbir CHECK bunu durdurmaz."""
    deger = donustur()["question_bank"]["review_status"]
    assert deger == "approved"
    assert deger != "APPROVED"


# ---------------------------------------------------------------------------
# KURAL 7 — quality_review_status
# ---------------------------------------------------------------------------


def test_quality_review_status_pending_ve_statistics_tablosunda():
    """Kural 7. Kaynak 'auto_judged_high' gelir; hedefte 'pending' yazılır —
    böylece satırlar `mv_safe_for_beta` kapısına GİRMEZ."""
    cikti = donustur(quality_review_status="auto_judged_high")
    assert cikti["question_statistics"]["quality_review_status"] == "pending"
    assert "quality_review_status" not in cikti["question_bank"]


# ---------------------------------------------------------------------------
# KURAL 8 — bloom: ALTI seviyenin ALTISI
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seviye", sorted(BEKLENEN_BLOOM))
def test_bloom_kategorisi_alti_seviyede_de_eslenir(seviye):
    """Tek örnekle ölçmek "dilim" ölçer (L-s219). Kaynakta altı seviyenin
    altısı da var: 222 / 3931 / 237 / 2 / 10 / 17 satır."""
    cikti = donustur(bloom_level=seviye, bloom_category=KAYNAK_BLOOM_ETIKETI[seviye])
    assert cikti["question_metadata"]["bloom_category"] == BEKLENEN_BLOOM[seviye]


@pytest.mark.parametrize("seviye", sorted(BEKLENEN_BLOOM))
def test_bloom_level_kaynaktan_tasinir_turkce_etiket_sizmaz(seviye):
    """Sayı kanondur, kelime değil. Kaynağın Türkçe etiketi ("kavrama",
    "sentez") hedefe sızarsa tüketici onu haritada bulamaz."""
    cikti = donustur(bloom_level=seviye, bloom_category=KAYNAK_BLOOM_ETIKETI[seviye])
    assert cikti["question_metadata"]["bloom_level"] == seviye
    assert cikti["question_metadata"]["bloom_category"] != KAYNAK_BLOOM_ETIKETI[seviye]


@pytest.mark.parametrize("seviye", sorted(BEKLENEN_BLOOM))
def test_bloom_kategorisi_tuketicinin_haritasinda_bulunur(seviye):
    """ "Göç ettin mi" != "koruduun mu". Asıl risk INSERT'in düşmesi DEĞİL —
    `bloom_category` varchar, yanlış değer sessizce geçer ve
    `empirical_irt_calibrator` `a=1.05` fallback'ine düşer.

    Tüketici `str(...).upper()` uyguluyor (`:85`), o yüzden casing risksiz;
    ölçülen şey ANAHTARIN VARLIĞI.
    """
    kategori = donustur(
        bloom_level=seviye, bloom_category=KAYNAK_BLOOM_ETIKETI[seviye]
    )["question_metadata"]["bloom_category"]
    assert kategori.upper() in BLOOM_A_MAP, (
        f"'{kategori}' BLOOM_A_MAP'te YOK -> irt_a sessizce 1.05 fallback'ine "
        "duser (INSERT patlamaz, kusur GORUNMEZ)"
    )
    assert BLOOM_A_MAP[kategori.upper()] != 1.05


@pytest.mark.parametrize("seviye", [0, 7, None, "2", -1, True, False])
def test_bilinmeyen_bloom_seviyesi_gurultulu_hata(seviye):
    """Sessiz varsayılan ('knowledge' bas, atla, None yaz) YASAK.

    Hedefte `bloom_level` CHECK 1-6 var, ama `bloom_category` serbest —
    yani yanlış seviye ya INSERT'i düşürür ya da sessiz yanlış kalibrasyon
    üretir. İkisi de burada durdurulur.

    `True`/`False` AYIRT EDİCİ parametrelerdir: Python'da `True == 1` ve
    `hash(True) == hash(1)`, yani `bloom_seviyesi not in BLOOM_KATEGORI`
    TEK BAŞINA `True`'yu sessizce `'knowledge'` yapar. Modüldeki
    `isinstance(..., bool)` kolu tam bunu eler ve o kol bu iki parametre
    olmadan hiçbir mutasyonla çivilenemiyordu (ölçüldü: kolu silmek
    101/101 PASS veriyordu).

    Kaynak `bloom_level` `integer NOT NULL` (ölçüldü, 187.835/187.835 satır
    1..6) — yani sürücüden `bool` GELMEZ; risk elle kurulan sözlüklerde
    (yükleyici, yeniden deneme, test yardımcısı). Kol ucuz, bekçisi de ucuz.
    """
    with pytest.raises(ValueError):
        donustur(bloom_level=seviye)


# ---------------------------------------------------------------------------
# KURAL 9/10 — sayaçlar ve zaman damgaları
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "alan", ["times_asked", "times_correct", "times_wrong", "times_skipped"]
)
def test_sayaclar_sifirlanir(alan):
    """Kural 9. Kaynak SIFIR-DIŞI verilir; geçiş yapılırsa yeni havuza başka
    bir DB'nin gösterim istatistikleri taşınır ve `exposure_rate` yalan söyler.

    `== 0` TİP-KÖRDÜR: `False == 0` olduğu için sayaçları `False` ile
    doldurmak testi geçerdi (ölçüldü: 101/101 PASS). Hedef kolon `integer`;
    sonuç sürücüye bağlı — asyncpg `bool`'u int alt sınıfı sayıp 0 yazar,
    psycopg2 ise `column is of type integer but expression is of type
    boolean` ile DÜŞER. Tip de iddia edilir.
    """
    cikti = donustur(times_asked=7, times_correct=3, times_wrong=4, times_skipped=1)
    deger = cikti["question_statistics"][alan]
    assert deger == 0
    assert type(deger) is int, f"{alan} tipi {type(deger).__name__}, int bekleniyordu"


def test_zaman_damgalari_kaynaktan_tasinir():
    """Kural 10. `now()` basmak geri alma penceresini ve kaynak izini siler."""
    satir = kaynak_satiri()
    qb = donustur()["question_bank"]
    assert qb["created_at"] == satir["created_at"]
    assert qb["updated_at"] == satir["updated_at"]
    assert qb["created_at"] != qb["updated_at"], "fixture ayirt edici degil"


# ---------------------------------------------------------------------------
# KURAL 11 — damga
# ---------------------------------------------------------------------------


def test_damga_pipeline_metadata_ya_yazilir():
    """Kural 11. Geri alma kümesinin taşıyıcısı; damgasız satır geri alınamaz."""
    pm = donustur()["question_metadata"]["pipeline_metadata"]
    assert pm["y11_batch"] == DAMGA


def test_kaynak_pipeline_metadata_korunur():
    """Üzerine YAZMAK değil, EKLEMEK. `match_tier`/`book_key_match` gibi
    alanlar kapı filtresinin ve sonraki yargı turlarının girdisi."""
    pm = donustur()["question_metadata"]["pipeline_metadata"]
    assert pm["source"] == "kiro2_batch_v4.14e"
    assert pm["blind_seen"] is True
    assert pm["book_key_match"] == {"status": "agree", "qbank_answer": "A"}


def test_farkli_damga_farkli_deger_uretir():
    """Damganın gerçekten argümandan geldiğini çivile — sabit dize gömülürse
    tüm batch'ler aynı damgayı alır ve geri alma kümesi ayrıştırılamaz."""
    satir = kaynak_satiri()
    a = kaynak_satiri_donustur(
        dict(satir), topic_kod_haritasi=dict(CANLI_TOPIC), damga="y11-fizik-2026-09"
    )
    assert a["question_metadata"]["pipeline_metadata"]["y11_batch"] == (
        "y11-fizik-2026-09"
    )


# ---------------------------------------------------------------------------
# KURAL 12 — anahtar ve şıklar AYNI satırdan, SIRA BOZULMADAN
# ---------------------------------------------------------------------------


def test_anahtar_ve_siklar_ayni_satirdan_sirasi_bozulmadan():
    """`correct_answer` bir DEĞER değil, şık listesine KONUMSAL referans.

    Şıkları normalize/yeniden sırala + harfi olduğu gibi bırak = anahtar
    sessizce YANLIŞ cevaba bağlanır ve hiçbir kısıt bunu görmez.
    """
    satir = kaynak_satiri()
    qc = donustur()["question_content"]
    for harf in ("a", "b", "c", "d", "e"):
        assert qc[f"option_{harf}"] == satir[f"option_{harf}"]
    assert qc["correct_answer"] == satir["correct_answer"]
    assert qc["option_a"] == "HCl + NaOH"


@pytest.mark.parametrize("harf", ["b", " B ", "b\n"])
def test_anahtar_normalize_edilmez(harf):
    """Kural 12'nin yasak yarısı: anahtara `.strip().upper()` uygulamak da
    bir DÖNÜŞÜMDÜR ve bu fonksiyonun işi değildir.

    Fixture anahtarı zaten `'A'` (ve permütasyon testinde `'B'`/`'A'`)
    olduğu için her normalizasyon bir no-op gibi görünüyordu: `correct_answer`
    alanına `str(...).strip().upper()` eklemek 101/101 PASS veriyordu.

    Bugünkü fiili zarar 0 — kaynağın 187.835 satırında `correct_answer`
    yalnız A/B/C/D/E (ölçüldü). Ama kusur POTANSİYEL: Y12/başka ders
    partileri ve ileride eklenecek bir "temizleme" adımı için bu bekçi,
    sessiz bir harf kaymasının önündeki tek şey.
    """
    assert donustur(correct_answer=harf)["question_content"]["correct_answer"] == harf


def test_sik_sirasi_varyantlar_arasinda_yeniden_atanmaz():
    """Ayırt edici çift: aynı gövde, şıklar PERMÜTE, anahtarlar farklı.

    Bir uygulama şıkları sıralarsa iki satır aynı listeye düşer ama
    anahtarlar farklı kalır — biri kesin yanlış olur. Bu test o mutasyonu
    öldürür (`L-s232-cevap-harfi-sik-listesi-olmadan-anlamsizdir`).
    """
    duz = donustur(
        option_a="24",
        option_b="30",
        option_c="36",
        option_d="42",
        option_e="48",
        correct_answer="B",
    )["question_content"]
    ters = donustur(
        option_a="30",
        option_b="24",
        option_c="36",
        option_d="42",
        option_e="48",
        correct_answer="A",
    )["question_content"]

    assert [duz[f"option_{h}"] for h in "abcde"] == ["24", "30", "36", "42", "48"]
    assert [ters[f"option_{h}"] for h in "abcde"] == ["30", "24", "36", "42", "48"]
    assert duz["correct_answer"] == "B"
    assert ters["correct_answer"] == "A"
    # Iki satir da AYNI degeri (30) isaret ediyor -> siralama yapilsaydi
    # ikisinden biri mutlaka kayardi.
    assert duz["option_b"] == ters["option_a"] == "30"


# ---------------------------------------------------------------------------
# KURAL 13 — görsel: ÜÇ sınıf
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url,kitap,beklenen,gerekce",
    [
        (
            PAGE_GORSEL,
            DIGER_KITAP,
            None,
            "_PAGE %88,5 basili cevap anahtari sizdiriyor",
        ),
        (PAGE_GORSEL, APOTEMI, None, "_PAGE kurali kitaptan bagimsiz"),
        (APOTEMI_CROP, APOTEMI, None, "onceki sahibin pembe kalemi (112 crop)"),
        (TEMIZ_CROP, DIGER_KITAP, TEMIZ_CROP, "25 kitabin crop'u temiz (30/30)"),
        # Kaynakta KIMYA'nin 265 satirinda question_image_url NULL (olculdu).
        # Koruma satiri silinirse `"_PAGE" in None` -> TypeError ve goc o 265
        # satirda COKER; hicbir parametre bunu gormuyordu.
        (None, DIGER_KITAP, None, "NULL url cokmemeli (265 KIMYA satiri)"),
        # Kaynakta KIMYA'nin 6 satirinda source_book NULL (olculdu).
        (TEMIZ_CROP, None, TEMIZ_CROP, "NULL kitap sizintili sayilmaz (6 satir)"),
    ],
)
def test_gorsel_uc_sinif(url, kitap, beklenen, gerekce):
    """Tek sınıfla ölçmek yanlış-negatifi görmez: yalnız `_PAGE` test edilseydi
    Apotemi crop'u sessizce taşınırdı; yalnız Apotemi test edilseydi temiz
    crop'ların da NULL'lanması fark edilmezdi (1.435 görsel kaybı)."""
    cikti = donustur(question_image_url=url, source_book=kitap)
    assert cikti["question_content"]["question_image_url"] == beklenen, gerekce


@pytest.mark.parametrize(
    "url,kitap,beklenen,gerekce",
    [
        (TEMIZ_CROP, APOTEMI, None, "kitap sizintili -> yol temiz gorunse de NULL"),
        (APOTEMI_CROP, DIGER_KITAP, APOTEMI_CROP, "kitap temiz -> yol adi onemsiz"),
    ],
)
def test_gorsel_kurali_source_book_a_bakar_yola_degil(url, kitap, beklenen, gerekce):
    """Kural 13'ün sızıntılı-kitap kolu METADATA'ya bağlıdır, dosya yoluna değil.

    Kaynakta ikisi bugün DENK: `source_book='Apotemi...'` olup yolunda kitap
    adı GEÇMEYEN satır 0, tersi de 0 (ölçüldü). Bu yüzden yol-tabanlı bir
    uygulama mevcut dört parametrenin dördünü de geçiyordu (ölçüldü:
    101/101 PASS) — fiili zarar 0, ama kural ÇİVİLENMEMİŞTİ.

    Ayırt edici çift burada: birinci satır yol-tabanlı uygulamayı öldürür,
    ikinci satır metadata-tabanlı uygulamanın fazla-agresif olmadığını
    gösterir. Y12 kapsam ölçümü `source_book`'a dayandığı için bağın
    hangi alanda olduğu yük taşıyor.
    """
    cikti = donustur(question_image_url=url, source_book=kitap)
    assert cikti["question_content"]["question_image_url"] == beklenen, gerekce


def test_gorsel_kurali_source_book_u_silmez():
    """Kural 13 `source_book`'u OKUR; silmez. Y12 kapsam ölçümü ona dayanıyor."""
    cikti = donustur(question_image_url=APOTEMI_CROP, source_book=APOTEMI)
    assert cikti["question_metadata"]["source_book"] == APOTEMI


# ---------------------------------------------------------------------------
# KURAL 14/15/16 — geçişi ölçülmüş alanlar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("deger", ["medium", "kolay", "orta"])
def test_irt_based_difficulty_kaynaktan_tasinir(deger):
    """Kural 14. "Sürükleme yok" iddiası ölçümde ÇÜRÜDÜ: kaynak KIMYA'da
    `medium` 19.354 · `kolay` 4 · `orta` 2. Kural yine de geçiştir —
    normalizasyon KARARI bu fonksiyonun işi değil; ama üç değerin de
    bozulmadan geçtiği çivilenir ki sürükleme SONRADAN ölçülebilsin."""
    cikti = donustur(irt_based_difficulty=deger)
    assert cikti["question_statistics"]["irt_based_difficulty"] == deger


@pytest.mark.parametrize("etiket", ["VERY_EASY", "EASY", "MEDIUM", "HARD", "VERY_HARD"])
def test_difficulty_level_kaynaktan_tasinir(etiket):
    """Kural 15. Enum etiketleri iki DB'de BİREBİR aynı. Göçün asıl değeri
    burada: canlıda 36.967/36.967 satır MEDIUM — adaptif motorda ayrıştırıcı
    sinyal YOK. Bu alan ezilirse göç o değeri kaybeder."""
    cikti = donustur(difficulty_level=etiket)
    assert cikti["question_statistics"]["difficulty_level"] == etiket


def test_id_ve_soru_hash_kaynaktan_tasinir():
    """Kural 16. Canlıyla kesişim 0 (id ve hash, ölçüldü) — yeniden üretmek
    kaynakla bağı koparır ve geri alma/karşılaştırma imkânsızlaşır."""
    satir = kaynak_satiri()
    qb = donustur()["question_bank"]
    assert qb["id"] == satir["id"]
    assert qb["soru_hash"] == satir["soru_hash"]


# ---------------------------------------------------------------------------
# KURAL 17 — hedef-özel 5 kolon
# ---------------------------------------------------------------------------


def test_hedef_ozel_bes_kolon_acikca_yazilir():
    """Kural 17 (+ kural 6 ayrı testte). Kaynakta KARŞILIĞI YOK; yazılmazsa
    ya `NotNullViolation` ya da hedef `server_default`'ı devreye girer."""
    cikti = donustur()
    assert cikti["question_bank"]["is_ai_generated"] is False
    assert cikti["question_bank"]["is_anchor"] is False
    assert cikti["question_content"]["structured_explanation"] is None
    assert cikti["question_metadata"]["pedagogical_status"] == "ACTIVE"


# ---------------------------------------------------------------------------
# ZIMNİ GEÇİŞ — 17 kuralın adıyla ANMADIĞI 23 NOT NULL + defaultsuz kolon
# ---------------------------------------------------------------------------

ZORUNLU_GECIS = [
    ("question_content", "question_text"),
    ("question_metadata", "exam_type"),
    ("question_metadata", "subject_area"),
    ("question_metadata", "grade_level"),
    ("question_metadata", "osym_format_compliant"),
    ("question_metadata", "morphology_complexity"),
    ("question_metadata", "word_count"),
    ("question_metadata", "unique_word_count"),
    ("question_metadata", "average_word_length"),
    ("question_metadata", "readability_score"),
    ("question_statistics", "student_success_rate"),
    ("question_statistics", "difficulty_update_count"),
    ("question_statistics", "irt_discrimination"),
    ("question_statistics", "irt_difficulty"),
    ("question_statistics", "irt_guessing"),
    ("question_statistics", "irt_upper_asymptote"),
    ("question_statistics", "is_calibrated"),
    ("question_statistics", "calibration_sample_size"),
    ("question_statistics", "calibration_quality_score"),
    ("question_statistics", "average_response_time"),
    ("question_statistics", "median_response_time"),
    ("question_statistics", "exposure_rate"),
    ("question_statistics", "quality_score"),
]


# Kural uygulanan / hedef-özel kolonlar — bunlar GEÇİŞ DEĞİLDİR.
# Bilerek LİTERAL: beklentiyi modülün kendi `_*_GECIS` demetlerinden türetmek,
# "kolonu geçiş listesinden düşür" mutasyonunu ölçülemez yapardı (test kendi
# oracle'ını koda sorardı).
KURALLI_KOLONLAR = {
    "question_bank": {
        "id",
        "primary_topic_id",
        "created_by",
        "reviewed_by",
        "is_public",
        "is_active",
        "review_status",
        "is_ai_generated",
        "is_anchor",
    },
    "question_content": {"id", "question_image_url", "structured_explanation"},
    "question_metadata": {
        "id",
        "bloom_category",
        "pipeline_metadata",
        "pedagogical_status",
    },
    "question_statistics": {
        "id",
        "quality_review_status",
        "times_asked",
        "times_correct",
        "times_wrong",
        "times_skipped",
    },
}

TUM_GECIS = sorted(
    (tablo, kolon)
    for tablo, hedef in (
        ("question_bank", HEDEF_BANK),
        ("question_content", HEDEF_CONTENT),
        ("question_metadata", HEDEF_METADATA),
        ("question_statistics", BEKLENEN_STATISTICS),
    )
    for kolon in hedef - KURALLI_KOLONLAR[tablo]
)


def test_gecis_kolonu_sayisi_63():
    """Ölçüm ALETİNİ doğrula: aşağıdaki parametrize gerçekten TÜM geçişi mi
    kapsıyor? 3 + 16 + 17 + 27 = 63 (modülün kendi muhasebesi). Bu sayı
    tutmazsa `KURALLI_KOLONLAR` bayatlamıştır ve geçiş testi sessizce
    daralmıştır — yanlış-sıfır, bu depoda tek kabul edilemez hata türü."""
    assert len(TUM_GECIS) == 63
    assert len(set(TUM_GECIS)) == 63


@pytest.mark.parametrize("tablo,kolon", TUM_GECIS)
def test_fixture_gecis_kolonlarinda_none_birakmaz(tablo, kolon):
    """ÖLÇÜM ALETİNİ doğrula — `assert cikti is None` hiçbir şey ölçmez.

    Bir geçiş alanı fixture'da `None` bırakılsaydı, o alanı koşulsuz
    `None`'a çeken mutasyon aşağıdaki geçiş testini GEÇERDİ. 63 geçiş
    kolonunun tamamı `None`-dışı olmak zorunda; bu, fixture'ın ayırt
    ediciliğini koruyan bir kontrol koludur.
    """
    assert (
        kaynak_satiri()[kolon] is not None
    ), f"{tablo}.{kolon} fixture'da None -> gecis assert'i kor kalir"


@pytest.mark.parametrize("tablo,kolon", TUM_GECIS)
def test_gecis_kolonlari_deger_olarak_tasinir(tablo, kolon):
    """Geçişin ANAHTARI değil DEĞERİ ölçülür.

    Kolon-kümesi testleri yalnız anahtarın VARLIĞINA bakar; bir alanı
    koşulsuz `None`'a çekmek onları geçer. Ölçüldü: `"explanation": None`
    eklemek 101/101 PASS veriyordu ve kaynakta KIMYA'nın 14.084 satırında
    dolu olan çözüm metnini sessizce yok ederdi. Aynı sınıf `source_page`
    (19.354 dolu), `irt_method` (18.399), `secondary_topics` (13.040),
    `image_ocr_text` (5.606) ve altı IRT ikizini de kapsıyor.

    Önceki sürüm yalnız hedefte NOT NULL olan 23 kolonu ölçüyordu; NULLABLE
    olan 40 kolon için hiçbir iddia yoktu (INSERT geçtiği için sessiz).
    """
    satir = kaynak_satiri()
    assert donustur()[tablo][kolon] == satir[kolon]


def test_zorunlu_gecis_listesi_tum_gecisin_alt_kumesi():
    """Hedefte NOT NULL + defaultsuz 23 kolonun belgesi ANKRAJLI kalsın.

    Bunlardan biri geçiş listesinden düşerse her INSERT
    `NotNullViolationError` ile düşer; yukarıdaki parametrize onu zaten
    kaybederdi ama bu assert kaybı ADIYLA raporlar.
    """
    eksik = [ik for ik in ZORUNLU_GECIS if ik not in set(TUM_GECIS)]
    assert not eksik, f"NOT NULL + defaultsuz kolon gecis kapsamindan dustu: {eksik}"


@pytest.mark.parametrize(
    "tablo,kolon",
    [
        ("question_statistics", "irt_calibrated"),
        ("question_statistics", "irt_n_responses"),
        ("question_statistics", "is_calib_pool"),
    ],
)
def test_not_null_defaultlu_kolonlar_none_basmaz(tablo, kolon):
    """Bu üçü NOT NULL AMA DEFAULT'lu: atlamak güvenli, AÇIKÇA `None` geçmek
    INSERT'i DÜŞÜRÜR.

    `is not None` TEK BAŞINA zayıf: `is_calib_pool`'u koşulsuz `True` yapmak
    da `None` değildir ve testi geçerdi (ölçüldü: 101/101 PASS) — oysa o
    mutasyon partinin tamamını IRT kalibrasyon havuzuna sokar. Bu yüzden
    geçiş eşitliği de burada iddia edilir.
    """
    satir = kaynak_satiri()
    sozluk = donustur()[tablo]
    if kolon in sozluk:
        assert sozluk[kolon] is not None
        assert sozluk[kolon] == satir[kolon]


# ---------------------------------------------------------------------------
# SAFLIK — DB yok, dosya yok, rastgelelik yok, YAN ETKİ yok
# ---------------------------------------------------------------------------


def test_ayni_girdi_ayni_cikti():
    """Rastgele id/zaman üreten bir uygulama iki koşumda farklı satır yazar."""
    assert donustur() == donustur()


def test_girdi_sozlugu_degistirilmez():
    """Girdiyi yerinde değiştirmek, çağıranın dedup/parity ölçümünü bozar."""
    satir = kaynak_satiri()
    onceki = copy.deepcopy(satir)
    kaynak_satiri_donustur(satir, topic_kod_haritasi=dict(CANLI_TOPIC), damga=DAMGA)
    assert satir == onceki


def test_kaynak_pipeline_metadata_yerinde_mutasyona_ugramaz():
    """Damgayı kaynak sözlüğün İÇİNE yazmak en sinsi yan etki: aynı `dict`
    nesnesi paylaşılıyorsa damga girdiye sızar ve `test_girdi_sozlugu...`
    dışındaki her ölçüm bulanır."""
    satir = kaynak_satiri()
    kaynak_satiri_donustur(satir, topic_kod_haritasi=dict(CANLI_TOPIC), damga=DAMGA)
    assert "y11_batch" not in satir["pipeline_metadata"]


def test_pipeline_metadata_ic_sozlukleri_de_paylasilmaz():
    """Kopya DERİN olmalı; sığ kopya üst düzeyi korur ama İÇ sözlüğü paylaşır.

    Yukarıdaki test yalnız ÜST düzey anahtar sızıntısını ölçüyor ve sığ
    kopyada da o sızıntı olmaz — bu yüzden `copy.deepcopy(ham)` yerine
    `dict(ham)` yazmak 101/101 PASS veriyordu, yani deepcopy ölçülemeyen
    bir ağırlıktı. Burada `book_key_match` iç sözlüğü üzerinden çivileniyor:
    çağıranın dedup/parity ölçümü aynı nesneyi paylaşırsa bulanır.
    """
    # `donustur()` her çağrıda TAZE bir fixture kurar. Kimlik (`is not`)
    # karşılaştırması AYNI kaynak nesnesi üzerinden yapılmazsa vakumdur:
    # iki ayrı sözlüğün iç sözlükleri zaten farklı nesnelerdir ve sığ kopya
    # da testi geçerdi (ölçüldü). Bu yüzden satır ELDE tutulur.
    satir = kaynak_satiri()
    cikti = kaynak_satiri_donustur(
        satir, topic_kod_haritasi=dict(CANLI_TOPIC), damga=DAMGA
    )
    pm = cikti["question_metadata"]["pipeline_metadata"]
    assert pm["book_key_match"] is not satir["pipeline_metadata"]["book_key_match"]

    # Davranışsal kanıt: çıktıyı kirlet, kaynak DEĞİŞMEMELİ.
    pm["book_key_match"]["status"] = "KIRLETILDI"
    assert satir["pipeline_metadata"]["book_key_match"]["status"] == "agree"


def test_harita_degistirilmez():
    harita = dict(CANLI_TOPIC)
    onceki = dict(harita)
    kaynak_satiri_donustur(kaynak_satiri(), topic_kod_haritasi=harita, damga=DAMGA)
    assert harita == onceki


def test_bos_girdi_gurultulu_hata():
    """Boş/eksik satır sessizce varsayılanlarla dolu bir satır ÜRETMEMELİ —
    o satır DB'ye gider ve kaynağı olmayan içerik doğurur.

    KAPSAM UYARISI: bu test yalnız İLK bekçiye (`_zorunlu(satir,"id")`)
    ulaşır. Modülün diğer iki sessiz-varsayılan bekçisi
    (`_zorunlu`'nun geri kalanı ve `_gecis`) için aşağıdaki iki test
    gerekli — boş sözlükle ölçmek 69 kolonun 68'i hakkında hiçbir şey
    söylemez.
    """
    with pytest.raises(ValueError) as hata:
        kaynak_satiri_donustur({}, topic_kod_haritasi=dict(CANLI_TOPIC), damga=DAMGA)
    assert "'id'" in str(hata.value)


# ---------------------------------------------------------------------------
# SESSİZ VARSAYILAN YOK — eksik kolon GÜRÜLTÜLÜ hata (yanlış-sıfır avı)
# ---------------------------------------------------------------------------

# `_zorunlu` ile okunan, geçiş listelerinde OLMAYAN kolonlar.
_ZORUNLU_OKUNANLAR = [
    "id",
    "topic_code",
    "question_image_url",
    "source_book",
    "bloom_level",
    "pipeline_metadata",
]

# Her hedef tablodan birer NULLABLE geçiş kolonu (hedef nullability canlı
# `information_schema`'dan ölçüldü: dördü de `is_nullable=YES`). NULLABLE
# seçilmesi bilinçli — sessizce `None` olsalar INSERT **GEÇER**, yani kusur
# DB tarafından yakalanmaz. NOT NULL olanlar zaten INSERT'te gürültülü düşer.
_NULLABLE_GECISLER = ["updated_at", "explanation", "source_page", "irt_method"]


@pytest.mark.parametrize("kolon", _ZORUNLU_OKUNANLAR)
def test_zorunlu_alan_eksikse_kolon_adi_mesajda(kolon):
    """`_zorunlu` bekçisi: `.get()`'e çevrilirse eksik alan sessizce `None`.

    Ölçüldü — gövdeyi `return satir.get(kolon)` yapmak 101/101 PASS
    veriyordu. `question_image_url` silindiğinde üretilen satır hatasız
    çıkıyordu; dahası `source_book` silinince `_gorsel_url`'un Apotemi
    süzgeci KÖRLEŞİYOR ve sızıntılı crop taşınıyordu.

    `pytest.raises` BİLEREK dar: çıplak `KeyError` de kabul edilseydi
    `if kolon not in satir:` bloğunu silmek testi geçerdi (`satir[kolon]`
    zaten `KeyError` atar) — ölçüldü, 101/101 PASS.
    """
    satir = kaynak_satiri()
    del satir[kolon]
    with pytest.raises(ValueError) as hata:
        kaynak_satiri_donustur(satir, topic_kod_haritasi=dict(CANLI_TOPIC), damga=DAMGA)
    assert kolon in str(hata.value)


@pytest.mark.parametrize("kolon", _NULLABLE_GECISLER)
def test_gecis_kolonu_eksikse_sessiz_none_uretilmez(kolon):
    """`_gecis` bekçisi: SELECT listesi kayarsa (drift) gürültülü dur.

    Ölçüldü — `{kolon: satir.get(kolon) ...}`'e çevirmek 101/101 PASS
    veriyordu ve `explanation`/`source_book`/`osym_year`/`option_e`
    silindiğinde hepsi sessizce `None` oluyordu. Dördü de hedefte
    NULLABLE, yani INSERT bunu YAKALAMAZ — kayıp ancak sonradan,
    veri üzerinden fark edilirdi.
    """
    satir = kaynak_satiri()
    del satir[kolon]
    with pytest.raises(ValueError) as hata:
        kaynak_satiri_donustur(satir, topic_kod_haritasi=dict(CANLI_TOPIC), damga=DAMGA)
    assert kolon in str(hata.value)


@pytest.mark.parametrize("kotu", ["", "   ", None, 0, b"y11"])
def test_gecersiz_damga_gurultulu_hata(kotu):
    """Damga, geri alma kümesinin TEK seçicisi — bekçisi olmadan iddia boş.

    Ölçüldü: doğrulamayı `if False:` yapmak 101/101 PASS veriyor ve
    `y11_batch` sırasıyla `''` / `'   '` / `None` oluyordu. Üçü de INSERT'e
    girer (`pipeline_metadata` json, üstünde kısıt yok). Canlı SQL ile
    ölçüldü: `('{"y11_batch": null}'::jsonb ->> 'y11_batch') IS NULL` → `t`,
    yani belgelenen seçici (`->> 'y11_batch' = '<damga>'`) o satırları
    KAÇIRIR; boş dizede ise partiler birbirinden ayrılamaz.
    """
    with pytest.raises(ValueError):
        kaynak_satiri_donustur(
            kaynak_satiri(), topic_kod_haritasi=dict(CANLI_TOPIC), damga=kotu
        )


def test_pipeline_metadata_none_ise_damga_yine_yazilir():
    """Kaynakta `pipeline_metadata IS NULL` olan satır VAR (ölçüldü: evrende 1).

    Bu dal ölü kod değil. Silinirse o satır `ValueError` ile reddedilir ve
    damgasız kalır; ölçüldü — dalı `if False:` yapmak 101/101 PASS veriyordu.
    """
    pm = donustur(pipeline_metadata=None)["question_metadata"]["pipeline_metadata"]
    assert pm == {"y11_batch": DAMGA}


@pytest.mark.parametrize(
    "ham",
    [
        # asyncpg'nin GERÇEK davranışı: jsonb -> `str` (ölçüldü, 0.31.0).
        '{"source": "kiro2_batch_v4.14e", "book_key_match": {"status": "agree"}}',
        ["liste"],
        42,
    ],
)
def test_pipeline_metadata_json_nesnesi_degilse_gurultulu_hata(ham):
    """P0 — bu bekçi yumuşatılırsa kaynak metadata'sının TAMAMI sessizce silinir.

    Senaryo teorik DEĞİL: `asyncpg` 0.31.0 `kiro2_temp.question_bank.
    pipeline_metadata`'yı **`str`** olarak döndürüyor (canlı ölçüldü) ve
    depoda `core/` altında hiçbir `set_type_codec` YOK — yani yükleyiciyi
    yazan kişi jsonb kodeki kaydetmezse bu dal ATEŞLENİR.

    Ölçüldü: `if ham is None:` yerine `if not isinstance(ham, dict):` yazmak
    (yani `raise` dalını erişilemez kılan "tolerans") 101/101 PASS veriyor ve
    çıktı `{'y11_batch': ...}` tek anahtarına iniyordu —
    `book_key_match`/`match_tier`/`ai_extras`/`v2_2_tier` HEPSİ giderdi.
    """
    with pytest.raises(ValueError) as hata:
        donustur(pipeline_metadata=ham)
    assert "JSON nesnesi" in str(hata.value)
