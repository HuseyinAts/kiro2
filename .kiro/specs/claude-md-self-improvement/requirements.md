# Requirements Document - CLAUDE.md Self-Improvement

## Introduction

Bu spec, CLAUDE.md dosyasının otomatik self-improvement mekanizmasını tanımlar. Feedback loop, pattern detection, rule evolution ile sürekli iyileşme sağlar.

## Glossary

- **CLAUDE.md**: Agent configuration file
- **Self-Improvement**: Kendini geliştirme
- **Feedback Loop**: Geri bildirim döngüsü
- **Pattern Detection**: Örüntü tespiti
- **Rule Evolution**: Kural evrimi
- **Meta-Learning**: Üst öğrenme

## Requirements

### Requirement 1: Feedback Collection
**User Story:** As a sistem yöneticisi, I want feedback collection, so that agent performance ölçülsün.
#### Acceptance Criteria
1. **REQ-1.1** WHEN agent task tamamladığında, THE System SHALL success/failure outcome kaydeder
2. **REQ-1.2** WHEN user feedback alındığında, THE System SHALL rating (1-5) ve comment saklar
3. **REQ-1.3** WHEN implicit feedback tespit edildiğinde, THE System SHALL retry count, edit frequency analiz eder
4. **REQ-1.4** WHEN feedback aggregate edildiğinde, THE System SHALL per-rule effectiveness score hesaplar
5. **REQ-1.5** WHEN feedback threshold aşıldığında, THE System SHALL improvement trigger eder
6. **REQ-1.6** WHEN feedback history tutulduğunda, THE System SHALL 30-day rolling window kullanır

### Requirement 2: Pattern Detection
**User Story:** As a AI researcher, I want pattern detection, so that recurring issues tespit edilsin.
#### Acceptance Criteria
1. **REQ-2.1** WHEN error pattern analiz edildiğinde, THE System SHALL frequent error types cluster eder
2. **REQ-2.2** WHEN success pattern tespit edildiğinde, THE System SHALL high-performing rule combinations bulur
3. **REQ-2.3** WHEN anti-pattern bulunduğunda, THE System SHALL problematic rule sequences highlight eder
4. **REQ-2.4** WHEN pattern confidence ölçüldüğünde, THE System SHALL statistical significance >= 0.95 gerektirir
5. **REQ-2.5** WHEN pattern visualization yapıldığında, THE System SHALL heatmap ve graph oluşturur
6. **REQ-2.6** WHEN pattern alert verildiğinde, THE System SHALL actionable recommendation sağlar

### Requirement 3: Rule Evolution
**User Story:** As a developer, I want rule evolution, so that kurallar otomatik iyileşsin.
#### Acceptance Criteria
1. **REQ-3.1** WHEN low-performing rule tespit edildiğinde, THE System SHALL alternative formulation önerir
2. **REQ-3.2** WHEN rule conflict bulunduğunda, THE System SHALL contradiction resolution yapar
3. **REQ-3.3** WHEN new rule önerildiğinde, THE System SHALL A/B testing ile validate eder
4. **REQ-3.4** WHEN rule update yapıldığında, THE System SHALL version control ile track eder
5. **REQ-3.5** WHEN rule rollback gerektiğinde, THE System SHALL previous version'a dönebilir
6. **REQ-3.6** WHEN rule effectiveness ölçüldüğünde, THE System SHALL before/after metrics karşılaştırır

### Requirement 4: A/B Testing Framework
**User Story:** As a product manager, I want A/B testing, so that rule değişiklikleri validate edilsin.
#### Acceptance Criteria
1. **REQ-4.1** WHEN yeni rule test edildiğinde, THE System SHALL traffic'i %50-%50 split eder
2. **REQ-4.2** WHEN test duration belirlediğinde, THE System SHALL minimum 1000 sample gerektirir
3. **REQ-4.3** WHEN statistical significance hesaplandığında, THE System SHALL p-value < 0.05 kullanır
4. **REQ-4.4** WHEN winner seçildiğinde, THE System SHALL multi-metric evaluation yapar
5. **REQ-4.5** WHEN test sonuçlandığında, THE System SHALL winning variant'ı production'a alır
6. **REQ-4.6** WHEN test report oluşturulduğunda, THE System SHALL confidence interval ve effect size gösterir

### Requirement 5: Meta-Learning System
**User Story:** As a AI researcher, I want meta-learning, so that agent öğrenmeyi öğrensin.
#### Acceptance Criteria
1. **REQ-5.1** WHEN learning strategy değerlendirildiğinde, THE System SHALL learning rate optimize eder
2. **REQ-5.2** WHEN task similarity tespit edildiğinde, THE System SHALL transfer learning uygular
3. **REQ-5.3** WHEN exploration-exploitation balance yapıldığında, THE System SHALL epsilon-greedy strategy kullanır
4. **REQ-5.4** WHEN meta-parameter tune edildiğinde, THE System SHALL Bayesian optimization yapar
5. **REQ-5.5** WHEN learning curve analiz edildiğinde, THE System SHALL plateau detection yapar
6. **REQ-5.6** WHEN meta-knowledge persist edildiğinde, THE System SHALL knowledge graph kullanır

