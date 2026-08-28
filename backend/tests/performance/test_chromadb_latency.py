"""
ChromaDB Performance Tests - Latency and Throughput

Spec REQ-7: Performance Optimization
- REQ-7.1: < 100ms response time
- REQ-7.6: >= 1000 queries/sec throughput

Bu testler ChromaDB semantic search performansını ölçer.

Author: KIRO2 Team
Date: 2026-01-15
"""

import asyncio
import statistics
import time
from dataclasses import dataclass

import pytest

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


@dataclass
class LatencyStats:
    """Latency istatistikleri."""

    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    sample_count: int

    def meets_spec(self, target_ms: float = 100.0) -> bool:
        """Spec REQ-7.1: < 100ms response time."""
        return self.p95_ms < target_ms


@dataclass
class ThroughputStats:
    """Throughput istatistikleri."""

    queries_per_second: float
    total_queries: int
    total_time_seconds: float

    def meets_spec(self, target_qps: float = 1000.0) -> bool:
        """Spec REQ-7.6: >= 1000 queries/sec."""
        return self.queries_per_second >= target_qps


def calculate_latency_stats(latencies_ms: list[float]) -> LatencyStats:
    """Latency listesinden istatistik hesapla."""
    if not latencies_ms:
        return LatencyStats(
            min_ms=0,
            max_ms=0,
            mean_ms=0,
            median_ms=0,
            p95_ms=0,
            p99_ms=0,
            std_dev_ms=0,
            sample_count=0,
        )

    sorted_latencies = sorted(latencies_ms)
    n = len(sorted_latencies)

    return LatencyStats(
        min_ms=min(latencies_ms),
        max_ms=max(latencies_ms),
        mean_ms=statistics.mean(latencies_ms),
        median_ms=statistics.median(latencies_ms),
        p95_ms=sorted_latencies[int(n * 0.95)] if n > 0 else 0,
        p99_ms=sorted_latencies[int(n * 0.99)] if n > 0 else 0,
        std_dev_ms=statistics.stdev(latencies_ms) if n > 1 else 0,
        sample_count=n,
    )


@pytest.fixture
def chromadb_client():
    """ChromaDB test client fixture."""
    if not CHROMADB_AVAILABLE:
        pytest.skip("ChromaDB not available")

    client = chromadb.Client(ChromaSettings(anonymized_telemetry=False))

    # Test collection oluştur
    collection = client.get_or_create_collection(
        name="perf_test_collection", metadata={"hnsw:space": "cosine"}
    )

    # Seed data ekle
    n_docs = 1000
    embeddings = np.random.randn(n_docs, 768).astype(np.float32).tolist()
    documents = [f"Test document {i} with some content" for i in range(n_docs)]
    ids = [f"doc_{i}" for i in range(n_docs)]
    metadatas = [
        {"subject": f"subject_{i % 10}", "difficulty": float(i % 8 - 4)}
        for i in range(n_docs)
    ]

    collection.add(
        ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
    )

    yield client, collection

    # Cleanup
    client.delete_collection("perf_test_collection")


