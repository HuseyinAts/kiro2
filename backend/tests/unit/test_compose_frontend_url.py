"""Backend'in ürettiği kullanıcı bağlantıları GERÇEKTEN AÇIK bir frontend'e gitmeli.

NEDEN BU TEST VAR — 23 Ağu 2026'da ÖLÇÜLDÜ
------------------------------------------
S247 e-posta doğrulamayı (A1 altın yolunun 2. ayağı) kodladı. Kod doğru, testleri
yeşil, uçlar canlı. Ama üretilen bağlantı hiçbir yere gitmiyordu:

    docker exec kiro2-backend python -c "..."
    ham deger    : '<TANIMSIZ>'          # FRONTEND_URL compose'da HİÇ yok
    üretilen link: 'http://localhost:3001/eposta-dogrula?token=ORNEK'

    curl localhost:3001  ->  000   (bağlantı yok)
    curl localhost:3000  ->  200   (frontend burada)

`core/eposta_dogrulama.py:324` ve `api/auth.py:2088` varsayılanı `:3001` — bu Vite
**dev sunucusu** portu (`vite.config.ts` override'ı, CLAUDE.md'de yazılı) ve Docker
yığınında hiçbir şey orada dinlemiyor; nginx **:3000**'de. Yani SMTP (#441) canlıya
alınsaydı bile her doğrulama linki ve her veli-onay linki ölü doğacaktı.

Kusur KODDA DEĞİL: `:3001` varsayılanı Docker'sız yerel geliştirmede DOĞRU. Kusur
compose'un backend'e dağıtım gerçeğini hiç söylememesiydi.

NEDEN PORTU SABİT YAZMIYORUZ
----------------------------
`assert port == 3000` bir totoloji olurdu: frontend yarın `3002`'ye taşınsa test
yeşil kalır ve bağlantılar yine ölür — tam da bugün olan şey. Bunun yerine iki
kaynak KARŞILAŞTIRILIYOR: frontend servisinin YAYINLADIĞI host portu ile backend'in
ürettiği bağlantının işaret ettiği port. `M3` mutasyonu (frontend portunu değiştir)
bu farkı çiviliyor.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import pytest
import yaml

pytestmark = [pytest.mark.unit]

COMPOSE = Path(__file__).resolve().parents[3] / "docker-compose.yml"

# `- FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}` içinden varsayılanı ayıklar.
# Operatör kendi değerini enjekte edebilsin diye `${VAR:-...}` biçimi korunuyor;
# test yalnızca DEVREYE GİREN varsayılanı denetler.
_VARSAYILAN = re.compile(r"^\$\{FRONTEND_URL:-(?P<deger>[^}]+)\}$")


def _servisler() -> dict:
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8")).get("services") or {}


def _host_portu(port_ifadesi: str) -> int | None:
    """`"3000:3000"` ve `"127.0.0.1:3000:3000"` biçimlerinden host portunu çıkarır."""
    parcalar = str(port_ifadesi).split(":")
    if len(parcalar) < 2:
        return None
    try:
        return int(parcalar[-2])
    except ValueError:
        return None


def _frontend_host_portlari() -> list[int]:
    frontend = _servisler().get("frontend") or {}
    portlar = [_host_portu(p) for p in frontend.get("ports") or []]
    return [p for p in portlar if p is not None]


def _backend_ortami() -> list[str]:
    return [
        str(x) for x in (_servisler().get("backend") or {}).get("environment") or []
    ]


def _frontend_url_varsayilani() -> str | None:
    for girdi in _backend_ortami():
        anahtar, _, deger = girdi.partition("=")
        if anahtar.strip() != "FRONTEND_URL":
            continue
        eslesme = _VARSAYILAN.match(deger.strip())
        return eslesme.group("deger") if eslesme else deger.strip()
    return None


# ---------------------------------------------------------------------------
# Körleşme güvencesi — bu üçü düşerse aşağıdaki denetimler BOŞ KÜME üzerinde
# geçer ve hiçbir şey korumaz. Bu depoda tam bu sınıf hata iki kez yaşandı
# (S238 XPASS'leri, S246'nın `parents[2]` yüzünden ölü doğan bekçisi).
# ---------------------------------------------------------------------------


def test_compose_dosyasi_bulunuyor():
    assert COMPOSE.is_file(), f"compose dosyası yok: {COMPOSE}"


def test_frontend_servisi_host_portu_yayinliyor():
    """Frontend port yayınlamıyorsa karşılaştıracak bir gerçek yok demektir."""
    portlar = _frontend_host_portlari()
    assert portlar, (
        "`frontend` servisi hiç host portu yayınlamıyor — karşılaştırma tabanı yok. "
        f"Compose'daki servisler: {sorted(_servisler())}"
    )


def test_backend_servisinin_ortam_blogu_var():
    assert _backend_ortami(), (
        "`backend` servisinde `environment:` bloğu yok; FRONTEND_URL denetimi "
        "boş küme üzerinde geçerdi."
    )


# ---------------------------------------------------------------------------
# Asıl iddia
# ---------------------------------------------------------------------------


def test_backend_frontend_url_tanimli():
    """Tanımsız bırakmak, koddaki `:3001` dev varsayılanını devreye sokar.

    Bu satır yokken (23 Ağu 2026 ölçümü) container'da
    `'FRONTEND_URL' in os.environ` -> **False**, üretilen bağlantı
    `http://localhost:3001/...` ve o port ölüydü.
    """
    assert _frontend_url_varsayilani() is not None, (
        "`backend` servisinde FRONTEND_URL tanımlı değil. Tanımsızken "
        "core/eposta_dogrulama.py:324 ve api/auth.py:2088 `http://localhost:3001` "
        "kullanır — bu Vite DEV portu, Docker yığınında ölüdür. E-posta doğrulama "
        "ve veli onayı bağlantılarının ikisi de hiçbir yere gitmez."
    )


def test_frontend_url_gercekten_yayinlanan_porta_isaret_ediyor():
    """Bağlantının portu, frontend'in YAYINLADIĞI portlardan biri olmalı.

    Sabit `3000` beklemiyoruz bilerek: frontend taşınırsa bu test taşınmayı
    görmeli, sessizce yeşil kalmamalı.
    """
    varsayilan = _frontend_url_varsayilani()
    assert varsayilan is not None, "önce test_backend_frontend_url_tanimli'ya bak"

    ayristirilmis = urlparse(varsayilan)
    assert ayristirilmis.scheme and ayristirilmis.hostname, (
        f"FRONTEND_URL varsayılanı mutlak bir URL değil: {varsayilan!r}. "
        "Göreli değer bağlantıyı `/eposta-dogrula?token=...` hâline getirir "
        "ve e-postadan tıklanamaz."
    )

    yayinlanan = _frontend_host_portlari()
    link_portu = ayristirilmis.port or (443 if ayristirilmis.scheme == "https" else 80)
    assert link_portu in yayinlanan, (
        f"FRONTEND_URL {link_portu} portunu gösteriyor ama `frontend` servisi "
        f"{yayinlanan} portlarını yayınlıyor. Kullanıcıya gönderilen doğrulama ve "
        "veli-onay bağlantıları ölü bir adrese gider."
    )
