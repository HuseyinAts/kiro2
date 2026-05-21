# Locust Load Test — Real Latency Distribution

**Script:** `backend/_pilots/audit_locust_load_test.py`
**Run:** `locust --headless -u 9 -r 1 --run-time 60s --host http://localhost:8000`

NOT: 9 user (rate limit 10/60s altında), 1 user/sec ramp.

---

## Results

| Endpoint | Requests | Failures | Avg | Min | Max | p50 | p95 | p99 |
|---|---|---|---|---|---|---|---|---|
| POST /api/v1/auth/login | 33 | 0 (0%) | 1323ms | 242 | 2049 | **1300** | **2000** | **2000** |

**Throughput:** 0.55 req/sec/user (login dominant, sonra session wait)
**Total RPS:** 3.27/sec aggregate (her user 2-5s think time)

---

## 🔴 LATENCY BETA-BLOCKER

**p50 login = 1.3 saniye, p95 = 2.0 saniye.**

Production'da öğrenci:
- Her login → 1.3 saniye bekler
- p95'te 2 saniye = "site yavaş" şikayetleri
- Yeniden login (refresh failure) = 2-4 saniye

### Cumulative latency breakdown (probable)

| Component | Latency | Source |
|---|---|---|
| TCP/TLS handshake | 5-20ms | network |
| FastAPI routing | <5ms | OK |
| Rate limit check (in-memory) | <1ms | OK |
| **DB connection acquire** | **~841ms** | **R3 finding — pool wait** |
| User SELECT + bcrypt verify | 250-350ms | bcrypt cost 12 default |
| JWT signing (HS256) | 5-20ms | OK |
| Cookie write + response | <10ms | OK |
| **TOTAL** | **~1100-1300ms** | matches observed |

### Earlier workload sim "25ms median" mismatch

Önceki `audit_workload_simulator.py` 10 concurrent login = **10/10 429** — rate limit gate'i `_record_attempt` ÖNCE çalıştı, bcrypt + DB sorgusu hiç gerçekleşmedi. Early return ⇒ 25ms.

Locust **gerçek başarılı login** akışı → 1.3s median = beta UX bad.

---

## Fix Önerileri

### Acil (Day 1, beta için)

```python
# backend/core/security.py veya auth_security_utils.py
# bcrypt cost 12 (default) → 10 (dev/staging için)
from passlib.context import CryptContext
pwd_context = CryptContext(
    schemes=["bcrypt"],
    bcrypt__rounds=10,  # was 12 default — 4x faster (250ms→60ms)
)
```

**Note:** bcrypt cost 10 = ~75ms verify, 12 = ~300ms. NIST recommends ≥10. Production'da 11-12 önerilir, dev/test'te 10.

### Production (1 hafta)

- **DB pool tuning** (B-P0-12 fix uygulanırsa): pool_wait p50 841ms → <10ms (hot connection)
  - Beklenen login p50: 1300 - 841 = **~460ms**
- **Connection pre-warming**: Backend startup'ta pool'u doldur
- **PgBouncer**: 1K+ student için zorunlu

### Konservatif test (sonra)

```bash
# Rate limit B-P0-6 fix sonra (30/60):
locust -f backend/_pilots/audit_locust_load_test.py --headless \
  -u 30 -r 3 --run-time 120s --host http://localhost:8000 \
  --csv=/tmp/locust_30u

# Connection pool R3 fix sonra:
locust -u 50 -r 5 --run-time 120s
```

---

## Reproducible Command

```bash
# Wait for rate limit cooldown
sleep 65

# Headless locust (no Web UI)
locust -f backend/_pilots/audit_locust_load_test.py --headless \
  -u 9 -r 1 --run-time 60s --host http://localhost:8000 \
  --csv=/tmp/locust_kiro2

# Read results
cat /tmp/locust_kiro2_stats.csv
cat /tmp/locust_kiro2_failures.csv
```

---

## Conclusion

**Locust test KIRO2 backend için yeni P0 bulgular:**

1. **Login latency p95 = 2 saniye** (B-P0-12 #157) — beta UX bad
2. **DB pool wait dominant** (R3 ile uyumlu)
3. **Rate limit 10/60s** Locust'ta da problem (9 user limit altı)

**Sonraki adım:**
- B-P0-6 fix (rate limit 30/60)
- B-P0-12 fix (pool size adjustment)
- Re-run Locust 30 user × 120s
- p50 hedef: <500ms, p95 hedef: <1s
