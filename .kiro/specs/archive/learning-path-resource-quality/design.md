# Design Document

## Overview

Bu tasarım, Learning Path sayfasındaki "Size Özel Kaynaklar" bölümünde gösterilen video kaynaklarının kalitesini artırmak için kapsamlı bir filtreleme ve doğrulama sistemi oluşturur. Sistem üç ana katmandan oluşur:

1. **Content Validation Layer**: Türkçe içerik ve konu uygunluğu kontrolü
2. **Quality Assurance Layer**: Video erişilebilirlik ve kalite doğrulaması
3. **Recommendation Engine Layer**: Skorlama ve sıralama

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│                  LearningPathPage.tsx                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API Layer                               │
│         /api/learning-path/search-resources                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          Enhanced Resource Recommendation Engine             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Turkish    │  │   Subject    │  │    Video     │     │
│  │   Content    │  │  Relevance   │  │   Quality    │     │
│  │   Filter     │  │   Scorer     │  │  Validator   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              YouTube Integration Service                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  YouTube API │  │   Semantic   │  │    Cache     │     │
│  │   Client     │  │    Search    │  │   Manager    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Component Flow

```
1. Öğrenci Learning Path sayfasını açar
   ↓
2. Frontend, öğrenci profili ve modül bilgilerini backend'e gönderir
   ↓
3. Enhanced Resource Recommendation Engine devreye girer
   ↓
4. YouTube Integration Service'den video adayları alınır
   ↓
5. Turkish Content Filter: Türkçe kontrolü yapar
   ↓
6. Subject Relevance Scorer: Konu uygunluğunu skorlar
   ↓
7. Video Quality Validator: Erişilebilirlik kontrolü yapar
   ↓
8. Tüm skorlar birleştirilerek final sıralama yapılır
   ↓
9. En iyi N video frontend'e döndürülür
   ↓
10. VideoResourceGrid bileşeni videoları gösterir
```

## Components and Interfaces

### 1. Turkish Content Filter

**Sorumluluk**: Video içeriğinin Türkçe olup olmadığını doğrular

**Interface**:
```python
class TurkishContentFilter:
    async def validate_turkish_content(
        self,
        video_title: str,
        video_description: str,
        channel_name: str
    ) -> TurkishValidationResult:
        """
        Video içeriğinin Türkçe olup olmadığını doğrular
        
        Returns:
            TurkishValidationResult(
                is_turkish: bool,
                confidence_score: float,  # 0.0-1.0
                detected_language: str,
                turkish_indicators: List[str]
            )
        """
        pass
    
    def calculate_turkish_score(
        self,
        text: str,
        channel_name: str
    ) -> float:
        """
        Türkçe içerik skoru hesaplar
        
        Scoring Factors:
        - Türkçe karakterler (ç, ğ, ı, ş, ü, ö): +0.2
        - Türkçe eğitim kelimeleri: +0.3
        - Güvenilir Türkçe kanal: +0.3
        - Dil tespiti (langdetect): +0.2
        
        Returns:
            float: 0.0-1.0 arası skor
        """
        pass
    
    def is_trusted_turkish_channel(self, channel_name: str) -> bool:
        """Güvenilir Türkçe eğitim kanalı kontrolü"""
        pass
```

**Trusted Turkish Channels**:
```python
TRUSTED_TURKISH_CHANNELS = {
    'TonguçAkademi': {'weight': 1.0, 'subjects': ['matematik', 'fizik', 'kimya']},
    'Khan Academy Türkçe': {'weight': 1.0, 'subjects': ['matematik', 'fizik']},
    'KAMP Online': {'weight': 0.95, 'subjects': ['matematik', 'fizik', 'kimya']},
    'Hocalara Geldik': {'weight': 0.9, 'subjects': ['matematik', 'fizik']},
    'MEB Uzaktan Eğitim': {'weight': 0.85, 'subjects': 'all'},
    'BTK Akademi': {'weight': 0.9, 'subjects': ['bilgisayar', 'teknoloji']},
    'Evrim Ağacı': {'weight': 0.85, 'subjects': ['biyoloji', 'fen']}
}
```

