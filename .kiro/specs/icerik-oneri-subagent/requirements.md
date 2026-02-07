# Requirements Document - İçerik Öneri Subagent'ları Sistemi

## Introduction

Bu spec, çoklu kaynaklardan (YouTube, Wikipedia, MEB, akademik makaleler, interaktif simülasyonlar) eğitim içeriği toplayan ve öğrenciye özel öneren 5 scraper subagent sistemini tanımlar. Sid Bidasaria'nın subagent architecture prensibi ile her agent farklı bir içerik kaynağına odaklanır. Bu yaklaşım içerik çeşitliliğini %500 artırır ve öğrenme deneyimini zenginleştirir.

## Glossary

- **Content Scraper**: İçerik toplama agent'ı
- **Relevance Scorer**: İçerik ilgililik skorlayıcı
- **Quality Ranker**: Kalite sıralayıcı
- **Multi-Modal Content**: Çoklu format içerik (video, metin, interaktif)
- **Content Freshness**: İçerik güncelliği
- **Semantic Search**: Anlamsal arama
- **Content Curation**: İçerik küratörlüğü

## Requirements

### Requirement 1: YouTube Content Scraper Agent

**User Story:** As a öğrenci, I want konuyla ilgili kaliteli YouTube videolarını bulmak, so that görsel öğrenme yapabiliyim.

#### Acceptance Criteria

1. **REQ-1.1** WHEN konu aranırken, THE YouTubeAgent SHALL YouTube Data API v3 kullanır
2. **REQ-1.2** WHEN arama yapıldığında, THE Agent SHALL Türkçe eğitim kanallarını önceliklendirir
3. **REQ-1.3** WHEN video filtrelendiğinde, THE Agent SHALL video süresi (10-30 dk), görüntülenme, ve like/dislike oranını kontrol eder
4. **REQ-1.4** WHEN video kalitesi değerlendirildiğinde, THE Agent SHALL kanal güvenilirliği (subscriber count, verification status) skorlar
5. **REQ-1.5** WHEN transcript çıkarıldığında, THE Agent SHALL YouTube caption API kullanır ve içerik relevance kontrol eder
6. **REQ-1.6** WHEN video önerildiğinde, THE Agent SHALL öğrenci seviyesine uygun (LGS/YKS) içerik seçer

---

### Requirement 2: Wikipedia Content Scraper Agent

**User Story:** As a öğrenci, I want konuyla ilgili Wikipedia makalelerini bulmak, so that temel bilgileri hızlıca öğreneyim.

#### Acceptance Criteria

1. **REQ-2.1** WHEN Wikipedia aranırken, THE WikipediaAgent SHALL Türkçe Wikipedia API kullanır
2. **REQ-2.2** WHEN makale bulunduğunda, THE Agent SHALL makale kalitesini (referans sayısı, uzunluk, güncellik) değerlendirir
3. **REQ-2.3** WHEN içerik çıkarıldığında, THE Agent SHALL summary section'ı önceliklendirir
4. **REQ-2.4** WHEN görsel aranırken, THE Agent SHALL Wikimedia Commons'tan ilgili görselleri çeker
5. **REQ-2.5** WHEN related topics bulunduğunda, THE Agent SHALL "Ayrıca bakınız" bölümünden ilgili konuları önerir
6. **REQ-2.6** WHEN citation gerektiğinde, THE Agent SHALL Wikipedia referanslarını kaynak olarak gösterir

---

### Requirement 3: MEB Official Content Scraper Agent

**User Story:** As a öğretmen, I want MEB'in resmi eğitim içeriklerini bulmak, so that müfredata %100 uygun materyal kullanayım.

#### Acceptance Criteria

1. **REQ-3.1** WHEN MEB içeriği aranırken, THE MEBAgent SHALL EBA (Eğitim Bilişim Ağı) API kullanır
2. **REQ-3.2** WHEN kazanım eşleştirildiğinde, THE Agent SHALL MEB müfredat kodlarını kullanır
3. **REQ-3.3** WHEN içerik tipi seçildiğinde, THE Agent SHALL video, PDF, interaktif içerik, ve test kategorilerini destekler
4. **REQ-3.4** WHEN sınıf seviyesi filtrelendiğinde, THE Agent SHALL 9, 10, 11, 12. sınıf içeriklerini ayırır
5. **REQ-3.5** WHEN içerik indirildiğinde, THE Agent SHALL telif haklarına uygun kullanım sağlar
6. **REQ-3.6** WHEN güncellik kontrol edildiğinde, THE Agent SHALL son müfredat değişikliklerine uygun içerik seçer

