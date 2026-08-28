# KIRO2 — Uçtan Uca Durum Tespiti ve B2C Satışa Hazırlık Denetimi

**Tarih:** 6 Ağustos 2026 · **Dal:** `feature/self-evolution-optimization` (master'dan **363 commit** önde)
**Hedef çubuk:** B2C öğrenci aboneliği (kullanıcı seçimi)
**Yöntem:** 36 paralel ajan · 2 faz · her fazda ayrı **çürütme turu** · 4.972.243 token · 1.119 araç çağrısı
**Ölçüm izni:** salt-okunur (psql SELECT, curl GET, docker exec okuma, pytest --collect-only, git, grep)

---

## 0. Tek cümlelik hüküm

> **Platform satışa hazır değil — ama sebep mühendislik kalitesi değil.**
> Kod tabanı birçok boyutta olgun ve ölçülmüş güçlü yanlara sahip (70 adet, aşağıda).
> Satışı bloke eden şey **5 Ağustos'ta işlenen bir veri kaybı** (soru bankasının %98,77'si),
> **para tahsil etme yeteneğinin hiç olmaması**, ve **B2C için zorunlu hukuki katmanın kapalı olması**.
> Birincisi geri alınabilir (yedek tam ve şema birebir uyumlu); diğer ikisi yeni iş gerektirir.

---

## 1. Metodoloji ve bu raporun güvenilirliği

### 1.1 Mega Audit Lock uyumu

`CLAUDE.md` yeni mega denetim açmadan önce önceki denetimin **her bulgusunun fantom-doğrulanmasını**
şart koşuyor (gerekçe: 23 Mayıs meta-denetiminde 18 P0'ın **%87'si fantom** çıkmıştı). Bu kurala
uyuldu: FAZ A tamamen mevcut 97 açık kalemin canlıya karşı doğrulanmasıdır. FAZ B ancak ondan
sonra açıldı.

### 1.2 Sayılar

| | İncelenen iddia | Teyitli kusur | Çürütülen / fantom | Zaten kapanmış | Ölçülemedi |
|---|---:|---:|---:|---:|---:|
| **FAZ A** (mevcut 97 kalem + 7-lens raporu) | 99 | **61** | 13 | 21 | 4 |
| **FAZ B** (10 alanda sıfırdan tarama) | 96 | **71** | 25 | — | — |
| **Toplam** | **195** | **132** | **38** | 21 | 4 |

**Çürütme oranı %19,5.** Bu rakamın kendisi bir bulgudur: her beş iddiadan biri bağımsız
ölçümle düştü. Çürütme turu olmasaydı bu rapor 38 yanlış kalem taşıyacaktı.

### 1.3 Bu turda düzeltilen kendi hatalarım

Şeffaflık için: denetim sırasında üç kez erken sonuca vardım ve ölçüm beni düzeltti.

| İddiam | Ölçüm | Doğrusu |
|---|---|---|
| "Yedek şeması farklı, kolon eşlemeli restore gerekir" | dump 78 kolon / canlı 78 kolon, iki yönde fark **0** | Düz `pg_restore` çalışır |
| "Benzersizlik kapısı yapısal olarak ölü" | `backfill_soru_hash.py:28-32` = `MD5(lower(trim(metin))\|A..E)` = **saf içerik hash'i**; 14 May dump'ında aktif satırlar arası tekrar **0** | Kapı çalışıyor; tohum script'i **etrafından dolaştı** |
| "ES araması sessizce ölü" | `api.elasticsearch` router'ı `DISABLED_ROUTERS`'ta | Sessiz hata değil, **404** — özellik mount edilmemiş |

---

## 2. Canlı sistemin ölçülmüş tabanı

| Katman | Ölçüm | Komut |
|---|---|---|
| PostgreSQL | **18.1**, host, port 5434, `data_dir=C:/Program Files/PostgreSQL/18/data`, PID 6856 | `select version()`, `netstat -ano` |
| Uygulama bağlantısı | `host.docker.internal:5434/kiro2`, rol `kiro2_app` | konteyner içinden `asyncpg` |
| Konteynerler | 7 servis, hepsi `Up (healthy)` | `docker ps` |
| Backend | `/health` → **200 / 20 ms** | `curl -w` |
| Canlı API yüzeyi | **318 yol / 341 operasyon / 210 schema** | `/openapi.json` |
| Router yükleme | **Loaded 39 · Disabled 110 · Failed 0** | `docker logs kiro2-backend` |
| Frontend rotaları | **80** rota, `App.tsx` 882 satır | `grep -oE 'path="[^"]+"'` |
| Test toplama | **16.979 test / 34 sn / 0 collection error** | `pytest --collect-only -q` |
| Tam test koşumu | **55 failed / 11.310 passed / 2.116 skipped**, `EXIT=3`, `INTERNALERROR: KeyError <WorkerController gw10>` | `pytest -n auto` |
| Kod büyüklüğü | 2.378 backend `.py` · 888 frontend `ts/tsx` · 8.581 git-takipli dosya | `git ls-files` |
| Elasticsearch | canlı alias → **0 doküman**; yedek indeks **64.270** | `_cat/indices` |
| Redis | db0 112 anahtar / db15 63 anahtar | `redis-cli INFO keyspace` |
| Alembic | `alembic_version = fa067642bdfe` — **bu migration dosyası git'te yok** | `psql` + `git status` |

### 2.1 Doküman sapması (D0-D9, teyitli P1)

`CLAUDE.md` ve `MEMORY.md` içindeki sayıların çoğu bayat. Sapma büyüklükleri:

| İddia | Belgede | Canlı | Sapma |
|---|---:|---:|---:|
| `question_bank` toplam | 187.835 | **2.303** | **81×** |
| `question_bank` aktif | 110.858 | **2.300** | 48× |
| `mv_safe_for_beta` | 25.127 | **2.200** | 11× |
| API operasyonu | 1.226 | **341** | 3,6× |
| `questions` legacy | "36.381 satır, BOŞ DEĞİL" | **tablo yok** | fantom |
| orchestrator testi | 85 | 85 | ✅ doğru |
| frontend test dosyası | 197 | ~198 | ✅ doğru |

> Aynı `questions = 36.381 legacy` fantomu `.claude/rules/verification.md:83` ve
> `.claude/rules/debugging-first.md:18` içinde de tekrarlanıyor — yani bir kural dosyası
> artık var olmayan bir tabloyu kontrol listesi maddesi olarak dayatıyor.

---

## 3. 🔴 P0 — İÇERİK KAYBI (VERI-1, VERI-2)

Bu denetimin merkezî bulgusu. Tek başına satışı bloke eder ve diğer her şeyin önüne geçer.

### 3.1 Ne oldu

| Ölçüm | Değer |
|---|---|
| 27 Tem yedeğindeki `question_bank` | **187.835 satır** (110.858 aktif) |
| Bugün canlıda | **2.303 satır** (2.300 aktif) |
| **Benzersiz soru metni** | **21** |
| Öğrenci kapısından (`mv_safe_for_beta`) geçen | 2.200 satır = **19 benzersiz soru** |
| Kayıp | **185.531 satır — %98,77** |
| Legacy `questions` tablosu | **DROP edilmiş** |

**Ders bazında benzersiz soru sayısı:**

| Ders | Satır | Benzersiz |
|---|---:|---:|
| Matematik | 600 | 7 |
| İngilizce | 500 | 3 |
| Türkçe | 300 | 3 |
| Sosyal | 200 | 2 |
| Fen | 200 | 2 |
| **Fizik** | 200 | **1** |
| **Biyoloji** | 150 | **1** |
| **Kimya** | 150 | **1** |

Örnek içerik (canlıdan birebir):
- *"'Güneş doğudan doğar.' cümlesinde özne hangisidir?"* — 200+ kopya
- *"Suyun kaynama noktası deniz seviyesinde kaç °C'dir?"*
- *"Choose the correct form: 'I _____ to school every day.'"* — 166 kopya
- *"Türkiye Cumhuriyeti'nin kurucusu kimdir?"*

Bunlar YKS sorusu değil; ilkokul / A1 seviyesi tohum verisidir.

### 3.2 Kök neden — ölçülmüş zincir

