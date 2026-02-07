# Requirements Document - AI Agent Yanıt Doğrulama Sistemi

## Introduction

Bu spec, AI agent'ların (LearningPathAgent, StudyBuddyAgent, ExamAgent) ürettiği yanıtların doğruluğunu ve tutarlılığını garanti eden verification sistemi için gereksinimleri tanımlar. Boris Cherny'nin verification feedback loops prensibi uygulanarak AI yanıt kalitesi %200-300 artırılacaktır.

## Glossary

- **LearningPathAgent**: Öğrenme yolu oluşturan AI agent
- **StudyBuddyAgent**: Öğrenci sohbet asistanı AI agent
- **ExamAgent**: Sınav ve değerlendirme yapan AI agent
- **Fact-Checking**: Bilgi doğruluğu kontrolü
- **RAG**: Retrieval-Augmented Generation - Bağlamsal AI yanıt sistemi
- **Confidence Score**: AI yanıtının güven skoru (0-1 arası)
- **Stop Hook**: AI yanıt tamamlandığında tetiklenen hook
- **Consistency Check**: Önceki yanıtlarla tutarlılık kontrolü

## Requirements

### Requirement 1: LearningPathAgent Yanıt Doğrulama

**User Story:** As a öğrenci, I want LearningPathAgent'ın önerdiği öğrenme yolunun doğru ve etkili olduğunu bilmek, so that zamanımı boşa harcamayayım.

#### Acceptance Criteria

1. **REQ-1.1** WHEN LearningPathAgent bir öğrenme yolu önerdiğinde, THE Validator SHALL önerilen konuların MEB müfredatında olduğunu doğrular
2. **REQ-1.2** WHEN konu sıralaması kontrol edildiğinde, THE Validator SHALL ön koşul ilişkilerinin doğru olduğunu kontrol eder
3. **REQ-1.3** WHEN zorluk seviyesi kontrol edildiğinde, THE Validator SHALL öğrenci seviyesine uygun olduğunu doğrular
4. **REQ-1.4** WHEN tahmini süre kontrol edildiğinde, THE Validator SHALL gerçekçi zaman tahminleri yapıldığını doğrular
5. **REQ-1.5** WHEN kaynak önerileri kontrol edildiğinde, THE Validator SHALL önerilen kaynakların erişilebilir olduğunu doğrular
6. **REQ-1.6** IF öğrenme yolu tutarsızlık içeriyorsa, THEN THE Validator SHALL düzeltme önerileri sunar

---

### Requirement 2: StudyBuddyAgent Yanıt Doğrulama

**User Story:** As a öğrenci, I want StudyBuddyAgent'ın verdiği cevapların doğru olduğunu bilmek, so that yanlış bilgi öğrenmeyeyim.

#### Acceptance Criteria

1. **REQ-2.1** WHEN StudyBuddyAgent bir soru cevapladığında, THE Validator SHALL cevabın konuyla ilgili olduğunu doğrular
2. **REQ-2.2** WHEN matematiksel bir cevap verildiğinde, THE Validator SHALL hesaplamaların doğru olduğunu kontrol eder
3. **REQ-2.3** WHEN tarihsel bir bilgi verildiğinde, THE Validator SHALL tarihlerin ve olayların doğru olduğunu kontrol eder
4. **REQ-2.4** WHEN bilimsel bir açıklama yapıldığında, THE Validator SHALL bilimsel doğruluğu kontrol eder
5. **REQ-2.5** WHEN kaynak gösterildiğinde, THE Validator SHALL kaynağın güvenilir olduğunu doğrular
6. **REQ-2.6** IF cevap belirsiz veya yanlışsa, THEN THE Validator SHALL uyarı verir ve düzeltme ister

---

### Requirement 3: ExamAgent Yanıt Doğrulama

**User Story:** As a öğretmen, I want ExamAgent'ın yaptığı değerlendirmelerin adil ve doğru olduğunu bilmek, so that öğrencilerim hak ettikleri notu alsın.

#### Acceptance Criteria

