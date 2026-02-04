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

---

## BÖLÜM 6: ERİŞİLEBİLİRLİK SİSTEMLERİ

### REQ-50: Disleksi Desteği Sistemi

**Kullanıcı Hikayesi:** Disleksili bir öğrenci olarak, okuma zorluklarımı azaltacak özel tipografi, renk ayarları ve okuma yardımcıları kullanmak istiyorum, böylece içerikleri daha rahat okuyabilir ve öğrenme sürecime eşit şekilde katılabilirim.

#### Kabul Kriterleri (104 Kriter - Özet)

**Tipografi ve Görsel Düzenlemeler (REQ-50.1 - REQ-50.13)**
1. **REQ-50.1** WHEN OpenDyslexic font seçildiğinde, THE Platform SHALL tüm metinlerde bu fontu uygulamak
2. **REQ-50.2** WHEN Dyslexie font seçildiğinde, THE Platform SHALL lisanslı Dyslexie fontunu kullanmak
3. **REQ-50.3** WHEN Font seçici gösterildiğinde, THE Platform SHALL en az 3 disleksi dostu font sunmak
4. **REQ-50.4** WHEN Font tercihi kaydedildiğinde, THE Platform SHALL kullanıcı profilinde saklamak
5. **REQ-50.5** WHEN Font boyutu ayarlandığında, THE Platform SHALL 12-24pt arası değerleri desteklemek
6. **REQ-50.6** WHEN Real-time preview gösterildiğinde, THE Platform SHALL değişiklikleri anında yansıtmak
7. **REQ-50.7** WHEN Responsive scaling uygulandığında, THE Platform SHALL tüm ekran boyutlarında çalışmak
8. **REQ-50.8** WHEN Satır aralığı ayarlandığında, THE Platform SHALL 1.0x-3.0x arası değerleri desteklemek
9. **REQ-50.9** WHEN Paragraph spacing ayarlandığında, THE Platform SHALL paragraflar arası boşluğu artırmak
10. **REQ-50.10** WHEN Reading comfort optimize edildiğinde, THE Platform SHALL optimal satır uzunluğu (50-75 karakter) sağlamak
11. **REQ-50.11** WHEN Letter spacing ayarlandığında, THE Platform SHALL harf arası boşluğu artırmak
12. **REQ-50.12** WHEN Word spacing ayarlandığında, THE Platform SHALL kelime arası boşluğu artırmak
13. **REQ-50.13** WHEN Kerning adjustment yapıldığında, THE Platform SHALL harf çiftleri arası boşluğu optimize etmek

**Renk ve Kontrast (REQ-50.14 - REQ-50.27)**
14-27. **REQ-50.14-27** SHALL renkli overlay (6 renk), opacity ayarlama, yüksek kontrast modları ve WCAG AAA uyumu sağlamak

**Okuma Yardımcıları (REQ-50.28 - REQ-50.42)**
28-42. **REQ-50.28-42** SHALL okuma cetveli, odak modu, kelime vurgulama ve hece ayırma özellikleri sunmak

**Text-to-Speech (REQ-50.43 - REQ-50.56)**
43-56. **REQ-50.43-56** SHALL Türkçe TTS, ses hızı/tonu ayarlama ve karaoke mode sağlamak

**Metin Basitleştirme (REQ-50.57 - REQ-50.72)**
57-72. **REQ-50.57-72** SHALL karmaşık kelime tespiti, basit eşanlamlı değiştirme, uzun cümle bölme ve Flesch-Kincaid skoru hesaplama sunmak

**Görsel Destekler (REQ-50.73 - REQ-50.88)**
73-88. **REQ-50.73-88** SHALL kavram haritaları, infografikler, resimli sözlük ve renk kodlama sağlamak

**Çoklu Duyusal Öğrenme (REQ-50.89 - REQ-50.104)**
89-104. **REQ-50.89-104** SHALL görsel+işitsel+kinestetik içerik, interaktif animasyonlar, video içerikler ve VR/AR desteği sunmak

---

### REQ-51: Diskalkuli Desteği Sistemi

**Kullanıcı Hikayesi:** Diskalkuli (matematik öğrenme güçlüğü) yaşayan bir öğrenci olarak, görsel matematik temsilleri, adım adım çözümler ve interaktif araçlar kullanmak istiyorum, böylece matematiksel kavramları daha iyi anlayabilir ve matematik kaygımı azaltabilirim.

