# Zorluk Seviyesi Sınıflandırma Sistemi
## Task 74: Difficulty Level Classification System

## Genel Bakış

Bu sistem, soru bankasındaki soruları 5 seviyeli bir zorluk ölçeğinde sınıflandırır ve gerçek zamanlı olarak günceller. Hem IRT (Item Response Theory) parametrelerini hem de öğrenci performans verilerini kullanarak hibrit bir sınıflandırma yapar.

## Özellikler

### ✅ Task 74.1: 5 Seviyeli Zorluk Sınıflandırması

**Zorluk Seviyeleri:**
1. **Çok Kolay (Very Easy)** - ⭐ - Yeşil (#4CAF50)
2. **Kolay (Easy)** - ⭐⭐ - Açık Yeşil (#8BC34A)
3. **Orta (Medium)** - ⭐⭐⭐ - Sarı (#FFC107)
4. **Zor (Hard)** - ⭐⭐⭐⭐ - Turuncu (#FF9800)
5. **Çok Zor (Very Hard)** - ⭐⭐⭐⭐⭐ - Kırmızı (#F44336)

**Görsel Göstergeler:**
- Renk kodları (frontend entegrasyonu için)
- Yıldız sayısı (1-5)
- Emoji göstergeleri
- CSS class isimleri

### ✅ Task 74.2: IRT b Parametresi Bazlı Sınıflandırma

**IRT Eşikleri:**
- Çok Kolay: b ≤ -1.5
- Kolay: -1.5 < b ≤ -0.5
- Orta: -0.5 < b ≤ 0.5
- Zor: 0.5 < b ≤ 1.5
- Çok Zor: b > 1.5

**Özellikler:**
- Otomatik IRT → Zorluk skoru dönüşümü
- Eşik kalibrasyonu (soru havuzuna göre)
- 1.0-5.0 arası sürekli zorluk skoru

### ✅ Task 74.3: Öğrenci Performansı Bazlı Zorluk

**Crowd-Sourced Zorluk Hesaplama:**
- Başarı oranı analizi (doğru/yanlış oranı)
- Ortalama yanıt süresi analizi
- Minimum 30 yanıt gereksinimi
- Son 90 günlük veri kullanımı

**Hibrit Skorlama:**
- IRT ağırlığı: %40
- Performans ağırlığı: %60
- Güven skoru hesaplama

### ✅ Task 74.4: Dinamik Güncelleme

**Gerçek Zamanlı Güncelleme:**
- Yeni yanıt geldiğinde otomatik güncelleme
- Trend analizi (yükseliyor/düşüyor/stabil)
- Performans bazlı yeniden kalibrasyon

**Trend Analizi:**
- Son 30 gün vs önceki 60 gün karşılaştırması
- %15+ değişim eşiği
- Otomatik zorluk ayarlama

## API Endpoints

### 1. Soru Zorluğunu Sınıflandır
```http
GET /api/v1/difficulty/classify/{question_id}?force_recalculate=false
```

**Response:**
```json
{
  "question_id": "q123",
  "difficulty_level": "medium",
  "difficulty_score": 3.2,
  "classification_method": "hybrid",
  "confidence": 0.9,
  "irt_based_difficulty": 3.0,
  "performance_based_difficulty": 3.3,
  "visual_indicator": {
    "label_tr": "Orta",
    "label_en": "Medium",
    "color": "#FFC107",
    "icon": "⭐⭐⭐",
    "stars": 3,
    "emoji": "😐",
    "css_class": "difficulty-medium"
  },
  "metadata": {
    "irt_difficulty": 0.2,
    "timestamp": "2025-10-23T10:30:00"
  }
}
```

### 2. Görsel Gösterge Bilgisi
```http
GET /api/v1/difficulty/visual-indicator/{level}
```

**Parametreler:**
- `level`: very_easy, easy, medium, hard, very_hard

### 3. Zorluğa Göre Filtrele
```http
POST /api/v1/difficulty/filter
```

**Request Body:**
```json
{
  "difficulty_levels": ["easy", "medium"],
  "topic_id": "topic_123",
  "limit": 50
}
```

### 4. Zorluk Dağılımı
```http
GET /api/v1/difficulty/distribution?topic_id=topic_123
```

**Response:**
```json
{
  "success": true,
  "distribution": {
    "very_easy": 150,
    "easy": 300,
    "medium": 400,
    "hard": 200,
    "very_hard": 50
  },
  "percentages": {
    "very_easy": 13.6,
    "easy": 27.3,
    "medium": 36.4,
    "hard": 18.2,
    "very_hard": 4.5
  },
  "total_questions": 1100
}
```

### 5. Gerçek Zamanlı Güncelleme
```http
POST /api/v1/difficulty/update-realtime
```

**Request Body:**
```json
{
  "question_id": "q123",
  "new_response_data": {
    "is_correct": true,
    "time_spent": 45
  }
}
```

### 6. Toplu Güncelleme
```http
POST /api/v1/difficulty/batch-update
```

**Request Body:**
```json
{
  "question_ids": ["q1", "q2", "q3"],
  "update_threshold_days": 7
}
```

### 7. Zorluk Trendi
```http
GET /api/v1/difficulty/trend/{question_id}?recent_days=30&historical_days=90
```

**Response:**
```json
{
  "success": true,
  "question_id": "q123",
  "trend": {
    "trend_direction": "easier",
    "adjustment_factor": -0.3,
    "confidence": 0.85,
    "recent_success_rate": 0.75,
    "historical_success_rate": 0.58,
    "success_rate_change": 0.17
  },
  "success_analysis": {
    "success_rate": 0.65,
    "avg_time": 52.3,
    "response_count": 145,
    "correct_count": 94,
    "difficulty_estimate": 2.8
  }
}
```

### 8. Eşik Kalibrasyonu
```http
GET /api/v1/difficulty/calibrate-thresholds?topic_id=topic_123
```

## Kullanım Örnekleri

### Python Service Kullanımı

```python
from backend.services.difficulty_classification_service import (
    DifficultyClassificationService,
    DifficultyLevel
)
from backend.core.database import get_db

# Service oluştur
db = next(get_db())
service = DifficultyClassificationService(db)

# Soru sınıflandır
classification = service.classify_question("question_123")
print(f"Zorluk: {classification.difficulty_level.value}")
print(f"Skor: {classification.difficulty_score}")

# Görsel gösterge al
indicator = service.get_visual_difficulty_indicator(classification.difficulty_level)
print(f"Renk: {indicator['color']}")
print(f"Etiket: {indicator['label_tr']}")

# Zorluğa göre filtrele
question_ids = service.filter_questions_by_difficulty(
    difficulty_levels=[DifficultyLevel.EASY, DifficultyLevel.MEDIUM],
    topic_id="math_algebra",
    limit=20
)

# Zorluk dağılımı
distribution = service.get_difficulty_distribution(topic_id="math_algebra")
print(f"Kolay sorular: {distribution['easy']}")

# Trend analizi
trend = service.analyze_difficulty_trend("question_123")
if trend['trend_direction'] == 'easier':
    print("Soru zamanla kolaylaşıyor")
```

### Frontend Entegrasyonu

```javascript
// Soru zorluğunu al
const response = await fetch(`/api/v1/difficulty/classify/${questionId}`);
const data = await response.json();

// Görsel göstergeyi kullan
const indicator = data.visual_indicator;
document.getElementById('difficulty-badge').style.backgroundColor = indicator.color;
document.getElementById('difficulty-label').textContent = indicator.label_tr;
document.getElementById('difficulty-stars').textContent = indicator.icon;

// Zorluğa göre filtrele
const filterResponse = await fetch('/api/v1/difficulty/filter', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    difficulty_levels: ['easy', 'medium'],
    topic_id: topicId,
    limit: 50
  })
});
const questions = await filterResponse.json();
```

## Veritabanı Şeması

Sistem mevcut `QuestionBankItem` modelini kullanır:

```python
class QuestionBankItem(Base):
    id: str
    irt_difficulty: float  # IRT b parametresi (-3.0 ile +3.0)
    primary_topic_id: str
    is_active: bool
    # ... diğer alanlar
```

## Performans Optimizasyonu

1. **Cache Stratejisi:**
   - Sınıflandırma sonuçları 1 saat cache'lenir
   - Trend analizi sonuçları 30 dakika cache'lenir

2. **Batch İşlemler:**
   - Toplu güncelleme desteği
   - Paralel sınıflandırma

3. **İndeksleme:**
   - `irt_difficulty` alanı indeksli
   - `primary_topic_id` alanı indeksli

## Test Coverage

- ✅ IRT bazlı sınıflandırma testleri
- ✅ Performans bazlı hesaplama testleri
- ✅ Görsel gösterge testleri
- ✅ Trend analizi testleri
- ✅ Filtreleme testleri
- ✅ Edge case testleri

Test dosyası: `backend/tests/test_difficulty_classification.py`

## Gelecek Geliştirmeler

1. **Makine Öğrenmesi Entegrasyonu:**
   - Daha gelişmiş zorluk tahmini modelleri
   - Öğrenci profiline göre kişiselleştirilmiş zorluk

2. **A/B Testing:**
   - Farklı zorluk hesaplama yöntemlerinin karşılaştırılması

3. **Gerçek Zamanlı Dashboard:**
   - Zorluk dağılımı görselleştirme
   - Trend takibi

4. **Otomatik Kalibrasyon:**
   - Belirli aralıklarla otomatik eşik güncellemesi
   - Soru havuzu değişikliklerine adaptasyon

## Lisans ve Katkı

Bu sistem Teknofest 2025 Eğitim Eylemci Platformu'nun bir parçasıdır.
