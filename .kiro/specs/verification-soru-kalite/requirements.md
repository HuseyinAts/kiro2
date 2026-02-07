# Requirements Document - YKS Soru Kalite Doğrulama Sistemi

## Introduction

Bu spec, Claude Code Agent Sistemi'nin **Verification Feedback Loops** prensibine göre tasarlanmış YKS soru kalite doğrulama sistemini tanımlar. Boris Cherny'nin #1 önerisi olan verification loops, kod kalitesini %200-300 artırır. Bu sistem, üretilen her ÖSYM sorusunun otomatik olarak doğrulanmasını ve kalite garantisini sağlar.

## Glossary

- **Verification Loop**: Kod/içerik üretimi sonrası otomatik doğrulama döngüsü
- **ÖSYM Format Validator**: Soru yapısını ÖSYM standartlarına göre kontrol eden modül
- **Müfredat Checker**: MEB kazanımları ile soru uyumluluğunu kontrol eden sistem
- **Zemberek**: Türkçe morfolojik analiz kütüphanesi
- **SymPy**: Python sembolik matematik kütüphanesi
- **PostToolUse Hook**: Kod yazma işlemi sonrası otomatik çalışan hook
- **Quality Score**: 0-100 arası soru kalite skoru
- **Kalite Eşiği**: Minimum kabul edilebilir kalite skoru (70)

## Requirements

### Requirement 1: ÖSYM Format Validation

**User Story:** As a soru üretim sistemi, I want her üretilen sorunun ÖSYM formatına uygun olduğunu doğrulamak, so that öğrenciler gerçek sınav formatında sorularla çalışabilsin.

#### Acceptance Criteria

1. **REQ-1.1** WHEN bir soru üretildiğinde, THE ÖSYM Format Validator SHALL soru yapısını kontrol eder (soru metni, 4 seçenek, doğru cevap)
2. **REQ-1.2** WHEN soru formatı kontrol edildiğinde, THE Validator SHALL seçenek sayısının tam 4 olduğunu doğrular
3. **REQ-1.3** WHEN seçenekler kontrol edildiğinde, THE Validator SHALL her seçeneğin A, B, C, D olarak etiketlendiğini doğrular
4. **REQ-1.4** WHEN doğru cevap kontrol edildiğinde, THE Validator SHALL doğru cevabın A, B, C veya D olduğunu doğrular
5. **REQ-1.5** WHEN zorluk seviyesi kontrol edildiğinde, THE Validator SHALL zorluk seviyesinin kolay/orta/zor kategorilerinden biri olduğunu doğrular
6. **REQ-1.6** IF format hatası tespit edilirse, THEN THE Validator SHALL detaylı hata mesajı ve düzeltme önerisi sunar

---

### Requirement 2: Müfredat Uyumluluk Kontrolü

**User Story:** As a öğretmen, I want üretilen soruların MEB müfredatına uygun olduğunu bilmek, so that öğrencilerim doğru konularda çalışabilsin.

#### Acceptance Criteria

1. **REQ-2.1** WHEN bir soru üretildiğinde, THE Müfredat Checker SHALL sorunun hangi MEB kazanımına ait olduğunu tespit eder
2. **REQ-2.2** WHEN kazanım tespiti yapıldığında, THE Checker SHALL soru içeriğini kazanım açıklaması ile karşılaştırır
3. **REQ-2.3** WHEN uyumluluk skoru hesaplandığında, THE Checker SHALL 0-100 arası bir skor üretir
4. **REQ-2.4** WHEN uyumluluk skoru %80'in altında olduğunda, THE Checker SHALL uyarı verir
5. **REQ-2.5** WHEN konu tespiti yapıldığında, THE Checker SHALL sorunun hangi ders ve konuya ait olduğunu belirler
6. **REQ-2.6** IF soru birden fazla kazanımı kapsıyorsa, THEN THE Checker SHALL tüm ilgili kazanımları listeler

---

### Requirement 3: Türkçe Dil Kalitesi Kontrolü

**User Story:** As a öğrenci, I want soruların dilbilgisi açısından doğru ve anlaşılır olmasını, so that soruyu okurken zorlanmayayım.

