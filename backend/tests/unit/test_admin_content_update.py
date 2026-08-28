"""PUT /api/v1/admin/content/questions/{id} — DELETE ile AYNI iki bastirici (#465/YENI-1).

30 Tem 2026 denetimi DELETE'i olctu (3/3 500) ve `a30416f34` onu duzeltti.
PUT ayni kod yolunu paylasiyor ama GERIDE KALDI — 1 Agu 2026 dogrulamasinda
`YENI-1` olarak raporlandi.

KOK NEDEN (DELETE ile birebir ayni, ayrica olculdu)
--------------------------------------------------
`api/admin.py:421` router'i POZISYONEL cagiriyor:

    soru = await admin_servisi.soru_guncelle(soru_id, soru_data)

`services/admin_service.py:31` (@admin_required):

    current_user = kwargs.get("current_user") or (args[0] if args else None)

`args[0]` burada SORU ID'si (str). Dekorator onu kullanici sanip
`_admin_yetkisi_kontrol`e verir; DEPRECATED in-memory `KullaniciServisi`de
aranir -> None -> False -> `AdminAuthorizationError`. Bu istisna router'daki
`except ValueError` VE `except HTTPException` dallarinin HICBIRINE uymaz ->
ciplak `except Exception` -> HTTP 500.

KAPSAM OLCULDU (1 Agu 2026) — denetimin sayisi duzeltildi
---------------------------------------------------------
Denetim "14 metot bozuk" demisti. AST ile sayildi: `@admin_required` /
`@super_admin_required` tasiyan **17** metot var, AMA uretim kodundan
korumali bir metoda yapilan cagri **TEK**: `api/admin.py:421 soru_guncelle`.
Kalan 16'nin uretim cagirani YOK (olu kod). Yani bozuk dekorator bugun
yalnizca BU ucta zarar veriyor.

FIX'IN SEKLI EV DESENI
----------------------
POST (`admin.py:349`) ve DELETE (`a30416f34`) zaten dogrudan
`soru_bankasi_servisi`yi cagiriyor. PUT ayni desene getiriliyor.
YETKI KAYBI YOK: router kapisi `Depends(admin_kullanici_getir)` duruyor ve
ADMIN/SUPER_ADMIN disindaki herkese 403 veriyor. Kaldirilan `@admin_required`
zaten HICBIR ZAMAN gecilemiyordu.

BILINEN SINIR (yeni bulgu olarak kaydedildi)
--------------------------------------------
`soru_bankasi_servisi.soru_guncelle` "bulunamadi" ve "istisna" durumlarinin
IKISINDE de `None` donuyor (satir 1265-1270 `except -> return None`). Router
bu yuzden gercek bir DB hatasini 404 diye raporlayabilir. Servis
DEGISTIRILMEDI cunku ikinci bir uretim cagirani var
(`api/soru_bankasi.py:845`) — cerrahi mudahale kurali. Belirsizlik durum
tablosuna `YENI-8` olarak yazildi.
"""

from __future__ import annotations

from typing import Any

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.security]

SORU_ID = "3faf4e57-1f38-4771-a209-30839101cd2c"
ADMIN_ID = "admin-42"
YUK = {"question_text": "Guncellenmis soru metni", "difficulty": "zor"}


class _SahteAdmin:
    id = ADMIN_ID
    role = "ADMIN"


class _SahteSoru:
    """Router'in yanit govdesine koydugu nesne."""

    id = SORU_ID
    question_text = YUK["question_text"]


@pytest.fixture
def admin_client(client):
    """Kimlik kapisini gecerli bir admin ile degistir."""
    from api.admin import admin_kullanici_getir
    from main import app

    app.dependency_overrides[admin_kullanici_getir] = lambda: _SahteAdmin()
    try:
        yield client
    finally:
        app.dependency_overrides.pop(admin_kullanici_getir, None)


