# Feature Flags ve Configuration Management Guide

## Genel Bakış

Bu doküman, video öneri sisteminin feature flag ve configuration management altyapısını açıklar.

### Özellikler

- ✅ **Feature Flags**: Özellikleri dinamik olarak açıp kapatma
- ✅ **Quality Thresholds**: Video kalite eşik değerlerini konfigüre etme
- ✅ **Performance Tuning**: Performance parametrelerini ayarlama
- ✅ **A/B Testing**: Farklı algoritmaları test etme
- ✅ **Environment-Specific**: Ortama göre farklı konfigürasyonlar
- ✅ **Runtime Updates**: Çalışma zamanında konfigürasyon değişikliği

## Mimari

```
┌─────────────────────────────────────────────────────────┐
│              Feature Flag Manager                        │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────┐  ┌──────────────────┐             │
│  │  Feature Flags  │  │ Quality          │             │
│  │  - Semantic     │  │ Thresholds       │             │
│  │  - Advanced     │  │ - Language: 0.8  │             │
│  │  - Hybrid       │  │ - Relevance: 0.7 │             │
│  │  - Filtering    │  │ - Difficulty: 0.5│             │
│  │  - Caching      │  │ - Overall: 0.7   │             │
│  └─────────────────┘  └──────────────────┘             │
│                                                           │
│  ┌─────────────────┐  ┌──────────────────┐             │
│  │  Performance    │  │ A/B Tests        │             │
│  │  Config         │  │ - Test ID        │             │
│  │  - Cache TTL    │  │ - Variants       │             │
│  │  - Parallel     │  │ - Traffic %      │             │
│  │  - Rate Limit   │  │ - Overrides      │             │
│  └─────────────────┘  └──────────────────┘             │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Kullanım

### 1. Feature Flag Kontrolü

```python
from backend.core.config_utils import is_feature_enabled, FeatureFlag

# Feature flag kontrolü
if is_feature_enabled(FeatureFlag.SEMANTIC_SEARCH):
    # Semantic search kullan
    results = await semantic_search.search(query)
else:
    # Advanced search kullan
    results = await advanced_search.search(query)
```

### 2. Quality Threshold Kullanımı

```python
from backend.core.config_utils import get_quality_thresholds

# Threshold'ları al
thresholds = get_quality_thresholds()

# Video filtreleme
if video.language_score >= thresholds.min_language_score:
    if video.relevance_score >= thresholds.min_relevance_score:
        # Video geçti
        filtered_videos.append(video)
```

### 3. Performance Config Kullanımı

```python
from backend.core.config_utils import get_performance_config

# Config al
config = get_performance_config()

# Cache TTL ayarla
cache.set(key, value, ttl=config.cache_ttl_seconds)

# Paralel arama sayısı
tasks = []
for i in range(config.max_parallel_searches):
    tasks.append(search_task(i))
```

### 4. A/B Testing

```python
from backend.core.config_utils import get_ab_test_variant

# Kullanıcı için variant al
variant = get_ab_test_variant('relevance_scoring_v2', user_id)

if variant and variant.name == 'treatment':
    # Yeni algoritma kullan
    score = ai_relevance_scorer.score(video)
else:
    # Mevcut algoritma kullan
    score = standard_relevance_scorer.score(video)
```

### 5. Kullanıcıya Özel Konfigürasyon

```python
from backend.core.config_utils import get_config_for_user

# Kullanıcıya özel tam config (A/B test overrides dahil)
config = get_config_for_user(user_id)

# Config kullan
if config['feature_flags']['ai_relevance_scoring']:
    # AI scoring kullan
    pass
