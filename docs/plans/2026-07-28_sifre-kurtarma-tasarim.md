# Şifre kurtarma — tasarım ve ölçümler (28 Tem 2026)

Satışa hazırlık denetiminin **blocker #1**'i. Kapsam: kullanıcının şifresini
kendi başına sıfırlayabilmesi. Karar sahibi: Hüseyin.

## Başlangıç ölçümü (varsayım değil)

| Katman | Bulunan durum |
|---|---|
| `POST /auth/forgot-password` | Var; token üretip Redis'e yazıyor, **`auth.py:1463` sadece TODO** — e-posta gitmiyor, kullanıcıya "gönderildi" deniyor |
| `POST /auth/reset-password` | Var ve doğru çalışıyor |
| `core/email_util.send_email` | **VAR** (SMTP env'li). "SMTP repo'da yok" notu yanlıştı — eksik olan config ve çağrıydı |
| `HesapKurtarmaPage.tsx` | Var, tasarımı bitmiş, testli — ama **%100 mock**: kodu istemcide doğruluyor, 3. adımda sunucuya hiç gitmiyor, "Panele dön" `() => undefined` |
| Rota | **Yok.** `/hesap-kurtarma` (GirisPage:337) ve `/forgot-password` (ModernLoginPage:430) ikisi de ölü link |
| Sözleşme | `api-client` `/auth/recover` çağırıyor — **backend'de böyle bir uç yok** (0 eşleşme). Mock modda gizlenmişti |

## Kararlar

1. **6 haneli kod** (magic link değil) — ekran zaten onun için tasarlanmış ve
   kopyası onaylı. Backend uydurulur.
2. **SMTP ertelendi** — kimlik bilgisi gelene kadar dev-fallback (yalnız
   `ENVIRONMENT=development` **ve** SMTP yokken kod log'a, e-posta maskeli).
3. **Ekran kuralları sunucuya hizalandı** (+büyük harf, +özel karakter).
   `Guclu2024` eskiden 3 tiki yeşil yapıp sunucudan reddediliyordu.
4. **"Panele dön" → "Girişe dön"** — sıfırlamadan sonra oturum açılmıyor;
   ekran gerçekte olmayan bir şeyi vaat etmemeli.

## Güvenlik gerekçesi (tasarım incelemesinde düzeltilen 4 hata)

**a) 6 hane global ad alanına düşemez.** 32 byte token'da zararsız olan
"anahtar = sırrın kendisi" deseni 6 hanede zafiyet: saldırgan 000000-999999
tararken *herhangi birinin* kodunu bulur. Kod `(e-posta, kod)` çiftine bağlandı;
anahtar e-postadan türetiliyor **ve** değer e-posta+kodun HMAC'i.

**b) IP rate-limit'i kaba kuvveti durdurmaz.** Kod başına 5 deneme + IP başına
5 istek/300s → tek IP'den 25 tahmin/5 dk, 24 saatte ~7.200 = 10⁶ uzayda %0,7;
100 IP ile %72. Eklendi: **hesap başına saatte 3 kod** — IP rotasyonunu etkisiz
kılar (15 tahmin/saat → günde %0,036).

**c) Gönderim sonucunu `await` etmek numaralandırma kanalı açar.** SMTP'yi
beklersek kayıtlı adres için yanıt ~200 ms uzar; saldırgan gövdeyi okumadan
sadece süreyi ölçerek kayıtlı adresleri çıkarır. Gönderim fire-and-forget,
sonuç yalnız log'a.

**d) Deneme sayacı atomik olmalı.** JSON içinde tutulursa eşzamanlı iki yanlış
tahmin aynı değeri okur ve limit aşınır. Ayrı anahtar + `INCR`.

## Akış

```
POST /auth/forgot-password   {email}              -> her zaman aynı 200
POST /auth/verify-reset-code {email, code}        -> {success, token}    [YENİ]
POST /auth/reset-password    {token, newPassword} -> DEĞİŞMEDİ
```

Kod → *token* → şifre. Çalışan `reset-password` ucuna hiç dokunulmadı; kod
katmanı onun önüne eklendi.

## Yol boyunca bulunan, planda olmayan hatalar

- **`_get_token_store()` her çağrıda YENİ store üretiyordu.** Redis varken
  zararsız; Redis yokken sınıf süreç-içi `dict`e düşüyor ve o dict her çağrıda
  sıfırlanıyordu → `forgot-password`'ün yazdığı token'ı `reset-password` asla
  bulamıyordu. **Redis'siz her kurulumda şifre sıfırlama zaten ölüydü.**
  Tek örneğe çevrildi.
- **`/giris`** ekranın üst linkiydi ama kayıtlı rota değil → `/login`.
- **Testin kendisi yanlış sözleşmeyi sabitlemişti** (`Guclu2024`).

## Doğrulama

| Kanıt | Sonuç |
|---|---|
| `tests/unit/test_password_reset_codes.py` | 28 test × 2 backend (gerçek Redis + bellek) — **PASS** |
| `scripts/mutation_check_password_reset.py` | **6/6 mutasyon yakalandı**, her biri beklenen testle |
| `tests/integration/test_password_recovery_flow.py` | **7/7 PASS** — e-postadaki kod yakalanıp zincir sonuna kadar koşuluyor, son adımda `pwd_context.verify(yeni_şifre, hash)` |
| `HesapKurtarmaPage.test.tsx` | **8/8 PASS** — canlı-mod sözleşme testi 3 ucun yolunu ve gövdesini sabitliyor |
| `tsc --noEmit` | 0 hata |

Mutasyon turu **gerçek bir boşluk buldu**: `_code_digest`'ten e-postayı
çıkarmak hiçbir testi kırmıyordu, çünkü iki yedekli kontrol birbirini
maskeliyordu. Beyaz-kutu testi + "ikisi birden" mutasyonu eklendi.

## Kapsam dışı (bilerek)

- Gerçek SMTP kimlik bilgisi — operatör işi, `.env`.
- **Sıfırlama sonrası mevcut oturumların düşürülmesi** — repoda refresh-token
  iptal mekanizması yok. Şifresi çalınan kullanıcı sıfırlasa bile saldırganın
  açık oturumu 7 gün yaşamaya devam eder. **Ayrı iş.**
- `users.email` case-sensitive; login de öyle. Farklı harf düzeniyle yazan
  kullanıcı sessizce kurtarılamaz. Düzeltmek login semantiğini değiştirir +
  `MultipleResultsFound` riski taşır. **Ayrı iş.**
- Mevcut `reset_token` Redis'te düz metin (kod hash'li). **Ayrı iş.**
