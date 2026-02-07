# Requirements Document - Database Migration Doğrulama Sistemi

## Introduction

Bu spec, Alembic database migration'larının güvenli ve hatasız uygulanmasını garanti eden doğrulama sistemini tanımlar. Boris Cherny'nin verification feedback loops prensibi ile migration hataları %95 azaltılacak ve data loss riski sıfırlanacaktır. Her migration öncesi ve sonrası otomatik doğrulama yapılır.

## Glossary

- **Alembic**: SQLAlchemy için database migration tool'u
- **Migration**: Database şema değişikliği
- **Upgrade**: Migration'ı uygulama (forward)
- **Downgrade**: Migration'ı geri alma (rollback)
- **Revision**: Migration versiyonu
- **PreMigration Hook**: Migration öncesi çalışan hook
- **PostMigration Hook**: Migration sonrası çalışan hook
- **Dry Run**: Gerçek değişiklik yapmadan test çalıştırma
- **Data Integrity**: Veri bütünlüğü

## Requirements

### Requirement 1: PreMigration Validation

**User Story:** As a DBA, I want migration çalıştırmadan önce doğrulama yapılmasını, so that hatalı migration'ları önleyeyim.

#### Acceptance Criteria

1. **REQ-1.1** WHEN migration çalıştırılmak istendiğinde, THE PreMigration Hook SHALL otomatik olarak tetiklenir
2. **REQ-1.2** WHEN hook tetiklendiğinde, THE Hook SHALL mevcut database şemasını yedekler
3. **REQ-1.3** WHEN şema yedeklendiğinde, THE Hook SHALL pg_dump ile full backup alır
4. **REQ-1.4** WHEN migration script kontrol edildiğinde, THE Hook SHALL SQL syntax hatalarını tespit eder
5. **REQ-1.5** WHEN migration dependencies kontrol edildiğinde, THE Hook SHALL eksik dependency'leri tespit eder
6. **REQ-1.6** IF kritik hata tespit edilirse, THEN THE Hook SHALL migration'ı engeller ve detaylı rapor verir

---

### Requirement 2: Dry Run Testing

**User Story:** As a developer, I want migration'ı test ortamında denemek, so that production'da sorun çıkmasın.

#### Acceptance Criteria

1. **REQ-2.1** WHEN dry run başlatıldığında, THE System SHALL test database'inde migration çalıştırır
2. **REQ-2.2** WHEN test database oluşturulduğunda, THE System SHALL production'ın exact kopyasını kullanır
3. **REQ-2.3** WHEN migration test edildiğinde, THE System SHALL upgrade ve downgrade'i sırayla test eder
4. **REQ-2.4** WHEN test tamamlandığında, THE System SHALL execution time ve affected rows raporlar
5. **REQ-2.5** WHEN test başarılı olduğunda, THE System SHALL yeşil onay verir
6. **REQ-2.6** IF test başarısız olursa, THEN THE System SHALL hata detayını ve stack trace'i gösterir

---

### Requirement 3: Schema Consistency Check

**User Story:** As a backend developer, I want SQLAlchemy model'ların database şeması ile uyumlu olduğunu bilmek, so that ORM hataları almayayım.

#### Acceptance Criteria

1. **REQ-3.1** WHEN schema consistency kontrol edildiğinde, THE System SHALL SQLAlchemy metadata'yı database şeması ile karşılaştırır
2. **REQ-3.2** WHEN tablo kontrol edildiğinde, THE System SHALL eksik/fazla tabloları tespit eder
3. **REQ-3.3** WHEN kolon kontrol edildiğinde, THE System SHALL kolon tipi, nullable, default value uyumsuzluklarını tespit eder
4. **REQ-3.4** WHEN index kontrol edildiğinde, THE System SHALL eksik/fazla index'leri tespit eder
5. **REQ-3.5** WHEN foreign key kontrol edildiğinde, THE System SHALL referential integrity sorunlarını tespit eder
6. **REQ-3.6** IF uyumsuzluk tespit edilirse, THEN THE System SHALL otomatik migration script önerir

---

### Requirement 4: Data Integrity Validation

**User Story:** As a DBA, I want migration sonrası veri bütünlüğünün korunduğunu bilmek, so that data loss yaşamayayım.

#### Acceptance Criteria

1. **REQ-4.1** WHEN migration tamamlandığında, THE Integrity Validator SHALL row count'ları karşılaştırır
2. **REQ-4.2** WHEN row count kontrol edildiğinde, THE Validator SHALL her tablo için before/after count'u karşılaştırır
3. **REQ-4.3** WHEN foreign key integrity kontrol edildiğinde, THE Validator SHALL orphaned record'ları tespit eder
4. **REQ-4.4** WHEN unique constraint kontrol edildiğinde, THE Validator SHALL duplicate record'ları tespit eder
5. **REQ-4.5** WHEN not null constraint kontrol edildiğinde, THE Validator SHALL null value ihlallerini tespit eder
6. **REQ-4.6** IF integrity ihlali tespit edilirse, THEN THE Validator SHALL otomatik rollback tetikler

---

### Requirement 5: Rollback Safety

**User Story:** As a DevOps engineer, I want migration'ı güvenli şekilde geri alabilmek, so that sorun çıktığında hızlıca düzelteyim.

#### Acceptance Criteria

