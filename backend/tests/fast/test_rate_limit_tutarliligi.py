"""Y1 — login/register hiz siniri IKI yerde tanimli; celismemeleri gerekir.

OLCULEN KUSUR (18 Agu 2026, S229):
Ayni uc icin iki bagimsiz limitleyici var:

  api/auth.py:94-97                 login = _LOGIN_RPM (env, varsayilan 300) / 60sn
  core/advanced_rate_limiter.py:126 login = 5 / 60sn          <- middleware, KAZANAN

Canli olcum: 5 istekte HTTP 429, yanit basligi `x-ratelimit-limit: 5`.
Golden Flow'da 15 test bu yuzden dustu.

URETIM ETKISI test hatasindan buyuk: auth.py'deki 300 degeri OLCUME dayali bir
kararla konmus ve yorumunda gerekcesi yaziyor -- "workload-simulator audit: 10
esszamanli ayni-WiFi ogrenci = 10/10 HTTP 429". Yani paylasimli NAT arkasindaki
bir sinifta 6. ogrenci giris yapamiyordu.

BILINCLI SERTLESTIRME DEGILDI (olculdu): `b3be80686` (7 Agu) toplu bir
"update core services, guardrails, algorithms..." commit'i, govdesi BOS.
O commit'ten ONCE advanced_rate_limiter'da da deger **300**'du -- yani iki taraf
hizaliydi ve sweep ikisini birden 5'e dusurdu. Gerekce/test/yorum yok.

Bu test celiskinin SESSIZCE geri gelmesini engeller: iki tanim ayrisirsa duser.
Mutasyon: advanced_rate_limiter'daki degeri 5'e cevir -> bu test dusmeli.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("TESTING", "true")


@pytest.mark.parametrize(
    ("yol", "auth_anahtari"),
    [
        ("/api/v1/auth/login", "login"),
        ("/api/v1/auth/register", "register"),
    ],
)
def test_iki_limitleyici_celismemeli(yol: str, auth_anahtari: str) -> None:
    """Middleware limiti, belgelenmis uc politikasindan FARKLI olmamali.

    Farkli olursa hangisinin kazandigi cagri sirasina baglidir ve belgelenmis
    politika sessizce yalana doner -- kusurun tam olarak olculen hali buydu.
    """
    from api.auth import RATE_LIMITS
    from core.advanced_rate_limiter import AdvancedRateLimiter

    limiter = AdvancedRateLimiter()  # __init__ Redis'e BAGLANMAZ (connect() ayri)

    assert yol in limiter.endpoint_limits, (
        f"{yol} advanced_rate_limiter.endpoint_limits'ten kaldirilmis. "
        "Kaldirmak da bir karardir ama bu testin varsayimini bozar -- "
        "kaldirdiysan testi de guncelle."
    )
    assert (
        auth_anahtari in RATE_LIMITS
    ), f"'{auth_anahtari}' api/auth.py RATE_LIMITS'ten kaldirilmis."

    middleware_limit = limiter.endpoint_limits[yol]["limit"]
    politika_limit = RATE_LIMITS[auth_anahtari][0]

    assert middleware_limit == politika_limit, (
        f"{yol} icin iki hiz siniri CELISIYOR: "
        f"advanced_rate_limiter={middleware_limit} vs api/auth.py={politika_limit}. "
        "Middleware once calistigi icin kucuk olan sessizce kazanir ve "
        "belgelenmis politika yalana doner. Ikisini birlikte degistir."
    )


def test_login_limiti_paylasimli_nat_icin_yeterli() -> None:
    """Login limiti bir sinif dolusu ogrenciyi ayni IP'den tasiyabilmeli.

    Bu, degerin ne oldugundan bagimsiz bir ALT SINIR: `api/auth.py`'deki yorum
    10 esszamanli ogrencinin 10/10 429 aldigini olcmus. 30, bir sinif mevcudu
    icin makul alt sinir (okul NAT'i tek IP olarak gorunur).

    Mutasyon: limiti 5'e cevir -> bu test de duser (celiski testinden BAGIMSIZ
    olarak, cunku o test yalnizca ESITLIK arar; ikisi ayni anda 5 olsaydi
    celiski testi GECERDI ama urun hala kirik olurdu).
    """
    from core.advanced_rate_limiter import AdvancedRateLimiter

    limiter = AdvancedRateLimiter()
    limit = limiter.endpoint_limits["/api/v1/auth/login"]["limit"]

    assert limit >= 30, (
        f"login limiti {limit}/dk -- paylasimli NAT arkasindaki bir sinif icin "
        "cok dusuk. Olculmus vaka: 10 esszamanli ayni-WiFi ogrenci = 10/10 "
        "HTTP 429 (api/auth.py:90-93 yorumu). Dusurmek istiyorsan once "
        "paylasimli-IP senaryosunu olc."
    )
