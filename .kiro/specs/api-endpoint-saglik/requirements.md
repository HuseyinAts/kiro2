# Requirements Document - API Endpoint Sağlık Doğrulama Sistemi

## Introduction

Bu spec, tüm FastAPI endpoint'lerinin sağlık durumunu sürekli izleyen ve doğrulayan sistemi tanımlar. Boris Cherny'nin verification feedback loops prensibi uygulanarak API güvenilirliği %99.9'a çıkarılacak ve downtime %95 azaltılacaktır. Sistem, her endpoint değişikliği sonrası otomatik health check yapar.

## Glossary

- **Health_Check_System**: Endpoint'lerin çalışır durumda olduğunu doğrulayan sistem
- **Discovery_System**: API endpoint'lerini otomatik keşfeden sistem bileşeni
- **SLA_Monitor**: Yanıt süresi hizmet seviyesi anlaşmasını izleyen bileşen (P95 < 200ms)
- **Circuit_Breaker**: Hatalı endpoint'leri otomatik devre dışı bırakan mekanizma
- **PostDeploy_Hook**: Deploy sonrası otomatik çalışan doğrulama hook'u
- **Health_Score**: 0-100 arası endpoint sağlık skoru
- **Degraded_State**: Endpoint'in kısmi çalışma durumu
- **Critical_Endpoint**: Sistem işleyişi için zorunlu olan endpoint

## Requirements

### Requirement 1: Otomatik Endpoint Discovery

**User Story:** As a DevOps engineer, I want tüm API endpoint'lerinin otomatik keşfedilmesini, so that manuel endpoint listesi tutmayayım.

#### Acceptance Criteria

1. **REQ-1.1** WHEN FastAPI uygulaması başlatıldığında, THE Discovery System SHALL tüm registered endpoint'leri tarar
2. **REQ-1.2** WHEN endpoint'ler tarandığında, THE System SHALL her endpoint'in path, method, ve handler bilgisini toplar
3. **REQ-1.3** WHEN yeni endpoint eklendiğinde, THE System SHALL otomatik olarak tespit eder
4. **REQ-1.4** WHEN endpoint silindiğinde, THE System SHALL monitoring listesinden çıkarır
5. **REQ-1.5** WHEN endpoint metadata toplandığında, THE System SHALL expected response time ve status code'ları kaydeder
6. **REQ-1.6** IF endpoint authentication gerektiriyorsa, THEN THE System SHALL auth requirement'ı işaretler

---

### Requirement 2: Sürekli Health Check

**User Story:** As a SRE, I want endpoint'lerin sürekli health check'ini, so that sorunları hemen tespit edeyim.

#### Acceptance Criteria

1. **REQ-2.1** WHEN health check çalıştığında, THE System SHALL her endpoint'e test request gönderir
2. **REQ-2.2** WHEN test request gönderildiğinde, THE System SHALL 30 saniye timeout uygular
3. **REQ-2.3** WHEN response alındığında, THE System SHALL status code'u kontrol eder (200-299 başarılı)
4. **REQ-2.4** WHEN response time ölçüldüğünde, THE System SHALL P50, P95, P99 metriklerini hesaplar
5. **REQ-2.5** WHEN health check tamamlandığında, THE System SHALL sonuçları Redis'e yazar
6. **REQ-2.6** WHEN kritik endpoint başarısız olduğunda, THE System SHALL anında alert gönderir

---

### Requirement 3: Response Time SLA Monitoring

**User Story:** As a product manager, I want API yanıt sürelerinin SLA'yı karşıladığını bilmek, so that kullanıcı deneyimi garantileyeyim.

#### Acceptance Criteria

1. **REQ-3.1** WHEN response time ölçüldüğünde, THE SLA Monitor SHALL P95 metriğini kontrol eder
2. **REQ-3.2** WHEN P95 < 200ms olduğunda, THE Monitor SHALL endpoint'i "healthy" olarak işaretler
3. **REQ-3.3** WHEN P95 200-500ms arasında olduğunda, THE Monitor SHALL endpoint'i "degraded" olarak işaretler
4. **REQ-3.4** WHEN P95 > 500ms olduğunda, THE Monitor SHALL endpoint'i "unhealthy" olarak işaretler
5. **REQ-3.5** WHEN SLA ihlali tespit edildiğinde, THE Monitor SHALL root cause analysis başlatır
6. **REQ-3.6** IF SLA ihlali 5 dakikadan uzun sürerse, THEN THE Monitor SHALL incident oluşturur

---

### Requirement 4: Circuit Breaker Pattern

**User Story:** As a backend developer, I want hatalı endpoint'lerin otomatik devre dışı bırakılmasını, so that cascade failure önlensin.

#### Acceptance Criteria

1. **REQ-4.1** WHEN bir endpoint 5 kez üst üste başarısız olduğunda, THE Circuit Breaker SHALL endpoint'i "open" durumuna alır
2. **REQ-4.2** WHEN circuit open durumda olduğunda, THE Breaker SHALL gelen istekleri hemen reddeder (503 Service Unavailable)
3. **REQ-4.3** WHEN 30 saniye geçtiğinde, THE Breaker SHALL "half-open" durumuna geçer
4. **REQ-4.4** WHEN half-open durumda test request başarılı olduğunda, THE Breaker SHALL circuit'i kapatır
5. **REQ-4.5** WHEN half-open durumda test request başarısız olduğunda, THE Breaker SHALL tekrar "open" durumuna döner
6. **REQ-4.6** WHEN circuit durumu değiştiğinde, THE Breaker SHALL durum değişikliğini loglar ve bildirim gönderir

---

### Requirement 5: Database Connection Health

**User Story:** As a DBA, I want database bağlantı sağlığının izlenmesini, so that connection pool sorunlarını tespit edeyim.

