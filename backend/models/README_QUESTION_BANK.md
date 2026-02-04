# Soru Bankası Sistemi - Task 70 Implementation

## Genel Bakış

Bu modül, Teknofest 2025 Eğitim Eylemci Platformu için gelişmiş soru bankası sistemini içerir. 10,000+ soru için optimize edilmiş, IRT (Item Response Theory) tabanlı adaptif test sistemi desteği sunar.

## Task 70: Soru Veritabanı Tasarımı

### ✅ 70.1 Soru Modeli
**Dosya:** `backend/models/question_bank.py` - `QuestionBankItem`

**Özellikler:**
- Gelişmiş soru şeması (metin, HTML, LaTeX, görsel, ses desteği)
- 5 seçenekli soru formatı (A-E)
- Alternatif çözüm yolları desteği
- Video açıklama URL'leri
- Türkçe morfoloji analizi (kelime sayısı, okunabilirlik skoru)
- Kapsamlı metadata (ÖSYM uyumu, kalite skoru, vb.)

**İlişkiler:**
- `primary_topic`: Ana konu (TopicHierarchy)
- `tag_associations`: Çoklu etiketler (QuestionTag)
- `calibration_history`: IRT kalibrasyon geçmişi
- `performance_analytics`: Performans analitiği

### ✅ 70.2 Konu Etiketleme
**Dosyalar:** 
- `TopicHierarchy` - Hiyerarşik konu taksonomisi
- `QuestionTag` - Soru etiketleri
- `QuestionTagAssociation` - Çoklu etiketleme

**Özellikler:**
- 5 seviyeli hiyerarşik yapı (Ana konu → Alt konu → Detay konu)
- Konu kodlama sistemi (örn: MAT.GEO.UCG.PIS)
- MEB müfredat uyumu (kazanım kodları)
- ÖSYM çıkma olasılığı ve frekans takibi
- Çoklu etiketleme desteği (skill, concept, difficulty, format)
- Etiket ağırlıklandırma

**Örnek Hiyerarşi:**
```
Matematik (MAT)
  └── Geometri (MAT.GEO)
      └── Üçgenler (MAT.GEO.UCG)
          └── Pisagor Teoremi (MAT.GEO.UCG.PIS)
```

### ✅ 70.3 Zorluk Seviyesi
**Enum:** `QuestionDifficultyLevel`

**5 Seviyeli Zorluk Ölçeği:**
1. `VERY_EASY` - Çok Kolay
2. `EASY` - Kolay
3. `MEDIUM` - Orta
4. `HARD` - Zor
5. `VERY_HARD` - Çok Zor

**IRT Bazlı Zorluk Hesaplama:**
```python
IRT Difficulty (b)  →  Zorluk Seviyesi
    < -1.5          →  very_easy
    -1.5 to -0.5    →  easy
    -0.5 to 0.5     →  medium
    0.5 to 1.5      →  hard
    > 1.5           →  very_hard
```

**Dinamik Güncelleme:**
- Minimum 100 deneme sonrası güncelleme
- 30 günde bir otomatik kontrol
- Başarı oranı bazlı ayarlama
- Güncelleme geçmişi takibi

### ✅ 70.4 IRT Parametreleri
**Model:** `IRTCalibrationHistory`

**4 Parametreli IRT Modeli (4PL):**

1. **a (discrimination)** - Ayırt Edicilik
   - Aralık: 0.1 - 3.0
   - Sorunun farklı yetenek seviyelerini ne kadar iyi ayırt ettiği
   - Yüksek değer = Daha ayırt edici soru

2. **b (difficulty)** - Zorluk
   - Aralık: -3.0 - +3.0
   - Sorunun zorluk seviyesi
   - 0 = Orta zorluk, pozitif = zor, negatif = kolay

3. **c (guessing)** - Tahmin
   - Aralık: 0.0 - 1.0
   - Şans eseri doğru cevaplama olasılığı
   - Varsayılan: 0.25 (4 seçenekli sorular için)

4. **d (upper asymptote)** - Üst Asimptot
   - Aralık: 0.0 - 1.0
   - Maksimum doğru cevaplama olasılığı
   - Varsayılan: 1.0

**Kalibrasyon Özellikleri:**
- Kalibrasyon yöntemleri: EM, MLE, Bayesian
- Minimum 30 öğrenci yanıtı gereksinimi
- Parametre güven aralıkları
- Convergence kalitesi takibi
- Tam kalibrasyon geçmişi

## Servis Katmanı

**Dosya:** `backend/services/question_bank_service.py`

### QuestionBankService Metodları

#### CRUD İşlemleri
- `create_question()` - Yeni soru oluştur
- `get_question()` - Soru detayı getir
- `update_question()` - Soru güncelle
- `delete_question()` - Soru sil (soft delete)

#### Konu Yönetimi
- `create_topic()` - Yeni konu oluştur
- `get_topic_hierarchy()` - Konu hiyerarşisi getir
- `get_topic_path()` - Konunun tam yolunu getir
- `add_question_tags()` - Soruya etiket ekle

#### Zorluk Yönetimi
- `update_question_difficulty()` - Dinamik zorluk güncelle
- `batch_update_difficulties()` - Toplu zorluk güncelleme

#### IRT Kalibrasyon
- `calibrate_question_irt()` - IRT parametrelerini kalibre et
- `get_calibration_history()` - Kalibrasyon geçmişi
- `get_questions_needing_calibration()` - Kalibrasyon gereken sorular

#### Arama ve Filtreleme
- `search_questions()` - Gelişmiş soru arama
- `get_question_statistics()` - Soru istatistikleri
- `get_topic_statistics()` - Konu istatistikleri

## Veritabanı Şeması

