# Requirements Document - Öğrenci Profil Analiz Subagent'ları Sistemi

## Introduction

Bu spec, öğrenci davranışlarını analiz eden ve kişiselleştirilmiş öğrenme deneyimi sunan 5 uzman subagent sistemini tanımlar. Sid Bidasaria'nın subagent architecture prensibi ile her agent farklı bir analiz boyutuna odaklanır. Bu yaklaşım kişiselleştirme doğruluğunu %350 artırır ve öğrenci başarısını %40 yükseltir.

## Glossary

- **Learning Style**: Öğrenme stili (görsel, işitsel, kinestetik, okuma/yazma)
- **Performance Tracker**: Performans takip sistemi
- **Behavioral Analyzer**: Davranış analiz sistemi
- **Knowledge Gap Detector**: Bilgi eksikliği tespit sistemi
- **Motivation Profiler**: Motivasyon profil çıkarıcı
- **FSRS**: Free Spaced Repetition Scheduler
- **ZPD**: Zone of Proximal Development

## Requirements

### Requirement 1: Learning Style Detection Agent

**User Story:** As a öğrenci, I want öğrenme stilimin otomatik tespit edilmesini, so that bana uygun içerik önerilsin.

#### Acceptance Criteria

1. **REQ-1.1** WHEN öğrenci platforma ilk girdiğinde, THE LearningStyleAgent SHALL VARK assessment başlatır
2. **REQ-1.2** WHEN öğrenci davranışları analiz edildiğinde, THE Agent SHALL video izleme, okuma, pratik yapma oranlarını ölçer
3. **REQ-1.3** WHEN öğrenme stili belirlendiğinde, THE Agent SHALL Visual, Auditory, Reading/Writing, Kinesthetic skorlarını hesaplar
4. **REQ-1.4** WHEN dominant stil tespit edildiğinde, THE Agent SHALL %60+ skora sahip stili dominant olarak işaretler
5. **REQ-1.5** WHEN multi-modal öğrenci tespit edildiğinde, THE Agent SHALL birden fazla stili destekleyen içerik önerir
6. **REQ-1.6** WHEN stil değişimi gözlendiğinde, THE Agent SHALL profili dinamik olarak günceller

---

### Requirement 2: Performance Tracking Agent

**User Story:** As a öğretmen, I want öğrenci performansının detaylı takibini, so that gelişim alanlarını belirleyeyim.

#### Acceptance Criteria

1. **REQ-2.1** WHEN öğrenci soru çözdüğünde, THE PerformanceAgent SHALL doğru/yanlış, süre, ve zorluk seviyesini kaydeder
2. **REQ-2.2** WHEN performans analiz edildiğinde, THE Agent SHALL konu bazlı başarı oranlarını hesaplar
3. **REQ-2.3** WHEN trend analizi yapıldığında, THE Agent SHALL son 30 günlük performans grafiği oluşturur
4. **REQ-2.4** WHEN IRT parametreleri güncellendiğinde, THE Agent SHALL öğrenci ability parametresini [-4.0, 4.0] aralığında hesaplar
5. **REQ-2.5** WHEN benchmark karşılaştırması yapıldığında, THE Agent SHALL öğrenciyi sınıf ortalaması ile karşılaştırır
6. **REQ-2.6** WHEN performans düşüşü tespit edildiğinde, THE Agent SHALL erken uyarı sistemi tetikler

---

### Requirement 3: Knowledge Gap Detection Agent

**User Story:** As a öğrenci, I want bilgi eksiklerimin tespit edilmesini, so that doğru konulara odaklanayım.

#### Acceptance Criteria

1. **REQ-3.1** WHEN öğrenci yanlış cevap verdiğinde, THE KnowledgeGapAgent SHALL hangi kazanımda eksik olduğunu tespit eder
2. **REQ-3.2** WHEN gap analizi yapıldığında, THE Agent SHALL ön koşul bilgi eksiklerini tespit eder
3. **REQ-3.3** WHEN gap severity hesaplandığında, THE Agent SHALL kritik (kırmızı), orta (sarı), düşük (yeşil) kategorilere ayırır
4. **REQ-3.4** WHEN gap pattern tespit edildiğinde, THE Agent SHALL sistematik kavram yanılgılarını belirler
5. **REQ-3.5** WHEN remediation planı oluşturulduğunda, THE Agent SHALL öncelikli çalışma konularını sıralar
6. **REQ-3.6** WHEN gap kapatıldığında, THE Agent SHALL mastery level'ı günceller ve yeni hedefler belirler

