"""6 haneli şifre sıfırlama kodu deposu.

NEDEN AYRI BİR MODÜL (28 Tem 2026)
----------------------------------
`api/auth.py` içindeki `RedisPasswordResetStore` 32 byte'lık token'ı Redis'e
ANAHTAR olarak yazar: `password_reset:<token>`. 32 byte'ta bu zararsızdır —
token tek başına kimliktir ve tahmin edilemez. Aynı deseni 6 haneli kod için
kullanmak zafiyet üretir: anahtar uzayı 10^6'ya iner ve GLOBAL olur, yani
saldırgan 000000-999999 tararken kendi hesabını değil, o sırada kod isteyen
herhangi bir kullanıcının kodunu bulur.

Bu yüzden kod ayrı bir depoda ve üç değişmezle tutulur:

  1. Kod (e-posta, kod) çiftine bağlıdır. Anahtar e-postadan türetilir, değer
     kodun HMAC'idir; kod tek başına hiçbir kapıyı açmaz.
  2. Kod başına en fazla MAX_ATTEMPTS yanlış deneme. Limit dolunca kod imha
     edilir — doğru kod bile artık kabul edilmez.
  3. Hesap başına ISSUE_WINDOW_SECONDS içinde en fazla MAX_ISSUES_PER_WINDOW
     kod. IP rate-limit'i (auth.py `password_reset` kovası) tek başına yetmez:
     saldırgan IP rotasyonuyla onu aşar, ama limit hesaba bağlıysa aşamaz.

Ne anahtar ne değer düz metin taşır (Redis dökümü kodları vermemeli). Aynı
yaklaşım `services/veli_onay_service.py:71`'de zaten kullanılıyor.

REDIS YOKSA
-----------
`redis_client=None` ile açıkça bellek-içi mod istenebilir (tek süreçli test /
geliştirme). Ama bir istemci VERİLMİŞ ve o istemci hata veriyorsa, sessizce
belleğe DÜŞMÜYORUZ: kod Redis'e yazılıp bellekten doğrulanırsa deneme sayacı
kaybolur ve kaba kuvvet limiti fiilen kalkar. Hata yukarı taşınır, uç jenerik
başarısızlık döner ve olay loglanır — güvenlik kontrolü sessizce kapanmaz.
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets
import time
from hashlib import sha256
from typing import Any

logger = logging.getLogger(__name__)

CODE_DIGITS = 6


def _pepper() -> bytes:
    """HMAC anahtarı.

    Süreç ömrü boyunca sabit olması yeterli: kodlar 15 dakikalık. Sır
    döndürüldüğünde uçuştaki kodlar geçersizleşir, bu kabul edilebilir.
    """
    secret = os.environ.get("JWT_SECRET") or os.environ.get("SECRET_KEY") or ""
    return secret.encode("utf-8") or b"kiro2-password-reset-pepper"


def _normalize_email(email: str) -> str:
    """E-postayı anahtar türetimi için sadeleştir.

    ASCII `lower()` KASITLI. `core.turkish_nlp_utils.normalize_tr()` Türkçe
    yerel ayarı uygular ve "I" -> "ı" yapar; bu bir e-posta adresini bozar.
    `.claude/rules/case-convention.md` "Endpoint Gate" tam olarak bunu yasaklar:
    tanımlayıcılar ASCII etikettir, Türkçe düzyazı değildir.
    """
    return email.strip().lower()


def _slot(email: str) -> str:
    """E-postadan türetilmiş, geri döndürülemez depo anahtarı parçası."""
    return hmac.new(
        _pepper(), f"slot:{_normalize_email(email)}".encode(), sha256
    ).hexdigest()[:40]


def _code_digest(email: str, code: str) -> str:
    """Kodun e-postaya bağlanmış HMAC'i — kodun kendisi hiç saklanmaz."""
    return hmac.new(
        _pepper(), f"code:{_normalize_email(email)}:{code}".encode(), sha256
    ).hexdigest()


