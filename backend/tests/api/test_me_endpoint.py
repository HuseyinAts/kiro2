"""GET /api/v1/me sozlesmesi (#447).

Bu uc, frontend'deki 30 `getMe()` cagrisinin (19 ekran) tek veri kaynagi.
Su an `/api/v1/me` **404** donuyor ve cagrilarin 25'i `Promise.all` icinde
korumasiz oldugu icin o ekranlar veri yukleyemiyor.

SOZLESME
--------
* 15 anahtar HER ZAMAN mevcut. Kaynagi olmayan alan `None` doner.
* `None` = "bu veri sistemde YOK". Sifir/bos string DEGIL: 0 XP ile
  "XP bilinmiyor" ayni sey degildir. Uydurma deger bu depoda YASAK — #444'te
  tam olarak bu desen ("5 uydurma ogrenci") bilincle silindi.

TEST TASARIMI — NEDEN IKIYE BOLUNDU (olcumle)
---------------------------------------------
`auth_headers` fixture'i `user_id="1"` icin JWT uretiyor, ama canli DB'de
o kullanici YOK (olculdu: `SELECT id FROM users WHERE id='1'` -> bos).
Dolayisiyla HTTP uzerinden 200 yolunu test etmek, testi DB icerigine
baglamak veya gercek DB'ye kayit yazmak demekti. Bunun yerine:

  1. HTTP katmani  -> auth kapisi (401) ve satiri olmayan kullanici (404).
     Bunlar DB icerigine bagli DEGIL.
  2. Esleme mantigi -> `_persona_kur()` saf fonksiyonu, sahte satirla.
     15 alan, `bas` turetme ve nullable davranisi burada civilenir.

Bu ayrim ayrica gercek bir tasarim kararini zorladi: kimligi gecerli ama
`users` satiri olmayan bir istek 500 DEGIL 404 vermeli.

A1 OLCUMU (bu testlerin beklentilerini belirledi)
-------------------------------------------------
77 kullanici · `total_xp>0` **8** · `level>1` **2** · `streaks` satiri **4** ·
`student_profiles` 74 · `target_university` dolu **0** · `study_hours_per_day`
dolu **0**. Yani `seri`/`seriRekor` cogu kullanici icin `None`; bu bir kusur
degil, olculmus gercek — test bunu "None olamaz" diye civilemez.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.security]

PERSONA_ANAHTARLARI = {
    "ad",
    "adKisa",
    "bas",
    "sinif",
    "seri",
    "seriRekor",
    "xp",
    "seviye",
    "hedefBolum",
    "hedefUni",
    "hedefSiralama",
    "guncelSiralama",
    "yksTarihi",
    "gunlukHedefDk",
    "bugunCozulenDk",
}


# ---------------------------------------------------------------------------
# 1) HTTP katmani — DB icerigine bagli degil
# ---------------------------------------------------------------------------


def test_auth_yoksa_401(client):
    """Kimliksiz erisim persona sizdirmamali."""
    assert client.get("/api/v1/me").status_code == 401


def test_satiri_olmayan_kullanici_404_verir(client, monkeypatch):
    """Kimlik gecerli ama `users` satiri yok -> 404, 500 DEGIL.

    NEDEN DB'YE BAGLANMIYORUZ: test ortami sqlite'a dusuyor ve orada `users`
    tablosu YOK — ilk denemede `sqlite3.OperationalError: no such table: users`
    alindi. Testi oraya baglamak, uretimde PostgreSQL kosan bir yolu SQLITE
    uzerinden "dogrulamak" olurdu; bu depoda daha once tam bu tuzak yasandi
    (tablesample vakasi: sqlite dali yesil, postgresql dali uretimde cokuyordu).

    NEDEN `auth_headers` DEGIL OVERRIDE: gercek JWT ile istek ATILAMIYOR —
    olculdu. `client` + `auth_headers` ile bu test 260 sn'de donmedi (SIGINT
    ile kesildi), kimliksiz 401 testi ise ayni app uzerinde 48 sn'de gecti.
    Fark auth yolunun DB erisimi. Bu depoda `client`+`auth_headers` ikilisini
    GERCEKTEN kosturan baska test de yok (tek aday `test_osym_exam_api.py`,
    31/31 skip) — yani bu bir depo kosulu, bu ucun kusuru degil. Ayri gorev.

    Burada test edilen sey ROUTER MANTIGI: servis None dondugunde 404 uretiliyor
    mu? Gercek auth KAPISI ustteki 401 testinde olculuyor; SQL'in kendisi canli
    duman testiyle dogrulanir.
    """
    from core.dependencies import get_current_user, get_db
    from main import app
    from services import persona_service

    async def _bos(_oturum, _kullanici_id):
        return None

    monkeypatch.setattr("api.me.persona_getir", _bos)
    assert persona_service.persona_getir is not _bos  # stub yalnizca router'da

    # Yalnizca EKLEDIGIM anahtarlar geri alinir; conftest'in override'lari
    # varsa onlari silmek testler arasi sessiz sizinti olurdu.
    app.dependency_overrides[get_current_user] = lambda: _SahteKullanici()
    app.dependency_overrides[get_db] = lambda: None
    try:
        assert client.get("/api/v1/me").status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


class _SahteKullanici:
    """`get_current_user`in dondurdugu nesnenin router'in kullandigi tek alani."""

    id = "1"


