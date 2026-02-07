# Health Monitoring Runbook

## Operasyonel Prosedurler

Bu dokuman, health monitoring sistemi icin operasyonel prosedurler ve
sorun giderme adimlari icerir.

---

## Alert Tepki Protokolu

### 1. Critical Alert - Endpoint Down

**Belirti:** Endpoint 3+ dakikadir yanit vermiyor

**Acil Adimlar:**
```bash
# 1. Endpoint durumunu kontrol et
curl -I https://api.kiro2.com/api/v1/endpoint

# 2. Container durumunu kontrol et
docker ps | grep kiro2-api

# 3. Loglari kontrol et
docker logs kiro2-api --tail 100

# 4. Pod durumunu kontrol et (k8s)
kubectl get pods -n production | grep api
kubectl describe pod <pod-name> -n production
```

**Cozum Adimlari:**
1. Container/pod restart
   ```bash
   docker restart kiro2-api
   # veya
   kubectl rollout restart deployment/api -n production
   ```
2. Olay kaydi olustur
3. Root cause analizi yap

---

### 2. High Response Time Alert

**Belirti:** P95 response time > 500ms

**Teshis Adimlari:**
```bash
# 1. Database baglanti havuzunu kontrol et
psql -h localhost -p 5434 -U kiro2 -c "SELECT count(*) FROM pg_stat_activity;"

# 2. Redis durumunu kontrol et
redis-cli -p 6379 INFO stats

# 3. CPU/Memory kullanımını kontrol et
htop
# veya k8s
kubectl top pods -n production
```

**Yaygin Nedenler:**
- Database slow query
- Redis cache miss
- Memory leak
- CPU throttling

**Cozum:**
1. Slow query'leri tespit et ve optimize et
2. Cache stratejisini gozden gecir
3. Kaynak limitlerini artir

---

### 3. Circuit Breaker Open

**Belirti:** Bir endpoint icin circuit breaker OPEN durumunda

**Kontrol:**
```python
# Python shell'de
from app.health.circuit_breaker import CircuitBreaker
cb = CircuitBreaker()
state = await cb.get_state("GET:/api/v1/problematic")
print(f"State: {state}, Failures: {cb.failures.get('GET:/api/v1/problematic', 0)}")
```

**Cozum:**
1. Altta yatan sorunu coz
2. Circuit breaker'in otomatik olarak HALF_OPEN'a gecmesini bekle (30s)
3. Veya manuel reset yap:
   ```python
   await cb.reset("GET:/api/v1/problematic")
   ```

---

### 4. Database Health Critical

**Belirti:** PostgreSQL baglantisi basarisiz

**Hizli Kontrol:**
```bash
# Baglanti testi
psql -h localhost -p 5434 -U kiro2 -c "SELECT 1;"

# Service durumu
systemctl status postgresql
# veya
docker exec kiro2-db pg_isready

# Baglanti sayisi
psql -h localhost -p 5434 -U kiro2 -c \
  "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
```

**Yaygin Sorunlar ve Cozumler:**

| Sorun | Cozum |
|-------|-------|
| Max connections | `SET max_connections = 200;` veya havuz boyutunu azalt |
| Disk full | Eski log/backup dosyalarini temizle |
| Deadlock | Blocking query'leri tespit et ve sonlandir |
| Replication lag | Replica sync durumunu kontrol et |

---

### 5. Redis Health Critical

**Belirti:** Redis baglantisi basarisiz veya memory critical

**Hizli Kontrol:**
```bash
# Baglanti testi
redis-cli -p 6379 PING

# Memory kullanimi
redis-cli -p 6379 INFO memory

# Slow log
redis-cli -p 6379 SLOWLOG GET 10
```

**Memory Yonetimi:**
```bash
# Buyuk key'leri bul
redis-cli -p 6379 --bigkeys

# TTL olmayan key'leri temizle (dikkatli!)
redis-cli -p 6379 SCAN 0 COUNT 100 | xargs -I {} redis-cli TTL {}

# Maxmemory policy kontrol
redis-cli -p 6379 CONFIG GET maxmemory-policy
```

---

## Periyodik Bakim Gorevleri

### Gunluk

- [ ] Health dashboard'u kontrol et
- [ ] Aktif alert'leri gozden gecir
- [ ] SLA raporunu incele

### Haftalik

- [ ] Response time trendlerini analiz et
- [ ] Error rate istatistiklerini gozden gecir
- [ ] Circuit breaker event'lerini incele
- [ ] Alerting esik degerlerini degerlendir

### Aylik

- [ ] SLA compliance raporunu olustur
- [ ] Capacity planning icin metrikleri analiz et
- [ ] Alert kurallarini optimize et
- [ ] Runbook'u guncelle

---

## Deployment Sonrasi Kontrol Listesi

### PostDeploy Hook Otomatik Kontroller

1. **Smoke Tests**
   - [ ] `/health` endpoint 200 donuyor
   - [ ] `/api/v1/auth/login` endpoint erisilebilir
   - [ ] Kritik endpoint'ler calisir durumda

