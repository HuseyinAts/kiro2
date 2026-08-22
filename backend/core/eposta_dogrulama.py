"""E-posta doğrulama: tek kullanımlık token deposu + giriş kapısı politikası.

NEDEN AYRI BİR MODÜL (22 Ağu 2026)
----------------------------------
A1 altın yolunun ikinci ayağı ("e-postasını doğrular") kodda YOKTU. Ölçüldü:
`users.is_verified` 21/21 `false`; kolonu **yükselten** bir uç yok, **okuyan**
bir giriş kontrolü yok. `application/commands/auth.py` kayıtta sabit `FALSE`
yazıyordu. Yani alan beyan edilmiş ama hiçbir yere bağlanmamıştı.

Politika (`muaf_mi` / `giris_engellenmeli_mi`) uçtan ve komuttan AYRI tutuluyor
ki karar tek yerde ölçülebilsin. `LoginCommandHandler` içine gömülü bir `if`
zinciri mutasyonla çivilenemez; saf fonksiyon çivilenir.

KAPI VARSAYILAN KAPALI — GEREKÇE ÖLÇÜLDÜ
----------------------------------------
SMTP yapılandırılmamış (#441, operatör işi). `core.email_util.send_email`
config yoksa gönderim yapmadan `False` döner. Kapı açık + SMTP ölü olsaydı:
yeni kullanıcı doğrulama e-postası alamaz, doğrulayamaz, giremez — kayıt akışı
sessizce kapanırdı. Bu yüzden kapı `EPOSTA_DOGRULAMA_ZORUNLU` ile açılır ve
SMTP canlıya alınana kadar KAPALI kalır.

MUAFİYET SINIRI — SAYI DEĞİL ÖLÇÜM
----------------------------------
Kapı açıldığında mevcut hesaplar kilitlenmemeli. 22 Ağu 2026 ölçümü:

    SELECT min(created_at), max(created_at), count(*) FROM users;
    -> 2026-08-09 23:07:18 | 2026-08-21 20:40:32 | 21     (UTC)
    SELECT now() AT TIME ZONE 'UTC';  -> 2026-08-22 04:18:53

`MUAFIYET_SINIRI` bu iki kısıtı birden karşılar: 21 hesabın **hepsinden**
sonra, ve `now()`'dan **önce** (gelecekteki bir sınır herkesi muaf yapar ve
kapıyı süse çevirirdi — `test_alet_dogrulamasi_muafiyet_siniri_gecmiste_ve_makul`
bunu çiviliyor).

Muafiyet KOD düzeyinde; DB'ye tek satır yazılmıyor, dolayısıyla sınırı
değiştirmek tek satırlık ve geri alınabilir bir işlem.

TOKEN DEPOSU
------------
`password_reset_codes.py` ile aynı ilke: ne anahtar ne değer düz metin token
taşır (depo dökümü linkleri vermemeli). Fark: burada token 32 byte'lık bir
link parçası, 6 haneli kod değil — anahtar uzayı zaten tahmin edilemez
olduğundan e-postaya bağlama gerekmiyor, token tek başına kimliktir.
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets
import time
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

logger = logging.getLogger(__name__)

# Bu tarihten ÖNCE açılmış hesaplar doğrulanmış sayılır (yukarıdaki ölçüme bak).
MUAFIYET_SINIRI = datetime(2026, 8, 22, tzinfo=UTC)

_ACIK_DEGERLER = frozenset({"1", "true", "yes", "evet", "on"})


def _pepper() -> bytes:
    """HMAC anahtarı — `password_reset_codes._pepper` ile aynı ilke.

    Süreç ömrü boyunca sabit olması yeterli: token'lar 24 saatlik. Sır
    döndürüldüğünde uçuştaki doğrulama linkleri geçersizleşir; kullanıcı
    yeniden gönderim isteyebildiği için bu kabul edilebilir.
    """
    secret = os.environ.get("JWT_SECRET") or os.environ.get("SECRET_KEY") or ""
    return secret.encode("utf-8") or b"kiro2-eposta-dogrulama-pepper"


def _token_digest(token: str) -> str:
    """Token'ın HMAC'i — token'ın kendisi hiç saklanmaz."""
    return hmac.new(_pepper(), f"eposta_dogrulama:{token}".encode(), sha256).hexdigest()


def _slot(email: str) -> str:
    """E-postadan türetilmiş, geri döndürülemez sayaç anahtarı.

    ASCII `lower()` KASITLI — `normalize_tr()` Türkçe yerel ayarı uygular ve
    "I" -> "ı" yaparak e-posta adresini bozar (`.claude/rules/case-convention.md`
    Endpoint Gate).
    """
    normalize = email.strip().lower()
    return hmac.new(_pepper(), f"slot:{normalize}".encode(), sha256).hexdigest()[:40]


# ---------------------------------------------------------------------------
# Kapı politikası — saf fonksiyonlar, tek karar noktası
# ---------------------------------------------------------------------------


