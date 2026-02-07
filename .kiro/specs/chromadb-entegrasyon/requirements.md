# Requirements Document - ChromaDB Entegrasyonu Sistemi

## Introduction

Bu spec, ChromaDB vector database entegrasyonunu tanımlar. Semantic search ile soru/içerik bulma %700 iyileşir. Embedding-based similarity search sağlar.

## Glossary

- **ChromaDB**: Vector database
- **Embedding**: Vektör temsili
- **Semantic Search**: Anlamsal arama
- **Cosine Similarity**: Kosinüs benzerliği
- **Collection**: Vektör koleksiyonu
- **HNSW**: Hierarchical Navigable Small World (index)

## Requirements

### Requirement 1: Embedding Generation
**User Story:** As a AI agent, I want metin içeriğini embedding'e çevirmek, so that semantic search yapabiliyim.
#### Acceptance Criteria
1. **REQ-1.1** WHEN metin embedding'e çevrildiğinde, THE System SHALL Sentence-Transformers kullanır
2. **REQ-1.2** WHEN Türkçe metin olduğunda, THE System SHALL multilingual model (paraphrase-multilingual-mpnet-base-v2) kullanır
3. **REQ-1.3** WHEN embedding dimension belirlendiğinde, THE System SHALL 768-dim vector üretir
4. **REQ-1.4** WHEN batch embedding yapıldığında, THE System SHALL 32 batch size kullanır
5. **REQ-1.5** WHEN embedding cache'lendiğinde, THE System SHALL Redis'te 24 saat saklar
6. **REQ-1.6** WHEN embedding quality ölçüldüğünde, THE System SHALL cosine similarity distribution kontrol eder

### Requirement 2: Collection Management
**User Story:** As a developer, I want farklı içerik tiplerini ayrı collection'larda saklamak, so that organize edeyim.
#### Acceptance Criteria
1. **REQ-2.1** WHEN collection oluşturulduğunda, THE System SHALL questions, content, concepts collection'ları ayırır
2. **REQ-2.2** WHEN collection metadata eklendiğinde, THE System SHALL name, description, created_at saklar
3. **REQ-2.3** WHEN collection index oluşturulduğunda, THE System SHALL HNSW index kullanır
4. **REQ-2.4** WHEN collection size büyüdüğünde, THE System SHALL automatic sharding yapar
5. **REQ-2.5** WHEN collection backup alındığında, THE System SHALL incremental backup destekler
6. **REQ-2.6** WHEN collection delete edildiğinde, THE System SHALL cascade delete uygular

### Requirement 3: Semantic Question Search
**User Story:** As a öğrenci, I want benzer soruları bulmak, so that pratik yapayım.
#### Acceptance Criteria
1. **REQ-3.1** WHEN soru aranırken, THE System SHALL query embedding oluşturur
2. **REQ-3.2** WHEN similarity search yapıldığında, THE System SHALL top-k nearest neighbors bulur
3. **REQ-3.3** WHEN similarity threshold uygulandığında, THE System SHALL cosine similarity > 0.7 filtreler
4. **REQ-3.4** WHEN metadata filter kullanıldığında, THE System SHALL konu, zorluk, kazanım filtreler
5. **REQ-3.5** WHEN diversity sağlandığında, THE System SHALL MMR (Maximal Marginal Relevance) uygular
6. **REQ-3.6** WHEN search results rank edildiğinde, THE System SHALL similarity + recency + popularity skorlar

### Requirement 4: Content Recommendation
**User Story:** As a AI agent, I want öğrenciye uygun içerik önermek, so that kişiselleştirilmiş öğrenme sağlayayım.
#### Acceptance Criteria
1. **REQ-4.1** WHEN içerik önerildiğinde, THE System SHALL öğrenci profil embedding'i kullanır
2. **REQ-4.2** WHEN profile embedding oluşturulduğunda, THE System SHALL geçmiş etkileşimleri aggregate eder
3. **REQ-4.3** WHEN recommendation yapıldığında, THE System SHALL collaborative filtering + content-based hybrid kullanır
4. **REQ-4.4** WHEN cold start problem olduğunda, THE System SHALL popularity-based fallback yapar
5. **REQ-4.5** WHEN recommendation diversity sağlandığında, THE System SHALL different topics'ten seçer
6. **REQ-4.6** WHEN recommendation quality ölçüldüğünde, THE System SHALL click-through rate takip eder

