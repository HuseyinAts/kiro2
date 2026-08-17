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

## Session Handoff — 2026-08-17 (S225)
**Branch:** feature/self-evolution-optimization
**Son commit:** `6f7c5dec3` test(soru-bankasi): mukerrer dali + strangler-bagimsizligi civilendi (#485)
**Push:** ❌ **EDILMEDI** — 3 commit bekliyor (`346150a00`, `efe632828`, `6f7c5dec3`).
**Uncommitted:** bu işin dosyaları temiz. ~3399 kirli dosya = S210 devri, ait değil.

### Yapılanlar — Adım 2 KAPANDI (`toplu_soru_ekle` + API tüketici)
- `346150a00` — **ders kaydı**: `audit-methodology.md`'ye "aynı aracın üç ruff sürümü"
  bölümü + `ders_kaydi.yaml` 102 → **104** (`L-s224-*`), bekçi 9/9.
- `efe632828` — **kod fix'i** (+906/−176): `toplu_soru_ekle` 4 seri kusur + casing,
  `soru_ekle` topic ValueError'ı, API tüketici göçü, HTTP sözleşmesi + sızıntı.
- `6f7c5dec3` — mükerrer dalı + strangler-bağımsızlığı testleri (+81).

### Ölçümler (bu turda üretildi, varsayım değil)
- **4 kusur SERİ**, kümülatif aşamayla birebir doğrulandı: `soru_hash` →
  `primary_topic_id` → `grade_level` → `difficulty_level` enum. Batch **%100**
  düşüyordu; uç **HTTP 201 + success:true + "0/3 eklendi"** dönüyordu.
- **Kusur 4 `LookupError` DEĞİL**: `enums_db.QuestionDifficulty` bir `str` alt sınıfı
  + kolonun `validate_strings=False` → SQLAlchemy ham dize sanıp geçiriyor, PG
  `invalid input value for enum questiondifficultylevel: "medium"` diyor.
- **Casing kusuru BUGÜN ULAŞILAMAZDI** (bir ajan kendi brifingini çürüttü): canlı
  DB'de 0 küçük-harf satır, çünkü batch zaten `soru_hash`'te ölüyordu. 1-4
  düzelince aktifleşirdi → aynı commit'te kapatıldı (S219 deseni).
- **`soru_ekle` KOŞULSUZ kırıktı**: `topic_hierarchy`'nin 12 satırının 12'sinde
  `subject_area` NULL → iki lookup da 0 satır → `ValueError` → HTTP 500.
  Çözüm **GEN sabit fallback** (kullanıcı kararı); 36.967 sorunun 36.967'si zaten GEN'de.
- 🔴 **YENİ: `is_active` ORM varsayılanı `False`, `server_default="true"`'yu EZİYOR.**
  İki sonucu ölçüldü: `uq_qb_soru_hash_active` **kısmi** indeksi (`WHERE is_active
  = true`) yeni satırlara uygulanmıyor → **mükerrer engelleme ÖLÜ**; ve yeni soru
  öğrenciye görünmüyor. Kullanıcı kararı: modele dokunmadan iki yazma yolunda
  açıkça `is_active=True`. **Model varsayılanı hâlâ `False` — diğer yazma yolları
  (scriptler, pipeline, `question_bank_service`, `question_crud_service`) AYNI
  kusuru taşıyor, ölçülmedi.**
- **Mutasyon 12/12** öldü (hiçbiri `error`, her geri alım `git status` ile boş).
- **Regresyon test-test karşılaştırıldı**: 90 önce / 90 sonra, küme **bayt-birebir
  aynı** → yeni kırık 0. (87 ERROR `TestClient(app=...)` httpx uyumsuzluğu, 3 FAILED
  dokunulmayan `soru_performans_guncelle`/`irt_yeniden_hesapla` — ikisi de önceden.)

### Fail Eden Testler
YOK. `test_toplu_soru_ekle_split.py` **12 passed**, iki split dosyası **20/20**.

### Engelleyiciler
- `kiro2-api-import-smoke` — `SKIP=` **kullanıcı onayıyla** (2 commit'te). Kontrol
  koluyla ölçüldü: dokunulmayan `api/health.py` ile de düşüyor (`WinError 127`,
  api.rag/youtube_routes/v1.semantic_search). **Kök neden S211'den beri açık.**
- Commit kanca zinciri **2 dk'yı aşıyor** → kısa timeout'ta commit sessizce düşüyor;
  `git log` hash'i ile doğrulanmalı (bu turda 1 kez yaşandı).

### Sonraki Adımlar (maks 5)
1. **PUSH** — 3 commit bekliyor (kullanıcı onayı).
2. 🔴 **`CacheManager.get_or_compute` YOK** (bağımsız doğrulandı; sınıfta `get_or_set` var).
   `soru_bankasi_service.py:519` ve `:648` → `AttributeError` → çıplak `except` →
   **`GET /soru/{id}` gerçek soruda 404, `GET /sorular` 36.967 aktif soruyla
   200+boş liste.** Testler görmüyor çünkü `:466` `isinstance(cache_manager.get,
   AsyncMock)` ile **teste özel dala** sapıyor. **Kapsam dışıydı, ayrı TDD turu.**
3. 🔴 **`QuestionCRUDService.create_question` ÜÇÜNCÜ yazma yolu** aynı `soru_hash`
   NOT NULL kusuruyla düşüyor (hakem kolu ölçtü). `soru_hash` tek kök neden, 2 çağrı yeri.
4. **Adım 3** (S224'ten devir): `repositories/question_repository.py` silmesini
   commit'le + `_scripts/test_database_repository.py:15` import'unu temizle.
5. `application/commands/sinav.py` (16 erişim, BKT ölü) — ayrı plan.

### Kararlar (gelecek session tekrar tartışmasın)
- **`monkeypatch.delattr` strangler devredicisinde KULLANILAMAZ** — pytest onu
  içeride `hasattr()` ile koruyor, devredici sınıf düzeyinde `AttributeError`
  fırlattığı için `hasattr` **her zaman False** → `raising=False` ile çağrı sessizce
  no-op. Testin ilk sürümü tam bu yüzden **vakumdu** ve kontrol kolu aynı bozuk
  yordamı kullandığı için göremedi. Doğru araç **`vars(cls)`**.
- **API'de parent→yavru göçü BUGÜN çivilenemiyordu** (M10 kaçtı): `refresh()`
  daraltmasından sonra ilişkiler yüklü kaldığı için devredici doğru değeri
  döndürüyor. Değeri **devredici silindiğinde** ortaya çıkıyor → o günü simüle eden
  test yazıldı, M10 artık ölüyor. (S214: çivilenemeyen kod test edilemez ağırlıktır.)
- **`efe632828` mesajı "10 test" diyor, doğrusu 11** — `6f7c5dec3` mesajında
  düzeltildi. Sayı bir ölçümdür, elle sayılmamalı.
- Kapı borcu (dokunulmayan kod, davranış nötr, hepsi HEAD'de vardı): `logger`
  import'ların altına (10× E402), iki md5 cache anahtarına `usedforsecurity=False`,
  1× E402 + 1× SIM102 gerekçeli `# noqa`. Biçimlendirici `SoruEkleRequest`'i de
  süpürdü — **AST ile ölçüldü** (kontrol kollu): import sırası normalize edilince
  fark YOK → davranış nötr.

---

## Session Handoff — 2026-08-17 (S224)
**Branch:** feature/self-evolution-optimization
**Son commit:** `6b87d2a95` fix(soru-bankasi): split gocu + split sonrasi 3 sessiz kusur (#485)
**Push:** ✅ `e2a1ef177..6b87d2a95` (origin ile fark 0)
**Uncommitted:** bu işin dosyaları temiz. Açık: ` D repositories/question_repository.py` (Adım 3).
3399 kirli dosya = S210 devri, ait değil.

### Yapılanlar
- **DB ölçümü:** `question_bank`/`content`/`metadata`/`statistics` = **36.967 her biri, YETİM 0**,
  `mv_safe_for_beta` **27.073** (`auto_judged_high` 27.073 / `pending` 9.894). S223'ün P0'ı KAPANDI.
  Veri oturum içinde 3 kez değişti (0 → 36.967 qb+qc → 4 tablo tam); her brifingde yeniden ölçüldü.
- **`services/soru_bankasi_service.py`** (`6b87d2a95`, +297/−121) — göç (SINIF 41→0) + 3 sessiz kusur:
  `:1441`/`:1534` `.select_from(Question)` (S214 koşullu kuralı, dosyada `select_from` HİÇ yoktu) ·
  `:1458`/`:1488`/`:1498` String kolonda `.value` kaldırıldı (`:1509` **gerçek Enum, KORUNDU**) ·
  `soru_guncelle:1342-1344` `joinedload ×3`.
- **`tests/fast/test_soru_bankasi_service_split.py`** — 8 test, 2'si canlı PG'ye vuruyor.
- **Doğrulama denetimi (26 ajan):** 18 doğrulanmış / 3 fantom bulgu. Fix'lenen 6 P0'ın dışındakiler
  Adım 2-3'e taşındı.

### Fail Eden Testler
YOK. `tests/fast/test_soru_bankasi_service_split.py` → **8 passed**. Regresyon 738 test, test-test
karşılaştırıldı, yeni kırık 0. Mutasyon **9/9 öldü** (hiçbiri `error`). Sayaç `SINIF 102 → 45`.

### Engelleyiciler
- Push 2 kez düştü, **ikisi de ortam kusuru** (aşağıdaki Kararlar'a bak).
- `_blindsolve/w22batches/g28.json` → `git checkout -- .` sırasında NTFS `Invalid argument`;
  pre-commit rollback'i bu yüzden patlıyor. Ayrı triyaj.

### Sonraki Adımlar (maks 5)
1. **Adım 2** — `toplu_soru_ekle` 4 seri kusur (`soru_hash`+`primary_topic_id`+`grade_level` NOT NULL
   doldurulmuyor · `'medium'` vs PG `'MEDIUM'` · `exam_type`/`subject_area` küçük harf) +
   `api/soru_bankasi.py:776` tüketici göçü. **Gövde hiçbir testte koşmuyor (mock'lu).**
2. **Adım 3** — `repositories/question_repository.py` silmesini commit'le +
   `_scripts/test_database_repository.py:15` import'unu temizle (**"sıfır tüketici" iddiası YANLIŞ**,
   `pytest _scripts/` şu an collection error + exit 2).
3. `application/commands/sinav.py` (16 erişim, BKT ölü) — ayrı plan.
4. P2: `_enum_donusturucu` küçük-harf `exam_type` üretiyor → `sinav_tipi` dallı sorgular canlıda 0 satır.
5. PRE-EXISTING: `api/soru_bankasi.py:843` `"difficulty"` anahtarı ↔ kolon `difficulty_level` →
   alan sessizce atlanıyor, uç `200 + updated_fields:["difficulty"]` dönüyor ama zorluk değişmiyor.

### Kararlar (gelecek session tekrar tartışmasın)
- **İKİ FARKLI RUFF SÜRÜMÜ var** — yerel `0.14.13`, pre-commit `v0.7.1` (izole venv,
  `.pre-commit-config.yaml:37`). Yerelde biçimlendirilen dosyayı kapı yeniden biçimlendirir →
  `files were modified by this hook` → **amend sessizce EXIT=1 ile iptal olur ve `git log` aynı
  hash'i gösterir**. Yordam: çalışan ağacı index'le eşitle → `pre-commit run ruff-format --files`
  (KAPININ sürümü) → sabit nokta doğrula → `git add` + amend.
  `reference_precommit-vs-bare-linter`'ın bir adım ötesi: farklı CWD değil, **farklı SÜRÜM**.
- **`# pragma: no cover` gerekçesi İKİNCİ BİR `#` yorumu olmalı** — bekçi
  `r"#\s*pragma:\s*no\s*cover(?!\s*#\s*\w)"` ile ölçüyor; tire (`- gerekçe`) yakalanır.
- **`select_from` koşulludur** (S214): kardeş sorgulara eklenmedi — derlenmiş SQL birebir aynı
  kalıyor, süs olurdu. Ölçüldü, eklenmedi.
- **`.value`'ların hepsi kaldırılamaz:** `QuestionStatistics.difficulty_level` gerçek `Enum`;
  "tümünü sil" aşırı-fix'i M5 mutasyonuyla çivili.
- Bir vakum test **ölçülüp silindi** (fix'ten önce de geçiyordu, servis dosyasından bağımsızdı).
- E2E testleri önce SQLite ölçüyordu (`conftest.py:100` `DATABASE_URL`'i ezliyor) → DSN `.env`'den
  okunuyor + fixture'da ">1000 aktif satır" kontrol kolu.

---

## Session Handoff — 2026-08-17 (S223)
**Branch:** feature/self-evolution-optimization
**Son commit:** `5b709a802` test(osym): golden'i TURKCE + zorluk dallarina genislet (#485)
**Push:** ✅ `173cf62da..310cd39d5` — **9 commit** (S222'nin 4'ü + S223'ün 5'i).
push-secret-guard (962 satır, sır yok) + reward-hacking-check PASS. Son 4 uyarı test
dosyasındaki "magic count" (`count=3`/`count=5`), bloklamıyor.
⚠️ Bu satır ilk yazıldığında **"7 commit" diyordu; yanlıştı** (gerçek 9). Sayı bir ölçümdür —
`git log --oneline origin/<dal>..HEAD | wc -l` ile üretilmeli, elle sayılmamalı.
**Uncommitted:** bu işin dosyaları temiz. ~3387 kirli dosya = S210 Gemini devri, ait değil.

### Yapılanlar — Plan **Task 7 KAPANDI**; `osym_exam_engine.py` `SINIF=42 → 0`
- `f2428eb81` — **37 sınıf-düzeyi erişim JOIN'e** (content 31 / metadata 3 / statistics 3) +
  iki id-havuzu sorgusuna **üçlü JOIN** (ana + zorluk-fallback) + **H1** (boş havuz cache'i).
- `b5fe75a5f` — **H2**: %15 IRT-ankraj kotası devre dışı (`ANCHOR_QUOTA_RATIO = 0.0`, `:158`).
  **Ayrı commit** — psikometri oturumu yalnız bunu geri alabilsin.
- `340b1e2d9` — golden WHERE karakterizasyon testi (7 hayatta kalan mutasyonu öldürdü).
- `5b709a802` — golden'ı TURKCE + zorluk dallarına genişletti + fark çıktısını okunur yaptı.
- **Yürütme:** subagent-driven (implementer → spec reviewer → kalite reviewer → 2 düzeltme turu).

### Ölçümler (bu turda üretildi)
- **`_select_questions` ÖLÜ KODDU** — `:1512` sınıf düzeyinde patlıyordu, altındaki ~200 satır
  hiç koşmamıştı. Bu commit onu **ilk kez** çalıştırılabilir yaptı.
- **Spec reviewer 37'yi TOKEN DÜZEYİNDE kanıtladı:** fonksiyonu iki revizyondan AST ile çıkardı,
  ikisini tokenize etti, HEAD akışında üç yavru sınıf adını `Question`'a geri çevirdi ve diff
  aldı → **273 satırda tek fark, üç kasıtlı düzenleme.** Bu, 37'sini birden operatör/eşik/`~`/
  `or_` sırası değişmemiş diye kanıtlar.
- **Eager-load N/A — ÖLÇÜLDÜ:** iki `select(Question)` sorgusunun tek üretim tüketicisi
  `create_exam_session:403` ve yalnız `len(questions)` + `q.id` okuyor → `selectinload`
  **eklenmedi** (Task 4/5'in tersi; ayrımı yapan şey tüketiciyi okumak).
- **INNER JOIN havuz-nötr, ama KOŞULLU:** üç yetim sınıfından ikisi zaten pre-split
  predicate'lerce eleniyordu; üçüncüsünü (`question_statistics` yetimi) **kalite kapısı**
  yakalıyor (`v_safe_for_beta` LEFT JOIN + `status IN (...)` → yetim NULL → elenir). Yani
  havuz boyutu değişmiyor — **`safe_for_beta_gate(Question.id)` `:1536`'da kaldığı sürece.**
- **H1 guard'ı `rows` üzerine kuruldu, havuz üzerine DEĞİL.** Tek sorgu iki havuz üretiyor;
  boş **anchor** alt kümesi meşru → `if anchor_pool:` sağlıklı veride sonsuza dek yeniden
  sorgulardı. Pre-split kodda (`295f34d9d`) `if pool:` vardı — bu bir **geri getirme**.
- **H2'de `> 0` guard'ı ZORUNLU:** `max(1, round(count * 0.0))` **1** döner, 0 değil
  (3/5/10/20/40/120 için doğrulandı) — naif oran değişimi kotayı "her derse 1 ankraj"da bırakırdı.
- **Golden testi İKİ turda doğru oldu.** İlk hâli MATEMATIK'e kuruldu ve "LaTeX/zorluk dalları
  başka testlerle çivili" diye **ölçülmemiş** bir gerekçe yazdı. Kalite reviewer ölçtü, yanlıştı:
  ikame assert'ler **içerik-kör** → 3 mutasyon hayatta, en ağırı `contains("x^2")` →
  `contains("")` = **TURKCE/EDEBIYAT/TARIH/COGRAFYA/SOSYAL havuzu her sınavda boş** (TYT'de
  TURKCE tek başına 40 soru). Golden 3 parametreye genişletildi.
- **Mutasyon toplamı: 10 (JOIN/H1/H2) + 7 (golden) + 3 (golden genişletme) = 20**, hepsi
  `failed`, hiçbiri `error`. **3 geçersiz ölçüm yakalandı ve ATILDI** (ankraj 3 yere uydu ·
  `IndentationError` → `error` · `base_filters` hoist'i `NameError` veriyor, iki sadık varyantla koşuldu).

### Fail Eden Testler
YOK. `tests/fast/test_osym_exam_engine_split.py` → **27 passed / 0 failed** (tur başında 12/7).
Sayaç: `core/osym_exam_engine.py [SINIF=0 KWARG=2 ENTITY=5]`.
⚠️ **`KWARG=2` GÜRÜLTÜ, kalan iş DEĞİL** — `:1882`/`:1888` Task 6'nın **doğru**
`update(QuestionStatistics).values(...)` satırları; sayaç kwarg **adına** bakıyor, UPDATE
hedefine değil. `ENTITY=5` de beklenen (2'si eager-load'lu, 3'ü N/A).

### Engelleyiciler
- **`question_bank` = 0 satır (bu makine)** — uçtan uca doğrulama YAPILAMIYOR.
- ~3387 dosyalık pre-existing kirli ağaç (S210 devri) — ayrı triyaj.

### Sonraki Adımlar (maks 5)
1. **Push** — 7 commit bekliyor (kullanıcı onayı).
2. **`question_statistics` yetim ölçümü** (S222'den devir, KAPANMADI): dolu DB'de
   `SELECT count(*) FROM question_bank qb LEFT JOIN question_statistics qs ON qs.id=qb.id WHERE qs.id IS NULL;`
   Sonra karar: (a) `rowcount` logu, (b) `'pending'` ile backfill — **ek onay şart**
   (`quality_review_status` öğrenci kapısını besliyor).
3. `services/soru_bankasi_service.py` (41+15) — ayrı plan, P0.
4. `application/commands/sinav.py` (16) — **BKT hiç çalışmıyor**, ayrı plan.
5. `core/irt_daemon.py` KWARG'ları (her IRT kalibrasyon yazımı `CompileError`) ·
   `repositories/question_repository.py` (sıfır tüketici → SİLME).

### Kararlar (gelecek session tekrar tartışmasın)
- **`filters = base_filters` aliasing'i BİLEREK BIRAKILDI.** `list()` kopyası bugün 0 hata
  önlüyor; bedeli `test_latex_filter_does_not_leak_to_next_subject`'i **yapısal olarak
  düşemez** hâle getirmek = vakum test. Çalışan bir dedektörü feda etme (#451 deseni).
- H2 geri alınırken: `git revert b5fe75a5f` **1 çakışma** verir, yalnız **test** dosyasında
  (golden hemen H2 testlerinden sonra eklendi). **Motor hunk'ı temiz döner.** Çözüm mekanik:
  iki H2 testini düşür, golden'ı koru.
- Ana/fallback ~40 satır kopya-yapıştır artık **üç** kavram paylaşıyor (JOIN üçlüsü, H1, H2) ve
  metinsel olarak zaten ayrışmış → **ayrı follow-up görevi hak ediyor** (bu planda yasaktı).

### Açık iş olarak düşen yeni kalemler (kalite incelemesinden, ertelendi)
- INNER JOIN havuz-nötrlüğü kalite kapısına bağlı — `:1532-1535` yorumuna tek cümle.
- `ANCHOR_QUOTA_RATIO` `services/irt_equating_service.py`'den **keşfedilemiyor** (o dosyada
  `is_anchor` hiç geçmiyor) — modül docstring'ine tek satır işaretçi.
- Sabitin yorumu `0.0`'ın etkisini **hafife alıyor**: kota "zorlanmıyor" değil, ankraj
  **hiç servis edilmiyor**.
- Golden `'%%'` paramstyle artefaktına bağlı (`pyformat`) — `postgresql.dialect(paramstyle=...)`
  ile sabitlenmeli veya yoruma yazılmalı.
- `_LATEX_FILTER_NEEDLE` sayımı ve `difficulty_level in where_sql` artık golden ile içerik
  bakımından **fazlalık**; şekil iddiası olarak duruyorlar.
- `:1493` `# nosec B311` yorumu "3 cagri yeri" diyor, **5** oldu (pre-existing).

---

## Session Handoff — 2026-08-17 (S222)
**Branch:** feature/self-evolution-optimization
**Son commit:** `07eb98d8a` test(osym): _analyze_performance UPDATE WHERE kapsamini civile (#485)
**Push:** ✅ S223 ile birlikte gönderildi (`173cf62da..310cd39d5`).
**Uncommitted:** bu işin dosyaları temiz. ~3387 kirli dosya = S210 Gemini devri, bu session'a ait değil.

### Yapılanlar — Plan **Task 6 KAPANDI** (3 commit, motor 1 kez dokunuldu)
- `69ee2566b` — `core/osym_exam_engine.py::_analyze_performance` (+16/-8): SELECT
  `select(Question.id, Question.correct_answer)` → `QuestionContent`'e JOIN; iki UPDATE
  (`times_asked`/`times_correct`) → `QuestionStatistics` (**hedef + `.where()` + `.values()`
  sağ tarafı**, üçü birden). `is_active` korundu, `select_from` EKLENMEDİ (S214).
- `c59326863` — test sertleştirme (+21/-0): `is_active` iddiası + evrensel UPDATE iddiası.
- `07eb98d8a` — test (+69/-13): UPDATE WHERE kapsamı testi + sayı iddiasının ölçümü.
- **Yürütme:** subagent-driven (implementer → spec reviewer → kalite reviewer → 2 düzeltme turu).

### Ölçümler (bu turda üretildi, varsayım değil)
- **Plandaki M8 bir VAKUM MUTASYONUYDU.** M8 iki UPDATE'ten yalnız birini bozuyor; testin o
  günkü hâli varlık iddia ettiği için hayatta kalan diğer UPDATE assert'i doyuruyordu.
  Ölçüldü (düzeltilmiş motor + eski test): **M8a ve M8b ikisi de `4 passed` — HAYATTA KALDI.**
  Spec reviewer bunu **bağımsız harness'le tekrar üretti**. Test sayıya bağlandı → ikisi de `failed`.
- **`is_active` hiçbir şey tarafından çivilenmiyordu.** Filtre silinince **18 testin HİÇBİRİ**
  düşmüyordu (`7 failed/11 passed` = mutasyonsuz HEAD ile birebir). İddia `_compiled_where()`
  üzerine yazıldı (S214), tam SQL'e DEĞİL.
- **`.where(all_answered_ids)` → `correct_ids` swap'i 18 testin hepsinden kaçıyordu** — fixture'ın
  tek sorusu doğru cevaplandığı için iki liste eşitti (S219 "test paketi de bir dilim ölçer").
  Yeni test iki soruyla (biri doğru biri yanlış) çiviledi.
- **Sayı iddiası (`len(stat_updates)==2`) YÜK TAŞIYOR** — kalite reviewer "tamamen gereksiz, sil"
  dedi; ölçüldü ve **yanlış çıktı**. M-SPURIOUS (üçüncü `question_statistics` UPDATE'i,
  `times_asked`/`times_correct` içermeyen): sayı iddiası varken `1 failed`, silinince **`4 passed`
  kaçıyor**. Reviewer'ın mutasyon kümesi o sınıfı içermiyordu. Silinmedi; yanıltıcı yorum düzeltildi.
- **Nihai mutasyon bataryası 8/8** (M7·M8a·M8b·M-EXTRA·M-SPURIOUS·M-WHERESWAP·M-ISACTIVE·M-JOIN),
  hepsi `failed`, hiçbiri `error`, her geri alım boş `git status --short` ile doğrulandı.
- **M-JOIN'e yeni iddia EKLENMEDİ** — mevcut `_assert_single_from` kartezyeni zaten yakalıyor
  (öncesi de sonrası da `failed`). Çivilenemeyen ağırlık eklenmedi (S214).

### Fail Eden Testler
`tests/fast/test_osym_exam_engine_split.py` → **12 passed / 7 failed** (önce 7/11).
7 FAIL **kasıtlı**: hepsi `TestSelectQuestions` (Task 7). Baseline ile **test-test**
karşılaştırıldı (agrega değil) — yeni kırık YOK.

### 🔴 YENİ BULGU — `question_statistics` 1:1 GARANTİ DEĞİL (Task 6'nın kazancını tehdit ediyor)
Task 6'nın iki UPDATE'i, satırı olmayan bir soruda **sessiz no-op**. Ölçüldü:
- **`INSERT INTO question_statistics` depoda HİÇBİR YERDE yok** — backfill yok, **split
  migration'ı da yok**. Aktif zincir tek revizyon (`0001_baseline_squash.py`) ve
  `pg_dump --schema-only` çıktısı, yani backfill İÇEREMEZ. Split commit'i `0fd9b8413`
  **sıfır** migration dosyasına dokunmuş → DDL **alembic dışı** uygulanmış.
- **FK yönü ters:** `question_statistics_id_fkey` çocuk→ebeveyn (`ON DELETE CASCADE`).
  Yetim **çocuğu** yasaklar; her ebeveynin çocuğu olmasını **şart koşmaz**. DB'de **0 trigger**.
  `cascade="all, delete-orphan"` atanmış çocuğu kalıcılaştırır, **üretmez**.
- **`rowcount` hiçbir yazım noktasında kontrol edilmiyor.**
- Bu makinede `qb=0 / qs=0` → **canlı yetim sayısı ÖLÇÜLEMEDİ** ("sıfır" değil).
- Kapı normalde korurdu (`mv_safe_for_beta` `quality_review_status`'ü `question_statistics`'ten
  LEFT JOIN'liyor → yetim NULL → elenir), ama **`_select_beta_questions` o kapıyı uygulamıyor**
  (docstring: "Standart `base_filters` UYGULANMAZ") → yetim o yoldan servis EDİLEBİLİR.
- **Operatör için tek komut** (salt-okunur, dolu DB'de meseleyi bitirir):
  `SELECT count(*) FROM question_bank qb LEFT JOIN question_statistics qs ON qs.id=qb.id WHERE qs.id IS NULL;`
- **Backfill YAPILMADI ve yapılmamalı-diye-karar-verilmedi** — 20 kolon `NOT NULL` ve
  defaultsuz; bunların biri `quality_review_status` ve **öğrenci kapısını besliyor**.
  `auto_judged_high` ile doldurmak denetlenmemiş soruyu havuza sokar. `'pending'` şart.
  **Kullanıcı kararı gerekiyor.**

### 🔴 Blast radius — parent'ı hedefleyen 5 göç edilmemiş `QuestionStatistics` yazımı (#485 backlog)
| Yer | Sonuç |
|---|---|
| `core/irt_daemon.py:210-222` | `CompileError: Unconsumed column names` → **her IRT kalibrasyon yazımı düşüyor**, `:227` `except` yutuyor |
| `services/irt_analysis_service.py:234-243` | aynı (alias `as Soru`) |
| `api/orchestrator_api.py:151-160` | raw SQL `UPDATE question_bank SET irt_difficulty=...` → `column does not exist`, `debug` seviyesinde loglanıyor |
| `repositories/question_repository.py:202-207` | okuma shim'den (çocuk), **yazma parent'a** — asimetrik. Sıfır tüketici → SİLME adayı |
| `services/soru_bankasi_service.py:330-333` | constructor kwarg → `AttributeError` |

Ayrıca latent: `migrations/015_question_bank_stats_triggers.sql:14-19` hâlâ
`UPDATE question_bank SET times_asked = ...` trigger'ı tanımlıyor ve `EXCEPTION WHEN OTHERS
THEN RAISE WARNING` ile sarılı — split şemasına karşı koşulursa **kalıcı sessiz hata** kurar.
Canlıda YOK (0 trigger, ölçüldü).

### Engelleyiciler
- **`question_bank` = 0 satır (bu makine)** — uçtan uca doğrulama YAPILAMIYOR (S219'dan devam).
  Kabul kriteri sorgu-yapısı düzeyinde kalıyor.
- ~3387 dosyalık pre-existing kirli ağaç (S210 devri) — ayrı triyaj.

### Sonraki Adımlar (maks 5)
1. **Task 7** — `_select_questions` 3-yollu JOIN (37 erişim). **Plandaki "TASK 7 TEHLİKELERİ"
   bloğunu OKUMADAN BAŞLAMA.** H1 (boş-havuz koşulsuz cache) → DÜZELT + test YAZ.
   H2 (%15 IRT-ankraj kotası) → `anchor_target = 0`, kod silinmez, gerekçe yorumla.
   ⚠️ **Uyarı (bu turda ölçüldü):** PostToolUse formatter hook'u kapının ruff'undan **farklı**
   bir ruff koşuyor; kullanımdan ÖNCE yazılan import'u F401 diye siliyor ve **ilgisiz assert
   bloklarını yeniden biçimlendiriyor** (bu turda ikisi `TestSelectQuestions` içindeydi).
   Kullanımı önce yaz, import'u sonra; commit öncesi `git diff -w` ile `git diff`'i karşılaştır.
2. **`question_statistics` yetim ölçümü** — yukarıdaki tek SQL'i dolu bir DB'de koştur.
   Sonra karar: (a) `rowcount` logu (bedava, sessizliği sinyale çevirir), (b) `'pending'`
   ile backfill migration'ı (**ek onay şart** — kapıyı besleyen kolon).
3. **Task 8** — handoff düzeltmesi + `ders_kaydi.yaml` satırı.
4. `application/commands/sinav.py` ayrı plan (16 erişim, **BKT hiç çalışmıyor**).
5. Kalan P0: `soru_bankasi_service` 41+15 · `irt_daemon` KWARG'ları · `question_repository`
   16+5 (sıfır tüketici → SİLME).

### Kararlar (gelecek session tekrar tartışmasın)
- **Bir mutasyonun "gereksiz" olduğu iddiası da bir ölçümdür.** Kalite reviewer sayı iddiasını
  "tamamen gereksiz, sil, kesin iyileştirme" diye raporladı; ölçünce yanlış çıktı (M-SPURIOUS).
  Gerekçesi "koştuğum mutasyonların hiçbirini öldürmüyor" idi — bu, **iddianın erişimi hakkında
  değil koşulan kümenin kapsamı hakkında** bir olgudur. Bir assert'i silmeden önce onu **tek
  başına** öldüren bir mutasyon ara.
- **Plandaki mutasyon reçetesi yanlış olabilir.** M8 planda yazılıydı ve vakumdu. Mutasyonun
  `failed` vermesi yetmez — **hangi assert'in** öldürdüğünü ve o assert'in tek başına yük taşıyıp
  taşımadığını da ölç.
- Plan satır ankrajları **her task'ta yeniden ölçülmeli**; Task 4+5 dosyayı +17 kaydırdı.
- Modül düzeyi import eklerken **kullanımı önce yaz** — ruff F401 aksi hâlde siliyor (2 kez ölçüldü).
- `SKIP=` gerekmedi; `pre-commit` depo **kökünden** koşuldu, tüm hook'lar Passed.

### Açık iş olarak düşen yeni kalemler
- `save_answer:705` notlandırma sorgusu `is_active` **filtrelemiyor**, `_analyze_performance:1753`
  filtreliyor → aynı cevabı notlandıran iki yol, soru sınav ortasında pasifleşirse **çelişebilir**.
  Pre-existing (BASE'de de vardı), bu turda dokunulmadı.
- `save_answer`'daki `_select`/`_QC` fonksiyon-gövdesi import'ları artık **saf duplikasyon**
  (ikisi de modül düzeyinde var). Kapsam dışıydı, tek satırlık ayrı commit.
- `tests/fast/test_osym_exam_engine_split.py:459` ve `:556` docstring'leri **bayat satır
  ankrajı** taşıyor (bu tur +8 daha kaydırdı) — #485 sonunda tek süpürmede.
- Planda **34 işaretsiz checkbox** kaldı; Task 0-3 S219'da bitti ama kutuları hiç işaretlenmedi
  → sayının çoğu "bayat", "açık" değil. Task 8'de tek geçişte doğrula.

---

## Session Handoff — 2026-08-16 (S221)
**Branch:** feature/self-evolution-optimization
**Son commit:** `ed07d7fb0` fix(osym): get_subject_performance uc split iliskiyi eager-load ediyor (#485)
**Push:** ✅ `887af3774..63fd61c87` (2 commit), push-secret-guard + reward-hacking-check PASS
**Uncommitted:** bu işin dosyaları temiz. Ağaçtaki ~3387 kirli dosya = S210 Gemini devri, bu session'a ait değil.

### Yapılanlar
- `backend/core/osym_exam_engine.py:1320-1330` — Plan **Task 5** kapandı (`ed07d7fb0`, +8/-0).
  `get_subject_performance` sorgusu üç split ilişkiyi `selectinload` ile eager-load ediyor.
  Kusur Task 4 ile aynı sınıfta: sorgu **kuruluyordu** (sınıf düzeyinde taşınmış alan yok),
  ölen şey dönen **örnek** idi. Döngü `:1345` `subject_area`(metadata) · `:1362`
  `irt_difficulty`(statistics) · `:1367` `correct_answer`(content) okuyor; `:1412`
  `except Exception` `MissingGreenlet`'i yutup `return []` yapıyordu → **HTTP 200 +
  boş ders kırılımı** (500 değil, bu yüzden aylardır görünmedi).
- **Yürütme:** subagent-driven (implementer → spec reviewer → kalite reviewer). Üçü de temiz.

### Ölçümler (bu turda üretildi, varsayım değil)
- **Eager-load fiilen çalışıyor mu:** `.options()` yokken döngü 3 lazy-load tetikliyor
  (`inspect(q).unloaded` = üç ilişki); varken fetch sonrası `unloaded` **boş**.
- **Maliyet (120 soruluk TYT, aynı sorgu şekli):** eager-load yok → **361** SELECT (N+1) ·
  `selectinload` → **4** · `joinedload` → **1**. İlişkiler `uselist=False`, `LIMIT` yok →
  `joinedload` satır çoğaltmıyor ve `ORDER BY`'ı bozmuyor, yani gerçekten 3 gidiş-dönüş ucuz.
  **Yine de `selectinload` seçildi:** 3 fazla sorgu satır başına değil **ekran başına**, ve
  Task 4 + #485'in geri kalanı bu kalıpta. Kalıp değişikliği ayrı kararın konusu.
- **Mutasyon 5/5 öldürüldü:** blok tümü · `content` tek · `metadata_info` tek · `statistics`
  tek + kontrol kolu yeşil. Hepsi `failed`, hiçbiri `error`.

### Fail Eden Testler
`tests/fast/test_osym_exam_engine_split.py` → **7 passed / 11 failed** (önce 6/12).
11 FAIL **kasıtlı**: `TestAnalyzePerformance` 4 (Task 6) · `TestSelectQuestions` 6 fonksiyon
/ 7 örnek (Task 7; `test_query_builds_and_compiles` ×2 parametrize). Yeni kırık YOK — spec
reviewer düşen kümeyi **test-test** karşılaştırdı, agrega değil.

### Engelleyiciler
- **`question_bank` = 0 satır (bu makine)** — uçtan uca doğrulama YAPILAMIYOR. Kabul kriteri
  sorgu-yapısı düzeyinde kalıyor (S219'dan devam).
- ~3387 dosyalık pre-existing kirli ağaç (S210 Gemini devri) — ayrı triyaj. **Bunun 9'u
  `backend/tests/fast/` altında takipsiz test dosyası** (`test_growth_mindset` ·
  `test_irt_equating` · `test_isomorphic_generator` · `test_motivation_generator` ·
  `test_osym_pdf_pipeline` · `test_osym_validator` · `test_turkish_readability` ·
  `test_yks_jargon_service` · `test_yks_trend_analyzer`) — #485'e ait DEĞİL, bu dizinde
  çalışan bir sonraki ajan bunları kendi işi sanmasın.

### Sonraki Adımlar (maks 5)
1. **Task 6** — `_analyze_performance`: `:1716` SELECT→JOIN + `:1779`/`:1785` iki UPDATE →
   `QuestionStatistics`. **TEK COMMIT** (seri bağlı: sadece SELECT düzelirse kullanıcı-görünür
   kazanç 0). M8'in naif hâli `AttributeError` = `error` üretir → plandaki **alternatif**
   mutasyonu kullan (`update(QuestionContent)` + `.values(question_text=...)`).
2. **Task 7** — `_select_questions` 3-yollu JOIN (37 erişim). **Plandaki "TASK 7 TEHLİKELERİ"
   bloğunu OKUMADAN BAŞLAMA.** H1 (boş-havuz koşulsuz cache) → DÜZELT, guard geri gelecek +
   test YAZ. H2 (%15 IRT-ankraj kotası) → `anchor_target = 0`, kod silinmez, gerekçe yorumla.
   Kullanıcı onaylı (16 Ağu).
3. **Task 8** — handoff düzeltmesi + `ders_kaydi.yaml` satırı.
4. `application/commands/sinav.py` için ayrı plan (16 erişim, **BKT hiç çalışmıyor**).
5. Kalan P0: `soru_bankasi_service` 41+15 · `irt_daemon` KWARG'ları (her IRT kalibrasyon
   yazımı `CompileError`) · `question_repository` 16+5 (sıfır tüketici → SİLME).

### Kararlar (gelecek session tekrar tartışmasın)
- **Plandaki Task 5 test adları/sayıları BAYATTI, kod değil.** `TestEntityQueriesEagerLoad`'da
  3 değil **2** test var: Task 1'in yazarı iki assert'i tek testte birleştirmiş
  (`test_get_subject_performance_eager_loads_and_reads_real_orm`, RED commit `e32ab0ace`'ten
  beri bayt-birebir aynı). Birleşik test **daha sıkı** — `_eager_loaded(...) == {...}` sözlük
  eşitliği eksik/fazla anahtarı da reddediyor; mutasyonu öldüren tam bu. Plana düzeltme
  satırı yazıldı, sessiz silme yok.
- **Mutasyon uygularken `selectinload(Question.metadata_info)` dosyada İKİ kez geçiyor**
  (Task 4 bloğu `:571`, Task 5 bloğu `:1327`). Yalnız ikincisi silinmeli, yoksa ölçülen şey
  Task 5 değil Task 4 olur.
- `SKIP=` **gerekmedi**, kapı kökten koşuldu, tüm hook'lar Passed
  (`kiro2-api-import-smoke` doğru şekilde Skipped — `api/**` dosyası yok).
- 5 adımlı kabul kriteri değişmedi.

### Açık iş olarak düşen yeni kalem
- `tests/fast/test_osym_exam_engine_split.py:430` docstring'i **bayat satır ankrajı**
  taşıyor (`:1329`/`:1346`/`:1351` → gerçek `:1345`/`:1362`/`:1367`; iki commit'te 16 satır
  kaydı). Kod yorumları bu turda güncellendi, test docstring'i güncellenmedi — **#485 sonunda
  tek süpürmede** düzeltilecek (şimdi dokunmak cerrahi kapsamı bozardı). Task 6 (`~:1716`) ve
  Task 7 (`~:1486`) bu satırların altında, yani #485 içinde daha fazla kaymayacak.

---

## Session Handoff — 2026-08-16 (S220)
**Branch:** feature/self-evolution-optimization
**Son commit:** 9098975bc docs: S220 checkpoint — Task 4 plan checkboxlari + handoff
**Push:** ✅ `3e3163fb4..9098975bc` (2 commit), push-secret-guard + reward-hacking-check PASS
**Uncommitted:** bu işin dosyaları **temiz**. Ağaçtaki 3387 kirli dosya = S210 Gemini devri, bu session'a ait değil.

### Yapılanlar
- `backend/core/osym_exam_engine.py:22-23,560-577` — Plan **Task 4** kapandı (`a189c4a34`).
  `get_current_question` sorgusu üç split ilişkiyi (`content`/`metadata_info`/`statistics`)
  `selectinload` ile eager-load ediyor. `api/sinav.py:493-508` dönen nesneden 12 split alan
  okuyor; `lazy='select'` + async = `MissingGreenlet` idi. `navigate_to_question:817` aynı
  fonksiyona delege ettiği için o yol da düzeldi. Diff +11/-2, tek dosya, süpürme yok.
- `docs/superpowers/plans/2026-08-16-osym-exam-engine-split-gocu.md` — Task 4'ün 6 adımı
  işaretlendi (`9098975bc`).
- **Yürütme:** subagent-driven (implementer → spec reviewer → kalite reviewer). Üçü de temiz;
  spec reviewer mutasyonu **bağımsız tekrar etti** (kendi silip koştu, `1 failed` aldı, geri aldı).

### Fail Eden Testler
`tests/fast/test_osym_exam_engine_split.py` → **6 passed / 12 failed** (önce 5/13).
12 FAIL **kasıtlı**: `TestEntityQueriesEagerLoad` 2 (Task 5) · `TestAnalyzePerformance` 4 (Task 6)
· `TestSelectQuestions` 5+1 (Task 7). Hepsi `AttributeError: ... sinif duzeyinde kullanilamaz`.
Yeni kırık YOK — spec reviewer geçen/düşen testleri tek tek karşılaştırdı, sadece agregayı değil.

### Engelleyiciler
- **`question_bank` = 0 satır (bu makine)** — uçtan uca doğrulama YAPILAMIYOR. Kabul kriteri
  sorgu-yapısı düzeyinde kalıyor (S219'dan devam).
- 3387 dosyalık pre-existing kirli ağaç (S210 Gemini devri) — ayrı triyaj.

### Sonraki Adımlar (maks 5)
1. **Task 5** — `get_subject_performance` eager-load (`:1313`), üç ilişki birden. `:1396` çıplak
   `except` → `return []` → HTTP 200 ile boş ders kırılımı. Mutasyon M6 hazır.
2. **Task 6** — `_analyze_performance` (`:1716` SELECT→JOIN + `:1779`/`:1785` iki UPDATE →
   `QuestionStatistics`), **tek commit** (seri bağlı).
3. **Task 7** — `_select_questions` 3-yollu JOIN (37 erişim). **Plandaki "TASK 7 TEHLİKELERİ"
   bloğunu OKUMADAN BAŞLAMA** — H1/H2 kararları alınmış (kullanıcı onaylı, 16 Ağu).
4. **Task 8** — handoff düzeltmesi + `application/commands/sinav.py` için ayrı plan.
5. Kalan P0 dosyalar: `soru_bankasi_service` 41+15 · `irt_daemon` KWARG'ları (her IRT
   kalibrasyon yazımı `CompileError`) · `question_repository` 16+5 (sıfır tüketici → SİLME).

### Kararlar (gelecek session tekrar tartışmasın)
- **`SKIP=pytest-fast` FANTOM** (S219'da ölçüldü) — hook `git commit`'te hiç yüklenmiyor.
  Bu turda doğrulandı: kapı çıktısında adı bile geçmiyor. `kiro2-api-import-smoke` ise
  `files: ^backend/api/.*\.py$` filtresiyle `core/` değişikliğinde zaten Skipped.
- **`pre-commit run --files`'ı `backend/` içinden ÇALIŞTIRMA** — yanlış config, `black` süpürmesi.
  Kökten koş (S219 kararı, bu turda uygulandı, temiz geçti).
- 5 adımlı kabul kriteri değişmedi (derle → `get_final_froms()` → eager-load **yapıdan** ölç →
  gerçek ORM modeline karşı test → mutasyon). Mutasyon `error` verirse ölçüm **geçersiz**.
- Task 4'te JOIN gerekmedi: sorgu yalnız `id`/`is_active` (bölünmemiş kolonlar) filtreliyor;
  kusur sorguda değil **dönen örnekte** idi → çözüm `.options()`, `.join()` değil.

---

## Session Handoff — 2026-08-16 (S219)

**Branch:** `feature/self-evolution-optimization` · **HEAD:** `05148d0ee` · **Push:** ✅ edildi (`74c8f9d80..05148d0ee`, 11 commit)
**Ana iş:** #485 — `core/osym_exam_engine.py` göçü. Ama asıl bulgu: **göç sayacı %94 kördü.**

### ⚠️ ÖNCE BUNU OKU — "kalan 9/5" rakamı GEÇERSİZ

S211-S218'in ilerleme ölçütü olan regex sayacı iki yönde birden yanılıyordu (ölçüldü):
- **FAZLA:** yorum satırını erişim sayıyordu (`osym_exam_engine.py:1327`, `models/question_bank.py:528` → 10 kalemin 2'si fantom)
- **EKSİK:** alias'lı import'ları göremiyordu (15 alias import / 11 dosya: `as Question` ×13, `as Soru`, `as _QB`)

**Gerçek kapsam (AST, alias-farkında):** `SINIF=146 · KWARG=12 · ENTITY=69 · 26 dosya`.
Alet: `backend/scripts/scan_split_accesses.py` (10 test + kontrol kolu ile çivili).
Ölçüm çıktısı: `docs/audits/2026-08-16_485_ast_olcum.txt`.

**İyi haber:** S211-S218'in kapanış ilanları FANTOM DEĞİL — 11 ilanın 10'u dosya okunarak
doğrulandı, gerçekten kapalı. Tek istisna `question_crud_service.py` `archive/restore`
(eager-load atlanmış, API tüketicisi yok). Sorun "yanlış kapatma" değil, **hiç açılmama**.

### Kalan iş (ölçülmüş, öncelik sırasıyla)

| Dosya | SINIF+KWARG+ENTITY | Not |
|---|---|---|
| `core/osym_exam_engine.py` | 42+2+5 | **bu planın konusu**, 2/7 task kapandı |
| `services/soru_bankasi_service.py` | 41+0+15 | canlı, P0 — ayrı plan |
| `application/commands/sinav.py` | 16+0+0 | canlı, P0 — **BKT hiç çalışmıyor**, ayrı plan |
| `repositories/question_repository.py` | 16+5 | **sıfır tüketici** → göç değil, SİLME kararı |
| `services/exam_performance_service.py` | 11+0+0 | P1 |
| `core/irt_daemon.py` | 2+6+1 | **KWARG'lar: her IRT kalibrasyon yazımı `CompileError`** |
| `services/irt_analysis_service.py` | 1+4+3 | alias `as Soru` |
| diğer 6 dosya | ~10 | P2 |

### Yapılanlar (11 commit, hepsi push edildi)

- `bdc84e9bc` · `2222337fb` · `224303eff` — **Task 0:** AST sayacı + KWARG/`db.query` sınıfları + 10 test (2 vakum test yakalandı ve düzeltildi)
- `f7f39c2bc` · `fc276b35d` · `e32ab0ace` — **Task 1:** `tests/fast/test_osym_exam_engine_split.py`, **18 RED test**. Bağımsız reviewer kendi fix'ini yazıp 15/15 geçirdi → aşırı-kısıt yok
- `d7eaeb3b1` — **Task 2:** `save_answer` notlandırma → `QuestionContent` (JOIN gerekmedi, paylaşılan PK). 3 mutasyon öldürüldü
- `398a6a5de` — **Task 3:** `_select_beta_questions` `pipeline_metadata` → `QuestionMetadata` JOIN. 2 mutasyon öldürüldü. Diff 12/2, süpürme yok
- `12a35b7b5` · `b46f6ffda` · `05148d0ee` — plan + Task 7 tehlike bloğu + H1/H2 kararları + pre-commit CWD uyarısı

**Test durumu:** `tests/fast/test_osym_exam_engine_split.py` → **5 passed / 13 failed** (13'ü Task 4-7 kapsamı, beklenen).

### Fail Eden Testler

13 FAIL **kasıtlı** (Task 4-7 henüz yapılmadı): `TestEntityQueriesEagerLoad` 2 ·
`TestAnalyzePerformance` 4 · `TestSelectQuestions` 7. Hepsi `AttributeError: ... sinif
duzeyinde kullanilamaz`. Yeni kırık YOK.

### Engelleyiciler

- **`question_bank` = 0 satır (bu makine).** Uçtan uca doğrulama YAPILAMIYOR. Kabul kriteri
  sorgu-yapısı düzeyinde; hiçbir task "öğrenci akışı çalışıyor" kanıtı üretmiyor.
- **3389 dosyalık pre-existing kirli ağaç** (S210 Gemini devri) — ayrı triyaj.
- ~~`SKIP=pytest-fast` zorunlu~~ **FANTOM, ÇÜRÜTÜLDÜ** (aşağıya bak).

### Sonraki Adımlar (maks 5)

1. **Task 4** — `get_current_question` eager-load (`:567`). Sorgu kuruluyor ama `.options()` yok;
   `api/sinav.py:493-508` **12 split alan** okuyor → `MissingGreenlet` → HTTP 500.
   `navigate_to_question:817` aynı fonksiyona delege ediyor. 1 test, 1 mutasyon hazır.
2. **Task 5** — `get_subject_performance` eager-load (`:1313`), üç ilişki birden.
3. **Task 6** — `_analyze_performance` (`:1716` + iki `update()`), **tek commit** (seri bağlı).
4. **Task 7** — `_select_questions` 3-yollu JOIN (37 erişim). **Plandaki TEHLİKE BLOĞUNU
   OKUMADAN BAŞLAMA** — H1/H2 kararları orada.
5. **Task 8** — handoff düzeltmesi + `application/commands/sinav.py` ayrı plan.

Plan: `docs/superpowers/plans/2026-08-16-osym-exam-engine-split-gocu.md`

### Kararlar (gelecek session tekrar tartışmasın)

- **`SKIP=` GEREKMİYOR — ölçüldü.** `.git/hooks/pre-commit` kök config'i sabitliyor
  (`--config=.pre-commit-config.yaml`); `pytest-fast` `backend/.pre-commit-config.yaml`'da
  ve o config `git commit`'te **hiç yüklenmiyor**. S215-S218'den taşınan engelleyici fantom.
- **`pre-commit run --files`'ı `backend/` içinden ÇALIŞTIRMA** — yanlış config yüklenir,
  kapıda olmayan `black` devreye girer, dokunulmamış satırları süpürür ve `# nosec B311`
  yorumunu kapanış parantezine taşıyıp bandit bastırmasını kırabilir. Kökten koş.
- **H1 (boş havuz koşulsuz cache) → Task 7'de DÜZELT** (kod kararı, guard geri gelecek).
- **H2 (%15 IRT-ankraj kotası) → Task 7'de KAPAT** (`anchor_target = 0`), kod silinmez,
  gerekçe yorumla yazılır. Psikometrik ürün kararı, ayrı oturumda ele alınacak.
  **Kullanıcı onayı alındı (16 Ağu).**
- Mutasyon harness'lerinde **`read_bytes()`/`write_bytes()`** kullan — `write_text()`
  Windows'ta LF→CRLF çevirip geri-alım doğrulamasını yanlış-pozitif bozuyor.
- Commit ayırma: "ağaç kirli" gerekçe değil, `git stash push -- <dosya>` tek komut.

### Bu oturumun dersleri (kalıcı kayıt)

`.claude/lessons/ders_kaydi.yaml` → **8 yeni ders** (`L-s219-*`), hepsi `aktif` + kanıtlı,
bekçi 9/9 geçiyor. Uzun anlatım: `.claude/rules/audit-methodology.md` (5 yeni bölüm).

Özet: ilerleme sayacı da bir ölçüm aletidir · yanlış-**sıfır** tek kabul edilemez hata
türü · test paketi de bir dilim ölçer · "göç ettin mi" ≠ "koruduun mu" · **yorum CI'da
düşmez** · `pre-commit` yanlış CWD'den kapının ölçümü değil · `write_text()` geri alımı
bozar · "ağaç kirli" süpürme gerekçesi değil.

### Açık iş olarak düşen yeni kalemler

- `tests/integration/test_beta_practice_selection.py:32` — canlı `Question.pipeline_metadata`
  erişimi, `except Exception: return False` içinde → beta-havuz hazırlık kontrolü **sonsuza
  dek `False`**
- `backend/.pre-commit-config.yaml` commit anında **ölü** — tanımladığı her hook sessizce
  yüklenmiyor (gerçek `pytest-fast` kapısı dahil). Ya köke taşınmalı ya ölü işaretlenmeli
- Sayaçta 5 minor kalem (sıralama, KWARG satır numarası zincir başını gösteriyor, iki
  docstring satırı) — hiçbiri yanlış-sıfır üretemez

---

## Session Handoff — 2026-08-16 (S218)
**Branch:** feature/self-evolution-optimization
**Son commit:** 7febaeac9 fix(backend): placement_assessment_api.py _check_correctness — QuestionContent'e çevrildi (#485)
**Uncommitted:** temiz (bu session'ın dosyaları). 3388 dosyalık pre-existing kirli ağaç (S210 Gemini devri) var, bu session'a ait değil — ayrı triyaj görevi. **Push edilmedi — kullanıcı onayı bekliyor.**

### Yapılanlar
- `backend/api/placement_assessment_api.py:281-302` — `_check_correctness`'taki `QuestionBankItem.correct_answer` (kolon-select) `QuestionContent`'e çevrildi (`7febaeac9`, #485). JOIN gerekmedi: dosyada `QuestionBankItem`'ın başka kolonu kullanılmıyordu, `QuestionContent.id` `question_bank.id` ile aynı paylaşılan PK.
- `backend/tests/fast/test_placement_assessment_api_split.py` — 7 yeni test, mutasyonla çivili (`git stash push -- <dosya>` ile eski kod geri konunca 7/7 aynı AttributeError'la düştü, sonra geri alındı)
- Yan bulgu — dosyada pre-existing pre-commit borcu (dokunulmayan kod): `_store_session`/`_load_session` pickle kullanımı (bandit B403×2 + B301) + mypy no-any-return (satır 301, `row[0]: Any`). Kontrol kolu: `pre-commit run bandit/mypy --files` stash'lenmiş HEAD'e karşı çalıştırıldı, ikisi de zaten vardı. Inline `# nosec`/`# type: ignore` ile işaretlendi, davranış değiştirilmedi.
- `SKIP=kiro2-api-import-smoke` (kullanıcı onayıyla) — değişen dosyayla ilgisiz WinError 127 ortam kusuru (`api.rag`/`api.youtube_routes`/`api.v1.semantic_search`, S211'den beri bilinen)

### Fail Eden Testler
YOK — yeni 7 test + `tests/unit/test_exam_event_wiring.py` (6 test, aynı modülü tüketiyor) hepsi PASS

### Engelleyiciler
- `pytest-fast` FK fixture kırığı (S215'ten devir) — backend commit'leri hâlâ `SKIP=` zorunda, bu turda dokunulmadı
- `kiro2-api-import-smoke` WinError 127 — S211'den beri her `api/` commit'inde SKIP gerektiriyor, kök neden hâlâ açık
- 3388 dosyalık kirli ağaç (S210 Gemini devri) — bu session'a ait değil, ayrı triyaj bekliyor

### Sonraki Adımlar (maks 5)
1. #485 devamı — `core/osym_exam_engine.py` (1 erişim) veya 4'lü grup (`difficulty_classification_service.py` · `placement_assessment_service.py` · `core/irt_daemon.py` · `tasks/mega_feature_tasks.py`, 2 erişim/dosya)
2. `git push` bekliyor (kullanıcı onayı gerekir)
3. `pytest-fast` FK fixture kırığı — ayrı görev, birikmeden kapatılmalı
4. `kiro2-api-import-smoke` WinError 127 kök nedeni — ayrı görev, her `api/` commit'ini SKIP'e zorluyor
5. Kirli ağaç triyajı (3388 dosya)

### Kararlar (gelecek session tekrar tartışmasın)
- 5 adımlı kabul kriteri değişmedi (derle → `get_final_froms` → eager-load ölçümü → gerçek model testi → mutasyon)
- Kolon-select sorgularda (entity-select değil), JOIN'e ihtiyaç YOKSA (başka split-tablo kolonu kullanılmıyorsa) doğrudan split tabloya filtrelemek yeterli — JOIN eklemek gereksiz karmaşıklık olurdu
- pre-commit borcu (bandit/mypy) keşfedilirse aynı dosyada: kontrol kolu (`pre-commit run <hook> --files`, stash'li) ile HEAD'de zaten var olduğu doğrulanmadan işaretleme yapılmaz

---

## Session Handoff — 2026-08-16 07:53
**Branch:** feature/self-evolution-optimization
**Son commit:** f5b1f5a6c chore: S217 handoff — parent_service.py 1/1 kapandı; kalan 10/6 ÖLÇÜLDÜ
**Uncommitted:** temiz (bu session'ın dosyaları). 3388 dosyalık pre-existing kirli ağaç (S210 Gemini devri) var, bu session'a ait değil — ayrı triyaj görevi.

### Yapılanlar
- `backend/services/parent_service.py:572-580` — `get_child_performance`'taki `QuestionBankItem.subject_area` `QuestionMetadata` JOIN'ine çevrildi (`a74755a43`, #485)
- `backend/tests/fast/test_parent_service_split.py` — 6 yeni test, mutasyonla çivili (`git stash` ile eski kod geri konunca 6/6 aynı AttributeError'la düştü)
- `backend/pyproject.toml` — pre-existing S112 borcu (`parent_service.py:854`, dokunulmayan fonksiyon) per-file-ignore + inline `# nosec B112` ile işaretlendi
- `.claude/sessions/latest.md` — S217 handoff yazıldı (`f5b1f5a6c`)
- `git push origin feature/self-evolution-optimization` — `bafdaf0ba..f5b1f5a6c` gönderildi, push-secret-guard + reward-hacking-check PASS
- `memory/MEMORY.md` — 22.7KB→17.5KB kompakte edildi (S206/S209-S214 satırları birleştirildi, detay zaten topic dosyalarında duruyordu, bilgi kaybı yok) + S215-S217 index satırı eklendi

### Fail Eden Testler
YOK — yeni 6 test + mevcut parent-ilişkili 39 test (kpi_aggregation 22 + link_code 17) hepsi PASS

### Engelleyiciler
- `pytest-fast` FK fixture kırığı (S215'ten devir) — backend commit'leri hâlâ `SKIP=` zorunda
- 3388 dosyalık kirli ağaç (S210 Gemini devri) — bu session'a ait değil, ayrı triyaj bekliyor

### Sonraki Adımlar (maks 5)
1. #485 devamı — `api/placement_assessment_api.py` (1 erişim, `correct_answer`→muhtemelen `QuestionContent`) veya 4'lü grup (`difficulty_classification_service.py` · `placement_assessment_service.py` · `core/irt_daemon.py` · `tasks/mega_feature_tasks.py`, 2 erişim/dosya)
2. `pytest-fast` FK fixture kırığı — ayrı görev, birikmeden kapatılmalı
3. Kirli ağaç triyajı (3388 dosya)

### Kararlar (gelecek session tekrar tartışmasın)
- 5 adımlı kabul kriteri değişmedi (derle → `get_final_froms` → eager-load ölçümü → gerçek model testi → mutasyon)
- Kolon-select sorgularda (entity-select değil) eager-load N/A — bu dosyada yalnız sınıf-düzeyi risk vardı

---

## Session Handoff — 2026-08-16 (S217)
**Branch:** `feature/self-evolution-optimization` · **HEAD:** `a74755a43` · **Push:** ⏳ commit'li, henüz push edilmedi
**Ana iş:** #485 devamı — `services/parent_service.py` (1/1 kapandı)

`a74755a43` — **`get_child_performance`**: sınıf-düzeyi `QuestionBankItem.subject_area`
(kolon-select `answers_stmt` içinde, entity-select DEĞİL) `QuestionMetadata` JOIN'ine
çevrildi. Eager-load N/A (ölçüldü: sorgu `StudentAnswer.*` + `subject_area` kolonlarını
tek satırda unpack ediyor, instance-level lazy-load riski yok — offline_sync/osym_routes'tan
farklı olarak bu dosyada örnek-düzeyi risk YOK). `tests/fast/test_parent_service_split.py`
(6 test: derleme + tek FROM + SELECT kolonunun `question_metadata`'ya ait olduğu + JOIN
yapısı + WHERE + subject_area→subject_progress unpacking doğruluğu). Mutasyon: `git stash
push -- services/parent_service.py` ile eski kod geri konunca 6/6 test aynı AttributeError
ile düştü, sonra geri alındı (git status ile doğrulandı).

**Yan bulgu — dosyada pre-existing pre-commit borcu (dokunulmayan fonksiyon):**
`get_parent_dashboard_data`'daki `except Exception: continue` (S112/bandit B112),
kontrol kolu `git show HEAD:...| ruff check -` → 1 hata (HEAD'de zaten vardı). Ruff
tarafı `pyproject.toml` per-file-ignore, bandit tarafı inline `# nosec B112` ile
işaretlendi — davranış değiştirilmedi, sadece görünür kılındı.

**Kalan: 10 erişim / 6 dosya** (S216 sonu: 11/7).

### Sonraki Adımlar
1. #485 devamı — sıradaki: `api/placement_assessment_api.py` (1 erişim, `correct_answer`
   → muhtemelen `QuestionContent`), veya 4'lü grup (`difficulty_classification_service.py`
   · `placement_assessment_service.py` · `core/irt_daemon.py` · `tasks/mega_feature_tasks.py`,
   2 erişim/dosya). Aynı 5 adımlı süreç.
2. `pytest-fast` FK fixture kırığı — S215'ten devir, hâlâ açık.
3. `git push` — S215+S216+S217 birlikte bekliyor (kullanıcı onayı gerekir).

---

## Session Handoff — 2026-08-16 (S216)
**Branch:** `feature/self-evolution-optimization` · **HEAD:** `22aedbf40` · **Push:** ⏳ commit'li, henüz push edilmedi
**Ana iş:** #485 devamı — `services/offline_sync_service.py` (1/1 kapandı)

`22aedbf40` — **`build_sync_package`**: sınıf-düzeyi `QuestionBankItem.subject_area` WHERE'i
`QuestionMetadata` JOIN'ine çevrildi. **Ayrıca** sayaç görmediği bir örnek-düzeyi risk ölçüldü
(S214 dersiyle aynı desen): `select(QuestionBankItem)` ile entity seçilip döngüde
`q.question_text`/`.option_a-e`/`.correct_answer` (content), `.subject_area` (metadata_info),
`.difficulty_level` (statistics) okunuyordu — üçü de `lazy='select'`, async oturumda
eager-load'suz erişim `MissingGreenlet` atardı. 3 ilişki için `selectinload` eklendi.
`tests/fast/test_offline_sync_service_split.py` (7 test); mutasyon: eski kod geri konunca
**3/7 test düştü** (eager-load yapısı, JOIN, subject WHERE) — 4 test (compile, is_active,
business-logic mock, empty-list) subject=None olduğu için eski koda karşı da geçiyordu,
bu beklenen (mnemonic testindeki business-logic testiyle aynı sınırlama: mock session lazy-load
tetiklemiyor). Ruff clean. `process_sync_results`/diğer offline_sync testleri (9+6) regresyonsuz.

**Kalan: 11 erişim / 7 dosya** (S215 sonu: 12/8).

### Sonraki Adımlar
1. #485 devamı — sıradaki en küçük: `services/parent_service.py` veya `api/placement_assessment_api.py`
   (1 erişim), veya 4'lü grup (`difficulty_classification_service.py` · `placement_assessment_service.py`
   · `irt_daemon.py` · `mega_feature_tasks.py`, 2 erişim). Aynı 5 adımlı süreç.
2. `pytest-fast` FK fixture kırığı — S215'ten devir, hâlâ açık.
3. `git push` — S215 + S216 birlikte bekliyor (kullanıcı onayı gerekir).

---

## Session Handoff — 2026-08-16 (S215)
**Branch:** `feature/self-evolution-optimization` · **HEAD:** `3a1aabd0d` · **Push:** ⏳ commit'li, henüz push edilmedi
**Ana iş:** #485 — `question_bank` 69-alan split'inin JOIN göçü (S210-S214 devamı)
**Uncommitted:** bu işin dosyaları **temiz**. (Ağaçtaki 3388 kirli dosya = Gemini S210 devri, ayrı görev.)

### İlerleme — ÖLÇÜLDÜ (aynı script, kontrol kolu S213'te doğrulanmıştı)

**Kalan: 12 erişim / 8 dosya** (S214 sonu: 14/9 — bu turda 2 erişim/1 dosya kapandı, arithmetik ile birebir örtüştü).

```
python -c "import re,sys;sys.path.insert(0,'.');from models.question_bank import QuestionContent,QuestionMetadata,QuestionStatistics;
d={c.name for t in (QuestionContent,QuestionMetadata,QuestionStatistics) for c in t.__table__.columns if c.name!='id'};
from pathlib import Path;[print(len([m for m in re.finditer(r'QuestionBankItem\.(\w+)',p.read_text(encoding='utf-8')) if m.group(1) in d]),p) for x in ('services','api','core','app','tasks') for p in Path(x).rglob('*.py') if '__pycache__' not in p.parts and any(m.group(1) in d for m in re.finditer(r'QuestionBankItem\.(\w+)',p.read_text(encoding='utf-8',errors='ignore')))]"
```

| # | Dosya | Erişim |
|---|---|---|
| 1 | `services/difficulty_classification_service.py` · `services/placement_assessment_service.py` · `core/irt_daemon.py` · `tasks/mega_feature_tasks.py` | 2 ×4 |
| 2 | `services/offline_sync_service.py` · `services/parent_service.py` · `api/placement_assessment_api.py` · `core/osym_exam_engine.py` | 1 ×4 |

### Yapılanlar

`3a1aabd0d` — **`backend/api/osym_routes.py` (8/17)** — `auto_assign_anchors()`'daki 2 sınıf-düzeyi
`QuestionBankItem.subject_area` erişimi (alan artık `QuestionMetadata`'da) JOIN'e çevrildi.
`id`/`is_anchor` split edilmedi, dokunulmadı — order_by ve `q.is_anchor = ...` aynen kaldı.
Eager-load **N/A** (ölçüldü: 2 `select(QuestionBankItem)`, ikisi de yalnız `is_anchor` yazıyor,
instance-level, split tabloya dokunmuyor). + `tests/fast/test_osym_routes_split.py` (6 test),
mutasyon **3/3 öldürüldü** (WHERE reverti → AttributeError, JOIN'siz kartezyen → `get_final_froms()==2`,
`order_by` kaybı).

**Yan bulgu — dosya HEAD'de hiç commit edilmemişti** (S210 Gemini devrinden kalma çalışan-ağaç
içeriği: `analyze_osym_pdf`/`auto_assign_anchors`/`run_equating` hiçbiri git'te yoktu). Bu yüzden
`pre-commit run --files` baseline'ı S211-S214'ten farklı bir sınıf borç çıkardı:
- mypy: `bloomLevel: int = 3` iki kez tanımlıydı (no-redef) — silindi.
- ruff B007: `batch_generate`'te kullanılmayan döngü değişkeni `i` — `_i`'ye çevrildi (dokunulmayan fonksiyon, tek-karakter, sıfır risk).
- ruff N815 ×4 (`examType`/`bloomLevel` — frontend camelCase JSON sözleşmesi) + RET504 ×2
  (`generate_question`/`validate_question`, ara değişken) — **dokunulmayan fonksiyonlarda,
  pre-existing.** `pyproject.toml` `per-file-ignores`'a `"api/osym_routes.py" = ["N815", "RET504"]`
  eklendi (5 emsal aynı desende zaten var: `multi_layer_cache.py`, `osym_exam_engine.py`,
  `soru_bankasi_service.py`, `admin.py`, `test_golden_flows.py`).

### Fail Eden Testler
- **Yeni testler: 6/6 PASS.** Mutasyon 3/3.
- ⚠️ **PRE-EXISTING, dokunulmadı, YENİ BULGU:** `pytest-fast` pre-commit hook'u (`pass_filenames:
  false`, `files:` filtresi yok → her backend commit'inde koşuyor) şu an KIRIK —
  `tests/unit/test_fsrs_card_persistence.py::test_fsrs_card_insert_persists_core_fields`
  FK ihlaliyle düşüyor (`bkt_states.student_id` → `users` tablosunda yok), ardından aynı
  worker'daki `test_bkt_record_answer_batch1b*.py` `PendingRollbackError` ile ERROR veriyor
  (aynı transaction'ın devamı). #485/`question_bank` ile **ilgisi yok** — BKT/FSRS test
  fixture'ında eksik `users` seed satırı. Kullanıcı onayıyla `SKIP=pytest-fast` ile commit'e
  devam edildi. **Bu turda çözülmedi, ayrı görev gerekiyor.**
- `kiro2-api-import-smoke` — bilinen ortam kusuru (WinError 127), kontrol kolu değişmedi.

### Engelleyiciler
- **Yeni:** `pytest-fast` hook'u kırık — yukarıya bkz. Backend'e dokunan HER commit bunu
  SKIP etmek zorunda kalacak ta ki fixture düzelene kadar.
- Kökte `models/` = YOLO ağırlık klasörü, `kiro2-api-import-smoke` kırık — değişmedi (S211-S214).

### Sonraki Adımlar
1. **#485 devamı — `services/offline_sync_service.py` (1 erişim) veya `services/difficulty_classification_service.py` (2 erişim).** Aynı 5 adımlı zorunlu sıra (S214 handoff'undaki liste).
2. **YENİ: `pytest-fast` FK fixture kırığı.** `test_fsrs_card_persistence.py` + `test_bkt_record_answer_batch1b*.py` — `users` tablosuna eksik seed satırı ekle veya fixture'ı `users` FK'sini karşılayacak şekilde düzelt. #485 kapsamı DIŞINDA, ayrı görev — ama her backend commit'i şu an bunu SKIP etmek zorunda, biriktirmeden kapatılmalı.
3. `git push` bekliyor (kullanıcı onayı gerekir).
4. `tests/test_curator_api.py`'nin 2 pre-existing kusuru (stale mock + celery hang) — S213'ten devir.
5. Kirli ağaç triyajı (3388 dosya) · `#444` Öğretmen Öğrenciler UI · `#467-471`.

### Kararlar (gelecek session tekrar tartışmasın)
- **Dosya hiç commit edilmemiş olabilir** (S210 devri) — bu durumda `pre-commit run --files`
  baseline'ı HEAD'e karşı değil, çalışan ağaca karşı ölçer; "kontrol kolu HEAD'de de var mı"
  sorusu bazı bulgular için (yeni eklenen fonksiyonlardaki N815 gibi) anlamsız hale gelir.
  Yine de karar aynı kalır: dokunulmayan fonksiyondaki borç per-file-ignore'a gider, dokunulan
  fonksiyondaki borç düzeltilir.
- **pytest-fast gibi unconditional pre-commit hook'ları** (`pass_filenames: false`, `files:`
  filtresiz) #485 dosyalarıyla hiç ilgisi olmayan bir hatayla kırılabilir. Kırıksa ve konu
  dışıysa `SKIP=` ile geç (kullanıcı onayı ile), ama görev listesine YENİ madde olarak düş —
  sessizce biriktirme.
- 5 adımlı kabul kriteri değişmedi (bkz. S214 handoff). **Skor: elden geçen 8 dosyanın 8'inde kusur.**

### Kalıcı kayıt nerede
- **Uzun anlatım:** `.claude/rules/audit-methodology.md`
- **Bellek:** `memory/MEMORY.md` S214 satırı → bu session S215 olarak eklenecek (ayrı adım)