### Requirement 6: Automated Documentation Update
**User Story:** As a developer, I want automated docs, so that CLAUDE.md güncel kalsın.
#### Acceptance Criteria
1. **REQ-6.1** WHEN rule değiştiğinde, THE System SHALL CLAUDE.md'yi otomatik update eder
2. **REQ-6.2** WHEN example eklediğinde, THE System SHALL best practice'lerden seçer
3. **REQ-6.3** WHEN deprecation yapıldığında, THE System SHALL migration guide ekler
4. **REQ-6.4** WHEN changelog oluşturulduğunda, THE System SHALL semantic versioning kullanır
5. **REQ-6.5** WHEN diff gösterildiğinde, THE System SHALL before/after comparison sağlar
6. **REQ-6.6** WHEN approval workflow çalıştığında, THE System SHALL human-in-the-loop review gerektirir

### Requirement 7: Performance Monitoring
**User Story:** As a sistem yöneticisi, I want performance monitoring, so that iyileşme track edilsin.
#### Acceptance Criteria
1. **REQ-7.1** WHEN baseline metric belirlediğinde, THE System SHALL initial performance snapshot alır
2. **REQ-7.2** WHEN improvement ölçüldüğünde, THE System SHALL task success rate, latency, quality score karşılaştırır
3. **REQ-7.3** WHEN regression tespit edildiğinde, THE System SHALL automatic rollback trigger eder
4. **REQ-7.4** WHEN trend analysis yapıldığında, THE System SHALL moving average ve seasonality hesaplar
5. **REQ-7.5** WHEN anomaly detection çalıştığında, THE System SHALL Z-score > 3 olan outlier'ları bulur
6. **REQ-7.6** WHEN dashboard gösterildiğinde, THE System SHALL real-time improvement metrics sağlar

### Requirement 8: Safety Guardrails
**User Story:** As a security engineer, I want safety guardrails, so that zararlı rule değişiklikleri önlensin.
#### Acceptance Criteria
1. **REQ-8.1** WHEN rule proposal validate edildiğinde, THE System SHALL safety policy compliance kontrol eder
2. **REQ-8.2** WHEN risky change tespit edildiğinde, THE System SHALL manual approval gerektirir
3. **REQ-8.3** WHEN sandbox testing yapıldığında, THE System SHALL isolated environment kullanır
4. **REQ-8.4** WHEN rollback mechanism test edildiğinde, THE System SHALL < 5s recovery time sağlar
5. **REQ-8.5** WHEN audit log tutulduğunda, THE System SHALL who, what, when, why kaydeder
6. **REQ-8.6** WHEN emergency stop gerektiğinde, THE System SHALL all auto-improvement'ı pause eder

### Requirement 9: Boris Cherny Verification Integration
**User Story:** As a developer, I want verification loops, so that kod kalitesi %200-300 artsın.
#### Acceptance Criteria
1. **REQ-9.1** WHEN kod değişikliği yapıldığında, THE System SHALL verification-agent otomatik tetikler
2. **REQ-9.2** WHEN reward hacking tespit edildiğinde, THE System SHALL Exit Code 2 döndürür
3. **REQ-9.3** WHEN test başarısız olduğunda, THE System SHALL blocking error verir
4. **REQ-9.4** WHEN linting/type check başarısız olduğunda, THE System SHALL commit engeller
5. **REQ-9.5** WHEN hook tetiklendiğinde, THE System SHALL mevcut .claude/hooks/ altyapısını kullanır
6. **REQ-9.6** WHEN subagent gerektiğinde, THE System SHALL verification-agent, test-runner OTOMATIK çalıştırır

### Requirement 10: KIRO2 YKS Platform Integration
**User Story:** As a YKS platform developer, I want KIRO2-specific features, so that platform kalitesi artsın.
#### Acceptance Criteria
1. **REQ-10.1** WHEN IRT parametresi değiştiğinde, THE System SHALL [-4.0, 4.0] sınırları kontrol eder
2. **REQ-10.2** WHEN Türkçe metin işlendiğinde, THE System SHALL I/ı dönüşümünü doğru yapar
3. **REQ-10.3** WHEN ZPD hesaplaması yapıldığında, THE System SHALL %15-85 başarı olasılığı kontrol eder
4. **REQ-10.4** WHEN MCP server kullanıldığında, THE System SHALL chromadb-mcp, zemberek-mcp entegre olur
5. **REQ-10.5** WHEN feedback kaydı yapıldığında, THE System SHALL PostgreSQL:5434 port kullanır
6. **REQ-10.6** WHEN cache gerektiğinde, THE System SHALL Redis:6379 kullanır

## Bağımlılıklar
- **git>=2.40.0**: Version control (mevcut)
- **pytest>=7.4.3**: A/B test validation (mevcut)
- **scikit-learn>=1.4.0**: Pattern detection (mevcut)
- **scipy>=1.12.0**: Statistical significance testing (EKLENMELİ)
- **scikit-optimize>=0.9.0**: Bayesian optimization (EKLENMELİ)
- **pandas>=2.2.0**: Data analysis (EKLENMELİ)
- **networkx>=3.2.0**: Knowledge graph (EKLENMELİ)
- **gitpython>=3.1.40**: Git integration (EKLENMELİ)
- **seaborn>=0.13.0**: Statistical visualization (EKLENMELİ)
- **matplotlib>=3.8.0**: Visualization (mevcut)
- **plotly>=5.18.0**: Real-time dashboard (mevcut)

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 10
**Toplam Kabul Kriteri:** 60
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 2 hafta
**Beklenen İyileşme:** %25 task success rate artışı + %200-300 kod kalitesi artışı (Boris Cherny)

## Success Metrics
1. **Task Success Rate Improvement:** >= %25
2. **Rule Effectiveness:** >= %80
3. **A/B Test Win Rate:** >= %60
4. **Regression Prevention:** %100
5. **Safety Compliance:** %100
