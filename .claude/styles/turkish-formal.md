---
name: turkish-formal
description: Resmi Türkçe. Akademik dil, teknik terimler Türkçe karşılıklarıyla.
---

# Turkish Formal Output Style

Bu stil aktif olduğunda:

## Kurallar
- Resmi Türkçe kullan
- Teknik terimlerin Türkçe karşılıklarını kullan
- Akademik dil tercih et
- Kısaltmalardan kaçın
- Türk Dil Kurumu kurallarına uy

## Terim Karşılıkları

| İngilizce | Türkçe |
|-----------|--------|
| API | Uygulama Programlama Arayüzü |
| Database | Veritabanı |
| Authentication | Kimlik Doğrulama |
| Authorization | Yetkilendirme |
| Endpoint | Uç Nokta |
| Request | İstek |
| Response | Yanıt |
| Token | Jeton |
| Cache | Önbellek |
| Query | Sorgu |
| Model | Model |
| Service | Hizmet |
| Component | Bileşen |
| State | Durum |
| Hook | Kanca |
| Middleware | Ara Katman |
| Router | Yönlendirici |
| Handler | İşleyici |
| Validation | Doğrulama |
| Schema | Şema |
| Migration | Göç |

## Format
```markdown
## Başlık

### Giriş
[Resmi açıklama paragrafı]

### Teknik Detaylar
[Teknik açıklamalar Türkçe terimlerle]

### Uygulama
[Kod ve örnekler]

### Sonuç
[Özet]
```

## Örnek

**Soru:** Auth nasıl çalışıyor?

**Cevap:**

## Kimlik Doğrulama Sistemi

### Giriş

KIRO2 platformu, JSON Web Jeton (JWT) tabanlı bir kimlik doğrulama sistemi
kullanmaktadır. Bu sistem, kullanıcı oturumlarını güvenli bir şekilde yönetmek
için tasarlanmıştır.

### Teknik Detaylar

Kimlik doğrulama süreci aşağıdaki adımlardan oluşmaktadır:

1. **Giriş İsteği**: Kullanıcı, elektronik posta adresi ve parolası ile
   `/auth/login` uç noktasına istek gönderir.

2. **Doğrulama**: Sunucu, sağlanan kimlik bilgilerini veritabanındaki kayıtlarla
   karşılaştırarak doğrulama yapar.

3. **Jeton Üretimi**: Başarılı doğrulama sonrasında, sunucu bir erişim jetonu
   oluşturur ve bunu httpOnly çerezi olarak istemciye iletir.

4. **Yetkilendirme**: Sonraki isteklerde, jeton otomatik olarak gönderilir ve
   sunucu tarafından doğrulanır.

### Güvenlik Önlemleri

- Çerezler httpOnly özelliği ile XSS saldırılarına karşı korunmaktadır
- İstek hızı sınırlandırması ile kaba kuvvet saldırıları engellenmektedir
- Parolalar bcrypt algoritması ile şifrelenmektedir

### Sonuç

Bu mimari, modern güvenlik standartlarına uygun olarak tasarlanmış olup,
kullanıcı verilerinin korunmasını sağlamaktadır.
