"""
Circuit Breaker Pattern Implementation
Learning Path Video Yükleme Sorunu için servis koruma mekanizması

Requirements: 5.18, 4.11
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker durumları"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker konfigürasyonu"""

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: int = 60
    half_open_max_calls: int = 3
    excluded_exceptions: tuple = ()


@dataclass
class CircuitBreakerStats:
    """Circuit breaker istatistikleri"""

    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    last_success_time: Optional[datetime]
    opened_at: Optional[datetime]
    total_calls: int
    total_failures: int
    total_successes: int
    half_open_attempts: int

    def to_dict(self) -> Dict[str, Any]:
        """İstatistikleri dictionary'ye çevir"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat()
            if self.last_failure_time
            else None,
            "last_success_time": self.last_success_time.isoformat()
            if self.last_success_time
            else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "half_open_attempts": self.half_open_attempts,
            "success_rate": self._calculate_success_rate(),
        }

    def _calculate_success_rate(self) -> float:
        """Başarı oranını hesapla"""
        if self.total_calls == 0:
            return 0.0
        return (self.total_successes / self.total_calls) * 100


class CircuitBreakerError(Exception):
    """Circuit breaker base exception"""

    def __init__(
        self,
        message: str,
        circuit_name: str,
        state: CircuitState,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message)
        self.message = message
        self.circuit_name = circuit_name
        self.state = state
        self.retry_after = retry_after
        self.timestamp = datetime.now()


class CircuitBreakerOpenError(CircuitBreakerError):
    """Circuit breaker açık durumda - istekler reddediliyor"""

    def __init__(
        self, circuit_name: str, retry_after: int = 60, message: Optional[str] = None
    ):
        message = message or f"Circuit breaker '{circuit_name}' is OPEN"
        super().__init__(
            message=message,
            circuit_name=circuit_name,
            state=CircuitState.OPEN,
            retry_after=retry_after,
        )


class CircuitBreakerHalfOpenError(CircuitBreakerError):
    """Circuit breaker half-open durumda - maksimum istek sayısına ulaşıldı"""

    def __init__(
        self, circuit_name: str, max_calls: int, message: Optional[str] = None
    ):
        message = (
            message
            or f"Circuit breaker '{circuit_name}' is HALF_OPEN - max calls reached"
        )
        super().__init__(
            message=message,
            circuit_name=circuit_name,
            state=CircuitState.HALF_OPEN,
            retry_after=5,
        )


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation

    Servis başarısızlıklarını izler ve cascading failure'ları önler.

    Requirements: 5.18, 4.11
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Circuit breaker oluştur"""
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.logger = logger or logging.getLogger(__name__)

        # State management
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._last_success_time: Optional[datetime] = None
        self._opened_at: Optional[datetime] = None
        self._half_open_calls = 0

        # Statistics
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0

        self.logger.info(f"Circuit breaker '{self.name}' initialized")

    @property
    def state(self) -> CircuitState:
        """Mevcut circuit durumunu al"""
        self._check_timeout()
        return self._state

    def _check_timeout(self) -> None:
        """Timeout kontrolü yap ve gerekirse HALF_OPEN'a geç"""
        if self._state == CircuitState.OPEN and self._opened_at:
            elapsed = (datetime.now() - self._opened_at).total_seconds()
            if elapsed >= self.config.timeout:
                self._transition_to_half_open()

    def _transition_to_half_open(self) -> None:
        """HALF_OPEN durumuna geç"""
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._success_count = 0
        self.logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")

    def _transition_to_open(self) -> None:
        """OPEN durumuna geç"""
        self._state = CircuitState.OPEN
        self._opened_at = datetime.now()
        self._half_open_calls = 0
        self._success_count = 0
        self.logger.error(
            f"Circuit breaker '{self.name}' OPENED after {self._failure_count} failures"
        )

    def _transition_to_closed(self) -> None:
        """CLOSED durumuna geç"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = None
        self._half_open_calls = 0
        self.logger.info(f"Circuit breaker '{self.name}' CLOSED - service recovered")

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Fonksiyonu circuit breaker koruması ile çalıştır

        Args:
            func: Çalıştırılacak async fonksiyon
            *args: Fonksiyon argümanları
            **kwargs: Fonksiyon keyword argümanları

        Returns:
            Fonksiyon sonucu

        Raises:
            CircuitBreakerOpenError: Circuit açık durumda
            CircuitBreakerHalfOpenError: Half-open durumda maksimum istek sayısına ulaşıldı
        """
        self._total_calls += 1

        # Circuit durumunu kontrol et
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                circuit_name=self.name, retry_after=self.config.timeout
            )

        if current_state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self.config.half_open_max_calls:
                raise CircuitBreakerHalfOpenError(
                    circuit_name=self.name, max_calls=self.config.half_open_max_calls
                )
            self._half_open_calls += 1

        # Fonksiyonu çalıştır
        try:
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            self._on_success(execution_time)
            return result

        except Exception as e:
            # Excluded exception'ları kontrol et
            if isinstance(e, self.config.excluded_exceptions):
                raise

            self._on_failure(e)
            raise

    def _on_success(self, execution_time_ms: float) -> None:
        """Başarılı çağrı sonrası işlemler"""
        self._total_successes += 1
        self._last_success_time = datetime.now()

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self._state == CircuitState.CLOSED:
            if self._failure_count > 0:
                self._failure_count = 0

    def _on_failure(self, exception: Exception) -> None:
        """Başarısız çağrı sonrası işlemler"""
        self._total_failures += 1
        self._last_failure_time = datetime.now()
        self._failure_count += 1

        if self._state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.config.failure_threshold:
                self._transition_to_open()

    def protect(self, func: Callable) -> Callable:
        """Decorator: Fonksiyonu circuit breaker ile koru"""

        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await self.call(func, *args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    def get_stats(self) -> CircuitBreakerStats:
        """Circuit breaker istatistiklerini al"""
        return CircuitBreakerStats(
            state=self.state,
            failure_count=self._failure_count,
            success_count=self._success_count,
            last_failure_time=self._last_failure_time,
            last_success_time=self._last_success_time,
            opened_at=self._opened_at,
            total_calls=self._total_calls,
            total_failures=self._total_failures,
            total_successes=self._total_successes,
            half_open_attempts=self._half_open_calls,
        )

    def reset(self) -> None:
        """Circuit breaker'ı başlangıç durumuna sıfırla"""
        self._transition_to_closed()
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        self._last_failure_time = None
        self._last_success_time = None
        self.logger.info(f"Circuit breaker '{self.name}' reset")

    def force_open(self) -> None:
        """Circuit'i zorla aç (maintenance mode için)"""
        self.logger.warning(f"Circuit breaker '{self.name}' forced OPEN")
        self._transition_to_open()

    def force_close(self) -> None:
        """Circuit'i zorla kapat (recovery sonrası)"""
        self.logger.info(f"Circuit breaker '{self.name}' forced CLOSED")
        self._transition_to_closed()


class CircuitBreakerManager:
    """
    Birden fazla circuit breaker'ı yönet

    Merkezi yönetim ve monitoring için kullanılır.
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self.logger = logging.getLogger(__name__)

    def register(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Yeni circuit breaker kaydet

        Args:
            name: Circuit breaker adı
            config: Konfigürasyon

        Returns:
            CircuitBreaker instance
        """
        if name in self._breakers:
            self.logger.warning(f"Circuit breaker '{name}' already registered")
            return self._breakers[name]

        breaker = CircuitBreaker(name=name, config=config, logger=self.logger)
        self._breakers[name] = breaker

        self.logger.info(f"Circuit breaker '{name}' registered")
        return breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Circuit breaker al"""
        return self._breakers.get(name)

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Tüm circuit breaker'ların istatistiklerini al"""
        return {
            name: breaker.get_stats().to_dict()
            for name, breaker in self._breakers.items()
        }

    def reset_all(self) -> None:
        """Tüm circuit breaker'ları sıfırla"""
        for breaker in self._breakers.values():
            breaker.reset()
        self.logger.info("All circuit breakers reset")


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()
