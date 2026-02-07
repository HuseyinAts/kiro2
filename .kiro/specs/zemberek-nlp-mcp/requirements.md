# Requirements Document - Zemberek-NLP MCP Server

## Introduction

Bu spec, Türkçe NLP için Zemberek kütüphanesini MCP server olarak entegre eden sistemi tanımlar. Morphological analysis, spell checking, tokenization ile Türkçe dil desteği sağlar.

## Glossary

- **Zemberek**: Türkçe NLP kütüphanesi
- **Morphological Analysis**: Biçimbilimsel analiz
- **Lemmatization**: Kök bulma
- **Tokenization**: Sözcük ayırma
- **Spell Checking**: Yazım denetimi
- **Diacritics**: Sesli harf işaretleri

## Requirements

### Requirement 1: Morphological Analysis
**User Story:** As a NLP developer, I want morphological analysis, so that Türkçe kelime yapısını anlayayım.
#### Acceptance Criteria
1. **REQ-1.1** WHEN Türkçe kelime analiz edildiğinde, THE System SHALL kök, ek, tip bilgilerini döner
2. **REQ-1.2** WHEN çekim analizi yapıldığında, THE System SHALL isim/fiil çekimlerini parse eder
3. **REQ-1.3** WHEN belirsizlik olduğunda, THE System SHALL tüm olası analiz'leri confidence score ile döner
4. **REQ-1.4** WHEN compound word tespit edildiğinde, THE System SHALL bileşik kelime parçalarını ayırır
5. **REQ-1.5** WHEN proper noun detect edildiğinde, THE System SHALL özel isim tag'i ekler
6. **REQ-1.6** WHEN analysis cache edildiğinde, THE System SHALL frequent word'leri Redis'te saklar

### Requirement 2: Lemmatization
**User Story:** As a search engineer, I want lemmatization, so that kelime köklerini bulayım.
#### Acceptance Criteria
1. **REQ-2.1** WHEN çekimli kelime verildiğinde, THE System SHALL kök formu döner
2. **REQ-2.2** WHEN multiple root olduğunda, THE System SHALL context-aware selection yapar
3. **REQ-2.3** WHEN verb lemmatize edildiğinde, THE System SHALL infinitive form döner
4. **REQ-2.4** WHEN noun lemmatize edildiğinde, THE System SHALL singular nominative form döner
5. **REQ-2.5** WHEN lemma validate edildiğinde, THE System SHALL Turkish dictionary check yapar
6. **REQ-2.6** WHEN batch lemmatization yapıldığında, THE System SHALL >= 1000 word/sec throughput sağlar

### Requirement 3: Spell Checking
**User Story:** As a content editor, I want spell checking, so that yazım hatalarını bulayım.
#### Acceptance Criteria
1. **REQ-3.1** WHEN text check edildiğinde, THE System SHALL misspelled word'leri highlight eder
2. **REQ-3.2** WHEN suggestion generate edildiğinde, THE System SHALL edit distance <= 2 olan candidate'leri döner
3. **REQ-3.3** WHEN context-aware correction yapıldığında, THE System SHALL n-gram probability kullanır
4. **REQ-3.4** WHEN custom dictionary eklediğinde, THE System SHALL domain-specific term'leri accept eder
5. **REQ-3.5** WHEN diacritic error tespit edildiğinde, THE System SHALL ı/i, ş/s, ğ/g confusion'ları düzeltir
6. **REQ-3.6** WHEN spell check performance ölçüldüğünde, THE System SHALL < 100ms per sentence hedefler

### Requirement 4: Tokenization
**User Story:** As a NLP engineer, I want tokenization, so that metni sözcüklere ayırayım.
#### Acceptance Criteria
1. **REQ-4.1** WHEN text tokenize edildiğinde, THE System SHALL word boundary'leri doğru tespit eder
2. **REQ-4.2** WHEN punctuation handle edildiğinde, THE System SHALL sentence-final vs mid-word ayırır
3. **REQ-4.3** WHEN abbreviation tespit edildiğinde, THE System SHALL "Dr.", "vb." gibi kısaltmaları korur
4. **REQ-4.4** WHEN number tokenize edildiğinde, THE System SHALL "1.000.000" gibi format'ları preserve eder
5. **REQ-4.5** WHEN URL/email tokenize edildiğinde, THE System SHALL single token olarak işler
6. **REQ-4.6** WHEN subword tokenization yapıldığında, THE System SHALL BPE algorithm destekler

