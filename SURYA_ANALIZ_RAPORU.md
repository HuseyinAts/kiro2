# 🔬 SURYA OCR SCRIPT MİKROSKOBİK ANALİZ RAPORU

## 📋 GENEL BAKIŞ

**Dosya:** `C:\Users\husey\kiro2\surya_extraction.py`
**Satır Sayısı:** ~350 satır
**Amaç:** Türk sınav kitaplarından cevap anahtarı çıkarma
**Tarih:** Ocak 2025

---

## 🔴 KRİTİK HATALAR VE DÜZELTİLMESİ GEREKENLER

### HATA 1: YANLIŞ API KULLANIMI (Satır 31-44)
```python
# ESKİ (HATALI - Eski API)
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
from surya.table_rec import TableRecPredictor
from surya.layout import LayoutPredictor
```

**SORUN:** Surya OCR v0.17.0 (Ocak 2025) yeni API kullanıyor. `FoundationPredictor` şart!

**DOĞRU KULLANIM:**
```python
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
from surya.table_rec import TableRecPredictor
from surya.layout import LayoutPredictor
from surya.settings import settings
```

---

### HATA 2: MODEL BAŞLATMA YANLIŞ (Satır 72-93)
```python
# ESKİ (HATALI)
det_predictor = DetectionPredictor()
rec_predictor = RecognitionPredictor()
table_predictor = TableRecPredictor()
layout_predictor = LayoutPredictor()
```

**SORUN:** `RecognitionPredictor` artık `FoundationPredictor` gerektiriyor.

**DOĞRU KULLANIM:**
```python
# FoundationPredictor ÖNCE başlatılmalı
foundation_predictor = FoundationPredictor()

# RecognitionPredictor FoundationPredictor'ı alır
recognition_predictor = RecognitionPredictor(foundation_predictor)

# DetectionPredictor bağımsız
detection_predictor = DetectionPredictor()

# TableRecPredictor bağımsız
table_predictor = TableRecPredictor()

# LayoutPredictor özel checkpoint ile
layout_predictor = LayoutPredictor(
    FoundationPredictor(checkpoint=settings.LAYOUT_MODEL_CHECKPOINT)
)
```

---

### HATA 3: OCR FONKSİYONU YANLIŞ (Satır 134-149)
```python
# ESKİ (HATALI)
def surya_ocr_full_page(pil_img):
    det_results = det_predictor([pil_img])
    rec_results = rec_predictor([pil_img], det_results)
```

**SORUN:** API değişti. `det_predictor` argüman olarak geçiriliyor.

**DOĞRU KULLANIM:**
```python
def surya_ocr_full_page(pil_img):
    # Tek çağrı ile detection + recognition
    predictions = recognition_predictor(
        [pil_img], 
        det_predictor=detection_predictor
    )
    
    # Sonuçları parse et
    text_lines = []
    for result in predictions:
        for line in result.text_lines:
            text_lines.append(line.text)
    
    return ' '.join(text_lines)
```

---

### HATA 4: TABLO ÇIKARMA API'SI YANLIŞ (Satır 151-166)
```python
# ESKİ (HATALI)
def surya_table_extract(pil_img):
    table_results = table_predictor([pil_img])
    for result in table_results:
        if hasattr(result, 'cells'):
            for cell in result.cells:
                if hasattr(cell, 'text'):
                    cells.append(cell.text)
```

**SORUN:** Tablo sonuçlarının yapısı farklı. Ayrıca `cells` attribute'u farklı.

**DOĞRU KULLANIM:**
```python
def surya_table_extract(pil_img):
    table_results = table_predictor([pil_img])
    
    all_cells = []
    for result in table_results:
        # rows, cols, cells attributes
        if hasattr(result, 'cells'):
            for cell in result.cells:
                # cell.text, cell.bbox, cell.row_id, cell.col_id
                if cell.text:
                    all_cells.append(cell.text)
    
    return all_cells
```

---

### HATA 5: LAYOUT FONKSİYONU KULLANILMIYOR (Satır 168-185)
```python
def surya_layout_analyze(pil_img):
    # Tanımlanmış ama hiç çağrılmıyor!
```

**SORUN:** Layout analizi tanımlanmış ama `process_book_surya` içinde kullanılmıyor.

**ÖNERİ:** Ya kaldır ya da cevap anahtarı bölgelerini tespit etmek için kullan.

---

## 🟡 PERFORMANS İYİLEŞTİRMELERİ

### İYİLEŞTİRME 1: BATCH SIZE AYARLARI EKSİK

**MEVCUT:** Hiçbir batch size ayarı yok

