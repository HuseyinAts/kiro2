# Ölçüm disiplini — vaka arşivi (Mayıs–Ağustos 2026)

> `.claude/rules/audit-methodology.md`'den 20 Ağu 2026'da ayrıldı (E2).
> İçerik **birebir**, tek satır silinmedi. Kuralların kısa hâli ve bu dosyaya
> işaretçiler aktif kural dosyasında.
>
> Gerekçe: aktif kural dosyası `paths:` frontmatter'ı olmadığı için **her oturumda**
> bağlama yükleniyordu ve 1.010 satırdı — her zaman yüklenen 1.345 kural satırının %75'i.
> Vaka kanıtı aranabilir kalmalı ama her oturumun bütçesini yemesi gerekmiyor.

---

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
| 15 Ağu 2026 | WHERE iddiası tam SQL'de arandı (S214) | `select(Entity)` TÜM kolonları SELECT'e koyar → `is_active` filtresi WHERE'den silinse bile alt-metin eşleşiyordu. Test kördü; **mutasyon hayatta kaldı** ve ancak o gösterdi | WHERE iddiası için **yalnız `stmt.whereclause`** derle. Tam SQL sadece JOIN/FROM sınamak için |
| 15 Ağu 2026 | `select_from` ezbere eklendi (S214) | S212'den "şart" diye taşındı ama **koşulluydu**. SELECT listesinde `QuestionBankItem.id` varken derlenmiş SQL onunla/onsuz birebir aynı → kazanç 0, hiçbir mutasyonla çivilenemez | SELECT listesi split-only ise ZORUNLU, değilse ekleme. Riski `FROM question_bank JOIN` assert'i karşılıyor |
| 15 Ağu 2026 | Göç sayacı örnek düzeyini görmedi (S214) | Sayaç `QuestionBankItem.<alan>` (sınıf düzeyi) sayar; `mnemonic_service`'in asıl kusuru `select(QuestionBankItem)` → `question.alan` (örnek düzeyi, `MissingGreenlet`) idi ve sayaçta **0** göründü | Sayacın çıktısı **alt sınır**. Dosya başına ayrıca `grep 'select(QuestionBankItem)'` |
| 15 Ağu 2026 | Göç hacmi toplamla ölçüldü | 69 alanlık şema split'i "2542 erişim / 340 dosya" göründü → repo-geneli göç sanıldı, iş bloke edildi. Ayrıştırınca **yalnız 108'i sınıf düzeyi** (`Model.alan`, SQL ifadesi, gerçek kolon şart) / 17 dosya; gerisi örnek düzeyi ve devrediciyle karşılanabilir | Göçün boyutu **toplam kullanım** değil, **karşılanamayan alt küme**. Bunu ayırmadan strateji seçme: ayrım strangler'ı uygulanabilir kıldı ve işi 340 dosyadan 17'ye indirdi |
| 17 Ağu 2026 | `ruff --version` kapının sürümü sanıldı (S224) | Makinede **üç** ruff var: kabuk+PostToolUse kancası **0.14.13**, `git commit` kapısı **0.7.1** (kök config `:37`), ölü `backend/` config **0.13.2**. Kanca her Edit sonrası 0.14.13 ile biçimlendiriyor, kapı 0.7.1 ile yeniden biçimlendirip EXIT 1 veriyor → `--amend` **sessizce iptal**, `git log` aynı hash'i gösterdiği için "oldu" sanıldı (2 kez). Geri alma `git checkout -- .` kirli ağaçta **ilgisiz** dosyada NTFS hatası verip yanlış teşhise yönlendirdi | "Aynı aracın üç sürümü var ve kapıyı en eskisi tutuyor" bölümü: kapının sürümüyle biçimlendir (`pre-commit run ruff-format --files`), sabit nokta doğrula, amend sonrası **hash'in değiştiğini** ölç |
| 17 Ağu 2026 | Kapı ölçümü dosyayı değiştirdi (S228) | Kontrol kolu için `git stash push` → `pre-commit run ruff` → `pop` dizisi kuruldu. Orta adım `--fix` ile HEAD sürümünü değiştirdi (1747→1745), `pop` reddetti, **stash saklı kaldı**. Ölçüm geçerliydi (19 kalem) ama aracın yan etkisi ağaçta üçüncü bir hâl bıraktı | `git checkout HEAD -- <dosya>` (yan etkiyi at, `status` boş olmalı) sonra `pop`. Kural: auto-fix'li kancayı kontrol kolu yaparken yazdığını varsay |
| 17 Ağu 2026 | Silme-only commit'e sessiz süpürme (S228) | Aynı koşumda `ruff-format` dokunulmamış koda +21/−4 satır uyguladı ve staged'ın üstüne bindi | `git diff --numstat` ile yakala; **`git checkout --`** (index'ten) ile geri al — `git checkout HEAD --` silmeyi de geri getirir |
| 17 Ağu 2026 | "Yeni sır bulundu" (S228) | `detect-secrets` 3 kalem bildirdi; kanca yalnız DEĞİŞEN dosyaları tarar, dosya ilk kez taranıyordu. 3'ü de HEAD'de birebir mevcut, baseline'da o dosya için **0 kayıt** | `git show HEAD:<dosya> \| grep -cF "<satır>"` + baseline kayıt sayısı. İkisi birlikte "yeni mi / hiç taranmamış mı" ayrımını verir |
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

## ŞEMA GÖÇÜNDE "ÇEVİRDİM + TESTLER YEŞİL" BİR ÖLÇÜM DEĞİLDİR (15 Ağu 2026, S212)

69 alanlık split'in JOIN göçünde **3 dosyanın 3'ünde de** kusur çıktı — ve hiçbirini
"testler geçiyor" yakalamadı. Kabul kriteri dört ayrı ölçüm ister; biri atlanırsa
o sınıftaki kusur sessizce commit'e girer.

| # | Ölçüm | Neden gözle/testle yakalanmaz |
|---|---|---|
| 1 | Sorguyu **derle** (`compile(dialect=postgresql, literal_binds)`) | Aşağıdaki A |
| 2 | Kartezyeni **`get_final_froms()`** ile kontrol et | Aşağıdaki B |
| 3 | Delege okuyan yolu **eager-load** et | Aşağıdaki C |
| 4 | **Gerçek modele** karşı test yaz | Aşağıdaki D |

### A. Sorgu ÇALIŞMA anında değil, KURULURKEN patlar

`select(func.avg(SplitTablo.x)).join(SplitTablo, ...)` — SELECT listesinde yalnız
split tablo olduğu için SQLAlchemy **sol tarafı o tablo sanar** ve kendisine JOIN
etmeye çalışır:

    InvalidRequestError: Don't know how to join to <Mapper QuestionStatistics>.
    Please use the .select_from() method to establish an explicit left side.

`.select_from(QuestionBankItem)` şart. Gözle okuma bunu **kaçırdı**: diğer 3 sorgu
(`select(Entity).join(...)`) aynı görünüyordu ve gerçekten doğruydu; kırık olan tek
sorgu SELECT listesi farklı olandı. Ayrıca o metodun **hiç testi yoktu**, yani
"212 test yeşil" o sorgu hakkında sıfır bilgi taşıyordu.

Kolon seçiminde ise devredici sınıf düzeyinde `AttributeError` fırlatır — sorgu hiç
kurulamaz. `duel_api`'de düello akışının **üç yolu da** bu yüzden üretimde kırıktı.

### B. Metinsel kartezyen kontrolü yanlış-pozitif verir

"FROM yan tümcesinde virgül var mı" kontrolü `SELECT count(*) FROM (SELECT a, b ...)`
şeklinde takılır — virgül **alt-sorgunun SELECT listesindedir**. Bu bir kez gerçek bir
sorguyu (`search_questions`) yanlış yere bayrakladı.

Beteri: aynı kontrolün ilk sürümü `sql.split(" from ")` kullanıyordu ve SQLAlchemy
`FROM`'u **yeni satıra** koyduğu için hiç eşleşmiyordu → kontrol sessizce boşa
düşüyordu, yani "temiz" çıktısı **boşlukta ölçümdü**.

    froms = stmt.get_final_froms()
    assert len(froms) == 1        # semantik; alt-sorguya takılmaz

Kontrol kolu zorunlu: gerçek kartezyen (`select(A, B)`) → 2, alt-sorgu → 1.

### C. JOIN yalnız SQL katmanını düzeltir — instance katmanı ayrı

Split ilişkileri `lazy='select'` (ölçüldü: `content`/`metadata_info`/`statistics`).
Async oturumda yüklenmemiş ilişkiye erişmek **`MissingGreenlet`** atar. Sorgu JOIN'li
olsa bile, dönen nesneden delege okuyan satır patlar.

Bu iki serviste **4 gerçek kusur** üretti ve hepsi **sessizdi**, çünkü o kod yollarında
çıplak `except Exception` var:
- `update_question` → `_create_question_version` 10 delege okuyor → versiyon geçmişi
  sessizce kayboluyordu.
- `get_question_by_id` → `except Exception: return None` → kusur **"soru bulunamadı"**
  gibi görünüyordu.

### D. Sahte-model stub'ıyla yazılmış test, KIRIK kodda da yeşil kalır

`tests/unit/test_coverage_final_50.py` kendi `models.question_bank` stub'ını
`sys.modules`'e koyuyor. `create_question` split sonrası **koşulsuz kırıktı**
(taze nesnede `statistics` yok → `AttributeError`), ama o dosyadaki
`test_create_question` **geçiyordu** — gerçek modeli hiç görmüyor.

Örnek doğru testler: `backend/tests/fast/test_question_bank_service_split.py`,
`test_question_crud_service_split.py`, `test_duel_api_split.py`.

### Yan ölçüm: eager-load gerekliliğini KOLON/ENTITY ayrımıyla belirle

Her dosyaya `selectinload` eklemek yanlış. `duel_api`'nin 12 erişiminin hepsi **kolon
seçimiydi** (`select(Model.alan, ...)`) — `Row` döner, ORM nesnesi değil, lazy-load
riski **yok**. Varsaymak yerine ölçüldü:

    grep 'select(QuestionBankItem)' api/duel_api.py   # 0 sonuc -> eager-load N/A

---

## ENTITY SEÇEN SORGUDA WHERE İDDİASINI TAM SQL'DE ARAMA (15 Ağu 2026, S214)

Yukarıdaki B maddesi "kartezyeni metinle ölçme" diyor. Aynı tuzağın ikinci
ağzı **WHERE iddialarında** ve bu oturumda ısırdı — kural yazılıydı, yine
düşüldü.

`select(QuestionBankItem)` **tüm** tablo kolonlarını SELECT listesine koyar.
Dolayısıyla `is_active` filtresi WHERE'den **tamamen silinse bile** derlenmiş
SQL'de `question_bank.is_active` dizesi durur — SELECT listesinde. Test yeşil
kalır. Ölçüldü:

    filtre YOKKEN 'question_bank.is_active' in sql   -> True
    stmt.whereclause                                 -> question_bank.id = 'q-1'

Mutasyon (filtreyi sil) **hayatta kaldı**; testin değersiz olduğu ancak
mutasyonla görüldü.

**Kural:** bir WHERE koşulunu iddia ediyorsan **yalnız `stmt.whereclause`**
derle. Tam SQL yalnız JOIN/FROM/ORDER BY gibi yapıları sınamak için.

```python
where_sql = str(stmt.whereclause.compile(
    dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
assert "question_bank.is_active" in where_sql
```

## `select_from` HER YERDE DEĞİL — SELECT LİSTESİ SPLIT-ONLY İSE (15 Ağu 2026, S214)

S212'de `.select_from(QuestionBankItem)` "şart" diye kaydedildi. Doğru, ama
**koşullu**: SQLAlchemy sol tarafı SELECT listesinden çıkarır.

| SELECT listesi | `select_from` | Ölçüm |
|---|---|---|
| Yalnız split tablo kolonları (`func.avg(QuestionStatistics.x)`) | **ZORUNLU** | Yoksa `InvalidRequestError`; S214 M1 mutasyonu 5 test düşürdü |
| `QuestionBankItem.id` de içeriyor | **SÜS** | Derlenmiş SQL onunla ve onsuz **birebir aynı**; mutasyon hayatta kaldı |

Kazancı ölçmeden ekleme: #451 deseninin tersi — *bir hole'un varlığı kapatmak
için yeterli gerekçe değildir* kadar *kodun var olması gerekli olduğunu
kanıtlamaz* da doğru. Süs `select_from` hiçbir mutasyonla çivilenemez, yani
test edilemez ağırlıktır.

Kapattığı riski **test** karşılasın: `assert "FROM question_bank JOIN" in sql`
— SELECT listesinden `QuestionBankItem.id` düşerse sorgu zaten kurulamaz.

## SAYAÇ SINIF DÜZEYİNİ SAYAR, ÖRNEK DÜZEYİNİ GÖRMEZ (15 Ağu 2026, S214)

`#485` göç sayacı `QuestionBankItem.<alan>` deseniyle **sınıf düzeyi** erişim
sayar. `mnemonic_service`'te asıl riski taşıyan kusur bu desende **hiç
görünmedi**: `select(QuestionBankItem)` ile entity seçilip sonra
`question.question_text` okunuyordu — örnek düzeyi, `lazy='select'`, async'te
`MissingGreenlet`.

**Kural:** göç kalanını raporlarken sayacın çıktısı **alt sınırdır**. Her
dosyada ayrıca `grep 'select(QuestionBankItem)'` koş; >0 ise okunan (ve
YAZILAN) alanları çıkar, eager-load gerekliliğini oradan belirle.

## ALAN TAŞIRKEN BİÇİMLENDİRİCİ IMPORT'U SİLER (15 Ağu 2026, S212)

`correct_answer` erişimi `QuestionBankItem` → `QuestionContent`'e çevrilince o
fonksiyonda `QuestionBankItem` kullanılmaz kaldı ve import **otomatik silindi** —
ama `QuestionContent` import'u henüz eklenmemişti. Sonuç `NameError` olacaktı;
`grep` ile yakalandı.

**Kural:** alan taşımadan sonra dosyadaki **import satırlarını yeniden say**; "silinen
bir import" ile "eklenmesi unutulan bir import" aynı diff'te yan yana durabilir.
İlgili: `reference_formatter-import-stripping` (kullanımı önce yaz, sonra import'u doğrula).

---

## KİRLİ AĞAÇTA PATHSPEC'SİZ `git stash` KULLANMA (15 Ağu 2026, S212 — near-miss)

Baseline ölçmek için `git stash` (pathspec'siz) çalıştırıldı. Ağaçta 3390 pre-existing
kirli dosya olduğu için stash **hepsini** aldı; arada `pre-commit run --files` baseline'a
küçük bir biçimlendirme uyguladı; `git stash pop` **conflict** verip durdu ve stash
KEPT olarak kaldı. İş kaybolmadı ama kurtarma gerekti (`git checkout HEAD -- <dosya>`
ile çakışan dosyayı temizle → `pop` tekrar).

**Kural:** kirli ağaçta baseline ölçümü için **daima** `git stash push -- <dosya>`
(pathspec'li). Bu oturumda pathspec'li form 2 kez kullanıldı, 2 kez sorunsuz döndü.
İlgili: `verification.md#GERI ALIM BIR IDDIADIR` — geri alım `git status` ile
doğrulanmadan "yapıldı" sayılmaz.

---

## DOSYA HİÇ COMMIT EDİLMEMİŞ OLABİLİR (15-16 Ağu 2026, S215)

`#485` göçünde dosya-başına akış hep şunu varsaydı: "dosya HEAD'de zaten var,
`pre-commit run --files` baseline'ı HEAD'e karşı ölçülen bir borcu gösterir".
`api/osym_routes.py`'de bu varsayım kırıldı: `git diff` alınınca `auto_assign_anchors`,
`run_equating`, `analyze_osym_pdf` fonksiyonlarının **hiçbiri HEAD'de yoktu** — S210
Gemini devrinden kalma, hiç commit edilmemiş çalışan-ağaç içeriğiydi (3388 kirli
dosyanın biri, ayrı ayrı fark edilmemişti). `git stash push -- <dosya>` ile HEAD'e
dönünce dosya 130 satır kısaldı ve import edilen sınıflar (`AutoAssignAnchorsRequest`)
tamamen kayboldu.

**Sonuç:** "kontrol kolu HEAD'de de var mı" sorusu (S211-S214'ün kapı-borcu
politikası) bu dosyanın bir kısmı için **anlamsız** oldu — orada karşılaştırılacak
bir HEAD hali yoktu. Örnek: `PDFAnalysisRequest.examType` alanındaki N815 ihlali
HEAD'de "önceden var" değildi, çünkü sınıfın kendisi HEAD'de yoktu; yine de aynı
karar geçerliydi (dokunulmayan koda ait, API sözleşmesi kasıtlı camelCase).

**Kural:** Bir dosyada pre-commit baseline borcu bulunduğunda ÖNCE
`git diff -- <dosya>` (veya `git log --oneline -1 -- <dosya>`) ile dosyanın HEAD'de
**gerçekten var olup olmadığını** doğrula. Yoksa/kısmen yoksa, "HEAD'de de var mıydı"
sorusunu sorma — karar ölçütü aynı kalır (dokunulan fonksiyon mu, dokunulmayan mı) ama
gerekçe metninde "önceden var olan" yerine "bu turda ilk kez commit edilen, dokunulmayan
kod" yazılmalı. Yanlış gerekçe (`git show HEAD:...` ile kontrol kolu aranması) sonuçsuz
kalır ve zaman kaybettirir.

---

## KOŞULSUZ PRE-COMMIT HOOK'U KONU-DIŞI SEBEPLE KIRILABİLİR (16 Ağu 2026, S215)

`pytest-fast` hook'u (`pass_filenames: false`, `files:` filtresi yok → değişen
dosyadan bağımsız her backend commit'inde koşar, sabit 6 test dosyasını çalıştırır)
`api/osym_routes.py` commit'inde **kırmızı** çıktı. Kök neden `#485`/`question_bank`
ile **hiç ilgisizdi**: `test_fsrs_card_persistence.py` bir `bkt_states` satırı INSERT
ediyor, `student_id` `users` tablosunda yok → `ForeignKeyViolationError` →
transaction abort → aynı worker'daki iki `test_bkt_record_answer_batch1b*.py`
`PendingRollbackError` ile ERROR veriyor (cascading failure, tek kök neden).

**Kural:** Dosya-filtresiz/`always_run` tipi bir pre-commit hook'u konu-dışı bir
sebeple kırıldığında iki ayrı karar var, ikisi de gerekli:
1. **Şimdi:** kullanıcı onayıyla `SKIP=<hook_id>` — `kiro2-api-import-smoke`
   emsaliyle aynı muamele.
2. **Sonra:** bu SKIP'i handoff'ta **yeni, ayrı bir açık iş** olarak kaydet — "zaten
   biliniyordu" diye mevcut bir maddeye gömme. Aksi halde hook'un ne zaman kırıldığı,
   kaç commit'in onu atladığı iz kaybeder ve düzeltme sonsuza kadar ertelenir. Bu
   depoda `kiro2-api-import-smoke` tam bu şekilde S211'den beri "bilinen ortam
   kusuru" diye taşınıyor — henüz kimse kök nedenini kapatmadı.

---

## İLERLEME SAYACI DA BİR ÖLÇÜM ALETİDİR (16 Ağu 2026, S219)

Bu dosya "ölçüm aletini doğrula" diyor ve bunu **bulgu üreten** aletlere uyguluyordu.
Boşluk: **ilerlemeyi** ölçen alet hiç doğrulanmamıştı. `#485` göçünde sekiz oturum
(S211-S218) tek satırlık bir regex sayacını ilerleme ölçütü olarak kullandı:

    re.finditer(r'QuestionBankItem\.(\w+)')

Sayaç **iki yönde birden** yanılıyordu ve ikisi de ölçüldü:

| Yön | Ne oluyor | Ölçüm |
|---|---|---|
| **FAZLA** | Yorum/docstring metnini erişim sayıyor | `osym_exam_engine.py:1327` ve `models/question_bank.py:528` birer **yorum satırı**; sayacın 10 kaleminin 2'si fantomdu |
| **EKSİK** | Alias'lı import'ları göremiyor | 15 alias'lı import / 11 dosya (`as Question` ×13, `as Soru`, `as _QB`). S214'ün yedek kontrolü `grep 'select(QuestionBankItem)'` de aynı körlükte |

Gerçek kapsam AST ile ölçüldü: **146 SINIF / 12 KWARG / 69 ENTITY / 26 dosya** —
sayacın gösterdiği 8 gerçek kalemin ~20 katı. En büyük üç dosya (`osym_exam_engine` 42,
`soru_bankasi_service` 41, `exam_performance_service` 11) **hiç görünmüyordu**; üçü de
alias kullanıyor. Alias takibi yükün %94,5'ini taşıyor (146 SINIF'in 138'i).

**Kural:** "Kalan N" bir ölçümdür. Doğrulanmamış bir aletten gelen N bir **tahmindir**.
Bir sayacı ilerleme ölçütü yapmadan önce:
1. **Kontrol kolu:** bilinen-iyi bir dosyanın bilinen sayısı birebir üremeli.
2. **Bilinen-kötü:** kasıtlı bir fantom (yorum satırı) elenmeli.
3. Sayaç **AST tabanlı** olmalı — regex yorum/docstring/alias ayrımını yapamaz.

Alet: `backend/scripts/scan_split_accesses.py` · Bekçi: `backend/tests/fast/test_scan_split_accesses.py`

### Bir ölçüm aletinde YANLIŞ-SIFIR tek kabul edilemez hata türüdür

AST'ye geçmek yetmedi. İlk AST sürümü de iki kör noktayla **sıfır** raporluyordu:

- `update(X).values(<taşınmış_alan>=...)` — taşınmış alan **keyword argüman ADI** olarak
  geçiyor, AST'de `Attribute` düğümü yok. **12 kalem / 3 dosya.**
- `db.query(<alias>)` — eski ORM biçimi; `select(...)` aranıyordu. **3 kalem.**

Neden ölümcül: sayaç `core/irt_daemon.py [SINIF=2]` diyordu. O 2'yi göç ettiren biri
dosyanın çıktıdan kaybolduğunu görüp **"bitti"** derdi. Oysa `irt_daemon.py:211` altı
taşınmış alanı `update(QuestionBankItem).values(...)`'a geçiriyor → **her IRT kalibrasyon
yazımı `CompileError`**. Ölçüldü:

    CompileError : Unconsumed column names: morphology_complexity, irt_difficulty

**Kural:** "Ne kadar iş kaldı" sorusunu yanıtlayan bir alette **yanlış-sıfır**, işi
sessizce bitirir. Aletin kör noktaları docstring'de **açıkça yazılmalı** (sessiz
varsayılan değil), parse edilemeyen dosya **gürültülü** olmalı (`except SyntaxError:
return 0` işi "bitmiş" gösterir), ve alet **kendi testine** sahip olmalı.

## TEST PAKETİ DE BİR DİLİM ÖLÇER (16 Ağu 2026, S219)

Sayaç körlüğünün aynısı **testlerde** çıktı. `osym_exam_engine` için yazılan 15 RED
testin hepsi `MATEMATIK`/`FIZIK` kullanıyordu. Ama `:1564-1572` dört ek sınıf-düzeyi
erişimi **yalnızca** `subject in ("TURKCE","EDEBIYAT","TARIH","COGRAFYA","SOSYAL")`
iken ekliyor (LaTeX süzgeci).

Ayırt edici mutasyonla ölçüldü — tüm alanları doğru göç ettiren ama `question_text`'in
12. erişiminden sonrasını reddeden bir vekil (= "base_filters göçürüldü, `filters.extend`
kaçırıldı" fix'inin birebir simülasyonu):

    MUTASYONLU fix · MATEMATIK : KURULDU   <- mutasyon KACAR (satirlar hic kosmuyor)
    MUTASYONLU fix · TURKCE    : DUSTU
    TAM fix        · her ikisi : KURULDU

Erişim sayısı: MATEMATIK 36 / `question_text` 12; TURKCE 40 / 16 → tam **+4**, satır
atfıyla `1567-1570`. Parametrize edilmeseydi bu mutasyon **hayatta kalırdı** ve TYT
Türkçe (40 soru, en büyük ders) üretimde kırık kalırdı.

### "Göç ettin mi" ≠ "koruduun mu"

Parametrize etmek yetmedi. Test yalnız *sorgu kuruluyor mu* diyordu. Bir ajan
`AttributeError`'dan kurtulmak için `filters.extend` bloğunu **silebilirdi** — iki
parametre de yeşil kalır, Türkçe sınavlar sessizce LaTeX formüllü soru servis ederdi.

**Kural:** bir filtreyi/kontrolü göç ettiren test, o filtrenin **hâlâ etkili olduğunu**
da iddia etmeli. Ölçülebilir hâli: doğru fix'in ürettiği koşul **sayısını** assert et
(`where.count("question_content.question_text NOT LIKE") == 4`), sadece "sorgu kuruldu"
değil. Sayının ayırt ediciliği de doğrulanmalı — burada pasaj süzgeçleri
`question_text)` NOT LIKE üretiyor (arada parantez), o yüzden 6 tanesi sayıma girmiyor.

### Yorum CI'da düşmez

Aliasing tehlikesi (`filters = base_filters` **aynı nesne**, sonra `filters.extend(...)`
`base_filters`'ı mutasyona uğratıyor) ölçüldü ve önce yalnız bir **handoff mesajında**
duruyordu. Mesajı sonraki ajan görmeyecek; dosyayı görecek.

**Kural, üç kademe:** mesajdaki bilgi **kaybolur** → yorumdaki bilgi **silinebilir** →
yalnız **test** CI'da düşer. Ölçülmüş bir tehlikeyi kaydederken üçünü de sor: bu bilgi
nerede yaşamalı? Load-bearing ise **test yaz**, yoruma güvenme.

## `pre-commit run` YANLIŞ CWD'DEN KAPININ ÖLÇÜMÜ DEĞİLDİR (16 Ağu 2026, S219)

`reference_precommit-vs-bare-linter` "farklı CWD → farklı `pyproject.toml`" diyor.
Daha kötüsü ölçüldü: **farklı CWD → tamamen farklı `pre-commit` config'i.**

Kurulu kanca kök config'i sabitliyor:

    .git/hooks/pre-commit -> ARGS=(hook-impl --config=.pre-commit-config.yaml ...)

Git kancaları depo kökünden koşar, dolayısıyla `backend/.pre-commit-config.yaml`
`git commit`'te **hiç yüklenmiyor**. `backend/` içinden `pre-commit run --files`
koşmak, kapının çalıştırmadığı hook'ları devreye sokar:

| Hook | Kök config'te | Zararı |
|---|---|---|
| `black` | **YOK** (satır 35: "Ruff (replaces black, isort, flake8)") | Dokunulmamış satırları yeniden biçimlendirir (= süpürme). Ayrıca `random.sample(...)  # nosec B311`'de yorumu kapanış parantezine taşıyor → **bandit bastırmasını kırabilir** |
| `bandit` (backend) | Ayrı, bozuk ortam | `ModuleNotFoundError: No module named 'pbr'`; kök config'in bandit'i geçiyor |
| `pytest-fast` | **YOK** | S215 FK fixture kırığı; konu dışı kırmızı |

**Doğrudan sonuç — S215-S218'in `SKIP=pytest-fast` engelleyicisi FANTOM.** Hook
`git commit`'te hiç koşmuyor; SKIP aylardır boşuna taşınıyordu. (Kaynak kafa karışıklığı:
kök config'teki `KALDIRILDI (28 Tem 2026)` bloğu **başka** bir hook'a ait —
pre-push tam-paket `pytest`. `git log -S "pytest-fast" -- .pre-commit-config.yaml` boş:
o dize kök config'in geçmişinde hiç bulunmadı.)

**Kural:** kapıyı ölçmek için **depo kökünden** koş, veya `--config` ver:

    cd <repo-root> && pre-commit run --files backend/<dosya>

## …AMA `pre-commit run` SALT-OKUNUR BİR ÖLÇÜM ARACI DA DEĞİL (17 Ağu 2026, S228)

Bir üstteki kural "kapıyı doğru **yerden** ölç" diyor. Eksik kalan yarısı: o ölçüm
**dosyayı değiştirir**. Kök config `ruff` hook'una `--fix --exit-non-zero-on-fix`
veriyor (`.pre-commit-config.yaml:39`) ve `ruff-format` zaten biçimlendirici.
Yani `pre-commit run` bir *gözlem* değil, bir *müdahale*.

Bu, S212'nin stash near-miss'ini birebir tekrarlattı. Kontrol kolu şu diziydi:

    git stash push -- <dosya>              # silmemi kaldır, HEAD'e dön
    pre-commit run ruff --files <dosya>    # HEAD'de kaç kalem vardı? -> 19
    git stash pop                          # silmemi geri koy

Üçüncü adım **düştü**: ikinci adım HEAD sürümünü auto-fix'lemişti (1747→1745
satır), dolayısıyla `pop` "Your local changes would be overwritten" ile reddetti
ve **stash SAKLI kaldı** — iş stash'te, çalışma ağacında ise ne HEAD ne benim
sürümüm olan üçüncü bir hâl vardı.

**Kurtarma (ölçüldü, çalıştı):**

    git checkout HEAD -- <dosya>   # ölçümün YAN ETKİSİNİ at
    git status --short <dosya>     # BOŞ olmalı
    git stash pop                  # artık temiz, uygular

**Kural:** biçimlendirici/auto-fix içeren bir kancayı kontrol kolu olarak
kullanacaksan, ölçüm adımının **yazdığını varsay**. Ya ölçümü ayrı bir çalışma
kopyasında yap, ya da `pop`'tan önce ölçülen dosyayı `git checkout HEAD --` ile
sıfırla. Genel hâli: *bir aracın çıktısını okumak, o aracın girdiyi değiştirmediği
anlamına gelmez.*

### Yan sonuç: auto-fix, kapsam dışı süpürmeyi SESSİZCE stage'ler

Aynı koşumda `ruff-format` dokunmadığım koda **+21/−4 satır** uyguladı (boş satır
ekleme, `class X(Exception): pass` bölme, satır sarma). Silme-only bir commit'e
bunlar fark edilmeden girebilirdi; `git diff --numstat` ile yakalandı ve geri
alındı — **`git checkout -- <dosya>`** ile, yani *index'ten*. `git checkout HEAD --`
kullanmak silmeyi de geri getirirdi; ikisinin farkı burada yük taşıyor. Bkz. bu
dosyada "AĞAÇ KİRLİ SÜPÜRME GEREKÇESİ DEĞİLDİR".

### Yan sonuç: `detect-secrets`in "yeni bulgusu" yeni olmayabilir

Kanca yalnız **değişen** dosyaları tarar. Yıllardır duran bir test literali,
dosyaya ilk kez dokunduğun commit'te "yeni sır" gibi düşer. Ayırt etmek iki
ölçüm: `git show HEAD:<dosya> | grep -cF "<satır>"` (>0 ise önceden var) ve
`.secrets.baseline`te o dosya için kayıt sayısı (**0** ise satır-kayması değil,
dosya hiç taranmamış). S228'de 3 kalemin 3'ü de HEAD'de birebir mevcuttu ve
baseline'da 0 kayıt vardı.

## AYNI ARACIN ÜÇ SÜRÜMÜ VAR VE KAPIYI EN ESKİSİ TUTUYOR (17 Ağu 2026, S224)

Bir üstteki bölüm "yanlış CWD → yanlış **config**" diyor. Bir adım daha var ve
bu oturumda iki commit'i sessizce yuttu: **yanlış giriş noktası → yanlış SÜRÜM.**
`ruff --version` yazıp gördüğün sayı, `git commit`'in çalıştırdığı sayı değil.

Bu makinede ölçüldü (`ruff.exe --version`, üç ayrı ikili):

| Giriş noktası | ruff | Ankraj |
|---|---|---|
| Kabuk (`ruff format x.py`) **ve** PostToolUse kancası | **0.14.13** | PATH → `Python313/Scripts/ruff`; kanca `.claude/hooks/post-edit-format.py:48,53` **çıplak `ruff`** çağırıyor |
| **`git commit` KAPISI** | **0.7.1** | kök `.pre-commit-config.yaml:37` `rev: v0.7.1`, izole venv (`~/.cache/pre-commit/repobiv5dj3f`) |
| `backend/.pre-commit-config.yaml:7` (`rev: v0.13.2`) | **0.13.2** | commit anında **HİÇ YÜKLENMİYOR** (S219) — kurulu ama ölü |

Yani kararı veren sürüm, başka hiçbir giriş noktasının kullanmadığı **en eski**
olanı. Ve PostToolUse kancası her `Edit`/`Write` sonrası dosyayı 0.14.13 ile
biçimlendirdiği için döngü kendi kendine kuruluyor:

    Edit -> kanca 0.14.13 ile bicimlendirir -> kapi 0.7.1 ile ayni dosyayi
    YENIDEN bicimlendirir -> "files were modified by this hook" -> EXIT 1

### Sinsi kısım: `--amend` sessizce iptal olur

Hook dosyayı değiştirip 1 döndürünce `git commit --amend` **çalışmaz**, ama
`git log --oneline -1` **aynı hash'i** gösterir — çünkü eski commit hâlâ
oradadır. Çıktıya bakan "amend oldu" sanır ve eski içeriği push etmeye çalışır.
Bu oturumda **2 kez** düşüldü; 3. denemede çıkış kodu ölçülünce görüldü.

İkinci tuzak aynı yerde: hook başarısız olunca pre-commit geri alma için
`git checkout -- .` çalıştırır. 3399 kirli dosyalı bir ağaçta bu, konuyla
**ilgisiz** bir dosyada NTFS `Invalid argument` ile patlar ve hata mesajı
**yanlış dosyayı** işaret eder (`_blindsolve/w22batches/g28.json`). Teşhis
oradan başlarsa saatler kaybedilir.

### Yordam (ölçüldü, çalıştı)

```bash
git checkout -- <dosya>                          # calisan agac = index
pre-commit run ruff-format --files <dosya>       # KAPININ surumuyle bicimlendir
pre-commit run ruff-format --files <dosya>       # sabit nokta mi? -> "Passed"
git add <dosya> && git commit --amend --no-edit
git log --oneline -1                             # HASH DEGISMELI
```

**Kural:** bir commit/amend'i "oldu" saymadan önce **hash'in değiştiğini**
doğrula. Çıkış kodu 0 mı, onu ölç — hook çıktısının son satırına güvenme.
Ve bir dosyayı "biçim temiz" ilan etmeden önce **kapının sürümüyle** biçimlendir;
`ruff --version`'ın söylediği sürüm bu depoda kapının sürümü **değildir**.

İlgili: [[reference_precommit-vs-bare-linter]] (aynı sınıfın CWD/config ayağı) ·
[[reference_formatter-import-stripping]] (kanca kullanılmayan import'u siler) ·
`verification.md#GERI ALIM BIR IDDIADIR`.

## `Path.write_text()` GERİ ALIM DOĞRULAMASINI BOZAR (16 Ağu 2026, S219)

`verification.md#GERI ALIM BIR IDDIADIR` geri alımın doğrulanmasını şart koşuyor.
Yeni tuzak: doğrulama **yanlış-pozitif** verebilir.

Windows'ta `Path.read_text()` CRLF'i LF'e çevirir, `write_text()` geri yazarken LF'i
CRLF yapar. Sonuç: içerik **birebir aynı**, ama `git status` dosyayı **kirli** gösterir
ve mutasyon harness'i "geri alım başarısız" diye durur. Ölçüldü: `git diff --stat` boş,
yalnız `CRLF will be replaced by LF` uyarısı.

**Kural:** mutasyon/geçici düzenleme harness'lerinde **`read_bytes()`/`write_bytes()`**
kullan. Bayt düzeyinde çalış, metin düzeyinde değil.

## "AĞAÇ KİRLİ" SÜPÜRME GEREKÇESİ DEĞİLDİR (16 Ağu 2026, S219)

Bir fix commit'ine ilgisiz, commit'siz bir blok (S210 devri) süpürüldü ve gerekçe
"ağaçta 3389 kirli dosya var, temizlemek küçük iş değil" oldu. Gerekçe **ölçüme
dayanmıyordu**: gereken ağacı temizlemek değil, **tek dosyayı** ayırmaktı.

    git stash push -- <dosya>     # bu dosyada bu kurulu, S212'de iki kez calisti

Bedeli: `73/40` satırlık bir "save_answer sorgusu düzeltildi" commit'i, içinde **iki
bildirilmemiş davranış değişikliği** taşıdı (boş-havuz koşulsuz cache'lenmesi; her sınava
%15 IRT-ankraj kotası). İkisi de o an **ulaşılamaz** koddaydı, yani sonraki task'ın
JOIN işi onları ilk kez canlandıracak ve suç **o task'a** yazılacaktı.

**Kural:** commit kapsamı bir iddiadır. "Ayıramadım" demeden önce `git stash push --
<dosya>`yı DENE. Süpürme kaçınılmazsa, süpürülen içeriğin **davranış değiştirip
değiştirmediğini** ölç ve commit mesajına yaz — "aynı dosyada olduğu için girdi" yeterli
değil.

---

## MUTASYONUN KENDİSİ DE BİR ÖLÇÜM ALETİDİR (17 Ağu 2026, S223)

Bu dosya "ölçüm aletini doğrula" diyor ve bunu **bulgu üreten** ve **ilerleme ölçen**
aletlere uyguluyordu. Üçüncü boşluk: **mutasyonun kendisi bir alettir ve o da yanılır.**
`failed` almak, testin yük taşıdığını kanıtlamaz — yalnız *o mutasyonun* yakalandığını
kanıtlar.

**Vaka 1 — planda yazılı mutasyon vakumdu.** Task 6'nın M8'i iki UPDATE'ten yalnız
**birini** bozuyordu. Test o gün varlık iddia ediyordu (`[u for u in updates if
"times_asked" in u or ...]`), dolayısıyla hayatta kalan diğer UPDATE hem listeyi dolu
hem prefix'i doğru tutuyordu. Ölçüldü: **M8a ve M8b'nin ikisi de `4 passed`** — mutasyon
hayatta kaldı. Kontrol kolu beklendiği gibi çalıştığı için ölçüm geçerliydi.

**Vaka 2 — "bu assert gereksiz" iddiası da ölçüm ister.** Bir kalite incelemesi
`len(stat_updates) == 2`'yi "tamamen subsumed, silmek kesin iyileştirme" diye raporladı.
Gerekçe: *"koştuğum mutasyonların hiçbirini öldürmüyor."* Bu, iddianın **erişimi** hakkında
değil **koşulan kümenin kapsamı** hakkında bir olgudur. `M-SPURIOUS` (üçüncü bir
`question_statistics` UPDATE'i, `times_asked`/`times_correct` **içermeyen**) ile ölçüldü:
assert varken `1 failed`, silininceye `4 passed` — kaçıyor. Assert korundu.

**Vaka 3 — golden testin KAPSAMI da bir iddiadır.** Task 7'de 7 hayatta kalan mutasyonu
öldüren bir golden WHERE testi yazıldı, ama MATEMATIK + zorluksuz dala kuruldu ve commit
mesajı LaTeX/zorluk dallarının "başka testlerle çivili" olduğunu **ölçmeden** yazdı.
Ölçünce yanlış: her iki ikame assert de **içerik-kör** (`count(needle) == 4` bir sayıdır,
iğne dizesi serbestçe değişir; `"...difficulty_level" in sql` bir kolon adıdır, yerine her
predicate gelebilir). Üç mutasyon hayatta kaldı; en ağırı `contains("x^2")` →
`contains("")`, beş sözel dersin havuzunu **her sınavda boşaltıyor**.

| Adım | Somut kontrol |
|---|---|
| 1 | Mutasyon `failed` mi, `error` mi? `error` = ölçüm **geçersiz** |
| 2 | **Hangi assert** öldürdü? Sayıyı değil, adı kaydet |
| 3 | O assert **tek başına** yük taşıyor mu? Diğerlerini geçici sil, tekrar koş |
| 4 | Mutasyon kümesi **hangi dalları** hiç dokunmuyor? Kapsanmayan dal = ölçülmemiş dal |
| 5 | Ankraj **tekil mi**? Yakın-aynı kopyalar (24 vs 28 boşluk girinti, `>= 50` ⊂ `>= 500`) sessizce yanlış yeri ölçtürür |

**Yan kural — golden'ın başarısızlık çıktısı da tasarımdır.** Tek dize karşılaştırması
pytest'te `Skipping N identical leading characters` + kırpma verir; hangi koşulun değiştiği
anlaşılmaz. `.split(" AND ")` ile liste karşılaştırması `At index 5 diff: ...` verir. Aynı
kesinlik, kullanılabilir çıktı.

**Yan kural — sayaçta yanlış-POZİTİF de "kalan iş" okumasını bozar.** S219 yanlış-sıfırı
tek kabul edilemez hata türü ilan etmişti; tersi de zarar veriyor. `scan_split_accesses.py`
`.values(alan=...)` kwarg'ını **UPDATE hedefinden bağımsız** sayar, yani göç edilmiş DOĞRU
kod da raporlanır. Bu dosyada doğru bitiş koşulu `KWARG=0` değil, `SINIF=0` + KWARG'ların
hedef-doğruluğunun elle teyidi.

**Yan kural — eager-load gerekliliği sorgudan değil TÜKETİCİDEN ölçülür.** Aynı dosyada
aynı desen (`select(Question)`) iki zıt sonuç verdi: Tasks 4/5'te dönen örnekten 12 ve 3
split alan okunuyordu (`selectinload` şart), Task 7'de tek tüketici yalnız `len()` ve `.id`
okuyor (eager-load N/A — eklemek çivilenemez ağırlık olurdu). Sayaç ikisini de `ENTITY`
diye aynı etiketle raporlar; ayrımı yapan şey **tüketici tarafını okumaktır**.

---

## BEKÇİ HAKLI OLABİLİR — "HEP FANTOM" BİR ÖLÇÜM DEĞİLDİR (18 Ağu 2026, S229)

S228 bir bekçiyi ölçüp SKIP etti ve haklıydı (20/20 bulgu HEAD'de zaten vardı). Bu,
sonraki turda sessiz bir alışkanlığa dönüştü: *bekçi kırmızıysa muhtemelen fantomdur.*
S229'da **iki ayrı bekçi** kırmızı verdi ve **ikisi de haklıydı** — çünkü bulgular bu
turun KENDİ kodundaydı:

| Bekçi | Bulgu | Doğru aksiyon |
|---|---|---|
| `reward-hacking-check` | Yeni testte `# pragma: no cover` | **Fix** — ölçüldü ki `.coveragerc:8-10` `*/tests/*` omit ediyor, pragma **kanıtlanabilir no-op**; regex'i geçsin diye yeniden yazmak oyunlamak olurdu |
| `detect-secrets` | Yeni testte DB parolası | **Fix** — DSN `conftest.py`'ye taşındı, env/`.env`'den çözülüyor |

**Ayrım ölçütü tek soru:** *bulgu benim bu turda yazdığım satırda mı?* Evetse SKIP
tartışması yok. Hayırsa (dokunulmamış kod) S228'in ölçülmüş SKIP'i geçerli.

### Bir kez geçmiş olmak güvenlik kanıtı değildir

Aynı DSN satırı **bir önceki commit'te repoya GİRDİ** ve `detect-secrets` onu
görmedi. Sebep ölçüldü: formatter satırı üç satıra sarmıştı, `BasicAuthDetector`'ın
regex'i tek satıra bakıyor. Sonraki turda satır tek satır kalınca yakalandı.

**Kural:** bir sırrın dedektörden geçmiş olması onu güvenli yapmaz — dedektörün o
biçimi görmediğini gösterir. Sır tespiti "geçti mi" ile değil, **grep ile** doğrulanır:
`grep -rn "<sır>" <yol>` ve `git show HEAD:<dosya> | grep -c`.

---

## COMMIT ÇIKIŞ KODU 0 + YENİ HASH ≠ HER ŞEY GİRDİ (18 Ağu 2026, S229)

`L-s224-amend-sessizce-iptal-olur` "amend sessizce iptal olur, HASH'i ölç" diyor.
S229 bir adım ötesini gösterdi: **hash DEĞİŞİR, commit BAŞARILI görünür, ama staged
dosyaların bir kısmı düşmüş olabilir.** Pre-commit'in `[WARNING] Unstaged files
detected` → stash → restore dizisi, bir hook başarısız olduktan sonra dosyaları
**unstaged** bırakıyor; ikinci deneme yalnız kalanları alıyor.

Bu oturumda **iki kez** oldu. İlkinde `5673ef0e9` yalnız test dosyasını aldı, asıl
JOIN fix'i (`api/*.py`) dışarıda kaldı — ve `git log` yepyeni bir hash gösterdiği
için "oldu" sanıldı. Yakalayan şey `git show --stat HEAD` oldu.

**Kural:** commit'ten sonra çıkış kodu VE hash yetmez; **`git show --stat HEAD` ile
NE girdiğini** oku. Beklediğin dosya listesi değilse commit yarımdır.

---

## MUTASYON REDDEDİLMİŞ OLABİLİR — "uygulandı" YAZDIRMAK ÖLÇÜM DEĞİLDİR (18 Ağu 2026, S229)

`L-s223-*` mutasyonun kendisinin bir alet olduğunu söylüyor. Yeni kör nokta:
**mutasyon hiç uygulanmamış olabilir ve harness bunu fark etmez.**

DDL mutasyonu `psql -U kiro2_app -c "ALTER TABLE ... DROP DEFAULT"` ile denendi;
Postgres `ERROR: must be owner of table question_bank` döndü. Script'in bir sonraki
satırı **koşulsuz** `echo "M2 uygulandi"` yazıyordu. Sonuç `4 passed` göründü ve bu
"testler yük taşımıyor" diye okunabilirdi — oysa mutasyon hiç olmamıştı.

**Kural:** mutasyonun uygulandığını **bağımsız olarak ölç**, uygulayan komutun
çıktısına güvenme. Burada doğru ölçüm `information_schema.column_default`
(`true` → `YOK`) idi. Yetki gerektiren mutasyonlarda yetkisi olan yolu kullan —
alembic `downgrade`/`upgrade` hem yetkiliydi hem `downgrade()` yolunu da sınadı.

---

## `server_default` BEYANI DDL'DE OLMAYABİLİR (18 Ağu 2026, S229)

ORM'de `mapped_column(..., server_default="true")` yazması, canlı DB'de o
varsayılanın **var olduğu anlamına gelmez**. `server_default` yalnızca DDL
üretilirken (create_all / migration) kullanılır; tablo onu içermeyen bir yoldan
oluştuysa beyan **fantom** kalır.

`question_bank.is_active` yıllardır `server_default="true"` beyan ediyordu;
ölçünce `information_schema.column_default IS NULL` çıktı ve kolonu atlayan ham
INSERT `NotNullViolationError` verdi. Yani ORM'i atlayan her yazma yolu kırıktı.

**Kural:** bir DB-tarafı varsayılana dayanmadan önce iki ölçüm yap —
(a) `information_schema.columns.column_default`, (b) davranış: kolonu **atlayan**
bir INSERT. Kardeş tuzak: Python-side `default=` INSERT'e kolonu **dahil eder**,
bu yüzden `server_default` gerçek olsa bile hiç ateşlenmez; ikisi aynı yöne bakmalı.

---

## TEST DSN'İ `DATABASE_URL`'E GÜVENEMEZ — SESSİZCE SQLITE'A DÜŞER (18 Ağu 2026, S229)

Canlı-DB testleri için DSN'i env'den çözen bir yardımcı yazıldı ve sırası
`KIRO2_TEST_DSN → KVKK_VERIFY_DSN → DATABASE_URL` idi. **11 test düştü**:
`no such table: information_schema.columns`. Sebep — test koşum ortamı
(`tests/conftest.py` ve bazı test modülleri) `DATABASE_URL`'i
`sqlite+aiosqlite:///:memory:` yapıyor.

Bu, deponun kayıtlı **"testler sqlite `else` dalını koştuğu için yeşildi"**
dersinin aynı sınıfı; orada sessiz (yeşil) hali üretimde ay boyu kırık kod
taşımıştı. Burada kırmızı verdiği için görünür oldu — şans, disiplin değil.

**Kural:** canlı-DB testinin DSN çözücüsü **postgres olmayan DSN'i REDDETMELİ** ve
`pytest.skip` etmeli; sessizce sqlite'a düşmemeli. Alet:
`backend/tests/integration/conftest.py::canli_dsn_cozumle`.

---

## KABUK `cd`'Sİ KALICIDIR — "0 collected" BULGU DEĞİL ALET ARIZASI (18 Ağu 2026, S229)

Bir düzenlemeden sonra `pytest tests/integration/... ` **`collected 0 items`**
verdi. İlk okuma "dosyayı bozdum" idi. Gerçek sebep: önceki bir komutta
`cd /c/Users/husey/kiro2` çalıştırılmıştı ve Bash oturumunun cwd'si **kalıcı**;
yol depo kökünün `pytest.ini`'sine çözülüyordu. `backend/`'den koşunca 8/8 PASS.

**Kural:** beklenmedik "0 test / 0 bulgu" gördüğünde önce `pwd`. Bu, bu dosyadaki
"ölçüm aletini doğrula" ailesinin en ucuz üyesi — ve kontrol kolu tek komut.

---

*Oluşturulma: 14 May 2026 (Session 156, Faz 0.8). Bir sonraki audit hatasında bu tablo güncellenir.*

---

## GIT BASH MUTLAK YOLU YENİDEN YAZAR — "dosya yok" bir bulgu değil (18 Ağu 2026, S229-B)

`verification.md` "bash `/tmp` = MSYS temp, Python `/tmp` = `C:\tmp`" diyor. Aynı
mekanizmanın **container/uzak-sistem** ayağı bu turda ısırdı:

    docker exec kiro2-backend grep -n '...' /app/core/advanced_rate_limiter.py
    -> grep: C:/Program Files/Git/app/core/advanced_rate_limiter.py: No such file

MSYS, `/` ile başlayan argümanı **Windows yoluna çevirdi** ve container'a hiç
ulaşmayan bir yol gönderdi. Hata mesajı "dosya yok" diyor — `docker cp` başarısız
sanılabilirdi; oysa cp başarılıydı.

**Kural:** Git Bash'te **mutlak yol içeren her dış-araç çağrısında**
(`docker exec`, `docker run -v`, `psql -f`, `wsl`) yol dönüşümünü sorgula.
Çözüm `MSYS_NO_PATHCONV=1 <komut>`. Container yolu içeren bir komuttan gelen
"dosya yok" **önce yol-dönüşümü kontrolü** ister, sonra teşhis.

## SKIP BİR MUAFİYET DEĞİL, ÖLÇÜLMÜŞ BİR ERTELEMEDİR (18 Ağu 2026, S229-B)

Pre-commit kapısı kırmızı verdiğinde `SKIP=<hook>` yazmak ucuzdur ve bu depoda
sessizce alışkanlığa dönüşebilir (S215 bunu "sonra ayrı iş olarak kaydet" diye
kısmen ele almıştı). Eksik olan şey **kararın kendisinin bir ölçüm olduğu**.

Üç ölçüm, hepsi gerekli:

| # | Soru | Komut |
|---|---|---|
| 1 | **Benim kodum** temiz mi? | Kapının sürümüyle, **gerçek yolda**, ihlali `--ignore` ile dışlayarak koş → "All checks passed" olmalı |
| 2 | **Kontrol kolu**: ben mi getirdim? | `git show HEAD:<dosya> \| grep -n '<ihlal>'` → HEAD'de de varsa dokunulmayan borç |
| 3 | **Yaygınlık**: doğru katman hangisi? | `ruff check --select <kural> backend/{core,api,services}` → sistemikse dosya-başına kapatmak yanlış |

S229-B'de sırasıyla: temiz · `HEAD:369`'da birebir var · **132 kalem** → karar
`SKIP=ruff` + gerekçe commit mesajında + ayrı açık iş (Y8).

Biri eksik olsaydı karar savunulamazdı: (1) yoksa kendi borcunu gizlersin,
(2) yoksa "ben mi getirdim" bilinemez, (3) yoksa tek dosyayı düzeltip sistemik
borcu görmezden gelirsin.

## YARIM COMMIT'İN ARTIĞI ÇALIŞAN AĞAÇTA SESSİZCE BEKLER (18 Ağu 2026, S229-B)

`L-s229-commit-yarim-gidebilir` "commit anında `git show --stat` ile ölç" diyor.
Eksik yarısı: o an **kaçırılırsa** artık dosya kalıcı olarak çalışan ağaçta kalır.

Vaka: `1dd12579d` (A1, sürüm matrisi) yalnız `backend/requirements-minimal.txt`'i
commit'ledi; `backend/requirements.txt` aynı pinlerle **kirli kaldı** ve günler
sonra, tamamen başka bir işin push'undan sonra fark edildi.

Neden görünmedi: bu depoda **~3400 takipsiz dosya** var, `git status` çıplak
haliyle kullanılamaz — artık dosya gürültüde kaybolur.

**Kural:** oturum kapanışında takipsiz gürültüyü **filtreleyerek** takipli-kirli
sayısını ölç (porcelain çıktısında baş harfi `M` olan satırlar). 0 değilse her
birinin sahibini bul: ya bu turun işi, ya devralınan, ya da bir yarım commit'in
artığı.
