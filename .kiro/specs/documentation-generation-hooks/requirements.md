# Requirements Document - Documentation Generation Hooks Sistemi

## Introduction

Bu spec, kod değişikliklerinden otomatik dokümantasyon üreten hook sistemini tanımlar. PostToolUse hook'ları ile API docs, README, ve code comments otomatik güncellenir. Dokümantasyon güncelliği %95'e çıkar.

## Glossary

- **Auto-doc**: Otomatik dokümantasyon
- **OpenAPI**: REST API dokümantasyon standardı
- **Docstring**: Python fonksiyon dokümantasyonu
- **Markdown**: Dokümantasyon formatı
- **MkDocs**: Dokümantasyon site generator

## Requirements

### Requirement 1: API Documentation Auto-Generation
**User Story:** As a API consumer, I want güncel API dokümantasyonu, so that endpoint'leri doğru kullanayım.
#### Acceptance Criteria
1. **REQ-1.1** WHEN FastAPI endpoint değiştiğinde, THE Hook SHALL OpenAPI spec'i otomatik günceller
2. **REQ-1.2** WHEN OpenAPI güncellediğinde, THE Hook SHALL Swagger UI'ı yeniler
3. **REQ-1.3** WHEN request/response model değiştiğinde, THE Hook SHALL schema documentation günceller
4. **REQ-1.4** WHEN endpoint eklendiğinde, THE Hook SHALL README.md'ye endpoint listesi ekler
5. **REQ-1.5** WHEN deprecation yapıldığında, THE Hook SHALL @deprecated decorator ve warning ekler
6. **REQ-1.6** WHEN API versioning olduğunda, THE Hook SHALL version-specific docs oluşturur

### Requirement 2: README Auto-Update
**User Story:** As a developer, I want README'nin otomatik güncellenmesini, so that proje dokümantasyonu güncel kalsın.
#### Acceptance Criteria
1. **REQ-2.1** WHEN yeni feature eklendiğinde, THE Hook SHALL README.md'ye feature section ekler
2. **REQ-2.2** WHEN dependency değiştiğinde, THE Hook SHALL requirements section günceller
3. **REQ-2.3** WHEN environment variable eklendiğinde, THE Hook SHALL .env.example ve README günceller
4. **REQ-2.4** WHEN setup adımı değiştiğinde, THE Hook SHALL installation section günceller
5. **REQ-2.5** WHEN badge eklendiğinde, THE Hook SHALL README header'a badge ekler
6. **REQ-2.6** WHEN changelog güncellendiğinde, THE Hook SHALL semantic versioning uygular

### Requirement 3: Code Comment Generation
**User Story:** As a developer, I want karmaşık kod bloklarına otomatik comment eklenmesini, so that kod anlaşılır olsun.
#### Acceptance Criteria
1. **REQ-3.1** WHEN karmaşık fonksiyon tespit edildiğinde, THE Hook SHALL AI ile comment önerir
2. **REQ-3.2** WHEN algorithm implementasyonu olduğunda, THE Hook SHALL step-by-step comment ekler
3. **REQ-3.3** WHEN magic number tespit edildiğinde, THE Hook SHALL açıklayıcı constant önerir
4. **REQ-3.4** WHEN regex pattern olduğunda, THE Hook SHALL pattern açıklaması ekler
5. **REQ-3.5** WHEN business logic olduğunda, THE Hook SHALL why comment (not what) önerir
6. **REQ-3.6** WHEN comment quality kontrol edildiğinde, THE Hook SHALL meaningless comment'leri tespit eder

### Requirement 4: Docstring Completeness Check
**User Story:** As a tech lead, I want tüm public fonksiyonların tam docstring'e sahip olmasını, so that API dokümante edilsin.
#### Acceptance Criteria
1. **REQ-4.1** WHEN public fonksiyon yazıldığında, THE Hook SHALL Google style docstring ister
2. **REQ-4.2** WHEN docstring eksik olduğunda, THE Hook SHALL AI ile docstring template önerir
3. **REQ-4.3** WHEN parameter dokümante edilmediğinde, THE Hook SHALL Args section ister
4. **REQ-4.4** WHEN return type dokümante edilmediğinde, THE Hook SHALL Returns section ister
5. **REQ-4.5** WHEN exception raise edildiğinde, THE Hook SHALL Raises section ister
6. **REQ-4.6** WHEN docstring coverage < %90 olduğunda, THE Hook SHALL warning verir