# ---------------------------------------------------------------------------
# 2) Esleme mantigi — saf fonksiyon, sahte satir
# ---------------------------------------------------------------------------


def _satir(**degisiklik):
    """Servisin SQL'inin dondurdugu satirin sahtesi."""
    temel = {
        "first_name": "Zeynep",
        "last_name": "Kaya",
        "total_xp": 120,
        "level": 3,
        "current_streak": 5,
        "largest_streak": 9,
        "grade_level": 12,
        "target_department": "Bilgisayar Muhendisligi",
        "target_university": None,
        "study_hours_per_day": 4,
        "sira": 7,
    }
    temel.update(degisiklik)
    return temel


def test_15_anahtarin_tamami_donuyor():
    """Sozlesme: eksik anahtar YOK. Frontend Persona tipi 15 alani bekliyor."""
    from services.persona_service import _persona_kur

    assert set(_persona_kur(_satir()).model_dump()) == PERSONA_ANAHTARLARI


def test_bas_turkce_buyuk_harfle_turetilir():
    """`bas` avatar harfleri. Turkce tuzagi: 'i' -> 'I' DEGIL 'İ'."""
    from services.persona_service import _persona_kur

    assert _persona_kur(_satir(first_name="irem", last_name="soylu")).bas == "İS"


def test_gunluk_hedef_saatten_dakikaya_cevrilir():
    """`study_hours_per_day` SAAT tutuyor, Persona DAKIKA istiyor."""
    from services.persona_service import _persona_kur

    assert _persona_kur(_satir(study_hours_per_day=4)).gunlukHedefDk == 240


def test_kaynagi_olmayan_alanlar_none_dondurur():
    """A1 olcumu: streak satiri 4/77, target_university 0/74, gunluk saat 0/74.

    Bos kaynak `None` doner — 0 veya "" DEGIL. `None` "veri yok" demek;
    0 ise "olculdu ve sifir" demek. Ikisini karistirmak uydurma veridir.
    """
    from services.persona_service import _persona_kur

    persona = _persona_kur(
        _satir(current_streak=None, largest_streak=None, study_hours_per_day=None)
    )
    assert persona.seri is None
    assert persona.seriRekor is None
    assert persona.gunlukHedefDk is None
    # Kaynagi hic olmayan 3 alan her zaman None
    assert persona.hedefSiralama is None
    assert persona.yksTarihi is None
    assert persona.bugunCozulenDk is None


def test_gercek_degerler_uydurulmuyor():
    """KORLESME GUVENCESI: dolu kaynak oldugu gibi aktarilmali.

    Esleme yanlislikla sabit/varsayilan doner hale gelirse bu test kirmiziya
    doner — "hep None don" veya "hep 0 don" gibi bir sadelestirme yakalanir.
    """
    from services.persona_service import _persona_kur

    persona = _persona_kur(_satir())
    assert persona.xp == 120
    assert persona.seviye == 3
    assert persona.seri == 5
    assert persona.seriRekor == 9
    assert persona.sinif == "12"
    assert persona.guncelSiralama == 7
    assert persona.hedefBolum == "Bilgisayar Muhendisligi"
    assert persona.ad == "Zeynep Kaya"
    assert persona.adKisa == "Zeynep"
