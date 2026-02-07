# Requirements Document - Memory Knowledge Graph Sistemi

## Introduction

Bu spec, öğrenci öğrenme geçmişini knowledge graph olarak saklayan ve ilişkilendiren sistemi tanımlar. Neo4j graph database ile %600 daha etkili kişiselleştirme sağlar.

## Glossary

- **Knowledge Graph**: Bilgi grafiği
- **Neo4j**: Graph database
- **Entity**: Varlık (konu, soru, kavram)
- **Relationship**: İlişki (ön koşul, ilgili, benzer)
- **Cypher**: Neo4j query dili
- **Graph Traversal**: Graf gezinme

## Requirements

### Requirement 1: Entity Extraction ve Storage
**User Story:** As a AI agent, I want öğrenci etkileşimlerinden entity çıkarmak, so that knowledge graph oluşturayım.
#### Acceptance Criteria
1. **REQ-1.1** WHEN öğrenci soru çözdüğünde, THE System SHALL konu, kazanım, kavram entity'lerini çıkarır
2. **REQ-1.2** WHEN entity oluşturulduğunda, THE System SHALL Neo4j'ye node olarak kaydeder
3. **REQ-1.3** WHEN entity properties belirlendiğinde, THE System SHALL name, type, difficulty, mastery_level saklar
4. **REQ-1.4** WHEN duplicate entity tespit edildiğinde, THE System SHALL merge operation yapar
5. **REQ-1.5** WHEN entity update edildiğinde, THE System SHALL version history tutar
6. **REQ-1.6** WHEN entity silindiğinde, THE System SHALL soft delete uygular

### Requirement 2: Relationship Mapping
**User Story:** As a öğretmen, I want konular arası ilişkileri görmek, so that öğrenme yolu planlayayım.
#### Acceptance Criteria
1. **REQ-2.1** WHEN iki entity ilişkilendirildiğinde, THE System SHALL relationship type belirler (PREREQUISITE, RELATED, SIMILAR)
2. **REQ-2.2** WHEN prerequisite ilişkisi oluşturulduğunda, THE System SHALL directed edge kullanır
3. **REQ-2.3** WHEN relationship weight hesaplandığında, THE System SHALL co-occurrence frequency kullanır
4. **REQ-2.4** WHEN bidirectional relationship olduğunda, THE System SHALL symmetric edge oluşturur
5. **REQ-2.5** WHEN relationship properties eklendiğinde, THE System SHALL strength, confidence, timestamp saklar
6. **REQ-2.6** WHEN relationship validation yapıldığında, THE System SHALL circular dependency kontrol eder

### Requirement 3: Learning Path Generation
**User Story:** As a öğrenci, I want bilgi grafından optimal öğrenme yolu oluşturulmasını, so that verimli çalışayım.
#### Acceptance Criteria
1. **REQ-3.1** WHEN öğrenme yolu istendiğinde, THE System SHALL Cypher query ile path bulur
2. **REQ-3.2** WHEN shortest path hesaplandığında, THE System SHALL Dijkstra algoritması kullanır
3. **REQ-3.3** WHEN prerequisite chain oluşturulduğunda, THE System SHALL topological sort uygular
4. **REQ-3.4** WHEN alternative paths bulunduğunda, THE System SHALL multiple options sunar
5. **REQ-3.5** WHEN path difficulty hesaplandığında, THE System SHALL cumulative difficulty skorlar
6. **REQ-3.6** WHEN personalization uygulandığında, THE System SHALL öğrenci mastery level'ı dikkate alır

### Requirement 4: Concept Mastery Tracking
**User Story:** As a öğrenci, I want kavram hakimiyetimin takip edilmesini, so that gelişimimi görebiliyim.
#### Acceptance Criteria
1. **REQ-4.1** WHEN öğrenci soru çözdüğünde, THE System SHALL ilgili concept node'un mastery_level'ını günceller
2. **REQ-4.2** WHEN mastery hesaplandığında, THE System SHALL doğru/yanlış oranı ve son performans kullanır
3. **REQ-4.3** WHEN mastery threshold aşıldığında, THE System SHALL concept'i "mastered" olarak işaretler
4. **REQ-4.4** WHEN regression tespit edildiğinde, THE System SHALL mastery_level'ı düşürür
5. **REQ-4.5** WHEN mastery visualization yapıldığında, THE System SHALL heat map gösterir
6. **REQ-4.6** WHEN mastery trend analiz edildiğinde, THE System SHALL improvement rate hesaplar

