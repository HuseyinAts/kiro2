# Database Stress Test Suite - KIRO2

Comprehensive database load testing for the KIRO2 platform's PostgreSQL database.

## Overview

This test suite validates database performance under realistic production-like loads, including:

1. **Concurrent Read Stress**: Multiple simultaneous SELECT queries
2. **Write Contention**: Concurrent INSERT/UPDATE operations
3. **Connection Pool Exhaustion**: Pool limit testing
4. **Query Performance Benchmarks**: Critical query timing assertions
5. **Transaction Isolation**: Concurrent updates to same records

## Requirements

- PostgreSQL running on **port 5434** (KIRO2 standard)
- Python 3.11+
- pytest with asyncio support
- SQLAlchemy async with asyncpg driver

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Running Tests

### Run All Stress Tests

```bash
# From backend directory
pytest tests/load/test_db_stress.py -v -s
```

### Run Specific Test Classes

```bash
# Concurrent read tests only
pytest tests/load/test_db_stress.py::TestDBConcurrentReads -v

# Write contention tests only
pytest tests/load/test_db_stress.py::TestDBWriteContention -v

# Connection pool tests only
pytest tests/load/test_db_stress.py::TestDBConnectionPool -v

# Query performance benchmarks only
pytest tests/load/test_db_stress.py::TestDBQueryPerformance -v
```

### Run Individual Tests

```bash
# Specific test
pytest tests/load/test_db_stress.py::TestDBConcurrentReads::test_concurrent_question_reads -v
```

### Run with Markers

```bash
# All slow tests (includes these stress tests)
pytest -m slow -v

# Skip slow tests
pytest -m "not slow"
```

## Test Classes

### TestDBConcurrentReads

Tests concurrent read operations:
- `test_concurrent_question_reads`: 50 concurrent workers, 10 reads each
- `test_complex_join_queries_concurrent`: 20 concurrent complex queries with JOINs

**Expected Results:**
- QPS > 100 queries per second
- Average query time < 50ms
- No exceptions

### TestDBWriteContention

Tests concurrent write operations:
- `test_concurrent_inserts`: 30 workers inserting 5 records each
- `test_concurrent_updates_same_record`: Transaction isolation with 20 concurrent updates

**Expected Results:**
- All inserts succeed
- No lost updates (transaction isolation verified)
- Final count matches expected

### TestDBConnectionPool

Tests connection pool behavior:
- `test_pool_exhaustion_handling`: Exceeds pool limit gracefully
- `test_connection_reuse`: Verifies connections are recycled

**Expected Results:**
- Graceful handling when pool is full
- Connection reuse within pool size limits

### TestDBQueryPerformance

Benchmarks critical query performance:
- `test_simple_select_performance`: 100 simple SELECT queries
- `test_index_usage_performance`: Verifies indexes are used
- `test_aggregation_performance`: Tests COUNT, AVG, GROUP BY

**Expected Results:**
- Simple SELECT < 10ms average
- P95 < 20ms
- All aggregations < 1s

### Comprehensive Stress Test

`test_comprehensive_stress_summary`: Mixed workload simulation
- 60% reads
- 30% updates
- 10% inserts
- 20 concurrent workers
- 5 second duration

**Expected Results:**
- OPS > 50 operations per second
- Error rate < 5%
- Total operations > 100

## Performance Assertions

The tests include meaningful performance assertions (NOT `assert True`):

```python
# Query performance
assert duration < 0.1, f"Query too slow: {duration:.3f}s"

# QPS threshold
assert qps > 100, f"QPS too low: {qps:.1f}"

# Transaction isolation
assert final_count == expected_count, "Transaction isolation failed"

# Error rate
assert error_rate < 0.05, f"Error rate too high: {error_rate:.2%}"
```

## Configuration

### Database Connection

Tests use the database URL from `backend/core/config.py`:

```python
database_url = settings.database_url  # Port 5434 for KIRO2
```

### Pool Settings

Test engine configuration:
```python
pool_size=20         # Base pool size
max_overflow=30      # Additional connections under load
pool_timeout=10      # Wait up to 10s for connection
pool_pre_ping=True   # Health check before use
pool_recycle=300     # Recycle after 5 minutes
```

## Troubleshooting

### Database Not Available

If tests are skipped with "Database not available":
1. Ensure PostgreSQL is running on port 5434
2. Check `DATABASE_URL` in `.env` file
3. Verify database migrations are up to date

```bash
# Check database connection
psql -h localhost -p 5434 -U your_user -d kiro2

# Run migrations
alembic upgrade head
```

### Connection Pool Exhausted

If you see `OperationalError` or `TimeoutError`:
1. Reduce concurrent worker count in tests
2. Increase pool size in database configuration
3. Check for connection leaks in application code

### Slow Query Performance

If performance assertions fail:
1. Check database indexes: `EXPLAIN ANALYZE SELECT ...`
2. Verify PostgreSQL is not under heavy load
3. Review query execution plans
4. Consider increasing hardware resources

### Transaction Isolation Failures

If concurrent update tests fail:
1. Verify PostgreSQL isolation level is READ_COMMITTED or higher
2. Check for deadlocks in PostgreSQL logs
3. Review application transaction handling

## Monitoring

During test execution, the suite prints detailed metrics:

```
=== Concurrent Read Test Results ===
Total queries: 500
Total duration: 2.45s
Queries per second: 204.1
Avg query time: 4.2ms
Max query time: 18.3ms
```

```
=== Transaction Isolation Test Results ===
Concurrent updates: 20
Final count: 20
Expected: 20
```

```
=== Comprehensive Stress Test Results ===
Duration: 5.02s
Workers: 20
Total operations: 1234
  - Reads: 740
  - Updates: 370
  - Inserts: 124
Errors: 2
Operations per second: 245.8
Error rate: 0.16%
```

## Integration with CI/CD

Add to GitHub Actions workflow:

```yaml
- name: Run Database Stress Tests
  run: |
    cd backend
    pytest tests/load/test_db_stress.py -v --tb=short
  env:
    DATABASE_URL: postgresql://user:pass@localhost:5434/kiro2_test
```

## Best Practices

1. **Run in isolation**: Close other database connections during tests
2. **Clean environment**: Use a test database, not production
3. **Monitor resources**: Watch CPU, memory, and I/O during tests
4. **Regular execution**: Run weekly or before major releases
5. **Baseline metrics**: Track performance trends over time

## Safety

These tests:
- ✅ Use `@pytest.mark.slow` marker
- ✅ Skip gracefully if DB is unavailable
- ✅ Clean up test data after execution
- ✅ Use separate test database (via `DATABASE_URL`)
- ✅ Include meaningful assertions (no `assert True`)
- ✅ Handle connection pool exhaustion gracefully

## Related Documentation

- [KIRO2 Database Configuration](../../core/database.py)
- [KIRO2 Testing Rules](../../../.claude/rules/testing.md)
- [KIRO2 Verification Standards](../../../.claude/rules/verification.md)

## Contact

For issues or questions:
- Project: KIRO2 - YKS AI Education Platform
- Tech Stack: FastAPI + PostgreSQL + SQLAlchemy Async
- Database Port: **5434** (NOT 5432!)

---

**Note**: Always verify tests pass locally before committing. Use `ruff check` and `mypy` as required by KIRO2 standards.
