"""Kanon rol kapisi bekcisi -- `get_current_admin_user` (K4 / S252).

NEDEN VAR
---------
`core/dependencies.py:219` `get_current_admin_user` bu depodaki EN GENIS rol
kapisi: AST olcumu (24 Agu 2026, provenance ayrimiyla, ad golgeleri elenmis)
**83 route fonksiyonu / 22 dosya**. Ikinci sirada `admin_kullanici_getir`
(17 uc), ucuncu `require_role` (21), sonra `jwt_auth.require_admin` (2).

VE BU KAPININ HICBIR TESTI YOKTU: `grep -rn PLATFORM_ADMIN_ROLES backend/tests`
-> **0 dosya**; `_auth_role_slug` -> 0 dosya. Yani 83 ucun tamamini koruyan
sozlesme -- super_admin genislemesi ve harf-buyuklugu dayanikliligi --
hicbir yerde civilenmemisti.

X06 (c) rol kapisi GOCU bu kapiyi kanon olarak secerse 126+ uc buraya yigilir.
Bekcisiz bir kapiya goc yapilamaz; bu dosya o on kosulu karsilar.

NE CIVILENIYOR (dordu de canli proplandi, 24 Agu 2026)
------------------------------------------------------
    GET /api/v1/admin/dashboard/stats
        none 401 | STUDENT 403 | TEACHER 403 | ADMIN 200 | SUPER_ADMIN 200

1. SUPER_ADMIN, ADMIN istenen her kapidan GECER (urun kurali; canli dort
   ailenin dordu de boyle davraniyor).
2. Harf buyuklugu IKI TARAFTA da cozulmus olmali: girdi tarafi
   `models/enums_db.py:24-32` `_missing_` (upper() aramasi), kiyas tarafi
   enum kimligi. 'admin' / 'ADMIN' / 'Admin' ucu de UserRole.ADMIN olmali.
3. KAPI HALA KAPI: STUDENT / TEACHER / PARENT 403 almali. Bu kontrol kolu
   olmasa "kapiyi kaldir" da yukaridaki testleri yesil yapardi.
4. Kume DARALTILAMAZ ve GENISLETILEMEZ: tam olarak {ADMIN, SUPER_ADMIN}.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from core.dependencies import (
    PLATFORM_ADMIN_ROLES,
    AuthenticatedUser,
    get_current_admin_user,
)
from models.enums_db import UserRole


def _kullanici(rol: UserRole | str) -> AuthenticatedUser:
    return AuthenticatedUser(
        id="k1",
        username="olcum_kullanici",
        role=rol,
        email="olcum@kiro2.com",
        permissions=[],
    )


def test_kanon_kume_tam_olarak_admin_ve_super_admin() -> None:
    """Kume DARALTILAMAZ ve GENISLETILEMEZ.

    `!=` yerine tam esitlik: birisi TEACHER eklerse (yetki genislemesi) veya
    SUPER_ADMIN'i cikarirsa (S252'de ogretmen kapisinda oldugu gibi) bu duser.
    """
    assert frozenset({UserRole.ADMIN, UserRole.SUPER_ADMIN}) == PLATFORM_ADMIN_ROLES


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [UserRole.ADMIN, UserRole.SUPER_ADMIN])
async def test_admin_ve_super_admin_geciyor(rol: UserRole) -> None:
    """SUPER_ADMIN, ADMIN istenen kapidan gecmeli (canli: 200)."""
    sonuc = await get_current_admin_user(_kullanici(rol))
    assert sonuc.role is rol


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [UserRole.STUDENT, UserRole.TEACHER, UserRole.PARENT])
async def test_kontrol_kolu_kapi_hala_403_veriyor(rol: UserRole) -> None:
    """KONTROL KOLU: kapinin hala KAPI oldugunu civiler (canli: 403).

    Bu test olmasa `if False:` mutasyonu da "gecer" testlerini yesil birakirdi.
    """
    with pytest.raises(HTTPException) as yakalanan:
        await get_current_admin_user(_kullanici(rol))
    assert yakalanan.value.status_code == 403


@pytest.mark.parametrize("yazim", ["ADMIN", "admin", "Admin", "aDmIn"])
def test_harf_buyuklugu_girdi_tarafinda_normalize_ediliyor(yazim: str) -> None:
    """Kanon BUYUK HARF (PG enum `userrole`) ama girdi her yazimda kabul edilmeli.

    S252'de `api/auth.py`'deki AYRI bir haritada tam bu normalizasyon eksikti ve
    kanonik BUYUK harf roller sessizce OGRENCI'ye dusuyordu (10 uc kapandi).
    Burada kanon kapinin AYNI kusuru tasimadigi civilenir.
    """
    assert _kullanici(yazim).role is UserRole.ADMIN


@pytest.mark.asyncio
@pytest.mark.parametrize("yazim", ["ADMIN", "admin", "Admin"])
async def test_harf_buyuklugu_kapiyi_da_geciyor(yazim: str) -> None:
    """Normalizasyon KAPIDA da ise yarayor mu (uctan uca, sadece model degil)."""
    sonuc = await get_current_admin_user(_kullanici(yazim))
    assert sonuc.role is UserRole.ADMIN


def test_alet_dogrulamasi_taninmayan_rol_reddediliyor() -> None:
    """KONTROL KOLU: normalizasyon HER dizeyi kabul etmiyor.

    Yukaridaki harf testleri tek basina anlamsiz olurdu: `role` alani her seyi
    kabul etse (orn. serbest dize) onlar da gecerdi. Taninmayan rol REDDEDILMELI
    -- aksi halde "rol normalize ediliyor" degil "rol dogrulanmiyor" demektir.
    """
    with pytest.raises(ValueError):
        _kullanici("KOZMIK_YONETICI")
