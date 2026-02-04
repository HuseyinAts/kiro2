# Requirements Document

## Introduction

Learning Path sayfasında video yükleme işlemi sistematik olarak başarısız oluyor. Kullanıcılar "AI size özel videoları buluyor" mesajını görüyor, ardından 10 saniye timeout sonrası "Videoları 10 saniye içinde yükleyemedik, örnek içerikler gösteriliyor" hatası alıyorlar. Bu kritik sorun, öğrencilerin kişiselleştirilmiş video içeriklerine erişimini tamamen engelliyor ve platformun temel değer önerisini (AI destekli kişiselleştirilmiş öğrenme) işlevsiz hale getiriyor.

Mevcut sistem analizi:
- Frontend: `main.tsx` içinde `/api/youtube/recommendations` endpoint'ine POST isteği gönderiliyor
- Backend: `youtube_routes.py` içinde endpoint tanımlı ve çalışır durumda
- Timeout: 10 saniye (çok kısa)
- Hata yönetimi: Yetersiz loglama ve kullanıcı geri bildirimi
- Performans: Video discovery işlemi optimize edilmemiş
- Monitoring: Servis sağlığı izlenmiyor

## Glossary

- **Learning Path**: Öğrencinin hedeflerine ve seviyesine göre oluşturulan kişiselleştirilmiş öğrenme yolu
- **Video Discovery API**: YouTube'dan eğitim videoları bulan ve öneren backend servisi (`youtube_routes.py`)
- **Frontend**: React/TypeScript tabanlı kullanıcı arayüzü (main.tsx)
- **Backend**: FastAPI tabanlı Python sunucusu
- **API_BASE_URL**: Frontend'in backend'e bağlanmak için kullandığı temel URL (environment variable)
- **Timeout**: API isteğinin maksimum bekleme süresi (şu an 10 saniye)
- **Fallback Videos**: API başarısız olduğunda gösterilen statik örnek videolar
- **AdvancedYouTubeSearch**: Backend'de video arama ve filtreleme servisi
- **SemanticYouTubeSearch**: Embedding tabanlı semantik video arama servisi
- **RealYouTubeAPI**: Gerçek YouTube Data API v3 entegrasyonu
- **StudentProfile**: Öğrenci hedefleri, seviye ve öğrenme stili bilgilerini içeren veri modeli
- **CORS**: Cross-Origin Resource Sharing - frontend-backend arası güvenli iletişim
- **Health Check**: Servis sağlık durumu kontrolü endpoint'i
- **Structured Logging**: JSON formatında detaylı log kayıtları
- **Cache Hit Rate**: Cache'den başarılı veri çekme oranı
- **Rate Limiting**: API isteklerinin hız sınırlaması
- **Circuit Breaker**: Başarısız servisleri geçici olarak devre dışı bırakan koruma mekanizması

## Requirements

### Requirement 0: Sistem Başlangıç Sağlık Kontrolü

**User Story:** Sistem yöneticisi olarak, sistem başlatıldığında tüm bileşenlerin sağlıklı çalıştığını doğrulamak istiyorum, böylece kullanıcılar hizmet almaya başlamadan önce sorunları tespit edebilirim.

#### Acceptance Criteria

1. WHEN Backend başlatıldığında, THE Backend SHALL tüm bağımlı servislerin (Database, Cache, YouTube API) sağlık durumunu kontrol etmeli
2. THE Backend SHALL başlangıç sağlık kontrolü sonuçlarını yapılandırılmış log formatında kaydetmeli
3. THE Backend SHALL `/api/youtube/test` endpoint'i üzerinden erişilebilirlik testi sağlamalı
4. WHEN CORS hatası oluştuğunda, THE Backend SHALL uygun CORS header'larını yanıta dahil etmeli
5. THE Backend SHALL başlangıçta API bağlantı bilgilerini doğrulamalı
6. WHEN kritik bir bağımlı servis erişilemez durumda ise, THE Backend SHALL uyarı seviyesinde log kaydı oluşturmalı
7. THE Backend SHALL başlangıç sağlık kontrolü sonuçlarını metrics sistemine raporlamalı

## Requirements

### Requirement 1: Video API Bağlantı Diagnostics ve Hata Yönetimi

**User Story:** Geliştirici olarak, video yükleme hatalarının kök nedenini anlayabilmek ve otomatik olarak çözebilmek için kapsamlı diagnostik ve self-healing mekanizması istiyorum, böylece kullanıcılar kesintisiz hizmet alabilsin.

