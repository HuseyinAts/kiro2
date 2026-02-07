---
name: perf-analysis
description: Kod performans analizi ve optimizasyon önerileri sunar. Database query analizi, API response time, memory profiling ve bottleneck tespiti yapar.
context: fork
model: sonnet
allowed-tools: Read, Grep, Glob, Bash
---

# Performance Analysis: $ARGUMENTS

Bu skill, belirtilen kod veya sistem için performans analizi yapar.

## Analiz Kategorileri

### 1. Database Performance
- Query execution time
- N+1 query detection
- Missing index analizi
- Connection pool durumu
- Slow query log analizi

### 2. API Performance
- Response time (p50, p95, p99)
- Throughput (req/sec)
- Error rate
- Payload size
- Caching effectiveness

### 3. Memory Performance
- Memory leaks
- Garbage collection
- Object allocation
- Cache memory usage

### 4. CPU Performance
- Hot paths
- Algorithm complexity
- Async/blocking operations
- Thread utilization

## Analiz Protokolü

### Adım 1: Metrik Toplama
```bash
# Database slow queries
EXPLAIN ANALYZE SELECT ...

# API timing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/endpoint

# Memory profiling
python -m memory_profiler script.py

# CPU profiling
python -m cProfile -o output.prof script.py
```

### Adım 2: Bottleneck Tespiti
```
Kontrol Listesi:
- [ ] Database queries (EXPLAIN ANALYZE)
- [ ] I/O operations (disk, network)
- [ ] Memory allocation patterns
- [ ] Algorithm complexity (Big O)
- [ ] Blocking operations in async code
- [ ] Missing caching opportunities
- [ ] Unnecessary serialization
```

### Adım 3: Root Cause Analizi
Her bottleneck için:
- Nerede oluşuyor?
- Neden oluşuyor?
- Impact nedir?
- Çözüm önerisi

## Çıktı Formatı

```markdown
## Performance Analysis: $ARGUMENTS

### Özet
| Metrik | Mevcut | Hedef | Durum |
|--------|--------|-------|-------|
| Response Time (p95) | 850ms | <500ms | ❌ |
| Throughput | 100 req/s | >200 req/s | ❌ |
| Memory Usage | 2GB | <1GB | ❌ |
| Error Rate | 0.5% | <0.1% | ⚠️ |

### Tespit Edilen Sorunlar

#### P0: Kritik (Hemen Düzelt)
1. **N+1 Query**: `backend/services/question_service.py:142`
   - **Impact**: 10x yavaşlama
   - **Çözüm**: `select_related()` / `prefetch_related()` kullan

#### P1: Yüksek (Sprint İçinde)
2. **Missing Index**: `questions` tablosu `subject_id` kolonu
   - **Impact**: Full table scan
   - **Çözüm**: `CREATE INDEX idx_questions_subject ON questions(subject_id)`

#### P2: Orta (Planla)
3. **Blocking I/O**: `backend/services/video_service.py:89`
   - **Impact**: Thread block
   - **Çözüm**: `aiohttp` ile async yap

### Optimizasyon Önerileri

1. **Database**
   - [ ] Index ekle: `subject_id`, `difficulty`
   - [ ] Query cache aktif et
   - [ ] Connection pool size: 10 → 20

2. **Caching**
   - [ ] Redis cache TTL: 5min → 15min
   - [ ] Static content CDN'e taşı
   - [ ] API response caching ekle

3. **Code**
   - [ ] Async/await pattern düzelt
   - [ ] Lazy loading implementasyonu
   - [ ] Pagination ekle

### Tahmini İyileştirme
| Aksiyon | Response Time | Effort |
|---------|---------------|--------|
| Index ekle | -40% | Low |
| N+1 fix | -30% | Medium |
| Cache optimize | -20% | Low |
| **TOPLAM** | **-70%** | - |
```

## KIRO2 Spesifik Analiz

### IRT Hesaplama Performansı
```python
# Mevcut: O(n²) - her öğrenci × her soru
# Hedef: O(n) - vektörize hesaplama

# Kontrol et:
- numpy broadcasting kullanımı
- Batch processing
- Pre-computed parameters
```

### Video Streaming
```
Kontrol:
- [ ] Chunk size optimal mı? (1-4MB)
- [ ] Adaptive bitrate aktif mi?
- [ ] Buffer strategy doğru mu?
```

### Elasticsearch Queries
```
Kontrol:
- [ ] Query complexity
- [ ] Shard distribution
- [ ] Cache hit rate
- [ ] Aggregation performance
```

## Örnek Kullanım

```bash
# Belirli endpoint
/perf-analysis "GET /api/v1/questions"

# Belirli servis
/perf-analysis backend/services/learning_path_service.py

# Database tablo
/perf-analysis "questions table query performance"

# Genel sistem
/perf-analysis "overall API performance"
```

## Benchmark Komutları

```bash
# API benchmark
ab -n 1000 -c 10 http://localhost:8000/api/v1/health

# Database benchmark
pgbench -c 10 -j 2 -t 100 kiro2

# Memory profiling
mprof run python script.py
mprof plot

# CPU profiling
py-spy record -o profile.svg -- python script.py
```

## Performans Hedefleri (KIRO2)

| Endpoint | Target p95 | Target p99 |
|----------|------------|------------|
| Health check | <50ms | <100ms |
| Question list | <200ms | <500ms |
| Exam submit | <500ms | <1000ms |
| Learning path | <1000ms | <2000ms |
| Report generate | <5000ms | <10000ms |

## Notlar

- Bu skill Sonnet model kullanır
- İzole context'te çalışır
- Production ortamda dikkatli kullan
- Profiling overhead'i göz önünde bulundur
