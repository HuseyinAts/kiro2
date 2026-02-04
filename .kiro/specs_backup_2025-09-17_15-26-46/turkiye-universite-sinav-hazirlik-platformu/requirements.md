# Gereksinimler Dokümantasyonu

## Giriş

Türkiye Üniversite Sınavları Hazırlık Platformu, YKS (TYT/AYT/YDT) sınavlarına hazırlanan öğrenciler için özel olarak tasarlanmış kapsamlı bir AI destekli eğitim sistemidir. Platform, ÖSYM ve MEB müfredatına %100 uyumlu içerikler sunarak, öğrencilerin bireysel öğrenme hızlarına göre kişiselleştirilmiş eğitim yolları oluşturur.

## Gereksinimler

### Gereksinim 1: ÖSYM Uyumlu Sınav Sistemi

**Kullanıcı Hikayesi:** YKS sınavlarına hazırlanan bir öğrenci olarak, gerçek sınav formatında deneme sınavları çözmek ve detaylı performans analizi almak istiyorum.

#### Kabul Kriterleri

1. WHEN öğrenci TYT denemesi başlattığında THEN sistem 120 soru ve 165 dakika süre ile ÖSYM formatında sınav sunmalı
2. WHEN öğrenci AYT denemesi başlattığında THEN sistem 160 soru ve 210 dakika süre ile ÖSYM formatında sınav sunmalı
3. WHEN öğrenci YDT denemesi başlattığında THEN sistem ilgili dil için ÖSYM formatında sınav sunmalı
4. WHEN sınav tamamlandığında THEN sistem detaylı performans analizi ve konu bazlı başarı raporu sunmalı
5. WHEN sınav sonuçları analiz edildiğinde THEN sistem zayıf konuları tespit edip özel çalışma önerileri sunmalı

### Gereksinim 2: Türkçe NLP ve Sohbet Desteği

**Kullanıcı Hikayesi:** Öğrenci olarak, Türkçe doğal dil işleme ile sorularımı sorabilmek ve anında yanıt alabilmek istiyorum.

#### Kabul Kriterleri

1. WHEN öğrenci Türkçe soru sorduğunda THEN sistem morfolojik analiz yaparak doğru anlam çıkarmalı
2. WHEN öğrenci konu hakkında açıklama istediğinde THEN sistem Türkçe eğitim terminolojisi kullanarak yanıt vermeli
3. WHEN öğrenci soru çözümü yardımı istediğinde THEN sistem adım adım Türkçe açıklama sunmalı
4. WHEN öğrenci duygu durumu olumsuz olduğunda THEN sistem motivasyonel destek sağlamalı
5. WHEN öğrenci sohbet geçmişi olduğunda THEN sistem önceki konuşmaları hatırlayarak bağlamsal yanıt vermeli

### Gereksinim 3: MEB ve ÖSYM Müfredat Uyumluluğu

**Kullanici Hikayesi:** Öğrenci olarak, MEB ve ÖSYM müfredatına uyumlu içeriklerle çalışmak istiyorum.

#### Kabul Kriterleri

1. WHEN içerik sunulduğunda THEN sistem MEB müfredat standartlarına uygun konuları içermeli
2. WHEN soru bankası erişildiğinde THEN her konu için en az 1000 ÖSYM tarzı soru bulunmalı
3. WHEN öğrenme kazanımları gösterildiğinde THEN MEB'in belirlediği kazanımlarla eşleşmeli
4. WHEN müfredat güncellendiğinde THEN sistem manuel olarak yeni standartlara uyum sağlamalı
5. WHEN konu sıralaması yapıldığında THEN ÖSYM'nin belirlediği öncelik sırasına uymalı

### Gereksinim 4: Adaptif Öğrenme ve Zorluk Ayarlama

**Kullanıcı Hikayesi:** Öğrenci olarak, performansıma göre zorluk seviyesinin dinamik olarak ayarlandığı adaptif bir öğrenme sistemi istiyorum.

#### Kabul Kriterleri

1. WHEN öğrenci başarılı performans gösterdiğinde THEN sistem zorluk seviyesini artırmalı
2. WHEN öğrenci zorlandığında THEN sistem daha basit sorular ve alternatif açıklamalar sunmalı
3. WHEN öğrenci öğrenme hızı değiştiğinde THEN sistem içerik sunma hızını ayarlamalı
4. WHEN öğrenci belirli konularda zayıf olduğunda THEN sistem o konulara odaklanan özel program oluşturmalı
5. WHEN öğrenci başarı tahmini yapıldığında THEN makine öğrenmesi modelleri kullanılmalı