#### Acceptance Criteria

1. **REQ-3.1** WHEN bir soru üretildiğinde, THE Zemberek Validator SHALL soru metnini morfolojik analize tabi tutar
2. **REQ-3.2** WHEN yazım kontrolü yapıldığında, THE Validator SHALL yazım hatalarını tespit eder ve düzeltme önerir
3. **REQ-3.3** WHEN cümle yapısı kontrol edildiğinde, THE Validator SHALL karmaşık cümleleri tespit eder
4. **REQ-3.4** WHEN kelime seçimi kontrol edildiğinde, THE Validator SHALL öğrenci seviyesine uygun olmayan kelimeleri işaretler
5. **REQ-3.5** WHEN Türkçe karakter kontrolü yapıldığında, THE Validator SHALL ç, ğ, ı, ö, ş, ü karakterlerinin doğru kullanıldığını doğrular
6. **REQ-3.6** IF dilbilgisi hatası tespit edilirse, THEN THE Validator SHALL hata türünü (yazım, sözdizimi, anlam) belirtir

---

### Requirement 4: Matematiksel Doğruluk Kontrolü

**User Story:** As a matematik öğretmeni, I want matematik sorularının matematiksel olarak doğru olduğunu bilmek, so that öğrencilerim yanlış bilgi öğrenmesin.

#### Acceptance Criteria

1. **REQ-4.1** WHEN bir matematik sorusu üretildiğinde, THE SymPy Validator SHALL matematiksel ifadeleri sembolik olarak analiz eder
2. **REQ-4.2** WHEN denklem kontrolü yapıldığında, THE Validator SHALL denklemin çözülebilir olduğunu doğrular
3. **REQ-4.3** WHEN doğru cevap kontrolü yapıldığında, THE Validator SHALL verilen doğru cevabın matematiksel olarak doğru olduğunu hesaplar
4. **REQ-4.4** WHEN çeldirici seçenekler kontrol edildiğinde, THE Validator SHALL çeldiricilerin matematiksel olarak yanlış olduğunu doğrular
5. **REQ-4.5** WHEN birim kontrolü yapıldığında, THE Validator SHALL birimlerin tutarlı kullanıldığını kontrol eder
6. **REQ-4.6** IF matematiksel hata tespit edilirse, THEN THE Validator SHALL soruyu reddeder ve hata detayını raporlar

---

### Requirement 5: PostToolUse Hook Entegrasyonu

**User Story:** As a sistem yöneticisi, I want soru üretimi sonrası otomatik doğrulama yapılmasını, so that manuel kontrol ihtiyacı ortadan kalksın.

#### Acceptance Criteria

1. **REQ-5.1** WHEN bir soru üretim işlemi tamamlandığında, THE PostToolUse Hook SHALL otomatik olarak tetiklenir
2. **REQ-5.2** WHEN hook tetiklendiğinde, THE Hook SHALL tüm validator'ları sırayla çalıştırır
3. **REQ-5.3** WHEN validation tamamlandığında, THE Hook SHALL toplam kalite skorunu hesaplar
4. **REQ-5.4** WHEN kalite skoru hesaplandığında, THE Hook SHALL skoru 0-100 arası normalize eder
5. **REQ-5.5** WHEN validation sonuçları hazır olduğunda, THE Hook SHALL sonuçları JSON formatında kaydeder
6. **REQ-5.6** IF herhangi bir validator başarısız olursa, THEN THE Hook SHALL süreci durdurur ve hata raporlar

---

### Requirement 6: Kalite Skoru Hesaplama

**User Story:** As a içerik yöneticisi, I want her sorunun kalite skorunu görmek, so that düşük kaliteli soruları filtreleyebileyim.

#### Acceptance Criteria

