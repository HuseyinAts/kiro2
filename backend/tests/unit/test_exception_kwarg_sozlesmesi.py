"""Bekci: core/exceptions.py sinif cagrilarinda KABUL EDILMEYEN kwarg olmamali.

Neden var (S250, 24 Agu 2026 olcumu):
`core/exceptions.py` iki kusak barindiriyor -- Gen-1 `ServiceError` (:12) ve
Gen-2 `EnhancedServiceError` (:233, `severity` kabul eder). Bazi siniflar Gen-1'de
kalirken cagri yerleri Gen-2 sozlesmesiyle yazilmis. Sonuc: yetki reddi veya
veritabani hatasi yerine **TypeError** firliyor ve istemci 500 goruyor.
Olcum: 24 ihlal / 8 dosya; `core/query_builder.py:867` konteynerde gercek bir
bozuk session ile kosulup TypeError uretildigi dogrulandi.

Bu dosya bir OLCUM ALETI degil KAPI'dir: esik SIFIR.

Bekcinin kendi bekcisi: `test_tarayici_*` testleri tarayicinin GORDUGUNU kanitlar.
Yanlis-SIFIR bir ilerleme sayacinda tek kabul edilemez hata turudur -- isi sessizce
bitmis gosterir. Ayni oturumda uc bekci tam bu sekilde olu dogmustu
(`.claude/rules/audit-methodology.md` -> "Olcum aletini dogrula").
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]

# Uretim disi gurultu: kendi testlerimiz, sanal ortam, goc dosyalari, gecici scriptler
HARIC_DIZIN = (
    "tests",
    "venv",
    ".venv",
    "node_modules",
    "alembic",
    "__pycache__",
    "scripts",
)

# Bir dosya exceptions'tan import etmiyorsa AST'ye hic girmeye gerek yok (1300+ dosya).
IMPORT_IZI = "exceptions import"

# Iki AYRI "imza bilinmiyor" hali var ve karistirilirlarsa bekci yanlis-pozitif uretir:
#   _ESNEK  -> sinifin ``**kwargs``i var; her kwarg'i kabul eder, ATADAN MIRAS ALINMAZ
#   _MIRAS  -> sinifin hic __init__'i yok; imza atadan cozulur
# Ilk surumde ikisi de None idi: ``**kwargs``li sinif atanin dar imzasiyla yargilaniyordu.
_ESNEK = object()
_MIRAS = object()


def _sinif_imzalari(kaynak: str) -> dict[str, set[str] | None]:
    """Her sinif icin __init__'in kabul ettigi kwarg adlari.

    None = yargilanamaz (``**kwargs`` var ya da imza cozulemedi).
    """
    ham: dict[str, tuple[list[str], object]] = {}

    for dugum in ast.walk(ast.parse(kaynak)):
        if not isinstance(dugum, ast.ClassDef):
            continue
        atalar = [a.id for a in dugum.bases if isinstance(a, ast.Name)]
        init = next(
            (
                g
                for g in dugum.body
                if isinstance(g, ast.FunctionDef) and g.name == "__init__"
            ),
            None,
        )
        if init is None:
            ham[dugum.name] = (atalar, _MIRAS)
            continue
        if init.args.kwarg is not None:
            ham[dugum.name] = (atalar, _ESNEK)
            continue
        kabul = {a.arg for a in init.args.args if a.arg != "self"}
        kabul |= {a.arg for a in init.args.kwonlyargs}
        ham[dugum.name] = (atalar, kabul)

    def coz(ad: str, derinlik: int = 0) -> set[str] | None:
        if derinlik > 10 or ad not in ham:
            return None
        atalar, kabul = ham[ad]
        if kabul is _ESNEK:
            return None  # **kwargs -> ATADAN MIRAS ALMA, yargilanamaz
        if kabul is not _MIRAS:
            return kabul  # type: ignore[return-value]
        for ata in atalar:
            miras = coz(ata, derinlik + 1)
            if miras is not None:
                return miras
        return None

    return {ad: coz(ad) for ad in ham}


def _exceptions_import_adlari(agac: ast.Module) -> dict[str, str]:
    """Bu dosyada core.exceptions'tan gelen isimler: yerel_ad -> kaynak_ad.

    ``as`` takma adlarini izler. Ayni adi baska modulden alan dosya
    (ornek: core/authorization.py kendi AuthorizationError'unu tanimlar) disarida kalir.
    """
    esleme: dict[str, str] = {}
    for dugum in ast.walk(agac):
        if not isinstance(dugum, ast.ImportFrom) or dugum.module is None:
            continue
        if not (
            dugum.module.endswith("exceptions")
            and ("core" in dugum.module or dugum.level > 0)
        ):
            continue
        for ad in dugum.names:
            esleme[ad.asname or ad.name] = ad.name
    return esleme


def _ihlalleri_bul(
    kaynak: str, imzalar: dict[str, set[str] | None]
) -> list[tuple[int, str, list[str]]]:
    """(satir, sinif_adi, fazla_kwarglar) -- kabul edilmeyen kwarg veren cagrilar.

    AST kullaniyoruz cunku bir deseni ANLATAN yorum o deseni ICERIR: duz metin
    aramasi docstring'deki ornegi gercek cagri sanar.
    """
    agac = ast.parse(kaynak)
    yerel = _exceptions_import_adlari(agac)
    if not yerel:
        return []

    ihlaller: list[tuple[int, str, list[str]]] = []
    for dugum in ast.walk(agac):
        if not isinstance(dugum, ast.Call) or not isinstance(dugum.func, ast.Name):
            continue
        kaynak_ad = yerel.get(dugum.func.id)
        if kaynak_ad is None:
            continue
        kabul = imzalar.get(kaynak_ad)
        if kabul is None:  # bilinmeyen sinif ya da **kwargs -> yargilanamaz
            continue
        fazla = [
            k.arg for k in dugum.keywords if k.arg is not None and k.arg not in kabul
        ]
        if fazla:
            ihlaller.append((dugum.lineno, kaynak_ad, fazla))
    return ihlaller


def _uretim_dosyalari() -> list[Path]:
    dosyalar = []
    for yol in BACKEND.rglob("*.py"):
        bagil = f"/{yol.relative_to(BACKEND).as_posix()}"
        if any(f"/{h}/" in bagil for h in HARIC_DIZIN) or yol.name.startswith("_"):
            continue
        dosyalar.append(yol)
    return dosyalar


def _kanon_imzalar() -> dict[str, set[str] | None]:
    return _sinif_imzalari(
        (BACKEND / "core" / "exceptions.py").read_text(encoding="utf-8")
    )


# --------------------------------------------------------------------------- KAPI


def test_uretim_kodunda_kabul_edilmeyen_kwarg_yok():
    """Esik SIFIR: hicbir uretim cagrisi exceptions.py imzasinin disina cikmamali."""
    imzalar = _kanon_imzalar()
    bulgular: list[str] = []
    taranan = 0

    for yol in _uretim_dosyalari():
        try:
            kaynak = yol.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if IMPORT_IZI not in kaynak:
            continue
        taranan += 1
        try:
            ihlaller = _ihlalleri_bul(kaynak, imzalar)
        except SyntaxError:
            continue
        bagil = yol.relative_to(BACKEND).as_posix()
        bulgular += [
            f"{bagil}:{satir} {sinif}(...) kabul edilmeyen kwarg: {fazla}"
            for satir, sinif, fazla in ihlaller
        ]

    # Alt sinir: tarayici hic dosya gormediyse yesil olmasi ANLAMSIZ (yanlis-SIFIR).
    assert (
        taranan >= 20
    ), f"Tarayici yalnizca {taranan} dosya gordu -- kapsam coktu, sonuc guvenilmez"

    assert not bulgular, (
        "exceptions.py imzasi disinda kwarg veren cagrilar (TypeError -> HTTP 500):\n"
        + "\n".join(bulgular)
    )


# ------------------------------------------------------------------- KONTROL KOLU


def test_tarayici_sentetik_ihlali_goruyor():
    """Kontrol kolu: bilinen-KOTU girdi ihlal olarak isaretlenmeli.

    Bu test dusmeden yukaridaki kapinin yesili bir sey KANITLAMAZ.
    """
    imzalar = {"DatabaseError": {"message", "operation"}}
    kaynak = (
        "from core.exceptions import DatabaseError\n"
        "raise DatabaseError(message='x', operation='y', details={'a': 1})\n"
    )
    assert _ihlalleri_bul(kaynak, imzalar) == [(2, "DatabaseError", ["details"])]


def test_tarayici_dogru_cagriyi_ihlal_saymiyor():
    """Kontrol kolu (ters yon): bilinen-IYI girdi temiz gecmeli."""
    imzalar = {"DatabaseError": {"message", "operation"}}
    kaynak = "from core.exceptions import DatabaseError\nraise DatabaseError(message='x', operation='y')\n"
    assert _ihlalleri_bul(kaynak, imzalar) == []


def test_tarayici_docstringdeki_ornegi_ihlal_saymiyor():
    """Bir deseni ANLATAN yorum o deseni ICERIR -- AST onu gormemeli."""
    imzalar = {"DatabaseError": {"message", "operation"}}
    kaynak = (
        "from core.exceptions import DatabaseError\n"
        "def f():\n"
        "    '''Yanlis kullanim ornegi: DatabaseError(message=..., details={...})'''\n"
        "    # ayrica yorumda da: DatabaseError(details={'a': 1})\n"
        "    return None\n"
    )
    assert _ihlalleri_bul(kaynak, imzalar) == []


def test_tarayici_alias_importu_izliyor():
    """``as`` takma adiyla gizlenen ihlal de yakalanmali."""
    imzalar = {"DatabaseError": {"message", "operation"}}
    kaynak = "from core.exceptions import DatabaseError as DbErr\nraise DbErr('x', details={'a': 1})\n"
    assert _ihlalleri_bul(kaynak, imzalar) == [(2, "DatabaseError", ["details"])]


def test_tarayici_baska_modulun_ayni_adli_sinifini_yargilamaz():
    """core/authorization.py kendi AuthorizationError'unu tanimlar -- karistirilmamali."""
    imzalar = {"AuthorizationError": {"message"}}
    kaynak = "from core.authorization import AuthorizationError\nraise AuthorizationError(detail='x')\n"
    assert _ihlalleri_bul(kaynak, imzalar) == []


def test_davranis_require_role_yetkisizde_authorization_error_firlatir():
    """Statik sozlesme yesili yetmez: kapi CALISMA ZAMANINDA da dogru tipi firlatmali.

    Duzeltme oncesi bu cagri ``TypeError`` firlatiyordu (yetki reddi degil, cokme).
    """
    from core.enhanced_authentication import AuthenticationContext
    from core.exceptions import AuthorizationError

    ctx = AuthenticationContext(user_id="u1", role="student")

    try:
        ctx.require_role("admin")
    except AuthorizationError as hata:
        assert hata.details["user_role"] == "student"
        assert hata.details["required_roles"] == ["admin"]
        assert hata.error_code == "AUTHORIZATION_ERROR"
    except TypeError as hata:  # pragma: no cover  # regresyon isareti: bu dal calisirsa kusur geri gelmis
        raise AssertionError(f"Yetki reddi yerine cokme: {hata}") from hata
    else:
        raise AssertionError("Yetkisiz rol icin hic hata firlatilmadi")


def test_davranis_require_permission_yetkisizde_authorization_error_firlatir():
    from core.enhanced_authentication import AuthenticationContext
    from core.exceptions import AuthorizationError

    ctx = AuthenticationContext(user_id="u1", role="student", permissions=["read"])

    try:
        ctx.require_permission("manage_users")
    except AuthorizationError as hata:
        assert hata.details["required_permission"] == "manage_users"
        assert hata.details["user_permissions"] == ["read"]
    except TypeError as hata:  # pragma: no cover  # regresyon isareti: bu dal calisirsa kusur geri gelmis
        raise AssertionError(f"Yetki reddi yerine cokme: {hata}") from hata
    else:
        raise AssertionError("Yetkisiz izin icin hic hata firlatilmadi")


def test_davranis_require_role_eslesince_firlatmaz():
    """Kontrol kolu: mutlu yol degismemis olmali (yalniz RED dali duzeltildi)."""
    from core.enhanced_authentication import AuthenticationContext

    ctx = AuthenticationContext(user_id="u1", role="admin")
    assert ctx.require_role("admin") is None


def test_davranis_database_error_details_operation_ile_birlesir():
    """22 cagri yerinin gonderdigi ``details`` artik kaybolmadan details'e girmeli."""
    from core.exceptions import DatabaseError

    hata = DatabaseError(
        message="Query execution failed",
        operation="query_builder_all",
        details={"model": "User", "error": "boom"},
    )
    assert hata.details == {
        "operation": "query_builder_all",
        "model": "User",
        "error": "boom",
    }


def test_davranis_database_error_eski_imzasi_bozulmadi():
    """Regresyon: ``details`` verilmeyen eski cagrilar birebir ayni davranmali."""
    from core.exceptions import DatabaseError

    assert DatabaseError("x", "select").details == {"operation": "select"}
    assert DatabaseError("x").details == {}
    assert str(DatabaseError("x")) == "x", "Gen-1 __str__ bicimi korunmali"


def test_imza_cozucu_kwargs_li_sinifi_yargilamiyor():
    """``**kwargs`` alan sinif her seyi kabul eder -> None (yargilanamaz) donmeli."""
    kaynak = (
        "class Taban:\n"
        "    def __init__(self, message, details=None): ...\n"
        "class Esnek(Taban):\n"
        "    def __init__(self, message, **kwargs): ...\n"
        "class Miras(Taban):\n"
        "    pass\n"
    )
    imzalar = _sinif_imzalari(kaynak)
    assert imzalar["Taban"] == {"message", "details"}
    assert imzalar["Esnek"] is None
    assert imzalar["Miras"] == {
        "message",
        "details",
    }, "__init__'siz sinif atadan miras almali"
