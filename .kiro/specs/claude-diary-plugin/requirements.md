# Requirements Document - Claude Diary Plugin

## Introduction

Bu spec, agent'ın günlük tutma ve reflection yapma sistemini tanımlar. Daily summary, insight extraction, learning journal ile sürekli öğrenme sağlar.

## Glossary

- **Diary Entry**: Günlük kaydı
- **Reflection**: Yansıtma/düşünme
- **Insight**: İçgörü
- **Learning Journal**: Öğrenme günlüğü
- **Meta-Cognition**: Üst biliş
- **Self-Awareness**: Öz farkındalık

## Requirements

### Requirement 1: Daily Summary Generation
**User Story:** As a agent, I want daily summary, so that günlük aktivitelerimi özetleyeyim.
#### Acceptance Criteria
1. **REQ-1.1** WHEN gün sonunda, THE System SHALL tüm task'ları aggregate eder
2. **REQ-1.2** WHEN summary oluşturulduğunda, THE System SHALL success/failure count, key learnings içerir
3. **REQ-1.3** WHEN highlight seçildiğinde, THE System SHALL most impactful task'ları belirler
4. **REQ-1.4** WHEN challenge kaydedildiğinde, THE System SHALL encountered difficulties listeler
5. **REQ-1.5** WHEN summary format edildiğinde, THE System SHALL markdown template kullanır
6. **REQ-1.6** WHEN summary persist edildiğinde, THE System SHALL `.kiro/diary/YYYY-MM-DD.md` path kullanır

### Requirement 2: Insight Extraction
**User Story:** As a developer, I want insight extraction, so that pattern'lerden öğreneyim.
#### Acceptance Criteria
1. **REQ-2.1** WHEN task pattern analiz edildiğinde, THE System SHALL recurring success factors bulur
2. **REQ-2.2** WHEN failure pattern tespit edildiğinde, THE System SHALL root cause identify eder
3. **REQ-2.3** WHEN correlation bulunduğunda, THE System SHALL cause-effect relationship kurar
4. **REQ-2.4** WHEN insight confidence ölçüldüğünde, THE System SHALL evidence strength >= 0.8 gerektirir
5. **REQ-2.5** WHEN actionable insight üretildiğinde, THE System SHALL specific recommendation verir
6. **REQ-2.6** WHEN insight categorize edildiğinde, THE System SHALL technical, process, communication gruplar

### Requirement 3: Reflection Prompts
**User Story:** As a AI researcher, I want reflection prompts, so that deep thinking tetiklensin.
#### Acceptance Criteria
1. **REQ-3.1** WHEN reflection başladığında, THE System SHALL guided questions sorar
2. **REQ-3.2** WHEN "What went well?" sorulduğunda, THE System SHALL success factors analiz eder
3. **REQ-3.3** WHEN "What could improve?" sorulduğunda, THE System SHALL improvement areas belirler
4. **REQ-3.4** WHEN "What did I learn?" sorulduğunda, THE System SHALL new knowledge extract eder
5. **REQ-3.5** WHEN "What will I do differently?" sorulduğunda, THE System SHALL action plan oluşturur
6. **REQ-3.6** WHEN reflection depth ölçüldüğünde, THE System SHALL surface vs deep thinking ratio hesaplar

### Requirement 4: Learning Journal
**User Story:** As a developer, I want learning journal, so that bilgi birikimi track edilsin.
#### Acceptance Criteria
1. **REQ-4.1** WHEN yeni bilgi öğrenildiğinde, THE System SHALL knowledge entry oluşturur
2. **REQ-4.2** WHEN knowledge categorize edildiğinde, THE System SHALL domain, skill, tool tag'leri ekler
3. **REQ-4.3** WHEN knowledge link kurulduğunda, THE System SHALL related concepts connect eder
4. **REQ-4.4** WHEN knowledge review yapıldığında, THE System SHALL spaced repetition schedule kullanır
5. **REQ-4.5** WHEN knowledge gap tespit edildiğinde, THE System SHALL learning recommendation verir
6. **REQ-4.6** WHEN knowledge graph gösterildiğinde, THE System SHALL interactive visualization sağlar

