# Requirements Document

## Introduction

Türkiye Üniversite Sınavları Hazırlık Platformu, YKS (TYT/AYT/YDT) sınavlarına hazırlanan öğrenciler için AI destekli kapsamlı bir eğitim sistemidir. Platform, ÖSYM ve MEB müfredatına tam uyumlu içerikler sunarak öğrencilerin bireysel öğrenme hızlarına göre kişiselleştirilmiş eğitim yolları oluşturur.

### Hedef Kullanıcılar

- **Öğrenciler**: YKS sınavlarına hazırlanan lise öğrencileri (9-12. sınıf)
- **Öğretmenler**: Öğrenci ilerlemesini takip eden ve ödev atayan eğitimciler
- **Veliler**: Çocuklarının eğitim sürecini izleyen aileler
- **Yöneticiler**: Okul ve kurum düzeyinde raporlama yapan eğitim yöneticileri

### Temel Özellikler

**Sınav ve Değerlendirme:**
- ÖSYM formatında deneme sınavları (TYT/AYT/YDT)
- Gerçek zamanlı performans analizi ve detaylı raporlama
- Konu bazlı zayıf alan tespiti ve özel çalışma önerileri

**Yapay Zeka ve Kişiselleştirme:**
- Türkçe NLP destekli AI sohbet asistanı
- Adaptif öğrenme ve kişiselleştirilmiş içerik sunumu
- 7 devrimsel AI özelliği (VARK+Felder hibrit, Türk ZPD, Morfoloji IRT, Türk FSRS, 3 seviyeli basitleştirme, Bionic Reading, Multi-Agent Blackboard)

**İçerik ve Entegrasyon:**
- MEB ve ÖSYM müfredatına tam uyumluluk
- Çoklu platform entegrasyonu (YouTube Education, Khan Academy Türkçe, EBA TV)
- 2300+ ÖSYM formatında kalibrasyon edilmiş soru bankası

**Takip ve Raporlama:**
- Öğretmen dashboard'u ile sınıf yönetimi
- Veli takip sistemi ile haftalık ilerleme raporları
- Ulusal ortalama ile karşılaştırmalı analiz

**Teknik Özellikler:**
- Yüksek performans (100K+ eşzamanlı kullanıcı, <200ms yanıt süresi)
- PWA desteği ve offline çalışma modu
- WCAG 2.1 Level AA erişilebilirlik standardı
- Çoklu cihaz desteği (web, mobil, tablet)

## Requirements

### Gereksinim 1: ÖSYM Uyumlu Sınav Sistemi

**Kullanıcı Hikayesi:** As a YKS sınavlarına hazırlanan öğrenci, I want gerçek sınav formatında deneme sınavları çözmek ve detaylı performans analizi almak, so that sınav gününde hazırlıklı olabileyim.

#### Kabul Kriterleri

1. WHEN öğrenci TYT denemesi başlattığında THEN sistem 120 soru ve 165 dakika süre ile ÖSYM formatında sınav sunmalı
2. WHEN öğrenci AYT denemesi başlattığında THEN sistem 160 soru ve 210 dakika süre ile ÖSYM formatında sınav sunmalı
3. WHEN öğrenci YDT denemesi başlattığında THEN sistem ilgili dil için ÖSYM formatında sınav sunmalı
4. WHEN sınav tamamlandığında THEN sistem detaylı performans analizi ve konu bazlı başarı raporu sunmalı
5. WHEN sınav sonuçları analiz edildiğinde THEN sistem zayıf konuları tespit edip özel çalışma önerileri sunmalı
6. IF öğrenci sınav sırasında teknik sorun yaşarsa THEN sistem otomatik kaydetme ile veri kaybını önlemeli

### Gereksinim 2: Türkçe NLP ve Sohbet Desteği

**Kullanıcı Hikayesi:** As an öğrenci, I want Türkçe doğal dil işleme ile sorularımı sorabilmek ve anında yanıt alabilmek, so that öğrenme sürecimde takıldığım noktalarda hızlıca yardım alabileyim.

#### Kabul Kriterleri

1. WHEN öğrenci Türkçe soru sorduğunda THEN sistem morfolojik analiz yaparak doğru anlam çıkarmalı
2. WHEN öğrenci konu hakkında açıklama istediğinde THEN sistem Türkçe eğitim terminolojisi kullanarak yanıt vermeli
3. WHEN öğrenci soru çözümü yardımı istediğinde THEN sistem adım adım Türkçe açıklama sunmalı
4. WHEN öğrenci duygu durumu olumsuz olduğunda THEN sistem motivasyonel destek sağlamalı
5. WHEN öğrenci sohbet geçmişi olduğunda THEN sistem önceki konuşmaları hatırlayarak bağlamsal yanıt vermeli
6. IF öğrenci yanlış Türkçe kullanırsa THEN sistem nazikçe düzeltme önerisi sunmalı

### Gereksinim 3: MEB ve ÖSYM Müfredat Uyumluluğu

**Kullanıcı Hikayesi:** As an öğrenci, I want MEB ve ÖSYM müfredatına uyumlu içeriklerle çalışmak, so that sınavda karşılaşacağım konulara tam olarak hazırlanabileyim.

