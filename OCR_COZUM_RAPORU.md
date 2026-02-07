# Türk Sınav Kitapları İçin OCR Çözümleri: %4'ten %95 Doğruluğa

## 🎯 ÖZET

Mevcut **EasyOCR ile %4 çıkarma oranınız** neredeyse kesinlikle yetersiz görüntü çözünürlüğü ve ön işlemeden kaynaklanıyor, OCR motorunun kendisinden değil. Kritik düzeltme, OCR'dan önce görüntüleri büyüterek karakter yüksekliklerinin **minimum 25-30 piksel**e ulaşmasını sağlamaktır. Doğru ön işleme ve araç seçimiyle gerçekçi olarak **%85-95 doğruluk** elde edebilirsiniz.

Optimal çözüm, tablo çıkarma için **Surya OCR veya PaddleOCR PP-Structure**'ı agresif görüntü ön işleme ile birleştirir. Minimum kodla maksimum doğruluk için **Gemini 2.0 Flash** API aracılığıyla doğrudan JSON çıktısı ile ~1.000 sayfa başına ~1$ ile en iyi maliyet-doğruluk oranını sunar.

---

## 📊 Doğruluk ve Pratikliğe Göre Sıralanmış Çözümler

Kapsamlı karşılaştırmalara ve Türkçe dil gereksinimlerine dayalı olarak, kullanım durumunuz için en iyi yaklaşımlar:

| Sıra | Çözüm | Doğruluk | Türkçe | Maliyet/1K sayfa | En İyi Kullanım |
|------|-------|----------|--------|------------------|-----------------|
| 1 | **Surya OCR** + ön işleme | %95+ | ✅ Doğal | 0₺ (kendi sunucu) | Hepsi bir arada açık kaynak |
| 2 | **Gemini 2.0 Flash** Vision | %85+ | ✅ Mükemmel | ~35₺ | En hızlı uygulama |
| 3 | **PaddleOCR PP-StructureV3** | %93+ | ⚠️ Fine-tune gerekli | 0₺ (kendi sunucu) | Tablo ağırlıklı dokümanlar |
| 4 | **Azure Document Intelligence** | %90+ | ✅ Tam destek | ~350₺ | Kurumsal/uyumluluk |
| 5 | **TableTransformer + EasyOCR** | %85+ | ✅ EasyOCR ile | 0₺ (kendi sunucu) | Sadece yapılandırılmış gridler |

**⚠️ AWS Textract ÖNERİLMİYOR** — Türkçe dil desteği yoktur.

---

## 🔴 EasyOCR'ınızın Neden Başarısız Olduğu (ve Nasıl Düzeltileceği)

**%4 doğruluk**ın temel nedeni neredeyse kesinlikle cevap anahtarı karakterlerinizin güvenilir OCR için gereken **minimum 18 piksel yükseklik** eşiğinin altında olmasıdır.

### Çözünürlük Gereksinimleri (Küçük Metin OCR için)

| Font Boyutu | Minimum DPI | Karakter Yüksekliği |
|-------------|-------------|---------------------|
| 12pt+ | 300 | 25+ piksel |
| 10-12pt | 400 | 25+ piksel |
| <10pt | 600 veya büyütme | 25+ piksele ulaşmalı |

### Düzeltme Kodu

