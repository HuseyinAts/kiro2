"""Kayıtta `username` çakışması HTTP 500 üretmemeli.

CANLI ÖLÇÜM (26 Ağu 2026, kontrol koluyla):
    POST /api/v1/auth/kayit  {"email": "<mevcut-yerel-ad>@baskabiralan.com", ...}
      -> HTTP 500  {"detail":"Dahili sunucu hatasi"}      users 47 -> 47 (oluşmadı)
    LOG: UniqueViolationError: duplicate key ... "ix_users_username"
    KONTROL KOLU: farklı yerel-ad ile aynı istek -> HTTP 201

Kök neden: `application/commands/auth.py:100` `username = email.split("@")[0]`
ve benzersizlik ön-kontrolü (`:67`) YALNIZ `email` üzerinde. DB'de
`ix_users_username` UNIQUE. Yani `ahmet@gmail.com` kayıtlıyken gelen
`ahmet@hotmail.com` **A1 altın yolunun 1. adımında** çöküyor ve kullanıcı
eyleme dönüştürülemez bir "Dahili sunucu hatasi" görüyor.

NEDEN SAF FONKSİYON
-------------------
Karar (hangi ad seçilir) DB erişiminden ayrıldı; `alinmis_mi` bir geri-çağrı.
Bu deponun kendi kalıbı (`core/eposta_dogrulama.py:10-12`): işleyicinin içine
gömülü bir döngü mutasyonla çivilenemez, saf fonksiyon çivilenir. Ayrıca test
canlı PostgreSQL gerektirmez — bu paket DSN'siz ortamda sessizce sqlite'a
düşüyor ve DB'ye dayanan bir test orada yanlış-yeşil olurdu.

ÜRÜN KARARI (kullanıcı seçti, 26 Ağu 2026): çakışmada RASTGELE son ek.
İlk kullanıcı temiz `ahmet` alır, çakışanlar `ahmet-k3f9` olur. Sayılı son ek
(`ahmet2`, `ahmet3`) reddedildi: username'den "bu yerel-adı kaç kişi kullanıyor"
okunabilirdi.
"""

from __future__ import annotations

import pytest

from application.commands.auth import (
    KULLANICI_ADI_MAX,
    KullaniciAdiUretilemediError,
    benzersiz_kullanici_adi,
)


def _sayan_kontrol(alinmislar: set[str]) -> tuple[callable, list[str]]:
    """`alinmis_mi` + hangi adayların sorulduğunun kaydı.

    Kayıt tutulmasının sebebi ALET DOĞRULAMASI: sorgu hiç yapılmazsa
    "çakışma yok" testi de geçerdi ve bekçi hiçbir şey ölçmezdi.
    """
    sorulanlar: list[str] = []

    async def alinmis_mi(aday: str) -> bool:
        sorulanlar.append(aday)
        return aday in alinmislar

    return alinmis_mi, sorulanlar


@pytest.mark.asyncio
async def test_alet_dogrulamasi_kontrol_gercekten_cagriliyor() -> None:
    """Sorgu hiç yapılmazsa aşağıdaki testler BOŞ geçerdi."""
    alinmis_mi, sorulanlar = _sayan_kontrol(set())
    await benzersiz_kullanici_adi("ahmet@gmail.com", alinmis_mi)
    assert sorulanlar == ["ahmet"], "taban aday tek seferde sorulmalıydı"


@pytest.mark.asyncio
async def test_cakisma_yoksa_taban_aynen_doner() -> None:
    alinmis_mi, _ = _sayan_kontrol(set())
    assert await benzersiz_kullanici_adi("ahmet@gmail.com", alinmis_mi) == "ahmet"


@pytest.mark.asyncio
async def test_taban_alinmissa_son_ekli_ad_uretilir() -> None:
    """CANLI KUSUR: bugün burada UniqueViolation -> HTTP 500 oluyor."""
    alinmis_mi, sorulanlar = _sayan_kontrol({"ahmet"})
    ad = await benzersiz_kullanici_adi("ahmet@hotmail.com", alinmis_mi)

    assert ad != "ahmet"
    assert ad.startswith("ahmet-"), f"taban korunmalı, üretilen: {ad!r}"
    assert len(sorulanlar) >= 2, "son ekli aday da sorgulanmalı"