**Migration:** `backend/migrations/add_question_bank_tables.sql`

### Tablolar

1. **topic_hierarchy** - Konu hiyerarşisi
2. **question_tags** - Soru etiketleri
3. **question_bank** - Ana soru tablosu
4. **question_tag_associations** - Soru-etiket ilişkileri
5. **irt_calibration_history** - IRT kalibrasyon geçmişi
6. **question_performance_analytics** - Performans analitiği

### İndeksler

**Performans Optimizasyonu:**
- Tek sütun indeksleri (topic, difficulty, exam_type, vb.)
- Composite indeksler (adaptif test seçimi için)
- Unique constraint'ler (veri bütünlüğü için)

**Örnek Composite İndeks:**
```sql
CREATE INDEX idx_qbank_exam_subject_difficulty 
ON question_bank(exam_type, subject_area, irt_difficulty);
```

## Kullanım Örnekleri

### 1. Yeni Soru Oluşturma

```python
from backend.services.question_bank_service import QuestionBankService

service = QuestionBankService(db)

question = await service.create_question({
    "question_text": "Bir üçgenin iç açıları toplamı kaç derecedir?",
    "option_a": "90°",
    "option_b": "180°",
    "option_c": "270°",
    "option_d": "360°",
    "correct_answer": "B",
    "exam_type": "TYT",
    "subject_area": "matematik",
    "grade_level": 9,
    "primary_topic_id": "topic-mat-geo-ucg",
    "difficulty_level": QuestionDifficultyLevel.EASY,
    "irt_difficulty": -0.8,
    "irt_discrimination": 1.2,
})
```

### 2. Konu Hiyerarşisi Oluşturma

```python
# Ana konu
matematik = await service.create_topic(
    code="MAT",
    name_tr="Matematik",
    level=1,
    osym_relevance=1.0
)

# Alt konu
geometri = await service.create_topic(
    code="MAT.GEO",
    name_tr="Geometri",
    level=2,
    parent_id=matematik.id,
    osym_relevance=0.95
)

# Detay konu
ucgenler = await service.create_topic(
    code="MAT.GEO.UCG",
    name_tr="Üçgenler",
    level=3,
    parent_id=geometri.id,
    osym_relevance=0.92
)
```

### 3. Soru Etiketleme

```python
await service.add_question_tags(
    question_id="question-123",
    tag_names=["problem_solving", "visual", "theorem"]
)
```

### 4. IRT Kalibrasyon

```python
calibration = await service.calibrate_question_irt(
    question_id="question-123",
    new_discrimination=1.5,
    new_difficulty=0.3,
    new_guessing=0.22,
    new_upper_asymptote=0.98,
    calibration_method="EM",
    sample_size=250,
    standard_error=0.05,
    convergence_iterations=15
)
```

### 5. Dinamik Zorluk Güncelleme

```python
# Tek soru güncelleme
updated_question = await service.update_question_difficulty(
    question_id="question-123",
    force=False
)

# Toplu güncelleme
updated_count = await service.batch_update_difficulties(
    min_attempts=100
)
print(f"{updated_count} soru güncellendi")
```

### 6. Gelişmiş Soru Arama

```python
questions = await service.search_questions(
    exam_type="TYT",
    subject_area="matematik",
    topic_id="topic-mat-geo-ucg",
    difficulty_level=QuestionDifficultyLevel.MEDIUM,
    min_quality_score=70.0,
    is_calibrated=True,
    limit=20
)
```

## Test Dosyası

**Dosya:** `backend/tests/test_question_bank.py`

### Test Kategorileri

1. **TestIRTDifficultyCalculation** - IRT zorluk hesaplama
2. **TestQuestionBankModel** - Soru model testleri
3. **TestTopicHierarchy** - Konu hiyerarşisi testleri
4. **TestIRTCalibration** - IRT kalibrasyon testleri
5. **TestDifficultyUpdate** - Zorluk güncelleme testleri

### Testleri Çalıştırma

```bash
pytest backend/tests/test_question_bank.py -v
```

## Performans Optimizasyonları

### 1. İndeksleme Stratejisi
- Composite indeksler adaptif test seçimi için
- Partial indeksler (is_active=true) için
- Covering indeksler sık kullanılan sorgular için

### 2. Query Optimizasyonu
- Eager loading (joinedload) N+1 problemini önler
- Batch operations toplu işlemler için
- Pagination büyük sonuç setleri için

### 3. Caching Stratejisi
- Topic hierarchy cache (nadiren değişir)
- Question metadata cache
- IRT parameter cache

## Güvenlik ve Validasyon

### Database Constraints
- CHECK constraints parametre aralıkları için
- UNIQUE constraints veri bütünlüğü için
- FOREIGN KEY constraints referential integrity için

### Application Level Validation
- Pydantic models input validation için
- Custom validators business logic için
- Permission checks CRUD operations için

## Gelecek Geliştirmeler

1. **Soru Benzerlik Analizi** (Task 75)
   - Question embeddings
   - Semantic similarity
   - Benzer soru önerisi

2. **Video Çözüm Sistemi** (Task 72)
   - Video upload
   - Video streaming
   - Transcript arama

3. **Alternatif Çözüm Yolları** (Task 73)
   - Çoklu çözüm desteği
   - Çözüm karşılaştırma
   - En hızlı çözüm önerisi

## Katkıda Bulunma

Bu modül Task 70'in tamamlanmış implementasyonudur. Yeni özellikler eklerken:

1. Model değişiklikleri için migration oluşturun
2. Servis metodları için unit test yazın
3. API endpoint'leri için integration test ekleyin
4. README'yi güncelleyin

## Lisans

Teknofest 2025 Eğitim Eylemci Platformu
