# 🚀 KIRO2 - Tüm Kitaplar İçin YOLO Detection Kılavuzu

**Tarih:** 31 Aralık 2024  
**Amaç:** 317 kitabın tüm sayfalarında soru/cevap bölgelerini tespit etmek

---

## 📋 ÖNKOŞULLARı KONTROL ET

### 1. Python Kütüphaneleri
```powershell
# ultralytics yüklü mü?
pip show ultralytics

# Değilse yükle
pip install ultralytics torch torchvision
```

### 2. Model Kontrolü
```powershell
# Model var mı?
Test-Path "C:\Users\husey\kiro2\models\yolo11_best.pt"
```

### 3. GPU Kontrolü (Opsiyonel ama ÇOK önerilir)
```python
import torch
print(f"GPU: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
```

---

## 🎯 ÇALIŞTIRMA

### Tek Komutla Başlat
```powershell
cd C:\Users\husey\kiro2
python run_yolo_all_books.py
```

### Beklenen Çıktı
```
================================================================================
🚀 KIRO2 - TÜM KİTAPLAR İÇİN YOLO DETECTION
================================================================================
⏰ Başlangıç: 2024-12-31 15:30:00
✅ GPU: NVIDIA GeForce RTX 3060 (12.0 GB)

📦 Model yükleniyor: C:\Users\husey\kiro2\models\yolo11_best.pt
✅ Model yüklendi

📚 Kitaplar taranıyor...
✅ 317 kitap, toplam 75,745 sayfa bulundu

================================================================================
🔄 Detection başlatılıyor...
================================================================================

[1/317] 📖 2019-2020-Acil Matematiğin ilacı-1 (286 sayfa)
   ✅ 286 sayfa işlendi (45.2s, 6.3 sayfa/s)
   📊 823 tespit: {'soru': 612, 'cevaplar': 45, 'konu': 28, 'test_no': 138}
   ⏱️ Tahmini kalan süre: 180 dakika

[2/317] 📖 2020-2021-ACİL-TYT Matematik Soru Bankası (430 sayfa)
   ...
```

---

## ⏱️ TAHMİNİ SÜRELER

| Donanım | Sayfa/Saniye | 75K Sayfa Süresi |
|---------|--------------|------------------|
| **RTX 4090** | ~30 | ~42 dakika |
| **RTX 3080** | ~20 | ~63 dakika |
| **RTX 3060** | ~10 | ~125 dakika |
| **GTX 1080** | ~6 | ~210 dakika |
| **CPU (i7)** | ~1 | ~21 saat |

---

## 📁 ÇIKTI YAPISI

```
C:\Users\husey\d-dataset\output\detections\
├── 2019-2020-Acil Matematiğin ilacı-1\
│   ├── page_0001.json
│   ├── page_0002.json
│   └── ...
├── 2020-2021-ACİL-TYT Matematik Soru Bankası\
│   ├── page_0001.json
│   └── ...
├── ... (317 kitap)
└── detection_summary.json   ← Genel özet
```

### Örnek JSON (page_0010.json)
```json
[
  {
    "class_id": 0,
    "class_name": "soru",
    "confidence": 0.92,
    "x1": 641,
    "y1": 119,
    "x2": 969,
    "y2": 274
  },
  {
    "class_id": 1,
    "class_name": "cevaplar",
    "confidence": 0.87,
    "x1": 638,
    "y1": 73,
    "x2": 787,
    "y2": 114
  }
]
```

---

## 🎯 DETECTION SONRASI

Detection tamamlandıktan sonra cevap eşleştirme scriptini çalıştır:

```python
# Claude'da çalıştır (veya Python scripti olarak)
python match_with_detections.py
```

**Beklenen sonuç:**
- Mevcut: %21.5 eşleşme (5 kitap detection ile)
- Hedef: **%60-80 eşleşme** (317 kitap detection ile)

---

## 🐛 SORUN GİDERME

### "CUDA out of memory"
```python
# Batch size küçült (script içinde)
BATCH_SIZE = 4  # veya 2
IMAGE_SIZE = 416  # 640 yerine
```

### "Model not found"
```powershell
# Model yolunu kontrol et
dir C:\Users\husey\kiro2\models\*.pt
```

### Detection çok yavaş
```powershell
# GPU kullanımını kontrol et
nvidia-smi

# CPU'da mı çalışıyor? Script çıktısına bak
# "⚠️ GPU bulunamadı" mesajı varsa CUDA kurulumu gerekli
```

### "No books found"
```powershell
# Screenshot klasörünü kontrol et
dir "C:\Users\husey\kiro2\veriseti\zkitap\screenshots"
```

---

## 📊 BAŞARI KRİTERLERİ

Detection başarılı sayılır eğer:

| Metrik | Hedef | Açıklama |
|--------|-------|----------|
| Soru tespiti | >90% | Her sayfadaki sorular tespit edilmeli |
| Cevap tespiti | >80% | Cevap anahtarı sayfaları bulunmalı |
| False positive | <5% | Yanlış tespit az olmalı |

---

## ✅ SONRAKI ADIMLAR

1. ✅ Detection çalıştır (`run_yolo_all_books.py`)
2. ⏳ Detection tamamlanmasını bekle (~2-3 saat)
3. 🔄 Eşleştirme scriptini çalıştır
4. 📊 Sonuçları kontrol et

---

## 📞 YARDIM

Sorun mu var?
- Script çıktısındaki hata mesajlarını paylaş
- `detection_summary.json` dosyasını incele
- GPU/CPU durumunu kontrol et

**BAŞARILAR! 🚀**
