---
name: retrieval-schedule
description: FSRS + Retrieval Practice birleşik tekrar planı
user-invocable: true
allowed-tools:
  - Read
  - Bash
---

# Retrieval Practice Schedule Skill

Bu skill, FSRS algoritması ile optimal tekrar takvimi oluşturur: Spaced repetition, interleaving, testing effect.

## Kullanım
```bash
/retrieval-schedule <student_id> [subject] [days:30]
```

## İşlem Adımları

1. **Öğrenci Performans Geçmişini Al**
   - Son N gün içindeki tüm yanıtları çek
   - Konu bazlı performans verilerini topla

2. **FSRS Parametrelerini Hesapla**
   - Stability (S): Bilginin hafızada kalma süresi
   - Difficulty (D): Konunun öğrenci için zorluğu
   - Retrievability (R): Şu anki hatırlama olasılığı

3. **Her Konu İçin Optimal Tekrar Aralığını Belirle**
   - FSRS formülü ile sonraki tekrar zamanını hesapla
   - Öğrenci performansına göre dinamik ayarlama

4. **Retrieval Practice Stratejisi Seç**
   - Spacing effect: Aralıklı tekrar
   - Interleaving: Konuları karıştırarak çalış
   - Testing effect: Test odaklı çalışma

5. **Günlük Çalışma Planı Oluştur**
   - Her gün için konu/soru listesi
   - Zorluk dengesi (ZPD içinde)
   - Süre tahmini

6. **Tahmini Performans Artışını Hesapla**
   - Mevcut performans vs beklenen performans
   - Plana uyulursa ne kadar iyileşme beklenebilir?

## Çıktı Formatı

### JSON Formatı
```json
{
  "student_id": "12345",
  "generated_at": "2026-02-06T10:30:00Z",
  "schedule_period": {
    "start": "2026-02-07",
    "end": "2026-03-09",
    "total_days": 30
  },
  "fsrs_parameters": {
    "matematik": {
      "topics": {
        "turevler": {
          "stability": 12.5,
          "difficulty": 0.45,
          "retrievability": 0.82,
          "next_review": "2026-02-15",
          "interval_days": 8
        },
        "integrallar": {
          "stability": 6.2,
          "difficulty": 0.68,
          "retrievability": 0.55,
          "next_review": "2026-02-09",
          "interval_days": 2
        }
      }
    },
    "fizik": {
      "topics": {
        "hareket": {
          "stability": 18.3,
          "difficulty": 0.32,
          "retrievability": 0.91,
          "next_review": "2026-02-20",
          "interval_days": 13
        }
      }
    }
  },
  "daily_schedule": [
    {
      "date": "2026-02-07",
      "sessions": [
        {
          "time": "09:00",
          "subject": "matematik",
          "topic": "integrallar",
          "activity": "retrieval_practice",
          "question_count": 10,
          "estimated_duration_min": 30,
          "difficulty_range": [0.4, 0.7]
        },
        {
          "time": "14:00",
          "subject": "fizik",
          "topic": "elektrik",
          "activity": "interleaving",
          "question_count": 8,
          "estimated_duration_min": 25,
          "difficulty_range": [0.3, 0.6]
        }
      ],
      "total_duration_min": 55,
      "topics_covered": 2
    }
  ],
  "retrieval_strategies": {
    "spacing": {
      "description": "Aralıklı tekrar - FSRS optimal aralıkları kullan",
      "topics": ["turevler", "hareket", "kimyasal_denge"]
    },
    "interleaving": {
      "description": "Farklı konuları karıştırarak çalış",
      "topic_pairs": [
        ["turevler", "integrallar"],
        ["elektrik", "manyetizma"]
      ]
    },
    "testing_effect": {
      "description": "Test odaklı çalışma - Pasif okuma yerine soru çöz",
      "recommended_ratio": "80% test / 20% okuma"
    }
  },
  "performance_prediction": {
    "current_avg": 0.68,
    "predicted_after_30_days": 0.82,
    "expected_improvement": 0.14,
    "confidence": 0.75
  },
  "recommendations": [
    "İntegrallar konusunu öncelikle çalış (düşük retrievability)",
    "Türevler konusu iyi durumda, 8 gün sonra tekrar et",
    "Matematik ve fizik konularını karıştırarak çalış (interleaving)",
    "Günde en az 1 saat soru çöz (testing effect)"
  ]
}
```

