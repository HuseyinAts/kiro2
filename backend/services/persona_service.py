"""Persona agregasyonu: users + student_profiles + streaks TEK sorguda (#447).

Frontend'deki 30 `getMe()` cagrisinin (19 ekran) tek veri kaynagi. Ekran
basina 5 ayri istek atmak yerine backend'de tek join yapilir; N+1 riski
boylece tek yerde yonetilir.

TASARIM: I/O ile ESLEME AYRI
----------------------------
`_persona_kur()` saf bir fonksiyon (satir sozlugu -> PersonaResponse) ve
DB'ye dokunmaz; 15 alanin tamami onun uzerinden testlenir. `persona_getir()`
yalnizca sorguyu kosar. Bu ayrim testin canli DB icerigine baglanmasini
onledi — `auth_headers` fixture'inin kullanicisi (id="1") DB'de YOK (olculdu),
dolayisiyla HTTP uzerinden 200 yolunu test etmek ya sahte kayit yazmayi ya da
testi veri icerigine baglamayi gerektirirdi.

`persona_getir` satir bulamazsa None doner; router bunu 404'e cevirir.
`.one()` kullanilsaydi NoResultFound -> 500 olurdu, yani "kimlik gecerli ama
veri yok" durumu SUNUCU HATASI gibi gorunurdu.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# --- Yanit semasi ---------------------------------------------------------
# Ev kurali: response modelleri ayri bir `schemas/` paketinde DEGIL, ilgili
# modulun icinde tanimlaniyor (ornek: api/billing_api.py:26 BillingMeResponse).
# Sema api/me.py yerine BURADA duruyor cunku servis onu dondurmek zorunda;
# api katmanina koysaydik service -> api yonunde ters bir bagimlilik olurdu.
class PersonaResponse(BaseModel):
    """15 alan HER ZAMAN mevcut; kaynagi olmayan alan None doner."""

    ad: str
    adKisa: str  # noqa: N815 — frontend Persona alan adi
    bas: str
    sinif: str | None
    seri: int | None
    seriRekor: int | None  # noqa: N815
    xp: int | None
    seviye: int | None
    hedefBolum: str | None  # noqa: N815
    hedefUni: str | None  # noqa: N815
    hedefSiralama: int | None  # noqa: N815
    guncelSiralama: int | None  # noqa: N815
    yksTarihi: str | None  # noqa: N815
    gunlukHedefDk: int | None  # noqa: N815
    bugunCozulenDk: int | None  # noqa: N815


# Tek sorgu, N+1 YOK. `guncelSiralama` window function ile GERCEK veriden
# hesaplanir (total_xp sirasi) — uydurulmaz. LEFT JOIN'ler: streaks ve
# student_profiles satiri olmayan kullanici da 200 alir, ilgili alanlar None.
_SORGU = text(
    """
    WITH siralama AS (
        SELECT id, RANK() OVER (ORDER BY total_xp DESC) AS sira
        FROM users
        WHERE is_active = TRUE
    )
    SELECT u.first_name,
           u.last_name,
           u.total_xp,
           u.level,
           s.current_streak,
           s.largest_streak,
           p.grade_level,
           p.target_department,
           p.target_university,
           p.study_hours_per_day,
           r.sira
    FROM users u
    LEFT JOIN streaks s          ON s.user_id = u.id
    LEFT JOIN student_profiles p ON p.user_id = u.id
    LEFT JOIN siralama r         ON r.id = u.id
    WHERE u.id = :kullanici_id
    """
)


def _bas_harfler(ad: str, soyad: str) -> str:
    """Avatar bas harfleri.

    Turkce tuzagi: `"irem".upper()` -> `"IREM"` verir, dogrusu `"İREM"`.
    CLAUDE.md Turkce NLP kurali: I/i donusumu `.upper()`e birakilmaz.
    """
    harfler = "".join(parca[0] for parca in (ad, soyad) if parca)
    return harfler.replace("i", "İ").upper()


def _persona_kur(satir: Mapping[str, Any]) -> PersonaResponse:
    """Sorgu satirini Persona'ya cevirir. SAF fonksiyon — DB'ye dokunmaz."""
    ad = satir["first_name"] or ""
    soyad = satir["last_name"] or ""
    saat = satir["study_hours_per_day"]
    sinif = satir["grade_level"]
    return PersonaResponse(
        ad=f"{ad} {soyad}".strip(),
        adKisa=ad,
        bas=_bas_harfler(ad, soyad),
        sinif=str(sinif) if sinif is not None else None,
        seri=satir["current_streak"],
        seriRekor=satir["largest_streak"],
        xp=satir["total_xp"],
        seviye=satir["level"],
        hedefBolum=satir["target_department"],
        hedefUni=satir["target_university"],
        guncelSiralama=satir["sira"],
        gunlukHedefDk=saat * 60 if saat is not None else None,
        # Kaynagi OLMAYAN uc alan. A1 olcumu bunlari besleyecek bir kolon
        # bulamadi: hedefSiralama learning_path'te STRING ("top_1000"),
        # yksTarihi ayri tabloda, bugunCozulenDk icin gunluk toplam kolonu yok.
        # Uydurmak yerine None doneriz; frontend "—" gosterir.
        hedefSiralama=None,
        yksTarihi=None,
        bugunCozulenDk=None,
    )


async def persona_getir(
    oturum: AsyncSession, kullanici_id: str
) -> PersonaResponse | None:
    """Kullanicinin personasini doner; `users` satiri yoksa None."""
    satir = (
        (await oturum.execute(_SORGU, {"kullanici_id": kullanici_id}))
        .mappings()
        .one_or_none()
    )
    # `dict(...)`: SQLAlchemy `RowMapping` dondurur, `_persona_kur` ise sade bir
    # `Mapping` bekliyor — saf fonksiyonun testi ORM turune baglanmasin diye.
    return None if satir is None else _persona_kur(dict(satir))
