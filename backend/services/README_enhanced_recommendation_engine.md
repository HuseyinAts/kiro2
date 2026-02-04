# Enhanced Resource Recommendation Engine

## Genel Bakış

Enhanced Resource Recommendation Engine, Learning Path sayfasındaki "Size Özel Kaynaklar" bölümü için kaliteli ve uygun video önerileri oluşturan gelişmiş bir sistemdir.

## Özellikler

### 1. Çok Katmanlı Filtreleme Pipeline'ı

```
YouTube Arama → Türkçe Filtresi → Konu Uygunluğu → Erişilebilirlik → Kalite Skorlama → Sıralama
```

### 2. Entegre Bileşenler

- **TurkishContentFilter**: Video içeriğinin Türkçe olup olmadığını doğrular
- **SubjectRelevanceScorer**: Video'nun ders ve konu ile uygunluğunu skorlar
- **VideoQualityValidator**: Video erişilebilirliği ve kalitesini kontrol eder
- **YouTubeService**: YouTube API entegrasyonu

### 3. Skorlama Sistemi

Final skor hesaplama ağırlıkları:
- Türkçe skoru: %25
- Konu uygunluğu: %40
- Kalite skoru: %25
- Erişilebilirlik: %10

### 4. Threshold Değerleri

- Minimum Türkçe skoru: 0.7
- Minimum uygunluk skoru: 0.6
- Minimum kalite skoru: 0.3

## Kullanım

```python
from backend.services.enhanced_resource_recommendation_engine import (
    get_enhanced_recommendation_engine
)

# Engine instance'ını al
engine = await get_enhanced_recommendation_engine()

# Video önerileri al
videos = await engine.get_recommended_videos(
    subject="matematik",
    topic="türev",
    difficulty="orta",
    max_results=10
)

# Sonuçları kullan
for video in videos:
    print(f"{video.title} - Score: {video.final_score:.2f}")
    print(f"  Turkish: {video.turkish_score:.2f}")
    print(f"  Relevance: {video.relevance_score:.2f}")
    print(f"  Quality: {video.quality_score:.2f}")
```

## RecommendedVideo Model

```python
@dataclass
class RecommendedVideo:
    # Temel bilgiler
    video_id: str
    title: str
    channel_name: str
    description: str
    thumbnail_url: str
    url: str
    
    # Skorlar
    turkish_score: float
    relevance_score: float
    quality_score: float
    final_score: float
    
    # Doğrulama
    is_accessible: bool
    is_embeddable: bool
    is_turkish: bool
    
    # Metadata
    duration_minutes: int
    view_count: int
    like_count: int
    tags: List[str]
    caption_available: bool
```

## Pipeline Detayları

### 1. Aday Video Toplama
- YouTube'dan `max_results * 3` adet video aranır
- Eğitim kategorisi ve dil filtreleri uygulanır

### 2. Türkçe Filtresi
- Video başlığı ve açıklaması analiz edilir
- Türkçe karakterler ve kelimeler kontrol edilir
- Güvenilir Türkçe kanallar bonus puan alır
- Minimum %70 Türkçe skoru gereklidir

### 3. Konu Uygunluğu Skorlama
- Ders ve konu anahtar kelimeleri eşleştirilir
- Semantik benzerlik hesaplanır (sentence transformers)
- Minimum %60 uygunluk skoru gereklidir

### 4. Erişilebilirlik Kontrolü
- YouTube API ile video durumu kontrol edilir
- Public/unlisted videolar kabul edilir
- Embeddable olma durumu kontrol edilir

### 5. Kalite Skorlama
- İzlenme sayısı (normalize edilmiş)
- Beğeni oranı
- Video süresi (5-60 dakika ideal)
- Altyazı desteği
- HD kalite
- Kanal güvenilirliği

### 6. Final Skorlama ve Sıralama
- Tüm skorlar ağırlıklı ortalama ile birleştirilir
- Videolar final skora göre sıralanır
- Top N video döndürülür

## Test Coverage

9 integration test ile %100 coverage:

1. ✅ Full pipeline başarı testi
2. ✅ Türkçe filtreleme entegrasyonu
3. ✅ Konu uygunluğu entegrasyonu
4. ✅ Erişilebilirlik entegrasyonu
5. ✅ Kalite skorlama entegrasyonu
6. ✅ Final skor hesaplama
7. ✅ Boş sonuç durumu
8. ✅ Tüm videolar filtrelendiğinde
9. ✅ Maksimum sonuç limiti

## Performance

- Paralel video işleme (asyncio.gather)
- Batch validation desteği
- 5 saniye timeout ile hızlı yanıt
- Cache desteği (gelecek implementasyon)

## Hata Yönetimi

- YouTube API hataları gracefully handle edilir
- Timeout durumları yönetilir
- Validation hataları loglanır
- Fallback mekanizmaları mevcut

## Gelecek İyileştirmeler

1. Redis cache entegrasyonu
2. Rate limiting optimizasyonu
3. A/B testing desteği
4. Kullanıcı feedback sistemi
5. Machine learning tabanlı skorlama

## İlgili Dosyalar

- `backend/services/enhanced_resource_recommendation_engine.py` - Ana implementasyon
- `backend/services/turkish_content_filter.py` - Türkçe filtresi
- `backend/services/subject_relevance_scorer.py` - Konu uygunluğu skorlayıcı
- `backend/services/video_quality_validator.py` - Kalite doğrulayıcı
- `backend/tests/integration/test_enhanced_recommendation_engine.py` - Integration testler

## Teknofest 2025 - Eğitim Eylemci Projesi

Bu modül, Teknofest 2025 Eğitim Eylemci yarışması için geliştirilmiştir.