### Requirement 5: Duplicate Detection
**User Story:** As a içerik yöneticisi, I want duplicate soruları tespit etmek, so that soru bankası temiz olsun.
#### Acceptance Criteria
1. **REQ-5.1** WHEN yeni soru eklendiğinde, THE System SHALL similarity search ile duplicate kontrol eder
2. **REQ-5.2** WHEN similarity > 0.95 olduğunda, THE System SHALL potential duplicate olarak işaretler
3. **REQ-5.3** WHEN exact match tespit edildiğinde, THE System SHALL eklemeyi engeller
4. **REQ-5.4** WHEN near-duplicate bulunduğunda, THE System SHALL manual review önerir
5. **REQ-5.5** WHEN paraphrase detection yapıldığında, THE System SHALL semantic similarity kullanır
6. **REQ-5.6** WHEN duplicate merge edildiğinde, THE System SHALL metadata'yı birleştirir

### Requirement 6: Concept Clustering
**User Story:** As a öğretmen, I want benzer kavramları gruplamak, so that konu organizasyonu yapayım.
#### Acceptance Criteria
1. **REQ-6.1** WHEN clustering yapıldığında, THE System SHALL K-means veya HDBSCAN kullanır
2. **REQ-6.2** WHEN optimal cluster sayısı belirlendiğinde, THE System SHALL elbow method uygular
3. **REQ-6.3** WHEN cluster label oluşturulduğunda, THE System SHALL centroid'e en yakın concept'i label yapar
4. **REQ-6.4** WHEN cluster quality ölçüldüğünde, THE System SHALL silhouette score hesaplar
5. **REQ-6.5** WHEN outlier tespit edildiğinde, THE System SHALL isolated concepts'i işaretler
6. **REQ-6.6** WHEN cluster visualization yapıldığında, THE System SHALL t-SNE veya UMAP kullanır

### Requirement 7: Performance Optimization
**User Story:** As a DevOps engineer, I want vector search'ün hızlı olmasını, so that real-time response verebiliyim.
#### Acceptance Criteria
1. **REQ-7.1** WHEN search query çalıştığında, THE System SHALL < 100ms response time hedefler
2. **REQ-7.2** WHEN index optimize edildiğinde, THE System SHALL HNSW parameters (M=16, efConstruction=200) tuning yapar
3. **REQ-7.3** WHEN cache kullanıldığında, THE System SHALL frequent queries'i Redis'te cache'ler
4. **REQ-7.4** WHEN batch query yapıldığında, THE System SHALL vectorized operations kullanır
5. **REQ-7.5** WHEN memory usage optimize edildiğinde, THE System SHALL quantization uygular
6. **REQ-7.6** WHEN throughput ölçüldüğünde, THE System SHALL >= 1000 queries/sec hedefler

### Requirement 8: MCP Server Integration
**User Story:** As a sistem yöneticisi, I want ChromaDB'yi MCP server olarak kullanmak, so that standardize edilmiş erişim sağlayayım.
#### Acceptance Criteria
1. **REQ-8.1** WHEN MCP server başlatıldığında, THE System SHALL ChromaDB client initialize eder
2. **REQ-8.2** WHEN MCP tool çağrıldığında, THE System SHALL search, add, update, delete operations destekler
3. **REQ-8.3** WHEN error handling yapıldığında, THE System SHALL graceful degradation sağlar
4. **REQ-8.4** WHEN rate limiting uygulandığında, THE System SHALL 100 req/min limit koyar
5. **REQ-8.5** WHEN health check yapıldığında, THE System SHALL ChromaDB connection test eder
6. **REQ-8.6** WHEN metrics export edildiğinde, THE System SHALL Prometheus metrics sağlar

## Bağımlılıklar
- **ChromaDB**: Vector database
- **Sentence-Transformers**: Embedding generation
- **Redis**: Embedding cache
- **scikit-learn**: Clustering algorithms
- **UMAP**: Dimensionality reduction

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 1 hafta
**Beklenen Search İyileşmesi:** %700

## Success Metrics
1. **Search Accuracy:** >= %90
2. **Search Latency:** < 100ms
3. **Duplicate Detection Rate:** >= %95
4. **Recommendation CTR:** %300 improvement
5. **Throughput:** >= 1000 queries/sec