1. **REQ-3.1** WHEN ExamAgent bir sınavı değerlendirdiğinde, THE Validator SHALL puanlama kriterlerinin tutarlı uygulandığını kontrol eder
2. **REQ-3.2** WHEN doğru/yanlış sayısı hesaplandığında, THE Validator SHALL hesaplamaların matematiksel olarak doğru olduğunu doğrular
3. **REQ-3.3** WHEN performans analizi yapıldığında, THE Validator SHALL istatistiksel hesaplamaların doğru olduğunu kontrol eder
4. **REQ-3.4** WHEN zayıf alan tespiti yapıldığında, THE Validator SHALL tespitlerin veriye dayalı olduğunu doğrular
5. **REQ-3.5** WHEN öneri sunulduğunda, THE Validator SHALL önerilerin öğrenci profiline uygun olduğunu kontrol eder
6. **REQ-3.6** IF değerlendirme tutarsızlık içeriyorsa, THEN THE Validator SHALL yeniden değerlendirme tetikler

---

### Requirement 4: Fact-Checking Sistemi

**User Story:** As a sistem yöneticisi, I want AI agent'ların verdiği bilgilerin doğruluğunun otomatik kontrol edilmesini, so that yanlış bilgi yayılmasını önleyeyim.

#### Acceptance Criteria

1. **REQ-4.1** WHEN bir AI yanıtı fact-check edildiğinde, THE Fact-Checker SHALL RAG sistemini kullanarak ilgili belgeleri bulur
2. **REQ-4.2** WHEN belgeler bulunduğunda, THE Fact-Checker SHALL yanıt ile belgeleri karşılaştırır
3. **REQ-4.3** WHEN Wikipedia API kullanıldığında, THE Fact-Checker SHALL Türkçe Wikipedia'dan bilgi doğrular
4. **REQ-4.4** WHEN MEB kaynakları kontrol edildiğinde, THE Fact-Checker SHALL resmi eğitim kaynaklarını önceliklendirir
5. **REQ-4.5** WHEN doğruluk skoru hesaplandığında, THE Fact-Checker SHALL 0-1 arası bir skor üretir
6. **REQ-4.6** IF bilgi doğrulanamıyorsa, THEN THE Fact-Checker SHALL "doğrulanamadı" uyarısı verir

---

### Requirement 5: Tutarlılık Kontrolü

**User Story:** As a öğrenci, I want AI agent'ın önceki söyledikleriyle çelişmemesini, so that kafam karışmasın.

#### Acceptance Criteria

1. **REQ-5.1** WHEN yeni bir yanıt üretildiğinde, THE Consistency Checker SHALL son 10 yanıtı kontrol eder
2. **REQ-5.2** WHEN önceki yanıtlar analiz edildiğinde, THE Checker SHALL aynı konu hakkındaki ifadeleri karşılaştırır
3. **REQ-5.3** WHEN çelişki tespit edildiğinde, THE Checker SHALL çelişkinin türünü belirler (doğrudan, dolaylı)
4. **REQ-5.4** WHEN çelişki skoru hesaplandığında, THE Checker SHALL 0-1 arası bir skor üretir
5. **REQ-5.5** WHEN tutarlılık skoru düşük olduğunda, THE Checker SHALL uyarı verir
6. **REQ-5.6** IF ciddi çelişki varsa, THEN THE Checker SHALL yanıtı engeller ve düzeltme ister

---

### Requirement 6: Stop Hook Entegrasyonu

**User Story:** As a sistem yöneticisi, I want AI yanıt tamamlandığında otomatik doğrulama yapılmasını, so that hatalı yanıtlar kullanıcıya ulaşmasın.

#### Acceptance Criteria

1. **REQ-6.1** WHEN AI agent yanıt vermeyi bitirdiğinde, THE Stop Hook SHALL otomatik olarak tetiklenir
2. **REQ-6.2** WHEN hook tetiklendiğinde, THE Hook SHALL tüm validator'ları paralel olarak çalıştırır
3. **REQ-6.3** WHEN validation tamamlandığında, THE Hook SHALL toplam güven skorunu hesaplar
4. **REQ-6.4** WHEN güven skoru 0.8'in altında olduğunda, THE Hook SHALL yanıtı işaretler
5. **REQ-6.5** WHEN validation sonuçları hazır olduğunda, THE Hook SHALL sonuçları loglar
6. **REQ-6.6** IF kritik hata tespit edilirse, THEN THE Hook SHALL yanıtı engeller ve yöneticiye bildirir

