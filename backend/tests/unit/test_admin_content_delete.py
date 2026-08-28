"""DELETE /api/v1/admin/content/questions/{id} — canlida 500 veriyordu.

30 TEM 2026 OLCUMU
------------------
Uc, gercek ve mevcut bir soru icin 3/3 `500 Internal Server Error` dondu.
Konteyner logunda TRACEBACK YOK ve `grep -c "Soru silme hatasi"` = 0 —
yani servis govdesi HIC CALISMAMISTI, hata daha once atiliyordu.

KOK NEDEN — IKI SERI BAGLI BASTIRICI
------------------------------------
1. `api/admin.py` router'i `admin_servisi.soru_sil(soru_id)` diye POZISYONEL
   cagiriyordu. `services/admin_service.py:31` (@admin_required):

       current_user = kwargs.get("current_user") or (args[0] if args else None)

   `args[0]` burada SORU ID'si. Dekorator onu kullanici sanip
   `_admin_yetkisi_kontrol`e veriyor; str oldugu icin DEPRECATED in-memory
   `KullaniciServisi`nde araniyor (0 kayit) -> None -> False ->
   AdminAuthorizationError -> router'in ciplak `except Exception` -> 500.

2. Dekorator DUZELTILSE BILE gecmezdi: `_admin_yetkisi_kontrol` (satir 87-95)
   `.rol` ve `.aktif` bekliyor, `AuthenticatedUser` ise `.role` tasiyor ->
   `hasattr(obj, "rol")` False -> `return False`.

Yani `args[0]`i duzeltmek TEK BASINA yetmez. Bu depoda "bir bastiriciyi
kaldirdim ama semptom surdu" vakasi daha once yasandi (bekci kok nedeni,
30 Tem) — o yuzden iki bastirici da burada acikca yaziyor.

FIX'IN SEKLI EV DESENI
----------------------
Ayni hata POST icin coktan tespit edilmis ve `api/admin.py:349` yorumunda
belgelenmis: "admin_kullanici_getir yetki dogrulamasini zaten yapiyor ...
dogrudan soru_bankasi_servisi.soru_ekle'yi cagiriyoruz". DELETE geride
kalmis. Ayni desen uygulaniyor.

YETKI KAYBI YOK: router kapisi `Depends(admin_kullanici_getir)` duruyor ve
ADMIN/SUPER_ADMIN disindaki herkese 403 veriyor (api/admin.py:42).
Kaldirilan `@admin_required` zaten HICBIR ZAMAN gecilemiyordu.

BU TESTLER NEDEN HTTP KATMANINDA AMA DB'SIZ
-------------------------------------------
Bu depoda `client` + `auth_headers` ile authed istek ASILIYOR (olculdu:
260 sn'de donmedi). O yuzden kimlik kapisi `dependency_overrides` ile
degistiriliyor; silme cagrisi da taklit ediliyor. Test edilen sey ROUTER
DAVRANISI: dogru kimlikle dogru fonksiyonu cagiriyor mu, durum kodu dogru mu,
denetim kaydina KIMIN kimligi gidiyor.
"""

from __future__ import annotations

from typing import Any

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.security]

SORU_ID = "3faf4e57-1f38-4771-a209-30839101cd2c"  # canlida 500 ureten gercek id
ADMIN_ID = "admin-42"


class _SahteAdmin:
    """`admin_kullanici_getir`in dondurdugu nesnenin router'in kullandigi alani."""

    id = ADMIN_ID
    role = "ADMIN"


@pytest.fixture
def admin_client(client, monkeypatch):
    """Kimlik kapisini gecerli bir admin ile degistir.

    Kapinin KENDISI ayrica test edilmiyor cunku bu testin konusu degil —
    `admin_kullanici_getir` ADMIN/SUPER_ADMIN disina 403 veriyor
    (api/admin.py:42) ve o davranis degistirilmiyor.
    """
    from api.admin import admin_kullanici_getir
    from main import app

    app.dependency_overrides[admin_kullanici_getir] = lambda: _SahteAdmin()
    try:
        yield client
    finally:
        app.dependency_overrides.pop(admin_kullanici_getir, None)


