---
name: student-cognitive-profile
description: Öğrenci yanıtlarından SOLO/Marzano bilişsel profil çıkarımı
user-invocable: true
allowed-tools:
  - Read
  - Bash
---

# Student Cognitive Profile Skill

Bu skill, öğrenci yanıt geçmişinden bilişsel profil analizi çıkarır: SOLO, Marzano, öğrenme stili, güçlü/zayıf yönler.

## Kullanım
```bash
/student-cognitive-profile <student_id> [subject]
```

## İşlem Adımları

1. **Yanıt Geçmişini Al**
   - Öğrenci ID ile veritabanından son N yanıtı çek
   - Filtre: subject (ders), date_range (tarih aralığı)

2. **Her Yanıtı SOLO Seviyesine Göre Sınıfla**
   - Ön-yapısal (prestructural)
   - Tek-yapısal (unistructural)
   - Çok-yapısal (multistructural)
   - İlişkisel (relational)
   - Genişletilmiş soyut (extended abstract)

3. **Marzano Bilişsel İşlem Seviyesi Belirle**
   - Hatırlama (retrieval)
   - Anlama (comprehension)
   - Analiz (analysis)
   - Bilgi kullanımı (knowledge utilization)

4. **Ders Bazlı Güçlü/Zayıf Bilişsel Yönler**
   - Her ders için SOLO/Marzano dağılımı
   - Güçlü alanlar: Hangi bilişsel seviyelerde başarılı?
   - Gelişim alanları: Hangi seviyelerde zorlanıyor?

5. **Tavan/Taban Etkisi Analizi**
   - Tavan etkisi: Sürekli en yüksek seviyede (daha zor soru gerekli)
   - Taban etkisi: Sürekli en düşük seviyede (daha kolay soru gerekli)

6. **Öğrenme Stili Tespiti**
   - VARK modeli: Görsel, İşitsel, Okuma/Yazma, Kinestetik
   - Felder-Silverman modeli: Aktif/Yansıtıcı, Algılayıcı/Sezgisel, vb.
   - backend/services/learning_style_service.py kullan

7. **Kişiselleştirilmiş Öneriler**
   - Konu bazlı çalışma stratejileri
   - Bilişsel seviye hedefleri
   - Öğrenme stili uyumlu kaynaklar

## Çıktı Formatı

### JSON Formatı
```json
{
  "student_id": "12345",
  "analysis_date": "2026-02-06T10:30:00Z",
  "total_responses": 150,
  "date_range": {
    "start": "2026-01-01",
    "end": "2026-02-06"
  },
  "cognitive_profile": {
    "solo_distribution": {
      "prestructural": 0.05,
      "unistructural": 0.20,
      "multistructural": 0.35,
      "relational": 0.30,
      "extended_abstract": 0.10
    },
    "marzano_distribution": {
      "retrieval": 0.25,
      "comprehension": 0.35,
      "analysis": 0.30,
      "knowledge_utilization": 0.10
    },
    "dominant_solo": "multistructural",
    "dominant_marzano": "comprehension"
  },
  "subject_breakdown": {
    "matematik": {
      "solo_avg": 3.2,
      "marzano_avg": 2.5,
      "performance": 0.75,
      "strengths": ["geometri", "cebirsel işlemler"],
      "weaknesses": ["analitik geometri", "trigonometri"]
    },
    "fizik": {
      "solo_avg": 2.8,
      "marzano_avg": 2.2,
      "performance": 0.68,
      "strengths": ["mekanik", "enerji"],
      "weaknesses": ["elektrik", "manyetizma"]
    }
  },
  "ceiling_floor_analysis": {
    "ceiling_effect": false,
    "floor_effect": false,
    "recommendation": "Mevcut zorluk seviyesi uygun"
  },
  "learning_style": {
    "vark": {
      "visual": 0.35,
      "auditory": 0.20,
      "reading_writing": 0.25,
      "kinesthetic": 0.20,
      "dominant": "visual"
    },
    "felder_silverman": {
      "active_reflective": "active",
      "sensing_intuitive": "sensing",
      "visual_verbal": "visual",
      "sequential_global": "sequential"
    }
  },
  "strengths": [
    "Çok-yapısal düşünme yeteneği güçlü",
    "Matematiksel işlemlerde başarılı",
    "Görsel öğrenme tercihi belirgin"
  ],
  "growth_areas": [
    "İlişkisel ve soyut düşünme geliştirilmeli",
    "Fizik konularında analiz becerisi zayıf",
    "Bilgi kullanımı seviyesine çıkmalı"
  ],
  "personalized_recommendations": {
    "matematik": [
      "Analitik geometri için görsel kaynaklar kullan",
      "Grafik ve diyagram çizerek çalış",
      "İlişkisel düşünme için farklı konuları birleştir"
    ],
    "fizik": [
      "Elektrik konusu için deney videoları izle",
      "Formülleri ezberlemek yerine anlamaya çalış",
      "Günlük hayat örnekleriyle ilişkilendir"
    ],
    "genel": [
      "SOLO seviyesini 'ilişkisel'e çıkarmak için çapraz konu çalışması yap",
      "Görsel öğrenme stiline uygun kaynakları tercih et",
      "Aktif öğrenme: Kendi notlarını oluştur, özet çıkar"
    ]
  }
}
```

