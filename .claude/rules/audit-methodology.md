---
name: audit-methodology
description: Audit/olcum disiplini — varsayimi olcumden ayirma kurallari
trigger: always
priority: critical
---

# Audit Methodology

Bu kural Faz 0.8 OCR truncation investigation (Session 156, 14 May 2026) sonrasi olusturuldu.
Kok neden: Audit sample TSV'de `LEFT(question_text, 200)` ile yapay truncate edilmis metin,
gercek OCR cut-off ile karistirildi. 50 sample audit'te %24 cut-off raporlandi, gercekte DB'de
%2.15. Plan v1'de Faz 1.10 (re-OCR) scope ~5x asiriya tahmin edildi (~17K vs gercek ~3.6K).

---

## Altın Kural

**Audit sample TSV uretirken metin TRUNCATE ETME.**

```sql
-- ❌ YANLIŞ — sample insan-okunurluk için truncate
\copy (SELECT id, LEFT(question_text, 200) AS question_text, ...)
       FROM question_bank ORDER BY md5(...) LIMIT 50

-- ✅ DOĞRU — full text export, sample size düşür
\copy (SELECT id, question_text, ...)
       FROM question_bank ORDER BY md5(...) LIMIT 30

-- ✅ ALTERNATİF — preview + full birlikte
\copy (SELECT id,
              LEFT(question_text, 200) AS preview,
              question_text AS full_text, ...)
```

**Sebep:** Truncated metin "OCR cut-off" gibi görünür. Audit yapan kişi
(insan veya LLM) preview'i gerçek metin sanır. Yanlış teşhis → yanlış strateji → wasted effort.

---

## Audit RAW TSV Üretim Kuralları

### 1. Full text always

Question text, option metinleri, OCR çıktıları → tam metin export et.
Sample size'i düşürerek dosya boyutunu kontrol et (200 satır × 200 char ≈ 30 satır × full).

### 2. Truncate gerekiyorsa AÇIKÇA İŞARETLE

```sql
-- Eğer text uzunluğu >2000 ise readability için kısalt, ama belirt
SELECT id,
       CASE WHEN LENGTH(question_text) > 2000
            THEN LEFT(question_text, 2000) || '...[TRUNCATED]'
            ELSE question_text
       END AS question_text,
       LENGTH(question_text) AS original_text_len
FROM question_bank
```

### 3. Audit sırasında DB'den re-verify

Cut-off / OCR / incomplete şüphesi olduğunda **DB'yi doğrudan sorgula**:

```sql
SELECT id::text, LENGTH(question_text), RIGHT(question_text, 50)
FROM question_bank
WHERE id::text = '<suspicious_id>';
```

**Kural:** "Bu cut-off görünüyor" tahmin etme — DB'den `RIGHT(question_text, N)` ile doğrula.

---

## Audit RESULT Yazım Kuralları

### Sample-based istatistikleri evren-bazlı doğrulama

Sample %24 cut-off → DB'de gerçekten %24 mi? Doğrula:

```sql
SELECT COUNT(*) FILTER (WHERE question_text !~ '[\?\.\!»"''\)\]\s]$') / COUNT(*)::float
FROM question_bank WHERE is_active = TRUE;
```

Sample ile evren tutmuyorsa **sample bias var** veya **measurement error** — RESULT'a yaz.

### Methodology bölümü zorunlu

Her RESULT.md'nin başında:

```markdown
## Methodology

- Sample SQL: [tam SQL veya dosya referansı]
- Sample size: N
- Sample selection: [random seed, stratified, vs]
- Truncation: [yok / belirtilmiş / sınır]
- Reproducible: [evet/hayır]
```

---

## Phantom Sorun Filtresi (audit context)

Audit'te "X probleminin oranı %Y" raporlandığında ÖNCE:

| Soru | Doğrulama yöntemi |
|---|---|
| Sample mı evren mı? | Evren-level SQL ile spot check |
| Sample bias var mı? | Stratified mi, random mi? Seed reproducible mi? |
| Measurement artifact mı? | Audit script'i tek başına problem mi yaratıyor? |
| TSV/JSON format truncation mı? | Ham veriyi DB'den re-verify et |

**Audit sonucu acil aksiyon planlanmadan önce:** evren-level doğrulama zorunlu.

---

## Varsayım ≠ Ölçüm (3 Haz 2026, garble efsanesi)

Bir sayı MEMORY/audit-doc'ta "toplam" olarak geçiyor diye **satır-bazında kanıt** sanma.

