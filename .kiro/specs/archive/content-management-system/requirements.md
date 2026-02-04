# İçerik Yönetim Sistemi - Gereksinimler Belgesi

## Giriş

Bu belge, Teknofest 2025 Eğitim Eylemci Platformu için geliştirilecek İçerik Yönetim Sistemi'nin gereksinimlerini tanımlar. Sistem, öğretmenlerin ve yöneticilerin eğitim içeriklerini (makale, video, quiz vb.) oluşturmasına, yönetmesine ve öğrencilere sunmasına olanak sağlar. Ayrıca öğrenciler için kişiselleştirilmiş içerik önerileri ve arama işlevselliği sunar.

## Gereksinimler

### Gereksinim 1: Makale İçerik Yönetimi

**Kullanıcı Hikayesi:** Öğretmen olarak, öğrencilerime eğitim makaleleri oluşturmak, düzenlemek ve paylaşmak istiyorum, böylece onlara kaliteli yazılı içerik sunabilirim.

#### Kabul Kriterleri

1. WHEN öğretmen yeni makale oluşturmak istediğinde THEN sistem başlık, içerik, kategori ve yazar bilgilerini almalı
2. WHEN makale içeriği girildiğinde THEN sistem otomatik olarak özet, okunma süresi ve etiketler oluşturmalı
3. WHEN makale kaydedildiğinde THEN sistem benzersiz ID atamalı ve yayınlanma tarihini kaydetmeli
4. WHEN öğrenci makaleyi görüntülediğinde THEN sistem görüntüleme sayısını artırmalı
5. IF makale sahibi veya admin ise THEN kullanıcı makaleyi güncelleyebilmeli
6. WHEN makale silindiğinde THEN sistem soft delete yapmalı (kalıcı silme değil)
7. WHEN kullanıcı makaleyi beğendiğinde THEN sistem beğeni sayısını güncellemeli

### Gereksinim 2: Video İçerik Yönetimi

**Kullanıcı Hikayesi:** Öğretmen olarak, öğrencilerime video içerikleri eklemek ve yönetmek istiyorum, böylece görsel öğrenmeyi destekleyebilirim.

#### Kabul Kriterleri

1. WHEN öğretmen video eklemek istediğinde THEN sistem video URL'ini doğrulamalı
2. WHEN geçerli video URL'i girildiğinde THEN sistem otomatik olarak video süresini almalı
3. WHEN video kaydedildiğinde THEN sistem arka planda thumbnail oluşturmalı
4. WHEN öğrenci videoyu izlediğinde THEN sistem izlenme sayısını artırmalı
5. WHEN video listesi istendiğinde THEN sistem süre filtresi (min/max) sunmalı
6. IF video sahibi veya yetkili kullanıcı ise THEN video bilgileri güncellenebilmeli

### Gereksinim 3: İçerik Arama ve Filtreleme

**Kullanıcı Hikayesi:** Öğrenci olarak, ihtiyacım olan içerikleri hızlıca bulabilmek istiyorum, böylece zamanımı verimli kullanabilirim.

#### Kabul Kriterleri

1. WHEN kullanıcı arama terimi girdiğinde THEN sistem tüm içerik tiplerinde arama yapmalı
2. WHEN arama sonuçları gösterildiğinde THEN sistem başlık ve içerik metninde eşleşmeleri vurgulamalı
3. WHEN filtreleme yapıldığında THEN sistem kategori, tarih aralığı ve içerik tipine göre filtrelemeli
4. WHEN sayfalama kullanıldığında THEN sistem skip ve limit parametrelerini desteklemeli
5. IF arama sonucu yoksa THEN sistem anlamlı mesaj göstermeli

### Gereksinim 4: Kişiselleştirilmiş İçerik Önerileri

**Kullanıcı Hikayesi:** Öğrenci olarak, öğrenme stilime ve seviyeme uygun içerik önerileri almak istiyorum, böylece daha etkili öğrenebilirim.

#### Kabul Kriterleri