```

## Feature Flag Listesi

### Video Discovery Features

| Flag | Açıklama | Production | Staging | Development |
|------|----------|------------|---------|-------------|
| `semantic_search` | Embedding tabanlı semantik arama | ✅ | ✅ | ✅ |
| `advanced_search` | Gelişmiş filtreli arama | ✅ | ✅ | ✅ |
| `hybrid_search` | Semantic + Advanced kombinasyon | ✅ | ✅ | ✅ |

### Filtering Features

| Flag | Açıklama | Production | Staging | Development |
|------|----------|------------|---------|-------------|
| `turkish_content_filter` | Türkçe içerik filtreleme | ✅ | ✅ | ✅ |
| `relevance_filter` | Konu alakalılık filtreleme | ✅ | ✅ | ✅ |
| `difficulty_filter` | Zorluk seviyesi filtreleme | ✅ | ✅ | ✅ |

### Cache Features

| Flag | Açıklama | Production | Staging | Development |
|------|----------|------------|---------|-------------|
| `multi_layer_cache` | Multi-layer cache (Memory + Redis) | ✅ | ✅ | ✅ |
| `cache_warming` | Cache ön yükleme | ✅ | ✅ | ❌ |
| `aggressive_caching` | Agresif cache stratejisi | ❌ | ✅ | ❌ |

### Performance Features

| Flag | Açıklama | Production | Staging | Development |
|------|----------|------------|---------|-------------|
| `parallel_discovery` | Paralel video discovery | ✅ | ✅ | ✅ |
| `circuit_breaker` | Circuit breaker pattern | ✅ | ✅ | ❌ |
| `rate_limiting` | API rate limiting | ✅ | ✅ | ❌ |

### Quality Features

| Flag | Açıklama | Production | Staging | Development |
|------|----------|------------|---------|-------------|
| `quality_scoring` | Video kalite skorlama | ✅ | ✅ | ✅ |
| `trusted_channels_boost` | Güvenilir kanallara bonus | ✅ | ✅ | ✅ |

### Monitoring Features

| Flag | Açıklama | Production | Staging | Development |
|------|----------|------------|---------|-------------|
| `detailed_logging` | Detaylı log toplama | ❌ | ✅ | ✅ |
| `metrics_collection` | Metrik toplama | ✅ | ✅ | ✅ |

### Experimental Features

| Flag | Açıklama | Production | Staging | Development |
|------|----------|------------|---------|-------------|
| `ai_relevance_scoring` | AI tabanlı alakalılık skorlama | ❌ | ✅ | ✅ |
| `personalized_ranking` | Kişiselleştirilmiş sıralama | ❌ | ✅ | ✅ |

## Quality Thresholds

### Language Detection

```python
{
    "min_score": 0.8,           # Minimum Türkçe güven skoru
    "turkish_char_weight": 0.3  # Türkçe karakter ağırlığı
}
```

### Relevance Scoring

```python
{
    "min_score": 0.7,           # Minimum alakalılık skoru
    "keyword_weight": 0.6,      # Ana konu eşleşme ağırlığı
    "subtopic_weight": 0.4      # Alt konu eşleşme ağırlığı
}
```

### Difficulty Matching

```python
{
    "min_match": 0.5,           # Minimum zorluk uyum skoru
    "tolerance": 1              # ±1 seviye toleransı
}
```

### Overall Quality

```python
{
    "min_score": 0.7,           # Minimum genel kalite skoru
    "language_weight": 0.3,     # Dil skoru ağırlığı
    "relevance_weight": 0.5,    # Alakalılık skoru ağırlığı
    "difficulty_weight": 0.2    # Zorluk uyum ağırlığı
}
```

## Performance Configuration

### Cache Settings

```python
{
    "ttl_seconds": 3600,        # Cache TTL (1 saat)
    "memory_size": 100,         # LRU cache boyutu
    "warming_enabled": true     # Cache warming aktif mi
}
```

### Parallel Processing

```python
{
    "max_searches": 3,          # Maksimum paralel arama
    "timeout_seconds": 5        # Arama timeout süresi
}
```

### Rate Limiting

```python
{
    "per_ip": 10,               # IP başına dakikada istek
    "per_user": 20,             # Kullanıcı başına dakikada istek
    "youtube_quota": 10000      # Günlük YouTube API quota
}
```

### Circuit Breaker

```python
{
    "failure_threshold": 5,     # Açılma eşiği
    "timeout_seconds": 60,      # Timeout süresi
    "success_threshold": 2      # Kapanma eşiği
}
```

## A/B Testing

### A/B Test Tanımlama

```json
{
  "test_id": "relevance_scoring_v2",
  "name": "Relevance Scoring Algorithm V2",
  "description": "Test yeni alakalılık skorlama algoritması",
  "variants": [
    {
      "name": "control",
      "description": "Mevcut algoritma",
      "traffic_percentage": 50,
      "config_overrides": {},
      "enabled": true
    },
    {
      "name": "treatment",
      "description": "Yeni algoritma (AI-based)",
      "traffic_percentage": 50,
      "config_overrides": {
        "ai_relevance_scoring": true,
        "relevance_weight": 0.6
      },
      "enabled": true
    }
  ],
  "start_date": "2025-11-01T00:00:00",
  "end_date": "2025-12-01T00:00:00",
  "enabled": true
}
```

### A/B Test Kullanımı

```python
# Kullanıcı için variant al
variant = get_ab_test_variant('relevance_scoring_v2', user_id)

