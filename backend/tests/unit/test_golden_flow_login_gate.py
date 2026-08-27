"""Golden Flow login kapisi sozlesmesi (#462 / B4).

NEDEN VAR
---------
30 Tem 2026 olcumu: 178 Golden Flow testinin **148'i SKIP** oluyordu, 147'si
rate-limit yuzunden. Sebep `tests/e2e/test_golden_flows.py::_login` — HER
non-200 yaniti `pytest.skip`'e ceviriyordu. Her test ayri login attigi icin
31. testten sonra hepsi HTTP 429 aliyor ve sessizce atlaniyordu.

`.claude/rules/golden-flows.md` bu pakete "Merge block" yetkisi veriyor, ama
**skip ASLA FAIL uretmez** — yani yesil bir GF kosumu hicbir sey kanitlamiyordu.

SOZLESME
--------
1. **429 = SKIP DEGIL, FAIL.** Rate-limit "ortam yok" demek degil, "kapinin
   kendisi bozuk" demek. Skip'e cevirmek yalan rapor uretir.
2. **401/403 = SKIP MESRU.** Seed verisi yoksa test kosulamaz; bu gercekten
   ortam eksikligidir.
3. **Token onbellege alinir.** Rol basina TEK login. 178 login yerine 4 ->
   rate-limit basinci yapisal olarak ortadan kalkar (asil duzeltme budur;
   429'u FAIL yapmak yalnizca yalani gorunur kilar).

Bu dosya `_login`'i SAHTE istemciyle sinar; canli backend GEREKTIRMEZ.
"""

from __future__ import annotations

from typing import Any

import pytest

# pytest.fail/skip `BaseException` turetir — `pytest.raises(Exception)` onlari
# YAKALAMAZ. Ilk surumumde tam bu hata vardi: 401 testi kendisi "skipped" oldu
# ve hicbir sey olcmedi. Gercek siniflari dogrudan import ediyoruz.
from _pytest.outcomes import Failed, Skipped

from tests.e2e import test_golden_flows as gf

pytestmark = [pytest.mark.unit]

# Sahte istemciye verilen uydurma kimlik — HTTP'ye hic cikmaz, gercek hesap degil.
KIMLIK = {
    "email": "ogrenci@kiro2.com",
    "password": "parola",  # pragma: allowlist secret
}


class _SahteYanit:
    def __init__(self, kod: int, govde: dict[str, Any] | None = None) -> None:
        self.status_code = kod
        self._govde = govde or {}
        self.text = str(self._govde)

    def json(self) -> dict[str, Any]:
        return self._govde


class _SahteIstemci:
    """post() cagrilarini sayan minimal httpx.Client taklidi."""

    def __init__(self, *yanitlar: _SahteYanit) -> None:
        self._yanitlar = list(yanitlar)
        self.cagri_sayisi = 0

    def post(self, yol: str, json: dict[str, Any] | None = None) -> _SahteYanit:
        self.cagri_sayisi += 1
        return self._yanitlar[min(self.cagri_sayisi - 1, len(self._yanitlar) - 1)]


@pytest.fixture(autouse=True)
def _onbellegi_temizle():
    """Testler arasi sizinti olmasin — onbellek modul duzeyinde."""
    gf._TOKEN_ONBELLEGI.clear()
    yield
    gf._TOKEN_ONBELLEGI.clear()


def test_200_token_donduruyor() -> None:
    """KONTROL KOLU: mutlu yol calismazsa asagidaki testler anlamsiz."""
    istemci = _SahteIstemci(_SahteYanit(200, {"access_token": "abc"}))
    assert gf._login(istemci, KIMLIK) == "abc"


def test_429_fail_uretir_skip_degil() -> None:
    """Rate-limit kapinin bozuklugudur; skip'e cevrilirse kapi yalan soyler.

    MUTASYON: `_login`'deki 429 dali silinirse bu test Skipped alir ve DUSER.
    """
    istemci = _SahteIstemci(_SahteYanit(429, {"detail": "Too Many Requests"}))
    with pytest.raises(BaseException) as kutu:
        gf._login(istemci, KIMLIK)
    assert not isinstance(kutu.value, Skipped), (
        "429 SKIP'e cevrildi — kapi rate-limit altinda yesil rapor verir. "
        "148/178 skip vakasinin tam kok nedeni budur."
    )
    assert isinstance(
        kutu.value, Failed
    ), f"beklenen Failed, gelen {type(kutu.value).__name__}"


