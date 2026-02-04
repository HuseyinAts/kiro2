# Turkish Content Filter Service

## Genel Bakış

`TurkishContentFilter` servisi, video içeriklerinin Türkçe olup olmadığını doğrular ve konu alakası (relevance) skorlaması yapar. Bu servis, Learning Path video önerilerinde sadece Türkçe ve alakalı videoların gösterilmesini sağlar.

## Özellikler

### 1. Dil Tespiti (Language Detection)
- **Türkçe Karakter Analizi**: ç, ğ, ı, ö, ş, ü karakterlerinin varlığını kontrol eder
- **Türkçe Eğitim Kelimeleri**: "konu", "ders", "anlatım", "sınav", "TYT", "AYT" gibi kelimeleri arar
- **Güvenilir Kanal Kontrolü**: Tonguç Akademi, EBA, Khan Academy Türkçe gibi güvenilir kanalları tanır
- **langdetect Entegrasyonu**: Mevcut ise langdetect kütüphanesi ile dil tespiti yapar
- **Adaptif Threshold**: langdetect yoksa daha düşük threshold kullanır (0.5 vs 0.7)

### 2. Konu Alakası Skorlaması (Relevance Scoring)
- **MEB Müfredatı Taxonomy**: 7 ana ders için detaylı konu taxonomy'si
  - Matematik (geometri, algebra, sayılar, trigonometri)
  - Fizik (hareket, enerji, elektrik, ışık)
  - Kimya (atom, bağlar, reaksiyonlar, periyodik)
  - Biyoloji (hücre, genetik, sistemler, ekoloji)
  - Türkçe (dil bilgisi, cümle, edebiyat, yazım)
  - Tarih (osmanlı, cumhuriyet, dünya)
  - Coğrafya (fiziki, beşeri, ekonomik)

- **Keyword Matching**: Video başlığı ve açıklamasında konu keyword'lerini arar
- **Sub-topic Matching**: Alt konuları (örn: üçgen, dörtgen, çember) tespit eder
- **Weighted Scoring**: Ana keyword'ler %60, alt konular %40 ağırlıkta

### 3. Zorluk Seviyesi Eşleştirme (Difficulty Matching)
- **3 Seviye**: Başlangıç (1), Orta (2), İleri (3)
- **±1 Tolerans**: Öğrenci seviyesine yakın videoları kabul eder
- **Skor Sistemi**:
  - Tam eşleşme: 1.0
  - ±1 seviye: 0.7
  - ±2 seviye: 0.3

### 4. Video Filtreleme
- **Multi-criteria Filtering**: Dil, alakası ve zorluk seviyesine göre filtreler
- **Weighted Overall Score**: 
  - Dil: %30
  - Alakası: %50
  - Zorluk: %20
- **Pass/Fail Logic**: Tüm kriterleri geçen videoları döndürür

## Kullanım

### Temel Kullanım

```python
from services.turkish_content_filter import get_turkish_content_filter

# Service instance'ını al
filter_service = await get_turkish_content_filter()

# Dil doğrulama
result = await filter_service.validate_turkish_content(
    video_title="Matematik Geometri Üçgenler",
    video_description="Bu videoda üçgenler konusunu işliyoruz",
    channel_name="Tonguç Akademi"
)

print(f"Turkish: {result.is_turkish}")
print(f"Score: {result.confidence_score}")
print(f"Language: {result.detected_language}")
```

### Video Filtreleme

```python
# Video listesini filtrele
videos = [
    {
        'title': 'Matematik Geometri Üçgenler',
        'description': 'Üçgenler konu anlatımı',
        'channel': 'Tonguç Akademi',
        'subject': 'matematik',
        'difficulty': 'orta',
        'quality_score': 8.5
    },
    # ... daha fazla video
]

filtered_videos = await filter_service.filter_videos(
    videos=videos,
    min_relevance=0.7,  # Minimum %70 alakası
    target_difficulty='orta',  # Orta seviye
    language='tr',  # Türkçe
    subject='matematik'  # Matematik konusu
)

# Sadece Türkçe, alakalı ve uygun seviyedeki videolar döner
```

### Relevance Scoring

```python
# Konu alakası hesapla
relevance_score = filter_service._calculate_relevance(
    title="Matematik Geometri Üçgenler Konu Anlatımı",
    description="Bu videoda üçgenler, açılar ve kenarlar konusunu işliyoruz",
    video_subject="matematik",
    target_subject="matematik"
)

print(f"Relevance: {relevance_score:.2f}")  # 0.0-1.0 arası
```

## Güvenilir Türkçe Kanallar

Servis, aşağıdaki güvenilir Türkçe eğitim kanallarını tanır:

- **Tonguç Akademi** (weight: 1.0) - Matematik, Fizik, Kimya, Biyoloji
- **Khan Academy Türkçe** (weight: 1.0) - Matematik, Fizik
- **EBA** (weight: 0.95) - Tüm dersler
- **KAMP Online** (weight: 0.95) - Matematik, Fizik, Kimya
- **Hocalara Geldik** (weight: 0.9) - Matematik, Fizik
- **Fizik Öğretmeni** (weight: 0.92) - Fizik
- **Matematik Öğretmeni** (weight: 0.9) - Matematik
- **Kimya Öğretmeni** (weight: 0.9) - Kimya
- **Biyoloji Öğretmeni** (weight: 0.9) - Biyoloji
- **Türkçe Öğretmeni** (weight: 0.9) - Türkçe, Edebiyat

