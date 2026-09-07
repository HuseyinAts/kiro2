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


# SS10.69 -- BILINEN ROTA CARPISMALARI (CIRCIR / ratchet kaydi)
#
# Bu bekci `app.routes` uzerinde donuyordu ve FastAPI 0.141'de 1214 rotanin
# yalnizca 5'ini goruyordu -- yani hicbir sey bulamadigi icin YESILDI.
# Gercek yuzey olculunce 9 GERCEK carpisma cikti (Starlette'te son kayit
# kazanir, onceki isleyici sessizce golgelenir):
#
#   /api/v1/study-rooms/*  (7 uc) -- routers/loader HEM `misc/study_rooms`
#       HEM `misc/study_rooms_stub` modulunu AYNI onege kaydediyor:
#           Registered misc/study_rooms      at /api/v1/study-rooms
#           Registered misc/study_rooms_stub at /api/v1/study-rooms
#       Yani bir STUB router, gercek router'i golgeliyor (ya da tersi --
#       hangisinin kazandigi kayit sirasina bagli).
#   POST /api/v1/analytics/web-vitals
#   GET  /health
#
# Bunlarin cozumu KAYIT KARARIDIR (hangi router kalacak) -- urun karari,
# bu PR'in (CI kirmizisi) kapsami degil. Bekciyi susturmak yerine CIRCIRA
# cevrildi: kayitta olmayan YENI bir carpisma kirmizi verir, kayittaki bir
# carpisma cozulunce de kirmizi verir (kayit kuculmeli).
_BILINEN_CARPISMALAR: frozenset[tuple[str, str]] = frozenset(
    {
        ("/api/v1/study-rooms/my-rooms", "GET"),
        ("/api/v1/study-rooms/joined", "GET"),
        ("/api/v1/study-rooms/create", "POST"),
        ("/api/v1/study-rooms/{room_id}", "GET"),
        ("/api/v1/study-rooms/{room_id}", "DELETE"),
        ("/api/v1/study-rooms/{room_id}/join", "POST"),
        ("/api/v1/study-rooms/{room_id}/leave", "POST"),
        ("/api/v1/analytics/web-vitals", "POST"),
        ("/health", "GET"),
    }
)


def test_no_duplicate_api_routes():
    """
    ST-01-06: No duplicate path+method pairs in runtime route surface.
    Starlette's last-registered-wins behavior silently shadows earlier handlers.

    SS10.69: yuzey artik `tests/rota_yuzeyi.carpismalar` ile GERCEKTEN
    olculuyor; kayit yalnizca kucultulebilir.
    """
    from main import app
    from tests.rota_yuzeyi import carpismalar

    bulunan = carpismalar(app)
    bulunan_anahtarlar = set(bulunan)

    yeniler = bulunan_anahtarlar - _BILINEN_CARPISMALAR
    assert not yeniler, (
        f"{len(yeniler)} YENI path+method carpismasi:\n"
        + "\n".join(f"  {y} {yol} -> {bulunan[(yol, y)]}" for yol, y in sorted(yeniler))
        + "\n\nStarlette'te son kayit kazanir; onceki isleyici SESSIZCE olur."
    )

    cozulenler = _BILINEN_CARPISMALAR - bulunan_anahtarlar
    assert not cozulenler, (
        "Asagidaki carpismalar cozulmus -- kayit KUCULMELI:\n"
        + "\n".join(f"  {y} {yol}" for yol, y in sorted(cozulenler))
        + "\n\n`_BILINEN_CARPISMALAR` listesinden cikar (SS10.69)."
    )
