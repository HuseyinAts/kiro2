# Requirements Document - Context7 Entegrasyonu Sistemi

## Introduction

Bu spec, Context7 MCP server entegrasyonunu tanımlar. Context7, 7 farklı context source'u (codebase, git history, documentation, dependencies, tests, issues, PRs) birleştirerek AI agent'lara zengin context sağlar. Context kalitesi %400 artar.

## Glossary

- **Context7**: 7 kaynaklı context aggregator MCP server
- **MCP Server**: Model Context Protocol server
- **Context Source**: Bağlam kaynağı
- **Semantic Search**: Anlamsal arama
- **Context Window**: AI model context penceresi
- **RAG**: Retrieval-Augmented Generation

## Requirements

### Requirement 1: Codebase Context Integration
**User Story:** As a AI agent, I want codebase'den ilgili kod parçalarını bulmak, so that doğru context ile yanıt vereyim.
#### Acceptance Criteria
1. **REQ-1.1** WHEN kod sorusu geldiğinde, THE Context7 SHALL semantic search ile ilgili dosyaları bulur
2. **REQ-1.2** WHEN dosyalar bulunduğunda, THE System SHALL AST analizi ile fonksiyon/class çıkarır
3. **REQ-1.3** WHEN relevance skorlandığında, THE System SHALL embedding similarity kullanır
4. **REQ-1.4** WHEN context limit aşıldığında, THE System SHALL en relevant parçaları seçer
5. **REQ-1.5** WHEN cross-reference bulunduğunda, THE System SHALL related files'ı da ekler
6. **REQ-1.6** WHEN context cache'lendiğinde, THE System SHALL Redis'te 1 saat saklar

### Requirement 2: Git History Context
**User Story:** As a AI agent, I want kod değişiklik geçmişini bilmek, so that why questions'a cevap verebiliyim.
#### Acceptance Criteria
1. **REQ-2.1** WHEN dosya history sorulduğunda, THE Context7 SHALL git log ile commit history çeker
2. **REQ-2.2** WHEN commit message analiz edildiğinde, THE System SHALL conventional commit parse eder
3. **REQ-2.3** WHEN blame bilgisi gerektiğinde, THE System SHALL git blame ile author bilgisi verir
4. **REQ-2.4** WHEN refactoring history sorulduğunda, THE System SHALL rename/move tracking yapar
5. **REQ-2.5** WHEN bug fix history gerektiğinde, THE System SHALL fix commit'leri filtreler
6. **REQ-2.6** WHEN history summarize edildiğinde, THE System SHALL major changes'i highlight eder

### Requirement 3: Documentation Context
**User Story:** As a AI agent, I want proje dokümantasyonuna erişmek, so that official docs'a göre yanıt vereyim.
#### Acceptance Criteria
1. **REQ-3.1** WHEN documentation aranırken, THE Context7 SHALL README, docs/, ve inline comments tarar
2. **REQ-3.2** WHEN markdown parse edildiğinde, THE System SHALL heading hierarchy korur
3. **REQ-3.3** WHEN code example bulunduğunda, THE System SHALL syntax highlighting ile gösterir
4. **REQ-3.4** WHEN API docs aranırken, THE System SHALL OpenAPI spec'i önceliklendirir
5. **REQ-3.5** WHEN tutorial bulunduğunda, THE System SHALL step-by-step format korur
6. **REQ-3.6** WHEN outdated docs tespit edildiğinde, THE System SHALL warning verir

### Requirement 4: Dependency Context
**User Story:** As a AI agent, I want kullanılan library'lerin dokümantasyonuna erişmek, so that doğru API kullanımı önerebiliyim.
#### Acceptance Criteria
1. **REQ-4.1** WHEN dependency sorulduğunda, THE Context7 SHALL requirements.txt/package.json parse eder
2. **REQ-4.2** WHEN library docs gerektiğinde, THE System SHALL PyPI/npm docs'a erişir
3. **REQ-4.3** WHEN version-specific docs gerektiğinde, THE System SHALL installed version'a göre docs bulur
4. **REQ-4.4** WHEN breaking change olduğunda, THE System SHALL migration guide gösterir
5. **REQ-4.5** WHEN alternative library sorulduğunda, THE System SHALL comparison yapar
6. **REQ-4.6** WHEN security advisory olduğunda, THE System SHALL vulnerability warning verir

