# Requirements Document - Performance Monitoring Hooks Sistemi

## Introduction

Bu spec, Daisy Stanton'ın hooks system expertise'ine göre tasarlanmış performans izleme hook'larını tanımlar. PostToolUse hook'ları ile API response time, database query performance, memory usage otomatik izlenir. Performans hedefleri (P95 < 200ms) %98 oranında karşılanır.

## Glossary

- **P50/P95/P99**: Percentile metrikleri (50th, 95th, 99th percentile)
- **Response Time**: API yanıt süresi
- **Query Performance**: Database sorgu performansı
- **Memory Profiling**: Bellek kullanım analizi
- **N+1 Query**: Verimli olmayan database query pattern'i
- **Slow Query Log**: Yavaş sorgu kaydı
- **Performance Budget**: Performans bütçesi

## Requirements

### Requirement 1: API Response Time Monitoring

**User Story:** As a backend developer, I want API endpoint'lerimin response time'ını izlemek, so that SLA'yı karşıladığımı biliyim.

#### Acceptance Criteria

1. **REQ-1.1** WHEN API endpoint çağrıldığında, THE PostToolUse Hook SHALL response time'ı ölçer
2. **REQ-1.2** WHEN response time ölçüldüğünde, THE Hook SHALL P50, P95, P99 metriklerini hesaplar
3. **REQ-1.3** WHEN P95 > 200ms olduğunda, THE Hook SHALL warning verir
4. **REQ-1.4** WHEN P95 > 500ms olduğunda, THE Hook SHALL exit code 2 döner (kritik)
5. **REQ-1.5** WHEN response time loglandığında, THE Hook SHALL X-Response-Time header'ı ekler
6. **REQ-1.6** WHEN trend analizi yapıldığında, THE Hook SHALL son 100 request'in ortalamasını hesaplar

---

### Requirement 2: Database Query Performance Monitoring

**User Story:** As a DBA, I want yavaş database query'lerinin tespit edilmesini, so that optimize edeyim.

#### Acceptance Criteria

1. **REQ-2.1** WHEN database query çalıştığında, THE Hook SHALL query execution time'ı ölçer
2. **REQ-2.2** WHEN query > 50ms sürdüğünde, THE Hook SHALL slow query olarak loglar
3. **REQ-2.3** WHEN query > 100ms sürdüğünde, THE Hook SHALL exit code 2 döner ve EXPLAIN ANALYZE önerir
4. **REQ-2.4** WHEN N+1 query tespit edildiğinde, THE Hook SHALL eager loading önerir
5. **REQ-2.5** WHEN SELECT * kullanıldığında, THE Hook SHALL specific column selection önerir
6. **REQ-2.6** WHEN query count yüksek olduğunda, THE Hook SHALL batch operation önerir

---

### Requirement 3: Memory Usage Profiling

**User Story:** As a developer, I want memory leak'lerin tespit edilmesini, so that production'da OOM error almayayım.

#### Acceptance Criteria

1. **REQ-3.1** WHEN fonksiyon çalıştığında, THE Hook SHALL memory usage'ı ölçer (before/after)
2. **REQ-3.2** WHEN memory increase > 100MB olduğunda, THE Hook SHALL warning verir
3. **REQ-3.3** WHEN memory leak pattern tespit edildiğinde, THE Hook SHALL objgraph ile referans analizi yapar
4. **REQ-3.4** WHEN large object oluşturulduğunda, THE Hook SHALL object size'ı raporlar
5. **REQ-3.5** WHEN generator kullanılabilir olduğunda, THE Hook SHALL list yerine generator önerir
6. **REQ-3.6** WHEN memory profiling aktif olduğunda, THE Hook SHALL memory_profiler decorator kullanır

---

### Requirement 4: N+1 Query Detection

**User Story:** As a backend developer, I want N+1 query problem'lerinin otomatik tespit edilmesini, so that database load azalsın.

#### Acceptance Criteria

1. **REQ-4.1** WHEN loop içinde query çalıştığında, THE Hook SHALL N+1 pattern tespit eder
2. **REQ-4.2** WHEN N+1 tespit edildiğinde, THE Hook SHALL query count ve loop iteration sayısını raporlar
3. **REQ-4.3** WHEN SQLAlchemy kullanıldığında, THE Hook SHALL joinedload() veya selectinload() önerir
4. **REQ-4.4** WHEN N+1 severity yüksek olduğunda, THE Hook SHALL exit code 2 döner
5. **REQ-4.5** WHEN fix suggestion sunulduğunda, THE Hook SHALL kod örneği gösterir
6. **REQ-4.6** WHEN N+1 fixed olduğunda, THE Hook SHALL query count azalmasını doğrular

---

### Requirement 5: Cache Hit Rate Monitoring

**User Story:** As a backend developer, I want cache effectiveness'ini izlemek, so that cache stratejisini optimize edeyim.

#### Acceptance Criteria

1. **REQ-5.1** WHEN cache access yapıldığında, THE Hook SHALL hit/miss durumunu loglar
2. **REQ-5.2** WHEN cache hit rate hesaplandığında, THE Hook SHALL hit / (hit + miss) formülünü kullanır
3. **REQ-5.3** WHEN hit rate < %70 olduğunda, THE Hook SHALL warning verir
4. **REQ-5.4** WHEN cache key pattern analiz edildiğinde, THE Hook SHALL ineffective key'leri tespit eder
5. **REQ-5.5** WHEN cache TTL optimize edildiğinde, THE Hook SHALL optimal TTL önerir
6. **REQ-5.6** WHEN cache eviction rate yüksek olduğunda, THE Hook SHALL cache size artırımı önerir

---

### Requirement 6: Async/Await Performance Check

