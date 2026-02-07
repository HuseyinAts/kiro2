# KIRO2 Hızlı Başlangıç Rehberi
## YKS Soru Çıkarma Pipeline

Bu rehber, KIRO2 sistemini kullanarak YKS kitaplarından otomatik soru çıkarmayı adım adım açıklar.

---

## 📋 Gereksinimler

### Donanım
- **GPU:** NVIDIA RTX 3080 veya üzeri (16GB+ VRAM önerilir)
- **RAM:** 32GB+
- **Disk:** 50GB+ boş alan

### Yazılım
```bash
# Python 3.10+
python --version

# CUDA kurulumu doğrulama
nvidia-smi
```

---

## 🚀 Kurulum

### 1. Sanal Ortam Oluştur
```bash
cd C:\Users\husey\kiro2
python -m venv venv
venv\Scripts\activate
```

### 2. Temel Paketleri Kur
```bash
# PyTorch (CUDA destekli)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# YOLO
pip install ultralytics

# Surya OCR
pip install surya-ocr

# PDF işleme
pip install pdf2image pillow

# Türkçe NLP (opsiyonel)
pip install zemberek-python
```

### 3. Poppler Kurulumu (PDF için)
Windows'ta:
1. https://github.com/oschwartz10612/poppler-windows/releases adresinden indir
2. `C:\poppler` dizinine çıkar
3. PATH'e ekle: `C:\poppler\bin`

---

## 📁 Proje Yapısı

```
C:\Users\husey\kiro2\
├── veriseti/
│   └── kiro2_yolo_dataset/     # YOLO veri seti
│       ├── data.yaml
│       ├── train/
│       │   ├── images/         # 1,516 eğitim görüntüsü
│       │   └── labels/         # 1,516 etiket dosyası
│       └── val/
│           ├── images/         # 270 doğrulama görüntüsü
│           └── labels/
├── runs/                       # Eğitim çıktıları
├── train_yolo.py              # YOLO eğitim scripti
├── extract_questions.py       # Soru çıkarma pipeline
├── yolo_dataset_analysis.py   # Veri seti analizi
└── outputs/                   # Çıkarılan sorular
```

---

## 🎯 Kullanım

### Adım 1: Veri Seti Analizi
```bash
python yolo_dataset_analysis.py
```

Çıktı: `veriseti/kiro2_yolo_dataset/dataset_analysis.json`

### Adım 2: YOLO Model Eğitimi

**Hızlı Eğitim (Test için):**
```bash
python train_yolo.py --epochs 10 --batch 4 --imgsz 640
```

**Tam Eğitim (Üretim için):**
```bash
python train_yolo.py \
    --epochs 100 \
    --batch 8 \
    --imgsz 1280 \
    --model yolov8l.pt \
    --cache \
    --augment
```

**Beklenen Süre:**
- Hızlı: ~30 dakika
- Tam: ~6-8 saat

**Beklenen Sonuç:**
- `runs/kiro2/train_YYYYMMDD_HHMM/weights/best.pt`
- mAP@0.5 > 0.85

### Adım 3: Model Değerlendirme
```bash
python train_yolo.py --eval-only runs/kiro2/train_*/weights/best.pt
```

### Adım 4: Soru Çıkarma

**Tek PDF:**
```bash
python extract_questions.py \
    --model runs/kiro2/train_*/weights/best.pt \
    --input "kitaplar/matematik_tyt.pdf" \
    --output outputs/matematik_sorulari.json
```

**Görüntü Klasörü:**
```bash
python extract_questions.py \
    --model runs/kiro2/train_*/weights/best.pt \
    --input "veriseti/zkitap/screenshots/Mikro_Orijinal-2025" \
    --output outputs/mikro_sorular.json
```

**Sadece Tespit (OCR olmadan):**
```bash
python extract_questions.py \
    --model runs/kiro2/train_*/weights/best.pt \
    --input sayfa.png \
    --output tespit.json \
    --no-ocr
```

---

## 📊 Çıktı Formatı

```json
{
  "total_pages": 200,
  "total_questions": 850,
  "pages": [
    {
      "page_number": 1,
      "test_number": "Test 1",
      "topic": "Fonksiyonlar",
      "question_count": 6,
      "questions": [
        {
          "number": 1,
          "text": "f(x) = 2x + 3 fonksiyonu için f(2) değeri kaçtır?",
          "options": ["A) 5", "B) 7", "C) 9", "D) 11", "E) 13"],
          "correct_answer": "B",
          "topic": "Fonksiyonlar",
          "difficulty": null,
          "page": 1,
          "bbox": {"x1": 50, "y1": 100, "x2": 400, "y2": 300},
          "raw_ocr": "..."
        }
      ]
    }
  ]
}
```

---

## ⚡ Performans İpuçları

### GPU Bellek Optimizasyonu
```bash
# Düşük VRAM için
python train_yolo.py --batch 4 --imgsz 640

# Yüksek VRAM için
python train_yolo.py --batch 16 --imgsz 1280 --cache
```

### Paralel İşleme
```python
# extract_questions.py içinde
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_page, pages))
```

### Batch OCR
```python
# Birden fazla bölgeyi tek seferde işle
regions = [crop_region(img, bbox) for bbox in question_boxes]
texts = ocr.batch_extract(regions)
```

---

## 🔧 Sorun Giderme

### CUDA Bellek Hatası
```bash
# Batch size düşür
python train_yolo.py --batch 2

# veya mixed precision kullan
python train_yolo.py --amp
```

### OCR Türkçe Karakter Sorunu
```python
# Zemberek ile post-processing
from zemberek import TurkishMorphology

morph = TurkishMorphology.create_with_defaults()
corrected = morph.normalize(text)
```

### PDF Dönüştürme Hatası
```bash
# Poppler yolunu kontrol et
where pdftoppm

# Manuel yol belirt
from pdf2image import convert_from_path
images = convert_from_path(pdf, poppler_path=r"C:\poppler\bin")
```

---

## 📈 Gelecek Adımlar

1. **Model İyileştirme:**
   - Daha fazla veri etiketleme
   - Data augmentation artırma
   - Ensemble model

2. **OCR İyileştirme:**
   - BERTurk fine-tuning
   - Matematik LaTeX dönüşümü

3. **Çözüm Üretimi:**
   - DeepSeek-Math entegrasyonu
   - Adım adım çözüm

4. **API Dağıtımı:**
   - FastAPI endpoint
   - Redis caching
   - Kubernetes scaling

---

## 📞 Destek

- **Proje:** KIRO2 YKS Hazırlık Platformu
- **Veri Seti:** 1,786 etiketli sayfa, 22 yayınevi, 32 kitap serisi
- **Hedef:** 340,000+ soru veritabanı

---

*Son Güncelleme: Ocak 2026*
