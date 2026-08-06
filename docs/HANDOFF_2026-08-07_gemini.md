# KIRO2 — Devir Planı (7 Ağustos 2026)

> Bu belge, projeyi devralacak yeni bir asistan (Gemini) için yazıldı.
> **Kendi kendine yeterlidir**: durum, tuzaklar, iş listesi ve her iş için
> kabul kriteri içerir. Önceki oturumların hafızasına ihtiyaç duymaz.
>
> Devreden: Claude (oturum S205) · Devir commit'i: `8196f5703`

---

## 0. Bu belgeyi nasıl kullan

1. **§1'i oku** — doğrulanmış durum. Sayıları kendin yeniden ölçmeden aksiyon alma.
2. **§2'yi ezberle** — bu deponun tuzakları. Buradaki her madde canlı sistemde
   en az bir kez acı verdi. Atlarsan aynı hataya düşersin.
3. **§3'ten sırayla ilerle** — işler bağımlılık sırasına dizildi.
4. Her işin sonunda **kabul kriteri** var. Kriteri ölçmeden "bitti" deme.

**En önemli tek kural:** Bu depoda *yeşil test, çalışan kod anlamına gelmez*.
Bunun en az 6 belgelenmiş vakası var (§2.1). Her iddianı **canlı sisteme karşı**
ölç.

---

## 1. Doğrulanmış durum (7 Ağu 2026, 01:45)

### 1.1 Veritabanı

| Ölçüm | Değer | Nasıl doğrularsın |
|---|---|---|
| PostgreSQL | **18.1, port 5434**, db `kiro2` | `"C:/Program Files/PostgreSQL/18/bin/pg_isready.exe" -p 5434` |
| `question_bank` | **187.835 satır / 182.519 benzersiz / 110.858 aktif** | `SELECT count(*), count(DISTINCT question_text), count(*) FILTER (WHERE is_active) FROM question_bank;` |
| Öğrenci kapısı `mv_safe_for_beta` | **25.127** | `SELECT count(*) FROM mv_safe_for_beta;` |
| `alembic_version` | **`fa067642bdfe`** | `SELECT version_num FROM alembic_version;` |
| `questions` (legacy) | **SİLİNMİŞ** — geri yüklenmeyecek (karar verildi) | `SELECT to_regclass('public.questions');` → NULL |
| HNSW index | `idx_qb_embedding_hnsw`, valid, 695 MB | `SELECT indisvalid FROM pg_index WHERE indexrelid='idx_qb_embedding_hnsw'::regclass;` |

**Not:** 5 Ağustos'ta `question_bank`'ın %98,77'si takipsiz bir `TRUNCATE` script'iyle
silinmişti (2.304 satır / **21 benzersiz** kalmıştı). 7 Ağustos'ta yedekten geri yüklendi.
Script mühürlendi, bir daha olmaması için invaryant testi eklendi.
Detay: `docs/audits/2026-08-06_uctan_uca_durum_tespiti.md`

### 1.2 Kod / dal

| Ölçüm | Değer |
|---|---|
| Aktif dal | `feature/self-evolution-optimization` |
| `master`'dan ileri | ~379 commit |
| **Push edilmemiş** | **20 commit** ← tek kopya, yedeksiz |
| **Commit'siz dosya** | **0 — çalışma ağacı TEMİZ** ✅ |
| Kayıtlı API yolu | **369** (`create_app()` ile ölçüldü) |

> **02:40 güncellemesi:** Devir planı yazıldığında 249 commit'siz dosya vardı.
> Hüseyin (veya paralel bir araç) bunları 4 commit'te kapattı:
> `b3be80686`, `f83fc9978`, `a77e660cc`, `54e5016d8` (178 dosya, +8586/-5859).
> **Doğrulandı:** bu commit'ler `loader.py`, `push_tasks.py`, `App.tsx`,
> `clean_import_question_bank.py`'ye **dokunmadı** (diff boş) — S205 işi ezilmedi.
> Dolayısıyla **İş #1 KAPANDI**, İş #2 (celery rebuild) artık engelsiz.

