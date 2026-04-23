"""
Circuit Breaker Pattern Implementation

Bu modul, hatalı endpoint'leri otomatik olarak devre dışı bırakan
circuit breaker pattern'ini implement eder.

State Machine:
- CLOSED: Normal işlem, tüm istekler geçer
- OPEN: Devre açık, tüm istekler reddedilir (503)
- HALF_OPEN: Test modu, tek istek kabul edilir

Transitions:
- CLOSED -> OPEN: 5 ardışık hata sonrası
- OPEN -> HALF_OPEN: 30 saniye sonra
- HALF_OPEN -> CLOSED: Test başarılı
- HALF_OPEN -> OPEN: Test başarısız
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from .models import CircuitState

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit Breaker pattern implementasyonu.

    Bu sınıf, endpoint'lerin hata durumlarını takip eder ve
    ardışık hatalar sonucunda circuit'i açarak sistemi korur.

    Attributes:
        redis_client: Redis client instance'ı
        failure_threshold: Circuit açma için gerekli ardışık hata sayısı
        recovery_timeout: OPEN -> HALF_OPEN geçiş süresi (saniye)
        states: Endpoint'lerin circuit durumları
        failure_counts: Endpoint'lerin ardışık hata sayıları
        last_failure_times: Son hata zamanları

    Requirements:
        REQ-4.1: 5 ardışık hata sonrası circuit OPEN
        REQ-4.2: OPEN durumda istekler 503 ile reddedilir
        REQ-4.3: 30 saniye sonra HALF_OPEN
        REQ-4.4: HALF_OPEN'da başarı -> CLOSED
        REQ-4.5: HALF_OPEN'da hata -> OPEN
        REQ-4.6: Durum değişikliklerini logla ve bildir
    """

    def __init__(
        self,
        redis_client=None,
        failure_threshold: int = 5,
        recovery_timeout: int = 30
    ):
        """
        CircuitBreaker sınıfını başlatır.

        Args:
            redis_client: Redis client instance'ı
            failure_threshold: Circuit açma eşiği (varsayılan: 5)
            recovery_timeout: Recovery süresi saniye cinsinden (varsayılan: 30)
        """
        self.redis_client = redis_client
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        # In-memory state storage (Redis backup olarak kullanılır)
        self.states: dict[str, CircuitState] = {}
        self.failure_counts: dict[str, int] = {}
        self.last_failure_times: dict[str, datetime] = {}
        self.opened_at: dict[str, datetime] = {}

        # State change callbacks
        self._on_state_change_callbacks: list[Callable] = []

        logger.info(
            f"CircuitBreaker başlatıldı: "
            f"threshold={failure_threshold}, timeout={recovery_timeout}s"
        )

    async def get_state(self, endpoint_key: str) -> CircuitState:
        """
        Endpoint'in mevcut circuit durumunu getirir.

        Eğer circuit OPEN durumda ve recovery_timeout geçmişse,
        otomatik olarak HALF_OPEN'a geçer.

        Args:
            endpoint_key: Endpoint key (method:path formatında)

        Returns:
            CircuitState enum değeri

        Requirements:
            REQ-4.3: 30 saniye sonra HALF_OPEN durumuna geçer
        """
        # Redis'ten state'i al (varsa)
        if self.redis_client:
            try:
                redis_key = f"kiro2:health:circuit:{endpoint_key}"
                state_data = await self.redis_client.hgetall(redis_key)

                if state_data:
                    state_str = state_data.get(b"state", b"closed").decode()
                    opened_at_str = state_data.get(b"opened_at", b"").decode()

                    if state_str == "open" and opened_at_str:
                        opened_at = datetime.fromisoformat(opened_at_str)
                        elapsed = datetime.now(UTC) - opened_at

                        # Recovery timeout geçti mi?
                        if elapsed.total_seconds() >= self.recovery_timeout:
                            await self._transition_to(
                                endpoint_key,
                                CircuitState.HALF_OPEN,
                                "Recovery timeout elapsed"
                            )
                            return CircuitState.HALF_OPEN

                    return CircuitState(state_str)
            except Exception as e:
                logger.error(f"Redis'ten state alınamadı: {e}")

        # In-memory fallback
        state = self.states.get(endpoint_key, CircuitState.CLOSED)

        # OPEN durumda timeout kontrolü
        if state == CircuitState.OPEN and endpoint_key in self.opened_at:
            elapsed = datetime.now(UTC) - self.opened_at[endpoint_key]
            if elapsed.total_seconds() >= self.recovery_timeout:
                await self._transition_to(
                    endpoint_key,
                    CircuitState.HALF_OPEN,
                    "Recovery timeout elapsed"
                )
                return CircuitState.HALF_OPEN

        return state

    async def record_success(self, endpoint_key: str) -> None:
        """
        Başarılı bir istek kaydeder.

        HALF_OPEN durumda başarılı istek circuit'i kapatır.
        CLOSED durumda hata sayacını sıfırlar.

        Args:
            endpoint_key: Endpoint key

        Requirements:
            REQ-4.4: HALF_OPEN durumda test başarılı -> CLOSED
        """
        current_state = await self.get_state(endpoint_key)

        if current_state == CircuitState.HALF_OPEN:
            # Test başarılı, circuit'i kapat
            await self._transition_to(
                endpoint_key,
                CircuitState.CLOSED,
                "Test request successful in HALF_OPEN state"
            )

        # Hata sayacını sıfırla
        self.failure_counts[endpoint_key] = 0

        logger.debug(f"Başarı kaydedildi: {endpoint_key}")

    async def record_failure(self, endpoint_key: str, error: str | None = None) -> None:
        """
        Başarısız bir istek kaydeder.

        Ardışık hata sayısı threshold'u aşarsa circuit açılır.
        HALF_OPEN durumda hata circuit'i tekrar açar.

        Args:
            endpoint_key: Endpoint key
            error: Hata mesajı (opsiyonel)

        Requirements:
            REQ-4.1: 5 ardışık hata -> OPEN
            REQ-4.5: HALF_OPEN durumda hata -> OPEN
        """
        current_state = await self.get_state(endpoint_key)

        if current_state == CircuitState.HALF_OPEN:
            # Test başarısız, tekrar OPEN'a geç
            await self._transition_to(
                endpoint_key,
                CircuitState.OPEN,
                f"Test request failed in HALF_OPEN state: {error}"
            )
            return

        if current_state == CircuitState.OPEN:
            # Zaten açık, işlem yapma
            return

        # CLOSED durumda hata sayacını artır
        self.failure_counts[endpoint_key] = self.failure_counts.get(endpoint_key, 0) + 1
        self.last_failure_times[endpoint_key] = datetime.now(UTC)

        logger.warning(
            f"Hata kaydedildi: {endpoint_key} - "
            f"Toplam: {self.failure_counts[endpoint_key]}/{self.failure_threshold}"
        )

        # Threshold'u geçtiyse circuit'i aç
        if self.failure_counts[endpoint_key] >= self.failure_threshold:
            await self._transition_to(
                endpoint_key,
                CircuitState.OPEN,
                f"Failure threshold reached ({self.failure_threshold} consecutive failures)"
            )

    async def _transition_to(
        self,
        endpoint_key: str,
        new_state: CircuitState,
        reason: str
    ) -> None:
        """
        Circuit durumunu değiştirir.

        Args:
            endpoint_key: Endpoint key
            new_state: Yeni durum
            reason: Geçiş nedeni

        Requirements:
            REQ-4.6: Durum değişikliğini loglar ve bildirim gönderir
        """
        old_state = self.states.get(endpoint_key, CircuitState.CLOSED)

        if old_state == new_state:
            return

        # State'i güncelle
        self.states[endpoint_key] = new_state

        # OPEN'a geçişte timestamp kaydet
        if new_state == CircuitState.OPEN:
            self.opened_at[endpoint_key] = datetime.now(UTC)
        elif new_state == CircuitState.CLOSED:
            # CLOSED'a geçişte temizlik yap
            self.failure_counts[endpoint_key] = 0
            if endpoint_key in self.opened_at:
                del self.opened_at[endpoint_key]

        # Loglama
        log_message = (
            f"Circuit state değişti: {endpoint_key}\n"
            f"  {old_state.value} -> {new_state.value}\n"
            f"  Neden: {reason}"
        )

        if new_state == CircuitState.OPEN:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Redis'e kaydet
        if self.redis_client:
            await self._store_state(endpoint_key, new_state)

        # Callbacks'leri çağır
        await self._notify_state_change(endpoint_key, old_state, new_state, reason)

    async def _store_state(self, endpoint_key: str, state: CircuitState) -> None:
        """
        Circuit state'ini Redis'e kaydeder.

        Args:
            endpoint_key: Endpoint key
            state: Circuit state
        """
        if not self.redis_client:
            return

        try:
            redis_key = f"kiro2:health:circuit:{endpoint_key}"

            data = {
                "state": state.value,
                "updated_at": datetime.now(UTC).isoformat(),
                "failure_count": str(self.failure_counts.get(endpoint_key, 0))
            }

            # OPEN durumda opened_at ekle
            if state == CircuitState.OPEN and endpoint_key in self.opened_at:
                data["opened_at"] = self.opened_at[endpoint_key].isoformat()

            await self.redis_client.hset(redis_key, mapping=data)
            await self.redis_client.expire(redis_key, 86400)  # 24 saat

            logger.debug(f"Circuit state Redis'e kaydedildi: {redis_key}")
        except Exception as e:
            logger.error(f"Circuit state kaydedilemedi: {e}")

    async def _notify_state_change(
        self,
        endpoint_key: str,
        old_state: CircuitState,
        new_state: CircuitState,
        reason: str
    ) -> None:
        """
        State değişikliği bildirimlerini gönderir.

        Args:
            endpoint_key: Endpoint key
            old_state: Eski durum
            new_state: Yeni durum
            reason: Geçiş nedeni
        """
        # Registered callbacks'leri çağır
        for callback in self._on_state_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(endpoint_key, old_state, new_state, reason)
                else:
                    callback(endpoint_key, old_state, new_state, reason)
            except Exception as e:
                logger.error(f"State change callback hatası: {e}")

        # Redis'e notification kaydet
        if self.redis_client and new_state == CircuitState.OPEN:
            try:
                notification = {
                    "type": "circuit_opened",
                    "endpoint": endpoint_key,
                    "reason": reason,
                    "timestamp": datetime.now(UTC).isoformat()
                }

                await self.redis_client.lpush(
                    "kiro2:health:notifications",
                    str(notification)
                )
                await self.redis_client.ltrim("kiro2:health:notifications", 0, 999)
            except Exception as e:
                logger.error(f"Notification kaydedilemedi: {e}")

    def on_state_change(self, callback: Callable) -> None:
        """
        State değişikliği callback'i ekler.

        Args:
            callback: Callback fonksiyonu
                     signature: (endpoint_key, old_state, new_state, reason)
        """
        self._on_state_change_callbacks.append(callback)

    async def should_allow_request(self, endpoint_key: str) -> bool:
        """
        İsteğin geçmesine izin verilip verilmeyeceğini belirler.

        Args:
            endpoint_key: Endpoint key

        Returns:
            True ise istek geçebilir, False ise reddedilmeli

        Requirements:
            REQ-4.2: OPEN durumda istekler reddedilir
        """
        state = await self.get_state(endpoint_key)

        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            # HALF_OPEN'da sadece bir test isteği kabul edilir
            # Gerçek implementasyonda bu kısım daha sofistike olabilir
            return True
        # OPEN
        return False

    async def get_all_states(self) -> dict[str, CircuitState]:
        """
        Tüm endpoint'lerin circuit durumlarını getirir.

        Returns:
            Endpoint key -> CircuitState dict'i
        """
        # In-memory states'i döndür
        # Redis'ten senkronize etmek için ayrı bir job gerekebilir
        return self.states.copy()

    async def reset(self, endpoint_key: str) -> None:
        """
        Endpoint'in circuit state'ini sıfırlar (CLOSED'a geçirir).

        Bu method manuel müdahale için kullanılır.

        Args:
            endpoint_key: Endpoint key
        """
        logger.info(f"Circuit manuel olarak sıfırlanıyor: {endpoint_key}")

        await self._transition_to(
            endpoint_key,
            CircuitState.CLOSED,
            "Manual reset by operator"
        )

    async def reset_all(self) -> None:
        """
        Tüm circuit'leri sıfırlar.

        Bu method dikkatli kullanılmalıdır.
        """
        logger.warning("Tüm circuit'ler sıfırlanıyor!")

        for endpoint_key in list(self.states.keys()):
            await self.reset(endpoint_key)