@pytest.fixture
def guncelleme_taklidi(monkeypatch):
    """`soru_bankasi_servisi.soru_guncelle`i taklit et, cagriyi yakala."""
    from services.soru_bankasi_service import soru_bankasi_servisi

    cagrilar: list[tuple[str, dict[str, Any]]] = []

    async def _guncelle(soru_id: str, guncelleme_verisi: dict) -> _SahteSoru:
        cagrilar.append((soru_id, guncelleme_verisi))
        return _SahteSoru()

    monkeypatch.setattr(soru_bankasi_servisi, "soru_guncelle", _guncelle)
    return cagrilar


def test_var_olan_soru_guncellenince_200_doner(admin_client, guncelleme_taklidi):
    """Olculen 500 kaybolmali VE servis govdesi gercekten cagrilmali.

    Fix ONCESI: dekorator soru_id'yi kullanici sanip reddeder ->
    AdminAuthorizationError -> ciplak except -> 500, ve `guncelleme_taklidi`
    BOS kalir. Yani sadece durum kodu degil, "govde hic calismadi" olgusu da
    civileniyor — bu ayrim olmadan test 500'u baska bir sebeple de gecebilirdi.
    """
    yanit = admin_client.put(f"/api/v1/admin/content/questions/{SORU_ID}", json=YUK)

    assert (
        yanit.status_code == 200
    ), f"hala 500/4xx: {yanit.status_code} {yanit.text[:300]}"
    assert guncelleme_taklidi == [
        (SORU_ID, YUK)
    ], f"guncelleme dogru id/yuk ile CAGRILMADI: {guncelleme_taklidi}"


def test_olmayan_soru_404_doner(admin_client, monkeypatch):
    """Bulunamayan soru 404 vermeli — 500 DEGIL.

    "Veri yok" bir SUNUCU HATASI degildir; bu ayrim olmadan izleme sistemleri
    normal durumu arizadan ayirt edemez.
    """
    from services.soru_bankasi_service import soru_bankasi_servisi

    async def _bulunamadi(soru_id: str, guncelleme_verisi: dict) -> None:
        return None

    monkeypatch.setattr(soru_bankasi_servisi, "soru_guncelle", _bulunamadi)

    yanit = admin_client.put(f"/api/v1/admin/content/questions/{SORU_ID}", json=YUK)
    assert (
        yanit.status_code == 404
    ), f"beklenen 404, gelen {yanit.status_code}: {yanit.text[:300]}"


def test_olu_dekorator_yolu_artik_kullanilmiyor(admin_client, guncelleme_taklidi):
    """REGRESYON BEKCISI: router `admin_servisi.soru_guncelle`e DONMEMELI.

    Eski yol geri gelirse @admin_required yeniden 500 uretir. Burada
    `admin_servisi.soru_guncelle` PATLAYICI ile degistiriliyor: cagrilirsa
    test duser.
    """
    from services.admin_service import admin_servisi

    async def _patlayici(*args: Any, **kwargs: Any):
        raise AssertionError(
            "router olu `admin_servisi.soru_guncelle` yoluna dondu — "
            "@admin_required soru_id'yi kullanici sanip 500 uretecek (#465/YENI-1)"
        )

    admin_client_monkeypatch = pytest.MonkeyPatch()
    admin_client_monkeypatch.setattr(admin_servisi, "soru_guncelle", _patlayici)
    try:
        yanit = admin_client.put(f"/api/v1/admin/content/questions/{SORU_ID}", json=YUK)
        assert yanit.status_code == 200
        assert guncelleme_taklidi, "dogru servis yolu hic cagrilmadi"
    finally:
        admin_client_monkeypatch.undo()


def test_dekorator_hala_soru_id_yi_kullanici_saniyor() -> None:
    """KOK NEDENIN KENDISI — fix'in NEDEN gerekli oldugunu civiler.

    Dekorator DUZELTILMEDI (17 metottan 16'sinin uretim cagirani yok, +0 deger
    -> #451 dersi). Ama davranisi burada belgelenmis olsun ki gelecekte biri
    o metotlari yeniden kablolarsa ne oldugunu bilsin.
    """
    import inspect

    from services import admin_service

    kaynak = inspect.getsource(admin_service.admin_required)
    assert "args[0] if args else None" in kaynak, (
        "dekorator degismis — bu testin varsayimi gecersiz, "
        "router'daki dogrudan-servis deseni yeniden degerlendirilmeli"
    )