### 1.3 Konteynerler

| Konteyner | Durum | İmaj tarihi | Uyarı |
|---|---|---|---|
| `kiro2-backend` | healthy | 6 Ağu | — |
| `kiro2-celery-worker` | healthy | **30 Tem** | ⚠️ Fix `docker cp` ile kondu, **imajda YOK** |
| `kiro2-celery-beat` | healthy | **30 Tem** | ⚠️ aynı |
| `kiro2-frontend` | healthy | **31 Tem** (7 gün eski) | ⚠️ Yayındaki sürüm bayat |
| `kiro2-redis` | healthy | — | — |

### 1.4 Test durumu (ölçüldü)

| Paket | Sonuç |
|---|---|
| `tests/unit/test_teacher_copilot.py` | **6/6** |
| `tests/fast/test_push_tasks.py` | **9/9** |
| `tests/unit/test_socratic_rag_guardrails.py` | **8/8** |
| `tests/db/test_migrations.py` | **9/9** (ama bkz. İş #9 — vekil ölçüm) |
| `tests/db/test_question_bank_invariants.py` | **2/2** (canlı DB'ye karşı) |
| `tests/test_router_registration.py` | **3/3** |
| Frontend PWA + CoPilot | **29/29** |
| **Frontend geniş paket** | 🔴 **28 dosya / 111 test KIRIK** — kök neden bilinmiyor |
| **Backend uçtan uca** | 🔴 **ÖLÇÜLEMİYOR** — `pytest_asyncio` teardown deadlock |

---

## 2. BU DEPONUN TUZAKLARI (atlama)

### 2.1 Yeşil test ≠ doğru kod (6 belgelenmiş vaka)

Bu depo tam olarak bu yüzden defalarca yanlış yönlendirildi:

| Vaka | Ne oldu |
|---|---|
| `select().tablesample()` | SQLAlchemy 2.0'da yok. PostgreSQL yolunda **her zaman** çöküyordu; testler sqlite `else` dalını koştuğu için yeşildi |
| `/fsrs/due` | Aylarca 500 dönüyordu; şema bekçisi **tablo adı** karşılaştırdığı için yeşildi |
| ES cevap sızıntısı | 64.270/64.270 soruda `correct_answer` öğrenciye gidiyordu; testler bakmıyordu |
| `test_indexes.py` | **Hâlâ vakum test** — 3 satır önce tanımladığı sabiti kendine assert ediyor, DB'ye hiç bakmıyor. Üstünde "NO REWARD HACKING" yazıyor |
| `test_migration_has_downgrade_function` | `def downgrade(): pass` gövdesini geçiriyor. `fa067642bdfe` gerçekten geri alınamaz ama test yeşil |
| `test_teacher_copilot` (eski hâli) | `get_db=None` verip `total_students > 0` bekliyordu; sabit `32` döndüğü için geçiyordu |

**Kural:** Bir testin geçmesi, ölçtüğünü sandığın şeyi ölçtüğü anlamına gelmez.
Yeni yazdığın her kritik testi **mutasyonla çivile**: fix'i geri al, test düşmeli.
Düşmüyorsa test değersizdir.

**Mutasyon testinin kendi tuzağı:** Sonuç `failed` değil `error` (collection hatası)
ise ölçüm **geçersizdir** — dosyayı bozmuşsundur, testin yük taşıdığını kanıtlamamışsındır.
Mutasyonu kabuk tırnağıyla değil Python ile uygula, ankrajı `assert eski in metin` ile doğrula.

### 2.2 Ölçüm aletini doğrula

Bu oturumda **benim kendi ölçümüm iki kez yanıldı**:

- `loader.py` diff'ine göz kararı bakıp "KVKK yeni kapatılıyor" dedim → yanlıştı
- Sonra düzeltmek için `grep -c` kullandım, o da yanlıştı (`ROUTER_MAPPING` satırlarını saydı)
- Doğrusu ancak yapıyı doğrudan okuyunca çıktı: HEAD'de `DISABLED_ROUTERS` **boş**

**Kural:** Bir A/B ölçümüne güvenmeden önce **kontrol kolunun bilinen sonucu
ürettiğini** göster. Üretmiyorsa bulgu değil, alet arızası vardır.

### 2.3 `git add` etmeden önce diff'i oku

Bu oturumun en pahalı yakalanan hatası: `backend/routers/loader.py`'yi Teacher
Co-Pilot commit'ine eklemek üzereydim. Diff'e baktığımda dosyanın **110 router'ın
kapatılmasını** (KVKK yasal uyum uçları dahil) taşıdığını gördüm.

Ayrıca: `backend/pytest.ini`'yi commit'lerken farkında olmadan Cursor'ın
xdist ayarlarını da içeri aldım.

**Kural:** Bir commit'in kapsamı dosya adlarıyla değil **diff'le** ölçülür.
Çalışma ağacında 249 commit'siz dosya varken bu kural hayati.

### 2.4 Windows / ortam

| Tuzak | Doğrusu |
|---|---|
| `python3` yok | `python` kullan |
| Türkçe SQL `psql -c "..."` ile bozulur | `psql -f dosya.sql` |
| Konsol cp1254 → Türkçe çıktı bozulur | Script başına `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` |
| `/tmp` yazılamaz (izin) | Depo içinde geçici dosya kullan, sonra sil |
| bash `/tmp` ≠ Python `/tmp` | İkisi farklı namespace; tek araçla yaz+oku |
| HNSW index build paralel çöker | `SET max_parallel_maintenance_workers = 0;` ZORUNLU (`.claude/rules/windows-hnsw-build.md`) |
| Ripgrep'i proje kökünde çalıştırma | 30 dk timeout. Alt dizin hedefle |

### 2.5 Docker döngüsü

Python dosyası değiştirdiğinde konteynere yansıması için:

```bash
docker cp [dosya] kiro2-backend:/app/[yol]
docker exec kiro2-backend find /app/[dizin] -name "*.pyc" -delete
docker restart kiro2-backend
sleep 22          # Start-Sleep 22 — daha kısası healthcheck'i yanıltır
curl -s http://localhost:8000/health   # /api/v1/health DEĞİL — o 404
```

- **Env değişkeni** değiştiyse: `docker compose up -d --no-deps backend` (restart yetmez)
- **Kalıcı** olması için: `docker compose build backend` — ama dikkat, çalışma ağacında
  249 commit'siz dosya var; rebuild onları imaja gömer

### 2.6 Pre-commit kapısı

Kapı **dosyanın tamamını** denetler, sadece diff'ini değil. Önceden var olan
ihlaller commit'ini bloklar. Bu oturumda 4 kez oldu.

Ayrıca **formatlayıcı commit sırasında dosyayı değiştirir** → commit düşer.
Çözüm: `git add` + `git commit` komutunu **aynen tekrarla** (dosya artık düzeltilmiş).

### 2.7 Veri kuralları (ihlal = sessiz bozulma)

- `question_bank` = üretim. `questions` = legacy (şu an silik).
- Soru sorgularında `is_active = TRUE` **ve** kalite-durum filtresi ZORUNLU.
  Sadece `is_active` filtrelemek, reddedilmiş soruları öğrenciye sızdırır
  (55.768 satırlık bir vakada yaşandı).
- `users.id` ve `user_badges.id` **VARCHAR**, UUID değil. FK sütunları `sa.String`.
- `sa.Enum(create_type=False)` güvenilmez → `sa.String` kullan.
- `correct_answer` / `is_active` **asla otomatik değiştirilmez**. Her DB değişikliği
  önce yedek tablo, sonra geri alınabilir olmalı.
- Türkçe metin: **UTF-8 + NFC**. `I→ı`, `İ→i` (asla `İ→I` değil).

---

## 3. İŞ LİSTESİ

### 🔴 P0 — Önce bunlar (kayıp/risk önleyici)

---

#### ~~İş #1 — 249 commit'siz dosyayı triyaj et ve commit'le~~ ✅ KAPANDI (02:40)

Hüseyin/paralel araç 4 commit'te kapattı. `git status` **temiz**.

**Ama iki takip kalemi doğdu:**

**1a — Push edilmemiş 20 commit.** Depo tek kopya, uzakta yedeği yok.
Disk arızası = 20 commit'lik iş kaybı. `.claude/rules/security.md` >2GB pack
uyarısına dikkat ederek push et.
**Kabul kriteri:** `git log origin/feature/self-evolution-optimization..HEAD` → boş.

**1b — 178 dosyalık toplu commit'ler denetlenmedi.** Bu ağaçta daha önce
**3 regresyon** bulundu (S204: 2, S205: `/login`). Dört commit
(`b3be80686`, `f83fc9978`, `a77e660cc`, `54e5016d8`) tek seferde 178 dosya
taşıdı; her biri kendi içinde diff okunarak mı hazırlandı bilinmiyor.
**Kabul kriteri:** Bu 4 commit'in diff'i regresyon açısından tarandı —
özellikle: geri alınan özellik, kapatılan router/kontrol, sabitlenmiş veri.
S205 dosyalarına dokunmadıkları **doğrulandı**; gerisi denetlenmedi.

---

#### İş #2 — Celery düzeltmesini imaja al

**Neden P0:** Şu anki düzeltme sadece **çalışan konteynerin dosya sisteminde**.
Konteyner yeniden oluşturulursa:
- `send_streak_reminders` yine çöker (4 gündür ölüydü, 7 Ağu'da düzeldi)
- `kiro2_app` **parolası tekrar log'a düşer** (14 kez düşmüştü)

**Ne düzeltildi (referans):** `backend/tasks/push_tasks.py`
- `_libpq_dsn()` — `postgresql+asyncpg://` → `postgresql://` (psycopg2 SQLAlchemy URL'ini ayrıştıramaz)
- `_redact_dsn()` — hata metnindeki parolayı maskele (iki sızıntı yüzeyi: log + Celery sonuç backend'i)
- INSERT'e `organization_id` eklendi (NOT NULL, seri bağlı 3. kusurdu)

**Nasıl:** İş #1 bittikten **sonra** (çünkü rebuild çalışma ağacını imaja gömer):
```bash
docker compose build celery-worker celery-beat
docker compose up -d --no-deps --force-recreate celery-worker celery-beat
```

**Kabul kriteri:**
```bash
docker exec kiro2-celery-worker sh -c "grep -c '_redact_dsn' /app/tasks/push_tasks.py"   # >0
docker exec kiro2-celery-worker celery -A celery_worker call tasks.push_tasks.send_streak_reminders
# beklenen: {'sent': N, 'status': 'sent'}  — 'error' DEĞİL
docker logs kiro2-celery-worker 2>&1 | grep -cE 'postgresql(\+[a-z0-9]+)?://[^:/@]+:[^@*]+@'   # 0
```

---

#### İş #3 — SMTP: şifremi-unuttum akışı ölü

**Neden P0:** Şifre kurtarma **kodu tamamlanmış ve test edilmiş** (54/54 test),
ama 6 SMTP değişkeninin **6'sı da tanımsız** → kullanıcı şifresini kurtaramıyor.
B2C'de bu, hesabını kaybeden her öğrenciyi kaybetmek demek.

**Ölçüldü (7 Ağu):** `.env.mvp` içinde `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`,
`SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TLS` → **hepsi TANIMSIZ**.

**Nasıl:** Bir SMTP sağlayıcı seç (kurumsal Gmail / SendGrid / Amazon SES),
kimlik bilgilerini `.env.mvp`'ye ekle. **Kimlik bilgilerini asla commit'leme.**

**Kabul kriteri:** Gerçek bir e-posta adresiyle uçtan uca:
`/forgot-password` → e-posta geldi → `/verify-reset-code` → `/reset-password` → yeni şifreyle giriş.
Kod düzeyinde "geçti" yetmez, **e-postanın geldiğini gör**.

---

#### İş #4 — TLS yok

**Neden P0:** `docker-compose.yml`'de 443 / sertifika yapılandırması **yok**.
Öğrenci verisi (KVKK kapsamında kişisel veri) düz HTTP üzerinden akıyor.
B2C satışta bu hem yasal hem güvenlik açığı.

**Nasıl:** Reverse proxy (nginx/Caddy/Traefik) + Let's Encrypt.
Alan adı kararı gerekiyor — bu bir **ürün kararı**, Hüseyin'e sor.

**Kabul kriteri:** `curl -I https://<alan-adı>/health` → 200, sertifika geçerli,
HTTP→HTTPS yönlendirmesi çalışıyor.

---

#### İş #5 — Ödeme altyapısı (PSP) yok

**Neden P0:** B2C öğrenci aboneliği hedefleniyor ama **abonelik, ödeme ve
faturalama yok**. Ürün mevcut hâliyle satılamaz.

**Gerekli:**
- PSP entegrasyonu (Türkiye için iyzico veya PayTR, **3DS zorunlu**)
- Abonelik yaşam döngüsü (başlat / yenile / iptal / geri ödeme)
- Fatura üretimi (e-arşiv fatura yükümlülüğü)
- **Mesafeli Satış Sözleşmesi + 4 ek belge** (yasal zorunluluk, 5/5'i eksik):
  Mesafeli Satış Sözleşmesi, Ön Bilgilendirme Formu, İptal/İade Politikası,
  Teslimat Politikası, Gizlilik Politikası

**Not:** `api.org_billing_api` router'ı 7 Ağu'da açıldı — altyapının bir kısmı
mevcut olabilir. Sıfırdan yazmadan önce **ne olduğunu ölç**.

**Kabul kriteri:** Test kartıyla uçtan uca abonelik satın alma, 3DS ekranı,
fatura üretimi, iptal akışı.

---

### 🟠 P1 — Doğruluk / kalite

---

#### İş #6 — 111 kırık frontend testinin kök nedeni

**Ölçüldü:** 28 test dosyası / 111 test kırık. `git stash` ile `App.tsx` çıkarılıp
tekrar koşuldu → **aynı şekilde kırık**. Yani App.tsx'ten bağımsız, önceden var
olan bir durum.

**Neden önemli:** Bu kadar test kırıkken hiçbir frontend değişikliğini güvenle
doğrulayamazsın. Test paketi şu an **karar verme aracı değil**.

**Nasıl:** Örnek bir kırığa bak (`src/test/components/LearningPath/VideoResourceGrid.test.tsx:164`
— `getByText('Zorluk')` çoklu eşleşme hatası veriyor). Muhtemelen ortak bir
sebep var (bileşen refactor'ü, testing-library sürümü, tema değişikliği).
Bir tanesini çöz, kaçının düzeldiğini ölç.

**Kabul kriteri:** `npx vitest run` → kırık sayısı ölçülmüş ve ya 0 ya da her
kalan kırık için gerekçe yazılmış.

---

#### İş #7 — Kalan 104 router: açılış maliyetini ölç, sonra aç

**Durum:** 110 router `DISABLED_ROUTERS`'taydı, gerekçe "Over-engineering /
Phase 3". **Ölçüldü: 110'unu da frontend çağırıyor, hiçbiri ölü değil.**
Envanter: `docs/audits/2026-08-07_disabled_routers_envanteri.md`

7 Ağu'da **6 yasal/ticari kritik açıldı** (KVKK×3, billing, audit, ferpa/coppa).
**104 kapalı** — çünkü kapatma gerekçesi muhtemelen **açılış performansıydı**
("1000+ gereksiz operasyon"), ve bu iddia **hiç ölçülmedi**.

**Nasıl:**
1. Açılış süresini ve bellek kullanımını iki durumda ölç (104 kapalı vs açık)
2. Kazanç anlamlıysa: kademeli aç, en çok çağrılandan başla
   (`api.study_rooms` 101 çağrı, `api.parent` 55, `api.youtube_routes` 53)
3. Kazanç yoksa: gerekçe çöker, hepsini aç

**Kabul kriteri:** Açılış süresi ölçümü belgelendi; her açılan router için
`create_app()` route tablosunda uçlarının göründüğü kanıtlandı (dosya adına
bakmak yetmez).

---

#### İş #8 — Sokratik guardrail bağlanmadı (P5 planı yarım)

**Durum:** `backend/services/socratic_rag_guardrail_service.py` (202 satır),
`backend/app/guardrails/guards/socratic_guard.py` (74 satır) ve 8 testi **var ve geçiyor**.
Ama `backend/api/enhanced_chat.py`'de **0 referans** → guard **ölü kod**.

`api.enhanced_chat` router'ı 7 Ağu'da açıldı, yani artık bağlanabilir.

**Nasıl:** `/api/v1/enhanced-chat/message` ve `/socratic-dialogue` uçlarına
RAG bağlamı + guardrail denetimini bağla.

**Kabul kriteri:** Uca "Bu sorunun cevabı nedir?" tipi bir istem gönder —
yanıt **doğrudan cevap vermemeli**, Sokratik yönlendirme dönmeli. Kod okumakla
değil, **uca istek atarak** doğrula.

---

#### İş #9 — Alembic round-trip testi gerçek değil

**Durum:** `tests/db/test_migrations.py` 9 test içeriyor, hepsi geçiyor. Ama
hepsi **statik dosya denetimi** — `alembic upgrade`/`downgrade` hiç çalıştırılmıyor.

**Kanıt:** `test_migration_has_downgrade_function`, `fa067642bdfe`'yi geçiriyor.
O migration `DROP TABLE questions CASCADE` yapıyor ve `downgrade()` gövdesi
`pass` — yani **geri alınamaz** ama test yeşil.

**Nasıl:** Tek kullanımlık bir test veritabanında gerçek turu koştur:
`alembic upgrade head && alembic downgrade -1 && alembic upgrade head`

**Kabul kriteri:** Test, `downgrade()` gövdesi `pass` olan bir migration'ı
**yakalamalı**. Mutasyonla çivile: sahte bir boş-downgrade migration ekle,
test düşmeli.

---

#### İş #10 — Backend test paketi uçtan uca koşamıyor

**Durum:** `pytest_asyncio` teardown deadlock'u nedeniyle paket bütün olarak
koşturulamıyor. Bu yüzden **coverage ölçülemiyor** ve CLAUDE.md'deki "~%53"
rakamı doğrulanamaz durumda.

**Neden önemli:** Test paketi koşamıyorsa CI kapısı da anlamsız.

**Kabul kriteri:** `pytest` uçtan uca tamamlanıyor ve gerçek bir coverage
rakamı üretiliyor.

---

#### İş #11 — CI aktif dalda tetiklenmiyor

**Durum:** 11 CI workflow'unun **0'ı** `feature/self-evolution-optimization`
dalına push'ta tetikleniyor (`on:` blokları `[main, master, develop]`).
Dal master'dan **375 commit** ilerde.

Ayrıca Golden Flow kapısı fiilen çalışmıyor: `_login()` 429'u `pytest.skip`'e
çeviriyor ve **skip asla FAIL üretmez**.

**Kabul kriteri:** Aktif dala push → CI koşuyor; rate-limit skip'i artık
yeşil sayılmıyor.

---

#### İş #12 — Test dosyası olmayan 3 bileşen

`AnimatedRoutes`, `GlobalCognitiveWrapper`, `SocraticAIAvatar` — App.tsx'te
mount edildiler, `tsc` + `build` geçiyor, ama **kendi testleri yok** ve
runtime davranışları doğrulanmadı.

`AnimatedRoutes` özellikle riskli: react-router'ın `<Routes>`'unu değiştiriyor,
yani **tüm yönlendirme** ondan geçiyor.

---

### 🟡 P2 — İyileştirme

| # | İş | Not |
|---|---|---|
| 13 | `vendor-mui-core` 794 kB + `vendor-prism` 619 kB | Planın "sıfır 500+ kB" kriteri tutmuyor. Granüler bölme zaten yapıldı, kalan iki chunk doğası gereği büyük |
| 14 | `kiro2_app` parola rotasyonu | Parola 14 kez log'a düştü (yerel log, dışarı çıkmadı). Rotasyon kararı Hüseyin'de |
| 15 | `test_indexes.py` vakum testi | Sabitleri kendine assert ediyor, DB'ye bakmıyor. Ya gerçek yap ya sil |
| 16 | Teacher Co-Pilot'u gerçek veriye bağla | Şu an mock (etiketli). Bloke eden: `user_item_fsrs`=1 satır, `student_learning_profiles`=2, `student_question_flags`=0. **Önce veri birikmeli** |
| 17 | Frontend imajı 7 gün eski | İş #1 sonrası rebuild |

---

## 4. Devredilirken açık bırakılan kararlar

| Karar | Durum |
|---|---|
| `questions` legacy tablosu | **Geri yüklenmeyecek** (çift-tablo tuzağını diriltmemek için). Yedekte mevcut: `backups/kiro2_pre_schema_restore_20260727.dump` |
| Teacher Co-Pilot mock | **Etiketli kalacak** — `data_source: "mock"`, bayrak true iken 501 |
| `kiro2_app` rotasyonu | **Karar verilmedi** |
| Alan adı / TLS sağlayıcı | **Karar verilmedi** |
| PSP seçimi (iyzico / PayTR) | **Karar verilmedi** |

---

## 5. Bu oturumda (S205) yapılanlar — referans

11 commit, `1091db7ab` → `8196f5703`:

| Commit | İş |
|---|---|
| `1091db7ab` | Tohum script'i mühürlendi + hacim/çeşitlilik invaryant testi |
| `6f3380072` | Celery DSN çözümü + parola maskeleme |
| `eb40cb30d` | Streak bildirimi `organization_id` |
| `d5bf6c339` | Takipsiz `fa067642bdfe` migration'ı sürüm kontrolüne alındı |
| `b84bdc503` | 22 scratch script `.gitignore`'a |
| `d9f6953f6` | Teacher Co-Pilot mock olarak kayıtlı + etiketli |
| `0fb271e97` | DISABLED_ROUTERS envanteri (110/110 çağrılıyor) |
| `0d17f924f` | 6 yasal/ticari kritik router açıldı |
| `af99079c2` | `/login` regresyonu geri alındı + copilot rotası mount |
| `0a7653911`, `6184f5e0e`, `8196f5703` | Oturum durumu |

**Kurtarılan:** `question_bank` 2.304/21 → 187.835/182.519 · kapı 2.200 → 25.127 ·
Fizik/Biyoloji/Kimya 1'er sorudan 11.071/5.251/13.096 benzersize.

**Kapatılan sızıntı:** `kiro2_app` parolası worker log'unda 14 kayıt → 0.

---

## 6. Faydalı referanslar

| Konu | Dosya |
|---|---|
| Proje kuralları | `CLAUDE.md` |
| Ölçüm metodolojisi + geçmiş hatalar | `.claude/rules/audit-methodology.md` |
| Sistematik hata ayıklama | `.claude/rules/systematic-debugging.md` |
| Test kuralları + 31 ders | `.claude/rules/testing.md` |
| Golden Flow kapısı | `.claude/rules/golden-flows.md` |
| Windows HNSW | `.claude/rules/windows-hnsw-build.md` |
| Son kapsamlı denetim | `docs/audits/2026-08-06_uctan_uca_durum_tespiti.md` |
| Kapalı router envanteri | `docs/audits/2026-08-07_disabled_routers_envanteri.md` |
| Ders kaydı (66 ders) | `.claude/lessons/ders_kaydi.yaml` |

---

*Hazırlayan: Claude (S205, 7 Ağu 2026 01:45). Buradaki her sayı bu tarihte
canlı sistemden ölçüldü. Aksiyon almadan önce yeniden ölç — bu depoda bayat
sayı, yanlış karar demek.*
