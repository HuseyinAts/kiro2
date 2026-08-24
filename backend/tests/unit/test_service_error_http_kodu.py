"""ServiceError ailesi -> HTTP kodu eslemesi bekcisi (K1 / S252).

NEDEN VAR
---------
CANLI OLCUM (24 Agu 2026, jeton konteyner icinde uretildi):

    GET /api/v1/users?page=1&page_size=1
        none -> 401 | STUDENT -> 500 | TEACHER -> 500 | ADMIN -> 200 | SUPER -> 200
    KONTROL KOLU  GET /api/v1/admin/dashboard/stats
        none -> 401 | STUDENT -> 403 | TEACHER -> 403 | ADMIN -> 200 | SUPER -> 200

Yani yetkisiz ogrenciye **500 Dahili sunucu hatasi** donuyor, 403 degil.

KOK NEDEN: `api/enhanced_user_management_api.py:108` `ErrorFactory.authorization_error`
`AuthorizationError` firlatiyor. O sinif `core/exceptions.py`'deki `ServiceError`
ailesinden ve `HTTPException` DEGIL. Canli `app.exception_handlers` yalnizca
BES anahtar tasiyor (olculdu, konteynerde):
    HTTPException · RequestValidationError · WebSocketRequestValidationError
    · RateLimitExceeded · Exception
`ServiceError` icin kayit YOK -> istek generic `Exception` catch-all'ina dusuyor
-> 500. `core/exception_handlers.py:518` `setup_exception_handlers` bu aileyi
kaydediyor ama o fonksiyonun depoda HICBIR CAGIRANI YOK (olu modul).

S251 DUZELTMESI (kendi iddiamin curutulmesi)
--------------------------------------------
S251'de bu kalem (plan G5) *"degeri +0"* gerekcesiyle DUSURULMUSTU. O olcum
17 BASKA ucu proplamisti ve 17/17 403 donmustu -- dogru ama EKSIK orneklem.
Bugun karsi-ornek olculdu: bu ailenin 3 ucu 500 donuyor. Ongul curudu, kalem
geri acildi.

KAPSAM SINIRI (bilerek dar)
---------------------------
Toptan `setup_exception_handlers(app)` CAGRILMAZ: o fonksiyon
`core/exception_handlers.py:545`'te `Exception` catch-all'ini DA kaydedip
`core/application.py:354`'teki mevcut catch-all'i devirir -- blast radius
uygulama geneli. Yalniz `ServiceError` kaydedilir.

Patlama yariapi OLCULDU: `status_mapping` (core/exception_handlers.py:162-169)
yalnizca ALTI hata kodunu esliyor, gerisi 500'de KALIYOR. api/+services/ icinde
bu aileden 4 dogrudan `raise` + 7 `ErrorFactory` cagrisi var. Gercek degisim:
  AUTHORIZATION_ERROR -> 403   (K1'in kendisi)
  DATABASE_ERROR      -> 503   (1 yer: enhanced_user_management_api.py:393)
  RATE_LIMIT / QUOTA / TIMEOUT -> DEGISMIYOR (mapping'de yok, 500 kaliyor)
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.exceptions import AuthorizationError, NotFoundError, ValidationError

_APPLICATION_PY = Path(__file__).resolve().parents[2] / "core" / "application.py"


def _create_app_icindeki_cagrilar() -> set[str]:
    """`create_app()` govdesinde CAGRILAN duz fonksiyon adlari (AST ile).

    Neden AST: yorum satirlari ve docstring'ler AST'de HIC YOKTUR. Duz metin
    aramasi olsaydi `# _servis_hatasi_handleri_kaydet(app)` seklinde yorumlanmis
    bir cagriyi "var" sayardi -- deponun tekrar tekrar isirdigi tuzak.
    """
    agac = ast.parse(_APPLICATION_PY.read_text(encoding="utf-8"))
    create_app = next(
        dugum
        for dugum in ast.walk(agac)
        if isinstance(dugum, ast.FunctionDef) and dugum.name == "create_app"
    )
    return {
        dugum.func.id
        for dugum in ast.walk(create_app)
        if isinstance(dugum, ast.Call) and isinstance(dugum.func, ast.Name)
    }


def _uygulama() -> FastAPI:
    """Kaydin YAPILDIGI uygulama."""
    from core.application import _servis_hatasi_handleri_kaydet

    app = FastAPI()
    _servis_hatasi_handleri_kaydet(app)

    @app.get("/yetkisiz")
    async def yetkisiz():
        raise AuthorizationError("Bu isleme yetkiniz yok")

    @app.get("/yok")
    async def yok():
        raise NotFoundError("Soru bulunamadi", resource_type="question")

    @app.get("/gecersiz")
    async def gecersiz():
        raise ValidationError("Alan gecersiz", field="email")

    return app


def test_authorization_error_403_doner() -> None:
    """K1'in kendisi: yetki reddi 500 DEGIL 403 olmali."""
    with TestClient(_uygulama(), raise_server_exceptions=False) as istemci:
        assert istemci.get("/yetkisiz").status_code == 403