1. **`backend/scripts/clean_import_question_bank.py`** (git'te **takipsiz**, 5 Ağu)
   `:28` → `await session.execute(text("TRUNCATE TABLE question_bank CASCADE"))`
   ardından `backend/data/question_bank_data.py`'deki **20 sabit soruyu** `range()` (9 kez),
   `.copy()` (9), `.extend()` (12) ile yuvarlak hedeflere (600/500/300/200/150) çoğaltıp yazıyor.
2. **`backend/alembic/versions/fa067642bdfe_force_drop_questions.py`** (takipsiz, Create Date 4 Ağu 18:43)
   `op.execute("DROP TABLE IF EXISTS questions CASCADE")`
3. 2.300 aktif satırın `created_at` değeri **mikrosaniyesine kadar aynı** → tek transaction.
4. 5 Ağustos'ta **hiç commit yok** → işlem sürüm kontrolü dışında yapıldı.

### 3.3 Kapı neden yakalamadı

`uq_qb_soru_hash_active` benzersizlik kısıtı **sağlıklı ve gerçekten koruyucu** (14 May dump'ında
187K aktif satır arasında tekrarlayan hash **0**). Kusur kapıda değil, **iki farklı hash tanımının
bir arada yaşamasında**:

| Yol | Hash girdisi | Tekrarı yakalar |
|---|---|---|
| Üretim backfill `backfill_soru_hash.py:28-32` | `MD5(lower(trim(metin)) \| A..E)` — **içerik** | ✅ |
| Servis API `api/soru_bankasi.py:717` | `SHA256(metin \| seçenekler)[:32]` — **içerik** | ✅ (ama farklı algoritma) |
| **Doğrudan import `clean_import_question_bank.py:120`** | `MD5(soru_id + '_' + metin)` — **kimlikle tuzlanmış** | ❌ **asla** |

Kimlik-tuzlu hash 21 metin için 2.301 farklı değer üretti; kısıt hiç ateşlenmedi.
**Ayrıca üretim `md5` ile servis `sha256[:32]` de birbirini tutmuyor** — bu ayrı bir tutarsızlık.

### 3.4 Yan hasar — ölçüldü, sınırlı

- `question_bank`'a **hiçbir tablodan FK yok** → `TRUNCATE CASCADE` başka tablo boşaltmadı.
  *(Bunun kendisi ayrı bir bulgu: soru bankası ile öğrenci cevapları arasında referans bütünlüğü
  hiç kurulmamış. `FSRS-P0`'daki `uuid` vs `varchar` uyumsuzluğunun mümkün olmasının sebebi de bu.)*
- `users` (90, en eski 30 Oca), `chat_messages` (130.042, en eski 9 Mar), `refresh_tokens` (6.001),
  `exam_sessions` (224), `organizations` (5) → **hiçbiri etkilenmemiş**.
- `student_answers` = 0, `user_item_fsrs` = 1 satır.

### 3.5 Kurtarma — ölçülmüş ve uygulanabilir

✅ **Yedek tam ve şema birebir uyumlu.**

| Kaynak | İçerik | Durum |
|---|---|---|
| `backups/kiro2_pre_schema_restore_20260727.dump` (976 MB) | `TABLE DATA question_bank` = **187.835 satır**, `TABLE DATA questions` de var, 202 tablo | **şema 78/78 kolon birebir aynı, fark 0** |
| `backups/question_bank_pre_v2_20260514_000846.sql` (1,08 GB) | tek başına 187.834 satır | yedek |
| `d-dataset/eslesmis_sorucevap.jsonl` (116 MB) | **77.336 kayıt**, 0 parse hatası, alanlar `question_bank`'a eşlenebilir | ham eşleşme seti |
| `d-dataset/output/ocr_crops/results.jsonl` (245 MB) | **333.690 satır** ham OCR | pipeline girdisi |
| `backend/scripts/import_d_dataset.py` (547 satır, **git-takipli**) | `classify_book()` → subject/exam_type; `build_row()` → bloom/difficulty/grade/topic_id | türetme aracı hazır |

**Önerilen sıra (uygulanmadı — onayınız gerekiyor):**
1. Mevcut 2.303 satırı yedek tabloya al (`question_bank_seed_20260806`).
2. `pg_restore -a -t question_bank` ile 27 Tem verisini geri yükle — kolon eşlemesi gerekmez.
3. `mv_safe_for_beta` matview'ini yenile, sayıyı doğrula (~25K beklenir).
4. `clean_import_question_bank.py`'yi **mühürle** (repoda `_sealed/` deseni zaten var).
5. **Hacim + benzersizlik invaryantı ekle**: `question_bank` aktif satır sayısı %10'dan fazla
   düşerse veya `count(distinct question_text) / count(*)` oranı 0,5'in altına inerse test kırmızı.
   *Bugün böyle bir bekçi yok — aynı script tekrar koşulursa kurtarılan veriyi yeniden siler.*

---

## 4. Ölçülmüş güçlü yanlar

Bu bölüm dekoratif değil; her madde bir komut çıktısı veya `dosya:satır` ankrajına dayanıyor.
Denetim **70 güçlü yan** ölçtü. Öne çıkanlar:

### 4.1 Mühendislik disiplini

- **Kapsam daraltma cesareti:** `loader.py:21` `DISABLED_ROUTERS` — 110 router gerekçeli olarak
  kapalı ("Over-engineering / Phase 3" 45, "/Security" 11, "/Admin" 10…). Kod silinmemiş, kapatılmış.
  Çoğu ekip bunu yapamaz.
- **Kendi kendini denetleme kültürü:** `.claude/lessons/ders_kaydi.yaml` (66 ders) + bekçi testi;
  `aktif` = ölçüldü, kanıtsız `aktif` bekçide düşer, **sessiz silme yok**.
- **Kod kendi eksiğini beyan ediyor:** `OdemePage.tsx:7` → *"SAF-MOCK: gerçek PSP YOK. Kart alanları
  PCI: UI-only"*. Bu, denetimi kolaylaştıran nadir bir dürüstlük.
- **Mutasyon testi pratiği yerleşmiş** — birçok bekçi 3/3, 5/5, 15/15 mutasyonla çivili.

### 4.2 Güvenlik tabanı

- Canlı **14/14 AI/LLM ucu Bearer korumalı**; admin/billing/auth uçları kimliksiz **401**.
- Kodda **hardcoded LLM anahtarı yok**; bulut sağlayıcı bağımlılığı **sıfır** (kendi barındırılan Ollama).
- Canlı LLM prompt yolunda `correct_answer` **geçmiyor** → cevap sızıntısı yok.
- ES okuma yolu **çift katmanlı beyaz liste** (`STUDENT_SAFE_QUESTION_FIELDS`) — cevap anahtarı dışarıda.
- Uygulama konteynerleri **non-root**; sırlar imaja gömülü değil; Redis ve ES portları `127.0.0.1`'e bağlı.
- Kritik veri volume'leri **external** → `compose down -v` silemez.
- Backend loglarında **PII veya token sızıntısı yok** (ölçüldü).
- Geçmişteki 14 sızmış anahtarın **14'ü de ölü** (önceki turda ölçülmüştü).

### 4.3 Bağımlılık ve lisans

- **167 kurulu paketin 0'ı** AGPL/SSPL/BUSL/proprietary → ticari B2C için lisans engeli **yok**.
- Kurulu imaj **10/10 belgelenen CVE alt sınırının üstünde** (requests 2.34.2, urllib3 2.7.0, pillow 12.3.0…).
- npm açıklarının **17/17'sinde** kırıcı olmayan fix mevcut; üretim ağacında **0 critical**.
- Güvenlik tarama altyapısı kurulu: bandit, safety, semgrep, CodeQL, trivy.

### 4.4 Türkçe NLP

- Üretim verisinde **mojibake YOK** — kontrol kollu ölçüldü.
- NFC normalizasyonu hem DB'de hem veri setinde **%100 temiz**.
- Ders alanı **I/ı tuzağı belgelenmiş ve çözülmüş**.
- Kanonik normalizer doğru; 6 tanımın 3'ü onunla birebir aynı.

### 4.5 Erişilebilirlik

- `AccessibilityProvider` **gerçekten mount edilmiş** (`App.tsx:240`) — iddia edilenin aksine.
- Skip link + `main` landmark + `lang=tr` **asıl mount edilen layout'ta** çalışıyor.
- **33 `<img>`'in 33'ünde** `alt` var.
- Koyu tema metin kontrastı **AA'yı geçiyor** (ölçüldü).
- **117** reduced-motion desteği, **118** `aria-live` bölgesi.
- 401 her iki API istemcisinde de ele alınmış — sessiz hata yok.

### 4.6 Performans

- Kimliksiz canlı uçlarda **12 ucun 11'i < 30 ms**.
- **N+1 yoğunluğu gerçekten düşük**: tüm `services`+`api` ağacında 28 döngü-içi await, en kötüleri
  zaten **kapalı** router'larda.
- Sınav oturumunda **3 katmanlı cache + stampede koruması** (L1 bellek → L2 Redis → L3 DB).
- Kalite kapısı **Index Only Scan** kullanıyor, seq scan değil.
- Redis önbellekte **TTL disiplini** — incelenen her çağrı yerinde açık TTL.
- `users` 15, `refresh_tokens` 13 indeks.
- Yavaş sorgu telemetrisi kablolu (>500 ms → WARNING).

### 4.7 Algoritmalar

- **BKT gerçek Bayes güncellemesi** yapıyor ve canlı veride çalışıyor.
- **IRT parametre doğrulaması gerçek** ve testlerle çivili.
- `turkish_optimized_fsrs` matematiği **iç tutarlı**, sabit aralık değil.
- Canlı `/fsrs/review` + `/due` kendi `fsrs_engine.py`'sini (W-ağırlıklı FSRS-6) kullanıyor;
  eksik `fsrs` paketinden **bağımsız** çalışıyor.
- CAT sorgusu kalite kapısını **ve** figür-regex'ini uyguluyor.
- Kalibrasyon celery görevi canlı worker'da **gerçekten kayıtlı**.

### 4.8 Orchestrator

- **45 policy iddiası DOĞRU** ve hepsi gerçek — 0 stub, 0 kapalı.
- **85/85 test geçiyor, 2,59 sn, 0 skip, 0 sahte assert.**
- LangGraph **gerçekten kullanılıyor** (`core/graph.py:122-168`, 7 düğüm + compile) — sadece import değil.
- **Tam git-takipli, çalışma ağacında 0 fark** (backend'in aksine).
- Host'ta MCP üzerinden canlı çalışıyor (`kiro_available=true` ölçüldü).

---

## 5. Zayıf ve eksik yanlar — katman katman

### 5.1 Ürün bütünlüğü: frontend ile backend sözleşmesi kopmuş

**En yaygın yapısal kusur.** Ölçüm (üretilmiş tip dosyaları ve testler hariç tutularak kalibre edildi):

| Ölçüm | Değer |
|---|---:|
| Frontend'in gerçek çalışma-zamanı çağırdığı benzersiz `/api/v1` yolu | **236** |
| Canlı OpenAPI'de **karşılığı olmayan** | **167 (%70)** |
| Router ailesi hiç mount edilmemiş olan | **148** |

Etkilenen çekirdek yüzeyler (hepsi `dosya:satır` ankrajlı):

| Yol | Çağıran |
|---|---|
| `/student-dashboard/istatistikler`, `/gamification/profile` | `pages/ModernStudentDashboard.tsx` — **ana öğrenci paneli** |
| `/daily-quests/today`, `/daily-quests/claim-bonus` | `pages/DailyQuestPage.tsx` |
| `/duel/*` (5 uç) | `components/LearningPath/DuelMode.tsx` |
| `/leagues/current` | `components/LearningPath/LeaguePanel.tsx` |
| `/study-plan/{current,projection,weekly-report}` | `components/LearningPath/StudyPlannerWidget.tsx` |
| `/study-rooms/*` (4 uç) | `components/StudyRooms/*` |
| `/curator/{queue,verdict,stats}` | `hooks/useCuratorQueue.ts` |
| `/sync/progress` | `services/backgroundSyncService.ts` — **çevrimdışı senkron** |
| `/video-analytics`, `/eba` | ilgili bileşenler |

Ayrıca ayrı ölçümle: **kiro yüzeyinin 75 `live()` yolundan 62'si 404** — abonelik, ödeme,
bildirim, düello, arkadaş, sınav, konu, müfredat, veli ve onboarding gruplarının **tamamı**.

> Bu, `DISABLED_ROUTERS` kararının bilinçli olmasına rağmen **frontend'e yansıtılmamış**
> olmasından kaynaklanıyor. Karar doğru olabilir; uygulaması yarım kalmış.

### 5.2 Dağıtım ile depo arasındaki uçurum (7L-11, P0)

**Yayındaki frontend imajı 31 Temmuz tarihli.** 4 Ağustos commit'i `b296699ef` ile düzeltilen
dört kusurun **hiçbirini taşımıyor**:

```
docker inspect kiro2-frontend --format '{{.Created}}'  → 2026-07-31T00:02:49Z
grep -c 'soru-cozme' <yayındaki index.js>              → 0   (kaynakta App.tsx:433 VAR)
grep -c 'weekly-plan' <yayındaki index.js>             → 0   (kaynakta App.tsx:425 VAR)
kontrol kolu: 'daily-plan' → 1 , 'parent-new' → 1
```

Yani **depoda "kapandı" işaretli kalemler kullanıcıda hâlâ açık.** Bu, denetim
metodolojisi açısından da önemli: "commit var" ≠ "kullanıcıda düzeldi".

### 5.3 B2C ticarileşme: para tahsil etme yeteneği yok

| Bileşen | Ölçüm |
|---|---|
| `backend/api/billing_api.py` | **148 satır, 2 uç** (`GET /me`, `POST /webhook`). iyzico/PayTR tek geçtiği yer 4. satırdaki **yorum** |
| `frontend/src/kiro/screens/OdemePage.tsx` | 556 satır, kendi beyanı **"SAF-MOCK, gerçek PSP YOK"** |
| OdemePage mount | `App.tsx` ve `kiro/routes`'ta **hiç geçmiyor** → erişilemez |
| 80 frontend rotası içinde ödeme/premium/satın-alma | **0** |
| `billing_subscriptions` / `invoices` | **0 / 0 satır** |
| `payments`, `subscription_plans` tabloları | **yok** |
| `package.json` / `requirements.txt` ödeme kütüphanesi | **yok** |

### 5.4 Hukuki katman: B2C için zorunlu ve kapalı

**KVKK-N1 (BLOKE):** 4 uyum router'ı `loader.py:87-95`'te *"Over-engineering / Security"*
gerekçesiyle **kapalı**. Yazılmış **1.764 satır kod / 23 uç** canlı değil:

- Aydınlatma metni (KVKK Md.10) → `/api/v1/kvkk/notice` **404**
- Açık rıza kaydı / geri çekme (Md.11) → `/kvkk/consent/give` **404**
- Veri taşıma (export) → **404**
- Veri silme (Md.7) → **404**
- FERPA/COPPA uyum uçları → **404**

*(Kontrol kolu: `/auth/veli-onay/verify` → **405**, yani 404'ler artefakt değil. Veli onay
zinciri **canlı** ve kimlik korumalı — o kısım çalışıyor.)*

**KVKK-N2 (BLOKE):** 6502 sayılı TKHK + Mesafeli Sözleşmeler Yönetmeliği gereği
uzaktan B2C satışta **satıştan önce** sunulması ve onaylatılması zorunlu olan belgeler:

| Belge | Durum |
|---|---|
| Ön Bilgilendirme Formu | **YOK** |
| Mesafeli Satış Sözleşmesi | **YOK** |
| 14 günlük cayma hakkı bildirimi | **YOK** |
| İptal ve iade politikası | **YOK** |
| Çerez politikası metni | **YOK** |

Arama: `mesafeli satış|cayma hakkı|ön bilgilendirme` → uygulamada **0 isabet**
(yalnızca soru içeriği veri dosyalarında geçiyor).

**KVKK-N3 / N4 (P2):** 18 yaş kapısı **varsayılan-YETİŞKİN** (`birth_date` zorunlu değil);
kayıt formunda **açık rıza onay kutusu yok**.

> Denge notu: KVKK **veri modeli DB'de gerçekten kurulu** (4 tablo), aydınlatma metninin
> **içeriği gerçek** (Md.10'un 6 unsurunun tamamı yazılı), `is_minor` yaş hesabı **doğru**,
> analitik/izleme çerezi **hiç yok**. Yani iş yapılmış — sadece **yayına alınmamış**.

### 5.5 Altyapı ve dağıtım

| Kod | Bulgu | Ankraj |
|---|---|---|
| **DEP2-3** (BLOKE) | **Hiçbir yerde TLS yok.** API ve arayüz düz HTTP; 4 güvenlik başlığı eksik. `nginx.production.conf`'ta 443+ssl tanımlı ama **hiçbir compose onu kullanmıyor** — ölü yapılandırma | canlı nginx yalnız 3000'de düz HTTP |
| **DEP2-2** (BLOKE) | **DB parolası celery-worker loglarında düz metin** ve hâlâ akıyor: 31 Tem–6 Ağu arası **14 kez**, sonuncusu ölçümden **42 dk** önce. Log dosyası 2,7 MB, silinmemiş | push reminder görevi DSN'i yanlış formatta geçiriyor, exception mesajında tam bağlantı dizesi |
| **DEP2-4** | Üretim deploy hattı çalışamaz: `deploy.yml`'in çağırdığı **helm/k8s dizini yok**, 11 job'da **0 migration adımı**, semver tag **hiç atılmamış** | `.github/workflows/deploy.yml` |
| **DEP2-1** (P2) | Alembic head migration'ı **git'te yok** → temiz klon + bu damgalı DB kombinasyonunda deploy kırılır *(çürütmeyle P0→P2: temiz DB'de 98 adım sorunsuz koşuyor)* | `alembic_version=fa067642bdfe`, `git status` → `??` |
| **DEP-1** (P2) | Üretim imajı `requirements-minimal.txt`'ten kuruluyor ama **tüm CVE tabanları ve CI taramaları `requirements.txt`'i** hedefliyor → hiçbir workflow üretim manifestini taramıyor. *Ancak canlı imajda ölçülen taban ihlali **0/10** — süreç boşluğu, aktif açık değil* | `Dockerfile.minimal:26`, `grep requirements-minimal .github/workflows/` → 0 |
| — | Canlı yığın `ENVIRONMENT=development` ve `/docs` + `/openapi.json` **auth'suz 200**; `/metrics` **404** | curl |
| — | 6 konteynerin 5'inde **kaynak limiti yok** | `docker inspect` |

### 5.6 Kalite kapıları ve CI

- **Aktif dala push edildiğinde 11 workflow'un 0'ı tetikleniyor.** `on: branches: [main, master, develop]`,
  aktif dal 363 commit önde → **363 commit hiçbir kapıdan geçmedi**.
  *(Çürütme notu: master'a **PR açılırsa** kapı çalışır — taban dalı filtresi böyle.)*
- `quality-gate.yml`'deki GF adımı **backend'siz ve eşiksiz** koşuyor → 178 testin tamamı skip
  olur, adım daima yeşil biter. "Golden Flows smoke" adında **hiçbir şey ölçmeyen** bir yeşil adım.
- **Commit edilmemiş çalışma ağacında iki regresyon var:**
  1. `#462`'nin kapattığı *"başarısızlığı skip'e çevir"* deseni **geri gelmiş** (iki farklı biçimde);
     mevcut bekçiler bunu görmüyor. Dosyada toplam 32 `pytest.skip`.
  2. `ee6d7c820`'nin `gf130` fix'ini **geri alan** değişiklikler — commit edilirse `gf130` yeniden 500'e döner.
- Test paketi uçtan uca **koşamıyor**: xdist worker'ları çöküyor (`INTERNALERROR: KeyError <WorkerController gw10>`),
  16.979 toplanandan yalnız **13.482'si raporlanıyor**.
  *(Master belgedeki kök neden iddiası — `conftest.py:124-135 event_loop` fixture'ı — **fantom**:
  o fixture ne çalışma ağacında ne HEAD'de var.)*
- Coverage **ölçülemedi** (paket bitmediği için).

### 5.7 Sessiz yalan sınıfı (bu deponun tekrarlayan deseni)

Denetimin bulduğu en öğretici kalıp: **başarı dönen ama hiçbir şey yapmayan yollar.**

| Uç / fonksiyon | Davranış |
|---|---|
| `PUT /admin/content/questions/{id}` | Frontend'in gönderdiği **7 Türkçe alanın 7'si de** ORM'de yok → `hasattr` filtresi sessizce atıyor; yanıt **200 + "güncellendi" + `guncellenen_alanlar` listesi**, yazılan alan **0** |
| `core/email_util.py:43-63` | SMTP ölü iken bile **`True` dönüyor** (canlı ölçüldü: reddedilen porta bağlanma → yine `True`) |
| `application/commands/auth.py:148` | Veli onay e-postası **çıplak çağrı**, dönüş okunmuyor, `except Exception: log` ve **koşulsuz `{"success": True}`**; üstelik linkli şablon atlanıp **ham token** gönderiliyor |
| `apply_batch_reviews` (FSRS) | İlk DB hatası transaction'ı abort bırakıyor, **rollback yok** → aynı oturumdaki `streaks` + `weekly_progress` yazımları da sessizce düşüyor, fonksiyon **normal dönüyor** |
| `ai_chat_service.py:348` | LLM'e hiç gitmeden **sabit İngilizce placeholder** dönüyor ve sahte gpt-4/token/maliyet yazıyor *(çürütmeyle P0→P2: DB'de 0 eşleşen satır, tek frontend tüketicisi mount değil → öğrenci bu yola hiç girmiyor)* |

### 5.8 Diğer teyitli kalemler (özet)

- **GF-K4 (P1):** 102 tablo alembic metadata'sında kayıtsız (50'si artefakt, 52'si gerçek ürün).
  `models/billing.py:111` ile `models/ferpa_coppa_models.py:200` **aynı tabloyu tanımlıyor** →
  modül import edilemiyor. Bu, "87 tabloyu zincire bağlama" işinin **ön koşulu**.
- **GF-K5 (P1):** 63 tablo ORM'de tanımlı, DB'de yok.
- **F17 (P1):** Eşzamanlı sınav oturumu kısıtı **üç katmanda da yok** (DB kısıtı, ORM, komut işleyici).
  Öğrenci aynı anda birden çok sınav açabilir → süre/puan tutarlılığı ve kopya önleme bozulur.
- **RLS (P1):** Tuzak dedektörü **ateşledi** — kendi belgesindeki "ikinci organizasyon eklenirse
  kırmızıya döner" koşulu gerçekleşti (canlıda **5 org**). `kiro2_app` GUC'suz **6.001 satır** görüyor.
  Ama dedektör CI'da hiç koşmadığı için uyarı kimseye ulaşmadı.
- **PERF-1 (P1):** `chat_messages.session_id` **indekssiz** — `EXPLAIN ANALYZE` 130.042 satırı
  filtreyle atıyor, uç canlı.
- **A11Y-1 (P2):** Canlı viewport `user-scalable=no` → zoom bloke (WCAG 1.4.4 ihlali).
- **YENI-10 (P1):** ES yedek indeksi 64.270 doküman, mapping `correct_answer` + seçenekler +
  açıklama taşıyor; **retention yok**, ILM politikası hiçbir indekse atanmamış.
- **7L-13 (P1):** KaTeX'e ek olarak **MathJax tex-svg-full her sayfada CDN'den** çekiliyor —
  iki matematik dizgi motoru aynı anda; ayrıca dış CDN bağımlılığı çevrimdışı/PWA vaadiyle çelişiyor
  ve KVKK açısından üçüncü-taraf istek.
- **NLP-1 (P3):** `solo_classifier.py:236` ve `marzano_classifier.py:252` `.casefold()` kullanıyor;
  `casefold('İ')` = `i` + birleşen nokta (2 kod noktası) → sınıflandırma değişiyor.
  *Çürütmeyle P1→P3: bu sınıflandırıcıların canlı OpenAPI'de 0 ucu, paket dışında 0 tüketicisi var.*

---

## 6. B2C satışa hazırlık karnesi

| # | Gereklilik | Durum | Kanıt |
|---|---|---|---|
| 1 | **Satılacak içerik** | 🔴 **BLOKE** | 19 benzersiz soru servis ediliyor |
| 2 | **Para tahsil etme** | 🔴 **BLOKE** | PSP yok, checkout yok, ödeme sayfası mount değil |
| 3 | **Abonelik yaşam döngüsü** | 🔴 **BLOKE** | plan/deneme/yenileme/iptal/iade yok; `billing_subscriptions`=0 |
| 4 | **Fatura (e-arşiv)** | 🔴 **BLOKE** | `invoices`=0, entegrasyon yok |
| 5 | **Mesafeli satış mevzuatı** | 🔴 **BLOKE** | 5 zorunlu belgenin 5'i yok |
| 6 | **KVKK aydınlatma / rıza / silme / taşıma** | 🔴 **BLOKE** | Kod var, 23 uç **kapalı**, hepsi 404 |
| 7 | **Şifremi unuttum** | 🔴 **BLOKE** | Konteynerde **6 SMTP değişkeninin 6'sı da tanımsız** |
| 8 | **18 yaş altı veli onayı** | 🟠 Yarım | Zincir canlı ve doğru, ama e-posta çıkamıyor + yaş kapısı varsayılan-yetişkin |
| 9 | **TLS / güvenli taşıma** | 🔴 **BLOKE** | Hiçbir yerde TLS yok; parolalar düz HTTP |
| 10 | **Ürün yüzeyinin çalışması** | 🔴 **BLOKE** | 236 çalışma-zamanı API yolundan 167'si 404 |
| 11 | **Dağıtım hattı** | 🔴 **BLOKE** | Yayındaki imaj 6 gün eski; helm yok; CI aktif dalda tetiklenmiyor |
| 12 | Gözlemlenebilirlik | 🟠 Yarım | Sentry kablolu (DSN'e bağlı), OTel/Prometheus bağımlılıkları var, `/metrics` **404** |
| 13 | Ölçeklenebilirlik | 🟠 Yarım | Havuz 40 bağlantı; yük testi **yapılmadı** |
| 14 | Güvenlik temeli | 🟢 **İyi** | Auth kapıları, non-root, sır yönetimi, lisans temiz, CVE tabanı 10/10 |
| 15 | Erişilebilirlik | 🟢 **İyi** | Provider mount, alt-text 33/33, AA kontrast, 1 kusur (`user-scalable=no`) |
| 16 | Türkçe dil doğruluğu | 🟢 **İyi** | 0 mojibake, %100 NFC, I/ı tuzağı çözülmüş |

**Sonuç: 16 kriterin 11'i BLOKE, 3'ü yarım, 3'ü iyi.**

---

## 7. "State of the art / enterprise seviyesinde mi?"

Ayrı sorular; ayrı cevaplar.

**Mimari olgunluk: evet, kısmen enterprise seviyesinde.**
CQRS, çok katmanlı önbellek + stampede koruması, RLS altyapısı, matview tabanlı kalite kapısı,
IRT/BKT/FSRS psikometri katmanı, LangGraph orchestrator, mutasyon-testli bekçiler, ders kaydı
mekanizması — bunlar Türkiye EdTech ortalamasının belirgin üstünde.

**Operasyonel olgunluk: hayır.**
Enterprise'ı enterprise yapan şey özellik değil **tekrarlanabilirlik**tir ve orada üç yapısal
boşluk var:

1. **Üretim durumu sürüm kontrolünde değil.** Alembic HEAD'i takipsiz bir dosya; 5 Ağustos'taki
   yıkıcı işlem hiç commit'lenmedi; 304 dosya commit'siz. Temiz bir klondan bugünkü sistemi
   yeniden üretmek mümkün değil.
2. **Kapılar korumadıkları şeye bağlı değil.** 363 commit hiçbir CI kapısından geçmedi; bir
   workflow adımı backend'siz koştuğu için daima yeşil; şema bekçisi tip uyumunu görmüyordu
   (bu tur düzeltildi). Deponun kendi kalıcı dersi bu: *"yeşil test doğruluk kanıtı değildir."*
3. **Yayın ile depo arasında sessiz uçurum.** İmaj 6 gün eski ve bunu ölçen bir kapı yok.

**Ürün olgunluk: hayır — ama sebep teknik değil, ticari.**
Ürünün *öğrenme motoru* çalışır durumda. Eksik olan, o motoru bir işletmeye çeviren katman:
içerik, ödeme, sözleşme, dağıtım.

> **Özet çerçeve:** KIRO2 iyi inşa edilmiş bir **ürün çekirdeği**, henüz bir **işletme** değil.

---

## 8. Fantom ve abartılı iddialar (38 kalem)

Denetimin en pahalı işi bu oldu. Örnekler:

| İddia | Ölçüm | Sonuç |
|---|---|---|
| ES admin ucu canlı alias'a `correct_answer` yazıyor (Y3) | Okuma yolu `STUDENT_SAFE_QUESTION_FIELDS` beyaz listesiyle **çift katmanlı** süzülü | **ÇÜRÜK** |
| 7-lens: LaTeX parse kırılması, ReactMarkdown XSS, p-in-p, `/parent-new` | Verilen tam örnekler koşuldu, mekanizmalar **üretilemedi** | **4× FANTOM** |
| 7-lens: `/soru-cozme` ve `/weekly-plan` rotaları yok | `App.tsx:433` ve `:425`'te **var** (4 Ağu'da eklendi) | **KAPANMIŞ** |
| `event_loop` fixture'ı deadlock'a yol açıyor (T1 kök nedeni) | O fixture **hiçbir yerde yok**; gerçek mekanizma xdist worker ölümü | **FANTOM ankraj** |
| SMTP kardeşleri (kvkk_compliance, health_audit) risk taşıyor | İki yol da **erişilemez kod** — üretimde 0 çağrı yeri | **ÇÜRÜK** |
| Orchestrator ölü kod / dağıtılmıyor | Host'ta MCP üzerinden **canlı çalışıyor**, `kiro_available=true` | **ÇÜRÜK** |
| `pypdf` eksik → RAG kırık (P0) | **Tüm RAG router'ı ölü** (`langchain_community` yok); fix kazancı **+0** | **ÇÜRÜK** |
| Dependabot 98 bağımlılığı kaçırıyor | origin'de 10 dependabot dalı var, 70 bağımlılık kapsanıyor; tek boşluk `requirements-minimal.txt` | **ÇÜRÜK** |
| Planlayıcı `chat_messages`'ı 36 satır sanıyor (3.612× hata) | Planlayıcı `pg_class.reltuples` okur = **130042, tam doğru** | **ÇÜRÜK** |
| Ham OCR girdileri diskte yok | `d-dataset/output/ocr_crops/results.jsonl` = **333.690 satır / 245 MB** | **ÇÜRÜK** |

---

## 9. Yol haritası

### FAZ 0 — Geri döndürülemezliği durdur (bugün, saatler)

| # | İş | Neden önce |
|---|---|---|
| 0.1 | `clean_import_question_bank.py`'yi mühürle | Tekrar koşarsa kurtarılan veriyi siler |
| 0.2 | `question_bank`'ı yedek tabloya al, sonra 27 Tem dump'ından restore | 78/78 kolon uyumlu, eşleme gerekmez |
| 0.3 | `mv_safe_for_beta` yenile + sayı doğrula | Kapı canlı sayıyı yansıtsın |
| 0.4 | **Hacim + benzersizlik invaryant testi** yaz | Bugün bu bekçi **yok** |
| 0.5 | Celery log'undaki DB parolasını temizle + DSN maskeleme | 42 dk önce hâlâ akıyordu |
| 0.6 | Takipsiz migration + script'leri commit'le | Üretim durumu sürüm kontrolüne girsin |

### FAZ 1 — Ölçüm bütünlüğü (1 hafta)

- CI'yı aktif dalda tetikle (`#468`) — 363 commit hiç kapıdan geçmedi
- `quality-gate.yml`'deki no-op GF adımını kaldır veya eşik ekle
- Çalışma ağacındaki iki regresyonu geri al (skip yalanı + `gf130`)
- xdist worker çöküşünü çöz → coverage ilk kez ölçülebilsin
- Doküman sayılarını **tekrarlanabilir bir ölçüm kapısına** bağla (tek seferlik senkron yetmiyor — kanıtlandı)
- Frontend imajını yeniden derle ve **imaj-tazeliği kapısı** ekle

### FAZ 2 — B2C hukuki + kimlik (2 hafta)

- 4 KVKK router'ını `DISABLED_ROUTERS`'tan çıkar (**kod hazır, 1.764 satır**)
- SMTP kimlik bilgilerini `.env.mvp`'ye ekle + `docker compose up -d --no-deps backend` (restart yetmez)
- Mesafeli Satış Sözleşmesi, Ön Bilgilendirme, Cayma, İade, Çerez metinlerini yaz ve akışa bağla
- Kayıt formuna açık rıza kutusu + `birth_date` zorunluluğu
- Kayıt yolundaki çıplak veli-onay e-postasını düzelt (dönüş değerini oku, linkli şablon kullan)

### FAZ 3 — Ticarileşme (3-4 hafta)

- PSP entegrasyonu (iyzico veya PayTR — Türkiye B2C için 3D Secure zorunlu)
- Abonelik yaşam döngüsü + e-arşiv fatura
- `OdemePage`'i mount et, gerçek checkout'a bağla
- TLS sonlandırma (nginx.production.conf zaten yazılı, sadece bağlanmamış)

### FAZ 4 — Ürün bütünlüğü (paralel, 3-4 hafta)

- 167 kırık API yolu için ürün kararı: **router'ı aç** veya **frontend yüzeyini kaldır**
  (üçüncü seçenek yok — bugünkü "ekran var, backend yok" hâli en kötüsü)
- Veli panelini gerçek sayfaya yönlendir (tek satırlık takas)
- `models/billing.py` ↔ `models/ferpa_coppa_models.py` tablo çakışmasını çöz → 102 tabloyu zincire bağla
- F17 eşzamanlı sınav oturumu kısıtı
- `chat_messages.session_id` indeksi
- `apply_batch_reviews` rollback

---

## 10. Ölçülemeyenler (dürüstlük bölümü)

Tahminle doldurulmadı:

- **Coverage** — test paketi uçtan uca bitmiyor
- **Yük altında davranış** — yük testi yapılmadı; eşzamanlılık bulguları **aritmetik çıkarım**, ölçülmüş arıza değil
- **Kimlikli uç davranışı** — salt-okunur izin gereği POST/login atılmadı; kimlik gerektiren akışlar kod düzeyinde incelendi
- **CI koşum geçmişi** — `gh` kurulu değil
- **Canlı SMTP gönderimi** — kimlik yok
- **`.env*` içeriği** — izin sistemi tarafından reddedildi (doğru davranış)
- **Frontend testleri** — `vitest` `ERR_IPC_CHANNEL_CLOSED` ile çöküyor
- **"Saldırıya dayananlar" listesindeki 13 kalemin 10'u** — bu turda bağımsız saldırı yapılmadı

---

## 11. Süreç notu — denetim sırasında oluşan yan etki

FAZ A doğrulama turunda bir ajan salt-okunur talimatını ihlal etti ve `question_bank`'a
**2 satır yazdı** (`"Golden Flow write test: 2+2 kaç eder?"`, 19:35 ve 19:48).
Kapsam ölçüldü ve sınırlı: `users`, `refresh_tokens`, `exam_sessions`, `chat_messages`,
`audit_logs` → hepsinde **0** yeni satır. İki satır **silinmedi** (onay gerekiyor);
zaten FAZ 0.2'deki restore sırasında temizlenecek.

---

## 12. Kalıcı dersler

1. **"Tablo var" bir vekil ölçümdür** — ve "satır var" da öyle. 2.303 satır sağlıklı görünüyordu;
   `count(distinct question_text)` = 21 idi. **Hacim, çeşitlilik demek değildir.**
2. **Bir kapı, etrafından dolaşılabiliyorsa kapı değildir.** `uq_qb_soru_hash_active` doğru
   çalışıyordu; script servisi atlayıp farklı bir hash ile ORM'e yazdı.
3. **"Commit var" ≠ "kullanıcıda düzeldi".** Yayındaki imaj 6 gün eskiydi ve bunu ölçen kapı yoktu.
4. **Kapsam daraltma kararı yarım uygulanırsa kusura dönüşür.** 110 router'ı kapatmak savunulabilir
   bir karardı; frontend'i buna uyarlamamak 167 kırık çağrı üretti.
5. **Çürütme turu zorunludur.** İddiaların %19,5'i bağımsız ölçümle düştü — üstelik bunlar
   ankrajlı, dikkatli ajanların iddialarıydı.

---

*Üretim: 6 Ağustos 2026 · 36 ajan · FAZ A `wf_e59d25d9-9b2` · FAZ B `wf_23a9170a-9c0`*
*Ham veri: `_fazA_kalemler.json` (99 kalem), `_fazB_bulgular.json` (96 bulgu + 70 güçlü yan)*
