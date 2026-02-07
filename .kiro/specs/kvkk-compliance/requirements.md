# Requirements Document - KVKK Compliance

## Introduction

Bu spec, Kişisel Verilerin Korunması Kanunu (KVKK) uyumluluğunu sağlayan sistemi tanımlar. Consent management, data anonymization, audit logging ile %100 KVKK compliance sağlar.

## Glossary

- **KVKK**: Kişisel Verilerin Korunması Kanunu
- **Consent**: Rıza/onay
- **Anonymization**: Anonimleştirme
- **Data Subject**: Veri sahibi
- **Data Controller**: Veri sorumlusu
- **Right to Erasure**: Unutulma hakkı

## Requirements

### Requirement 1: Consent Management
**User Story:** As a veri sorumlusu, I want consent management, so that açık rıza alınsin.
#### Acceptance Criteria
1. **REQ-1.1** WHEN kullanıcı kaydolduğunda, THE System SHALL explicit consent form gösterir
2. **REQ-1.2** WHEN consent verildiğinde, THE System SHALL purpose, scope, duration belirtir
3. **REQ-1.3** WHEN consent kaydedildiğinde, THE System SHALL timestamp, IP, user agent saklar
4. **REQ-1.4** WHEN consent withdraw edildiğinde, THE System SHALL immediate effect sağlar
5. **REQ-1.5** WHEN consent history tutulduğunda, THE System SHALL audit trail oluşturur
6. **REQ-1.6** WHEN consent expire edildiğinde, THE System SHALL 1-year validity period uygular

### Requirement 2: Data Minimization
**User Story:** As a privacy officer, I want data minimization, so that sadece gerekli veri toplansin.
#### Acceptance Criteria
1. **REQ-2.1** WHEN veri toplandığında, THE System SHALL purpose limitation principle uygular
2. **REQ-2.2** WHEN optional field belirlediğinde, THE System SHALL mandatory vs optional ayırır
3. **REQ-2.3** WHEN data retention set edildiğinde, THE System SHALL purpose-based TTL kullanır
4. **REQ-2.4** WHEN excessive data tespit edildiğinde, THE System SHALL collection warning verir
5. **REQ-2.5** WHEN data inventory yapıldığında, THE System SHALL collected data catalog oluşturur
6. **REQ-2.6** WHEN data necessity validate edildiğinde, THE System SHALL legal basis check yapar

### Requirement 3: Data Anonymization
**User Story:** As a data scientist, I want anonymization, so that kişisel veri korunsin.
#### Acceptance Criteria
1. **REQ-3.1** WHEN PII tespit edildiğinde, THE System SHALL name, email, phone, TC no identify eder
2. **REQ-3.2** WHEN anonymization uygulandığında, THE System SHALL k-anonymity (k>=5) sağlar
3. **REQ-3.3** WHEN masking yapıldığında, THE System SHALL email: a***@example.com format kullanır
4. **REQ-3.4** WHEN pseudonymization uygulandığında, THE System SHALL reversible hash kullanır
5. **REQ-3.5** WHEN aggregation yapıldığında, THE System SHALL individual identification önler
6. **REQ-3.6** WHEN anonymization validate edildiğinde, THE System SHALL re-identification risk < %5 hedefler

### Requirement 4: Right to Access
**User Story:** As a veri sahibi, I want data access, so that verilerimi görebileyim.
#### Acceptance Criteria
1. **REQ-4.1** WHEN access request geldiğinde, THE System SHALL identity verification yapar
2. **REQ-4.2** WHEN data export edildiğinde, THE System SHALL machine-readable format (JSON) kullanır
3. **REQ-4.3** WHEN data scope belirlediğinde, THE System SHALL all personal data include eder
4. **REQ-4.4** WHEN response time limit edildiğinde, THE System SHALL 30-day deadline uygular
5. **REQ-4.5** WHEN access log tutulduğunda, THE System SHALL who, when, what kaydeder
6. **REQ-4.6** WHEN access frequency limit edildiğinde, THE System SHALL max 1 request per month uygular