1. WHEN öğrenci öneriler sayfasını ziyaret ettiğinde THEN sistem kişiselleştirilmiş öneriler sunmalı
2. WHEN öğrenci profili analiz edildiğinde THEN sistem öğrenme geçmişini ve tercihlerini dikkate almalı
3. WHEN kategori belirtildiğinde THEN sistem o kategoriye özel öneriler getirmeli
4. WHEN yeni kullanıcı için öneri istendiğinde THEN sistem genel popüler içerikleri önermeliI
5. IF öğrenci etkileşim geçmişi varsa THEN sistem benzer içerikleri önceliklemeli

### Gereksinim 5: Trend ve İstatistik Analizi

**Kullanıcı Hikayesi:** Yönetici olarak, platform üzerindeki içerik performansını ve kullanım trendlerini görmek istiyorum, böylece veri odaklı kararlar alabilirim.

#### Kabul Kriterleri

1. WHEN yönetici istatistikleri görüntülediğinde THEN sistem toplam içerik sayılarını göstermeli
2. WHEN trend analizi istendiğinde THEN sistem günlük, haftalık, aylık trendleri sunmalı
3. WHEN içerik performansı analiz edildiğinde THEN sistem görüntüleme, beğeni ve etkileşim verilerini göstermeli
4. WHEN kategori bazlı analiz yapıldığında THEN sistem kategori dağılımını ve performansını göstermeli
5. IF yetkisiz kullanıcı istatistiklere erişmeye çalışırsa THEN sistem erişimi engellemeli

### Gereksinim 6: Toplu İçerik Yükleme

**Kullanıcı Hikayesi:** Yönetici olarak, çok sayıda içeriği tek seferde yükleyebilmek istiyorum, böylece manuel işlem yükünü azaltabilirim.

#### Kabul Kriterleri

1. WHEN yönetici CSV veya JSON dosyası yüklediğinde THEN sistem dosya formatını doğrulamalı
2. WHEN toplu yükleme başlatıldığında THEN sistem arka planda işleme almalı
3. WHEN yükleme devam ederken THEN sistem ilerleme durumunu takip edilebilir hale getirmeli
4. WHEN hatalı veri tespit edildiğinde THEN sistem detaylı hata raporu sunmalı
5. IF yükleme tamamlandığında THEN sistem başarı/başarısızlık özetini göstermeli

### Gereksinim 7: Cache ve Performans Optimizasyonu

**Kullanıcı Hikayesi:** Platform kullanıcısı olarak, içeriklerin hızlı yüklenmesini istiyorum, böylece kesintisiz bir deneyim yaşayabilirim.

#### Kabul Kriterleri

1. WHEN sık erişilen içerikler istendiğinde THEN sistem cache'den sunmalı
2. WHEN içerik güncellendiğinde THEN sistem ilgili cache'i temizlemeli
3. WHEN yeni içerik oluşturulduğında THEN sistem arka planda indexleme yapmalı
4. WHEN büyük listeler istendiğinde THEN sistem sayfalama kullanmalı
5. IF cache süresi dolmuşsa THEN sistem otomatik olarak yenilemeli

### Gereksinim 8: İçerik Güvenliği ve Yetkilendirme

**Kullanıcı Hikayesi:** Platform yöneticisi olarak, içeriklerin güvenli bir şekilde yönetilmesini istiyorum, böylece yetkisiz erişimleri engelleyebilirim.

#### Kabul Kriterleri

1. WHEN kullanıcı içerik oluşturmaya çalıştığında THEN sistem yetki kontrolü yapmalı
2. WHEN içerik düzenleme işlemi yapıldığında THEN sistem sahiplik veya admin yetkisi kontrolü yapmalı
3. WHEN silme işlemi gerçekleştirildiğinde THEN sistem sadece yetkili kullanıcılara izin vermeli
4. WHEN hassas işlemler yapıldığında THEN sistem audit log tutmalı
5. IF yetkisiz erişim tespit edilirse THEN sistem güvenlik uyarısı vermeli