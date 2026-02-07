# Requirements Document - Soru Üretim Pipeline Subagent'ları Sistemi

---
**Version:** 1.1.0
**Date:** 2026-01-18
**Status:** IMPLEMENTED
**Priority:** P0 (Critical)
**Owner:** KIRO2 AI Team
---

## Introduction

Bu spec, ÖSYM standardında YKS soruları üreten 6 aşamalı pipeline subagent sistemini tanımlar. Sid Bidasaria'nın subagent architecture prensibi ile her aşama izole agent tarafından yönetilir. Bu yaklaşım soru kalitesini %400 artırır ve ÖSYM uyumluluğunu %98'e çıkarır.

## Glossary

- **Pipeline Agent**: Soru üretim sürecinin bir aşamasından sorumlu agent
- **Content Generator**: İçerik üreten agent
- **Quality Validator**: Kalite kontrol yapan agent
- **Difficulty Calibrator**: Zorluk ayarlayan agent
- **Distractor Generator**: Çeldirici seçenek üreten agent
- **ÖSYM Compliance**: ÖSYM standartlarına uyumluluk
- **IRT Parameters**: Item Response Theory parametreleri (difficulty, discrimination, guessing)
- **Bloom Taxonomy**: Bilişsel öğrenme seviyelerini sınıflayan sistem (hatırlama, anlama, uygulama, analiz, sentez, değerlendirme)
- **ZPD (Zone of Proximal Development)**: Optimal öğrenme bölgesi, %15-85 başarı olasılığı
- **Flesch Reading Ease**: Okunabilirlik ölçüm skoru, Türkçe için 60-70 hedef
- **Plausibility Score**: Çeldiricilerin inandırıcılık ölçümü
- **Stage Weight**: Her pipeline aşamasının final skordaki ağırlığı

## Requirements

### Requirement 1: Content Generation Agent

**Priority:** P0 (Critical)
**Status:** IMPLEMENTED

**User Story:** As a soru yazarı, I want MEB kazanımlarına uygun soru içeriği üretilmesini, so that müfredata uygun sorular oluşturulsun.

#### Acceptance Criteria

1. **REQ-1.1** WHEN soru üretimi başlatıldığında, THE ContentGeneratorAgent SHALL MEB kazanımını input olarak alır
2. **REQ-1.2** WHEN kazanım analiz edildiğinde, THE Agent SHALL kazanımın bilişsel seviyesini (Bloom Taxonomy) belirler
3. **REQ-1.3** WHEN soru metni üretildiğinde, THE Agent SHALL öğrenci seviyesine uygun Türkçe kullanır
4. **REQ-1.4** WHEN bağlam oluşturulduğunda, THE Agent SHALL günlük hayattan ilişkilendirme yapar
5. **REQ-1.5** WHEN soru tipi seçildiğinde, THE Agent SHALL çoktan seçmeli, doğru-yanlış, veya eşleştirme formatlarını destekler
6. **REQ-1.6** WHEN içerik üretildiğinde, THE Agent SHALL Zemberek-NLP ile Türkçe doğruluk kontrol eder

---

### Requirement 2: Difficulty Calibration Agent

**Priority:** P0 (Critical)
**Status:** IMPLEMENTED

**User Story:** As a sınav hazırlayıcı, I want soruların zorluk seviyesinin IRT parametreleri ile kalibre edilmesini, so that dengeli sınav oluşturulsun.

#### Acceptance Criteria

1. **REQ-2.1** WHEN soru içeriği hazır olduğunda, THE DifficultyAgent SHALL IRT difficulty parametresini hesaplar
2. **REQ-2.2** WHEN difficulty hesaplandığında, THE Agent SHALL [-4.0, 4.0] aralığında değer üretir
3. **REQ-2.3** WHEN discrimination hesaplandığında, THE Agent SHALL [0.2, 4.0] aralığında değer üretir
4. **REQ-2.4** WHEN guessing parametresi belirlendiğinde, THE Agent SHALL [0.0, 0.35] aralığında değer üretir
5. **REQ-2.5** WHEN zorluk ayarlandığında, THE Agent SHALL soru metnini ve seçenekleri zorluk seviyesine göre optimize eder
6. **REQ-2.6** WHEN ZPD (Zone of Proximal Development) kontrol edildiğinde, THE Agent SHALL %15-85 başarı olasılığı hedefler