#### Kabul Kriterleri (100 Kriter - Özet)

**Görsel Matematik Temsilleri (REQ-51.1 - REQ-51.20)**
1-20. **REQ-51.1-20** SHALL sayı blokları, kesir çubukları, 3D geometrik şekiller ve grafik çizim araçları sağlamak

**Adım Adım Çözüm (REQ-51.21 - REQ-51.40)**

**Her Adımı Ayrı Gösterme (REQ-51.21 - REQ-51.25)**
21. **REQ-51.21** WHEN öğrenci matematik problemi çözerken, THE Adım Adım Çözüm Sistemi SHALL her çözüm adımını ayrı bir bölüm olarak göstermek
22. **REQ-51.22** WHEN öğrenci bir adımı görüntülediğinde, THE Adım Adım Çözüm Sistemi SHALL adım numarası, açıklama ve matematiksel ifadeyi içermek
23. **REQ-51.23** WHEN öğrenci adımlar arasında gezindiğinde, THE Adım Adım Çözüm Sistemi SHALL ileri/geri butonları ile navigasyon sağlamak
24. **REQ-51.24** WHEN öğrenci progressive disclosure modunu seçtiğinde, THE Adım Adım Çözüm Sistemi SHALL adımları teker teker açığa çıkarmak
25. **REQ-51.25** WHEN öğrenci tüm adımları görmek istediğinde, THE Adım Adım Çözüm Sistemi SHALL "Tümünü Göster" seçeneği sunmak

**Animasyonlu Geçişler (REQ-51.26 - REQ-51.30)**
26. **REQ-51.26** WHEN öğrenci bir adımdan diğerine geçtiğinde, THE Adım Adım Çözüm Sistemi SHALL 300-500ms yumuşak geçiş animasyonu göstermek
27. **REQ-51.27** WHEN matematiksel ifade değiştiğinde, THE Adım Adım Çözüm Sistemi SHALL değişen kısmı vurgulayarak göstermek
28. **REQ-51.28** WHEN yeni bir adım açıldığında, THE Adım Adım Çözüm Sistemi SHALL fade-in veya slide-in animasyonu kullanmak
29. **REQ-51.29** WHEN öğrenci animasyon hızını ayarlamak istediğinde, THE Adım Adım Çözüm Sistemi SHALL yavaş/normal/hızlı seçenekleri sunmak
30. **REQ-51.30** WHEN öğrenci animasyonları kapatmak istediğinde, THE Adım Adım Çözüm Sistemi SHALL "Animasyonsuz Mod" seçeneği sunmak

**İpucu Sistemi (REQ-51.31 - REQ-51.35)**
31. **REQ-51.31** WHEN öğrenci bir adımda takıldığında, THE İpucu Sistemi SHALL "İpucu Al" butonu göstermek
32. **REQ-51.32** WHEN öğrenci ilk ipucunu istediğinde, THE İpucu Sistemi SHALL hafif seviye ipucu (genel yönlendirme) sunmak
33. **REQ-51.33** WHEN öğrenci ikinci ipucunu istediğinde, THE İpucu Sistemi SHALL orta seviye ipucu (daha spesifik yönlendirme) sunmak
34. **REQ-51.34** WHEN öğrenci üçüncü ipucunu istediğinde, THE İpucu Sistemi SHALL detaylı seviye ipucu (neredeyse tam çözüm) sunmak
35. **REQ-51.35** WHEN öğrenci ipucu kullandığında, THE İpucu Sistemi SHALL kullanım sayısını kaydetmek ve istatistiklere eklemek

**Hata Vurgulama (REQ-51.36 - REQ-51.40)**
36. **REQ-51.36** WHEN öğrenci yanlış bir adım girdiğinde, THE Hata Vurgulama Sistemi SHALL hatalı kısmı kırmızı renk ile vurgulamak
37. **REQ-51.37** WHEN hata tespit edildiğinde, THE Hata Vurgulama Sistemi SHALL hata türünü (işlem hatası, kavram hatası, dikkat hatası) belirlemek
38. **REQ-51.38** WHEN hata gösterildiğinde, THE Hata Vurgulama Sistemi SHALL düzeltici öneri mesajı göstermek
39. **REQ-51.39** WHEN öğrenci hatayı düzelttiğinde, THE Hata Vurgulama Sistemi SHALL yeşil onay işareti ve pozitif geri bildirim göstermek
40. **REQ-51.40** WHEN öğrenci tekrarlayan hata yaptığında, THE Hata Vurgulama Sistemi SHALL ek açıklama ve alternatif çözüm yolu önermek

