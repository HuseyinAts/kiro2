# Türk Üniversite Sınavlarına Hazırlık İçin Uçtan Uca Eğitim Yapay Zekası Geliştirme Raporu

## 📋 YÖNETİCİ ÖZETİ

Türk üniversite giriş sınavları (YKS/TYT/AYT) artık soruların fotoğrafını çekip anında çözüm sunan bir yapay zeka pipeline'ı ile fethedilmeye hazır. Optimal mimari şunları birleştiriyor: **YOLO tabanlı layout tespiti**, **Surya veya Qwen2.5-VL ile OCR/anlama**, ve **DeepSeekMath veya ToRA ile çözüm üretimi**—doküman çıkarmada %90'ın üzerinde, matematik problem çözmede ise %85+ doğruluk elde ediliyor. Bu rapor, 426 kitaplık veri setinizi işlemek için 2023-2025 dönemindeki doküman yapay zekası, eğitim sistemleri ve üretim en iyi uygulamalarındaki gelişmeleri sentezliyor.

---

## 1. DOKÜMAN ÇIKARMA ARTIK GELENEKSEL OCR YERİNE GÖRÜŞ-DİL MODELLERİNİ TERCİH EDİYOR

Doküman anlama manzarası 2023'ten bu yana dramatik şekilde değişti. Geleneksel OCR pipeline'ları (Tesseract → layout analizi → son işleme) yerini, doküman yapısını örtük olarak anlayan uçtan uca görüş-dil modellerine bırakıyor.

### 1.1 Doküman Çıkarma Araçlarının Yeni Hiyerarşisi

| Araç | Doğruluk | Hız | Türkçe Desteği | En İyi Kullanım Alanı |
|------|----------|-----|----------------|----------------------|
| **Surya OCR** | %97.7 | Orta | Doğal (90+ dil) | Karmaşık layoutlar, matematik |
| **Qwen2.5-VL** | %95+ DocVQA | Orta | Açık destek | Anlama + çıkarma |
| **PaddleOCR v4** | %96.6 | Hızlı | Latin modeli | Yüksek hacimli üretim |
| **GPT-4o/Claude Vision** | %92-95 | Yavaş | Tam | Karmaşık muhakeme |
| **Tesseract 5.x** | %87.7 | Hızlı | Doğal | Basit basılı metin |

### 1.2 Surya OCR - En İyi Açık Kaynak Seçenek

**Surya** (github.com/VikParuchuri/surya) en iyi açık kaynak seçenek olarak öne çıkıyor. Sunduğu özellikler:
- OCR (Optik Karakter Tanıma)
- Layout analizi
- Okuma sırası tespiti
- Tablo tanıma
- Yerleşik matematik desteği

Saf çıkarmanın ötesinde semantik anlama için **Qwen2.5-VL**, DocVQA benchmark'larında GPT-4o'yu geride bırakırken yerel olarak **7B parametreli** bir modelde çalışabiliyor.

### 1.3 YOLO Etiketli Veri Setiniz İçin Kritik İçgörü

**Hibrit yaklaşımlar kazanıyor!** Mevcut YOLO etiketlerinizi (sorular, cevaplar, çözümler, konular, zorluk seviyeleri) bölge tespiti için kullanın, sonra her bölgeyi özelleşmiş işlemcilere yönlendirin:
- Metin için Surya
- Formüller için Pix2Text
- Cevap tabloları için Table Transformer

---

## 2. YOLO TESPİTİ + ÖZELLEŞMİŞ İŞLEMCİLER, SAF UÇTAN UCA MODELLERDEN DAHA İYİ PERFORMANS GÖSTERİYOR

Mevcut YOLO anotasyonlarınız önemli bir değer temsil ediyor. **DocLayout-YOLO** (arXiv:2410.12628) ve DocLayNet üzerinde eğitilmiş **YOLOv11/v12**, doküman elemanı tespitinde **mAP50-95 0.79+** elde ediyor—yapılandırılmış dokümanlarda uçtan uca yaklaşımları yakalıyor veya aşıyor.

