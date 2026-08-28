#!/usr/bin/env python
"""Y11 göçü — `kiro2_temp` satırını 4-tablo split'ine çeviren SAF dönüşüm.

Kaynak `kiro2_temp.question_bank` (pre-split, **78 kolon**), hedef canlı
`kiro2`'nun dört tablosu (`question_bank` 12 / `question_content` 19 /
`question_metadata` 21 / `question_statistics` 34 → **83 distinct** kolon adı).
Muhasebe: 78 kaynak + 5 hedef-özel = 83. Bu modül DB'ye dokunmaz, dosya
okumaz, rastgelelik üretmez; girdi sözlüğünü **yerinde değiştirmez**.

Dedup bu modülün işi DEĞİLDİR: `siki_kimlik`/`mukerrer_gruplar` bir **küme**
üzerinde çalışır (`backend/scripts/quality/y11_dedup.py`), buradaki fonksiyon
ise tek satır alır. Çağıran katman önce eler, sonra dönüştürür.

ÜÇ KARARIN GEREKÇESİ (hepsi ölçüldü)
------------------------------------

**1. `embedding` çıktıya HİÇ konmuyor.** Kaynak kolon `vector(768)`, hedef
kolon `vector(1536)`. Değeri taşımak boyut uyuşmazlığı üretir; anahtarı `None`
değeriyle koymak bile INSERT'e girer. Hedef kolon NULLABLE olduğu için tek
güvenli davranış **anahtarı hiç üretmemektir**. Gömme, hedef modelin kendi
boyutuyla sonradan üretilir.

**2. `review_status` AÇIKÇA lowercase `'approved'` yazılıyor.** Canlı kanon
36.967/36.967 satırda `'approved'`; ama hedef kolonun `server_default`'ı
`'APPROVED'` (BÜYÜK). Kolonu yazmadan bırakmak sessiz bir **sürükleme** üretir:
satır girer, INSERT patlamaz, kolon `varchar` olduğu ve üstünde CHECK
bulunmadığı için hiçbir kısıt bunu durdurmaz — canlı kanon iki değerli hâle
gelir ve `review_status`'a bakan her filtre bugünden sonra yanlış sayar.

**3. Bloom ALTI seviyenin ALTISI için de eşleniyor.** Kaynak `bloom_category`
Türkçe ("bilgi", "kavrama", "sentez"); tüketici
`services/empirical_irt_calibrator.py:119` ise
`BLOOM_A_MAP.get(str(bloom_category).upper(), 1.05)` yapıyor ve haritada
yalnız KNOWLEDGE/COMPREHENSION/APPLICATION/ANALYSIS/EVALUATION/CREATION var.
Türkçe etiket taşınırsa INSERT **patlamaz** (kolon `varchar`), kusur
görünmez — kaynak KIMYA'nın 4.419 satırının 4.392'si (bloom 2..6) sessizce
`a=1.05` sabitine düşerdi. Yalnız bloom=1'i eşleyip gerisini bırakmak da aynı
sonucu verir; bu yüzden altısı birden eşlenir ve bilinmeyen seviye
**gürültülü hata** verir.

DİKKAT — kaynak ESKİ Bloom sırasını kullanıyor (5=sentez, 6=değerlendirme).
Kullanıcı kararı **SAYIYI** kanon kabul eder, kelimeyi değil: 5→`evaluation`
(a=1.65), 6→`creation` (a=1.80). Etkilenen satır 27 (10+17) ve karar bilinçli.

17 KURALIN ANMADIĞI KOLONLAR
----------------------------
Kural listesi kaynağın yalnız 26 kolonunu adıyla anıyor. Kalan 52 kolon burada
**açık geçiş listeleriyle** taşınır; bunların 23'ü hedefte NOT NULL + defaultsuz
(`question_text`, 9 metadata, 13 statistics kolonu) ve atlanmaları hâlinde her
INSERT `NotNullViolationError` ile düşerdi. Geçiş `.get()` ile değil doğrudan
indeksle yapılır: eksik kolon **sessizce None** olmaz, gürültülü hata verir.

Bekçi: `backend/tests/fast/test_y11_goc.py`
"""

