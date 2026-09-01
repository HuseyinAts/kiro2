"""SSRF sertlestirme testleri -- api/enhanced_chat.py URL getirme yolu.

Kaynak: CodeQL code-scanning alert #114 -> #2976 (py/full-ssrf, CWE-918),
backend/api/enhanced_chat.py:_fetch_url_content.

Bekci sozlesmesi:
  1. Sema http/https disi reddedilir.
  2. Cozumlenen IP private/loopback/link-local/reserved/multicast/
     unspecified ise reddedilir (169.254.169.254 = bulut metadata dahil).
  3. Cok-A-kayitli isimde IP'lerden HERHANGI biri dahili ise reddedilir.
  4. Public bir URL 3xx ile dahili bir adrese YONLENDIRSE bile, yonlendirme
     hedefi ayrica dogrulandigi icin istek dahili adrese ULASMAZ.
  5. (SS10.34) Fiili istek, dogrulama sirasinda cozumlenen IP'ye PINLENIR --
     httpx/httpcore bu istek icin AYRICA getaddrinfo cagirmaz, TLS sertifika
     dogrulamasi extensions={"sni_hostname": ...} ile gercek hostname'e
     karsi calismaya devam eder. Bu, onceki surumde "bilinen kalinti
     (kabul edildi)" olarak belgelenen DNS-rebinding / TOCTOU penceresini
     kapatir.
"""

import asyncio
from unittest.mock import patch

import pytest

from api.enhanced_chat import (
    _fetch_url_content,
    _host_netloc_bicimi,
    _ssrf_guvenli_ipler,
    _ssrf_pinli_istek_bilgisi,
    _ssrf_url_guvenli,
)


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
# 2b) Bekci birimi: _ssrf_pinli_istek_bilgisi (SS10.34 -- IP-pinleme)
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "kotu_url",
    ["file:///etc/passwd", "gopher://127.0.0.1:6379/_INFO"],
)
def test_pinli_sema_disi_reddedilir(kotu_url):
    pinli_url, host_basligi, sni, hata = _ssrf_pinli_istek_bilgisi(kotu_url)
    assert pinli_url is None
    assert host_basligi is None
    assert sni is None
    assert "http" in hata


def test_pinli_dahili_ip_reddedilir():
    with patch("socket.getaddrinfo", _mock_getaddrinfo("127.0.0.1")):
        pinli_url, _, _, hata = _ssrf_pinli_istek_bilgisi("http://kotu.example/x")
    assert pinli_url is None
    assert "engellenmistir" in hata


def test_pinli_public_url_ipye_pinlenir():
    with patch("socket.getaddrinfo", _mock_getaddrinfo("93.184.216.34")):
        pinli_url, host_basligi, sni, hata = _ssrf_pinli_istek_bilgisi(
            "http://example.com/yol?q=1"
        )
    assert hata == ""
    assert pinli_url == "http://93.184.216.34/yol?q=1"
    assert host_basligi == "example.com"
    assert sni == "example.com"


def test_pinli_port_korunur():
    with patch("socket.getaddrinfo", _mock_getaddrinfo("93.184.216.34")):
        pinli_url, host_basligi, sni, _ = _ssrf_pinli_istek_bilgisi(
            "https://example.com:8443/x"
        )
    assert pinli_url == "https://93.184.216.34:8443/x"
    assert host_basligi == "example.com:8443"
    assert sni == "example.com"


def test_host_netloc_bicimi_ipv6_koseli_parantez():
    assert _host_netloc_bicimi("2001:db8::1") == "[2001:db8::1]"
    assert _host_netloc_bicimi("93.184.216.34") == "93.184.216.34"
    assert _host_netloc_bicimi("example.com") == "example.com"


def test_ssrf_guvenli_ipler_ve_url_guvenli_ayni_sonucu_verir():
    """Paylasilan dogrulama noktasi: iki cagiran da ayni girdide anlasmali."""
    with patch("socket.getaddrinfo", _mock_getaddrinfo("10.0.0.1")):
        ipler, hata1 = _ssrf_guvenli_ipler("dahili.example")
        guvenli, hata2 = _ssrf_url_guvenli("http://dahili.example/x")
    assert ipler is None
    assert guvenli is False
    assert hata1 == hata2


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
    cagrilan_headers = []
    cagrilan_extensions = []

    class _SahteClient:
        def __init__(self, *a, **k):
            # SSRF sertlestirmesinin cekirdegi: yonlendirmeler KAPALI olmali ki
            # her hop elle dogrulanabilsin. _fetch_url_content'in bu sozlesmeyi
            # tuttugunu burada dogruluyoruz.
            assert (
                k.get("follow_redirects") is False
            ), "SSRF: follow_redirects=False bekleniyordu"

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None, extensions=None):
            cagrilan_url.append(url)
            cagrilan_headers.append(headers)
            cagrilan_extensions.append(extensions)
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

    # Yalniz ILK (public) istek atildi -- pinlenmis IP formunda; metadata
    # URL'sine GET yok (dogrulama basarisiz olunca client.get hic cagrilmadi).
    assert cagrilan_url == ["http://93.184.216.34/paylas"]
    assert cagrilan_headers[0]["Host"] == "example.com"
    assert cagrilan_extensions[0] == {"sni_hostname": "example.com"}
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
            assert (
                k.get("follow_redirects") is False
            ), "SSRF: follow_redirects=False bekleniyordu"

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None, extensions=None):
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


# --------------------------------------------------------------------------
# 4) SS10.34: IP-pinleme -- DNS-rebinding / TOCTOU kapanisinin kaniti
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ip_pinlenir_ikinci_cozumleme_yok():
    """DNS-rebinding kapanisi: getaddrinfo TEK sefer cagrilir (dogrulama
    aninda), httpx'e verilen URL ZATEN o IP'nin literal'i oldugundan ayrica
    bir cozumleme adimi (ve dolayisiyla rebinding penceresi) YOKTUR.
    """
    cagri_sayisi = {"n": 0}
    cagrilan_url = []
    cagrilan_headers = []
    cagrilan_extensions = []

    class _SahteClient:
        def __init__(self, *a, **k):
            assert k.get("follow_redirects") is False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None, extensions=None):
            cagrilan_url.append(url)
            cagrilan_headers.append(headers)
            cagrilan_extensions.append(extensions)
            return _SahteYanit(text="ICERIK")

    def _resolver(host, *a, **k):
        cagri_sayisi["n"] += 1
        return [(2, 1, 6, "", ("93.184.216.34", 0))]

    with (
        patch("httpx.AsyncClient", _SahteClient),
        patch("socket.getaddrinfo", _resolver),
    ):
        sonuc = await _fetch_url_content("http://example.com/paylas")

    assert cagri_sayisi["n"] == 1  # tek cozumleme -- pinlemenin kaniti
    assert cagrilan_url == ["http://93.184.216.34/paylas"]
    assert cagrilan_headers[0]["Host"] == "example.com"
    assert cagrilan_extensions[0] == {"sni_hostname": "example.com"}
    assert sonuc == "ICERIK"