**Hesap Makinesi ve Araçlar (REQ-51.41 - REQ-51.60)**
41-60. **REQ-51.41-60** SHALL bilimsel hesap makinesi, grafik hesap makinesi, geometri araçları ve formül editörü sağlamak

**Renkli Kodlama (REQ-51.61 - REQ-51.80)**
61-80. **REQ-51.61-80** SHALL pozitif/negatif renkleri, işlem renkleri, parantez seviyeleri ve değişken/sabit renkleri sunmak

**Manipülatifler (REQ-51.81 - REQ-51.100)**
81-100. **REQ-51.81-100** SHALL sanal bloklar, GeoGebra entegrasyonu, interaktif geometri ve dijital tangram sağlamak

---

### REQ-52: DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) Desteği Sistemi

**Kullanıcı Hikayesi:** DEHB tanılı bir öğrenci olarak, dikkatimi yönetmeme yardımcı olacak araçlar, focus mode ve gamification özellikleri kullanmak istiyorum, böylece daha uzun süre odaklanabilir ve öğrenme hedeflerime ulaşabilirim.

#### Kabul Kriterleri (100 Kriter - Özet)

**Dikkat Yönetimi (REQ-52.1 - REQ-52.20)**
1-20. **REQ-52.1-20** SHALL Pomodoro timer, görsel zamanlayıcı, dikkat dağınıklığı tespiti ve konsantrasyon egzersizleri sağlamak

**Focus Mode (REQ-52.21 - REQ-52.40)**
21-40. **REQ-52.21-40** SHALL sadece aktif görev görünümü, minimal arayüz, bildirimler kapalı ve dikkat dağıtıcı unsurları gizleme sunmak

**Görev Bölme ve Organizasyon (REQ-52.41 - REQ-52.60)**
41-60. **REQ-52.41-60** SHALL büyük görevleri küçük adımlara bölme, görsel ilerleme göstergesi, öncelik sıralaması ve renk kodlama sağlamak

**Gamification (REQ-52.61 - REQ-52.80)**
61-80. **REQ-52.61-80** SHALL puan sistemi, seviye sistemi, rozet koleksiyonu ve liderlik tablosu sunmak

**Anında Geri Bildirim (REQ-52.81 - REQ-52.100)**
81-100. **REQ-52.81-100** SHALL her doğru cevap kutlaması, puan kazanma animasyonu, streak takibi ve başarı grafiği sağlamak

---

### REQ-53: OSB (Otizm Spektrum Bozukluğu) Desteği Sistemi

**Kullanıcı Hikayesi:** Otizm spektrumunda olan bir öğrenci olarak, öngörülebilir arayüz, görsel programlar ve net talimatlar içeren bir platform kullanmak istiyorum, böylece belirsizlik ve kaygı yaşamadan öğrenme sürecime devam edebilirim.

#### Kabul Kriterleri (80 Kriter - Özet)

**Öngörülebilir Arayüz (REQ-53.1 - REQ-53.20)**
1-20. **REQ-53.1-20** SHALL tutarlı düzen, sabit menü konumları, değişmeyen renk şeması ve standart ikonlar sağlamak

**Görsel Programlar ve Rutinler (REQ-53.21 - REQ-53.40)**
21-40. **REQ-53.21-40** SHALL günlük program görselleştirmesi, haftalık takvim, adım adım rehberler ve sosyal hikayeler sunmak

**Net ve Açık Talimatlar (REQ-53.41 - REQ-53.60)**
41-60. **REQ-53.41-60** SHALL basit dil kullanımı, kısa cümleler, numaralandırılmış adımlar ve örnekler sağlamak

**Duyusal Yük Azaltma (REQ-53.61 - REQ-53.80)**
61-80. **REQ-53.61-80** SHALL minimal animasyon, sessiz mod, basit arka planlar ve temiz tasarım sunmak

---