from __future__ import annotations

import copy
from typing import Any

# --- canlı kanon sabitleri (36.967 satırın tamamından ölçüldü) --------------
REVIEW_STATUS = "approved"  # kural 6 — server_default 'APPROVED' sürüklerdi
QUALITY_REVIEW_STATUS = "pending"  # kural 7 — mv_safe_for_beta kapısına GİRMEZ
PEDAGOJIK_DURUM = "ACTIVE"  # kural 17
DAMGA_ANAHTARI = "y11_batch"  # kural 11 — geri alma kümesinin TEK taşıyıcısı

# --- kural 13: görsel sınıfları --------------------------------------------
# Tam sayfa görüntüsü: ölçüldü, %88,5'i sayfa altına BASILI cevap anahtarı
# sızdırıyor (biri 180 derece ters basılmış).
SAYFA_GORSELI_ISARETI = "_PAGE"
# Önceki sahibinin pembe kalemle işaretlediği kitap; crop'ları da sızdırıyor.
SIZINTILI_KITAP = "Apotemi 2024 Ayt Kimya Soru Bankasi"

# --- kural 8: seviye -> canlı kanon (lowercase İngilizce) -------------------
BLOOM_KATEGORI: dict[int, str] = {
    1: "knowledge",
    2: "comprehension",
    3: "application",
    4: "analysis",
    5: "evaluation",
    6: "creation",
}

# --- kural 9: yeni havuzda gösterim geçmişi YOKTUR --------------------------
SIFIRLANAN_SAYACLAR = ("times_asked", "times_correct", "times_wrong", "times_skipped")

# ---------------------------------------------------------------------------
# GEÇİŞ LİSTELERİ — kaynak adı == hedef adı olan kolonlar.
# Kural uygulanan kolonlar bilerek DIŞARIDA; ikisi birden yazılırsa kural
# sessizce ezilir. Toplam: 3 + 16 + 17 + 27 = 63 geçiş + 14 kurallı + id.
# ---------------------------------------------------------------------------

_BANK_GECIS = (
    "soru_hash",  # kural 16
    "created_at",  # kural 10 — now() basmak kaynak izini siler
    "updated_at",  # kural 10
)

_CONTENT_GECIS = (
    "question_text",
    "question_html",
    "question_latex",
    "image_ocr_text",
    "image_width",
    "image_height",
    "question_audio_url",
    # kural 12: şıklar ve anahtar AYNI satırdan, SIRA BOZULMADAN. `correct_answer`
    # bir DEĞER değil, şık listesine KONUMSAL referans — normalize/yeniden
    # sıralama anahtarı sessizce yanlış cevaba bağlar.
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
    "correct_answer",
    "explanation",
    "explanation_video_url",
    "alternative_solutions",
)

_METADATA_GECIS = (
    "secondary_topics",
    "bloom_level",  # kural 8: SAYI kanondur, kelime değil
    "exam_type",
    "subject_area",
    "grade_level",
    "osym_format_compliant",
    "osym_year",
    "source_book",  # kural 13 bunu OKUR, silmez
    "source_page",
    "misconception_tags",
    "solution_steps",
    "similar_question_ids",
    "morphology_complexity",
    "word_count",
    "unique_word_count",
    "average_word_length",
    "readability_score",
)

_STATISTICS_GECIS = (
    "difficulty_level",  # kural 15 — göçün asıl değeri (canlıda 36.967/36.967 MEDIUM)
    "irt_based_difficulty",  # kural 14 — sürükleme SONRADAN ölçülebilsin diye ham geçer
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
    "average_response_time",
    "median_response_time",
    "exposure_rate",
    "last_used_date",
    "quality_score",
    "reviewed_at",
)


def _zorunlu(satir: dict[str, Any], kolon: str) -> Any:
    """Tek alanı gürültülü oku. `.get()` YASAK: eksik alan sessizce `None`
    olursa kaynağı olmayan bir satır DB'ye gider."""
    if kolon not in satir:
        raise ValueError(
            f"kaynak satirda '{kolon}' alani YOK. Beklenen: kiro2_temp."
            "question_bank'in 78 kolonu + JOIN'den gelen 'topic_code'. "
            "SELECT listesini kontrol et."
        )
    return satir[kolon]