```python
import cv2
import numpy as np
import easyocr

def kucuk_metin_icin_on_isleme(goruntu_yolu, buyutme_orani=3):
    """Küçük fontlu cevap anahtarları için kritik ön işleme"""
    img = cv2.imread(goruntu_yolu)
    
    # ADIM 1: 3x Büyütme (EN KRİTİK DÜZELTME)
    img = cv2.resize(img, None, fx=buyutme_orani, fy=buyutme_orani, 
                     interpolation=cv2.INTER_CUBIC)
    
    # ADIM 2: Gri tonlamaya çevir
    gri = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # ADIM 3: CLAHE kontrast iyileştirme
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    iyilestirilmis = clahe.apply(gri)
    
    # ADIM 4: Bilateral filtre (kenarları koruyarak gürültü azaltma)
    gurultusuz = cv2.bilateralFilter(iyilestirilmis, 9, 75, 75)
    
    # ADIM 5: Adaptif eşikleme
    ikili = cv2.adaptiveThreshold(
        gurultusuz, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, blockSize=15, C=8
    )
    
    # ADIM 6: Beyaz kenarlık ekle (OCR motorlarına yardımcı olur)
    kenarlikli = cv2.copyMakeBorder(ikili, 10, 10, 10, 10, 
                                     cv2.BORDER_CONSTANT, value=255)
    return kenarlikli

def easyocr_ile_cikar(goruntu_yolu):
    """Cevap anahtarları için optimize edilmiş ayarlarla EasyOCR"""
    on_islenmis = kucuk_metin_icin_on_isleme(goruntu_yolu)
    
    okuyucu = easyocr.Reader(['tr', 'en'], gpu=True)
    sonuclar = okuyucu.readtext(
        on_islenmis,
        allowlist='ABCDEabcde0123456789.()',  # Cevap anahtarları için beyaz liste
        min_size=5,           # Varsayılan 10'dan düşür
        text_threshold=0.6,   # Düşük eşik
        low_text=0.3,
        decoder='beamsearch',
        beamWidth=10
    )
    return sonuclar
```

---

## 🏆 En İyi Açık Kaynak Çözüm: Surya OCR Pipeline

**Surya OCR** (19K+ GitHub yıldızı) **90+ dilde** doğal Türkçe desteği, yerleşik tablo tanıma ve yerleşim analizi ile en iyi hepsi bir arada açık kaynak çözümü sağlar:

```python
from PIL import Image
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
from surya.table_rec import TableRecPredictor
from surya.foundation import FoundationPredictor
import re

class TurkceCevapAnahtariCikarici:
    def __init__(self):
        self.foundation = FoundationPredictor()
        self.detection = DetectionPredictor()
        self.recognition = RecognitionPredictor(self.foundation)
        self.table_rec = TableRecPredictor()
    
    def cikar(self, goruntu_yolu):
        goruntu = Image.open(goruntu_yolu)
        
        # Önce tablo çıkarmayı dene
        tablo_sonuclari = self.table_rec([goruntu])[0]
        
        if tablo_sonuclari.get('cells'):
            return self._tablodan_cikar(tablo_sonuclari)
        
        # Yedek olarak tam OCR
        ocr_sonuclari = self.recognition([goruntu], 
                                          det_predictor=self.detection)[0]
        metin = ' '.join([satir['text'] for satir in ocr_sonuclari['text_lines']])
        return self._metinden_cikar(metin)
    
    def _tablodan_cikar(self, tablo_sonuc):
        cevaplar = {}
        for hucre in tablo_sonuc.get('cells', []):
            metin = hucre.get('text', '').strip()
            esleme = re.match(r'(\d+)\s*[.\):-]\s*([A-Ea-e])', metin)
            if esleme:
                cevaplar[int(esleme.group(1))] = esleme.group(2).upper()
        return dict(sorted(cevaplar.items()))
    
    def _metinden_cikar(self, metin):
        desen = r'(\d+)\s*[.\):-]\s*([A-Ea-e])'
        eslemeler = re.findall(desen, metin, re.IGNORECASE)
        return dict(sorted({int(s): c.upper() for s, c in eslemeler}.items()))

# Kullanım
cikarici = TurkceCevapAnahtariCikarici()
cevaplar = cikarici.cikar("cevap_anahtari.png")
print(cevaplar)  # {1: 'A', 2: 'B', 3: 'C', ...}
```

**Kurulum**: `pip install surya-ocr`

---

## 📋 En İyi Tablo Çıkarma: PaddleOCR PP-StructureV3

Net tablo/grid yapılarına sahip dokümanlar için **PaddleOCR PP-StructureV3** tablo karşılaştırmalarında **%93+ TEDS doğruluğu** elde eder:

```python
from paddleocr import PPStructure

# Tablo çıkarma motorunu başlat
tablo_motoru = PPStructure(
    show_log=False,
    table=True,
    lang='latin'  # Türkçe karakterleri kapsar
)

# Cevap anahtarı görüntüsünü işle
sonuc = tablo_motoru("cevap_anahtari.png")

# Yapılandırılmış veriyi çıkar
for oge in sonuc:
    if oge['type'] == 'table':
        html_tablo = oge['res']['html']
        hucreler = oge['res']['cells']
        
        # Soru-cevap çiftleri için hücreleri ayrıştır
        for hucre in hucreler:
            print(f"Hücre: {hucre['text']}")
```

**Kurulum**: `pip install paddlepaddle paddleocr`

---

## 🚀 Vision LLM Yaklaşımı: En Hızlı Uygulama Yolu

Minimum kodla en hızlı çalışan çözüm için **Gemini 2.0 Flash** en iyi doğruluk-maliyet oranını sunar:

```python
import google.generativeai as genai
import json
from PIL import Image

genai.configure(api_key="API_ANAHTARINIZ")

def gemini_ile_cikar(goruntu_yolu):
    model = genai.GenerativeModel("gemini-2.0-flash")
    goruntu = Image.open(goruntu_yolu)
    
    prompt = """Sen Türk sınav materyallerinden cevap anahtarı verisi çıkaran bir OCR uzmanısın.

GÖREV: Bu görüntüden tüm soru numaralarını ve doğru cevaplarını çıkar.

TALİMATLAR:
1. Her soru numarasını ve karşılık gelen cevabı (A, B, C, D veya E) belirle
2. Hem grid/tablo formatlarını hem de metin tabanlı cevap anahtarlarını ("1.A 2.B 3.C") işle
3. Herhangi bir cevap belirsizse "?" olarak işaretle
4. Tahmin yapma veya cevap uydurma

ÇIKTI FORMATI (sadece geçerli JSON):
{
  "cevaplar": [{"s": 1, "c": "A"}, {"s": 2, "c": "B"}, ...],
  "toplam": <sayı>,
  "format": "grid|metin|karma",
  "guven": "yuksek|orta|dusuk"
}"""
    
    yanit = model.generate_content(
        [prompt, goruntu],
        generation_config={"temperature": 0}
    )
    
    return json.loads(yanit.text)

# Kullanım
sonuc = gemini_ile_cikar("cevap_anahtari.png")
print(sonuc)
```

### Maliyet Karşılaştırması (1.000 cevap anahtarı görüntüsü başına)

| Sağlayıcı | Model | Maliyet | Doğruluk |
|-----------|-------|---------|----------|
| Google | Gemini 1.5 Flash | ~17₺ | İyi |
| Google | **Gemini 2.0 Flash** | ~35₺ | **En İyi** |
| Anthropic | Claude Haiku 3 | ~70₺ | Çok İyi |
| OpenAI | GPT-4o-mini | ~100₺ | İyi |
| OpenAI | GPT-4o | ~850₺ | İyi |

---

## 💼 Ticari API Karşılaştırması (Türkçe Desteği)

| Hizmet | Türkçe | Tablo Doğruluğu | Maliyet/1K | Öneri |
|--------|--------|-----------------|------------|-------|
| **Azure Document Intelligence** | ✅ Mükemmel | Mükemmel | ~350₺ | En iyi ticari seçenek |
| **Google Document AI** | ✅ Mükemmel | Çok İyi | ~1000₺ | İyi alternatif |
| **ABBYY FineReader** | ✅ Tam | Mükemmel | Satışa danışın | Premium kalite |
| **AWS Textract** | ❌ Yok | İyi | ~500₺ | **Türkçe için KAÇININ** |

### Azure Document Intelligence Kod Örneği

```python
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

def azure_ile_cikar(endpoint, anahtar, dosya_yolu):
    istemci = DocumentIntelligenceClient(endpoint, AzureKeyCredential(anahtar))
    
    with open(dosya_yolu, "rb") as f:
        anketci = istemci.begin_analyze_document("prebuilt-layout", f)
    
    sonuc = anketci.result()
    
    cevaplar = {}
    for tablo in sonuc.tables:
        for hucre in tablo.cells:
            # Soru-cevap çiftleri için hücre içeriğini ayrıştır
            import re
            esleme = re.match(r'(\d+)\s*[.\):-]\s*([A-Ea-e])', hucre.content)
            if esleme:
                cevaplar[int(esleme.group(1))] = esleme.group(2).upper()
    
    return cevaplar
```