### Requirement 5: Knowledge Gap Detection
**User Story:** As a AI agent, I want bilgi eksiklerini graf analizi ile tespit etmek, so that targeted öneriler yapayım.
#### Acceptance Criteria
1. **REQ-5.1** WHEN gap analysis yapıldığında, THE System SHALL unmastered prerequisite'leri bulur
2. **REQ-5.2** WHEN gap severity hesaplandığında, THE System SHALL downstream impact analiz eder
3. **REQ-5.3** WHEN gap prioritization yapıldığında, THE System SHALL critical path üzerindeki gap'leri önceliklendirir
4. **REQ-5.4** WHEN gap remediation planı oluşturulduğunda, THE System SHALL fill order belirler
5. **REQ-5.5** WHEN gap closure tracking yapıldığında, THE System SHALL progress percentage hesaplar
6. **REQ-5.6** WHEN gap pattern tespit edildiğinde, THE System SHALL systematic weakness'leri raporlar

### Requirement 6: Semantic Search on Graph
**User Story:** As a öğrenci, I want benzer kavramları bulmak, so that ilgili konuları keşfedeyim.
#### Acceptance Criteria
1. **REQ-6.1** WHEN semantic search yapıldığında, THE System SHALL graph embedding kullanır
2. **REQ-6.2** WHEN similar concepts aranırken, THE System SHALL cosine similarity hesaplar
3. **REQ-6.3** WHEN neighborhood search yapıldığında, THE System SHALL k-hop neighbors bulur
4. **REQ-6.4** WHEN community detection yapıldığında, THE System SHALL Louvain algorithm kullanır
5. **REQ-6.5** WHEN centrality hesaplandığında, THE System SHALL PageRank uygular
6. **REQ-6.6** WHEN search results rank edildiğinde, THE System SHALL relevance ve mastery level dikkate alır

### Requirement 7: Graph Visualization
**User Story:** As a öğretmen, I want bilgi grafını görselleştirmek, so that öğrenci ilerlemesini görebiliyim.
#### Acceptance Criteria
1. **REQ-7.1** WHEN graph render edildiğinde, THE System SHALL D3.js veya Cytoscape kullanır
2. **REQ-7.2** WHEN node color'u belirlendiğinde, THE System SHALL mastery level'a göre renklendirme yapar
3. **REQ-7.3** WHEN edge thickness ayarlandığında, THE System SHALL relationship strength'e göre kalınlık verir
4. **REQ-7.4** WHEN layout seçildiğinde, THE System SHALL force-directed layout uygular
5. **REQ-7.5** WHEN interactive exploration olduğunda, THE System SHALL node click ile detail gösterir
6. **REQ-7.6** WHEN subgraph filter edildiğinde, THE System SHALL specific topic'e odaklanır

### Requirement 8: Graph Analytics ve Insights
**User Story:** As a AI trainer, I want graf analitikleri ile pattern tespit etmek, so that sistem iyileştireyim.
#### Acceptance Criteria
1. **REQ-8.1** WHEN graph metrics hesaplandığında, THE System SHALL node count, edge count, density hesaplar
2. **REQ-8.2** WHEN clustering coefficient hesaplandığında, THE System SHALL graph connectivity ölçer
3. **REQ-8.3** WHEN bottleneck tespit edildiğinde, THE System SHALL critical nodes bulur
4. **REQ-8.4** WHEN learning pattern analiz edildiğinde, THE System SHALL common paths tespit eder
5. **REQ-8.5** WHEN anomaly detection yapıldığında, THE System SHALL unusual learning patterns bulur
6. **REQ-8.6** WHEN recommendation quality ölçüldüğünde, THE System SHALL graph-based vs baseline karşılaştırır

## Bağımlılıklar
- **Neo4j**: Graph database
- **py2neo**: Python Neo4j driver
- **NetworkX**: Graph algorithms
- **D3.js**: Graph visualization
- **Sentence-Transformers**: Graph embedding

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 1 hafta
**Beklenen Kişiselleştirme Artışı:** %600

## Success Metrics
1. **Graph Coverage:** >= %90 concepts
2. **Relationship Accuracy:** >= %95
3. **Path Recommendation Quality:** %600 improvement
4. **Query Performance:** < 100ms
5. **Student Engagement:** %50 artış

