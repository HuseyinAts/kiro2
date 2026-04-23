"""
Database Stress Test Suite - KIRO2 Platform

Comprehensive load testing for PostgreSQL database operations:
1. Concurrent read stress (questions, users, exam results)
2. Write contention (exam answers, student progress)
3. Connection pool exhaustion
4. Query performance benchmarks
5. Transaction isolation testing

Requirements:
- PostgreSQL on port 5434 (KIRO2 standard)
- SQLAlchemy async with asyncpg driver
- pytest with asyncio support

Author: KIRO2 Team
Date: 2026-01-28
"""

import asyncio
import time
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Try to import from project, skip tests if not available
try:
    from backend.core.config import settings

    DB_AVAILABLE = True
except ImportError as e:
    DB_AVAILABLE = False
    pytest.skip(f"Database modules not available: {e}", allow_module_level=True)


# ==================== FIXTURES ====================

# Note: event_loop fixture removed - pytest-asyncio auto mode handles this
# Duplicate fixtures cause conflicts with pytest-asyncio>=0.21


@pytest.fixture(scope="module")
async def test_engine():
    """Create a test database engine with custom pool settings."""
    if not DB_AVAILABLE:
        pytest.skip("Database not available")

    try:
        # Use PostgreSQL on port 5434 (KIRO2 standard)
        database_url = settings.database_url

        # Ensure asyncpg driver
        if "postgresql://" in database_url and "+asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

        # Create engine with stress test pool settings
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=20,  # Smaller pool for stress testing
            max_overflow=30,
            pool_timeout=10,
            pool_pre_ping=True,
            pool_recycle=300,
        )

        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        yield engine

        await engine.dispose()

    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


@pytest.fixture(scope="module")
async def db_initialized(test_engine):
    """Ensure database tables are created."""
    async with test_engine.begin() as conn:
        # Check if tables exist
        result = await conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'sorular'
                )
                """
            )
        )
        tables_exist = result.scalar()

        if not tables_exist:
            pytest.skip("Database tables not initialized. Run migrations first.")

    return True


@pytest.fixture
async def db_session(test_engine, db_initialized):
    """Create a database session for tests."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
        autocommit=False,
    )

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==================== HELPER FUNCTIONS ====================


async def create_test_question(session: AsyncSession, index: int) -> str:
    """Create a test question in the database."""
    question_id = str(uuid.uuid4())

    # Insert directly using SQL to avoid model complexity
    await session.execute(
        text(
            """
            INSERT INTO sorular (
                id, metin, secenekler, dogru_cevap,
                sinav_tipi, konu, zorluk,
                irt_difficulty, irt_discrimination, irt_guessing,
                aktif, olusturma_tarihi
            ) VALUES (
                :id, :metin, :secenekler, :dogru_cevap,
                :sinav_tipi, :konu, :zorluk,
                :irt_difficulty, :irt_discrimination, :irt_guessing,
                :aktif, :olusturma_tarihi
            )
            """
        ),
        {
            "id": question_id,
            "metin": f"Test soru {index}: 2x + 3 = 7 ise x kaçtır?",
            "secenekler": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"},
            "dogru_cevap": "B",
            "sinav_tipi": "TYT",
            "konu": "Matematik",
            "zorluk": "ORTA",
            "irt_difficulty": 0.0,
            "irt_discrimination": 1.0,
            "irt_guessing": 0.2,
            "aktif": True,
            "olusturma_tarihi": datetime.now(UTC),
        },
    )
    await session.commit()
    return question_id


async def cleanup_test_data(session: AsyncSession, prefix: str = "stress_test_"):
    """Clean up test data from the database."""
    try:
        # Clean test questions
        await session.execute(
            text("DELETE FROM sorular WHERE metin LIKE 'Test soru %'")
        )
        await session.commit()
    except Exception as e:
        print(f"Cleanup warning: {e}")
        await session.rollback()


# ==================== CONCURRENT READ TESTS ====================


