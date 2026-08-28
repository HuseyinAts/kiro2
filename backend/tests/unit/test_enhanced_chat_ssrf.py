"""SSRF sertlestirme testleri — api/enhanced_chat.py URL getirme yolu.

Kaynak: CodeQL code-scanning alert #114 (py/full-ssrf, CWE-918),
backend/api/enhanced_chat.py:_fetch_url_content.

Bekci sozlesmesi:
  1. Sema http/https disi reddedilir.
  2. Cozumlenen IP private/loopback/link-local/reserved/multicast/
     unspecified ise reddedilir (169.254.169.254 = bulut metadata dahil).
  3. Cok-A-kayitli isimde IP'lerden HERHANGI biri dahili ise reddedilir.
  4. Public bir URL 3xx ile dahili bir adrese YONLENDIRSE bile, yonlendirme
     hedefi ayrica dogrulandigi icin istek dahili adrese ULASMAZ.
"""

import asyncio
from unittest.mock import patch

import pytest

from api.enhanced_chat import _fetch_url_content, _ssrf_url_guvenli


# tests/conftest.py:335 global_db_manager_cleanup SESSION-kapsamli autouse async
# fixture'i event_loop ister; pytest-asyncio 0.21.1'in varsayilan event_loop'u
# FUNCTION-kapsamli oldugundan unit/ dizininde ScopeMismatch olusur (golden-flow
# icin tests/e2e/conftest.py'de cozulen ayni sinif). Modul-lokal session
# event_loop ile bu dosyaya sinirli, izole cozum:
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class _SahteYanit:
    """httpx.Response yerine minimal ikame."""

    def __init__(self, *, status_code=200, headers=None, text=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text

    @property
    def is_redirect(self) -> bool:
        return self.status_code in (301, 302, 303, 307, 308)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


# --------------------------------------------------------------------------
# 1) Bekci birimi: sema
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "kotu_url",
    [
        "file:///etc/passwd",
        "gopher://127.0.0.1:6379/_INFO",
        "dict://localhost:11211/stats",
        "ftp://example.com/x",
    ],
)
def test_sema_disi_reddedilir(kotu_url):
    guvenli, mesaj = _ssrf_url_guvenli(kotu_url)
    assert guvenli is False
    assert "http" in mesaj


# --------------------------------------------------------------------------
# 2) Bekci birimi: dahili IP araliklari (getaddrinfo mock'lu)
# --------------------------------------------------------------------------
def _mock_getaddrinfo(ip: str):
    def _fake(host, *a, **k):
        return [(2, 1, 6, "", (ip, 0))]

    return _fake


@pytest.mark.parametrize(
    "dahili_ip",
    [
        "127.0.0.1",  # loopback
        "10.0.0.5",  # private
        "192.168.1.1",  # private
        "172.16.0.1",  # private
        "169.254.169.254",  # link-local — AWS/GCP metadata
        "0.0.0.0",  # unspecified
    ],
)
def test_dahili_ip_reddedilir(dahili_ip):
    with patch("socket.getaddrinfo", _mock_getaddrinfo(dahili_ip)):
        guvenli, mesaj = _ssrf_url_guvenli(f"http://kotu.example/{dahili_ip}")
    assert guvenli is False
    assert "engellenmistir" in mesaj


def test_public_ip_gecer():
    with patch("socket.getaddrinfo", _mock_getaddrinfo("93.184.216.34")):
        guvenli, mesaj = _ssrf_url_guvenli("http://example.com/x")
    assert guvenli is True
    assert mesaj == ""


def test_cok_a_kaydinda_bir_dahili_yeter():
    """Bir public + bir private IP karisimi engellenir (yalniz-ilk bug'i)."""

    def _iki_ip(host, *a, **k):
        return [
            (2, 1, 6, "", ("93.184.216.34", 0)),  # public
            (2, 1, 6, "", ("10.1.2.3", 0)),  # private
        ]

    with patch("socket.getaddrinfo", _iki_ip):
        guvenli, _ = _ssrf_url_guvenli("http://karisik.example/x")
    assert guvenli is False


# --------------------------------------------------------------------------
# 3) Uctan uca: public URL, metadata'ya YONLENDIRME denemesi
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_yonlendirme_ile_metadata_engellenir():
    """
    example.com (public) -> 302 -> http://169.254.169.254/... (metadata).
    Bekci yonlendirme hedefini de dogruladigi icin ikinci istek ASLA
    atilmaz; sonuc bir hata mesajidir, metadata icerigi DEGIL.
    """
    cagrilan_url = []

    class _SahteClient:
        def __init__(self, *a, **k):
            # SSRF sertlestirmesinin cekirdegi: yonlendirmeler KAPALI olmali ki
            # her hop elle dogrulanabilsin. _fetch_url_content'in bu sozlesmeyi
            # tuttugunu burada dogruluyoruz.
            assert k.get("follow_redirects") is False, (
                "SSRF: follow_redirects=False bekleniyordu"
            )

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None):
            cagrilan_url.append(url)
            # Ilk (public) istek 302 ile metadata'ya yonlendirir.
            return _SahteYanit(
                status_code=302,
                headers={"location": "http://169.254.169.254/latest/meta-data/"},
            )

    def _resolver(host, *a, **k):
        # example.com public; metadata host'u link-local.
        if host == "169.254.169.254":
            return [(2, 1, 6, "", ("169.254.169.254", 0))]
        return [(2, 1, 6, "", ("93.184.216.34", 0))]

    with (
        patch("httpx.AsyncClient", _SahteClient),
        patch("socket.getaddrinfo", _resolver),
    ):
        sonuc = await _fetch_url_content("http://example.com/paylas")

    # Yalniz ILK (public) istek atildi; metadata URL'sine GET yok.
    assert cagrilan_url == ["http://example.com/paylas"]
    assert "engellenmistir" in sonuc
    assert "meta-data" not in sonuc


@pytest.mark.asyncio
async def test_dogrudan_metadata_url_engellenir():
    """Dogrudan 169.254.169.254 verilirse hic istek atilmaz."""
    atildi = []

    class _SahteClient:
        def __init__(self, *a, **k):
            # SSRF sertlestirmesinin cekirdegi: yonlendirmeler KAPALI olmali ki
            # her hop elle dogrulanabilsin. _fetch_url_content'in bu sozlesmeyi
            # tuttugunu burada dogruluyoruz.
            assert k.get("follow_redirects") is False, (
                "SSRF: follow_redirects=False bekleniyordu"
            )

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None):
            atildi.append(url)
            return _SahteYanit(text="SECRET")

    def _resolver(host, *a, **k):
        return [(2, 1, 6, "", ("169.254.169.254", 0))]

    with (
        patch("httpx.AsyncClient", _SahteClient),
        patch("socket.getaddrinfo", _resolver),
    ):
        sonuc = await _fetch_url_content("http://169.254.169.254/latest/meta-data/")

    assert atildi == []  # hic ag istegi yok
    assert "engellenmistir" in sonuc