2. **Response Time Kontrol**
   - [ ] P95 < 200ms (normal)
   - [ ] P99 < 500ms (acceptable)

3. **Error Rate Kontrol**
   - [ ] Error rate < 1%

### Manuel Kontroller

```bash
# 1. Deployment durumu
kubectl rollout status deployment/api -n production

# 2. Pod saglik durumu
kubectl get pods -n production -l app=api

# 3. Log kontrolu (son 5 dakika)
kubectl logs -l app=api -n production --since=5m | grep -i error

# 4. Health endpoint testi
for i in {1..5}; do
  curl -w "%{http_code}\n" -o /dev/null -s https://api.kiro2.com/health
  sleep 1
done
```

---

## Rollback Proseduru

### Otomatik Rollback (PostDeploy Hook)

PostDeploy hook smoke test basarisiz olursa otomatik rollback tetiklenir:

```bash
# Rollback loglarini kontrol et
kubectl logs -l app=postdeploy-hook -n production --tail 50
```

### Manuel Rollback

```bash
# 1. Mevcut revision'i kontrol et
kubectl rollout history deployment/api -n production

# 2. Onceki revision'a don
kubectl rollout undo deployment/api -n production

# 3. Belirli bir revision'a don
kubectl rollout undo deployment/api -n production --to-revision=5

# 4. Rollback durumunu takip et
kubectl rollout status deployment/api -n production
```

---

## Eskalasyon Matrisi

| Severity | Response Time | Eskalasyon |
|----------|--------------|------------|
| CRITICAL | 5 dakika | On-call → Team Lead → CTO |
| WARNING | 30 dakika | On-call → Team Lead |
| INFO | 2 saat | Ticket olustur |

### Iletisim Kanallari

1. **Slack:** #kiro2-alerts
2. **PagerDuty:** kiro2-oncall
3. **Email:** alerts@kiro2.com

---

## Metric Toplama ve Debugging

### Prometheus Queries

```promql
# Endpoint response time (P95)
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{job="kiro2-api"}[5m])
)

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m])) * 100

# Uptime
avg_over_time(up{job="kiro2-api"}[24h]) * 100
```

### Log Analysis

```bash
# Son 1 saatteki hatalari say
kubectl logs -l app=api -n production --since=1h | \
  grep -c "ERROR"

# En sik gorulen hatalar
kubectl logs -l app=api -n production --since=1h | \
  grep "ERROR" | \
  sort | uniq -c | sort -rn | head -10

# Yavas istekleri bul (>1s)
kubectl logs -l app=api -n production --since=1h | \
  grep "response_time" | \
  awk '$NF > 1000 {print}'
```

---

## Yapılandırma Referansi

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HEALTH_CHECK_INTERVAL` | 30 | Saniye cinsinden kontrol araligi |
| `CIRCUIT_FAILURE_THRESHOLD` | 5 | Circuit acmak icin hata sayisi |
| `CIRCUIT_RECOVERY_TIMEOUT` | 30 | Circuit recovery suresi (saniye) |
| `SLA_UPTIME_TARGET` | 99.0 | Hedef uptime yuzdesi |
| `SLA_RESPONSE_TIME_TARGET` | 200 | Hedef response time (ms) |
| `ALERT_COOLDOWN` | 300 | Alert cooldown suresi (saniye) |

### Konfigurasyon Dosyasi

```yaml
# config/health.yaml
health_check:
  interval: 30
  timeout: 10
  retry_count: 3

circuit_breaker:
  failure_threshold: 5
  recovery_timeout: 30
  half_open_max_calls: 3

sla:
  default_uptime: 99.0
  default_response_time_ms: 200
  default_error_rate: 1.0

alerting:
  channels:
    - type: slack
      webhook_url: ${SLACK_WEBHOOK_URL}
      severity_filter: [critical, warning]
    - type: email
      smtp_host: smtp.example.com
      recipients: [alerts@kiro2.com]
      severity_filter: [critical]
```

---

## SSS (Sik Sorulan Sorular)

**S: Circuit breaker ne zaman kapanir?**
C: Recovery timeout (30s) sonunda HALF_OPEN'a gecer. Basarili bir istek
gelirse CLOSED'a doner.

**S: Alert neden tekrar gonderilmiyor?**
C: Alert throttling aktif. Ayni alert 5 dakika icinde tekrar gonderilmez.
Cooldown suresini `ALERT_COOLDOWN` ile ayarlayabilirsiniz.

**S: Health score nasil hesaplaniyor?**
C: Response Time (%40) + Error Rate (%30) + Uptime (%20) + Dependencies (%10)
agirliklarla hesaplaniyor.

**S: Yeni endpoint otomatik izleniyor mu?**
C: Evet, EndpointDiscovery scheduler ile periyodik olarak yeni endpoint'leri
tespit eder ve izlemeye alir.