## Versiyon Geçmişi

| Versiyon | Tarih | Değişiklikler | Yazar |
|----------|-------|---------------|-------|
| 1.0 | 18 Ekim 2025 | İlk versiyon - Tüm speclerin birleştirilmesi | Claude AI |
| 1.1 | 20 Ekim 2025 | Spec tutarlılık analizi ve 6 yeni requirement eklendi (REQ-48 to REQ-53) | Kiro AI |

---

## Onaylar

| Rol | İsim | Tarih | İmza |
|-----|------|-------|------|
| Product Owner | - | - | - |
| Technical Lead | - | - | - |
| QA Lead | - | - | - |

---

**Toplam Gereksinim Sayısı**: 53 ana gereksinim, 600+ kabul kriteri
**Kapsanan Spec Sayısı**: 6 (Ana Platform, İçerik Yönetimi, Kaynak Kalitesi, Sağlık Denetimi, Gelişmiş AI, Erişilebilirlik)
**Tahmini Okuma Süresi**: 90 dakika

**Yeni Eklenen Gereksinimler (v1.1)**:
- REQ-48: LLM Tabanlı ÖSYM Soru Üretim Sistemi (96 kriter)
- REQ-49: Adaptif Test Sistemi - CAT (100 kriter)
- REQ-50: Disleksi Desteği Sistemi (104 kriter)
- REQ-51: Diskalkuli Desteği Sistemi (100 kriter)
- REQ-52: DEHB Desteği Sistemi (100 kriter)
- REQ-53: OSB Desteği Sistemi (80 kriter)


---

## BÖLÜM 6: ERİŞİLEBİLİRLİK VE ÖZEL GEREKSİNİMLER

### REQ-50: Disleksi Desteği - Tipografi ve Görsel Düzenlemeler

**Kullanıcı Hikayesi:** Disleksisi olan bir öğrenci olarak, okuma zorluğumu azaltacak özel fontlar ve tipografi ayarları kullanmak istiyorum, böylece içerikleri daha rahat okuyabilir ve öğrenme deneyimimi iyileştirebilirim.

#### Kabul Kriterleri

**OpenDyslexic/Dyslexie Font Entegrasyonu (REQ-50.1 - REQ-50.4)**

1. **REQ-50.1** WHEN Platform font seçeneklerini sunduğunda, THE Platform SHALL OpenDyslexic Regular, OpenDyslexic Bold, Dyslexie Regular ve Dyslexie Bold fontlarını WOFF2 formatında yükler ve 500ms içinde kullanılabilir hale getirir
2. **REQ-50.2** WHEN öğrenci font seçici UI component'i açtığında, THE Platform SHALL minimum 5 font seçeneği (Arial, Verdana, OpenDyslexic, Dyslexie, Comic Sans MS) gösterir ve her font için önizleme metni sunar
3. **REQ-50.3** WHEN öğrenci bir font seçtiğinde, THE Platform SHALL seçimi localStorage'da "userFontPreference" anahtarı ile kalıcı olarak saklar ve tüm metin içeriklerine 200ms içinde uygular
4. **REQ-50.4** WHEN öğrenci platformu yeniden açtığında, THE Platform SHALL localStorage'dan font tercihini okur ve sayfa yüklenmesinden sonra 300ms içinde otomatik olarak uygular

**Font Boyutu Ayarlama (REQ-50.5 - REQ-50.7)**

5. **REQ-50.5** WHEN öğrenci font boyutu ayarını açtığında, THE Platform SHALL 12pt ile 24pt arası 1pt artışlarla ayarlama imkanı sunan slider component gösterir ve mevcut boyutu numerik olarak (örn: "16pt") gösterir
6. **REQ-50.6** WHEN öğrenci font boyutunu değiştirdiğinde, THE Platform SHALL değişikliği 100ms içinde gerçek zamanlı önizleme ile gösterir ve tüm metin içeriklerine anında uygular
7. **REQ-50.7** WHEN font boyutu değiştirildiğinde, THE Platform SHALL responsive scaling uygulayarak mobil cihazlarda (320px-768px) minimum 14pt, tablet cihazlarda (768px-1024px) seçilen boyutu ve masaüstü cihazlarda (1024px+) seçilen boyutu koruyarak uyumlu görünüm sağlar