### Requirement 5: MkDocs Site Generation
**User Story:** As a documentation maintainer, I want otomatik documentation site oluşturulmasını, so that searchable docs olsun.
#### Acceptance Criteria
1. **REQ-5.1** WHEN docs/ dizini değiştiğinde, THE Hook SHALL mkdocs build çalıştırır
2. **REQ-5.2** WHEN build tamamlandığında, THE Hook SHALL site/ dizinine static site oluşturur
3. **REQ-5.3** WHEN navigation güncellediğinde, THE Hook SHALL mkdocs.yml'i otomatik düzenler
4. **REQ-5.4** WHEN search index oluşturulduğunda, THE Hook SHALL Türkçe stemming uygular
5. **REQ-5.5** WHEN deployment yapıldığında, THE Hook SHALL GitHub Pages'e publish eder
6. **REQ-5.6** WHEN broken link tespit edildiğinde, THE Hook SHALL link validation yapar

### Requirement 6: Changelog Auto-Generation
**User Story:** As a product manager, I want otomatik changelog oluşturulmasını, so that release notes hazır olsun.
#### Acceptance Criteria
1. **REQ-6.1** WHEN commit yapıldığında, THE Hook SHALL conventional commit format kontrol eder
2. **REQ-6.2** WHEN release tag oluşturulduğunda, THE Hook SHALL CHANGELOG.md günceller
3. **REQ-6.3** WHEN changelog kategorize edildiğinde, THE Hook SHALL feat/fix/breaking/chore ayırır
4. **REQ-6.4** WHEN semantic version hesaplandığında, THE Hook SHALL major/minor/patch belirler
5. **REQ-6.5** WHEN release notes oluşturulduğunda, THE Hook SHALL GitHub Release oluşturur
6. **REQ-6.6** WHEN migration guide gerektiğinde, THE Hook SHALL breaking change dokümante eder

### Requirement 7: Architecture Diagram Auto-Update
**User Story:** As a architect, I want mimari diyagramların otomatik güncellenmesini, so that architecture docs güncel kalsın.
#### Acceptance Criteria
1. **REQ-7.1** WHEN yeni service eklendiğinde, THE Hook SHALL architecture.md'ye service ekler
2. **REQ-7.2** WHEN dependency değiştiğinde, THE Hook SHALL dependency graph günceller
3. **REQ-7.3** WHEN mermaid diagram kullanıldığında, THE Hook SHALL diagram syntax validate eder
4. **REQ-7.4** WHEN C4 model uygulandığında, THE Hook SHALL context/container/component diagram'ları günceller
5. **REQ-7.5** WHEN API flow değiştiğinde, THE Hook SHALL sequence diagram günceller
6. **REQ-7.6** WHEN database schema değiştiğinde, THE Hook SHALL ER diagram günceller

### Requirement 8: Documentation Quality Metrics
**User Story:** As a documentation lead, I want dokümantasyon kalitesini ölçmek, so that improvement alanlarını belirleyeyim.
#### Acceptance Criteria
1. **REQ-8.1** WHEN docs analiz edildiğinde, THE Hook SHALL coverage, freshness, ve readability ölçer
2. **REQ-8.2** WHEN coverage hesaplandığında, THE Hook SHALL documented / total items oranını hesaplar
3. **REQ-8.3** WHEN freshness kontrol edildiğinde, THE Hook SHALL last_updated timestamp'i kontrol eder
4. **REQ-8.4** WHEN readability skorlandığında, THE Hook SHALL Flesch Reading Ease kullanır
5. **REQ-8.5** WHEN broken link tespit edildiğinde, THE Hook SHALL link health score hesaplar
6. **REQ-8.6** WHEN quality report oluşturulduğunda, THE Hook SHALL improvement suggestions verir

## Bağımlılıklar
- **FastAPI**: OpenAPI generation
- **MkDocs**: Documentation site
- **Pydantic**: Schema documentation
- **Mermaid**: Diagram generation
- **conventional-changelog**: Changelog generation

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P2 (Orta)
**Tahmini Süre:** 1 hafta
**Beklenen Dokümantasyon Güncelliği:** %95

## Success Metrics
1. **Documentation Coverage:** >= %90
2. **Documentation Freshness:** <= 7 gün
3. **Broken Link Rate:** < %1
4. **Auto-generation Success:** >= %95
5. **Developer Satisfaction:** >= 4.5/5.0