### Requirement 5: Test Context
**User Story:** As a AI agent, I want test dosyalarından usage example öğrenmek, so that doğru kullanım gösterebiliyim.
#### Acceptance Criteria
1. **REQ-5.1** WHEN test example aranırken, THE Context7 SHALL tests/ dizinini tarar
2. **REQ-5.2** WHEN test case bulunduğunda, THE System SHALL setup/teardown ile birlikte gösterir
3. **REQ-5.3** WHEN fixture kullanıldığında, THE System SHALL fixture definition'ı da ekler
4. **REQ-5.4** WHEN mock kullanıldığında, THE System SHALL mock configuration gösterir
5. **REQ-5.5** WHEN edge case test bulunduğunda, THE System SHALL boundary conditions highlight eder
6. **REQ-5.6** WHEN test coverage düşük olduğunda, THE System SHALL missing test önerir

### Requirement 6: Issue/PR Context
**User Story:** As a AI agent, I want GitHub issue/PR'lardan context almak, so that known issues'a göre yanıt vereyim.
#### Acceptance Criteria
1. **REQ-6.1** WHEN issue aranırken, THE Context7 SHALL GitHub API kullanır
2. **REQ-6.2** WHEN related issue bulunduğunda, THE System SHALL issue title, body, ve comments çeker
3. **REQ-6.3** WHEN PR context gerektiğinde, THE System SHALL code review comments ekler
4. **REQ-6.4** WHEN bug report bulunduğunda, THE System SHALL reproduction steps gösterir
5. **REQ-6.5** WHEN feature request bulunduğunda, THE System SHALL discussion summary verir
6. **REQ-6.6** WHEN closed issue olduğunda, THE System SHALL resolution'ı açıklar

### Requirement 7: Context Aggregation ve Ranking
**User Story:** As a AI agent, I want 7 kaynaktan gelen context'in optimal şekilde birleştirilmesini, so that en relevant bilgiyi alayım.
#### Acceptance Criteria
1. **REQ-7.1** WHEN tüm kaynaklar tarandığında, THE Context7 SHALL unified ranking algoritması uygular
2. **REQ-7.2** WHEN ranking yapıldığında, THE System SHALL recency, relevance, ve authority skorlar
3. **REQ-7.3** WHEN context limit aşıldığında, THE System SHALL top-k selection yapar
4. **REQ-7.4** WHEN duplicate content olduğunda, THE System SHALL deduplication uygular
5. **REQ-7.5** WHEN context summarize edildiğinde, THE System SHALL key points extraction yapar
6. **REQ-7.6** WHEN context quality ölçüldüğünde, THE System SHALL completeness ve accuracy skorlar

### Requirement 8: MCP Server Configuration
**User Story:** As a sistem yöneticisi, I want Context7 MCP server'ın kolay yapılandırılmasını, so that hızlıca entegre edeyim.
#### Acceptance Criteria
1. **REQ-8.1** WHEN MCP server başlatıldığında, THE System SHALL .mcp.json config okur
2. **REQ-8.2** WHEN config validate edildiğinde, THE System SHALL required fields kontrol eder
3. **REQ-8.3** WHEN API key gerektiğinde, THE System SHALL environment variable'dan alır
4. **REQ-8.4** WHEN rate limit uygulandığında, THE System SHALL exponential backoff kullanır
5. **REQ-8.5** WHEN health check yapıldığında, THE System SHALL tüm 7 source'u test eder
6. **REQ-8.6** WHEN error handling yapıldığında, THE System SHALL graceful degradation sağlar

## Bağımlılıklar
- **Context7 MCP Server**: Ana MCP server
- **GitHub API**: Issue/PR context
- **Git**: Version control history
- **Sentence-Transformers**: Semantic search
- **Redis**: Context caching
- **FastAPI**: MCP server hosting

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 1 hafta
**Beklenen Context Kalitesi Artışı:** %400

## Success Metrics
1. **Context Relevance:** >= %90
2. **Context Retrieval Time:** < 500ms
3. **Cache Hit Rate:** >= %70
4. **Source Coverage:** 7/7 sources active
5. **AI Response Quality:** %300 improvement

