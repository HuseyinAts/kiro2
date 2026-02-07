# Requirements Document - Filesystem MCP Sistemi

## Introduction

Bu spec, dosya sistemi operasyonlarını MCP server üzerinden güvenli şekilde yapan sistemi tanımlar. Sandbox environment ile %100 güvenli dosya erişimi sağlar.

## Glossary

- **Filesystem MCP**: Dosya sistemi MCP server
- **Sandbox**: İzole çalışma ortamı
- **Path Traversal**: Dizin gezinme saldırısı
- **Whitelist**: İzin verilen path listesi
- **File Operations**: Dosya işlemleri (read, write, delete)

## Requirements

### Requirement 1: Secure File Read
**User Story:** As a AI agent, I want dosya okumak, so that kod analizi yapabiliyim.
#### Acceptance Criteria
1. **REQ-1.1** WHEN dosya okunduğunda, THE System SHALL path traversal attack kontrol eder
2. **REQ-1.2** WHEN whitelist kontrol edildiğinde, THE System SHALL sadece workspace içi dosyalara izin verir
3. **REQ-1.3** WHEN binary dosya tespit edildiğinde, THE System SHALL encoding error önler
4. **REQ-1.4** WHEN büyük dosya okunduğunda, THE System SHALL streaming read kullanır
5. **REQ-1.5** WHEN dosya bulunamadığında, THE System SHALL descriptive error verir
6. **REQ-1.6** WHEN permission denied olduğunda, THE System SHALL security log tutar

### Requirement 2: Safe File Write
**User Story:** As a AI agent, I want dosya yazmak, so that kod üretebiliyim.
#### Acceptance Criteria
1. **REQ-2.1** WHEN dosya yazıldığında, THE System SHALL backup oluşturur
2. **REQ-2.2** WHEN overwrite yapıldığında, THE System SHALL confirmation ister
3. **REQ-2.3** WHEN atomic write yapıldığında, THE System SHALL temp file + rename kullanır
4. **REQ-2.4** WHEN disk space kontrol edildiğinde, THE System SHALL minimum 100MB free space bekler
5. **REQ-2.5** WHEN write başarısız olduğunda, THE System SHALL rollback yapar
6. **REQ-2.6** WHEN sensitive file yazıldığında, THE System SHALL .gitignore'a ekler

### Requirement 3: Directory Operations
**User Story:** As a AI agent, I want dizin işlemleri yapmak, so that proje yapısı oluşturayım.
#### Acceptance Criteria
1. **REQ-3.1** WHEN dizin oluşturulduğunda, THE System SHALL parent directories'i otomatik oluşturur
2. **REQ-3.2** WHEN dizin listelediğinde, THE System SHALL hidden files'ı filtreler
3. **REQ-3.3** WHEN recursive list yapıldığında, THE System SHALL max depth limit uygular
4. **REQ-3.4** WHEN dizin silindiğinde, THE System SHALL non-empty directory uyarısı verir
5. **REQ-3.5** WHEN dizin taşındığında, THE System SHALL cross-device move destekler
6. **REQ-3.6** WHEN dizin permission kontrol edildiğinde, THE System SHALL rwx check yapar

### Requirement 4: File Search
**User Story:** As a AI agent, I want dosya aramak, so that ilgili dosyaları bulabiliyim.
#### Acceptance Criteria
1. **REQ-4.1** WHEN dosya aranırken, THE System SHALL glob pattern destekler
2. **REQ-4.2** WHEN regex search yapıldığında, THE System SHALL content search yapar
3. **REQ-4.3** WHEN file type filter uygulandığında, THE System SHALL extension-based filter kullanır
4. **REQ-4.4** WHEN size filter uygulandığında, THE System SHALL min/max size destekler
5. **REQ-4.5** WHEN modified date filter uygulandığında, THE System SHALL date range destekler
6. **REQ-4.6** WHEN search results limit edildiğinde, THE System SHALL top 100 result döner