def test_401_skip_uretir() -> None:
    """Seed yoksa skip MESRU — bu dal korunmali (asiri duzeltme olmasin)."""
    istemci = _SahteIstemci(_SahteYanit(401, {"detail": "Invalid credentials"}))
    with pytest.raises(BaseException) as kutu:
        gf._login(istemci, KIMLIK)
    assert isinstance(kutu.value, Skipped), (
        "401 FAIL'e cevrildi — seed'siz ortamda paket kirmiziya doner, "
        "bu da ayri bir yalan olur"
    )


def test_token_onbellekleniyor_tek_login() -> None:
    """Rol basina TEK login — 178 login yerine 4.

    Asil duzeltme bu: rate-limit basincini yapisal olarak kaldirir.
    MUTASYON: onbellek satiri silinirse cagri_sayisi 3 olur ve test DUSER.
    """
    istemci = _SahteIstemci(_SahteYanit(200, {"access_token": "tok"}))
    assert gf._login(istemci, KIMLIK) == "tok"
    assert gf._login(istemci, KIMLIK) == "tok"
    assert gf._login(istemci, KIMLIK) == "tok"
    assert (
        istemci.cagri_sayisi == 1
    ), f"onbellek calismiyor: {istemci.cagri_sayisi} HTTP login atildi, 1 bekleniyordu"


def test_farkli_roller_ayri_onbellek() -> None:
    """Ogrenci token'i ogretmene servis edilmemeli."""
    istemci = _SahteIstemci(
        _SahteYanit(200, {"access_token": "ogrenci-tok"}),
        _SahteYanit(200, {"access_token": "ogretmen-tok"}),
    )
    assert gf._login(istemci, {"email": "a@k.com", "password": "p"}) == "ogrenci-tok"
    assert gf._login(istemci, {"email": "b@k.com", "password": "p"}) == "ogretmen-tok"
    assert istemci.cagri_sayisi == 2


