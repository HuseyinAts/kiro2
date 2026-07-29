"""Kayıt ucundaki rol eşleştirmesi — iki bug birbirini maskeliyordu.

29 Tem 2026 ölçümü. `backend/api/auth.py:595` şunu yapıyordu:

    rol_str = ROL_MAP.get(str(kullanici_data.rol).lower(), "STUDENT")

`kullanici_data.rol` Pydantic doğrulamasından `KullaniciRolu` **enum üyesi** olarak
çıkar ve Python 3.11+ `class X(str, Enum)` için `str(X.OGRETMEN)` değeri değil
`"KullaniciRolu.OGRETMEN"` üretir. Yani ROL_MAP hiçbir anahtarı tutturmuyordu ve
`.get(..., "STUDENT")` her seferinde fallback'e düşüyordu:

    rol="ogretmen" -> STUDENT   (öğretmen kaydı fiilen çalışmıyordu)
    rol="veli"     -> STUDENT   (veli kaydı fiilen çalışmıyordu)
    rol="admin"    -> STUDENT   (yetki yükseltme tesadüfen kapalıydı)

TUZAK: bariz düzeltme (`str(rol)` yerine `rol.value`) öğretmen/veli kaydını onarır
AMA aynı anda admin yükseltmesini AÇAR — çünkü ROL_MAP'te `"admin": "ADMIN"` vardı ve
uç herkese açık. İki bug birbirini maskeliyordu. Bu yüzden aşağıdaki testler dördünü
birden çiviler; biri olmadan diğeri regresyon üretir.

Karar: ayrıcalıklı rol **sessizce düşürülmez, açıkça reddedilir**. Bu bug'ı aylarca
gizleyen şey tam olarak sessiz düşürmeydi. Admin hesapları admin panelinden açılır
(`adminService.createUser` -> `POST /admin/users`, ölçüldü — `/auth/kayit` değil).
"""

import pytest
from fastapi import HTTPException

from api.auth import _map_registration_role
from models.enums import KullaniciRolu

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("gonderilen", "beklenen_db_rolu"),
    [
        (KullaniciRolu.OGRENCI, "STUDENT"),
        (KullaniciRolu.OGRETMEN, "TEACHER"),
        (KullaniciRolu.VELI, "PARENT"),
    ],
)
def test_self_registerable_role_maps_to_its_own_db_role(gonderilen, beklenen_db_rolu):
    """Kendi kendine kaydolabilen roller DOĞRU users.role değerine gitmeli.

    Bu testin yakaladığı arıza: herkes sessizce STUDENT oluyordu. Hata yok, log yok —
    öğretmen kaydolur, öğrenci hesabı alır, öğretmen panosunu hiç göremez.
    """
    assert _map_registration_role(gonderilen) == beklenen_db_rolu


@pytest.mark.parametrize(
    ("takma_ad", "beklenen_db_rolu"),
    [("ogrenci", "STUDENT"), ("teacher", "TEACHER"), ("parent", "PARENT")],
)
def test_string_aliases_still_map(takma_ad, beklenen_db_rolu):
    """`/register` (İngilizce alias) çağıranları kırılmamalı — eski ROL_MAP'te vardılar."""
    assert _map_registration_role(takma_ad) == beklenen_db_rolu


@pytest.mark.parametrize(
    "ayricalikli",
    [KullaniciRolu.ADMIN, KullaniciRolu.SUPER_ADMIN, "admin", "super_admin"],
)
def test_privileged_role_is_rejected_not_silently_downgraded(ayricalikli):
    """Herkese açık kayıt ucu ayrıcalıklı rol ÜRETMEMELİ ve sessizce yutmamalı.

    İki ayrı şeyi birden kanıtlar:
    (a) yetki yükseltme yok — dönüş 'ADMIN' olamaz,
    (b) sessiz düşürme de yok — 'STUDENT' döndürüp geçiştirmek de kabul değil.
        Sessiz düşürme bu bug'ı aylarca gizleyen davranışın ta kendisiydi.
    """
    with pytest.raises(HTTPException) as exc:
        _map_registration_role(ayricalikli)
    assert exc.value.status_code == 403


def test_mapping_never_yields_a_privileged_db_role():
    """Hiçbir girdi ADMIN/SUPER_ADMIN üretemez — eşleştirmenin tamamı üzerinden.

    Bir sonraki geliştirici tabloya yeni rol eklerse bu test onu yakalar.
    """
    for rol in KullaniciRolu:
        try:
            sonuc = _map_registration_role(rol)
        except HTTPException:
            continue
        assert sonuc not in {
            "ADMIN",
            "SUPER_ADMIN",
        }, f"{rol!r} herkese açık kayıttan {sonuc!r} üretiyor — yetki yükseltme"