**ÖNERİLEN:** Environment variables ekle
```python
import os

# RTX 3080 16GB VRAM için optimize edilmiş ayarlar
os.environ['RECOGNITION_BATCH_SIZE'] = '256'      # 40MB × 256 = 10GB
os.environ['DETECTOR_BATCH_SIZE'] = '24'          # 440MB × 24 = 10.5GB
os.environ['TABLE_REC_BATCH_SIZE'] = '48'         # 150MB × 48 = 7.2GB
os.environ['LAYOUT_BATCH_SIZE'] = '32'            # 220MB × 32 = 7GB

# VEYA daha güvenli (12GB kullanım)
os.environ['RECOGNITION_BATCH_SIZE'] = '200'
os.environ['DETECTOR_BATCH_SIZE'] = '20'
```

---

### İYİLEŞTİRME 2: MODEL COMPILATION EKSİK

**MEVCUT:** Compilation yok

**ÖNERİLEN:** %3-11 speedup için
```python
import os

# Tüm modelleri compile et
os.environ['COMPILE_ALL'] = 'true'

# VEYA ayrı ayrı
os.environ['COMPILE_DETECTOR'] = 'true'      # %3 speedup
os.environ['COMPILE_LAYOUT'] = 'true'        # %1 speedup
os.environ['COMPILE_TABLE_REC'] = 'true'     # %11 speedup
```

**NOT:** İlk çalıştırma yavaş olacak (compilation süresi). Sonraki çalıştırmalar hızlı.

---

### İYİLEŞTİRME 3: GÖRÜNTÜ BOYUTU OPTİMİZASYONU (Satır 100-116)

**MEVCUT:**
```python
SCALE_FACTOR = 2.0  # 2x büyütme
if max(new_w, new_h) > 3000:
    ratio = 3000 / max(new_w, new_h)
```

**SORUN:** Surya dokümentasyonu max 2048px width öneriyor.

**ÖNERİLEN:**
```python
SCALE_FACTOR = 2.0
MAX_DIMENSION = 2048  # Surya için optimal

def preprocess_pil(pil_img, scale=SCALE_FACTOR):
    w, h = pil_img.size
    new_w, new_h = int(w * scale), int(h * scale)
    
    # Max 2048px (Surya optimal)
    if max(new_w, new_h) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / max(new_w, new_h)
        new_w, new_h = int(new_w * ratio), int(new_h * ratio)
    
    # Min boyut kontrolü (çok küçük görüntüler için)
    if min(new_w, new_h) < 256:
        ratio = 256 / min(new_w, new_h)
        new_w, new_h = int(new_w * ratio), int(new_h * ratio)
```

---

### İYİLEŞTİRME 4: BATCH PROCESSING EKSİK

**MEVCUT:** Her görüntü ayrı ayrı işleniyor (satır 213-250)
```python
for page_path in end_pages:
    pil_img = read_image_safe(page_path)
    text = surya_ocr_full_page(pil_img)  # Tek görüntü
```

**SORUN:** Surya batch processing için optimize edilmiş. Tek tek işlemek VRAM'i verimsiz kullanıyor.

**ÖNERİLEN:**
```python
def process_pages_batch(page_paths, batch_size=8):
    """Görüntüleri batch halinde işle"""
    all_texts = []
    
    for i in range(0, len(page_paths), batch_size):
        batch_paths = page_paths[i:i+batch_size]
        
        # Batch yükle
        images = []
        for path in batch_paths:
            img = read_image_safe(path)
            if img:
                img = preprocess_pil(img)
                images.append(img)
        
        if not images:
            continue
        
        # BATCH OCR (çok daha hızlı!)
        predictions = recognition_predictor(
            images, 
            det_predictor=detection_predictor
        )
        
        # Sonuçları parse et
        for pred in predictions:
            text = ' '.join([line.text for line in pred.text_lines])
            all_texts.append(text)
    
    return all_texts
```

---

### İYİLEŞTİRME 5: DİL PARAMETRESİ

**MEVCUT:** Dil belirtilmiyor

**ÖNERİLEN:** Türkçe için optimize
```python
# Dil belirtmek opsiyonel ama önerilir
# Türkçe: 'tr', İngilizce: 'en'
langs = ['tr']  # veya None (otomatik tespit)

predictions = recognition_predictor(
    images,
    langs=[langs] * len(images),  # Her görüntü için dil
    det_predictor=detection_predictor
)
```

---

### İYİLEŞTİRME 6: TASK NAME KULLANIMI

**MEVCUT:** Varsayılan task kullanılıyor

**ÖNERİLEN:** Cevap anahtarları için optimize
```python
# task_name seçenekleri:
# - 'ocr_with_boxes': Varsayılan, bbox + text (önerilir)
# - 'ocr_without_boxes': Sadece text, daha hızlı
# - 'block_without_boxes': Paragraf/denklem blokları için

# Cevap anahtarları için 'ocr_with_boxes' en uygun
# Çünkü bbox bilgisi sıralama için gerekli olabilir
```