### Gereksinim 5: Çoklu Platform İçerik Entegrasyonu

**Kullanıcı Hikayesi:** Öğrenci olarak, YouTube Education, Khan Academy Türkçe ve EBA TV gibi platformlardan kaliteli eğitim içeriklerine erişmek istiyorum.

#### Kabul Kriterleri

1. WHEN video içerik arandığında THEN sistem YouTube Education API ile eğitim kanallarını filtrelemeli
2. WHEN yapılandırılmış kurs arandığında THEN sistem Khan Academy Türkçe içeriklerini entegre etmeli
3. WHEN EBA içerikleri arandığında THEN sistem TRT EBA TV video linklerini dahil etmeli
4. WHEN içerikler sıralandığında THEN kalite, uygunluk ve öğrenci profiline göre derecelendirme yapmalı
5. WHEN içerik meta verileri gösterildiğinde THEN süre, zorluk seviyesi ve erişilebilirlik özellikleri dahil edilmeli

### Gereksinim 6: Öğretmen ve Veli Takip Sistemi

**Kullanıcı Hikayesi:** Öğretmen olarak, öğrencilerimin bireysel ilerlemelerini takip edebilmek ve sınıf geneli performans raporları alabilmek istiyorum.

#### Kabul Kriterleri

1. WHEN öğretmen öğrenci listesini görüntülediğinde THEN her öğrencinin güncel ilerleme durumu gösterilmeli
2. WHEN öğretmen sınıf raporu istediğinde THEN konu bazlı başarı dağılımı sunulmalı
3. WHEN öğretmen ödev oluşturduğunda THEN ÖSYM müfredatına uygun sorular otomatik seçilmeli
4. WHEN veli haftalık rapor istediğinde THEN çocuk ilerleme raporu sunulmalı
5. WHEN performans karşılaştırması yapıldığında THEN sınıf, okul ve ulusal ortalamalarla kıyaslama sunulmalı

### Gereksinim 7: Yüksek Performans ve Ölçeklenebilirlik

**Kullanıcı Hikayesi:** Platform kullanıcısı olarak, 100.000+ eşzamanlı kullanıcı olsa bile 200ms altında yanıt alabilmek istiyorum.

#### Kabul Kriterleri

1. WHEN sistem yükü arttığında THEN p95 yanıt süresi 200ms altında kalmalı
2. WHEN 100.000 eşzamanlı kullanıcı olduğunda THEN sistem stabil çalışmaya devam etmeli
3. WHEN sistem uptime ölçüldüğünde THEN %99.9 kullanılabilirlik sağlanmalı
4. WHEN Türkçe karakter işlendiğinde THEN UTF-8 encoding ile doğru görüntülenmeli
5. WHEN mobil cihazlardan erişildiğinde THEN responsive design ile uyumlu çalışmalı

### Gereksinim 8: Offline Çalışma ve PWA Desteği

**Kullanıcı Hikayesi:** Öğrenci olarak, internet bağlantısı olmadığında bile indirdiğim içeriklerle çalışabilmek istiyorum.

#### Kabul Kriterleri

1. WHEN öğrenci offline modda çalıştığında THEN önceden indirilen içerikler erişilebilir olmalı
2. WHEN PWA yüklendiğinde THEN uygulama native app gibi çalışmalı
3. WHEN offline soru çözüldüğünde THEN yanıtlar yerel olarak saklanıp senkronize edilmeli
4. WHEN bağlantı geri geldiğinde THEN offline veriler otomatik senkronize edilmeli
5. WHEN offline içerik güncellendiğinde THEN kullanıcı bilgilendirilmeli

### Gereksinim 9: Erişilebilirlik ve Kapsayıcı Tasarım

**Kullanıcı Hikayesi:** Görme engelli öğrenci olarak, ekran okuyucu teknolojileri ile platformu tam olarak kullanabilmek istiyorum.

#### Kabul Kriterleri

1. WHEN görsel içerik sunulduğunda THEN alternatif metin açıklamaları bulunmalı
2. WHEN matematiksel formüller gösterildiğinde THEN ekran okuyucu uyumlu format sunulmalı
3. WHEN video içerik izlendiğinde THEN altyazı ve transkript mevcut olmalı
4. WHEN klavye ile navigasyon yapıldığında THEN tüm özellikler erişilebilir olmalı
5. WHEN WCAG 2.1 Level AA standartları kontrol edildiğinde THEN tam uyumluluk sağlanmalı