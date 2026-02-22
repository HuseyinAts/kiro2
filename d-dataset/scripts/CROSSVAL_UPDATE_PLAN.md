# Cross-Validation Güncelleme Planı
# =========================================

## MEVCUT YAPI (Sorunlu)
```
cross_validate_answers.py:
├── load_vision_results()     # Sadece tek dosya yükler
├── opus_results = {}        # Opus v1 + v2 birleştiriliyor
├── score_answer()           # Sadece opus_answer kullanılıyor
│
└── Problem:
    - Sonnet yüklenmiyor
    - Gemini yüklenmiyor
    - Tek "opus" kaynağı var
```

## HEDEF YAPI
```
cross_validate_answers.py:
├── load_all_vision_results() # Tüm dosyaları yükler
├── ai_results = {}           # Priority birleştirme
│   ├── sonnet   (en yüksek öncelik)
│   ├── opus_v2
│   ├── opus_v1
│   └── gemini   (en düşük öncelik)
│
├── score_answer_multi()      # Çoklu AI kaynağı
│   ├── sonnet_answer + sonnet_confidence
│   ├── opus_answer + opus_confidence
│   └── gemini_answer + gemini_confidence
│
└── Sonuç:
    - AI coverage: %32.9 → %80+
    - Daha doğru Bayesian posterior
```

## ADIM ADIM DEĞİŞİKLİKLER

### Adım 1: Path Tanımları Ekle (satır ~520)
```python
# Yeni path'ler ekle
sonnet_path = BASE_DIR / "processed" / "vision_solve_sonnet" / "vision_results.jsonl"
gemini_path = BASE_DIR / "processed" / "vision_solve_gemini" / "vision_results_clean.jsonl"
```

### Adım 2: load_all_vision_results() Fonksiyonu Oluştur
```python
def load_all_vision_results() -> Dict[Tuple[str, int, int], Dict]:
    """
    Load and merge ALL vision AI results with priority:
    1. Sonnet (highest confidence)
    2. Opus v2
    3. Opus v1
    4. Gemini (lowest priority)
    """
    # Priority: sonnet > opus_v2 > opus_v1 > gemini
```

### Adım 3: score_answer_multi() Fonksiyonu Oluştur
```python
def score_answer_multi(
    original: str,
    original_source: str,
    rematch: Optional[str],
    sonnet_answer: Optional[str],
    sonnet_confidence: float,
    opus_answer: Optional[str],
    opus_confidence: float,
    gemini_answer: Optional[str],
    gemini_confidence: float,
) -> Tuple[str, float, str]:
    """
    Multi-AI Bayesian scoring with priority:
    - Sonnet highest priority (usually best OCR understanding)
    - Opus v2 second
    - Gemini third
    """
```

### Adım 4: ACCURACY Tablosuna Yeni Kaynaklar Ekle
```python
ACCURACY = {
    # ... mevcutlar ...
    "sonnet_high":   0.87,  # Sonnet conf >= 0.9
    "sonnet_med":    0.75,  # Sonnet conf 0.7-0.9
    "sonnet_low":    0.40,  # Sonnet conf < 0.7
    "gemini_high":   0.80,  # Gemini conf >= 0.9
    "gemini_med":    0.65,  # Gemini conf 0.7-0.9
    "gemini_low":    0.30,  # Gemini conf < 0.7
}
```

### Adım 5: cross_validate() Fonksiyonunu Güncelle
```python
def cross_validate(
    production,
    sonnet_results,
    opus_results,
    gemini_results,
    ...
):
    # Her soru için tüm AI kaynaklarını kontrol et
    # Priority'ye göre en iyi sonucu seç
```

### Adım 6: main() Güncelle
```python
# Tüm AI sonuçlarını yükle
sonnet_results = load_vision_results(sonnet_path)
opus_results = load_vision_results(opus_v2_path)  # sadece v2
opus_v1_results = load_vision_results(opus_v1_path)
gemini_results = load_vision_results(gemini_path)

# Birleştir (priority ile)
all_ai = merge_with_priority(sonnet, opus_v2, opus_v1, gemini)

# cross_validate'a aktar
result = cross_validate(production, all_ai, ...)
```

## ÖNEMLİ DETAYLAR

### 1. Priority Mantığı
```
Aynı soru için birden fazla AI cevabı varsa:
  - Önce Sonnet'e bak
  - Sonnet yoksa Opus v2'ye bak
  - Opus v2 yoksa Opus v1'e bak
  - O da yoksa Gemini'ye bak

Bu, "ensemble" değil - tek kaynak seçimi!
```

### 2. Farklı Key'ler
- Her AI farklı screenshot'ları işlemiş olabilir
- Aynı (book, page, qnum) için farklı AI'lar farklı sonuç verebilir
- Priority ile çakışma durumunda en güvenilir olanı seç

### 3. Output Formatı
```python
{
    # ... mevcut alanlar ...
    "sonnet_answer": "A",
    "sonnet_confidence": 0.95,
    "opus_answer": "C",
    "opus_confidence": 0.88,
    "gemini_answer": None,
    "best_ai_answer": "A",  # Priority'ye göre seçilen
    "best_ai_source": "sonnet",
}
```

## TEST PLANI

1. **Dry-run test:**
   ```bash
   python cross_validate_answers.py --zero-db --analyze --simulate --dry-run
   ```

2. **Coverage karşılaştırma:**
   - Önceki: %32.9
   - Hedef: %70+

3. **Chi-square kontrolü:**
   - Önceki: 650.93 (FAIL)
   - Hedef: <15 (PASS)

## RİSKLER

1. **Memory:** 21K+ sonuç yüklüyor - RAM yeterli olmalı
2. **Time:** Daha fazla veri = daha uzun çalışma süresi
3. **Accuracy:** Yeni accuracy değerleri calibrate edilmeli

## SONUÇ

Bu güncelleme ile:
- AI coverage %32.9 → %80+
- Chi-square düzelmesi bekleniyor
- Daha doğru Bayesian posterior hesaplaması