---

## 🟢 İYİ OLAN KISIMLAR

### ✅ Türkçe Karakter Güvenli Okuma (Satır 98-107)
```python
def read_image_safe(img_path):
    """Türkçe karakter güvenli okuma"""
    try:
        img = Image.open(img_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        return None
```
**YORUM:** PIL ile Unicode destekli okuma doğru yaklaşım.

---

### ✅ Çoklu Regex Pattern (Satır 192-207)
```python
patterns = [
    r'(\d{1,3})\s*[.]\s*([A-E])\b',      # 1.A
    r'(\d{1,3})\s*\)\s*([A-E])\b',        # 1)A
    r'(\d{1,3})\s*[-]\s*([A-E])\b',       # 1-A
    r'(\d{1,3})\s*[:]\s*([A-E])\b',       # 1:A
    r'(\d{1,3})\s+([A-E])(?=\s|\d|$)',    # 1 A
    r'(\d{1,3})([A-E])(?=\s|\d|$)',       # 1A
    r'([A-E])\s*[-.:)]\s*(\d{1,3})',      # A-1 (ters)
]
```
**YORUM:** Kapsamlı pattern listesi. Tüm yaygın formatları kapsıyor.

---

### ✅ OCR Hata Düzeltme (Satır 219-231)
```python
def fix_ocr_errors(text):
    replacements = [
        (r'[lI|](?=\s*[.\):-]?\s*[A-Ea-e])', '1'),  # l/I/| → 1
        (r'O(?=\s*[.\):-]?\s*[A-Ea-e])', '0'),       # O → 0
        (r'S(?=\d)', '5'),                            # S5 → 55
        (r'Z(?=\d)', '2'),                            # Z3 → 23
    ]
```
**YORUM:** Yaygın OCR karıştırmalarını düzeltiyor. İyi yaklaşım.

---

### ✅ Dual Strateji (Satır 237-282)
```python
# STRATEJİ 1: SON SAYFALAR (Kitap sonu cevap anahtarı)
# STRATEJİ 2: SAYFA ALTLARI
```
**YORUM:** İki farklı cevap anahtarı konumunu kontrol etmek mantıklı.

---

### ✅ GPU Temizleme (Satır 320-324)
```python
if idx % 20 == 0:
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
```
**YORUM:** VRAM sızıntısını önlemek için düzenli temizlik yapılıyor.

---

## 📊 VRAM KULLANIM ANALİZİ (RTX 3080 16GB)

| Model | Batch Size | VRAM/Batch | Toplam VRAM |
|-------|------------|------------|-------------|
| Detection | 24 | 440MB | 10.5GB |
| Recognition | 256 | 40MB | 10.2GB |
| Table Rec | 48 | 150MB | 7.2GB |
| Layout | 32 | 220MB | 7.0GB |

**NOT:** Modeller aynı anda yüklü olacak, bu yüzden toplam VRAM kullanımı daha yüksek olacak. Güvenli batch size'lar kullanılmalı.

**ÖNERİLEN GÜVENLI AYARLAR (16GB VRAM için):**
```python
os.environ['RECOGNITION_BATCH_SIZE'] = '128'   # ~5GB
os.environ['DETECTOR_BATCH_SIZE'] = '16'       # ~7GB
os.environ['TABLE_REC_BATCH_SIZE'] = '32'      # ~5GB
os.environ['LAYOUT_BATCH_SIZE'] = '24'         # ~5GB
```

---

## 🚀 TAM DÜZELTİLMİŞ SCRIPT ÖNERİSİ

Aşağıdaki değişiklikler yapılmalı:

1. **Import düzeltmeleri** - FoundationPredictor eklenmeli
2. **Model başlatma** - Doğru sıra ve bağımlılıklar
3. **Batch size** - Environment variables
4. **Compilation** - Speedup için
5. **Batch processing** - Verimlilik için
6. **Max dimension** - 2048px
7. **Dil parametresi** - Türkçe için

---

## 📈 BEKLENEN İYİLEŞMELER

| Metrik | Mevcut | Düzeltme Sonrası |
|--------|--------|------------------|
| Hız | ~0.5 kitap/dk | ~2-3 kitap/dk |
| VRAM Kullanımı | Verimsiz | Optimize |
| Doğruluk | ? | %70-85 |
| Hata Oranı | Yüksek | Düşük |

---

## 📝 SONUÇ

Script'in temel mantığı doğru ancak:
1. **API uyumsuzluğu** - Surya v0.17.0 ile çalışmayacak
2. **Performans kaybı** - Batch processing eksik
3. **Kaynak israfı** - Batch size optimize edilmemiş

**ACİL EYLEM:** Script'i güncel Surya API'sine uyumlu hale getir.
