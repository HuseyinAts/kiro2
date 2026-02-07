# Requirements Document - Loop Guardrails Sistemi

## Introduction

Bu spec, AI agent infinite loop'larını önleyen guardrail sistemini tanımlar. maxTurns, timeout, circuit breaker ile %100 loop prevention sağlar.

## Glossary

- **Loop Guardrail**: Döngü koruma mekanizması
- **maxTurns**: Maksimum iterasyon sayısı
- **Timeout**: Zaman aşımı
- **Circuit Breaker**: Devre kesici
- **Infinite Loop**: Sonsuz döngü
- **Recursion Depth**: Özyineleme derinliği

## Requirements

### Requirement 1: maxTurns Enforcement
**User Story:** As a sistem yöneticisi, I want maksimum iterasyon sınırı, so that infinite loop önlensin.
#### Acceptance Criteria
1. **REQ-1.1** WHEN agent loop başladığında, THE System SHALL maxTurns counter başlatır
2. **REQ-1.2** WHEN her iterasyonda, THE System SHALL counter'ı increment eder
3. **REQ-1.3** WHEN counter maxTurns'e ulaştığında, THE System SHALL loop'u durdurur
4. **REQ-1.4** WHEN maxTurns aşıldığında, THE System SHALL partial result döner
5. **REQ-1.5** WHEN maxTurns config edildiğinde, THE System SHALL agent type'a göre farklı limit uygular
6. **REQ-1.6** WHEN maxTurns log tutulduğunda, THE System SHALL iteration count ve reason kaydeder

### Requirement 2: Timeout Management
**User Story:** As a developer, I want timeout mekanizması, so that uzun süren işlemler kesilsin.
#### Acceptance Criteria
1. **REQ-2.1** WHEN agent execution başladığında, THE System SHALL timeout timer başlatır
2. **REQ-2.2** WHEN timeout süresi dolduğunda, THE System SHALL execution'ı interrupt eder
3. **REQ-2.3** WHEN timeout config edildiğinde, THE System SHALL operation type'a göre farklı timeout uygular
4. **REQ-2.4** WHEN timeout warning verildiğinde, THE System SHALL %80 threshold'da uyarı verir
5. **REQ-2.5** WHEN graceful shutdown yapıldığında, THE System SHALL cleanup operations çalıştırır
6. **REQ-2.6** WHEN timeout log tutulduğunda, THE System SHALL elapsed time ve state kaydeder

### Requirement 3: Circuit Breaker Pattern
**User Story:** As a reliability engineer, I want circuit breaker, so that cascade failure önlensin.
#### Acceptance Criteria
1. **REQ-3.1** WHEN consecutive failure sayısı threshold'u aştığında, THE Circuit Breaker SHALL open olur
2. **REQ-3.2** WHEN circuit open olduğunda, THE Breaker SHALL yeni request'leri hemen reddeder
3. **REQ-3.3** WHEN timeout geçtiğinde, THE Breaker SHALL half-open state'e geçer
4. **REQ-3.4** WHEN half-open state'te success olduğunda, THE Breaker SHALL circuit'i kapatır
5. **REQ-3.5** WHEN half-open state'te failure olduğunda, THE Breaker SHALL tekrar open olur
6. **REQ-3.6** WHEN circuit state değiştiğinde, THE Breaker SHALL event emit eder

### Requirement 4: Recursion Depth Limit
**User Story:** As a developer, I want recursion depth limiti, so that stack overflow önlensin.
#### Acceptance Criteria
1. **REQ-4.1** WHEN recursive call yapıldığında, THE System SHALL depth counter increment eder
2. **REQ-4.2** WHEN depth limit aşıldığında, THE System SHALL RecursionError raise eder
3. **REQ-4.3** WHEN depth limit config edildiğinde, THE System SHALL Python sys.setrecursionlimit kullanır
4. **REQ-4.4** WHEN tail recursion optimize edildiğinde, THE System SHALL iteration'a çevirir
5. **REQ-4.5** WHEN recursion pattern tespit edildiğinde, THE System SHALL alternative approach önerir
6. **REQ-4.6** WHEN recursion log tutulduğunda, THE System SHALL call stack trace kaydeder