**Turkish Detection Logic**:
```python
def detect_turkish_content(text: str) -> float:
    score = 0.0
    
    # 1. Türkçe karakterler
    turkish_chars = ['ç', 'ğ', 'ı', 'ş', 'ü', 'ö']
    char_count = sum(1 for char in turkish_chars if char in text.lower())
    score += min(char_count * 0.05, 0.2)
    
    # 2. Türkçe eğitim kelimeleri
    turkish_edu_words = [
        'konu', 'ders', 'anlatım', 'öğretmen', 'sınav', 
        'türkçe', 'matematik', 'fizik', 'kimya', 'biyoloji',
        'çözüm', 'soru', 'test', 'örnek', 'açıklama'
    ]
    word_count = sum(1 for word in turkish_edu_words if word in text.lower())
    score += min(word_count * 0.05, 0.3)
    
    # 3. Dil tespiti (langdetect kütüphanesi)
    try:
        from langdetect import detect
        if detect(text) == 'tr':
            score += 0.2
    except:
        pass
    
    return min(score, 1.0)
```

### 2. Subject Relevance Scorer

**Sorumluluk**: Video içeriğinin ders ve konu ile uygunluğunu skorlar

**Interface**:
```python
class SubjectRelevanceScorer:
    def __init__(self):
        self.semantic_matcher = SemanticMatcher()
        self.subject_keywords = self._load_subject_keywords()
    
    async def calculate_relevance_score(
        self,
        video_title: str,
        video_description: str,
        video_tags: List[str],
        target_subject: str,
        target_topic: Optional[str] = None
    ) -> RelevanceScore:
        """
        Video'nun konu ile uygunluk skorunu hesaplar
        
        Returns:
            RelevanceScore(
                overall_score: float,  # 0.0-1.0
                subject_match: float,
                topic_match: float,
                semantic_similarity: float,
                keyword_overlap: float
            )
        """
        pass
    
    def _calculate_keyword_overlap(
        self,
        video_text: str,
        subject: str,
        topic: Optional[str]
    ) -> float:
        """Anahtar kelime örtüşme oranı"""
        pass
    
    async def _calculate_semantic_similarity(
        self,
        video_text: str,
        subject: str,
        topic: Optional[str]
    ) -> float:
        """Embedding tabanlı semantik benzerlik"""
        pass
```

**Subject Keywords Mapping**:
```python
SUBJECT_KEYWORDS = {
    'matematik': {
        'core': ['matematik', 'sayı', 'fonksiyon', 'türev', 'integral', 'limit'],
        'topics': {
            'türev': ['türev', 'diferansiyel', 'eğim', 'teğet'],
            'integral': ['integral', 'alan', 'hacim', 'belirsiz'],
            'limit': ['limit', 'süreklilik', 'yakınsama']
        }
    },
    'fizik': {
        'core': ['fizik', 'kuvvet', 'hareket', 'enerji', 'elektrik'],
        'topics': {
            'hareket': ['hız', 'ivme', 'yol', 'zaman', 'kinematik'],
            'kuvvet': ['newton', 'kütle', 'ağırlık', 'sürtünme'],
            'enerji': ['iş', 'güç', 'potansiyel', 'kinetik']
        }
    },
    'kimya': {
        'core': ['kimya', 'atom', 'molekül', 'reaksiyon', 'element'],
        'topics': {
            'atom': ['proton', 'nötron', 'elektron', 'periyodik'],
            'reaksiyon': ['asit', 'baz', 'oksidasyon', 'indirgenme']
        }
    }
}
```

**Relevance Scoring Algorithm**:
```python
def calculate_relevance_score(
    video_text: str,
    subject: str,
    topic: Optional[str]
) -> float:
    score = 0.0
    
    # 1. Subject keyword match (40%)
    subject_keywords = SUBJECT_KEYWORDS.get(subject, {}).get('core', [])
    subject_matches = sum(1 for kw in subject_keywords if kw in video_text.lower())
    score += (subject_matches / len(subject_keywords)) * 0.4
    
    # 2. Topic keyword match (30%)
    if topic:
        topic_keywords = SUBJECT_KEYWORDS.get(subject, {}).get('topics', {}).get(topic, [])
        if topic_keywords:
            topic_matches = sum(1 for kw in topic_keywords if kw in video_text.lower())
            score += (topic_matches / len(topic_keywords)) * 0.3
    else:
        score += 0.15  # Partial score if no specific topic
    
    # 3. Semantic similarity (30%)
    semantic_score = semantic_matcher.calculate_similarity(video_text, subject, topic)
    score += semantic_score * 0.3
    
    return min(score, 1.0)
```

