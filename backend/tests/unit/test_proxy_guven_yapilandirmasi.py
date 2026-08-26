"""nginx arkasındaki kullanıcılar TEK rate-limit kovasını paylaşmamalı.

CANLI ÖLÇÜM (26 Ağu 2026)
------------------------
    redis-cli del ratelimit:eposta_dogrulama_gonder:172.25.0.2
    A) host'tan          -> HTTP 200, zcard=1
    B) frontend konteyneri içinden -> HTTP 200, zcard=2   <-- AYNI kova
    3 farklı X-Forwarded-For ile 3. istek -> HTTP 429
    ratelimit:*9.9.9*  -> 0 anahtar

Yani gerçekten farklı iki kaynak aynı kovayı artırdı. Üretimde bu, nginx
arkasındaki TÜM öğrencilerin `password_reset` (5/300sn) ve
`eposta_dogrulama_gonder` (5/300sn) kotalarını paylaşması demek: 6. öğrenci
doğrulama bağlantısı isteyemez. A1 altın yolunun 2. adımı çoklu kullanıcıda
bloke olur.

KÖK NEDEN VE NEDEN TEK BİR ORTAM DEĞİŞKENİ YETİYOR
---------------------------------------------------
Canlı ASGI yığınındaki üç limiter de istemciyi `request.client.host`'tan
okuyor (`core/rate_limit_middleware.py:113`, `core/auth_rate_limiting.py:87`,
ve `api/auth.py:129` fallback'i). uvicorn'un `ProxyHeadersMiddleware`'i
**varsayılan olarak açık** (`proxy_headers=True`) ve `scope["client"]`'ı zaten
yeniden yazıyor — ama `forwarded_allow_ips` varsayılanı `127.0.0.1` olduğu için
nginx'i TANIMIYOR. Ölçüldü:

    Config.proxy_headers        varsayılan = True
    Config.forwarded_allow_ips  varsayılan = None  -> '127.0.0.1'

Dolayısıyla nginx'in IP'sine güvenmek ÜÇ limiteri birden düzeltir.

🔴 NEDEN SUBNET DEĞİL, TAM IP
-----------------------------
uvicorn 0.52.4 zincirin **en sağdaki güvenilmez** adresini seçiyor (ölçüldü:
`'1.2.3.4, 5.6.7.8'` -> `'5.6.7.8'`). Bu, nginx'in `$proxy_add_x_forwarded_for`
append semantiğini spoof'a KAPALI yapar: zincir `<sahte>, <gerçek>` olur ve en
sağdaki gerçek istemcidir.

AMA tek elemanlı zincirde en sağdaki de sahtedir (`'9.9.9.9'` -> `'9.9.9.9'`).
Backend :8000 dışarıya açık olduğundan, subnet'e güvenilirse gateway
(`172.25.0.1`) de güvenilir olur ve nginx'i ATLAYAN bir istek kendi
`X-Forwarded-For`'unu dikte edebilir -> rate limit tamamen atlatılır.
Bu yüzden güven kümesi **yalnız nginx'in IP'si** olmalı.

BU BEKÇİ NE KORUYOR
-------------------
Statik IP ile `FORWARDED_ALLOW_IPS` **iki ayrı yerde** yazılı. Biri değişip
diğeri değişmezse düzeltme SESSİZCE ölür: uvicorn nginx'i tanımaz, herkes yine
tek kovaya düşer ve hiçbir test kırılmaz. Bekçi bu iki kaynağı karşılaştırır.
"""

from __future__ import annotations

import ipaddress
from pathlib import Path

import pytest
import yaml

KOK = Path(__file__).resolve().parents[3]
COMPOSE = KOK / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose() -> dict:
    if not COMPOSE.exists():  # pragma: no cover - yol kayarsa ölçüm geçersiz
        pytest.fail(f"docker-compose.yml bulunamadı: {COMPOSE}")
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def _frontend_statik_ip(compose: dict) -> str:
    aglar = compose["services"]["frontend"].get("networks") or {}
    if not isinstance(aglar, dict):
        pytest.fail(
            "frontend.networks liste biçiminde — statik IP atamak için sözlük "
            f"biçimi gerekir. Bulunan: {aglar!r}"
        )
    varsayilan = aglar.get("default") or {}
    ip = varsayilan.get("ipv4_address")
    if not ip:
        pytest.fail("frontend'e statik ipv4_address atanmamış")
    return str(ip)


def _backend_forwarded(compose: dict) -> str:
    ortam = compose["services"]["backend"].get("environment") or {}
    if isinstance(ortam, list):
        for satir in ortam:
            if str(satir).startswith("FORWARDED_ALLOW_IPS="):
                return str(satir).split("=", 1)[1]
        pytest.fail("backend ortamında FORWARDED_ALLOW_IPS yok (liste biçimi)")
    deger = ortam.get("FORWARDED_ALLOW_IPS")
    if not deger:
        pytest.fail("backend ortamında FORWARDED_ALLOW_IPS yok")
    return str(deger)