### Requirement 5: Named Entity Recognition
**User Story:** As a information extraction engineer, I want NER, so that özel isimleri bulayım.
#### Acceptance Criteria
1. **REQ-5.1** WHEN text analiz edildiğinde, THE System SHALL person, location, organization detect eder
2. **REQ-5.2** WHEN entity boundary belirlediğinde, THE System SHALL multi-word entity'leri group eder
3. **REQ-5.3** WHEN entity type classify edildiğinde, THE System SHALL >= %85 accuracy sağlar
4. **REQ-5.4** WHEN Turkish-specific entity handle edildiğinde, THE System SHALL "İstanbul", "Türkiye" gibi proper noun'ları recognize eder
5. **REQ-5.5** WHEN entity linking yapıldığında, THE System SHALL knowledge base'e map eder
6. **REQ-5.6** WHEN NER model update edildiğinde, THE System SHALL fine-tuning destekler

### Requirement 6: Sentence Segmentation
**User Story:** As a text processing engineer, I want sentence segmentation, so that cümleleri ayırayım.
#### Acceptance Criteria
1. **REQ-6.1** WHEN text segment edildiğinde, THE System SHALL sentence boundary'leri doğru tespit eder
2. **REQ-6.2** WHEN abbreviation içeren cümle olduğunda, THE System SHALL false positive önler
3. **REQ-6.3** WHEN quotation handle edildiğinde, THE System SHALL nested quote'ları parse eder
4. **REQ-6.4** WHEN ellipsis tespit edildiğinde, THE System SHALL "..." sentence-final olarak işler
5. **REQ-6.5** WHEN dialog segment edildiğinde, THE System SHALL speaker turn'leri ayırır
6. **REQ-6.6** WHEN segmentation validate edildiğinde, THE System SHALL >= %98 accuracy hedefler

### Requirement 7: Normalization
**User Story:** As a social media analyst, I want normalization, so that informal text'i standardize edeyim.
#### Acceptance Criteria
1. **REQ-7.1** WHEN informal text normalize edildiğinde, THE System SHALL "naber" -> "ne haber" dönüşümü yapar
2. **REQ-7.2** WHEN repeated character tespit edildiğinde, THE System SHALL "çoooook" -> "çok" düzeltir
3. **REQ-7.3** WHEN emoji/emoticon handle edildiğinde, THE System SHALL text equivalent'e çevirir
4. **REQ-7.4** WHEN slang detect edildiğinde, THE System SHALL formal equivalent önerir
5. **REQ-7.5** WHEN case normalization yapıldığında, THE System SHALL Turkish uppercase rules (I/İ, i/ı) uygular
6. **REQ-7.6** WHEN normalization dictionary update edildiğinde, THE System SHALL crowdsourced data kullanır

### Requirement 8: MCP Server Integration
**User Story:** As a sistem yöneticisi, I want MCP integration, so that Zemberek Claude'a entegre olsun.
#### Acceptance Criteria
1. **REQ-8.1** WHEN MCP server başladığında, THE System SHALL Zemberek library'yi initialize eder
2. **REQ-8.2** WHEN tool call geldiğinde, THE System SHALL analyze, lemmatize, spell_check, tokenize method'larını expose eder
3. **REQ-8.3** WHEN error handle edildiğinde, THE System SHALL graceful degradation sağlar
4. **REQ-8.4** WHEN performance optimize edildiğinde, THE System SHALL connection pooling kullanır
5. **REQ-8.5** WHEN logging yapıldığında, THE System SHALL request/response ve latency kaydeder
6. **REQ-8.6** WHEN health check çalıştığında, THE System SHALL Zemberek availability test eder

## Bağımlılıklar
- **zemberek-python**: Python binding
- **jpype**: Java-Python bridge
- **redis**: Caching
- **fastapi**: MCP server
- **pydantic**: Schema validation

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 2 hafta
**Beklenen Türkçe NLP Accuracy:** >= %90

## Success Metrics
1. **Morphological Analysis Accuracy:** >= %95
2. **Spell Check Precision:** >= %90
3. **Tokenization Accuracy:** >= %98
4. **NER F1-Score:** >= %85
5. **API Latency:** < 100ms (P95)