**Vaka:** "61K garble soru" 198 oturum boyunca tekrarlandı, plan kararlarını yönlendirdi.
Ölçünce: `unverified=61,482` sadece **incelenmemiş** demekti — garble-yargılı değil.
DB'de `student_coherent='false'` = **0 satır** (kör-yargı yalnız keep'leri işaretledi,
drop nedenleri persist EDİLMEDİ). Yani "61K garble" hiç ölçülmemiş bir varsayımdı.

**Kural:** Bir kategoriyi (garble, figure-dependent, wrong-answer) "şu kadar var" diye
kullanmadan önce, o etiketin **satır-bazında DB'de sorgulanabilir** olduğunu doğrula.
Sorgulanamıyorsa o sayı bir tahmindir — "ölçülmedi" diye işaretle, aksiyona temel yapma.

> Karpathy bağı: "61K garble → re-OCR → Gemini-bloke → çıkmaz" ezberi 3 oturum üst üste
> yazıldı. Kullanıcı itince ölçüm yapıldı, ezber çürüdü. **Ezbere kategori-sayısı yazma.**

### SEVERITY DE BİR ÖLÇÜMDÜR (28 Tem 2026 — kural yazılıydı ve yine ihlal edildi)

Yukarıdaki bölüm **sayılar** üzerine kurulu ("şu kadar var"). Bu yüzden bir boşluk
bıraktı ve o boşluktan düşüldü: **"acil", "P0", "kritik", "güvenli", "bloke edilmiş"
de birer iddiadır ve çoğu doğrudan ölçülebilir.** Bunlar sayı gibi görünmediği için
"varsayım ≠ ölçüm" deseni onlara eşleşmiyor.

**Vaka:** Depo GitHub'da PUBLIC bulundu (auth'suz API 200) ve geçmişinde 14 anahtar
vardı. Buradan **"rotasyon P0, acil"** sonucu çıkarıldı. Çıkarım mantıklıydı ama
ölçüm değildi. Ölçünce (`backend/scripts/secret_inventory.py --check-live`):

    10 Google -> 400   2 OpenAI -> 401   1 Anthropic -> 401   1 HF -> 401
    HÂLÂ CANLI: 0 / 14