### Markdown Formatı
```markdown
# Bilişsel Profil Raporu

**Öğrenci ID:** 12345
**Analiz Tarihi:** 2026-02-06
**Toplam Yanıt:** 150 (2026-01-01 - 2026-02-06)

---

## Bilişsel Profil Özeti

### SOLO Dağılımı
| Seviye | Yüzde | Grafik |
|--------|-------|--------|
| Ön-yapısal | 5% | █ |
| Tek-yapısal | 20% | ████ |
| Çok-yapısal | 35% | ███████ |
| İlişkisel | 30% | ██████ |
| Genişletilmiş Soyut | 10% | ██ |

**Baskın Seviye:** Çok-yapısal

### Marzano Dağılımı
| Seviye | Yüzde | Grafik |
|--------|-------|--------|
| Hatırlama | 25% | █████ |
| Anlama | 35% | ███████ |
| Analiz | 30% | ██████ |
| Bilgi Kullanımı | 10% | ██ |

**Baskın Seviye:** Anlama

---

## Ders Bazlı Analiz

### Matematik (Performans: 0.75)
- **SOLO Ortalama:** 3.2 (Çok-yapısal / İlişkisel arası)
- **Marzano Ortalama:** 2.5 (Anlama / Analiz arası)
- **Güçlü Yönler:** Geometri, Cebirsel İşlemler
- **Gelişim Alanları:** Analitik Geometri, Trigonometri

### Fizik (Performans: 0.68)
- **SOLO Ortalama:** 2.8 (Çok-yapısal)
- **Marzano Ortalama:** 2.2 (Anlama)
- **Güçlü Yönler:** Mekanik, Enerji
- **Gelişim Alanları:** Elektrik, Manyetizma

---

## Tavan/Taban Etkisi
- **Tavan Etkisi:** ❌ Yok
- **Taban Etkisi:** ❌ Yok
- **Öneri:** Mevcut zorluk seviyesi uygun

---

## Öğrenme Stili

### VARK Modeli
- **Görsel:** 35% ⭐ (Baskın)
- **İşitsel:** 20%
- **Okuma/Yazma:** 25%
- **Kinestetik:** 20%

### Felder-Silverman
- **Aktif** vs Yansıtıcı
- **Algılayıcı** vs Sezgisel
- **Görsel** vs Sözel
- **Sıralı** vs Bütünsel

---

## Güçlü Yönler
1. ✅ Çok-yapısal düşünme yeteneği güçlü
2. ✅ Matematiksel işlemlerde başarılı
3. ✅ Görsel öğrenme tercihi belirgin

## Gelişim Alanları
1. ⚠️ İlişkisel ve soyut düşünme geliştirilmeli
2. ⚠️ Fizik konularında analiz becerisi zayıf
3. ⚠️ Bilgi kullanımı seviyesine çıkmalı

---

## Kişiselleştirilmiş Öneriler

### Matematik
1. 📊 Analitik geometri için görsel kaynaklar kullan
2. ✏️ Grafik ve diyagram çizerek çalış
3. 🔗 İlişkisel düşünme için farklı konuları birleştir

### Fizik
1. 🎥 Elektrik konusu için deney videoları izle
2. 💡 Formülleri ezberlemek yerine anlamaya çalış
3. 🌍 Günlük hayat örnekleriyle ilişkilendir

### Genel
1. 🎯 SOLO seviyesini 'ilişkisel'e çıkarmak için çapraz konu çalışması yap
2. 👁️ Görsel öğrenme stiline uygun kaynakları tercih et
3. ✍️ Aktif öğrenme: Kendi notlarını oluştur, özet çıkar
```

## SOLO Seviye Hesaplama