### 2.1 Önerilen Pipeline Mimarisi

```
Girdi (PDF/Görüntü)
       ↓
DocLayout-YOLO veya Özel YOLO Modeliniz
       ↓
Bölge Sınıflandırma & Yönlendirme
       ├── Metin bölgeleri → Surya OCR
       ├── Formül bölgeleri → Pix2Text (github.com/breezedeus/Pix2Text)
       ├── Tablo bölgeleri → Table Transformer + OCR
       └── Diyagram bölgeleri → Qwen2.5-VL açıklaması
       ↓
Yapılandırılmış JSON Çıktısı (soru, seçenekler, cevap, metadata)
```

### 2.2 Bu Yaklaşım Neden Saf VLM Yaklaşımlarını Yeniyor?

GPT-4V gibi görüş-dil modelleri, özellikle Türkçe metin içeren yoğun dokümanlarda halüsinasyon yapabiliyor. YOLO tespitiniz kesin sınırlar sağlayarak mekansal belirsizliği ortadan kaldırıyor. Yönlendirme yaklaşımı ayrıca özelleşmiş işlemeyi mümkün kılıyor:
- **Pix2Text** LaTeX formül tanımayı **%95+ doğrulukla** hallediyor
- Genel VLM'ler matematiksel notasyonla zorlanıyor

### 2.3 Tablo Çıkarma İçin Table Transformer

Özellikle tablo çıkarma için **Table Transformer** (github.com/microsoft/table-transformer) şu sonuçları elde ediyor:
- Basit tablolarda **%98.5 TEDS**
- Karmaşık tablolarda **%95**

Bu, Türk sınav kitaplarında yaygın olan "1.A 2.B 3.C" grid formatındaki cevap anahtarlarını ayrıştırmak için kritik öneme sahip.

---

## 3. SORU-CEVAP EŞLEŞTİRME MEKANSAL ANALİZ VE DESEN EŞLEŞTİRME GEREKTİRİYOR

Türk sınav kitaplarındaki cevap konumları iki kategoriye ayrılıyor:
1. **Satır içi (sayfa altı)** 
2. **Ayrı bölüm (kitap sonu)**

Her biri farklı çıkarma stratejileri gerektiriyor.

### 3.1 Satır İçi Cevaplar (Sayfa Altı) İçin Python Kodu

```python
def extract_inline_answers(page, threshold_y=0.8):
    """Sayfa altındaki cevapları çıkarır"""
    answer_zone = page.height * threshold_y
    bottom_text = [elem for elem in page.chars if elem['top'] > answer_zone]
    # Desen: "1.A 2.B 3.C 4.D 5.E"
    answers = re.findall(r'(\d+)\s*[\.:\-]\s*([A-E])', extract_text(bottom_text))
    return dict(answers)
```

### 3.2 Ayrı Cevap Bölümü İçin Python Kodu

```python
CEVAP_ISARETLERI = ['CEVAP ANAHTARI', 'ÇÖZÜMLER', 'CEVAPLAR', 'ANSWER KEY']

def find_answer_section(document):
    """Kitap sonundaki cevap bölümünü bulur"""
    for page_num, page in enumerate(document.pages):
        if any(marker in page.extract_text().upper() for marker in CEVAP_ISARETLERI):
            return page_num
    return None
```

### 3.3 Türkçe İçin Semantik Eşleştirme

Desen eşleştirme başarısız olduğunda semantik eşleştirme için **Türkçe'ye özel gömme modelleri** çokdilli alternatiflerden önemli ölçüde daha iyi performans gösteriyor.

**Önerilen model:** `emrecan/bert-base-turkish-cased-mean-nli-stsb-tr`
- Türkçe semantik benzerlikte **Pearson 0.845** elde ediyor
- Türkçe metin üzerinde multilingual-MiniLM'den **%20 daha iyi**

### 3.4 Al-ve-Yeniden-Sırala Deseni

Optimal eşleştirme için şu desen önerilir:

1. **Bi-encoder** ile hızlı aday çıkarma (top-100, O(n) karmaşıklık)
2. **Cross-encoder** ile doğru yeniden sıralama (top-20, O(n×m) karmaşıklık)  
3. **Desen doğrulama** ile soru numarası hizalamasını onaylama

---

## 4. LLM'LERLE MATEMATİK PROBLEM ÇÖZME ARTIK İLKOKUL PROBLEMLERİNDE %95'İ AŞIYOR

Özelleşmiş modellerin matematik muhakeme yetenekleri dramatik şekilde ilerledi. **DeepSeekMath-7B** şu sonuçları elde ediyor:
- **GSM8K'da %88.2** (ilkokul matematik)
- **MATH'ta %51.7** (yarışma seviyesi)

Bu, açık kaynak 7B model için dikkat çekici bir performans. Araç entegrasyonu (Python yürütücü) ile doğruluk MATH'ta **%60+'a** çıkıyor.

### 4.1 Türk Sınav Hazırlığı İçin Temel Modeller

| Model | GSM8K | MATH | Mimari | Lisans |
|-------|-------|------|--------|--------|
| **GPT-4 + Code Interpreter** | %97 | %69.7 | Tescilli | Ticari |
| **DeepSeekMath-7B-RL** | %88.2 | %51.7 | Açık | Apache 2.0 |
| **ToRA-Code-34B** | %90+ | %50+ | Araç entegreli | MIT |
| **Qwen2.5-Math-72B** | %95+ | %70+ | Açık | Apache 2.0 |
| **WizardMath-70B** | %81.6 | %22.7 | Llama tabanlı | Llama lisansı |

### 4.2 Düşünce Zinciri vs Program Düşüncesi

Adım adım çözümler için **her iki yaklaşımı birleştirin**. 

**ToRA** (github.com/microsoft/ToRA), doğal dil muhakemesini Python kod yürütmesiyle iç içe geçiriyor—insanların takip edebileceği açıklamalar üretirken hesaplama doğruluğunu garanti ediyor. Bu tam olarak Türk öğrencilerin ihtiyacı olan şey: sadece "C" cevabı değil, muhakeme yolu.

### 4.3 Görsel Matematik Problemleri

Görsel matematik problemleri (geometri, grafikler) için **MathVista benchmark** sonuçları:
- Güncel SOTA: **%73.9** (OpenAI o1)
- İnsan performansı: **%60.3**

**GeoX** ve **Geo-LLaVA** özellikle geometriyi hedefliyor:
- **GeoQA'da %65.25** elde ediyorlar
- Türk müfredatındaki düzlem ve katı geometriyi kapsıyorlar

---

## 5. TİCARİ EĞİTİM YAPAY ZEKASI KANITLANMIŞ MİMARİ DESENLERİ ORTAYA KOYUYOR

Photomath, Mathpix ve Khanmigo'yu incelemek üretimde test edilmiş desenleri ortaya koyuyor:

### 5.1 Photomath (Google tarafından satın alındı, Şubat 2024)

- Microblink'ten özel OCR, el yazısı + basılı denklemleri hallediyor
- Bilgisayar Cebir Sistemi çıkarılan ifadeleri çözüyor
- **300M+ kullanıcı, 2.2B problem/ay** modelin işe yaradığını kanıtlıyor
- **Sınırlama:** Öncelikle denklem odaklı, sınırlı sözel problem yorumlama

### 5.2 Mathpix API - STEM OCR İçin Endüstri Benchmark'ı

- Günde **10M+ görüntü** işliyor, %99.9+ çalışma süresiyle
- Formüller için LaTeX, MathML, Markdown çıktısı veriyor
- El yazısı matematik, tablolar, kimya yapılarını destekliyor
- Mathway, Doubtnut, Toppr, Gradescope tarafından kullanılıyor

### 5.3 Khanmigo (Khan Academy) - Özel Ders Mimarisi

- Sokratik yönlendirmeli GPT-4 Omni tabanı (cevap vermek yerine yönlendiriyor)
- LLM aritmetik hatalarını atlamak için yerleşik hesap makinesi
- Karmaşık problemler için bağlam sağlayan insan üretimi ipuçları
- 2024-25 öğretim yılında **700,000+ kullanıcı**