#### Acceptance Criteria

1. **REQ-5.1** WHEN database health check yapıldığında, THE System SHALL SELECT 1 query'si çalıştırır
2. **REQ-5.2** WHEN connection pool kontrol edildiğinde, THE System SHALL active/idle connection sayısını ölçer
3. **REQ-5.3** WHEN connection pool %90 dolu olduğunda, THE System SHALL uyarı verir
4. **REQ-5.4** WHEN query response time ölçüldüğünde, THE System SHALL < 50ms hedefler
5. **REQ-5.5** WHEN database unreachable olduğunda, THE System SHALL tüm DB-dependent endpoint'leri degraded yapar
6. **REQ-5.6** IF connection leak tespit edilirse, THEN THE System SHALL detaylı connection trace raporu oluşturur

---

### Requirement 6: Redis Cache Health

**User Story:** As a backend developer, I want Redis cache sağlığının izlenmesini, so that cache miss oranını optimize edeyim.

#### Acceptance Criteria

1. **REQ-6.1** WHEN Redis health check yapıldığında, THE System SHALL PING komutu gönderir
2. **REQ-6.2** WHEN cache metrics toplandığında, THE System SHALL hit rate, miss rate, eviction rate ölçer
3. **REQ-6.3** WHEN hit rate %70'in altında olduğunda, THE System SHALL cache stratejisini gözden geçirme önerir
4. **REQ-6.4** WHEN memory usage %90'ı aştığında, THE System SHALL eviction policy uyarısı verir
5. **REQ-6.5** WHEN Redis unreachable olduğunda, THE System SHALL cache bypass mode'a geçer
6. **REQ-6.6** WHEN cache recovery tamamlandığında, THE System SHALL cache warming işlemi başlatır

---

### Requirement 7: PostDeploy Verification

**User Story:** As a DevOps engineer, I want deploy sonrası otomatik doğrulama, so that broken deployment'ları hemen tespit edeyim.

#### Acceptance Criteria

1. **REQ-7.1** WHEN deployment tamamlandığında, THE PostDeploy Hook SHALL otomatik olarak tetiklenir
2. **REQ-7.2** WHEN hook tetiklendiğinde, THE Hook SHALL tüm kritik endpoint'lere smoke test yapar
3. **REQ-7.3** WHEN smoke test başarısız olduğunda, THE Hook SHALL deployment'ı rollback eder
4. **REQ-7.4** WHEN smoke test başarılı olduğunda, THE Hook SHALL full health check başlatır
5. **REQ-7.5** WHEN health check tamamlandığında, THE Hook SHALL deployment success/failure raporlar
6. **REQ-7.6** IF deployment başarısız olursa, THEN THE Hook SHALL incident ticket oluşturur ve team'i bilgilendirir

---

### Requirement 8: Health Dashboard ve Alerting

**User Story:** As a team lead, I want API sağlık durumunu görsel dashboard'da görmek, so that sistem durumunu hızlıca anlayayım.

#### Acceptance Criteria

1. **REQ-8.1** WHEN dashboard açıldığında, THE System SHALL tüm endpoint'lerin health score'unu gösterir
2. **REQ-8.2** WHEN endpoint detayı görüntülendiğinde, THE System SHALL response time grafiği, error rate, ve uptime gösterir
3. **REQ-8.3** WHEN alert kuralı tanımlandığında, THE System SHALL threshold-based alerting destekler
4. **REQ-8.4** WHEN alert tetiklendiğinde, THE System SHALL Slack/email/SMS ile bildirim gönderir
5. **REQ-8.5** WHEN historical data görüntülendiğinde, THE System SHALL son 30 günlük trend analizi gösterir
6. **REQ-8.6** WHEN SLA raporu oluşturulduğunda, THE System SHALL aylık uptime ve performance metriklerini raporlar

---

## Bağımlılıklar

- **FastAPI**: API framework
- **Redis**: Health check sonuçları cache
- **PostgreSQL**: Historical metrics storage
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboard
- **httpx**: Async HTTP client (health check için)
- **APScheduler**: Scheduled health checks

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 1 hafta
**Beklenen Uptime:** %99.9

## Health Check Flow

```
1. Sistem Başlatıldı / Deploy Tamamlandı
   ↓
2. Endpoint Discovery
   ├─ FastAPI route registry tarama
   ├─ Endpoint metadata toplama
   └─ Monitoring listesi oluşturma
   ↓
3. Sürekli Health Check (her 30 saniye)
   ├─ Test Request Gönderme
   ├─ Response Time Ölçümü
   ├─ Status Code Kontrolü
   └─ Error Rate Hesaplama
   ↓
4. Dependency Health Check
   ├─ PostgreSQL Connection (SELECT 1)
   ├─ Redis PING
   └─ External API Health
   ↓
5. SLA Monitoring
   ├─ P95 Response Time < 200ms?
   ├─ Error Rate < %1?
   └─ Uptime > %99.9?
   ↓
6. Circuit Breaker Logic
   ├─ 5 Consecutive Failures → OPEN
   ├─ 30s Wait → HALF-OPEN
   └─ Success → CLOSED
   ↓
7. Health Score Calculation (0-100)
   ├─ Response Time: 40%
   ├─ Error Rate: 30%
   ├─ Uptime: 20%
   └─ Dependency Health: 10%
   ↓
8. Alerting & Dashboard Update
   ├─ Score < 70 → Warning Alert
   ├─ Score < 50 → Critical Alert
   └─ Dashboard Real-time Update
```

## Success Metrics

1. **API Uptime:** >= %99.9
2. **P95 Response Time:** < 200ms
3. **Error Rate:** < %1
4. **MTTR (Mean Time To Recovery):** < 5 dakika
5. **False Positive Alert Rate:** < %5