### Requirement 5: File Metadata
**User Story:** As a AI agent, I want dosya metadata'sını okumak, so that dosya hakkında bilgi alayım.
#### Acceptance Criteria
1. **REQ-5.1** WHEN metadata okunduğunda, THE System SHALL size, modified_time, created_time, permissions döner
2. **REQ-5.2** WHEN file type tespit edildiğinde, THE System SHALL MIME type kullanır
3. **REQ-5.3** WHEN encoding tespit edildiğinde, THE System SHALL chardet library kullanır
4. **REQ-5.4** WHEN line count hesaplandığında, THE System SHALL efficient counting yapar
5. **REQ-5.5** WHEN checksum hesaplandığında, THE System SHALL SHA256 kullanır
6. **REQ-5.6** WHEN git info eklendiğinde, THE System SHALL last commit, author, date ekler

### Requirement 6: Temporary File Management
**User Story:** As a AI agent, I want geçici dosya oluşturmak, so that intermediate results saklayayım.
#### Acceptance Criteria
1. **REQ-6.1** WHEN temp file oluşturulduğunda, THE System SHALL /tmp veya system temp dir kullanır
2. **REQ-6.2** WHEN temp file cleanup yapıldığında, THE System SHALL automatic cleanup sağlar
3. **REQ-6.3** WHEN temp file TTL belirlendiğinde, THE System SHALL 1 saat sonra siler
4. **REQ-6.4** WHEN temp file prefix kullanıldığında, THE System SHALL kiro2_temp_ prefix ekler
5. **REQ-6.5** WHEN temp file security sağlandığında, THE System SHALL 0600 permission kullanır
6. **REQ-6.6** WHEN temp file tracking yapıldığında, THE System SHALL active temp files listeler

### Requirement 7: File Watching
**User Story:** As a AI agent, I want dosya değişikliklerini izlemek, so that otomatik işlem tetikleyeyim.
#### Acceptance Criteria
1. **REQ-7.1** WHEN file watch başlatıldığında, THE System SHALL watchdog library kullanır
2. **REQ-7.2** WHEN file modified olduğunda, THE System SHALL event trigger eder
3. **REQ-7.3** WHEN debounce uygulandığında, THE System SHALL 500ms debounce kullanır
4. **REQ-7.4** WHEN watch pattern belirlendiğinde, THE System SHALL glob pattern destekler
5. **REQ-7.5** WHEN watch stop edildiğinde, THE System SHALL cleanup yapar
6. **REQ-7.6** WHEN watch error olduğunda, THE System SHALL graceful restart yapar

### Requirement 8: Security ve Audit
**User Story:** As a security engineer, I want dosya işlemlerinin audit edilmesini, so that güvenlik takip edeyim.
#### Acceptance Criteria
1. **REQ-8.1** WHEN dosya işlemi yapıldığında, THE System SHALL operation, path, user, timestamp loglar
2. **REQ-8.2** WHEN suspicious activity tespit edildiğinde, THE System SHALL alert gönderir
3. **REQ-8.3** WHEN rate limiting uygulandığında, THE System SHALL 100 operations/min limit koyar
4. **REQ-8.4** WHEN blacklist kontrol edildiğinde, THE System SHALL .env, .git, node_modules erişimini engeller
5. **REQ-8.5** WHEN audit log tutulduğunda, THE System SHALL tamper-proof logging sağlar
6. **REQ-8.6** WHEN compliance check yapıldığında, THE System SHALL GDPR/KVKK uyumlu olur

## Bağımlılıklar
- **watchdog**: File watching
- **chardet**: Encoding detection
- **pathlib**: Path operations
- **tempfile**: Temporary file management

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P2 (Orta)
**Tahmini Süre:** 3 gün
**Beklenen Güvenlik:** %100

## Success Metrics
1. **Security Incidents:** 0
2. **Path Traversal Prevention:** %100
3. **Operation Success Rate:** >= %99
4. **Audit Log Completeness:** %100
5. **Performance:** < 50ms per operation

