"""`StudentLearningProfile.needs_update` naive/aware tarih karışımına dayanmalı.

NEDEN VAR (gf82, 2 Ağu 2026)
----------------------------
`POST /api/v1/learning-style/behavioral-data/{id}` canlıda 500 veriyordu:

    TypeError: can't subtract offset-naive and offset-aware datetimes
    models/student_learning_profile.py:153  needs_update

Çağrı zinciri (canlı traceback):
    api/learning_style.py:219  update_behavioral_data
    services/learning_style_service.py:451
    services/learning_style_service.py:89   detect_learning_style
    models/student_learning_profile.py:153  needs_update

KÖK NEDEN — aynı sınıfın iki yarısı çelişiyor
----------------------------------------------
    :113  updated_at = Column(DateTime, default=datetime.utcnow, ...)
          -> tz-BILGISIZ (naive): `DateTime` timezone=True DEĞİL,
             `utcnow` da naive üretir
    :153  age = datetime.now(UTC) - self.updated_at
          -> tz-BILGILI (aware)

Yani nesne DB'den okunduğunda `updated_at` naive gelir ve çıkarma patlar.
Bu, gf25'in ikinci sebebiyle **aynı sınıf**: ORM'in bir yarısı tz-aware
davranırken diğer yarısı naive.

NEDEN KOLON DEĞİL DE KARŞILAŞTIRMA DÜZELTİLDİ
----------------------------------------------
Kolonu `timestamptz`e çevirmek migration + canlı veri dönüşümü demek.
Demo gününde bu risk alınmadı; karşılaştırma tarafı savunmaya alındı —
davranış aynı, yarıçap tek satır. Kolonun kendisi `GF-K6` altında açık
kalem olarak duruyor.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from models.student_learning_profile import StudentLearningProfile


def _profil(updated_at: datetime | None) -> StudentLearningProfile:
    """ORM nesnesi — DB'ye DOKUNMADAN, yalnizca `needs_update` icin."""
    p = StudentLearningProfile()
    p.updated_at = updated_at
    return p


def test_naive_tarih_ile_patlamaz() -> None:
    """ASIL KUSUR: DB'den gelen naive `updated_at` ile 500 atiyordu.

    Fix'ten ONCE KIRMIZI:
        TypeError: can't subtract offset-naive and offset-aware datetimes
    """
    naive_dun = datetime.utcnow() - timedelta(days=1)  # noqa: DTZ003 — KASITLI naive

    sonuc = _profil(naive_dun).needs_update

    assert sonuc is False, (
        "1 gunluk profil 'guncellenmeli' dedi — yas hesabi yanlis "
        "(veya naive tarih yanlis yorumlandi)."
    )


def test_naive_eski_profil_guncellenmeli_der() -> None:
    """Naive tarih DOGRU yorumlanmali: 40 gunluk profil eskimis sayilir.

    Bu, fix'in istisnayi yutup her zaman `False` donmesini engeller —
    "patlamiyor" yetmez, YANIT da dogru olmali.
    """
    naive_eski = datetime.utcnow() - timedelta(days=40)  # noqa: DTZ003 — KASITLI naive

    assert _profil(naive_eski).needs_update is True


def test_aware_tarih_de_calisir() -> None:
    """REGRESYON KALKANI: tz-bilgili tarih zaten calisiyordu, bozulmamali."""
    assert _profil(datetime.now(UTC) - timedelta(days=1)).needs_update is False
    assert _profil(datetime.now(UTC) - timedelta(days=40)).needs_update is True


def test_tarih_yoksa_guncellenmeli() -> None:
    """Mevcut sozlesme: `updated_at is None` -> True (degismedi)."""
    assert _profil(None).needs_update is True


def test_alet_dogrulamasi_esik_gercekten_30_gun() -> None:
    """KONTROL KOLU — esik gercekten 30 gun mu?

    Bu dusmezse yukaridaki 1-gun/40-gun ornekleri anlamli sinir olusturmaz.
    """
    assert _profil(datetime.now(UTC) - timedelta(days=29)).needs_update is False
    assert _profil(datetime.now(UTC) - timedelta(days=31)).needs_update is True