def dogrulama_zorunlu_mu() -> bool:
    """Giriş kapısı açık mı? **Varsayılan KAPALI** (yukarıdaki SMTP gerekçesi)."""
    return (
        os.environ.get("EPOSTA_DOGRULAMA_ZORUNLU", "").strip().lower() in _ACIK_DEGERLER
    )


def muaf_mi(created_at: datetime | None) -> bool:
    """Hesap muafiyet sınırından önce mi açılmış?

    `created_at is None` -> **muaf**. Fail-open KASITLI: tarihi bilinmeyen
    satır bir veri kusurudur; kullanıcıyı dışarıda bırakmak o kusuru müşteriye
    fatura etmek olur.
    """
    if created_at is None:
        return True
    # DB sürücüsü naive datetime döndürebilir; UTC varsay (sütun UTC yazılıyor).
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return created_at < MUAFIYET_SINIRI


def giris_engellenmeli_mi(
    is_verified: bool, created_at: datetime | None = None
) -> bool:
    """Bu kullanıcının girişi e-posta doğrulanmadığı için engellenmeli mi?

    Üç koşulun ÜÇÜ birden gerekli: kapı açık **ve** hesap doğrulanmamış **ve**
    hesap muafiyet sınırından sonra açılmış.
    """
    if is_verified:
        return False
    if not dogrulama_zorunlu_mu():
        return False
    return not muaf_mi(created_at)


# ---------------------------------------------------------------------------
# Token deposu
# ---------------------------------------------------------------------------


class EpostaDogrulamaStore:
    """Tek kullanımlık doğrulama token'ını hash'li saklar.

    Redis verilmezse bellek-içi çalışır (tek süreçli test/geliştirme). İki dal
    değerleri AYNI biçimde tutar ki aynı testlerle doğrulanabilsinler.
    """

    TOKEN_TTL_SECONDS = 86_400  # 24 saat — e-postanın okunmasını bekleyecek kadar
    MAX_GONDERIM = 5
    GONDERIM_PENCERESI_SECONDS = 3600

    # Ad "TOKEN" içermiyor: ruff S105 değeri değil DEĞİŞKEN ADINI deseniyor ve
    # `KEY_TOKEN` yanlış-pozitif "hardcoded password" üretiyordu. Kardeş modül
    # `password_reset_codes.py` de alan adlarını (KEY_CODE/KEY_ISSUES) kullanıyor.
    KEY_DOGRULAMA = "eposta_dogrulama_token"
    KEY_GONDERIM = "eposta_dogrulama_gonderim"

    def __init__(self, redis_client: Any | None = None) -> None:
        self._redis = redis_client
        self._memory: dict[str, tuple[str, float]] = {}

    # ---- depo işlemleri ---------------------------------------------------

    def _mem_get(self, key: str) -> str | None:
        entry = self._memory.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at <= time.time():
            self._memory.pop(key, None)
            return None
        return value

    async def _get(self, key: str) -> str | None:
        if self._redis is None:
            return self._mem_get(key)
        deger = await self._redis.get(key)
        return str(deger) if deger is not None else None

    async def _set(self, key: str, value: str, ttl: int) -> None:
        if self._redis is None:
            self._memory[key] = (value, time.time() + ttl)
            return
        await self._redis.setex(key, ttl, value)

    async def _delete(self, key: str) -> None:
        if self._redis is None:
            self._memory.pop(key, None)
            return
        await self._redis.delete(key)

    async def _incr(self, key: str, ttl: int) -> int:
        """Sayacı atomik artır; ilk artışta TTL kur.

        Bellek dalında read-modify-write arasında `await` YOK — tek olay
        döngüsünde bölünemez, eşzamanlı istekler sayacı aşındıramaz.
        """
        if self._redis is None:
            current = self._mem_get(key)
            count = int(current) + 1 if current is not None else 1
            expires_at = (
                self._memory[key][1] if key in self._memory else time.time() + ttl
            )
            self._memory[key] = (str(count), expires_at)
            return count

        count = int(await self._redis.incr(key))
        if count == 1:
            await self._redis.expire(key, ttl)
        return count

    # ---- genel API --------------------------------------------------------

    async def token_uret(self, user_id: str, email: str) -> str:
        """Yeni doğrulama token'ı üret ve hash'ini sakla.

        Dönen değer e-postadaki linke konur; depoda YALNIZCA HMAC'i durur.
        """
        token = secrets.token_urlsafe(32)
        await self._set(
            f"{self.KEY_DOGRULAMA}:{_token_digest(token)}",
            user_id,
            self.TOKEN_TTL_SECONDS,
        )
        logger.info("e-posta doğrulama token'ı üretildi: %s", _slot(email))
        return token

    async def token_coz(self, token: str) -> str | None:
        """Token geçerliyse `user_id` döndür ve token'ı **imha et**.

        Tek kullanımlık: aynı link ikinci kez çalışmaz (replay koruması).
        """
        key = f"{self.KEY_DOGRULAMA}:{_token_digest(token)}"
        user_id = await self._get(key)
        if user_id is None:
            return None
        await self._delete(key)
        return user_id

    async def gonderim_hakki_var_mi(self, email: str) -> bool:
        """Hesap başına yeniden gönderim limiti.

        IP rate-limit'i tek başına yetmez: saldırgan IP rotasyonuyla onu aşar,
        ama limit hesaba bağlıysa aşamaz (`password_reset_codes` ile aynı ders).
        """
        count = await self._incr(
            f"{self.KEY_GONDERIM}:{_slot(email)}", self.GONDERIM_PENCERESI_SECONDS
        )
        return count <= self.MAX_GONDERIM


