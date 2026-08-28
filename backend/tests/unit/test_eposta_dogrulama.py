"""L2 — e-posta doğrulama: token deposu + giriş kapısı politikası.

NEDEN VAR
---------
22 Ağu 2026 ölçümü: A1 altın yolunun ("kayıt → **e-postasını doğrular** → test
çözer → netini görür") ikinci ayağı YOKTU. Ölçüldü:

  users.is_verified                     -> 21/21 `false`
  `is_verified` okuyan giriş kodu       -> 0  (grep, backend/**)
  doğrulama ucu (openapi 1119 yol)      -> 0
  application/commands/auth.py:94       -> INSERT ... is_verified FALSE  (sabit)

Yani kolon vardı, hiçbir şey onu **yükseltmiyordu** ve hiçbir şey onu
**okumuyordu** — beyan edilmiş ama bağlanmamış bir alan.

TASARIM KARARLARI (kullanıcı onayı, 22 Ağu 2026)
------------------------------------------------
1. **Kapı varsayılan KAPALI** (`EPOSTA_DOGRULAMA_ZORUNLU`). Gerekçe ölçüldü:
   SMTP yapılandırılmamış (#441, operatör). `core.email_util.send_email` config
   yoksa sessizce `False` döner. Kapı açık + SMTP ölü = yeni kayıtlar doğrulama
   e-postası ALAMAZ ve giriş de yapamaz -> kayıt akışı fiilen kapanır.
   Flag, SMTP canlıya alınınca tek env değişkeniyle açılır.
2. **Muafiyet sınırı** — kapı açıldığında mevcut hesaplar kilitlenmemeli.
   `MUAFIYET_SINIRI`'ndan önce açılmış hesaplar doğrulanmış sayılır. Kod
   düzeyinde; DB yazımı YOK, dolayısıyla geri alınabilir.

KONTROL KOLU NOTU
-----------------
Bu dosyadaki her "engelle" testinin bir "engelleme" ikizi var. Aksi hâlde
`return True` yazan bir "fix" (herkesi engelle) veya `return False` yazan bir
"fix" (hiç kimseyi engelleme) testleri geçerdi.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from core.eposta_dogrulama import (
    MUAFIYET_SINIRI,
    EpostaDogrulamaStore,
    dogrulama_zorunlu_mu,
    giris_engellenmeli_mi,
    muaf_mi,
)

# --------------------------------------------------------------------------
# Alet doğrulaması — premis ölçümü
# --------------------------------------------------------------------------


def test_alet_dogrulamasi_muafiyet_siniri_gecmiste_ve_makul() -> None:
    """Premis: sınır geçmişte olmalı, yoksa muafiyet HERKESİ kapsar.

    Bu düşerse aşağıdaki muafiyet testleri anlamsızdır — sınır geleceği
    gösteriyorsa `muaf_mi` sabit `True` döndüren bir fonksiyondur.
    """
    assert MUAFIYET_SINIRI.tzinfo is not None, "sınır naive datetime — UTC şart"
    assert datetime.now(UTC) >= MUAFIYET_SINIRI, (
        f"muafiyet sınırı gelecekte ({MUAFIYET_SINIRI}) — her hesap muaf olur, "
        "kapı hiçbir zaman kimseyi engellemez"
    )


def _smtp_hazir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kapinin acilabilmesi icin SMTP de gerekli (S251 sira yaptirimi).

    Bayrak TEK BASINA yetmiyor: SMTP olmadan kapi acilsaydi dogrulanmamis
    kullanicilar ne girebilir ne dogrulama postasi alabilirdi. Bu on kosul
    testlerde GORUNUR birakiliyor -- autouse fixture ile gizlenirse yaptirim
    kazara kaldirildiginda hicbir test dusmezdi.
    """
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "kiro2@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "x")


# --------------------------------------------------------------------------
# Flag — varsayılan KAPALI
# --------------------------------------------------------------------------


def test_flag_varsayilan_kapali(monkeypatch: pytest.MonkeyPatch) -> None:
    """SMTP ölüyken kapı kendiliğinden açılmamalı (#441 kilitlenme tuzağı)."""
    monkeypatch.delenv("EPOSTA_DOGRULAMA_ZORUNLU", raising=False)
    assert dogrulama_zorunlu_mu() is False


@pytest.mark.parametrize("deger", ["1", "true", "TRUE", "yes", " true "])
def test_flag_acilabiliyor(monkeypatch: pytest.MonkeyPatch, deger: str) -> None:
    """KONTROL KOLU: flag hiç açılamıyorsa 'varsayılan kapalı' anlamsızdır."""
    _smtp_hazir(monkeypatch)
    monkeypatch.setenv("EPOSTA_DOGRULAMA_ZORUNLU", deger)
    assert dogrulama_zorunlu_mu() is True


@pytest.mark.parametrize("deger", ["0", "false", "", "hayir"])
def test_flag_sacma_degerde_kapali(monkeypatch: pytest.MonkeyPatch, deger: str) -> None:
    monkeypatch.setenv("EPOSTA_DOGRULAMA_ZORUNLU", deger)
    assert dogrulama_zorunlu_mu() is False


# --------------------------------------------------------------------------
# Muafiyet — mevcut hesaplar kilitlenmemeli
# --------------------------------------------------------------------------