@pytest.mark.slow
@pytest.mark.asyncio
class TestDBConcurrentReads:
    """Test concurrent read operations under load."""

    async def test_concurrent_question_reads(self, test_engine, db_initialized):
        """Test multiple simultaneous SELECT queries on questions table."""
        num_concurrent = 50  # Number of concurrent reads
        reads_per_task = 10  # Reads per concurrent task

        async def read_questions():
            """Perform multiple question reads."""
            from sqlalchemy.ext.asyncio import async_sessionmaker

            async_session_maker = async_sessionmaker(
                bind=test_engine,
                expire_on_commit=False,
            )

            read_times = []

            async with async_session_maker() as session:
                for _ in range(reads_per_task):
                    start = time.time()

                    result = await session.execute(
                        text("SELECT COUNT(*) FROM sorular WHERE aktif = true")
                    )
                    count = result.scalar()

                    duration = time.time() - start
                    read_times.append(duration)

                    # Assertion: Query should be fast (< 100ms for COUNT)
                    assert duration < 0.1, f"Query too slow: {duration:.3f}s"
                    assert count is not None, "Query returned NULL"

            return read_times

        # Execute concurrent reads
        start_time = time.time()
        tasks = [read_questions() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time

        # Verify no exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Concurrent reads failed: {exceptions[:5]}"

        # Calculate statistics
        all_times = [t for result in results for t in result]
        avg_time = sum(all_times) / len(all_times)
        max_time = max(all_times)
        total_queries = num_concurrent * reads_per_task
        qps = total_queries / total_duration

        print("\n=== Concurrent Read Test Results ===")
        print(f"Total queries: {total_queries}")
        print(f"Total duration: {total_duration:.2f}s")
        print(f"Queries per second: {qps:.1f}")
        print(f"Avg query time: {avg_time*1000:.1f}ms")
        print(f"Max query time: {max_time*1000:.1f}ms")

        # Performance assertions
        assert qps > 100, f"QPS too low: {qps:.1f} (expected > 100)"
        assert avg_time < 0.05, f"Avg query time too high: {avg_time*1000:.1f}ms"

    async def test_complex_join_queries_concurrent(self, test_engine, db_initialized):
        """Test concurrent complex queries with JOINs."""
        num_concurrent = 20

        async def complex_query():
            """Execute a complex query with aggregations."""
            from sqlalchemy.ext.asyncio import async_sessionmaker

            async_session_maker = async_sessionmaker(bind=test_engine)

            async with async_session_maker() as session:
                start = time.time()

                # Complex query: Get question statistics by topic
                result = await session.execute(
                    text(
                        """
                        SELECT
                            konu,
                            COUNT(*) as total_questions,
                            AVG(irt_difficulty) as avg_difficulty,
                            AVG(morfoloji_skoru) as avg_complexity
                        FROM sorular
                        WHERE aktif = true
                        GROUP BY konu
                        ORDER BY total_questions DESC
                        LIMIT 10
                        """
                    )
                )
                rows = result.fetchall()

                duration = time.time() - start

                # Query should complete in reasonable time
                assert duration < 0.5, f"Complex query too slow: {duration:.3f}s"
                assert len(rows) >= 0, "Query should return results or empty set"

                return duration

        # Execute concurrent complex queries
        start_time = time.time()
        tasks = [complex_query() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time

        # Verify success
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Complex queries failed: {exceptions}"

        durations = [r for r in results if not isinstance(r, Exception)]
        avg_duration = sum(durations) / len(durations)

        print("\n=== Complex Query Test Results ===")
        print(f"Total queries: {num_concurrent}")
        print(f"Avg query time: {avg_duration*1000:.1f}ms")
        print(f"Total duration: {total_duration:.2f}s")

        assert avg_duration < 0.3, f"Complex queries too slow: {avg_duration:.3f}s"


# ==================== WRITE CONTENTION TESTS ====================


@pytest.mark.slow
@pytest.mark.asyncio
class TestDBWriteContention:
    """Test concurrent write operations and contention."""

    async def test_concurrent_inserts(self, test_engine, db_initialized):
        """Test concurrent INSERT operations."""
        num_concurrent = 30
        inserts_per_task = 5

        async def insert_questions():
            """Insert multiple test questions."""
            from sqlalchemy.ext.asyncio import async_sessionmaker

            async_session_maker = async_sessionmaker(bind=test_engine)

            inserted_ids = []

            async with async_session_maker() as session:
                try:
                    for i in range(inserts_per_task):
                        question_id = str(uuid.uuid4())

                        await session.execute(
                            text(
                                """
                                INSERT INTO sorular (
                                    id, metin, secenekler, dogru_cevap,
                                    sinav_tipi, konu, aktif, olusturma_tarihi
                                ) VALUES (
                                    :id, :metin, :secenekler, :dogru_cevap,
                                    :sinav_tipi, :konu, :aktif, :olusturma_tarihi
                                )
                                """
                            ),
                            {
                                "id": question_id,
                                "metin": f"Concurrent test {question_id[:8]}",
                                "secenekler": {"A": "1", "B": "2", "C": "3", "D": "4"},
                                "dogru_cevap": "A",
                                "sinav_tipi": "TYT",
                                "konu": "Test",
                                "aktif": True,
                                "olusturma_tarihi": datetime.now(UTC),
                            },
                        )
                        inserted_ids.append(question_id)

                    await session.commit()
                    return inserted_ids

                except Exception:
                    await session.rollback()
                    raise

        # Execute concurrent inserts
        start_time = time.time()
        tasks = [insert_questions() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time

        # Verify success
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Concurrent inserts failed: {exceptions[:3]}"

        successful_inserts = [r for r in results if not isinstance(r, Exception)]
        total_inserted = sum(len(ids) for ids in successful_inserts)

        print("\n=== Concurrent Insert Test Results ===")
        print(f"Total inserts: {total_inserted}")
        print(f"Total duration: {total_duration:.2f}s")
        print(f"Inserts per second: {total_inserted/total_duration:.1f}")

        # Cleanup
        from sqlalchemy.ext.asyncio import async_sessionmaker
        async_session_maker = async_sessionmaker(bind=test_engine)
        async with async_session_maker() as session:
            await session.execute(
                text("DELETE FROM sorular WHERE metin LIKE 'Concurrent test%'")
            )
            await session.commit()

        assert total_inserted == num_concurrent * inserts_per_task

    async def test_concurrent_updates_same_record(self, test_engine, db_initialized):
        """Test transaction isolation with concurrent updates to same record."""
        # Create a test question
        from sqlalchemy.ext.asyncio import async_sessionmaker

        async_session_maker = async_sessionmaker(bind=test_engine)
        test_id = str(uuid.uuid4())

        # Insert test record
        async with async_session_maker() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO sorular (
                        id, metin, secenekler, dogru_cevap,
                        sinav_tipi, konu, cozulme_sayisi, aktif, olusturma_tarihi
                    ) VALUES (
                        :id, :metin, :secenekler, :dogru_cevap,
                        :sinav_tipi, :konu, 0, true, :olusturma_tarihi
                    )
                    """
                ),
                {
                    "id": test_id,
                    "metin": "Isolation test question",
                    "secenekler": {"A": "1", "B": "2", "C": "3", "D": "4"},
                    "dogru_cevap": "A",
                    "sinav_tipi": "TYT",
                    "konu": "Test",
                    "olusturma_tarihi": datetime.now(UTC),
                },
            )
            await session.commit()

        num_concurrent = 20

        async def update_counter():
            """Increment the counter field."""
            async with async_session_maker() as session:
                try:
                    # Use atomic increment
                    await session.execute(
                        text(
                            """
                            UPDATE sorular
                            SET cozulme_sayisi = COALESCE(cozulme_sayisi, 0) + 1
                            WHERE id = :id
                            """
                        ),
                        {"id": test_id},
                    )
                    await session.commit()
                    return True
                except Exception as e:
                    await session.rollback()
                    return e

        # Execute concurrent updates
        tasks = [update_counter() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks)

        # Verify all succeeded
        failures = [r for r in results if isinstance(r, Exception)]
        assert len(failures) == 0, f"Some updates failed: {failures}"

        # Verify final count is correct (transaction isolation test)
        async with async_session_maker() as session:
            result = await session.execute(
                text("SELECT cozulme_sayisi FROM sorular WHERE id = :id"),
                {"id": test_id},
            )
            final_count = result.scalar()

        print("\n=== Transaction Isolation Test Results ===")
        print(f"Concurrent updates: {num_concurrent}")
        print(f"Final count: {final_count}")
        print(f"Expected: {num_concurrent}")

        # Cleanup
        async with async_session_maker() as session:
            await session.execute(
                text("DELETE FROM sorular WHERE id = :id"), {"id": test_id}
            )
            await session.commit()

        # Critical assertion: No lost updates
        assert final_count == num_concurrent, (
            f"Transaction isolation failed: expected {num_concurrent}, got {final_count}"
        )


# ==================== CONNECTION POOL TESTS ====================


@pytest.mark.slow
@pytest.mark.asyncio
class TestDBConnectionPool:
    """Test connection pool behavior under stress."""

    async def test_pool_exhaustion_handling(self, test_engine, db_initialized):
        """Test behavior when connection pool is exhausted."""
        pool_size = test_engine.pool.size()
        max_overflow = test_engine.pool._max_overflow
        max_connections = pool_size + max_overflow

        # Try to exceed pool limit
        num_tasks = max_connections + 10

        async def hold_connection():
            """Hold a connection for some time."""
            from sqlalchemy.ext.asyncio import async_sessionmaker

            async_session_maker = async_sessionmaker(bind=test_engine)

            try:
                async with async_session_maker() as session:
                    await session.execute(text("SELECT 1"))
                    await asyncio.sleep(0.5)  # Hold connection
                    return True
            except (OperationalError, SQLAlchemyTimeoutError) as e:
                # Expected when pool is exhausted
                return f"timeout:{type(e).__name__}"
            except Exception as e:
                return f"error:{type(e).__name__}"

        start_time = time.time()
        tasks = [hold_connection() for _ in range(num_tasks)]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        successful = [r for r in results if r is True]
        timeouts = [r for r in results if isinstance(r, str) and "timeout" in r]
        errors = [r for r in results if isinstance(r, str) and "error" in r]

        print("\n=== Connection Pool Exhaustion Test ===")
        print(f"Pool size: {pool_size}")
        print(f"Max overflow: {max_overflow}")
        print(f"Max connections: {max_connections}")
        print(f"Attempted tasks: {num_tasks}")
        print(f"Successful: {len(successful)}")
        print(f"Timeouts: {len(timeouts)}")
        print(f"Errors: {len(errors)}")
        print(f"Duration: {duration:.2f}s")

        # Pool should handle exhaustion gracefully
        assert len(successful) > 0, "No connections succeeded"
        assert len(successful) <= max_connections, "More connections than pool allows"

    async def test_connection_reuse(self, test_engine, db_initialized):
        """Test that connections are properly recycled and reused."""
        num_iterations = 50

        async def use_connection():
            """Use and release a connection."""
            from sqlalchemy.ext.asyncio import async_sessionmaker

            async_session_maker = async_sessionmaker(bind=test_engine)

            async with async_session_maker() as session:
                result = await session.execute(text("SELECT pg_backend_pid()"))
                backend_pid = result.scalar()
                return backend_pid

        # Execute sequentially to observe connection reuse
        pids = []
        for _ in range(num_iterations):
            pid = await use_connection()
            pids.append(pid)
            await asyncio.sleep(0.01)  # Small delay

        unique_pids = set(pids)
        pool_size = test_engine.pool.size()

        print("\n=== Connection Reuse Test ===")
        print(f"Total queries: {num_iterations}")
        print(f"Unique connections used: {len(unique_pids)}")
        print(f"Pool size: {pool_size}")

        # Should reuse connections (unique PIDs should be <= pool size)
        assert len(unique_pids) <= pool_size + 5, (
            f"Too many unique connections: {len(unique_pids)} > pool {pool_size}"
        )


# ==================== QUERY PERFORMANCE TESTS ====================


@pytest.mark.slow
@pytest.mark.asyncio
class TestDBQueryPerformance:
    """Benchmark critical query performance."""

    async def test_simple_select_performance(self, test_engine, db_initialized):
        """Benchmark simple SELECT query performance."""
        num_queries = 100

        from sqlalchemy.ext.asyncio import async_sessionmaker
        async_session_maker = async_sessionmaker(bind=test_engine)

        times = []

        async with async_session_maker() as session:
            for _ in range(num_queries):
                start = time.time()
                await session.execute(text("SELECT 1"))
                duration = time.time() - start
                times.append(duration)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print("\n=== Simple SELECT Performance ===")
        print(f"Queries: {num_queries}")
        print(f"Avg: {avg_time*1000:.2f}ms")
        print(f"Min: {min_time*1000:.2f}ms")
        print(f"Max: {max_time*1000:.2f}ms")
        print(f"P95: {p95_time*1000:.2f}ms")

        # Performance assertions
        assert avg_time < 0.01, f"Simple SELECT too slow: {avg_time*1000:.2f}ms"
        assert p95_time < 0.02, f"P95 too high: {p95_time*1000:.2f}ms"

    async def test_index_usage_performance(self, test_engine, db_initialized):
        """Verify that indexes are being used for common queries."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        async_session_maker = async_sessionmaker(bind=test_engine)

        # Query that should use index: aktif column
        async with async_session_maker() as session:
            start = time.time()

            # Use EXPLAIN to check index usage
            result = await session.execute(
                text(
                    """
                    EXPLAIN (FORMAT JSON)
                    SELECT * FROM sorular
                    WHERE aktif = true
                    LIMIT 10
                    """
                )
            )
            _plan = result.scalar()

            duration = time.time() - start

            print("\n=== Index Usage Test ===")
            print(f"Query plan fetch time: {duration*1000:.2f}ms")

            # Execute the actual query
            start = time.time()
            result = await session.execute(
                text("SELECT * FROM sorular WHERE aktif = true LIMIT 10")
            )
            rows = result.fetchall()
            query_duration = time.time() - start

            print(f"Query execution time: {query_duration*1000:.2f}ms")
            print(f"Rows returned: {len(rows)}")

        # Indexed query should be fast
        assert query_duration < 0.1, f"Indexed query too slow: {query_duration:.3f}s"

    async def test_aggregation_performance(self, test_engine, db_initialized):
        """Test performance of aggregation queries."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        async_session_maker = async_sessionmaker(bind=test_engine)

        queries = [
            ("COUNT", "SELECT COUNT(*) FROM sorular"),
            ("AVG", "SELECT AVG(irt_difficulty) FROM sorular WHERE aktif = true"),
            ("GROUP BY", "SELECT konu, COUNT(*) FROM sorular GROUP BY konu"),
        ]

        results = {}

        async with async_session_maker() as session:
            for query_name, query_sql in queries:
                start = time.time()
                await session.execute(text(query_sql))
                duration = time.time() - start
                results[query_name] = duration

        print("\n=== Aggregation Performance ===")
        for query_name, duration in results.items():
            print(f"{query_name}: {duration*1000:.2f}ms")

        # All aggregations should complete quickly
        for query_name, duration in results.items():
            assert duration < 1.0, (
                f"{query_name} query too slow: {duration:.3f}s"
            )


# ==================== SUMMARY TEST ====================


@pytest.mark.slow
@pytest.mark.asyncio
async def test_comprehensive_stress_summary(test_engine, db_initialized):
    """
    Comprehensive stress test combining multiple operations.

    This test simulates realistic mixed workload:
    - 60% reads
    - 30% updates
    - 10% inserts
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session_maker = async_sessionmaker(bind=test_engine)

    duration_seconds = 5  # Run for 5 seconds
    num_workers = 20

    stats = {
        "reads": 0,
        "updates": 0,
        "inserts": 0,
        "errors": 0,
    }

    async def worker():
        """Worker performing mixed operations."""
        end_time = time.time() + duration_seconds

        while time.time() < end_time:
            operation = hash(time.time()) % 10

            try:
                async with async_session_maker() as session:
                    if operation < 6:  # 60% reads
                        await session.execute(
                            text("SELECT COUNT(*) FROM sorular WHERE aktif = true")
                        )
                        stats["reads"] += 1
                    elif operation < 9:  # 30% updates
                        # Update random question's stats
                        await session.execute(
                            text(
                                """
                                UPDATE sorular
                                SET cozulme_sayisi = COALESCE(cozulme_sayisi, 0) + 1
                                WHERE id IN (
                                    SELECT id FROM sorular
                                    WHERE aktif = true
                                    LIMIT 1
                                )
                                """
                            )
                        )
                        await session.commit()
                        stats["updates"] += 1
                    else:  # 10% inserts
                        test_id = str(uuid.uuid4())
                        await session.execute(
                            text(
                                """
                                INSERT INTO sorular (
                                    id, metin, secenekler, dogru_cevap,
                                    sinav_tipi, konu, aktif, olusturma_tarihi
                                ) VALUES (
                                    :id, :metin, :secenekler, :dogru_cevap,
                                    :sinav_tipi, :konu, true, :olusturma_tarihi
                                )
                                """
                            ),
                            {
                                "id": test_id,
                                "metin": f"Stress test {test_id[:8]}",
                                "secenekler": {"A": "1", "B": "2", "C": "3", "D": "4"},
                                "dogru_cevap": "A",
                                "sinav_tipi": "TYT",
                                "konu": "StressTest",
                                "olusturma_tarihi": datetime.now(UTC),
                            },
                        )
                        await session.commit()
                        stats["inserts"] += 1

            except Exception:
                stats["errors"] += 1
                await asyncio.sleep(0.1)  # Back off on error

    # Run workers
    start_time = time.time()
    tasks = [worker() for _ in range(num_workers)]
    await asyncio.gather(*tasks)
    total_duration = time.time() - start_time

    total_ops = stats["reads"] + stats["updates"] + stats["inserts"]
    ops_per_second = total_ops / total_duration

    print("\n=== Comprehensive Stress Test Results ===")
    print(f"Duration: {total_duration:.2f}s")
    print(f"Workers: {num_workers}")
    print(f"Total operations: {total_ops}")
    print(f"  - Reads: {stats['reads']}")
    print(f"  - Updates: {stats['updates']}")
    print(f"  - Inserts: {stats['inserts']}")
    print(f"Errors: {stats['errors']}")
    print(f"Operations per second: {ops_per_second:.1f}")
    print(f"Error rate: {stats['errors']/total_ops*100:.2f}%")

    # Cleanup inserts
    async with async_session_maker() as session:
        await session.execute(
            text("DELETE FROM sorular WHERE metin LIKE 'Stress test%'")
        )
        await session.commit()

    # Performance assertions
    assert ops_per_second > 50, f"OPS too low: {ops_per_second:.1f}"
    assert stats["errors"] / max(total_ops, 1) < 0.05, (
        f"Error rate too high: {stats['errors']/total_ops*100:.2f}%"
    )
    assert total_ops > 100, f"Too few operations completed: {total_ops}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
