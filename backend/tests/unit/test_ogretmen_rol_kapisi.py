"""Ogretmen kapisi + JWT rol eslemesi bekcisi (K2 / S252).

NEDEN VAR -- IKI AYRI KUSUR, TEK ZINCIR
---------------------------------------
CANLI OLCUM (24 Agu 2026, jeton konteyner icinde uretildi):

    GET /api/v1/ogretmen/raporlar   role="TEACHER"     -> 403
    GET /api/v1/ogretmen/raporlar   role="teacher"     -> 200   <-- AYNI UC
    GET /api/v1/ogretmen/raporlar   role="admin"       -> 403
    GET /api/v1/ogretmen/raporlar   role="super_admin" -> 403

K2a -- `api/auth.py:348` `role_map.get(jwt_role, KullaniciRolu.OGRENCI)`
  Harita anahtarlari KUCUK harf ("teacher"), kanonik rol ise BUYUK harf:
  `users.role` PG enum `userrole` -> STUDENT/TEACHER/PARENT/ADMIN/SUPER_ADMIN
  (`models/enums_db.py:18`, *"Do NOT redefine"*). Kanonik jeton haritayi
  ISKALIYOR ve SESSIZCE `OGRENCI`'ye dusuyor. Sonuc: `/api/v1/ogretmen/*`
  yuzeyinin 10 ucu kanonik rolle HIC ACILMIYOR.

  BU BUG AYNI DOSYADA 45 SATIR ASAGIDA ZATEN DUZELTILMIS: `_map_registration_role`
  (`api/auth.py:389`) docstring'i birebir ayni sinifi anlatiyor -- *"eski
  eslestirme HICBIR anahtari tutturamiyor ve herkesi sessizce STUDENT yapiyordu"*.
  Kayit tarafi onarilmis, kimlik dogrulama tarafi onarilmamis.

K2b -- `api/ogretmen.py:46` `!= KullaniciRolu.OGRETMEN`
  Esitsizlik (kume degil) ADMIN ve SUPER_ADMIN'i disarida birakiyor. Diger DORT
  canli rol kapisi ailesinin dordu de ADMIN istendiginde SUPER_ADMIN'i geciriyor
  (`get_current_admin_user` 83 uc, `admin_kullanici_getir` 17, `require_role` 21,
  `jwt_auth.require_admin` 2 -- hepsi canli proplandi). ogretmen.py TEK SAPMA.
  Urun karari (kullanici, 24 Agu): ADMIN ve SUPER_ADMIN GECMELI.

KONTROL KOLLARI
---------------
Bu dosyadaki "gecer" testleri tek basina anlamsizdir: kapiyi tamamen kaldirmak da
onlari yesil yapardi. `test_kapi_ogrenci_ve_veliyi_hala_reddediyor` bu yuzden var
-- kapinin hala KAPI oldugunu civiler.
"""

from __future__ import annotations

import types
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api.auth import mevcut_kullanici_getir
from api.ogretmen import ogretmen_yetkisi_kontrol
from models.enums import KullaniciRolu

TEST_SECRET = "test-secret-yalnizca-birim-testi"  # noqa: S105 # pragma: allowlist secret
TEST_ALG = "HS256"

# `models/enums_db.py:18` PG enum `userrole` etiketleri -> Turkce ic enum karsiligi.
# Kanon BUYUK HARF'tir; kucuk harfli varyantlar eski jetonlar icin geriye donuk
# uyumluluk olarak DA calismali (asagida ayri test).
KANONIK_ESLEME = [
    ("STUDENT", KullaniciRolu.OGRENCI),
    ("TEACHER", KullaniciRolu.OGRETMEN),
    ("PARENT", KullaniciRolu.VELI),
    ("ADMIN", KullaniciRolu.ADMIN),
    ("SUPER_ADMIN", KullaniciRolu.SUPER_ADMIN),
]


@pytest.fixture(autouse=True)
def _jwt_ve_blacklist(monkeypatch):
    """JWT sirrini sabitle + blacklist'i (Redis, HARICI bagimlilik) devre disi birak.

    Rol eslemesi -- yani OLCULEN sey -- mock'lanMIYOR. Yalnizca Redis mock'lanir;
    testing.md: *"Sadece external dependencies mock'la"*.
    """
    monkeypatch.setattr("api.auth.JWT_SECRET", TEST_SECRET)
    monkeypatch.setattr("api.auth.JWT_ALGORITHM", TEST_ALG)

    class _SahteJwtManager:
        async def is_blacklisted_async(self, _token: str) -> bool:
            return False

    monkeypatch.setattr("api.auth.get_jwt_manager", lambda: _SahteJwtManager())