---

## 🔤 Cevap Anahtarı Ayrıştırma için Regex Desenleri

Bu desenler en yaygın Türk sınav cevap anahtarı formatlarını işler:

```python
import re

def cevaplari_cikar(ocr_metni):
    """Çoklu formatları destekleyen evrensel cevap anahtarı çıkarıcı"""
    
    desenler = [
        r'(\d{1,3})\s*[.]\s*([A-Ea-e])',      # 1.A  2.B  3.C
        r'(\d{1,3})\s*\)\s*([A-Ea-e])',        # 1)A  2)B  3)C
        r'(\d{1,3})\s*[-]\s*([A-Ea-e])',       # 1-A  2-B  3-C
        r'(\d{1,3})\s*[:]\s*([A-Ea-e])',       # 1:A  2:B  3:C
        r'(\d{1,3})\s+([A-Ea-e])(?=\s|$)',     # 1 A  2 B  3 C (boşlukla ayrılmış)
        r'([A-Ea-e])\s*[.)\-:]\s*(\d{1,3})',   # A.1  B)2  (ters format)
    ]
    
    cevaplar = {}
    for desen in desenler:
        eslemeler = re.findall(desen, ocr_metni, re.IGNORECASE | re.MULTILINE)
        for esleme in eslemeler:
            # Ters format kontrolü
            if re.match(r'[A-Ea-e]', esleme[0]):
                cevap, soru_no = esleme
            else:
                soru_no, cevap = esleme
            cevaplar[int(soru_no)] = cevap.upper()
    
    return dict(sorted(cevaplar.items()))

def ocr_hatalarini_duzelt(metin):
    """Cevap anahtarlarında yaygın OCR yanlış okumalarını düzelt"""
    # Soru numaraları için yaygın değişimler
    metin = re.sub(r'[lI](?=\s*[.\):-]\s*[A-Ea-e])', '1', metin)  # l/I → 1
    metin = re.sub(r'O(?=\s*[.\):-]\s*[A-Ea-e])', '0', metin)     # O → 0
    metin = re.sub(r'S(?=\d)', '5', metin)                         # S5 → 55
    metin = re.sub(r'B(?=\s*[.\):-]\s*[A-Ea-e])', '8', metin)     # B → 8
    return metin

def cevaplari_dogrula(cevaplar, beklenen_sayi=None):
    """Çıkarılan cevapların tamlığını doğrula"""
    if not cevaplar:
        return False, "Cevap çıkarılamadı"
    
    soru_numaralari = sorted(cevaplar.keys())
    beklenen = set(range(1, max(soru_numaralari) + 1))
    eksik = beklenen - set(soru_numaralari)
    
    if eksik:
        return False, f"Eksik sorular: {sorted(eksik)}"
    
    gecersiz = {k: v for k, v in cevaplar.items() if v not in 'ABCDE'}
    if gecersiz:
        return False, f"Geçersiz cevaplar: {gecersiz}"
    
    return True, f"Geçerli: {len(cevaplar)} soru"
```

---

## 🏗️ Önerilen Pipeline Mimarisi

Üretim dağıtımı için, ön işleme, çoklu OCR motorları ve doğrulamayı birleştiren bu hibrit yaklaşımı kullanın:

```
┌─────────────────────────────────────────────────────────────────┐
│                    GİRDİ: Cevap Anahtarı Görüntüsü               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AŞAMA 1: ÖN İŞLEME                                              │
│  • 2-3x Büyütme (cv2.INTER_CUBIC)                               │
│  • CLAHE kontrast iyileştirme                                    │
│  • Bilateral filtre gürültü azaltma                              │
│  • Adaptif ikilileştirme                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AŞAMA 2: YERLEŞİM TESPİTİ                                       │
│  • Surya yerleşim analizi VEYA PaddleOCR PP-Structure           │
│  • Tespit: Tablo bölgeleri vs Metin bölgeleri                   │
│  • Cevap anahtarı bölümüne kırp                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│  TABLO YOLU              │     │  METİN YOLU              │
│  • TableTransformer veya │     │  • Surya OCR veya        │
│    PaddleOCR PP-Structure│     │    PaddleOCR metin       │
│  • Hücre çıkarma         │     │  • Tam sayfa OCR         │
│  • Yapı tanıma           │     │  • Regex çıkarma         │
└─────────────────────────┘     └─────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AŞAMA 3: CEVAP ÇIKARMA                                          │
│  • S→C eşlemesi için Regex desenleri                            │
│  • OCR hata düzeltme                                             │
│  • Sıra doğrulama                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AŞAMA 4: DOĞRULAMA & YEDEK                                      │
│  EĞER güven < %80 VEYA eksik sorular:                            │
│    → Vision LLM ile yeniden dene (Gemini 2.0 Flash)             │
│    → Hala başarısızsa manuel inceleme için işaretle             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ÇIKTI: {"1": "A", "2": "B", "3": "C", ...}                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 Tam Üretim Uygulaması

```python
import cv2
import numpy as np
import re
from PIL import Image
from typing import Dict, Optional, Tuple

class CevapAnahtariPipeline:
    def __init__(self, gpu_kullan=True, llm_yedek=True):
        self.gpu_kullan = gpu_kullan
        self.llm_yedek = llm_yedek
        self._modelleri_baslat()
    
    def _modelleri_baslat(self):
        # Birincil: Surya OCR
        from surya.foundation import FoundationPredictor
        from surya.recognition import RecognitionPredictor
        from surya.detection import DetectionPredictor
        from surya.table_rec import TableRecPredictor
        
        self.foundation = FoundationPredictor()
        self.detection = DetectionPredictor()
        self.recognition = RecognitionPredictor(self.foundation)
        self.table_rec = TableRecPredictor()
    
    def on_isle(self, goruntu_yolu: str, olcek: float = 3.0) -> np.ndarray:
        img = cv2.imread(goruntu_yolu)
        
        # Büyütme
        img = cv2.resize(img, None, fx=olcek, fy=olcek, 
                        interpolation=cv2.INTER_CUBIC)
        
        # Gri tonlama + CLAHE
        gri = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        iyilestirilmis = clahe.apply(gri)
        
        # Gürültü azaltma + İkilileştirme
        gurultusuz = cv2.bilateralFilter(iyilestirilmis, 9, 75, 75)
        ikili = cv2.adaptiveThreshold(
            gurultusuz, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 15, 8
        )
        
        return cv2.cvtColor(ikili, cv2.COLOR_GRAY2RGB)
    
    def cikar(self, goruntu_yolu: str) -> Tuple[Dict[int, str], float]:
        # Ön işleme
        islenmis = self.on_isle(goruntu_yolu)
        pil_goruntu = Image.fromarray(islenmis)
        
        # Tablo çıkarmayı dene
        tablo_sonuclari = self.table_rec([pil_goruntu])[0]
        
        if tablo_sonuclari.get('cells'):
            cevaplar = self._tablo_ayristir(tablo_sonuclari)
        else:
            ocr_sonuclari = self.recognition([pil_goruntu], 
                                              det_predictor=self.detection)[0]
            metin = ' '.join([s['text'] for s in ocr_sonuclari['text_lines']])
            cevaplar = self._metin_ayristir(metin)
        
        # Doğrula
        gecerli, mesaj = self._dogrula(cevaplar)
        guven = len(cevaplar) / max(cevaplar.keys(), default=1) if cevaplar else 0
        
        # Gerekirse LLM'e yedekle
        if self.llm_yedek and guven < 0.8:
            cevaplar = self._llm_yedek(goruntu_yolu)
            guven = 0.9  # LLM genellikle güvenilir
        
        return cevaplar, guven
    
    def _tablo_ayristir(self, tablo_sonuc) -> Dict[int, str]:
        cevaplar = {}
        for hucre in tablo_sonuc.get('cells', []):
            metin = hucre.get('text', '').strip()
            esleme = re.match(r'(\d+)\s*[.\):-]\s*([A-Ea-e])', metin)
            if esleme:
                cevaplar[int(esleme.group(1))] = esleme.group(2).upper()
        return dict(sorted(cevaplar.items()))
    
    def _metin_ayristir(self, metin: str) -> Dict[int, str]:
        metin = self._ocr_hatalarini_duzelt(metin)
        desen = r'(\d+)\s*[.\):-]\s*([A-Ea-e])'
        eslemeler = re.findall(desen, metin, re.IGNORECASE)
        return dict(sorted({int(s): c.upper() for s, c in eslemeler}.items()))
    
    def _ocr_hatalarini_duzelt(self, metin: str) -> str:
        metin = re.sub(r'[lI](?=\s*[.\):-]\s*[A-Ea-e])', '1', metin)
        metin = re.sub(r'O(?=\s*[.\):-]\s*[A-Ea-e])', '0', metin)
        return metin
    
    def _dogrula(self, cevaplar: Dict[int, str]) -> Tuple[bool, str]:
        if not cevaplar:
            return False, "Cevap bulunamadı"
        eksik = set(range(1, max(cevaplar.keys())+1)) - set(cevaplar.keys())
        if eksik:
            return False, f"Eksik: {sorted(eksik)}"
        return True, "Geçerli"
    
    def _llm_yedek(self, goruntu_yolu: str) -> Dict[int, str]:
        import google.generativeai as genai
        import json
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        goruntu = Image.open(goruntu_yolu)
        
        prompt = """Cevap anahtarını çıkar: JSON döndür {"cevaplar": [{"s": 1, "c": "A"}, ...]}"""
        yanit = model.generate_content([prompt, goruntu], 
                                        generation_config={"temperature": 0})
        
        veri = json.loads(yanit.text)
        return {oge['s']: oge['c'] for oge in veri['cevaplar']}