### Markdown Formatı
```markdown
# Retrieval Practice Schedule

**Öğrenci ID:** 12345
**Oluşturma Tarihi:** 2026-02-06
**Plan Dönemi:** 2026-02-07 - 2026-03-09 (30 gün)

---

## FSRS Parametreleri

### Matematik

#### Türevler
- **Stability:** 12.5 gün
- **Difficulty:** 0.45
- **Retrievability:** 0.82 (İyi)
- **Sonraki Tekrar:** 2026-02-15 (8 gün sonra)

#### İntegrallar
- **Stability:** 6.2 gün
- **Difficulty:** 0.68
- **Retrievability:** 0.55 ⚠️ (Orta-Düşük)
- **Sonraki Tekrar:** 2026-02-09 (2 gün sonra)

### Fizik

#### Hareket
- **Stability:** 18.3 gün
- **Difficulty:** 0.32
- **Retrievability:** 0.91 ✅ (Çok İyi)
- **Sonraki Tekrar:** 2026-02-20 (13 gün sonra)

---

## Günlük Çalışma Planı

### 7 Şubat 2026 (Cumartesi)

#### 09:00 - Matematik: İntegrallar (30 dk)
- **Aktivite:** Retrieval Practice (Hatırlamaya Dayalı Çalışma)
- **Soru Sayısı:** 10
- **Zorluk:** 0.4-0.7 (Orta)

#### 14:00 - Fizik: Elektrik (25 dk)
- **Aktivite:** Interleaving (Karışık Çalışma)
- **Soru Sayısı:** 8
- **Zorluk:** 0.3-0.6 (Kolay-Orta)

**Toplam Süre:** 55 dakika
**Konu Sayısı:** 2

### 8 Şubat 2026 (Pazar)

#### 10:00 - Matematik: Türevler + İntegrallar (40 dk)
- **Aktivite:** Interleaving (İki konu karışık)
- **Soru Sayısı:** 12
- **Zorluk:** 0.4-0.6

#### 15:00 - Kimya: Kimyasal Denge (30 dk)
- **Aktivite:** Testing Effect (Test odaklı)
- **Soru Sayısı:** 10
- **Zorluk:** 0.5-0.7

**Toplam Süre:** 70 dakika
**Konu Sayısı:** 3

[... Diğer günler ...]

---

## Retrieval Practice Stratejileri

### 1. Spacing Effect (Aralıklı Tekrar)
FSRS optimal aralıklarını kullanarak konuları tekrar et:
- ✅ **Türevler:** 8 gün sonra (2026-02-15)
- ⚠️ **İntegrallar:** 2 gün sonra (2026-02-09) - Acil!
- ✅ **Hareket:** 13 gün sonra (2026-02-20)

### 2. Interleaving (Karışık Çalışma)
Farklı konuları karıştırarak çalış (daha etkili öğrenme):
- Türevler ↔ İntegrallar
- Elektrik ↔ Manyetizma
- Kimyasal Denge ↔ Termodinamik

### 3. Testing Effect (Test Odaklı)
Pasif okuma yerine aktif test çözme:
- **Önerilen Oran:** 80% test çözme / 20% konu okuma
- Günde en az 1 saat soru çöz
- Hatalarını analiz et ve not al

---

## Performans Tahmini

| Metrik | Mevcut | 30 Gün Sonra | İyileşme |
|--------|--------|--------------|----------|
| Ortalama Başarı | 68% | 82% | +14% |
| Güven Aralığı | - | ±5% | - |

**Tahmin Güvenilirliği:** 0.75 (Yüksek)

---

## Öneriler

1. ⚠️ **İntegrallar konusunu öncelikle çalış** (düşük retrievability: 0.55)
2. ✅ **Türevler konusu iyi durumda**, 8 gün sonra tekrar et
3. 🔀 **Matematik ve fizik konularını karıştırarak çalış** (interleaving effect)
4. 📝 **Günde en az 1 saat soru çöz** (testing effect)
5. 📊 **Her hafta sonu progress kontrolü yap**

---

## Bilimsel Temeller

### Spacing Effect
- **Kaynak:** Cepeda et al. (2006) - Optimal spacing interval
- **Etki:** %200-300 daha iyi uzun dönem hafıza

### Interleaving
- **Kaynak:** Rohrer & Taylor (2007) - Math learning
- **Etki:** %43 daha iyi performans

### Testing Effect
- **Kaynak:** Roediger & Karpicke (2006)
- **Etki:** Pasif okumaya göre %50 daha etkili
```

## FSRS Parametreleri Hesaplama

### Stability (S) Hesaplama
```python
def calculate_stability(
    last_review: datetime,
    performance: float,
    difficulty: float,
) -> float:
    """
    Bilginin hafızada kalma süresini hesapla.

    Args:
        last_review: Son tekrar tarihi
        performance: Son performans (0-1)
        difficulty: Konu zorluğu (0-1)

    Returns:
        Stability (gün cinsinden)
    """
    # FSRS-4 formülü
    base_stability = 1.0
    if performance >= 0.6:
        # Başarılı recall
        stability = base_stability * (1 + 0.5 * performance) / (1 - difficulty)
    else:
        # Başarısız recall
        stability = base_stability * 0.5

    return stability
```

### Retrievability (R) Hesaplama
```python
import math
from datetime import datetime, timedelta

def calculate_retrievability(
    stability: float,
    days_since_review: int,
) -> float:
    """
    Şu anki hatırlama olasılığını hesapla.

    Args:
        stability: Bilgi stabilitesi (gün)
        days_since_review: Son tekrardan bu yana geçen gün

    Returns:
        Retrievability (0-1)
    """
    # FSRS-4 exponential decay
    decay = math.exp(-days_since_review / stability)
    return decay
```

