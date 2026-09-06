"""6 haneli şifre sıfırlama kodu deposu — kod HESABA BAĞLI olmalı.

28 Tem 2026 tasarım incelemesi (satışa hazırlık blocker #1).

Mevcut akış `secrets.token_urlsafe(32)` üretip Redis'e `password_reset:<token>`
anahtarıyla yazıyor — yani token TEK BAŞINA kimlik. Ekran (`HesapKurtarmaPage`)
ise 6 haneli kod için tasarlanmış. Kodu aynı desenle saklamak (anahtar = kodun
kendisi) 10^6'lık GLOBAL bir ad alanı yaratırdı: saldırgan 000000-999999
tararken kendi hesabını değil, o sırada kod isteyen HERHANGİ BİRİNİN kodunu
bulurdu. 32 byte'ta zararsız olan desen 6 hanede zafiyete dönüşüyor.

Bu yüzden depo üç değişmezi taşımak zorunda:

  1. Kod (e-posta, kod) ÇİFTİNE bağlıdır — başka e-posta ile doğrulanamaz.
  2. Kod başına en fazla 5 deneme; aşılınca doğru kod bile reddedilir.
  3. Hesap başına saatte en fazla 3 kod. IP rate-limit'i tek başına YETMEZ:
     kod başına 5 deneme + IP başına 5 istek/300s => tek IP'den 25 tahmin/5dk,
     24 saatte ~7.200 tahmin = 10^6 uzayda %0,7. 100 IP ile %72. Limit hesaba
     bağlanınca IP rotasyonu etkisiz kalır (15 tahmin/saat => günde %0,036).

Testler İKİ backend'i de koşar (gerçek Redis + in-memory fallback). Sebep:
`backend/conftest.py:24` REDIS_URL'i `localhost:6380`'e eziyor ve orada Redis
yok, yani pytest içinde üretimdeki Redis dalı DEĞİL fallback dalı çalışıyor.
İki dal aynı kuralları uygulamazsa, test ettiğimiz kod üretimde koşan kod
olmaz — bu deponun 28 Tem'de üç kez ısırdığı hata sınıfı.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.password_reset_codes import PasswordResetCodeStore, _code_digest

pytestmark = [pytest.mark.unit, pytest.mark.security]

REDIS_TEST_URL = "redis://localhost:6379/15"


def _email() -> str:
    """Her test kendi e-postasını kullanır — testler birbirinin limitini yemesin."""
    return f"pwreset-{uuid.uuid4().hex[:12]}@kiro2.test"


async def _redis_kapat(client) -> None:
    """redis-py surum farkini yutan kapatma.

    OLCUM (6 Eyl 2026): CI'da bu dosya teardown'da patliyordu --
    `AttributeError: 'Redis' object has no attribute 'aclose'`. Sebep saf
    surum farki: `aclose()` redis-py 5.0.1'de eklendi; bu makinede kurulu
    surum 6.4.0 (aclose VAR, o yuzden yerelde hic gorulmedi) ama CI
    `requirements.txt`teki `redis[hiredis]==4.6.0` ile kuruluyor (aclose YOK).
    Test PASS ediyordu, yalnizca teardown patliyor, ama pytest bunu "1 error"
    sayip exit code 2 donduruyor -- yani tek basina Backend Tests is'ini
    kirmiziya cekiyordu.

    Uretim bagimliligini yukseltmek yerine testi iki surumle de calisir
    kilmak tercih edildi: burada olculen kusur surum secimi degil, testin
    tek bir surume sabitlenmis olmasi.
    """
    kapat = getattr(client, "aclose", None) or client.close
    await kapat()


async def _redis_client():
    try:
        import redis.asyncio as aioredis
    except ImportError:  # pragma: no cover - redis paketi her ortamda var
        return None
    client = aioredis.from_url(REDIS_TEST_URL, decode_responses=True)
    try:
        await client.ping()
    except Exception:
        await _redis_kapat(client)
        return None
    return client


@pytest.fixture(params=["memory", "redis"])
async def store(request):
    """Aynı test gövdesi iki backend'de de koşar."""
    if request.param == "memory":
        yield PasswordResetCodeStore(redis_client=None)
        return

    client = await _redis_client()
    if client is None:
        pytest.skip(f"Redis yok ({REDIS_TEST_URL}) — redis dalı doğrulanamıyor")
    try:
        yield PasswordResetCodeStore(redis_client=client)
    finally:
        await _redis_kapat(client)