def _default_subnet(compose: dict) -> str:
    ag = (compose.get("networks") or {}).get("default") or {}
    yapilandirma = ((ag.get("ipam") or {}).get("config")) or []
    if not yapilandirma or "subnet" not in yapilandirma[0]:
        pytest.fail(
            "networks.default sabit subnet ilan etmiyor — Docker rastgele atar "
            "ve statik IP her ağ yeniden yaratıldığında kayar"
        )
    return str(yapilandirma[0]["subnet"])


# ---------------------------------------------------------------------------
# Alet doğrulaması
# ---------------------------------------------------------------------------


def test_alet_dogrulamasi_compose_ayristirilabiliyor(compose: dict) -> None:
    """Ayrıştırma sessizce boş dönerse aşağıdaki testler BOŞ geçerdi."""
    assert "services" in compose
    for servis in ("backend", "frontend"):
        assert servis in compose["services"], f"{servis} servisi yok"


# ---------------------------------------------------------------------------
# Yapılandırma
# ---------------------------------------------------------------------------


def test_default_agi_sabit_subnet_ilan_ediyor(compose: dict) -> None:
    ag = ipaddress.ip_network(_default_subnet(compose))
    assert ag.prefixlen <= 24, f"subnet fazla dar: {ag}"


def test_frontend_statik_ip_subnet_icinde(compose: dict) -> None:
    ip = ipaddress.ip_address(_frontend_statik_ip(compose))
    ag = ipaddress.ip_network(_default_subnet(compose))
    assert ip in ag, f"{ip} ilan edilen subnet {ag} içinde değil"


def test_statik_ip_dinamik_atama_araliginda_degil(compose: dict) -> None:
    """Docker düşük adresleri sırayla dağıtır; çakışırsa konteyner açılmaz.

    Ölçüldü (26 Ağu 2026): mevcut 6 konteyner .2–.7 aralığında.
    """
    ip = ipaddress.ip_address(_frontend_statik_ip(compose))
    ag = ipaddress.ip_network(_default_subnet(compose))
    ilk_yuz = list(ag.hosts())[:100]
    assert ip not in ilk_yuz, (
        f"{ip} Docker'ın sıralı dağıttığı ilk 100 adres içinde — başka bir "
        "konteyner bu adresi kapabilir ve frontend açılmaz"
    )


# ---------------------------------------------------------------------------
# İki bağımsız kaynağın hizası — bu testin ASIL sebebi
# ---------------------------------------------------------------------------


def test_forwarded_allow_ips_frontend_statik_ipsiyle_ayni(compose: dict) -> None:
    """İKİ BAĞIMSIZ KAYNAK AYNI OLMALI — bu dosyanın asıl sebebi."""
    statik = _frontend_statik_ip(compose)
    guvenilen = _backend_forwarded(compose)
    assert guvenilen == statik, (
        f"FORWARDED_ALLOW_IPS={guvenilen!r} ile frontend statik IP {statik!r} "
        "AYRIŞMIŞ. Bu sürüklenme SESSİZDİR: uvicorn nginx'i tanımaz, herkes "
        "yine tek rate-limit kovasına düşer ve hiçbir test kırılmaz."
    )


def test_forwarded_allow_ips_subnet_veya_gateway_icermez(compose: dict) -> None:
    """Güven kümesi genişletilirse rate limit ATLATILABİLİR hale gelir.

    uvicorn zincirin en sağdaki güvenilmez adresini alır; tek elemanlı zincirde
    bu, istemcinin dikte ettiği değerdir (ölçüldü: `'9.9.9.9'` -> `'9.9.9.9'`).
    Backend :8000 dışarıya açık olduğu için, gateway güvenilirse nginx'i atlayan
    bir istek kendi IP'sini uydurup her istekte yeni kova açabilir.
    """
    guvenilen = _backend_forwarded(compose)
    assert "/" not in guvenilen, (
        f"FORWARDED_ALLOW_IPS={guvenilen!r} bir AĞ bloğu. Subnet güvenilirse "
        "gateway de güvenilir olur ve :8000'e doğrudan gelen istek "
        "X-Forwarded-For'unu dikte edebilir."
    )
    assert guvenilen != "*", "FORWARDED_ALLOW_IPS='*' herkese güvenir"

    ag = ipaddress.ip_network(_default_subnet(compose))
    gateway = str(next(ag.hosts()))
    assert guvenilen != gateway, (
        f"FORWARDED_ALLOW_IPS gateway'i ({gateway}) gösteriyor — nginx'i atlayan "
        "her istek güvenilir sayılır"
    )
