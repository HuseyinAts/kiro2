---
name: question-quality-multi
description: OSYM kalite skoru + taxonomy coverage + CLT skoru tek raporda
user-invocable: true
allowed-tools:
  - Read
  - Bash
---

# Multi-Dimensional Question Quality Report Skill

Bu skill, soru için çok boyutlu kalite raporu oluşturur: OSYM uyumluluk, taksonomi kapsama, bilişsel yük, okunabilirlik.

## Kullanım
```bash
/question-quality-multi <soru_metni>
```

## İşlem Adımları

1. **OSYM Format Uyumluluk Kontrolü**
   - 5 seçenek var mı?
   - Tek doğru cevap var mı?
   - Türkçe metin (UTF-8 + NFC normalizasyon)
   - Seçenek formatı doğru mu? (A), B), C), D), E))
   - backend/services/quality/osym_quality_scorer.py kullan

2. **Taxonomy Coverage Analizi**
   - Bloom seviyesi
   - SOLO seviyesi
   - Marzano bilişsel seviye
   - Webb DOK seviyesi
   - Tutarlılık skoru
   - backend/services/taxonomy/multi_taxonomy_analyzer.py kullan

3. **Cognitive Load Theory (CLT) Analizi**
   - İçsel yük (intrinsic load)
   - Dışsal yük (extraneous load)
   - İlişkili yük (germane load)
   - Toplam bilişsel yük tahmini
   - backend/services/taxonomy/cognitive_load_calculator.py kullan

4. **BERTScore Benzerlik Kontrolü**
   - Veritabanındaki mevcut sorularla karşılaştır
   - Kopyalama/plagiarism riski tespit et
   - backend/services/bertscore_evaluator.py kullan

5. **Türkçe Okunabilirlik İndeksi**
   - Cümle uzunluğu
   - Kelime karmaşıklığı
   - Ateş okunabilirlik formülü (Türkçe uyarlaması)
   - backend/core/text_simplification_service.py kullan

6. **Genel Kalite Skoru**
   - Tüm metrikleri ağırlıklandır
   - 0.0-1.0 arası skor hesapla

## Çıktı Formatı

### JSON Formatı
```json
{
  "question_text": "Soru metni...",
  "timestamp": "2026-02-06T10:30:00Z",
  "quality_metrics": {
    "osym_compliance": {
      "score": 0.95,
      "details": {
        "has_5_options": true,
        "has_single_answer": true,
        "turkish_encoding": true,
        "format_correct": true
      }
    },
    "taxonomy": {
      "bloom_level": "analiz",
      "solo_level": "iliskisel",
      "marzano_system": "zihinsel_islemler",
      "marzano_cognitive": "analiz",
      "webb_dok": 3,
      "consistency_score": 0.85
    },
    "cognitive_load": {
      "intrinsic": 0.6,
      "extraneous": 0.3,
      "germane": 0.5,
      "total_estimate": 0.45,
      "category": "orta",
      "recommendation": "Optimal bilişsel yük"
    },
    "similarity_check": {
      "max_similarity": 0.32,
      "plagiarism_risk": "düşük",
      "similar_questions": []
    },
    "readability": {
      "score": 0.78,
      "level": "orta",
      "avg_sentence_length": 18,
      "avg_word_length": 5.2
    }
  },
  "overall_quality": {
    "score": 0.82,
    "grade": "A",
    "status": "geçerli"
  },
  "suggestions": [
    "Bilişsel yük optimal seviyede",
    "Taksonomi etiketleri tutarlı",
    "OSYM formatına uygun"
  ],
  "warnings": [],
  "errors": []
}
```

### Markdown Formatı
```markdown
# Soru Kalite Raporu

## Soru
[Soru metni]

## Genel Kalite
- **Skor:** 0.82 / 1.00
- **Not:** A
- **Durum:** ✅ Geçerli

## OSYM Uyumluluk (0.95)
- ✅ 5 seçenek
- ✅ Tek doğru cevap
- ✅ Türkçe kodlama
- ✅ Format doğru

## Taksonomi Kapsama (0.85)
- **Bloom:** Analiz
- **SOLO:** İlişkisel
- **Marzano:** Zihinsel İşlemler / Analiz
- **Webb DOK:** 3 (Stratejik Düşünme)
- **Tutarlılık:** 0.85

## Bilişsel Yük Analizi (0.45 - Orta)
- **İçsel:** 0.60
- **Dışsal:** 0.30
- **İlişkili:** 0.50
- **Kategori:** Orta
- **Öneri:** Optimal bilişsel yük

## Benzerlik Kontrolü
- **Maksimum Benzerlik:** 0.32
- **Plagiarism Riski:** Düşük
- **Benzer Soru Sayısı:** 0

## Okunabilirlik (0.78)
- **Seviye:** Orta
- **Ortalama Cümle Uzunluğu:** 18 kelime
- **Ortalama Kelime Uzunluğu:** 5.2 harf

## Öneriler
1. Bilişsel yük optimal seviyede
2. Taksonomi etiketleri tutarlı
3. OSYM formatına uygun

## Uyarılar
[Uyarı yoksa boş]

## Hatalar
[Hata yoksa boş]
```