**Satır Aralığı Ayarlama (REQ-50.8 - REQ-50.10)**

8. **REQ-50.8** WHEN öğrenci satır aralığı ayarını açtığında, THE Platform SHALL 1.0x ile 3.0x arası 0.1x artışlarla line-height kontrolü sunan slider component gösterir ve mevcut değeri yüzde olarak (örn: "150%") gösterir
9. **REQ-50.9** WHEN satır aralığı değiştirildiğinde, THE Platform SHALL paragraf aralıklarını (margin-bottom) satır aralığının 1.5 katı olacak şekilde orantılı olarak ayarlar ve 100ms içinde uygular
10. **REQ-50.10** WHEN satır aralığı 1.5x veya üzerine ayarlandığında, THE Platform SHALL okuma konforunu maksimize etmek için satır uzunluğunu maksimum 75 karakter ile sınırlar ve metin hizalamasını sola yaslar

**Kelime ve Harf Aralığı Ayarlama (REQ-50.11 - REQ-50.13)**

11. **REQ-50.11** WHEN öğrenci harf aralığı ayarını açtığında, THE Platform SHALL letter-spacing kontrolü sunar
12. **REQ-50.12** WHEN öğrenci kelime aralığı ayarını açtığında, THE Platform SHALL word-spacing kontrolü sunar
13. **REQ-50.13** WHEN kerning ayarlaması yapıldığında, THE Platform SHALL harf çiftleri arasındaki boşlukları optimize eder

---

### REQ-51: Diskalkuli Desteği - Görsel Matematik Temsilleri

**Kullanıcı Hikayesi:** Diskalkulisi olan bir öğrenci olarak, matematiksel kavramları görsel olarak görmek istiyorum, böylece soyut matematik problemlerini daha iyi anlayabilir ve çözebilirim.

#### Kabul Kriterleri

1. **REQ-51.1** WHEN Platform matematik sorusu sunduğunda, THE Platform SHALL sayı bloklarını görsel olarak temsil eder
2. **REQ-51.2** WHEN kesir problemi gösterildiğinde, THE Platform SHALL kesir çubuklarını interaktif olarak sunar
3. **REQ-51.3** WHEN geometri sorusu sunulduğunda, THE Platform SHALL 3D şekilleri döndürülebilir ve manipüle edilebilir hale getirir
4. **REQ-51.4** WHEN grafik çizimi gerektiğinde, THE Platform SHALL interaktif grafik çizim araçları sağlar
5. **REQ-51.5** WHEN adım adım çözüm gösterildiğinde, THE Platform SHALL her adımı ayrı ve animasyonlu olarak sunar

---

### REQ-52: DEHB Desteği - Dikkat Yönetimi

**Kullanıcı Hikayesi:** DEHB'si olan bir öğrenci olarak, dikkatimi yönetmeme yardımcı olacak araçlar kullanmak istiyorum, böylece odaklanabilir ve çalışma verimliliğimi artırabilirim.

#### Kabul Kriterleri

1. **REQ-52.1** WHEN öğrenci çalışma oturumu başlattığında, THE Platform SHALL Pomodoro timer (25dk çalışma, 5dk mola) sunar
2. **REQ-52.2** WHEN zamanlayıcı çalıştığında, THE Platform SHALL görsel countdown ve progress ring gösterir
3. **REQ-52.3** WHEN dikkat dağınıklığı tespit edildiğinde, THE Platform SHALL nazik hatırlatma bildirimleri gönderir
4. **REQ-52.4** WHEN focus mode aktifleştirildiğinde, THE Platform SHALL sadece aktif görevi gösterir ve dikkat dağıtıcı unsurları gizler
5. **REQ-52.5** WHEN gamification özellikleri kullanıldığında, THE Platform SHALL puan, seviye ve rozet sistemi ile motivasyon sağlar

---

### REQ-53: OSB Desteği - Öngörülebilir Arayüz

**Kullanıcı Hikayesi:** Otizm spektrum bozukluğu olan bir öğrenci olarak, tutarlı ve öngörülebilir bir arayüz kullanmak istiyorum, böylece değişikliklerden rahatsız olmadan rahatça öğrenebilirim.

#### Kabul Kriterleri

