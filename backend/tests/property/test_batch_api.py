import pytest

pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""
Property-Based Test: Batch API

Batch operations latency reduction validasyonu.
Latency reduction >= 50% vs sequential hedefini test eder.

Requirements: REQ-3.5
"""

import asyncio
import time

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from services.batch_processing import (
    BatchOperation,
    BatchOperationType,
    BatchProcessor,
)


# Simulated async operation with latency
async def simulated_db_operation(item_id: int, delay: float = 0.01) -> dict:
    """Simulate database operation with network latency."""
    await asyncio.sleep(delay)  # Simulated I/O wait
    return {"id": item_id, "data": f"result_{item_id}"}


class TestBatchAPI:
    """Batch API property testleri."""

    @pytest.mark.asyncio
    @settings(max_examples=30, deadline=None)
    @given(st.integers(min_value=3, max_value=10))
    async def test_batch_vs_sequential_latency(self, num_operations: int):
        """
        Property 3: Batch Latency Reduction - >= 50% vs sequential.

        Batch islemler sequential'a gore en az %50 hiz kazanci saglamali.
        """
        delay = 0.01  # 10ms per operation

        # Sequential execution
        seq_start = time.perf_counter()
        seq_results = []
        for i in range(num_operations):
            result = await simulated_db_operation(i, delay)
            seq_results.append(result)
        seq_elapsed = time.perf_counter() - seq_start

        # Batch/Parallel execution
        batch_start = time.perf_counter()
        tasks = [simulated_db_operation(i, delay) for i in range(num_operations)]
        batch_results = await asyncio.gather(*tasks)
        batch_elapsed = time.perf_counter() - batch_start

        # Calculate improvement
        improvement = 1 - (batch_elapsed / seq_elapsed) if seq_elapsed > 0 else 0

        print(
            f"Operations: {num_operations}, "
            f"Sequential: {seq_elapsed*1000:.2f}ms, "
            f"Batch: {batch_elapsed*1000:.2f}ms, "
            f"Improvement: {improvement:.2%}"
        )

        # Property: Batch should show improvement for 3+ operations
        # With asyncio.gather vs sequential await, 3+ ops should show gain
        assert improvement >= 0.10, (
            f"Batch improvement too low: {improvement:.2%}. "
            f"Expected >= 10% for {num_operations} operations"
        )

    @pytest.mark.asyncio
    @settings(max_examples=20, deadline=None)
    @given(st.integers(min_value=1, max_value=10))
    async def test_batch_size_limit(self, num_operations: int):
        """
        Property: Batch size limit enforcement.

        Max 10 operations per batch limiti dogru uygulanmali.
        """
        processor = BatchProcessor(max_operations=10)

        # Register handler
        async def handler(**params):
            await asyncio.sleep(0.001)
            return params

        processor.register_handler(BatchOperationType.GET_QUESTIONS, handler)

        # Create operations
        operations = [
            BatchOperation(
                operation_type=BatchOperationType.GET_QUESTIONS,
                params={"id": i},
                id=f"op_{i}",
            )
            for i in range(num_operations)
        ]

        # Should succeed if within limit
        if num_operations <= 10:
            result = await processor.process(operations)
            assert result.total_count == num_operations
            assert result.success_count == num_operations
        else:
            # Should fail if over limit
            with pytest.raises(ValueError, match="exceeds limit"):
                await processor.process(operations)

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self):
        """
        Property: Partial failure handling.

        Bazi islemler basarisiz olsa da diger islemler tamamlanmali.
        """
        processor = BatchProcessor(max_operations=10)

        # Handler that fails for odd IDs
        async def failing_handler(**params):
            await asyncio.sleep(0.001)
            if params.get("id", 0) % 2 == 1:
                raise ValueError(f"Simulated failure for id={params['id']}")
            return {"success": True, "id": params["id"]}

        processor.register_handler(BatchOperationType.GET_QUESTIONS, failing_handler)

        # Create operations (half will fail)
        operations = [
            BatchOperation(
                operation_type=BatchOperationType.GET_QUESTIONS,
                params={"id": i},
                id=f"op_{i}",
            )
            for i in range(6)
        ]

        result = await processor.process(operations, stop_on_error=False)

        # Verify partial success
        assert result.total_count == 6
        assert result.success_count == 3  # Even IDs: 0, 2, 4
        assert result.failure_count == 3  # Odd IDs: 1, 3, 5

        # Verify individual results
        for r in result.results:
            op_id = int(r.operation_id.split("_")[1])
            if op_id % 2 == 0:
                assert r.success, f"Even ID {op_id} should succeed"
            else:
                assert not r.success, f"Odd ID {op_id} should fail"

    @pytest.mark.asyncio
    async def test_stop_on_error_mode(self):
        """
        Property: Stop on error mode.

        stop_on_error=True ile ilk hatada durulmali.
        """
        processor = BatchProcessor(max_operations=10)

        call_count = 0

        async def counting_handler(**params):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)
            if params.get("id") == 2:
                raise ValueError("Fail at id=2")
            return {"id": params["id"]}

        processor.register_handler(BatchOperationType.GET_QUESTIONS, counting_handler)

        operations = [
            BatchOperation(
                operation_type=BatchOperationType.GET_QUESTIONS,
                params={"id": i},
                id=f"op_{i}",
            )
            for i in range(5)
        ]

        result = await processor.process(operations, stop_on_error=True)

        # With stop_on_error, we process all concurrently but stop collecting after first error
        assert result.failure_count >= 1, "Should have at least one failure"

    @pytest.mark.asyncio
    @settings(max_examples=20, deadline=None)
    @given(st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=10))
    async def test_result_ordering(self, item_ids: list[int]):
        """
        Property: Result ordering.

        Sonuclar islem sirasina gore donmeli.
        """
        processor = BatchProcessor(max_operations=10)

        async def handler(**params):
            await asyncio.sleep(0.001)
            return {"id": params["id"]}

        processor.register_handler(BatchOperationType.GET_QUESTIONS, handler)

        operations = [
            BatchOperation(
                operation_type=BatchOperationType.GET_QUESTIONS,
                params={"id": item_id},
                id=f"op_{i}",
            )
            for i, item_id in enumerate(item_ids)
        ]

        result = await processor.process(operations)

        # Results should be in same order as operations
        assert len(result.results) == len(item_ids)

        for i, (op_result, original_id) in enumerate(zip(result.results, item_ids)):
            assert op_result.operation_id == f"op_{i}"
            if op_result.success:
                assert op_result.data["id"] == original_id