```python
def calculate_solo_average(responses: list[dict]) -> float:
    """
    SOLO seviye ortalaması hesapla.

    SOLO seviyeleri:
    - 1: Ön-yapısal
    - 2: Tek-yapısal
    - 3: Çok-yapısal
    - 4: İlişkisel
    - 5: Genişletilmiş soyut

    Returns:
        1.0-5.0 arası ortalama
    """
    solo_map = {
        'prestructural': 1,
        'unistructural': 2,
        'multistructural': 3,
        'relational': 4,
        'extended_abstract': 5,
    }

    total = sum(solo_map[r['solo_level']] for r in responses)
    return total / len(responses)
```

## Tavan/Taban Etkisi Tespit

```python
def detect_ceiling_floor(responses: list[dict]) -> dict:
    """
    Tavan/taban etkisi tespit et.

    Tavan etkisi: %80+ yanıt en yüksek seviyede
    Taban etkisi: %80+ yanıt en düşük seviyede
    """
    solo_levels = [r['solo_level_numeric'] for r in responses]

    ceiling = sum(1 for s in solo_levels if s >= 4) / len(solo_levels)
    floor = sum(1 for s in solo_levels if s <= 2) / len(solo_levels)

    return {
        'ceiling_effect': ceiling > 0.8,
        'floor_effect': floor > 0.8,
        'recommendation': _get_recommendation(ceiling, floor),
    }

def _get_recommendation(ceiling: float, floor: float) -> str:
    if ceiling > 0.8:
        return "Daha zor sorular sunulmalı"
    elif floor > 0.8:
        return "Daha kolay sorular sunulmalı"
    else:
        return "Mevcut zorluk seviyesi uygun"
```

## Kullanılan Dosyalar

### Backend Services
- `orchestrator/core/cognitive_profiler.py` - Bilişsel profil analizi
- `backend/services/taxonomy/solo_classifier.py` - SOLO sınıflandırıcı
- `backend/services/taxonomy/marzano_classifier.py` - Marzano sınıflandırıcı
- `backend/services/learning_style_service.py` - Öğrenme stili tespiti
- `backend/ai_engine/ml_performance_analytics.py` - Performans analizi

### Models
- `backend/models/user.py` - Öğrenci modeli
- `backend/models/exam.py` - Yanıt geçmişi

## Örnek Kullanım

```bash
# Temel kullanım
/student-cognitive-profile 12345

# Sadece matematik
/student-cognitive-profile 12345 matematik

# Son 30 gün
/student-cognitive-profile 12345 --days 30

# JSON çıktı
/student-cognitive-profile 12345 --format json

# Detaylı rapor
/student-cognitive-profile 12345 --verbose
```

## Minimum Veri Gereksinimleri

| Güvenilirlik | Minimum Yanıt | Öneri |
|--------------|---------------|-------|
| Düşük | 10-30 | Öneriler genel olabilir |
| Orta | 30-100 | Güvenilir profil |
| Yüksek | 100+ | Çok güvenilir profil |

## Performans

- **Ortalama Süre:** ~3-5 saniye (100 yanıt için)
- **Cache:** Profil sonuçları 1 saat cache'lenir
- **API Limiti:** 20 istek/dakika
- **Optimizasyon:** Veri toplu sorgu ile alınır

## İyileştirme Önerileri Türleri

Skill şu kategorilerde öneriler üretir:

1. **Bilişsel Seviye Hedefleri**
   - SOLO seviyesini artırmak için stratejiler
   - Marzano bilişsel işlem geliştirme

2. **Konu Bazlı Stratejiler**
   - Zayıf konular için özel çalışma planı
   - Güçlü konuları pekiştirme

3. **Öğrenme Stili Uyumlu Kaynaklar**
   - Görsel öğrenciler için: Video, diyagram, grafik
   - İşitsel öğrenciler için: Podcast, ders anlatımı
   - Okuma/Yazma: Kitap, not alma
   - Kinestetik: Uygulama, deney

4. **Metabilişsel Stratejiler**
   - Kendi öğrenme sürecini izleme
   - Hata analizi yapma
   - Hedef belirleme

## Gizlilik ve Etik

- ⚠️ Öğrenci profili hassas veridir
- 🔒 Sadece yetkili kullanıcılar erişebilir (öğrenci, veli, öğretmen)
- 📊 Profil sonuçları etiketleme için değil, öğrenmeyi desteklemek için kullanılmalıdır
- ❌ "Yetersiz" gibi olumsuz etiketlerden kaçınılmalıdır
