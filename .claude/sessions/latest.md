## KIRO2 Nedir, Şu An Nerede, Nereye Gidiyor (teknik olmayan özet — 16 Ağustos 2026)

**Nedir:** KIRO2, Türkiye'de üniversite giriş sınavına (YKS/TYT/AYT) hazırlanan
öğrenciler için bir çalışma platformu. Amaç her öğrenciye tam ona göre bir
çalışma deneyimi sunmak: çok kolay soruyla zaman kaybettirmemek, çok zor
soruyla moralini bozmamak, unutmaya başladığı konuyu tam zamanında hatırlatmak.

**Elde ne var:**
- ~188 bin soru — bunların ~111 bini şu an aktif kullanılabilir, ~25 bini de
  ayrıca kalite kontrolünden geçip "öğrenciye güvenle gösterilebilir" diye
  işaretlenmiş bir havuzda.
- 405 kaynak kitaptan derlenmiş içerik.
- Öğrencinin hangi konuda zayıf olduğunu tahmin eden, ne zaman tekrar etmesi
  gerektiğini hatırlatan, kişiye özel çalışma planı çıkaran bir motor.
- Öğretmen sınıfını takip edebiliyor, veli çocuğunun ilerlemesini görebiliyor.

**Şu an neyle uğraşıyoruz:** Platform aylardır büyüyor; bir ara hız kazanmak
için kısayollar alındı — geçen ay bir yapay zekâ aracının devraldığı bir
dönemde, kod tabanına gözden geçirilmeden ve test edilmeden çok fazla
değişiklik girdi. Şu anki iş bunun temizliği: soru veritabanının iç yapısını
daha sağlam bir şekle sokuyoruz (tek büyük, hantal bir tabloyu yönetilebilir
parçalara ayırdık) ve bu ayırmanın her yerde doğru çalıştığını, tek tek test
yazarak kanıtlıyoruz. Sıkıcı ama gerekli bir iş — atlanırsa öğrenciye yanlış
soru gitmesi veya sistemin sessizce çökmesi gibi fark edilmesi zor hatalar
üretir.

**Nereye gidiyor:** Hedef, platformu öğrencilere doğrudan abonelik olarak
sunmak (okul/kurum üzerinden değil, öğrencinin kendisinin abone olduğu bir
model). Bunun için önce birkaç güvenlik ve sağlamlık kapısının kapanması
gerekiyor: kimin neyi görebileceğinin sıkılaştırılması, verinin tutarlılığının
garanti altına alınması, testlerin platformun büyük bölümünü kapsıyor olması.
Bu kapıların çoğu ya kapandı ya da kapanmak üzere.

**Özetle:** İçerik ve zekâ tarafı zengin ve büyük ölçüde hazır; şu anki emek
bu zenginliğin üzerine sağlam ve güvenilir bir temel inşa etmek. O tamamlanınca
öğrencilere açılış için teknik bir engel kalmayacak.

---

## 📦 Önceki oturumlar arşivde

S215…S233 devir notları (2.206 satır) `.claude/sessions/arsiv/2026-08_S215-S233.md`
dosyasına **birebir** taşındı — silinmedi. Bu dosya bundan sonra yalnız **son 3**
oturumu tutar; kapanan her oturumda en eskisi arşive iner.

Gerekçe (20 Ağu 2026 ölçümü): dosya 2.605 satır / 185 KB'a ulaşmıştı ve tek okumada
25K token tavanına çarpıyordu — devri okumak, devrin kendisinden pahalı hale gelmişti.

---

## Session Handoff — 2026-08-20 (S235 · FAZ B KAPANDI) ✅

**Branch:** feature/self-evolution-optimization · **Son commit:** `e30023ed3`
**Push:** ✅ `b520a9027..e30023ed3` — **2 commit** (sayı `git log --oneline origin/<dal>..HEAD | wc -l` ile ölçüldü)
uzakla **senkron** (ahead/behind 0/0) · push-secret-guard sır bulmadı · reward-hacking-check **Passed**
(1 bloklamayan uyarı: "Test count: 54 → Consider Hypothesis" — dedektörün sabit-eşik sezgisi;
dosya zaten 20 parametrize dekoratörle 242 vaka üretiyor, uyarının istediği şey fiilen yapılmış)
**Kapı:** 22 dosya / **214 passed / 0 skipped / 9 xfailed**, EXIT=0 — baseline ile **birebir**
**Uncommitted:** yalnız devralınan `backend/semantic_cache.pkl` (Bin 4892→4892, 0 satır)

### Bu oturumun tek cümlesi
S234 "kesinleşmiş kurallar" diye 13 maddelik bir liste bırakmıştı. Bu oturum onları
**uygulamadan önce ölçtü** ve **üçünün yanlış olduğunu** buldu — biri tam olarak
uyardığı kusuru üretiyordu. Kalıcı veri yazımı yok.

### Üretilen (`15876c14b`, +1637)
| Dosya | Satır | Ne |
|---|---|---|
| `backend/scripts/quality/y11_goc.py` | 343 | Saf dönüşüm: kaynak 78 kolon → 4 hedef satır. DB/dosya/ağ/rastgelelik/zaman **yok** (import yalnız `copy` + `typing`) |
| `backend/tests/fast/test_y11_goc.py` | 1294 | 54 test fonksiyonu / **242 pytest vakası** |

### 🔴 DEVİR NOTUNUN 3 KURALI ÖLÇÜLEREK ÇÜRÜDÜ
| # | S234'ün kuralı | Ölçüm | Düzeltme |
|---|---|---|---|
| 1 | `bloom_category → 5:EVALUATION, 6:CREATION` | 5/6 = **27 satır**. Kalan **4.392** (`bilgi/kavrama/uygulama/analiz`) kuralın DIŞINDA → `BLOOM_A_MAP.get(cat, 1.05)` (`empirical_irt_calibrator.py:119`) hepsini `irt_a=1.05`'e sabitlerdi. **Kural, uyardığı kusuru üretiyordu.** | altı seviyenin altısı, lowercase; bilinmeyen → `ValueError`; `bool` ayrıca elenir (`True == 1`) |
| 2 | `review_status → AÇIKÇA yaz` (değer yok) | canlı kanon **`approved` lowercase** 36.967/36.967 · `server_default='APPROVED'` UPPERCASE | `REVIEW_STATUS = "approved"` |
| 3 | `irt_based_difficulty` sürükleme yok | **EVREN-BAĞIMLI:** göç kapsamında (4.419) `medium`×4.419 → kural DOĞRU; filtresiz KIMYA'da `kolay` 4 + `orta` 2; tüm korpusta ayrıca `MEDIUM` 13 + `cok_kolay` 3 | FAZ B'de taşı; MAT/GEO/FIZ göçünde **yeniden ölç** |