@pytest.fixture(params=["memory", "redis"])
async def store_and_dump(request):
    """Depo + ham saklanan değerleri dökebilen yardımcı.

    Dökücü BİLEREK test tarafında: üretim sınıfına yalnız testin çağırdığı bir
    `debug_*` metodu eklemek, testi üretim yüzeyine borç yazmak olurdu. Bellek
    dalında özel alana dokunuyoruz — kasıtlı ve tek yerde.
    """
    if request.param == "memory":
        store = PasswordResetCodeStore(redis_client=None)

        # NOT: iki dalin dokucusu ayri isimlerde. Ikisi de `dump` olsaydi
        # mypy `no-redef` veriyordu (CI'da olculdu) -- ayni isim, ayni
        # kapsamda iki kez tanimlanmis sayiliyor, dallar birbirini disliyor
        # olsa bile. Isimlendirme ayrica hangi dalin okundugunu da belli ediyor.
        async def dump_bellek() -> list[str]:
            return [value for value, _expires in store._memory.values()]

        yield store, dump_bellek
        return

    client = await _redis_client()
    if client is None:
        pytest.skip(f"Redis yok ({REDIS_TEST_URL}) — redis dalı doğrulanamıyor")

    store = PasswordResetCodeStore(redis_client=client)

    async def dump_redis() -> list[str]:
        keys = await client.keys("password_reset*")
        values = [await client.get(k) for k in keys]
        return list(keys) + [v for v in values if v is not None]

    try:
        yield store, dump_redis
    finally:
        await _redis_kapat(client)


async def test_issued_code_is_six_digits(store: PasswordResetCodeStore):
    """Kod tam 6 rakam olmalı — baştaki sıfırlar dahil (ekran 6 hane bekliyor)."""
    code = await store.issue(_email(), "user-1")

    assert code is not None
    assert len(code) == 6, f"kod 6 haneli değil: {code!r}"
    assert code.isdigit(), f"kod rakam değil: {code!r}"


async def test_correct_code_returns_user_id(store: PasswordResetCodeStore):
    email = _email()
    code = await store.issue(email, "user-42")

    assert await store.verify(email, code) == "user-42"


async def test_code_is_bound_to_its_email(store: PasswordResetCodeStore):
    """EN KRİTİK DEĞİŞMEZ: kod başka bir e-posta ile doğrulanamaz.

    Bu test kırmızıya dönerse 6 haneli kod global ad alanına düşmüş demektir
    ve tüm akış kaba kuvvete açılır (bkz. modül docstring'i).
    """
    saldirgan = _email()
    kurban = _email()

    # SIRA ÖNEMLİ: saldırgan ÖNCE kod alır, kurban SONRA. Depo paylaşımlı bir
    # ad alanı kullanıyorsa kurbanın kaydı saldırganınkini ezer ve saldırganın
    # e-postasıyla yapılan doğrulama kurbanın kimliğini döndürür. Ters sırada
    # bu kusur gizli kalır — mutasyon testinde bizzat böyle oldu.
    await store.issue(saldirgan, "saldirgan-id")
    kurban_kodu = await store.issue(kurban, "kurban-id")

    sonuc = await store.verify(saldirgan, kurban_kodu)
    assert sonuc is None, (
        f"kurbanın kodu saldırganın e-postasıyla doğrulandı ({sonuc!r}) — "
        "kod hesaba bağlı değil, 6 hane global ad alanına düşmüş"
    )