**User Story:** As a developer, I want blocking I/O kullanımının tespit edilmesini, so that async performance'ı koruyayım.

#### Acceptance Criteria

1. **REQ-6.1** WHEN async function içinde sync I/O tespit edildiğinde, THE Hook SHALL warning verir
2. **REQ-6.2** WHEN requests library kullanıldığında, THE Hook SHALL httpx veya aiohttp önerir
3. **REQ-6.3** WHEN time.sleep() tespit edildiğinde, THE Hook SHALL asyncio.sleep() önerir
4. **REQ-6.4** WHEN blocking database call tespit edildiğinde, THE Hook SHALL async driver önerir
5. **REQ-6.5** WHEN event loop blocking ölçüldüğünde, THE Hook SHALL > 50ms blocking'i raporlar
6. **REQ-6.6** WHEN async best practice ihlali olduğunda, THE Hook SHALL exit code 2 döner

---

### Requirement 7: Performance Budget Enforcement

**User Story:** As a tech lead, I want performans bütçesinin zorlanmasını, so that performance regression önlensin.

#### Acceptance Criteria

1. **REQ-7.1** WHEN performance budget tanımlandığında, THE Hook SHALL .performance-budget.yml dosyasını okur
2. **REQ-7.2** WHEN budget aşıldığında, THE Hook SHALL exit code 2 döner ve CI/CD'yi başarısız yapar
3. **REQ-7.3** WHEN endpoint-specific budget kontrol edildiğinde, THE Hook SHALL her endpoint için ayrı limit uygular
4. **REQ-7.4** WHEN budget trend analizi yapıldığında, THE Hook SHALL son 7 günlük performans grafiği gösterir
5. **REQ-7.5** WHEN budget violation raporlandığında, THE Hook SHALL hangi metric'in aşıldığını belirtir
6. **REQ-7.6** WHEN budget güncellediğinde, THE Hook SHALL değişiklik gerekçesini commit message'da ister

---

### Requirement 8: Real-Time Performance Dashboard

**User Story:** As a DevOps engineer, I want performans metriklerini real-time görmek, so that sorunları hemen tespit edeyim.

#### Acceptance Criteria

1. **REQ-8.1** WHEN metrikler toplandığında, THE Hook SHALL Prometheus'a export eder
2. **REQ-8.2** WHEN dashboard görüntülendiğinde, THE Hook SHALL Grafana ile visualization sağlar
3. **REQ-8.3** WHEN alert rule tanımlandığında, THE Hook SHALL threshold-based alerting destekler
4. **REQ-8.4** WHEN anomaly tespit edildiğinde, THE Hook SHALL otomatik alert gönderir
5. **REQ-8.5** WHEN historical data sorgulandığında, THE Hook SHALL son 30 günlük data sağlar
6. **REQ-8.6** WHEN custom metric eklendiğinde, THE Hook SHALL metric registration API sağlar

---

## Bağımlılıklar

- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **memory_profiler**: Memory profiling
- **py-spy**: CPU profiling
- **SQLAlchemy**: Query monitoring
- **Redis**: Cache metrics
- **asyncio**: Async performance

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 1 hafta
**Beklenen SLA Karşılama:** %98

## Performance Monitoring Flow

```
1. API Request / Function Execution
   ↓
2. PostToolUse Hook Tetiklendi
   ↓
3. Performance Metrics Collection
   ├─ API Response Time
   │  ├─ Start Timer
   │  ├─ Execute Function
   │  ├─ Stop Timer
   │  └─ Calculate P50/P95/P99
   ├─ Database Query Performance
   │  ├─ Query Execution Time
   │  ├─ Slow Query Detection (> 50ms)
   │  └─ N+1 Query Detection
   ├─ Memory Usage
   │  ├─ Memory Before
   │  ├─ Memory After
   │  └─ Memory Leak Detection
   ├─ Cache Hit Rate
   │  ├─ Hit/Miss Tracking
   │  └─ Hit Rate Calculation
   └─ Async/Await Check
      ├─ Blocking I/O Detection
      └─ Event Loop Monitoring
   ↓
4. Performance Budget Check
   ├─ Compare with Budget (.performance-budget.yml)
   ├─ API Response Time <= 200ms (P95)?
   ├─ DB Query Time <= 50ms?
   ├─ Memory Increase <= 100MB?
   └─ Cache Hit Rate >= 70%?
   ↓
5. Result Evaluation
   ├─ All Budgets Met? → Exit 0 ✓
   └─ Budget Exceeded? → Exit 2 ✗
   ↓
6. Metrics Export
   ├─ Prometheus Metrics
   ├─ Grafana Dashboard Update
   └─ Alert Triggering (if threshold exceeded)
   ↓
7. Feedback to Developer
   ├─ Performance Report
   ├─ Optimization Suggestions
   └─ Code Examples
```

## Success Metrics

1. **API P95 Response Time:** < 200ms
2. **DB Query P95 Time:** < 50ms
3. **Cache Hit Rate:** >= %70
4. **Memory Leak Detection:** %100
5. **Performance Budget Compliance:** >= %98

## .performance-budget.yml Example

```yaml
global:
  api_response_time_p95: 200  # ms
  api_response_time_p99: 500  # ms
  db_query_time_p95: 50       # ms
  memory_increase_max: 100    # MB
  cache_hit_rate_min: 70      # %

endpoints:
  /api/v1/questions:
    response_time_p95: 150    # ms (stricter)
  
  /api/v1/exams:
    response_time_p95: 300    # ms (relaxed)
    db_query_time_p95: 100    # ms

database:
  max_query_count_per_request: 10
  n_plus_one_tolerance: 0

cache:
  redis_hit_rate_min: 75      # %
  eviction_rate_max: 10       # %
```