def test_not_found_error_404_doner() -> None:
    with TestClient(_uygulama(), raise_server_exceptions=False) as istemci:
        assert istemci.get("/yok").status_code == 404


def test_validation_error_400_doner() -> None:
    with TestClient(_uygulama(), raise_server_exceptions=False) as istemci:
        assert istemci.get("/gecersiz").status_code == 400


def test_kontrol_kolu_kayit_yapilmazsa_500_donerdi() -> None:
    """KONTROL KOLU: kayit olmadan ayni istisna 500 uretir.

    Bu test kirmizi olursa yukaridaki uc yesil ANLAMSIZDIR -- FastAPI zaten
    403 donduruyor olurdu ve bu bekci hicbir sey olcmuyor demektir.
    """
    app = FastAPI()

    @app.get("/yetkisiz")
    async def yetkisiz():
        raise AuthorizationError("x")

    with TestClient(app, raise_server_exceptions=False) as istemci:
        assert istemci.get("/yetkisiz").status_code == 500


def test_toptan_kurulum_cagrilmiyor() -> None:
    """Kapsam bekcisi: `setup_exception_handlers` uygulama kurulumunda kullanilmamali.

    O fonksiyon `Exception` catch-all'ini da kaydedip `core/application.py:354`
    catch-all'ini devirirdi. Yorum yaptirim degildir -- burada civilenir.

    Olcum kaynak METNI uzerinde degil, kayitli handler KUMESI uzerinde yapilir:
    metin araması docstring/yorum yuzunden yanlis-pozitif uretirdi.
    """
    from core.application import _servis_hatasi_handleri_kaydet
    from core.exceptions import ServiceError

    app = FastAPI()
    once = set(app.exception_handlers)
    _servis_hatasi_handleri_kaydet(app)
    eklenen = set(app.exception_handlers) - once

    assert eklenen == {ServiceError}, (
        f"Yalniz ServiceError kaydedilmeliydi, eklenen: {eklenen}. "
        "Toptan setup_exception_handlers cagrildiysa Exception catch-all'i da "
        "gelir ve uygulamanin kendi catch-all'ini devirir."
    )


def test_alet_dogrulamasi_ast_cikartici_calisiyor() -> None:
    """KONTROL KOLU: cikartici bilinen-CAGRILAN adlari goruyor mu.

    Bos veya eksik bir kume donerse asagidaki bekci hicbir sey olcmeden
    KIRMIZI olur ve "kayit silinmis" yanlis teshisi uretirdi.
    """
    cagrilar = _create_app_icindeki_cagrilar()
    assert {"setup_middleware", "setup_rate_limiting", "setup_routers"} <= cagrilar, (
        f"AST cikartici bilinen cagrilari goremiyor: {sorted(cagrilar)} -- "
        "alet arizali, bu dosyadaki uretim-yolu bekcisine guvenilmez"
    )


def test_kayit_create_app_icinde_gercekten_cagriliyor() -> None:
    """URETIM YOLU BEKCISI: fonksiyonu tanimlamak YETMEZ, baglanmasi gerekir.

    S252 ilk mutasyon turunde M1 (`create_app()` icindeki cagriyi yorum satiri
    yap) HICBIR testi dusurmedi: bekci fonksiyonu dogrudan cagiriyordu ve
    uretim kablosunu hic olcmuyordu. Yani kayit silinse canli uygulama yine
    500 dondurmeye baslardi ve paket yesil kalirdi. Bu test o bosluğu kapatir.
    """
    assert "_servis_hatasi_handleri_kaydet" in _create_app_icindeki_cagrilar(), (
        "create_app() ServiceError handler'ini KAYDETMIYOR. Fonksiyon tanimli "
        "olsa bile cagrilmadan canli uygulamada yetki reddi 500 doner (K1)."
    )


@pytest.mark.parametrize(
    ("hata", "beklenen"),
    [
        (AuthorizationError("a"), 403),
        (NotFoundError("b"), 404),
        (ValidationError("c"), 400),
    ],
)
def test_alt_siniflar_mro_uzerinden_kapsaniyor(hata, beklenen: int) -> None:
    """Tek `ServiceError` kaydi tum alt siniflari kapsamali (Starlette MRO).

    Bu civilenmezse birisi ileride her alt sinif icin ayri kayit eklemeye
    calisir; asil sozlesme MRO'nun calistigidir.
    """
    app = FastAPI()
    from core.application import _servis_hatasi_handleri_kaydet

    _servis_hatasi_handleri_kaydet(app)

    @app.get("/x")
    async def x():
        raise hata

    with TestClient(app, raise_server_exceptions=False) as istemci:
        assert istemci.get("/x").status_code == beklenen