class PasswordResetCodeStore:
    """6 haneli kodu hash'li saklar, denemeleri atomik sayar."""

    CODE_TTL_SECONDS = 900  # 15 dk — ekrandaki "kod yolda" adımıyla uyumlu
    MAX_ATTEMPTS = 5
    MAX_ISSUES_PER_WINDOW = 3
    ISSUE_WINDOW_SECONDS = 3600

    KEY_CODE = "password_reset_code"
    KEY_ATTEMPTS = "password_reset_attempts"
    KEY_ISSUES = "password_reset_issues"

    def __init__(self, redis_client: Any | None = None) -> None:
        self._redis = redis_client
        # key -> (value, expires_at). Redis'siz mod için; değerler Redis'tekiyle
        # AYNI biçimde tutulur ki iki dal aynı testlerle doğrulanabilsin.
        self._memory: dict[str, tuple[str, float]] = {}

    # ---- backend işlemleri -------------------------------------------------

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
        # redis-py tip bilgisi yok (stub kurulu değil) -> Any döner; sözleşmeyi
        # burada sabitliyoruz (decode_responses=True ile istemci str verir).
        deger = await self._redis.get(key)
        return str(deger) if deger is not None else None

    async def _set(self, key: str, value: str, ttl: int) -> None:
        if self._redis is None:
            self._memory[key] = (value, time.time() + ttl)
            return
        await self._redis.setex(key, ttl, value)

    async def _incr(self, key: str, ttl: int) -> int:
        """Sayacı atomik artır; ilk artışta TTL kur.

        Bellek dalında read-modify-write arasında `await` YOK — tek olay
        döngüsünde bölünemez, dolayısıyla eşzamanlı denemeler sayacı aşındıramaz.
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

    async def _delete(self, *keys: str) -> None:
        if self._redis is None:
            for key in keys:
                self._memory.pop(key, None)
            return
        await self._redis.delete(*keys)

    # ---- genel API ---------------------------------------------------------

    async def issue(self, email: str, user_id: str) -> str | None:
        """Yeni kod üret ve sakla. Hesap limiti aşıldıysa `None`.

        `None` dönmesi çağırana "kullanıcıya farklı bir şey söyle" demez —
        numaralandırmayı önlemek için uç yine aynı jenerik yanıtı vermelidir.
        """
        slot = _slot(email)

        issued = await self._incr(
            f"{self.KEY_ISSUES}:{slot}", self.ISSUE_WINDOW_SECONDS
        )
        if issued > self.MAX_ISSUES_PER_WINDOW:
            logger.warning(
                "şifre sıfırlama: hesap başına kod limiti aşıldı (slot=%s, sayı=%d)",
                slot[:8],
                issued,
            )
            return None

        code = f"{secrets.randbelow(10**CODE_DIGITS):0{CODE_DIGITS}d}"
        await self._set(
            f"{self.KEY_CODE}:{slot}",
            f"{_code_digest(email, code)}:{user_id}",
            self.CODE_TTL_SECONDS,
        )
        # Yeni kod = yeni deneme hakkı. Kötüye kullanımı sınırlayan şey deneme
        # sayacı değil, yukarıdaki hesap-başına kod limitidir.
        await self._delete(f"{self.KEY_ATTEMPTS}:{slot}")
        return code

    async def verify(self, email: str, code: str) -> str | None:
        """Kod doğruysa `user_id`, değilse `None`. Doğru kod tek kullanımlıktır."""
        slot = _slot(email)
        code_key = f"{self.KEY_CODE}:{slot}"
        attempts_key = f"{self.KEY_ATTEMPTS}:{slot}"

        payload = await self._get(code_key)
        if payload is None:
            return None

        stored_digest, _, user_id = payload.partition(":")
        if not hmac.compare_digest(stored_digest, _code_digest(email, code)):
            attempts = await self._incr(attempts_key, self.CODE_TTL_SECONDS)
            if attempts >= self.MAX_ATTEMPTS:
                # Kilit: kodu imha et. Bundan sonra DOĞRU kod da çalışmaz;
                # kullanıcı yeni kod ister (hesap limitine tabi).
                await self._delete(code_key, attempts_key)
                logger.warning(
                    "şifre sıfırlama: kod deneme limiti doldu, kod imha edildi "
                    "(slot=%s)",
                    slot[:8],
                )
            return None

        await self._delete(code_key, attempts_key)
        return user_id or None