#### Acceptance Criteria

1. WHEN Frontend video öneri isteği gönderdiğinde, THE Backend SHALL isteği timestamp, request_id ve profil özeti ile birlikte yapılandırılmış formatta loglamalı
2. WHEN API isteği başarısız olduğunda, THE Frontend SHALL hata detaylarını yapılandırılmış formatta loglamalı
3. WHEN Backend servisi erişilemez durumda ise, THE Frontend SHALL kullanıcıya anlaşılır hata mesajı göstermeli
4. WHEN CORS hatası oluştuğunda, THE Backend SHALL gerekli CORS header'larını yanıta dahil etmeli
5. WHEN API bağlantı adresi geçersiz ise, THE Frontend SHALL kullanıcıya yapılandırma hatası mesajı göstermeli
6. THE Backend SHALL her API isteği için benzersiz tanımlayıcı oluşturmalı ve tüm ilgili loglarda kullanmalı
7. WHEN ağ zaman aşımı oluştuğunda, THE Frontend SHALL otomatik olarak bir kez daha deneme yapmalı
8. THE Backend SHALL API yanıt sürelerini ölçmeli ve 5 saniyeyi aşan istekleri uyarı seviyesinde loglamalı
9. THE Frontend SHALL sayfa yüklendiğinde API erişilebilirliğini test etmeli

### Requirement 2: Video Yükleme Performans Optimizasyonu

**User Story:** Öğrenci olarak, learning path sayfasını açtığımda videoların 3 saniye içinde yüklenmesini istiyorum, böylece beklemeden öğrenmeye başlayabilirim ve platformun hızlı olduğunu hissedebilirim.

#### Acceptance Criteria

1. WHEN öğrenci learning path sayfasını açtığında, THE Backend SHALL video önerilerini 3 saniye içinde döndürmeli (P95 latency)
2. IF video yükleme 2 saniyeden uzun sürerse, THEN THE Frontend SHALL kullanıcıya ilerleme yüzdesi ile birlikte durum mesajı göstermeli
3. WHEN Backend 20 saniye içinde yanıt vermediğinde, THE Frontend SHALL alternatif örnek videolara geçmeli
4. WHEN aynı öğrenci profili için öneri cache'de mevcut ise, THE Backend SHALL cache'den 100ms içinde yanıt döndürmeli
5. THE Backend SHALL video keşif işlemlerini paralel olarak yürütmeli
6. WHEN video arama servisi yavaş yanıt verdiğinde, THE Backend SHALL önce cache'deki verileri döndürmeli ve arka planda güncelleme yapmalı
7. THE Backend SHALL video meta verilerini kalıcı depolamada önbelleklemeli
8. WHEN birden fazla konu için video istendiğinde, THE Backend SHALL istekleri eşzamanlı olarak işlemeli
9. THE Backend SHALL video kalite skorlamasını optimize etmeli
10. THE Frontend SHALL video görsellerini gerektiğinde yüklemeli
11. WHEN video listesi uzun ise, THE Frontend SHALL sayfalama veya sonsuz kaydırma kullanmalı
12. THE Backend SHALL veritabanı sorgularını optimize etmeli

### Requirement 3: Kullanıcı Deneyimi İyileştirmeleri

**User Story:** Öğrenci olarak, video yükleme sırasında ne olduğunu net bir şekilde anlamak ve kontrol sahibi olmak istiyorum, böylece sistemin çalıştığından emin olabilir ve gerektiğinde müdahale edebilirim.

#### Acceptance Criteria

