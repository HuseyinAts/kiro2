# Health Monitoring Architecture

## Genel Bakis

KIRO2 Health Monitoring sistemi, tum API endpoint'lerinin sagligini izlemek,
SLA uyumluluğunu takip etmek ve kritik sorunlarda otomatik alert gondermek
icin tasarlanmistir.

## Mimari Diyagrami

```
┌──────────────────────────────────────────────────────────────────┐
│                     Health Monitoring System                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │
│  │  Endpoint   │───▶│   Health    │───▶│   SLA Monitor      │   │
│  │  Discovery  │    │   Checker   │    │   (Compliance)     │   │
│  └─────────────┘    └─────────────┘    └─────────────────────┘   │
│         │                  │                      │               │
│         │                  ▼                      │               │
│         │           ┌─────────────┐               │               │
│         │           │   Circuit   │               │               │
│         │           │   Breaker   │               │               │
│         │           └─────────────┘               │               │
│         │                  │                      │               │
│         ▼                  ▼                      ▼               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Health Score Calculator                 │    │
│  │         (Response Time + Error Rate + Uptime)           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                      │
│         ┌──────────────────┼──────────────────┐                  │
│         ▼                  ▼                  ▼                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   Alert     │    │  Dashboard  │    │   Redis     │          │
│  │   Manager   │    │    API      │    │   Cache     │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Notifiers (Slack, Email, SMS)               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

## Temel Bilesenler

### 1. Endpoint Discovery (`discovery.py`)

FastAPI uygulamasindan tum endpoint'leri otomatik olarak kesfecter.

**Ozellikler:**
- Runtime'da yeni endpoint tespiti
- Kritik endpoint isretlemesi (`/health`, `/auth/*`)
- Authentication gereksinimi tespiti
- Beklenen status code listesi cikarimi

**Kullanim:**
```python
from app.health.discovery import EndpointDiscovery

discovery = EndpointDiscovery(app)
endpoints = await discovery.discover_all_endpoints()
```

### 2. Health Checker (`checker.py`)

Endpoint'lere HTTP istekleri gondererek saglik durumunu kontrol eder.

**Ozellikler:**
- Async HTTP istekleri (httpx)
- Response time olcumu (ms)
- Status code dogrulamasi
- Sliding window percentile hesaplama (P50, P95, P99)

**Kullanim:**
```python
from app.health.checker import HealthChecker

checker = HealthChecker(base_url="http://localhost:8000")
result = await checker.check_endpoint(metadata)
```

### 3. Circuit Breaker (`circuit_breaker.py`)

Ardisik hatalarda endpoint'i gecici olarak devre disi birakir.

**State Machine:**
```
CLOSED ──[5 failures]──▶ OPEN ──[30s timeout]──▶ HALF_OPEN
   ▲                                                  │
   └──────────────[success]───────────────────────────┘
```

**Parametreler:**
- `failure_threshold`: 5 (varsayilan)
- `recovery_timeout`: 30 saniye (varsayilan)
- `half_open_max_calls`: 3 (varsayilan)

### 4. SLA Monitor (`sla_monitor.py`)

Service Level Agreement uyumlulugunu takip eder.

**Metrikler:**
- Uptime yüzdesi
- Response time (P95)
- Error rate

**Esik Degerleri:**
- Healthy: P95 < 200ms
- Degraded: 200ms <= P95 < 500ms
- Unhealthy: P95 >= 500ms

### 5. Health Score Calculator (`score_calculator.py`)

Tum metrikleri tek bir skora donusturur (0-100).

**Agirliklar:**
| Metrik | Agirlik |
|--------|---------|
| Response Time | 40% |
| Error Rate | 30% |
| Uptime | 20% |
| Dependencies | 10% |

**Formul:**
```
score = (response_score * 0.4) + (error_score * 0.3) +
        (uptime_score * 0.2) + (dependency_score * 0.1)
```

### 6. Alert Manager (`alerting/alert_manager.py`)

Esik degerlerine gore alert olusturur ve throttling uygular.

**Alert Seviyeleri:**
- CRITICAL: Hemen bildirim
- WARNING: 5 dakika cooldown
- INFO: 15 dakika cooldown

**Throttling:**
- Ayni alert 5 dakika icinde tekrar gonderilmez
- Cooldown suresi gecince sayac sifirlanir

### 7. Dependencies Health

#### Database Health (`dependencies/database_health.py`)
- SELECT 1 sorgusu ile baglanti testi
- Connection pool durumu
- Aktif baglanti sayisi

#### Redis Health (`dependencies/redis_health.py`)
- PING komutu ile baglanti testi
- Memory kullanimi
- Hit rate hesaplama

## Veri Akisi

1. **Scheduler** belirli araliklarla health check tetikler
2. **Discovery** endpoint listesini gunceller
3. **Circuit Breaker** durumuna gore check yapilip yapilmayacagini belirler
4. **Checker** endpoint'e istek gonderir ve sonucu kaydeder
5. **SLA Monitor** sonucu SLA hesaplamalarina ekler
6. **Score Calculator** tum sonuclari tek skora donusturur
7. **Alert Manager** esik asimlarinda alert olusturur
8. **Notifiers** alert'leri ilgili kanallara gonderir

## Redis Cache Stratejisi

**Key Formati:**
- Health sonuclari: `health:{method}:{path}`
- Endpoint metadata: `endpoint:{method}:{path}`
- Alert history: `alert:{endpoint}:{timestamp}`

**TTL Degerleri:**
- Health sonuclari: 5 dakika
- Endpoint metadata: 24 saat
- Alert history: 7 gun

## PostDeploy Hook

Deployment sonrasi otomatik dogrulama:

1. Kritik endpoint'lere smoke test
2. Response time kontrolu
3. Basarisiz olursa rollback tetikleme
4. Deployment raporu olusturma

## Guvenlik Notlari

- Health endpoint'ler authentication gerektirmez (`/health`)
- Dashboard API admin yetkisi gerektirir
- Hassas metrikler loglanmaz
- Rate limiting uygulanir (100 req/dakika)
