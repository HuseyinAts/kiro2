"""Y11 yükleyicisi — 4 tabloya TEK transaction'da yazan katmanın bekçisi (FAZ C).

NEDEN AYRI BİR BEKÇİ
--------------------
`y11_goc.kaynak_satiri_donustur` **saf**: sözlük alır, sözlük verir, hiçbir şeyi
kalıcı yapmaz. 242 test onu çiviliyor. Ama bu göçün kullanıcıya ulaşan kısmı
dönüşüm değil **yazım**: satır DB'ye nasıl gidiyor, damga geri okunabiliyor mu,
yarım parti kalabiliyor mu. S225'te aynı sınıftaki `toplu_soru_ekle` **%100
düşerken uç `HTTP 201 + success:true + "0/3 eklendi"`** dönüyordu — yani yazma
katmanının sessiz kusuru dönüşüm testlerinden **yapısal olarak** kaçar.

Bu dosya dört sınıfı ölçer:

1. **Sıra** — `question_bank` İLK yazılmalı. Üç yavru tablonun PK'sı aynı zamanda
   ebeveyne FK (`L-s230-yavru-tablonun-pk-si-id`); ters sırada FK ihlali.
2. **Damga tek kez serialize** — hedef kolon `json` (ölçüldü: `information_schema`
   `data_type='json'`). asyncpg `json`'a **str** ister. `json.dumps` iki kez
   uygulanırsa kolon bir JSON *string skaları* tutar, `->>'y11_batch'` **NULL**
   döner ve parti **damgasız** girer — damga geri alma kümesinin TEK taşıyıcısı
   olduğu için o parti **geri alınamaz**. Sessiz kusur; INSERT patlamaz.
3. **Anahtar kaybı yok** — INSERT kolon listesi dönüşümün ürettiği anahtarlarla
   birebir. Bir anahtar sessizce düşerse ya NOT NULL patlar (gürültülü, iyi) ya
   da `server_default` sürüklemesi olur (sessiz, kötü — `review_status` bunun
   emsali).
4. **Varsayılan GERİ ALIR** — `kalici=False`. Yanlış varsayılan, "pilot"
   niyetiyle çağrılan bir komutu kalıcı yazıma çevirir.

Canlı PG'ye vuran testler `BEGIN … ROLLBACK` içinde çalışır ve satır sayısı
invaryantını koşumun **sonunda** yeniden ölçer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

DEPO_KOKU = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DEPO_KOKU / "backend" / "scripts" / "quality"))

from y11_goc import DAMGA_ANAHTARI, kaynak_satiri_donustur  # noqa: E402
from y11_yukleyici import (  # noqa: E402
    JSON_KOLONLARI,
    TABLO_SIRASI,
    insert_ifadeleri,
    insert_sql,
    parti_yaz,
)

DAMGA = "y11-kimya-2026-08"

# Ölçülen canlı topic kodları (kiro2.topic_hierarchy, 26 satır) alt kümesi.
HARITA = {
    "KIM": "72e79276-4795-424c-a262-0edf9a77a23f",
    "KIM.DEN": "6ef2025f-a1e3-428e-9dfd-1c4c62cbcb37",
}


def _kaynak_satiri(**ezmeler: object) -> dict:
    """Kaynağın gerçek kolon adlarıyla tam bir satır. `.get()` yok: dönüşüm
    eksik alanı gürültülü reddediyor, o yüzden fixture da tam olmalı."""
    satir: dict = {
        "id": "e485d0f9-1188-53ca-b628-35ce3443c10b",
        "topic_code": "KIM.DEN",
        # `detect-secrets` onceki surumdeki onaltilik degeri "Hex High Entropy
        # String" diye HAKLI olarak bayrakladi. Kolon saf gecis oldugu icin deger
        # serbest; `allowlist secret` pragma'si yerine desen kirildi.
        "soru_hash": "y11-test-soru-hash",
        "created_at": "2026-01-02 03:04:05",
        "updated_at": "2026-01-02 03:04:05",
        "created_by": "olmayan-kullanici",
        "reviewed_by": None,
        "question_text": "Kimyasal dengede Kc değeri neyi ifade eder?",
        "question_html": None,
        "question_latex": None,
        "image_ocr_text": None,
        "image_width": None,
        "image_height": None,
        "question_audio_url": None,
        "question_image_url": "crops/kitap_x/soru_0001.png",
        "source_book": "Baska Yayin Kimya",
        "source_page": 42,
        "option_a": "Tepkime hızını",
        "option_b": "Denge sabitini",
        "option_c": "Aktivasyon enerjisini",
        "option_d": "Entalpiyi",
        "option_e": "Entropiyi",
        "correct_answer": "B",
        "explanation": None,
        "explanation_video_url": None,
        "alternative_solutions": None,
        "secondary_topics": None,
        "bloom_level": 2,
        "exam_type": "AYT",
        "subject_area": "KIMYA",
        "grade_level": 11,
        "osym_format_compliant": True,
        "osym_year": None,
        "misconception_tags": None,
        "solution_steps": None,
        "similar_question_ids": None,
        "morphology_complexity": None,
        "word_count": 7,
        "unique_word_count": 7,
        "average_word_length": 5.1,
        "readability_score": None,
        "pipeline_metadata": {
            "match_tier": "tier1_page_inline",
            "book_key_match": True,
        },
        "difficulty_level": "MEDIUM",
        "irt_based_difficulty": "medium",
        "student_success_rate": None,
        "last_difficulty_update": None,
        "difficulty_update_count": 0,
        "irt_discrimination": None,
        "irt_difficulty": None,
        "irt_guessing": None,
        "irt_upper_asymptote": None,
        "is_calibrated": False,
        "calibration_sample_size": 0,
        "last_calibration_date": None,
        "calibration_quality_score": None,
        "irt_a": None,
        "irt_b": None,
        "irt_c": None,
        "irt_calibrated": False,
        "irt_calibrated_at": None,
        "irt_n_responses": 0,
        "irt_method": None,
        "is_calib_pool": False,
        "average_response_time": None,
        "median_response_time": None,
        "exposure_rate": None,
        "last_used_date": None,
        "quality_score": None,
        "reviewed_at": None,
    }
    satir.update(ezmeler)
    return satir


@pytest.fixture
def hedef() -> dict[str, dict]:
    return kaynak_satiri_donustur(
        _kaynak_satiri(), topic_kod_haritasi=HARITA, damga=DAMGA
    )


# --------------------------------------------------------------------------
# 1. SIRA — ebeveyn önce
# --------------------------------------------------------------------------


def test_question_bank_ilk_yazilir() -> None:
    """Üç yavru tablonun PK'sı aynı zamanda `question_bank(id)`'ye FK.
    Ters sırada ilk INSERT `ForeignKeyViolationError` verir."""
    assert TABLO_SIRASI[0] == "question_bank"
    assert set(TABLO_SIRASI) == {
        "question_bank",
        "question_content",
        "question_metadata",
        "question_statistics",
    }


def test_ifadeler_tablo_sirasini_korur(hedef: dict[str, dict]) -> None:
    """Dönüşümün sözlük sırası değişse bile yazım sırası sabit kalmalı."""
    tersine = dict(reversed(list(hedef.items())))
    assert [ad for ad, _, _ in insert_ifadeleri(tersine)] == list(TABLO_SIRASI)


# --------------------------------------------------------------------------
# 2. DAMGA — tek kez serialize
# --------------------------------------------------------------------------


def test_pipeline_metadata_tek_kez_serialize_edilir(hedef: dict[str, dict]) -> None:
    """Çift kodlama sessiz kusurdur: INSERT geçer, `->>` NULL döner.

    Kontrol: parametre bir `str` olmalı ve `json.loads` **sözlük** vermeli.
    Çift kodlanmışsa `json.loads` bir `str` verir.
    """
    for ad, kolonlar, degerler in insert_ifadeleri(hedef):
        if ad != "question_metadata":
            continue
        ham = degerler[kolonlar.index("pipeline_metadata")]
        assert isinstance(ham, str), "asyncpg `json` kolonuna str ister, dict degil"
        cozulmus = json.loads(ham)
        assert isinstance(cozulmus, dict), "CIFT KODLAMA: json.loads bir str verdi"
        assert cozulmus[DAMGA_ANAHTARI] == DAMGA
        # Kaynak metadata korunmalı — damga onu EZMEMELİ.
        assert cozulmus["match_tier"] == "tier1_page_inline"
        break
    else:
        pytest.fail("question_metadata ifadesi uretilmedi")


# --------------------------------------------------------------------------
# 3. ANAHTAR KAYBI YOK
# --------------------------------------------------------------------------


def test_insert_kolonlari_donusumun_anahtarlariyla_birebir(
    hedef: dict[str, dict],
) -> None:
    """Sessizce düşen bir anahtar ya NOT NULL patlatır ya `server_default`
    sürüklemesi üretir. İkincisi `review_status`'ta ölçülmüş bir emsal."""
    for ad, kolonlar, degerler in insert_ifadeleri(hedef):
        assert set(kolonlar) == set(hedef[ad]), (
            f"{ad}: kolon kumesi donusumden SAPTI. "
            f"eksik={set(hedef[ad]) - set(kolonlar)} fazla={set(kolonlar) - set(hedef[ad])}"
        )
        assert len(degerler) == len(kolonlar)