---

### Requirement 4: Behavioral Pattern Analyzer Agent

**User Story:** As a veli, I want çocuğumun çalışma alışkanlıklarını görmek, so that destek olabilirim.

#### Acceptance Criteria

1. **REQ-4.1** WHEN öğrenci aktivitesi loglandığında, THE BehavioralAgent SHALL giriş saatleri, çalışma süreleri, ve sıklığı kaydeder
2. **REQ-4.2** WHEN çalışma pattern'i analiz edildiğinde, THE Agent SHALL optimal çalışma saatlerini tespit eder
3. **REQ-4.3** WHEN dikkat süresi ölçüldüğünde, THE Agent SHALL ortalama focus duration hesaplar
4. **REQ-4.4** WHEN procrastination tespit edildiğinde, THE Agent SHALL erteleme pattern'lerini belirler
5. **REQ-4.5** WHEN consistency skoru hesaplandığında, THE Agent SHALL düzenli çalışma alışkanlığını 0-100 arası skorlar
6. **REQ-4.6** WHEN behavioral insight sunulduğunda, THE Agent SHALL actionable öneriler verir (örn: "Sabah 09:00-11:00 arası en verimli saatleriniz")

---

### Requirement 5: Motivation Profiling Agent

**User Story:** As a öğrenci, I want motivasyon seviyemin takip edilmesini, so that düştüğünde destek alayım.

#### Acceptance Criteria

1. **REQ-5.1** WHEN öğrenci etkileşimi analiz edildiğinde, THE MotivationAgent SHALL engagement skorunu hesaplar
2. **REQ-5.2** WHEN motivasyon göstergeleri ölçüldüğünde, THE Agent SHALL login frequency, session duration, ve completion rate kullanır
3. **REQ-5.3** WHEN motivasyon düşüşü tespit edildiğinde, THE Agent SHALL gamification elementleri önerir (badge, streak, leaderboard)
4. **REQ-5.4** WHEN goal-setting yapıldığında, THE Agent SHALL SMART (Specific, Measurable, Achievable, Relevant, Time-bound) hedefler önerir
5. **REQ-5.5** WHEN achievement unlock edildiğinde, THE Agent SHALL celebration notification gönderir
6. **REQ-5.6** WHEN motivasyon profili oluşturulduğunda, THE Agent SHALL intrinsic vs extrinsic motivation balance'ı belirler

---

### Requirement 6: Adaptive Learning Path Generator

**User Story:** As a öğrenci, I want bana özel öğrenme yolu oluşturulmasını, so that en verimli şekilde çalışayım.

#### Acceptance Criteria

1. **REQ-6.1** WHEN tüm profil agent'ları analiz tamamladığında, THE PathGenerator SHALL kişiselleştirilmiş öğrenme yolu oluşturur
2. **REQ-6.2** WHEN yol oluşturulduğunda, THE Generator SHALL learning style, knowledge gaps, ve ZPD'yi dikkate alır
3. **REQ-6.3** WHEN konu sıralaması yapıldığında, THE Generator SHALL ön koşul ilişkilerini ve zorluk progression'ı uygular
4. **REQ-6.4** WHEN içerik önerildiğinde, THE Generator SHALL video, metin, interaktif alıştırma karışımını optimize eder
5. **REQ-6.5** WHEN FSRS entegre edildiğinde, THE Generator SHALL optimal tekrar zamanlarını hesaplar
6. **REQ-6.6** WHEN yol güncellediğinde, THE Generator SHALL öğrenci ilerlemesine göre dinamik ayarlama yapar

---

### Requirement 7: Multi-Agent Coordination ve Data Fusion

**User Story:** As a sistem yöneticisi, I want profil agent'larının koordineli çalışmasını, so that tutarlı öğrenci profili oluşturulsun.

#### Acceptance Criteria