### 3. Video Quality Validator

**Sorumluluk**: Video erişilebilirliği ve kalitesini doğrular

**Interface**:
```python
class VideoQualityValidator:
    def __init__(self):
        self.youtube_client = YouTubeAPIClient()
        self.cache_manager = CacheManager()
    
    async def validate_video_accessibility(
        self,
        video_id: str
    ) -> VideoAccessibilityResult:
        """
        Video erişilebilirliğini kontrol eder
        
        Returns:
            VideoAccessibilityResult(
                is_accessible: bool,
                is_embeddable: bool,
                privacy_status: str,  # public, private, unlisted
                error_reason: Optional[str]
            )
        """
        pass
    
    async def calculate_quality_score(
        self,
        video_metadata: Dict[str, Any]
    ) -> float:
        """
        Video kalite skoru hesaplar
        
        Quality Factors:
        - View count (normalized): 0-0.2
        - Like ratio: 0-0.2
        - Duration (5-60 min ideal): 0-0.2
        - Caption availability: 0-0.1
        - HD quality: 0-0.1
        - Channel trust: 0-0.2
        
        Returns:
            float: 0.0-1.0 arası skor
        """
        pass
    
    async def batch_validate_videos(
        self,
        video_ids: List[str],
        timeout_seconds: int = 5
    ) -> Dict[str, VideoAccessibilityResult]:
        """Toplu video doğrulama (paralel)"""
        pass
```

**Quality Scoring Algorithm**:
```python
def calculate_quality_score(video_metadata: Dict) -> float:
    score = 0.0
    
    # 1. View count (normalized, 0-0.2)
    view_count = video_metadata.get('view_count', 0)
    if 10000 <= view_count <= 500000:
        score += 0.2
    elif 5000 <= view_count < 10000 or 500000 < view_count <= 1000000:
        score += 0.15
    elif view_count > 1000000:
        score += 0.1  # Çok popüler videolar eğitim odaklı olmayabilir
    
    # 2. Like ratio (0-0.2)
    like_count = video_metadata.get('like_count', 0)
    if view_count > 0:
        like_ratio = like_count / view_count
        if like_ratio > 0.02:  # %2+
            score += 0.2
        elif like_ratio > 0.01:  # %1-2
            score += 0.15
        elif like_ratio > 0.005:  # %0.5-1
            score += 0.1
    
    # 3. Duration (0-0.2)
    duration_minutes = video_metadata.get('duration_minutes', 0)
    if 5 <= duration_minutes <= 60:
        score += 0.2
    elif 3 <= duration_minutes < 5 or 60 < duration_minutes <= 90:
        score += 0.1
    
    # 4. Caption availability (0-0.1)
    if video_metadata.get('caption_available', False):
        score += 0.1
    
    # 5. HD quality (0-0.1)
    if video_metadata.get('definition', '') == 'hd':
        score += 0.1
    
    # 6. Channel trust (0-0.2)
    channel_name = video_metadata.get('channel_name', '')
    if channel_name in TRUSTED_TURKISH_CHANNELS:
        score += 0.2
    
    return min(score, 1.0)
```

### 4. Enhanced Resource Recommendation Engine

**Sorumluluk**: Tüm filtreleri ve skorları birleştirerek final önerileri oluşturur

**Interface**:
```python
class EnhancedResourceRecommendationEngine:
    def __init__(self):
        self.turkish_filter = TurkishContentFilter()
        self.relevance_scorer = SubjectRelevanceScorer()
        self.quality_validator = VideoQualityValidator()
        self.youtube_service = YouTubeIntegrationService()
    
    async def get_recommended_videos(
        self,
        subject: str,
        topic: Optional[str],
        difficulty: str,
        max_results: int = 10,
        student_profile: Optional[Dict] = None
    ) -> List[RecommendedVideo]:
        """
        Filtrelenmiş ve skorlanmış video önerileri döner
        
        Pipeline:
        1. YouTube'dan aday videolar al (max_results * 3)
        2. Türkçe filtresi uygula (min score: 0.7)
        3. Konu uygunluğu skorla (min score: 0.6)
        4. Erişilebilirlik doğrula
        5. Kalite skorla
        6. Final skorlama ve sıralama
        7. Top N video döndür
        
        Returns:
            List[RecommendedVideo]: Skorlanmış ve sıralanmış videolar
        """
        pass
    
    def _calculate_final_score(
        self,
        turkish_score: float,
        relevance_score: float,
        quality_score: float,
        accessibility_ok: bool
    ) -> float:
        """
        Final skor hesaplama
        
        Weights:
        - Turkish score: 25%
        - Relevance score: 40%
        - Quality score: 25%
        - Accessibility: 10% (bonus if OK)
        """
        if not accessibility_ok:
            return 0.0
        
        final_score = (
            turkish_score * 0.25 +
            relevance_score * 0.40 +
            quality_score * 0.25 +
            0.10  # Accessibility bonus
        )
        
        return final_score
```