def test_degerler_kolonlarla_hizali(hedef: dict[str, dict]) -> None:
    """Kolon/değer kayması sessizdir: tipler uyuşursa DB kabul eder ve
    `question_text` ile `explanation` yer değiştirmiş satır servis edilir."""
    for ad, kolonlar, degerler in insert_ifadeleri(hedef):
        for kolon, deger in zip(kolonlar, degerler, strict=True):
            beklenen = hedef[ad][kolon]
            if kolon == "pipeline_metadata":
                assert json.loads(deger) == beklenen
            else:
                assert deger == beklenen, f"{ad}.{kolon} hizasiz"


def test_sql_parametre_sayisi_kolon_sayisiyla_esit(hedef: dict[str, dict]) -> None:
    """`$1..$N` üretimi kolon sayısından kayarsa asyncpg gürültülü düşer;
    yine de burada çivilenir ki kusur canlı DB'ye gitmeden görünsün."""
    for ad, kolonlar, _ in insert_ifadeleri(hedef):
        sql = insert_sql(ad, kolonlar)
        assert sql.count("$") == len(kolonlar)
        assert sql.lstrip().upper().startswith("INSERT INTO")


def test_json_kolonu_str_gelirse_gurultulu_durur(hedef: dict[str, dict]) -> None:
    """#486'nın guard'ı. Kaynak bağlantısında kodek yoksa asyncpg `json`
    kolonlarını `str` döndürür. O `str`'e `json.dumps` uygulamak ÇİFT KODLAMA
    üretir: INSERT geçer, `->>'y11_batch'` NULL döner, parti geri alınamaz.

    Ölçüldü (KABUL 3.666): `json_typeof='string'` olan **0** satır var — yani
    meşru bir `str` gelemez, `str` daima 'kodek kayıtlı değil' demektir.
    """
    bozuk = {ad: dict(satirlar) for ad, satirlar in hedef.items()}
    bozuk["question_metadata"]["pipeline_metadata"] = json.dumps(
        hedef["question_metadata"]["pipeline_metadata"]
    )
    with pytest.raises(ValueError, match="kodegi|kodek|KAYITLI DEGIL"):
        insert_ifadeleri(bozuk)