#### Kabul Kriterleri

1. WHEN içerik sunulduğunda THEN sistem MEB müfredat standartlarına uygun konuları içermeli
2. WHEN soru bankası erişildiğinde THEN her konu için en az 1000 ÖSYM tarzı soru bulunmalı
3. WHEN öğrenme kazanımları gösterildiğinde THEN MEB'in belirlediği kazanımlarla eşleşmeli
4. WHEN müfredat güncellendiğinde THEN sistem manuel olarak yeni standartlara uyum sağlamalı
5. WHEN konu sıralaması yapıldığında THEN ÖSYM'nin belirlediği öncelik sırasına uymalı

### Gereksinim 4: Adaptif Öğrenme ve Zorluk Ayarlama

**Kullanıcı Hikayesi:** As an öğrenci, I want performansıma göre zorluk seviyesinin dinamik olarak ayarlandığı adaptif bir öğrenme sistemi, so that hem zorlanmadan hem de sıkılmadan etkili bir şekilde öğrenebileyim.

#### Kabul Kriterleri

1. WHEN öğrenci başarılı performans gösterdiğinde THEN sistem zorluk seviyesini artırmalı
2. WHEN öğrenci zorlandığında THEN sistem daha basit sorular ve alternatif açıklamalar sunmalı
3. WHEN öğrenci öğrenme hızı değiştiğinde THEN sistem içerik sunma hızını ayarlamalı
4. WHEN öğrenci belirli konularda zayıf olduğunda THEN sistem o konulara odaklanan özel program oluşturmalı
5. WHEN öğrenci başarı tahmini yapıldığında THEN makine öğrenmesi modelleri kullanılmalı

### Gereksinim 5: Çoklu Platform İçerik Entegrasyonu

**Kullanıcı Hikayesi:** As an öğrenci, I want YouTube Education, Khan Academy Türkçe ve EBA TV gibi platformlardan kaliteli eğitim içeriklerine erişmek, so that farklı kaynaklardan zengin içeriklerle öğrenme deneyimimi geliştirebileyim.

#### Kabul Kriterleri

1. WHEN video içerik arandığında THEN sistem YouTube Education API ile eğitim kanallarını filtrelemeli
2. WHEN yapılandırılmış kurs arandığında THEN sistem Khan Academy Türkçe içeriklerini entegre etmeli
3. WHEN EBA içerikleri arandığında THEN sistem TRT EBA TV video linklerini dahil etmeli
4. WHEN içerikler sıralandığında THEN kalite, uygunluk ve öğrenci profiline göre derecelendirme yapmalı
5. WHEN içerik meta verileri gösterildiğinde THEN süre, zorluk seviyesi ve erişilebilirlik özellikleri dahil edilmeli

### Gereksinim 6: Öğretmen ve Veli Takip Sistemi

**Kullanıcı Hikayesi:** As an öğretmen, I want öğrencilerimin bireysel ilerlemelerini takip edebilmek ve sınıf geneli performans raporları alabilmek, so that eğitim sürecini daha etkili yönetebileyim ve velilerle işbirliği yapabileyim.

#### Kabul Kriterleri

1. WHEN öğretmen öğrenci listesini görüntülediğinde THEN her öğrencinin güncel ilerleme durumu gösterilmeli
2. WHEN öğretmen sınıf raporu istediğinde THEN konu bazlı başarı dağılımı sunulmalı
3. WHEN öğretmen ödev oluşturduğunda THEN ÖSYM müfredatına uygun sorular otomatik seçilmeli
4. WHEN veli haftalık rapor istediğinde THEN çocuk ilerleme raporu sunulmalı
5. WHEN performans karşılaştırması yapıldığında THEN sınıf, okul ve ulusal ortalamalarla kıyaslama sunulmalı

### Gereksinim 7: Yüksek Performans ve Ölçeklenebilirlik

**Kullanıcı Hikayesi:** As a platform kullanıcısı, I want 100.000+ eşzamanlı kullanıcı olsa bile 200ms altında yanıt alabilmek, so that kesintisiz ve akıcı bir öğrenme deneyimi yaşayabileyim.

#### Kabul Kriterleri

1. WHEN sistem yükü arttığında THEN p95 yanıt süresi 200ms altında kalmalı
2. WHEN 100.000 eşzamanlı kullanıcı olduğunda THEN sistem stabil çalışmaya devam etmeli
3. WHEN sistem uptime ölçüldüğünde THEN %99.9 kullanılabilirlik sağlanmalı
4. WHEN Türkçe karakter işlendiğinde THEN UTF-8 encoding ile doğru görüntülenmeli
5. WHEN mobil cihazlardan erişildiğinde THEN responsive design ile uyumlu çalışmalı
6. IF sistem kapasitesi %80'e ulaşırsa THEN otomatik ölçeklendirme devreye girmeli

### Gereksinim 8: Offline Çalışma ve PWA Desteği

**Kullanıcı Hikayesi:** As an öğrenci, I want internet bağlantısı olmadığında bile indirdiğim içeriklerle çalışabilmek, so that her koşulda öğrenme sürecimi devam ettirebilleyim.