1. **REQ-5.1** WHEN rollback gerektiğinde, THE System SHALL alembic downgrade komutunu çalıştırır
2. **REQ-5.2** WHEN downgrade çalıştırıldığında, THE System SHALL önce dry run test yapar
3. **REQ-5.3** WHEN rollback tamamlandığında, THE System SHALL data integrity check yapar
4. **REQ-5.4** WHEN rollback başarılı olduğunda, THE System SHALL önceki şema state'ine döner
5. **REQ-5.5** WHEN rollback başarısız olduğunda, THE System SHALL backup'tan restore eder
6. **REQ-5.6** IF rollback mümkün değilse, THEN THE System SHALL manual intervention gerektiğini bildirir

---

### Requirement 6: Migration History Tracking

**User Story:** As a tech lead, I want tüm migration geçmişini görmek, so that şema evrimini takip edeyim.

#### Acceptance Criteria

1. **REQ-6.1** WHEN migration çalıştırıldığında, THE History Tracker SHALL migration detaylarını kaydeder
2. **REQ-6.2** WHEN history kaydedildiğinde, THE Tracker SHALL revision, timestamp, author, description, execution time kaydeder
3. **REQ-6.3** WHEN migration başarısız olduğunda, THE Tracker SHALL hata detayını ve rollback bilgisini kaydeder
4. **REQ-6.4** WHEN history sorgulandığında, THE Tracker SHALL filtreleme ve arama destekler
5. **REQ-6.5** WHEN migration chain görüntülendiğinde, THE Tracker SHALL dependency graph gösterir
6. **REQ-6.6** WHEN audit raporu oluşturulduğunda, THE Tracker SHALL compliance için detaylı log sağlar

---

### Requirement 7: Performance Impact Analysis

**User Story:** As a DBA, I want migration'ın performans etkisini bilmek, so that production'da yavaşlama yaşamayayım.

#### Acceptance Criteria

1. **REQ-7.1** WHEN migration analiz edildiğinde, THE Performance Analyzer SHALL EXPLAIN ANALYZE çalıştırır
2. **REQ-7.2** WHEN execution plan incelendiğinde, THE Analyzer SHALL table lock sürelerini tahmin eder
3. **REQ-7.3** WHEN affected rows hesaplandığında, THE Analyzer SHALL migration süresini tahmin eder
4. **REQ-7.4** WHEN index oluşturulduğunda, THE Analyzer SHALL CONCURRENTLY option kullanımını önerir
5. **REQ-7.5** WHEN büyük tablo değiştiğinde, THE Analyzer SHALL downtime uyarısı verir
6. **REQ-7.6** IF migration 5 dakikadan uzun sürecekse, THEN THE Analyzer SHALL maintenance window önerir

---

### Requirement 8: Automated Testing Integration

**User Story:** As a QA engineer, I want migration'ların CI/CD pipeline'da test edilmesini, so that broken migration'lar merge edilmesin.

#### Acceptance Criteria

1. **REQ-8.1** WHEN PR oluşturulduğunda, THE CI Pipeline SHALL migration testlerini otomatik çalıştırır
2. **REQ-8.2** WHEN migration test edildiğinde, THE Pipeline SHALL temiz database'den başlar
3. **REQ-8.3** WHEN test çalıştığında, THE Pipeline SHALL tüm migration'ları sırayla uygular
4. **REQ-8.4** WHEN test tamamlandığında, THE Pipeline SHALL downgrade testini de yapar
5. **REQ-8.5** WHEN test başarısız olduğunda, THE Pipeline SHALL PR'ı block eder
6. **REQ-8.6** IF test başarılı olursa, THEN THE Pipeline SHALL merge approval verir

---

## Bağımlılıklar

- **Alembic**: Migration tool
- **SQLAlchemy**: ORM
- **PostgreSQL**: Database
- **pg_dump**: Backup tool
- **pytest**: Test framework
- **GitHub Actions**: CI/CD
- **Redis**: Migration lock için

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 1 hafta
**Beklenen Hata Azalması:** %95

## Migration Verification Flow

```
1. Migration Script Oluşturuldu
   ↓
2. PreMigration Hook Tetiklendi
   ↓
3. Validation Checks
   ├─ SQL Syntax Check
   ├─ Dependency Check
   └─ Schema Consistency Check
   ↓
4. Backup Creation
   ├─ pg_dump Full Backup
   └─ Backup Verification
   ↓
5. Dry Run Testing
   ├─ Test DB Oluşturma
   ├─ Migration Uygulama
   ├─ Downgrade Test
   └─ Performance Analysis
   ↓
6. Production Migration
   ├─ Migration Lock (Redis)
   ├─ Upgrade Execution
   └─ Execution Time Monitoring
   ↓
7. PostMigration Validation
   ├─ Data Integrity Check
   ├─ Row Count Verification
   ├─ Foreign Key Check
   └─ Constraint Validation
   ↓
8. History Recording
   ├─ Migration Metadata
   ├─ Execution Metrics
   └─ Success/Failure Status
   ↓
9. Validation Başarılı?
   ├─ EVET → Migration Tamamlandı ✓
   └─ HAYIR → Otomatik Rollback ✗
```

## Success Metrics

1. **Migration Success Rate:** >= %99
2. **Data Loss Incidents:** 0
3. **Rollback Success Rate:** >= %100
4. **Average Migration Time:** < 30 saniye
5. **Schema Consistency:** %100

