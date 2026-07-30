"""ES yeniden indeksleme — saf mantık testleri (ES/DB gerektirmez).

NEDEN BU TESTLER VAR
--------------------
Teşhis turunda ölçüldü: ES soru index'ini uygulama içinden yazabilecek TEK yol
`elasticsearch_service.initialize_index` ve o ilk satırında ölüyor
(`create_index(mapping=...)`, gerçek parametre `mappings`). Ama NAİF onarım
daha tehlikeli: `index_question` doc_id'yi `str(question.get("id",""))` ile
kuruyor; anahtar uymazsa doc_id `""` olur, elasticsearch-py boş string'i
SKIP_IN_PATH sayıp OTOMATİK id üretir ve aynı kayıt her koşuda yeniden yazılır.

Aşağıdaki iki değişmez tam olarak o iki tuzağı kapatıyor ve ES'siz
sınanabiliyor:

  1. Boş doc_id SESSİZCE GEÇMEZ — hata fırlatır.
  2. Cevap alanları belgeye SIZAMAZ — kaynak sorgu ileride genişlese bile.

Üçüncü test, senkron tasarımının kendisini çiviliyor: kapıdan DÜŞEN kayıtlar
(`rejected` olup `mv_safe_for_beta`den çıkanlar) bir `updated_at` watermark'ı
ile YAKALANAMAZ. Bugünkü kusurun ta kendisi bu — ES'te 25.303 dokümanda
bayat `is_active` var. Bu yüzden küme farkı kullanılıyor.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.security]

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from es_reindex import (  # noqa: E402
    ALANLAR,
    YASAKLI_ALANLAR,
    _belge_kur,
    _yeni_index_adi,
    esitleme_plani,
)


def _satir(**degisiklik):
    temel = {a: f"deger-{a}" for a in ALANLAR}
    temel["id"] = "soru-1"
    temel.update(degisiklik)
    return temel


def test_bos_doc_id_sessizce_gecmez():
    """KURULU SİLAH GUARD'I.

    Boş id ile devam etmek, ES'in otomatik id üretmesine ve her koşuda çöp
    doküman birikmesine yol açardı (teşhis turunda 110.858 tahmini).
    """
    for bos in ("", "   ", None):
        with pytest.raises(ValueError, match="Bos doc_id"):
            _belge_kur(_satir(id=bos))


def test_cevap_alanlari_belgeye_sizmaz():
    """Kaynak satır cevap taşısa BİLE belge taşımamalı.

    Kontrol sorgu metnine değil ÜRETİLEN VERİYE bakıyor: biri ileride
    `SELECT`e `correct_answer` eklerse bu test kırmızıya döner.
    """
    satir = _satir(correct_answer="B", explanation="Doğru cevap: B", is_active=True)
    _doc_id, belge = _belge_kur(satir)

    assert not (YASAKLI_ALANLAR & set(belge)), f"yasakli alan sizdi: {belge.keys()}"
    assert "correct_answer" not in belge
    assert "explanation" not in belge
    # KÖRLEŞME GUARD'I: belge gerçekten dolu olmalı. Aksi halde "her şeyi at"
    # gibi bir sadeleştirme ustteki iddiaları geçirir ve index'i işlevsiz bırakır.
    assert belge["question_text"], "belge bos — indekslenecek icerik yok"
    assert belge["id"] == "soru-1"
    assert len(belge) == len(ALANLAR)


def test_esitleme_plani_iki_yonu_de_verir():
    """Kapıdan DÜŞEN kayıt watermark ile yakalanamaz; küme farkı gerekir."""
    eklenecek, silinecek = esitleme_plani({"a", "b", "c"}, {"b", "c", "d"})

    assert eklenecek == {"a"}, "kapiya yeni giren kayit eklenmeli"
    assert silinecek == {"d"}, "kapidan dusen kayit ES'ten SILINMELI"


def test_esitleme_plani_ayni_kumede_bos_doner():
    """Değişiklik yoksa iş de yok — gereksiz yazma yapılmamalı."""
    assert esitleme_plani({"a", "b"}, {"a", "b"}) == (set(), set())


def test_yeni_index_adi_damgayi_disaridan_alir():
    """Zaman damgası DIŞARIDAN veriliyor: aynı girdi aynı adı üretir.

    `datetime.now()` içeride çağrılsaydı ad her koşuda değişir ve bir takas
    prova edilemezdi (aynı adı iki kez üretmek imkânsız olurdu).
    """
    assert _yeni_index_adi("20260731") == _yeni_index_adi("20260731")
    assert _yeni_index_adi("20260731").endswith("_v20260731")


def test_mapping_ve_alanlar_tutarli():
    """Şema kayması guard'ı: MAPPING ile ALANLAR aynı kümeyi tanımlamalı.

    Biri ALANLAR'a alan ekleyip MAPPING'i unutursa ES o alanı dinamik olarak
    eşler ve tip sessizce yanlış olabilir (ör. sayı alanı `text`).
    """
    from es_reindex import MAPPING

    assert set(MAPPING["properties"]) == set(ALANLAR)


# ---------------------------------------------------------------------------
# Artımlı senkron görevi — beat kaydı ve kilit ayrımı
# ---------------------------------------------------------------------------


def test_senkron_gorevi_beat_e_kayitli_ve_matview_den_sonra():
    """Beat sırası kritik: matview 03:30, senkron 04:00.

    Ters sıra sessizce bir gün ESKİ havuzu indeksler — yani görev koşar,
    yeşil görünür ve yanlış veriyi servis eder. Bu yüzden yalnız "kayıtlı mı"
    değil, SAAT İLİŞKİSİ de çivileniyor.
    """
    from core.celery_app import celery_app

    plan = celery_app.conf.beat_schedule
    assert "sync-search-index-nightly" in plan, "ES senkronu beat'e kayitli degil"

    matview = plan["refresh-safe-pool-nightly"]["schedule"]
    senkron = plan["sync-search-index-nightly"]["schedule"]
    assert min(matview.hour) < min(
        senkron.hour
    ), f"senkron matview'den ONCE kosuyor: matview={matview}, senkron={senkron}"


def test_senkron_kilidi_matview_kilidinden_farkli():
    """Aynı advisory lock anahtarı iki FARKLI işi birbirine bloke ettirirdi.

    Senkron koşarken matview yenilemesi sessizce atlanır (veya tersi) — ikisi
    de "başarılı" raporlar, biri hiç çalışmaz.
    """
    from tasks.es_sync_tasks import _SENKRON_LOCK_KEY
    from tasks.quality_gate_tasks import _REFRESH_LOCK_KEY

    assert _SENKRON_LOCK_KEY != _REFRESH_LOCK_KEY
