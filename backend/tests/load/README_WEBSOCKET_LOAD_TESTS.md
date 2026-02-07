# WebSocket + HTTP Load Testing for KIRO2

Bu dizin, KIRO2 YKS sınav hazırlık platformu için WebSocket ve HTTP yük testlerini içerir.

## Test Dosyaları

### 1. `test_websocket_load.py`
Pytest entegrasyonlu ana WebSocket + HTTP yük test dosyası.

**Özellikler:**
- ✅ WebSocket + HTTP karma yük testi
- ✅ Türkçe içerik ile gerçekçi test senaryoları
- ✅ Pytest smoke test (CI/CD için)
- ✅ Performans assertionları (P95 < 500ms HTTP, WS connection < 2s)
- ✅ Otomatik requirement validation

**Kullanım:**

```bash
# Pytest ile smoke test (CI/CD)
pytest backend/tests/load/test_websocket_load.py -v

# Locust ile tam yük testi
locust -f backend/tests/load/test_websocket_load.py \
    --users 1000 \
    --spawn-rate 50 \
    --run-time 10m \
    --host http://localhost:8000

# Headless mode (production)
locust -f backend/tests/load/test_websocket_load.py \
    --users 1000 \
    --spawn-rate 50 \
    --run-time 10m \
    --host http://localhost:8000 \
    --headless \
    --csv=results/websocket_load
```

### 2. `locustfile_websocket.py`
CLI kullanımı için optimize edilmiş standalone locustfile.

**Özellikler:**
- ✅ 3 farklı user tipi (Student: 70%, Teacher: 20%, Stress: 10%)
- ✅ Gerçekçi YKS sınav senaryoları
- ✅ Türkçe soru ve cevap içerikleri
- ✅ WebSocket simülasyonu (HTTP long-polling ile)
- ✅ Detaylı performans raporlaması

**Kullanım:**

```bash
# Web UI ile (önerilen - ilk test için)
locust -f locustfile_websocket.py --host http://localhost:8000

# 1000 kullanıcı headless mode
locust -f locustfile_websocket.py \
    --users 1000 \
    --spawn-rate 50 \
    --run-time 10m \
    --host http://localhost:8000 \
    --headless \
    --csv=results/ws_1k

# Stress test - 5000 kullanıcı
locust -f locustfile_websocket.py \
    --users 5000 \
    --spawn-rate 100 \
    --run-time 30m \
    --host http://production.com \
    --headless \
    --csv=results/ws_stress_5k

# Quick smoke test
locust -f locustfile_websocket.py \
    --users 50 \
    --spawn-rate 10 \
    --run-time 2m \
    --host http://localhost:8000 \
    --headless
```

## Test Senaryoları

### 1. Exam Session Simulation (Ana Senaryo)
**Akış:**
1. Login (POST /api/v1/auth/giris)
2. Sınav konfigürasyonu al (GET /api/v1/osym-exam/exam-configs)
3. Sınav başlat (POST /api/v1/sinav/start)
4. WebSocket bağlantısı kur
5. Soruları al (WebSocket receive)
6. Cevapları gönder (WebSocket send)
7. Sınavı bitir (POST /api/v1/sinav/finish)
8. Sonuçları al (GET /api/v1/sinav/results)
9. WebSocket bağlantısını kapat

**Hedef:** Gerçek sınav deneyimini simüle eder.

### 2. Real-time Monitoring (Öğretmen)
**Akış:**
1. Öğretmen login
2. Sınıf analitiklerini görüntüle
3. Öğrenci ilerlemesini takip et
4. Ödev oluştur

**Hedef:** Öğretmen kullanım senaryolarını test eder.

### 3. Connection Stress Test
**Akış:**
- Hızlı bağlantı kurma
- Anında bağlantı kesme
- Döngüsel tekrar

**Hedef:** Connection pooling, resource cleanup, memory leak tespiti.

## Performans Gereksinimleri

| Metrik | Hedef | Açıklama |
|--------|-------|----------|
| HTTP P95 | < 500ms | HTTP endpoint yanıt süreleri |
| WebSocket Connection | < 2000ms | WS bağlantı kurma süresi |
| Message Latency | < 100ms | WS mesaj iletim gecikmesi |
| Success Rate | > 95% | Başarılı istek oranı |
| Concurrent Users | 1000 | Eşzamanlı kullanıcı (50K hedef) |