1. WHEN video yükleme başladığında, THE Frontend SHALL kullanıcıya konu bazlı dinamik yükleme mesajı göstermeli
2. WHILE videolar yüklenirken, THE Frontend SHALL animasyonlu ilerleme göstergesi göstermeli
3. WHEN video yükleme başarılı olduğunda, THE Frontend SHALL video sayısı ile birlikte başarı mesajı göstermeli
4. IF video yükleme başarısız olursa, THEN THE Frontend SHALL kullanıcıya yeniden deneme ve alternatif içerik seçenekleri sunmalı
5. WHEN alternatif videolar gösterildiğinde, THE Frontend SHALL kullanıcıya durum açıklaması ve arka plan işlemi bilgisi göstermeli
6. THE Frontend SHALL video yükleme süresini kullanıcıya göstermeli
7. WHEN video yükleme 5 saniyeden uzun sürdüğünde, THE Frontend SHALL bekleme mesajı göstermeli
8. THE Frontend SHALL yükleme sırasında kullanıcıya sayfa kapatma uyarısı göstermeli
9. WHEN kullanıcı yeniden deneme seçeneğini kullandığında, THE Frontend SHALL yeni tanımlayıcı ile istek göndermelidir
10. THE Frontend SHALL hata nedenlerini teknik olmayan dilde açıklamalı
11. WHEN videolar yüklendiğinde, THE Frontend SHALL videoları yumuşak geçiş animasyonu ile göstermeli
12. THE Frontend SHALL kullanıcının tercih değişikliklerini anında işlemeli
13. WHEN kullanıcı video izlediğinde, THE Frontend SHALL izleme bilgisini Backend'e iletmeli
14. THE Frontend SHALL hataları kullanıcıya göstermeden önce 2 kez otomatik yeniden deneme yapmalı
15. WHEN alternatif mod aktif iken, THE Frontend SHALL arka planda kişiselleştirilmiş önerileri almaya devam etmeli ve hazır olduğunda bildirim göstermeli

### Requirement 4: Servis Sağlık İzleme ve Yönetimi

**User Story:** Sistem yöneticisi olarak, video öneri servisinin sağlık durumunu gerçek zamanlı izleyebilmek ve sorunları otomatik tespit edip müdahale edebilmek istiyorum, böylece kullanıcılar kesintisiz hizmet alabilsin.

#### Acceptance Criteria

1. THE Backend SHALL sağlık kontrolü endpoint'i üzerinden detaylı durum bilgisi sağlamalı
2. WHEN sağlık kontrolü çağrıldığında, THE Backend SHALL 500ms içinde yanıt vermeli
3. THE Backend SHALL video öneri servisinin durumunu ve her bileşenin ayrı ayrı durumunu raporlamalı
4. THE Backend SHALL belirtilen zaman aralıklarında başarılı ve başarısız istek sayısını, ortalama yanıt süresini ve hata oranını raporlamalı
5. WHEN servis hata oranı eşik değerini aştığında, THE System SHALL otomatik olarak alternatif moda geçmeli ve alarm göndermelidir
6. THE Backend SHALL düzenli aralıklarla kendi sağlık kontrolünü yapmalı ve sonuçları loglamalı
7. THE Backend SHALL API kota kullanımını izlemeli ve eşik değere ulaştığında uyarı loglamalı
8. WHEN veritabanı bağlantısı koptuğunda, THE Backend SHALL otomatik olarak yeniden bağlanmayı denemeli
9. THE Backend SHALL önbellek isabet oranını izlemeli ve eşik değerin altına düştüğünde stratejiyi optimize etmeli
10. THE Backend SHALL her endpoint için yanıt süresi metriklerini toplamalı
11. WHEN bir endpoint sürekli başarısız olduğunda, THE Backend SHALL devre kesici mekanizması uygulayarak servisi geçici olarak devre dışı bırakmalı
12. THE Backend SHALL sistem kaynak kullanımını izlemeli ve eşik değeri aştığında uyarı loglamalı
13. THE Backend SHALL aktif bağlantı sayısını izlemeli ve limite yaklaştığında yeni bağlantıları sınırlamalı
14. THE Backend SHALL sağlık kontrolü sonuçlarını standart metrik formatında sunmalı
15. WHEN kritik bir bileşen erişilemez durumda ise, THE Backend SHALL alternatif veri kaynaklarına geçmeli

### Requirement 5: Hata Yönetimi ve Gözlemlenebilirlik

**User Story:** Geliştirici olarak, production ortamında oluşan hataları gerçek zamanlı yakalayıp analiz edebilmek ve kök nedeni hızlıca tespit edebilmek istiyorum, böylece kullanıcı deneyimini sürekli iyileştirebilirim ve ortalama kurtarma süresini minimize edebilirim.

#### Acceptance Criteria