@pytest.mark.asyncio
async def test_ilk_son_ek_de_alinmissa_yeniden_denenir() -> None:
    alinmis_mi, sorulanlar = _sayan_kontrol(set())
    cagri = {"n": 0}

    async def ilk_ikisi_alinmis(aday: str) -> bool:
        sorulanlar.append(aday)
        cagri["n"] += 1
        return cagri["n"] <= 2

    ad = await benzersiz_kullanici_adi("ahmet@gmail.com", ilk_ikisi_alinmis)
    assert ad.startswith("ahmet-")
    assert cagri["n"] == 3, "üçüncü adaya kadar denenmeliydi"
    assert len(set(sorulanlar[1:])) == len(sorulanlar[1:]), "son ekler TEKRARLANMAMALI"


@pytest.mark.asyncio
async def test_hepsi_alinmissa_sessizce_cakisan_ad_donmez() -> None:
    """Kontrol kolu: koruma "her zaman bir ad üret"e dönüşmemeli.

    Sessizce çakışan bir ad dönseydi çağıran yine UniqueViolation alır ve
    bugünkü 500 geri gelirdi — bu kez gizlenmiş hâlde.
    """
    alinmis_mi, _ = _sayan_kontrol(set())

    async def hep_alinmis(_aday: str) -> bool:
        return True

    with pytest.raises(KullaniciAdiUretilemediError):
        await benzersiz_kullanici_adi("ahmet@gmail.com", hep_alinmis)


@pytest.mark.asyncio
async def test_uzun_yerel_ad_kolon_sinirini_asmaz() -> None:
    """`users.username` varchar(100) NOT NULL (information_schema ile ölçüldü)."""
    uzun = "u" * 120
    alinmis_mi, _ = _sayan_kontrol(set())
    assert (
        len(await benzersiz_kullanici_adi(f"{uzun}@x.com", alinmis_mi))
        <= KULLANICI_ADI_MAX
    )

    # Çakışma dalında da: taban + ayraç + son ek sınırı aşmamalı.
    alinmis_mi2, _ = _sayan_kontrol({uzun[:KULLANICI_ADI_MAX]})

    async def taban_alinmis(aday: str) -> bool:
        return "-" not in aday

    ad = await benzersiz_kullanici_adi(f"{uzun}@x.com", taban_alinmis)
    assert len(ad) <= KULLANICI_ADI_MAX, f"{len(ad)} karakter üretildi"


@pytest.mark.asyncio
async def test_tek_harfli_yerel_ad_gecerli_ad_uretir() -> None:
    """`AuthenticatedUser.username` min_length=1 (core/dependencies.py:49)."""
    alinmis_mi, _ = _sayan_kontrol(set())
    assert await benzersiz_kullanici_adi("a@x.com", alinmis_mi) == "a"


@pytest.mark.asyncio
async def test_son_ek_tahmin_edilemez_olmali() -> None:
    """Sayılı son ek (ahmet2/ahmet3) ürün kararında REDDEDİLDİ.

    Gerekçe: `ahmet7` görmek "bu yerel-adı 7 kişi kullanıyor" bilgisini sızdırır.
    Bu test o kararı çiviler — sayaç tabanlı bir uygulamaya dönülürse düşer.
    """
    uretilenler = set()
    for _ in range(12):
        alinmis_mi, _ = _sayan_kontrol({"ahmet"})
        uretilenler.add(await benzersiz_kullanici_adi("ahmet@gmail.com", alinmis_mi))

    assert len(uretilenler) > 1, (
        f"12 denemede tek ad üretildi ({uretilenler}) — son ek deterministik, "
        "yani sayaç tabanlı veya sabit"
    )
    assert "ahmet2" not in uretilenler, "sayılı son ek ürün kararında reddedildi"