### Requirement 5: Progress Monitoring
**User Story:** As a user, I want işlem ilerlemesini görmek, so that takılıp takılmadığını anlayayım.
#### Acceptance Criteria
1. **REQ-5.1** WHEN long-running operation çalıştığında, THE System SHALL progress bar gösterir
2. **REQ-5.2** WHEN progress update edildiğinde, THE System SHALL percentage ve ETA hesaplar
3. **REQ-5.3** WHEN progress stall tespit edildiğinde, THE System SHALL warning verir
4. **REQ-5.4** WHEN progress callback kullanıldığında, THE System SHALL periodic update gönderir
5. **REQ-5.5** WHEN progress cancel edildiğinde, THE System SHALL graceful cancellation destekler
6. **REQ-5.6** WHEN progress complete olduğunda, THE System SHALL summary report gösterir

### Requirement 6: Resource Limit Enforcement
**User Story:** As a sistem yöneticisi, I want resource limitleri, so that resource exhaustion önlensin.
#### Acceptance Criteria
1. **REQ-6.1** WHEN memory usage ölçüldüğünde, THE System SHALL process memory monitor eder
2. **REQ-6.2** WHEN memory limit aşıldığında, THE System SHALL MemoryError raise eder
3. **REQ-6.3** WHEN CPU usage yüksek olduğunda, THE System SHALL throttling uygular
4. **REQ-6.4** WHEN disk space düşük olduğunda, THE System SHALL cleanup trigger eder
5. **REQ-6.5** WHEN network bandwidth limit aşıldığında, THE System SHALL rate limiting uygular
6. **REQ-6.6** WHEN resource quota aşıldığında, THE System SHALL alert gönderir

### Requirement 7: Deadlock Detection
**User Story:** As a developer, I want deadlock detection, so that stuck processes tespit edilsin.
#### Acceptance Criteria
1. **REQ-7.1** WHEN concurrent operations çalıştığında, THE System SHALL lock dependency graph oluşturur
2. **REQ-7.2** WHEN circular wait tespit edildiğinde, THE System SHALL deadlock alert verir
3. **REQ-7.3** WHEN deadlock resolution yapıldığında, THE System SHALL victim process seçer
4. **REQ-7.4** WHEN timeout-based detection kullanıldığında, THE System SHALL watchdog timer kullanır
5. **REQ-7.5** WHEN deadlock prevention yapıldığında, THE System SHALL lock ordering enforce eder
6. **REQ-7.6** WHEN deadlock log tutulduğunda, THE System SHALL lock acquisition order kaydeder

### Requirement 8: Emergency Stop Mechanism
**User Story:** As a operator, I want emergency stop, so that kritik durumlarda sistemi durdurayım.
#### Acceptance Criteria
1. **REQ-8.1** WHEN emergency stop trigger edildiğinde, THE System SHALL tüm running operations'ı durdurur
2. **REQ-8.2** WHEN stop signal gönderildiğinde, THE System SHALL SIGTERM ile graceful shutdown dener
3. **REQ-8.3** WHEN graceful shutdown başarısız olduğunda, THE System SHALL SIGKILL ile force kill yapar
4. **REQ-8.4** WHEN stop reason kaydedildiğinde, THE System SHALL incident log oluşturur
5. **REQ-8.5** WHEN recovery yapıldığında, THE System SHALL state restore eder
6. **REQ-8.6** WHEN post-mortem analiz yapıldığında, THE System SHALL root cause report oluşturur

## Bağımlılıklar
- **asyncio**: Async timeout
- **signal**: Signal handling
- **psutil**: Resource monitoring
- **threading**: Thread management
- **multiprocessing**: Process management

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 1 hafta
**Beklenen Loop Prevention:** %100

## Success Metrics
1. **Infinite Loop Prevention:** %100
2. **Timeout Accuracy:** >= %99
3. **Circuit Breaker Effectiveness:** >= %95
4. **Resource Exhaustion Prevention:** %100
5. **System Stability:** >= %99.9