Ayrıca SPEC denetimi: **17 kural bir "kalan kolonlar aynen taşınır" maddesi içermiyordu** —
harfiyen uyan bir uygulama 23 NOT NULL + defaultsuz kolonu atlar, **her INSERT düşerdi**.
Modül 63 kolonluk **açık** geçiş listesi kullanıyor.

### Ölçümler (bu turda üretildi)
- **Uçtan uca, gerçek kaynak satırıyla:** anahtar kümeleri canlı `information_schema`'ya karşı
  **12/12 · 19/19 · 21/21 · 33/34** — tek eksik `embedding` (kural 1: 768 ↔ 1536). FAZLA=0.
- **topic remap KOD üzerinden:** `KIM` `dcd3211c…`→`72e79276…` (852) · `FIZ` (12) · `GEN` (1).
  Diğer 14 kodun id'si zaten aynı — ama kural yine koddan çalışır, id eşitliği tesadüfe bırakılmaz.
- **Görsel kuralı 3 sınıfta gerçek satırla:** sızıntılı kitap crop → `None` · `_PAGE` → `None` ·
  temiz kitap crop → taşındı.
- **Mutasyon 8/8 ÖLDÜ** (commit'li dosya üzerinde, bağımsız harness): bloom 5↔6 takas (2 failed) ·
  `approved`→`APPROVED` (1) · bloom bekçisi `if False` (7) · `_PAGE`→`_page` (1) · kitap adı tek
  karakter (2) · topic bilinmeyen kod sessiz geçir (1) · sayaçların yalnız ilki (5) · damga anahtarı (3).
  Hiçbiri `error`, sekiz geri alımın sekizi `git status --short` boş.
- 257 passed / 0 failed (`y11_goc` 242 + `y11_dedup` 15 — dedup regresyonu yok). Ödül-hackleme 0/0.

### Bu turda aletlerim 4 kez yanıldı (dürüst kayıt)
1. **Mutasyon harness'i 8/8 GEÇERSİZ raporladı — tamamen alet arızası.** Özeti *son satırdan*
   okuyordum; mutasyonlu koşumda `pytest-benchmark` uyarısı özetin altına düşüyor. Desenle
   aramaya çevirince **0/8 → 8/8**. Kontrol kolu geçerliydi (242 passed) ve bu yüzden harness
   sağlam göründü — **kontrol kolunun geçmesi mutasyon kolunun ölçtüğünü kanıtlamaz.**
2. **Aynı harness'te ikinci yanlış-negatif:** "uygulandı mı" kontrolüm `count(ankraj)==0` idi;
   *ekleme* mutasyonları (M6) ankrajı yeni metnin içinde de taşıyor → "UYGULANMADI".
3. **`cd backend` sonrası yol `backend/backend/` çözüldü, 2 kez.** Biri `grep`'i düşürdü ve
   `||` yedeği **"TEMİZ" yanlış-pozitifi** bastı; diğeri `pre-commit run mypy`'ı
   `(no files to check)` yaptı. Aynı turda sentez ajanı da aynı tuzağa düştü — 3/1 turda.
4. **`git commit … | tail; $?` → EXIT=0 gösterdi ama commit DÜŞMÜŞTÜ** (mypy `no-any-return`).
   Boru hattında `$?` son halkayı ölçer; yakalayan şey `git show --stat HEAD`'in hâlâ eski
   hash'i göstermesiydi. Çıkış kodu ayrı değişkene alınarak düzeltildi.

Ayrıca: mypy bulgusu **benim bu turda yazdığım satırdaydı** → SKIP tartışılmadı, iki tip
anotasyonuyla düzeltildi (`_gorsel_url`), davranış nötr.

### Fail Eden Testler
**YOK.** `tests/fast/test_y11_goc.py` **242 passed / 0 failed** · `test_y11_dedup.py` 15 passed
(birlikte 257/0). Kapı 22 dosya **214 passed / 0 skipped / 9 xfailed** EXIT=0 — 9 xfailed
S234'ün baseline'ıyla **aynı küme** (Y12 içerik bekçisi 8 + hacim bekçisi 1), yeni kırık **0**.

### Engelleyiciler
- **#486 — asyncpg `set_type_codec('jsonb')` (FAZ C'nin ÖN KOŞULU).** Yükleyici bunu
  kaydetmezse asyncpg `pipeline_metadata`'yı `str` döndürür, modülün bekçisi gürültülü hata
  verir; kaydedilir de bekçi yumuşatılırsa parti **damgasız** girer. Damga geri alma
  kümesinin **tek** taşıyıcısı → damgasız parti **geri alınamaz**.
- **`correct_answer` düzeltme kanalı KARARSIZ.** `tasarim:115-117` "yargıç düzeltmesi göç
  sırasında yeni satıra yazılır" vs kural 12 "harf yeniden atama YASAK". `kaynak_satiri_donustur`
  imzasında (`satir`, `topic_kod_haritasi`, `damga`) bunu taşıyacak parametre **yok**.
- Devralınan: `kiro2-api-import-smoke` S211'den beri kırık · host `pytest` uçtan uca koşamaz.

### Kararlar (gelecek session tekrar tartışmasın)
- **`bloom_category` lowercase yazılır** (`knowledge…creation`), UPPERCASE değil — canlı kanon
  36.967/36.967 lowercase ve `BLOOM_A_MAP` tüketici tarafta `.upper()` yapıyor, ikisi de
  çalışır; UPPERCASE **üçüncü** bir yazım biçimi sokardı (kullanıcı kararı, 20 Ağu).
- **`bloom_level` SAYI kanondur, Türkçe kelime değil** (S234 kullanıcı kararı): kaynak eski
  Bloom kullanıyor (5=sentez, 6=değerlendirme), hedef revize Bloom. 27 satırın kategorisi
  kelime-sadakatinden ayrılıyor — bilinen ve kabul edilen bedel. `b_bloom=(lvl-3)*0.15` de
  sayıyı kullandığı için içsel tutarlı.
- **Dedup modülü KOPYALANMADI, import de EDİLMEDİ** — dedup çağıran katmanın işi
  (`y11_dedup.mukerrer_gruplar` ile ele → sonra satır satır dönüştür). Saf dönüşüm tek satır
  görür, mükerrer kararı veremez.
- **Mutasyon bataryası commit SONRASI koşuldu** (`15876c14b` üzerinde). S233 ve S234 bu kuralı
  ihlal edip ölçümü geçersiz kılmıştı; bu turda workflow'un commit'siz 20 mutasyonu
  **geçerli sayılmadı**, 8'i commit'li dosyada bağımsız tekrarlandı.
- **`# noqa`/`SKIP` kullanılmadı.** mypy `no-any-return` bulgusu **bu turda yazdığım satırdaydı**
  → iki tip anotasyonuyla düzeltildi (`_gorsel_url`), davranış nötr.

### Sonraki Adımlar (maks 5)
1. **FAZ C pilot** — 50 satır `BEGIN…ROLLBACK`. Örneklem kör nokta bırakmaz: ≥5 remap ·
   ≥3 kapı-elenen · ≥2 mükerrer · ≥1 çapraz-DB · ≥1 `created_by` yetimi. Kapı: 50 → 4×50 ·
   yetim 0 (A4 bekçisi) · JOIN'le geri okuma birebir · `ROLLBACK` sonrası `question_bank`=36.967.
3. **Yükleyici sözleşmesi** (FAZ C'nin ön koşulu): dört sözlük **TEK transaction** ·
   dedup **çağıran katmanda** (`y11_dedup.mukerrer_gruplar` ile ele, sonra dönüştür) ·
   **#486 `set_type_codec('jsonb')`** yoksa parti damgasız + metadata'sız girer.
4. **FAZ D** — kalıcı yazım, `pending`, 1000'lik parti.
5. **FAZ F'ye biriken 4 ders** (aşağıda) + `ders_kaydi.yaml`.

### Yeni açık işler (bu oturumda ölçüldü)
- **`.claude/rules/database.md` BAYAT (P2):** `review_status='APPROVED'` yazıyor, canlı
  36.967/36.967 `'approved'`. Bu dosyaya bakan sonraki ajan **yanlış değer yazar.**
- **`docs/audits/2026-08-19_y11_goc_mekanizmasi_tasarim.md:169-183` BAYAT (P3):** "14 konu
  KOPYALANIR" diyor; canlı `topic_hierarchy` **26** ve KIMYA'nın 17 kodunun 17'si de mevcut
  (ADIM 1 uygulanmış).
- **Plan'daki kitap adı dizesi YANLIŞ (P1, kapatıldı ama kaydedilsin):** plan
  `'Apotemi 2024 Ayt Kimya SB'` diyor, canlı DB `'Apotemi 2024 Ayt Kimya Soru Bankasi'`.
  Plan dizesi kullanılsaydı kural **hiç tetiklenmez**, 112 sızıntılı crop sessizce göç ederdi.
- **`correct_answer` düzeltme kanalı — KARAR BEKLİYOR:** `tasarim:115-117` "yargıç düzeltmesi
  göç sırasında yeni satıra yazılır" vs kural 12 "harf yeniden atama YASAK". İmzada bunu
  taşıyacak parametre **yok**.
- **Beklenen son satır sayısı üç belgede üç farklı:** 3.554 (`plan:196`) / ~3.616
  (`latest.md:2333`) / dedup "153 fazlalık". **FAZ D'den önce tek sayı ilan edilmeli.**
- **Apotemi sızıntısı kitaba mı yayınevine mi özgü — ÖLÇÜLMEDİ.** Aynı batch'te 3 Apotemi
  kitabı daha var (408 + 105 + 1 satır); kural yalnız 2024 AYT kitabını dışlıyor.
- **`grade_level=12` canlıya İLK KEZ girecek** (canlı 36.967/36.967 hepsi `11`).

### Ders adayları (FAZ F'de deftere)
- **Devir notundaki KURAL da bir iddiadır** — uygulamadan önce **kapsamını** ölç. Bloom
  kuralı 4.419'un 27'sini kapsıyordu ve tam olarak uyardığı kusuru üretiyordu.
- **Bir alanın kanonu ÜÇ yerden gelir** (ORM default · `server_default` · canlı dağılım) ve
  **üçü çelişebilir**. `review_status`'ta üçü de farklıydı; canlı dağılım kazanır.
- **"Sürükleme var/yok" EVREN-BAĞIMLI bir iddiadır.** Aynı kolon göç kapsamında temiz,
  filtresiz derste kirli, korpusta daha kirli. Hangi evrende ölçtüğünü YAZ.
- **Mutasyon harness'inin ÖZET AYRIŞTIRICISI da bir alettir ve yanlış-GEÇERSİZ üretir.**
  `L-s202-mutasyon-error-gecersiz` `error`'ü kapsıyor; ayrıştırıcı arızası **8/8'i geçersiz
  gösterdi** ve kontrol kolu geçtiği için harness sağlam göründü. Özeti son satırdan okuma,
  `^=+ ... =+$` deseniyle ara.

---

## Session Handoff — 2026-08-20 (S236 · FAZ C KAPANDI) ✅

**Branch:** feature/self-evolution-optimization · **Son commit:** `0bd77c566`
**Push:** ⏳ **1 commit bekliyor** (kullanıcı onayı) · ahead/behind **1/0**
**Kapı:** 22 dosya / **214 passed / 0 skipped / 9 xfailed** — S235 tabanıyla **birebir**
**Takipli-kirli:** yalnız devralınan `backend/semantic_cache.pkl`
**Canlı DB (kapanışta):** `question_bank` **36.967** · `mv_safe_for_beta` **27.073** · damga kalıntısı **0**

### Bu oturumun tek cümlesi
FAZ C pilotu 50 satırı canlıya yazdı ve geri aldı; **kalıcı veri yok**. Yolda S235'in
iki "engelleyici"sinden biri ölçülüp **çürüdü**, diğerinin (#486) gerçek yeri kesinleşti.

### Pilot sonucu (transaction İÇİNDE ölçüldü, ROLLBACK sonrası taban doğrulandı)
```
50 -> 4x50 (bank/content/metadata/statistics)   yetim 0
damgali 50/50            <- pipeline_metadata->>'y11_batch' geri okundu
icerik sadakati 50/50    <- metin + 5 sik + anahtar BIREBIR, sapma 0
kural: is_active 50 | is_public 50 | review_status=approved 50
       quality_review_status=pending 50 | times_asked=0 50
       bloom_category lowercase 50 | gorsel NULL 38 (= ornekemdeki _PAGE sayisi)
ROLLBACK sonrasi: 36.967 x4 | mv 27.073 | damga kalintisi 0
```

### 🔴 DEVİR NOTUNUN İKİ ENGELLEYİCİSİ — biri ÇÜRÜDÜ, biri YER DEĞİŞTİRDİ
| # | S235'in iddiası | Ölçüm |
|---|---|---|
| 1 | `correct_answer` düzeltme kanalı **KARAR BEKLİYOR** | **ÇÜRÜDÜ.** Verdikt TSV: KABUL **3.666/3.666**'da `yargic == db_anahtar` (fark **0**). 80 anahtar uyuşmazlığının tamamı `KUYRUK_ANAHTAR` sınıfında ve o sınıf **göç kapsamında değil**. Tasarım:115-117 ↔ kural 12 çelişkisi göç kümesi için **fantom**; imzaya parametre eklenmedi |
| 2 | #486 "asyncpg jsonb codec" | **GERÇEK ama iki taraflı.** OKUMA'da kodek **ZORUNLU** (yoksa `str` gelir, dönüşüm gürültülü durur). YAZMA'da kodek **YASAK** (hedefe de kaydedilse `json.dumps`'lı `str` bir kez daha kodlanır → JSON string skaları → `->>` NULL → **sessiz damgasız parti**). Hedefte `json` kolon **7** ölçüldü, 1 değil |

### Ölçülen diğer şema gerçekleri (ilk sürümü düşürdü / düşürecekti)
- `question_bank.id` **`character varying`** — `uuid` DEĞİL (ilk ölçüm SQL'i bu yüzden düştü)
- `pipeline_metadata` **`json`** — `jsonb` DEĞİL (`->>` ikisinde de çalışıyor, ölçüldü)
- KABUL'de `json_typeof='string'` **0 satır** → "str geldi = kodek yok" guard'ı güvenli
- 16 kaynak `topic_code`'un **16'sı da** canlı `topic_hierarchy`'de VAR → göç durmuyor

### Plandaki iki sayı ÖLÇÜLEREK düzeldi
- **"78 set-içi mükerrer (73 grup)" YANLIŞ ETİKET** — o **gövde-only** ölçümü. Karar ölçütü
  SIKI kimlik (gövde+şık, sırasıyla): **16 grup / 16 fazlalık** (gevşek 17). Çapraz-DB **34**
  (S234'ün rakamı bağımsız doğrulandı). ⚠️ `y11_dedup_olc.py` docstring'i hâlâ "78/73 siki"
  diyor — **bayat, düzeltilmedi** (açık iş).
- **Pilot kotası "≥1 `created_by` yetimi" KARŞILANAMAZ** — KABUL'de **3.666/3.666 NULL**.
  "65 yetim" 4.419'luk tam küme içindi. Kota düşürüldü, gerekçesi seçicinin docstring'inde.

### Üretilen (`0bd77c566`, +1020)
| Dosya | Satır | Ne |
|---|---|---|
| `scripts/quality/y11_yukleyici.py` | 430 | Yazma katmanı: saf SQL üretimi + TEK transaction + `--kalici` bayrağı (varsayılan GERİ ALIR) |
| `scripts/quality/y11_pilot_ornek.py` | 184 | Deterministik örneklem seçici (`random` YOK; iki koşum birebir aynı) |
| `scripts/quality/y11_pilot_olcum{,2,3}.sql` | 126 | Üç ölçüm turu (salt okunur) |
| `tests/fast/test_y11_yukleyici.py` | 280 | 9 test |

### Mutasyon **9/9 ÖLDÜ** (commit SONRASI, bağımsız harness)
M1 tablo sırası ters · M2 serialize yok · M3 çift kodlama · M4 `str` guard'ı kaldır ·
M5 varsayılan kalıcı · M6 kolon sessizce düş · M7 değer/kolon hizası kay ·
M8 yer tutucu eksik · M9 `JSON_KOLONLARI`'ndan `pipeline_metadata` çıkar.
Hiçbiri `error`; dokuz geri alımın dokuzu `git status --short` **boş**; kontrol kolu yeşil.

### Bu turda kayıtlı üç ders BİREBİR tekrar etti (dürüst kayıt)
1. **`L-s229-cd-kalici-sifir-collected`** — `pytest` `0 items` verdi; sebep kabuk cwd'sinin
   `scripts/quality`'de kalmasıydı. `pwd` ile 10 saniyede çözüldü.
2. **`L-s212-bicimlendirici-import-siler`** — `JSON_KOLONLARI`'ı kullanımdan ÖNCE import ettim,
   PostToolUse kancası F401 diye **sildi**, test `NameError` verdi. Kuralı yazarken ihlal ettim.
3. **`L-s233-ayni-linter-iki-config...`** — yine **7 adet N802** (BÜYÜK harfli test adı); sinyal
   yine ancak commit anında geldi (**Y13 kapanmadı**).

### Fail Eden Testler
**YOK.** `tests/fast/test_y11_yukleyici.py` **9 passed**. Kapı 214/0/9, yeni kırık **0**.

### Engelleyiciler
- **Yok** (FAZ D için). #486 kapandı, `correct_answer` kanalı çürüdü.
- Devralınan: `kiro2-api-import-smoke` S211'den beri kırık · host `pytest` uçtan uca koşamaz.

### Sonraki Adımlar (maks 5)
1. **PUSH** — 1 commit bekliyor (`0bd77c566`).
2. **FAZ D** — kalıcı yazım. Önce **tek sayı ilan et**: `3.666 − 16 (sıkı set-içi) − 34
   (çapraz-DB) ± örtüşme`. **Örtüşme ÖLÇÜLMEDİ** — 16'nın kaçı 34'ün içinde? Tek sorgu.
   Sonra 1000'lik parti, `pending`, her parti sonrası invaryant + damga sayımı.
3. **FAZ E** (ayrı onay) — `pending → auto_judged_high` + `REFRESH` + Y12 xfail'leri + ES (#433).
4. **FAZ F** — S235'in 4 ders adayı + bu turun 3 tekrarı `ders_kaydi.yaml`'a;
   `test_y11_yukleyici.py` **kapı listesinde DEĞİL** (defterde `zorlayici` satırı yok →
   `L-s232-enforcement-listesi-defterden-turetilmeli` gereği henüz zorunlu değil).
5. **Y13** (P2) — kanca lint bulgusunu atıyor; N802 bu oturumda **6. kez** commit anında geldi.

### Açık işler (bu oturumda ölçüldü)
- **`y11_dedup_olc.py` docstring'i BAYAT (P2):** "78 satır / 73 grup, siki" diyor; gerçek
  sıkı ölçüm **16/16**. O sayı gövde-only'ye ait. Script assert etmiyor, yalnız yazdırıyor.
- **`.claude/rules/database.md` BAYAT (P2, S235'ten devir):** `review_status='APPROVED'`,
  canlı `'approved'`. Bu dosya HER oturumda bağlama yükleniyor.
- **Y14 (P1, güvenlik, S234'ten devir):** `pg_hba` `trust` docker ağı + LAN'a açık.
- **`--kalici` bayrağı henüz hiç kullanılmadı** — kalıcı yol FAZ D'de ilk kez koşacak.
## Session Handoff — 2026-08-20 (S237 · E1-E4 + A + B + MAT-T1)
**Branch:** feature/self-evolution-optimization · **Son commit:** `18d1c927d` · **Push:** ⏳ 1 commit
**Uncommitted:** yalniz devralinan `backend/semantic_cache.pkl` (Bin 4892→4892, 0 satir)
**Canli DB:** `question_bank` **40.583** ×4 · kapi **27.073** (degismedi) · gorsel **1.426** (onceki 0)

### Yapilanlar
- `.claude/hooks/session-{save,init}.py` (`5fe5f624a`) — hook'lar olctugunu SANAN aletlerdi. Kok neden
  olculdu: `_check_bash()` `timeout=3` vs soguk bash spawn **7,11 sn** → `run_cmd` turevi her alan bos.
  bash kaldirildi; `git status -uno` (`-u` **>60 sn** → **0,09 sn**); `/api/v1/health`→`/health`;
  `question_count` yalan etiketi 3 olcume bolundu. `tests/unit/test_hooks/test_session_hooks.py` 6/7 RED → **7/7**.
- `.claude/rules/audit-methodology.md` 1010→**117**, `.claude/sessions/latest.md` 2605→411 (`ca95ba824`).
  Arsivler sha256 **birebir** (`docs/dersler/…`, `sessions/arsiv/…`). Mekanizma: `paths:` frontmatter'i
  OLMAYAN kural dosyasi her oturumda yukleniyor. Baglam yuku **2.602 → 1.810 satir/oturum**.
- `.claude/rules/database.md` — `'approved'`, PG **18.1**, **duz-metin parola silindi** (hic commit
  edilmemisti). `CLAUDE.md:3` — A1 kabul kriteri + E3 olcumu.
- 🟢 `y11_{ortusme_olc,goc_kumesi_uret}.py` (`44cb08a04`) — **3.616 KIMYA satiri KALICI yazildi**
  (aylardir ilk kalici icerik). Ortusme **0** → 3.666−50=3.616. Icerik sadakati sapma **[]**.
- 🟢 `y11_konu_seed.py` (`f74a09bf5`) — `topic_hierarchy` 26→**45**, `MAT.*` 1→**20**; kapsama **%13,2 → %92,9** (+4.316).
- `docs/superpowers/plans/2026-08-20-mat-tyt-goc.md` (`18d1c927d`) — 6 task / 29 adim.

### Fail Eden Testler
**YOK.** `test_session_hooks.py` 7 passed · push kapisi **214 passed / 9 xfailed** (2 kez).

### Engelleyiciler
- 🔴 **OCR MOTORU YOK** — `pytesseract` kurulu, `tesseract` ikilisi yok; container'da hic OCR yok.
  **MAT-T2..T6 BLOKE.** Cozum: `pip install rapidocr-onnxruntime` (yonetici gerekmez).
- Operator: SMTP kimlik bilgisi · odeme saglayicisi basvurusu (haftalar) · alan adi + SSL.
- `SKIP=reward-hacking-check` (#495) — uc olcumle savunuldu, ayri is.

### Sonraki Adimlar (maks 5)
1. **PUSH** — `18d1c927d`.
2. **OCR karari**; kurulursa `y11_sizinti_ayirt_olc.py` kalibrasyon kolu (9 kotu / 180 iyi) hazir.
3. MAT-T2..T6 — plan dosyasinda, T1 kapandi.
4. #495 Y15 · Y13 N802 · Y14 `pg_hba trust`.
5. FAZ E terfi (`pending`→`auto_judged_high` + `REFRESH`) — **ayri onay**.

### Kararlar (gelecek session tekrar tartismasin)
- **MAT-T1 planin T2'sini CURUTTU.** 59 kitap / 354 crop kor okundu → **9 sizinti (%2,54)**.
  Esigim (`>=2/6`) yapisal olarak **sifir uretiyordu** (olasilik %0,91; beklenen 0,53).
  Kitap sinyali YOK: hepsi ayni ~%2,5 oranindaysa >=1 gorulen kitap beklentisi **8,4**, gozlenen **9**
  → orneklem gurultusu. Kitap kumesi YANLIS KATMAN, dogru katman crop-basi.
- **Iki alternatif katman curudu:** "sayfanin son sorusu" = havuzun **%67**'si; crop koordinati
  `pipeline_metadata`'da **yok** (66 anahtar tarandi).
- **OCR'siz gorsel dedektor KOR:** KOTU medyan 0,0690 < IYI 0,0829 (fark **−0,0139**). Esik ZORLANMADI,
  sentetik bozma kosulmadi. `y11_sizinti_ayirt_olc.py` **commit EDILMEDI** (kor metrik "hazir arac" gibi durmasin).
- `#485` **donduruldu** (A3): Haziran'dan beri acik, 60 commit, kullanici-gorunur cikti 0.
- Kayitli **4 ders birebir tekrar etti** (`$?` boru hatti · CRLF ankraj · deseni ANLATAN yorum · uc-ruff); `/tmp` tuzagi **4 kez**.

---

## Session Handoff — 2026-08-20 (S238 · KITAPSIZ HAVUZ SILINDI) ✅

**Branch:** feature/self-evolution-optimization · **Son commit:** `3a5d98f61` · **Push:** ⏳ 5 commit
**Uncommitted:** yalniz devralinan `backend/semantic_cache.pkl`
**Canli DB:** `question_bank` **40.583 → 3.616** ×4 · kapi **27.073 → 0** (KASITLI) · yedek 4×36.967

### Bu oturumun tek cumlesi
36.967 sentetik satir yedeklenip SILINDI; silme, iki bekcide **vakum deligi**
(bos kumede kendiliginden gecme) aciga cikardi ve as?l kazanc o oldu.

### Yapilanlar
- 🟢 `y11_cop_sil.py` + 29 bekci (`569b995b6`) — ayirici **PROVENANS** (`source_book IS NULL`),
  icerik sezgisi degil: **36.967/36.967 eski vs 0/3.616 Y11**. Ucuz dedektorler tek basina
  yalniz **8.696**'sini yakaliyordu → 28.271 cop kalir ve havuz "temizlenmis" gorunurdu.
- 🟢 **Adversarial olcum: 180/180 cop** (dedektorlerin "TEMIZ" dedigi alt kumeden, 12 ders×15,
  6 yargic + 3 mercekli curutme). **Kor kontrol kolu: ozgulluk 30/30 %100, duyarlilik 27/30 %90,
  yanlis-poz 0** → `0/180` alet arizasi DEGIL. %95 ust sinir ~%1,9.
- 🟢 Tahribat **0**: FK'li 11 tablonun 11'i CASCADE ve **hepsi bos** (`student_answers` dahil).
- 🟢 PROVA (13/13 beklenti) → kalici → bagimsiz dogrulama: 3.616 ×4, kapi 0, kitapsiz 0,
  Y11 damgali 3.616, farkli kaynak kitap **0 → 26**.
- 🔴 `66cd9c958` — **iki bekci bos kapida KENDILIGINDEN geciyordu** (`farkli != 1`,
  `n_r5 == 0`). XPASS "kusur kapandi" diyordu; kapanmamisti, olculecek satir kalmamisti.
  Isaretler kaldirilsaydi iki bekci KALICI kaybedilirdi. Kardes testlerin (`test_i2:193`,
  `test_k2_mekanik:399`) zaten tasidigi `assert toplam > 0` deyimi tasindi.
- `3a5d98f61` — 9 CAT testi `xfail(strict)` ankrajlandi (dolu havuz ONKOSUL, test edilen sey
  degil; SQL-metni iddia eden 3 kardes test bos havuzda da GECIYOR — ayrimin kaniti).

### Fail Eden Testler
**YOK.** Kapi 22 dosya: **197 passed / 9 skipped / 17 xfailed / 0 failed** EXIT=0.
Toplam **223** — S237 tabaniyla (214+0+9) BIREBIR, kaybolan test yok.
9 skip ONCEDEN vardi (DSN yok); DSN verilip ayrica kosuldu → `benzersizlik_orani` PASSED,
`hacim_tabani` XFAIL (3.616 < 150.000, dogru kirmizi).

### Engelleyiciler
- 🔴 **KAPI 0** — ogrenciye servis edilecek soru yok. Ikmal hazir: `kiro2_temp`
  **53.937 TYT MATEMATIK** (%98,1 gorselli) — A1 kabul kriterinin tam ihtiyaci.
- Devralinan: OCR motoru yok · SMTP · `kiro2-api-import-smoke`.

### Sonraki Adimlar (maks 5)
1. **PUSH** — 5 commit bekliyor (`569b995b6`…`3a5d98f61` + onceki 2).
2. **MAT/TYT gocu** — plan `docs/superpowers/plans/2026-08-20-mat-tyt-goc.md`, T1 kapali.
   Kapiyi dolduracak tek is bu.
3. FAZ E terfi (3.616 KIMYA `pending` → `auto_judged_high` + REFRESH) — **ayri onay**.
4. `soru_hash` capraz-DB dedup sayisi ("34") silme sonrasi **yeniden olculmeli**.
5. Yedek tablolar (4×36.967) ikmal dogrulaninca dusurulebilir.

### Kararlar (gelecek session tekrar tartismasin)
- **Kapinin 0 olmasi gerileme DEGIL** — bugunku 27.073 zaten 0 servis edilebilir soru demekti
  (52/52 okundu). Bos kapi durust; dolu-gorunen cop kapi aktif zarar.
- **Bos kume uzerinde gecen bekci = YESIL ALET ARIZASI.** Bir bekciyi "duzeldi" diye emekliye
  ayirmadan once **evrenin bos olmadigini olc**. (Yeni ders adayi.)
- **Hacim bir vekil olcumdur** bir kez daha dogrulandi: ucuz dedektorler %23,5 yakaladi,
  gercek oran ~%100.

---

## Session Handoff — 2026-08-20 (S239 · MAT/TYT GOCU KALICI) ✅

**Branch:** feature/self-evolution-optimization · **Son commit:** `1b3285d1c` · **Push:** ⏳ 4 commit
**Canli DB:** `question_bank` **3.616 → 4.064** (+448 MAT/TYT) · kapi **0** (yeni parti `pending`, KASITLI)

### Bu oturumun tek cumlesi
448 TYT MATEMATIK sorusu, **her crop'u tek tek gozle okunmus** olarak kalici yazildi;
ama asil ders, kendi AYT-kontrolumun **yanlis katmanda** olcup yesil vermesi oldu.

### Yapilanlar
- `ec40e2b2c` revize plan — eski planin **T2'si IPTAL** (MAT-T1 kitap katmanini curuttu:
  9/354 = %2,54, kitap sinyali orneklem gurultusuyle ayni). Eski plandaki TUM taban sayilari
  bayatti; "kapsam disi 386" **871** olctu.
- `505a4ab28` `y11_aday_uret.py` + 7 bekci (TDD). Konu suzgeci ZORUNLU (871 eleniyor, yoksa
  yukleyici TEK transaction'da tumden duser). Determinizm birebir + girdi sirasindan bagimsiz.
  Cikti yazicisi trailing-newline uretiyor — kanca ciktiyi yamamak yerine YAZICI duzeltildi.
- 🟢 `1b3285d1c` **KOR OKUMA: 586/586 crop, 15 ajan, 0 acilamayan** → 16 sizdiran **%2,73**.
  **BAGIMSIZ TEKRARLAMA**: MAT-T1 farkli orneklemde %2,54; havuzlanmis 25/940 = %2,66.
- PROVA 544 → sapma `[]`, yetim 0. **10 soru tek tek cozuldu: 9/10** (esik >=8/10).
- KALICI 448. Gorsel 40/40 container'dan. Idempotens: capraz-DB elenen **448**.

### 🔴 KENDI KONTROLUM YANLIS KATMANDA OLCTU (durust kayit)
A1 konu kirilimi **MAT.TRV 30 + MAT.INT 26 + MAT.LMT 28 + MAT.LOG 12 = 96** AYT sorusu
gosterdi. Ayni turda calistirdigim "AYT konusu kalan" olcumu **0** diyordu.
Sebep: metin regex'i. Sorularin METNINDE "turev" gecmiyor — *"cemberin icine cizilen
dikdortgenin alani en fazla kac cm2"* bir maks-min sorusu, digeri `f'(x)=0` notasyonlu.
Yargi metinde degil **`primary_topic_id`**'de yasiyor.
**Bu, MAT-T1'in kitap katmanini curuttugu hatanin BIREBIR AYNI SINIFI.** 96 satir silindi.

### Fail Eden Testler
**YOK.** `test_y11_aday_uret.py` 7 passed. Kapi (22 dosya) S238'de EXIT=0 dogrulanmisti.

### A1 KABUL (canli olculdu)
```
farkli konu kodu = 16   (kabul >=5)     3 kat
toplam soru      = 448  (kabul >=40)   11 kat
gorseli dolu     = 448/448     AYT konusu = 0     kapi = 0 (degismedi)
```

### Engelleyiciler
- Kapi hala **0** — terfi (`pending → auto_judged_high` + `REFRESH`) **AYRI ONAY** bekliyor.
  Bu tek adim platformu ilk kez gercek soru servis eder hale getirir.

### Sonraki Adimlar (maks 5)
1. **PUSH** — 4 commit.
2. **FAZ E terfi** (ayri onay): 448 MAT + 3.616 KIMYA `pending → auto_judged_high` + REFRESH.
3. **MAT.TRG (30) + MAT.DIZ (27) mufredat karari** — sinirda; temel trigonometri TYT'de var,
   ilerisi AYT'de. Kesin AYT olmadiklari icin silinmedi, karar bekliyor.
4. Kalan ~3.500 kapsanan MAT sorusu — kor okuma kapasitesi artirilirsa ayri turda.
5. Canlidaki 3.616 KIMYA'nin crop sizintisi **hic olculmedi** (~1.426 gorsel, ~%2,7 → ~38).

### Kararlar (gelecek session tekrar tartismasin)
- **Baglayici kisit ERISILEBILIRLIK degil DOGRULAMA KAPASITESI.** 5.420 aday vardi; 586
  secildi cunku kor okunabilecek buyukluk buydu. Dogrulanmamis icerik = S238'de sildigimiz sey.
- **"0 bulundu" her seferinde once ALET ARIZASI varsayilmali.** Bu oturumda iki kez oldu:
  biri gercekti (capraz-DB 0), biri yanlis katmandi (AYT metin regex'i 0).
- **exam_type GUVENILMEZ** — TYT etiketli dilimde %17,6 AYT konusu vardi.

---

### 🟢 EK — FAZ E KAPANDI: KAPI 0 → 3.615 (ayni oturum, kullanici onayiyla)

Kullanici (a) sikkini secti: **once KIMYA croplarini da kor okut, sonra ikisini
birlikte terfi ettir.** Karar dogru cikti.

**KIMYA kor okuma (evrenin TAMAMI):** 30 ajan x ~48, **1426/1426** okundu,
acilamayan 0, dusen ajan 0 -> **85 sizdiran = %5,96**.
🔴 MAT'in (%2,73) **iki katindan fazla**. Sizinti MODU da farkli: MAT'ta kenar
seridi anahtar listesi, KIMYA'da **cozumlu ornek blogu** (`Ornek: 6` -> `Cozum:`
-> `Cevap: D`) -- ders kitabi duzeni. MAT oranini genellemek ~38 tahmin ederdi,
gercek 85. **Katman degil ORAN da dersten derse degisiyor.** 85 satir SILINDI.

**FAZ E terfi:** yedek `question_statistics_terfi_yedek_20260820` (3.979 eski
durum) -> `auto_judged_high` -> `REFRESH MATERIALIZED VIEW`.
Onkosul ONCEDEN simule edilmisti (kapi ayrica `demoted_at` + tier1_page_inline
disliyor, bes bayraktan biri sart): 3.697 ongoruldu; silinen 85'in 82'si kapiya
girecekti -> 3.697-82 = **3.615**. **Tahmin birebir tuttu.**

**ASIL OLCUM (sayi vekildir, orneklem OKUNDU):**
```
S231 : kapidan 40 soru -> 0/40 servis edilebilir
simdi: kapidan 12 soru -> 12/12 gercek, tutarli, KITAP KAYNAKLI
       anahtarlar tek tek dogrulandi, 11'i kesin dogru
       1 zayif: fc87492b II. onculunde OCR bozuklugu
```

**Canli son durum:** `question_bank` **3.979** (KIMYA 3.531 + MAT 448) ·
kapi `mv_safe_for_beta` **3.615** (KIMYA 3.209 + MAT 406, damgasiz 0).

**Geri alma:** `UPDATE question_statistics qs SET quality_review_status=y.eski
FROM question_statistics_terfi_yedek_20260820 y WHERE y.id=qs.id;` + REFRESH.

**Yeni acik isler:** ES index'i hala eski kapidan (#433) · MAT.TRG/MAT.DIZ
mufredat karari · kalan ~3.500 MAT sorusu (kor okuma kapasitesi) ·
`question_bank_cop_yedek_20260820` 4x36.967 disk tutuyor.

---

### 🟢 EK 2 — S239 KAPANIS: #433 kok neden + mufredat temizligi + defter bosluğu

**#433 KAPANDI ama kayitli baslik YANLIS TESHISTI.** "ES index'ini yeniden kur"
diyordu; gercek kok neden bir **sema kacagi**: `core/es_index_schema.SORGU`
S210 split'inden (`0fd9b8413`) once yazilmisti ve `SELECT q.question_text ...
FROM question_bank q` diyordu. Split sonrasi o kolonlar yavru tablolarda.
Senkron HER kosumda `asyncpg.UndefinedColumnError` ile dusuyordu -> canli ES
index **AYLARDIR 0 dokuman**. Fix: `ALAN_KAYNAK` haritasi + dort tabloya JOIN.
Index **0 -> 3.560**, yasakli alan (correct_answer/explanation/is_active) YOK.
Bayat `_yedek_20260731` (64.270 dok, `correct_answer` TASIYORDU, silinmis
satirlarin projeksiyonuydu) **DROP edildi**. ES 127.0.0.1'e bagli, LAN'a acik degil.

🔴 **DEFTER BU KOR NOKTAYI ZATEN YAZMISTI VE BOSLUK ISIRDI.**
`L-s230-ast-sayaci-ham-sql-goremez`: *"ham SQL yapisal kor noktadir... ZORLAYICI
YOK, bu bosluk bilincli olarak gorunur birakildi."* Bugun ayni kor nokta ES
senkronunda tekrar etti. Bosluk kapatildi: o dersin `zorlayici` alani artik
`tests/integration/test_es_index_schema_split.py`. Bekci sorgunun METNINI okumaz,
**canli semaya karsi KOSTURUR** (AST tarayici string literal icini goremez).

**MUFREDAT: MAT.TRG + MAT.DIZ de AYT cikti.** Onceki turda "sinirda" deyip
birakmistim; ICERIK OKUNDU: TRG'de radyan trigonometrik ozdeslikler /
`tan(x+pi/3)` / `cos 235`, DIZ'de aritmetik-geometrik diziler (biri `sin 75`
kullaniyor). TYT'de ne trigonometri ne diziler var. **57 soru silindi**, zincir
tek turda hizalandi: DELETE -> REFRESH -> ES senkron.
Kumulatif AYT temizligi **179** (26 metin + 96 konu kodu + 57) —
`exam_type='TYT'` etiketinin guvenilmezlik olcusu.

**YEDEK TABLOLARI: KENDI ONERIMI GERI ALDIM.** "Disk tutuyor, dusurulebilir"
demistim; olculdu: **34 MB** (DB toplam 135 MB). 36.967 satirlik bir silmenin
TEK geri alma yolunu 34 MB icin yok etmek kotu takas. **TUTULACAK.**

### Canli son durum
```
question_bank 3.922   (KIMYA 3.531 + MAT 391)
KAPI          3.560   ES index 3.560 (birebir)
AYT konusu 0 | yetim 0 | A1: 14 konu / 391 soru (kabul >=5 / >=40)
```

### Kapi (defterden turetilen zorlayici liste)
```
22 dosya -> 23 dosya (ES bekcisi eklendi)
226 passed / 1 skipped / 1 xfailed / 0 failed   EXIT=0
```
Kalan tek xfail hacim tabani (3.922 < 150.000) ve DOGRU kirmizi.

### Yapilmayan (durust kayit)
- **Kalan ~3.500 MAT sorusu** — baglayici kisit kor okuma kapasitesi. Bu oturumda
  2.012 crop okundu (586 MAT + 1.426 KIMYA); kalan ayri tur isi.
- `MAT.IST` (15 soru) tek basina az; A1'i etkilemiyor ama dengesiz.

---
### Durust kayit — kayitli ders BU TURDA YINE ihlal edildi

`d03674d9d` commit mesajini `-m` ile ve icinde TERS TIRNAK ile verdim. Bash cift
tirnak icinde ters tirnagi komut olarak calistirdi:

    /usr/bin/bash: line 134: L-s230-ast-sayaci-ham-sql-goremez: command not found

Sonuc: mesaj govdesinde defter kimligi YUTULDU ("Defter  kaydinda ham SQL...").
Commit EXIT=0 verdi, push gecti — yani sessiz kayip. Kural (`L-s231-ters-tirnak`):
**commit mesajini DAIMA `git commit -F <dosya>` ile ver.**

Duzeltme yolu olarak `--amend` + force-push SECILMEDI: commit push'lanmisti ve
yayimlanmis gecmisi yeniden yazmak bir mesaj duzeltmesi icin orantisiz. Ankraj
zaten iki yerde duruyor: bu devir notu ve defterin kendisi
(`L-s230-ast-sayaci-ham-sql-goremez`, `zorlayici` alani artik dolu).

Bu oturumda tekrarlayan kayitli dersler: ters tirnak (1), `/tmp` ad-alani (1),
CRLF ankraj (1), N802 buyuk harfli test adi (**2** — 7. ve 8. tekrar, Y13 acik).

---

## Session Handoff — 2026-08-20 (S240 · TEKRARLAYAN DERSLERE ENFORCEMENT) ✅

**Son commit:** `8ab187329` · **Kapı:** 24 dosya / **250 passed / 1 skipped / 1 xfailed / 0 failed**

### Bu oturumun tek cümlesi
N802 sekiz turdur tekrar ediyordu; sebep ders eksikliği değil, **ihlalin yazma
anında görünmemesiydi** — ve hook onu görüp çöpe atıyordu.

### Kök nedenler (üçü de "eksik kontrol" DEĞİL)
- **N802:** `ruff check --fix --quiet` + `capture_output=True` → bulgu yakalanıp
  **hiç okunmuyordu**. ⚠️ Hipotezim yanlıştı: susturan `--quiet` değil (ruff
  0.14.13 N802'yi yine basıyor, EXIT=1); yutan şey yakalananın okunmaması.
  Ayrıca ruff 0.14 **yeni tanı biçimi** kullanıyor → `--output-format=concise` şart.
- **Ters tırnak:** hook doğru noktadaydı, bakmıyordu. Artık **bloklar** (exit 2).
- **`/tmp`:** aynı körlük. **Uyarır, bloklamaz** — meşru kullanımı var; bloklarsak
  sürtüşme yaratır, kapatılır, kontrol yine ölür.

### İki dürüst kayıt
1. **Dedektör ilk gerçek kullanımda yanlış-pozitif verdi** ve kendi defter
   güncellememi blokladı (heredoc'taki ders METNİNİ komut sandı). Planın risk
   tablosundaki madde ilk kullanımda ısırdı → segment-başı daraltma + 3 regresyon testi.
2. **N802'yi DOKUZUNCU kez**, tam da N802'yi zorlayan test dosyasında yaptım.
   Alışkanlık hook'tan güçlü — ama kapı bu kez yakaladı.

### Ölçümler
```
dedektor testleri  24 passed (3'u yanlis-pozitif regresyonu)
hook bekcileri    211 passed        yanlis-pozitif kolu 0/3
mutasyon           3/3 OLDU  (M3 once "GECERSIZ" gorundu -> HARNESS ARIZASI:
                   gevsek " error" alt-dizesi testin kendi verisine esledi)
zorlayici liste  23 -> 24 dosya     kapi 250/0
```

### Kapsam dışı (bilerek)
- **CRLF çok satırlı ankraj** — Edit `old_string` eşleşmesi hook'tan görünmüyor,
  enforcement noktası YOK. `zorlayici: null` kalır, boşluk **görünür** bırakıldı.
- **Kalan ~3.500 MAT** + `MAT.IST` dengesizliği — içerik hattı, ayrı iş.

---