def test_cikis_yapan_test_onbellegi_kullanmamali() -> None:
    """SINIF BEKCISI — #462'nin YARATTIGI regresyonu civiler.

    Onbellek eklendiginde GF1x (`/auth/cikis`) PAYLASILAN token'i blacklist'ledi;
    ondan sonraki **148** test olu token aldi ve `-x` yuzunden kapi 13. testte
    KALICI KIRMIZI oldu. Yani fix, duzeltmeye calistigi yalani baska bir
    kiliga soktu.

    KURAL: token'i gecersiz kilan (`/auth/cikis`) her test `_login_taze`
    kullanmali — onbellege hic girmeyen kendi token'ini almali. Boylece
    zehirlenme YAPISAL olarak imkansiz; temizlik adimina veya test sirasina
    bagli degil.

    MUTASYON: GF1x'i `_login`e geri cevir -> bu test DUSER.
    """
    import ast
    from pathlib import Path

    kaynak = Path(gf.__file__).read_text(encoding="utf-8")
    agac = ast.parse(kaynak)

    def _cagrilan_adlar(dugum: ast.AST) -> set[str]:
        return {
            d.func.id
            for d in ast.walk(dugum)
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Name)
        }

    def _metin(dugum: ast.AST) -> str:
        return " ".join(
            d.value
            for d in ast.walk(dugum)
            if isinstance(d, ast.Constant) and isinstance(d.value, str)
        )

    suclular: list[str] = []
    cikis_yapan = 0
    for d in ast.walk(agac):
        if not isinstance(d, ast.FunctionDef) or not d.name.startswith("test_"):
            continue
        if "auth/cikis" not in _metin(d):
            continue
        cikis_yapan += 1
        if "_login" in _cagrilan_adlar(d):
            suclular.append(f"{d.name} (satir {d.lineno})")

    # ALET DOGRULAMASI: hic cikis yapan test bulunamazsa bekci BOS kume
    # uzerinde sessizce gecerdi (bu depoda "0 satir tarandi, sorun yok"
    # sahte yesili yasandi).
    assert cikis_yapan > 0, (
        "`auth/cikis` cagiran hicbir test bulunamadi -> bekci hicbir sey "
        "olcmuyor. Desen degistiyse bu test guncellenmeli."
    )
    assert not suclular, (
        "Token'i gecersiz kilan test PAYLASILAN onbellegi kullaniyor -> "
        f"sonraki testler olu token alir (#462 regresyonu): {suclular}. "
        "`_login_taze` kullan."
    )

    # KENDI BOSLUGUM (1 Agu, 4. kez ayni tuzak): bu bekcinin ilk surumu yalnizca
    # CAGRI adlarina bakiyordu. `git checkout HEAD --` `_login_taze` TANIMINI
    # sildi, elle geri alimim yalniz CAGRIYI geri koydu -> dosyada tanimsiz
    # fonksiyona cagri kaldi (178 test NameError) ve bekci 7/7 YESIL dondu.
    # Yesil test, kendi yarattigim kirilmayi GIZLEDI. Cozumleme kontrolu sart.
    tanimli = {
        n.name
        for n in ast.walk(agac)
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    for yardimci in ("_login", "_login_taze", "_auth_headers"):
        assert yardimci in tanimli, (
            f"`{yardimci}` CAGRILIYOR ama TANIMLI DEGIL -> paket toplanirken "
            "NameError verir. (Bu kontrol olmadan bekci yesil kalip kirilmayi gizler.)"
        )


def test_token_yoksa_assert_duser() -> None:
    """200 ama govdede token yok -> sessiz gecmemeli."""
    istemci = _SahteIstemci(_SahteYanit(200, {}))
    with pytest.raises(AssertionError):
        gf._login(istemci, KIMLIK)


def test_gf_istemcisi_baglanti_yeniden_kullanmiyor() -> None:
    """KOSUM HATTI SOZLESMESI (S255) -- havuzdaki baglanti YENIDEN KULLANILMAZ.

    Olculdu: paket ~%13 oranda `httpx.RemoteProtocolError: Server
    disconnected without sending a response` ile dusuyordu. Dusen istek her
    seferinde HAVUZDAN gelen bir baglanti uzerindeydi ve sunucu o istegi HIC
    GORMUYORDU (konteyner gunlugunde ne 500 ne erisim satiri; uvicorn
    RestartCount=0, OOM yok) -- yani baglanti istemci ile uygulama ARASINDA
    dusuyordu. Kok neden KANITLANMADI; dort hipotez olculup curutuldu
    (login rate-limit, idle timeout, 5 sn keep-alive yarisi, hizli ates).

    `max_keepalive_connections=0` bayat-baglanti yarisini YAPISAL OLARAK
    imkansiz kilar. A/B olcumu: oncesi ~4/30 dusme, sonrasi **35/35 temiz**
    (ayni taban oranda tesadufen 35 temiz tur olasiligi ~%0,8).

    Bu bir CIRCIR: biri keep-alive'i geri acarsa paket yeniden araliklarla
    KIRMIZI olur ve o kirmizi bir URUN kusuru sanilir -- yalan rapor.
    """
    import ast
    from pathlib import Path

    kaynak = Path(gf.__file__).read_text(encoding="utf-8")
    agac = ast.parse(kaynak)

    fixture = next(
        (
            n
            for n in ast.walk(agac)
            if isinstance(n, ast.FunctionDef) and n.name == "client"
        ),
        None,
    )
    # ALET DOGRULAMASI: fixture bulunamazsa asagidaki kontrol BOS KUMEDE gecerdi.
    assert fixture is not None, (
        "`client` fixture bulunamadi -> bu bekci hicbir sey olcmuyor. "
        "Ad degistiyse test guncellenmeli."
    )

    limitler = [
        kw.value
        for d in ast.walk(fixture)
        if isinstance(d, ast.Call)
        for kw in d.keywords
        if kw.arg == "limits"
    ]
    assert limitler, (
        "GF istemcisi `limits=` GONDERMIYOR -> baglanti havuzu varsayilan "
        "davranista, bayat-baglanti yarisi geri gelir (S255)."
    )

    metin = " ".join(ast.unparse(d) for d in limitler)
    assert "max_keepalive_connections=0" in metin, (
        f"GF istemcisinde keep-alive KAPALI DEGIL: {metin!r}. "
        "Paket araliklarla RemoteProtocolError ile duser ve bu, urun "
        "kusuru sanilan bir YALAN KIRMIZI uretir."
    )
