# Async Operations Guide

KIRO2 Platform için asenkron işlemler rehberi.

## Genel Bakış

Bu dokümantasyon, KIRO2 platformunda kullanılan async/await patternlerini,
connection pooling yapılandırmasını ve en iyi uygulamaları açıklar.

## Async Utilities

### gather_with_results

Birden fazla coroutine'i paralel çalıştırır ve sonuçları yapılı bir şekilde döndürür.

```python
from core.async_utils import gather_with_results

async def fetch_user_data(user_id: int):
    results = await gather_with_results(
        fetch_profile(user_id),
        fetch_posts(user_id),
        fetch_settings(user_id),
        task_names=["profile", "posts", "settings"]
    )

    if results.all_succeeded:
        return {name: r.value for name, r in zip(task_names, results.successes)}
    else:
        # Partial failure handling
        for failure in results.failures:
            logger.warning(f"Task {failure.task_name} failed: {failure.error}")
```

### AsyncPool

Rate limiting ile concurrent işlem yönetimi.

```python
from core.async_utils import AsyncPool

async def process_items(items: list):
    async with AsyncPool(max_workers=10) as pool:
        results = await pool.map(process_item, items)
    return results
```

### Retry Decorator

Exponential backoff ile retry mekanizması.

```python
from core.async_utils import async_retry

@async_retry(max_retries=3, delay=1.0, backoff=2.0)
async def fetch_external_api(url: str):
    async with http_client() as client:
        response = await client.get(url)
        return response.json_data
```

## Connection Pooling

### Database (asyncpg)

```python
# core/database.py'de yapılandırılmış
# pool_size=20, max_overflow=10

async with db_manager.get_session() as session:
    result = await session.execute(query)
```

### HTTP Client (aiohttp)

```python
from core.http_client import http_client, HttpClientConfig

config = HttpClientConfig(
    base_url="https://api.example.com",
    timeout=5.0,
    max_connections=100,
    max_retries=3,
)

async with http_client(config) as client:
    response = await client.get("/users")
```

## Best Practices

### 1. asyncio.gather Kullanımı

```python
# DOĞRU - Bağımsız işlemleri paralel çalıştır
async def get_dashboard_data(user_id: int):
    profile, stats, notifications = await asyncio.gather(
        get_profile(user_id),
        get_stats(user_id),
        get_notifications(user_id),
        return_exceptions=True  # Partial failure handling
    )
    return {"profile": profile, "stats": stats, "notifications": notifications}

# YANLIŞ - Sequential çalıştırma
async def get_dashboard_data_slow(user_id: int):
    profile = await get_profile(user_id)  # Wait
    stats = await get_stats(user_id)       # Wait
    notifications = await get_notifications(user_id)  # Wait
```

### 2. Timeout Handling

```python
from core.async_utils import run_with_timeout

result = await run_with_timeout(
    slow_operation(),
    timeout=5.0,
    default=None
)

if result is None:
    # Timeout occurred, use fallback
    result = get_cached_result()
```

### 3. Batch Processing

```python
from core.async_utils import batch_process

# Memory-efficient processing of large datasets
results = await batch_process(
    items=large_list,
    processor=process_item,
    batch_size=100,
    delay_between_batches=0.1
)
```

### 4. Context Managers

```python
from core.async_utils import async_timer

async with async_timer("database_query"):
    result = await db.execute(complex_query)
# Logs: "database_query completed in 45.23ms"
```

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| P50 Latency | < 100ms | Varies |
| P95 Latency | < 200ms | Varies |
| P99 Latency | < 500ms | Varies |
| Throughput | >= 1000 req/sec | Varies |

## Troubleshooting

### Connection Pool Exhaustion

```
sqlalchemy.exc.TimeoutError: QueuePool limit reached
```

**Çözüm:**
1. Connection pool size artır
2. Session leak kontrolü yap
3. Long-running transaction'ları optimize et

### Async Context Errors

```
RuntimeError: Event loop is closed
```

**Çözüm:**
1. Proper async context management kullan
2. `asyncio.run()` yerine `uvicorn` kullan
3. Background task'larda `asyncio.create_task()` kullan

## Related Documentation

- [API Response Time Optimization](./api-optimization.md)
- [Database Query Optimization](./database-optimization.md)
- [Caching Strategy](./caching-strategy.md)
