
# KIRO2 — Eksiklik Master Belgesi

**Oluşturulma:** 1 Ağustos 2026 · **Durum:** aktif referans
**Önceki belgelerin yerini alır** (onlar kanıt arşivi olarak kalır):
`2026-07-30_gercek_durum_olcumu.md` · `2026-07-29_son-12-oturum-gozden-gecirme.md` ·
`2026-07-31_eksiklik_durum_dogrulamasi.md`

---

## 0. Bu belge nedir

KIRO2'nin **ölçülmüş** eksikliklerinin tek envanteri. Üç kaynağın birleşimi:

| Kaynak | Bulgu | Durum |
|---|---:|---|
| 30-31 Tem "Gerçek Durum Ölçümü" + çürütme turu | 113 | 21'i kapandı, **50'si açık** |
| 29 Tem 12-oturum gözden geçirmesi | 12 | K5/K4.5 kapandı, kalanı açık |
| **1 Ağu öz-denetim** (kapatılan işlere saldırı) | **49** | **hepsi açık** |

**Toplam açık: 97 kalem.**
*(Açılış 99 · S201'de `A.1`+`A.1b` kapandı `2d68e4811` · doğrulama turunda `T2b`
eklendi = 98 · S202'de `A.4`+`A.4b`+`A.4c` kapandı `75c70dab5`+`2e439f40a` = 95 ·
`A.2` kapandı `d5f07039d` = 94, ama onun canlı ölçümü **12 kırık Golden Flow**
ortaya çıkardı → `GF-K1`/`GF-K2`/`GF-K3` eklendi = **97**)*

> Sayaç bu turda **arttı**. Bu bir gerileme değil: `A.2` zaten "eşik hiç
> ölçülmedi" diyordu; ölçüldüğünde ölçüm bütünlüğü kusuru kapandı ve altından
> gerçek ürün kusurları çıktı. **Ölçmeyen bir kapı, kalem sayısını düşük
> gösterir** — FAZ 0'ın önce gelme sebebi tam olarak budur.

### Nasıl kullanılır

1. §3 kontrol listesinden **sıradaki ilk açık kalemi** al.
2. Kapat, kutucuğu işaretle, **ANKRAJ yaz** (commit + `dosya:satır`). Ankrajsız kapanış yok.
3. §5'teki fantomlarla **uğraşma**. §4'teki kapanışları **yeniden açma**.
4. Yeni mega denetim açmadan önce: `.claude/rules/audit-methodology.md` "Mega Audit Lock".

### Bu belgenin varlık sebebi