1. THE Backend SHALL tüm API hatalarını yapılandırılmış log formatında timestamp, request_id, user_id, endpoint, error_type, error_message ve stack_trace bilgileriyle kaydetmeli
2. WHEN kritik bir hata oluştuğunda, THE Backend SHALL hata detaylarını, stack trace'i, istek verisini ve sistem durumunu loglamalı
3. THE Frontend SHALL hata durumlarını hata izleme servisi ile raporlamalı ve kullanıcı bağlamı bilgilerini eklemeli
4. THE System SHALL hata oranını gerçek zamanlı izlemeli ve eşik değeri aştığında alarm vermeli
5. WHEN aynı hata kısa sürede tekrar ettiğinde, THE System SHALL hata desenini tespit edip otomatik olay kaydı oluşturmalı
6. THE Backend SHALL her API isteği için dağıtık izleme kullanmalı ve istek akışını görselleştirmeli
7. THE Backend SHALL özel hata sınıfları tanımlamalı ve her hata tipini farklı şekilde yönetmeli
8. WHEN API kota limitine ulaşıldığında, THE Backend SHALL bunu özel hata tipi olarak loglamalı ve otomatik olarak önbelleğe geçmeli
9. THE Backend SHALL hata kurtarma stratejileri uygulamalı
10. THE Frontend SHALL ağ hatalarını kategorize etmeli ve kullanıcıya uygun mesaj göstermeli
11. THE Backend SHALL hata loglarını önem derecesine göre kategorize etmeli
12. THE System SHALL hata trendlerini analiz etmeli ve tekrarlayan sorunları otomatik tespit etmeli
13. THE Backend SHALL API yanıt süresi SLA'yı aştığında uyarı loglamalı
14. THE Frontend SHALL kullanıcı hata raporlama mekanizması sağlamalı
15. THE Backend SHALL hata loglarını merkezi log toplama sistemine göndermelidir
16. WHEN veritabanı sorgu zaman aşımı oluştuğunda, THE Backend SHALL sorguyu ve yürütme planını loglamalı
17. THE System SHALL hata bütçesi takibi yapmalı
18. THE Backend SHALL kademeli bozulma uygulayarak kritik olmayan özellikleri devre dışı bırakmalı ancak temel işlevselliği korumalı
19. THE Frontend SHALL çevrimdışı mod desteği sağlamalı ve ağ bağlantısı geri geldiğinde otomatik senkronizasyon yapmalı
20. THE Backend SHALL kritik sistem hatalarında otomatik yeniden başlatma mekanizması ve hata dökümü oluşturmalı


### Requirement 6: Video Cache Stratejisini Optimize Et

**User Story:** Öğrenci olarak, aynı konularda tekrar video aramak istediğimde anında sonuç almak istiyorum, böylece her seferinde beklemek zorunda kalmam.

#### Acceptance Criteria