### Requirement 5: Right to Erasure
**User Story:** As a veri sahibi, I want data deletion, so that unutulma hakkımı kullanayım.
#### Acceptance Criteria
1. **REQ-5.1** WHEN deletion request geldiğinde, THE System SHALL identity verification yapar
2. **REQ-5.2** WHEN data delete edildiğinde, THE System SHALL all copies (DB, backup, cache) temizler
3. **REQ-5.3** WHEN legal retention gerektiğinde, THE System SHALL exception apply eder
4. **REQ-5.4** WHEN deletion confirm edildiğinde, THE System SHALL confirmation email gönderir
5. **REQ-5.5** WHEN deletion log tutulduğunda, THE System SHALL audit trail oluşturur
6. **REQ-5.6** WHEN deletion deadline uygulandığında, THE System SHALL 30-day response time sağlar

### Requirement 6: Data Breach Notification
**User Story:** As a CISO, I want breach notification, so that ihlal bildirilsin.
#### Acceptance Criteria
1. **REQ-6.1** WHEN data breach tespit edildiğinde, THE System SHALL immediate alert trigger eder
2. **REQ-6.2** WHEN breach assess edildiğinde, THE System SHALL impact, scope, affected users belirler
3. **REQ-6.3** WHEN authority notification yapıldığında, THE System SHALL 72-hour deadline uygular
4. **REQ-6.4** WHEN user notification gerektiğinde, THE System SHALL affected user'lara email gönderir
5. **REQ-6.5** WHEN breach log tutulduğunda, THE System SHALL incident details kaydeder
6. **REQ-6.6** WHEN breach report oluşturulduğunda, THE System SHALL KVKK template kullanır

### Requirement 7: Data Processing Agreement
**User Story:** As a legal counsel, I want DPA, so that veri işleme sözleşmesi olsun.
#### Acceptance Criteria
1. **REQ-7.1** WHEN third-party processor kullanıldığında, THE System SHALL DPA requirement enforce eder
2. **REQ-7.2** WHEN DPA sign edildiğinde, THE System SHALL digital signature kullanır
3. **REQ-7.3** WHEN processor list tutulduğunda, THE System SHALL active processor inventory oluşturur
4. **REQ-7.4** WHEN sub-processor eklediğinde, THE System SHALL approval workflow trigger eder
5. **REQ-7.5** WHEN DPA audit yapıldığında, THE System SHALL compliance check yapar
6. **REQ-7.6** WHEN DPA expire edildiğinde, THE System SHALL renewal reminder gönderir

### Requirement 8: Audit and Compliance Reporting
**User Story:** As a compliance officer, I want audit reporting, so that uyumluluk raporlansin.
#### Acceptance Criteria
1. **REQ-8.1** WHEN audit log tutulduğunda, THE System SHALL all data access/modification kaydeder
2. **REQ-8.2** WHEN compliance report oluşturulduğunda, THE System SHALL monthly summary generate eder
3. **REQ-8.3** WHEN KVKK checklist validate edildiğinde, THE System SHALL all requirements check eder
4. **REQ-8.4** WHEN risk assessment yapıldığında, THE System SHALL DPIA (Data Protection Impact Assessment) çalıştırır
5. **REQ-8.5** WHEN audit trail export edildiğinde, THE System SHALL tamper-proof format kullanır
6. **REQ-8.6** WHEN compliance score hesaplandığında, THE System SHALL >= %95 compliance hedefler

## Bağımlılıklar
- **cryptography**: Encryption
- **hashlib**: Hashing
- **pydantic**: Data validation
- **sqlalchemy**: Database ORM
- **celery**: Background tasks

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 2 hafta
**Beklenen KVKK Compliance:** %100

## Success Metrics
1. **KVKK Compliance:** %100
2. **Consent Coverage:** %100
3. **Data Breach Response Time:** < 72 hours
4. **Anonymization Effectiveness:** >= %95
5. **Audit Trail Completeness:** %100