1. **REQ-53.1** WHEN Platform arayüzü tasarlandığında, THE Platform SHALL tüm sayfalarda tutarlı düzen kullanır
2. **REQ-53.2** WHEN menü konumları belirlediğinde, THE Platform SHALL sabit ve değişmeyen menü pozisyonları sağlar
3. **REQ-53.3** WHEN renk şeması uygulandığında, THE Platform SHALL değişmeyen ve tutarlı renk paleti kullanır
4. **REQ-53.4** WHEN ikonlar gösterildiğinde, THE Platform SHALL standart ve evrensel ikonlar kullanır
5. **REQ-53.5** WHEN günlük program gösterildiğinde, THE Platform SHALL görsel program ve rutinler sunar

---



---

## BÖLÜM 6: ERİŞİLEBİLİRLİK VE ÖZEL GEREKSİNİMLER

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

---

**Kabul Kriterleri Özeti:**
- ✅ REQ-51.1 - REQ-51.5: Sayı Blokları (Base-10 blocks, interaktif manipülasyon)
- ✅ REQ-51.6 - REQ-51.10: Kesir Çubukları (fraction bars, denk kesir görselleştirme)
- ✅ REQ-51.11 - REQ-51.15: Geometrik Şekiller 3D (3D rendering, rotasyon, ölçüm araçları)
- ✅ REQ-51.16 - REQ-51.20: Grafik Çizim (fonksiyon plotting, interaktif manipülasyon)

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

## BÖLÜM 6: GAMİFİKASYON SİSTEMİ

### REQ-52: Oyunlaştırma ve Motivasyon Sistemi

**Kullanıcı Hikayesi:** Bir öğrenci olarak, çalışmalarım karşılığında puan kazanmak, seviye atlamak ve rozetler toplamak istiyorum, böylece öğrenme sürecim daha eğlenceli ve motive edici olur.

#### Puan Sistemi (REQ-52.61 - REQ-52.65)

1. **REQ-52.61** WHEN öğrenci bir soruyu doğru cevapladığında, THE Gamification Sistemi SHALL soru zorluğuna göre 10-50 puan arasında puan verir
2. **REQ-52.62** WHEN öğrenci günlük çalışma hedefini tamamladığında, THE Gamification Sistemi SHALL 100 bonus puan verir
3. **REQ-52.63** WHEN öğrenci sınavı tamamladığında, THE Gamification Sistemi SHALL performansa göre 50-500 puan arasında puan verir
4. **REQ-52.64** WHEN öğrenci puan geçmişini görüntülediğinde, THE Gamification Sistemi SHALL son 30 günlük puan kazanımlarını grafik ve liste formatında gösterir
5. **REQ-52.65** WHEN öğrenci dashboard'unu açtığında, THE Gamification Sistemi SHALL toplam puan, günlük kazanılan puan ve haftalık kazanılan puanı gösterir

#### Seviye Sistemi (REQ-52.66 - REQ-52.70)

6. **REQ-52.66** WHEN öğrenci yeterli deneyim puanı topladığında, THE Seviye Sistemi SHALL otomatik olarak bir üst seviyeye yükseltir
7. **REQ-52.67** WHEN öğrenci seviye atladığında, THE Seviye Sistemi SHALL kutlama animasyonu gösterir ve bildirim gönderir
8. **REQ-52.68** WHEN Seviye Sistemi deneyim puanı hesapladığında, THE Seviye Sistemi SHALL her seviye için gereken XP'yi üstel formül ile hesaplar (Level * 100 * 1.5^Level)
9. **REQ-52.69** WHEN öğrenci profil sayfasını görüntülediğinde, THE Seviye Sistemi SHALL mevcut seviye, toplam XP, bir sonraki seviyeye kalan XP ve ilerleme çubuğunu gösterir
10. **REQ-52.70** WHEN öğrenci seviye 10, 25, 50, 75, 100'e ulaştığında, THE Seviye Sistemi SHALL özel milestone rozeti verir

#### Rozet Koleksiyonu (REQ-52.71 - REQ-52.75)

