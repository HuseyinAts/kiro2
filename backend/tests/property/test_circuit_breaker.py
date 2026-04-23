"""
Property-Based Tests - Circuit Breaker

Bu modül, hypothesis kullanarak circuit breaker için
property-based testler içerir.

Property 2: Circuit Breaker State Transition - 5 failure → OPEN state
"""

import sys

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from app.health.circuit_breaker import CircuitBreaker
from app.health.models import CircuitState


class TestCircuitBreakerProperties:
    """Circuit breaker property-based testleri."""

    def setup_method(self):
        """Test setup."""
        self.breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30
        )

    @pytest.mark.asyncio
    @given(
        failure_count=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=50)
    async def test_circuit_opens_after_threshold_failures(
        self,
        failure_count: int
    ):
        """
        Property 2: 5 ardışık failure sonrası circuit OPEN olmalı.

        REQ-4.1: 5 ardışık hata sonrası circuit OPEN
        """
        endpoint = f"/api/v1/test_{failure_count}"

        # Threshold kadar failure kaydet
        for i in range(failure_count):
            await self.breaker.record_failure(endpoint, f"Error {i}")

        state = await self.breaker.get_state(endpoint)

        # 5+ failure sonrası OPEN olmalı
        assert state == CircuitState.OPEN, \
            f"Circuit should be OPEN after {failure_count} failures, got {state}"

    @pytest.mark.asyncio
    @given(
        failure_count=st.integers(min_value=1, max_value=4)
    )
    @settings(max_examples=20)
    async def test_circuit_stays_closed_below_threshold(
        self,
        failure_count: int
    ):
        """
        Property: Threshold altında failure ile circuit CLOSED kalmalı.
        """
        endpoint = f"/api/v1/test_closed_{failure_count}"

        # Threshold'un altında failure kaydet
        for i in range(failure_count):
            await self.breaker.record_failure(endpoint, f"Error {i}")

        state = await self.breaker.get_state(endpoint)

        # Threshold altında CLOSED kalmalı
        assert state == CircuitState.CLOSED, \
            f"Circuit should be CLOSED with {failure_count} failures, got {state}"

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        """
        Property: Başarılı istek failure sayacını sıfırlamalı.
        """
        endpoint = "/api/v1/test_reset"

        # 3 failure kaydet
        for i in range(3):
            await self.breaker.record_failure(endpoint)

        # Başarılı istek
        await self.breaker.record_success(endpoint)

        # Tekrar 3 failure - toplam 3, threshold 5
        for i in range(3):
            await self.breaker.record_failure(endpoint)

        state = await self.breaker.get_state(endpoint)

        # Hala CLOSED olmalı (3 failure, reset sonrası)
        assert state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self):
        """
        Property: HALF_OPEN durumda success circuit'i kapatmalı.

        REQ-4.4: HALF_OPEN durumda test başarılı -> CLOSED
        """
        endpoint = "/api/v1/test_halfopen"

        # Circuit'i aç
        for i in range(5):
            await self.breaker.record_failure(endpoint)

        # Manuel olarak HALF_OPEN'a geç
        await self.breaker._transition_to(
            endpoint,
            CircuitState.HALF_OPEN,
            "Test transition"
        )

        # Başarılı istek
        await self.breaker.record_success(endpoint)

        state = await self.breaker.get_state(endpoint)

        # CLOSED olmalı
        assert state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_opens_circuit(self):
        """
        Property: HALF_OPEN durumda failure circuit'i tekrar açmalı.

        REQ-4.5: HALF_OPEN durumda hata -> OPEN
        """
        endpoint = "/api/v1/test_halfopen_fail"

        # Circuit'i aç
        for i in range(5):
            await self.breaker.record_failure(endpoint)

        # Manuel olarak HALF_OPEN'a geç
        await self.breaker._transition_to(
            endpoint,
            CircuitState.HALF_OPEN,
            "Test transition"
        )

        # Başarısız istek
        await self.breaker.record_failure(endpoint)

        state = await self.breaker.get_state(endpoint)

        # OPEN olmalı
        assert state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_requests(self):
        """
        Property: OPEN circuit istekleri reddetmeli.

        REQ-4.2: OPEN durumda istekler reddedilir
        """
        endpoint = "/api/v1/test_reject"

        # Circuit'i aç
        for i in range(5):
            await self.breaker.record_failure(endpoint)

        allowed = await self.breaker.should_allow_request(endpoint)

        # Reddedilmeli
        assert allowed is False

    @pytest.mark.asyncio
    async def test_closed_circuit_allows_requests(self):
        """
        Property: CLOSED circuit isteklere izin vermeli.
        """
        endpoint = "/api/v1/test_allow"

        allowed = await self.breaker.should_allow_request(endpoint)

        # İzin verilmeli
        assert allowed is True

    @pytest.mark.asyncio
    async def test_reset_closes_circuit(self):
        """
        Property: Manuel reset circuit'i kapatmalı.
        """
        endpoint = "/api/v1/test_manual_reset"

        # Circuit'i aç
        for i in range(5):
            await self.breaker.record_failure(endpoint)

        state = await self.breaker.get_state(endpoint)
        assert state == CircuitState.OPEN

        # Manuel reset
        await self.breaker.reset(endpoint)

        state = await self.breaker.get_state(endpoint)
        assert state == CircuitState.CLOSED

    @pytest.mark.asyncio
    @given(
        endpoint_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20)
    async def test_independent_circuit_states(self, endpoint_count: int):
        """
        Property: Her endpoint bağımsız circuit state'e sahip olmalı.
        """
        endpoints = [f"/api/v1/endpoint_{i}" for i in range(endpoint_count)]

        # Sadece ilk endpoint'i aç
        for i in range(5):
            await self.breaker.record_failure(endpoints[0])

        # İlk endpoint OPEN, diğerleri CLOSED
        for i, endpoint in enumerate(endpoints):
            state = await self.breaker.get_state(endpoint)
            if i == 0:
                assert state == CircuitState.OPEN
            else:
                assert state == CircuitState.CLOSED