## Data Models

### RecommendedVideo

```python
@dataclass
class RecommendedVideo:
    video_id: str
    title: str
    channel_name: str
    channel_id: str
    description: str
    thumbnail_url: str
    duration: str
    duration_minutes: int
    view_count: int
    like_count: int
    upload_date: str
    url: str
    
    # Scores
    turkish_score: float
    relevance_score: float
    quality_score: float
    final_score: float
    
    # Validation
    is_accessible: bool
    is_embeddable: bool
    is_turkish: bool
    
    # Metadata
    tags: List[str]
    caption_available: bool
    definition: str  # 'hd' or 'sd'
```

### TurkishValidationResult

```python
@dataclass
class TurkishValidationResult:
    is_turkish: bool
    confidence_score: float
    detected_language: str
    turkish_indicators: List[str]
```

### RelevanceScore

```python
@dataclass
class RelevanceScore:
    overall_score: float
    subject_match: float
    topic_match: float
    semantic_similarity: float
    keyword_overlap: float
```

### VideoAccessibilityResult

```python
@dataclass
class VideoAccessibilityResult:
    is_accessible: bool
    is_embeddable: bool
    privacy_status: str
    error_reason: Optional[str]
```

## Error Handling

### 1. YouTube API Errors

```python
class YouTubeAPIErrorHandler:
    async def handle_api_error(self, error: Exception) -> FallbackResponse:
        if isinstance(error, QuotaExceededError):
            # Fallback to cached videos
            return await self.get_cached_videos()
        
        elif isinstance(error, InvalidAPIKeyError):
            # Log critical error, use mock data
            logger.critical("Invalid YouTube API key")
            return await self.get_mock_videos()
        
        elif isinstance(error, RateLimitError):
            # Wait and retry with exponential backoff
            await asyncio.sleep(2 ** retry_count)
            return await self.retry_request()
        
        else:
            # Generic error handling
            logger.error(f"YouTube API error: {error}")
            return await self.get_fallback_videos()
```

### 2. Validation Failures

```python
class ValidationErrorHandler:
    def handle_validation_failure(
        self,
        video_id: str,
        failure_type: str
    ) -> None:
        """
        Validation başarısızlıklarını logla ve alternatif ara
        
        Failure Types:
        - turkish_filter_failed
        - relevance_too_low
        - accessibility_failed
        - quality_too_low
        """
        logger.warning(f"Video {video_id} failed {failure_type}")
        
        # Metrics için kaydet
        self.metrics_collector.record_failure(video_id, failure_type)
        
        # Alternatif video ara
        return self.find_alternative_video()
```

### 3. Timeout Handling

```python
class TimeoutHandler:
    async def with_timeout(
        self,
        coro: Coroutine,
        timeout_seconds: int = 5
    ) -> Any:
        """Timeout ile async işlem yürüt"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout_seconds}s")
            return None
```

## Testing Strategy

### 1. Unit Tests