1 Ağu'da 7 görev "kapandı" ilan edildi. Aynı gün o işlere saldırıldı ve
**49 kusur** bulundu — biri **kendi yaratılmış P0 regresyon**du (Golden Flow
kapısını "gerçek yapan" fix, 178 testin 165'ini öldürüyordu).

Ders şu: **kapanış iddiası da bir ölçümdür.** Bu belge o dersin kurumsal hâli.

---

## 1. Metodoloji

**1 Ağu öz-denetimi:** 7 skeptik ajan (ayrı mercekler) + 2 hakem turu.
Her skeptiğe "belirsizsen kusur VAR tarafına eğil" talimatı verildi; hakem turu
her iddianın ankrajını **bağımsız** açtı. Sonuç: **49 teyitli · 1 fantom ·
13 "saldırdım, dayandı"**.

**Kabul kuralı:** her verdict commit hash / `dosya:satır` / komut çıktısı ankrajı
taşır. Oturum notları ve commit mesajları **kanıt sayılmadı**, iddia sayıldı.

### ÖLÇÜLMEYENLER (tahminle doldurulmadı)

- **Golden Flow paketi canlı koşulmadı.** 178 test *toplanıyor* (ölçüldü) ama
  pass/fail dağılımı bilinmiyor. `-x` + eşik 150 birlikte CI'ı kalıcı kırmızı
  yapabilir — bu **ölçülmedi**, `A.2`'de açık kalem.
- **Tam backend paketi koşamıyor** (`pytest_asyncio` teardown deadlock).
  Coverage ve gerçek pass sayısı bu yüzden bilinmiyor.
- **CI koşum durumu** — `gh` kurulu değil.
- **Frontend testleri** bu oturumda hiç koşulmadı.
- **Canlı SMTP gönderimi** — kimlik yok, uçtan uca denenmedi.

---

## 2. Karne

| Ağırlık | 31 Tem devreden | 1 Ağu öz-denetim | Toplam |
|---|---:|---:|---:|
| **P0** | 2 | 2 *(ikisi de düzeltildi)* | **2 açık** |
| P1 | ~25 | 13 | ~38 |
| P2 | ~15 | 17 | ~32 |
| P3 | ~8 | 16 | ~24 |
| **Toplam** | **50** | **49** | **99** |

**Öz-denetim kusur türleri:** Kaçan kardeş 10 · Vakum test 10 · Eksik fix 10 ·
Yanlış iddia 11 · Regresyon 8.

> Bu dağılımın kendisi bir bulgu: kusurların **%41'i** (vakum test + yanlış iddia)
> *doğrulama katmanının kendisinde*. Yani ölçüm aletleri, ölçtükleri şeyden daha
> güvenilmez durumda.

---

## 3. KONTROL LİSTESİ

> **Sıralama ilkesi:** önce **ölçüm bütünlüğü**. Bekçiler yalan söylüyorsa
> diğer hiçbir doğrulama anlam taşımaz. Bu, `audit-methodology.md`'nin
> "ölçüm aletini doğrula" kuralının iş sıralamasına çevrilmiş hâli.

### FAZ 0 — Ölçüm bütünlüğü (ÖNCE BU)

Bu fazın tamamı **yeşil rapor veren ama hiçbir şey ölçmeyen** bekçileri onarır.

- [x] **A.1** ✅ **KAPANDI** `2d68e4811` — çıkarıcı artık AST ∪ **çalışma-zamanı**
      birleşimi (`test_fsrs_schema_contract.py:125-132`). `/due`'nun gerçek SQL'i
      f-string ile birleşiyor, ad `quality_gate.py:69`'dan geliyor ve
      `fsrs_service.py` kaynak metninde **hiç geçmiyor** → salt-AST yapısal olarak
      kör. Ölçüm: çıkarılan `['question_bank','user_item_fsrs']` · çalışma-zamanı
      `str(_FETCH_DUE_SQL)` içinde `mv_safe_for_beta` → **True**.
- [x] **A.1b** ✅ **KAPANDI** `2d68e4811` — `_canli_tablolar()` artık
      `pg_class relkind IN ('r','p','v','m','f')` + şema filtresi
      (`test_fsrs_schema_contract.py:135-156`); bağlantı da kapatılıyor.
      Ölçüm: `to_regclass('mv_safe_for_beta')` VAR · `information_schema` (217 ad)
      içinde YOK · `pg_matviews` → 2 matview.
      **Maskeleme empirik olarak üretildi** (mutasyon M1): A.1b tek başına geri
      alınınca sınıf bekçisi *yanlış-kırmızıya* döndü — belgenin öngörüsü doğrulandı.
      RED 2 fail → GREEN 9/9 · mutasyon **4/4** (M1 A.1b-geri · M2 salt-AST ·
      M3 salt-çalışma · M4 çalışma-yarımı-boş). Üretim kodu değişmedi.
- [x] **A.4** ✅ **KAPANDI** `75c70dab5` + `2e439f40a` — iddia düzeltildi **ve**
      bu kalemin kendi ifadesi de yanlış çıktı. Ölçüm: `ci.yml:281`
      `pytest tests/ … -x` **marker filtresiz** koşuyor → dosya **TOPLANIYOR**;
      koşmamasının sebebi işin *tetiklenmemesi* (dal master'dan **334** commit
      önde, `on:` = [main,master,develop]). `deploy.yml:225` `-m integration`
      bacağına sahip ama tetiği `push: tags: v*.*.*` ve eşleşen tag **0**.
      Yani "hiç koşmuyor" ≠ "toplanmıyor" — ikisi ayrı şey ve ikincisi
      **merge-anı mayınıydı**: `psycopg2-binary` CI kurulum kümesinde yok
      (`requirements.txt:10` psycopg **v3**; sqlalchemy'de psycopg2 yalnız
      `[postgresql*]` extra'sında) → collection ERROR, `-x` ile tüm test job'u.
      Fix: `pytest.importorskip` (2 dosya) + **yeni sınıf bekçisi**
      `tests/test_ci_collection_guard.py` (3 kontrol kolu + 633 dosya taban).
      Ayrıca "163 router" sayısı hiçbir sayma yönteminden çıkmıyordu → ölçüldü
      (**153** dosya / **155** `APIRouter(` / **2** `get_current_tenant`) ve
      ölçüm komutları docstring'e yazıldı. Tuzak dedektörüne `db_hazir`
      fixture'ı eklendi (tek fixture'sız testti → DB'siz ortamda ERROR).
      A/B: psycopg2 gölgelenmiş → korumasız **ERROR**, korumalı **2 skipped**.
- [x] **A.4b** ✅ **KAPANDI** `2e439f40a` — `POLITIKA_TABANI = 79` + saf
      `_kalip_ihlali()`. Vakum **sentetik olarak üretildi**: `(toplam=1,
      permissive=1)` girdisi tam olarak "78 politika silindi" senaryosudur ve
      eski oran-eşitliği bunu YEŞİL geçiriyordu. Mutasyon M1/M2 → doğru test
      düştü.
- [x] **A.4c** ✅ **KAPANDI** `2e439f40a` — `_kiracilik_yargisi()` 0/1/2'yi üç
      ayrı yargıya böler (`kor` | `tek` | `cok`); eski `<= 1` dalı 0 ile 1'i
      aynı kefeye koyuyordu. Saf fonksiyon, çünkü canlı DB'de `organizations=0`
      **üretilemez** → runtime'da çivilenemeyen bir assert olurdu. Mutasyon M3
      → doğru test düştü. Mutasyon M4 (fixture kaldır + DB'siz simülasyon) →
      `OperationalError` ile FAILED, fixture'lı hâlde 2 passed / 6 skipped.
- [x] **A.2** ✅ **KAPANDI** `d5f07039d` — eşik **ilk kez ölçüldü**. Canlı koşum
      (`pytest tests/e2e/test_golden_flows.py -m golden_flow --junitxml=…`, 94 sn):
      **178 test → 164 GEÇTİ / 12 DÜŞTÜ / 2 ATLANDI**. Atlanan ikisi de belgeli
      (`gf4w2` seed'e bağlı due-card, `gf1wb` Bearer-only deploy). Yani
      `ESIK = 150` **ulaşılabilirdi** — "kapı kalıcı kırmızı olur" endişesi
      **çürüdü**. Kusur başka yerdeydi ve üçü de RED testle üretildi:
      **(1)** sabit eşik suite büyüdükçe **gevşer** (250 testte `gecen>=150`
      kuralı 90 skip'i yeşil geçirir — golden-flows.md "yeni özellik → yeni GF"
      diyor); **(2)** `hata` hesaplanıyor ama **assert edilmiyordu** — gerçek
      raporda ölçüldü: *eski kural 12 kırık akışa rağmen YEŞİL, yeni kural
      KIRMIZI*; **(3)** mantık YAML içi heredoc'tu, **hiçbir testi yoktu**.
      Fix: `backend/scripts/gf_esik_kapisi.py` + `tests/unit/test_gf_esik_kapisi.py`
      (11 test, 3 alet-doğrulama), kural `toplam>=170 · hata==0 · atlanan<=5`
      (mutlak geçen-sayısına bağlı değil → bayatlamaz). `-x` kaldırıldı: kapı
      artık `hata`yı kendi ölçüyor ve rapor ilk hatada kesilmiyor.
      **Mutasyon 5/5** (M4 ilk denemede syntax hatası verdi = geçersiz ölçüm,
      tekrarlandı). Ölçümün yan ürünü aşağıdaki `GF-K1..K3`.
- [ ] **A.3** 4 TDD testinden biri **vakum**: dekoratör kaynak metninde substring
      arıyor, fix'ten önce de sonra da geçer.
- [ ] **A.5** F21-yeni'nin 503'ü **hiçbir testte çivili değil** (AST testi
      mutasyonda düşmez); SMTP_HOST **önceliği** de ölçülmüyor.
- [ ] **A.6** Durum tablosunun iki yarısı çelişiyor: kutucuk ✅, Ek A'da 🔴.
- [ ] **A.6b** "Açık P0 7→2" sayacı **commit sayıyor, korumayı değil**.

### FAZ 1 — Yarım kalan fix'ler (bağlam taze, en yüksek ROI)

- [ ] **A.5b** **F20 yarım**: `kvkk_compliance.py:812` + `health_audit_service.py:755`
      hâlâ yalnız `SMTP_SERVER` okuyor → KVKK ihlal bildirimi ve sağlık alarmı
      hâlâ kör.
- [ ] **A.5c** **F21 kayıt yolunda duruyor**: `auth.py:711` dönüş değerini
      okumuyor. AST bekçisi bunu **yapısal olarak göremiyor**.
- [ ] **A.3b** **PUT hiçbir alanı yazmıyor** — 500 gitti ama istemcinin
      gönderdiği alan adları servisin beklediğiyle uyuşmuyor; "güncellendi" diyor.
- [ ] **A.3c** Kardeş uç aynı sınıfı taşıyor: `zorluk_seviyesi` → `difficulty`
      sessizce düşüyor.
- [ ] **A.3d** Fix "kardeş desen" diyor ama kardeşin **cache geçersizleştirmesini
      almadı** — yazma canlı, okuma 2 saat bayat.
- [ ] **A.1c** **Sessiz kayıp yalnız FSRS değildi**: aynı transaction'da
      `streaks` + `weekly_progress` da yutuluyor, rollback yok. Commit bunu saymıyor.
- [ ] **A.2b** `429→FAIL` kuralı kardeşlerde yok: aynı dosyada GF1wB + 2 e2e
      dosyası hâlâ 429'u skip'e çeviriyor.
- [ ] **A.2c** Kaldırılan `\|\| echo` amplifikatörünün **ikizi bir satır yukarıda**
      duruyor (alembic adımı).
- [ ] **A.7** GF eşiği tek workflow'a kondu; **ikinci workflow** aynı paketi
      eşiksiz ve backend'siz koşuyor.

### FAZ 2 — Kaçan kardeşler (sınıf kapatma)

- [ ] **A.1d** "Sınıf bekçisi" **150 üretim dosyasından 2'sini** tarıyor.
      `c555a10f4b93`'ün diğer 130 kurbanını hiçbir test kollamıyor.
- [ ] **A.4d** Tüm atlatma ölçümü **tek tabloya** (`refresh_tokens`) dayanıyor —
      79 tablodan 1'i örneklendi.
- [ ] **Y3** ES admin reindex ucu **canlı alias'a `correct_answer` yazıyor**;
      onu bugün kapatan tek şey bir kwarg hatası (`mapping=` vs `mappings=`).
- [ ] **YENI-7** `/content-management/questions` **tamamen mock** — F1'in tarif
      ettiği kusur orada aynen yaşıyor.

### FAZ 3 — Ürün kusurları

- [ ] **F17 + F17b** Eşzamanlı sınav oturumu kısıtı üç katmanda da yok; **ölü 409
      bekçisini 3 test yeşil doğruluyor**.
- [ ] **K3** 70 `live()` yolundan **~43'ü backend'de yok**.
- [ ] **K4.6** Veli `/parent/dashboard`'a iniyor, orası **656 satır sabit veri**;
      gerçek sayfa mount'lu ama hiçbir yol götürmüyor (tek satırlık takas).
- [ ] **K4.3** AI yasal uyarısı **hiçbir kullanıcıya gösterilmiyor** (importer'ı yok).
- [ ] **Y1(kod)** `learning_path.py` ölü router — 2 frontend çağrısı 404.
- [ ] **A.5d** `/veli-onay/resend` 503'ü **yıkıcı**: önceki geçerli token'ı
      önce öldürüyor, sonra 503 diyor.
- [ ] **YENI-8** `soru_guncelle` "bulunamadı" ve "istisna" için aynı `None` →
      DB arızası 404 "Soru bulunamadı" diye raporlanıyor.

#### GF-K · 12 Golden Flow CANLIDA KIRIK (1 Ağu 2026 ölçümü, `A.2`'nin yan ürünü)

> Ölçüm: 178 GF testinin **12'si düşüyor** — 10× HTTP 500, 1× ReadTimeout (30 sn),
> 1× "Server disconnected". `golden-flows.md` bunları **merge-blocker** sayar.
> **Fantom değil:** o uçların modülleri konteyner imajından (30 Tem 21:40) beri
> değişmemiş; ayrıca 6 tablonun yokluğu `to_regclass` ile doğrulandı ve
> trigram araması alias bulmadı.

- [ ] **GF-K1** **ORM↔DB şema kayması — 6 tablo yok** (baskın sınıf, `UndefinedTable`
      log'da **74 kez**). `A.1`/`K1`'deki `user_item_fsrs` vakasının aynısı:
      | tablo | düşen test |
      |---|---|
      | `video_watch_sessions` | `gf59` video-analytics/sessions/start |
      | `video_notes` | `gf94` video-analytics/notes |
      | `emotional_states` | `gf49` diary/emotional |
      | `appointments` | `gf137` teachers/my-appointments |
      | `live_sessions` | `gf36` live-sessions create |
      | `reasoning_cache` | (uç eşlemesi yapılmadı) |
      Karar gerekiyor: migration ile **tabloları geri getir** mi, yoksa uçlar
      ölü mü? (`user_item_fsrs`'te "geri getir" seçilmişti — `#461`.)
- [ ] **GF-K2** **Kod kusuru ×2** — (a) `AttributeError: 'LearningStyleService'
      object has no attribute 'update_behavioral_data'` (`gf82`); (b)
      `AttributeError: 'AsyncSession' object has no attribute 'query'` — **senkron
      ORM API'si async oturumda** (testing.md #25 sınıfı, uç eşlemesi yapılmadı).
- [ ] **GF-K3** **Altyapı/performans ×2** — `gf27` content-management question
      create **30 sn ReadTimeout** (suitedeki en yavaş test), `gf50` xp/awards
      `RemoteProtocolError: Server disconnected` (worker çökmesi şüphesi).
      Kalan 500'ler (`gf25` coaching/signals, `gf26` diary/goals, `gf88`
      reports/exam/generate-pdf, `gf130` fsrs/flashcards/due) log ankrajıyla
      henüz eşlenmedi — triyajın ikinci turu.

### FAZ 4 — Test altyapısı

- [ ] **T1** Paket uçtan uca koşamıyor (`pytest_asyncio` deadlock). **Kaldırma
      deneyi:** `backend/conftest.py:124-135` `event_loop` fixture'ını devre dışı
      bırak, kilitlenme kayboluyor mu?
- [ ] **T2** 27 kırık test (`test_analytics_api.py`).
- [ ] **T2b** *(YENİ, 1 Ağu — S201 doğrulama turunda ölçüldü)* `test_fsrs_system.py:567`
      hâlâ `patch("services.fsrs_service.DBFSRSStudySession")` diyor; o modül
      `_deprecated`'e taşındı → `AttributeError`, izole koşumda da düşüyor.
      **Eksik fix**: aynı dosyada `:379` `services._deprecated...` diye güncellenmiş,
      `:567` kaçmış (`93f10f7fe` "update patch path after fsrs_service → _deprecated move").
      Yol düzeltmek **deprecated uygulamaya test diriltmek** demek → önce
      "iki paralel FSRS implementasyonu" kanonik seçimi (bkz. §Kararlar) yapılmalı;
      alternatif: testi sil. Karar verilmeden dokunulmadı.
- [ ] **T3** 99 modül `skipif(True)` — gerekçelerini triyaj et (#458a dersi:
      silinen dosyanın gerekçesi **fantom** çıkmıştı).
- [ ] **T4** Coverage eşiği 60.0; `source` listesinde `models` yok.
- [ ] **T5** 17 frontend test dosyası hiç koşamaz.
- [ ] **A.7b** Zamanlama-duyarlı 20 perf testi varsayılan pakete girdi, CI'da
      atlama kapısı yok; birinde **makineye çakılı mutlak yol** var.
- [ ] **A.2d** Önbellekte TTL yok; access token 15 dk, uzun koşumda 401 sessizce "geçer".

### FAZ 5 — CI

- [ ] **F8-b** Kapı **aktif dalda hiç tetiklenmiyor** (`[main,master,develop]`,
      dal 318 commit önde) → #462'nin tüm değeri bugün **sıfır**.
- [ ] **B3** CI kök nedeni ölçülmedi (`gh` yok).
- [ ] **#390** Dependabot triyajı.

### FAZ 6 — Doküman / hijyen

- [ ] **D0-D9** CLAUDE.md ve kural dosyalarının kalan bayat sayıları.
- [ ] **A.6c** `Y6` ✅ işaretli ama **reçete uygulanmadı**: `.gitignore:266`
      hâlâ ankrajsız.
- [ ] **A.6d** `DEPLOY` kutucuğu ✅ ama ölçüm bu oturumun kodundan **önce** koşuldu.
- [ ] **A.3e** Dokunulan testin **adı** hâlâ "500" diyor, assert 404.
- [ ] **A.4e** `psycopg2` bağlantıları kapatılmıyor; `pg_class` sorgularında
      şema filtresi yok.
- [ ] **YENI-10** ES yedek indeksi (64.270 dok, hepsi cevap anahtarlı) —
      sızıntı riski yok ölçüldü ama **retention da yok**.
- [ ] Kalan P2/P3 hijyen (Ek B).

### OPERATÖR KUYRUĞU (kod işi değil)

- [ ] **#441** SMTP kimlik bilgisi → `.env.mvp` + `docker compose up -d --no-deps backend`
      (**restart yetmez**). Kod tarafında yapılacak şey kalmadı.
      Not: `.env.mvp.example`'da şablon **yok** ve `.env*` salt-okunur olduğu için
      kod tarafından eklenemez (`YENI-9`).
- [ ] **#390 / #436** `gh` CLI + faturalama penceresi.
- [ ] **#445** 73 STUDENT hesabının iş-kararı triyajı.
- [ ] **OTURUM-1** DB'de 31 çöp sınıf (silme ucu yok → SQL + onay gerek).

---

## 4. Kapananlar — yeniden açma

| İş | Ankraj |
|---|---|
| `#461` `user_item_fsrs` restore + GRANT | `3773b3d42` |
| `#462` GF login kapısı (429→FAIL, önbellek) | `c5a4f2c98` |
| **`#462-R` önbellek zehirlenmesi (kendi regresyonum)** | **`b57be1ace`** |
| `#463` doküman sayıları canlı ölçümle senkron | `962f7d4c9` |
| `#464` RLS ölçülebilir yapıldı (kapatılmadı) | `64d6452be` |
| `#465` admin PUT 3 bastırıcı + 5 bayat test | `b93cfcd3c`, `0d0dfd069` |
| `#466` SMTP F20/F21/F21-yeni (kısmi — bkz. A.5b/A.5c) | `4ddd74383`, `ef6bafe47` |
| `B1/#433` ES index kaynağı kalite kapısına bağlandı | 6bc1febec + canlı ölçüm |
| `K5` 9/9 yazma ucu kapılı, bekçi mutasyona dayanıyor | `d7f80175b` |

## 5. Fantomlar — uğraşma

| # | Neden |
|---|---|
| `F12` | `n_live_tup` okuyan canlı sağlık sorgusu yok |
| `#458a-2` | `test_turkish_nlp.py` mojibake'si **kasıtlı fixture** |
| `AUTH` | Admin uçlarında rol kapısı var ve negatif testli |
| `F20-alt` / `F21-alt` | `EMAIL_FROM` fallback var; log var |
| `f357e4647` | Skip mekanizmasına dokunmadı |
| `B4-5dk` | "5/dk login limiti" yanlış (gerçek 30/dk) |
| `#447-schema` | `backend/schemas/persona.py` hiç olmadı |
| `"5 uç 500"` | Gerçekte **4** HTTP ucu (mercy ayrı uç değil, Query parametresi) |

## 6. Saldırıya dayananlar (13)

Öz-denetimde saldırılıp **doğrulanan** kararlar — tekrar tartışılmasın:
DDL birebir + GRANT/zincir canlıda doğru · workflow YAML + heredoc + rapor-yoksa-düş
sağlam · `@admin_required` kaldırılmasıyla yetki kaybı **yok** · `SET LOCAL`
işlem-içi (yanlış-sebeple-geçme imkânsız) · SMTP_HOST önceliği regresyon
yaratmıyor · 4 nicel iddia bağımsız aletle doğrulandı · `.gitignore` negasyonunun
blast radius'u 6 kontrol koluyla temiz · `status`/`HTTPException` import'ları mevcut
(NameError yok) · `_TOKEN_ONBELLEGI` için xdist yarışması yok · admin PUT fix'i
dekoratör tuzağını yeniden açmıyor.

---

## 7. Kalıcı dersler (bu turdan)

1. **Kapanış iddiası da bir ölçümdür.** 7 "kapandı"nın birinde aktif zarar vardı.
2. **Doğrulama kapsamı = değişikliğin kapsamı.** GF regresyonu, e2e paketi hiç
   koşulmadığı için kaçtı.
3. **Yeşil test kırılmayı gizleyebilir.** Bekçim 7/7 yeşilken dosyada tanımsız
   fonksiyona çağrı vardı — AST adlarına bakıyordu, çözümleme yapmıyordu.
4. **İki hatalı bileşen birbirini maskeler** (A.1 + A.1b). Birini düzeltmek
   diğerini görünür kılar; **birlikte** düzelt.
5. **`cd` kalıcı** → geri alım bu oturumda **4 kez** sessizce başarısız oldu.
   Her geri alımı repo kökünden ölç.

---

<!-- EK-A-BASLANGIC -->
## Ek A — 1 Ağu öz-denetiminde bulunan 49 kusur (tam envanter)

> Her satır **hakem turundan geçmiş** ve ANKRAJ taşıyor. Bu bulgular
> 1 Ağu'da kapatılan işlerin **kendisine** yapılan saldırıdan çıktı.


### A.2 Golden Flow kapısı

| Önc. | Tür | Bulgu | Kanıt (ankraj) | Önerilen |
|---|---|---|---|---|
| **P0** | Regresyon | Token önbelleği GF1x logout testi tarafından zehirleniyor — sonraki 148 test blacklist'li token alıyor | backend/tests/e2e/test_golden_flows.py:93 `_TOKEN_ONBELLEGI` hiç geçersizleştirilmiyor (grep -rn _TOKEN_ONBELLEGI tests/ → yalnız 3 satır: decl/get/set, hiç `pop`/`clear` yok). backend/tests/e2e/test_golden_flows.py:459 `test_gf1x_logout_invalidates_bearer_token` → `token = _login(client, STUDENT)` (artık ÖNBELLEKTEN gelir) → `client.post("/api/v1/auth/cikis", headers=headers)` → `assert me2.status_code == 401`. backend/api/auth.py:1213-1235 `kullanici_ci… | `_login`'e geçersizleştirme ekle: GF1x logout'tan sonra `_TOKEN_ONBELLEGI.pop(STUDENT['email'], None)`; ya da GF1x'i önbelleği baypas eden ayrı bir taze login ile besle (`_login_taze`). Ek olarak `_login` dönerken /auth/me ile canlılık doğ… |
| **P1** | Yanlış iddia | ESIK=150 hiç ölçülmedi; kapı aktif dalda zaten hiç tetiklenmiyor | .github/workflows/golden-flows.yml:233 `ESIK = 150 # 178 testin buyuk cogunlugu GERCEKTEN kosmali`. Commit c5a4f2c98 DOGRULAMA bölümü yalnızca şunları listeliyor: `6/6 login kapisi testi PASS`, `12/12 test_workflow_yaml.py PASS`, `Iki workflow YAML da PyYAML ile ayristirildi` — **canlı GF koşumu YOK**. .claude/sessions/latest.md:24 `F8-b: kapı aktif dalda hiç tetiklenmiyor ([main,master,develop], dal 318 commit önde). #462'de kapıyı gerçek yaptım ama koşm… | Eşiği sabitlemeden ÖNCE canlı bir GF koşumu yapıp gerçek pass sayısını ölç; eşiği o ölçümün altına (ör. gözlenen-5) koy. Ayrıca #468 (CI tetikleme) kapanmadan bu kapının değeri sıfır — `on:` bloğuna feature dalları veya `pull_request` hede… |
| **P2** | Regresyon | Önbellekte TTL/yenileme yok; access token 15 dk, uzun koşumda 401 sessizce 'geçer' | backend/core/config.py:101 `self.jwt_access_token_expire_minutes = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '15'))`; backend/core/auth.py:72,105 bu değeri `timedelta(minutes=...)` ile kullanıyor. backend/tests/e2e/test_golden_flows.py:93-122 `_login` — süre/`exp` kontrolü YOK, yenileme YOK, tek `dict` get/set. backend/tests/e2e/test_golden_flows.py: `status_code != 500` = 136 iddia, `status_code < 500` = 21 iddia (toplam 157/178). 401 bu iddiaları… | Önbelleğe zaman damgası koy ve `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`'un yarısında yeniden login at; veya kullanımdan önce `/auth/me` ile canlılık doğrula. Ayrıca 157 gevşek iddiaya `!= 401` şartı ekle — 401 hiçbir GF için meşru sonuç değil. |
| **P2** | Kaçan kardeş | 429->FAIL kuralı kaçırılan kardeşlerde yok: aynı dosyada GF1wB + 2 e2e dosyası hâlâ 429'u skip'e çeviriyor | backend/tests/e2e/test_golden_flows.py:1317-1324 (`test_gf1wb_auth_refresh_token_is_persisted`) — `_login` BAYPAS ediliyor: `login_resp = c.post("/api/v1/auth/login", json=STUDENT)` ardından `if login_resp.status_code != 200: pytest.skip(...)` → 429 dahil HER şey skip. backend/tests/e2e/test_es_answer_leak.py:86-90 aynı desen. backend/tests/e2e/test_osym_inspired_auth.py:79-81 ve 89-91 aynı desen (2 kez). Kontrol kolu: `grep -n "auth/login" tests/e2e/test… | GF1wB'yi ortak bir `_login_taze(client, creds)` yardımcısına taşı (429->fail, non-200->skip aynı sözleşme). test_es_answer_leak.py ve test_osym_inspired_auth.py fixture'larına da 429 dalı ekle. |
| **P2** | Kaçan kardeş | Kaldırılan `\|\| echo` amplifikatörünün ikizi bir satır yukarıda duruyor (alembic) | .github/workflows/golden-flows.yml:191 `alembic upgrade head \|\| echo "::warning::alembic upgrade failed — continuing with raw schema"` Aynı commit bir alt adımdaki ikizini kaldırdı: satır 193-199 `Seed MVP users` → `\|\| echo` KALDIRILDI (#462/B4-x) yorumu ile. | `\|\| echo` kaldırılsın ya da neden opsiyonel bırakıldığı satır içi ölçümle gerekçelendirilsin (hangi migration'ın CI'da düşmesi bekleniyor?). |
| **P2** | Vakum test | Birim testleri vakum DEĞİL ama sözleşmesi eksik: sahte istemci blacklist'i modelleyemediği için P0 bulgusunu yakalayamaz | Koşuldu: `python -m pytest tests/unit/test_golden_flow_login_gate.py -q --timeout=60` → `6 passed, 2 warnings in 0.33s`. Mutasyon duyarlılığı KOD OKUYARAK doğrulandı: 429 dalı silinirse akış `if resp.status_code != 200: pytest.skip` dalına düşer → `Skipped` → tests/unit/test_golden_flow_login_gate.py:90-93 `assert not isinstance(kutu.value, Skipped)` DÜŞER. Önbellek satırı (test_golden_flows.py:121) silinirse `cagri_sayisi` 3 olur → tests/unit/test_golden… | Yeni test: `_login` → önbelleğe yaz → sahte istemciye 401 döndüren `get()` ekle → `_login`'in ikinci çağrıda TAZE login attığını iddia et. Bu test bugün RED verir (bulgu #1'i çivilerdi). |

### A.7 Regresyon süpürme

| Önc. | Tür | Bulgu | Kanıt (ankraj) | Önerilen |
|---|---|---|---|---|
| **P0** | Regresyon | GF token onbellegi cikis testiyle ZEHIRLENIYOR — 178 testin 165'i olu token aliyor | backend/tests/e2e/test_golden_flows.py:93 `_TOKEN_ONBELLEGI: dict[str,str] = {}` (modul-global, HIC temizlenmiyor; dosyada `autouse` yok, tests/e2e/ altinda conftest.py YOK — `ls tests/e2e/` ile dogrulandi). test_golden_flows.py:460 `token = _login(client, STUDENT)` -> ONBELLEKTEN gelir; :466 `client.post("/api/v1/auth/cikis", headers=headers)`; :471 `assert me2.status_code == 401` — yani testin KENDI iddiasi token'in oldugudur. backend/api/auth.py:1235 `… | `_login` icinde cagri oncesi/sonrasi gecerlilik dogrula veya gf1x'e ozel token al (`_TOKEN_ONBELLEGI.pop(STUDENT['email'])` ile cikis oncesi taze login + cikis sonrasi onbellegi temizle). Alternatif: gf1x'i ayri bir kimlikle kosur. Ardinda… |
| **P1** | Kaçan kardeş | SMTP_HOST kabulu yalniz email_util'e verildi; iki kardes tuketici ayni sessiz hatada duruyor | Fix: backend/core/email_util.py:37 `smtp_server = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER")`. Dokunulmayan kardesler (ripgrep, backend/ hedefli): backend/core/kvkk_compliance.py:812 `smtp_server = os.getenv("SMTP_SERVER")` — `_send_kvkk_email_notification`, :817 `if not all([kvkk_email, smtp_server, ...]): logger.warning(...); return` backend/analytics/health_audit_service.py:755 `smtp_server = os.getenv("SMTP_SERVER")` — `_send_email_alert`, :76… | Ortak bir cozucu cikar (`core.email_util`'de `_smtp_host()` gibi) ve iki kardes de onu kullansin; veya en az `os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER")` desenini iki dosyaya da uygula. Kontrol kolu: SMTP_HOST set, SMTP_SERVER bos … |
| **P1** | Kaçan kardeş | Golden Flow esigi tek workflow'a kondu; ikinci workflow ayni paketi ESIKSIZ ve BACKEND'SIZ kosuyor | .github/workflows/quality-gate.yml:64 `pytest tests/e2e/test_golden_flows.py -m golden_flow -v --tb=short` — `-x` YOK, `--junitxml` YOK, esik adimi YOK. Ayni dosya :57-60 yorumu: "GF1-GF8 ... auto-skip when backend is unreachable ... so we don't need to spin up docker-compose in CI" — yani bu is'te postgres/redis servisi, seed adimi ve uvicorn baslatma ADIMI YOK; test_golden_flows.py:80 `pytest.skip(f"backend {BACKEND_URL} ulasilamiyor")` her testi atlati… | Ya quality-gate.yml'deki adimi kaldir (golden-flows.yml zaten ayni PR'larda kosuyor), ya da ayni esik/rapor adimini oraya da ekle. Yesil goruntusu veren no-op adim birakma. |
| **P2** | Regresyon | Zamanlama-duyarli 20 perf testi varsayilan pakete girdi, CI'da atlama kapisi yok | backend/tests/performance/test_elk_performance.py — 13 assert'in cogu esik-bazli: :139/:184/:214 throughput (`MIN_ACCEPTABLE_THROUGHPUT = 5000` :47), :306 `assert p99 < 1.0`, :409 `assert peak_mb < 100`, :458 `assert growth_ratio < 1.5`, :541 `assert throughput >= 100`. Dosyada `skipif` YOK (grep: yalniz :412 tek bir skipif var); yalnizca `@pytest.mark.performance` var, pytest.ini'de bu marker deselect EDILMIYOR (addopts: `-v --strict-markers --tb=short -… | Ya `-m "not performance"` ile CI'dan disla, ya da dosyaya `pytest.mark.skipif(os.getenv("CI"), ...)` benzeri kapi koy. En azindan bir kez CI'da kosturup gecip gecmedigini olc. |
| **P3** | Regresyon | Yeniden takibe alinan perf testinde makineye-cakili mutlak yol | backend/tests/performance/test_elk_performance.py:33 `sys.path.insert(0, "c:/Users/husey/kiro2/backend")` — commit 962f7d4c9 ile ILK KEZ takibe alindi ve toplaniyor. Commit mesaji: "Geri kazanilan 3 dosya kapidan ILK KEZ geciyor ... 8 ruff ihlali duzeltildi (RUF059 x5, RET504, B007 x2)". | Satiri sil (pytest.ini `pythonpath = . app` zaten yolu veriyor) veya `Path(__file__).resolve().parents[2]` ile turet. |
| **P3** | Vakum test | F21-yeni testi AST'te sadece 'ciplak cagri degil' diyor — atama-ama-kullanma mutasyonunu yakalamiyor | backend/tests/unit/test_smtp_zinciri.py:209-219: `ciplak_cagri = [d for d in ast.walk(hedef) if isinstance(d, ast.Expr) and isinstance(d.value, ast.Call) and getattr(d.value.func, "id", "") == "_send_veli_onay_email"]` ; `assert not ciplak_cagri`. Kosuldu: `pytest tests/unit/test_smtp_zinciri.py -q` -> 6 passed. Hedef secimi: `next(d for d in ast.walk(agac) if isinstance(d, ast.AsyncFunctionDef) and "resend" in d.name.lower())` — kontrol kolu: `grep -n "a… | Sozlesmeyi HTTP katmaninda civile (test_admin_content_update.py'deki `app.dependency_overrides` deseni bu depoda calisiyor — 200/404 testleri oyle yazilmis); veya AST testini "donus degeri bir kosula bagli olmali (If/BoolOp icinde kullanil… |
| **BILGI** | Yanlış iddia | BILGI — tuketici entegrasyon testi bu ortamda KOSMUYOR (asiliyor), "23/23 PASS" tekrar uretilemedi | `pytest tests/integration/test_password_recovery_flow.py --timeout=60 -q` -> 150+ saniye boyunca cikti dosyasi TAMAMEN BOS (arka plan is b7svj7829), toplama asamasi bile satir uretmedi. Karsilastirma kontrol kolu: `pytest tests/unit/test_smtp_zinciri.py -q` -> 0.68s'de `6 passed`. Depo bu asilmayi zaten biliyor: tests/unit/test_smtp_zinciri.py:186-188 "HTTP katmanindan sinamak icin authed istemci gerekiyor; bu depoda authed istek asiliyor". | Asilmanin nedenini ayri bir gorevde bul (authed TestClient deadlock'u zaten #468/test altyapisi kaleminde). O zamana kadar commit mesajlarinda bu paketi "dogrulama kaniti" olarak gostermeyi birak. |

### A.1 FSRS restore

| Önc. | Tür | Bulgu | Kanıt (ankraj) | Önerilen |
|---|---|---|---|---|
| **P1** | Kaçan kardeş | Bekci, /due'nun GERCEK SQL'indeki mv_safe_for_beta'yi HIC gormuyor | backend/app/services/fsrs_service.py:74 ve :113 — `_FETCH_DUE_SQL` ve `_FETCH_DUE_MERCY_SQL` duz literal + `f" AND {safe_for_beta_sql('q.id')}\n"` + duz literal seklinde BIRLESTIRILIYOR. `safe_for_beta_sql` (backend/core/quality_gate.py:93-103) `SELECT id FROM mv_safe_for_beta` dondurur (quality_gate.py:69 `SAFE_POOL_RELATION`, :78 `_SAFE_POOL_ID_SQL`). Bekcinin cikaricisini (test_fsrs_schema_contract.py:61-82) dosyaya birebir uyguladim: app/services/fsrs… | Cikariciyi calisma-zamani SQL uzerinden yurut (ornegin `str(_FETCH_DUE_SQL)` gibi modulu import edip `text()` nesnelerinin derlenmis metnini tara) veya `SAFE_POOL_RELATION`/`SAFE_POOL_SOURCE_VIEW` sabitlerini bekciye acikca ekle. |
| **P1** | Vakum test | Olcum aleti matview'leri GOREMIYOR — information_schema.tables matview listelemez | backend/tests/integration/test_fsrs_schema_contract.py:85-92 — `_canli_tablolar()` docstring'i 'Canli semadaki tablo + view adlari' diyor ama sorgu `SELECT table_name FROM information_schema.tables WHERE table_schema='public'`. CANLI OLCUM (psycopg2, salt-okunur): to_regclass -> ('mv_safe_for_beta', 'v_safe_for_beta', 'user_item_fsrs', None) information_schema.tables icinde -> ['user_item_fsrs', 'v_safe_for_beta'] Yani `v_safe_for_beta` (normal view) list… | `_canli_tablolar()` sorgusunu `information_schema.tables` UNION `pg_matviews` (veya `pg_class WHERE relkind IN ('r','v','m','p','f')`) yap ve kontrol koluna bilinen bir matview adi ekle (bugun 'mv_safe_for_beta' bilinen-VAR olmali). |
| **P1** | Eksik fix | Sessiz kayip SADECE FSRS degildi — ayni oturumda streaks + weekly_progress da yutuluyordu, commit bunu saymiyor | backend/app/services/fsrs_service.py:347-374 — `apply_batch_reviews` her review'i KENDI `except Exception` icinde yutuyor (satir 362-367) ve **rollback YOK**. Hata DB'den geldigi icin AsyncSession transaction'i abort durumunda kalir; sonraki `get_item_state` cagrilari da duser, `written` 0 kalir ve fonksiyon NORMAL doner. backend/app/services/cat_session.py:1017-1041 — disaridaki `except Exception` (satir 1039) bu yuzden HIC tetiklenmez; commit mesajindak… | `apply_batch_reviews` except blogunda `await self.db.rollback()` (veya per-review SAVEPOINT/`begin_nested`) uygula; streak/weekly blogunu ayri bir session/savepoint'e al. En az bir RED testi: user_item_fsrs erisilemezken streaks yazimi HAL… |
| **P2** | Kaçan kardeş | 'Sinif bekcisi' 150 uretim dosyasindan 2'sini tariyor | backend/tests/integration/test_fsrs_schema_contract.py:43-46 — `SQL_KAYNAKLARI` sadece `app/services/fsrs_service.py` ve `app/api/fsrs.py`. Ayni cikariciyi app/services, app/api, services, api, core altinda kosturdum (__pycache__ ve _deprecated haric): Ham SQL tablo referansi TASIYAN uretim dosyasi sayisi: 150 Bekcinin taradigi: 2 En yogunlar: app/services/cat_session.py (11 tablo), api/analytics.py (9), core/timezone_orm.py (8), app/api/learning_path_dun… | `SQL_KAYNAKLARI`'ni dizin taramasina cevir (allowlist yerine) veya en azindan cat_session.py / analytics.py gibi yogun ham-SQL dosyalarini ekle. CTE adlarinin yanlis-pozitif uretecegini unutma — `WITH x AS (...) ... FROM x` mevcut regex'te… |
| **P3** | Yanlış iddia | '5 uc 500 veriyordu' — gercekte 4 HTTP ucu (mercy ayri uc degil, Query parametresi) | backend/app/api/fsrs.py:120 `@router.get("/due")` — `mercy: bool = Query(False, ...)` satir 127'de AYNI fonksiyonun parametresi (`get_due_items`, satir 134-136 dallanma). Ayri route DEGIL. user_item_fsrs'e vuran route'lar: /due (120), /review (181), /due-count (211), /stats (225) = **4**. /health (550) DB'ye dokunmuyor (sadece `fsrs_algorithm.turkish_params`). Cikarici da app/api/fsrs.py'de tek bir tablo referansi buldu (/stats icindeki satir-ici SQL). | Docstring'i 'dort uc / bes SQL ifadesi' olarak duzelt. |

### A.4 RLS bekçisi

| Önc. | Tür | Bulgu | Kanıt (ankraj) | Önerilen |
|---|---|---|---|---|
| **P1** | Yanlış iddia | "CI'i kirmiziya cevirir" iddiasi yanlis — hicbir CI isi bu dosyayi kosmuyor | Aktif workflow'lar: ci.yml/quality-gate.yml/quality-gates.yml/golden-flows.yml/security.yml/deploy.yml/claude-ci.yml. - ci.yml:7-13 → `on: push/pull_request branches: [main, master, develop]`. Mevcut dal `feature/self-evolution-optimization`, `git rev-list --count origin/master..HEAD` = **330**. Bu dal icin ci.yml HIC tetiklenmedi ve PR yok. - quality-gate.yml:54,64 sadece `test_router_registration.py` + golden flows kosuyor. quality-gates.yml:138 `... -q… | Ya dosyayi CI'da fiilen kosan bir ise bagla (ci.yml matrisine `-m integration` bacagi + DSN'i env'den oku, `KIRO2_TEST_DSN` fallback), ya da commit/docstring iddiasini "elle kosulan bekci" olarak duzelt. #468 (CI tetikleme) zaten acik. |
| **P1** | Regresyon | `import psycopg2` CI'da kurulu degil — dosya calistirilirsa collection ERROR | test dosyasi:50 `import psycopg2` (modul duzeyi, korumasiz). `backend/requirements.txt:9-10` → `asyncpg`, `psycopg[binary]>=3.1.0` (psycopg **3**; modul adi `psycopg`). requirements.txt'in tamami tarandi, `psycopg2` YOK. ci.yml:248-249 kurulum: `uv pip install -r requirements.txt` + `pytest pytest-cov pytest-asyncio pytest-xdist httpx` (+pyyaml/pillow/tqdm/numpy). deploy.yml:213-215 ayni (requirements.txt + pytest extras). `psycopg2-binary` sadece `requir… | `psycopg2 = pytest.importorskip("psycopg2")` veya `psycopg` (v3) kullan; ayrica `psycopg2-binary` requirements.txt'e eklenecekse bilincli karar olsun. Kardes dosya `tests/integration/test_fsrs_schema_contract.py:31` ayni sekilde duzeltilme… |
| **P2** | Eksik fix | Tuzak dedektorunun kendisinde skip kapisi yok — DB yoksa SKIP degil ERROR | test dosyasi:160 `def test_ikinci_organizasyon_permissive_dali_aktif_sizintiya_cevirir() -> None:` — **hicbir fixture almiyor**. Diger 5 test `db_hazir` (satir 81-89) veya `taban_satir` (92-98) uzerinden `psycopg2.OperationalError` → `pytest.skip` koruma zincirine sahip. Dolayisiyla PG:5434/`kiro2` erisilemeyen her ortamda (CI runner'i, ikinci gelistirici makinesi) 5 test SKIP, 1 test `_sorgula` (satir 74) icinde OperationalError ile ERROR verir. Dosyanin… | Testi `def test_...(db_hazir: None)` imzasina cek (tek satir). |
| **P2** | Vakum test | Dedektor kor kalabilir: `org_sayisi == 0` sessizce "tek kiraci" sayiliyor, kontrol kolu yok | test dosyasi:170-173: ``` org_sayisi = _sorgula("SELECT count(*) FROM organizations") if org_sayisi <= 1: return ``` `organizations` RLS + FORCE RLS tasiyor: `backend/alembic/versions/faz1_billing_rls_20260704_billing_org_rls.py:66-70`, politika `_PRED_ID` (satir 50-55) `... IS NULL OR = '' OR id = current_setting(...)`. Bugun DSN `postgres` (superuser, RLS bypass) oldugu icin sayim dogru; ama `<= 1` dali **0'i da** yutuyor ve 0 saglikli bir DB'de imkansi… | `assert org_sayisi >= 1, "organizations 0 satir gorundu — dedektor kor, olcum gecersiz"` ekle (alet dogrulamasi); `<= 1` yerine `== 1` semantigini acikca ayir. |
| **P2** | Vakum test | Politika bekcisi ORAN assert ediyor, TABAN degil — 79'un 78'i silinse test yesil kalir | test dosyasi:196-204: ``` toplam = count(*) FROM pg_policies WHERE schemaname='public' permissive = ... AND qual LIKE '%IS NULL%' AND qual LIKE '%= ''''%' assert toplam == permissive ``` 79 sayisi hicbir yerde assert EDILMIYOR (docstring satir 191 ve commit mesaji "79/79" diyor). Mutasyon (mantiksal): 79 politikadan 78'i DROP + o tablolarda RLS disable → `toplam=1, permissive=1` → **YESIL**. `test_alet_dogrulamasi` (101-114) ve `test_permissive...` (136-1… | `assert toplam >= 79` (veya migration'daki RLS_TABLES + ORG_ID_TABLES listesinden turetilen bir taban) ekle; ayrica `relrowsecurity AND relforcerowsecurity` sayimini da tabana bagla. |
| **P3** | Eksik fix | Tum atlatma olcumu tek tabloya (`refresh_tokens`) dayaniyor — 79 tablodan 1'i orneklendi | test dosyasi:59 `ORNEK_TABLO = "refresh_tokens"`. satir 95, 124, 144, 148, 176 — dosyadaki HER satir-gorunurlugu olcumu bu tek tabloyu kullaniyor. RLS'li tablo evreni: `faz1_rls_20260704_row_level_security.py:33 RLS_TABLES` + `faz1_rls2_...` + `faz1_billing_rls_...:35-40 ORG_ID_TABLES` + `organizations`. `test_alet_dogrulamasi` (107-114) FORCE RLS'i yalniz `refresh_tokens` icin dogruluyor. | ORNEK_TABLO yerine migration listelerinden parametrize et (`@pytest.mark.parametrize`) veya en azindan "RLS'li ama FORCE'suz tablo sayisi == 0" invaryantini ekle. |
| **P3** | Yanlış iddia | "163 router dosyasi" olculmemis bir sayi — gercek 153/155 | test dosyasi:28 ve 163-186 (`pytest.fail` mesaji): "163 router dosyasinin 2'sinde", "GUC set etmeyen 161 router dosyasi". Olcum: `ls backend/api/*.py backend/app/api/*.py \| wc -l` = **153**; `grep -rl 'APIRouter(' api/ app/api/ routers/` = **155**; `routers/loader.py` ROUTER_MAPPING girdisi = **155**. Hicbir sayma yontemi 163 vermiyor. Dogrulanan kisim: `grep -rln get_current_tenant api/ app/api/` → `api/org_api.py`, `api/org_billing_api.py` = **2** (dogr… | 153 (veya 155, hangi tanim kullaniliyorsa acikca) yaz; sayiyi ureten komutu docstring'e ekle. |
| **P3** | Eksik fix | `psycopg2` baglantilari kapatilmiyor — her `_sorgula` cagrisinda bir baglanti sizdiriliyor | test dosyasi:74 `with psycopg2.connect(DSN) as baglanti, baglanti.cursor() as imlec:`. psycopg2'de connection context-manager'i **transaction**'i yonetir (commit/rollback), baglantiyi KAPATMAZ; `close()` cagrilmiyor. Dosyadaki cagri sayisi ~10 (db_hazir 1, taban_satir 1, testler 8) → kosum basina ~10 acik baglanti, GC'ye birakiliyor. | `with contextlib.closing(psycopg2.connect(DSN)) as baglanti:` veya `try/finally: baglanti.close()`. |
| **P3** | Eksik fix | `pg_class` sorgularinda sema filtresi yok | test dosyasi:107-111 ve 214-218: `SELECT count(*) FROM pg_class WHERE relname = %s ...` / `relname IN ('users','question_bank','student_answers') AND NOT relrowsecurity` — `relnamespace`/`pg_namespace` join YOK. Karsilastirma: satir 196-199'daki `pg_policies` sorgulari `schemaname='public'` filtresi kullaniyor (yani filtre ihtiyaci fark edilmis, iki yerde uygulanmamis). | `JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'` + `relkind='r'` ekle. |

### A.6 İddia doğruluğu

| Önc. | Tür | Bulgu | Kanıt (ankraj) | Önerilen |
|---|---|---|---|---|
| **P1** | Yanlış iddia | Durum tablosu kendi kapattigi isi "acik" gosteriyor — YENI-1 ve YENI-4 hem kutucukta hem Ek A'da 🔴 | docs/audits/2026-07-31_eksiklik_durum_dogrulamasi.md:407 `- [ ] YENI-1 PUT /admin/content/questions/{id} ayni iki bastiriciyla HALA 500 — F2'nin kardesi, duzeltilmedi` ve :413 `- [ ] YENI-4 test_admin_api.py::TestDeleteQuestion fix'le bayatladi`. Ek A satirlari da 🔴: :577 (`satir 421 await admin_servisi.soru_guncelle(...) POZISYONEL`) ve :580. AMA b93cfcd3c PUT'u duzeltti (backend/api/admin.py:429 `soru_bankasi_servisi.soru_guncelle` + acik sozluk yanit :… | YENI-1 ve YENI-4 kutucuklarini [x] yap, Ek A:577/:580 satirlarini ✅ + ankraj (b93cfcd3c admin.py:429 / 0d0dfd069) ile guncelle. |
| **P1** | Kaçan kardeş | F20 fix'i commit mesajinin saydigi 3 tuketiciden yalnizca 1'ine uygulandi (kacan kardesler KVKK ihlal bildirimi ve saglik alarmi) | Commit 4ddd74383 mesaji aynen: "SMTP_SERVER okuyanlar: core/email_util · core/kvkk_compliance · analytics/health_audit_service (hepsi TUKETICI) ... FIX: email_util artik IKISINI DE kabul ediyor". Olcum (Grep, backend/): backend/core/kvkk_compliance.py:812 `smtp_server = os.getenv("SMTP_SERVER")` ve backend/analytics/health_audit_service.py:755 `smtp_server = os.getenv("SMTP_SERVER")` AYNEN duruyor; yalniz backend/core/email_util.py:37 `os.getenv("SMTP_HOS… | kvkk_compliance.py:812 ve health_audit_service.py:755'i `os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER")` yap (veya ucunu de email_util.send_email'e cevir) + iki isim icin tek bir ortak cozucu ve onu civileyen test. |
| **P1** | Yanlış iddia | "Acik P0 7 → 2" sayaci commit sayiyor, korumayi degil: B4/B4-x P0'i kapali sayildi ama kapi aktif dalda hic tetiklenmiyor | .github/workflows/golden-flows.yml:18-23 `on: push: branches: [main, master, develop]` + `pull_request: branches: [main, master, develop]`. `git rev-list --count master..HEAD` = **330** (aktif dal feature/self-evolution-optimization). Belge :244 ve :250'de B4 ve B4-x `- [x] ✅` isaretli ve §0.5 "Acik P0 sayisi: 7 → 2" diyor. AYNI belge :396 ve latest.md:24 ise aynen: "#462'de kapiyi gercek yaptim ama KOSMUYOR → degeri sifir" (F8-b, acik). | B4/B4-x'i "kismen" olarak isaretle veya F8-b (tetikleme) kapanana kadar P0 sayacinda tut; aksi halde #468'e kadar sayac yaniltici. |
| **P2** | Kaçan kardeş | F21 fix'i yalniz /veli-onay/resend'e uygulandi; asil KVKK yolu olan kayit cagirisi (auth.py:711) ciplak kaldi ve AST bekcisi onu YAPISAL olarak gorem… | backend/api/auth.py:711 `_send_veli_onay_email(kullanici_data.veli_email, token)` — ciplak ast.Expr, sonuc atiliyor; hemen ardindan :717-722 kosulsuz `return {"success": True, "message": "Kullanici kaydi basariyla olusturuldu"}`. Fix yalniz :2370'e (resend) uygulandi (503). Bekci testi backend/tests/unit/test_smtp_zinciri.py:198-204 `next(... if isinstance(d, ast.AsyncFunctionDef) and "resend" in d.name.lower())` — hedefi ADIYLA resend'e kilitli, dolayisi… | Ya :711'de sonucu bir dala bagla (yanitta `veli_onay_email_gonderildi: bool` alani), ya da bekci testini modul genelinde ciplak `_send_veli_onay_email` cagirisi arayacak sekilde genislet (o zaman su an KIRMIZI verir — mutasyon kaniti). |
| **P2** | Eksik fix | Y6 ✅ isaretli ama recete uygulanmadi: `.gitignore:266` hala ankrajsiz `performance/` — kok kaynak paketi silinmeye devam ediyor | Checklist :370 `- [x] ✅ Y6 · .gitignore:266 ankrajsiz performance/ → /performance/ YAP + git add -f ...`. Gercek dosya: `.gitignore:266` = `performance/` (ANKRAJSIZ, degismemis); :271 = `!backend/tests/performance/` (yalniz negasyon eklenmis). Probe (git check-ignore -v): `performance/newfile.py -> .gitignore:266`, `frontend/performance/x.ts -> .gitignore:266`, `orchestrator/performance/y.py -> .gitignore:266`, `backend/performance/z.py -> .gitignore:266`… | `.gitignore:266`'yi `/performance/` yap (recete zaten yazilmisti) veya kok `performance/` kaynak paketini de negasyonla geri al; sonra `git check-ignore -v performance/x.py` ile NOT_IGNORED dogrula. |
| **P2** | Vakum test | DEPLOY kutucugu ✅ ama olcum bu oturumun kodundan ONCE kosuldu; hicbir yerde rebuild kaydi yok | §3.2-SONUC :327 `3 \| Backend imaji \| soru_bankasi_servisi.soru_sil = 1, zaten_mevcuttu = 1 ... DEPLOY → ✅ KAPANDI`. Bu iki imza a30416f34 (ONCEKI oturum, DELETE+POST) urunu. Olcum turu (#460) §0.5'te ilk sirada, commit'siz; sonra 03:14 b93cfcd3c (admin.py PUT), 10:16 4ddd74383 (auth.py + email_util.py) geldi (`git log --date=format:%H:%M`). `grep -i "rebuild\|docker\|imaj\|deploy" .claude/sessions/latest.md` → TEK isabet :62, o da operatore SMTP icin verilen… | DEPLOY kutucugunu geri ac veya "olcum zamani: b93cfcd3c oncesi" notu dus; sonraki oturumun ilk adimina backend rebuild + PUT/SMTP canli probu koy. |
| **P3** | Yanlış iddia | "Uretimden cagrilan tek metot (admin.py:421)" — kendi fix'inden sonra bayatlamis ankraj; ayrica ayni belgede 14 / 16 / 17 diye uc farkli sayi var | Belge :53 `@admin_required 14 metotta bozuk \| 17 metot korumali, ama uretimden cagrilan TEK metot (admin.py:421). Kalan 16 olu kod`. AST olcumu (services/admin_service.py): `@admin_required` = 16, `@super_admin_required` = 1 → 17 (dogru). AMA admin.py:421 artik bir YORUM satiri (`# admin_servisi.soru_guncelle POZISYONEL cagrildigi icin`). Grep `admin_servisi\.` backend genelinde uretimde yalniz admin.py:441 ve :498 → ikisi de `admin_aktivite_kaydet`, ki o… | Satiri "olcum aninda tek uretim cagirani vardi (admin.py:421, b93cfcd3c ile kaldirildi); simdi 17 dekoratorlu metodun uretim cagirani 0" olarak duzelt; Ek A:582'deki 14'u 16'ya cek. |
| **P3** | Yanlış iddia | F20/F21/F21-yeni kutucukta ✅ ama Ek A envanterinde hala 🔴 — belgenin iki yarisi celisiyor | Checklist :388-390 uc kalem de `- [x] ✅`. Ek A §A.2 satirlari (belge :606-608 civari) aynen 🔴: "F20 \| SMTP_HOST vs SMTP_SERVER anahtar ayrisimi DUZELMEDI", "F21 \| Veli onay e-postasinda donus degeri HALA kontrol edilmiyor", "F21-yeni \| /veli-onay/resend gonderim olmesine ragmen 'gonderildi' diyor". Commit 4ddd74383 + ef6bafe47 bunlarin (kismi) fix'i. | Ek A §A.2 uc satirini ✅ + ankraj yap; F20'yi ise (bkz. kacan kardes bulgusu) "KISMI — 1/3 tuketici" olarak isaretle. |

### A.5 SMTP zinciri

| Önc. | Tür | Bulgu | Kanıt (ankraj) | Önerilen |
|---|---|---|---|---|
| **P1** | Kaçan kardeş | KACAN CAGRI YERI: kayit yolu (auth.py:711) yeni bool'u OKUMUYOR — F21 orada aynen duruyor | backend/api/auth.py:711 -> `_send_veli_onay_email(kullanici_data.veli_email, token)` — ciplak ifade, donus atilmiyor. Fonksiyon artik `-> bool` (auth.py:2264). Cagri yerlerinin tamami: `grep -n "_send_veli_onay_email" api/auth.py` -> 711 (ciplak), 2264 (tanim), 2370 (atanmis). Cagri `try/except Exception` icinde (712-713) ve endpoint 716-720'de kosulsuz `{"success": True, "message": "Kullanici kaydi basariyla olusturuldu"}` donuyor. | En azindan yanit govdesine `veli_onay_email_gonderildi: bool` alani ekle (kayiti 503 yapmak dogru degil, kullanici olusturuldu) ve gonderilemedigi durumu istemciye bildir; ayrica :711 icin bir cagri-yeri testi ekle. |
| **P2** | Eksik fix | send_email GONDERIM BASARISIZKEN DE True donuyor — "gonderildi yalani" sinifi kapanmadi | backend/core/email_util.py:43-63. Canli olcum (salt-okunur, 127.0.0.1:1 reddedilen port): $ SMTP_HOST=127.0.0.1 SMTP_PORT=1 SMTP_USERNAME=u SMTP_PASSWORD=p python -c "...send_email(...)" email gonderim hatasi (a@b.com): [WinError 10061] ... baglanti kurulamadi blocking=True -> True blocking=False -> True Satir 51-57: `_send()` TUM exception'lari yutuyor (`except Exception: logger.error`), satir 63 kosulsuz `return True`. Yani donus degeri "gonderildi" DEG… | blocking=False yolunda donus degeri bir vaat degildir — ya `blocking=True` + gercek sonuc dondur, ya da `_send()` icindeki basarisizligi bir kuyruk/durum kaydina yaz ve ucun sozlesmesini "kuyruga alindi, teslim garanti edilmez" olarak duze… |
| **P3** | Vakum test | VAKUM: F21-yeni'nin 503'u hicbir test tarafindan civilenmemis (AST testi mutasyonda dusmez) | backend/tests/unit/test_smtp_zinciri.py:209-219 — test yalnizca `ast.Expr` govdeli `_send_veli_onay_email` cagrisi ARIYOR. api/auth.py:2370'te satir `kuyruga_alindi = _send_veli_onay_email(...)` bir `ast.Assign`. `if not kuyruga_alindi: raise HTTPException(503)` blogu (2371-2378) TAMAMEN SILINSE bile `ciplak_cagri` listesi bos kalir -> assert gecer. Kapsam kontrolu: `grep -rln "veli-onay/resend\|veli_onay_resend" tests/` -> yalnizca test_smtp_zinciri.py. Y… | AST testini `raise ... 503` dalinin varliginı arayacak sekilde guclendir veya (tercihen) `_send_veli_onay_email`'i monkeypatch'leyip fonksiyonu dogrudan cagiran bir birim testi yaz: False -> HTTPException(503), True -> 200. |
| **P3** | Vakum test | VAKUM: SMTP_HOST onceligi ("tercihli") hicbir testte olculmuyor | backend/tests/unit/test_smtp_zinciri.py:144-150 `test_iki_anahtar_da_varsa_catisma_yok` — SMTP_HOST=smtp.ornek.com + SMTP_SERVER=smtp.ikinci.com set ediliyor, tek assert `is True`. Fixture `sahte_smtp` hangi sunucuya baglanildigini KAYDEDIYOR (satir 65: `gonderilenler.append(f"baglanti:{sunucu}:{port}")`) ama bu test o listeye HIC bakmiyor. Diger 5 testin hicbirinde iki anahtar birlikte set edilmiyor. Sonuc: core/email_util.py:37'deki `os.getenv("SMTP_HOS… | Ayni teste `assert "baglanti:smtp.ornek.com:587" in sahte_smtp` ve `assert "baglanti:smtp.ikinci.com:587" not in sahte_smtp` ekle (tek satir, mutasyonu dusurur). |
| **P3** | Regresyon | 503 YIKICI: resend, ONCEKI GECERLI token'i once olduruyor, sonra 503 diyor | backend/api/auth.py:2366 `token = await svc.resend(...)` -> services/veli_onay_service.py:170 -> `request_consent` (satir 49-70): mevcut pending kayitlar icin `c.status = "expired"; c.token_hash = None`, ardindan yeni kayit + `await self.db.commit()` (satir 69). Gonderim ve 503 bundan SONRA geliyor (auth.py:2370-2378). Commit mesaji yalnizca "Token URETILIYOR (geri alinmiyor)" diyor — yok edilen ESKI token'dan hic bahsetmiyor. | Sirayi tersine cevir: once gonderilebilirligi dogrula (veya gonder), ancak basarili olursa eski pending'i invalidate et. Alternatif: 503 yolunda transaction'i rollback et. |
| **P3** | Eksik fix | F20 YARIM: kvkk_compliance ve health_audit_service hala yalniz SMTP_SERVER okuyor | backend/core/kvkk_compliance.py:812 `smtp_server = os.getenv("SMTP_SERVER")` ve backend/analytics/health_audit_service.py:755 ayni satir — ikisi de dokunulmamis. Commit mesaji bu iki dosyayi "TUKETICI" olarak ISMEN listeliyor ama yalnizca email_util duzeltilmis. Depoda SMTP_SERVER'i tanimlayan HICBIR env dosyasi yok: `.env.example`, `.env.production`, `.env.production.template` -> SMTP_HOST=1 / SMTP_SERVER=0; diger 5 env dosyasinda ikisi de 0. Hafifletici… | Iki dosyayi da `core.email_util.send_email`'e devret (tekrarlanan SMTP blogunu sil) veya en azindan `os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER")` yap. |
| **P3** | Yanlış iddia | Fix sonrasi operator log'u hala yanlis anahtari soyluyor | backend/api/auth.py:1572-1576 — SMTP yapilandirilmamisken atilan ERROR: "SMTP_SERVER / SMTP_USERNAME / SMTP_PASSWORD gerekli." Ayni oturum email_util.py:35-36'da "SMTP_HOST tercih edilir cunku dogrulayicilarin ve .env sablonunun kullandigi ad odur" diye yaziyor ve commit mesajinda operatore "SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM girin" diyor. | Mesaji "SMTP_HOST (veya SMTP_SERVER) / SMTP_USERNAME / SMTP_PASSWORD gerekli" yap. |
| **P3** | Vakum test | Test asimetrisi: ef6bafe47 iki kardesten yalnizca birini gucledirdi | backend/tests/unit/test_smtp_zinciri.py:112-118 `test_smtp_server_ile_gonderim_calisir` -> tek kanit assert'i `assert "gonderildi" in sahte_smtp`. Kardesi :121-141 `test_smtp_host_ile_de_gonderim_calisir` -> `baglanti:smtp.ornek.com:587` + `starttls` + `login:kullanici` + `gonderildi` (4 assert, ef6bafe47 ile eklendi). ef6bafe47 commit mesaji: "Onceki hali yalnizca 'gonderildi' bakiyordu; yanlis sunucuya duz metin gonderimi yapilsa bile gecerdi." | Ayni 3 assert'i :118'e de kopyala (veya ortak bir `_gonderim_dogrula(sahte_smtp, sunucu)` yardimcisina cikar). |

### A.3 Admin PUT

| Önc. | Tür | Bulgu | Kanıt (ankraj) | Önerilen |
|---|---|---|---|---|
| **P1** | Eksik fix | PUT artik 500 vermiyor ama istemcinin gonderdigi HICBIR alani yazmiyor — ve yazdim diyor | backend/services/soru_bankasi_service.py:1239 `if hasattr(soru, alan)` — eslesmeyen anahtar SESSIZCE atlanir. Olculdu (salt-okunur python, backend/): `soru_metni False · konu False · dogru_cevap False · secenekler False · zorluk_seviyesi False · sinav_tipi False · difficulty False` / `question_text True · exam_type True · subject_area True`. Istemci sozlesmesi TAM OLARAK bu Turkce anahtarlari gonderiyor: frontend/src/services/adminService.ts:67-75 (Create… | Router'da POST/kardes-uc ile ayni Turkce->ORM anahtar ceviri katmanini uygula (bkz. backend/api/soru_bankasi.py:825-843) VEYA bilinmeyen anahtarlari 400 ile reddet. `guncellenen_alanlar` istenen degil GERCEKTEN uygulanan alanlardan uretilm… |
| **P2** | Kaçan kardeş | Kardes uc ayni sinifi tasiyor: `zorluk_seviyesi` -> `difficulty` da sessizce dusuyor | backend/api/soru_bankasi.py:843 `guncelleme_verisi["difficulty"] = request.zorluk_seviyesi`. Model olculdu: `hasattr(QuestionBankItem,"difficulty") == False` (kolon adi `difficulty_level`, backend/models/question_bank.py:333). Dolayisiyla backend/services/soru_bankasi_service.py:1239 filtresi bu alani atar; backend/services/soru_bankasi_service.py:1246-1249'daki `elif alan == "difficulty"` enum-donusum dali ULASILAMAZ olu koddur. Yanit yine de backend/api… | `difficulty` -> `difficulty_level` (+ QuestionDifficultyLevel enum donusumu) esle veya olu dali sil; her iki ucta `updated_fields`/`guncellenen_alanlar`'i servisin gercekten uyguladigi alanlardan uret. |
| **P2** | Regresyon | Fix 'kardes desen' diyor ama kardesin cache gecersizlestirmesini almadi — yazma yolu artik canli, okuma 2 saat bayat | Kardes uc her yazmadan sonra cagiriyor: backend/api/soru_bankasi.py:766, :855, :944 `await invalidate_question_cache()` (tanim :39-45). Yeni admin PUT'ta (backend/api/admin.py:417-460) ve 30 Tem'de duzeltilen admin DELETE'te (backend/api/admin.py:470-505) boyle bir cagri YOK — `grep -n invalidate_question_cache backend/api/*.py` yalnizca soru_bankasi.py'de 4 isabet veriyor. Okuma yolu cache'li: backend/services/soru_bankasi_service.py:451 `cache_key = f"s… | `soru_guncelle`/`soru_sil` servis metotlarinda basarili commit sonrasi `cache_manager.delete(f"soru:{soru_id}")` (+ liste namespace temizligi) yap; tek noktada cozulunce her iki uc da duzelir. |
| **P2** | Yanlış iddia | Dokunulan testin ADI ve docstring'i hala 500 diyor, assert 404 — kaynak-i hakikat kendi kendisiyle celisiyor | backend/tests/unit/test_admin_api.py:845 `async def test_delete_question_returns_500_when_not_found`; docstring :848-856 hala 'endpoint currently returns 500', 'the bare `except Exception` ... replaces it with a 500', 'This test documents the current (buggy) behaviour'; ayni testin assert'i :877 `assert response.status_code == 404`. Commit 0d0dfd069 bu testi DEGISTIRDI (patch hedefi + `mock_sil.assert_awaited_once()`) ve ikizini yeniden ADLANDIRDI (`test_… | Adi `test_delete_question_returns_404_when_not_found` yap; docstring'i a30416f34 sonrasi gercek davranisi anlatacak sekilde yeniden yaz. |
| **P2** | Eksik fix | YENI-8 kabul edildi ama uc tarafinda ucuz bir ayrim varken yapilmadi: DB arizasi 404 'Soru bulunamadi' diye raporlaniyor | backend/services/soru_bankasi_service.py:1266-1270 `except Exception as e: await session.rollback(); logger.error(...); return None` — bulunamadi (:1234 `if not soru: return None`) ile AYNI deger. Yutulanlar arasinda `_enum_donusturucu` hatalari (:1240-1252), IntegrityError, baglanti kopmasi var. Router bunu kosulsuz 404'e ceviriyor: backend/api/admin.py:437-439. Kardes uc de ayni (backend/api/soru_bankasi.py:849-852). | Router'da `None` gelince once `await soru_bankasi_servisi.soru_getir(soru_id)` ile varligi teyit et: soru VARSA 500 (+ log), YOKSA 404. Servise dokunmadan ayrimi kurar. |
| **P3** | Vakum test | 4 TDD testinin biri vakum: dekorator KAYNAK METNINDE substring ariyor, fix'ten once de sonra da gecer | backend/tests/unit/test_admin_content_update.py son test `test_dekorator_hala_soru_id_yi_kullanici_saniyor`: `kaynak = inspect.getsource(admin_service.admin_required)` + `assert "args[0] if args else None" in kaynak`. b93cfcd3c yalnizca backend/api/admin.py'yi degistirdi; backend/services/admin_service.py:31 dokunulmadi — yani bu assert fix ONCESI de aynen geciyordu. Kosuldu: 4 passed (tests/unit/test_admin_content_update.py, 11.79s). | Ya davranisa cevir (`admin_servisi.soru_guncelle(<id>, {})` cagir ve `AdminAuthorizationError` bekle — kaldirma deneyi), ya da assert'i tersine cevirip 'dekorator duzeltildiyse router deseni gozden gecirilsin' seklinde acikca xfail/skip-ca… |

---

## Ek B — 31 Tem denetiminden devreden açık kalemler

> 50 kalem. Ayrıntılı kanıt: `2026-07-31_eksiklik_durum_dogrulamasi.md` Ek A.

- [ ] B5 · Tenant GUC'u 163 router dosyasının 2'sinde
- [ ] B2/#441 · SMTP kimlik bilgisi *(operatör)* — §3.2
- [ ] B1-canlı · ES takası canlıda mı *(operatör)* — §3.2
- [ ] DEPLOY · Admin fix'leri canlı imajda mı *(operatör)* — §3.2
- [ ] 6. CI fix sonrası ilk koşum yeşil mi (B3 — önce `gh` kurulmalı)
- [ ] #458a-ref · Silinen e2e dosyasına 14 bayat referans (2'si sahte alarm).
- [ ] `Y3` Admin reindex ucu TypeError'la kapalı (tasarım değil kaza) — kapıyı ve alan
- [ ] `Y1` `_senkronla` gövdesi hiçbir testte çağrılmıyor; 8 test yalnız saf yardımcıları
- [ ] `Y2` Advisory kilit ES işi başlamadan düşüyor (xact kapsamlı, blok satır 83'te bitiyor).
- [ ] `Y4` `/similar` ucu takas sonrası yapısal olarak 0 sonuç döner (MLT alanları index'te yok).
- [ ] `F8-b` Ayrıştırma düzeldi, tetikleme düzelmedi. 11 workflow'un dal-push tetikleyicisi
- [ ] `#390` `gh` CLI kurulu değil; 20 açık PR'ın 20'si Dependabot *(operatör)*.
- [ ] `N1` Permissive politikayı haklı çıkaran "app-katman savunması" kodda yok —
- [ ] `F7` 79/79 politika aynı permissive kalıpta; desen 26 Tem'de eklenen yeni tabloda da sürüyor.
- [ ] `B5-c` `users` / `student_answers` hiçbir RLS listesinde değil (gerekçe de yazılmamış).
- [ ] `YENI-1` PUT `/admin/content/questions/{id}` aynı iki bastırıcıyla hâlâ 500 —
- [ ] `F2-B` İki "seri bağlı sebep" kaldırılmadı, atlandı. Bozuk `@admin_required`
- [ ] `YENI-2` Fix'in servis yarısı (`zaten_mevcuttu`) sıfır test kapsamında — mutasyon
- [ ] `YENI-4` `test_admin_api.py::TestDeleteQuestion` fix'le bayatladı (patch artık tutmuyor).
- [ ] `YENI-7` Paralel yüzey `/content-management/questions` tamamen mock —
- [ ] `YENI-6` "Denetim kaydı" DB'ye yazmıyor, `logger.debug` — B2B/KVKK için
- [ ] `T1` Paket uçtan uca koşamıyor. Kaldırma deneyi: `backend/conftest.py:124-135`
- [ ] `T2` 27 kırık test — `test_analytics_api.py`'ye denetimden sonra hiç dokunulmadı.
- [ ] `T3` `skipif(True)` modül sayısı 100 → 99 (yalnız silinen dosya kadar azaldı).
- [ ] `T4` Coverage eşiği `backend/.coveragerc:103` = 60.0 duruyor; `source` listesinde
- [ ] `F17` Eşzamanlı sınav oturumu kısıtı üç katmanda da yok (ORM/migration/uygulama).
- [ ] `F17b` 409 bekçisi kodda var ama üretimde kayıtlı değil
- [ ] `F23` CLAUDE.md 2026-05-12 tarihli 105.152 satırlık partiden (tablonun %56'sı) hiç bahsetmiyor.
- [ ] `Y1(kod)` `learning_path.py` ölü router (1.829 satır / 18 uç) — 2 frontend çağrısı
- [ ] `D0` CLAUDE.md 69 gündür dokunulmadı — 19 sapmanın ortak kök nedeni.
- [ ] `Y2(kod)` `litellm_chat.py` 0 bayt, loader'da kayıtlı, git'te yok
- [ ] `Y7` `study_rooms_stub` 7 rotayı gölgeliyor
- [ ] `Y8` `_deprecated` importer 8 dosya / 18 satır
- [ ] `Y4(kod)` 24 `.bak` auth dosyası git'te takipli (toplam 30)
- [ ] `Y5` `.git` 6,52 GiB (MEMORY.md 218 MB diyor)
- [ ] `Y3(kod)` 20 mock bayrağından 6'sı ölü
- [ ] `F9` 4 yetim frontend testi — hedef modül diskte yok
- [ ] `F10` 3 eksik modül + yanlış yola `ElasticsearchConfig` import'u
- [ ] `F11` `backend/.coveragerc` source listesinde `models` yok
- [ ] `F19` `timeout_func_only` çelişkisi (kök `true` / backend varsayılan `False`)
- [ ] `T5` 17 frontend test dosyası hâlâ koşamaz (13 Playwright + 4 yetim)
- [ ] `F14` `eslesmis_sorucevap.jsonl` git'te takipsiz (provenance kırılganlığı)
- [ ] `F15` `question_number` kolon değil, metadata'ya da yazılmıyor
- [ ] `F6` `human_verified` kolu kodda duruyor, DB'de 0 satır
- [ ] `OTURUM-1` Sınıf silme ucu gerçekten yok — GF CI her koşumda çöp bırakıyor (31 sınıf)
- [ ] `OTURUM-2` `soru_bankasi_service.py` lint borcu (E712) — önce dosyayı kapsayan test
- [ ] `D3` `D5` `D8` `D9` CLAUDE.md/MEMORY.md kalan bayat sayılar
- [ ] `N2` `BaseRepository.update/delete` org filtresi uygulamıyor (N1 kablolanırsa yazma açığı)
- [ ] `N4` `dependencies.py:451-452` yorumu bayat ("App superuser, RLS bypass edilir")
- [ ] `DUELLO` Mount edilmiş `DuelloPage` nullable `seviye`'yi çıplak basıyor