### 5.4 Ortaya Çıkan Desen

**Girdi için OCR/VLM → Hesaplama için Özelleşmiş Çözücü → Açıklama üretimi için LLM**

Tek bir modelin her şeyi iyi yapmasını beklemeyin!

---

## 6. TÜRKÇE DİL İŞLEME ÖZELLEŞMİŞ DİKKAT GEREKTİRİYOR

Türkçe'nin sondan eklemeli morfolojisi benzersiz zorluklar yaratıyor. "anlayabildiklerimizden" gibi tek bir Türkçe kelime, standart tokenizer'ların eşdeğer İngilizce içerikten **2.5 kat daha fazla alt kelimeye** böldüğü 5+ morfem içeriyor—bu da model performansını düşürüyor.

### 6.1 Temel Türkçe NLP Kaynakları

| Kaynak | Link | Amaç |
|--------|------|------|
| **BERTurk** | huggingface.co/dbmdz/bert-base-turkish-cased | En iyi Türkçe anlama |
| **Turkcell-LLM-7b** | huggingface.co/TURKCELL/Turkcell-LLM-7b-v1 | Doğal Türkçe LLM |
| **Zemberek** | github.com/ahmetaa/zemberek-nlp | Morfolojik analiz |
| **TQuAD** | github.com/TQuad/turkish-nlp-qa-dataset | Türkçe S-C veri seti |
| **TR-MMLU** | - | Türkçe LLM benchmark'ı (6,200 soru) |

### 6.2 Türkçe OCR Dikkat Edilecek Noktalar

- Özel karakterler (ş, ğ, ü, ö, ı, ç, İ) doğrulama gerektirir
- Noktasız ı / noktalı İ ayrımı kritiktir ve sık karıştırılır
- Google Cloud Vision ve Surya Türkçe'yi doğal olarak destekliyor
- OCR hata düzeltmesi için Zemberek yazım denetleyicisi ile son işleme yapın

### 6.3 Anahtar Bulgu

Tek dilli Türkçe modeller (BERTurk), Türkçe'ye özgü görevlerde çokdilli alternatiflerden (mBERT, XLM-R) tutarlı olarak **%10-15 daha iyi** performans gösteriyor.

**Önerimiz:** Sınav hazırlık sisteminiz için, sıfır atışlı çokdilli transfere güvenmek yerine Türkçe eğitim içeriği üzerinde ince ayar yapın.

---

## 7. YKS SINAV YAPISI ÇÖZÜM MİMARİSİNİ ŞEKİLLENDİRİYOR

Doğru sistemi oluşturmak için sınav formatını anlamak esastır:

### 7.1 YKS Sınav Yapısı

| Oturum | Soru Sayısı | Süre | İçerik | Puan Ağırlığı |
|--------|-------------|------|--------|---------------|
| **TYT** | 120 | 165 dk | Türkçe, Sosyal Bilimler, Temel Matematik, Fen | %40 |
| **AYT** | 160 | 180 dk | Edebiyat, Sosyal Bilimler, İleri Matematik, Fen | %60 |

### 7.2 İstatistikler ve Fırsatlar

- Yıllık **1.6 milyondan fazla öğrenci** YKS'ye giriyor
- Sorular 5 seçenekli (A-E) çoktan seçmeli
- 2023 AYT matematik bölümü ortalaması sadece **40 üzerinden 7.6 doğru**
- Bu önemli zorluk ve yapay zeka destekli hazırlık için büyük fırsat demek

### 7.3 426 Kitaplık Veri Setinizin Gereksinimleri

25+ yayınevinden 426 kitaplık veri setiniz pazar çeşitliliğini temsil ediyor. Çözüm şunları halletmeli:
- Değişken cevap konumları (satır içi vs. kitap sonu)
- Farklı yayınevi layoutları ve formatlama kuralları
- Karma içerik: Türkçe metin, matematiksel formüller, diyagramlar
- Tek kitaplarda birden fazla test bölümü

