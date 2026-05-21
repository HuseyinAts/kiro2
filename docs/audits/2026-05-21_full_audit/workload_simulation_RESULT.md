# Workload Simulation — KRİTİK BULGU

**Script:** `backend/_pilots/audit_workload_simulator.py`
**Run:** `python audit_workload_simulator.py --students 10 --quizzes 30 --duration 45`

---

## 🔴 BETA-BLOCKER BULGU: Login Rate Limit Concurrent Block

**Scenario:** 10 öğrenci ThreadPoolExecutor ile aynı anda backend'e login dener

**Result:**
```
Wall time: 1.4s
Session outcomes: {'login_failed_429': 10}
  Sessions OK: 0/10
  Failed reasons: ['login_failed_429'] × 10

STATUS CODE DISTRIBUTION:
  429: 10 (100.0%) ⚠️
```

**Root cause:** `backend/api/auth.py:80`

```python
RATE_LIMITS = {
    "login": (10, 60),  # 10 attempt / 60s per IP
}
```

**Plus:** `_rate_buckets` **in-memory defaultdict** — process-local, restart'ta sıfırlanır, distributed instance arası tutarsız.

---

## Production Impact Analysis

| Senaryo | Etki | Önem |
|---|---|---|
| School WiFi 15+ öğrenci aynı IP | 11. öğrenci LOGIN OLAMAZ | 🔴 BETA-BLOCKER |
| Aile evi (sibling + parent) | 3 cihaz 10 dakikada 4 retry = limit dolu | 🟡 |
| Mobile carrier-grade NAT (TR yaygın) | Binlerce öğrenci aynı IP | 🔴 P0 |
| Multi-instance deploy + restart | Bucket inconsistent, double-charge | 🟡 |
| Brute-force attacker tek IP | Sadece 10 attempt/dakika → güvenlik OK | ✅ |

---

## Fix Alternatifleri

### A. Acil fix (5 dk, beta için minimum)
```python
# backend/api/auth.py:80
RATE_LIMITS = {
    "login": (30, 60),  # 10→30, NAT network'leri tolere et
    "register": (5, 60),
    ...
}
```
**Impact:** Single shared IP'de 30 login/dakika tolere. Brute-force hala blokeli (3s/attempt sınırı).

### B. Production fix (Quality Hardening Task 7 — Redis-backed)
```python
# backend/core/rate_limiter.py (yeni)
import redis.asyncio as aioredis

class RedisRateLimiter:
    """Distributed sliding-window rate limiter."""
    async def check(self, key: str, limit: int, window: int) -> bool:
        # Redis ZRANGEBYSCORE + ZADD + EXPIRE
        ...
```
**Impact:** Tüm instance'lar tutarlı, restart-safe, distributed.

### C. Combined bucket (en güvenli)
```python
# Key = ip:email — IP başına 30, ama aynı email aynı IP'den 5/dk
def _check_combined(request, email: str):
    _check_rate_limit(request, "login_ip")  # 30/min per IP
    _check_rate_limit(request, f"login_email:{email}", limit=5)  # 5/min per email
```

---

## DB Delta During Workload

```
Δ connections   :      +0   (in-memory rate limit short-circuit, DB hit yok)
Δ commits       :      +1
Δ rollbacks     :      +1
Δ deadlocks     :      +0
Δ temp_files    :      +0
Cache hit during run: 100.0% (256 hit / 0 read)
```

Login 429 → DB query bile çağrılmadı (early return). Auth flow query path test edilemedi.

---

## Endpoint Latency

```
POST /auth/login    n=10  p50=25ms  p95=28ms  p99=28ms  max=28ms  Err 100%
```

🟢 **Login endpoint kendisi hızlı (25ms median).** Sorun rate limit gate'inde, business logic'te değil.

---

## Sonraki Adımlar

1. **Hemen fix (B-P0-6):** `RATE_LIMITS["login"] = (30, 60)` — beta için yeterli
2. **Quality Task 7 sprint:** Redis-backed rate limiter (büyük scope)
3. **Re-run workload simulator** rate limit raise sonrası — gerçek concurrent quiz submit latency ölç
4. **Locust full load test:** 100 concurrent student için profile, p95 latency targets

---

## Reproduction (5 dk)

```bash
# 1 dakika bekle (rate limit cooldown)
sleep 60

# 5 student ile retry (limit altında)
PYTHONIOENCODING=utf-8 python backend/_pilots/audit_workload_simulator.py \
  --students 5 --quizzes 20 --duration 30

# Sonra 11+ student dene → blok kanıtla
sleep 60
PYTHONIOENCODING=utf-8 python backend/_pilots/audit_workload_simulator.py \
  --students 11 --quizzes 10 --duration 30
# Beklenen: 10 OK + 1 fail veya tamamı 429
```

---

## Methodology Notes

- ThreadPoolExecutor max_workers=10 — Windows ProcessPool 61 limit aşılmadı
- httpx.Client per-thread → connection isolation (gerçek 10 farklı TCP)
- All from same `127.0.0.1` source IP → rate limit kasıtlı tetiklendi
- pg_stat_database delta — DB tarafı zaten temas etmedi (early return)
- Bu test **rate limit behavior'ı doğru detect etmek için** dizayn edildi. Different IP'lerden gelen 10 paralel login farklı sonuç verecektir.

**Bu finding olmasaydı, beta launch günü 11. öğrenci kaydolduğunda mystery 429 hatası ile karşılaşırdık.**