---

### Requirement 4: Academic Paper Scraper Agent

**User Story:** As a ileri seviye öğrenci, I want konuyla ilgili akademik makaleleri bulmak, so that derinlemesine öğreneyim.

#### Acceptance Criteria

1. **REQ-4.1** WHEN akademik içerik aranırken, THE AcademicAgent SHALL Google Scholar ve arXiv API kullanır
2. **REQ-4.2** WHEN makale filtrelendiğinde, THE Agent SHALL Türkçe ve İngilizce makaleleri destekler
3. **REQ-4.3** WHEN relevance skorlandığında, THE Agent SHALL citation count ve publication date dikkate alır
4. **REQ-4.4** WHEN abstract çıkarıldığında, THE Agent SHALL öğrenci seviyesine uygun basitleştirme yapar
5. **REQ-4.5** WHEN open access kontrol edildiğinde, THE Agent SHALL sadece ücretsiz erişilebilir makaleleri önerir
6. **REQ-4.6** WHEN citation format istendiğinde, THE Agent SHALL APA, MLA, Chicago formatlarını destekler

---

### Requirement 5: Interactive Simulation Scraper Agent

**User Story:** As a öğrenci, I want interaktif simülasyonlar bulmak, so that deneyerek öğreneyim.

#### Acceptance Criteria

1. **REQ-5.1** WHEN simülasyon aranırken, THE SimulationAgent SHALL PhET, GeoGebra, ve Türkçe eğitim platformlarını tarar
2. **REQ-5.2** WHEN simülasyon değerlendirildiğinde, THE Agent SHALL interactivity level ve educational value skorlar
3. **REQ-5.3** WHEN platform uyumluluğu kontrol edildiğinde, THE Agent SHALL web-based, mobile-friendly simülasyonları önceliklendirir
4. **REQ-5.4** WHEN dil desteği kontrol edildiğinde, THE Agent SHALL Türkçe arayüze sahip simülasyonları filtreler
5. **REQ-5.5** WHEN accessibility kontrol edildiğinde, THE Agent SHALL keyboard navigation ve screen reader desteğini doğrular
6. **REQ-5.6** WHEN embedding mümkün olduğunda, THE Agent SHALL iframe embed code sağlar

---

### Requirement 6: Unified Content Ranking ve Recommendation

**User Story:** As a öğrenci, I want tüm kaynaklardan gelen içeriklerin kalite sırasına göre sunulmasını, so that en iyi içerikle başlayayım.

#### Acceptance Criteria

1. **REQ-6.1** WHEN tüm agent'lar içerik topladığında, THE Ranker SHALL unified scoring algoritması uygular
2. **REQ-6.2** WHEN scoring yapıldığında, THE Ranker SHALL relevance (40%), quality (30%), freshness (20%), accessibility (10%) ağırlıkları kullanır
3. **REQ-6.3** WHEN öğrenci profili dikkate alındığında, THE Ranker SHALL learning style'a göre içerik tipi önceliklendirir
4. **REQ-6.4** WHEN multi-modal öneriler sunulduğunda, THE Ranker SHALL video, metin, ve interaktif içerik karışımını optimize eder
5. **REQ-6.5** WHEN diversity sağlandığında, THE Ranker SHALL farklı kaynaklardan içerik seçer (tek kaynağa bağımlı kalmaz)
6. **REQ-6.6** WHEN personalization uygulandığında, THE Ranker SHALL öğrencinin geçmiş etkileşimlerini (beğeni, tamamlama) dikkate alır

---

### Requirement 7: Content Caching ve Freshness Management

**User Story:** As a sistem yöneticisi, I want içeriklerin cache'lenmesini ve güncel tutulmasını, so that performans ve güncellik dengesi sağlansın.

#### Acceptance Criteria

1. **REQ-7.1** WHEN içerik ilk kez çekildiğinde, THE Cache Manager SHALL Redis'e metadata ve URL kaydeder
2. **REQ-7.2** WHEN cache TTL belirlendiğinde, THE Manager SHALL içerik tipine göre farklı TTL uygular (YouTube: 7 gün, Wikipedia: 30 gün, MEB: 90 gün)
3. **REQ-7.3** WHEN cache expire olduğunda, THE Manager SHALL background job ile içeriği yeniler
4. **REQ-7.4** WHEN içerik değişikliği tespit edildiğinde, THE Manager SHALL invalidation trigger'ı çalıştırır
5. **REQ-7.5** WHEN cache hit rate ölçüldüğünde, THE Manager SHALL %70+ hit rate hedefler
6. **REQ-7.6** WHEN cache eviction gerektiğinde, THE Manager SHALL LRU (Least Recently Used) stratejisi uygular