---

## 8. 426 KİTAP İÇİN ÜRETİM PIPELINE'I TOPLU OPTİMİZASYON GEREKTİRİYOR

426 kitabı (~128,000 sayfa) verimli işlemek dikkatli mimari gerektirir:

### 8.1 Önerilen Toplu İşleme Pipeline'ı

```
S3 Bucket (PDF'ler) → Doküman Sınıflandırıcı → İşleme Kuyruğu
                                                    ↓
                      ┌─────────────────────────────┼─────────────────────────────┐
                      ↓                             ↓                             ↓
               Dijital PDF'ler              Taranmış/Karmaşık              Cevap Bölümleri
               (Marker çıkarma)             (VLM işleme)                   (Table Transformer)
                      ↓                             ↓                             ↓
                      └─────────────────────────────┼─────────────────────────────┘
                                                    ↓
                                Kalite Güvence (Güven < 0.8 → İnsan İncelemesi)
                                                    ↓
                                PostgreSQL (Yapılandırılmış) + Qdrant (Gömmeler)
```

### 8.2 İşleme Tahminleri

- **Marker** A6000 üzerinde (12 paralel): ~122 sayfa/saniye → tam veri seti **15 saatte**
- 4× GPU ölçeklendirme ile: **3-4 saatte** tam çıkarma
- İnsan inceleme kuyruğu (düşük güvenli %10): İş gücüne bağlı değişken

### 8.3 Kalite Güvence Eşikleri

| Durum | Aksiyon |
|-------|---------|
| OCR güveni < 0.8 | İnsan incelemesine yönlendir |
| Soru numarası uyumsuzluğu | Doğrulama için işaretle |
| Cevap format ihlalleri | Otomatik red |

### 8.4 Pipeline İçin Açık Kaynak Araçlar

| Araç | GitHub | Özellik |
|------|--------|---------|
| **Marker** | github.com/VikParuchuri/marker | Nougat'tan 10× hızlı, düşük halüsinasyon |
| **Unstructured.io** | github.com/Unstructured-IO/unstructured | 20+ format desteği |
| **DocTR** | github.com/mindee/doctr | Çoklu mimari ile 2 aşamalı OCR |
| **MinerU** | github.com/opendatalab/MinerU | LLM iş akışları için PDF'den Markdown'a |

---

## 9. AKADEMİK MAKALELER TEKNİK YAKLAŞIMI BİLGİLENDİRİYOR

Son araştırmalar (2023-2025) teorik temel sağlıyor:

### 9.1 Doküman Anlama Makaleleri

| Makale | Konferans/Yıl | Sonuç | Notlar |
|--------|---------------|-------|--------|
| **LayoutLMv3** | ACM MM 2022 | %83.37 DocVQA | Birleşik metin-görüntü maskeleme, ticari olmayan lisans |
| **Pix2Struct** | ICML 2023 | %72.1 DocVQA | Ekran görüntüsü ayrıştırma ön eğitimi |
| **Nougat** | Meta, 2023 | - | LaTeX korumalı Bilimsel PDF'den Markdown'a |
| **DocLayout-YOLO** | arXiv 2024 | mAP 0.79+ | DocSynth300K ön eğitimli doküman spesifik YOLO |

### 9.2 Matematik Muhakeme Makaleleri

| Makale | Konferans/Yıl | Sonuç | Notlar |
|--------|---------------|-------|--------|
| **MathVista** | ICLR 2024 Oral | GPT-4V %49.9 | 6,141 görsel matematik örneği |
| **DeepSeekMath** | arXiv 2024 | MATH %51.7 | GRPO algoritması, araçsız |
| **ToRA** | ICLR 2024 | MATH %50+ | İlk açık kaynak %50+ MATH, araç entegreli muhakeme ajanı |
| **AlphaGeometry** | Nature 2024 | IMO seviyesi | Nöral-sembolik muhakeme ile geometri |

### 9.3 Akıllı Özel Ders Sistemleri Makaleleri