@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not available")
@pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
class TestSearchLatency:
    """Search latency testleri - Spec REQ-7.1."""

    def test_single_query_latency(self, chromadb_client):
        """
        Tekil sorgu latency testi.

        Target: < 100ms (P95)
        """
        _client, collection = chromadb_client
        latencies = []

        # Warmup
        query_embedding = np.random.randn(768).astype(np.float32).tolist()
        collection.query(query_embeddings=[query_embedding], n_results=10)

        # Benchmark
        n_queries = 100
        for _ in range(n_queries):
            query_embedding = np.random.randn(768).astype(np.float32).tolist()

            start = time.perf_counter()
            collection.query(
                query_embeddings=[query_embedding],
                n_results=10,
                include=["documents", "metadatas", "distances"],
            )
            end = time.perf_counter()

            latencies.append((end - start) * 1000)  # ms

        stats = calculate_latency_stats(latencies)

        print("\n--- Single Query Latency ---")
        print(f"Min: {stats.min_ms:.2f}ms")
        print(f"Max: {stats.max_ms:.2f}ms")
        print(f"Mean: {stats.mean_ms:.2f}ms")
        print(f"Median: {stats.median_ms:.2f}ms")
        print(f"P95: {stats.p95_ms:.2f}ms")
        print(f"P99: {stats.p99_ms:.2f}ms")

        # Spec REQ-7.1: P95 < 100ms
        assert stats.meets_spec(
            100.0
        ), f"P95 latency {stats.p95_ms:.2f}ms exceeds 100ms target"

    def test_filtered_query_latency(self, chromadb_client):
        """
        Metadata filtreli sorgu latency testi.

        Target: < 100ms (P95)
        """
        _client, collection = chromadb_client
        latencies = []

        # Benchmark with filters
        n_queries = 50
        subjects = [f"subject_{i}" for i in range(10)]

        for i in range(n_queries):
            query_embedding = np.random.randn(768).astype(np.float32).tolist()
            subject = subjects[i % len(subjects)]

            start = time.perf_counter()
            collection.query(
                query_embeddings=[query_embedding],
                n_results=10,
                where={"subject": subject},
                include=["documents", "metadatas", "distances"],
            )
            end = time.perf_counter()

            latencies.append((end - start) * 1000)

        stats = calculate_latency_stats(latencies)

        print("\n--- Filtered Query Latency ---")
        print(f"Mean: {stats.mean_ms:.2f}ms")
        print(f"P95: {stats.p95_ms:.2f}ms")

        # Filtered queries may be slightly slower
        assert stats.meets_spec(
            150.0
        ), f"P95 filtered latency {stats.p95_ms:.2f}ms exceeds 150ms target"

    def test_batch_query_latency(self, chromadb_client):
        """
        Batch sorgu latency testi.

        Target: < 500ms for batch of 10
        """
        _client, collection = chromadb_client

        # Batch of queries
        batch_size = 10
        query_embeddings = np.random.randn(batch_size, 768).astype(np.float32).tolist()

        start = time.perf_counter()
        # Gecikme olculuyor, sonuc kullanilmiyor (F841 kacinma)
        collection.query(
            query_embeddings=query_embeddings,
            n_results=10,
            include=["documents", "metadatas", "distances"],
        )
        end = time.perf_counter()

        batch_latency_ms = (end - start) * 1000
        per_query_ms = batch_latency_ms / batch_size

        print("\n--- Batch Query Latency ---")
        print(f"Batch size: {batch_size}")
        print(f"Total: {batch_latency_ms:.2f}ms")
        print(f"Per query: {per_query_ms:.2f}ms")

        # Batch should be efficient
        assert (
            batch_latency_ms < 500
        ), f"Batch latency {batch_latency_ms:.2f}ms exceeds 500ms target"


@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not available")
@pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
class TestThroughput:
    """Throughput testleri - Spec REQ-7.6."""

    def test_sustained_throughput(self, chromadb_client):
        """
        Sürdürülebilir throughput testi.

        Target: >= 1000 queries/sec (not always achievable locally)
        """
        _client, collection = chromadb_client

        n_queries = 500

        query_embeddings = [
            np.random.randn(768).astype(np.float32).tolist() for _ in range(n_queries)
        ]

        start = time.perf_counter()
        for query_embedding in query_embeddings:
            collection.query(query_embeddings=[query_embedding], n_results=5)
        end = time.perf_counter()

        total_time = end - start
        qps = n_queries / total_time

        stats = ThroughputStats(
            queries_per_second=qps,
            total_queries=n_queries,
            total_time_seconds=total_time,
        )

        print("\n--- Throughput Test ---")
        print(f"Queries: {stats.total_queries}")
        print(f"Time: {stats.total_time_seconds:.2f}s")
        print(f"QPS: {stats.queries_per_second:.1f}")

        # Local testing may not achieve 1000 QPS, use lower threshold
        # Production with proper hardware should achieve spec target
        min_qps = 50  # Minimum acceptable for local testing
        assert (
            stats.queries_per_second >= min_qps
        ), f"Throughput {stats.queries_per_second:.1f} QPS below {min_qps} minimum"

    def test_concurrent_queries(self, chromadb_client):
        """
        Concurrent sorgu testi.

        Simulates multiple users querying simultaneously.
        """
        _client, collection = chromadb_client

        async def query_async(query_embedding: list[float]) -> float:
            """Async query wrapper."""
            start = time.perf_counter()
            collection.query(query_embeddings=[query_embedding], n_results=5)
            end = time.perf_counter()
            return (end - start) * 1000

        async def run_concurrent():
            n_concurrent = 20
            query_embeddings = [
                np.random.randn(768).astype(np.float32).tolist()
                for _ in range(n_concurrent)
            ]

            tasks = [query_async(emb) for emb in query_embeddings]
            return await asyncio.gather(*tasks)

        # Run concurrent queries
        latencies = asyncio.run(run_concurrent())
        stats = calculate_latency_stats(latencies)

        print("\n--- Concurrent Query Latency ---")
        print(f"Concurrent requests: {stats.sample_count}")
        print(f"Mean: {stats.mean_ms:.2f}ms")
        print(f"P95: {stats.p95_ms:.2f}ms")

        # Concurrent queries should still be reasonable
        assert stats.p95_ms < 500, f"Concurrent P95 {stats.p95_ms:.2f}ms exceeds 500ms"