if variant:
    print(f"User {user_id} is in variant: {variant.name}")
    
    # Config overrides uygula
    if 'ai_relevance_scoring' in variant.config_overrides:
        use_ai_scoring = variant.config_overrides['ai_relevance_scoring']
```

### Consistent Hashing

A/B test varyant ataması consistent hashing kullanır:
- Aynı kullanıcı her zaman aynı varyanta atanır
- Test ID + User ID hash'lenerek variant belirlenir
- Traffic percentage'a göre dağılım yapılır

## API Endpoints

### Configuration Summary

```bash
GET /api/config/summary
```

Response:
```json
{
  "environment": "production",
  "enabled_features": ["semantic_search", "advanced_search", ...],
  "disabled_features": ["ai_relevance_scoring", ...],
  "quality_thresholds": {...},
  "performance_config": {...},
  "active_ab_tests": [...]
}
```

### Feature Flags

```bash
GET /api/config/features
```

### Quality Thresholds

```bash
GET /api/config/quality-thresholds
```

### Performance Config

```bash
GET /api/config/performance
```

### User Config

```bash
GET /api/config/user/{user_id}
```

### A/B Test Variant

```bash
GET /api/config/ab-tests/{test_id}/variant/{user_id}
```

## Environment Variables

```bash
# Environment seçimi
ENVIRONMENT=production  # production, staging, development, test

# Custom config dosyası (opsiyonel)
FEATURE_FLAGS_CONFIG=/path/to/custom/config.json
```

## Configuration Dosyaları

### Dosya Konumları

```
backend/config/
├── feature_flags_production.json
├── feature_flags_staging.json
├── feature_flags_development.json
└── feature_flags_test.json
```

### Dosya Formatı

```json
{
  "environment": "production",
  "feature_flags": {
    "semantic_search": true,
    "advanced_search": true,
    ...
  },
  "quality_thresholds": {
    "language": {...},
    "relevance": {...},
    ...
  },
  "performance_config": {
    "cache": {...},
    "parallel": {...},
    ...
  },
  "ab_tests": [...]
}
```

## Best Practices

### 1. Feature Flag Kullanımı

```python
# ✅ İyi
if is_feature_enabled(FeatureFlag.SEMANTIC_SEARCH):
    result = await semantic_search()

# ❌ Kötü - Hard-coded
if True:  # Always use semantic search
    result = await semantic_search()
```

### 2. Threshold Kullanımı

```python
# ✅ İyi
thresholds = get_quality_thresholds()
if score >= thresholds.min_relevance_score:
    pass

# ❌ Kötü - Magic number
if score >= 0.7:
    pass