| Makale/Kaynak | Yıl | Bulgu |
|---------------|-----|-------|
| **ITS Survey** | arXiv 2025 | 2010-2025 kapsamlı inceleme, %20 öğrenci iyileştirmesi |
| **SocraticLM** | - | Pedagojik uyum için 35K matematik özel ders diyaloğu |
| **PRM800K** | OpenAI | Süreç denetimi, sonuç denetimini önemli ölçüde aşıyor |

---

## 10. ÖNERİLEN UYGULAMA YOL HARİTASI

### Faz 1 (Hafta 1-4): Doküman Çıkarma Pipeline'ı

**Hedefler:**
- DocLayout-YOLO dağıtın veya mevcut YOLO etiketlerinizi ince ayarlayın
- Türkçe metin OCR'ı için Surya entegre edin
- Formül bölgeleri için Pix2Text ekleyin
- Cevap tabloları için Table Transformer uygulayın

**Çıktılar:**
- Çalışan bölge tespit sistemi
- %95+ OCR doğruluğu
- Formül tanıma kapasitesi
- Tablo çıkarma yeteneği

### Faz 2 (Hafta 5-8): Soru-Cevap Eşleştirme

**Hedefler:**
- Türk sınav formatları için desen eşleştirme oluşturun (regex kütüphanesi)
- Satır içi cevaplar için mekansal analiz uygulayın
- Semantik eşleştirme için Türkçe gömme modeli dağıtın
- S-C çifti doğrulaması için doğrulama pipeline'ı oluşturun

**Çıktılar:**
- %98+ soru-cevap eşleştirme doğruluğu
- Otomatik cevap anahtarı çıkarma
- Semantik yedek sistem

### Faz 3 (Hafta 9-12): Çözüm Üretimi

**Hedefler:**
- Problem çözme için DeepSeekMath-7B veya Qwen2.5-Math dağıtın
- Python yürütücülü ToRA tarzı araç entegrasyonu uygulayın
- Türkçe YKS/TYT/AYT geçmiş sınav kağıtları üzerinde ince ayar yapın
- Adım adım açıklamalar için Sokratik yönlendirme katmanı ekleyin

**Çıktılar:**
- %85+ matematik problem çözme doğruluğu
- Türkçe açıklama üretimi
- Kod yürütme entegrasyonu

### Faz 4 (Hafta 13-16): Üretim Sağlamlaştırma

**Hedefler:**
- 426 kitap için toplu işlemeyi ölçeklendirin
- Düşük güvenli çıkarmalar için döngüde-insan sistemi uygulayın
- Fotoğraf girdili öğrenci yüzlü API oluşturun
- Kalite izleme ve geri bildirim döngüleri dağıtın

**Çıktılar:**
- Tam veri seti işleme
- Üretim hazır API
- Kalite güvence sistemi
- İzleme dashboard'ı

---

## 11. TEMEL GITHUB DEPOLARI

### 11.1 OCR ve Doküman İşleme

| Depo | Link | Açıklama |
|------|------|----------|
| **Surya OCR** | github.com/VikParuchuri/surya | Çok dilli OCR, layout analizi, tablo tanıma |
| **DocLayout-YOLO** | github.com/opendatalab/DocLayout-YOLO | Doküman spesifik YOLO |
| **Marker** | github.com/VikParuchuri/marker | Hızlı PDF→Markdown dönüştürücü |
| **Pix2Text** | github.com/breezedeus/Pix2Text | Formül ve metin tanıma |
| **Table Transformer** | github.com/microsoft/table-transformer | Tablo yapı tanıma |

### 11.2 Matematik Çözme

| Depo | Link | Açıklama |
|------|------|----------|
| **DeepSeekMath** | github.com/deepseek-ai/DeepSeek-Math | Matematik muhakeme modeli |
| **ToRA** | github.com/microsoft/ToRA | Araç entegreli muhakeme ajanı |
| **MathVista** | github.com/lupantech/MathVista | Görsel matematik benchmark'ı |

### 11.3 Türkçe NLP