def _gecis(
    satir: dict[str, Any], kolonlar: tuple[str, ...], tablo: str
) -> dict[str, Any]:
    """Adı değişmeyen kolonları taşı; eksik olanları TEK SEFERDE bildir."""
    eksik = [k for k in kolonlar if k not in satir]
    if eksik:
        raise ValueError(
            f"kaynak satirda '{tablo}' icin gerekli {len(eksik)} kolon YOK: "
            f"{eksik}. Bunlarin cogu hedefte NOT NULL + defaultsuz — atlanirsa "
            "INSERT NotNullViolationError ile duser."
        )
    return {kolon: satir[kolon] for kolon in kolonlar}


def _canli_topic_id(topic_kodu: Any, topic_kod_haritasi: dict[str, str]) -> str:
    """Kural 2 — remap KOD üzerinden.

    Kaynak id'yi geçirmek FK ihlali üretir (kesişim ölçüldü: KIM/FIZ/GEN
    canlıda FARKLI id taşıyor). Eksik kodu KOPYALAMAK da yasak:
    `topic_hierarchy_code_key` UNIQUE ihlali. Tek doğru davranış DURMAK.
    """
    if topic_kodu not in topic_kod_haritasi:
        raise ValueError(
            f"topic_code '{topic_kodu}' haritada YOK. Sessiz varsayilan (kaynak "
            "id'yi gecirme / None / ilk konuya baglama) FK ihlali veya yanlis "
            "konu uretir. Haritaya CANLI topic_hierarchy id'sini ekle veya "
            "satiri gocten cikar."
        )
    return topic_kod_haritasi[topic_kodu]


def _bloom_kategorisi(bloom_seviyesi: Any) -> str:
    """Kural 8 — bilinmeyen seviye için sessiz 'knowledge' YASAK.

    `bool` ayrıca elenir: `True == 1` olduğu için harita onu sessizce
    'knowledge' yapardı.
    """
    if isinstance(bloom_seviyesi, bool) or bloom_seviyesi not in BLOOM_KATEGORI:
        raise ValueError(
            f"bloom_level={bloom_seviyesi!r} taninmiyor; beklenen 1..6 (int). "
            "Sessiz varsayilan yazmak INSERT'i DUSURMEZ (bloom_category varchar) "
            "ama empirical_irt_calibrator'i a=1.05 fallback'ine dusurur."
        )
    return BLOOM_KATEGORI[bloom_seviyesi]


def _gorsel_url(satir: dict[str, Any]) -> str | None:
    """Kural 13 — üç sınıf: `_PAGE` → None, sızıntılı kitabın crop'u → None,
    diğer kitapların crop'u → taşınır (30/30 örnek temiz ölçüldü)."""
    url: str | None = _zorunlu(satir, "question_image_url")
    kitap: str | None = _zorunlu(satir, "source_book")
    if url is None:
        return None
    if SAYFA_GORSELI_ISARETI in url:
        return None
    if kitap == SIZINTILI_KITAP:
        return None
    return url


def _damgali_pipeline_metadata(satir: dict[str, Any], damga: str) -> dict[str, Any]:
    """Kural 11 — kaynak metadata KORUNUR, damga ÜZERİNE EKLENİR.

    `match_tier` / `book_key_match` gibi alanlar kapı filtresinin ve sonraki
    yargı turunun girdisi; üzerine yazmak onları siler. Derin kopya alınır:
    damga kaynak sözlüğe sızarsa çağıranın dedup/parity ölçümü bulanır.
    """
    ham = _zorunlu(satir, "pipeline_metadata")
    if ham is None:
        pm: dict[str, Any] = {}
    elif isinstance(ham, dict):
        pm = copy.deepcopy(ham)
    else:
        raise ValueError(
            f"pipeline_metadata bir JSON nesnesi olmali, {type(ham).__name__} geldi. "
            "Damga baska bir tipe eklenemez ve damgasiz satir GERI ALINAMAZ."
        )
    pm[DAMGA_ANAHTARI] = damga
    return pm