### Requirement 5: Emotional State Tracking
**User Story:** As a AI researcher, I want emotional tracking, so that agent state awareness olsun.
#### Acceptance Criteria
1. **REQ-5.1** WHEN task tamamlandığında, THE System SHALL confidence level (1-10) kaydeder
2. **REQ-5.2** WHEN frustration tespit edildiğinde, THE System SHALL retry count ve error frequency analiz eder
3. **REQ-5.3** WHEN flow state bulunduğunda, THE System SHALL high productivity period'ları identify eder
4. **REQ-5.4** WHEN emotional pattern analiz edildiğinde, THE System SHALL trigger factors bulur
5. **REQ-5.5** WHEN mood trend gösterildiğinde, THE System SHALL time-series chart oluşturur
6. **REQ-5.6** WHEN emotional intelligence ölçüldüğünde, THE System SHALL self-awareness score hesaplar

### Requirement 6: Goal Tracking
**User Story:** As a product manager, I want goal tracking, so that progress monitor edilsin.
#### Acceptance Criteria
1. **REQ-6.1** WHEN goal set edildiğinde, THE System SHALL SMART criteria validate eder
2. **REQ-6.2** WHEN progress update edildiğinde, THE System SHALL completion percentage hesaplar
3. **REQ-6.3** WHEN milestone ulaşıldığında, THE System SHALL celebration message gösterir
4. **REQ-6.4** WHEN goal risk tespit edildiğinde, THE System SHALL early warning verir
5. **REQ-6.5** WHEN goal adjust edildiğinde, THE System SHALL reason ve impact kaydeder
6. **REQ-6.6** WHEN goal retrospective yapıldığında, THE System SHALL lessons learned extract eder

### Requirement 7: Peer Comparison
**User Story:** As a developer, I want peer comparison, so that benchmark yapayım.
#### Acceptance Criteria
1. **REQ-7.1** WHEN performance compare edildiğinde, THE System SHALL anonymized peer data kullanır
2. **REQ-7.2** WHEN percentile hesaplandığında, THE System SHALL task success rate, speed, quality metriklerini karşılaştırır
3. **REQ-7.3** WHEN strength area bulunduğunda, THE System SHALL top 25% olduğu skill'leri highlight eder
4. **REQ-7.4** WHEN improvement area tespit edildiğinde, THE System SHALL bottom 25% olduğu skill'leri gösterir
5. **REQ-7.5** WHEN best practice öğrenildiğinde, THE System SHALL top performer strategy'lerini analiz eder
6. **REQ-7.6** WHEN comparison privacy korunduğunda, THE System SHALL differential privacy uygular

### Requirement 8: Export and Sharing
**User Story:** As a user, I want export, so that diary'yi paylaşayım.
#### Acceptance Criteria
1. **REQ-8.1** WHEN export request geldiğinde, THE System SHALL markdown, PDF, JSON format destekler
2. **REQ-8.2** WHEN date range seçildiğinde, THE System SHALL filtered export oluşturur
3. **REQ-8.3** WHEN privacy filter uygulandığında, THE System SHALL sensitive data redact eder
4. **REQ-8.4** WHEN sharing link oluşturulduğunda, THE System SHALL read-only access sağlar
5. **REQ-8.5** WHEN template kullanıldığında, THE System SHALL customizable format destekler
6. **REQ-8.6** WHEN backup yapıldığında, THE System SHALL encrypted storage kullanır

## Bağımlılıklar
- **markdown>=3.5.0**: Diary formatting
- **matplotlib>=3.8.0**: Visualization
- **networkx>=3.2.0**: Knowledge graph
- **schedule>=1.2.0**: Daily trigger
- **cryptography>=41.0.0**: Encryption
- **diffprivlib>=0.6.0**: Differential privacy (Peer Comparison)
- **scikit-learn>=1.4.0**: Pattern analysis (Insight Extraction)
- **reportlab>=4.0.0**: PDF export

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P2 (Orta)
**Tahmini Süre:** 3 gün
**Beklenen Self-Awareness:** %50 artış

## Success Metrics
1. **Daily Entry Completion:** >= %90
2. **Insight Quality:** >= %75
3. **Learning Retention:** >= %80
4. **Goal Achievement:** >= %70
5. **User Engagement:** >= %60