11. **REQ-52.71** WHEN öğrenci belirli bir başarıyı tamamladığında, THE Rozet Sistemi SHALL ilgili rozeti otomatik olarak verir ve bildirim gösterir
12. **REQ-52.72** WHEN öğrenci rozet koleksiyonunu görüntülediğinde, THE Rozet Sistemi SHALL kazanılan rozetleri renkli, kazanılmayanları gri olarak gösterir
13. **REQ-52.73** WHEN Rozet Sistemi nadir rozet verdiğinde, THE Rozet Sistemi SHALL özel animasyon ve ses efekti ile kutlama yapar
14. **REQ-52.74** WHEN öğrenci rozet detayını görüntülediğinde, THE Rozet Sistemi SHALL rozet adı, açıklama, kazanma tarihi ve nadir seviyesini (yaygın/nadir/efsanevi) gösterir
15. **REQ-52.75** WHEN öğrenci 7 gün üst üste çalıştığında, THE Rozet Sistemi SHALL "Kararlı Öğrenci" rozetini verir

#### Liderlik Tablosu (REQ-52.76 - REQ-52.80)

16. **REQ-52.76** WHEN öğrenci liderlik tablosunu görüntülediğinde, THE Liderlik Sistemi SHALL haftalık, aylık ve tüm zamanlar olmak üzere 3 farklı zaman dilimi sunar
17. **REQ-52.77** WHEN Liderlik Sistemi sıralama yaptığında, THE Liderlik Sistemi SHALL toplam puana göre ilk 100 öğrenciyi listeler
18. **REQ-52.78** WHEN öğrenci arkadaş karşılaştırması yaptığında, THE Liderlik Sistemi SHALL sadece arkadaş listesindeki öğrencileri gösterir
19. **REQ-52.79** WHEN öğrenci sınıf sıralamasını görüntülediğinde, THE Liderlik Sistemi SHALL aynı sınıftaki tüm öğrencileri puana göre sıralar
20. **REQ-52.80** WHEN öğrenci liderlik tablosunda ilk 3'e girdiğinde, THE Liderlik Sistemi SHALL profil sayfasında özel altın/gümüş/bronz rozet gösterir

---

### REQ-53: Rozet Kategorileri ve Başarı Kriterleri

**Kullanıcı Hikayesi:** Bir öğrenci olarak, farklı kategorilerde rozetler kazanmak istiyorum, böylece çeşitli alanlarda gelişimimi görebilirim.

#### Kabul Kriterleri

**Çalışma Rozetleri (REQ-53.1 - REQ-53.5)**

1. **REQ-53.1** WHEN öğrenci 7 gün üst üste çalıştığında, THE Rozet Sistemi SHALL "Kararlı Öğrenci" (yaygın) rozetini verir
2. **REQ-53.2** WHEN öğrenci 30 gün üst üste çalıştığında, THE Rozet Sistemi SHALL "Azimli Öğrenci" (nadir) rozetini verir
3. **REQ-53.3** WHEN öğrenci 100 gün üst üste çalıştığında, THE Rozet Sistemi SHALL "Efsane Öğrenci" (efsanevi) rozetini verir
4. **REQ-53.4** WHEN öğrenci toplam 1000 soru çözdüğünde, THE Rozet Sistemi SHALL "Soru Avcısı" rozetini verir
5. **REQ-53.5** WHEN öğrenci toplam 100 saat çalıştığında, THE Rozet Sistemi SHALL "Zaman Yöneticisi" rozetini verir

**Sınav Rozetleri (REQ-53.6 - REQ-53.10)**

6. **REQ-53.6** WHEN öğrenci ilk denemesinde %80 üzeri aldığında, THE Rozet Sistemi SHALL "Parlak Başlangıç" rozetini verir
7. **REQ-53.7** WHEN öğrenci 10 deneme sınavı tamamladığında, THE Rozet Sistemi SHALL "Sınav Ustası" rozetini verir
8. **REQ-53.8** WHEN öğrenci bir konuda 3 sınavda üst üste %90 üzeri aldığında, THE Rozet Sistemi SHALL "Konu Uzmanı" rozetini verir
9. **REQ-53.9** WHEN öğrenci tam puan aldığında, THE Rozet Sistemi SHALL "Mükemmeliyetçi" (nadir) rozetini verir
10. **REQ-53.10** WHEN öğrenci TYT, AYT ve YDT'nin hepsini tamamladığında, THE Rozet Sistemi SHALL "Tam Hazır" rozetini verir

**Sosyal Rozetler (REQ-53.11 - REQ-53.15)**