### Optimal Interval Hesaplama
```python
def calculate_next_interval(
    stability: float,
    target_retrievability: float = 0.9,
) -> int:
    """
    Optimal tekrar aralığını hesapla.

    Args:
        stability: Mevcut stability
        target_retrievability: Hedef hatırlama olasılığı (varsayılan: 0.9)

    Returns:
        Sonraki tekrara kadar gün sayısı
    """
    interval = -stability * math.log(target_retrievability)
    return max(1, int(interval))
```

## Günlük Plan Oluşturma Algoritması

```python
def generate_daily_schedule(
    student_id: str,
    topics: list[dict],
    days: int = 30,
    daily_study_time_min: int = 60,
) -> list[dict]:
    """
    Günlük çalışma planı oluştur.

    Algoritma:
    1. Tüm konuları retrievability'ye göre sırala (düşük önce)
    2. Her gün için:
       - Acil konuları seç (R < 0.6)
       - Günlük süre limitine göre doldur
       - Interleaving için farklı derslerden seç
    """
    schedule = []

    for day in range(days):
        date = datetime.now() + timedelta(days=day)

        # Retrievability hesapla
        for topic in topics:
            topic['current_r'] = calculate_retrievability(
                topic['stability'],
                (date - topic['last_review']).days
            )

        # Düşük R olan konuları seç
        urgent = [t for t in topics if t['current_r'] < 0.6]
        urgent.sort(key=lambda t: t['current_r'])

        # Günlük sessions oluştur
        sessions = []
        remaining_time = daily_study_time_min

        for topic in urgent[:3]:  # Maksimum 3 konu/gün
            session_time = min(30, remaining_time)
            if session_time < 15:
                break

            sessions.append({
                'topic': topic['name'],
                'duration_min': session_time,
                'question_count': session_time // 3,  # ~3dk/soru
                'strategy': _select_strategy(topic),
            })

            remaining_time -= session_time

        schedule.append({
            'date': date.strftime('%Y-%m-%d'),
            'sessions': sessions,
            'total_duration': daily_study_time_min - remaining_time,
        })

    return schedule

def _select_strategy(topic: dict) -> str:
    """Konu için optimal strateji seç."""
    if topic['current_r'] < 0.5:
        return 'retrieval_practice'
    elif topic['difficulty'] > 0.6:
        return 'testing_effect'
    else:
        return 'interleaving'
```

## Kullanılan Dosyalar

### Backend Services
- `backend/algorithms/turkish_optimized_fsrs.py` - FSRS algoritması
- `backend/services/realtime_adaptation_system.py` - Dinamik zorluk ayarlama
- `backend/ai_engine/adaptive_learning_paths.py` - Öğrenme yolu optimizasyonu

### Models
- `backend/models/user.py` - Öğrenci modeli
- `backend/models/exam.py` - Yanıt geçmişi
- `backend/models/learning_path_models.py` - Öğrenme yolu

## Örnek Kullanım

```bash
# Temel kullanım (30 gün)
/retrieval-schedule 12345

# Sadece matematik (60 gün)
/retrieval-schedule 12345 matematik --days 60

# JSON çıktı
/retrieval-schedule 12345 --format json

# Günlük çalışma süresi belirt (90 dakika)
/retrieval-schedule 12345 --daily-time 90

# Detaylı bilimsel açıklamalarla
/retrieval-schedule 12345 --verbose --scientific
```

## Performans

- **Ortalama Süre:** ~4-6 saniye (100+ konu için)
- **Cache:** FSRS parametreleri 6 saat cache'lenir
- **API Limiti:** 10 istek/dakika
- **Optimizasyon:** Toplu hesaplama

## Bilimsel Kaynaklar

### FSRS Algoritması
- Ye, J., et al. (2024). "A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling"
- Wozniak, P. (2021). "SuperMemo Algorithm SM-18"

### Retrieval Practice
- Roediger, H.L., & Karpicke, J.D. (2006). "Test-Enhanced Learning"
- Bjork, R.A. (1994). "Memory and Metamemory Considerations in the Training of Human Beings"

### Spacing Effect
- Cepeda, N.J., et al. (2006). "Distributed Practice in Verbal Recall Tasks"
- Ebbinghaus, H. (1885). "Memory: A Contribution to Experimental Psychology"

### Interleaving
- Rohrer, D., & Taylor, K. (2007). "The Shuffling of Mathematics Problems Improves Learning"
- Dunlosky, J., et al. (2013). "Improving Students' Learning With Effective Learning Techniques"

## Uyarılar

- ⚠️ **Minimum veri:** En az 20 yanıt gerekli (güvenilir FSRS parametreleri için)
- ⚠️ **Aşırı yük:** Günlük önerilen süre >2 saat ise uyarı ver
- ⚠️ **Düşük performans:** Mevcut performans <0.5 ise daha temel konuları öner
