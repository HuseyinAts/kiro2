"""Veri deposu servisleri host'ta TUM arayuzlere acilmamali.

NEDEN BU TEST VAR — 30 Tem 2026'da OLCULDU
------------------------------------------
Elasticsearch ve Redis `0.0.0.0`'a yayinlanmisti ve ikisinde de kimlik
dogrulama yoktu. Makinenin LAN adresinden (192.168.8.2) kimliksiz olarak:

    GET  http://192.168.8.2:9200/                       -> 200
    POST http://192.168.8.2:9200/<index>/_search        -> {"correct_answer": "D"}
    TCP  192.168.8.2:6379  "PING"                       -> +PONG

Yani ayni agdaki HERHANGI bir cihaz butun sinav cevap anahtarini okuyabiliyor
ve oturum/JWT-blacklist katmanina konusabiliyordu. Kontrol kolu: ayni adreste
kapali bir port (9999) baglanti reddi verdi, yani "her seye 200 donen" bir
alet arizasi degildi.

NEDEN 127.0.0.1'E CEKMEK UYGULAMAYI KIRMAZ (olculdu)
-----------------------------------------------------
Konteynerler birbirine DOCKER AGI uzerinden konusuyor, yayinlanan host portu
uzerinden DEGIL:

    backend  ELASTICSEARCH_URL = http://turkiye_sinav_elasticsearch:9200
    backend  REDIS_URL         = redis://kiro2-redis:6379/0
    celery   REDIS_URL         = redis://kiro2-redis:6379/0

Host portu yalnizca native script/araclarin `localhost:6379` erisimi icin
vardi (compose'daki kendi yorumu bunu soyluyor) — `127.0.0.1:6379:6379` o
erisimi AYNEN korur, sadece LAN'i keser. Yani bu degisiklik yorumun
niyetini bozmuyor.

KAPSAM
------
Bu test yalnizca `docker-compose.yml`i denetler. Elasticsearch HICBIR compose
dosyasinda tanimli DEGIL (docker-compose.yml:12 yalnizca yorum birakmis);
konteyner 2025-10-18'de elle yaratilmis ve o gunden beri yonetimsiz. Onun
baglamasi bu testin ulasabilecegi bir yerde degil — operator yeniden
yaratmali. Bu bilinen bosluk asagida ayrica isaretli.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = [pytest.mark.unit, pytest.mark.security]

COMPOSE = Path(__file__).resolve().parents[3] / "docker-compose.yml"

# Imaj adinda bunlardan biri gecen servis "veri deposu" sayilir. Uygulama
# servisleri (backend/frontend) bilerek disarida: onlarin disaridan
# erisilebilir olmasi urunun ta kendisi.
VERI_DEPOSU_IMZALARI = (
    "redis",
    "postgres",
    "elasticsearch",
    "mongo",
    "memcached",
    "rabbitmq",
    "mysql",
    "mariadb",
)

YEREL_ONEKLER = ("127.0.0.1:", "localhost:", "::1:")


def _servisler() -> dict:
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8")).get("services") or {}


def _veri_depolari() -> list[tuple[str, dict]]:
    return [
        (ad, s)
        for ad, s in _servisler().items()
        if any(imza in str(s.get("image", "")).lower() for imza in VERI_DEPOSU_IMZALARI)
    ]


def test_denetlenecek_veri_deposu_bulunuyor():
    """KORLESME GUVENCESI.

    Imaj adi degisirse (orn. redis -> valkey) veya servis yeniden
    adlandirilirsa asagidaki test BOS kume uzerinde gecer ve hicbir sey
    korumaz. Bu depoda tam bu sinif hata yasandi: 0 dosya tarayan bir sir
    bekcisi aylarca yesil gorunmustu.
    """
    assert COMPOSE.is_file(), f"compose dosyasi yok: {COMPOSE}"
    depolar = _veri_depolari()
    assert depolar, (
        "Hicbir veri deposu servisi taninmadi — imza listesi guncel mi? "
        f"Mevcut servisler: {sorted(_servisler())}"
    )


@pytest.mark.parametrize(
    "ad,servis", _veri_depolari(), ids=lambda x: x if isinstance(x, str) else ""
)
def test_veri_deposu_lan_e_acilmiyor(ad: str, servis: dict):
    """Yayinlanan her port acikca yerel arayuze baglanmali.

    `"6379:6379"` Docker'da `0.0.0.0:6379:6379` demektir — LAN'daki herkes
    erisir. `"127.0.0.1:6379:6379"` ayni localhost erisimini verir, LAN'i keser.
    """
    for port in servis.get("ports") or []:
        metin = str(port)
        assert metin.startswith(YEREL_ONEKLER), (
            f"'{ad}' servisi '{metin}' portunu TUM arayuzlere aciyor. "
            f"Veri deposu LAN'a acilmamali — '127.0.0.1:{metin}' kullan. "
            "30 Tem 2026 olcumu: kimliksiz LAN erisimiyle cevap anahtari cekildi."
        )


def test_elasticsearch_compose_disi_boslugu_belgeli():
    """Bilinen bosluk: ES bu testin ulasabilecegi yerde DEGIL.

    Bu test bir 'yapilmadi' isaretidir, bir dogrulama degil. ES konteyneri
    hicbir compose dosyasinda tanimli olmadigi icin baglamasi burada
    denetlenemiyor. Biri ES'i compose'a eklerse bu test kirmiziya doner ve
    o kisi ES'i de ustteki denetime dahil etmis olur.
    """
    icerik = COMPOSE.read_text(encoding="utf-8")
    assert (
        "elasticsearch:" not in icerik
        or "image" not in icerik.split("elasticsearch:")[1][:200]
    ), (
        "Elasticsearch artik compose'da tanimli — port baglamasini "
        "test_veri_deposu_lan_e_acilmiyor kapsamina aldigini dogrula ve "
        "bu isaret testini SIL."
    )