@pytest.fixture
def silme_taklidi(monkeypatch):
    """`soru_bankasi_servisi.soru_sil`i taklit et; cagri argumanlarini yakala."""
    from services.soru_bankasi_service import soru_bankasi_servisi

    cagrilar: list[str] = []

    async def _sil(soru_id: str) -> bool:
        cagrilar.append(soru_id)
        return True

    monkeypatch.setattr(soru_bankasi_servisi, "soru_sil", _sil)
    return cagrilar


@pytest.fixture
def denetim_taklidi(monkeypatch):
    """`admin_aktivite_kaydet`i taklit et; hangi kimligin gectigini yakala."""
    from services.admin_service import admin_servisi

    kayitlar: list[dict[str, Any]] = []

    async def _kaydet(admin_id, aktivite_tipi, hedef_id=None, detaylar=None):
        kayitlar.append({"admin_id": admin_id, "tip": aktivite_tipi, "hedef": hedef_id})
        return True

    monkeypatch.setattr(admin_servisi, "admin_aktivite_kaydet", _kaydet)
    return kayitlar


def test_var_olan_soru_silinince_200_doner(admin_client, silme_taklidi):
    """Canlida olculen 500 kaybolmali.

    Fix ONCESI: @admin_required soru_id'yi kullanici sanip reddeder ->
    AdminAuthorizationError -> ciplak except -> 500. Silme taklidi hic
    cagrilmaz (cagrilar listesi bos kalir) — yani sadece durum kodu degil,
    "govde hic calismadi" olgusu da civileniyor.
    """
    yanit = admin_client.delete(f"/api/v1/admin/content/questions/{SORU_ID}")

    assert (
        yanit.status_code == 200
    ), f"hala 500/4xx: {yanit.status_code} {yanit.text[:300]}"
    assert silme_taklidi == [
        SORU_ID
    ], f"silme cagrisi dogru id ile YAPILMADI: {silme_taklidi}"


def test_olmayan_soru_404_doner(admin_client, monkeypatch):
    """Bulunamayan soru 404 vermeli — 500 DEGIL.

    "Veri yok" bir SUNUCU HATASI degildir. Bu ayrim olmadan izleme sistemleri
    normal durumu arizadan ayirt edemez.
    """
    from services.soru_bankasi_service import soru_bankasi_servisi

    async def _bulunamadi(_soru_id: str) -> bool:
        return False

    monkeypatch.setattr(soru_bankasi_servisi, "soru_sil", _bulunamadi)

    yanit = admin_client.delete(f"/api/v1/admin/content/questions/{SORU_ID}")
    assert yanit.status_code == 404, f"{yanit.status_code} {yanit.text[:200]}"


def test_denetim_kaydina_admin_kimligi_gidiyor(
    admin_client, silme_taklidi, denetim_taklidi
):
    """KOK NEDEN SINIFINI DOGRUDAN CIVILEYEN TEST.

    Kusurun ozu "soru kimligi ile kullanici kimliginin birbirine karismasi"
    idi. Bu test tam onu olcer: denetim kaydina ADMIN'in kimligi gitmeli —
    ne `None` (eski kodda oyleydi: `current_user` hic gecirilmiyordu) ne de
    SORU kimligi (dekoratorun sandigi sey).
    """
    admin_client.delete(f"/api/v1/admin/content/questions/{SORU_ID}")

    assert denetim_taklidi, "silme denetim kaydi HIC olusmadi"
    kayit = denetim_taklidi[0]
    assert kayit["admin_id"] == ADMIN_ID, (
        f"denetim kaydinda yanlis kimlik: {kayit['admin_id']!r} "
        f"(SORU kimligi {SORU_ID!r} veya None olmamali)"
    )
    assert kayit["admin_id"] != SORU_ID
    assert kayit["hedef"] == SORU_ID, "silinen sorunun kimligi kaydedilmeli"