#### Kabul Kriterleri

1. WHEN öğrenci offline modda çalıştığında THEN önceden indirilen içerikler erişilebilir olmalı
2. WHEN PWA yüklendiğinde THEN uygulama native app gibi çalışmalı
3. WHEN offline soru çözüldüğünde THEN yanıtlar yerel olarak saklanıp senkronize edilmeli
4. WHEN bağlantı geri geldiğinde THEN offline veriler otomatik senkronize edilmeli
5. WHEN offline içerik güncellendiğinde THEN kullanıcı bilgilendirilmeli

### Gereksinim 9: Erişilebilirlik ve Kapsayıcı Tasarım

**Kullanıcı Hikayesi:** As a görme engelli öğrenci, I want ekran okuyucu teknolojileri ile platformu tam olarak kullanabilmek, so that eğitim fırsatlarından eşit şekilde yararlanabileyim.

#### Kabul Kriterleri

1. WHEN görsel içerik sunulduğunda THEN alternatif metin açıklamaları bulunmalı
2. WHEN matematiksel formüller gösterildiğinde THEN ekran okuyucu uyumlu format sunulmalı
3. WHEN video içerik izlendiğinde THEN altyazı ve transkript mevcut olmalı
4. WHEN klavye ile navigasyon yapıldığında THEN tüm özellikler erişilebilir olmalı
5. WHEN WCAG 2.1 Level AA standartları kontrol edildiğinde THEN tam uyumluluk sağlanmalı

### Gereksinim 10: Devrimsel AI Özellikler Sistemi

**Kullanıcı Hikayesi:** As an öğrenci, I want dünya çapında benzersiz AI teknolojileri ile kişiselleştirilmiş ve etkili bir öğrenme deneyimi yaşamak, so that maksimum verimlilikle öğrenebileyim ve sınav başarımı artırabileyim.

#### Kabul Kriterleri

1. WHEN öğrenme stili tespiti yapıldığında THEN VARK + Felder-Silverman hibrit sistemi 64 farklı profil sunmalı
2. WHEN zorluk seviyesi ayarlandığında THEN Türk ZPD + MEB Maarif modeli kültürel faktörleri dikkate almalı
3. WHEN soru analizi yapıldığında THEN Türkçe Morfoloji IRT sistemi ÖSYM/ETS standartlarını aşmalı
4. WHEN tekrar zamanlaması hesaplandığında THEN Türk FSRS sistemi 17 parametre ile optimize edilmeli
5. WHEN metin basitleştirme istendiğinde THEN 3 seviyeli sistem (lexical, syntactic, semantic) çalışmalı
6. WHEN disleksi desteği aktifleştirildiğinde THEN Türkçe Bionic Reading kök-ek ayrımı yapmalı
7. WHEN AI agentlar çalıştığında THEN Multi-Agent Blackboard gerçek zamanlı koordinasyon sağlamalı

### Gereksinim 11: Gerçek Zamanlı İletişim ve Koordinasyon

**Kullanıcı Hikayesi:** As an öğrenci, I want AI agentların birbirleriyle koordineli çalışarak bana en iyi öğrenme deneyimini sunmasını, so that tutarlı ve optimize edilmiş bir eğitim süreci yaşayabileyim.

#### Kabul Kriterleri

1. WHEN bir agent keşif yaptığında THEN diğer agentlar anında bilgilendirilmeli
2. WHEN öğrenme stili tespit edildiğinde THEN tüm agentlar bu bilgiyi kullanarak adapte olmalı
3. WHEN performans verisi güncellendiğinde THEN agentlar koordineli şekilde tepki vermeli
4. WHEN WebSocket bağlantısı kurulduğunda THEN gerçek zamanlı agent iletişimi başlamalı
5. WHEN blackboard'a veri yazıldığında THEN abone agentlar 100ms içinde bildirim almalı
6. IF agent arası iletişim kesilirse THEN sistem otomatik yeniden bağlantı kurmalı

### Gereksinim 12: Türkçe Dil İşleme ve Kültürel Adaptasyon

**Kullanıcı Hikayesi:** As a Türk öğrenci, I want Türkçe'nin zengin yapısını anlayan ve Türk kültürüne uygun bir sistem kullanmak, so that kendi dilim ve kültürümle uyumlu bir öğrenme deneyimi yaşayabileyim.

#### Kabul Kriterleri

1. WHEN Türkçe metin analiz edildiğinde THEN Zemberek NLP morfolojik analiz yapmalı
2. WHEN karmaşık kelimeler tespit edildiğinde THEN ek sayısı ve türetim derinliği hesaplanmalı
3. WHEN kültürel dönemler (Ramazan, sınav dönemi) olduğunda THEN sistem davranışı adapte olmalı
4. WHEN grup çalışması tercihi yüksek olduğunda THEN ZPD aralığı genişletilmeli
5. WHEN Osmanlıca/akademik kelimeler bulunduğunda THEN modern Türkçe karşılıkları önerilmeli
6. IF öğrenci bölgesel lehçe kullanırsa THEN sistem standart Türkçe'ye çeviri desteği sunmalı