---

### Requirement 7: Confidence Score Hesaplama

**User Story:** As a içerik yöneticisi, I want her AI yanıtının güven skorunu görmek, so that düşük güvenli yanıtları manuel kontrol edebiliyim.

#### Acceptance Criteria

1. **REQ-7.1** WHEN güven skoru hesaplandığında, THE Scoring System SHALL fact-checking sonucuna %40 ağırlık verir
2. **REQ-7.2** WHEN güven skoru hesaplandığında, THE Scoring System SHALL tutarlılık skoruna %30 ağırlık verir
3. **REQ-7.3** WHEN güven skoru hesaplandığında, THE Scoring System SHALL agent-specific validation'a %30 ağırlık verir
4. **REQ-7.4** WHEN toplam skor hesaplandığında, THE Scoring System SHALL ağırlıklı ortalama kullanır
5. **REQ-7.5** WHEN skor 0.8'in altında olduğunda, THE Scoring System SHALL yanıtı "düşük güven" olarak işaretler
6. **REQ-7.6** WHEN skor 0.5'in altında olduğunda, THE Scoring System SHALL yanıtı reddeder

---

### Requirement 8: Hata Raporlama ve İyileştirme

**User Story:** As a AI model trainer, I want hangi tür hataların yapıldığını görmek, so that modeli iyileştirebiliyim.

#### Acceptance Criteria

1. **REQ-8.1** WHEN bir hata tespit edildiğinde, THE Error Reporter SHALL hata türünü kategorize eder
2. **REQ-8.2** WHEN hata raporu oluşturulduğunda, THE Reporter SHALL hatanın kaynağını belirler (agent, model, data)
3. **REQ-8.3** WHEN hata sıklığı analiz edildiğinde, THE Reporter SHALL en sık yapılan hataları listeler
4. **REQ-8.4** WHEN iyileştirme önerisi sunulduğunda, THE Reporter SHALL somut örnekler verir
5. **REQ-8.5** WHEN rapor oluşturulduğunda, THE Reporter SHALL trend analizi yapar
6. **REQ-8.6** WHEN rapor kaydedildiğinde, THE Reporter SHALL raporu veritabanına ve dashboard'a gönderir

---

## Bağımlılıklar

- **RAG System**: Fact-checking için
- **Wikipedia API**: Bilgi doğrulama için
- **MEB Müfredat API**: Eğitim içeriği doğrulama için
- **Redis**: Yanıt geçmişi cache için
- **PostgreSQL**: Validation sonuçları için
- **LangSmith**: Agent monitoring için

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 1.5 hafta
**Beklenen Kalite Artışı:** %200-300

## Verification Flow

```
1. AI Agent Yanıt Üretti
   ↓
2. Stop Hook Tetiklendi
   ↓
3. Agent-Specific Validation (30%)
   ├─ LearningPathAgent → Müfredat + Sıralama
   ├─ StudyBuddyAgent → Konu İlgisi + Doğruluk
   └─ ExamAgent → Puanlama + İstatistik
   ↓
4. Fact-Checking (40%)
   ├─ RAG System Query
   ├─ Wikipedia Lookup
   └─ MEB Kaynak Kontrolü
   ↓
5. Consistency Check (30%)
   ├─ Son 10 Yanıt Analizi
   └─ Çelişki Tespiti
   ↓
6. Confidence Score Hesaplama (0-1)
   ↓
7. Score >= 0.8?
   ├─ EVET → Yanıt Onaylandı ✓
   ├─ 0.5-0.8 → Manuel İnceleme Gerekli ⚠
   └─ < 0.5 → Yanıt Reddedildi ✗
```

## Success Metrics

1. **Ortalama Confidence Score:** >= 0.85
2. **Otomatik Onay Oranı:** >= %85
3. **Hata Tespit Oranı:** >= %90
4. **Ortalama Doğrulama Süresi:** < 2 saniye
5. **Yanlış Pozitif Oranı:** < %5