## WebSocket Simülasyonu

Locust'un native WebSocket desteği olmadığı için, WebSocket davranışı HTTP long-polling ile simüle edilir:

- **WS Connect:** `POST /api/v1/sinav/ws-connect`
- **WS Send:** `POST /api/v1/sinav/ws-send/{connection_id}`
- **WS Receive:** `GET /api/v1/sinav/ws-receive/{connection_id}`
- **WS Disconnect:** `DELETE /api/v1/sinav/ws-disconnect/{connection_id}`

## Türkçe İçerik

Testler gerçekçi Türkçe içerik kullanır:

- **Dersler:** Matematik, Fizik, Kimya, Biyoloji, Türkçe, Tarih, Coğrafya, Felsefe
- **Sınav Tipleri:** TYT, AYT, YDT, LGS
- **İsimler:** Ahmet, Mehmet, Ayşe, Fatma, Ali, Zeynep, vb.
- **Sorular:** Gerçek YKS tarzı sorular (UTF-8)

## CI/CD Entegrasyonu

### Pytest Smoke Test

```bash
# CI pipeline içinde
pytest backend/tests/load/test_websocket_load.py -v --timeout=300
```

Smoke test:
- 10 kullanıcı, 2 spawn rate
- 30 saniye çalışma süresi
- Failure rate < 50% (smoke test için)
- Health check başarı oranı > 50%

### GitHub Actions Örneği

```yaml
- name: WebSocket Load Test Smoke
  run: |
    cd backend
    pytest tests/load/test_websocket_load.py -v --timeout=300
```

## Sonuç Analizi

Test tamamlandıktan sonra şu metriklere bakın:

1. **Request Statistics:**
   - Total requests
   - Failure rate
   - RPS (requests per second)

2. **Response Times:**
   - Average, P50, P95, P99, Max

3. **Endpoint-Specific:**
   - Health check: < 500ms
   - WS Connect: < 2000ms
   - WS Send: < 100ms

4. **Requirement Validation:**
   - ✅/❌ Her requirement için PASS/FAIL

## Troubleshooting

### Health Check Fails
```bash
# Backend çalışıyor mu kontrol et
curl http://localhost:8000/health
```

### WebSocket Connection Errors
```bash
# WebSocket endpoint mevcut mu kontrol et
curl -X POST http://localhost:8000/api/v1/sinav/ws-connect \
  -H "Content-Type: application/json" \
  -d '{"exam_session_id": "test"}'
```

### Rate Limiting
Backend'de rate limiting varsa, `--spawn-rate` değerini azaltın:
```bash
locust -f locustfile_websocket.py --spawn-rate 10  # Daha yavaş
```

### Memory Issues
Çok fazla kullanıcı ile test ediyorsanız:
```bash
# Daha az kullanıcı ile başlayın
locust -f locustfile_websocket.py --users 100 --spawn-rate 10
```

## YASAK Patternler (Verification Rules)

❌ ASLA bu patternleri kullanmayın:

```python
# YASAK - Sahte testler
assert True
assert 1 == 1

# YASAK - Sahte başarı
print("Success")
echo Success

# YASAK - Boş implementasyon
pass  # placeholder
return None  # stub
```

✅ Her assertion anlamlı olmalı:

```python
# DOĞRU
assert total_requests > 0, "No requests were made"
assert failure_rate < 50, f"Failure rate too high: {failure_rate}%"
```

## Gelecek İyileştirmeler

1. **Native WebSocket:** Gerçek WebSocket kütüphanesi entegrasyonu (socketio-locust)
2. **50K Kullanıcı:** Distributed Locust ile 50K concurrent user testi
3. **Database Metrics:** PostgreSQL connection pool monitoring
4. **Redis Metrics:** Cache hit/miss rate tracking
5. **Prometheus Integration:** Real-time metrics export

## Referanslar

- [Locust Documentation](https://docs.locust.io/)
- [KIRO2 API Docs](../../api/)
- [Verification Rules](../../../.claude/rules/verification.md)
- [Testing Rules](../../../.claude/rules/testing.md)

---

**Not:** Bu testler KIRO2 platformunun gerçek YKS sınavlarını simüle eder ve Türkçe karakter desteği ile geliştirilmiştir (UTF-8).
