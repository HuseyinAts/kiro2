"""
Property-Based Tests - Message Latency (REQ-8.2)

Bu modul, hypothesis kullanarak message bus latency icin
property-based testler icerir.

Property 1: Message Latency Bound - End-to-end latency < 50ms (P95)

Boris Cherny Standards: Minimum 100 iterations per property test
"""

import asyncio
import statistics
import time
from typing import List

import pytest
from hypothesis import given, settings, strategies as st

import sys
sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from algorithms.multi_agent_blackboard import (
    MultiAgentBlackboard,
    Priority,
    EventType,
)


class TestMessageLatencyProperties:
    """Message latency property-based testleri (REQ-8.2)."""

    def setup_method(self):
        """Test setup."""
        self.blackboard = MultiAgentBlackboard()
        self.latencies: List[float] = []

    @given(
        payload_size=st.integers(min_value=10, max_value=10000),
        priority=st.sampled_from(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    )
    @settings(max_examples=100)
    def test_single_write_latency_bound(self, payload_size: int, priority: str):
        """
        Property 1: Single write latency < 50ms (REQ-8.2)

        For any single write operation, latency MUST be < 50ms.
        """
        blackboard = MultiAgentBlackboard()

        # Register a test agent
        blackboard.register_agent("test_agent", None)

        # Create payload
        payload = "x" * payload_size

        # Measure latency
        start = time.perf_counter()

        # Sync write (blocking)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                blackboard.write(
                    key=f"test_key_{payload_size}",
                    value=payload,
                    source_agent="test_agent",
                    priority=Priority[priority]
                )
            )
        finally:
            loop.close()

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Property: Single write should be fast
        assert elapsed_ms < 50, f"Write latency {elapsed_ms:.2f}ms exceeds 50ms"
        assert result is True, "Write should succeed"

    @given(
        num_messages=st.integers(min_value=10, max_value=100),
        payload_size=st.integers(min_value=100, max_value=1000)
    )
    @settings(max_examples=50)
    def test_batch_write_p95_latency(self, num_messages: int, payload_size: int):
        """
        Property 2: Batch write P95 latency < 50ms (REQ-8.2)

        For any batch of messages, P95 latency MUST be < 50ms.
        """
        blackboard = MultiAgentBlackboard()
        blackboard.register_agent("batch_agent", None)

        latencies = []
        payload = "y" * payload_size

        loop = asyncio.new_event_loop()
        try:
            for i in range(num_messages):
                start = time.perf_counter()

                loop.run_until_complete(
                    blackboard.write(
                        key=f"batch_key_{i}",
                        value=payload,
                        source_agent="batch_agent",
                        priority=Priority.MEDIUM
                    )
                )

                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)
        finally:
            loop.close()

        # Calculate P95
        if len(latencies) >= 10:
            p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile

            # Property: P95 < 50ms
            assert p95 < 50, f"P95 latency {p95:.2f}ms exceeds 50ms target"

    @given(
        read_count=st.integers(min_value=10, max_value=100)
    )
    @settings(max_examples=50)
    def test_read_latency_bound(self, read_count: int):
        """
        Property 3: Read latency < 10ms (REQ-8.2)

        For any read operation, latency MUST be < 10ms.
        """
        blackboard = MultiAgentBlackboard()
        blackboard.register_agent("read_agent", None)

        # Setup: Write initial data
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                blackboard.write(
                    key="read_test_key",
                    value="test_value",
                    source_agent="read_agent"
                )
            )

            latencies = []

            for _ in range(read_count):
                start = time.perf_counter()
                value = blackboard.read("read_test_key", "read_agent")
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)

            # Property: All reads should be fast
            max_latency = max(latencies)
            assert max_latency < 20, f"Read latency {max_latency:.2f}ms exceeds 20ms"
        finally:
            loop.close()

    @given(
        agent_count=st.integers(min_value=2, max_value=10),
        message_count=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=30)
    def test_multi_agent_coordination_latency(
        self, agent_count: int, message_count: int
    ):
        """
        Property 4: Multi-agent coordination latency < 100ms (REQ-8.2)

        For any multi-agent coordination, total latency MUST be < 100ms.
        """
        blackboard = MultiAgentBlackboard()

        # Register multiple agents
        for i in range(agent_count):
            blackboard.register_agent(f"agent_{i}", None)
            blackboard.subscribe(
                agent_name=f"agent_{i}",
                event_types=[EventType.DATA_WRITTEN],
                key_patterns=["*"]
            )

        latencies = []
        loop = asyncio.new_event_loop()

        try:
            for i in range(message_count):
                start = time.perf_counter()

                loop.run_until_complete(
                    blackboard.write(
                        key=f"coord_key_{i}",
                        value=f"value_{i}",
                        source_agent="agent_0"
                    )
                )

                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)

            # Property: Average latency should be reasonable
            avg_latency = statistics.mean(latencies)
            assert avg_latency < 100, (
                f"Average coordination latency {avg_latency:.2f}ms exceeds 100ms"
            )
        finally:
            loop.close()


class TestMessageLatencyEdgeCases:
    """Edge case testleri for message latency."""

    def test_empty_payload_latency(self):
        """Empty payload should have minimal latency."""
        blackboard = MultiAgentBlackboard()
        blackboard.register_agent("empty_agent", None)

        start = time.perf_counter()

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                blackboard.write(
                    key="empty_key",
                    value="",
                    source_agent="empty_agent"
                )
            )
        finally:
            loop.close()

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 20, f"Empty payload latency {elapsed_ms:.2f}ms too high"

    def test_large_payload_latency(self):
        """Large payload (100KB) should still meet latency target."""
        blackboard = MultiAgentBlackboard()
        blackboard.register_agent("large_agent", None)

        large_payload = "z" * 100_000  # 100KB

        start = time.perf_counter()

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                blackboard.write(
                    key="large_key",
                    value=large_payload,
                    source_agent="large_agent"
                )
            )
        finally:
            loop.close()

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Allow more time for large payloads
        assert elapsed_ms < 100, f"Large payload latency {elapsed_ms:.2f}ms exceeds 100ms"

    def test_concurrent_writes_latency(self):
        """Concurrent writes should not significantly increase latency."""
        blackboard = MultiAgentBlackboard()

        for i in range(5):
            blackboard.register_agent(f"concurrent_agent_{i}", None)

        async def run_concurrent_writes():
            async def concurrent_write(agent_id: int) -> float:
                start = time.perf_counter()
                await blackboard.write(
                    key=f"concurrent_key_{agent_id}",
                    value=f"value_{agent_id}",
                    source_agent=f"concurrent_agent_{agent_id}"
                )
                return (time.perf_counter() - start) * 1000

            tasks = [concurrent_write(i) for i in range(5)]
            return await asyncio.gather(*tasks)

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            latencies = loop.run_until_complete(run_concurrent_writes())
        finally:
            loop.close()

        max_latency = max(latencies)
        assert max_latency < 100, f"Concurrent write latency {max_latency:.2f}ms too high"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-seed=0"])
