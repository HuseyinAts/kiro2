# Concurrency Analysis — A+B Katmanı
**Tarih:** 2026-04-10 | **Agent sayısı:** 3 (4. agent API overload) | **Kapsam:** services/ + api/ + core/

---

## ÖZET SKOR

| Katman | P0 | P1 | P2 | Durum |
|--------|----|----|-----|-------|
| A) Services (app/services/) | 0 | 0 | 0 | ✅ Temiz |
| A) API (app/api/) | 1 | 2 | 1 | ⚠️ 1 kritik |
| B) Resource Pool (core/) | 5 | 5 | 5 | 🔴 Acil |
| **TOPLAM** | **6** | **7** | **6** | |

---

## P0 — HEMEN FIX (6 bulgu)

### P0-1: `backend/app/api/placement.py:128-134`
**Sorun:** `row = await svc.db.execute(...)` sonrası `.fetchone()` sonuçsuz — `result` değişkeni execute result değil, yanlış atama.

**Fix:**
```python
result = await svc.db.execute(
    text("SELECT correct_answer FROM question_bank WHERE id = :qid AND is_active = TRUE"),
    {"qid": body.question_id},
)
q_row = result.fetchone()  # result üzerinden çağır
```

---

### P0-2: `backend/app/core/deps.py:43`
**Sorun:** Fallback path'te her request'e yeni `aioredis.from_url()` instance açılıyor. Connection pool yok → 1000 concurrent request = 1000 ayrı TCP bağlantı.

**Fix:**
```python
_redis_client = None

async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=False,
            max_connections=100,
        )
    return _redis_client
```

---

### P0-3: `backend/core/database.py:395-418`
**Sorun:** `get_db()` **sync** fonksiyon — `session.commit()` blocking I/O async context'te. Async endpoint'ler bu dependency'i kullanırsa event loop bloke olur.

**Fix:**
```python
async def get_db():
    async with db_manager.get_session() as session:
        yield session
```

---

### P0-4: `backend/core/database.py:166`
**Sorun:** `pool_recycle=300` (5 dk) < PostgreSQL idle timeout (600s). 300-600s arasında idle kalan connection → "server closed the connection unexpectedly".

**Fix:**
```python
"pool_recycle": 600,  # PostgreSQL default idle timeout ile eşle
```

---

### P0-5: `backend/config/redis_optimized_config.py:38-44`
**Sorun:** `_pool` ve `_client` class attribute'leri thread-safe değil — double-checked locking yok. 10 concurrent thread 10 farklı pool yaratabilir.

**Fix:**
```python
import threading
_lock = threading.Lock()

@classmethod
def get_client(cls) -> redis.Redis:
    with _lock:
        if cls._client is None:
            cls._pool = ConnectionPool(**OptimizedRedisConfig.REDIS_CONFIG)
            cls._client = redis.Redis(connection_pool=cls._pool)
    return cls._client
```

---

### P0-6: `backend/core/cache/cache_manager.py:71`
**Sorun:** `max_connections=50` — 50+ concurrent Redis operasyonunda yeni request'ler timeout bekler. CAT exam session'larında cascade çöküş riski.

**Fix:**
```python
max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "100"))
self.redis = await aioredis.from_url(
    self.redis_url,
    decode_responses=False,
    max_connections=max_connections,
)
```

---

## P1 — BU SPRINT İÇİNDE (7 bulgu)

| # | Dosya:Satır | Sorun | Fix Yönü |
|---|-------------|-------|----------|
| 1 | `app/api/learning_path_daily.py:283-314` | Exception between commit-rollback → half-update DB | try/except atomicity |
| 2 | `app/api/fsrs.py:48-69` | `irt` tuple unpacking'de validation yok — None keys silent | `isinstance` check veya type hint |
| 3 | `core/database_replication.py:123` | Replica: `create_engine()` sync, primary async — pool mismatch | `create_async_engine()` |
| 4 | `core/enhanced_database.py:54-76` | `pool_size=30` hard-default, settings'ten gelmiyor | Settings'ten `db_pool_size` al |
| 5 | `core/advanced_cache.py:99-102` | L2 Redis pool `max_connections=20` — L1 miss cascade | min 50 connections |
| 6 | `core/jwt_auth.py:317-349` | In-memory blacklist 10K limit < 100K logout/gün | LRU bounded cache |
| 7 | `core/cache/cache_manager.py:196` | `invalidate_pattern()` pipeline yok — O(n) blocking delete | `pipeline()` kullan |

---

## P2 — TEKNİK BORÇ (6 bulgu)

| # | Dosya:Satır | Sorun |
|---|-------------|-------|
| 1 | `app/api/fsrs.py:31-69` | Response model'de unsafe list comprehension |
| 2 | `core/config.py:112` | `DB_POOL_SIZE=200` default — capacity planning doc yok |
| 3 | `core/database.py:164` | `pool_pre_ping=True` overhead ~1ms/req — monitoring yok |
| 4 | `config/redis_optimized_config.py:20` | `max_connections=50` hard-coded, env override yok |
| 5 | `core/cache/cache_manager.py:64` | `print()` kullanımı — `logger.error()` olmalı |
| 6 | `core/database_replication.py:113` | Replica URL loop — max limit yok, 100 engine riski |

---

## KONSENSUS (2+ agent hemfikir)

1. **Redis pool yetersizliği** — deps.py + cache_manager + redis_optimized_config üç ayrı yerde bağımsız pool sorunu → tek singleton pattern'e geçiş şart.
2. **Sync/async session karmaşası** — services katmanı temiz, ama core katmanında sync get_db() hâlâ aktif. API layer bu ikisini birlikte kullanıyor.
3. **Services katmanı temiz** — services/ tüm async pattern'leri doğru kullanıyor. Sorunlar yalnızca core/ ve api/ sınırında.

---

## ÖNCELİK SIRASI

```
Week 1 (P0): deps.py + cache_manager max_connections → Redis pool tek noktada topla
Week 1 (P0): database.py get_db() sync→async + pool_recycle 300→600
Week 2 (P1): jwt_auth.py blacklist + invalidate_pattern pipeline
Week 3 (P1): database_replication.py async engine migration
```

---

*Audit: Claude Code 2026-04-10 | Paralel 3-agent tarama*
