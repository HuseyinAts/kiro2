"""
ST-01: Smoke tests for backend startup and initialization.

Tests:
- Backend import without errors
- FastAPI instance verification
- UTF-8 encoding support
- Middleware loading
- Router loading
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from fastapi import FastAPI  # noqa: E402


def test_backend_import_no_error():
    """ST-01-01: Backend main module imports without error."""
    from main import app

    assert app is not None, "App should be initialized"


def test_app_is_fastapi_instance():
    """ST-01-02: App is a valid FastAPI instance."""
    from main import app

    assert isinstance(app, FastAPI), "App must be a FastAPI instance"
    assert app.title is not None, "App should have a title"


def test_utf8_encoding():
    """ST-01-03: UTF-8 encoding configured for Turkish characters."""
    # Test 1: System stdout encoding
    if hasattr(sys.stdout, "encoding"):
        encoding = sys.stdout.encoding
        # On Windows, after io.TextIOWrapper fix, should be UTF-8
        assert encoding is not None, "Stdout encoding should be set"

    # Test 2: Turkish string handling
    turkish_text = "İstanbul Diyarbakır Şanlıurfa"
    turkish_upper = turkish_text.upper()

    # Verify no encoding errors occurred
    assert len(turkish_upper) > 0, "Turkish text should be processable"
    assert (
        "İ" in turkish_text or "I" in turkish_upper
    ), "Turkish characters should be preserved"


def test_middleware_loaded():
    """ST-01-04: Middleware configuration is present."""
    from main import app

    # FastAPI stores middleware in user_middleware before first request
    has_middleware = (
        hasattr(app, "user_middleware") and len(app.user_middleware) > 0
    ) or (hasattr(app, "middleware_stack") and app.middleware_stack is not None)
    assert has_middleware, "App should have middleware configured"


def test_routers_loaded():
    """ST-01-05: API routers are loaded (115+ endpoints expected).

    SS10.69 -- BU TEST YANLIS YUZEYI OLCUYORDU.

    Eskiden `app.routes` uzerinde donup `path.startswith("/api")` sayiyordu.
    FastAPI 0.141'de `include_router()` her router icin `app.routes`a
    `.path`i OLMAYAN bir `_IncludedRouter` isaretcisi koyuyor ve alt rotalari
    duzlestirmiyor. Olculdu:

        app.routes toplam : 156  (151'i isaretci, 5'i /docs /redoc /openapi.json ...)
        /api ile baslayan :   0
        gercek rota       : 1214

    Yani test "Expected 10+ API routes, got 0" diyordu -- urun kusuru degil,
    ALET kusuru. `tests/rota_yuzeyi.gercek_rotalar` isaretcileri aciyor.
    """
    from main import app
    from tests.rota_yuzeyi import gercek_rotalar

    rotalar = list(gercek_rotalar(app))
    assert len(rotalar) > 50, f"Expected 50+ routes, got {len(rotalar)}"

    api_rotalari = [yol for yol, _y, _a in rotalar if yol.startswith("/api")]
    assert len(api_rotalari) > 10, (
        f"Expected 10+ API routes, got {len(api_rotalari)} "
        f"(toplam gercek rota: {len(rotalar)})"
    )


def test_no_duplicate_api_routes():
    """
    ST-01-06: No duplicate path+method pairs in runtime route surface.
    Starlette's last-registered-wins behavior silently shadows earlier handlers.

    SS10.69 -- BU BEKCI KORDU, ARTIK GORUYOR
    ----------------------------------------
    Eskiden `app.routes` uzerinde donuyordu. FastAPI 0.141'de 1214 rotanin
    yalnizca 5'i orada goruluyor (151'i `.path`i olmayan `_IncludedRouter`
    isaretcisi), yani bekci hicbir sey bulamadigi icin SAHTE YESILDI.
    Yuzey artik `tests/rota_yuzeyi` ile aciliyor.

    IKI CARPISMA SINIFI -- VE NEDEN AYRI ELE ALINIYOR
    -------------------------------------------------
    a) AYNI mantiksal router IKI KEZ kaydedilmis -> carpisan girislerin
       isleyici ADLARI birebir ayni. Zarar tekrar/israftir.
    b) FARKLI iki isleyici ayni (yol, yontem) uzerinde -> biri SESSIZCE olur.
       Tehlikeli sinif budur.

    Bu test (b)'yi civiliyor: kosulsuz kirmizi.

    (a) ORTAMA GORE DEGISIYOR -- olculdu, iki ortamda iki AYRI liste:
        yerel : /api/v1/study-rooms/* (7), POST /api/v1/analytics/web-vitals,
                GET /health
        CI    : /api/v1/revolutionary-features/* (9)
    Fark, hangi router'larin yuklenebildiginden geliyor. Bu yuzden SABIT bir
    yol listesiyle circir kurmak YANLIS ARACTIR: bir ortamda yesil, otekinde
    kirmizi olur -- ilk denemede tam olarak bu oldu ve geri alindi.

    KONTROL KOLU (aracin kendi dogrulamasi): carpisan girisler gercekten ayri
    nesneler mi, yoksa sayim ciftlemesi mi? Olculdu -- 9/9 carpismada hem rota
    nesnesi kimlikleri hem isaretci kimlikleri farkli, ve 151 isaretcinin
    151'inin `original_router`i benzersiz. Ciftleme YOK; carpismalar gercek.

    KARAR HUSEYIN'IN: ayni router'i iki kez kaydeden yukleyici girisleri
    (ornegin `misc/study_rooms` + `misc/study_rooms_stub` ayni onege)
    temizlenecek mi? Detay: docs/guvenlik-borcu.md SS10.69.
    """
    from main import app
    from tests.rota_yuzeyi import carpismalar

    bulunan = carpismalar(app)

    # (b) sinifi: carpisan isleyicilerin ADLARI farkli -> biri sessizce olu.
    tehlikeli = {k: v for k, v in bulunan.items() if len(set(v)) > 1}
    assert not tehlikeli, (
        f"{len(tehlikeli)} adet FARKLI-ISLEYICI carpismasi -- biri sessizce olu:\n"
        + "\n".join(
            f"  {yontem} {yol} -> {adlar}"
            for (yol, yontem), adlar in sorted(tehlikeli.items())
        )
        + "\n\nStarlette'te son kayit kazanir; onceki isleyici HIC calismaz."
    )
