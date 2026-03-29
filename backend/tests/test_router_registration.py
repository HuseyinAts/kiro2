"""
Router Registration Guard Test

RCA-1 prevention: Her app/api/*.py router dosyasının loader.py
ROUTER_MAPPING'de kayıtlı olduğunu doğrular. Kayıtsız router = 404.

Session 120 — 5 router 2+ hafta boyunca 404 döndü çünkü loader.py'ye
ekleme adımı atlanmıştı. Bu test o sorunun tekrarını engeller.
"""

from pathlib import Path

from routers.loader import ROUTER_MAPPING

# app/api/fsrs.py kasıtlı kayıtsız — eski api/fsrs.py (9 route) aktif
KNOWN_EXCEPTIONS = {"__init__", "fsrs"}


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