```python
# test_turkish_content_filter.py
async def test_turkish_content_detection():
    filter = TurkishContentFilter()
    
    # Test 1: Türkçe video
    result = await filter.validate_turkish_content(
        "Matematik Türev Konu Anlatımı",
        "Bu videoda türev konusunu detaylı şekilde işliyoruz",
        "TonguçAkademi"
    )
    assert result.is_turkish == True
    assert result.confidence_score > 0.7
    
    # Test 2: İngilizce video
    result = await filter.validate_turkish_content(
        "Calculus Tutorial - Derivatives",
        "In this video we explain derivatives",
        "Khan Academy"
    )
    assert result.is_turkish == False

# test_subject_relevance_scorer.py
async def test_relevance_scoring():
    scorer = SubjectRelevanceScorer()
    
    # Test 1: Yüksek uygunluk
    score = await scorer.calculate_relevance_score(
        "Matematik Türev Konu Anlatımı",
        "Türev konusunda detaylı açıklama",
        ["matematik", "türev", "konu"],
        "matematik",
        "türev"
    )
    assert score.overall_score > 0.8
    
    # Test 2: Düşük uygunluk
    score = await scorer.calculate_relevance_score(
        "Fizik Hareket Konusu",
        "Fizik dersi hareket",
        ["fizik", "hareket"],
        "matematik",
        "türev"
    )
    assert score.overall_score < 0.4

# test_video_quality_validator.py
async def test_video_accessibility():
    validator = VideoQualityValidator()
    
    # Test 1: Erişilebilir video
    result = await validator.validate_video_accessibility("valid_video_id")
    assert result.is_accessible == True
    assert result.is_embeddable == True
    
    # Test 2: Erişilemeyen video
    result = await validator.validate_video_accessibility("invalid_video_id")
    assert result.is_accessible == False
```

### 2. Integration Tests

```python
# test_recommendation_engine_integration.py
async def test_full_recommendation_pipeline():
    engine = EnhancedResourceRecommendationEngine()
    
    # Test: Matematik türev için öneri al
    videos = await engine.get_recommended_videos(
        subject="matematik",
        topic="türev",
        difficulty="orta",
        max_results=5
    )
    
    # Assertions
    assert len(videos) > 0
    assert all(v.is_turkish for v in videos)
    assert all(v.is_accessible for v in videos)
    assert all(v.relevance_score > 0.6 for v in videos)
    assert all(v.turkish_score > 0.7 for v in videos)
    
    # Sıralama kontrolü
    scores = [v.final_score for v in videos]
    assert scores == sorted(scores, reverse=True)
```

### 3. Performance Tests

```python
# test_performance.py
async def test_recommendation_performance():
    engine = EnhancedResourceRecommendationEngine()
    
    start_time = time.time()
    videos = await engine.get_recommended_videos(
        subject="matematik",
        topic="türev",
        difficulty="orta",
        max_results=10
    )
    end_time = time.time()
    
    # Performance assertion: < 5 saniye
    assert (end_time - start_time) < 5.0
    assert len(videos) > 0
```

## Performance Considerations

### 1. Caching Strategy

```python
class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.cache_ttl = 3600  # 1 saat
    
    async def get_cached_videos(
        self,
        cache_key: str
    ) -> Optional[List[RecommendedVideo]]:
        """Cache'den video önerilerini al"""
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            return pickle.loads(cached_data)
        return None
    
    async def cache_videos(
        self,
        cache_key: str,
        videos: List[RecommendedVideo]
    ) -> None:
        """Video önerilerini cache'e kaydet"""
        await self.redis_client.setex(
            cache_key,
            self.cache_ttl,
            pickle.dumps(videos)
        )
```

### 2. Parallel Processing

```python
async def batch_validate_videos(video_ids: List[str]) -> Dict[str, VideoAccessibilityResult]:
    """Videoları paralel olarak doğrula"""
    tasks = [validate_video_accessibility(vid) for vid in video_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        video_id: result
        for video_id, result in zip(video_ids, results)
        if not isinstance(result, Exception)
    }
```

### 3. Rate Limiting

```python
class RateLimiter:
    def __init__(self, max_requests_per_second: int = 10):
        self.max_requests = max_requests_per_second
        self.request_times = []
    
    async def acquire(self):
        """Rate limit kontrolü"""
        now = time.time()
        
        # Eski istekleri temizle
        self.request_times = [t for t in self.request_times if now - t < 1.0]
        
        # Limit kontrolü
        if len(self.request_times) >= self.max_requests:
            wait_time = 1.0 - (now - self.request_times[0])
            await asyncio.sleep(wait_time)
        
        self.request_times.append(now)
```

## Security Considerations

1. **API Key Protection**: YouTube API anahtarı environment variable'da saklanır
2. **Input Validation**: Tüm kullanıcı girdileri sanitize edilir
3. **Rate Limiting**: API abuse'ü önlemek için rate limiting uygulanır
4. **Error Masking**: Detaylı hata mesajları kullanıcıya gösterilmez
5. **CORS Policy**: Sadece izin verilen origin'lerden isteklere izin verilir