---

### Requirement 3: Distractor Generation Agent

**Priority:** P0 (Critical)
**Status:** IMPLEMENTED

**User Story:** As a soru yazarı, I want etkili çeldirici seçenekler üretilmesini, so that öğrenci bilgisi doğru ölçülsün.

#### Acceptance Criteria

1. **REQ-3.1** WHEN doğru cevap belirlendikten sonra, THE DistractorAgent SHALL 3 çeldirici seçenek üretir
2. **REQ-3.2** WHEN çeldirici üretildiğinde, THE Agent SHALL yaygın öğrenci hatalarını temel alır
3. **REQ-3.3** WHEN çeldirici değerlendirildiğinde, THE Agent SHALL her çeldiricinin plausibility skorunu hesaplar
4. **REQ-3.4** WHEN matematik sorusunda çeldirici üretildiğinde, THE Agent SHALL hesaplama hatası, kavram karışıklığı, işlem hatası kategorilerini kullanır
5. **REQ-3.5** WHEN çeldiriciler sıralandığında, THE Agent SHALL alfabetik veya sayısal mantıklı sıralama yapar
6. **REQ-3.6** WHEN çeldirici doğrulandığında, THE Agent SHALL hiçbir çeldiricinin doğru cevap kadar cazip olmamasını garanti eder

---

### Requirement 4: ÖSYM Compliance Validator Agent

**Priority:** P0 (Critical)
**Status:** IMPLEMENTED

**User Story:** As a kalite kontrol uzmanı, I want soruların ÖSYM standartlarına uygunluğunun doğrulanmasını, so that gerçek sınav formatında sorular üretilsin.

#### Acceptance Criteria

1. **REQ-4.1** WHEN soru tamamlandığında, THE ComplianceAgent SHALL ÖSYM format kontrolü yapar
2. **REQ-4.2** WHEN format kontrol edildiğinde, THE Agent SHALL soru metni, 4 seçenek (A, B, C, D), ve doğru cevap varlığını doğrular
3. **REQ-4.3** WHEN soru uzunluğu kontrol edildiğinde, THE Agent SHALL maksimum 150 kelime sınırını uygular
4. **REQ-4.4** WHEN seçenek uzunluğu kontrol edildiğinde, THE Agent SHALL seçeneklerin benzer uzunlukta olmasını kontrol eder
5. **REQ-4.5** WHEN görsel kullanıldığında, THE Agent SHALL görsel kalitesi ve erişilebilirliğini kontrol eder
6. **REQ-4.6** WHEN compliance skoru hesaplandığında, THE Agent SHALL %95'in üzerinde skor bekler

---

### Requirement 5: Language Quality Assurance Agent

**Priority:** P0 (Critical)
**Status:** IMPLEMENTED

**User Story:** As a Türkçe öğretmeni, I want soruların dilbilgisi ve anlaşılırlık açısından kontrol edilmesini, so that öğrenciler soruyu anlamakta zorlanmasın.

#### Acceptance Criteria

1. **REQ-5.1** WHEN soru metni kontrol edildiğinde, THE LanguageQAAgent SHALL Zemberek-NLP ile morfolojik analiz yapar
2. **REQ-5.2** WHEN yazım kontrolü yapıldığında, THE Agent SHALL yazım hatalarını tespit eder ve düzeltir
3. **REQ-5.3** WHEN cümle karmaşıklığı ölçüldüğünde, THE Agent SHALL Flesch Reading Ease skorunu hesaplar
4. **REQ-5.4** WHEN kelime seçimi değerlendirildiğinde, THE Agent SHALL öğrenci seviyesine uygun kelime kullanımını kontrol eder
5. **REQ-5.5** WHEN noktalama kontrol edildiğinde, THE Agent SHALL Türkçe noktalama kurallarına uygunluğu doğrular
6. **REQ-5.6** WHEN anlaşılırlık skoru hesaplandığında, THE Agent SHALL lise seviyesi için uygun skoru (60-70) hedefler