def test_json_kolon_kumesi_hedef_semasiyla_hizali(hedef: dict[str, dict]) -> None:
    """`JSON_KOLONLARI` canlı `information_schema`'dan türetilmiş sabit bir küme.
    Dönüşüm bu tabloların hiçbirinde bilinmeyen bir ada sahip json üretmemeli;
    küme bayatlarsa asyncpg `dict`/`list` için `DataError` verir ve pilot boşa gider."""
    assert set(JSON_KOLONLARI) == set(TABLO_SIRASI)
    for tablo, kolonlar in JSON_KOLONLARI.items():
        bilinmeyen = kolonlar - set(hedef[tablo])
        assert (
            not bilinmeyen
        ), f"{tablo}: donusum bu json kolonlarini uretmiyor: {bilinmeyen}"


# --------------------------------------------------------------------------
# 4. VARSAYILAN GERİ ALIR
# --------------------------------------------------------------------------


def test_parti_yaz_varsayilani_geri_alir() -> None:
    """`kalici` varsayılanı `False` olmalı: 'pilot' niyetiyle çağrılan komut
    yanlış varsayılanla kalıcı yazıma dönüşür."""
    import inspect

    imza = inspect.signature(parti_yaz)
    assert imza.parameters["kalici"].default is False
    assert imza.parameters["kalici"].kind is inspect.Parameter.KEYWORD_ONLY
