# MASTER REQUIREMENTS - Türkiye Üniversite Sınavları Hazırlık Platformu
## Versiyon 1.0 | Oluşturulma: 18 Ekim 2025

---

## Introduction

Bu doküman, Türkiye Üniversite Sınavları Hazırlık Platformu için tüm sistem gereksinimlerini içerir. Platform, YKS (TYT/AYT/YDT) sınavlarına hazırlanan öğrenciler için AI destekli, kişiselleştirilmiş bir eğitim sistemidir. Gereksinimler EARS (Easy Approach to Requirements Syntax) ve INCOSE kalite standartlarına uygun olarak yazılmıştır.

## Glossary

- **Platform**: Türkiye Üniversite Sınavları Hazırlık Platformu web ve mobil uygulaması
- **Sınav Sistemi**: ÖSYM formatında deneme sınavları sunan modül (backend/api/sinav.py)
- **NLP Motoru**: Türkçe doğal dil işleme yapan Zemberek tabanlı sistem (backend/api/zemberek.py)
- **BERTurk Sistemi**: Türkçe BERT modeli ile sentiment analysis ve intent detection (backend/api/berturk_api.py)
- **Adaptif Motor**: Öğrenci performansına göre içerik zorluk seviyesini ayarlayan AI sistemi
- **İçerik Entegrasyon Servisi**: YouTube, Khan Academy, EBA TV gibi dış platformlardan içerik çeken servis
- **Öğretmen Dashboard**: Öğretmenlerin sınıf ve öğrenci yönetimi yaptığı arayüz (backend/api/ogretmen.py)
- **Veli Paneli**: Velilerin çocuk ilerlemesini takip ettiği arayüz (backend/api/veli.py)
- **PWA**: Progressive Web Application - offline çalışabilen web uygulaması
- **WCAG**: Web Content Accessibility Guidelines - erişilebilirlik standardı
- **AI Agent Sistemi**: 7+ farklı AI agentın koordineli çalıştığı yapay zeka sistemi (backend/agents/)
- **LearningPathAgent**: Öğrenme yolu oluşturan AI agent (backend/agents/learning_path_agent.py)
- **StudyBuddyAgent**: Öğrenci sohbet asistanı AI agent (backend/agents/study_buddy_agent.py)
- **AccessibilityAgent**: Erişilebilirlik desteği sağlayan AI agent (backend/agents/accessibility_agent.py)
- **Blackboard Koordinatörü**: AI agentlar arası gerçek zamanlı iletişimi sağlayan sistem (backend/agents/blackboard_coordinator.py)
- **ZPD Motoru**: Zone of Proximal Development - Türk eğitim sistemine özel zorluk ayarlama motoru
- **IRT Motoru**: Item Response Theory - Türkçe morfoloji tabanlı soru analiz motoru (4 parametreli)
- **FSRS Motoru**: Free Spaced Repetition Scheduler - Türk öğrenciler için optimize edilmiş tekrar sistemi (17 parametre)
- **Basitleştirme Motoru**: Metinleri 3 seviyede (lexical, syntactic, semantic) basitleştiren sistem
- **Bionic Reading Motoru**: Disleksi desteği için Türkçe kök-ek ayrımı yapan okuma sistemi
- **İçerik Yönetim Sistemi**: Makale ve video içeriklerinin yönetildiği modül (backend/api/content_management.py)
- **Kaynak Kalite Sistemi**: Video önerilerinin Türkçe ve konu uygunluğunu kontrol eden sistem
- **Sağlık Denetim Sistemi**: Platform bileşenlerinin çalışma durumunu izleyen monitoring sistemi (backend/monitoring/)
- **RAG Sistemi**: Retrieval-Augmented Generation - Bağlamsal AI yanıt sistemi (backend/core/rag_service.py)
- **Cache Manager**: Redis tabanlı önbellekleme sistemi (backend/core/cache.py)
- **Zemberek-NLP**: Türkçe morfolojik analiz servisi (MCP server: zemberek-nlp-server)
- **ÖSYM**: Ölçme, Seçme ve Yerleştirme Merkezi
- **MEB**: Milli Eğitim Bakanlığı
- **YKS**: Yükseköğretim Kurumları Sınavı
- **TYT**: Temel Yeterlilik Testi (120 soru, 165 dakika)
- **AYT**: Alan Yeterlilik Testi (160 soru, 210 dakika)
- **YDT**: Yabancı Dil Testi (80 soru)
- **KVKK**: Kişisel Verilerin Korunması Kanunu
- **FastAPI**: Python web framework (backend/main.py)
- **PostgreSQL**: İlişkisel veritabanı sistemi
- **Redis**: In-memory cache ve message broker
- **Elasticsearch**: Full-text search engine
- **Docker**: Containerization platform
- **MCP**: Model Context Protocol - AI agent iletişim protokolü

---

## 📋 İçindekiler