Yani rotasyon fiilen ZATEN yapılmıştı; aciliyet yoktu. Aynı oturumda sayı iddiaları
(367 auth'suz uç → gerçekte 89; "hassas" bulgu → `api_key_configured` boolean bayrağı)
titizlikle doğrulanmıştı. Doğrulanmayan tek şey **severity** oldu.

**Kural:** Bir riski/aciliyeti raporlamadan önce sor — *bu iddianın yanlış olduğunu
gösterecek tek bir ölçüm var mı?* Varsa ONU YAP.

| İddia | Onu çürütebilecek ölçüm |
|---|---|
| "Bu sızmış anahtar tehlikeli" | Anahtar hâlâ geçerli mi? (sağlayıcının en ucuz auth ucu) |
| "Bu uç sızdırıyor" | Auth'suz/yetkisiz çağır, gövdeye bak |
| "Bu kontrol bizi koruyor" | Atlatmayı DENE (bkz. mutasyon testi) |
| "Bu kapı bloke ediyor" | Kapıyı kaldır, kırmızıya dönüyor mu? |
| "Bu veri kaybolmuş/bozuk" | Satır-bazında sorgula, örneklem al |
| "Bu kod ölü" | Import et / çağrı yerlerini say / canlı logdan bak |

**Ve olumsuz yön de aynı:** "sorun yok", "temiz", "hepsi geçiyor" da ölçüm ister.
Yeşil bir test, ölçtüğünü sandığın şeyi ölçmüyor olabilir — bu depo bunu bir günde
üç kez yaşadı (sqlite'a düşen e2e, hiç koşmayan hook, 0 satır tarayan sır bekçisi).

## Metrik Doğrulama Gate (detector'a güvenmeden önce)

Bir ölçüm metriği (garble skoru, kalite skoru, benzerlik) uygulamadan ÖNCE
**kendi doğrulamasını geçmeli.** Geçemezse o metrikle aksiyon ALMA.

İki zorunlu test:

1. **Bilinen-iyi vs bilinen-kötü ayrımı:** metrik, etiketli temiz seti (örn.
   `student_coherent=true`) etiketli bozuk setten ayırıyor mu? Medyanlar çakışıyorsa
   metrik kördür.
2. **Sentetik bozma testi:** temiz veriye bilinen hata enjekte et (OCR char-swap,
   l↔t/o↔e), skor YÜKSELMELİ. Yükselmiyorsa metrik o hataya duyarsız.

**Vaka:** word-DF "nadir-token" metriği DOĞRULAMA-1'i geçemedi (auto_judged_high garble
skoru unverified'den yüksek — çünkü nadir=meşru özel ad/teknik terim). Atıldı.
Char-trigram LM her iki testi de geçti (sentetik bozma 2.68→4.27), uygulandı.
(`backend/scripts/quality/garble_char_lm.py`)

## Ucuz Filtre Tuzağı (içerik silmeden önce)

Deterministik ucuz kural (regex, sözlük-yokluğu, char-yokluğu) ile içerik silerken
**geçerli içeriği yanlış-pozitif yakalama riski yüksektir.** Türkçe STEM özellikle.

**Vaka:** garble-tail'i silmek için 3 ucuz filtre denendi, her biri geçerli Türkçe'yi
çöpe attı: word-DF (MmBb genotip), no-Türkçe-char ("olduguna gore" ASCII-Türkçe +
"3-Metil-3-heksen" kimya), no-Türkçe-word ("Otozomal çekinik özelliği" biyoloji).

**Kurallar:**
- **Pozitif kanıt** ara, negatif yokluk değil. "Yabancı" = İngilizce/Romance kelime VAR,
  "Türkçe-char yok" DEĞİL.
- **Guard zinciri:** Türkçe karakter (ç/ğ/ı/ö/ş/ü) içereni silme listesinden ZORUNLU çıkar.
- **Yargılanmamışı silme:** `unverified` (incelenmemiş) "işe yaramaz" sayılamaz — silmek
  varsayımdır. Sadece **yargılanmış-kötü** (`rejected`, kör-judge drop) silinir.
- Tail küçük + heterojense (geçerli + çöp karışık) → ucuz kuralı bırak, gözle/LLM-yargı.

---

## KÖK NEDEN DE BİR ÖLÇÜMDÜR (30 Tem 2026 — kural üçüncü kez aynı yerden kırıldı)

Bu dosya "sayılar ölçüm ister" (Haz) ve "severity ölçüm ister" (28 Tem) diyor.
Üçüncü boşluk: **"X'in sebebi Y'dir" de bir iddiadır ve tek bir deneyle
çürütülebilir — Y'yi KALDIR, X kayboluyor mu?**

**Vaka.** Bir bekçinin tek-başına yorum satırlarını kaçırdığı ölçüldü (doğru).
Sebep olarak `_is_in_exception`'daki `startswith("#")` dalı gösterildi — kodu
okuyup "bu kesin" denerek, kaldırma testi yapılmadan. Görev bu iddiayla açıldı.
Sonra kaldırıldı ve semptom **sürdü** → "teşhis yanlış" denildi. O da yanlıştı:
`.pyc` bayat + ölçüm `detect()` üzerinden yapılmıştı. `inspect.getsource` ile
yüklenen sürüm kanıtlanınca gerçek tablo çıktı — dal gerçekten sebeplerden
**biriydi**, ama **seri bağlı ikinci** bir bastırıcı daha vardı
(`ContextAnalyzer.should_ignore`). Yani aynı soruda iki kez, iki zıt yönde
yanlış rapor verildi.

**Kural.** Bir kök neden raporlamadan önce:

| Adım | Somut kontrol |
|---|---|
| 1. Kaldırma deneyi | Y'yi devre dışı bırak; X kayboluyor mu? Kaybolmuyorsa Y sebep DEĞİL (veya tek sebep değil) |
| 2. Yüklenen sürümü kanıtla | `inspect.getsource(fn)` içinde işaretçi ara; Python'da `.pyc` sil. "Düzenledim" ≠ "koştu" |
| 3. En alt katmanda ölç | `detect()` gibi sarmalayıcı yerine kusurun olduğu fonksiyonu (`_regex_detect`) doğrudan çağır — arada başka filtre olabilir |
| 4. Tek sebep varsayma | Semptom sürüyorsa ikinci bastırıcıyı ara; "seri bağlı filtre" bu depoda gerçek bir desen |
| 5. Fix'in DEĞERİNİ ölç | Y kaldırılınca kaç bulgu değişiyor? **+0 ise fix yapılmaz** |

**5. adım bu vakada kararı tersine çevirdi:** yorum dalını kaldırmanın kazancı
250 gerçek dosyada **+0 bulgu**; docstring dalını kaldırmanın bedeli ise **+231
CRITICAL** ve hepsi sıradan test deyimi (`MagicMock()`, `@patch(...)`,
`except Exception:`). Yani hatalı heuristik bekçiyi kullanılabilir tutan **yük
taşıyan kaza**ydı. Doğru karar fix YAPMAMAK oldu. Bir hole'un varlığı onu
kapatmak için yeterli gerekçe değildir — **kapatmanın bedeli de ölçülür.**

---

## ÖLÇÜM ALETİNİ DOĞRULA (aynı gün, 4 geçersiz ölçüm)

Bulguları titizlikle doğrulayıp **ölçüm aletini** doğrulamamak bu oturumda 4 kez
yanlış sonuç üretti. Alet sessizce ölçtüğü şeyi değiştirdi:

| Geçersiz ölçüm | Neden geçersiz | Doğrusu |
|---|---|---|
| A/B için dosyayı `/tmp`'ye kopyalamak (2 kez) | Dedektörler dosya adına bakıyor (`test_` öneki), ruff'ta `per-file-ignores` var → kopya farklı davranıyor | A/B'yi **gerçek yolda** yap, geri alımı doğrula |
| Kod düzenleyip ölçmek | `.pyc` bayat kalabilir; ayrıca ölçüm sarmalayıcıdan yapılırsa arada filtre var | `.pyc` sil + `inspect.getsource` ile işaretçi kanıtla |
| Yeni testlerin ilk sürümü | 8 testin 6'sı fix'ten ÖNCE de geçiyordu (vakum test) | Her testi **mutasyonla** çivile; geçmeyen mutasyon = değersiz test |
| Bir uca 404 deyip bulgu sanmak | Yol yanlıştı (`/api/v1/health` yok, `/health` 200) | Bulgu bildirmeden önce aracın kendi doğruluğunu sına |

**Kural:** Bir A/B'ye güvenmeden önce **kontrol kolunun bilinen sonucu ürettiğini**
göster. Kontrol kolu beklediğini vermiyorsa ölçüm bitmiştir — bulgu değil, alet
arızası vardır.

---

## İlişkili Kurallar

- `.claude/rules/systematic-debugging.md` — Phantom sorun filtresi (gercek/fake ayrimi)
- `.claude/rules/debugging-first.md` — Root cause analysis tablosu
- `.claude/rules/verification.md` — Boris Cherny verification standards
- `.claude/rules/testing.md` — Lesson #31 (rejected+is_active=true servis sızıntısı)

---

## Bilinen Audit Methodology Hataları (referans)

| Tarih | Audit | Hata | Fix |
|---|---|---|---|
| 14 May 2026 | C2 audit (Faz 0.2) | LEFT(question_text, 200) truncation | Sample size 30 LIMIT, full text |
| 3 Haz 2026 | Garble efsanesi | "61K garble" = ölçülmemiş varsayım (unverified=incelenmemiş); word-DF metriği doğrulama geçemedi | Char-trigram LM (sentetik-bozma doğrulamalı); satır-bazında etiket şartı |
| 3 Haz 2026 | Garble-tail silme | 3 ucuz filtre geçerli Türkçe STEM'i yanlış-pozitif sildi | Pozitif yabancı-kanıt + Türkçe-char guard |
| 28 Tem 2026 | Sızmış anahtar aciliyeti | "public depo + geçmişte anahtar → P0 acil" ÇIKARIMDI; ölçünce 14/14 anahtar ölü. Kural yazılıydı ama yalnız SAYILARI kapsıyordu, severity'yi değil | `secret_inventory.py --check-live`; kurala "Severity de bir ölçümdür" bölümü |
| 30 Tem 2026 | Bekçi kök nedeni (#451) | "Sebep şu dal" kodu OKUYARAK iddia edildi, kaldırma testi yapılmadı; sonra yapılınca `.pyc`+sarmalayıcı yüzünden ters yönde ikinci yanlış rapor | "Kök neden de bir ölçümdür" bölümü: kaldırma deneyi + `inspect.getsource` + en alt katman + tek-sebep varsaymama |
| 30 Tem 2026 | Fix'in değeri ölçülmedi | Hole gerçekti ama kapatmanın kazancı **+0 bulgu**; docstring dalını kaldırmanın bedeli **+231 CRITICAL** (sıradan mock deyimleri). Hatalı heuristik bekçiyi kullanılabilir tutan yük taşıyan kazaydı | Karar: fix YAPILMADI, ölçüm koda yorum olarak yazıldı; asıl iş kalibrasyona devredildi (#453) |
| 30 Tem 2026 | Ölçüm aleti geçersiz (4 kez) | `/tmp` kopyası (dosya-adı + per-file-ignores bağımlı), bayat `.pyc`, sarmalayıcıdan ölçüm, yanlış URL yolu | "Ölçüm aletini doğrula" bölümü: kontrol kolu bilinen sonucu vermeli, yoksa alet arızası |
| ... | ... | ... | ... |

---

*Oluşturulma: 14 May 2026 (Session 156, Faz 0.8). Bir sonraki audit hatasında bu tablo güncellenir.*
