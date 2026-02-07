# Design Document - ChromaDB Entegrasyonu

## Architecture Overview

ChromaDB vector database ile semantic search sistemi. Sentence-Transformers embedding + HNSW index + cosine similarity ile %700 search iyileşmesi sağlar.

## Components

### 1. Embedding Service (backend/services/embedding_service.py)
- **Purpose**: Metin → 768-dim vector dönüşümü
- **Dependencies**: sentence-transformers>=2.3.0
- **Key Features**:
  - Model: paraphrase-multilingual-mpnet-base-v2 (Türkçe destekli)
  - Batch processing (batch_size: 32)
  - Redis cache (TTL: 24h)
  - Cosine similarity calculation

### 2. ChromaDB Client (backend/services/chromadb_collection_manager.py)
- **Purpose**: Vector database operations
- **Dependencies**: chromadb>=0.4.22
- **Key Features**:
  - Collections: questions, content, concepts
  - HNSW index (M=16, efConstruction=200)
  - Metadata filtering
  - Batch upsert/query

### 3. Semantic Search (backend/api/v1/semantic_search.py)
- **Purpose**: Similarity-based search
- **Dependencies**: numpy>=1.26.0
- **Key Features**:
  - Top-k nearest neighbors (k=10)
  - Similarity threshold (> 0.7)
  - MMR diversity (lambda=0.5)
  - Hybrid ranking (similarity + recency + popularity)

### 4. Recommendation Engine (backend/services/content_recommendation_service.py)
- **Purpose**: Personalized content recommendation
- **Dependencies**: scikit-learn>=1.4.0
- **Key Features**:
  - User profile embedding (aggregate interactions)
  - Hybrid filtering (collaborative + content-based)
  - Cold start fallback (popularity-based)
  - Diversity sampling

### 5. Duplicate Detector (backend/services/duplicate_detection_service.py)
- **Purpose**: Duplicate question detection
- **Dependencies**: chromadb>=0.4.22
- **Key Features**:
  - Similarity threshold (> 0.95 = duplicate)
  - Exact match prevention
  - Near-duplicate flagging
  - Metadata merge

### 6. Concept Clusterer (backend/services/concept_clustering_service.py)
- **Purpose**: Concept grouping
- **Dependencies**: scikit-learn>=1.4.0, umap-learn>=0.5.5
- **Key Features**:
  - K-means / HDBSCAN clustering
  - Elbow method (optimal k)
  - Silhouette score (quality)
  - t-SNE/UMAP visualization

### 7. MCP Server (backend/mcp_servers/chromadb_mcp.py)
- **Purpose**: Standardized ChromaDB access
- **Dependencies**: mcp>=0.9.0
- **Key Features**:
  - Tools: search, add, update, delete
  - Rate limiting (100 req/min)
  - Health check
  - Prometheus metrics

## Data Flow

```
Text → EmbeddingService → ChromaDB → SemanticSearch → Results
                              ↓
                        DuplicateDetector
                              ↓
                      RecommendationEngine
```

## Correctness Properties

### Property 1: Embedding Consistency
```python
@given(text=st.text(min_size=1, max_size=1000))
def test_embedding_consistency(text):
    emb1 = embedding_service.embed(text)
    emb2 = embedding_service.embed(text)
    assert np.allclose(emb1, emb2, atol=1e-6)
```

### Property 2: Similarity Symmetry
```python
@given(text1=st.text(), text2=st.text())
def test_similarity_symmetry(text1, text2):
    sim12 = chromadb_service.similarity(text1, text2)
    sim21 = chromadb_service.similarity(text2, text1)
    assert abs(sim12 - sim21) < 1e-6
```

### Property 3: Duplicate Detection
```python
@given(text=st.text(min_size=10))
def test_duplicate_detection(text):
    chromadb_service.add(text)
    is_duplicate = duplicate_service.check(text)
    assert is_duplicate == True
```

### Property 4: Top-K Ordering
```python
@given(k=st.integers(min_value=1, max_value=100))
def test_topk_ordering(k):
    results = semantic_search.search(query, k=k)
    similarities = [r['similarity'] for r in results]
    assert similarities == sorted(similarities, reverse=True)
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Search latency | < 100ms | < 200ms |
| Embedding latency | < 50ms | < 100ms |
| Throughput | >= 1000 q/s | >= 500 q/s |
| Search accuracy | >= 90% | >= 80% |
| Duplicate detection | >= 95% | >= 90% |

## Security Considerations

- API key authentication (MCP server)
- Rate limiting (100 req/min)
- Input validation (max text length: 10000 chars)
- Metadata sanitization

## Scalability

- Horizontal scaling (ChromaDB sharding)
- Redis cache (reduce embedding compute)
- Batch processing (32 items)
- Quantization (reduce memory)

## Monitoring

- Search latency (P50, P95, P99)
- Cache hit rate (%)
- Duplicate detection rate (%)
- Recommendation CTR (%)
- Throughput (queries/sec)