1. **REQ-6.1** WHEN kalite skoru hesaplandığında, THE Scoring System SHALL ÖSYM format uyumluluğuna %30 ağırlık verir
2. **REQ-6.2** WHEN kalite skoru hesaplandığında, THE Scoring System SHALL müfredat uyumluluğuna %30 ağırlık verir
3. **REQ-6.3** WHEN kalite skoru hesaplandığında, THE Scoring System SHALL Türkçe dil kalitesine %20 ağırlık verir
4. **REQ-6.4** WHEN kalite skoru hesaplandığında, THE Scoring System SHALL matematiksel doğruluğa %20 ağırlık verir
5. **REQ-6.5** WHEN toplam skor hesaplandığında, THE Scoring System SHALL ağırlıklı ortalama kullanır
6. **REQ-6.6** WHEN skor 70'in altında olduğunda, THE Scoring System SHALL soruyu "düşük kalite" olarak işaretler

---

### Requirement 7: Hata Raporlama ve Düzeltme Önerileri

**User Story:** As a soru yazarı, I want hataların ne olduğunu ve nasıl düzelteceğimi bilmek, so that soruyu hızlıca düzeltip tekrar gönderebiliyim.

#### Acceptance Criteria

1. **REQ-7.1** WHEN bir hata tespit edildiğinde, THE Error Reporter SHALL hata türünü kategorize eder (format, müfredat, dil, matematik)
2. **REQ-7.2** WHEN hata raporu oluşturulduğunda, THE Reporter SHALL hatanın tam konumunu belirtir (satır, kelime)
3. **REQ-7.3** WHEN düzeltme önerisi sunulduğunda, THE Reporter SHALL somut düzeltme örneği verir
4. **REQ-7.4** WHEN birden fazla hata olduğunda, THE Reporter SHALL hataları öncelik sırasına göre listeler
5. **REQ-7.5** WHEN rapor oluşturulduğunda, THE Reporter SHALL Türkçe açıklama kullanır
6. **REQ-7.6** WHEN rapor kaydedildiğinde, THE Reporter SHALL raporu veritabanına ve log dosyasına yazar

---

### Requirement 8: Performans ve Ölçeklenebilirlik

**User Story:** As a sistem yöneticisi, I want doğrulama sürecinin hızlı olmasını, so that soru üretim akışı yavaşlamasın.

#### Acceptance Criteria

1. **REQ-8.1** WHEN bir soru doğrulandığında, THE Validation System SHALL toplam süreyi 5 saniye altında tutar
2. **REQ-8.2** WHEN paralel doğrulama yapıldığında, THE System SHALL 10 soruyu aynı anda işleyebilir
3. **REQ-8.3** WHEN yük arttığında, THE System SHALL otomatik olarak ölçeklenir
4. **REQ-8.4** WHEN cache kullanıldığında, THE System SHALL sık kullanılan validation sonuçlarını önbelleğe alır
5. **REQ-8.5** WHEN performans ölçüldüğünde, THE System SHALL ortalama yanıt süresini loglar
6. **REQ-8.6** IF sistem yavaşlarsa, THEN THE System SHALL uyarı verir ve yöneticiye bildirim gönderir

---

## Bağımlılıklar

- **Zemberek-NLP**: Türkçe morfolojik analiz için
- **SymPy**: Matematiksel doğrulama için
- **MEB Müfredat API**: Kazanım kontrolü için
- **Redis**: Cache için
- **PostgreSQL**: Validation sonuçları için
- **FastAPI**: API endpoints için

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 2 hafta
**Beklenen Kalite Artışı:** %200-300

## Verification Loop Akışı

```
1. Soru Üretildi
   ↓
2. PostToolUse Hook Tetiklendi
   ↓
3. ÖSYM Format Validation (30%)
   ↓
4. Müfredat Uyumluluk Kontrolü (30%)
   ↓
5. Türkçe Dil Kalitesi Kontrolü (20%)
   ↓
6. Matematiksel Doğruluk Kontrolü (20%)
   ↓
7. Kalite Skoru Hesaplama (0-100)
   ↓
8. Skor >= 70? 
   ├─ EVET → Soru Onaylandı ✓
   └─ HAYIR → Hata Raporu + Düzeltme Önerileri ✗
```

## Success Metrics

1. **Kalite Skoru Ortalaması:** >= 85
2. **Otomatik Onay Oranı:** >= %80
3. **Hata Tespit Oranı:** >= %95
4. **Ortalama Doğrulama Süresi:** < 5 saniye
5. **Sistem Uptime:** >= %99.9