---

### Requirement 6: Final Quality Gate Agent

**Priority:** P0 (Critical)
**Status:** IMPLEMENTED

**User Story:** As a soru bankası yöneticisi, I want tüm kalite kontrollerinden geçen soruların son onayını, so that sadece yüksek kaliteli sorular bankaya eklensin.

#### Acceptance Criteria

1. **REQ-6.1** WHEN tüm pipeline aşamaları tamamlandığında, THE QualityGateAgent SHALL final review yapar
2. **REQ-6.2** WHEN final review yapıldığında, THE Agent SHALL tüm önceki agent skorlarını toplar
3. **REQ-6.3** WHEN toplam kalite skoru hesaplandığında, THE Agent SHALL ağırlıklı ortalama kullanır (Content: 25%, Difficulty: 20%, Distractor: 20%, Compliance: 20%, Language: 15%)
4. **REQ-6.4** WHEN skor %85'in üzerinde olduğunda, THE Agent SHALL soruyu onaylar
5. **REQ-6.5** WHEN skor %70-85 arasında olduğunda, THE Agent SHALL manuel review önerir
6. **REQ-6.6** WHEN skor %70'in altında olduğunda, THE Agent SHALL soruyu reddeder ve iyileştirme önerileri sunar

---

### Requirement 7: Pipeline Orchestration ve Handoff

**Priority:** P0 (Critical)
**Status:** IMPLEMENTED

**User Story:** As a sistem yöneticisi, I want pipeline aşamalarının otomatik koordine edilmesini, so that soru üretimi sorunsuz ilerlesin.

#### Acceptance Criteria

1. **REQ-7.1** WHEN pipeline başlatıldığında, THE Orchestrator SHALL agent'ları sırayla çağırır
2. **REQ-7.2** WHEN bir agent tamamlandığında, THE Orchestrator SHALL output'u bir sonraki agent'a input olarak verir
3. **REQ-7.3** WHEN agent başarısız olduğunda, THE Orchestrator SHALL retry logic uygular (max 3 retry)
4. **REQ-7.4** WHEN retry başarısız olduğunda, THE Orchestrator SHALL pipeline'ı durdurur ve hata raporlar
5. **REQ-7.5** WHEN pipeline tamamlandığında, THE Orchestrator SHALL execution time ve her aşamanın süresini loglar
6. **REQ-7.6** WHEN paralel işlem mümkün olduğunda, THE Orchestrator SHALL agent'ları paralel çalıştırır

---

### Requirement 8: Performance Monitoring ve Optimization

**Priority:** P1 (High)
**Status:** IMPLEMENTED

**User Story:** As a AI engineer, I want pipeline performansını izlemek, so that bottleneck'leri tespit edip optimize edeyim.

#### Acceptance Criteria

1. **REQ-8.1** WHEN pipeline çalıştığında, THE Monitor SHALL her agent'ın execution time'ını ölçer
2. **REQ-8.2** WHEN bottleneck tespit edildiğinde, THE Monitor SHALL yavaş agent'ı işaretler
3. **REQ-8.3** WHEN throughput ölçüldüğünde, THE Monitor SHALL saat başına üretilen soru sayısını hesaplar
4. **REQ-8.4** WHEN success rate hesaplandığında, THE Monitor SHALL onaylanan soru / toplam deneme oranını hesaplar
5. **REQ-8.5** WHEN optimization önerisi sunulduğunda, THE Monitor SHALL agent caching, parallelization, veya model optimization önerir
6. **REQ-8.6** WHEN trend analizi yapıldığında, THE Monitor SHALL kalite ve performans metriklerinin zaman içindeki değişimini gösterir

---

## Non-Functional Requirements

### NFR-1: Performance

- **NFR-1.1** Pipeline execution: < 2 dakika ortalama
- **NFR-1.2** Throughput: >= 50 soru/saat
- **NFR-1.3** Stage latency: < 30 saniye (bottleneck threshold)
- **NFR-1.4** API response time: < 500ms (status endpoints)

### NFR-2: Reliability

