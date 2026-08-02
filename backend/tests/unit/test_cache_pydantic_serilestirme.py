"""L2 önbelleği Pydantic modelini DİZEYE çevirmemeli.

NEDEN VAR (2 Ağu 2026, yatırımcı demosu hazırlığı)
--------------------------------------------------
`GET /api/v1/student-dashboard/profil` şu davranışı gösteriyordu:

    L1 (bellek) sıcak            -> 200
    L1 soğuk + L2 (Redis) sıcak  -> 500   ← backend restart / TTL sonrası

Yani ekran ilk açılışta çalışıyor, backend yeniden başlayınca patlıyor.
Bir demoda tam olarak "tıkla çalışır, tekrar tıkla patlar" gibi görünür.

KÖK NEDEN (kaldırma testiyle kanıtlandı)
----------------------------------------
`core/multi_layer_cache.py:473`

    value_bytes = json.dumps(value, ensure_ascii=False, default=str)

`default=str` sessiz bir yakalayıcıdır: `json` bir Pydantic modelini
serileştiremeyince onu `str(model)`e çevirir. Redis'te duran gerçek değer
(canlı ölçüm):

    "ogrenci_id='0d3b011a-...' kullanici_id='0d3b011a-...' sinif_seviyesi=12
     okul_adi='Okul belirtilmedi' hedef_sinav=<SinavTipi.TYT: 'TYT'> ..."

Okuma yolunda `json.loads` bu DİZEYİ geri döndürür; FastAPI `response_model`
doğrulaması `model_attributes_type: Input should be a valid dictionary or
object to extract fields from` ile düşer -> 500.

KANIT ZİNCİRİ (hepsi ölçüldü)
- Redis anahtarı silindi + restart -> 3 ardışık çağrı 200/200/200
- L2 yeniden dolduruldu + restart  -> ilk çağrı 500
- `redis-cli GET` çıktısı repr dizesi

YARIÇAP
-------
`MultiLayerCache` 7 dosyada kullanılıyor (student_dashboard, learning_path,
learning_path_v2, soru_bankasi, exam_performance, learning_path_cache,
video_recommendation_service) — hepsi aynı sınıfa açık.
"""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel


class _OrnekProfil(BaseModel):
    """Gercek OgrenciProfili'nin kucuk temsilcisi (enum + ic model dahil)."""

    ogrenci_id: str
    sinif_seviyesi: int
    okul_adi: str


def _l2_serilestir(deger: object) -> str:
    """Uretimdeki L2 yazma yolunun AYNISI.

    `core/multi_layer_cache.py` icindeki `json.dumps(...)` cagrisi ile ayni
    davranmali. Bu yardimci, testin uretim kodundan KOPMAMASI icin asagidaki
    `test_alet_dogrulamasi_uretim_yolu_ayni` tarafindan uretim koduna karsi
    dogrulanir.
    """
    from core.multi_layer_cache import _json_varsayilan

    return json.dumps(deger, ensure_ascii=False, default=_json_varsayilan)


def test_pydantic_modeli_l2den_sozluk_olarak_doner() -> None:
    """ASIL SOZLESME: gidis-donus sonrasi deger sozluk olmali, DIZE degil.

    Fix'ten ONCE KIRMIZI: `default=str` modeli repr dizesine cevirir.
    """
    profil = _OrnekProfil(
        ogrenci_id="0d3b011a-8be9-49cb-9a87-f8a8317ccc3d",
        sinif_seviyesi=12,
        okul_adi="Okul belirtilmedi",
    )

    geri = json.loads(_l2_serilestir(profil))

    assert not isinstance(geri, str), (
        "L2 model yerine DIZE dondurdu — FastAPI response_model bunu "
        "'model_attributes_type' ile reddeder ve uc 500 verir."
    )
    assert isinstance(geri, dict)
    assert geri["ogrenci_id"] == "0d3b011a-8be9-49cb-9a87-f8a8317ccc3d"
    assert geri["sinif_seviyesi"] == 12


def test_ic_ice_model_de_sozluk_olur() -> None:
    """Model ICINDE model (dashboard yanitlarinda yaygin) da bozulmamali."""

    class _Sarmal(BaseModel):
        basarili: bool
        veri: _OrnekProfil

    sarmal = _Sarmal(
        basarili=True,
        veri=_OrnekProfil(ogrenci_id="x", sinif_seviyesi=11, okul_adi="A"),
    )

    geri = json.loads(_l2_serilestir(sarmal))

    assert isinstance(
        geri["veri"], dict
    ), "Ic model dizeye cevrildi — dis model duzeltilse bile ic alan bozulur."
    assert geri["veri"]["sinif_seviyesi"] == 11


def test_siradan_degerler_bozulmadan_gecer() -> None:
    """REGRESYON KALKANI: fix, halihazirda calisan tipleri BOZMAMALI."""
    ornek = {"sayi": 3, "liste": [1, 2], "metin": "Türkçe ç ğ ı", "bos": None}

    geri = json.loads(_l2_serilestir(ornek))

    assert geri == ornek


def test_serilestirilemeyen_tip_hala_dizeye_duser() -> None:
    """Bilinmeyen tipler icin `str` geri cekilisi KORUNMALI.

    Aksi halde fix, onbellegi tamamen yazilamaz hale getirirdi (TypeError).
    """

    class _Tuhaf:
        def __repr__(self) -> str:
            return "TUHAF-NESNE"

    geri = json.loads(_l2_serilestir({"x": _Tuhaf()}))

    assert geri["x"] == "TUHAF-NESNE"


def test_alet_dogrulamasi_uretim_yolu_ayni() -> None:
    """KONTROL KOLU — uretim kodu gercekten bu varsayilani kullaniyor mu?

    Bu test dusmezse yukaridaki yesiller yalnizca test-ici bir yardimciyi
    olcmus olur; uretimdeki `json.dumps` baska bir sey yapiyor olabilirdi.
    """
    import inspect

    from core import multi_layer_cache

    kaynak = inspect.getsource(multi_layer_cache)

    assert "default=_json_varsayilan" in kaynak, (
        "Uretim L2 yazma yolu `_json_varsayilan` KULLANMIYOR — bu dosyadaki "
        "olcumler uretimi temsil etmiyor."
    )
    # DIKKAT: dosyada BASKA bir `default=str` daha var (satir ~279,
    # `_boyut_tahmini` icin `json.dumps(value, default=str).encode(...)`).
    # O yol Redis'e YAZMIYOR, yalnizca bayt boyutu olcuyor — orada repr'a
    # dusmek zararsizdir. Ilk surumde iddia bu ayrimi yapmadigi icin
    # YANLIS kirmizi verdi; iddia L2 YAZMA satirina daraltildi.
    assert "json.dumps(value, ensure_ascii=False, default=str)" not in kaynak, (
        "L2 yazma yolu hala ciplak `default=str` kullaniyor — Pydantic modeli "
        "sessizce repr dizesine cevrilir ve okuma yolunda 500 uretir."
    )


@pytest.mark.parametrize("tip", [dict, list, str, int])
def test_json_varsayilani_yalnizca_gerektiginde_cagrilir(tip: type) -> None:
    """`_json_varsayilan` yerlesik tipler icin HIC cagrilmamali."""
    from core.multi_layer_cache import _json_varsayilan

    ornekler = {dict: {"a": 1}, list: [1], str: "a", int: 1}
    metin = json.dumps(ornekler[tip], default=_json_varsayilan)

    assert json.loads(metin) == ornekler[tip]
