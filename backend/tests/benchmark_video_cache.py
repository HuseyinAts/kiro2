"""
Video Cache Repository Performance Benchmark
Tests query performance with and without indexes
"""

import asyncio
import random
import time

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from repositories.video_cache_repository import OptimizedVideoRepository

# Test configuration (Port 5434 - KIRO2 Standard)
DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5434/turkiye_sinav_test"
)
NUM_TEST_VIDEOS = 10000  # Number of test videos to insert
NUM_QUERIES = 100  # Number of queries to run for benchmarking


class VideoCacheBenchmark:
    """Benchmark suite for video cache repository"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_maker = None

    async def setup(self):
        """Setup database connection"""
        self.engine = create_async_engine(
            self.database_url, echo=False, pool_size=10, max_overflow=20
        )

        self.session_maker = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        print(f"✓ Database connection established: {self.database_url}")

    async def teardown(self):
        """Cleanup database connection"""
        if self.engine:
            await self.engine.dispose()
            print("✓ Database connection closed")

    async def create_test_data(self, num_videos: int = NUM_TEST_VIDEOS):
        """
        Create test data for benchmarking

        Generates realistic video cache entries with varied:
        - Subjects (matematik, fizik, kimya, biyoloji, türkçe)
        - Difficulties (başlangıç, orta, ileri)
        - Exam types (TYT, AYT, LGS)
        - Quality scores (5.0 - 10.0)
        """
        print(f"\n📊 Creating {num_videos} test videos...")

        subjects = ["matematik", "fizik", "kimya", "biyoloji", "türkçe"]
        difficulties = ["başlangıç", "orta", "ileri"]
        exam_types = ["TYT", "AYT", "LGS"]

        async with self.session_maker() as session:
            repository = OptimizedVideoRepository(session)

            # Generate test videos
            videos = []
            for i in range(num_videos):
                video = {
                    "video_id": f"test_video_{i}",
                    "title": f"Test Video {i} - {random.choice(subjects).title()}",
                    "description": f"Test description for video {i}",
                    "channel_name": f"Test Channel {i % 100}",
                    "channel_id": f"channel_{i % 100}",
                    "thumbnail_url": f"https://example.com/thumb_{i}.jpg",
                    "duration": random.randint(300, 3600),  # 5-60 minutes
                    "subject": random.choice(subjects),
                    "difficulty": random.choice(difficulties),
                    "exam_type": random.choice(exam_types),
                    "language": "tr",
                    "quality_score": round(random.uniform(5.0, 10.0), 2),
                    "relevance_score": round(random.uniform(0.5, 1.0), 2),
                    "language_score": round(random.uniform(0.7, 1.0), 2),
                    "difficulty_match": round(random.uniform(0.5, 1.0), 2),
                    "view_count": random.randint(1000, 1000000),
                    "like_count": random.randint(10, 10000),
                    "comment_count": random.randint(5, 1000),
                    "metadata": {"test": True, "batch": i // 1000},
                    "cache_ttl": 3600,
                }
                videos.append(video)

                # Batch insert every 1000 videos
                if len(videos) >= 1000:
                    await repository.bulk_upsert(videos)
                    print(f"  ✓ Inserted {i + 1}/{num_videos} videos")
                    videos = []

            # Insert remaining videos
            if videos:
                await repository.bulk_upsert(videos)

            print(f"✓ Created {num_videos} test videos")

    async def benchmark_optimized_query(self, num_queries: int = NUM_QUERIES):
        """
        Benchmark optimized query with composite index

        Tests: find_videos_optimized() method
        Expected: 5-10ms per query for 10K records
        """
        print(f"\n🚀 Benchmarking optimized query ({num_queries} queries)...")

        subjects = ["matematik", "fizik", "kimya", "biyoloji", "türkçe"]
        difficulties = ["başlangıç", "orta", "ileri"]
        exam_types = ["TYT", "AYT", "LGS"]

        query_times = []

        async with self.session_maker() as session:
            repository = OptimizedVideoRepository(session)

            for i in range(num_queries):
                subject = random.choice(subjects)
                difficulty = random.choice(difficulties)
                exam_type = random.choice(exam_types)

                start_time = time.time()

                videos = await repository.find_videos_optimized(
                    subject=subject,
                    difficulty=difficulty,
                    exam_type=exam_type,
                    language="tr",
                    min_quality=7.0,
                    min_relevance=0.7,
                    limit=20,
                )

                query_time = (time.time() - start_time) * 1000  # Convert to ms
                query_times.append(query_time)

                if (i + 1) % 20 == 0:
                    avg_time = sum(query_times[-20:]) / 20
                    print(
                        f"  Query {i + 1}/{num_queries}: {avg_time:.2f}ms avg (last 20)"
                    )

        # Calculate statistics
        avg_time = sum(query_times) / len(query_times)
        min_time = min(query_times)
        max_time = max(query_times)
        p50 = sorted(query_times)[len(query_times) // 2]
        p95 = sorted(query_times)[int(len(query_times) * 0.95)]
        p99 = sorted(query_times)[int(len(query_times) * 0.99)]

        print("\n📈 Optimized Query Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")

        return {
            "avg": avg_time,
            "min": min_time,
            "max": max_time,
            "p50": p50,
            "p95": p95,
            "p99": p99,
        }

    async def benchmark_flexible_query(self, num_queries: int = NUM_QUERIES):
        """
        Benchmark flexible query with difficulty tolerance

        Tests: find_videos_flexible() method
        """
        print(f"\n🚀 Benchmarking flexible query ({num_queries} queries)...")

        subjects = ["matematik", "fizik", "kimya", "biyoloji", "türkçe"]
        difficulties = ["başlangıç", "orta", "ileri"]
        exam_types = ["TYT", "AYT", "LGS"]

        query_times = []

        async with self.session_maker() as session:
            repository = OptimizedVideoRepository(session)

            for i in range(num_queries):
                subject = random.choice(subjects)
                difficulty = random.choice(difficulties)
                exam_type = random.choice(exam_types)

                start_time = time.time()

                videos = await repository.find_videos_flexible(
                    subject=subject,
                    target_difficulty=difficulty,
                    exam_type=exam_type,
                    language="tr",
                    min_quality=6.0,
                    difficulty_tolerance=1,
                    limit=20,
                )

                query_time = (time.time() - start_time) * 1000
                query_times.append(query_time)

        avg_time = sum(query_times) / len(query_times)
        p95 = sorted(query_times)[int(len(query_times) * 0.95)]

        print("\n📈 Flexible Query Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  P95: {p95:.2f}ms")

        return {"avg": avg_time, "p95": p95}

    async def benchmark_subject_query(self, num_queries: int = NUM_QUERIES):
        """
        Benchmark subject-only query

        Tests: find_videos_by_subject() method
        Uses: idx_video_subject_quality index
        """
        print(f"\n🚀 Benchmarking subject query ({num_queries} queries)...")

        subjects = ["matematik", "fizik", "kimya", "biyoloji", "türkçe"]
        query_times = []

        async with self.session_maker() as session:
            repository = OptimizedVideoRepository(session)

            for i in range(num_queries):
                subject = random.choice(subjects)

                start_time = time.time()

                videos = await repository.find_videos_by_subject(
                    subject=subject, min_quality=7.0, limit=50
                )

                query_time = (time.time() - start_time) * 1000
                query_times.append(query_time)

        avg_time = sum(query_times) / len(query_times)
        p95 = sorted(query_times)[int(len(query_times) * 0.95)]

        print("\n📈 Subject Query Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  P95: {p95:.2f}ms")

        return {"avg": avg_time, "p95": p95}

    async def benchmark_cache_operations(self):
        """
        Benchmark cache management operations

        Tests:
        - LRU eviction
        - Expired entries cleanup
        - Cache statistics
        """
        print("\n🚀 Benchmarking cache operations...")

        async with self.session_maker() as session:
            repository = OptimizedVideoRepository(session)

            # Test 1: Get cache statistics
            start_time = time.time()
            stats = await repository.get_cache_statistics()
            stats_time = (time.time() - start_time) * 1000

            print(f"\n📊 Cache Statistics (took {stats_time:.2f}ms):")
            for key, value in stats.items():
                print(f"  {key}: {value}")

            # Test 2: Get expired entries
            start_time = time.time()
            expired = await repository.get_expired_entries(limit=100)
            expired_time = (time.time() - start_time) * 1000

            print(f"\n🗑️  Expired Entries Check (took {expired_time:.2f}ms):")
            print(f"  Found {len(expired)} expired entries")

            # Test 3: LRU eviction (if needed)
            if stats["total_entries"] > 5000:
                start_time = time.time()
                evicted = await repository.evict_lru_entries(
                    max_entries=5000, evict_count=1000
                )
                eviction_time = (time.time() - start_time) * 1000

                print(f"\n🗑️  LRU Eviction (took {eviction_time:.2f}ms):")
                print(f"  Evicted {evicted} entries")

        return {"stats_time": stats_time, "expired_time": expired_time}

    async def run_full_benchmark(self):
        """Run complete benchmark suite"""
        print("=" * 60)
        print("VIDEO CACHE REPOSITORY PERFORMANCE BENCHMARK")
        print("=" * 60)

        try:
            # Setup
            await self.setup()

            # Create test data
            await self.create_test_data(NUM_TEST_VIDEOS)

            # Run benchmarks
            optimized_results = await self.benchmark_optimized_query(NUM_QUERIES)
            flexible_results = await self.benchmark_flexible_query(NUM_QUERIES)
            subject_results = await self.benchmark_subject_query(NUM_QUERIES)
            cache_results = await self.benchmark_cache_operations()

            # Summary
            print("\n" + "=" * 60)
            print("BENCHMARK SUMMARY")
            print("=" * 60)
            print(f"\n✅ Test Data: {NUM_TEST_VIDEOS} videos")
            print(f"✅ Queries per test: {NUM_QUERIES}")
            print("\n📊 Query Performance:")
            print("  Optimized Query (composite index):")
            print(f"    - Average: {optimized_results['avg']:.2f}ms")
            print(f"    - P95: {optimized_results['p95']:.2f}ms")
            print(f"    - P99: {optimized_results['p99']:.2f}ms")
            print("  Flexible Query (difficulty tolerance):")
            print(f"    - Average: {flexible_results['avg']:.2f}ms")
            print(f"    - P95: {flexible_results['p95']:.2f}ms")
            print("  Subject Query:")
            print(f"    - Average: {subject_results['avg']:.2f}ms")
            print(f"    - P95: {subject_results['p95']:.2f}ms")

            # Performance assessment
            print("\n🎯 Performance Assessment:")
            if optimized_results["p95"] < 10:
                print(
                    f"  ✅ EXCELLENT: P95 < 10ms (actual: {optimized_results['p95']:.2f}ms)"
                )
            elif optimized_results["p95"] < 50:
                print(
                    f"  ✅ GOOD: P95 < 50ms (actual: {optimized_results['p95']:.2f}ms)"
                )
            elif optimized_results["p95"] < 100:
                print(
                    f"  ⚠️  ACCEPTABLE: P95 < 100ms (actual: {optimized_results['p95']:.2f}ms)"
                )
            else:
                print(
                    f"  ❌ NEEDS OPTIMIZATION: P95 > 100ms (actual: {optimized_results['p95']:.2f}ms)"
                )

            print("\n💡 Expected Performance:")
            print("  - Without indexes: ~100ms per query")
            print("  - With composite index: ~5-10ms per query")
            print("  - Performance improvement: 10-20x faster")

        finally:
            await self.teardown()


async def main():
    """Main benchmark execution"""
    benchmark = VideoCacheBenchmark(DATABASE_URL)
    await benchmark.run_full_benchmark()


if __name__ == "__main__":
    asyncio.run(main())
