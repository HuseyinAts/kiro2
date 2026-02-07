---
allowed-tools: Bash, Read, Glob
argument-hint: [test|analyze|benchmark] [image_path]
description: OCR pipeline test ve analiz
---

## Task
OCR pipeline işlemi: $ARGUMENTS

## OCR Pipeline (KIRO2)

```
Görüntü → YOLO (Alan Tespit) → Surya (Layout) → EasyOCR (Metin) → Gemini Vision (Doğrulama)
```

## Komutlar

### Test - Tek görüntü test
```bash
cd ai_ml && python -m ocr.pipeline --test --image "$ARGUMENTS"
```

### Analyze - Detaylı analiz
```bash
cd ai_ml && python -m ocr.pipeline --analyze --image "$ARGUMENTS" --verbose
```

### Benchmark - Performans testi
```bash
cd ai_ml && python -m ocr.benchmark --samples 100
```

## Test Görüntüleri
```
ai_ml/tests/fixtures/ocr/
├── math_question.png      # Matematik sorusu
├── physics_diagram.png    # Fizik şeması
├── turkish_paragraph.png  # Türkçe paragraf
├── multiple_choice.png    # Çoktan seçmeli
└── handwritten.png        # El yazısı
```

## Çıktı Metrikleri

| Metrik | Hedef | Açıklama |
|--------|-------|----------|
| Accuracy | >95% | Karakter doğruluğu |
| Latency | <2s | İşlem süresi |
| Layout | >90% | Alan tespiti |
| Turkish | >98% | Türkçe karakter |

## Sorun Giderme

### Düşük Accuracy
1. YOLO model güncelle
2. Preprocessing ayarla (contrast, threshold)
3. Surya confidence threshold düşür

### Türkçe Karakter Sorunu
- EasyOCR lang='tr' kontrol
- UTF-8 encoding doğrula
- Zemberek normalizasyon
