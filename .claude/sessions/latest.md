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