## Kalite Skoru Hesaplama

```python
def calculate_overall_quality(metrics: dict) -> float:
    """
    Çok boyutlu kalite skoru hesapla.

    Ağırlıklar:
    - OSYM Uyumluluk: 30%
    - Taksonomi Tutarlılık: 25%
    - Bilişsel Yük (optimal): 20%
    - Okunabilirlik: 15%
    - Benzerlik (düşük olmalı): 10%
    """
    weights = {
        'osym': 0.30,
        'taxonomy': 0.25,
        'cognitive_load': 0.20,
        'readability': 0.15,
        'similarity': 0.10,
    }

    # Bilişsel yük skoru (0.3-0.7 optimal)
    clt = metrics['cognitive_load']['total_estimate']
    clt_score = 1.0 - abs(0.5 - clt) * 2

    # Benzerlik skoru (düşük olmalı)
    similarity = metrics['similarity_check']['max_similarity']
    similarity_score = 1.0 - similarity

    overall = (
        metrics['osym_compliance']['score'] * weights['osym'] +
        metrics['taxonomy']['consistency_score'] * weights['taxonomy'] +
        clt_score * weights['cognitive_load'] +
        metrics['readability']['score'] * weights['readability'] +
        similarity_score * weights['similarity']
    )

    return overall
```

## Kalite Notlandırma

| Skor | Not | Açıklama |
|------|-----|----------|
| 0.90-1.00 | A+ | Mükemmel kalite |
| 0.80-0.89 | A | Çok iyi kalite |
| 0.70-0.79 | B | İyi kalite |
| 0.60-0.69 | C | Kabul edilebilir |
| 0.50-0.59 | D | Zayıf, iyileştirme gerekli |
| < 0.50 | F | Reddedilmeli |

## Kullanılan Dosyalar

### Backend Services
- `backend/services/quality/osym_quality_scorer.py` - OSYM format kontrolü
- `backend/services/taxonomy/multi_taxonomy_analyzer.py` - Taksonomi analizi
- `backend/services/taxonomy/cognitive_load_calculator.py` - CLT analizi
- `backend/services/bertscore_evaluator.py` - Benzerlik kontrolü
- `backend/core/text_simplification_service.py` - Okunabilirlik

### Models
- `backend/models/soru_model.py` - Soru modeli

## Örnek Kullanım

```bash
# Temel kullanım
/question-quality-multi "Aşağıdakilerden hangisi..."

# JSON çıktı
/question-quality-multi --format json "Soru metni..."

# Detaylı rapor
/question-quality-multi --verbose "Soru metni..."

# Dosyadan okuma
/question-quality-multi --file sorular.txt
```

## Uyarı ve Hata Durumları

### Uyarılar (score 0.6-0.8)
- ⚠️ Bilişsel yük yüksek (>0.7)
- ⚠️ Okunabilirlik düşük (<0.6)
- ⚠️ Taksonomi tutarsızlığı (<0.7)

### Hatalar (score <0.6)
- ❌ OSYM formatına uygun değil
- ❌ Yüksek benzerlik (plagiarism riski)
- ❌ Çok yüksek bilişsel yük (>0.9)
- ❌ Türkçe kodlama hatası

## Performans

- **Ortalama Süre:** ~5-7 saniye (tüm analizler)
- **Cache:** BERTScore sonuçları cache'lenir
- **API Limiti:** 50 istek/dakika
- **Paralel İşlem:** 5 analiz paralel çalışır

## İyileştirme Önerileri

Skill otomatik olarak şu önerileri üretir:

1. **OSYM Uyumluluk İçin:**
   - Eksik seçenekleri ekle
   - Format hatalarını düzelt
   - Türkçe karakter sorunlarını gider

2. **Taksonomi İçin:**
   - Uyumsuz seviyeleri düzelt
   - Daha yüksek bilişsel seviyeye çık (eğer çok kolay)

3. **Bilişsel Yük İçin:**
   - Dışsal yükü azalt (gereksiz bilgileri kaldır)
   - İlişkili yükü artır (öğrenmeyi destekleyen ipuçları ekle)

4. **Okunabilirlik İçin:**
   - Uzun cümleleri böl
   - Karmaşık kelimeleri basitleştir

5. **Benzerlik İçin:**
   - Yüksek benzerlik varsa soru metnini değiştir
   - Farklı açıdan sor