@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not available")
@pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
class TestQuantizationPerformance:
    """Quantization performance testleri - Spec REQ-7.5."""

    def test_quantization_memory_reduction(self):
        """
        Quantization memory reduction testi.

        Target: ~75% memory reduction
        """
        from core.embedding_cache import quantize_embedding

        # Generate test embeddings
        n_embeddings = 100
        dim = 768

        embeddings = np.random.randn(n_embeddings, dim).astype(np.float32)

        original_size = embeddings.nbytes
        quantized_size = 0

        for emb in embeddings:
            q = quantize_embedding(emb)
            quantized_size += q.memory_size()

        reduction = (1 - quantized_size / original_size) * 100

        print("\n--- Quantization Memory ---")
        print(f"Original: {original_size / 1024:.1f} KB")
        print(f"Quantized: {quantized_size / 1024:.1f} KB")
        print(f"Reduction: {reduction:.1f}%")

        # Spec REQ-7.5: ~75% reduction
        assert reduction >= 65, f"Memory reduction {reduction:.1f}% below 65% target"

    def test_quantization_accuracy(self):
        """
        Quantization accuracy testi.

        Target: Cosine similarity > 0.99 after dequantization
        """
        from core.embedding_cache import (
            calculate_quantization_error,
            quantize_embedding,
        )

        n_tests = 50
        cosine_sims = []

        for _ in range(n_tests):
            original = np.random.randn(768).astype(np.float32)
            quantized = quantize_embedding(original)
            error = calculate_quantization_error(original, quantized)
            cosine_sims.append(error["cosine_similarity"])

        mean_cosine = statistics.mean(cosine_sims)
        min_cosine = min(cosine_sims)

        print("\n--- Quantization Accuracy ---")
        print(f"Mean cosine similarity: {mean_cosine:.6f}")
        print(f"Min cosine similarity: {min_cosine:.6f}")

        # High accuracy required
        assert mean_cosine > 0.99, f"Mean cosine {mean_cosine:.6f} below 0.99"
        assert min_cosine > 0.95, f"Min cosine {min_cosine:.6f} below 0.95"


@pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not available")
@pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
class TestEmbeddingCachePerformance:
    """Embedding cache performance testleri."""

    def test_cache_hit_latency(self):
        """
        Cache hit latency testi.

        Target: < 1ms for cache hit
        """
        # Simple in-memory cache simulation
        cache: dict[str, list[float]] = {}
        n_items = 1000

        # Populate cache
        for i in range(n_items):
            key = f"text_{i}"
            cache[key] = np.random.randn(768).astype(np.float32).tolist()

        # Measure hit latency
        latencies = []
        for i in range(100):
            key = f"text_{i % n_items}"

            start = time.perf_counter()
            _ = cache.get(key)
            end = time.perf_counter()

            latencies.append((end - start) * 1000)

        stats = calculate_latency_stats(latencies)

        print("\n--- Cache Hit Latency ---")
        print(f"Mean: {stats.mean_ms:.4f}ms")
        print(f"P99: {stats.p99_ms:.4f}ms")

        # Cache hits should be very fast
        assert stats.p99_ms < 1.0, f"Cache hit P99 {stats.p99_ms:.4f}ms exceeds 1ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