---

### Requirement 8: Content Quality Monitoring ve Feedback Loop

**User Story:** As a içerik yöneticisi, I want önerilen içeriklerin kalitesini izlemek, so that düşük kaliteli içerikleri filtreleyeyim.

#### Acceptance Criteria

1. **REQ-8.1** WHEN öğrenci içerik tükettiğinde, THE Monitor SHALL engagement metrics toplar (watch time, completion rate, rating)
2. **REQ-8.2** WHEN feedback alındığında, THE Monitor SHALL thumbs up/down ve yorum verilerini kaydeder
3. **REQ-8.3** WHEN quality score güncellediğinde, THE Monitor SHALL user feedback'i scoring algoritmasına entegre eder
4. **REQ-8.4** WHEN low-quality içerik tespit edildiğinde, THE Monitor SHALL içeriği blacklist'e alır
5. **REQ-8.5** WHEN trend analizi yapıldığında, THE Monitor SHALL en popüler ve en etkili içerikleri raporlar
6. **REQ-8.6** WHEN A/B testing yapıldığında, THE Monitor SHALL farklı ranking stratejilerini karşılaştırır

---

## Bağımlılıklar

- **YouTube Data API v3**: Video içerik
- **Wikipedia API**: Ansiklopedik içerik
- **EBA API**: MEB resmi içerik
- **Google Scholar API**: Akademik makaleler
- **PhET/GeoGebra API**: İnteraktif simülasyonlar
- **Redis**: Content caching
- **PostgreSQL**: Content metadata
- **Celery**: Async scraping tasks

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 2 hafta
**Beklenen İçerik Çeşitliliği Artışı:** %500

## Content Recommendation Flow

```
1. Öğrenci Konu Arama / Öğrenme Yolu Başlatma
   ↓
2. Paralel Content Scraping (5 Agent)
   ├─ YouTubeAgent
   │  ├─ YouTube Data API v3
   │  ├─ Türkçe Eğitim Kanalları
   │  └─ Video Quality Scoring
   ├─ WikipediaAgent
   │  ├─ Türkçe Wikipedia API
   │  ├─ Article Quality Check
   │  └─ Related Topics
   ├─ MEBAgent
   │  ├─ EBA API
   │  ├─ Kazanım Eşleştirme
   │  └─ Sınıf Seviyesi Filtreleme
   ├─ AcademicAgent
   │  ├─ Google Scholar / arXiv
   │  ├─ Citation Count
   │  └─ Open Access Filter
   └─ SimulationAgent
      ├─ PhET / GeoGebra
      ├─ Interactivity Level
      └─ Türkçe Dil Desteği
   ↓
3. Content Aggregation & Deduplication
   ├─ Tüm Sonuçları Toplama
   ├─ Duplicate Detection
   └─ Metadata Normalization
   ↓
4. Unified Content Ranking
   ├─ Relevance Score (40%)
   ├─ Quality Score (30%)
   ├─ Freshness Score (20%)
   └─ Accessibility Score (10%)
   ↓
5. Personalization Layer
   ├─ Learning Style Matching
   ├─ Knowledge Gap Alignment
   ├─ Past Interaction History
   └─ Multi-Modal Mix Optimization
   ↓
6. Content Presentation
   ├─ Top 10 Recommendations
   ├─ Grouped by Type (Video/Text/Interactive)
   └─ Thumbnail, Title, Description, Duration
   ↓
7. User Engagement Tracking
   ├─ Click-through Rate
   ├─ Watch/Read Time
   ├─ Completion Rate
   └─ User Rating
   ↓
8. Feedback Loop & Quality Update
   ├─ Engagement Metrics → Ranking Update
   ├─ Low Quality → Blacklist
   └─ High Quality → Boost Score
```

## Success Metrics

1. **İçerik Çeşitliliği:** 5 farklı kaynak entegrasyonu
2. **Relevance Accuracy:** >= %85
3. **Cache Hit Rate:** >= %70
4. **User Engagement:** %60 artış
5. **Content Freshness:** %90 güncel içerik