## Veri Modelleri

### TurkishValidationResult

```python
@dataclass
class TurkishValidationResult:
    is_turkish: bool  # Türkçe mi?
    confidence_score: float  # 0.0-1.0 güven skoru
    detected_language: str  # Tespit edilen dil kodu
    turkish_indicators: List[str]  # Türkçe göstergeler
```

### FilterResult

```python
@dataclass
class FilterResult:
    video: Any  # Video objesi
    language_score: float  # 0-1 dil skoru
    relevance_score: float  # 0-1 alakası skoru
    difficulty_match: float  # 0-1 zorluk eşleşmesi
    overall_score: float  # 0-1 genel skor
    passed: bool  # Filtreyi geçti mi?
    failure_reasons: List[str]  # Başarısızlık nedenleri
```

## Performans

- **Dil Tespiti**: ~10ms (langdetect ile ~50ms)
- **Relevance Scoring**: ~5ms
- **Video Filtreleme**: ~20ms per video
- **Batch Filtering**: 100 video için ~2 saniye

## Konfigürasyon

### Threshold'lar

```python
# Minimum Türkçe skoru
min_turkish_score = 0.5  # langdetect yoksa
min_turkish_score = 0.7  # langdetect varsa

# Minimum relevance skoru
min_relevance = 0.7  # Önerilen: 0.6-0.8 arası

# Minimum language skoru (filtreleme için)
min_language_score = 0.5  # langdetect yoksa
min_language_score = 0.8  # langdetect varsa

# Minimum difficulty match
min_difficulty_match = 0.5  # ±1 seviye tolerans

# Minimum overall score
min_overall_score = 0.6  # Genel skor
```

## Geliştirme Notları

### langdetect Kurulumu (Opsiyonel)

```bash
pip install langdetect
```

langdetect kurulu değilse, servis temel Türkçe karakter analizi kullanır ve daha düşük threshold'lar uygular.

### Yeni Kanal Ekleme

```python
TRUSTED_TURKISH_CHANNELS = {
    'Yeni Kanal': {
        'weight': 0.9,  # 0.0-1.0 arası güven skoru
        'subjects': ['matematik', 'fizik']  # veya 'all'
    }
}
```

### Yeni Konu Ekleme

```python
SUBJECT_TAXONOMY = {
    'yeni_ders': {
        'keywords': ['anahtar', 'kelimeler'],
        'sub_topics': {
            'alt_konu_1': ['keyword1', 'keyword2'],
            'alt_konu_2': ['keyword3', 'keyword4']
        }
    }
}
```

## Test

```python
# Test dosyası oluştur
python backend/test_turkish_filter_quick.py

# Beklenen çıktı:
# - Test 1: Turkish validation (PASS)
# - Test 2: English content rejection (PASS)
# - Test 3: Video filtering (PASS)
# - Test 4: Relevance scoring (PASS)
# - Test 5: Difficulty matching (PASS)
# - Test 6: Taxonomy (PASS)
# - Test 7: Trusted channels (PASS)
```

## Entegrasyon

### VideoRecommendationService ile

```python
from services.turkish_content_filter import get_turkish_content_filter

class VideoRecommendationService:
    def __init__(self):
        self.content_filter = await get_turkish_content_filter()
    
    async def get_recommendations(self, profile):
        # Video discovery
        videos = await self.discover_videos(profile)
        
        # Türkçe içerik filtreleme
        filtered_videos = await self.content_filter.filter_videos(
            videos=videos,
            min_relevance=0.7,
            target_difficulty=profile.difficulty,
            subject=profile.subject
        )
        
        return filtered_videos
```

## Sorun Giderme

### Problem: Tüm videolar filtreleniyor

**Çözüm**: min_relevance threshold'unu düşürün (0.7 -> 0.5)

```python
filtered = await filter_service.filter_videos(
    videos=videos,
    min_relevance=0.5  # Daha düşük threshold
)
```

### Problem: İngilizce videolar geçiyor

**Çözüm**: langdetect kurun veya Türkçe karakter kontrolünü güçlendirin

```bash
pip install langdetect
```

### Problem: Alakasız videolar geçiyor

**Çözüm**: Taxonomy'ye daha fazla keyword ekleyin

```python
SUBJECT_TAXONOMY['matematik']['keywords'].append('yeni_keyword')
```

## Gelecek Geliştirmeler

1. **Machine Learning**: Video başlığı ve açıklaması için ML-based classification
2. **Semantic Similarity**: Sentence transformers ile semantic matching
3. **User Feedback**: Kullanıcı feedback'i ile relevance scoring iyileştirme
4. **A/B Testing**: Farklı threshold'lar için A/B testing
5. **Cache**: Sık kullanılan video skorlarını cache'leme

## Lisans

Teknofest 2025 - Eğitim Eylemci Projesi