# ---------------------------------------------------------------------------
# TEK ÖRNEK — iki çağıran da BURADAN alır
# ---------------------------------------------------------------------------
# Token'ı üreten (`RegisterUserCommandHandler`, komut katmanı) ile onu çözen
# (`/eposta-dogrula/verify`, API katmanı) FARKLI katmanlarda. Her biri kendi
# örneğini yaratsaydı Redis'siz kurulumda ikisi ayrı süreç-içi `dict`e yazar ve
# doğrulama HER ZAMAN başarısız olurdu — sessizce. `api/auth.py:1297`'de
# belgelenen şifre-sıfırlama kusurunun birebir aynısı.
#
# Redis edinimi de bu yüzden burada: çağıranlardan biri istemciyi enjekte etseydi
# hangisinin önce çalıştığına bağlı olarak depo bazen Redis'li bazen bellekli
# olurdu (sıraya bağlı, teşhisi zor bir kusur).


class _Depo:
    def __init__(self) -> None:
        self.ornek: EpostaDogrulamaStore | None = None
        self.redis: Any | None = None
        self.redis_denendi = False


_depo = _Depo()


async def _redis_al() -> Any | None:
    """Redis istemcisi; erişilemezse `None` (bellek-içi moda düşülür).

    `redis_denendi` bayrağı olmadan Redis kapalıyken her istekte bir bağlantı
    zaman aşımı ödenirdi.
    """
    if _depo.redis_denendi:
        return _depo.redis

    _depo.redis_denendi = True
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
        await client.ping()
        _depo.redis = client
    except Exception:
        logger.warning(
            "e-posta doğrulama: Redis yok, süreç-içi belleğe düşülüyor. Çok "
            "işçili kurulumda token bir işçide üretilip diğerinde doğrulanacağı "
            "için akış SESSİZCE bozulur."
        )
        _depo.redis = None
    return _depo.redis


async def store_al() -> EpostaDogrulamaStore:
    """Süreç genelinde TEK `EpostaDogrulamaStore` örneği."""
    if _depo.ornek is None:
        _depo.ornek = EpostaDogrulamaStore(await _redis_al())
    return _depo.ornek


def dogrulama_epostasi_gonder(email: str, token: str) -> bool:
    """Doğrulama linkli e-postayı gönder.

    Gövde BURADA, tek yerde. Kayıt akışı (komut katmanı) ile "yeniden gönder"
    ucu (API katmanı) ayrı gövdeler yazsaydı ikisi zamanla ayrışırdı — komşu
    `veli_onay` kodunda tam olarak bu oldu: uç düzgün HTML gönderirken kayıt
    akışı `f"Token: {token}"` stub'ı gönderiyor (`commands/auth.py:148`).

    Returns:
        True  — mesaj gönderim kuyruğuna alındı
        False — SMTP yapılandırılmamış, e-posta GİTMEDİ
    """
    from core.email_util import send_email

    frontend = os.environ.get("FRONTEND_URL", "http://localhost:3001").rstrip("/")
    link = f"{frontend}/eposta-dogrula?token={token}"
    saat = EpostaDogrulamaStore.TOKEN_TTL_SECONDS // 3600
    html = (
        "<p>Merhaba,</p>"
        "<p>KIRO2 hesabınızı etkinleştirmek için e-posta adresinizi doğrulayın.</p>"
        f'<p><a href="{link}">E-postamı doğrula</a> '
        f"(bağlantı {saat} saat geçerli)</p>"
        '<p style="font-size:12px;color:#888">Bu kaydı siz yapmadıysanız bu '
        "e-postayı yok sayabilirsiniz.</p>"
    )
    kuyruga_alindi = send_email(email, "KIRO2 — E-posta Adresinizi Doğrulayın", html)
    if not kuyruga_alindi:
        logger.error(
            "Doğrulama e-postası GÖNDERİLEMEDİ (SMTP yapılandırılmamış): %s. "
            "EPOSTA_DOGRULAMA_ZORUNLU açıksa bu kullanıcı giriş YAPAMAZ.",
            email,
        )
    return bool(kuyruga_alindi)


async def dogrulama_baslat(user_id: str, email: str) -> bool:
    """Token üret + e-posta gönder. Kota dolduysa sessizce `False`.

    Hem kayıt akışı hem "yeniden gönder" ucu bunu çağırır — ikisinin de aynı
    kota ve aynı gövdeyi kullanması böyle garanti ediliyor.
    """
    store = await store_al()
    if not await store.gonderim_hakki_var_mi(email):
        logger.warning("doğrulama e-postası hesap limitine takıldı: %s", _slot(email))
        return False
    token = await store.token_uret(user_id, email)
    return dogrulama_epostasi_gonder(email, token)