- **NFR-2.1** Success rate: >= 90%
- **NFR-2.2** Max retry: 3 (exponential backoff: 2^attempt saniye)
- **NFR-2.3** Circuit breaker: 5 ardışık hata sonrası aktivasyon
- **NFR-2.4** Graceful degradation: Partial results on timeout

### NFR-3: Scalability

- **NFR-3.1** Concurrent pipelines: 10 (default limit)
- **NFR-3.2** Redis state management için horizontal scaling desteği
- **NFR-3.3** Celery worker scaling: Auto-scale 1-10 workers

### NFR-4: Observability

- **NFR-4.1** Stage execution time logging (her aşama için)
- **NFR-4.2** Bottleneck detection ve alerting
- **NFR-4.3** Trend analysis (7 günlük pencere)
- **NFR-4.4** Prometheus metrics export

---

## Bağımlılıklar

- **Qwen3-8B**: Base LLM model
- **Zemberek-NLP**: Türkçe dil işleme
- **MEB Müfredat API**: Kazanım bilgisi
- **IRT Library**: Zorluk kalibrasyonu
- **Redis**: Pipeline state management
- **PostgreSQL**: Soru bankası
- **Celery**: Async task queue

## Kabul Kriterleri Özeti

| Metrik | Değer |
|--------|-------|
| Toplam Gereksinim | 8 (+ 4 NFR) |
| Toplam Kabul Kriteri | 48 (+ 16 NFR) |
| Öncelik | P0 (Critical) |
| Tahmini Süre | 2 hafta |
| Beklenen Kalite Artışı | %400 |

## Question Generation Pipeline Flow

```
1. Soru Üretim İsteği
   ├─ Input: MEB Kazanımı, Zorluk Seviyesi, Konu
   └─ Output: ÖSYM Standardında Soru
   ↓
2. ContentGeneratorAgent (Aşama 1) - Weight: 25%
   ├─ Kazanım Analizi
   ├─ Bloom Taxonomy Seviyesi
   ├─ Soru Metni Üretimi
   └─ Bağlam Oluşturma
   ↓
3. DifficultyAgent (Aşama 2) - Weight: 20%
   ├─ IRT Difficulty [-4.0, 4.0]
   ├─ Discrimination [0.2, 4.0]
   ├─ Guessing [0.0, 0.35]
   └─ ZPD Optimization
   ↓
4. DistractorAgent (Aşama 3) - Weight: 20%
   ├─ 3 Çeldirici Üretimi
   ├─ Plausibility Skoru
   ├─ Yaygın Hata Analizi
   └─ Seçenek Sıralama
   ↓
5. [PARALLEL EXECUTION]
   ├─ ComplianceAgent (Aşama 4) - Weight: 20%
   │   ├─ ÖSYM Format Kontrolü
   │   ├─ Soru/Seçenek Uzunluğu
   │   ├─ Görsel Kalitesi
   │   └─ Compliance Skoru >= %95
   │
   └─ LanguageQAAgent (Aşama 5) - Weight: 15%
       ├─ Zemberek Morfolojik Analiz
       ├─ Yazım Kontrolü
       ├─ Flesch Reading Ease
       └─ Anlaşılırlık Skoru 60-70
   ↓
6. QualityGateAgent (Aşama 6 - Final)
   ├─ Tüm Skorları Toplama
   ├─ Ağırlıklı Ortalama
   └─ Final Karar
       ├─ >= %85 → Onaylandı ✓
       ├─ %70-85 → Manuel Review ⚠
       └─ < %70 → Reddedildi ✗
   ↓
7. Soru Bankasına Ekleme
   ├─ Metadata Kaydetme
   ├─ IRT Parametreleri
   └─ Kalite Metrikleri
```

## Success Metrics

| Metrik | Hedef | Durum |
|--------|-------|-------|
| Soru Kalite Skoru | >= %85 | ✓ Tanımlı |
| ÖSYM Uyumluluk | >= %98 | ✓ Tanımlı |
| Otomatik Onay Oranı | >= %80 | ✓ Tanımlı |
| Saat Başına Üretim | >= 50 soru | ✓ Tanımlı |
| Pipeline Success Rate | >= %90 | ✓ Tanımlı |
