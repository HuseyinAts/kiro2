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
| 31 Tem 2026 | Mojibake "ikinci dosya" bulgusu | Desen-eşlemesi (`Ã\|Å\|Ä`) **kasıtlı fixture'ı** kusur saydı: `test_turkish_nlp.py`'deki iki dize encoding-onarımı testinin GİRDİSİ (`broken_text`). "Temizlemek" `assert fixes>0`'ı kıracaktı (ölçüldü: fixes 3 → 0) | Bozuk-görünen veriyi düzeltmeden önce **tüketicisine bak**: bir test onu ONARMAK için mi kullanıyor? Değişken adı (`broken_`, `invalid_`, `malformed_`) ilk ipucu |
| 31 Tem 2026 | Bare süreçte `app.tasks` (celery) | Worker kayıt defteri sanıldı; `include` modüllerini **worker önyüklemesi** import ettiği için 15 beat girdisinin 14'ü "kayıtsız" göründü — ikisi o gece logda BAŞARIYLA koşmuştu | Kontrol kolu bilinen-iyi örnek içermeli; canlı `inspect registered` veya `loader.import_default_modules()` kullan |
| 1 Ağu 2026 | Mutasyon kabuk tırnağında bozuldu | M4 mutasyonu `1 error` (collection) verdi, `1 failed` değil — kabuk tırnaklaması dosyaya **syntax hatası** yazmıştı. Syntax hatası veren mutasyon testin yük taşıdığını KANITLAMAZ; sadece dosyanın bozulduğunu gösterir | Mutasyon sonucu `failed` DEĞİL `error` ise ölçüm **geçersiz**; mutasyonu Python ile (kabuk tırnağı olmadan) tekrar uygula. Ankraj `assert eski in t` ile doğrulanmalı |
| 1 Ağu 2026 | "Bu bekçi CI'da koşmuyor" | Yalnız `on:` bloğuna bakıldı. Ölçünce: `ci.yml:281` **marker filtresiz** koşuyor → dosya **TOPLANIYOR**; koşmama sebebi dalın tetiklenmemesi. İkisi ayrı şey ve fark kritikti: toplanma, eksik `psycopg2` yüzünden **merge-anı collection ERROR** demekti (`-x` ile tüm job) | "CI'da koşuyor mu" iki ayrı ölçüm ister: **(a)** iş tetikleniyor mu (`on:` + dal/PR durumu), **(b)** dosya toplanıyor mu (`pytest` çağrısının **marker filtresi**). Yalnız (a)'ya bakmak mayını zararsız gösterir |
| 1 Ağu 2026 | Sabit eşik "ölçüldü" sanıldı | `ESIK = 150` yorumunda "178 testin büyük çoğunluğu koşmalı" yazıyordu ama **hiç canlı koşum yapılmamıştı**. Ölçünce 164/12/2 çıktı: eşik doğruydu, asıl kusur eşiğin **suite büyüdükçe gevşemesi** ve `hata`nın assert edilmemesiydi | Bir eşiği doğrulamak = eşiği aşan/aşmayan **gerçek koşumu** üretmek. Ayrıca mutlak sayıya bağlı eşik, ölçülen evren büyüdükçe sessizce gevşer — orana/farka bağla |
| 14 Ağu 2026 | "`tsc` temiz → eksik dosya yok" | Silinen dosyaları `tsc`'nin `TS2307`'siyle sabit-noktaya kadar geri yükledim, **0 eksik modül** dedi. Sonra `npm run build` **5 CSS** istedi; ayrıca 19 `ImportMeta.env` hatasının tek kaynağı silinmiş `vite-env.d.ts`'ti — import edilmediği için import-grafiği onu **yapısal olarak** göremez | "Eksik dosya" sorusu **her derleyiciye ayrı** sorulur: tip grafiği (`tsc`) ≠ paketleyici grafiği (`vite`). Ambient `.d.ts`, CSS, resim, worker tip grafiğinde YOK |
| 14 Ağu 2026 | mypy "0 hata" artefaktı | `QuestionBankItem has no attribute` taraması **0** verdi. Kontrol kolu: mypy `errors prevented further checking` ile numpy stub syntax hatasında durmuş, gövdeleri hiç analiz etmemişti. `--python-version 3.13` ile 1363 satır çıktı — **yine 0**, çünkü `question = await self.get_question(...)` anotasyonsuz → `Any` | mypy'ı dedektör sayarken iki kontrol: (a) `errors prevented` var mı, (b) hedef değişken **anotasyonlu** mu. Tipsiz servis katmanında mypy'ın 0'ı hiçbir şey ölçmez |
| 14 Ağu 2026 | `git status` `D` = "silinmiş" sanıldı | 142 silinen `.py`'nin **75'i** `script_mezarligi/`'na birebir **taşınmış**, 7'si taşınmış+düzenlenmiş; yalnız 60'ı gerçek silme (ve hiçbiri import edilmiyor) | Silme raporlamadan önce **aynı basename'i depoda ara** + içeriği (satır sonu normalize ederek) karşılaştır. Taşıma, `D` + `??` çifti olarak görünür |
| 15 Ağu 2026 | Göç hacmi toplamla ölçüldü | 69 alanlık şema split'i "2542 erişim / 340 dosya" göründü → repo-geneli göç sanıldı, iş bloke edildi. Ayrıştırınca **yalnız 108'i sınıf düzeyi** (`Model.alan`, SQL ifadesi, gerçek kolon şart) / 17 dosya; gerisi örnek düzeyi ve devrediciyle karşılanabilir | Göçün boyutu **toplam kullanım** değil, **karşılanamayan alt küme**. Bunu ayırmadan strateji seçme: ayrım strangler'ı uygulanabilir kıldı ve işi 340 dosyadan 17'ye indirdi |
| ... | ... | ... | ... |