1. THE Backend SHALL video önerilerini student profile hash'ine göre cache'lemeli (Redis veya in-memory cache)
2. WHEN aynı student profile için istek geldiğinde, THE Backend SHALL cache'den 100ms içinde dönmeli
3. THE Backend SHALL cache TTL (Time To Live) değerini 1 saat olarak ayarlamalı
4. WHEN cache miss olduğunda, THE Backend SHALL video discovery yapmalı ve sonucu cache'e yazmalı
5. THE Backend SHALL cache invalidation stratejisi uygulamalı (yeni videolar eklendiğinde cache'i güncelleme)
6. THE Backend SHALL cache hit/miss oranını metrik olarak toplamalı
7. WHEN cache full olduğunda, THE Backend SHALL LRU (Least Recently Used) eviction policy uygulamalı
8. THE Backend SHALL video metadata'sını ayrı bir cache layer'da saklamalı (video details cache)
9. THE Backend SHALL cache warming stratejisi uygulamalı (popüler konular için önceden cache doldurma)
10. THE Backend SHALL cache'i async olarak güncellemelidir (blocking operation olmamalı)

### Requirement 7: API Rate Limiting ve Throttling Uygula

**User Story:** Sistem yöneticisi olarak, YouTube API quota'sını verimli kullanmak ve aşırı yüklenmeyi önlemek istiyorum, böylece servis sürdürülebilir olsun.

#### Acceptance Criteria

1. THE Backend SHALL YouTube API çağrılarına rate limiting uygulamalı (günlük 10,000 quota limit)
2. WHEN rate limit'e yaklaşıldığında (%80), THE Backend SHALL cache'i daha agresif kullanmalı
3. THE Backend SHALL user bazlı rate limiting uygulamalı (kullanıcı başına dakikada 10 istek)
4. WHEN rate limit aşıldığında, THE Backend SHALL 429 (Too Many Requests) status code dönmeli
5. THE Backend SHALL rate limit bilgisini response header'larında döndürmeli (X-RateLimit-Remaining)
6. THE Backend SHALL IP bazlı throttling uygulamalı (DDoS koruması)
7. THE Backend SHALL authenticated user'lara daha yüksek rate limit vermeli
8. THE Backend SHALL rate limit metriklerini izlemeli ve raporlamalı
9. WHEN YouTube API quota bitti ise, THE Backend SHALL tamamen cache'e geçmeli ve kullanıcıyı bilgilendirmeli
10. THE Backend SHALL adaptive rate limiting uygulamalı (sistem yükü yüksekse rate limit'i düşürmeli)

### Requirement 8: Video Kalite Skorlama Algoritması

**User Story:** Öğrenci olarak, bana önerilen videoların gerçekten kaliteli ve öğretici olmasını istiyorum, böylece zamanımı verimli kullanabilirim.

#### Acceptance Criteria

1. THE Backend SHALL video kalite skorunu çoklu faktöre göre hesaplamalı
2. THE Backend SHALL güvenilir eğitim kanallarına bonus puan vermeli
3. THE Backend SHALL video süresini değerlendirmeli ve uygun olmayan sürelere düşük puan vermeli
4. THE Backend SHALL video güncelliğini değerlendirmeli ve yakın tarihli içeriklere bonus vermeli
5. THE Backend SHALL etkileşim oranını hesaplamalı
6. THE Backend SHALL spam ve yanıltıcı içerikleri filtrelemeli
7. THE Backend SHALL öğrenci seviyesine göre video zorluğunu eşleştirmeli
8. THE Backend SHALL mümkün olduğunda video içeriğini analiz ederek kaliteyi değerlendirmeli
9. THE Backend SHALL kullanıcı geri bildirimini kalite skoruna dahil etmeli
10. THE Backend SHALL farklı skorlama algoritmalarını test etmeli

### Requirement 9: Semantic Search ve AI Tabanlı Öneri Sistemini Geliştir

**User Story:** Öğrenci olarak, tam olarak ne aradığımı bilmesem bile ihtiyacıma uygun videoların bulunmasını istiyorum, böylece öğrenme hedeflerime daha hızlı ulaşabilirim.

#### Acceptance Criteria

1. THE Backend SHALL video başlıklarını ve açıklamalarını embedding'e çevirmeli (sentence transformers)
2. THE Backend SHALL student profile'ı embedding'e çevirmeli (goals, interests, learning style)
3. THE Backend SHALL cosine similarity ile en yakın videoları bulmalı
4. THE Backend SHALL hybrid search uygulamalı (keyword + semantic search kombinasyonu)
5. THE Backend SHALL öğrencinin geçmiş izleme davranışını analiz ederek personalize öneri vermeli
6. THE Backend SHALL collaborative filtering uygulamalı (benzer öğrencilerin izlediği videolar)
7. THE Backend SHALL content-based filtering uygulamalı (izlenen videoların benzerlerini önerme)
8. THE Backend SHALL diversity'yi sağlamalı (sadece aynı tip videoları önermemeli)
9. THE Backend SHALL exploration vs exploitation balance kurmalı (yeni içerikler vs bilinen içerikler)
10. THE Backend SHALL real-time learning uygulamalı (öğrenci feedback'ine göre model'i güncelleme)

### Requirement 10: Frontend State Management ve Error Handling İyileştir

**User Story:** Geliştirici olarak, frontend'de state management'ı daha iyi yönetmek ve hataları gracefully handle etmek istiyorum, böylece kullanıcı deneyimi tutarlı olsun.

#### Acceptance Criteria

1. THE Frontend SHALL video loading state'ini merkezi bir state management ile yönetmeli (React Context veya Redux)
2. THE Frontend SHALL loading, success, error state'lerini ayrı ayrı handle etmeli
3. THE Frontend SHALL optimistic UI update uygulamalı (kullanıcıya anında feedback)
4. THE Frontend SHALL error boundary kullanarak component crash'lerini yakalamalı
5. THE Frontend SHALL retry logic'i exponential backoff ile uygulamalı
6. THE Frontend SHALL network status'ü izlemeli (online/offline detection)
7. THE Frontend SHALL request cancellation uygulamalı (kullanıcı sayfadan ayrılırsa)
8. THE Frontend SHALL loading skeleton göstermeli (content placeholder)
9. THE Frontend SHALL error recovery UI sağlamalı (kullanıcı ne yapmalı?)
10. THE Frontend SHALL state persistence uygulamalı (sayfa yenilendiğinde state'i koruma)

### Requirement 11: Testing ve Quality Assurance Stratejisi

**User Story:** Geliştirici olarak, video yükleme özelliğinin her zaman çalıştığından emin olmak istiyorum, böylece regression bug'ları önleyebilirim.

#### Acceptance Criteria

1. THE Backend SHALL video discovery endpoint'leri için unit test yazmalı (%80+ coverage)
2. THE Backend SHALL integration test yazmalı (YouTube API mock'lama ile)
3. THE Backend SHALL load test yapmalı (100 concurrent user simülasyonu)
4. THE Frontend SHALL component test yazmalı (React Testing Library)
5. THE Frontend SHALL E2E test yazmalı (Playwright/Cypress ile video yükleme flow'u)
6. THE System SHALL smoke test uygulamalı (production deploy sonrası otomatik test)
7. THE Backend SHALL contract testing uygulamalı (API schema validation)
8. THE Backend SHALL chaos engineering uygulamalı (servis failure simülasyonu)
9. THE System SHALL performance regression test yapmalı (response time monitoring)
10. THE System SHALL security testing yapmalı (OWASP Top 10 kontrolleri)

### Requirement 12: Documentation ve Developer Experience

**User Story:** Geliştirici olarak, video API'sini kullanmak ve troubleshoot etmek için kapsamlı dokümantasyon istiyorum, böylece hızlıca sorun çözebilirim.

#### Acceptance Criteria

1. THE Backend SHALL OpenAPI/Swagger dokümantasyonu sağlamalı
2. THE Backend SHALL her endpoint için örnek request/response göstermeli
3. THE Backend SHALL hata kodları ve çözüm önerileri dokümante etmeli
4. THE Backend SHALL API versioning stratejisi uygulamalı
5. THE Backend SHALL changelog tutmalı (API değişiklikleri)
6. THE Backend SHALL developer guide yazmalı (local setup, testing, debugging)
7. THE Backend SHALL architecture diagram sağlamalı (system design)
8. THE Backend SHALL troubleshooting guide yazmalı (common issues ve solutions)
9. THE Backend SHALL performance tuning guide sağlamalı
10. THE Backend SHALL API usage examples sağlamalı (farklı use case'ler için)


### Requirement 13: Video Alakalılık ve Türkçe İçerik Filtreleme

**User Story:** Öğrenci olarak, bana önerilen videoların tam olarak ders konusu ve zorluk seviyemle alakalı olmasını ve Türkçe olmasını istiyorum, böylece alakasız veya yabancı dilde videolarla zaman kaybetmeyeyim.

#### Acceptance Criteria

1. THE Backend SHALL her videonun ders konusu ile alakasını 0-100 arası alakalılık skoru ile hesaplamalı
2. THE Backend SHALL video başlığını ve açıklamasını doğal dil işleme ile analiz ederek konu uyumunu değerlendirmeli
3. THE Backend SHALL minimum eşik değerinin üzerinde alakalılık skoruna sahip videoları önermeli
4. THE Backend SHALL video dilini otomatik tespit etmeli
5. THE Backend SHALL Türkçe dil koduna sahip videoları filtrelemeli
6. THE Backend SHALL video başlığında ve açıklamasında Türkçe karakter varlığını kontrol etmeli
7. THE Backend SHALL mümkün olduğunda video içeriğini analiz ederek dilin Türkçe olduğunu doğrulamalı
8. THE Backend SHALL Türkçe olmayan videoları filtrelemeli
9. THE Backend SHALL zorluk seviyesi uyumunu hesaplamalı
10. THE Backend SHALL belirtilen eşik değerinden fazla zorluk seviyesi farkı olan videoları filtrelemeli
11. THE Backend SHALL konu taksonomisi kullanarak video konusunu kategorize etmeli
12. THE Backend SHALL video konusu ile istenen konu arasındaki anlamsal benzerliği hesaplamalı
13. THE Backend SHALL ulusal müfredata uygun konu eşleştirmesi yapmalı
14. THE Backend SHALL video içeriğinde konu dışı segmentleri tespit etmeli
15. THE Backend SHALL kanal itibarını kontrol ederek güvenilir eğitim kanallarını önceliklendirmeli
16. THE Backend SHALL video meta verilerinde dil etiketi uygun olmayanları filtrelemeli
17. THE Backend SHALL video yorumlarını analiz ederek Türkçe içerik olduğunu doğrulamalı
18. THE Backend SHALL yabancı dilde videoları filtrelemeli
19. THE Backend SHALL karışık dilli videoları tespit etmeli ve filtrelemeli
20. THE Backend SHALL alakalılık ve dil filtreleme metriklerini loglamalı ve raporlamalı

### Requirement 14: Konu Bazlı Video Kategorilendirme ve Eşleştirme

**User Story:** Öğrenci olarak, aradığım konuyla tam olarak eşleşen videoların bulunmasını istiyorum, böylece yanlış konuda video izleyerek zaman kaybetmeyeyim.

#### Acceptance Criteria

1. THE Backend SHALL ulusal müfredata uygun konu taksonomisi oluşturmalı
2. THE Backend SHALL her videoyu taksonomi içindeki bir veya birden fazla konuya eşleştirmeli
3. THE Backend SHALL video başlığından konu anahtar kelimelerini çıkarmalı
4. THE Backend SHALL video açıklamasından konu anahtar kelimelerini çıkarmalı
5. THE Backend SHALL konu eşleştirmesinde eş anlamlıları dikkate almalı
6. THE Backend SHALL konu hiyerarşisini dikkate almalı
7. THE Backend SHALL çoklu konulu videoları tespit etmeli ve her konuya ayrı ayrı eşleştirmeli
8. THE Backend SHALL konu eşleştirme güven skoru hesaplamalı
9. THE Backend SHALL düşük güven skorlu eşleştirmeleri filtrelemeli
10. THE Backend SHALL öğrencinin aradığı konu ile video konusu arasında tam eşleşme, kısmi eşleşme veya eşleşme yok durumunu tespit etmeli
11. THE Backend SHALL tam eşleşen videoları en üstte sıralamalı
12. THE Backend SHALL kısmi eşleşen videoları ikinci sırada sıralamalı
13. THE Backend SHALL eşleşmeyen videoları sonuç listesine dahil etmemeli
14. THE Backend SHALL konu eşleştirme algoritmasını makine öğrenmesi ile sürekli iyileştirmeli
15. THE Backend SHALL öğrenci geri bildirimini kullanarak konu eşleştirmesini optimize etmeli

### Requirement 15: Zorluk Seviyesi Uyumu ve Uyarlanabilir Zorluk

**User Story:** Öğrenci olarak, bana önerilen videoların seviyeme uygun olmasını istiyorum, böylece ne çok kolay ne de çok zor videolarla karşılaşmayayım.

#### Acceptance Criteria

1. THE Backend SHALL her videonun zorluk seviyesini belirtilen skala ile hesaplamalı
2. THE Backend SHALL video içeriğini analiz ederek zorluk seviyesini otomatik tespit etmeli
3. THE Backend SHALL öğrencinin mevcut seviyesini dikkate alarak uygun videoları filtrelemeli
4. THE Backend SHALL öğrenci seviyesine yakın aralıktaki videoları önermeli
5. THE Backend SHALL öğrencinin gelişimine göre zorluk seviyesini uyarlanabilir şekilde artırmalı
6. THE Backend SHALL öğrenci seviyesinden çok düşük videoları filtrelemeli
7. THE Backend SHALL öğrenci seviyesinden çok yüksek videoları filtrelemeli
8. THE Backend SHALL video meta verilerinde zorluk seviyesi belirtilmişse bunu dikkate almalı
9. THE Backend SHALL etkileşim metriklerini kullanarak zorluk seviyesini kalibre etmeli
10. THE Backend SHALL öğrencinin video izleme davranışını analiz ederek seviye uyumunu değerlendirmeli
11. THE Backend SHALL zorluk seviyesi uyumsuzluğunu kullanıcıya bildirmeli
12. THE Backend SHALL öğrenciye zorluk seviyesini manuel olarak ayarlama seçeneği sunmalı
13. THE Backend SHALL zorluk seviyesi ilerleme yolu oluşturmalı
14. THE Backend SHALL öğrencinin başarı oranına göre zorluk seviyesini otomatik ayarlamalı
15. THE Backend SHALL zorluk seviyesi metriklerini izlemeli ve raporlamalı