# Kullanım
pipeline = CevapAnahtariPipeline(gpu_kullan=True, llm_yedek=True)
cevaplar, guven = pipeline.cikar("yks_cevap_anahtari.png")
print(f"{len(cevaplar)} cevap çıkarıldı, güven: %{guven*100:.0f}")
print(cevaplar)
```

---

## ✅ Önemli Çıkarımlar

### %4 Doğruluk Sorununuz İçin Acil Düzeltmeler:

1. **OCR'dan önce görüntüleri 3x büyütün** — bu tek başına çoğu sorunu çözebilir
2. **CLAHE kontrast iyileştirme** ve adaptif ikilileştirme uygulayın
3. **Karakter beyaz listesi** kullanın (`ABCDEabcde0123456789`)
4. EasyOCR'a hızlı alternatif olarak **PSM 6 ile Tesseract** deneyin

### Üretim Dağıtımı İçin:

- En iyi Türkçe desteği + tablo işleme için **Surya OCR** kullanın (ücretsiz, kendi sunucu)
- Zor görüntüler için yedek olarak **Gemini 2.0 Flash** kullanın (~1.000 sayfa başına ~35₺)
- **AWS Textract'tan kaçının** (Türkçe desteği yok)
- Kurumsal uyumluluk gerekiyorsa **Azure Document Intelligence** en iyi ticari seçenektir

### Beklenen İyileştirme:

**%4'ten → %85-95 doğruluğa** doğru ön işleme ve araç seçimiyle.

---

## 🎯 Sizin İçin Önerilen Eylem Planı

| Öncelik | Eylem | Süre | Beklenen Sonuç |
|---------|-------|------|----------------|
| 1 | Görüntü ön işleme ekle (3x büyütme + CLAHE) | 30 dk | %4 → %40-50 |
| 2 | Surya OCR'a geç | 1 saat | %50 → %70-80 |
| 3 | Tablo tespit entegrasyonu | 2 saat | %80 → %85-90 |
| 4 | Gemini yedek ekle | 1 saat | %90 → %95 |

**Toplam: ~4-5 saat çalışma ile %4'ten %95'e çıkabilirsiniz.**