```

### 3. A/B Test Logging

```python
# ✅ İyi - Variant bilgisini logla
variant = get_ab_test_variant(test_id, user_id)
logger.info(
    "ab_test_variant_assigned",
    test_id=test_id,
    user_id=user_id,
    variant=variant.name
)

# Metrik kaydet
metrics.record_ab_test_assignment(test_id, user_id, variant.name)
```

### 4. Graceful Degradation

```python
# ✅ İyi - Feature kapalıysa fallback
if is_feature_enabled(FeatureFlag.SEMANTIC_SEARCH):
    try:
        result = await semantic_search()
    except Exception:
        # Fallback to advanced search
        result = await advanced_search()
else:
    result = await advanced_search()
```

## Troubleshooting

### Config Yüklenmiyor

```python
# Config dosyasını kontrol et
import os
from backend.core.feature_flags import get_feature_flag_manager

manager = get_feature_flag_manager()
print(f"Config file: {manager.config_file}")
print(f"File exists: {os.path.exists(manager.config_file)}")
```

### Feature Flag Çalışmıyor

```python
# Feature flag durumunu kontrol et
from backend.core.config_utils import is_feature_enabled, FeatureFlag

flag = FeatureFlag.SEMANTIC_SEARCH
enabled = is_feature_enabled(flag)
print(f"{flag.value}: {enabled}")
```

### A/B Test Variant Atanmıyor

```python
# A/B test durumunu kontrol et
from backend.core.feature_flags import get_feature_flag_manager

manager = get_feature_flag_manager()
test = manager.ab_tests.get('test_id')

if test:
    print(f"Test enabled: {test.enabled}")
    print(f"Start date: {test.start_date}")
    print(f"End date: {test.end_date}")
else:
    print("Test not found")
```

## Monitoring

### Metrics

```python
# Feature flag kullanım metrikleri
metrics.record_feature_flag_usage(flag_name, enabled)

# A/B test assignment metrikleri
metrics.record_ab_test_assignment(test_id, user_id, variant_name)

# Config değişiklik metrikleri
metrics.record_config_change(config_key, old_value, new_value)
```

### Logging

```python
# Feature flag değişikliği
logger.info(
    "feature_flag_changed",
    flag=flag_name,
    old_value=old_enabled,
    new_value=new_enabled
)

# A/B test başlatma
logger.info(
    "ab_test_started",
    test_id=test_id,
    variants=len(variants)
)
```

## Örnek Senaryolar

### Senaryo 1: Yeni Algoritma Test Etme

```python
# 1. A/B test tanımla (config dosyasında)
# 2. Kodda variant kontrolü yap
variant = get_ab_test_variant('new_algorithm_test', user_id)

if variant and variant.name == 'treatment':
    result = new_algorithm(data)
else:
    result = old_algorithm(data)

# 3. Metrikleri topla
metrics.record_algorithm_performance(
    variant=variant.name,
    response_time=response_time,
    quality_score=quality_score
)
```

### Senaryo 2: Performance Tuning

```python
# 1. Staging'de threshold'ları düşür
# staging config: min_relevance_score = 0.65

# 2. Test et ve metrikleri gözlemle
# 3. Başarılıysa production'a uygula
# production config: min_relevance_score = 0.65
```

### Senaryo 3: Feature Rollout

```python
# 1. Development'ta test et (feature enabled)
# 2. Staging'e deploy et (feature enabled)
# 3. Production'da A/B test ile %10 traffic
# 4. Başarılıysa %100'e çıkar
# 5. Feature flag'i kaldır (artık default)
```

## Sonuç

Feature flag ve configuration management sistemi:
- ✅ Dinamik feature kontrolü
- ✅ Environment-specific konfigürasyon
- ✅ A/B testing altyapısı
- ✅ Runtime configuration updates
- ✅ Graceful degradation
- ✅ Comprehensive monitoring

Bu sistem sayesinde video öneri algoritmasını güvenli bir şekilde test edebilir ve optimize edebilirsiniz.