def test_code_digest_is_bound_to_email():
    """Aynı kod, farklı e-posta => farklı özet.

    BEYAZ KUTU, bilerek. Kodun hesaba bağlılığı iki YEDEKLİ mekanizmayla
    sağlanıyor: anahtar e-postadan türetiliyor (`_slot`) ve değer e-posta+kodun
    HMAC'i (`_code_digest`). Mutasyon testi (scripts/mutation_check_password_
    reset.py) gösterdi ki birini tek başına bozmak kara-kutu testlerini
    kırmıyor — diğeri maskeliyor. Yedekli bir kontrol "var" sayılamaz, ayrıca
    sabitlenmesi gerekir.
    """
    kod = "123456"
    a = _code_digest("ayse@kiro2.test", kod)
    b = _code_digest("mehmet@kiro2.test", kod)

    assert a != b, "özet e-postadan bağımsız — kod hesaba bağlanmıyor"
    assert kod not in a, "özet kodu sızdırıyor"


@settings(max_examples=60, deadline=None)
@given(
    eposta=st.emails(),
    kod=st.text(alphabet="0123456789", min_size=6, max_size=6),
)
def test_digest_properties_hold_for_arbitrary_inputs(eposta: str, kod: str):
    """Özetin iki değişmezi RASTGELE girdide de tutmalı.

    Yukarıdaki iki beyaz-kutu testi elle seçilmiş örneklerle çalışıyor; burada
    Hypothesis aynı iddiaları geniş bir girdi uzayında sınıyor. Aradığımız şey
    "unuttuğum bir e-posta biçiminde özet çakışıyor mu" — elle örneklemenin
    yapısal olarak bulamayacağı sınıf.
    """
    ozet = _code_digest(eposta, kod)

    # 1) Deterministik: aynı çift her zaman aynı özeti verir (yoksa kullanıcı
    #    doğru kodu girse bile doğrulanamaz).
    assert ozet == _code_digest(eposta, kod)
    assert len(ozet) == 64  # sha256 hex

    # 2) E-postaya bağlı: aynı kod, farklı adres => farklı özet.
    assert ozet != _code_digest(eposta + "x", kod)


def test_code_digest_ignores_email_case_and_spacing():
    """Kullanıcı 1. adımda 'Ayse@X.com', 2. adımda 'ayse@x.com ' yazarsa akış kırılmamalı."""
    kod = "123456"
    assert _code_digest("Ayse@Kiro2.TEST", kod) == _code_digest(
        "  ayse@kiro2.test  ", kod
    )


async def test_code_is_single_use(store: PasswordResetCodeStore):
    email = _email()
    code = await store.issue(email, "user-1")

    assert await store.verify(email, code) == "user-1"
    assert await store.verify(email, code) is None, "kod ikinci kez kullanıldı"


@pytest.mark.parametrize(
    "yanlis_kod",
    ["000000", "999999", "12345", "1234567", "abcdef", "", "  "],
    ids=["sifirlar", "dokuzlar", "kisa", "uzun", "harf", "bos", "bosluk"],
)
async def test_wrong_or_malformed_code_is_rejected(
    store: PasswordResetCodeStore, yanlis_kod: str
):
    """Yanlış VE biçimi bozuk kodlar aynı şekilde reddedilmeli.

    Depo katmanı biçim doğrulaması yapmaz — kısa/uzun/harfli girdi de
    yalnızca "eşleşmedi" sonucunu vermeli, istisna fırlatmamalı. Uç
    katmanındaki uzunluk kontrolü kaldırılsa bile depo güvenli kalır.
    """
    email = _email()
    code = await store.issue(email, "user-1")
    if yanlis_kod == code:
        # Üretilen kod parametreyle çakışırsa test anlamsızlaşır (~10^-6).
        pytest.skip("üretilen kod parametreyle çakıştı")

    assert await store.verify(email, yanlis_kod) is None