def _jeton(rol: str) -> HTTPAuthorizationCredentials:
    simdi = datetime.now(UTC)
    ham = pyjwt.encode(
        {
            "sub": "kullanici-1",
            # `.test` TLD KULLANMA: pydantic EmailStr onu "reserved" diye reddeder
            # ve test, olcmek istedigi seye HIC ULASMADAN duser (S247'de birebir
            # ayni tuzak iki testi bosuna gecirmisti).
            "email": "olcum@kiro2.com",
            "username": "olcum_kullanici",
            "role": rol,
            "iat": simdi,
            "exp": simdi + timedelta(minutes=5),
        },
        TEST_SECRET,
        algorithm=TEST_ALG,
    )
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=ham)


# --------------------------------------------------------------------------
# K2a -- JWT rol eslemesi
# --------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(("jwt_rol", "beklenen"), KANONIK_ESLEME)
async def test_kanonik_buyuk_harf_rol_dogru_eslesiyor(
    jwt_rol: str, beklenen: KullaniciRolu
) -> None:
    """KANON BUYUK HARF. Bugun 5/5 sessizce OGRENCI'ye dusuyor (K2a)."""
    kullanici = await mevcut_kullanici_getir(None, _jeton(jwt_rol))
    assert kullanici.rol is beklenen, (
        f"Kanonik jeton rolu {jwt_rol!r} -> {kullanici.rol!r} oldu; "
        f"{beklenen!r} bekleniyordu. Sessiz dusurme yine mi devrede?"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("jwt_rol", "beklenen"), KANONIK_ESLEME)
async def test_kucuk_harf_rol_hala_calisiyor(
    jwt_rol: str, beklenen: KullaniciRolu
) -> None:
    """GERIYE DONUK UYUMLULUK KOLU: eski kucuk-harfli jetonlar bozulmamali.

    Bu kirmizi olursa duzeltme kanonu tanirken eskiyi KIRMIS demektir --
    ortamda dolasan gecerli jetonlar aninda yetkisiz kalirdi.
    """
    kullanici = await mevcut_kullanici_getir(None, _jeton(jwt_rol.lower()))
    assert kullanici.rol is beklenen


@pytest.mark.asyncio
async def test_taninmayan_rol_en_dusuk_yetkiye_duser_ve_sessiz_kalmaz(caplog) -> None:
    """Taninmayan rol fail-closed (OGRENCI) olmali AMA gorunur olmali.

    Sessiz varsayilan bu kusuru aylarca gizledi. Ayni ders `_map_registration_role`
    docstring'inde yazili. Burada kilitlenme riski olmadan gorunur kilinir:
    yetki DUSURULUR (guvenli) ama ERROR loglanir (gorunur).
    """
    with caplog.at_level("ERROR"):
        kullanici = await mevcut_kullanici_getir(None, _jeton("KOZMIK_YONETICI"))

    assert kullanici.rol is KullaniciRolu.OGRENCI, "taninmayan rol yukseltilmemeli"
    assert any(
        "KOZMIK_YONETICI" in kayit.message or "KOZMIK_YONETICI" in str(kayit.args)
        for kayit in caplog.records
    ), "taninmayan rol SESSIZCE dusuruldu -- bu kusuru gizleyen desenin ta kendisi"


# --------------------------------------------------------------------------
# K2b -- ogretmen kapisi
# --------------------------------------------------------------------------


def _kullanici(rol: KullaniciRolu) -> types.SimpleNamespace:
    """Kapi yalnizca `.rol` okuyor; tam `Kullanici` kurmak gereksiz baglanti kurar."""
    return types.SimpleNamespace(id="k1", email="a@b.c", rol=rol)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "rol",
    [KullaniciRolu.OGRETMEN, KullaniciRolu.ADMIN, KullaniciRolu.SUPER_ADMIN],
)
async def test_kapi_ogretmen_admin_ve_super_admini_geciriyor(
    rol: KullaniciRolu,
) -> None:
    """Urun karari (24 Agu): ADMIN + SUPER_ADMIN ogretmen uclarindan gecmeli."""
    sonuc = await ogretmen_yetkisi_kontrol(_kullanici(rol))
    assert sonuc.rol is rol


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [KullaniciRolu.OGRENCI, KullaniciRolu.VELI])
async def test_kapi_ogrenci_ve_veliyi_hala_reddediyor(rol: KullaniciRolu) -> None:
    """KONTROL KOLU: kapinin hala KAPI oldugunu civiler.

    Bu test olmasa "kapiyi tamamen kaldir" da yukaridaki testleri yesil yapardi.
    """
    with pytest.raises(HTTPException) as yakalanan:
        await ogretmen_yetkisi_kontrol(_kullanici(rol))
    assert yakalanan.value.status_code == 403