1. [Introduction](#introduction)
2. [Glossary](#glossary)
3. [Platform Özeti](#platform-özeti)
4. [Temel Gereksinimler](#temel-gereksinimler)
5. [İçerik Yönetimi](#içerik-yönetimi)
6. [Kalite Kontrol ve Sağlık Denetimi](#kalite-kontrol-ve-sağlık-denetimi)
7. [Öğrenme Yolu Kaynak Kalitesi](#öğrenme-yolu-kaynak-kalitesi)
8. [Bağımlılıklar](#bağımlılıklar)
9. [Kabul Kriterleri Özeti](#kabul-kriterleri-özeti)

---

## Platform Özeti

**Türkiye Üniversite Sınavları Hazırlık Platformu**, YKS (TYT/AYT/YDT) sınavlarına hazırlanan öğrenciler için AI destekli kapsamlı bir eğitim sistemidir. Platform, ÖSYM ve MEB müfredatına tam uyumlu içerikler sunarak öğrencilerin bireysel öğrenme hızlarına göre kişiselleştirilmiş eğitim yolları oluşturur.

### Hedef Kullanıcılar

- **Öğrenciler**: YKS sınavlarına hazırlanan lise öğrencileri (9-12. sınıf)
- **Öğretmenler**: Öğrenci ilerlemesini takip eden ve ödev atayan eğitimciler
- **Veliler**: Çocuklarının eğitim sürecini izleyen aileler
- **Yöneticiler**: Okul ve kurum düzeyinde raporlama yapan eğitim yöneticileri

### İmplementasyon Durumu (Ekim 2025)

**✅ Tamamlanan Sistemler (30+ API Endpoint):**
- ✅ ÖSYM Uyumlu Sınav Motoru (TYT/AYT/YDT)
- ✅ 64 Hibrit Öğrenme Profili Sistemi (VARK × Felder-Silverman)
- ✅ ZPD + MEB Maarif Kültürel Adaptasyon Motoru
- ✅ IRT + Türkçe Morfoloji Analiz Sistemi
- ✅ FSRS Tekrar Sistemi (17 parametre)
- ✅ Multi-Agent Blackboard Koordinasyonu
- ✅ RAG (Retrieval-Augmented Generation) Sistemi
- ✅ BERTurk NLP Entegrasyonu
- ✅ Zemberek-NLP Türkçe Morfolojik Analiz
- ✅ 3 Seviyeli Metin Basitleştirme (Lexical, Syntactic, Semantic)
- ✅ Bionic Reading (Disleksi Desteği)
- ✅ EBA TV İçerik Entegrasyonu
- ✅ YouTube Education API Entegrasyonu
- ✅ Öğretmen Paneli (Sınıf Yönetimi)
- ✅ Veli Takip Sistemi (Haftalık Raporlar)
- ✅ Elasticsearch Full-Text Search
- ✅ Redis Cache Management
- ✅ Production Health Monitoring
- ✅ Advanced Analytics & Reporting
- ✅ Soru CRUD İşlemleri (Rich Text, Image Upload)
- ✅ İçerik Yönetim Sistemi
- ✅ Admin Panel
- ✅ Student Dashboard
- ✅ Enhanced Chat (Bağlamsal Konuşma)
- ✅ Curriculum Compliance (MEB/ÖSYM Uyumluluk)
- ✅ Video Solution System
- ✅ Performance Optimization APIs
- ✅ Token Monitoring & A/B Testing
- ✅ ÖSYM Question Generation (AI-powered)
- ✅ Security & Authentication (JWT, Rate Limiting, CSRF)

### Temel Özellikler

**Sınav ve Değerlendirme:**
- ÖSYM formatında deneme sınavları (TYT/AYT/YDT)
- Gerçek zamanlı performans analizi ve detaylı raporlama
- Konu bazlı zayıf alan tespiti ve özel çalışma önerileri
- IRT tabanlı adaptif soru seçimi
- Sınav performans analizi ve tahminleme

**Yapay Zeka ve Kişiselleştirme:**
- Türkçe NLP destekli AI sohbet asistanı (BERTurk + Zemberek)
- Adaptif öğrenme ve kişiselleştirilmiş içerik sunumu
- 64 hibrit öğrenme profili (VARK × Felder-Silverman)
- Multi-Agent AI koordinasyonu (Blackboard pattern)
- RAG sistemi ile bağlamsal yanıtlar
- Kültürel adaptasyon motoru (8 Türk kültür faktörü)
 
**Devrimsel AI Özellikleri:**
1. **64 Hibrit Öğrenme Profili** (DÜNYADA İLK): VARK × Felder-Silverman kombinasyonu
2. **Türk ZPD Sistemi**: Vygotsky + MEB Maarif değerleri entegrasyonu
3. **IRT + Morfoloji**: 4 parametreli IRT + Zemberek morfolojik analiz
4. **Türk FSRS**: 17 parametreli Türk öğrenci davranışları optimize edilmiş tekrar sistemi
5. **3 Seviyeli Basitleştirme**: Lexical, Syntactic, Semantic metin basitleştirme
6. **Bionic Reading**: Türkçe kök-ek ayrımı ile disleksi desteği
7. **Multi-Agent Blackboard**: Gerçek zamanlı AI agent koordinasyonu

**İçerik ve Entegrasyon:**
- MEB ve ÖSYM müfredatına tam uyumluluk
- EBA TV içerik entegrasyonu (TRT EBA TV)
- YouTube Education API entegrasyonu
- Khan Academy Türkçe desteği
- 2300+ ÖSYM formatında kalibrasyon edilmiş soru bankası
- Elasticsearch ile Türkçe full-text search

**Takip ve Raporlama:**
- Öğretmen dashboard'u ile sınıf yönetimi
- Veli takip sistemi ile haftalık ilerleme raporları
- Ulusal ortalama ile karşılaştırmalı analiz
- Advanced analytics ve export özellikleri
- Token monitoring ve A/B testing

**Teknik Özellikler:**
- Yüksek performans (100K+ eşzamanlı kullanıcı hedefi, <500ms yanıt süresi)
- Redis cache management (cache hit rate %70+ hedef)
- PostgreSQL 15+ database
- Elasticsearch 8+ search engine
- Production health monitoring
- Security: JWT, Rate Limiting, CSRF Protection, Input Validation
- PWA desteği ve offline çalışma modu (planlanan)
- WCAG 2.1 Level AA erişilebilirlik standardı (implementasyon devam ediyor)
- Çoklu cihaz desteği (web, mobil, tablet)

---

## Temel Gereksinimler

## BÖLÜM 1: SINAV SİSTEMİ

### REQ-1: ÖSYM Uyumlu Sınav Sistemi

**İmplementasyon Durumu:** ✅ TAMAMLANDI (api/sinav.py, api/exam_performance.py)

**Kullanıcı Hikayesi:** As a YKS sınavlarına hazırlanan öğrenci, I want gerçek sınav formatında deneme sınavları çözmek ve detaylı performans analizi almak, so that sınav gününde hazırlıklı olabileyim.

#### Kabul Kriterleri

1. **REQ-1.1** ✅ WHEN öğrenci TYT denemesi başlattığında, THE Sınav Sistemi SHALL 120 soru ve 165 dakika süre ile ÖSYM formatında sınav sunar
2. **REQ-1.2** ✅ WHEN öğrenci AYT denemesi başlattığında, THE Sınav Sistemi SHALL 160 soru ve 210 dakika süre ile ÖSYM formatında sınav sunar
3. **REQ-1.3** ✅ WHEN öğrenci YDT denemesi başlattığında, THE Sınav Sistemi SHALL seçilen dil için ÖSYM formatında 80 soruluk sınav sunar
4. **REQ-1.4** ✅ WHEN öğrenci sınavı tamamladığında, THE Sınav Sistemi SHALL 30 saniye içinde detaylı performans analizi ve konu bazlı başarı raporu sunar
5. **REQ-1.5** ✅ WHEN Sınav Sistemi sonuçları analiz ettiğinde, THE Sınav Sistemi SHALL %60 altı başarı gösteren konuları tespit eder ve özel çalışma önerileri sunar
6. **REQ-1.6** ⏳ IF öğrenci sınav sırasında bağlantı kesilirse, THEN THE Sınav Sistemi SHALL her 30 saniyede bir otomatik kayıt yaparak veri kaybını önler

**API Endpoints:**
- `POST /api/sinav/olustur` - Sınav oluşturma
- `POST /api/sinav/{id}/baslat` - Sınav başlatma
- `POST /api/sinav/{id}/cevap` - Cevap gönderme
- `GET /api/sinav/{id}/sonuc` - Sonuç alma
- `GET /api/exam-performance/analysis/{exam_id}` - Detaylı performans analizi

---

### REQ-2: Türkçe NLP ve Sohbet Desteği

**İmplementasyon Durumu:** ✅ TAMAMLANDI (api/zemberek.py, api/berturk_api.py, api/turkish_nlp_chat.py, api/enhanced_chat.py)

**Kullanıcı Hikayesi:** As an öğrenci, I want Türkçe doğal dil işleme ile sorularımı sorabilmek ve anında yanıt alabilmek, so that öğrenme sürecimde takıldığım noktalarda hızlıca yardım alabileyim.

#### Kabul Kriterleri

1. **REQ-2.1** ✅ WHEN öğrenci Türkçe soru sorduğunda, THE NLP Motoru SHALL Zemberek kullanarak morfolojik analiz yapar ve doğru anlam çıkarır
2. **REQ-2.2** ✅ WHEN öğrenci konu hakkında açıklama istediğinde, THE NLP Motoru SHALL MEB onaylı Türkçe eğitim terminolojisi kullanarak 3 saniye içinde yanıt verir
3. **REQ-2.3** ✅ WHEN öğrenci soru çözümü yardımı istediğinde, THE NLP Motoru SHALL minimum 3 adımlı Türkçe açıklama sunar
4. **REQ-2.4** ✅ WHEN NLP Motoru öğrenci mesajında olumsuz duygu tespit ettiğinde, THE NLP Motoru SHALL motivasyonel destek mesajı ekler (BERTurk sentiment analysis)
5. **REQ-2.5** ✅ WHEN öğrenci sohbet geçmişi 1 mesajdan fazla olduğunda, THE NLP Motoru SHALL son 10 mesajı bağlam olarak kullanarak yanıt verir (Enhanced Chat)
6. **REQ-2.6** ✅ IF NLP Motoru öğrenci mesajında dilbilgisi hatası tespit ederse, THEN THE NLP Motoru SHALL nazik bir şekilde düzeltme önerisi sunar (Zemberek spell check)

**API Endpoints:**
- `POST /api/zemberek/analyze` - Morfolojik analiz
- `POST /api/zemberek/tokenize` - Tokenization
- `POST /api/zemberek/spell-check` - Yazım denetimi
- `POST /api/berturk/sentiment` - Duygu analizi
- `POST /api/berturk/intent` - Intent detection
- `POST /api/turkish-nlp-chat/message` - Bağlamsal konuşma
- `POST /api/enhanced-chat/message` - ZPD + Öğrenme Stili entegreli chat

---

### REQ-3: MEB ve ÖSYM Müfredat Uyumluluğu

**Kullanıcı Hikayesi:** As an öğrenci, I want MEB ve ÖSYM müfredatına uyumlu içeriklerle çalışmak, so that sınavda karşılaşacağım konulara tam olarak hazırlanabileyim.

#### Kabul Kriterleri

1. **REQ-3.1** WHEN Platform içerik sunduğunda, THE Platform SHALL MEB müfredat standartlarına uygun konuları içerir
2. **REQ-3.2** WHEN Sınav Sistemi soru bankasına erişildiğinde, THE Sınav Sistemi SHALL her konu için en az 1000 ÖSYM formatında soru sunar
3. **REQ-3.3** WHEN Platform öğrenme kazanımlarını gösterdiğinde, THE Platform SHALL MEB'in belirlediği kazanımlarla %100 eşleşme sağlar
4. **REQ-3.4** WHEN yönetici müfredat güncelleme başlattığında, THE Platform SHALL 24 saat içinde yeni MEB standartlarına uyum sağlar
5. **REQ-3.5** WHEN Adaptif Motor konu sıralaması yaptığında, THE Adaptif Motor SHALL ÖSYM'nin belirlediği öncelik sırasını uygular

---

### REQ-4: Adaptif Öğrenme ve Zorluk Ayarlama

**Kullanıcı Hikayesi:** As an öğrenci, I want performansıma göre zorluk seviyesinin dinamik olarak ayarlandığı adaptif bir öğrenme sistemi, so that hem zorlanmadan hem de sıkılmadan etkili bir şekilde öğrenebileyim.

#### Kabul Kriterleri

1. **REQ-4.1** WHEN öğrenci 3 ardışık soruda %80 üzeri başarı gösterdiğinde, THE Adaptif Motor SHALL zorluk seviyesini 1 kademe artırır
2. **REQ-4.2** WHEN öğrenci 3 ardışık soruda %40 altı başarı gösterdiğinde, THE Adaptif Motor SHALL zorluk seviyesini 1 kademe azaltır ve alternatif açıklamalar sunar
3. **REQ-4.3** WHEN öğrenci öğrenme hızı son 7 günde %30 değiştiğinde, THE Adaptif Motor SHALL içerik sunma hızını otomatik olarak ayarlar
4. **REQ-4.4** WHEN öğrenci belirli konuda 5 soruda %50 altı başarı gösterdiğinde, THE Adaptif Motor SHALL o konuya odaklanan özel çalışma programı oluşturur
5. **REQ-4.5** WHEN Adaptif Motor başarı tahmini yaptığında, THE Adaptif Motor SHALL son 30 günlük performans verisini kullanarak makine öğrenmesi modeli ile tahmin üretir

---

### REQ-5: Çoklu Platform İçerik Entegrasyonu

**Kullanıcı Hikayesi:** As an öğrenci, I want YouTube Education, Khan Academy Türkçe ve EBA TV gibi platformlardan kaliteli eğitim içeriklerine erişmek, so that farklı kaynaklardan zengin içeriklerle öğrenme deneyimimi geliştirebileyim.

#### Kabul Kriterleri

1. **REQ-5.1** WHEN İçerik Entegrasyon Servisi video aradığında, THE İçerik Entegrasyon Servisi SHALL YouTube Data API v3 kullanarak sadece eğitim kanallarını filtreler
2. **REQ-5.2** WHEN İçerik Entegrasyon Servisi yapılandırılmış kurs aradığında, THE İçerik Entegrasyon Servisi SHALL Khan Academy Türkçe API'den uygun içerikleri entegre eder
3. **REQ-5.3** WHEN İçerik Entegrasyon Servisi EBA içerikleri aradığında, THE İçerik Entegrasyon Servisi SHALL TRT EBA TV video linklerini sonuçlara dahil eder
4. **REQ-5.4** WHEN İçerik Entegrasyon Servisi içerikleri sıraladığında, THE İçerik Entegrasyon Servisi SHALL kalite skoru, konu uygunluğu ve öğrenci profiline göre 0-100 arası skor verir
5. **REQ-5.5** WHEN Platform içerik meta verilerini gösterdiğinde, THE Platform SHALL video süresi, zorluk seviyesi (kolay/orta/zor) ve erişilebilirlik özelliklerini (altyazı, transkript) gösterir

---

### REQ-6: Öğretmen ve Veli Takip Sistemi

**Kullanıcı Hikayesi:** As an öğretmen, I want öğrencilerimin bireysel ilerlemelerini takip edebilmek ve sınıf geneli performans raporları alabilmek, so that eğitim sürecini daha etkili yönetebileyim ve velilerle işbirliği yapabileyim.

#### Kabul Kriterleri

1. **REQ-6.1** WHEN öğretmen Öğretmen Dashboard'da öğrenci listesini görüntülediğinde, THE Öğretmen Dashboard SHALL her öğrencinin son 24 saat içindeki ilerleme durumunu gösterir
2. **REQ-6.2** WHEN öğretmen sınıf raporu istediğinde, THE Öğretmen Dashboard SHALL konu bazlı başarı dağılımını grafik ve tablo formatında sunar
3. **REQ-6.3** WHEN öğretmen ödev oluşturduğunda, THE Sınav Sistemi SHALL seçilen konu ve zorluk seviyesine göre ÖSYM müfredatından otomatik soru seçer
4. **REQ-6.4** WHEN veli Veli Paneli'nden haftalık rapor istediğinde, THE Veli Paneli SHALL çocuğun son 7 günlük çalışma süresi, başarı oranı ve zayıf konuları içeren rapor sunar
5. **REQ-6.5** WHEN Öğretmen Dashboard performans karşılaştırması yaptığında, THE Öğretmen Dashboard SHALL öğrenci performansını sınıf ortalaması, okul ortalaması ve ulusal ortalama ile karşılaştırır

---

### REQ-7: Yüksek Performans ve Ölçeklenebilirlik

**Kullanıcı Hikayesi:** As a platform kullanıcısı, I want 100.000+ eşzamanlı kullanıcı olsa bile 200ms altında yanıt alabilmek, so that kesintisiz ve akıcı bir öğrenme deneyimi yaşayabileyim.

#### Kabul Kriterleri

1. **REQ-7.1** WHEN Platform yükü arttığında, THE Platform SHALL p95 yanıt süresini 200ms altında tutar
2. **REQ-7.2** WHEN Platform 100.000 eşzamanlı kullanıcıya hizmet verdiğinde, THE Platform SHALL %99.9 uptime ile stabil çalışır
3. **REQ-7.3** WHEN Platform uptime 30 günlük periyotta ölçüldüğünde, THE Platform SHALL minimum %99.9 kullanılabilirlik sağlar
4. **REQ-7.4** WHEN Platform Türkçe karakter işlediğinde, THE Platform SHALL UTF-8 encoding kullanarak tüm karakterleri doğru görüntüler
5. **REQ-7.5** WHEN kullanıcı mobil cihazdan eriştiğinde, THE Platform SHALL 320px-2560px arası tüm ekran boyutlarında responsive çalışır
6. **REQ-7.6** IF Platform CPU veya RAM kullanımı %80'e ulaşırsa, THEN THE Platform SHALL 60 saniye içinde otomatik ölçeklendirme başlatır

---

### REQ-8: Offline Çalışma ve PWA Desteği

**Kullanıcı Hikayesi:** As an öğrenci, I want internet bağlantısı olmadığında bile indirdiğim içeriklerle çalışabilmek, so that her koşulda öğrenme sürecimi devam ettirebilleyim.

#### Kabul Kriterleri

1. **REQ-8.1** WHEN öğrenci offline modda çalıştığında, THE PWA SHALL önceden indirilen tüm içeriklere tam erişim sağlar
2. **REQ-8.2** WHEN PWA cihaza yüklendiğinde, THE PWA SHALL native uygulama gibi tam ekran modda çalışır
3. **REQ-8.3** WHEN öğrenci offline modda soru çözdüğünde, THE PWA SHALL yanıtları IndexedDB'de saklar ve bağlantı geldiğinde senkronize eder
4. **REQ-8.4** WHEN internet bağlantısı geri geldiğinde, THE PWA SHALL 10 saniye içinde offline verileri otomatik senkronize eder
5. **REQ-8.5** WHEN offline içerik sunucuda güncellendiğinde, THE PWA SHALL kullanıcıya bildirim gösterir ve güncelleme seçeneği sunar

---

### REQ-9: Erişilebilirlik ve Kapsayıcı Tasarım

**Kullanıcı Hikayesi:** As a görme engelli öğrenci, I want ekran okuyucu teknolojileri ile platformu tam olarak kullanabilmek, so that eğitim fırsatlarından eşit şekilde yararlanabileyim.

#### Kabul Kriterleri

1. **REQ-9.1** WHEN Platform görsel içerik sunduğunda, THE Platform SHALL her görselde WCAG uyumlu alternatif metin (alt text) sağlar
2. **REQ-9.2** WHEN Platform matematiksel formül gösterdiğinde, THE Platform SHALL MathML veya ARIA-label ile ekran okuyucu uyumlu format sunar
3. **REQ-9.3** WHEN öğrenci video içerik izlediğinde, THE Platform SHALL Türkçe altyazı ve tam transkript sağlar
4. **REQ-9.4** WHEN kullanıcı sadece klavye ile navigasyon yaptığında, THE Platform SHALL Tab, Enter, Space tuşları ile tüm özelliklere erişim sağlar
5. **REQ-9.5** WHEN Platform WCAG 2.1 Level AA otomatik test araçları ile kontrol edildiğinde, THE Platform SHALL %100 uyumluluk skoru alır

---

### REQ-10: Devrimsel AI Özellikler Sistemi

**Kullanıcı Hikayesi:** As an öğrenci, I want dünya çapında benzersiz AI teknolojileri ile kişiselleştirilmiş ve etkili bir öğrenme deneyimi yaşamak, so that maksimum verimlilikle öğrenebileyim ve sınav başarımı artırabileyim.

#### Kabul Kriterleri

1. **REQ-10.1** WHEN öğrenme stili tespiti yapıldığında THEN VARK + Felder-Silverman hibrit sistemi 64 farklı profil sunmalı
2. **REQ-10.2** WHEN zorluk seviyesi ayarlandığında THEN Türk ZPD + MEB Maarif modeli kültürel faktörleri dikkate almalı
3. **REQ-10.3** WHEN soru analizi yapıldığında THEN Türkçe Morfoloji IRT sistemi ÖSYM/ETS standartlarını aşmalı
4. **REQ-10.4** WHEN tekrar zamanlaması hesaplandığında THEN Türk FSRS sistemi 17 parametre ile optimize edilmeli
5. **REQ-10.5** WHEN metin basitleştirme istendiğinde THEN 3 seviyeli sistem (lexical, syntactic, semantic) çalışmalı
6. **REQ-10.6** WHEN disleksi desteği aktifleştirildiğinde THEN Türkçe Bionic Reading kök-ek ayrımı yapmalı
7. **REQ-10.7** WHEN AI agentlar çalıştığında THEN Multi-Agent Blackboard gerçek zamanlı koordinasyon sağlamalı

---

### REQ-11: Gerçek Zamanlı İletişim ve Koordinasyon

**Kullanıcı Hikayesi:** As an öğrenci, I want AI agentların birbirleriyle koordineli çalışarak bana en iyi öğrenme deneyimini sunmasını, so that tutarlı ve optimize edilmiş bir eğitim süreci yaşayabileyim.

#### Kabul Kriterleri

1. **REQ-11.1** WHEN bir agent keşif yaptığında THEN diğer agentlar anında bilgilendirilmeli
2. **REQ-11.2** WHEN öğrenme stili tespit edildiğinde THEN tüm agentlar bu bilgiyi kullanarak adapte olmalı
3. **REQ-11.3** WHEN performans verisi güncellendiğinde THEN agentlar koordineli şekilde tepki vermeli
4. **REQ-11.4** WHEN WebSocket bağlantısı kurulduğunda THEN gerçek zamanlı agent iletişimi başlamalı
5. **REQ-11.5** WHEN blackboard'a veri yazıldığında THEN abone agentlar 100ms içinde bildirim almalı
6. **REQ-11.6** IF agent arası iletişim kesilirse THEN sistem otomatik yeniden bağlantı kurmalı

---

### REQ-12: Türkçe Dil İşleme ve Kültürel Adaptasyon

**Kullanıcı Hikayesi:** As a Türk öğrenci, I want Türkçe'nin zengin yapısını anlayan ve Türk kültürüne uygun bir sistem kullanmak, so that kendi dilim ve kültürümle uyumlu bir öğrenme deneyimi yaşayabileyim.

#### Kabul Kriterleri

1. **REQ-12.1** WHEN Türkçe metin analiz edildiğinde THEN Zemberek NLP morfolojik analiz yapmalı
2. **REQ-12.2** WHEN karmaşık kelimeler tespit edildiğinde THEN ek sayısı ve türetim derinliği hesaplanmalı
3. **REQ-12.3** WHEN kültürel dönemler (Ramazan, sınav dönemi) olduğunda THEN sistem davranışı adapte olmalı
4. **REQ-12.4** WHEN grup çalışması tercihi yüksek olduğunda THEN ZPD aralığı genişletilmeli
5. **REQ-12.5** WHEN Osmanlıca/akademik kelimeler bulunduğunda THEN modern Türkçe karşılıkları önerilmeli
6. **REQ-12.6** IF öğrenci bölgesel lehçe kullanırsa THEN sistem standart Türkçe'ye çeviri desteği sunmalı

---

## BÖLÜM 2: İÇERİK YÖNETİMİ

### REQ-13: Makale İçerik Yönetimi

**Kullanıcı Hikayesi:** Öğretmen olarak, öğrencilerime eğitim makaleleri oluşturmak, düzenlemek ve paylaşmak istiyorum, böylece onlara kaliteli yazılı içerik sunabilirim.

#### Kabul Kriterleri

1. **REQ-13.1** WHEN öğretmen yeni makale oluşturmak istediğinde THEN sistem başlık, içerik, kategori ve yazar bilgilerini almalı
2. **REQ-13.2** WHEN makale içeriği girildiğinde THEN sistem otomatik olarak özet, okunma süresi ve etiketler oluşturmalı
3. **REQ-13.3** WHEN makale kaydedildiğinde THEN sistem benzersiz ID atamalı ve yayınlanma tarihini kaydetmeli
4. **REQ-13.4** WHEN öğrenci makaleyi görüntülediğinde THEN sistem görüntüleme sayısını artırmalı
5. **REQ-13.5** IF makale sahibi veya admin ise THEN kullanıcı makaleyi güncelleyebilmeli
6. **REQ-13.6** WHEN makale silindiğinde THEN sistem soft delete yapmalı (kalıcı silme değil)
7. **REQ-13.7** WHEN kullanıcı makaleyi beğendiğinde THEN sistem beğeni sayısını güncellemeli

---

### REQ-14: Video İçerik Yönetimi

**Kullanıcı Hikayesi:** Öğretmen olarak, öğrencilerime video içerikleri eklemek ve yönetmek istiyorum, böylece görsel öğrenmeyi destekleyebilirim.

#### Kabul Kriterleri

1. **REQ-14.1** WHEN öğretmen video eklemek istediğinde THEN sistem video URL'ini doğrulamalı
2. **REQ-14.2** WHEN geçerli video URL'i girildiğinde THEN sistem otomatik olarak video süresini almalı
3. **REQ-14.3** WHEN video kaydedildiğinde THEN sistem arka planda thumbnail oluşturmalı
4. **REQ-14.4** WHEN öğrenci videoyu izlediğinde THEN sistem izlenme sayısını artırmalı
5. **REQ-14.5** WHEN video listesi istendiğinde THEN sistem süre filtresi (min/max) sunmalı
6. **REQ-14.6** IF video sahibi veya yetkili kullanıcı ise THEN video bilgileri güncellenebilmeli

---

### REQ-15: İçerik Arama ve Filtreleme

**Kullanıcı Hikayesi:** Öğrenci olarak, ihtiyacım olan içerikleri hızlıca bulabilmek istiyorum, böylece zamanımı verimli kullanabilirim.

#### Kabul Kriterleri

1. **REQ-15.1** WHEN kullanıcı arama terimi girdiğinde THEN sistem tüm içerik tiplerinde arama yapmalı
2. **REQ-15.2** WHEN arama sonuçları gösterildiğinde THEN sistem başlık ve içerik metninde eşleşmeleri vurgulamalı
3. **REQ-15.3** WHEN filtreleme yapıldığında THEN sistem kategori, tarih aralığı ve içerik tipine göre filtrelemeli
4. **REQ-15.4** WHEN sayfalama kullanıldığında THEN sistem skip ve limit parametrelerini desteklemeli
5. **REQ-15.5** IF arama sonucu yoksa THEN sistem anlamlı mesaj göstermeli

---

### REQ-16: Kişiselleştirilmiş İçerik Önerileri

**Kullanıcı Hikayesi:** Öğrenci olarak, öğrenme stilime ve seviyeme uygun içerik önerileri almak istiyorum, böylece daha etkili öğrenebilirim.

#### Kabul Kriterleri

1. **REQ-16.1** WHEN öğrenci öneriler sayfasını ziyaret ettiğinde THEN sistem kişiselleştirilmiş öneriler sunmalı
2. **REQ-16.2** WHEN öğrenci profili analiz edildiğinde THEN sistem öğrenme geçmişini ve tercihlerini dikkate almalı
3. **REQ-16.3** WHEN kategori belirtildiğinde THEN sistem o kategoriye özel öneriler getirmeli
4. **REQ-16.4** WHEN yeni kullanıcı için öneri istendiğinde THEN sistem genel popüler içerikleri önermeli
5. **REQ-16.5** IF öğrenci etkileşim geçmişi varsa THEN sistem benzer içerikleri önceliklemeli

---

### REQ-17: Trend ve İstatistik Analizi

**Kullanıcı Hikayesi:** Yönetici olarak, platform üzerindeki içerik performansını ve kullanım trendlerini görmek istiyorum, böylece veri odaklı kararlar alabilirim.

#### Kabul Kriterleri

1. **REQ-17.1** WHEN yönetici istatistikleri görüntülediğinde THEN sistem toplam içerik sayılarını göstermeli
2. **REQ-17.2** WHEN trend analizi istendiğinde THEN sistem günlük, haftalık, aylık trendleri sunmalı
3. **REQ-17.3** WHEN içerik performansı analiz edildiğinde THEN sistem görüntüleme, beğeni ve etkileşim verilerini göstermeli
4. **REQ-17.4** WHEN kategori bazlı analiz yapıldığında THEN sistem kategori dağılımını ve performansını göstermeli
5. **REQ-17.5** IF yetkisiz kullanıcı istatistiklere erişmeye çalışırsa THEN sistem erişimi engellemeli

---

### REQ-18: Toplu İçerik Yükleme

**Kullanıcı Hikayesi:** Yönetici olarak, çok sayıda içeriği tek seferde yükleyebilmek istiyorum, böylece manuel işlem yükünü azaltabilirim.

#### Kabul Kriterleri

1. **REQ-18.1** WHEN yönetici CSV veya JSON dosyası yüklediğinde THEN sistem dosya formatını doğrulamalı
2. **REQ-18.2** WHEN toplu yükleme başlatıldığında THEN sistem arka planda işleme almalı
3. **REQ-18.3** WHEN yükleme devam ederken THEN sistem ilerleme durumunu takip edilebilir hale getirmeli
4. **REQ-18.4** WHEN hatalı veri tespit edildiğinde THEN sistem detaylı hata raporu sunmalı
5. **REQ-18.5** IF yükleme tamamlandığında THEN sistem başarı/başarısızlık özetini göstermeli

---

### REQ-19: Cache ve Performans Optimizasyonu

**Kullanıcı Hikayesi:** Platform kullanıcısı olarak, içeriklerin hızlı yüklenmesini istiyorum, böylece kesintisiz bir deneyim yaşayabilirim.

#### Kabul Kriterleri

1. **REQ-19.1** WHEN sık erişilen içerikler istendiğinde THEN sistem cache'den sunmalı
2. **REQ-19.2** WHEN içerik güncellendiğinde THEN sistem ilgili cache'i temizlemeli
3. **REQ-19.3** WHEN yeni içerik oluşturulduğunda THEN sistem arka planda indexleme yapmalı
4. **REQ-19.4** WHEN büyük listeler istendiğinde THEN sistem sayfalama kullanmalı
5. **REQ-19.5** IF cache süresi dolmuşsa THEN sistem otomatik olarak yenilemeli

---

### REQ-20: İçerik Güvenliği ve Yetkilendirme

**Kullanıcı Hikayesi:** Platform yöneticisi olarak, içeriklerin güvenli bir şekilde yönetilmesini istiyorum, böylece yetkisiz erişimleri engelleyebilirim.

#### Kabul Kriterleri

1. **REQ-20.1** WHEN kullanıcı içerik oluşturmaya çalıştığında THEN sistem yetki kontrolü yapmalı
2. **REQ-20.2** WHEN içerik düzenleme işlemi yapıldığında THEN sistem sahiplik veya admin yetkisi kontrolü yapmalı
3. **REQ-20.3** WHEN silme işlemi gerçekleştirildiğinde THEN sistem sadece yetkili kullanıcılara izin vermeli
4. **REQ-20.4** WHEN hassas işlemler yapıldığında THEN sistem audit log tutmalı
5. **REQ-20.5** IF yetkisiz erişim tespit edilirse THEN sistem güvenlik uyarısı vermeli

---

## BÖLÜM 3: ÖĞRENME YOLU KAYNAK KALİTESİ

### REQ-21: Türkçe İçerik Garantisi

**Kullanıcı Hikayesi:** Öğrenci olarak, öğrenme yolumda önerilen tüm videoların Türkçe olmasını istiyorum, böylece içeriği tam olarak anlayabilirim.

#### Kabul Kriterleri

1. **REQ-21.1** WHEN ResourceRecommendationEngine bir video önerisi oluşturduğunda, THE TurkishContentFilter SHALL video başlığını ve açıklamasını Türkçe dil kontrolünden geçirir
2. **REQ-21.2** WHEN TurkishContentFilter bir videoyu analiz ettiğinde, THE TurkishContentFilter SHALL video kanalının Türkçe eğitim kanalları listesinde olup olmadığını kontrol eder
3. **REQ-21.3** WHEN bir video Türkçe olmadığı tespit edildiğinde, THE ResourceRecommendationEngine SHALL bu videoyu öneri listesinden çıkarır
4. **REQ-21.4** WHEN TurkishContentFilter Türkçe skorunu hesapladığında, THE TurkishContentFilter SHALL minimum %70 Türkçe skoru olan videoları kabul eder
5. **REQ-21.5** WHEN öğrenci "Size Özel Kaynaklar" bölümünü görüntülediğinde, THE LearningPathSystem SHALL sadece Türkçe onaylı videoları gösterir

---

### REQ-22: Konu Uygunluğu Doğrulaması

**Kullanıcı Hikayesi:** Öğrenci olarak, önerilen videoların çalıştığım ders ve konuyla tam uyumlu olmasını istiyorum, böylece zamanımı boşa harcamam.

#### Kabul Kriterleri

1. **REQ-22.1** WHEN SubjectRelevanceScorer bir videoyu değerlendirdiğinde, THE SubjectRelevanceScorer SHALL video başlığı ve açıklamasını öğrenci profilindeki ders ve konu ile karşılaştırır
2. **REQ-22.2** WHEN SemanticMatcher konu uygunluğunu hesapladığında, THE SemanticMatcher SHALL embedding tabanlı semantik benzerlik skoru hesaplar
3. **REQ-22.3** WHEN bir videonun konu uygunluk skoru %60'ın altında olduğunda, THE ResourceRecommendationEngine SHALL bu videoyu öneri listesinden çıkarır
4. **REQ-22.4** WHEN ResourceRecommendationEngine video sıralaması yaptığında, THE ResourceRecommendationEngine SHALL konu uygunluk skorunu öncelikli sıralama kriteri olarak kullanır
5. **REQ-22.5** WHEN öğrenci bir modül için video önerileri aldığında, THE LearningPathSystem SHALL modülün konusu ile %80 üzeri uyumlu videoları önceliklendirir

---

### REQ-23: Video Erişilebilirlik Kontrolü

**Kullanıcı Hikayesi:** Öğrenci olarak, önerilen videoların çalışır durumda olmasını istiyorum, böylece kırık linklerle zaman kaybetmem.

#### Kabul Kriterleri

1. **REQ-23.1** WHEN VideoQualityValidator bir video önerisi aldığında, THE VideoQualityValidator SHALL videonun YouTube'da erişilebilir olup olmadığını kontrol eder
2. **REQ-23.2** WHEN bir video erişilemez durumda tespit edildiğinde, THE ResourceRecommendationEngine SHALL bu videoyu öneri listesinden çıkarır ve alternatif video arar
3. **REQ-23.3** WHEN YouTubeIntegrationService video metadata'sını çektiğinde, THE YouTubeIntegrationService SHALL videonun gömülebilir (embeddable) olup olmadığını doğrular
4. **REQ-23.4** WHEN VideoQualityValidator video kalitesini değerlendirdiğinde, THE VideoQualityValidator SHALL videonun yayın durumunu (public/private/unlisted) kontrol eder
5. **REQ-23.5** WHEN öğrenci bir videoyu oynatmaya çalıştığında, THE LearningPathSystem SHALL sadece erişilebilir ve gömülebilir videoları gösterir

---

### REQ-24: Öneri Kalite Metrikleri

**Kullanıcı Hikayesi:** Öğrenci olarak, en kaliteli ve güvenilir eğitim videolarını görmek istiyorum, böylece doğru bilgi edinebilirim.

#### Kabul Kriterleri

1. **REQ-24.1** WHEN ResourceRecommendationEngine video skorlaması yaptığında, THE ResourceRecommendationEngine SHALL kanal güvenilirliği, görüntülenme sayısı ve beğeni oranını hesaba katar
2. **REQ-24.2** WHEN bir video güvenilir eğitim kanallarından birinden geldiğinde, THE ResourceRecommendationEngine SHALL bu videoya %20 bonus skor ekler
3. **REQ-24.3** WHEN VideoQualityValidator video süresini kontrol ettiğinde, THE VideoQualityValidator SHALL 5-60 dakika arası videoları ideal olarak değerlendirir
4. **REQ-24.4** WHEN bir videonun altyazı desteği olduğu tespit edildiğinde, THE ResourceRecommendationEngine SHALL bu videoya %10 bonus skor ekler
5. **REQ-24.5** WHEN öğrenci video önerilerini görüntülediğinde, THE LearningPathSystem SHALL videoları toplam kalite skoruna göre sıralı olarak gösterir

---

### REQ-25: Gerçek Zamanlı Doğrulama

**Kullanıcı Hikayesi:** Öğrenci olarak, öğrenme yolum her yüklendiğinde güncel ve çalışan videoların gösterilmesini istiyorum.

#### Kabul Kriterleri

1. **REQ-25.1** WHEN öğrenci learning path sayfasını açtığında, THE LearningPathSystem SHALL video önerilerini gerçek zamanlı olarak doğrular
2. **REQ-25.2** WHEN VideoQualityValidator toplu video kontrolü yaptığında, THE VideoQualityValidator SHALL maksimum 5 saniye içinde sonuç döner
3. **REQ-25.3** WHEN bir video doğrulama başarısız olduğunda, THE ResourceRecommendationEngine SHALL önbellekten (cache) alternatif video önerir
4. **REQ-25.4** WHEN YouTubeIntegrationService API limitine ulaştığında, THE YouTubeIntegrationService SHALL fallback mekanizmasını devreye sokar
5. **REQ-25.5** WHEN sistem video önerilerini güncellerken, THE LearningPathSystem SHALL kullanıcıya yükleme göstergesi gösterir

---

## BÖLÜM 4: PROJE SAĞLIK DENETİMİ

### REQ-26: Backend API Durum Kontrolü

**Kullanıcı Hikayesi:** Bir geliştirici olarak, tüm backend API endpoint'lerinin çalışır durumda olmasını istiyorum, böylece frontend entegrasyonu sorunsuz çalışabilir.

#### Kabul Kriterleri

1. **REQ-26.1** THE Denetim Sistemi SHALL tanımlı her API endpoint için HTTP durum kodu kaydetmek
2. **REQ-26.2** THE Denetim Sistemi SHALL her API endpoint için yanıt süresini milisaniye cinsinden ölçmek
3. **REQ-26.3** IF bir endpoint 500 milisaniyeden uzun yanıt verirse, THEN THE Denetim Sistemi SHALL performans uyarısı üretmek
4. **REQ-26.4** IF bir endpoint 400 ile 599 arasında HTTP durum kodu döndürürse, THEN THE Denetim Sistemi SHALL hata detayını log dosyasına yazmak
5. **REQ-26.5** THE Denetim Sistemi SHALL son 30 günde çağrılmamış endpoint'leri tespit etmek

---

### REQ-27: AI Agent Modül Yükleme Kontrolü

**Kullanıcı Hikayesi:** As a sistem yöneticisi, I want AI agent modüllerinin yüklenebilir olduğunu bilmek, so that sistemin AI yeteneklerinin çalışır durumda olduğundan emin olabilirim.

#### Kabul Kriterleri

1. **REQ-27.1** THE Denetim Sistemi SHALL LearningPathAgent modülünün import edilebilir olduğunu doğrular
2. **REQ-27.2** THE Denetim Sistemi SHALL StudyAgent modülünün import edilebilir olduğunu doğrular
3. **REQ-27.3** THE Denetim Sistemi SHALL ExamAgent modülünün import edilebilir olduğunu doğrular
4. **REQ-27.4** WHEN Denetim Sistemi bir AI Agent'ı çağırdığında, THE Denetim Sistemi SHALL yanıt süresini milisaniye cinsinden kaydeder
5. **REQ-27.5** IF bir AI Agent import hatası üretirse, THEN THE Denetim Sistemi SHALL hata mesajını raporlar

---

### REQ-28: Dış Servis API Bağlantı Kontrolü

**Kullanıcı Hikayesi:** As a sistem yöneticisi, I want dış servis entegrasyonlarının çalıştığını bilmek, so that platform'un dış kaynaklarla bağlantısının sağlıklı olduğundan emin olabilirim.

#### Kabul Kriterleri

1. **REQ-28.1** THE Denetim Sistemi SHALL YouTube API bağlantısının aktif olduğunu doğrular
2. **REQ-28.2** THE Denetim Sistemi SHALL EBA TV API bağlantısının aktif olduğunu doğrular
3. **REQ-28.3** THE Denetim Sistemi SHALL Wikipedia API bağlantısının aktif olduğunu doğrular
4. **REQ-28.4** WHEN Denetim Sistemi bir dış API'yi test ettiğinde, THE Denetim Sistemi SHALL yanıt süresini milisaniye cinsinden kaydeder
5. **REQ-28.5** IF bir dış API 3 saniye içinde yanıt vermezse, THEN THE Denetim Sistemi SHALL timeout uyarısı üretir

---

### REQ-29: Veritabanı Bağlantı Kontrolü

**Kullanıcı Hikayesi:** As a veritabanı yöneticisi, I want veritabanı bağlantılarının sağlıklı olduğunu görmek, so that veri erişiminin kesintisiz çalıştığından emin olabilirim.

#### Kabul Kriterleri

1. **REQ-29.1** THE Denetim Sistemi SHALL PostgreSQL bağlantı havuzunun aktif olduğunu doğrular
2. **REQ-29.2** THE Denetim Sistemi SHALL Redis cache bağlantısının aktif olduğunu doğrular
3. **REQ-29.3** THE Denetim Sistemi SHALL Elasticsearch bağlantısının aktif olduğunu doğrular
4. **REQ-29.4** THE Denetim Sistemi SHALL Redis cache hit oranını yüzde olarak hesaplar
5. **REQ-29.5** IF cache hit oranı yüzde 70'den düşükse, THEN THE Denetim Sistemi SHALL performans uyarısı üretir

---

### REQ-30 - REQ-46: Güvenlik, Performans, Monitoring Kontrolleri

*(Kısalık için sadece kritik gereksinimler gösterilmiştir. Tam liste 47 gereksinime kadar devam eder)*

**REQ-30**: Frontend-Backend CORS Kontrolü
**REQ-31**: Güvenlik Kontrolleri (Rate limiting, encryption, HTTPS)
**REQ-32**: Test Coverage Analizi
**REQ-33**: API Dokümantasyon Kontrolü
**REQ-34**: Docker Container Kontrolü
**REQ-35**: Performans Metrikleri
**REQ-36**: Logging Sistemi Kontrolü
**REQ-37**: WebSocket Bağlantı Kontrolü
**REQ-38**: Authentication Token Kontrolü
**REQ-39**: Database Migration Kontrolü
**REQ-40**: Health Check Endpoint Kontrolü
**REQ-41**: Monitoring Sistemi Kontrolü
**REQ-42**: Cache Stratejisi Kontrolü
**REQ-43**: Database Query Performansı
**REQ-44**: Integration Test Kontrolü
**REQ-45**: Security Hardening (SQL Injection, XSS, etc.)
**REQ-46**: Audit Trail ve Compliance

### REQ-47: Rapor Oluşturma

**Kullanıcı Hikayesi:** As a proje yöneticisi, I want denetim sonuçlarının raporunu görmek, so that platform sağlığını değerlendirebilir ve gerekli aksiyonları alabilirim.

#### Kabul Kriterleri

1. **REQ-47.1** THE Denetim Sistemi SHALL tüm test sonuçlarını içeren HTML raporu oluşturur
2. **REQ-47.2** THE Denetim Sistemi SHALL başarılı test sayısını raporlar
3. **REQ-47.3** THE Denetim Sistemi SHALL başarısız test sayısını raporlar
4. **REQ-47.4** THE Denetim Sistemi SHALL uyarı sayısını raporlar
5. **REQ-47.5** THE Denetim Sistemi SHALL kritik hata sayısını raporlar
6. **REQ-47.6** THE Denetim Sistemi SHALL genel sağlık skorunu yüzde olarak hesaplar
7. **REQ-47.7** THE Denetim Sistemi SHALL raporu JSON formatında dışa aktarır
8. **REQ-47.8** THE Denetim Sistemi SHALL raporu timestamp ile kaydeder

---

## BÖLÜM 5: GELİŞMİŞ AI ÖZELLİKLERİ

### REQ-48: LLM Tabanlı ÖSYM Soru Üretim Sistemi

**Kullanıcı Hikayesi:** Bir içerik yöneticisi olarak, yapay zeka ile otomatik ÖSYM formatında soru üretmek istiyorum, böylece soru bankasını hızlıca genişletebilirim ve kaliteli sorular oluşturabilirim.

#### Kabul Kriterleri

**Veri Toplama ve Analiz (REQ-48.1 - REQ-48.16)**

1. **REQ-48.1** WHEN Soru Scraper 2014-2024 arası ÖSYM sorularını topladığında, THE Soru Scraper SHALL her soruyu benzersiz ID ile veritabanına kaydetmek
2. **REQ-48.2** WHEN Soru Parser bir ÖSYM sorusunu işlediğinde, THE Soru Parser SHALL soru gövdesini (stem) doğru şekilde çıkarmak
3. **REQ-48.3** WHEN Soru Parser doğru cevabı tespit ettiğinde, THE Soru Parser SHALL key (doğru cevap) bilgisini kaydetmek
4. **REQ-48.4** WHEN Soru Parser çeldiricileri ayırdığında, THE Soru Parser SHALL tüm distractor'ları ayrı ayrı kaydetmek
5. **REQ-48.5** WHEN Soru Parser metadata çıkardığında, THE Soru Parser SHALL konu, alt konu ve zorluk seviyesini tespit etmek
6. **REQ-48.6** WHEN Soru Parser bir soruyu işlediğinde, THE Soru Parser SHALL ÖSYM soru formatına %100 uygunluk sağlamak
7. **REQ-48.7** WHEN Soru Parser görsel içeren soru işlediğinde, THE Soru Parser SHALL görsel referanslarını doğru şekilde kaydetmek
8. **REQ-48.8** WHEN Soru Parser matematiksel formül tespit ettiğinde, THE Soru Parser SHALL LaTeX formatında kaydetmek
9. **REQ-48.9** WHEN Bloom Sınıflandırıcı bir soruyu analiz ettiğinde, THE Bloom Sınıflandırıcı SHALL 6 seviyeli Bloom taksonomisine göre sınıflandırmak
10. **REQ-48.10** WHEN Bloom Sınıflandırıcı ML modeli eğitildiğinde, THE Bloom Sınıflandırıcı SHALL minimum %85 doğruluk oranı sağlamak
11. **REQ-48.11** WHEN Bloom Sınıflandırıcı soru seviyesi tespit ettiğinde, THE Bloom Sınıflandırıcı SHALL bilgi, kavrama, uygulama, analiz, sentez, değerlendirme seviyelerini ayırt etmek
12. **REQ-48.12** WHEN Bloom Sınıflandırıcı otomatik tespit yaptığında, THE Bloom Sınıflandırıcı SHALL confidence score (güven skoru) %70 üzerinde olmak
13. **REQ-48.13** WHEN IRT Parametre Tahmin Modeli çalıştığında, THE IRT Modeli SHALL 4 parametreli IRT modelini kullanmak
14. **REQ-48.14** WHEN IRT Modeli difficulty (b) parametresini hesapladığında, THE IRT Modeli SHALL -3 ile +3 arasında değer üretmek
15. **REQ-48.15** WHEN IRT Modeli discrimination (a) parametresini hesapladığında, THE IRT Modeli SHALL 0 ile 2 arasında değer üretmek
16. **REQ-48.16** WHEN IRT Modeli guessing (c) ve upper asymptote (d) parametrelerini hesapladığında, THE IRT Modeli SHALL 0 ile 1 arasında değer üretmek

**NLP Model Training (REQ-48.17 - REQ-48.32)**

17. **REQ-48.17** WHEN GPT-4 Fine-tuning başlatıldığında, THE Fine-tuning Sistemi SHALL OpenAI API kullanarak model eğitmek
18. **REQ-48.18** WHEN Training Data hazırlandığında, THE Fine-tuning Sistemi SHALL ÖSYM formatına uygun örnekler kullanmak
19. **REQ-48.19** WHEN Hyperparameter Tuning yapıldığında, THE Fine-tuning Sistemi SHALL learning rate, batch size ve epoch sayısını optimize etmek
20. **REQ-48.20** WHEN Model Evaluation yapıldığında, THE Fine-tuning Sistemi SHALL BLEU, ROUGE ve BERTScore metriklerini hesaplamak
21. **REQ-48.21** WHEN BERTurk Embedding Modeli yüklendiğinde, THE BERTurk Sistemi SHALL Türkçe pre-trained model kullanmak
22. **REQ-48.22** WHEN Sentence Embedding oluşturulduğunda, THE BERTurk Sistemi SHALL 768 boyutlu vektör üretmek
23. **REQ-48.23** WHEN Semantic Similarity hesaplandığında, THE BERTurk Sistemi SHALL cosine similarity kullanmak
24. **REQ-48.24** WHEN Semantic Similarity skoru hesaplandığında, THE BERTurk Sistemi SHALL 0 ile 1 arasında değer döndürmek
25. **REQ-48.25** WHEN T5 Generation Modeli çalıştığında, THE T5 Modeli SHALL Türkçe soru üretimi için optimize edilmiş olmak
26. **REQ-48.26** WHEN BART Paraphrasing yapıldığında, THE BART Modeli SHALL anlam korunarak farklı ifadeler üretmek
27. **REQ-48.27** WHEN Beam Search Optimization uygulandığında, THE Generation Modeli SHALL en iyi 5 alternatifi değerlendirmek
28. **REQ-48.28** WHEN Generation Modeli soru ürettiğinde, THE Generation Modeli SHALL ÖSYM formatına %95 uygunluk sağlamak
29. **REQ-48.29** WHEN RLHF Training Loop başlatıldığında, THE RLHF Sistemi SHALL insan geri bildirimlerini kullanmak
30. **REQ-48.30** WHEN Reward Model eğitildiğinde, THE Reward Model SHALL soru kalitesini 0-100 arası skorlamak
31. **REQ-48.31** WHEN PPO Algorithm uygulandığında, THE RLHF Sistemi SHALL policy gradient optimization kullanmak
32. **REQ-48.32** WHEN RLHF tamamlandığında, THE RLHF Sistemi SHALL model performansını %20 artırmak

**Soru Üretim Motoru (REQ-48.33 - REQ-48.48)**

33. **REQ-48.33** WHEN Konu Bazlı Üretim yapıldığında, THE Soru Üretim Motoru SHALL MEB müfredatına uygun konuları kullanmak
34. **REQ-48.34** WHEN Context Injection yapıldığında, THE Soru Üretim Motoru SHALL konu bağlamını prompt'a eklemek
35. **REQ-48.35** WHEN Question Template kullanıldığında, THE Soru Üretim Motoru SHALL ÖSYM soru yapısını taklit etmek
36. **REQ-48.36** WHEN Soru üretildiğinde, THE Soru Üretim Motoru SHALL 3 saniye içinde sonuç döndürmek
37. **REQ-48.37** WHEN Distractor Generation başlatıldığında, THE Distractor Sistemi SHALL plausible (makul) çeldiriciler üretmek
38. **REQ-48.38** WHEN Common Misconception Database kullanıldığında, THE Distractor Sistemi SHALL yaygın öğrenci hatalarını içermek
39. **REQ-48.39** WHEN Distractor Quality skorlandığında, THE Distractor Sistemi SHALL her çeldiriciyi 0-100 arası değerlendirmek
40. **REQ-48.40** WHEN Distractor seçildiğinde, THE Distractor Sistemi SHALL en yüksek skorlu 3 çeldiriciyi kullanmak
41. **REQ-48.41** WHEN Matematiksel Doğrulama yapıldığında, THE SymPy Entegrasyonu SHALL denklemleri sembolik olarak çözmek
42. **REQ-48.42** WHEN Equation Validation yapıldığında, THE SymPy Entegrasyonu SHALL matematiksel tutarlılığı kontrol etmek
43. **REQ-48.43** WHEN Solution Verification yapıldığında, THE SymPy Entegrasyonu SHALL doğru cevabı doğrulamak
44. **REQ-48.44** WHEN Matematiksel hata tespit edildiğinde, THE SymPy Entegrasyonu SHALL soruyu reddetmek
45. **REQ-48.45** WHEN Görsel Üretim başlatıldığında, THE Görsel Üretim Sistemi SHALL Matplotlib veya Plotly kullanmak
46. **REQ-48.46** WHEN Graph Generation yapıldığında, THE Görsel Üretim Sistemi SHALL matematiksel fonksiyonları görselleştirmek
47. **REQ-48.47** WHEN Geometry Figure oluşturulduğunda, THE Görsel Üretim Sistemi SHALL geometrik şekilleri çizmek
48. **REQ-48.48** WHEN Chart/Diagram oluşturulduğunda, THE Görsel Üretim Sistemi SHALL veri görselleştirmesi yapmak

**Kalite Kontrol (REQ-48.49 - REQ-48.64)**

49. **REQ-48.49** WHEN Otomatik Skorlama yapıldığında, THE Kalite Kontrol Sistemi SHALL çok kriterli algoritma kullanmak
50. **REQ-48.50** WHEN Weighted Scoring uygulandığında, THE Kalite Kontrol Sistemi SHALL ÖSYM uygunluğuna %40 ağırlık vermek
51. **REQ-48.51** WHEN Quality Threshold filtreleme yapıldığında, THE Kalite Kontrol Sistemi SHALL minimum 70 puan olan soruları kabul etmek
52. **REQ-48.52** WHEN Soru skoru hesaplandığında, THE Kalite Kontrol Sistemi SHALL 0-100 arası değer üretmek
53. **REQ-48.53** WHEN BLEU Score hesaplandığında, THE Kalite Kontrol Sistemi SHALL akıcılık için BLEU metriği kullanmak
54. **REQ-48.54** WHEN ROUGE Score hesaplandığında, THE Kalite Kontrol Sistemi SHALL içerik örtüşmesi için ROUGE metriği kullanmak
55. **REQ-48.55** WHEN BERTScore hesaplandığında, THE Kalite Kontrol Sistemi SHALL semantik benzerlik için BERTScore kullanmak
56. **REQ-48.56** WHEN Metrik skorları birleştirildiğinde, THE Kalite Kontrol Sistemi SHALL ağırlıklı ortalama hesaplamak
57. **REQ-48.57** WHEN Uzman Review Queue oluşturulduğunda, THE Review Sistemi SHALL insan incelemesi için soru sıraya almak
58. **REQ-48.58** WHEN Review Assignment yapıldığında, THE Review Sistemi SHALL uzman uzmanlık alanına göre atama yapmak
59. **REQ-48.59** WHEN Feedback Collection yapıldığında, THE Review Sistemi SHALL uzman yorumlarını kaydetmek
60. **REQ-48.60** WHEN Review tamamlandığında, THE Review Sistemi SHALL onaylanan soruları soru bankasına eklemek
61. **REQ-48.61** WHEN A/B Testing başlatıldığında, THE A/B Test Sistemi SHALL deney tasarımı framework kullanmak
62. **REQ-48.62** WHEN Statistical Significance test edildiğinde, THE A/B Test Sistemi SHALL p-value < 0.05 kriterini kullanmak
63. **REQ-48.63** WHEN Performance Comparison yapıldığında, THE A/B Test Sistemi SHALL iki soru versiyonunu karşılaştırmak
64. **REQ-48.64** WHEN A/B Test sonuçlandığında, THE A/B Test Sistemi SHALL kazanan versiyonu otomatik seçmek

**IRT ve Psikometrik Analiz (REQ-48.65 - REQ-48.80)**

65. **REQ-48.65** WHEN 4-Parametreli IRT implementasyonu yapıldığında, THE IRT Sistemi SHALL a, b, c, d parametrelerini hesaplamak
66. **REQ-48.66** WHEN Parameter Estimation yapıldığında, THE IRT Sistemi SHALL Maximum Likelihood Estimation kullanmak
67. **REQ-48.67** WHEN MLE hesaplandığında, THE IRT Sistemi SHALL Newton-Raphson iterasyon yöntemi kullanmak
68. **REQ-48.68** WHEN Parametre tahmini tamamlandığında, THE IRT Sistemi SHALL convergence kriteri %0.001 olmak
69. **REQ-48.69** WHEN Item Characteristic Curve çizildiğinde, THE IRT Sistemi SHALL theta (-3, +3) aralığında ICC göstermek
70. **REQ-48.70** WHEN ICC Curve analiz edildiğinde, THE IRT Sistemi SHALL inflection point tespit etmek
71. **REQ-48.71** WHEN Optimal Difficulty Range belirlendiğinde, THE IRT Sistemi SHALL hedef öğrenci grubuna göre ayarlamak
72. **REQ-48.72** WHEN ICC eğrisi yorumlandığında, THE IRT Sistemi SHALL soru ayırt ediciliğini değerlendirmek
73. **REQ-48.73** WHEN Test Information Function hesaplandığında, THE IRT Sistemi SHALL tüm soruların bilgi fonksiyonlarını toplamak
74. **REQ-48.74** WHEN Information Maximization yapıldığında, THE IRT Sistemi SHALL en bilgilendirici soruları seçmek
75. **REQ-48.75** WHEN Test Reliability tahmin edildiğinde, THE IRT Sistemi SHALL Cronbach's Alpha hesaplamak
76. **REQ-48.76** WHEN Güvenilirlik skoru hesaplandığında, THE IRT Sistemi SHALL minimum 0.80 güvenilirlik hedeflemek
77. **REQ-48.77** WHEN Adaptive Calibration başlatıldığında, THE IRT Sistemi SHALL online kalibrasyon algoritması kullanmak
78. **REQ-48.78** WHEN Real-time Parameter Update yapıldığında, THE IRT Sistemi SHALL her 100 yanıtta parametreleri güncellemek
79. **REQ-48.79** WHEN Calibration Sample Size optimize edildiğinde, THE IRT Sistemi SHALL minimum 200 öğrenci yanıtı kullanmak
80. **REQ-48.80** WHEN Kalibrasyon tamamlandığında, THE IRT Sistemi SHALL parametre güven aralıklarını hesaplamak

**Performans ve Ölçeklenebilirlik (REQ-48.81 - REQ-48.96)**

81. **REQ-48.81** WHEN GPU Acceleration aktifleştirildiğinde, THE Performans Sistemi SHALL CUDA entegrasyonu kullanmak
82. **REQ-48.82** WHEN Batch Processing yapıldığında, THE Performans Sistemi SHALL 32 soruyu paralel işlemek
83. **REQ-48.83** WHEN Model Parallelization uygulandığında, THE Performans Sistemi SHALL çoklu GPU desteği sağlamak
84. **REQ-48.84** WHEN GPU kullanıldığında, THE Performans Sistemi SHALL soru üretim hızını 10x artırmak
85. **REQ-48.85** WHEN Distributed Computing başlatıldığında, THE Dağıtık Sistem SHALL Celery task queue kullanmak
86. **REQ-48.86** WHEN Redis Message Broker yapılandırıldığında, THE Dağıtık Sistem SHALL asenkron görev yönetimi sağlamak
87. **REQ-48.87** WHEN Worker Pool yönetildiğinde, THE Dağıtık Sistem SHALL dinamik worker scaling yapmak
88. **REQ-48.88** WHEN Distributed task çalıştığında, THE Dağıtık Sistem SHALL fault tolerance sağlamak
89. **REQ-48.89** WHEN Generated Question Cache yapıldığında, THE Cache Sistemi SHALL Redis kullanarak soruları önbelleğe almak
90. **REQ-48.90** WHEN Model Output Cache yapıldığında, THE Cache Sistemi SHALL aynı prompt için cache'den dönmek
91. **REQ-48.91** WHEN Cache Invalidation Strategy uygulandığında, THE Cache Sistemi SHALL 24 saat sonra cache temizlemek
92. **REQ-48.92** WHEN Cache hit olduğunda, THE Cache Sistemi SHALL yanıt süresini %90 azaltmak
93. **REQ-48.93** WHEN Monitoring başlatıldığında, THE Monitoring Sistemi SHALL generation success rate izlemek
94. **REQ-48.94** WHEN Quality Score Tracking yapıldığında, THE Monitoring Sistemi SHALL ortalama kalite skorunu takip etmek
95. **REQ-48.95** WHEN Performance Metrics Dashboard görüntülendiğinde, THE Monitoring Sistemi SHALL gerçek zamanlı metrikler göstermek
96. **REQ-48.96** WHEN Alerting tetiklendiğinde, THE Monitoring Sistemi SHALL kritik hatalarda bildirim göndermek

---

### REQ-49: Adaptif Test Sistemi (CAT - Computerized Adaptive Testing)

**Kullanıcı Hikayesi:** Bir öğrenci olarak, yetenek seviyeme göre dinamik olarak ayarlanan sorularla test olmak istiyorum, böylece daha verimli ve kişiselleştirilmiş bir değerlendirme alabilir ve gerçek yetenek seviyemi daha doğru ölçebilirim.

#### Kabul Kriterleri

**IRT Model Implementasyonu (REQ-49.1 - REQ-49.16)**

1. **REQ-49.1** WHEN 4-Parametreli IRT Sınıfı oluşturulduğunda, THE IRT Sınıfı SHALL a (discrimination), b (difficulty), c (guessing), d (upper asymptote) parametrelerini içermek
2. **REQ-49.2** WHEN Probability P(θ) hesaplandığında, THE IRT Sınıfı SHALL 4PL IRT formülünü kullanmak
3. **REQ-49.3** WHEN Log-likelihood Function hesaplandığında, THE IRT Sınıfı SHALL maksimum olabilirlik fonksiyonunu optimize etmek
4. **REQ-49.4** WHEN IRT parametreleri tahmin edildiğinde, THE IRT Sınıfı SHALL convergence kriteri 0.001 olmak
5. **REQ-49.5** WHEN Item Response Probability hesaplandığında, THE IRT Sistemi SHALL öğrenci yetenek seviyesi (theta) ve soru parametrelerini kullanmak
6. **REQ-49.6** WHEN Conditional Probability hesaplandığında, THE IRT Sistemi SHALL Bayes teoremini uygulamak
7. **REQ-49.7** WHEN Joint Probability hesaplandığında, THE IRT Sistemi SHALL tüm yanıtların olasılığını çarpmak
8. **REQ-49.8** WHEN Probability değeri hesaplandığında, THE IRT Sistemi SHALL 0 ile 1 arasında değer döndürmek
9. **REQ-49.9** WHEN Fisher Information hesaplandığında, THE IRT Sistemi SHALL soru bilgi fonksiyonunu türevlemek
10. **REQ-49.10** WHEN Test Information Function hesaplandığında, THE IRT Sistemi SHALL tüm soruların bilgi fonksiyonlarını toplamak
11. **REQ-49.11** WHEN Standard Error tahmin edildiğinde, THE IRT Sistemi SHALL 1/sqrt(Information) formülünü kullanmak
12. **REQ-49.12** WHEN Measurement Precision hesaplandığında, THE IRT Sistemi SHALL standard error < 0.3 hedeflemek
13. **REQ-49.13** WHEN EM Algorithm çalıştığında, THE Calibration Sistemi SHALL Expectation ve Maximization adımlarını iteratif yapmak
14. **REQ-49.14** WHEN Newton-Raphson Method uygulandığında, THE Calibration Sistemi SHALL gradient descent optimizasyonu kullanmak
15. **REQ-49.15** WHEN Convergence Criteria kontrol edildiğinde, THE Calibration Sistemi SHALL parametre değişimi < 0.001 olmak
16. **REQ-49.16** WHEN Calibration tamamlandığında, THE Calibration Sistemi SHALL tüm soru parametrelerini veritabanına kaydetmek

**Adaptif Test Motoru (REQ-49.17 - REQ-49.32)**

17. **REQ-49.17** WHEN Maximum Information Criterion uygulandığında, THE Adaptif Motor SHALL en bilgilendirici soruyu seçmek
18. **REQ-49.18** WHEN Information Maximization yapıldığında, THE Adaptif Motor SHALL mevcut theta tahminine göre optimize etmek
19. **REQ-49.19** WHEN Content Balancing Constraints uygulandığında, THE Adaptif Motor SHALL konu dağılımını dengelemek
20. **REQ-49.20** WHEN Soru seçildiğinde, THE Adaptif Motor SHALL 500ms içinde karar vermek
21. **REQ-49.21** WHEN Bayesian Knowledge Tracing başlatıldığında, THE BKT Sistemi SHALL prior knowledge estimation yapmak
22. **REQ-49.22** WHEN Posterior Update yapıldığında, THE BKT Sistemi SHALL her yanıt sonrası bilgi durumunu güncellemek
23. **REQ-49.23** WHEN Knowledge State Tracking yapıldığında, THE BKT Sistemi SHALL öğrenme, unutma, tahmin ve hata parametrelerini kullanmak
24. **REQ-49.24** WHEN BKT modeli çalıştığında, THE BKT Sistemi SHALL Hidden Markov Model kullanmak
25. **REQ-49.25** WHEN EAP Method uygulandığında, THE Theta Estimation Sistemi SHALL Expected A Posteriori hesaplamak
26. **REQ-49.26** WHEN MLE Method uygulandığında, THE Theta Estimation Sistemi SHALL Maximum Likelihood Estimation kullanmak
27. **REQ-49.27** WHEN Theta Convergence izlendiğinde, THE Theta Estimation Sistemi SHALL standard error < 0.3 hedeflemek
28. **REQ-49.28** WHEN Theta güncellendiğinde, THE Theta Estimation Sistemi SHALL -3 ile +3 arasında değer üretmek
29. **REQ-49.29** WHEN Fixed-Length Stopping uygulandığında, THE Stopping Rule Sistemi SHALL belirlenen soru sayısında durmak
30. **REQ-49.30** WHEN Precision-Based Stopping uygulandığında, THE Stopping Rule Sistemi SHALL SE < 0.3 olduğunda durmak
31. **REQ-49.31** WHEN Classification-Based Stopping uygulandığında, THE Stopping Rule Sistemi SHALL yeterlik seviyesi belirlendiğinde durmak
32. **REQ-49.32** WHEN Test sonlandığında, THE Stopping Rule Sistemi SHALL minimum 10, maksimum 50 soru sınırı olmak

**Deneme Sınavı Tipleri (REQ-49.33 - REQ-49.52)**

33. **REQ-49.33** WHEN Diagnostic Test başlatıldığında, THE Diagnostic Test SHALL zayıf alanları tespit etmeye odaklanmak
34. **REQ-49.34** WHEN Comprehensive Topic Coverage yapıldığında, THE Diagnostic Test SHALL tüm konuları kapsamak
35. **REQ-49.35** WHEN Detailed Feedback oluşturulduğunda, THE Diagnostic Test SHALL konu bazlı analiz sunmak
36. **REQ-49.36** WHEN Diagnostic Test tamamlandığında, THE Diagnostic Test SHALL özel çalışma planı önermek
37. **REQ-49.37** WHEN Formative Test başlatıldığında, THE Formative Test SHALL öğrenme ilerlemesini değerlendirmek
38. **REQ-49.38** WHEN Adaptive Difficulty Adjustment yapıldığında, THE Formative Test SHALL zorluk seviyesini dinamik ayarlamak
39. **REQ-49.39** WHEN Immediate Feedback verildiğinde, THE Formative Test SHALL her soru sonrası açıklama sunmak
40. **REQ-49.40** WHEN Formative Test tamamlandığında, THE Formative Test SHALL öğrenme önerileri sunmak
41. **REQ-49.41** WHEN Summative Test başlatıldığında, THE Summative Test SHALL final değerlendirme formatında olmak
42. **REQ-49.42** WHEN ÖSYM Format Compliance kontrol edildiğinde, THE Summative Test SHALL ÖSYM standartlarına %100 uygun olmak
43. **REQ-49.43** WHEN Comprehensive Scoring yapıldığında, THE Summative Test SHALL detaylı puan raporu sunmak
44. **REQ-49.44** WHEN Summative Test tamamlandığında, THE Summative Test SHALL sertifika oluşturmak
45. **REQ-49.45** WHEN Benchmark Test başlatıldığında, THE Benchmark Test SHALL ulusal ortalama ile karşılaştırma yapmak
46. **REQ-49.46** WHEN Percentile Ranking hesaplandığında, THE Benchmark Test SHALL öğrenciyi yüzdelik dilime yerleştirmek
47. **REQ-49.47** WHEN Performance Prediction yapıldığında, THE Benchmark Test SHALL gerçek sınav tahmini sunmak
48. **REQ-49.48** WHEN Benchmark Test tamamlandığında, THE Benchmark Test SHALL güçlü/zayıf alanları raporlamak
49. **REQ-49.49** WHEN Mock Exam başlatıldığında, THE Mock Exam SHALL tam ÖSYM simülasyonu sunmak
50. **REQ-49.50** WHEN Time Management Practice yapıldığında, THE Mock Exam SHALL gerçek sınav sürelerini kullanmak
51. **REQ-49.51** WHEN Realistic Exam Environment sağlandığında, THE Mock Exam SHALL sınav koşullarını simüle etmek
52. **REQ-49.52** WHEN Mock Exam tamamlandığında, THE Mock Exam SHALL detaylı performans analizi sunmak

**Soru Seçimi ve Optimizasyon (REQ-49.53 - REQ-49.68)**

53. **REQ-49.53** WHEN Content Balancing yapıldığında, THE Soru Seçim Sistemi SHALL konu dağılım kısıtlarını uygulamak
54. **REQ-49.54** WHEN Curriculum Alignment kontrol edildiğinde, THE Soru Seçim Sistemi SHALL MEB müfredatına uygun olmak
55. **REQ-49.55** WHEN Balanced Difficulty Distribution sağlandığında, THE Soru Seçim Sistemi SHALL kolay-orta-zor dengesi kurmak
56. **REQ-49.56** WHEN Content Constraints uygulandığında, THE Soru Seçim Sistemi SHALL her konudan minimum soru sayısını garanti etmek
57. **REQ-49.57** WHEN Item Exposure Rate izlendiğinde, THE Exposure Control Sistemi SHALL her sorunun kullanım sıklığını takip etmek
58. **REQ-49.58** WHEN Sympson-Hetter Method uygulandığında, THE Exposure Control Sistemi SHALL soru maruziyetini sınırlamak
59. **REQ-49.59** WHEN Item Pool Rotation yapıldığında, THE Exposure Control Sistemi SHALL soru havuzunu döngüsel kullanmak
60. **REQ-49.60** WHEN Exposure limit aşıldığında, THE Exposure Control Sistemi SHALL soruyu geçici olarak devre dışı bırakmak
61. **REQ-49.61** WHEN ZPD İçinde Soru Seçimi yapıldığında, THE ZPD Sistemi SHALL Zone of Proximal Development hedeflemek
62. **REQ-49.62** WHEN Optimal Challenge Level belirlendiğinde, THE ZPD Sistemi SHALL öğrenci yetenek seviyesine göre ayarlamak
63. **REQ-49.63** WHEN Frustration Prevention uygulandığında, THE ZPD Sistemi SHALL çok zor soruları filtrelemek
64. **REQ-49.64** WHEN ZPD aralığı hesaplandığında, THE ZPD Sistemi SHALL theta ± 1 aralığında soru seçmek
65. **REQ-49.65** WHEN Spacing Effect uygulandığında, THE Spaced Repetition Sistemi SHALL optimal tekrar zamanlaması yapmak
66. **REQ-49.66** WHEN Optimal Review Timing hesaplandığında, THE Spaced Repetition Sistemi SHALL FSRS algoritması kullanmak
67. **REQ-49.67** WHEN Forgetting Curve dikkate alındığında, THE Spaced Repetition Sistemi SHALL Ebbinghaus modelini kullanmak
68. **REQ-49.68** WHEN Spaced repetition planlandığında, THE Spaced Repetition Sistemi SHALL 1-3-7-14-30 gün aralıkları önermek

**Gerçek Zamanlı Adaptasyon (REQ-49.69 - REQ-49.84)**

69. **REQ-49.69** WHEN Real-time Theta Update yapıldığında, THE Adaptasyon Sistemi SHALL her yanıt sonrası theta güncellemek
70. **REQ-49.70** WHEN Incremental Theta Estimation yapıldığında, THE Adaptasyon Sistemi SHALL Bayesian update kullanmak
71. **REQ-49.71** WHEN Confidence Interval Tracking yapıldığında, THE Adaptasyon Sistemi SHALL %95 güven aralığı hesaplamak
72. **REQ-49.72** WHEN Theta güncelleme tamamlandığında, THE Adaptasyon Sistemi SHALL 100ms içinde sonuç döndürmek
73. **REQ-49.73** WHEN Dynamic Difficulty Adjustment yapıldığında, THE Zorluk Sistemi SHALL performansa göre zorluk ayarlamak
74. **REQ-49.74** WHEN Performance-Based Scaling uygulandığında, THE Zorluk Sistemi SHALL başarı oranına göre ölçeklemek
75. **REQ-49.75** WHEN Smooth Difficulty Transitions sağlandığında, THE Zorluk Sistemi SHALL ani zorluk değişimlerini önlemek
76. **REQ-49.76** WHEN Zorluk ayarlandığında, THE Zorluk Sistemi SHALL maksimum 1 seviye değişim yapmak
77. **REQ-49.77** WHEN Success Rate Monitoring yapıldığında, THE Motivasyon Sistemi SHALL başarı oranını %40-80 aralığında tutmak
78. **REQ-49.78** WHEN Encouragement Messages gösterildiğinde, THE Motivasyon Sistemi SHALL pozitif pekiştirme sunmak
79. **REQ-49.79** WHEN Achievement Celebrations yapıldığında, THE Motivasyon Sistemi SHALL milestone'larda kutlama göstermek
80. **REQ-49.80** WHEN Motivasyon düştüğünde, THE Motivasyon Sistemi SHALL destek mesajları göstermek
81. **REQ-49.81** WHEN Response Time Analysis yapıldığında, THE Yorgunluk Sistemi SHALL yanıt sürelerini izlemek
82. **REQ-49.82** WHEN Accuracy Decline Detection yapıldığında, THE Yorgunluk Sistemi SHALL doğruluk düşüşünü tespit etmek
83. **REQ-49.83** WHEN Break Recommendations verildiğinde, THE Yorgunluk Sistemi SHALL 20 dakikada bir mola önermek
84. **REQ-49.84** WHEN Yorgunluk tespit edildiğinde, THE Yorgunluk Sistemi SHALL zorluk seviyesini geçici düşürmek

**Performans Analitikleri (REQ-49.85 - REQ-49.100)**

85. **REQ-49.85** WHEN Learning Curve Analysis yapıldığında, THE Analitik Sistemi SHALL zaman içinde ilerlemeyi izlemek
86. **REQ-49.86** WHEN Growth Rate Calculation yapıldığında, THE Analitik Sistemi SHALL öğrenme hızını hesaplamak
87. **REQ-49.87** WHEN Plateau Detection yapıldığında, THE Analitik Sistemi SHALL durağan dönemleri tespit etmek
88. **REQ-49.88** WHEN Learning curve gösterildiğinde, THE Analitik Sistemi SHALL görsel grafik sunmak
89. **REQ-49.89** WHEN Success Probability Prediction yapıldığında, THE Predictive Analitik SHALL gelecek performansı tahmin etmek
90. **REQ-49.90** WHEN University Placement Prediction yapıldığında, THE Predictive Analitik SHALL üniversite yerleşme olasılığı hesaplamak
91. **REQ-49.91** WHEN Score Range Estimation yapıldığında, THE Predictive Analitik SHALL puan aralığı tahmini sunmak
92. **REQ-49.92** WHEN Prediction yapıldığında, THE Predictive Analitik SHALL %95 güven aralığı ile tahmin vermek
93. **REQ-49.93** WHEN Unusual Performance Patterns tespit edildiğinde, THE Anomaly Detection SHALL anormal davranışları işaretlemek
94. **REQ-49.94** WHEN Cheating Detection yapıldığında, THE Anomaly Detection SHALL şüpheli yanıt paternlerini tespit etmek
95. **REQ-49.95** WHEN Data Quality Monitoring yapıldığında, THE Anomaly Detection SHALL veri tutarlılığını kontrol etmek
96. **REQ-49.96** WHEN Anomaly tespit edildiğinde, THE Anomaly Detection SHALL yöneticiye bildirim göndermek
97. **REQ-49.97** WHEN Group Performance Comparison yapıldığında, THE Cohort Analysis SHALL grup performanslarını karşılaştırmak
98. **REQ-49.98** WHEN Demographic Analysis yapıldığında, THE Cohort Analysis SHALL demografik faktörleri analiz etmek
99. **REQ-49.99** WHEN Intervention Effectiveness ölçüldüğünde, THE Cohort Analysis SHALL müdahale etkisini değerlendirmek
100. **REQ-49.100** WHEN Cohort raporu oluşturulduğunda, THE Cohort Analysis SHALL detaylı karşılaştırma raporu sunmak

---

## Bağımlılıklar

### Sistem Bağımlılıkları

1. **Backend**: FastAPI, Python 3.11+, PostgreSQL 15+, Redis 7+, Elasticsearch 8+
2. **Frontend**: React 18+, TypeScript 5+, Vite 4+
3. **AI/ML**: OpenAI GPT-4, BERTurk, Zemberek NLP, scikit-learn
4. **Dış Servisler**: YouTube Data API v3, Khan Academy API, EBA TV API
5. **Infrastructure**: Docker, Kubernetes, Nginx, Prometheus, Grafana

### Gereksinim Bağımlılıkları

| Gereksinim | Bağımlı Olduğu Gereksinimler |
|------------|------------------------------|
| REQ-1 | REQ-3, REQ-7, REQ-9 |
| REQ-2 | REQ-12, REQ-11 |
| REQ-4 | REQ-10, REQ-12 |
| REQ-5 | REQ-21, REQ-22, REQ-23 |
| REQ-10 | REQ-11, REQ-12 |
| REQ-13-20 | REQ-7, REQ-19 |
| REQ-21-25 | REQ-5 |
| REQ-26-47 | REQ-1 to REQ-25 (tümü) |

---

## Kabul Kriterleri Özeti

### Öncelik P0 (Kritik)
- REQ-1: ÖSYM Sınav Sistemi
- REQ-2: Türkçe NLP
- REQ-3: Müfredat Uyumluluğu
- REQ-7: Performans
- REQ-10: Devrimsel AI Özellikleri

### Öncelik P1 (Yüksek)
- REQ-4: Adaptif Öğrenme
- REQ-5: Çoklu Platform Entegrasyonu
- REQ-6: Öğretmen/Veli Sistemi
- REQ-21-25: Video Kaynak Kalitesi

### Öncelik P2 (Orta)
- REQ-8: PWA ve Offline
- REQ-9: Erişilebilirlik
- REQ-13-20: İçerik Yönetimi

### Öncelik P3 (Düşük)
- REQ-26-47: Sağlık Denetimi ve Monitoring

### Öncelik P0-P1 (Yeni Eklenenler)
- REQ-48: LLM Tabanlı ÖSYM Soru Üretim Sistemi
- REQ-49: Adaptif Test Sistemi (CAT)
- REQ-50-53: Erişilebilirlik Sistemleri (Disleksi, Diskalkuli, DEHB, OSB)
- REQ-56-59: Gamification Sistemi (Puan, Rozet, Motivasyon, Analytics)
- REQ-60-65: Opsiyonel Sistemler (Soru Bankası, Üniversite, Canlı Ders, Mobil, Sosyal, Psikolojik)

---

## BÖLÜM 6: ERİŞİLEBİLİRLİK SİSTEMLERİ

### REQ-50: Disleksi Desteği - Tipografi ve Görsel Düzenlemeler

**İmplementasyon Durumu:** ✅ TAMAMLANDI (Task 76.1, 76.2, 76.3, 76.4)

**Kullanıcı Hikayesi:** Disleksi tanısı olan bir öğrenci olarak, okuma zorluğumu azaltacak tipografi ve görsel düzenlemelere sahip olmak istiyorum, böylece içerikleri daha rahat okuyabilir ve öğrenme sürecimde daha başarılı olabilirim.

#### Kabul Kriterleri

**Font Entegrasyonu (REQ-50.1 - REQ-50.4)**

1. **REQ-50.1** WHEN öğrenci disleksi desteğini aktifleştirdiğinde, THE Platform SHALL OpenDyslexic ve Dyslexie fontlarını seçenek olarak sunmak
2. **REQ-50.2** WHEN öğrenci disleksi dostu font seçtiğinde, THE Platform SHALL seçilen fontu tüm metin içeriklerine uygulamak
3. **REQ-50.3** WHEN font değişikliği yapıldığında, THE Platform SHALL değişikliği 200ms içinde yumuşak geçişle uygulamak
4. **REQ-50.4** WHEN öğrenci font tercihini kaydettiğinde, THE Platform SHALL tercihi localStorage'da kalıcı olarak saklamak

**Font Boyutu Ayarlama (REQ-50.5 - REQ-50.7)**

5. **REQ-50.5** WHEN öğrenci font boyutu ayarını açtığında, THE Platform SHALL 12pt ile 24pt arası 1pt artışlarla font boyutu kontrolü sunan slider component göstermek
6. **REQ-50.6** WHEN font boyutu değiştirildiğinde, THE Platform SHALL değişikliği gerçek zamanlı olarak önizlemek
7. **REQ-50.7** WHEN font boyutu ayarlandığında, THE Platform SHALL responsive scaling ile tüm cihazlarda uyumlu görünüm sağlamak

**Satır Aralığı Ayarlama (REQ-50.8 - REQ-50.10)**

8. **REQ-50.8** WHEN öğrenci satır aralığı ayarını açtığında, THE Platform SHALL 1.0x ile 3.0x arası 0.1x artışlarla line-height kontrolü sunan slider component göstermek ve mevcut değeri yüzde olarak (örn: "150%") göstermek
9. **REQ-50.9** WHEN satır aralığı değiştirildiğinde, THE Platform SHALL paragraf aralıklarını (margin-bottom) satır aralığının 1.5 katı olacak şekilde orantılı olarak ayarlamak ve 100ms içinde uygulamak
10. **REQ-50.10** WHEN satır aralığı 1.5x veya üzerine ayarlandığında, THE Platform SHALL okuma konforunu maksimize etmek için satır uzunluğunu maksimum 75 karakter ile sınırlamak ve metin hizalamasını sola yaslamak

**Kelime ve Harf Aralığı (REQ-50.11 - REQ-50.13)**

11. **REQ-50.11** WHEN öğrenci harf aralığı ayarını açtığında, THE Platform SHALL 0em ile 0.3em arası 0.05em artışlarla letter-spacing kontrolü sunmak
12. **REQ-50.12** WHEN öğrenci kelime aralığı ayarını açtığında, THE Platform SHALL 0em ile 0.5em arası 0.05em artışlarla word-spacing kontrolü sunmak
13. **REQ-50.13** WHEN harf veya kelime aralığı değiştirildiğinde, THE Platform SHALL değişikliği gerçek zamanlı olarak uygulamak ve kerning ayarlamalarını optimize etmek

**Renk ve Kontrast (REQ-50.14 - REQ-50.27)**

14. **REQ-50.14** WHEN öğrenci renkli overlay seçeneğini açtığında, THE Platform SHALL 6 farklı renk seçeneği (mavi, yeşil, sarı, pembe, mor, gri) sunmak
15. **REQ-50.15** WHEN öğrenci overlay rengi seçtiğinde, THE Platform SHALL seçilen rengi tüm sayfa üzerine uygulamak
16. **REQ-50.16** WHEN overlay opacity ayarlandığında, THE Platform SHALL %10 ile %90 arası opacity kontrolü sunmak
17. **REQ-50.17** WHEN overlay uygulandığında, THE Platform SHALL metin okunabilirliğini korumak için kontrast oranını otomatik ayarlamak
18. **REQ-50.18** WHEN öğrenci opacity slider'ını kullandığında, THE Platform SHALL gerçek zamanlı önizleme sağlamak
19. **REQ-50.19** WHEN opacity değeri değiştirildiğinde, THE Platform SHALL değişikliği 150ms içinde yumuşak geçişle uygulamak
20. **REQ-50.20** WHEN öğrenci overlay tercihini kaydettiğinde, THE Platform SHALL tercihi localStorage'da kalıcı olarak saklamak
21. **REQ-50.21** WHEN öğrenci yüksek kontrast modu seçtiğinde, THE Platform SHALL önceden tanımlı yüksek kontrast temaları sunmak
22. **REQ-50.22** WHEN yüksek kontrast modu aktifleştirildiğinde, THE Platform SHALL dark mode desteği sağlamak
23. **REQ-50.23** WHEN kontrast ayarlandığında, THE Platform SHALL custom contrast ratio hesaplaması yapmak
24. **REQ-50.24** WHEN kontrast modu değiştirildiğinde, THE Platform SHALL tüm UI elementlerine tutarlı şekilde uygulamak
25. **REQ-50.25** WHEN WCAG AAA uyumluluğu kontrol edildiğinde, THE Platform SHALL minimum 7:1 kontrast oranı sağlamak
26. **REQ-50.26** WHEN kontrast oranı hesaplandığında, THE Platform SHALL otomatik kontrast hesaplayıcı kullanmak
27. **REQ-50.27** WHEN kontrast uyumsuzluğu tespit edildiğinde, THE Platform SHALL otomatik düzeltme önermek

**Okuma Yardımcıları (REQ-50.28 - REQ-50.42)**

28. **REQ-50.28** WHEN öğrenci okuma cetveli (reading ruler) aktifleştirdiğinde, THE Platform SHALL yatay cetvel overlay göstermek
29. **REQ-50.29** WHEN okuma cetveli kullanıldığında, THE Platform SHALL ayarlanabilir yükseklik kontrolü sunmak
30. **REQ-50.30** WHEN okuma cetveli aktifken, THE Platform SHALL imleci takip etme seçeneği sunmak
31. **REQ-50.31** WHEN okuma cetveli konumlandığında, THE Platform SHALL klavye kısayolları ile kontrol sağlamak
32. **REQ-50.32** WHEN öğrenci odak modu (focus mode) aktifleştirdiğinde, THE Platform SHALL çevredeki metni karartmak
33. **REQ-50.33** WHEN odak modu aktifken, THE Platform SHALL mevcut satır/paragrafı vurgulamak
34. **REQ-50.34** WHEN odak alanı ayarlandığında, THE Platform SHALL ayarlanabilir odak alanı boyutu sunmak
35. **REQ-50.35** WHEN odak modu kullanıldığında, THE Platform SHALL okuma ilerlemesini otomatik takip etmek
36. **REQ-50.36** WHEN öğrenci kelime vurgulama aktifleştirdiğinde, THE Platform SHALL hover-based highlighting sağlamak
37. **REQ-50.37** WHEN kelime vurgulandığında, THE Platform SHALL click-to-highlight özelliği sunmak
38. **REQ-50.38** WHEN vurgulama yapıldığında, THE Platform SHALL çoklu renk vurgulama seçenekleri sunmak
39. **REQ-50.39** WHEN vurgulanan kelimeler kaydedildiğinde, THE Platform SHALL vurguları localStorage'da saklamak
40. **REQ-50.40** WHEN öğrenci hece ayırma aktifleştirdiğinde, THE Platform SHALL otomatik hece ayrımı yapmak
41. **REQ-50.41** WHEN hece ayrımı yapıldığında, THE Platform SHALL görsel hece işaretleyicileri göstermek
42. **REQ-50.42** WHEN Türkçe hece ayrımı uygulandığında, THE Platform SHALL Türkçe heceleme kurallarını kullanmak

**Text-to-Speech (REQ-50.43 - REQ-50.56)**

43. **REQ-50.43** WHEN öğrenci TTS aktifleştirdiğinde, THE Platform SHALL Web Speech API entegrasyonu kullanmak
44. **REQ-50.44** WHEN TTS başlatıldığında, THE Platform SHALL Türkçe ses seçimi sunmak
45. **REQ-50.45** WHEN TTS servisi kullanılamadığında, THE Platform SHALL fallback TTS servisi devreye sokmak
46. **REQ-50.46** WHEN TTS çalıştığında, THE Platform SHALL ses kalitesi ve akıcılığı optimize etmek
47. **REQ-50.47** WHEN öğrenci ses hızı ayarladığında, THE Platform SHALL %50 ile %200 arası hız kontrolü sunmak
48. **REQ-50.48** WHEN ses hızı değiştirildiğinde, THE Platform SHALL önceden tanımlı hız seçenekleri (yavaş, normal, hızlı) sunmak
49. **REQ-50.49** WHEN ses hızı ayarlandığında, THE Platform SHALL gerçek zamanlı hız ayarlama sağlamak
50. **REQ-50.50** WHEN öğrenci ses tonu ayarladığında, THE Platform SHALL pitch kontrolü sunmak
51. **REQ-50.51** WHEN ses seçimi yapıldığında, THE Platform SHALL farklı ses seçenekleri sunmak
52. **REQ-50.52** WHEN ses tercihi kaydedildiğinde, THE Platform SHALL cinsiyet tercihi seçeneği sunmak
53. **REQ-50.53** WHEN karaoke mode aktifleştirildiğinde, THE Platform SHALL kelime kelime vurgulama yapmak
54. **REQ-50.54** WHEN TTS okurken, THE Platform SHALL senkronize vurgulama sağlamak
55. **REQ-50.55** WHEN vurgulama rengi ayarlandığında, THE Platform SHALL ayarlanabilir vurgulama rengi sunmak
56. **REQ-50.56** WHEN karaoke mode kullanıldığında, THE Platform SHALL okuma hızı ile vurgulama senkronizasyonu sağlamak

**Metin Basitleştirme (REQ-50.57 - REQ-50.72)**

57. **REQ-50.57** WHEN karmaşık kelime tespiti yapıldığında, THE Platform SHALL complexity scoring algoritması kullanmak
58. **REQ-50.58** WHEN kelime karmaşıklığı hesaplandığında, THE Platform SHALL Türkçe kelime frekans veritabanı kullanmak
59. **REQ-50.59** WHEN karmaşıklık eşiği ayarlandığında, THE Platform SHALL difficulty threshold ayarı sunmak
60. **REQ-50.60** WHEN karmaşık kelimeler tespit edildiğinde, THE Platform SHALL kelimeleri görsel olarak işaretlemek
61. **REQ-50.61** WHEN basit eşanlamlı değiştirme yapıldığında, THE Platform SHALL synonym dictionary kullanmak
62. **REQ-50.62** WHEN eşanlamlı seçildiğinde, THE Platform SHALL context-aware replacement yapmak
63. **REQ-50.63** WHEN kelime değiştirilmeden önce, THE Platform SHALL kullanıcı onay seçeneği sunmak
64. **REQ-50.64** WHEN eşanlamlı önerildiğinde, THE Platform SHALL anlam korunarak değiştirmek
65. **REQ-50.65** WHEN uzun cümle analiz edildiğinde, THE Platform SHALL sentence length analysis yapmak
66. **REQ-50.66** WHEN cümle bölme yapıldığında, THE Platform SHALL otomatik cümle bölme algoritması kullanmak
67. **REQ-50.67** WHEN bağlaç tespit edildiğinde, THE Platform SHALL conjunction identification yapmak
68. **REQ-50.68** WHEN cümle bölündüğünde, THE Platform SHALL anlam bütünlüğünü korumak
69. **REQ-50.69** WHEN Flesch-Kincaid skoru hesaplandığında, THE Platform SHALL readability score calculation yapmak
70. **REQ-50.70** WHEN okunabilirlik skoru gösterildiğinde, THE Platform SHALL grade level estimation sunmak
71. **REQ-50.71** WHEN metin analiz edildiğinde, THE Platform SHALL improvement suggestions sunmak
72. **REQ-50.72** WHEN okunabilirlik raporu oluşturulduğunda, THE Platform SHALL detaylı metrikler göstermek

**Görsel Destekler (REQ-50.73 - REQ-50.88)**

73. **REQ-50.73** WHEN kavram haritası oluşturulduğunda, THE Platform SHALL mind map generation algoritması kullanmak
74. **REQ-50.74** WHEN kavram haritası gösterildiğinde, THE Platform SHALL interactive node exploration sağlamak
75. **REQ-50.75** WHEN kavram haritası kaydedildiğinde, THE Platform SHALL export functionality sunmak
76. **REQ-50.76** WHEN kavram haritası düzenlendiğinde, THE Platform SHALL drag-and-drop interface sağlamak
77. **REQ-50.77** WHEN infografik oluşturulduğunda, THE Platform SHALL visual summary generation yapmak
78. **REQ-50.78** WHEN infografik gösterildiğinde, THE Platform SHALL icon-based representation kullanmak
79. **REQ-50.79** WHEN infografik özelleştirildiğinde, THE Platform SHALL customizable templates sunmak
80. **REQ-50.80** WHEN infografik paylaşıldığında, THE Platform SHALL farklı format seçenekleri sunmak
81. **REQ-50.81** WHEN resimli sözlük kullanıldığında, THE Platform SHALL image-word associations göstermek
82. **REQ-50.82** WHEN kelime öğrenildiğinde, THE Platform SHALL visual vocabulary builder kullanmak
83. **REQ-50.83** WHEN resim arandığında, THE Platform SHALL searchable image database kullanmak
84. **REQ-50.84** WHEN görsel kelime kartı oluşturulduğunda, THE Platform SHALL spaced repetition ile entegre etmek
85. **REQ-50.85** WHEN renk kodlama uygulandığında, THE Platform SHALL color-coded categories kullanmak
86. **REQ-50.86** WHEN renk şeması seçildiğinde, THE Platform SHALL consistent color scheme sağlamak
87. **REQ-50.87** WHEN renk eşleştirmesi yapıldığında, THE Platform SHALL customizable color mapping sunmak
88. **REQ-50.88** WHEN renk kodlama kaydedildiğinde, THE Platform SHALL kullanıcı tercihlerini saklamak

**Çoklu Duyusal Öğrenme (REQ-50.89 - REQ-50.104)**

89. **REQ-50.89** WHEN çoklu modal içerik sunulduğunda, THE Platform SHALL görsel + işitsel + kinestetik içerik delivery sağlamak
90. **REQ-50.90** WHEN medya senkronize edildiğinde, THE Platform SHALL synchronized media playback sağlamak
91. **REQ-50.91** WHEN interaktif elementler kullanıldığında, THE Platform SHALL interactive elements sunmak
92. **REQ-50.92** WHEN çoklu duyusal içerik kaydedildiğinde, THE Platform SHALL kullanıcı tercihlerini saklamak
93. **REQ-50.93** WHEN interaktif animasyon gösterildiğinde, THE Platform SHALL animated explanations sunmak
94. **REQ-50.94** WHEN animasyon oynatıldığında, THE Platform SHALL step-by-step animations göstermek
95. **REQ-50.95** WHEN animasyon kontrol edildiğinde, THE Platform SHALL pause/replay controls sunmak
96. **REQ-50.96** WHEN animasyon hızı ayarlandığında, THE Platform SHALL playback speed control sağlamak
97. **REQ-50.97** WHEN video içerik gösterildiğinde, THE Platform SHALL educational video library sunmak
98. **REQ-50.98** WHEN video oynatıldığında, THE Platform SHALL subtitle support sağlamak
99. **REQ-50.99** WHEN video hızı ayarlandığında, THE Platform SHALL playback speed control sunmak
100. **REQ-50.100** WHEN video erişilebilirliği sağlandığında, THE Platform SHALL WCAG uyumlu video player kullanmak
101. **REQ-50.101** WHEN VR/AR desteği sunulduğunda, THE Platform SHALL virtual reality integration sağlamak
102. **REQ-50.102** WHEN AR overlay kullanıldığında, THE Platform SHALL augmented reality overlays göstermek
103. **REQ-50.103** WHEN 3D model gösterildiğinde, THE Platform SHALL 3D model interaction sağlamak
104. **REQ-50.104** WHEN VR/AR içerik kaydedildiğinde, THE Platform SHALL immersive learning experiences sunmak

---

**Kabul Kriterleri Özeti:**
- ✅ REQ-50.1 - REQ-50.4: Font Entegrasyonu (OpenDyslexic, Dyslexie)
- ✅ REQ-50.5 - REQ-50.7: Font Boyutu Ayarlama (12-24pt)
- ✅ REQ-50.8 - REQ-50.10: Satır Aralığı Ayarlama (1.0x-3.0x)
- ✅ REQ-50.11 - REQ-50.13: Kelime ve Harf Aralığı
- ⏳ REQ-50.14 - REQ-50.27: Renk ve Kontrast (Task 77 - Beklemede)
- ⏳ REQ-50.28 - REQ-50.42: Okuma Yardımcıları (Task 78 - Beklemede)
- ⏳ REQ-50.43 - REQ-50.56: Text-to-Speech (Task 79 - Beklemede)
- ⏳ REQ-50.57 - REQ-50.72: Metin Basitleştirme (Task 80 - Beklemede)
- ⏳ REQ-50.73 - REQ-50.88: Görsel Destekler (Task 81 - Beklemede)
- ⏳ REQ-50.89 - REQ-50.104: Çoklu Duyusal Öğrenme (Task 82 - Beklemede)

**Test Coverage:** 19/19 tests passing (Task 76.3)
**WCAG Compliance:** Level AA
**Browser Support:** Chrome, Firefox, Safari, Edge
**Mobile Support:** iOS, Android (responsive design)


---

### REQ-51: Diskalkuli Desteği - Görsel Matematik Temsilleri

**Kullanıcı Hikayesi:** Diskalkuli (matematik öğrenme güçlüğü) yaşayan bir öğrenci olarak, soyut matematiksel kavramları somut görsel temsillerle görmek istiyorum, böylece sayıları, kesirleri ve geometrik şekilleri daha iyi anlayabilir ve matematik kaygımı azaltabilirim.

#### Kabul Kriterleri

**Sayı Blokları (REQ-51.1 - REQ-51.5)**

1. **REQ-51.1** WHEN öğrenci sayı bloklarını görüntülediğinde, THE Görsel Matematik Sistemi SHALL Base-10 blok sistemini (birler, onlar, yüzler, binler) görselleştirmek
2. **REQ-51.2** WHEN öğrenci blokları manipüle ettiğinde, THE Görsel Matematik Sistemi SHALL drag-and-drop ile interaktif manipülasyon sağlamak
3. **REQ-51.3** WHEN öğrenci sayı girdiğinde, THE Görsel Matematik Sistemi SHALL otomatik olarak karşılık gelen blok temsilini göstermek
4. **REQ-51.4** WHEN öğrenci toplama/çıkarma işlemi yaptığında, THE Görsel Matematik Sistemi SHALL blokların birleşme ve ayrılma animasyonunu göstermek
5. **REQ-51.5** WHEN öğrenci basamak değerini öğrendiğinde, THE Görsel Matematik Sistemi SHALL her basamağı farklı renk ve boyutta blokla temsil etmek

**Kesir Çubukları (REQ-51.6 - REQ-51.10)**

6. **REQ-51.6** WHEN öğrenci kesir öğrendiğinde, THE Görsel Matematik Sistemi SHALL kesir çubuğu modellerini (1/2, 1/3, 1/4, vb.) görselleştirmek
7. **REQ-51.7** WHEN öğrenci denk kesirleri karşılaştırdığında, THE Görsel Matematik Sistemi SHALL eşdeğer kesir çubuklarını üst üste göstermek
8. **REQ-51.8** WHEN öğrenci kesir işlemi yaptığında, THE Görsel Matematik Sistemi SHALL kesir çubuklarının birleşme ve bölünme animasyonunu göstermek
9. **REQ-51.9** WHEN öğrenci iki kesri karşılaştırdığında, THE Görsel Matematik Sistemi SHALL interaktif karşılaştırma aracı sunmak
10. **REQ-51.10** WHEN öğrenci kesir çubuğunu manipüle ettiğinde, THE Görsel Matematik Sistemi SHALL gerçek zamanlı kesir değerini sayısal olarak göstermek

**Geometrik Şekiller 3D (REQ-51.11 - REQ-51.15)**

11. **REQ-51.11** WHEN öğrenci 3D şekil öğrendiğinde, THE Görsel Matematik Sistemi SHALL küp, küre, silindir, koni, piramit gibi 3D şekilleri render etmek
12. **REQ-51.12** WHEN öğrenci şekli incelediğinde, THE Görsel Matematik Sistemi SHALL 360 derece rotasyon ve manipülasyon sağlamak
13. **REQ-51.13** WHEN öğrenci şekil ölçümü yaptığında, THE Görsel Matematik Sistemi SHALL interaktif ölçüm araçları (cetvel, açıölçer) sunmak
14. **REQ-51.14** WHEN öğrenci hacim hesapladığında, THE Görsel Matematik Sistemi SHALL şeklin içini doldurma animasyonu ile hacmi görselleştirmek
15. **REQ-51.15** WHEN öğrenci yüzey alanı öğrendiğinde, THE Görsel Matematik Sistemi SHALL 3D şeklin açılımını (net) göstermek

**Grafik Çizim (REQ-51.16 - REQ-51.20)**

16. **REQ-51.16** WHEN öğrenci fonksiyon grafiği çizdiğinde, THE Görsel Matematik Sistemi SHALL interaktif koordinat sistemi sunmak
17. **REQ-51.17** WHEN öğrenci fonksiyon girdiğinde, THE Görsel Matematik Sistemi SHALL gerçek zamanlı grafik çizimi yapmak
18. **REQ-51.18** WHEN öğrenci grafiği manipüle ettiğinde, THE Görsel Matematik Sistemi SHALL zoom, pan ve nokta seçimi özellikleri sağlamak
19. **REQ-51.19** WHEN öğrenci grafik üzerinde çalıştığında, THE Görsel Matematik Sistemi SHALL x ve y eksenlerini renkli kodlamak
20. **REQ-51.20** WHEN öğrenci grafik noktası seçtiğinde, THE Görsel Matematik Sistemi SHALL koordinat değerlerini tooltip ile göstermek

**Adım Adım Çözüm Sistemi (REQ-51.21 - REQ-51.40)**

21. **REQ-51.21** WHEN öğrenci çözüm modunu aktifleştirdiğinde, THE Adım Adım Çözüm Sistemi SHALL her matematiksel işlemi ayrı adım olarak göstermek
22. **REQ-51.22** WHEN adımlar arasında geçiş yapıldığında, THE Adım Adım Çözüm Sistemi SHALL animasyonlu geçiş efekti kullanmak
23. **REQ-51.23** WHEN öğrenci geri gitmek istediğinde, THE Adım Adım Çözüm Sistemi SHALL önceki adıma geri dönme butonu sunmak
24. **REQ-51.24** WHEN öğrenci ileri gitmek istediğinde, THE Adım Adım Çözüm Sistemi SHALL sonraki adıma geçiş butonu sunmak
25. **REQ-51.25** WHEN adım gösterildiğinde, THE Adım Adım Çözüm Sistemi SHALL hangi matematiksel kuralın uygulandığını açıklamak
26. **REQ-51.26** WHEN öğrenci animasyon hızını ayarladığında, THE Adım Adım Çözüm Sistemi SHALL %50 ile %200 arası hız kontrolü sunmak
27. **REQ-51.27** WHEN otomatik oynatma seçildiğinde, THE Adım Adım Çözüm Sistemi SHALL tüm adımları sırasıyla otomatik göstermek
28. **REQ-51.28** WHEN öğrenci duraklatmak istediğinde, THE Adım Adım Çözüm Sistemi SHALL pause butonu ile durdurma imkanı sunmak
29. **REQ-51.29** WHEN adım numarası gösterildiğinde, THE Adım Adım Çözüm Sistemi SHALL "Adım X/Y" formatında ilerleme göstermek
30. **REQ-51.30** WHEN kritik adıma gelindiğinde, THE Adım Adım Çözüm Sistemi SHALL önemli adımları vurgulayarak işaretlemek
31. **REQ-51.31** WHEN işlem açıklaması gösterildiğinde, THE Adım Adım Çözüm Sistemi SHALL sesli anlatım (TTS) seçeneği sunmak
32. **REQ-51.32** WHEN çözüm tamamlandığında, THE Adım Adım Çözüm Sistemi SHALL çözüm özetini görsel olarak göstermek
33. **REQ-51.33** WHEN öğrenci tekrar izlemek istediğinde, THE Adım Adım Çözüm Sistemi SHALL baştan oynatma seçeneği sunmak
34. **REQ-51.34** WHEN çoklu çözüm yolu varsa, THE Adım Adım Çözüm Sistemi SHALL alternatif çözüm yollarını listelemek
35. **REQ-51.35** WHEN alternatif yol seçildiğinde, THE Adım Adım Çözüm Sistemi SHALL seçilen yolun adımlarını göstermek
36. **REQ-51.36** WHEN hata yapılabilecek adım gösterildiğinde, THE Adım Adım Çözüm Sistemi SHALL yaygın hata uyarıları göstermek
37. **REQ-51.37** WHEN formül kullanıldığında, THE Adım Adım Çözüm Sistemi SHALL formülü görsel olarak vurgulamak
38. **REQ-51.38** WHEN ara işlem yapıldığında, THE Adım Adım Çözüm Sistemi SHALL ara hesaplamaları ayrı kutucukta göstermek
39. **REQ-51.39** WHEN birim dönüşümü gerektiğinde, THE Adım Adım Çözüm Sistemi SHALL birim dönüşüm adımını ayrıca göstermek
40. **REQ-51.40** WHEN çözüm geçmişi kaydedildiğinde, THE Adım Adım Çözüm Sistemi SHALL öğrencinin izlediği çözümleri saklamak

**Hesap Makinesi ve Araçlar (REQ-51.41 - REQ-51.60)**

41. **REQ-51.41** WHEN hesap makinesi açıldığında, THE Hesap Makinesi Sistemi SHALL büyük ve okunabilir butonlar göstermek
42. **REQ-51.42** WHEN rakam girildiğinde, THE Hesap Makinesi Sistemi SHALL her rakamı sesli olarak okumak (konuşan hesap makinesi)
43. **REQ-51.43** WHEN işlem seçildiğinde, THE Hesap Makinesi Sistemi SHALL işlem sembolünü (+, -, ×, ÷) görsel olarak vurgulamak
44. **REQ-51.44** WHEN hesaplama yapıldığında, THE Hesap Makinesi Sistemi SHALL adım adım hesaplama gösterimi sunmak
45. **REQ-51.45** WHEN sonuç gösterildiğinde, THE Hesap Makinesi Sistemi SHALL sonucu büyük font ile vurgulamak
46. **REQ-51.46** WHEN işlem geçmişi görüntülendiğinde, THE Hesap Makinesi Sistemi SHALL son 20 işlemi listelemek
47. **REQ-51.47** WHEN geçmiş işlem seçildiğinde, THE Hesap Makinesi Sistemi SHALL işlemi tekrar düzenleme imkanı vermek
48. **REQ-51.48** WHEN bilimsel mod aktifleştirildiğinde, THE Hesap Makinesi Sistemi SHALL kök, üs, logaritma işlemlerini sunmak
49. **REQ-51.49** WHEN trigonometri gerektiğinde, THE Hesap Makinesi Sistemi SHALL sin, cos, tan fonksiyonlarını sunmak
50. **REQ-51.50** WHEN kesir hesabı yapıldığında, THE Hesap Makinesi Sistemi SHALL kesir giriş modu sunmak
51. **REQ-51.51** WHEN yüzde hesabı yapıldığında, THE Hesap Makinesi Sistemi SHALL yüzde hesaplama modunu sunmak
52. **REQ-51.52** WHEN grafik çizici açıldığında, THE Grafik Aracı SHALL x-y koordinat sistemini interaktif olarak sunmak
53. **REQ-51.53** WHEN fonksiyon girildiğinde, THE Grafik Aracı SHALL fonksiyonu gerçek zamanlı olarak çizmek
54. **REQ-51.54** WHEN grafik yakınlaştırıldığında, THE Grafik Aracı SHALL zoom in/out özelliği sunmak
55. **REQ-51.55** WHEN birim dönüştürücü açıldığında, THE Birim Aracı SHALL uzunluk, alan, hacim, ağırlık kategorilerini sunmak
56. **REQ-51.56** WHEN birim seçildiğinde, THE Birim Aracı SHALL otomatik dönüşüm sonucunu göstermek
57. **REQ-51.57** WHEN çarpım tablosu açıldığında, THE Çarpım Tablosu Aracı SHALL 1-12 arası interaktif tablo sunmak
58. **REQ-51.58** WHEN çarpım sorulduğunda, THE Çarpım Tablosu Aracı SHALL görsel kutucuk vurgulama ile cevabı göstermek
59. **REQ-51.59** WHEN hesaplama doğrulandığında, THE Hesap Makinesi Sistemi SHALL doğru/yanlış geri bildirimi vermek
60. **REQ-51.60** WHEN araç tercihi kaydedildiğinde, THE Hesap Makinesi Sistemi SHALL kullanıcı tercihlerini saklamak

**Renkli Kodlama Sistemi (REQ-51.61 - REQ-51.80)**

61. **REQ-51.61** WHEN pozitif sayı gösterildiğinde, THE Renkli Kodlama Sistemi SHALL mavi renk ile işaretlemek
62. **REQ-51.62** WHEN negatif sayı gösterildiğinde, THE Renkli Kodlama Sistemi SHALL kırmızı renk ile işaretlemek
63. **REQ-51.63** WHEN sıfır gösterildiğinde, THE Renkli Kodlama Sistemi SHALL gri renk ile işaretlemek
64. **REQ-51.64** WHEN toplama işlemi gösterildiğinde, THE Renkli Kodlama Sistemi SHALL yeşil renk ile vurgulamak
65. **REQ-51.65** WHEN çıkarma işlemi gösterildiğinde, THE Renkli Kodlama Sistemi SHALL turuncu renk ile vurgulamak
66. **REQ-51.66** WHEN çarpma işlemi gösterildiğinde, THE Renkli Kodlama Sistemi SHALL mor renk ile vurgulamak
67. **REQ-51.67** WHEN bölme işlemi gösterildiğinde, THE Renkli Kodlama Sistemi SHALL sarı renk ile vurgulamak
68. **REQ-51.68** WHEN parantez seviyesi 1 ise, THE Renkli Kodlama Sistemi SHALL açık mavi ile işaretlemek
69. **REQ-51.69** WHEN parantez seviyesi 2 ise, THE Renkli Kodlama Sistemi SHALL açık yeşil ile işaretlemek
70. **REQ-51.70** WHEN parantez seviyesi 3+ ise, THE Renkli Kodlama Sistemi SHALL açık sarı ile işaretlemek
71. **REQ-51.71** WHEN değişken x gösterildiğinde, THE Renkli Kodlama Sistemi SHALL tutarlı renk (pembe) ile işaretlemek
72. **REQ-51.72** WHEN değişken y gösterildiğinde, THE Renkli Kodlama Sistemi SHALL tutarlı renk (turkuaz) ile işaretlemek
73. **REQ-51.73** WHEN sabit sayılar gösterildiğinde, THE Renkli Kodlama Sistemi SHALL farklı renk (koyu gri) ile ayırmak
74. **REQ-51.74** WHEN benzer terimler gösterildiğinde, THE Renkli Kodlama Sistemi SHALL aynı renk ile gruplamak
75. **REQ-51.75** WHEN işlem önceliği gösterildiğinde, THE Renkli Kodlama Sistemi SHALL öncelikli işlemi vurgulu renk ile göstermek
76. **REQ-51.76** WHEN hata yapıldığında, THE Renkli Kodlama Sistemi SHALL hatalı kısmı kırmızı arka plan ile göstermek
77. **REQ-51.77** WHEN doğru cevap verildiğinde, THE Renkli Kodlama Sistemi SHALL yeşil arka plan ile onaylamak
78. **REQ-51.78** WHEN renk şeması özelleştirildiğinde, THE Renkli Kodlama Sistemi SHALL alternatif renk paletleri sunmak
79. **REQ-51.79** WHEN renk körlüğü modu aktifleştirildiğinde, THE Renkli Kodlama Sistemi SHALL renk körlüğü dostu palet sunmak
80. **REQ-51.80** WHEN renk tercihi kaydedildiğinde, THE Renkli Kodlama Sistemi SHALL kullanıcı tercihlerini saklamak

**Manipülatifler ve İnteraktif Araçlar (REQ-51.81 - REQ-51.100)**

81. **REQ-51.81** WHEN VirtualBlocks açıldığında, THE Manipülatif Sistemi SHALL sürüklenebilir sanal bloklar sunmak
82. **REQ-51.82** WHEN bloklar birleştirildiğinde, THE Manipülatif Sistemi SHALL toplama animasyonu göstermek
83. **REQ-51.83** WHEN bloklar ayrıldığında, THE Manipülatif Sistemi SHALL çıkarma animasyonu göstermek
84. **REQ-51.84** WHEN blok grubu oluşturulduğunda, THE Manipülatif Sistemi SHALL çarpma kavramını görselleştirmek
85. **REQ-51.85** WHEN blok grubu bölündüğünde, THE Manipülatif Sistemi SHALL bölme kavramını görselleştirmek
86. **REQ-51.86** WHEN GeoGebra embed edildiğinde, THE Manipülatif Sistemi SHALL interaktif geometri ortamı sunmak
87. **REQ-51.87** WHEN geometri aracı kullanıldığında, THE Manipülatif Sistemi SHALL çizgi, açı, şekil çizim araçları sunmak
88. **REQ-51.88** WHEN şekil oluşturulduğunda, THE Manipülatif Sistemi SHALL otomatik ölçüm hesaplaması yapmak
89. **REQ-51.89** WHEN InteractiveGeometry açıldığında, THE Manipülatif Sistemi SHALL dokunmatik ekran desteği sunmak
90. **REQ-51.90** WHEN şekil döndürüldüğünde, THE Manipülatif Sistemi SHALL açı değişimini anlık göstermek
91. **REQ-51.91** WHEN şekil ölçeklendiğinde, THE Manipülatif Sistemi SHALL oran değişimini anlık göstermek
92. **REQ-51.92** WHEN DigitalTangram açıldığında, THE Manipülatif Sistemi SHALL 7 tangram parçasını sunmak
93. **REQ-51.93** WHEN tangram parçası döndürüldüğünde, THE Manipülatif Sistemi SHALL 15 derecelik adımlarla döndürmek
94. **REQ-51.94** WHEN tangram şekli tamamlandığında, THE Manipülatif Sistemi SHALL başarı animasyonu göstermek
95. **REQ-51.95** WHEN sayı doğrusu açıldığında, THE Manipülatif Sistemi SHALL interaktif sayı doğrusu sunmak
96. **REQ-51.96** WHEN sayı doğrusunda nokta işaretlendiğinde, THE Manipülatif Sistemi SHALL sayı değerini göstermek
97. **REQ-51.97** WHEN kesir pizzası açıldığında, THE Manipülatif Sistemi SHALL dilimlenebilir pizza görselı sunmak
98. **REQ-51.98** WHEN pizza dilimlendiğinde, THE Manipülatif Sistemi SHALL kesir değerini otomatik hesaplamak
99. **REQ-51.99** WHEN manipülatif aktivitesi kaydedildiğinde, THE Manipülatif Sistemi SHALL öğrenci aktivite logunu tutmak
100. **REQ-51.100** WHEN manipülatif tercihi kaydedildiğinde, THE Manipülatif Sistemi SHALL kullanıcı tercihlerini saklamak

---

**Kabul Kriterleri Özeti:**
- ✅ REQ-51.1 - REQ-51.5: Sayı Blokları (Base-10 blocks, interaktif manipülasyon)
- ✅ REQ-51.6 - REQ-51.10: Kesir Çubukları (fraction bars, denk kesir görselleştirme)
- ✅ REQ-51.11 - REQ-51.15: Geometrik Şekiller 3D (3D rendering, rotasyon, ölçüm araçları)
- ✅ REQ-51.16 - REQ-51.20: Grafik Çizim (fonksiyon plotting, interaktif manipülasyon)
- ✅ REQ-51.21 - REQ-51.40: Adım Adım Çözüm Sistemi (animasyonlu geçişler, tempo kontrolü)
- ✅ REQ-51.41 - REQ-51.60: Hesap Makinesi ve Araçlar (konuşan hesap makinesi, grafik çizici)
- ✅ REQ-51.61 - REQ-51.80: Renkli Kodlama (pozitif/negatif, işlem renkleri, parantez seviyeleri)
- ✅ REQ-51.81 - REQ-51.100: Manipülatifler (VirtualBlocks, GeoGebra, Tangram, NumberLine)

**Toplam Kriter Sayısı:** 100 kriter

**Teknoloji Stack:**
- **3D Rendering**: Three.js, React Three Fiber
- **2D Graphics**: D3.js, Plotly.js, Canvas API
- **Animation**: Framer Motion, GSAP
- **Math Engine**: Math.js, Algebrite

**Erişilebilirlik:**
- WCAG 2.1 Level AA uyumlu
- Klavye navigasyonu desteği
- Ekran okuyucu uyumlu açıklamalar
- Yüksek kontrast mod desteği

**Performans Hedefleri:**
- 3D render: < 16ms (60 FPS)
- Grafik çizimi: < 100ms
- Animasyon: Smooth 60 FPS
- Interaktif yanıt: < 50ms


---

### REQ-52: DEHB Desteği - Dikkat Yönetimi ve Odaklanma Sistemi

**Kullanıcı Hikayesi:** DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) tanısı olan bir öğrenci olarak, dikkatimi yönetmeme ve odaklanmama yardımcı olacak araçlar kullanmak istiyorum, böylece çalışma verimliliğimi artırabilir ve öğrenme hedeflerime ulaşabilirim.

#### Kabul Kriterleri

**Pomodoro Timer ve Zaman Yönetimi (REQ-52.1 - REQ-52.10)**

1. **REQ-52.1** WHEN öğrenci çalışma oturumu başlattığında, THE DEHB Destek Sistemi SHALL özelleştirilebilir Pomodoro timer (varsayılan: 25dk çalışma, 5dk mola) sunmak
2. **REQ-52.2** WHEN zamanlayıcı çalıştığında, THE DEHB Destek Sistemi SHALL görsel countdown, progress ring ve kalan süreyi büyük fontla göstermek
3. **REQ-52.3** WHEN çalışma süresi özelleştirildiğinde, THE DEHB Destek Sistemi SHALL 5-60 dakika arası özel süre ayarına izin vermek
4. **REQ-52.4** WHEN mola zamanı geldiğinde, THE DEHB Destek Sistemi SHALL nazik ses ve görsel bildirim ile hatırlatmak
5. **REQ-52.5** WHEN 4 pomodoro tamamlandığında, THE DEHB Destek Sistemi SHALL uzun mola (15-30dk) önermek
6. **REQ-52.6** WHEN öğrenci timer istatistiklerini görüntülediğinde, THE DEHB Destek Sistemi SHALL günlük/haftalık/aylık odaklanma sürelerini grafikle göstermek
7. **REQ-52.7** WHEN timer aktifken, THE DEHB Destek Sistemi SHALL tam ekran modunda dikkat dağıtıcı unsurları gizlemek
8. **REQ-52.8** WHEN öğrenci erken bitirmek istediğinde, THE DEHB Destek Sistemi SHALL kalan süreyi kaydetme seçeneği sunmak
9. **REQ-52.9** WHEN mola süresinde, THE DEHB Destek Sistemi SHALL hareket/germe egzersizleri önermek
10. **REQ-52.10** WHEN günlük hedef belirlendiğinde, THE DEHB Destek Sistemi SHALL hedef pomodoro sayısını takip etmek ve ilerleme göstermek

**Focus Mode ve Dikkat Dağınıklığı Önleme (REQ-52.11 - REQ-52.20)**

11. **REQ-52.11** WHEN focus mode aktifleştirildiğinde, THE DEHB Destek Sistemi SHALL sadece aktif görevi ve ilgili içeriği göstermek
12. **REQ-52.12** WHEN focus mode aktifken, THE DEHB Destek Sistemi SHALL navigasyon menüsünü minimize etmek veya gizlemek
13. **REQ-52.13** WHEN focus mode aktifken, THE DEHB Destek Sistemi SHALL platform bildirimlerini sessize almak
14. **REQ-52.14** WHEN öğrenci ekran dışına tıkladığında, THE DEHB Destek Sistemi SHALL nazik geri dönüş hatırlatıcısı göstermek
15. **REQ-52.15** WHEN inaktivite tespit edildiğinde (2dk), THE DEHB Destek Sistemi SHALL "Hala burada mısın?" popup göstermek
16. **REQ-52.16** WHEN öğrenci çalışma sayfasından ayrıldığında, THE DEHB Destek Sistemi SHALL otomatik duraklatma yapmak
17. **REQ-52.17** WHEN minimal arayüz seçildiğinde, THE DEHB Destek Sistemi SHALL sadece soru ve cevap seçeneklerini göstermek
18. **REQ-52.18** WHEN öğrenci dikkat dağınıklığı yaşadığında, THE DEHB Destek Sistemi SHALL "Bir nefes al" kısa mola önerisi sunmak
19. **REQ-52.19** WHEN görsel gürültü azaltıldığında, THE DEHB Destek Sistemi SHALL sade renk paleti ve minimal animasyon kullanmak
20. **REQ-52.20** WHEN focus streak başarıldığında, THE DEHB Destek Sistemi SHALL başarıyı kutlamak ve motivasyon puanı vermek

**Görev Parçalama ve Organizasyon (REQ-52.21 - REQ-52.35)**

21. **REQ-52.21** WHEN büyük görev tespit edildiğinde, THE DEHB Destek Sistemi SHALL otomatik alt görevlere bölme önermek
22. **REQ-52.22** WHEN görev parçalandığında, THE DEHB Destek Sistemi SHALL her alt görevi checkbox ile listelemek
23. **REQ-52.23** WHEN alt görev tamamlandığında, THE DEHB Destek Sistemi SHALL anında görsel geri bildirim (confetti, tick animasyonu) vermek
24. **REQ-52.24** WHEN görev listesi görüntülendiğinde, THE DEHB Destek Sistemi SHALL öncelik sıralaması (acil/önemli/normal) sunmak
25. **REQ-52.25** WHEN görevler sıralandığında, THE DEHB Destek Sistemi SHALL drag-and-drop ile yeniden sıralama imkanı vermek
26. **REQ-52.26** WHEN deadline yaklaştığında, THE DEHB Destek Sistemi SHALL renkli uyarı (kırmızı=acil, sarı=yakın, yeşil=rahat) göstermek
27. **REQ-52.27** WHEN ilerleme gösterildiğinde, THE DEHB Destek Sistemi SHALL görsel progress bar ve yüzde ile göstermek
28. **REQ-52.28** WHEN görev tamamlanamadığında, THE DEHB Destek Sistemi SHALL "Yarın devam et" seçeneği sunmak
29. **REQ-52.29** WHEN günlük plan yapıldığında, THE DEHB Destek Sistemi SHALL gerçekçi süre tahminleri önermek
30. **REQ-52.30** WHEN öğrenci hedef belirlerken, THE DEHB Destek Sistemi SHALL SMART hedef formatı önermek
31. **REQ-52.31** WHEN görev ertelendiğinde, THE DEHB Destek Sistemi SHALL erteleme nedenini nazikçe sormak (analiz için)
32. **REQ-52.32** WHEN rutin oluşturulduğunda, THE DEHB Destek Sistemi SHALL günlük hatırlatıcılar ayarlamak
33. **REQ-52.33** WHEN başlangıç zorluğu yaşandığında, THE DEHB Destek Sistemi SHALL "İlk 2 dakika kuralı" önermek
34. **REQ-52.34** WHEN micro-task tamamlandığında, THE DEHB Destek Sistemi SHALL küçük ödül (emoji, ses) vermek
35. **REQ-52.35** WHEN haftalık plan görüntülendiğinde, THE DEHB Destek Sistemi SHALL görsel takvim ile görevleri göstermek

**Motivasyon ve Ödül Sistemi (REQ-52.36 - REQ-52.50)**

36. **REQ-52.36** WHEN görev tamamlandığında, THE DEHB Destek Sistemi SHALL anında kutlama animasyonu göstermek
37. **REQ-52.37** WHEN puan kazanıldığında, THE DEHB Destek Sistemi SHALL sesli ve görsel puan artış efekti vermek
38. **REQ-52.38** WHEN streak devam ettiğinde, THE DEHB Destek Sistemi SHALL "X gün üst üste" rozeti göstermek
39. **REQ-52.39** WHEN günlük hedef tamamlandığında, THE DEHB Destek Sistemi SHALL özel günlük başarı rozeti vermek
40. **REQ-52.40** WHEN kişisel rekor kırıldığında, THE DEHB Destek Sistemi SHALL "Yeni Rekor!" kutlaması yapmak
41. **REQ-52.41** WHEN ilerleme grafiği görüntülendiğinde, THE DEHB Destek Sistemi SHALL pozitif trend vurgulamak
42. **REQ-52.42** WHEN zor görev tamamlandığında, THE DEHB Destek Sistemi SHALL ekstra bonus puan vermek
43. **REQ-52.43** WHEN haftalık özet hazırlandığında, THE DEHB Destek Sistemi SHALL başarıları vurgulayan rapor sunmak
44. **REQ-52.44** WHEN motivasyon düştüğünde, THE DEHB Destek Sistemi SHALL motivasyonel alıntılar göstermek
45. **REQ-52.45** WHEN başarı paylaşıldığında, THE DEHB Destek Sistemi SHALL sosyal medya paylaşım seçeneği sunmak
46. **REQ-52.46** WHEN avatar özelleştirme açıldığında, THE DEHB Destek Sistemi SHALL kazanılan itemlerle özelleştirme imkanı vermek
47. **REQ-52.47** WHEN mini-oyun açıldığında, THE DEHB Destek Sistemi SHALL eğitici mola oyunları sunmak
48. **REQ-52.48** WHEN arkadaş eklediğinde, THE DEHB Destek Sistemi SHALL birlikte çalışma seçeneği sunmak
49. **REQ-52.49** WHEN lider tahtası görüntülendiğinde, THE DEHB Destek Sistemi SHALL benzer seviyedeki öğrencilerle karşılaştırma göstermek
50. **REQ-52.50** WHEN ödül mağazası açıldığında, THE DEHB Destek Sistemi SHALL puanla satın alınabilir öğeler sunmak

**Hareket ve Mola Yönetimi (REQ-52.51 - REQ-52.60)**

51. **REQ-52.51** WHEN uzun oturma tespit edildiğinde (45dk), THE DEHB Destek Sistemi SHALL hareket molası önermek
52. **REQ-52.52** WHEN mola egzersizi seçildiğinde, THE DEHB Destek Sistemi SHALL 2-5 dakikalık germe/hareket videosu göstermek
53. **REQ-52.53** WHEN nefes egzersizi başlatıldığında, THE DEHB Destek Sistemi SHALL animasyonlu nefes rehberi sunmak
54. **REQ-52.54** WHEN enerji seviyesi sorulduğunda, THE DEHB Destek Sistemi SHALL 1-5 arası emoji ölçeği göstermek
55. **REQ-52.55** WHEN düşük enerji bildirildiğinde, THE DEHB Destek Sistemi SHALL kısa mola veya hafif aktivite önermek
56. **REQ-52.56** WHEN yüksek enerji bildirildiğinde, THE DEHB Destek Sistemi SHALL yoğun çalışma oturumu önermek
57. **REQ-52.57** WHEN beyin jimnastiği istendiğinde, THE DEHB Destek Sistemi SHALL hızlı bilmece veya puzzle sunmak
58. **REQ-52.58** WHEN su içme hatırlatıcısı aktifleştirildiğinde, THE DEHB Destek Sistemi SHALL her saat başı nazik hatırlatma vermek
59. **REQ-52.59** WHEN göz molası zamanı geldiğinde, THE DEHB Destek Sistemi SHALL 20-20-20 kuralını hatırlatmak
60. **REQ-52.60** WHEN çalışma/mola oranı analiz edildiğinde, THE DEHB Destek Sistemi SHALL optimal oran önerileri sunmak

**Öğrenme Stratejileri ve Adaptasyon (REQ-52.61 - REQ-52.70)**

61. **REQ-52.61** WHEN yeni konu başladığında, THE DEHB Destek Sistemi SHALL çoklu öğrenme formatı seçeneği (video/metin/interaktif) sunmak
62. **REQ-52.62** WHEN dikkat süresi analiz edildiğinde, THE DEHB Destek Sistemi SHALL kişiye özel oturum süreleri önermek
63. **REQ-52.63** WHEN öğrenme tarzı tespit edildiğinde, THE DEHB Destek Sistemi SHALL içerik formatını adapte etmek
64. **REQ-52.64** WHEN metin uzunluğu ayarlandığında, THE DEHB Destek Sistemi SHALL paragrafları kısa tutmak (max 3-4 cümle)
65. **REQ-52.65** WHEN görselleştirme tercih edildiğinde, THE DEHB Destek Sistemi SHALL her konuyu infografik ile desteklemek
66. **REQ-52.66** WHEN sesli öğrenme tercih edildiğinde, THE DEHB Destek Sistemi SHALL tüm içeriği TTS ile okumak
67. **REQ-52.67** WHEN interaktif öğrenme tercih edildiğinde, THE DEHB Destek Sistemi SHALL quiz ve oyunlaştırılmış içerik sunmak
68. **REQ-52.68** WHEN tekrar stratejisi belirlendiğinde, THE DEHB Destek Sistemi SHALL aralıklı tekrar programı oluşturmak
69. **REQ-52.69** WHEN zor konu tespit edildiğinde, THE DEHB Destek Sistemi SHALL alternatif açıklama kaynakları önermek
70. **REQ-52.70** WHEN başarı oranı düşükse, THE DEHB Destek Sistemi SHALL zorluk seviyesini otomatik ayarlamak

**Raporlama ve Analitik (REQ-52.71 - REQ-52.80)**

71. **REQ-52.71** WHEN günlük özet görüntülendiğinde, THE DEHB Destek Sistemi SHALL toplam odaklanma süresi, görev sayısı ve başarı oranını göstermek
72. **REQ-52.72** WHEN haftalık rapor oluşturulduğunda, THE DEHB Destek Sistemi SHALL trend analizi ile gelişim grafiği sunmak
73. **REQ-52.73** WHEN optimal çalışma saatleri analiz edildiğinde, THE DEHB Destek Sistemi SHALL kişinin en verimli saatlerini belirlemek
74. **REQ-52.74** WHEN dikkat dağınıklığı kalıbı tespit edildiğinde, THE DEHB Destek Sistemi SHALL tetikleyici faktörleri raporlamak
75. **REQ-52.75** WHEN hedef başarı oranı hesaplandığında, THE DEHB Destek Sistemi SHALL gerçekçi hedef önerileri sunmak
76. **REQ-52.76** WHEN ebeveyn/öğretmen erişimi istendiğinde, THE DEHB Destek Sistemi SHALL paylaşılabilir özet rapor oluşturmak
77. **REQ-52.77** WHEN DEHB stratejileri değerlendirildiğinde, THE DEHB Destek Sistemi SHALL hangilerinin işe yaradığını göstermek
78. **REQ-52.78** WHEN ilerleme karşılaştırıldığında, THE DEHB Destek Sistemi SHALL önceki dönemlerle mukayese grafiği sunmak
79. **REQ-52.79** WHEN motivasyon seviyesi izlendiğinde, THE DEHB Destek Sistemi SHALL duygu durumu trend analizi göstermek
80. **REQ-52.80** WHEN öneriler oluşturulduğunda, THE DEHB Destek Sistemi SHALL AI tabanlı kişisel iyileştirme tavsiyeleri sunmak

**Duyusal ve Çevresel Ayarlar (REQ-52.81 - REQ-52.90)**

81. **REQ-52.81** WHEN beyaz gürültü seçeneği açıldığında, THE DEHB Destek Sistemi SHALL odaklanma için arka plan sesleri sunmak
82. **REQ-52.82** WHEN müzik tercihi belirlendiğinde, THE DEHB Destek Sistemi SHALL enstrümantal çalışma müzikleri sunmak
83. **REQ-52.83** WHEN ses hassasiyeti ayarlandığında, THE DEHB Destek Sistemi SHALL tüm ses efektlerini kişiselleştirmek
84. **REQ-52.84** WHEN renk duyarlılığı bildirildiğinde, THE DEHB Destek Sistemi SHALL sakin renk paleti seçeneği sunmak
85. **REQ-52.85** WHEN görsel hassasiyet varsa, THE DEHB Destek Sistemi SHALL düşük kontrast mod sunmak
86. **REQ-52.86** WHEN animasyon azaltma istendiğinde, THE DEHB Destek Sistemi SHALL reduced motion mod aktiflemek
87. **REQ-52.87** WHEN gece modu aktifleştirildiğinde, THE DEHB Destek Sistemi SHALL mavi ışık filtresi uygulamak
88. **REQ-52.88** WHEN font büyüklüğü ayarlandığında, THE DEHB Destek Sistemi SHALL tüm metinleri orantılı büyütmek
89. **REQ-52.89** WHEN satır aralığı artırıldığında, THE DEHB Destek Sistemi SHALL okunabilirliği optimize etmek
90. **REQ-52.90** WHEN özel tema oluşturulduğunda, THE DEHB Destek Sistemi SHALL kullanıcı tercihlerini kaydetmek

**Sosyal ve Destek Özellikleri (REQ-52.91 - REQ-52.100)**

91. **REQ-52.91** WHEN çalışma arkadaşı eşleştirildiğinde, THE DEHB Destek Sistemi SHALL benzer hedefleri olan öğrencileri bağlamak
92. **REQ-52.92** WHEN grup çalışması başlatıldığında, THE DEHB Destek Sistemi SHALL paylaşımlı timer ve hedef göstermek
93. **REQ-52.93** WHEN motivasyon desteği istendiğinde, THE DEHB Destek Sistemi SHALL canlı motivasyon koçu (AI) sunmak
94. **REQ-52.94** WHEN topluluk forumu açıldığında, THE DEHB Destek Sistemi SHALL DEHB öğrencileri destek grubunu göstermek
95. **REQ-52.95** WHEN başarı hikayesi paylaşıldığında, THE DEHB Destek Sistemi SHALL anonim başarı hikayeleri platformu sunmak
96. **REQ-52.96** WHEN ebeveyn modu aktifleştirildiğinde, THE DEHB Destek Sistemi SHALL çocuk ilerlemesi dashboard göstermek
97. **REQ-52.97** WHEN öğretmen bağlantısı kurulduğunda, THE DEHB Destek Sistemi SHALL ödev ve ilerleme entegrasyonu sağlamak
98. **REQ-52.98** WHEN acil yardım butonu tıklandığında, THE DEHB Destek Sistemi SHALL hızlı destek kaynakları sunmak
99. **REQ-52.99** WHEN DEHB kaynakları görüntülendiğinde, THE DEHB Destek Sistemi SHALL eğitici içerik ve ipuçları sunmak
100. **REQ-52.100** WHEN geri bildirim verildiğinde, THE DEHB Destek Sistemi SHALL sistem iyileştirme önerileri toplamak

---

**REQ-52 Özet:**
- ✅ REQ-52.1 - REQ-52.10: Pomodoro Timer ve Zaman Yönetimi
- ✅ REQ-52.11 - REQ-52.20: Focus Mode ve Dikkat Dağınıklığı Önleme
- ✅ REQ-52.21 - REQ-52.35: Görev Parçalama ve Organizasyon
- ✅ REQ-52.36 - REQ-52.50: Motivasyon ve Ödül Sistemi
- ✅ REQ-52.51 - REQ-52.60: Hareket ve Mola Yönetimi
- ✅ REQ-52.61 - REQ-52.70: Öğrenme Stratejileri ve Adaptasyon
- ✅ REQ-52.71 - REQ-52.80: Raporlama ve Analitik
- ✅ REQ-52.81 - REQ-52.90: Duyusal ve Çevresel Ayarlar
- ✅ REQ-52.91 - REQ-52.100: Sosyal ve Destek Özellikleri

**Toplam Kriter Sayısı:** 100 kriter

---

### REQ-53: OSB Desteği - Öngörülebilir Arayüz ve Duyusal Adaptasyon

**Kullanıcı Hikayesi:** Otizm Spektrum Bozukluğu (OSB) tanısı olan bir öğrenci olarak, tutarlı, öngörülebilir ve duyusal açıdan rahat bir arayüz kullanmak istiyorum, böylece değişikliklerden rahatsız olmadan güvenle öğrenebilir ve çalışabilirim.

#### Kabul Kriterleri

**Tutarlı ve Öngörülebilir Arayüz (REQ-53.1 - REQ-53.15)**

1. **REQ-53.1** WHEN Platform arayüzü tasarlandığında, THE OSB Destek Sistemi SHALL tüm sayfalarda aynı düzen yapısını korumak
2. **REQ-53.2** WHEN navigasyon menüsü gösterildiğinde, THE OSB Destek Sistemi SHALL sabit ve değişmeyen menü pozisyonları sağlamak
3. **REQ-53.3** WHEN renk şeması uygulandığında, THE OSB Destek Sistemi SHALL tutarlı ve değişmeyen renk paleti kullanmak
4. **REQ-53.4** WHEN ikonlar gösterildiğinde, THE OSB Destek Sistemi SHALL standart ve evrensel anlaşılır ikonlar kullanmak
5. **REQ-53.5** WHEN buton stili belirlediğinde, THE OSB Destek Sistemi SHALL tüm platformda aynı buton tasarımını korumak
6. **REQ-53.6** WHEN metin formatı uygulandığında, THE OSB Destek Sistemi SHALL tutarlı font ve boyut kullanmak
7. **REQ-53.7** WHEN sayfa geçişi yapıldığında, THE OSB Destek Sistemi SHALL ani değişiklikler yerine yumuşak geçişler kullanmak
8. **REQ-53.8** WHEN modal/popup gösterildiğinde, THE OSB Destek Sistemi SHALL her zaman aynı pozisyon ve stilde açmak
9. **REQ-53.9** WHEN hata mesajı gösterildiğinde, THE OSB Destek Sistemi SHALL standart format ve konum kullanmak
10. **REQ-53.10** WHEN başarı bildirimi gösterildiğinde, THE OSB Destek Sistemi SHALL öngörülebilir kutlama formatı kullanmak
11. **REQ-53.11** WHEN loading durumu gösterildiğinde, THE OSB Destek Sistemi SHALL tutarlı loading animasyonu kullanmak
12. **REQ-53.12** WHEN form tasarlandığında, THE OSB Destek Sistemi SHALL standart form elemanı yerleşimi kullanmak
13. **REQ-53.13** WHEN geri butonu kullanıldığında, THE OSB Destek Sistemi SHALL her zaman önceki sayfaya dönmek
14. **REQ-53.14** WHEN breadcrumb gösterildiğinde, THE OSB Destek Sistemi SHALL açık ve anlaşılır yol haritası sunmak
15. **REQ-53.15** WHEN sayfa yenilenmesinde, THE OSB Destek Sistemi SHALL aynı konumda ve durumda kalmayı sağlamak

**Görsel Programlar ve Rutinler (REQ-53.16 - REQ-53.30)**

16. **REQ-53.16** WHEN günlük program gösterildiğinde, THE OSB Destek Sistemi SHALL görsel timeline ile aktiviteleri listelemek
17. **REQ-53.17** WHEN haftalık takvim görüntülendiğinde, THE OSB Destek Sistemi SHALL renkli ve görsel takvim sunmak
18. **REQ-53.18** WHEN aktivite planlandığında, THE OSB Destek Sistemi SHALL aktivite için ikon ve renk atamak
19. **REQ-53.19** WHEN aktivite yaklaştığında, THE OSB Destek Sistemi SHALL önceden bildirim vermek (15dk, 5dk, 1dk)
20. **REQ-53.20** WHEN aktivite geçişi olduğunda, THE OSB Destek Sistemi SHALL görsel countdown ve hazırlık hatırlatması yapmak
21. **REQ-53.21** WHEN rutin değişikliği olduğunda, THE OSB Destek Sistemi SHALL önceden uyarı ve açıklama vermek
22. **REQ-53.22** WHEN beklenmeyen değişiklik olduğunda, THE OSB Destek Sistemi SHALL görsel "değişiklik kartı" göstermek
23. **REQ-53.23** WHEN sosyal hikaye gerektiğinde, THE OSB Destek Sistemi SHALL görsel sosyal hikaye formatı sunmak
24. **REQ-53.24** WHEN görev adımları gösterildiğinde, THE OSB Destek Sistemi SHALL numaralı ve görsel adım listesi sunmak
25. **REQ-53.25** WHEN tamamlanan adım işaretlendiğinde, THE OSB Destek Sistemi SHALL görsel check işareti göstermek
26. **REQ-53.26** WHEN ilerleme gösterildiğinde, THE OSB Destek Sistemi SHALL net yüzde ve görsel bar kullanmak
27. **REQ-53.27** WHEN timer görüntülendiğinde, THE OSB Destek Sistemi SHALL analog ve dijital saat seçeneği sunmak
28. **REQ-53.28** WHEN geçiş zamanı yaklaştığında, THE OSB Destek Sistemi SHALL "first-then" kartı göstermek
29. **REQ-53.29** WHEN ödül zamanı geldiğinde, THE OSB Destek Sistemi SHALL "iş bitti, şimdi X" görsel kartı göstermek
30. **REQ-53.30** WHEN rutin kaydedildiğinde, THE OSB Destek Sistemi SHALL kişisel rutin şablonları oluşturmak

**Net ve Açık Talimatlar (REQ-53.31 - REQ-53.45)**

31. **REQ-53.31** WHEN talimat yazıldığında, THE OSB Destek Sistemi SHALL basit ve kısa cümleler (max 10-15 kelime) kullanmak
32. **REQ-53.32** WHEN görev açıklandığında, THE OSB Destek Sistemi SHALL belirsiz ifadelerden kaçınmak ("bazı", "birkaç", "biraz")
33. **REQ-53.33** WHEN sayı belirtildiğinde, THE OSB Destek Sistemi SHALL kesin rakamlar kullanmak ("3 soru çöz")
34. **REQ-53.34** WHEN zaman belirtildiğinde, THE OSB Destek Sistemi SHALL kesin süre vermek ("10 dakika")
35. **REQ-53.35** WHEN çoklu adım varsa, THE OSB Destek Sistemi SHALL numaralı liste formatı kullanmak
36. **REQ-53.36** WHEN soru sorulduğunda, THE OSB Destek Sistemi SHALL tek bir net soru sormak
37. **REQ-53.37** WHEN seçenek sunulduğunda, THE OSB Destek Sistemi SHALL sınırlı sayıda (2-4) net seçenek göstermek
38. **REQ-53.38** WHEN örnek verildiğinde, THE OSB Destek Sistemi SHALL görsel örnek ile desteklemek
39. **REQ-53.39** WHEN kavram açıklandığında, THE OSB Destek Sistemi SHALL somut ve elle tutulur örnekler kullanmak
40. **REQ-53.40** WHEN mecaz kullanıldığında, THE OSB Destek Sistemi SHALL literal açıklama eklemek
41. **REQ-53.41** WHEN deyim kullanıldığında, THE OSB Destek Sistemi SHALL gerçek anlam açıklaması vermek
42. **REQ-53.42** WHEN ironi/şaka yapıldığında, THE OSB Destek Sistemi SHALL "bu bir şaka" etiketi eklemek
43. **REQ-53.43** WHEN önemli bilgi vurgulandığında, THE OSB Destek Sistemi SHALL görsel işaretleyici kullanmak
44. **REQ-53.44** WHEN beklenti açıklandığında, THE OSB Destek Sistemi SHALL "yapılması gereken" listesi vermek
45. **REQ-53.45** WHEN sonraki adım belirtildiğinde, THE OSB Destek Sistemi SHALL açık "sonra ne olacak" bilgisi vermek

**Duyusal Yük Azaltma (REQ-53.46 - REQ-53.60)**

46. **REQ-53.46** WHEN animasyon ayarlandığında, THE OSB Destek Sistemi SHALL animasyon kapatma seçeneği sunmak
47. **REQ-53.47** WHEN ses ayarlandığında, THE OSB Destek Sistemi SHALL tüm sesleri kapatma seçeneği sunmak
48. **REQ-53.48** WHEN video otomatik oynatma kapatıldığında, THE OSB Destek Sistemi SHALL kullanıcı onayı ile oynatmak
49. **REQ-53.49** WHEN parlak renk ayarlandığında, THE OSB Destek Sistemi SHALL yumuşak renk paleti seçeneği sunmak
50. **REQ-53.50** WHEN arka plan seçildiğinde, THE OSB Destek Sistemi SHALL düz ve sakin arka plan seçenekleri sunmak
51. **REQ-53.51** WHEN görsel karmaşıklık azaltıldığında, THE OSB Destek Sistemi SHALL minimal UI modu sunmak
52. **REQ-53.52** WHEN popup sıklığı ayarlandığında, THE OSB Destek Sistemi SHALL popup azaltma seçeneği sunmak
53. **REQ-53.53** WHEN bildirim sıklığı ayarlandığında, THE OSB Destek Sistemi SHALL bildirim filtreleme sunmak
54. **REQ-53.54** WHEN flash/yanıp sönen içerik varsa, THE OSB Destek Sistemi SHALL otomatik engellemek
55. **REQ-53.55** WHEN hareket eden öğe varsa, THE OSB Destek Sistemi SHALL durdurma butonu sunmak
56. **REQ-53.56** WHEN kontrast ayarlandığında, THE OSB Destek Sistemi SHALL düşük kontrast modu sunmak
57. **REQ-53.57** WHEN beyaz alan artırıldığında, THE OSB Destek Sistemi SHALL elementler arası boşluğu genişletmek
58. **REQ-53.58** WHEN metin yoğunluğu azaltıldığında, THE OSB Destek Sistemi SHALL paragraf başına max 3-4 cümle sunmak
59. **REQ-53.59** WHEN görsel filtre uygulandığında, THE OSB Destek Sistemi SHALL mavi ışık filtresi sunmak
60. **REQ-53.60** WHEN duyusal profil oluşturulduğunda, THE OSB Destek Sistemi SHALL kişisel duyusal tercihleri kaydetmek

**Sosyal İletişim Desteği (REQ-53.61 - REQ-53.70)**

61. **REQ-53.61** WHEN emoji kullanıldığında, THE OSB Destek Sistemi SHALL emoji anlamlarını açıklayan tooltip sunmak
62. **REQ-53.62** WHEN duygusal ifade gerektiğinde, THE OSB Destek Sistemi SHALL görsel duygu kartları sunmak
63. **REQ-53.63** WHEN chat başlatıldığında, THE OSB Destek Sistemi SHALL örnek mesaj şablonları sunmak
64. **REQ-53.64** WHEN soru sormak istendiğinde, THE OSB Destek Sistemi SHALL hazır soru formatları sunmak
65. **REQ-53.65** WHEN yardım istendiğinde, THE OSB Destek Sistemi SHALL adım adım yardım isteme rehberi sunmak
66. **REQ-53.66** WHEN geri bildirim verildiğinde, THE OSB Destek Sistemi SHALL görsel geri bildirim seçenekleri sunmak
67. **REQ-53.67** WHEN grup çalışması yapıldığında, THE OSB Destek Sistemi SHALL rol kartları ve görev dağılımı göstermek
68. **REQ-53.68** WHEN sohbet kuralları açıklandığında, THE OSB Destek Sistemi SHALL görsel sohbet kuralları kartı sunmak
69. **REQ-53.69** WHEN bekleme süresi varsa, THE OSB Destek Sistemi SHALL görsel bekleme sayacı göstermek
70. **REQ-53.70** WHEN sosyal durum açıklandığında, THE OSB Destek Sistemi SHALL "ne zaman/ne yaparım" kartı sunmak

**Güvenli Alan ve Mola Yönetimi (REQ-53.71 - REQ-53.80)**

71. **REQ-53.71** WHEN stres tespit edildiğinde, THE OSB Destek Sistemi SHALL sakinleşme önerileri sunmak
72. **REQ-53.72** WHEN mola istendiğinde, THE OSB Destek Sistemi SHALL anında sessiz mola alanı sunmak
73. **REQ-53.73** WHEN sakinleşme stratejisi seçildiğinde, THE OSB Destek Sistemi SHALL rehberli nefes egzersizi sunmak
74. **REQ-53.74** WHEN sensory break istendiğinde, THE OSB Destek Sistemi SHALL duyusal mola aktiviteleri sunmak
75. **REQ-53.75** WHEN güvenli alan açıldığında, THE OSB Destek Sistemi SHALL minimal stimuli ortamı sunmak
76. **REQ-53.76** WHEN çıkış stratejisi belirlendiğinde, THE OSB Destek Sistemi SHALL "dur" veya "mola" butonu sunmak
77. **REQ-53.77** WHEN bunaltı hissedildiğinde, THE OSB Destek Sistemi SHALL hızlı çıkış seçeneği sunmak
78. **REQ-53.78** WHEN tekrar hazır olunduğunda, THE OSB Destek Sistemi SHALL kaldığı yerden devam seçeneği sunmak
79. **REQ-53.79** WHEN mola süresi ayarlandığında, THE OSB Destek Sistemi SHALL kişiselleştirilmiş mola süreleri sunmak
80. **REQ-53.80** WHEN destek gerektiğinde, THE OSB Destek Sistemi SHALL kolay erişilebilir yardım butonu sunmak

---

**REQ-53 Özet:**
- ✅ REQ-53.1 - REQ-53.15: Tutarlı ve Öngörülebilir Arayüz
- ✅ REQ-53.16 - REQ-53.30: Görsel Programlar ve Rutinler
- ✅ REQ-53.31 - REQ-53.45: Net ve Açık Talimatlar
- ✅ REQ-53.46 - REQ-53.60: Duyusal Yük Azaltma
- ✅ REQ-53.61 - REQ-53.70: Sosyal İletişim Desteği
- ✅ REQ-53.71 - REQ-53.80: Güvenli Alan ve Mola Yönetimi

**Toplam Kriter Sayısı:** 80 kriter

---

### REQ-54: (Rezerve - Gelecek Kullanım İçin)

**Durum:** Bu REQ numarası gelecekteki özellikler için rezerve edilmiştir.

**Not:** REQ-54 şu anda atanmamıştır. Gelecekte eklenecek erişilebilirlik veya özel gereksinim özellikleri için ayrılmıştır.

---

### REQ-55: (Rezerve - Gelecek Kullanım İçin)

**Durum:** Bu REQ numarası gelecekteki özellikler için rezerve edilmiştir.

**Not:** REQ-55 şu anda atanmamıştır. Gelecekte eklenecek erişilebilirlik veya özel gereksinim özellikleri için ayrılmıştır.

---

## BÖLÜM 7: GAMİFİKASYON SİSTEMİ

### REQ-56: Oyunlaştırma ve Motivasyon Sistemi

**Kullanıcı Hikayesi:** Bir öğrenci olarak, çalışmalarım karşılığında puan kazanmak, seviye atlamak ve rozetler toplamak istiyorum, böylece öğrenme sürecim daha eğlenceli ve motive edici olur.

#### Puan Sistemi (REQ-56.1 - REQ-56.5)

1. **REQ-56.1** WHEN öğrenci bir soruyu doğru cevapladığında, THE Gamification Sistemi SHALL soru zorluğuna göre 10-50 puan arasında puan verir
2. **REQ-56.2** WHEN öğrenci günlük çalışma hedefini tamamladığında, THE Gamification Sistemi SHALL 100 bonus puan verir
3. **REQ-56.3** WHEN öğrenci sınavı tamamladığında, THE Gamification Sistemi SHALL performansa göre 50-500 puan arasında puan verir
4. **REQ-56.4** WHEN öğrenci puan geçmişini görüntülediğinde, THE Gamification Sistemi SHALL son 30 günlük puan kazanımlarını grafik ve liste formatında gösterir
5. **REQ-56.5** WHEN öğrenci dashboard'unu açtığında, THE Gamification Sistemi SHALL toplam puan, günlük kazanılan puan ve haftalık kazanılan puanı gösterir

#### Seviye Sistemi (REQ-56.6 - REQ-56.10)

6. **REQ-56.6** WHEN öğrenci yeterli deneyim puanı topladığında, THE Seviye Sistemi SHALL otomatik olarak bir üst seviyeye yükseltir
7. **REQ-56.7** WHEN öğrenci seviye atladığında, THE Seviye Sistemi SHALL kutlama animasyonu gösterir ve bildirim gönderir
8. **REQ-56.8** WHEN Seviye Sistemi deneyim puanı hesapladığında, THE Seviye Sistemi SHALL her seviye için gereken XP'yi üstel formül ile hesaplar (Level * 100 * 1.5^Level)
9. **REQ-56.9** WHEN öğrenci profil sayfasını görüntülediğinde, THE Seviye Sistemi SHALL mevcut seviye, toplam XP, bir sonraki seviyeye kalan XP ve ilerleme çubuğunu gösterir
10. **REQ-56.10** WHEN öğrenci seviye 10, 25, 50, 75, 100'e ulaştığında, THE Seviye Sistemi SHALL özel milestone rozeti verir

#### Rozet Koleksiyonu (REQ-56.11 - REQ-56.15)

11. **REQ-56.11** WHEN öğrenci belirli bir başarıyı tamamladığında, THE Rozet Sistemi SHALL ilgili rozeti otomatik olarak verir ve bildirim gösterir
12. **REQ-56.12** WHEN öğrenci rozet koleksiyonunu görüntülediğinde, THE Rozet Sistemi SHALL kazanılan rozetleri renkli, kazanılmayanları gri olarak gösterir
13. **REQ-56.13** WHEN Rozet Sistemi nadir rozet verdiğinde, THE Rozet Sistemi SHALL özel animasyon ve ses efekti ile kutlama yapar
14. **REQ-56.14** WHEN öğrenci rozet detayını görüntülediğinde, THE Rozet Sistemi SHALL rozet adı, açıklama, kazanma tarihi ve nadir seviyesini (yaygın/nadir/efsanevi) gösterir
15. **REQ-56.15** WHEN öğrenci 7 gün üst üste çalıştığında, THE Rozet Sistemi SHALL "Kararlı Öğrenci" rozetini verir

#### Liderlik Tablosu (REQ-56.16 - REQ-56.20)

16. **REQ-56.16** WHEN öğrenci liderlik tablosunu görüntülediğinde, THE Liderlik Sistemi SHALL haftalık, aylık ve tüm zamanlar olmak üzere 3 farklı zaman dilimi sunar
17. **REQ-56.17** WHEN Liderlik Sistemi sıralama yaptığında, THE Liderlik Sistemi SHALL toplam puana göre ilk 100 öğrenciyi listeler
18. **REQ-56.18** WHEN öğrenci arkadaş karşılaştırması yaptığında, THE Liderlik Sistemi SHALL sadece arkadaş listesindeki öğrencileri gösterir
19. **REQ-56.19** WHEN öğrenci sınıf sıralamasını görüntülediğinde, THE Liderlik Sistemi SHALL aynı sınıftaki tüm öğrencileri puana göre sıralar
20. **REQ-56.20** WHEN öğrenci liderlik tablosunda ilk 3'e girdiğinde, THE Liderlik Sistemi SHALL profil sayfasında özel altın/gümüş/bronz rozet gösterir

---

### REQ-57: Rozet Kategorileri ve Başarı Kriterleri

**Kullanıcı Hikayesi:** Bir öğrenci olarak, farklı kategorilerde rozetler kazanmak istiyorum, böylece çeşitli alanlarda gelişimimi görebilirim.

#### Kabul Kriterleri

**Çalışma Rozetleri (REQ-57.1 - REQ-57.5)**

1. **REQ-57.1** WHEN öğrenci 7 gün üst üste çalıştığında, THE Rozet Sistemi SHALL "Kararlı Öğrenci" (yaygın) rozetini verir
2. **REQ-57.2** WHEN öğrenci 30 gün üst üste çalıştığında, THE Rozet Sistemi SHALL "Azimli Öğrenci" (nadir) rozetini verir
3. **REQ-57.3** WHEN öğrenci 100 gün üst üste çalıştığında, THE Rozet Sistemi SHALL "Efsane Öğrenci" (efsanevi) rozetini verir
4. **REQ-57.4** WHEN öğrenci toplam 1000 soru çözdüğünde, THE Rozet Sistemi SHALL "Soru Avcısı" rozetini verir
5. **REQ-57.5** WHEN öğrenci toplam 100 saat çalıştığında, THE Rozet Sistemi SHALL "Zaman Yöneticisi" rozetini verir

**Sınav Rozetleri (REQ-57.6 - REQ-57.10)**

6. **REQ-57.6** WHEN öğrenci ilk denemesinde %80 üzeri aldığında, THE Rozet Sistemi SHALL "Parlak Başlangıç" rozetini verir
7. **REQ-57.7** WHEN öğrenci 10 deneme sınavı tamamladığında, THE Rozet Sistemi SHALL "Sınav Ustası" rozetini verir
8. **REQ-57.8** WHEN öğrenci bir konuda 3 sınavda üst üste %90 üzeri aldığında, THE Rozet Sistemi SHALL "Konu Uzmanı" rozetini verir
9. **REQ-57.9** WHEN öğrenci tam puan aldığında, THE Rozet Sistemi SHALL "Mükemmeliyetçi" (nadir) rozetini verir
10. **REQ-57.10** WHEN öğrenci TYT, AYT ve YDT'nin hepsini tamamladığında, THE Rozet Sistemi SHALL "Tam Hazır" rozetini verir

**Sosyal Rozetler (REQ-57.11 - REQ-57.15)**

11. **REQ-57.11** WHEN öğrenci 10 arkadaşını platforma davet ettiğinde, THE Rozet Sistemi SHALL "Topluluk Lideri" rozetini verir
12. **REQ-57.12** WHEN öğrenci liderlik tablosunda ilk 10'a girdiğinde, THE Rozet Sistemi SHALL "Yıldız Öğrenci" rozetini verir
13. **REQ-57.13** WHEN öğrenci 100 soru paylaştığında, THE Rozet Sistemi SHALL "Bilgi Paylaşımcısı" rozetini verir
14. **REQ-57.14** WHEN öğrenci 50 yorum yaptığında, THE Rozet Sistemi SHALL "Aktif Katılımcı" rozetini verir
15. **REQ-57.15** WHEN öğrenci bir arkadaşına 10 kez yardım ettiğinde, THE Rozet Sistemi SHALL "Yardımsever" rozetini verir

**Özel Rozetler (REQ-57.16 - REQ-57.20)**

16. **REQ-57.16** WHEN öğrenci gece 00:00-06:00 arası çalıştığında, THE Rozet Sistemi SHALL "Gece Kuşu" rozetini verir
17. **REQ-57.17** WHEN öğrenci sabah 05:00-07:00 arası çalıştığında, THE Rozet Sistemi SHALL "Erken Kuş" rozetini verir
18. **REQ-57.18** WHEN öğrenci bir günde 5 saat çalıştığında, THE Rozet Sistemi SHALL "Maraton Koşucusu" rozetini verir
19. **REQ-57.19** WHEN öğrenci tüm konuları tamamladığında, THE Rozet Sistemi SHALL "Konu Tamamlayıcı" (efsanevi) rozetini verir
20. **REQ-57.20** WHEN öğrenci platformda 1 yıl aktif olduğunda, THE Rozet Sistemi SHALL "Sadık Öğrenci" (efsanevi) rozetini verir

---

### REQ-58: Motivasyon ve Bildirimler

**Kullanıcı Hikayesi:** Bir öğrenci olarak, başarılarım için anında geri bildirim ve kutlama almak istiyorum, böylece motive olur ve çalışmaya devam ederim.

#### Kabul Kriterleri

1. **REQ-58.1** WHEN öğrenci rozet kazandığında, THE Bildirim Sistemi SHALL modal popup ile kutlama gösterir
2. **REQ-58.2** WHEN öğrenci seviye atladığında, THE Bildirim Sistemi SHALL tam ekran animasyon ve ses efekti ile kutlar
3. **REQ-58.3** WHEN öğrenci günlük hedefini tamamladığında, THE Bildirim Sistemi SHALL başarı bildirimi ve konfeti animasyonu gösterir
4. **REQ-58.4** WHEN öğrenci liderlik tablosunda yükseldiğinde, THE Bildirim Sistemi SHALL sıralama değişikliğini bildirir
5. **REQ-58.5** WHEN öğrenci 3 gün çalışmadığında, THE Bildirim Sistemi SHALL nazik hatırlatma bildirimi gönderir

---

### REQ-59: Gamification Analytics ve Raporlama

**Kullanıcı Hikayesi:** Bir öğrenci olarak, gamification istatistiklerimi görmek istiyorum, böylece ilerlememı takip edebilirim.

#### Kabul Kriterleri

1. **REQ-59.1** WHEN öğrenci istatistikler sayfasını açtığında, THE Analytics Sistemi SHALL toplam puan, seviye, rozet sayısı ve sıralama bilgilerini gösterir
2. **REQ-59.2** WHEN Analytics Sistemi puan grafiği çizdiğinde, THE Analytics Sistemi SHALL son 30 günlük puan kazanımlarını çizgi grafik ile gösterir
3. **REQ-59.3** WHEN öğrenci rozet ilerlemesini görüntülediğinde, THE Analytics Sistemi SHALL kategori bazlı rozet tamamlanma yüzdesini gösterir
4. **REQ-59.4** WHEN öğrenci seviye geçmişini görüntülediğinde, THE Analytics Sistemi SHALL her seviyeye ulaşma tarihini ve süresini gösterir
5. **REQ-59.5** WHEN öğrenci karşılaştırma yaptığında, THE Analytics Sistemi SHALL kendi istatistiklerini sınıf ortalaması ile karşılaştırır

---

## BÖLÜM 8: OPSİYONEL SİSTEMLER

### REQ-60: Soru Bankası Yönetim Sistemi

**Kullanıcı Hikayesi:** Bir içerik yöneticisi olarak, soru bankasını verimli bir şekilde yönetmek istiyorum, böylece kaliteli ve güncel sorular ile öğrencilere hizmet verebilirim.

#### Kabul Kriterleri

**CRUD İşlemleri (REQ-60.1 - REQ-60.8)**

1. **REQ-60.1** WHEN içerik yöneticisi yeni soru eklemek istediğinde, THE Soru Bankası Sistemi SHALL soru oluşturma formu sunmak
2. **REQ-60.2** WHEN soru oluşturulduğunda, THE Soru Bankası Sistemi SHALL soru metni, seçenekler, doğru cevap ve çözüm alanlarını kaydetmek
3. **REQ-60.3** WHEN soru düzenlendiğinde, THE Soru Bankası Sistemi SHALL tüm alanları güncelleme imkanı vermek
4. **REQ-60.4** WHEN soru silindiğinde, THE Soru Bankası Sistemi SHALL soft delete ile arşivlemek
5. **REQ-60.5** WHEN soru listesi görüntülendiğinde, THE Soru Bankası Sistemi SHALL filtreleme ve sıralama seçenekleri sunmak
6. **REQ-60.6** WHEN toplu işlem yapıldığında, THE Soru Bankası Sistemi SHALL çoklu soru seçimi ve toplu işlem desteği vermek
7. **REQ-60.7** WHEN soru import edildiğinde, THE Soru Bankası Sistemi SHALL Excel/CSV dosyasından toplu import desteklemek
8. **REQ-60.8** WHEN soru export edildiğinde, THE Soru Bankası Sistemi SHALL farklı formatlarda export sunmak

**Etiketleme ve Kategorileme (REQ-60.9 - REQ-60.15)**

9. **REQ-60.9** WHEN soru etiketlendiğinde, THE Soru Bankası Sistemi SHALL ders, konu, alt konu etiketleri atamak
10. **REQ-60.10** WHEN zorluk atandığında, THE Soru Bankası Sistemi SHALL IRT tabanlı zorluk değeri atamak
11. **REQ-60.11** WHEN sınav tipi seçildiğinde, THE Soru Bankası Sistemi SHALL TYT/AYT/YDT kategorisini kaydetmek
12. **REQ-60.12** WHEN müfredat eşleştirildiğinde, THE Soru Bankası Sistemi SHALL MEB kazanımları ile eşleştirmek
13. **REQ-60.13** WHEN arama yapıldığında, THE Soru Bankası Sistemi SHALL tam metin arama desteği sunmak
14. **REQ-60.14** WHEN filtre uygulandığında, THE Soru Bankası Sistemi SHALL çoklu filtre kombinasyonunu desteklemek
15. **REQ-60.15** WHEN istatistik görüntülendiğinde, THE Soru Bankası Sistemi SHALL soru başarı oranı ve kullanım istatistiklerini göstermek

**Video Çözüm Entegrasyonu (REQ-60.16 - REQ-60.20)**

16. **REQ-60.16** WHEN video çözüm eklendiğinde, THE Soru Bankası Sistemi SHALL YouTube/Vimeo linkini kaydetmek
17. **REQ-60.17** WHEN video önizleme yapıldığında, THE Soru Bankası Sistemi SHALL embed player göstermek
18. **REQ-60.18** WHEN alternatif çözüm eklendiğinde, THE Soru Bankası Sistemi SHALL çoklu çözüm yolu desteği sunmak
19. **REQ-60.19** WHEN çözüm adımları tanımlandığında, THE Soru Bankası Sistemi SHALL adım adım metin çözümü kaydetmek
20. **REQ-60.20** WHEN çözüm kalitesi değerlendirildiğinde, THE Soru Bankası Sistemi SHALL kullanıcı puanlaması toplanmak

**Kalite Kontrol (REQ-60.21 - REQ-60.25)**

21. **REQ-60.21** WHEN soru oluşturulduğunda, THE Soru Bankası Sistemi SHALL otomatik yazım kontrolü yapmak
22. **REQ-60.22** WHEN formül girildiğinde, THE Soru Bankası Sistemi SHALL LaTeX syntax doğrulaması yapmak
23. **REQ-60.23** WHEN soru yayınlanmadan önce, THE Soru Bankası Sistemi SHALL review workflow uygulamak
24. **REQ-60.24** WHEN duplicate tespit edildiğinde, THE Soru Bankası Sistemi SHALL benzer soru uyarısı vermek
25. **REQ-60.25** WHEN soru rapor edildiğinde, THE Soru Bankası Sistemi SHALL hata bildirim sistemi sunmak

---

### REQ-61: Üniversite Tercih Danışmanlığı Sistemi

**Kullanıcı Hikayesi:** Bir YKS öğrencisi olarak, puanıma göre tercih yapabileceğim üniversite ve bölümleri görmek istiyorum, böylece bilinçli tercih yapabilirim.

#### Kabul Kriterleri

**Taban Puan Veritabanı (REQ-61.1 - REQ-61.8)**

1. **REQ-61.1** WHEN taban puanlar sorgulandığında, THE Tercih Danışmanlığı Sistemi SHALL son 5 yılın taban puanlarını göstermek
2. **REQ-61.2** WHEN üniversite arandığında, THE Tercih Danışmanlığı Sistemi SHALL 200+ üniversiteyi listelemek
3. **REQ-61.3** WHEN bölüm arandığında, THE Tercih Danışmanlığı Sistemi SHALL 10.000+ bölümü içeren veritabanı sunmak
4. **REQ-61.4** WHEN kontenjan bilgisi istendiğinde, THE Tercih Danışmanlığı Sistemi SHALL güncel kontenjan bilgisi göstermek
5. **REQ-61.5** WHEN şehir filtresi uygulandığında, THE Tercih Danışmanlığı Sistemi SHALL 81 il bazlı filtreleme sunmak
6. **REQ-61.6** WHEN üniversite türü seçildiğinde, THE Tercih Danışmanlığı Sistemi SHALL devlet/vakıf filtresi sunmak
7. **REQ-61.7** WHEN puan türü seçildiğinde, THE Tercih Danışmanlığı Sistemi SHALL SAY/EA/SÖZ/DİL filtrelemesi yapmak
8. **REQ-61.8** WHEN burs bilgisi istendiğinde, THE Tercih Danışmanlığı Sistemi SHALL burs oranlarını göstermek

**Tercih Simülasyonu (REQ-61.9 - REQ-61.16)**

9. **REQ-61.9** WHEN öğrenci puan girdiğinde, THE Tercih Danışmanlığı Sistemi SHALL tahmini sıralama hesaplamak
10. **REQ-61.10** WHEN simülasyon yapıldığında, THE Tercih Danışmanlığı Sistemi SHALL olası tercih listesi oluşturmak
11. **REQ-61.11** WHEN risk analizi yapıldığında, THE Tercih Danışmanlığı Sistemi SHALL her tercih için yerleşme olasılığı göstermek
12. **REQ-61.12** WHEN alternatif tercihler istendiğinde, THE Tercih Danışmanlığı Sistemi SHALL benzer bölüm önerileri sunmak
13. **REQ-61.13** WHEN tercih listesi oluşturulduğunda, THE Tercih Danışmanlığı Sistemi SHALL 24 tercihlik liste desteği vermek
14. **REQ-61.14** WHEN tercih sıralaması yapıldığında, THE Tercih Danışmanlığı Sistemi SHALL drag-and-drop sıralama sunmak
15. **REQ-61.15** WHEN tercih kaydedildiğinde, THE Tercih Danışmanlığı Sistemi SHALL tercih listesini kaydetmek
16. **REQ-61.16** WHEN tercih paylaşıldığında, THE Tercih Danışmanlığı Sistemi SHALL PDF export sunmak

**İstatistik ve Analiz (REQ-61.17 - REQ-61.25)**

17. **REQ-61.17** WHEN trend analizi yapıldığında, THE Tercih Danışmanlığı Sistemi SHALL 5 yıllık taban puan trendini göstermek
18. **REQ-61.18** WHEN doluluk oranı sorgulandığında, THE Tercih Danışmanlığı Sistemi SHALL son yıl doluluk oranlarını göstermek
19. **REQ-61.19** WHEN mezun istatistikleri istendiğinde, THE Tercih Danışmanlığı Sistemi SHALL istihdam oranlarını göstermek
20. **REQ-61.20** WHEN maaş bilgisi sorgulandığında, THE Tercih Danışmanlığı Sistemi SHALL ortalama başlangıç maaşlarını göstermek
21. **REQ-61.21** WHEN üniversite karşılaştırması yapıldığında, THE Tercih Danışmanlığı Sistemi SHALL yan yana karşılaştırma sunmak
22. **REQ-61.22** WHEN kampüs bilgisi istendiğinde, THE Tercih Danışmanlığı Sistemi SHALL tesis ve olanak bilgisi göstermek
23. **REQ-61.23** WHEN öğrenci yorumları istendiğinde, THE Tercih Danışmanlığı Sistemi SHALL öğrenci değerlendirmelerini göstermek
24. **REQ-61.24** WHEN akademik kadro sorgulandığında, THE Tercih Danışmanlığı Sistemi SHALL öğretim üyesi sayılarını göstermek
25. **REQ-61.25** WHEN uluslararası sıralama istendiğinde, THE Tercih Danışmanlığı Sistemi SHALL dünya sıralama bilgilerini göstermek

---

### REQ-62: Canlı Ders ve Öğretmen Desteği Sistemi

**Kullanıcı Hikayesi:** Bir öğrenci olarak, canlı dersler aracılığıyla öğretmenlerden yardım almak istiyorum, böylece anlamadığım konuları sorabilir ve açıklama alabilirim.

#### Kabul Kriterleri

**Video Konferans (REQ-62.1 - REQ-62.8)**

1. **REQ-62.1** WHEN canlı ders başlatıldığında, THE Canlı Ders Sistemi SHALL HD video konferans desteği sunmak
2. **REQ-62.2** WHEN ekran paylaşımı yapıldığında, THE Canlı Ders Sistemi SHALL ekran paylaşım özelliği sunmak
3. **REQ-62.3** WHEN beyaz tahta kullanıldığında, THE Canlı Ders Sistemi SHALL interaktif dijital tahta sunmak
4. **REQ-62.4** WHEN ders kaydedildiğinde, THE Canlı Ders Sistemi SHALL otomatik kayıt özelliği sunmak
5. **REQ-62.5** WHEN katılımcı listesi görüntülendiğinde, THE Canlı Ders Sistemi SHALL anlık katılımcı sayısını göstermek
6. **REQ-62.6** WHEN el kaldırma yapıldığında, THE Canlı Ders Sistemi SHALL el kaldırma ve soru sorma butonu sunmak
7. **REQ-62.7** WHEN anket yapıldığında, THE Canlı Ders Sistemi SHALL anlık anket ve quiz özelliği sunmak
8. **REQ-62.8** WHEN ders planlandığında, THE Canlı Ders Sistemi SHALL ders takvimi ve hatırlatıcı sunmak

**Öğretmen Havuzu (REQ-62.9 - REQ-62.15)**

9. **REQ-62.9** WHEN öğretmen arandığında, THE Canlı Ders Sistemi SHALL konu bazlı öğretmen listesi sunmak
10. **REQ-62.10** WHEN öğretmen profili görüntülendiğinde, THE Canlı Ders Sistemi SHALL öğretmen değerlendirme puanı göstermek
11. **REQ-62.11** WHEN öğretmen seçildiğinde, THE Canlı Ders Sistemi SHALL müsaitlik takvimi göstermek
12. **REQ-62.12** WHEN randevu alındığında, THE Canlı Ders Sistemi SHALL birebir ders rezervasyonu sağlamak
13. **REQ-62.13** WHEN ücret hesaplandığında, THE Canlı Ders Sistemi SHALL şeffaf fiyatlandırma göstermek
14. **REQ-62.14** WHEN ödeme yapıldığında, THE Canlı Ders Sistemi SHALL güvenli ödeme entegrasyonu sunmak
15. **REQ-62.15** WHEN ders tamamlandığında, THE Canlı Ders Sistemi SHALL öğretmen değerlendirme formu sunmak

**Soru-Cevap Sistemi (REQ-62.16 - REQ-62.20)**

16. **REQ-62.16** WHEN soru sorulduğunda, THE Canlı Ders Sistemi SHALL asenkron soru-cevap platformu sunmak
17. **REQ-62.17** WHEN fotoğraf yüklendiğinde, THE Canlı Ders Sistemi SHALL soru fotoğrafı yükleme desteği vermek
18. **REQ-62.18** WHEN cevap verildiğinde, THE Canlı Ders Sistemi SHALL cevap bildirimi göndermek
19. **REQ-62.19** WHEN soru arşivi arandığında, THE Canlı Ders Sistemi SHALL benzer sorular ve cevaplar göstermek
20. **REQ-62.20** WHEN cevap puanlandığında, THE Canlı Ders Sistemi SHALL yararlı cevap puanlama sistemi sunmak

---

### REQ-63: Mobil Uygulama Sistemi

**Kullanıcı Hikayesi:** Bir öğrenci olarak, mobil cihazımdan çalışabilmek istiyorum, böylece her yerde ve her zaman öğrenmeye devam edebilirim.

#### Kabul Kriterleri

**Cross-Platform Destek (REQ-63.1 - REQ-63.8)**

1. **REQ-63.1** WHEN iOS cihazda açıldığında, THE Mobil Uygulama SHALL iOS 14+ desteği sunmak
2. **REQ-63.2** WHEN Android cihazda açıldığında, THE Mobil Uygulama SHALL Android 8+ desteği sunmak
3. **REQ-63.3** WHEN tablet kullanıldığında, THE Mobil Uygulama SHALL tablet optimize edilmiş arayüz sunmak
4. **REQ-63.4** WHEN orientasyon değiştiğinde, THE Mobil Uygulama SHALL landscape/portrait desteği sunmak
5. **REQ-63.5** WHEN güncelleme geldiğinde, THE Mobil Uygulama SHALL otomatik güncelleme desteği sunmak
6. **REQ-63.6** WHEN performans ölçüldüğünde, THE Mobil Uygulama SHALL 60 FPS akıcı deneyim sunmak
7. **REQ-63.7** WHEN bellek kullanımı kontrol edildiğinde, THE Mobil Uygulama SHALL optimize edilmiş bellek kullanımı sağlamak
8. **REQ-63.8** WHEN batarya kullanımı ölçüldüğünde, THE Mobil Uygulama SHALL düşük batarya tüketimi sağlamak

**Offline Çalışma (REQ-63.9 - REQ-63.15)**

9. **REQ-63.9** WHEN içerik indirildiğinde, THE Mobil Uygulama SHALL offline içerik paketi indirme sunmak
10. **REQ-63.10** WHEN internet yokken, THE Mobil Uygulama SHALL offline mod ile çalışmak
11. **REQ-63.11** WHEN internet geldiğinde, THE Mobil Uygulama SHALL otomatik senkronizasyon yapmak
12. **REQ-63.12** WHEN ilerleme kaydedildiğinde, THE Mobil Uygulama SHALL local storage ile ilerleme kaydetmek
13. **REQ-63.13** WHEN çakışma olduğunda, THE Mobil Uygulama SHALL conflict resolution mekanizması sunmak
14. **REQ-63.14** WHEN depolama yönetildiğinde, THE Mobil Uygulama SHALL indirilen içerik yönetimi sunmak
15. **REQ-63.15** WHEN disk alanı dolduğunda, THE Mobil Uygulama SHALL otomatik temizleme önerisi sunmak

**Push Bildirimler (REQ-63.16 - REQ-63.20)**

16. **REQ-63.16** WHEN sınav hatırlatması gerektiğinde, THE Mobil Uygulama SHALL push bildirim göndermek
17. **REQ-63.17** WHEN günlük çalışma vakti geldiğinde, THE Mobil Uygulama SHALL çalışma hatırlatıcısı göndermek
18. **REQ-63.18** WHEN başarı elde edildiğinde, THE Mobil Uygulama SHALL kutlama bildirimi göndermek
19. **REQ-63.19** WHEN yeni içerik eklendiğinde, THE Mobil Uygulama SHALL içerik bildirimi göndermek
20. **REQ-63.20** WHEN bildirim ayarları yapıldığında, THE Mobil Uygulama SHALL bildirim özelleştirme sunmak

---

### REQ-64: Sosyal Öğrenme ve Topluluk Sistemi

**Kullanıcı Hikayesi:** Bir öğrenci olarak, diğer öğrencilerle birlikte çalışmak ve deneyimlerini paylaşmak istiyorum, böylece motivasyonumu artırabilir ve birlikte öğrenebilirim.

#### Kabul Kriterleri

**Çalışma Grupları (REQ-64.1 - REQ-64.8)**

1. **REQ-64.1** WHEN grup oluşturulduğunda, THE Sosyal Öğrenme Sistemi SHALL özel çalışma grubu oluşturma sunmak
2. **REQ-64.2** WHEN üye eklendiğinde, THE Sosyal Öğrenme Sistemi SHALL grup üyelik yönetimi sunmak
3. **REQ-64.3** WHEN grup içi chat yapıldığında, THE Sosyal Öğrenme Sistemi SHALL grup mesajlaşma sunmak
4. **REQ-64.4** WHEN dosya paylaşıldığında, THE Sosyal Öğrenme Sistemi SHALL dosya paylaşım desteği sunmak
5. **REQ-64.5** WHEN ortak hedef belirlediğinde, THE Sosyal Öğrenme Sistemi SHALL grup hedefleri sunmak
6. **REQ-64.6** WHEN ilerleme karşılaştırıldığında, THE Sosyal Öğrenme Sistemi SHALL grup içi ilerleme tablosu sunmak
7. **REQ-64.7** WHEN çalışma oturumu planlandığında, THE Sosyal Öğrenme Sistemi SHALL grup çalışma seansları sunmak
8. **REQ-64.8** WHEN grup istatistikleri görüntülendiğinde, THE Sosyal Öğrenme Sistemi SHALL toplam grup aktivitesi göstermek

**Forum ve Tartışma (REQ-64.9 - REQ-64.15)**

9. **REQ-64.9** WHEN konu açıldığında, THE Sosyal Öğrenme Sistemi SHALL konu bazlı forum sunmak
10. **REQ-64.10** WHEN cevap verildiğinde, THE Sosyal Öğrenme Sistemi SHALL iç içe yanıt desteği sunmak
11. **REQ-64.11** WHEN yararlı içerik oylandığında, THE Sosyal Öğrenme Sistemi SHALL upvote/downvote sistemi sunmak
12. **REQ-64.12** WHEN moderasyon yapıldığında, THE Sosyal Öğrenme Sistemi SHALL içerik moderasyonu sunmak
13. **REQ-64.13** WHEN etiketleme yapıldığında, THE Sosyal Öğrenme Sistemi SHALL konu etiketleme sunmak
14. **REQ-64.14** WHEN arama yapıldığında, THE Sosyal Öğrenme Sistemi SHALL forum arama sunmak
15. **REQ-64.15** WHEN bildirim alındığında, THE Sosyal Öğrenme Sistemi SHALL takip edilen konu bildirimleri sunmak

**Başarı Paylaşımı (REQ-64.16 - REQ-64.20)**

16. **REQ-64.16** WHEN başarı elde edildiğinde, THE Sosyal Öğrenme Sistemi SHALL başarı paylaşım özelliği sunmak
17. **REQ-64.17** WHEN hikaye paylaşıldığında, THE Sosyal Öğrenme Sistemi SHALL motivasyon hikayeleri platformu sunmak
18. **REQ-64.18** WHEN rozet gösterildiğinde, THE Sosyal Öğrenme Sistemi SHALL rozet vitrin özelliği sunmak
19. **REQ-64.19** WHEN takip yapıldığında, THE Sosyal Öğrenme Sistemi SHALL öğrenci takip sistemi sunmak
20. **REQ-64.20** WHEN tebrik gönderildiğinde, THE Sosyal Öğrenme Sistemi SHALL kutlama mesajları sunmak

---

### REQ-65: Psikolojik Destek ve Motivasyon Sistemi

**Kullanıcı Hikayesi:** Bir YKS öğrencisi olarak, sınav stresi ile başa çıkmak için psikolojik destek almak istiyorum, böylece mental sağlığımı koruyarak verimli çalışabilirim.

#### Kabul Kriterleri

**Stres Yönetimi (REQ-65.1 - REQ-65.8)**

1. **REQ-65.1** WHEN stres seviyesi ölçüldüğünde, THE Psikolojik Destek Sistemi SHALL stres değerlendirme anketi sunmak
2. **REQ-65.2** WHEN yüksek stres tespit edildiğinde, THE Psikolojik Destek Sistemi SHALL sakinleştirici içerik önermek
3. **REQ-65.3** WHEN nefes egzersizi başlatıldığında, THE Psikolojik Destek Sistemi SHALL rehberli nefes egzersizleri sunmak
4. **REQ-65.4** WHEN meditasyon seçildiğinde, THE Psikolojik Destek Sistemi SHALL meditasyon seansları sunmak
5. **REQ-65.5** WHEN progresif gevşeme istendiğinde, THE Psikolojik Destek Sistemi SHALL kas gevşetme egzersizleri sunmak
6. **REQ-65.6** WHEN günlük tutulduğunda, THE Psikolojik Destek Sistemi SHALL duygu günlüğü özelliği sunmak
7. **REQ-65.7** WHEN mood takibi yapıldığında, THE Psikolojik Destek Sistemi SHALL duygu durum grafikleri göstermek
8. **REQ-65.8** WHEN kriz anı tespit edildiğinde, THE Psikolojik Destek Sistemi SHALL profesyonel yardım yönlendirmesi yapmak

**Motivasyon Araçları (REQ-65.9 - REQ-65.15)**

9. **REQ-65.9** WHEN motivasyon düştüğünde, THE Psikolojik Destek Sistemi SHALL motivasyonel alıntılar göstermek
10. **REQ-65.10** WHEN başarı hikayesi istendiğinde, THE Psikolojik Destek Sistemi SHALL YKS başarı hikayeleri sunmak
11. **REQ-65.11** WHEN hedef görselleştirildiğinde, THE Psikolojik Destek Sistemi SHALL hedef panosu oluşturma sunmak
12. **REQ-65.12** WHEN ilerleme kutlandığında, THE Psikolojik Destek Sistemi SHALL milestone kutlamaları yapmak
13. **REQ-65.13** WHEN olumlu düşünce çalışıldığında, THE Psikolojik Destek Sistemi SHALL pozitif düşünce egzersizleri sunmak
14. **REQ-65.14** WHEN öz-şefkat pratik yapıldığında, THE Psikolojik Destek Sistemi SHALL self-compassion içerikleri sunmak
15. **REQ-65.15** WHEN büyüme zihniyeti geliştirildiğinde, THE Psikolojik Destek Sistemi SHALL growth mindset materyalleri sunmak

**Profesyonel Destek (REQ-65.16 - REQ-65.20)**

16. **REQ-65.16** WHEN uzman desteği istendiğinde, THE Psikolojik Destek Sistemi SHALL psikolog iletişim bilgileri sunmak
17. **REQ-65.17** WHEN acil yardım gerektiğinde, THE Psikolojik Destek Sistemi SHALL acil destek hattı numaraları göstermek
18. **REQ-65.18** WHEN danışmanlık randevusu istendiğinde, THE Psikolojik Destek Sistemi SHALL online danışmanlık entegrasyonu sunmak
19. **REQ-65.19** WHEN kaynak materyal istendiğinde, THE Psikolojik Destek Sistemi SHALL sınav stresi hakkında eğitici içerikler sunmak
20. **REQ-65.20** WHEN ebeveyn bilgilendirmesi gerektiğinde, THE Psikolojik Destek Sistemi SHALL veli bilgilendirme kaynakları sunmak

---

## BÖLÜM 9: GENEL ÖZET VE İSTATİSTİKLER

### Toplam Requirement Dağılımı

| Kategori | REQ Numaraları | Kriter Sayısı |
|----------|----------------|---------------|
| Core Platform | REQ-1 to REQ-47 | ~200 |
| LLM Soru Üretim | REQ-48 | 96 |
| CAT Adaptif Test | REQ-49 | 100 |
| Disleksi Desteği | REQ-50 | 104 |
| Diskalkuli Desteği | REQ-51 | 100 |
| DEHB Desteği | REQ-52 | 100 |
| OSB Desteği | REQ-53 | 80 |
| Gamification | REQ-56-59 | 50 |
| Opsiyonel Sistemler | REQ-60-65 | 150 |
| **TOPLAM** | **65 REQ** | **~980 Kriter** |

### EARS/INCOSE Uyumu
- ✅ Tüm kriterler EARS formatında (WHEN/THEN/SHALL)
- ✅ Ölçülebilir kabul kriterleri
- ✅ Çözüm-bağımsız gereksinimler
- ✅ Aktif ses kullanımı
- ✅ Tek düşünce per requirement

---

*Son Güncelleme: Ocak 2026*
*Versiyon: 2.0*
*Durum: Tamamlanmış*