def kaynak_satiri_donustur(
    satir: dict[str, Any],
    *,
    topic_kod_haritasi: dict[str, str],
    damga: str,
) -> dict[str, dict[str, Any]]:
    """4 hedef tablo için satır sözlükleri döndürür.

    Anahtarlar: 'question_bank','question_content','question_metadata',
    'question_statistics'. Dördü TEK transaction'da yazılmak üzere ATOMİK bir
    birimdir — damga `question_metadata`'da, çapa `question_bank`'ta olduğu
    için yarım INSERT geri alınamaz.

    `satir`, kaynağın 78 kolonu + JOIN'den gelen `topic_code` alanını taşır.
    Girdi sözlüğü ve `topic_kod_haritasi` DEĞİŞTİRİLMEZ.
    """
    if not isinstance(damga, str) or not damga.strip():
        raise ValueError(
            f"damga bos olamaz (gelen: {damga!r}). Geri alma kumesinin TEK "
            "secicisi bu deger; damgasiz satirlar ayristirilamaz."
        )

    soru_id = _zorunlu(satir, "id")  # kural 16 — üç yavru tablonun PK'sı da BU
    topic_kodu = _zorunlu(satir, "topic_code")

    question_bank = {
        "id": soru_id,
        "primary_topic_id": _canli_topic_id(topic_kodu, topic_kod_haritasi),
        # Kural 3. Kaynağın kullanıcı id'leri hedef `users`'ta YOK; geçirmek
        # yetim FK üretir. `reviewed_by` aynı FK'nın kardeşi ve 17 kural onu
        # anmıyor — ölçüldü: batch'te 4419/4419 zaten NULL, yani bu batch için
        # no-op; başka bir alt kümede FK ihlalini önler.
        "created_by": None,
        "reviewed_by": None,
        # Kural 4. Kaynak 4.419/4.419 FALSE, canlı kanon 36.967/36.967 TRUE:
        # bu bir GEÇİŞ değil, DÖNÜŞÜM.
        "is_public": True,
        # Kural 5. `server_default` var ama ORM default False (S225): varsayılana
        # bırakmak satırı kapının DIŞINDA bırakırdı.
        "is_active": True,
        "review_status": REVIEW_STATUS,  # kural 6 — modül docstring'i, madde 2
        "is_ai_generated": False,  # kural 17
        "is_anchor": False,  # kural 17
        **_gecis(satir, _BANK_GECIS, "question_bank"),
    }

    question_content = {
        "id": soru_id,
        "question_image_url": _gorsel_url(satir),  # kural 13
        "structured_explanation": None,  # kural 17 — kaynakta karşılığı YOK
        **_gecis(satir, _CONTENT_GECIS, "question_content"),
    }

    question_metadata = {
        "id": soru_id,
        "bloom_category": _bloom_kategorisi(_zorunlu(satir, "bloom_level")),  # kural 8
        "pipeline_metadata": _damgali_pipeline_metadata(satir, damga),  # kural 11
        "pedagogical_status": PEDAGOJIK_DURUM,  # kural 17
        **_gecis(satir, _METADATA_GECIS, "question_metadata"),
    }

    question_statistics = {
        "id": soru_id,
        # Kural 7. Kaynakta 'auto_judged_high' olsa bile 'pending' yazılır;
        # satırlar `mv_safe_for_beta` kapısına GİRMEZ, insan yargısı bekler.
        "quality_review_status": QUALITY_REVIEW_STATUS,
        # Kural 9. Başka bir DB'nin gösterim geçmişini taşımak `exposure_rate`
        # ve seçim algoritmasını yalancı yapar.
        **dict.fromkeys(SIFIRLANAN_SAYACLAR, 0),
        **_gecis(satir, _STATISTICS_GECIS, "question_statistics"),
        # Kural 1: `embedding` BİLEREK yok — bkz. modül docstring'i, madde 1.
    }

    return {
        "question_bank": question_bank,
        "question_content": question_content,
        "question_metadata": question_metadata,
        "question_statistics": question_statistics,
    }
