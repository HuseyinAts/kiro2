# 🚀 KIRO2 - YOLO Eğitimi Adım Adım Kılavuz

**Tarih:** 14 Aralık 2024
**Durum:** 1,934 annotation HAZIR - Hemen başlanabilir!
**Süre:** 12-16 saat toplam

---

## 📋 ÖNKOŞULLARı KONTROL ET

### 1. Python ve Gerekli Kütüphaneler

```bash
# Python 3.8+ gerekli
python --version

# Gerekli kütüphaneleri yükle
pip install ultralytics torch torchvision tqdm Pillow PyYAML
```

### 2. GPU Kontrolü (Opsiyonel ama ÇOK önerilir)

```bash
# GPU var mı?
python -c "import torch; print('GPU:', torch.cuda.is_available())"
python -c "import torch; print('GPU Name:', torch.cuda.get_device_name(0))"
```

**GPU yoksa:** CPU ile de çalışır ama çok yavaş olur (16 saat yerine 2-3 gün)

---

## 🎯 ADIM 1: Dataset Conversion (2 saat)

### Script'i İndir

İki dosyayı **C:\Users\husey\kiro2** klasörüne kaydet:
1. `labelme_to_yolo_converter.py`
2. `train_yolo_kiro2.py`

### Conversion'ı Çalıştır

```bash
cd C:\Users\husey\kiro2
python labelme_to_yolo_converter.py
```

**Ne yapıyor?**
- ✅ 1,934 JSON annotation'u YOLO formatına çeviriyor
- ✅ 8,813 PNG görseli kopyalıyor
- ✅ %80 train, %20 val split yapıyor
- ✅ dataset.yaml config dosyası oluşturuyor

**Beklenen Süre:** 10-20 dakika

**Output:**
```
C:\Users\husey\kiro2\yolo_dataset\
├── images/
│   ├── train/  (1,547 PNG)
│   └── val/    (387 PNG)
├── labels/
│   ├── train/  (1,547 TXT)
│   └── val/    (387 TXT)
└── dataset.yaml
```

**✅ Başarı Kontrolü:**
```bash
# Klasörleri kontrol et
dir C:\Users\husey\kiro2\yolo_dataset\images\train
dir C:\Users\husey\kiro2\yolo_dataset\labels\train
```

---

## 🎯 ADIM 2: Model Eğitimi (4-6 saat)

### Eğitimi Başlat

```bash
cd C:\Users\husey\kiro2
python train_yolo_kiro2.py
```

**Ne yapıyor?**
- ✅ YOLOv11n (nano) modelini yüklüyor
- ✅ 100 epoch eğitim yapıyor
- ✅ Her 10 epoch'ta checkpoint kaydediyor
- ✅ Validation sonuçlarını gösteriyor

**Beklenen Süre:**
- GPU ile: 4-6 saat
- CPU ile: 2-3 gün ⚠️

**İlerlemeyi Takip Et:**
```
Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
  1/100      1.2G      1.234      0.876      1.123        128        640
  2/100      1.2G      1.156      0.812      1.089        128        640
  ...
```

**✅ Başarı Kontrolü:**
- `mAP@50` > 0.80 → Çok iyi! ✅
- `mAP@50` > 0.70 → İyi ✅
- `mAP@50` < 0.70 → Daha fazla epoch gerekebilir

---

## 🎯 ADIM 3: Sonuçları İncele (30 dakika)

### Model Konumu

```
C:\Users\husey\kiro2\runs\detect\kiro2_soru_detection\
├── weights/
│   ├── best.pt       ← En iyi model
│   └── last.pt       ← Son epoch
├── results.png       ← Eğitim grafikleri
├── confusion_matrix.png
└── ...
```

### Grafikleri İncele

**results.png açın:**
- Box Loss düşüyor mu? ✅
- mAP artıyor mu? ✅
- Overfitting var mı? (train çok iyi, val kötü ise ⚠️)

### Test Et