def test_sinirdan_onceki_hesap_muaf() -> None:
    assert muaf_mi(MUAFIYET_SINIRI - timedelta(seconds=1)) is True


def test_sinirdan_sonraki_hesap_muaf_degil() -> None:
    """KONTROL KOLU: `return True` yazan bir muafiyet fonksiyonunu öldürür."""
    assert muaf_mi(MUAFIYET_SINIRI + timedelta(seconds=1)) is False


def test_created_at_yoksa_muaf() -> None:
    """Tarihi bilinmeyen hesabı kilitleme — fail-open KASITLI.

    Gerekçe: `created_at` NULL olan bir satır veri kusurudur; kullanıcıyı
    dışarıda bırakmak o kusuru müşteriye fatura etmektir.
    """
    assert muaf_mi(None) is True


def test_naive_created_at_utc_sayilir() -> None:
    """DB'den naive datetime gelebilir — karşılaştırma patlamamalı."""
    naive = (MUAFIYET_SINIRI - timedelta(days=1)).replace(tzinfo=None)
    assert muaf_mi(naive) is True


# --------------------------------------------------------------------------
# Tek karar noktası — giris_engellenmeli_mi
# --------------------------------------------------------------------------


def _yeni() -> datetime:
    return MUAFIYET_SINIRI + timedelta(days=1)


def test_flag_kapaliyken_dogrulanmamis_giris_engellenmez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bugünkü canlı davranış: kapı kapalı, kimse kilitlenmiyor."""
    monkeypatch.delenv("EPOSTA_DOGRULAMA_ZORUNLU", raising=False)
    assert giris_engellenmeli_mi(is_verified=False, created_at=_yeni()) is False


def test_flag_acikken_dogrulanmamis_yeni_hesap_engellenir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kapının ASIL işi. Bu düşerse kapı süstür."""
    _smtp_hazir(monkeypatch)
    monkeypatch.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")
    assert giris_engellenmeli_mi(is_verified=False, created_at=_yeni()) is True


def test_flag_acikken_dogrulanmis_engellenmez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KONTROL KOLU: `return True` yazan bir kapı herkesi kilitlerdi."""
    _smtp_hazir(monkeypatch)
    monkeypatch.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")
    assert giris_engellenmeli_mi(is_verified=True, created_at=_yeni()) is False


def test_flag_acikken_eski_hesap_engellenmez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """21 mevcut hesabın kilitlenmemesini çivileyen assert."""
    _smtp_hazir(monkeypatch)
    monkeypatch.setenv("EPOSTA_DOGRULAMA_ZORUNLU", "true")
    eski = MUAFIYET_SINIRI - timedelta(days=30)
    assert giris_engellenmeli_mi(is_verified=False, created_at=eski) is False


# --------------------------------------------------------------------------
# Token deposu
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_token_uretilir_ve_dogrulanir() -> None:
    store = EpostaDogrulamaStore()
    token = await store.token_uret("usr-1", "ogrenci@example.com")
    assert token, "boş token üretildi"
    assert await store.token_coz(token) == "usr-1"


@pytest.mark.asyncio
async def test_token_tek_kullanimlik() -> None:
    """Doğrulama linki iki kez çalışmamalı (replay)."""
    store = EpostaDogrulamaStore()
    token = await store.token_uret("usr-1", "ogrenci@example.com")
    assert await store.token_coz(token) == "usr-1"
    assert await store.token_coz(token) is None


@pytest.mark.asyncio
async def test_gecersiz_token_none_doner() -> None:
    store = EpostaDogrulamaStore()
    assert await store.token_coz("boyle-bir-token-yok") is None


@pytest.mark.asyncio
async def test_ham_token_bellekte_saklanmaz() -> None:
    """Depo sızarsa token'lar doğrudan kullanılabilir OLMAMALI."""
    store = EpostaDogrulamaStore()
    token = await store.token_uret("usr-1", "ogrenci@example.com")
    seri = repr(store._memory)
    assert token not in seri, "ham token depoda düz metin duruyor"


@pytest.mark.asyncio
async def test_iki_token_farklidir() -> None:
    """KONTROL KOLU: sabit token döndüren bir 'fix' üstteki testleri geçerdi."""
    store = EpostaDogrulamaStore()
    t1 = await store.token_uret("usr-1", "a@example.com")
    t2 = await store.token_uret("usr-2", "b@example.com")
    assert t1 != t2


@pytest.mark.asyncio
async def test_yeniden_gonderim_siniri() -> None:
    """Doğrulama e-postası spam aracına dönüşmemeli."""
    store = EpostaDogrulamaStore()
    eposta = "ogrenci@example.com"
    for _ in range(store.MAX_GONDERIM):
        assert await store.gonderim_hakki_var_mi(eposta) is True
    assert await store.gonderim_hakki_var_mi(eposta) is False


@pytest.mark.asyncio
async def test_yeniden_gonderim_siniri_epostaya_ozel() -> None:
    """KONTROL KOLU: global sayaç bir kullanıcının diğerini kilitlemesine yol açar."""
    store = EpostaDogrulamaStore()
    for _ in range(store.MAX_GONDERIM):
        await store.gonderim_hakki_var_mi("dolan@example.com")
    assert await store.gonderim_hakki_var_mi("baskasi@example.com") is True