---

## GRAFİĞİ, SORDUĞUN DERLEYİCİ KADAR GÖRÜRSÜN (14 Ağu 2026)

"Hangi silinmiş dosya gerekli?" sorusunu **tek bir araca** sormak eksik cevap verir.
Aynı depoda üç ayrı bağımlılık grafiği var ve hiçbiri diğerini kapsamaz:

| Grafik | Aracı | Gördüğü | KAÇIRDIĞI |
|---|---|---|---|
| Tip | `tsc` | `.ts/.tsx` import'ları | ambient `.d.ts`, CSS, resim, worker |
| Paketleyici | `vite build` | import edilen her varlık | tip-only import, ambient bildirim |
| Çalışma-zamanı | test / canlı | fiilen çağrılan yollar | hiç çağrılmayan ölü dal |

**Yordam:** sabit-noktaya kadar döngüyü **her araç için ayrı** koştur; biri "temiz"
dediğinde bitmiş sayma. 14 Ağu'da `tsc` 0 dedikten sonra `vite` 5 dosya daha istedi,
ve en pahalı bulgu (19 hata) hiçbir import grafiğinde görünmeyen `vite-env.d.ts`'ti.

## UYUMLULUK KATMANI YARDIM EDEMEDİĞİ YERDE SESSİZ KALMAMALI (15 Ağu 2026)

Strangler/shim yazarken asıl risk, kapsayamadığı durumda **makul görünen bir değer**
döndürmesidir. 69 alanlık split'te devrediciler örnek düzeyini karşılıyor ama sınıf
düzeyini (SQL ifadesi) karşılayamıyor. Orada `None` dönmek, JOIN'e çevrilmesi gereken
**108 yeri görünmez** kılardı — borç ölçülemez hale gelirdi.

**Kural:** shim'in kör noktası **açık ve yol gösteren hata** vermeli, sessiz varsayılan
değil. Bu davranışın kendisi testle çivilenmeli (mutasyon: korumayı kaldır → test düşmeli).

---

*Oluşturulma: 14 May 2026 (Session 156, Faz 0.8). Bir sonraki audit hatasında bu tablo güncellenir.*
