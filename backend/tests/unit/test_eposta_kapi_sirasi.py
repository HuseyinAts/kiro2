"""Bekci: e-posta dogrulama kapisi SMTP'den ONCE kapanamaz.

TEHLIKE (S251, 24 Agu 2026 canli olcumu):
  konteynerde SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD/EMAIL_FROM -> 5/5 TANIMSIZ
  users.is_verified -> false=26 / true=12
Operator `EPOSTA_DOGRULAMA_ZORUNLU=true` yaparsa o 26 kullanici:
  (a) giris YAPAMAZ  (kapi kapali)
  (b) dogrulama e-postasi ALAMAZ (`send_email` SMTP yokken False donuyor)
-> KALICI KILITLENME. Sira "once SMTP, sonra kapi" olmak ZORUNDA.

Bu sira bugune kadar yalniz devir notunda yaziyordu. Yorum yaptirim degildir
(ayni ders: tests/test_migrations.py URETIM_DB_ADLARI). Burada YAPTIRIMA cevrildi.

AYRICA #466 dersi: dogrulayici ile tuketici FARKLI degisken okursa yanlis-pozitif
saglik sinyali uretilir. Bu yuzden `smtp_yapilandirilmis_mi()` ile `send_email`
AYNI kaynagi kullanmali -- son test bunu assert eder.
"""

from __future__ import annotations

import pytest

SMTP_DEGISKENLERI = (
    "SMTP_HOST",
    "SMTP_SERVER",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "EMAIL_FROM",
    "SMTP_PORT",
)


@pytest.fixture
def temiz_ortam(monkeypatch):
    """Her test kendi ortamini kurar; disaridan sizinti olmasin."""
    for ad in (*SMTP_DEGISKENLERI, "EPOSTA_DOGRULAMA_ZORUNLU"):
        monkeypatch.delenv(ad, raising=False)
    return monkeypatch


def _smtp_kur(monkeypatch) -> None:
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "kiro2@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "x")


def test_bayrak_acik_ama_smtp_yokken_kapi_acilmaz(temiz_ortam):
    """En kritik senaryo: operator kapiyi SMTP'den ONCE acmaya calisir."""
    from core.eposta_dogrulama import dogrulama_zorunlu_mu, kapi_engeli

    temiz_ortam.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")

    engel = kapi_engeli()
    assert engel is not None, "SMTP yokken kapi ACILDI -- 26 kullanici kilitlenirdi"
    assert "SMTP" in engel.upper()
    assert dogrulama_zorunlu_mu() is False


def test_bayrak_acik_ama_smtp_yokken_gurultu_cikarir(temiz_ortam, caplog):
    """Sessiz varsayilan YASAK: operator kapatmak istedi, edemedik -> haber ver."""
    import logging

    from core.eposta_dogrulama import dogrulama_zorunlu_mu

    temiz_ortam.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")

    with caplog.at_level(logging.ERROR):
        dogrulama_zorunlu_mu()

    assert any(
        "SMTP" in kayit.getMessage().upper() for kayit in caplog.records
    ), "kapi sessizce acilmadi -- operator yanlis sandigini dogru saniyor"


def test_smtp_hazir_ve_bayrak_acikken_kapi_acilir(temiz_ortam):
    """Kontrol kolu: koruma cok genis degil -- dogru sirada kapi GERCEKTEN acilir."""
    from core.eposta_dogrulama import dogrulama_zorunlu_mu, kapi_engeli

    _smtp_kur(temiz_ortam)
    temiz_ortam.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")

    assert kapi_engeli() is None
    assert dogrulama_zorunlu_mu() is True


def test_bayrak_kapaliyken_engel_sebebi_smtp_degil_bayrak(temiz_ortam):
    """Sebep ayirt edilmeli: 'SMTP yok' demek bayrak-kapali durumu yanlis raporlar."""
    from core.eposta_dogrulama import kapi_engeli

    _smtp_kur(temiz_ortam)  # SMTP TAMAM, bayrak yok

    engel = kapi_engeli()
    assert engel is not None
    assert "SMTP" not in engel.upper()
    assert "EPOSTA_DOGRULAMA_ZORUNLU" in engel


def test_giris_engellenmeli_smtp_yokken_kullaniciyi_disari_kilitlemez(temiz_ortam):
    """Uctan uca: dogrulanmamis + yeni hesap, bayrak acik, SMTP yok -> giris SERBEST."""
    from datetime import UTC, datetime

    from core.eposta_dogrulama import giris_engellenmeli_mi

    temiz_ortam.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")

    engellendi = giris_engellenmeli_mi(
        is_verified=False,
        created_at=datetime(2026, 8, 23, tzinfo=UTC),  # muafiyet sinirindan SONRA
    )
    assert engellendi is False, "SMTP yokken dogrulanmamis kullanici DISARI kilitlendi"


def test_giris_engellenmeli_smtp_hazirken_kullaniciyi_engeller(temiz_ortam):
    """Kontrol kolu: dogru sirada kapi GERCEKTEN engelliyor -- yukaridaki yesil anlamli."""
    from datetime import UTC, datetime

    from core.eposta_dogrulama import giris_engellenmeli_mi

    _smtp_kur(temiz_ortam)
    temiz_ortam.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")

    assert (
        giris_engellenmeli_mi(
            is_verified=False, created_at=datetime(2026, 8, 23, tzinfo=UTC)
        )
        is True
    )


@pytest.mark.parametrize(
    ("kurulan", "beklenen"),
    [
        (("SMTP_HOST",), False),  # #466: yalniz HOST YETMEZ
        (("SMTP_HOST", "SMTP_USERNAME"), False),
        (("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"), True),
        (("SMTP_SERVER", "SMTP_USERNAME", "SMTP_PASSWORD"), True),  # eski ad da gecerli
    ],
)
def test_smtp_kontrolu_send_email_ile_ayni_degiskenleri_okur(
    temiz_ortam, kurulan, beklenen
):
    """#466 dersi: dogrulayici ile tuketici ayrisirsa yanlis-pozitif saglik sinyali.

    `send_email` uc kosulu birden arar (host + username + password). Kapi kontrolu
    daha GEVSEK olursa kapi acilir ama e-posta gitmez -- tam da onlemeye calistigimiz
    kilitlenme.
    """
    from core.email_util import smtp_yapilandirilmis_mi

    for ad in kurulan:
        temiz_ortam.setenv(ad, "x")

    assert smtp_yapilandirilmis_mi() is beklenen