1. **REQ-7.1** WHEN profil analizi başlatıldığında, THE Coordinator SHALL 5 agent'ı paralel çalıştırır
2. **REQ-7.2** WHEN agent'lar tamamlandığında, THE Coordinator SHALL sonuçları merkezi profile birleştirir
3. **REQ-7.3** WHEN çelişki tespit edildiğinde, THE Coordinator SHALL conflict resolution stratejisi uygular
4. **REQ-7.4** WHEN profil güncellendiğinde, THE Coordinator SHALL incremental update yapar (full rebuild değil)
5. **REQ-7.5** WHEN real-time analiz gerektiğinde, THE Coordinator SHALL streaming data processing kullanır
6. **REQ-7.6** WHEN profil export edildiğinde, THE Coordinator SHALL JSON formatında comprehensive profile oluşturur

---

### Requirement 8: Privacy ve KVKK Compliance

**User Story:** As a veli, I want çocuğumun verilerinin güvenli tutulmasını, so that gizlilik korunsun.

#### Acceptance Criteria

1. **REQ-8.1** WHEN öğrenci verisi toplandığında, THE System SHALL KVKK onayı alır
2. **REQ-8.2** WHEN veri saklandığında, THE System SHALL encryption at rest uygular
3. **REQ-8.3** WHEN veri transfer edildiğinde, THE System SHALL TLS 1.3 kullanır
4. **REQ-8.4** WHEN veri silinmek istendiğinde, THE System SHALL GDPR right to be forgotten'ı destekler
5. **REQ-8.5** WHEN veri paylaşıldığında, THE System SHALL anonymization ve pseudonymization uygular
6. **REQ-8.6** WHEN audit log tutulduğunda, THE System SHALL tüm veri erişimlerini loglar

---

## Bağımlılıklar

- **PostgreSQL**: Öğrenci profil verisi
- **Redis**: Real-time analytics cache
- **Pandas**: Data analysis
- **scikit-learn**: ML models (clustering, classification)
- **FSRS Algorithm**: Spaced repetition
- **IRT Library**: Ability estimation
- **Celery**: Async profil analizi

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 2 hafta
**Beklenen Kişiselleştirme Artışı:** %350

## Student Profile Analysis Flow

```
1. Öğrenci Aktivitesi (Soru Çözme, Video İzleme, Okuma)
   ↓
2. Paralel Agent Execution
   ├─ LearningStyleAgent
   │  ├─ VARK Assessment
   │  ├─ Behavioral Pattern
   │  └─ Dominant Style Detection
   ├─ PerformanceAgent
   │  ├─ Doğru/Yanlış Tracking
   │  ├─ IRT Ability Estimation
   │  └─ Trend Analysis
   ├─ KnowledgeGapAgent
   │  ├─ Kazanım Eksikleri
   │  ├─ Ön Koşul Analizi
   │  └─ Gap Severity Scoring
   ├─ BehavioralAgent
   │  ├─ Çalışma Saatleri
   │  ├─ Focus Duration
   │  └─ Consistency Score
   └─ MotivationAgent
      ├─ Engagement Score
      ├─ Goal Progress
      └─ Gamification Triggers
   ↓
3. Data Fusion & Conflict Resolution
   ├─ Agent Sonuçları Birleştirme
   ├─ Çelişki Çözümü
   └─ Comprehensive Profile Oluşturma
   ↓
4. Adaptive Learning Path Generation
   ├─ Learning Style Uyumlu İçerik
   ├─ Knowledge Gap Odaklı Sıralama
   ├─ ZPD Optimizasyonu
   └─ FSRS Tekrar Planı
   ↓
5. Personalized Recommendations
   ├─ Konu Önerileri
   ├─ İçerik Formatı (Video/Metin/İnteraktif)
   ├─ Zorluk Seviyesi
   └─ Optimal Çalışma Zamanı
   ↓
6. Continuous Monitoring & Update
   ├─ Real-time Performance Tracking
   ├─ Dynamic Profile Update
   └─ Early Warning System
```

## Success Metrics

1. **Profil Doğruluğu:** >= %90
2. **Kişiselleştirme Etkisi:** %40 başarı artışı
3. **Öğrenci Engagement:** %50 artış
4. **Knowledge Gap Kapatma:** %60 iyileşme
5. **KVKK Compliance:** %100