11. **REQ-53.11** WHEN öğrenci 10 arkadaşını platforma davet ettiğinde, THE Rozet Sistemi SHALL "Topluluk Lideri" rozetini verir
12. **REQ-53.12** WHEN öğrenci liderlik tablosunda ilk 10'a girdiğinde, THE Rozet Sistemi SHALL "Yıldız Öğrenci" rozetini verir
13. **REQ-53.13** WHEN öğrenci 100 soru paylaştığında, THE Rozet Sistemi SHALL "Bilgi Paylaşımcısı" rozetini verir
14. **REQ-53.14** WHEN öğrenci 50 yorum yaptığında, THE Rozet Sistemi SHALL "Aktif Katılımcı" rozetini verir
15. **REQ-53.15** WHEN öğrenci bir arkadaşına 10 kez yardım ettiğinde, THE Rozet Sistemi SHALL "Yardımsever" rozetini verir

**Özel Rozetler (REQ-53.16 - REQ-53.20)**

16. **REQ-53.16** WHEN öğrenci gece 00:00-06:00 arası çalıştığında, THE Rozet Sistemi SHALL "Gece Kuşu" rozetini verir
17. **REQ-53.17** WHEN öğrenci sabah 05:00-07:00 arası çalıştığında, THE Rozet Sistemi SHALL "Erken Kuş" rozetini verir
18. **REQ-53.18** WHEN öğrenci bir günde 5 saat çalıştığında, THE Rozet Sistemi SHALL "Maraton Koşucusu" rozetini verir
19. **REQ-53.19** WHEN öğrenci tüm konuları tamamladığında, THE Rozet Sistemi SHALL "Konu Tamamlayıcı" (efsanevi) rozetini verir
20. **REQ-53.20** WHEN öğrenci platformda 1 yıl aktif olduğunda, THE Rozet Sistemi SHALL "Sadık Öğrenci" (efsanevi) rozetini verir

---

### REQ-54: Motivasyon ve Bildirimler

**Kullanıcı Hikayesi:** Bir öğrenci olarak, başarılarım için anında geri bildirim ve kutlama almak istiyorum, böylece motive olur ve çalışmaya devam ederim.

#### Kabul Kriterleri

1. **REQ-54.1** WHEN öğrenci rozet kazandığında, THE Bildirim Sistemi SHALL modal popup ile kutlama gösterir
2. **REQ-54.2** WHEN öğrenci seviye atladığında, THE Bildirim Sistemi SHALL tam ekran animasyon ve ses efekti ile kutlar
3. **REQ-54.3** WHEN öğrenci günlük hedefini tamamladığında, THE Bildirim Sistemi SHALL başarı bildirimi ve konfeti animasyonu gösterir
4. **REQ-54.4** WHEN öğrenci liderlik tablosunda yükseldiğinde, THE Bildirim Sistemi SHALL sıralama değişikliğini bildirir
5. **REQ-54.5** WHEN öğrenci 3 gün çalışmadığında, THE Bildirim Sistemi SHALL nazik hatırlatma bildirimi gönderir

---

### REQ-55: Gamification Analytics ve Raporlama

**Kullanıcı Hikayesi:** Bir öğrenci olarak, gamification istatistiklerimi görmek istiyorum, böylece ilerlememı takip edebilirim.

#### Kabul Kriterleri

1. **REQ-55.1** WHEN öğrenci istatistikler sayfasını açtığında, THE Analytics Sistemi SHALL toplam puan, seviye, rozet sayısı ve sıralama bilgilerini gösterir
2. **REQ-55.2** WHEN Analytics Sistemi puan grafiği çizdiğinde, THE Analytics Sistemi SHALL son 30 günlük puan kazanımlarını çizgi grafik ile gösterir
3. **REQ-55.3** WHEN öğrenci rozet ilerlemesini görüntülediğinde, THE Analytics Sistemi SHALL kategori bazlı rozet tamamlanma yüzdesini gösterir
4. **REQ-55.4** WHEN öğrenci seviye geçmişini görüntülediğinde, THE Analytics Sistemi SHALL her seviyeye ulaşma tarihini ve süresini gösterir
5. **REQ-55.5** WHEN öğrenci karşılaştırma yaptığında, THE Analytics Sistemi SHALL kendi istatistiklerini sınıf ortalaması ile karşılaştırır