async def test_correct_code_rejected_after_max_wrong_attempts(
    store: PasswordResetCodeStore,
):
    """5 yanlış denemeden sonra DOĞRU kod da reddedilmeli.

    Kilit yoksa 6 hane, IP rotasyonu ile taranabilir hale gelir.
    """
    email = _email()
    code = await store.issue(email, "user-1")
    yanlis = "000000" if code != "000000" else "111111"

    for i in range(PasswordResetCodeStore.MAX_ATTEMPTS):
        assert await store.verify(email, yanlis) is None, f"{i}. yanlış deneme geçti"

    assert (
        await store.verify(email, code) is None
    ), "kilit tutmadı — 5 yanlış denemeden sonra doğru kod hâlâ kabul ediliyor"


async def test_new_code_invalidates_previous_one(store: PasswordResetCodeStore):
    """'Kodu yeniden gönder' eskisini geçersiz kılmalı — iki geçerli kod olmaz."""
    email = _email()
    eski = await store.issue(email, "user-1")
    yeni = await store.issue(email, "user-1")

    assert eski != yeni
    assert await store.verify(email, eski) is None, "eski kod hâlâ geçerli"
    assert await store.verify(email, yeni) == "user-1"


async def test_issue_is_limited_per_account(store: PasswordResetCodeStore):
    """Hesap başına saatlik kod limiti — IP rotasyonuna karşı tek gerçek savunma."""
    email = _email()

    for i in range(PasswordResetCodeStore.MAX_ISSUES_PER_WINDOW):
        assert await store.issue(email, "user-1") is not None, f"{i}. kod verilmedi"

    assert (
        await store.issue(email, "user-1") is None
    ), "hesap başına kod limiti uygulanmıyor — kaba kuvvet penceresi sınırsız"


async def test_issue_limit_is_per_account_not_global(store: PasswordResetCodeStore):
    """Bir hesabın limiti dolunca BAŞKA hesap etkilenmemeli (DoS olur)."""
    dolu = _email()
    for _ in range(PasswordResetCodeStore.MAX_ISSUES_PER_WINDOW):
        await store.issue(dolu, "user-1")
    assert await store.issue(dolu, "user-1") is None

    assert (
        await store.issue(_email(), "user-2") is not None
    ), "bir hesabın limiti diğerlerini kilitliyor — hizmet dışı bırakma"


async def test_code_is_not_stored_in_plaintext(store_and_dump):
    """Redis dökümü ne kodu ne e-postayı vermeli.

    Veli-onay akışı (`veli_onay_service.py:71`) token'ı zaten hash'liyor;
    şifre sıfırlama token'ı ise düz metin saklıyor. Yeni kod deposu doğru
    tarafta duruyor: anahtar da değer de türetilmiş.
    """
    store, dump = store_and_dump
    email = _email()
    code = await store.issue(email, "user-1")

    ham = await dump()
    assert ham, "depo hiçbir şey yazmamış görünüyor"
    for parca in ham:
        assert code not in parca, f"kod düz metin saklanmış: {parca!r}"
        assert email not in parca, f"e-posta düz metin saklanmış: {parca!r}"


async def test_unknown_email_verify_returns_none(store: PasswordResetCodeStore):
    """Hiç kod istememiş e-posta için doğrulama sessizce başarısız olmalı."""
    assert await store.verify(_email(), "123456") is None


async def test_concurrent_wrong_attempts_do_not_exceed_limit(
    store: PasswordResetCodeStore,
):
    """Deneme sayacı atomik olmalı — oku-değiştir-yaz yarışı limiti aşındırır.

    JSON içinde sayaç tutulursa iki eşzamanlı yanlış tahmin aynı değeri okur
    ve limit fiilen 5'ten büyük olur.
    """
    email = _email()
    code = await store.issue(email, "user-1")
    yanlis = "000000" if code != "000000" else "111111"

    await asyncio.gather(
        *(
            store.verify(email, yanlis)
            for _ in range(PasswordResetCodeStore.MAX_ATTEMPTS)
        )
    )

    assert (
        await store.verify(email, code) is None
    ), "eşzamanlı yanlış denemeler sayacı aşındırdı — sayaç atomik değil"
