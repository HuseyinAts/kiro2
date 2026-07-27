"""
Router Registration Guard Test

RCA-1 prevention: Her app/api/*.py router dosyasının loader.py
ROUTER_MAPPING'de kayıtlı olduğunu doğrular. Kayıtsız router = 404.

Session 120 — 5 router 2+ hafta boyunca 404 döndü çünkü loader.py'ye
ekleme adımı atlanmıştı. Bu test o sorunun tekrarını engeller.
"""

from pathlib import Path

from routers.loader import ROUTER_MAPPING

# __init__.py is not a router
KNOWN_EXCEPTIONS = {"__init__"}


def test_all_app_api_routers_registered():
    """app/api/ altındaki her router dosyası loader.py'de kayıtlı olmalı."""
    app_api = Path("app/api")
    missing = []

    for f in sorted(app_api.glob("*.py")):
        if f.stem in KNOWN_EXCEPTIONS:
            continue
        key = f"app.api.{f.stem}"
        if key not in ROUTER_MAPPING:
            missing.append(key)

    assert not missing, (
        f"Kayıtsız router(lar) bulundu: {missing}\n"
        f"routers/loader.py ROUTER_MAPPING'e ekle.\n"
        f"Kasıtlı istisna ise KNOWN_EXCEPTIONS'a ekle."
    )


def test_mapped_routers_are_importable():
    """ROUTER_MAPPING'deki her modül GERÇEKTEN import edilebilmeli.

    Dosya-adı kontrolü YETMEZ: loader.py bir modül import edilemediğinde
    WARNING yazıp DEVAM eder (routers/loader.py). Router sessizce kayıtsız
    kalır, tüm endpoint'leri 404 döner ve mevcut iki test bunu göremez —
    ikisi de yalnız dosyanın VARLIĞINA bakıyor.

    Bu sınıf 27 Tem 2026'da iki kez yakalandı, ikisi de farklı sebeple:
      app.api.cat                    → FastAPI 0.103.2'de `-> None` + 204
                                       assert'i (TÜM CAT router'ı 404'tü)
      api.alternative_solutions_api  → defaultsuz parametre defaultludan
                                       sonra (SyntaxError, 8 endpoint 404)
    İkisi de canlı logdan tesadüfen fark edildi; test yakalamadı.
    """
    import importlib

    from routers.loader import DISABLED_ROUTERS, ROUTER_MAPPING

    hatalar = []
    for eski_ad, (_kategori, modul) in sorted(ROUTER_MAPPING.items()):
        if eski_ad in DISABLED_ROUTERS:
            continue
        try:
            importlib.import_module(modul)
        except Exception as exc:
            hatalar.append(f"  {modul}\n      {type(exc).__name__}: {exc}")

    assert not hatalar, (
        f"{len(hatalar)} router import EDİLEMİYOR — endpoint'leri 404 döner:\n"
        + "\n".join(hatalar)
        + "\n\nloader.py bu hatayı WARNING'e çevirip geçer; sessiz 404 üretir."
    )


def test_registered_app_api_modules_exist():
    """ROUTER_MAPPING'deki app.api.* kayıtlarının dosyası mevcut olmalı."""
    missing = []

    for module_key in ROUTER_MAPPING:
        if not module_key.startswith("app.api."):
            continue
        stem = module_key.split(".")[-1]
        filepath = Path("app/api") / f"{stem}.py"
        if not filepath.exists():
            missing.append((module_key, str(filepath)))

    assert not missing, (
        f"ROUTER_MAPPING'de kayıtlı ama dosyası olmayan modüller: {missing}\n"
        f"Dosyayı oluştur veya ROUTER_MAPPING'den kaldır."
    )