```python
from ultralytics import YOLO

# Model yükle
model = YOLO('runs/detect/kiro2_soru_detection/weights/best.pt')

# Bir görseli test et
results = model.predict(
    source='C:/Users/husey/kiro2/veriseti/annotation/images/1.gercek sayilar/s1.png',
    save=True
)

# Sonucu göster
print(f"Tespit edilen: {len(results[0].boxes)} nesne")
```

**Output:**
```
runs/detect/predict/
└── s1.png  (bounding box'lar çizili)
```

---

## 🎯 ADIM 4: Production'a Al (2 saat)

### ONNX Export

```python
from ultralytics import YOLO

model = YOLO('runs/detect/kiro2_soru_detection/weights/best.pt')
model.export(format='onnx')
```

### FastAPI Backend'e Entegre Et

```python
# backend/services/yolo_service.py
from ultralytics import YOLO

class YOLODetectionService:
    def __init__(self):
        self.model = YOLO('path/to/best.pt')

    def detect_questions(self, image_path: str):
        results = self.model.predict(source=image_path)

        questions = []
        for box in results[0].boxes:
            questions.append({
                'bbox': box.xyxy.tolist(),
                'confidence': float(box.conf),
                'class': int(box.cls)
            })

        return questions
```

---

## 📊 BEKLENTİLER

### İlk Model (100 epoch)

| Metrik | Hedef | Açıklama |
|--------|-------|----------|
| mAP@50 | >0.80 | Ana metrik |
| mAP@50-95 | >0.60 | Detaylı metrik |
| Precision | >0.85 | Yanlış pozitif oranı |
| Recall | >0.80 | Kaçırılan soru oranı |

### Eğer Hedefler Tutmazsa

**mAP < 0.70:**
1. Epoch artır (100 → 200)
2. Model büyüt (n → s veya m)
3. Learning rate ayarla

**Overfitting var:**
1. Data augmentation artır
2. Dropout ekle
3. Daha fazla annotation ekle

---

## 🐛 SORUN GİDERME

### "CUDA out of memory"
```bash
# Batch size küçült
python train_yolo_kiro2.py  # script içinde batch=16 → batch=8 yap
```

### "No module named 'ultralytics'"
```bash
pip install ultralytics
```

### "Dataset not found"
```bash
# Yolları kontrol et
python -c "from pathlib import Path; print(Path('C:/Users/husey/kiro2/yolo_dataset').exists())"
```

### Eğitim çok yavaş
- GPU kullanımını kontrol et: `nvidia-smi`
- CPU'da mı çalışıyor? `device='cpu'` olabilir
- Batch size düşür: `batch=8` veya `batch=4`

---

## ✅ SONRAKİ ADIMLAR

### 1. Model iyileştirme (Opsiyonel)
- [ ] Eksik 6,847 PNG'yi annotate et
- [ ] Toplam 8,813 annotation'a ulaş
- [ ] Model yeniden eğit → mAP %95+

### 2. Production entegrasyonu
- [ ] ONNX modeli backend'e ekle
- [ ] API endpoint'i oluştur
- [ ] Frontend'den test et

### 3. Otomatik OCR pipeline
- [ ] YOLO detection → crop → OCR
- [ ] Soru metinlerini extract et
- [ ] Veritabanına kaydet

---

## 🎯 ÖZET: HEMEN BAŞLA!

```bash
# 1. Conversion (10-20 dk)
cd C:\Users\husey\kiro2
python labelme_to_yolo_converter.py

# 2. Eğitim (4-6 saat)
python train_yolo_kiro2.py

# 3. Test
# runs/detect/kiro2_soru_detection/results.png'yi aç

# 4. Model kullan
# runs/detect/kiro2_soru_detection/weights/best.pt
```

**Toplam Süre:** 12-16 saat (çoğu otomatik çalışıyor)

**Beklenen Sonuç:** %85-90 doğrulukla soru detection! 🎉

---

## 📞 YARDIM

Script'lerde sorun mu var?
- Script'leri göster, düzeltelim
- Hata mesajlarını paylaş
- GPU/CPU durumunu kontrol et

**BAŞARILAR! 🚀**