| Depo | Link | Açıklama |
|------|------|----------|
| **Zemberek** | github.com/ahmetaa/zemberek-nlp | Türkçe morfolojik analiz |
| **BERTurk** | huggingface.co/dbmdz/bert-base-turkish-cased | Türkçe BERT modeli |
| **TQuAD** | github.com/TQuad/turkish-nlp-qa-dataset | Türkçe soru-cevap veri seti |

---

## 12. SONUÇ VE ÖNERİLER

Türk üniversite sınav hazırlığı için eğitim yapay zekası oluşturmak artık **açık kaynak araçların ticari alternatifleri yakaladığı veya aştığı** bir dönemde teknik olarak mümkün. Optimal mimari şunları birleştiriyor:

### 12.1 Önerilen Mimari Bileşenleri

1. **YOLO tabanlı layout tespiti** - mevcut etiketlerinizi kullanarak
2. **Surya/Qwen2.5-VL** - çok dilli OCR ve doküman anlama için
3. **Desen eşleştirme + semantik gömmeler** - soru-cevap korelasyonu için
4. **DeepSeekMath/ToRA** - araç entegrasyonlu matematiksel muhakeme için
5. **Türkçe'ye özgü ince ayar** - BERTurk ve eğitim veri setleri üzerinde

### 12.2 Kritik İçgörü

**Modüler pipeline'lar, üretim eğitim sistemleri için monolitik modelleri aşıyor.** 

Her doküman bölgesini özelleşmiş işlemcilere yönlendirin, güven puanlaması ile doğrulayın ve sınır durumları için insan gözetimini koruyun.

### 12.3 Beklenen Sonuçlar

Bu mimari ile 426 kitaplık veri setiniz milyonlarca Türk öğrenciye hizmet eden kapsamlı bir soru bankasına dönüşebilir—yapay zeka destekli anında çözümler ve açıklamalarla sınav hazırlığını dönüştürebilir.

### 12.4 Başarı Metrikleri

| Metrik | Hedef |
|--------|-------|
| Doküman çıkarma doğruluğu | %95+ |
| Soru-cevap eşleştirme | %98+ |
| Matematik problem çözme | %85+ |
| Türkçe açıklama kalitesi | %90+ kullanıcı memnuniyeti |
| Toplam işleme süresi | 426 kitap < 24 saat |

---

## 13. KAYNAKLAR VE REFERANSLAR

### 13.1 Akademik Makaleler

1. LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking (ACM MM 2022)
2. Pix2Struct: Screenshot Parsing as Pretraining (ICML 2023)
3. Nougat: Neural Optical Understanding for Academic Documents (Meta, 2023)
4. MathVista: Evaluating Mathematical Reasoning in Visual Contexts (ICLR 2024)
5. DeepSeekMath: Pushing the Limits of Mathematical Reasoning (arXiv 2024)
6. ToRA: A Tool-Integrated Reasoning Agent (ICLR 2024)
7. AlphaGeometry: Solving Olympiad Geometry without Human Demonstrations (Nature 2024)
8. DocLayout-YOLO: Enhancing Document Layout Analysis (arXiv 2024)

### 13.2 Web Kaynakları

- Medium: From OCR Pipelines to VQA - Rethinking Document Digitalization
- Roboflow: Top Multimodal Models Guide
- Researchify: Comparing PyTesseract, PaddleOCR, and Surya OCR
- Joshua Berkowitz: PDF Data Extraction - OCR Pipelines vs VLMs

### 13.3 Benchmark'lar ve Veri Setleri

- DocVQA: Document Visual Question Answering
- MathVista: Visual Mathematical Reasoning
- GSM8K: Grade School Math
- MATH: Competition Mathematics
- GeoQA: Geometry Question Answering
- TQuAD: Turkish Question Answering Dataset
- TR-MMLU: Turkish Massive Multitask Language Understanding

---

**Rapor Tarihi:** Ocak 2025
**Hazırlayan:** Claude AI Araştırma Asistanı
**Proje:** KIRO2 - Türk Üniversite Sınav Hazırlık Platformu
