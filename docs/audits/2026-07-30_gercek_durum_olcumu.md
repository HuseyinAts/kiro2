# KIRO2 Gerçek Durum Ölçümü — 30 Temmuz 2026

> **Bu bir audit değil, bir ölçümdür.** Aşağıdaki her satır ham komut çıktısına dayanır.
> Ölçülemeyen hiçbir şey tahminle doldurulmamıştır. Bu deponun en pahalı hatası tam
> olarak buydu (`.claude/rules/audit-methodology.md` — "Varsayım ≠ Ölçüm").

| | |
|---|---|
| **Ölçüm tarihi** | 2026-07-30, 14:45–19:20 (TSS) |
| **Depo kökü** | `C:\Users\husey\kiro2` |
| **Dal / HEAD** | `feature/self-evolution-optimization` / `889c71a3a923fd16ae3f612b8cb4692b234a4f5b` |
| **Boyut sayısı** | 7 (git, db, servisler, testler, kod, iddialar, backlog) |
| **Yöntem** | Her boyut önce ölçüldü, sonra **farklı bir aletle** çapraz doğrulandı |
| **Yazma işlemi** | YOK — salt okunur. Ölçüm sonunda `git status --short` BOŞ |

---

## 0. Tek Cümlelik Durum

**KIRO2 canlı ve ayakta (9 konteyner healthy, 187.835 soru, 1.226 uç), fakat dokümantasyonun
neredeyse tüm sayısal iddiaları 2–12 kat bayat, CI'ın son 100 koşusunun 100'ü kırmızı,
"merge kapısı" sayılan Golden Flow paketinin %83'ü rate-limit yüzünden hiç koşmuyor ve
bugün bitirilen iki özellik (#444, #447) canlıya dağıtılmamış durumda.**

---

## 1. Metodoloji

### 1.1 Kullanılan aletler

| Alet | Nerede | Not |
|---|---|---|
| `git` (ls-files, ls-tree, ls-remote, check-ignore, count-objects, fsck, merge-base) | git boyutu, kod envanteri | `ls-remote` **canlı uzak uçtan** okundu, yerel remote-tracking ref'e güvenilmedi |
| `psql.exe` (PostgreSQL 18 native) | db boyutu | `-f -` ile stdin borulama; Türkçe SQL için `-c` kullanılmadı |
| `psycopg2` (host python) | db çapraz doğrulama | Farklı sürücü = bağımsız alet |
| `asyncpg` (konteyner içi) | db çapraz doğrulama | Farklı rol (`kiro2_app`), farklı ağ yolu |
| `curl` + `python urllib` | servis/uç ölçümü | İkisi de ayrı ayrı koşuldu |
| ham TCP soket (RESP) | Redis | `redis-cli` ve `docker` **hiç kullanılmadan** |
| `docker` (ps, ps -a, inspect, exec, logs, port) | servisler | `ps -a` ile durmuş konteynerler de listelendi |
| `pytest` (--collect-only, gerçek koşum) | testler | Tam suite koşulmadı (kilitleniyor) |
| Python `ast` | kod, testler, iddialar | grep'in sahte pozitiflerini elemek için |
| `tinyglobby` (vitest'in kendi glob motoru) | frontend | vitest.config.ts desenleri birebir uygulandı |
| `coverage` (sqlite yeniden hesap) | testler | `-i` bayrağıyla |
| GitHub REST API (auth'suz) | backlog | Kontrol kolu: var olmayan depo → 404 |

### 1.2 Alet doğrulama disiplini

Her sıfır/404/boş sonuç, **bulgu sayılmadan önce** bilinen-pozitif bir kontrol koluyla
sınandı. Bu disiplin bu oturumda **14 sahte bulgu** üretmemizi engelledi (bkz. §9).

Örnek kontrol kolları:

```
# "kayıtsız router = 0 canlı rota" iddiası için bilinen-kayıtlı router ile kontrol:
/api/v1/cat  -> 4 canlı rota   (probe çalışıyor)
/api/v1/learning-path -> 0     (gerçek yokluk)

# "GUC yoksa RLS geçirir" iddiası için:
kiro2_app + GUC yok    -> refresh_tokens 5558  (= superuser taban çizgisi)
kiro2_app + sahte GUC  -> refresh_tokens 0     (kol beklenen sonucu verdi)

# "untracked = 0" iddiası için:
git status --porcelain             -> 0 satır
git status --porcelain --ignored   -> 4114 satır  (alet dosya görebiliyor)
```

### 1.3 Bu ölçümde YAPILMAYANLAR

- Tam `pytest` suite koşulmadı (16.931 test; ayrıca `tests/unit` kilitleniyor)
- Coverage taze ölçülmedi (diskteki 27 Mayıs artefaktı yeniden hesaplandı)
- `frontend` tam `npm test` koşulmadı
- Hiçbir DB yazması, commit, checkout, rebuild yapılmadı
- Şifre kurtarma ucu **bilerek tetiklenmedi** (Redis'e kod yazacaktı)
- Anahtar canlılığı (`--check-live`) yeniden ölçülmedi (sağlayıcılara istek atacaktı)

---

## 2. Boyut: Sürüm Kontrolü (git)

### 2.1 Ölçümler

| Konu | İddia | Ölçülen | Durum | Kanıt komutu |
|---|---|---|---|---|
| Aktif dal | MEMORY: `feature/self-evolution-optimization` | aynı | ✅ UYUMLU | `git rev-parse --abbrev-ref HEAD` |
| HEAD | Oturum-başı snapshot `688e42377` | `889c71a3a92…` — snapshot **25 commit geride** | ⚠️ BAYAT | `git rev-list --count 688e42377..HEAD` = 25 |
| Çalışma ağacı | `(clean)` | 0 değişiklik, 0 untracked (`-uall`) | ✅ UYUMLU | `git status --porcelain -uall \| wc -l` = 0 |
| Uzak uç senkron | — | ahead=0, behind=0; uzak dal = `889c71a3a` | ✅ | `git ls-remote origin` (canlı) |
| Bugünkü commit | — | **39 commit**, tek yazar, 03:41:19 → 17:49:28 (14s 8dk) | ✅ | `git log --since=midnight` |
| master farkı | — | `master..HEAD` = **296 ileri**, `HEAD..master` = **0** (sapma yok) | ✅ | `git rev-list --count` |
| `.git` boyutu | MEMORY/CLAUDE.local: **218 MB** (Session 71) | **6,7 GiB** (`du`), 7.125.605.052 bayt (python) | ❌ ~31x BAYAT | `git count-objects -vH` + `os.walk` |
| Nesne sayısı | — | in-pack 98.093, loose 3.234 (11,47 MiB), 4 pack | ✅ | `git count-objects -vH` |
| Büyük pack | — | 6,0 GiB; **ctime 2026-07-01 15:10:19** (mtime 07-30 03:36) | ✅ | `os.stat` |
| Depo sağlığı | — | `fsck` exit 0; ≥8 dangling commit, ≥12 dangling tree; 1 garbage (123 bayt) | ✅ | `git fsck --connectivity-only` |
| LFS desen sayısı | CLAUDE.md: 4 desen (`*.jsonl`,`*.bin`,`*.pt`,`*.db`) | **5 desen** — `*.onnx` dokümante edilmemiş | ❌ | `git lfs track` + `.gitattributes` |
| LFS >50MB eşiği | CLAUDE.md: `*.jsonl (>50MB)`, `*.db (>50MB)` | **.gitattributes'ta hiçbir boyut eşiği YOK** (`grep -c '50'` = 0) | ❌ | desenler koşulsuz |
| LFS dosya sayısı | — | 527 (`lfs ls-files`) / 528 (`check-attr filter=lfs`) | ✅ | fark = 1 sıfır-baytlık jsonl, alet artefaktı |
| `.git/lfs` yerel önbellek | — | 15,2 MiB | ✅ | Şişme LFS'ten DEĞİL |
| `backend/.gitignore` | Görev metni varlığını varsaydı | **YOK.** backend yolları kök `.gitignore`:24/63/149 tarafından yönetiliyor | ❌ | `git check-ignore -v` |
| Kök `.gitignore` | — | 402 satır, **69 ankrajsız dizin deseni** | ⚠️ | python parse |
| `models/` vakası | MEMORY: kapandı (b9d4fb967) | **Kapalı** — `/models/` ankrajlı (satır 247), 4 yol `NOT-IGNORED` | ✅ UYUMLU | `git check-ignore -v` |

### 2.2 Ankrajsız `.gitignore` deseninin **hâlâ açık** canlı zararı

`models/` düzeltildi, ama aynı sınıf hata başka satırlarda sürüyor:

```
.gitignore:266:performance/    backend/tests/performance/test_elk_performance.py
```

| | |
|---|---|
| Diskte | 5 `.py` dosyası |
| Takipli | 2 (`locustfile.py`, `test_video_api_performance.py`) |
| **Taze klonda kayıp** | `__init__.py`, `test_chromadb_latency.py`, `test_elk_performance.py` |

Diğer riskli ankrajsız desenler: `cache/` (198), `agent/` (221), `archive/` (223),
`files/` (275), `logs/` (64), `build/` (72), `dist/` (72).
Ayrıca şaşırtıcı satırlar: `129: nul`, `213: c:Usershusey*/`, `334: d-`,
`226/227: veriseti/` + `!veriseti/` (aynı dosyada karşıt çift).

### 2.3 Kayıtlı ama gizlenmiş router

```
.gitignore:333            -> backend/api/litellm_chat.py  (AÇIKÇA ignore)
git ls-files              -> 0  (takipsiz)
ls -l                     -> 0 BAYT (boş)
backend/routers/loader.py:101 -> "api.litellm_chat": ("ai", "api.litellm_chat")   ← KAYITLI
```

Takipli kod, takipsiz + boş bir modüle referans veriyor. Toplam **259** ignore edilmiş
`.py/.ts/.tsx` kaynak dosyası var (bağımlılık/cache dizinleri hariç).

### 2.4 Alet tuzağı (raporlanmalı)

`.git/packed-refs` aynı dal için **bayat** bir hash tutuyor
(`e253266701cdf508a46c5b0ea0968a13c01b1c6e`). Loose ref önceliği olduğu için zararsız,
ama `packed-refs`'i doğrudan okuyan bir alet yanlış hash üretir.

---

## 3. Boyut: Veritabanı

### 3.1 Bağlantı kimliği (ön-şart, kanıtlandı)

```
SELECT version(), current_database(), inet_server_port();
 PostgreSQL 18.1 on x86_64-windows, compiled by msvc-19.44.35219, 64-bit | kiro2 | 5434

docker exec kiro2-backend -> DATABASE_URL = postgresql+asyncpg://kiro2_app:***@host.docker.internal:5434/kiro2
pg_stat_activity          -> ('kiro2','kiro2_app','127.0.0.1/32','turkiye_sinav_platform', 5 bağlantı)
```

Yani ölçülen sunucu, **backend'in kullandığı sunucunun ta kendisi.**
`x86_64-windows / msvc` = native derleme, docker pg15 DEĞİL.

### 3.2 Ölçümler

| Konu | İddia | Ölçülen | Durum |
|---|---|---|---|
| PostgreSQL sürümü | CLAUDE.md Tech Stack: **15.x** / aynı dosya Current Status: 18.1 | **18.1** | ❌ Dosya kendi içinde çelişiyor |
| `kiro2_postgres` konteyneri | CLAUDE.md Hard Rule: "var ama kullanılmıyor" | **HİÇ YOK** (`docker inspect` → no such object; hiçbir compose dosyası tanımlamıyor) | ❌ BAYAT |
| `kiro2_db` veritabanı | CLAUDE.md | Bu sunucuda **yok** (`psql -l`: kiro2, postgres, template0/1) | ❌ BAYAT |
| public tablo | MEMORY/audit: 178 (Haz) / 131 (27 Tem) | **209 BASE TABLE** + 7 VIEW + 2 MATVIEW = 218 nesne | ❌ İkisi de bayat |
| `question_bank` toplam | CLAUDE.md: **77.336 "in production"** ve tabloda **192K** | **187.835** | ❌ 2,4x / +2,2% |
| `question_bank` aktif | — | **110.858** (%59,0); pasif 76.977 | ✅ |
| MEMORY question_bank | MEMORY: ~187.835 | **187.835** | ✅ **UYUMLU** |
| `questions` legacy | CLAUDE.md mimari tablo: 36.381 (NOT BOŞ) / verification.md + testing.md: **"BOŞ legacy"** | **36.381** | ❌ İki kural dosyası YANLIŞ |
| `v_safe_for_beta` | MEMORY: ~25.152 (3 Tem) | **25.127** (mv ile senkron, ispopulated=True) | ⚠️ −25 (%0,1) |
| `v_safe_for_beta_unfiltered` | — | 71.645 | ✅ |
| `users` | MEMORY: 77 | **77** (STUDENT 73, PARENT 2, TEACHER 1, ADMIN 1) | ✅ UYUMLU |
| `question_image_url` | CLAUDE.md: **58.523 / 77.336 = %75,7** | **181.652 / 187.835 = %96,71**; aktifte 110.606/110.858 = **%99,77** | ❌ Pay, payda, oran — üçü de geçersiz |
| DB boyutu | — | 2.530 MB; `question_bank` tek başına **2.210 MB (%87)** | ✅ |
| `pg_stat_user_tables` | — | **GEÇERSİZ** — `question_bank` için `n_live_tup`=0, `last_analyze`=NULL | ⚠️ ANALYZE hiç koşmamış |

### 3.3 Kalite × `is_active` dağılımı (tam tablo)

| quality_review_status | is_active | count |
|---|---|---|
| rejected | f | 56.690 |
| unverified | t | 38.880 |
| pending | t | 36.799 |
| auto_judged_high | t | 34.982 |
| legacy_v3_unaudited | f | 20.231 |
| bronze_clean | t | 197 |
| pending | f | 44 |
| auto_judged_high | f | 11 |
| unverified | f | 1 |
| **TOPLAM** | | **187.835** |

**`rejected`'ın TAMAMI `is_active=false` — servis sızıntısı YOK** (testing.md Ders #31'in
kapatıldığı doğrulandı). Aktif + kabul-edilmiş-statü (`auto_judged_high`) = **34.982**.

### 3.4 "77.336" sayısının gerçek kaynağı — çözüldü

```
python satır sayacı (wc DEĞİL): d-dataset/eslesmis_sorucevap.jsonl = 77336 satır
son satır newline ile bitiyor  = True   (yarım-satır artefaktı yok)
dosya boyutu = 116.742.178 bayt ; mtime = 2026-03-04 20:28:57
jsonl anahtarları: [ai_count, ai_sources, answer, answer_page, ..., text, v2_2_tier]
                   -> hiçbir image/url alanı YOK
```

**77.336, 4 Mart 2026 tarihli donmuş bir DOSYANIN satır sayısıdır.** CLAUDE.md bunu
**5 ayrı yerde** (satır 272, 273, 299, 308, 683) "CURRENT PRODUCTION" diye raporluyor.
DB'de bu sayıya karşılık gelen hiçbir katman yok:

| Katman | Sayı |
|---|---|
| question_bank toplam | 187.835 |
| aktif | 110.858 |
| aktif + kabul edilmiş statü | 34.982 |
| öğrenciye açılan kapı (`mv_safe_for_beta`) | **25.127** |

### 3.5 RLS — çok katmanlı ölçüm

| Ölçüm | Sonuç |
|---|---|
| RLS açık tablo | **79** |
| FORCE RLS | **79** |
| Politika sayısı | **79** (tablo başına 1, adı `tenant_isolation`) |
| Toplam public tablo | 209 → **korunan yüzey %38** |
| `kiro2_app` rolü | `rolsuper=f`, `rolbypassrls=f` (RLS gerçekten uygulanıyor) |

Politika ifadesi (79/79 aynı):

```sql
((current_setting('app.current_org_id', true) IS NULL)
 OR (current_setting('app.current_org_id', true) = '')
 OR ((organization_id)::text = current_setting('app.current_org_id', true)))
```

**Atlatma denemesi (gerçek RLS'li tablolarda, kontrol kollu):**

| Kol | refresh_tokens | chat_sessions | image_uploads |
|---|---|---|---|
| [C] superuser `postgres` (taban çizgisi) | 5.558 | 10.096 | 70.000 |
| [A] `kiro2_app`, GUC **yok** | **5.558** | **10.096** | **70.000** |
| [B] `kiro2_app`, eşleşmeyen GUC | **0** | **0** | **0** |

[B] kolunun 0 vermesi mekanizmanın çalıştığını kanıtlar. Sonuç: **RLS mekanizması sağlam,
politika kasıtlı olarak "GUC set edilmemişse hepsini geçir" şeklinde açık.** İzolasyon
tamamen uygulamanın her istekte GUC set etmesine bağlı.

**MEMORY'nin kanıtı GEÇERSİZ ALET:** `users` tablosunda `relrowsecurity=f` ve **0 politika**
var — `users` 79'un içinde değil. "SET ROLE + GUC yok → users 77/77" testi hiçbir politikayı
sınamıyor; [B] kolunda GUC yanlış değere set edildiğinde bile `users` 77 dönüyor.
**Sonuç doğruydu, gerekçe yanlıştı.** `question_bank` ve `student_answers`'ta da RLS kapalı.

### 3.6 Gerçek öğrenci trafiği (platform fiilen kullanılmıyor)

| Tablo | Satır |
|---|---|
| kiro2_learning_events | 334 |
| daily_plans | 216 |
| exam_sessions | 105 |
| coaching_events | 100 |
| **student_answers** | **53** |
| kiro2_cat_sessions | 8 |
| topic_progress | 8 |
| weekly_progress | 2 |
| learning_progress_daily | 1 |
| fsrs_study_sessions / sessions / study_sessions | 0 / 0 / 0 |

Gerçek tablo adı `student_answers` (`user_answers` YOK).

---

## 4. Boyut: Servisler

### 4.1 Konteyner envanteri (tam liste, kesilmemiş)

| Konteyner | Durum | Port | RestartCount |
|---|---|---|---|
| kiro2-backend | Up 13h (healthy) | 0.0.0.0:8000 | 0 |
| kiro2-frontend | Up 13h (healthy) | 0.0.0.0:3000 | 0 |
| kiro2-redis | Up 13h (healthy) | 0.0.0.0:6379 | 0 |
| kiro2-celery-worker | Up 13h (healthy) | 8000/tcp | 0 |
| kiro2-celery-beat | Up 13h (healthy) | 8000/tcp | 0 |
| kiro2-ollama | Up 13h (healthy) | 0.0.0.0:11434 | 0 |
| turkiye_sinav_elasticsearch | Up 13h | 0.0.0.0:9200/9300 | 0 |
| openwebui-litellm-prometheus-1 | Up 13h | 9090/tcp | — |
| openwebui-litellm-redis-1 | Up 13h (healthy) | 6379, 8001 | — |
| *memgraph_nexus* | Exited (255) 3 gün | — | — |
| *qdrant_nexus* | Exited (255) 3 gün | — | — |
| *turkiye_sinav_postgres_dev* | Exited (0) **3 hafta** | postgres:15-alpine | — |

Hepsi ~01:48 UTC'de birlikte kalkmış, **crash-loop YOK**.

### 4.2 Ölçümler

| Konu | İddia | Ölçülen | Durum |
|---|---|---|---|
| Health check gecikmesi | CLAUDE.md: **~9 s** | medyan **20,1 ms** (min 7,9 / max 289,7 soğuk) | ❌ ~450x yanlış |
| Health bileşenleri | — | 5/5 healthy; ES `degraded/yellow` ama `healthy=true` | ✅ |
| Health uç yolu | verification.md preflight: `/api/v1/health` | **404.** Çalışan: `/health`, `/health/ready`, `/health/live`, `/api/v2/health` = 200 | ❌ Kural dosyasındaki komut bugün çalışmaz |
| Frontend :3000 | CLAUDE.md: nginx 3000 | **200** (LISTENING pid 29280) | ✅ |
| Vite :3001 | CLAUDE.md: dev port 3001 | **Bağlantı reddedildi**, netstat'ta yok → dev sunucu koşmuyor | ✅ (beklenen) |
| `redis-cli ping` | CLAUDE.md preflight | Host'ta **kurulu değil**. Ham TCP RESP → `+PONG`, redis 7.4.5 | ❌ Alet yokluğu ≠ servis yokluğu |
| ES doküman | MEMORY (28 Tem): 64.270 | **64.270** — **hiç değişmemiş** | ⚠️ #433 hâlâ açık |
| ES kümesi | — | yellow, 1 node, 6 aktif shard, **4 unassigned**, %60 | ✅ (tek-node beklenen) |
| OpenAPI operasyon | CLAUDE.md: **1.163** | **1.226** (1.147 yol) | ❌ +63 |
| OpenAPI schema | CLAUDE.md: **770** | **799** | ❌ +29 |

### 4.3 Endpoint muhasebesi — tam kapanış

İki bağımsız alet (HTTP `urllib` + ağsız `app.openapi()`) aynı: **1.226 / 1.147 / 799**.
Üçüncü alet (süreç-içi rota ağacı yürüyüşü) 1.246 ham çift verdi ve fark **tamamen** açıklandı:

```
1.246 (ham leaf APIRoute çifti)
 −10  (çift kayıt: study_rooms_stub gerçek /health ve 6 study-rooms rotasını gölgeliyor)
= 1.236 (benzersiz kayıtlı operasyon)
 −10  (include_in_schema=False — HEPSİ /api/v1/auth/*)
= 1.226 (servis edilen spec)   ✅ BİREBİR
```

**HTTP metod kırılımı:**

| Metod | CLAUDE.md | Canlı spec | Kayıtlı (süreç-içi) | HEAD deposu (AST) |
|---|---|---|---|---|
| GET | 619 | **647** | 653 | 677 |
| POST | 456 | **484** | 496 | 514 |
| PUT | 35 | **35** | 36 | 38 |
| DELETE | 43 | **48** | 49 | 49 |
| PATCH | 10 | **11** | 11 | 11 |
| OPTIONS | — | 1 | 1 | 1 |
| **Toplam** | **1.163** | **1.226** | **1.236** | **1.290** |

CLAUDE.md'nin 5 rakamı kendi içinde tutarlı (619+456+35+43+10=1.163) → uydurma değil,
**dondurulmuş eski bir ölçüm.** Tutan tek metod PUT (35) ve o da tesadüfi (HEAD'de 38).

**OpenAPI'de gizli 10 auth ucu** (canlı ve çağrılabilir, `/docs`'ta görünmez):
`POST /api/v1/auth/{register, login, logout, validate, change-password, forgot-password,
reset-password, verify-reset-code}`, `GET /api/v1/auth/me`, `PUT /api/v1/auth/profile`.

### 4.4 Konteyner BAYAT (kritik)

```
konteyner Created         : 2026-07-30T01:48:07Z   (image 01:42:58Z)
backend/api son commit    : c92ca057b  2026-07-30 17:47:35 +0300
HEAD                      : 889c71a3a  2026-07-30 17:49:28 +0300
loader.py md5 (konteyner) : 127db67adeeca368a5fa82cbce4f1c6a  (16.273 B)
loader.py md5 (host)      : 6970140b63cf0a69e0f14eaf6cef5985  (16.736 B)
docker inspect Mounts     : vector_db, static/crops(ro), logs   -> /app KODU BIND-MOUNT DEĞİL
```

Yani **canlı 1.226 rakamı doğru ama güncel değil.** Bugünün ~16 saatlik işi dağıtılmamış.

### 4.5 Celery — sessiz, süregelen kusur

```
[worker] Task tasks.social_tasks.expire_duel_voting[...] received
[worker] ERROR/ForkPoolWorker-8: Database session error: Event loop is closed
[worker] retry: Retry in 60s: RuntimeError('Event loop is closed')
[worker] (+60s) duel_voting_expiry: 0 duels expired  -> succeeded in 0.157s
```

Son 500 log satırında **13 benzersiz olay**, 08:48 → 14:48 arası **her 30 dakikada bir**,
kesintisiz. Görev sonuçlanıyor ama her koşumda 1 başarısız deneme + 60 s gecikme üretiyor.
Bu, kapatılan #430'dan **ayrı** bir kusur. **Kök neden ÖLÇÜLMEDİ** (kaldırma deneyi yapılmadı).

---

## 5. Boyut: Testler

### 5.1 Ölçümler

| Konu | İddia | Ölçülen | Durum |
|---|---|---|---|
| Backend toplanan test | CLAUDE.md: ~1.223 + 169 + 1 = **1.393** | **16.931** (+18 collect-anı skip) | ❌ **12,2x** |
| Toplama hatası | — | **0**, pytest exit 0 | ✅ |
| Test dosyası (backend) | — | 615 takipli; 17 Mar'dan beri **+173** yeni dosya | ✅ |
| Modül-düzeyi skip | — | **136 / 615 = %22,1** | ⚠️ |
| Garantili hiç koşmayan | — | **2.327 test** (413 koşulsuz skip + 1.914 `skipif(True)`) = **%13,7** | ⚠️ |
| Golden Flow test sayısı | rules: **166** / pytest.ini: "8 critical user journeys" | **178** | ❌ İkisi de bayat |
| Golden Flow sonucu | rules: **164 PASS / 0 FAIL / 2 SKIP** | **30 PASS / 148 SKIP / 0 FAIL** | ❌ **ÇÜRÜTÜLDÜ** |
| Orchestrator | CLAUDE.md: **71 passed** | **85 passed / 0 failed** (2,06 s) | ❌ Sayı bayat, yön iyi |
| tests/unit/test_hooks | — | **185 passed / 0 failed** | ✅ |
| tests/unit | CLAUDE.md (tüm backend): **1 fail** | **27 FAILED** + tekrarlanabilir kilitlenme | ❌ |
| Frontend test dosyası | CLAUDE.md: **86** | **196** (150 test.tsx + 33 test.ts + 13 spec.ts) | ❌ 2,3x |
| Frontend koşabilir test | — | **2.705 test / 175 dosya** (~7 dk) | ✅ ÖLÇÜLDÜ |
| Frontend koşamayan | — | **17 / 196** (13 Playwright + 4 eksik modül) | ❌ |
| Coverage | CLAUDE.md: **~%53** | **%39,74** (dal dahil) / **%43,67** (deyim) — 27 May artefaktı | ❌ |
| `assert True` | testing.md: YASAK | grep 54 → **AST ile gerçek 10** (2 dosya) | ⚠️ grep %540 şişirdi |

### 5.2 Golden Flow — "merge kapısı" fiilen çalışmıyor

Doküman `164 PASS / 0 FAIL / 2 SKIP` diyor. **Gerçekten koşuldu:**

```
collected 178 items
================ 30 passed, 148 skipped, 2 warnings in 21.57s =================

SKIP nedeni kırılımı (-rs):
   147  login 429 rate-limit ('Çok fazla istek. 60 saniye sonra tekrar deneyin.')
     1  data/seed dependent
```

3 ayrı koşumda, 70 s ve 150 s soğutma sonrasında bile **aynı**: 30 passed / 148 skipped.

**Kök neden ölçüldü:** `_login()` yardımcısı 200 dışı her yanıtı `pytest.skip`'e çeviriyor.
178 test peş peşe login denediği için platformun **5/dk login rate-limit'i** devreye giriyor
ve 147 test **sessizce atlanıyor.** Atlanan bir test **asla FAIL üretmez.**

Ek olarak:
- `golden-flows.yml` yalnız `main/master/develop` push + PR'da tetikleniyor →
  aktif dal `feature/self-evolution-optimization`'da **hiç koşmuyor**
- CI komutu `-x` (ilk hatada dur) → kırmızı koşu yalnızca İLK hatayı gösterir
- Paket yazma yüzeyi: 69 GET, **131 POST**, 2 PUT, 1 PATCH, 1 DELETE

> **Not:** Rate-limit ayarı CI'da farklı olabilir; bu ölçüm bu makineye aittir.

### 5.3 `tests/unit` — 27 başarısızlık izole edildi + kilitlenme çivilendi

İlk ölçüm "27 F, sonra kilitlenme; ama arka planda vitest CPU yiyordu — yük mü deadlock mu
ayrıştırılamadı" demişti. **İzole edildi:**

```
# TEK DOSYA, tek süreç, %31 CPU (yüksüz makine):
pytest tests/unit/test_analytics_api.py -q --timeout=30
-> 27 failed, 112 passed, 22 warnings in 14.17s
-> kök neden: sqlite3.OperationalError: no such table: learning_path_student_profiles

# Kontrol kolu: bu dosyayı ÇIKAR
pytest tests/unit --ignore=tests/unit/test_analytics_api.py
-> total F chars: 0        (27'nin TAMAMI tek dosyadan)

# Kilitlenme yük artefaktı DEĞİL:
pytest tests/unit/test_api_batch2.py -q --timeout=30
-> 288/403'te kilitlendi; yığın izi:
   _pytest/fixtures.py:939 _teardown_yield_fixture
   -> pytest_asyncio/plugin.py:817 _scoped_runner
   -> asyncio/runners.py:205 _cancel_all_tasks
   -> run_until_complete -> select.select
```

`.pytest_cache/v/cache/lastfailed`: **5.711** başarısız node id (kümülatif, 300'ü
`tests/unit` altında, 15 dosya) — CLAUDE.md'nin "1 fail" iddiasıyla bağdaşmıyor.

### 5.4 Frontend — 17 dosya hiçbir zaman koşamaz

**13 Playwright spec'i vitest include desenine takılıyor:**

```
vitest.config.ts:13 include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}']
vitest.config.ts:14 exclude: ['node_modules','dist','.idea','.git','.cache']   <- e2e YOK
playwright.config.ts:8  testDir: './src/test/e2e'
13/13 dosya '@playwright/test' import ediyor

npx vitest run src/test/e2e/mvp-smoke.spec.ts
-> FAIL ; Tests: no tests ; Error: Playwright Test did not expect test.use() to be called here.
```

`npm test` = `vitest --run` → bu 13 dosyada **kesin kırmızı**.

**4 test var olmayan modülü import ediyor** (dosyalar git'te takipli, kaynak modüller ne
diskte ne git index'inde):

| Test dosyası | Aranan modül | Disk | Kardeş |
|---|---|---|---|
| `src/hooks/__tests__/useOfflineMode.test.ts` | `../useOfflineMode` | YOK | — |
| `src/services/__tests__/modernApiClient.test.ts` | `../modernApiClient` | YOK | — |
| `src/services/__tests__/VideoErrorHandler.test.ts` | `../VideoErrorHandler` | YOK | sadece `.README.md` |
| `src/services/__tests__/VideoLoadingComponent.test.tsx` | `../VideoErrorHandler` | YOK | sadece `.README.md` |

### 5.5 CI durumu

11 workflow + `desktop.ini`. Tetikleyiciler:

| Workflow | Tetikleyici | Aktif dalda koşar mı? |
|---|---|---|
| ci.yml | push [main,master,develop] + PR + dispatch | ❌ |
| golden-flows.yml | push [main,master,develop] + PR + dispatch | ❌ |
| quality-gate.yml | PR [main,master] + dispatch | ❌ |
| claude-ci.yml, quality-gates.yml | **yalnız** workflow_dispatch | ❌ |
| security.yml | PR [master] + haftalık schedule | ❌ |
| deploy.yml, release.yml | tag `v*.*.*` | ❌ |
| health-checks.yml | deployment_status | ❌ |

CI backend test adımı:

```yaml
pytest tests/ --tb=short --cov=. --cov-report=term-missing \
  --cov-fail-under=60 --junit-xml=pytest-report.xml -v -x
```

Yerelde `tests/unit`'in ilk %12'sinde 27 FAILED olduğuna göre bu adım `-x` ile **erken düşer.**
`.coveragerc` `fail_under = 60.0`, mevcut kayıt %39,74 → depo **kendi eşiğini de geçmiyor.**

`quality-gate.yml` `on:` bloğunda `workflow_dispatch:` **iki kez** tanımlı (satır 17–18).
PyYAML tolere ediyor; **GitHub Actions ayrıştırıcısının davranışı ÖLÇÜLMEDİ** (`gh` kurulu değil).

---

## 6. Boyut: Kod Envanteri

### 6.1 Ölçümler

| Konu | İddia | Ölçülen | Durum |
|---|---|---|---|
| Backend `.py` (takipli) | Görev metni `backend/**/*.py` önerdi → 2.330 | **2.415** (3 bağımsız alet) | ❌ Önerilen komut 85 dosya atlıyor |
| Frontend `src` ts+tsx | Görev metni → 878 | **887** (663 tsx + 224 ts) | ❌ 9 dosya atlanıyor (App.tsx, main.tsx, index.tsx, api.ts dahil) |
| ROUTER_MAPPING | — | **152** (AST 152 = runtime 152), `DISABLED_ROUTERS`=0 | ✅ |
| `APIRouter()` içeren dosya | — | 154 | ✅ |
| Kayıtsız router | MEMORY: 2 router sessizce yüklenmiyordu (kapandı) | **3 kayıtsız + 1 hayalet** | ⚠️ Yeni |
| TODO / FIXME / HACK | — | **39 TODO**, 0 FIXME, 0 HACK, 7 XXX (hepsi yanlış-pozitif) | ✅ |
| mock bayrağı | Görev #311: **38 mock impl** | **20 bayrak** (19 mock, 1 gerçek); **6'sı ölü** | ❌ |
| `NotImplementedError` | — | 29 / 12 dosya; **15'i bekçinin kendi tespit kalıbı** | ⚠️ |
| `_deprecated` dizin | — | Kod içeren **3** dizin, **9** takipli dosya | ✅ |
| `_deprecated` importer | Görev #369: "5 importer refactor gerek" | **8 dosya / 17 import**, bunun **5'i üretim** | ✅ **UYUMLU** |
| Commit edilmiş `.bak` | — | **24** dosya `frontend/src/.migration-backup/` (2025-11-18) | ⚠️ |
| Çift path+method | — | **10** (`study_rooms_stub` `/health`'i ve 6 study-rooms ucunu gölgeliyor) | ⚠️ |

### 6.2 Yetim router — canlı sistemde doğrulandı

```
curl /health                     -> 200      (backend canlı)
curl /api/learning-path          -> 404
curl /api/v1/cat  (kontrol kolu) -> 4 canlı rota   (probe çalışıyor)

/api/learning-path   live_routes = 0   <- api/learning_path.py, 1.822 satır, 18 endpoint, HEPSİ ÖLÜ
/api/v1/sentry-demo  live_routes = 0   <- loader.py:137 bilinçli yorum satırı
/api/v1/tracing-demo live_routes = 0   <- loader.py:138 bilinçli yorum satırı
```

**Hayalet kayıt:** `api.litellm_chat` ROUTER_MAPPING satır 101'de kayıtlı, dosya **0 bayt**,
`hasattr(module,'router')` = **False** → `loader._load_router` her açılışta
`logger.warning("No router found")` + `failed_count++` üretiyor.

### 6.3 Mock bayrak altyapısı — 6 bayrak ÖLÜ

```
mock_endpoint_flags.json: 21 anahtar = 20 bayrak + 1 '_comment'
TRUE (gerçek impl): 1   -> analytics.d7_retention
FALSE (mock)      : 19
```

Cross-reference (`is_real_impl(...)` çağrı yerleri ↔ tanımlı bayraklar):

| | |
|---|---|
| Üretim çağrı yeri | 18 |
| Kodda kullanılan benzersiz bayrak | **14** |
| **Tanımlı ama HİÇ kullanılmayan** | **6** — `analytics.{admin_dashboard, class, student}`, `content_management.{questions_create, questions_detail, search}` |
| Kullanılan ama tanımsız | 0 |

Bu 6 bayrak **ölü**: operatör `true`'ya çevirse bile hiçbir şey değişmez.

AST ile mock-yardımcı fonksiyon sayımı: `advanced_reports.py` 6, `analytics.py` 9,
`content_management.py` **0** (ne `is_real_impl` çağrısı ne `mock` isimli fonksiyon).
Görev #311'in "content_mgmt 9" kalemi bu dosyada **karşılıksız**; "38 mock impl" rakamı
hiçbir birimde yeniden üretilemedi. Kesin olan: **bayrak altyapısı 38'in en fazla 14'ünü
kontrol ediyor.**

### 6.4 Gerçek ürün-yüzeyi stub'ları

`NotImplementedError`'ların 15'i reward-hacking bekçisinin **kendi tespit kalıpları**
(stub değil). Gerçek stub'lar:

| Dosya | Adet | Not |
|---|---|---|
| `services/veli_service.py` | 3 | Kodda: *"DISABLED until real database implementation"* + *"ETHICAL VIOLATION and LEGAL LIABILITY"* — sahte veli performans verisi kapatılmış |
| `repositories/base.py` | 1 | |
| `services/llm/gemini_provider.py` | 2 | |
| `services/llm/qwen_provider.py` | 1 | |
| `core/rag_service.py` | 1 | |
| `core/error_monitoring.py` | 1 | |

### 6.5 Diğer artıklar

- **24 `.bak` dosyası git'e commit edilmiş** — `frontend/src/.migration-backup/`, hepsi
  2025-11-18 tarihli tek bir auth migration'ından. İçinde `ProtectedRoute.tsx`,
  `AuthProvider.tsx`, `useAuth.ts/.tsx` (×3), `LoginPage.tsx` gibi **auth/RBAC kritik**
  dosyaların eski kopyaları var.
- **Bozuk isimli dizin:** `backend/C:Usershuseykiro2backendtestsunit/` (takipsiz, içinde
  yalnız `desktop.ini`) — bir script'in Windows yolunu düzleştirip klasör açmasının izi.
- `backend/fix_validators.py` (#458b) hâlâ mevcut ve takipli; kod importu 0 ama
  `backend/pyproject.toml:216` bir `per-file-ignores` girdisi tutuyor.

---

## 7. İddia vs Gerçeklik — Konsolide Fark Tablosu

### 7.1 Bayat sayılar (doküman geride)

| # | Kaynak | İddia | Ölçülen | Sapma |
|---|---|---|---|---|
| 1 | CLAUDE.md ×5 yer | 77.336 soru "in production" | 187.835 (DB) / 77.336 = 4 Mart tarihli **dosya** satırı | **2,4x + kategori hatası** |
| 2 | CLAUDE.md mimari tablo | question_bank = 192K | 187.835 | −2,2% |
| 3 | CLAUDE.md | question_image_url 58.523/77.336 (%75,7) | 181.652/187.835 (%96,71) | pay+payda+oran geçersiz |
| 4 | CLAUDE.md | 1.163 endpoint | 1.226 canlı / 1.236 kayıtlı / 1.290 kaynak | +63 / +73 / +127 |
| 5 | CLAUDE.md | 770 Pydantic schema | 799 | +29 |
| 6 | CLAUDE.md Tech Stack | PostgreSQL 15.x | 18.1 | Dosya kendi içinde çelişiyor |
| 7 | CLAUDE.md | Health check ~9 s | 20,1 ms (medyan) | ~450x |
| 8 | CLAUDE.md | backend testleri ~1.393 | 16.931 toplandı | **12,2x** |
| 9 | CLAUDE.md | backend "1 fail" | tests/unit'te 27 fail + kilitlenme | — |
| 10 | CLAUDE.md | coverage ~%53 | %39,74 / %43,67 (27 May artefaktı) | −9 ila −13 puan |
| 11 | CLAUDE.md | frontend 86 test dosyası | 196 (iddia tarihinde bile 96'ydı) | 2,3x |
| 12 | CLAUDE.md | orchestrator 71 passed | 85 passed | +14 |
| 13 | CLAUDE.md + README | orchestrator 24 core modül | 35 disk / 31 import'lu / 8 README-Active | 24 hiçbirine uymuyor |
| 14 | CLAUDE.md + README | orchestrator 20 agent | 7 enum + 7 sınıf (`.claude/agents/` 13) | 20 hiçbirine uymuyor |
| 15 | CLAUDE.md | LFS 4 desen, `>50MB` eşikli | 5 desen (`*.onnx` eksik), **eşik yok** | — |
| 16 | rules/golden-flows.md | 166 test → 164 PASS / 2 SKIP | 178 test → **30 PASS / 148 SKIP** | — |
| 17 | MEMORY / CLAUDE.local | `.git` 218 MB | 6,7 GiB | **~31x** |
| 18 | MEMORY / audit | 178 tablo (Haz) / 131 (27 Tem) | 209 base tablo | — |
| 19 | MEMORY | v_safe_for_beta ~25.152 | 25.127 | −25 (%0,1) |
| 20 | MEMORY | "153 router dosyası" (payda) | 167 (163 `__init__` hariç) | pay (2) doğru |
| 21 | pytest.ini:36 | golden_flow = "8 critical user journeys" | 178 test | — |
| 22 | Görev #311 | 38 mock impl | 20 bayrak / 14 kablolu / 13 mock-fonksiyon | — |

### 7.2 Doküman DOĞRU çıkanlar (fantom değil)

| Kaynak | İddia | Ölçülen | |
|---|---|---|---|
| MEMORY | question_bank ~187.835 | 187.835 | ✅ |
| MEMORY | users 77 | 77 | ✅ |
| MEMORY | 79 tabloda FORCE RLS | 79 / 79 / 79 politika | ✅ |
| MEMORY | RLS fiilen kapalı (GUC yoksa hepsi geçer) | Atlatma kanıtlandı (5.558 = taban çizgisi) | ✅ (gerekçe hariç) |
| MEMORY | app `kiro2_app` non-superuser bağlanıyor | `rolsuper=f`, `rolbypassrls=f`, DSN doğrulandı | ✅ |
| MEMORY | `get_current_tenant` 2 router dosyasında | tam 2 (`org_api.py`, `org_billing_api.py`) | ✅ |
| MEMORY | `models/` ankraj vakası kapandı | `/models/` ankrajlı, 4 yol NOT-IGNORED | ✅ |
| CLAUDE.md mimari tablo | `questions` = 36.381 legacy (NOT BOŞ) | 36.381 | ✅ |
| CLAUDE.md | `eslesmis_sorucevap.jsonl` = 77.336 | 77.336 (tam) | ✅ |
| CLAUDE.md | Docker stack ready | 6 konteyner healthy, restart 0 | ✅ |
| CLAUDE.md ×2 | orchestrator v2.5.0 | `__version__ = "2.5.0"` | ✅ |
| **CLAUDE.md + README** | **orchestrator 45 policy** | **runtime 45 (P1..P45)** | ✅ **ilk ölçüm çürütüldü** |
| Görev #369 | `_deprecated` purge: 5 importer bloke | tam 5 üretim importer'ı | ✅ |
| Görev #432 | ES cevap sızıntısı API'de kapatıldı | `STUDENT_SAFE_QUESTION_FIELDS` canlıda (4 geçiş) | ✅ |
| Görev #445 | rol fix canlıda | `_map_registration_role` konteynerde mevcut | ✅ |

### 7.3 Depo İÇİ çelişkiler (aynı depo, iki farklı gerçek)

| Konu | Kaynak A | Kaynak B | Gerçek |
|---|---|---|---|
| `questions` tablosu | CLAUDE.md mimari tablo: **36.381 (NOT BOŞ)** | `verification.md` + `testing.md`: **"BOŞ legacy"** | **36.381** → A doğru |
| PostgreSQL sürümü | CLAUDE.md Current Status: **18.1** | CLAUDE.md Tech Stack: **15.x** | **18.1** → aynı dosya çelişiyor |
| Health uç yolu | `verification.md` preflight: `/api/v1/health` | canlı: `/health` | `/api/v1/health` = **404** |
| Redis kontrolü | CLAUDE.md preflight: `redis-cli ping` | host'ta `redis-cli` kurulu değil | `docker exec kiro2-redis redis-cli ping` |
| PostgreSQL konteyneri | `verification.md:99` + 14 dosya: `kiro2_postgres` | `docker inspect` → no such object | Konteyner **hiç yok** |
| CLAUDE.md tarih beyanı | "Last Updated: April 27, 2026" | son gerçek commit `31b1f617d` **2026-05-23** | **68 gün** dokunulmamış |
| CLAUDE.md başlıkları | "Current Status (March 2026)" | "Current Status (as of 17 Mar 2026)" | 3 farklı tarih beyanı |

**Yukarıdaki 22 sapmanın ortak kök nedeni budur:** CLAUDE.md 23 Mayıs'tan beri
dokunulmamış; sistem 68 gün ilerlemiş.

---

## 8. Boyut: Açık Görevler (Backlog) — Kanıtlı Durum

| # | Görev | Durum | Kanıt |
|---|---|---|---|
| **#433** | ES index'ini `v_safe_for_beta`'dan yeniden kur | 🔴 **AÇIK** | ES 64.270 vs v_safe 25.127 (2,56x). 300-doküman örneklem: yalnız **21 (%7,0)** v_safe'te, 181 (%60,3) `is_active`. Kontrol kolu 300/300 → ölçüm geçerli. Mapping'de `correct_answer` + `explanation` VAR, `quality_review_status` **YOK** → ES kalite filtresi yapamaz. API katmanı beyaz listesi canlıda (#432 gerçekten kapalı), **index-seviyesi bypass sürüyor** |
| **#441** | SMTP / şifre kurtarma e-postası | 🔴 **AÇIK** | 6/6 SMTP env değişkeni **UNSET**. `core/email_util.py:38` guard'ı `return False` → `send_email` her çağrıda e-postayı atlıyor |
| **#447** | `GET /api/v1/me` persona ucu | 🟡 **KOD BİTTİ, DAĞITIM BEKLİYOR** | Canlı **404** (kontrol: `/api/v1/auth/me`→401, `/api/v1/billing/me`→401, `/zzz`→404). Kod HEAD'in atası (`8d9f6738a` 17:19:35): `api/me.py` + `persona_service.py` + `loader.py:39` + test. İmaj 01:42:58Z. `/app` **bind-mount değil** |
| **#444** | Öğretmen sınıfına öğrenci ekleme/**çıkarma** | 🟡 **KOD BİTTİ, DAĞITIM BEKLİYOR** | Frontend kodu tam (`ogrenciEkle:86`, `ogrenciCikar:114`, DELETE:128, `PersonRemove:442`, **0 mock/fallback**). Host backend yanıtında `classroom_id` VAR (md5 `78172dd…`), konteynerde **YOK** (md5 `1842dad…`, Jul 29 15:17). Dağıtılmış **82 chunk'ın tamamı** HTTP ile çekildi (3.451.477 bayt, 0 hata) → `ogrenciCikar`/`classroom_id`/`student_user_id` **0 isabet**; kontrol iğnesi `teacher/classes` 4 chunk'ta bulundu |
| **#270** | GitHub Actions durumu | 🔴 **AÇIK — KRİTİK** | Son **100 koşunun 100'ü FAILURE** (8.447 toplam). quality-gate 36, golden-flows 36, health-checks 28. En son 2026-07-30T14:49:39Z failure. **Kök neden ÖLÇÜLMEDİ** (job logları çekilmedi) |
| **#390** | `gh` CLI + Dependabot triyajı | 🔴 **AÇIK** | `gh` **kurulu değil** (`command not found`, PATH'te yok). **20 açık PR'ın 20'si de Dependabot**. `dependabot.yml` 4 ekosistemle aktif (pip, docker, github-actions, npm/frontend) |
| ~~**#458b**~~ | `fix_validators.py` sil | ✅ **KAPANDI** (31 Tem, `a7e3971f9`) | Silmeden ÖNCE işinin uygulanmış olduğu ölçüldü: `sanitize_url`/`sanitize_integer`/`sanitize_float` üçü de `core/input_validation.py` içinde (1/1/1) → harcanmış tek-seferlik script. `pyproject.toml` per-file-ignores girdisi birlikte kaldırıldı. ruff 11.156 → 11.156 (nötr, HEAD~1 ile A/B) |
| ~~**#458a**~~ | e2e testinde çift-kodlanmış Türkçe | ✅ **KAPANDI — DOSYA SİLİNDİ** (31 Tem, `0fe82b2c3`) | 127 satır teyit edildi (bu audit'in sayısıyla birebir). Ama asıl bulgu: dosya `skipif(True)` ile **2026-02-06'dan beri (~6 ay) koşulsuz atlanıyordu** ve skip gerekçesi (**"Multiple PointTransaction classes"**) FANTOM — `class PointTransaction` tek tanım, `configure_mappers()` temiz. Koşmayan dosyada mojibake onarımı = **0 davranış değeri** (#451 dersi) → 1.475 satır silindi. Dosyayı adıyla anan 2 bekçi testi yalnız yorumda anıyor: silme sonrası 6/6 PASS |
| **#458a-2** | `test_turkish_nlp.py` "ikinci mojibake dosyası" | ❌ **YANLIŞ-POZİTİF — DOKUNULMADI** | 2 satır (131, 251) mojibake içeriyor ama bunlar **test edilen GİRDİ**: `test_fix_encoding_issues` / `test_text_normalization_encoding_issues`. Ölçüldü: mevcut fixture `_fix_encoding_issues → fixes=3` (`assert fixes>0` GEÇER); "düzeltilmiş" hâli `fixes=0` (**KIRILIR**). Değişken adı zaten `broken_text`. Mojibake detektörünün desen-eşlemesi kasıtlı fixture'ı kusur sandı |
| **#445** | Geçmiş STUDENT hesap triyajı | 🟢 **SINIRLI, DB'de kanıt YOK** | 77 hesap / 73 STUDENT. Rol fix `25784449d` **2026-07-29 16:22:10**; **73 STUDENT fix'ten ÖNCE**, fix'ten sonra **0**. Beş yapısal sinyalin beşi de sıfır: 27 sınıfın tek sahibi TEACHER; `teacher_{assignments,contents,exam_configs,profiles,pool_profiles}` 0 satır; hiç STUDENT'ta `is_parent=true` yok; `parent_profiles` sahibi PARENT; roster 0 satır. Tek zayıf işaret: `ogrenci_veli_test@kiro2.com` (test fixture adı). Fix **canlıda** |
| **#436** | Faturalama / kullanım kontrolü | ⚫ **ÖLÇÜLEMEZ (operatör gerekir)** | Depo **HÂLÂ PUBLIC** (200, `private=false`, `pushed_at` 2026-07-30T14:49:37Z; kontrol kolu: var olmayan depo → 404). Dört faturalama ucunun **dördü de** kimlik istiyor: OpenAI 401, Anthropic 405, Google 403, GitHub billing 401 |

---

## 9. Çürütülen İlk Ölçümler — "Neredeyse Yanlış Rapor Edecektik"

Bu bölüm bu ölçümün en değerli çıktısıdır. Çapraz doğrulama olmasaydı aşağıdakiler
rapora **bulgu** olarak girecekti.

### 9.1 Çapraz doğrulamada TERSİNE dönenler

| # | İlk ölçüm | Neden yanlıştı | Gerçek |
|---|---|---|---|
| **1** | orchestrator "45 policy" → **26 Policy() / 23 policy_id** → *"doküman yanlış"* | `grep` **yapıcı SİTE'lerini** sayar, üretilen NESNELERİ değil. P1–P20 tek tek, **P21–P45 bir for-döngüsünde** kayıt ediliyor. Ayrıca alan adı `id`, `policy_id` değil | `len(engine.policies)` = **45**, benzersiz 45, P1..P45 kesintisiz → **DOKÜMAN DOĞRU** |
| **2** | `.coverage` sqlite → *"No source for code"* → *"artefakt kullanılamaz, ÖLÇÜLEMEDİ"* | 661 kayıtlı dosyadan **yalnız 1'i** diskte yok; coverage varsayılan olarak tek eksik dosyada tüm raporu iptal ediyor | `-i` bayrağıyla rapor üretildi: **%39,74** |
| **3** | frontend vitest → *"list iki kez tamamlanamadı, ÖLÇÜLEMEDİ"* | Alet arızası değil, **17 bozuk dosya** vardı | 17'si dışlanınca EXIT=0, **2.705 test / 175 dosya** |
| **4** | #445 → *"yanlış rol var mı ÖLÇÜLEMEDİ"* | Rol-fix commit'inin **TARİHİ** ölçülmemişti | 73 STUDENT'ın tamamı fix'ten önce, sonrasında 0 → evren **tam 73**, üst sınır kesin; 5 yapısal sinyal sıfır |
| **5** | Büyük pack *"BUGÜN 03:36'da oluşmuş"* | `mtime` `ctime` sanıldı | Windows `st_ctime` = **2026-07-01 15:10:19**; 30 Tem 03:36 yalnızca dokunulma |
| **6** | LFS `527` vs `528` → fark bulgu sanılabilirdi | Sıfır-baytlık `.jsonl`'de clean filtresi pointer üretmiyor → `lfs ls-files` atlıyor, `check-attr` sayıyor | **Alet artefaktı, bulgu değil** — iki alet de kendi tanımına göre doğru |
| **7** | Golden Flow → *"PASS/FAIL ölçülmedi"* | Salt-okunur kısıt gerekçesiyle koşulmamıştı | Koşuldu: **30 PASS / 148 SKIP** → doküman iddiası (164/2) çürütüldü |

### 9.2 İlk ölçüm sırasında yakalanan alet arızaları (14 adet)

| Alet | Ne dedi | Neden yanlış | Doğrusu |
|---|---|---|---|
| FastAPI rota yürüyüşü | `APIRoute = 1` | FastAPI 0.140 rotaları `_IncludedRouter` tembel proxy'sinde tutuyor; `isinstance` filtresi kör | 1.246 çift → **"router'lar yüklenmiyor" sahte P0'ı önlendi** |
| `grep "assert True"` | 54 vuruş / 19 dosya | Docstring, yorum ve **reward-hacking bekçisinin kendi fixture'ları** | AST ile **10** |
| `grep` basename ile `_deprecated` | *"0 canlı importer"* | Ad çakışması (`fsrs_service` ayrı canlı dosya) | Paket-yolu ile **8 dosya / 17 import** — iddiayı TAM TERSİNE çevirecekti |
| `find -name _deprecated` | 6 dizin | 3'ünde yalnız gitignore'lu `desktop.ini` | Kod içeren **3** dizin |
| `pg_stat_user_tables` | question_bank `n_live_tup = 0` | ANALYZE hiç koşmamış (`last_analyze`=NULL) | Exact `COUNT(*)` = 187.835 |
| MEMORY'nin RLS kontrol kolu | `users` 77/77 → "RLS kapalı" | `users`'ta RLS **hiç açık değil** (0 politika) — test hiçbir politikayı sınamıyor | `refresh_tokens`/`chat_sessions`/`image_uploads` ile ölçüldü |
| `git ls-files "backend/**/*.py"` | 2.330 | git pathspec `**/` **en az bir dizin** şart koşar | **2.415** (85 dosya atlanıyordu) |
| `curl /api/v1/osym-exam/configs` | 404 | Yol yanlış; gerçek uç `/exam-configs` (35 osym yolu mevcut) | **Fantom bulgu önlendi** |
| `redis-cli ping` | `command not found` | Host'ta alet kurulu değil | Ham TCP RESP → `+PONG`, redis 7.4.5 |
| `docker exec ... ls /app/api/me.py` | *"dosya yok"* (ilk deneme) | Git Bash yolu `C:/Program Files/Git/app/...` yaptı | `MSYS_NO_PATHCONV=1` + kontrol kolu (`/app/main.py` var) |
| frontend bundle `/usr/share/nginx/html/assets` | 0 dosya | Yanlış dizin | Gerçek yol `/js`; kontrol iğnesi `useState` 71/85 dosyada |
| `npx vitest list "src/utils/**/*.test.ts"` | 0 satır, EXIT=0 | Positional arg **glob değil alt-dizi** eşleşmesi | `npx vitest list src/utils` → 75 satır |
| bash `/tmp` ↔ python `/tmp` | `FileNotFoundError` | İki ayrı namespace (MSYS `AppData\Local\Temp` vs `C:\tmp`) | Depo-içi mutlak yol / stdin borulama |
| `grep -r` proje kökünde | 120 s timeout | venv/node_modules taraması | `git ls-files` üzerinden tarama |

---

## 10. ÖLÇÜLEMEYENLER (tahminle DOLDURULMADI)

> Bu listedeki hiçbir kalem için "hazır" veya "hazır değil" denemez.

### 10.1 Test ve kalite

1. **Tam backend suite pass/fail** (16.931 test) — `tests/unit` `pytest_asyncio` teardown'ında
   kilitleniyor (izole, yüksüz makinede de tekrarlanıyor). Uçtan uca koşum şu an **mümkün değil**.
2. **Taze coverage yüzdesi** — aynı kilitlenme nedeniyle. Rapor edilen %39,74 **27 Mayıs 2026**
   tarihli artefakttan; hangi test alt kümesiyle üretildiği bilinmiyor.
3. **`tests/unit`'teki 27 FAILED testin ADLARI** — özet satırına ulaşılamadı; sayılar
   ilerleme karakterlerinden türetildi, dosya (`test_analytics_api.py`) ve kök neden
   (`no such table: learning_path_student_profiles`) izole edildi ama isimler yok.
4. **`npm test` tam koşumunun nihai tablosu** — 175 dosyanın koşabilir olduğu ölçüldü;
   179 dosyanın pass/fail sonucu bilinmiyor.
5. **108 `skipif(...)` modülünden hardcoded-`True` olmayan 8'i** — ortama bağlı; garantili-skip
   sayısı (2.327) bu 8'i **içermiyor**, gerçek skip daha yüksek olabilir.
6. **GitHub Actions'ın çift `workflow_dispatch:` anahtarını reddedip reddetmediği** —
   `gh` kurulu değil; PyYAML tolere etti ama GH'in kendi ayrıştırıcısı denenmedi.
7. **CI kırmızısının KÖK NEDENİ** — 100/100 failure ölçüldü, **job logları çekilmedi**.
   Hangi adımın patladığı, yeni regresyon mu uzun süreli durum mu **bilinmiyor**.
   8.447 koşunun tarihsel başarı eğrisi çıkarılmadı.

### 10.2 Veritabanı ve içerik

8. **v_safe_for_beta'daki 25 satırlık sapmanın (25.152→25.127) sebebi** — `question_bank`
   üzerinde `updated_at` bakan **trigger yok** (uygulama-yazımlı), 3 Tem'deki değer yeniden
   inşa edilemez. 3 Tem'den beri 12 satır güncellenmiş, 0 demote.
9. **CLAUDE.md'deki 58.523 rakamının hangi tarihe/snapshot'a ait olduğu** — geriye dönük
   sorgulanamaz. DB'de 181.652, diskte 612.345 crop dosyası, jsonl'de görüntü alanı hiç yok.
10. **jsonl'deki 77.336 satırın kaçının `question_bank`'a girdiği** — join anahtarı belirlenmedi.
11. **38.880 `unverified` + 36.799 `pending` satırın KALİTESİ** — yalnız etiket sayıldı,
    içerik yargılanmadı.
12. **209 tablonun tamamının satır sayısı** — `pg_stat` kısayolu arızalı olduğu için toplu
    tahmin mümkün değildi; 20 tablo tek tek sayıldı.
13. **`exam_sessions`/`student_answers` satırlarının gerçek kullanıcı mı test fixture'ı mı
    olduğu** — `created_at`/`user_id` profillemesi yapılmadı.
14. **`405 source books in production`** — DB'de karşılık gelen kolon/tablo doğrulanmadı.

### 10.3 Servis ve mimari

15. **ES `_source` içinde `correct_answer`'ın gerçek öğrenci token'ıyla uçtan uca dönüp
    dönmediği** — mapping'de var olduğu ve API beyaz listesinin canlıda olduğu ayrı ayrı
    ölçüldü, **uçtan uca canlı doğrulama yapılmadı** (token üretimi gerekirdi).
16. **ES'i `v_safe_for_beta`'dan yeniden kurmanın ETKİSİ** — hangi öğrenci sorgularının
    recall kaybedeceği ölçülmedi.
17. **Celery `Event loop is closed` KÖK NEDENİ** — semptom deseni ölçüldü, **kaldırma deneyi
    yapılmadı**. Sebep İDDİA EDİLMİYOR.
18. **`backend/api/litellm_chat.py`'nin taze klonda router yükleme hatası verip vermediği** —
    `loader.py`'nin eksik modülü try/except ile yutup yutmadığı ölçülmedi.
19. **17 `_deprecated` import'unun kaçının açılışta gerçekten çalıştığı** — modül-düzeyi vs
    fonksiyon-içi (lazy) ayrımı yapılmadı.
20. **Kayıtsız `api/learning_path.py`'nin 18 ucuna frontend'den çağrı yapılıp yapılmadığı** —
    "ölü kod mu kırık özellik mi" ayrımı yapılmadı.
21. **`kiro2-ollama` servis-içi sağlığı ve yüklü modeller** — yalnız docker healthcheck.
22. **Frontend'in servis ettiği build'in hangi commit'ten olduğu** — 82 chunk içerik olarak
    tarandı, commit damgası yok.
23. **PgBouncer** — `docker ps -a`'da yok; host process olarak taranmadı.
24. **Backend imajının HANGİ commit'ten kurulduğu** — yalnız zaman damgası ve dosya
    checksum farkı ölçüldü.

### 10.4 Güvenlik / süreç

25. **#436 faturalama/harcama** — dört sağlayıcının dördü de kimlik istiyor; `gh` kurulu değil.
    **Operatör gerektirir.**
26. **Anahtar canlılığı** — bu oturumda YENİDEN ölçülmedi (önceki #435 ölçümü 14/14 ölü diyor;
    teyit sağlayıcılara istek atacağı için salt-okunur görevde koşulmadı).
27. **Dependabot güvenlik uyarılarının CVE ciddiyeti** — `/security-advisories` ve
    `/dependabot/alerts` kimlik istiyor.
28. **#441 canlı duman testi** — `/auth/forgot-password` **bilerek tetiklenmedi** (Redis'e
    kod yazacaktı). SMTP'nin doğru kimlikle gerçekten e-posta gönderip göndermediği bilinmiyor.
29. **#444/#447 rebuild sonrası sonucu** — yazma/dağıtım işlemi, salt-okunur kapsam dışı.
30. **Backend'in `app.current_org_id` GUC'unu her istekte set edip etmediği (uçtan uca)** —
    DB tarafı ölçüldü, HTTP tarafı ölçülmedi.
31. **73 STUDENT hesabının SEMANTİK doğruluğu** — yapısal sinyaller sıfır, ama kullanıcı
    teması / e-posta alan adı eşleşmesi gerektirir.
32. **6,0 GiB'lik pack'in İÇERİĞİ** (hangi blob'lar şişiriyor) — 98K nesne üzerinde dakikalar
    sürer, koşulmadı.
33. **259 ignore edilmiş kaynak dosyanın kaçının gerçekten gerekli olduğu** — 2 örnek
    doğrulandı, tek tek taranmadı.
34. **`#458a` mojibake'nin testi fiilen bozup bozmadığı** — dosya AST ile parse ediliyor,
    ama pytest ile koşulmadı.

---

## 11. Kanıta Dayalı Satış / Beta Hazırlık Değerlendirmesi

> **Kural:** Ölçülmemiş bir şey için "hazır" veya "hazır değil" denmez — "**ölçülmedi**" denir.

### 11.1 Ölçülen ve YEŞİL

| Kalem | Kanıt |
|---|---|
| **Altyapı ayakta** | 9 konteyner Up 13h, RestartCount=0, crash-loop yok |
| **DB canlı ve dolu** | PG 18.1:5434, 187.835 soru, 110.858 aktif, 2.530 MB |
| **Backend performansı** | `/health` medyan 20,1 ms; OpenAPI (1,43 MB) 47 ms |
| **İçerik görsel kapsamı** | Aktif soruların **%99,77**'sinde `question_image_url` |
| **Kalite sızıntısı yok (DB)** | 56.690 `rejected`'ın **tamamı** `is_active=false` |
| **Cevap sızıntısı (API katmanı)** | `STUDENT_SAFE_QUESTION_FIELDS` canlıda — #432 gerçekten kapalı |
| **RLS mekanizması** | Uygulanıyor; `kiro2_app` non-superuser, non-bypassrls; doğru GUC ile izolasyon **çalışıyor** (kontrol kolu 0 satır) |
| **Orchestrator** | 85/85 test yeşil, 2,06 s; 45 policy runtime'da doğrulandı |
| **Depo hijyeni (git)** | Çalışma ağacı temiz, uzak uç senkron, sapma yok, `fsck` exit 0 |

### 11.2 Ölçülen ve KIRMIZI — satış/beta blokerleri

| # | Bloker | Ölçülen kanıt | Neden bloker |
|---|---|---|---|
| **B1** | **Kalite kapısı ES seviyesinde bypass ediliyor** | ES 64.270 dok; 300-örneklemin yalnız **%7'si** `v_safe_for_beta`'da. Index'te `quality_review_status` alanı **yok** → filtrelenemez | Öğrenci arama yaptığında kalite kapısından geçmemiş soru görebilir. `is_active` bile %60 |
| **B2** | **Şifre kurtarma işlevsiz** | 6/6 SMTP env **UNSET**; `email_util.py:38` guard `return False` | Şifresini unutan kullanıcı hesabına **erişemez**. Herhangi bir ticari satış için kabul edilemez |
| **B3** | **CI tamamen kırmızı** | Son **100/100** koşu FAILURE (8.447 toplam); en son 14:49 | Regresyon koruması **fiilen yok** |
| **B4** | **"Merge kapısı" fiilen çalışmıyor** | 178 GF testinin **148'i** rate-limit yüzünden skip → 30 gerçek koşum. Skip **asla FAIL üretmez**. Ayrıca aktif dalda hiç tetiklenmiyor | Yeşil bir GF koşusu **hiçbir şey kanıtlamaz** |
| **B5** | **Çok-kiracılı izolasyon uygulamaya bağımlı** | Politika GUC boşken **her satırı geçiriyor** (5.558 = superuser taban çizgisi); `get_current_tenant` 167 router dosyasının **2'sinde**; 79/209 tablo korunuyor (`users`, `question_bank`, `student_answers` **korunmuyor**) | B2B okul/kurumsal satışta kiracı sızıntısı riski. **Not:** kalan 165 router'ın GUC'u başka yoldan set edip etmediği **ÖLÇÜLMEDİ** |
| **B6** | **Bugünün işi canlıya dağıtılmamış** | #447 → 404; #444 çıkarma UI'ı 82 chunk'ın hiçbirinde; iki imaj da ~01:43'te kurulmuş, kod 17:19–17:47'de yazılmış | Demo/satış ortamı bugünün özelliklerini göstermiyor |
| **B7** | **Depo PUBLIC** | `private=false`, `visibility=public`, `pushed_at` bugün 14:49 | Geçmişte 12–14 sızmış anahtar vardı. **Anahtarların şu an canlı olup olmadığı bu oturumda ÖLÇÜLMEDİ** (önceki ölçüm 14/14 ölü) |

### 11.3 Ölçülen ve SARI — bloker değil, borç

| Kalem | Ölçüm |
|---|---|
| Test paketi uçtan uca koşamıyor | `pytest_asyncio` teardown deadlock, 288/403'te |
| 27 test kırık | Hepsi tek dosyadan; kök neden sqlite fixture eksik tablo |
| 2.327 test (%13,7) garantili hiç koşmuyor | 100 modül `skipif(True)` hardcoded |
| Coverage kendi eşiğini geçmiyor | %39,74 vs `fail_under=60.0` |
| 17 frontend test dosyası hiç koşamaz | 13 Playwright yanlış runner'da + 4 eksik modül |
| 1.822 satır / 18 endpoint ölü router | `api/learning_path.py`, canlı rota 0 |
| Boş dosyaya router kaydı | `litellm_chat.py` 0 bayt, her açılışta warning |
| 6 mock bayrağı ölü | Çevirmek hiçbir şeyi değiştirmez |
| 24 `.bak` auth dosyası git'te | 2025-11-18 migration artığı |
| `.git` 6,7 GiB | Klon maliyeti; MEMORY 218 MB diyor |
| Ankrajsız `.gitignore` | `backend/tests/performance/` 3 dosya taze klonda kayıp |
| Celery 30 dk'da bir hata + 60 s gecikme | `Event loop is closed` |
| 10 çift path+method | `study_rooms_stub` `/health`'i gölgeliyor |
| Dokümantasyon 68 gün bayat | 22 sayısal sapmanın ortak kök nedeni |

### 11.4 Karar

**Beta (kontrollü, sınırlı kullanıcı):** B1 ve B2 kapatılmadan **başlatılamaz.**
B1 öğrenciye kalitesiz içerik gösterir, B2 kullanıcıyı hesabından kilitler.
Her ikisi de **tek bir sprint'lik iş**: B1 = index'i `v_safe_for_beta`'dan yeniden kur
(+ mapping'e `quality_review_status` ekle), B2 = SMTP env doldur.

**Ticari satış (B2B okul/kurumsal):** B1–B5'in tamamı gerekli. **B5 en ağırı** çünkü
düzeltme ölçeği bilinmiyor: `get_current_tenant`'ın 167 router dosyasının 2'sinde olduğu
ölçüldü, ama kalan 165'in GUC'u **başka bir yoldan** (middleware, dependency chain) set edip
etmediği **ÖLÇÜLMEDİ**. Bu ölçüm yapılmadan B5'in maliyeti hakkında konuşulamaz —
**bir sonraki ölçümün ilk kalemi budur.**

**Şu an "hazır" denemeyecek, çünkü ölçülmedi:**
- Uçtan uca test geçerliliği (suite koşamıyor)
- Gerçek coverage
- CI kırmızısının nedeni
- ES cevap sızıntısının uçtan uca durumu (mapping'de alan var, API'de beyaz liste var,
  ikisi birlikte canlı token'la sınanmadı)
- Sızmış anahtarların şu anki canlılığı

---

## 12. Ölçülen Ana Sayılar — Tek Bakışta

```
DEPO
  HEAD                          889c71a3a  (oturum-başı snapshot 25 commit geride)
  bugünkü commit                39         (03:41 -> 17:49, tek yazar)
  master'a fark                 296 ileri / 0 geri
  .git                          6,7 GiB    (doküman: 218 MB)
  LFS                           5 desen / 527 dosya / eşik YOK

VERİTABANI  (PG 18.1, :5434, kiro2 — backend'in bağlandığı örnek)
  public tablo                  209 base + 7 view + 2 matview
  question_bank                 187.835 toplam / 110.858 aktif
  aktif + kabul statüsü         34.982
  öğrenci kapısı (mv_safe)      25.127
  questions (legacy)            36.381
  users                         77 (STUDENT 73 / PARENT 2 / TEACHER 1 / ADMIN 1)
  student_answers               53          <- platform fiilen kullanılmıyor
  question_image_url dolu       181.652 (%96,71) ; aktifte %99,77
  RLS                           79 tablo / 79 force / 79 politika  (209'un %38'i)
  DB boyutu                     2.530 MB   (question_bank 2.210 MB = %87)

SERVİSLER
  ayakta konteyner              9  (kiro2 stack 6, hepsi healthy, restart 0)
  /health                       200, medyan 20,1 ms
  OpenAPI                       1.226 operasyon / 1.147 yol / 799 schema
  kayıtlı (süreç-içi)           1.236  (10'u OpenAPI'de gizli auth ucu)
  HEAD deposu (statik AST)      1.290  -> KONTEYNER BAYAT (01:43 imaj vs 17:47 commit)
  ES index                      64.270 dok (v_safe 25.127 iken)  <- #433 açık

KOD
  backend .py (takipli)         2.415
  frontend src ts+tsx           887
  ROUTER_MAPPING                152  (3 kayıtsız + 1 hayalet)
  TODO / FIXME / HACK           39 / 0 / 0
  mock bayrağı                  20 (19 mock, 1 gerçek, 6'sı ölü)
  _deprecated importer          8 dosya / 17 import (5 üretim)

TESTLER
  backend toplanan              16.931   (doküman: 1.393)
  garantili hiç koşmayan        2.327 (%13,7)
  Golden Flow                   178 test -> 30 PASS / 148 SKIP / 0 FAIL
  orchestrator                  85 passed / 0 failed
  tests/unit                    27 FAILED + deadlock
  frontend koşabilir            2.705 test / 175 dosya  (17 dosya hiç koşamaz)
  coverage (27 May artefaktı)   %39,74 dal-dahil / %43,67 deyim   (eşik: 60)
  CI son 100 koşu               100 FAILURE
```

---

## 13. Metodolojik Ders (kural dosyasına aday)

Bu oturum `.claude/rules/audit-methodology.md`'nin üç bölümünü de **çalışırken** doğruladı
ve bir dördüncüsünü önerir hale getirdi:

1. **Varsayım ≠ Ölçüm** (Haz) → "77.336 in production" 5 ayrı yerde tekrarlanmış bir
   **dosya satır sayısıydı**.
2. **Severity de bir ölçümdür** (28 Tem) → "merge kapısı koruyor" iddiası, kapıyı
   **gerçekten koşunca** çürüdü (148/178 skip).
3. **Kök neden de bir ölçümdür** (30 Tem) → `tests/unit` kilitlenmesi "yük olabilir"
   diye bırakılmıştı; izole koşumla **deadlock olduğu kanıtlandı**.
4. **YENİ ADAY — Payda da bir ölçümdür.** Bu oturumda **dört** iddianın payı doğru,
   paydası yanlıştı:
   - `get_current_tenant` 2/**153** → gerçek 2/**167**
   - question_image_url 58.523/**77.336** → 181.652/**187.835**
   - `git ls-files "backend/**/*.py"` → 85 dosya eksik payda
   - LFS 527 vs 528 → iki alet, iki farklı payda tanımı

   **Kural:** Bir oran raporlamadan önce **payı ve paydayı ayrı ayrı** ölç ve her ikisinin
   de hangi kümeyi saydığını yaz.

5. **İKİNCİ ADAY — `grep` bir sayaç değildir.** Bu oturumda grep **beş kez** yanlış
   sayı üretti: `assert True` (%540 şişirme), `Policy(` (%42 eksik — doküman haksız yere
   yanlış ilan edilecekti), `_deprecated` basename (iddiayı tersine çevirecekti),
   `pytest.mark.skip` (skipif'i yutuyordu), `XXX` (7/7 yanlış-pozitif).
   **Kural:** Sayım raporlanacaksa AST veya runtime introspection kullan; `grep` yalnız
   **keşif** aracıdır.

---

*Oluşturulma: 2026-07-30. Ölçüm salt-okunur; `git status --short` başta ve sonda BOŞ.*
*Bu rapordaki her sayı §1'de listelenen aletlerden birinin ham çıktısıdır. Yuvarlanmamış,*
*güzelleştirilmemiştir. Ölçülemeyenler §10'da açıkça listelenmiştir.*

---

## Çürütme Turu (aynı gün)

> Bu ek, yukarıdaki raporun **kendisine** uygulanan saldırıdır. 6 bağımsız skeptik ajan
> raporun manşet iddialarını **farklı aletlerle** çürütmeye çalıştı; 5 tartışmalı kümede
> ayrıca **üçüncü bir hakem turu** koşuldu. Toplam **~60 iddia** sınandı.
> Kural: her ajan önce kendi aletinin **kontrol kolunu** kurdu; kontrol kolu beklenen
> sonucu vermediğinde bulgu **raporlanmadı**, alet arızası ilan edildi.
>
> **Bu ekin varlık nedeni:** aşağıdaki 8 manşet iddia yanlıştı ve kullanıcının karar
> almasına girmeden yakalandı.

### A. AYAKTA — saldırıya dayandı (34 iddia)

| # | İddia | Nasıl saldırıldı | Sonuç |
|---|---|---|---|
| 1 | `question_bank` = 187.835 | SQLAlchemy + asyncpg + host psycopg3 (3 sürücü); RLS gizleme kontrolü | Birebir; `is_active` NULL = 0, 110.858+76.977=187.835 iç tutarlı |
| 2 | `is_active=true` = 110.858 | Üç-değerli mantık (NULL) tuzağı test edildi | Birebir |
| 3 | aktif + kabul statüsü = 34.982 | `pg_get_viewdef` ile kabul kümesi DB'nin kendi DDL'inden okundu | Birebir. **Nüans:** `human_verified` statülü **0 satır** var — kabul kümesi fiilen tek elemanlı |
| 4 | `mv_safe_for_beta` = 25.127 | Aynı adlı VIEW arandı, çift yönlü `EXCEPT` simetrik fark | 25.127 = 25.127, fark 0/0; matview **taze** |
| 5 | legacy `questions` = 36.381 | İki sürücü + RLS kontrolü | Birebir. CLAUDE.md'nin "BOŞ legacy" ifadesi **yanlış** |
| 6 | `question_image_url` 181.652 (%96,71) / aktif 110.606 (%99,77) | Boş-string tuzağı (`<> ''`) test edildi | Birebir; yüzdeler yeniden hesaplandı |
| 7 | 209 BASE TABLE + 7 VIEW + 2 MATVIEW | `pg_class`/relkind vs `information_schema` çapraz; partitioned/foreign dahil | Birebir; beklenen fark (matview `information_schema`'da yok) çıktı |
| 8 | 77.336 = `eslesmis_sorucevap.jsonl` satır sayısı | `wc -l` KULLANILMADAN: ham-bayt sayacı + `json.loads` + `awk NR`; ayrıca üretici replay | 77.336; dosya newline ile **bitiyor** (77.337 değil), 0 bozuk JSON |
| 9 | CLAUDE.md 77.336'yı "DB üretim sayısı" diye sunuyor | Satır bağlamı okundu, "sadece dataset etiketi" okuması kurtarılmaya çalışıldı | Ayakta: `### Database & Content` / "in production" / "CURRENT PRODUCTION" |
| 10 | B1-a: ES 64.270 dok vs kapı 25.127 | `track_total_hits:true` ile kesin toplam | `{'value':64270,'relation':'eq'}` |
| 11 | B1-c: ES'te `correct_answer` + `explanation` var, kalite alanı yok | Mapping'e değil **gerçek belgeye** bakıldı | **Güçlendi:** `correct_answer` 64.270/64.270 dolu; `explanation`'ın 61.847'si "Doğru cevap: X" yazıyor; `quality_review_status` mapping'de bile **0** |
| 12 | B5-a: 79 tablo RLS+FORCE+politika | Üç küme ayrı sayılıp çapraz kesildi | 79/209 = %37,8; üç küme **birebir aynı** 79 tablo |
| 13 | B5-c: `users`/`question_bank`/`student_answers`'ta RLS hiç açık değil | "Uykuda politika" arandı | `False/False/0`; aynı sorguda RLS'li tablolar `True/True/1` (kontrol kolu) |
| 14 | B4-a: Golden Flow 178 test toplar | `--collect-only` + AST + sunucu login logları | 178; 30 başarılı login **3 ayrı koşumda** birebir |
| 15 | B6-a: `/api/v1/me` = 404 | Host + konteyner içi + canlı OpenAPI (1.147 yol) | 404; kontrol kolu `/api/v1/auth/me` → **401** (proxy karışıklığı elendi) |
| 16 | B6-b: öğretmen "sınıftan çıkar" UI'ı bundle'da yok | Minify'a dayanıklı **string literal**'lerle yeniden arandı; Türkçe kontrol kolu | 0 isabet; kontrol kolu (`ogrenci@okul.tr`, `Sınıfa ekle`) **bulundu** → grep kör değil |
| 17 | B6-c: imaj 01:42:58Z, commitler 14:19Z/14:47Z, `/app` bind-mount değil | Tam mount listesi (kesilmeden) + saat dilimi açık hesap | 3 mount, hiçbiri kodu kapsamıyor; frontend `Mounts: []` |
| 18 | B2-a: 6/6 SMTP değişkeni UNSET | `docker exec env` + `/proc/1/environ` + çalışan python `os.environ` | Üç katmanda da 0 |
| 19 | B2-b: `core/email_util.py:38` guard | Host + konteyner kopyası + **çağıran zinciri** | Birebir; util içinde yedek yok |
| 20 | T-a: 16.931 toplanan / 0 toplama hatası | AST (14.056 tanım) + ripgrep (14.175) bağımsız alt sınır | Ayakta; 817 "error" geçişinin hepsi test **adı** |
| 21 | T-d: 27 FAILED, kök neden `no such table: learning_path_student_profiles` | Dosya izole koşuldu, hata **sınıfları** ayrı sayıldı | 27 failed/112 passed, 108 geçiş, başka `no such table` **yok** |
| 22 | T-g: orchestrator 85/85 yeşil | Canlı koşum; skip/xfail şişirmesi arandı | 85 passed, 0 skip, 9,26 s |
| 23 | §3.3: 56.690 rejected'in tamamı `is_active=false` | ORM `group_by`, tüm 9 satır filtresiz | `rejected`+`true` satırı **yok** — testing.md Ders #31 DB'de kapalı |
| 24 | §4.3: canlı OpenAPI 1.226 / 1.147 / 799 | Telden `http.client` + konteyner içi urllib | Birebir; metod kırılımı da (647/484/35/48/11/1) |
| 25 | §3.1: PG 18.1 / 5434 / kiro2 / kiro2_app | Backend'in **kendi havuzundan** soruldu | Birebir; "docker pg15 5434'ü kaptı" tuzağı elendi |
| 26 | §3.5: MEMORY'nin RLS kontrol kolu **geçersiz alet** | `users`/`question_bank` RLS durumu bağımsız ölçüldü | `False`/`False` — raporun kendi kaynağını eleştirisi haklı |
| 27 | §2.1: `.git` = 6,7 GiB (218 MB doküman ~31x bayat) | PowerShell FS API + `du --apparent-size` | 4.926 dosya / **7.125.645.477 bayt** = 6,64 GiB; `du -sh` gerçekten `6.7G` basıyor |
| 28 | CLAUDE.md son commit 23 May, 68 gün / frontend 196 test dosyası / "17 Mar'da bile 96'ydı" | `git ls-tree` geçmiş ağacı | Üçü de birebir; 2026-03-18 ağacında tam **96** |
| 29 | §5.2 kök neden: `_login()` 200 dışı her yanıtı `pytest.skip`'e çeviriyor | Kaynak + rate-limit yapılandırması + davranışsal 429 eşiği | Birebir; limit 30/60 s, dev-bypass listesi Docker gateway'i **içermiyor** |
| 30 | §6.2: `api.litellm_chat` için loader `No router found` uyarısı üretiyor | Canlı konteyner açılış logu | `2026-07-30 01:48:13 ... No router found in api.litellm_chat` |
| 31 | §2.2/§2.3: `.gitignore:266 performance/` + `litellm_chat.py` 0 bayt/ignore | `git check-ignore -v` çıktısı karakter karakter yeniden üretildi | Birebir; diskte 5 `.py`, takipli 2 → taze klonda 3 kayıp |
| 32 | §9.2 alet tuzağı: FastAPI `_IncludedRouter` proxy'si | Aynı hata **bilerek** tekrarlandı | Naif walker `APIRoute=1` verdi ve `/api/v1/cat` için 0 döndü → tuzak gerçek |
| 33 | Özet: `pre-commit-check.py:73` kabuk komutunu boşluktan bölüyor | Fonksiyon **çalıştırıldı**, 2 kontrol kolu | Doğru ve **eksik**: `&&` sonrası yanlış-pozitif; **tırnaklı yol 111,3 MB dosyayı geçiriyor** |
| 34 | B4-b mekanizması: skip'ler login 429 kaynaklı | AST + davranışsal limiter + konteyner logları | 176 login-dokunan test − 30 izin = **146** 429 |

### B. DÜZELTİLDİ — özü aynı, sayı değişti (19 iddia)

| # | İddia | Eski | Yeni | Kanıt |
|---|---|---|---|---|
| 1 | jsonl kayıtlarının DB'ye girip girmediği | "ÖLÇÜLEMEDİ" (§10.2 md.10) | **%99,988** (77.327/77.336); ilişki çift yönlü birebir | Script'in kendi `uuid5(NS,'book\|page\|qnum')` üreteci replay edildi; Mar-04 partisinde jsonl'den gelmeyen **0** satır |
| 2 | 4 Mart DB katmanı | 77.336 | **77.327** (9 eksik, hepsi AYT MATEMATİK) | 198 tablo tarandı, hiçbirinde yok; kitap dağılımı 345-2024:3 / 345-2025:4 / Full:2 |
| 3 | B1-b: ES'in v_safe oranı | %7,0 (300 örneklem) | **%5,70** (3.665/64.270) — tam sayım | ES-tarafı `terms` sayımı; ayrıca `is_active` %60,3 → **%60,63** |
| 4 | B1-d: ES ne zamandır değişmemiş | "28 Tem'den beri" | **1 Nisan 2026'dan beri**; tüm index **19 saniyede** yazılmış | Lucene segment mtime'ları 2026-04-01 01:51:55–01:52:14; kontrol kolu `analytics-2026-07` 27/28/29/30 Tem yazmış |
| 5 | B5-b: RLS GUC bypass satır sayıları | 5.558 / 10.096 / 70.000 | **5.662 / 10.099 / 70.000** | Uygulamanın **kendi asyncpg motoruyla**, `SET ROLE` simülasyonu olmadan; taze bağlantıda GUC gerçekten NULL |
| 6 | B3: toplam CI koşumu | 8.447 | **8.450**; son 100'ün **74'ü 0-iş kaydı** | Sunucu-taraflı `total_count`; sıfır-süre damgası (created=started=updated) |
| 7 | B4-b: 429 kaynaklı skip | 147 | **146** (kalan 2 test login'e hiç dokunmuyor) | AST + doğrudan endpoint literali çift tarama |
| 8 | T-b: garantili hiç koşmayan test | 2.327 (%13,7) | **2.841 (%16,78)** toplanan içinde; +**18 modül / 335 test hiç toplanmıyor**; genel **3.176/17.266 = %18,4** | pytest'in kendi `evaluate_skip_marks` fonksiyonu her item için çağrıldı |
| 9 | T-e: deadlock noktası | 288/403 | **336 test sonuçlanıyor**, kilit 337. maddeye geçişteki `teardown_exact` | `-v` tamponsuz koşum; son satır `TestOSYMExamExtendedScenarios::test_save_answer_all_options [83%]` |
| 10 | T-f: frontend koşabilir/koşamaz | 175 / 17 | **179 / 17** (175+17=192≠196 aritmetiği kapanmıyordu) | `vitest list` tam collection: 13 playwright + **4 yetim dosya** (silinmiş modül import ediyor) |
| 11 | T-c: coverage karşılaştırması | "%53 vs %39,74" | Elma-elma: **%53 line vs %43,54 line** (aynı 5 paket, 108.563 deyim) | `.coverage` sqlite'ından 661 dosyanın paket dağılımı; CLAUDE.md'nin kendi "(109K lines)" parantezi paydayı doğruluyor |
| 12 | §3.6: öğrenci trafiği sayıları | 53 / 105 | **59 / 117** (+6 / +12) | Artışın tamamı **bu ölçümün kendi Golden Flow koşumlarından** |
| 13 | §4.3 "Kayıtlı (süreç-içi)" sütunu | 653/496/36/49/11/1, toplam 1.236 | Sütun **ham** (toplamı 1.246), toplam **dedup sonrası**. Doğrusu: **648/492/36/48/11/1 = 1.236** | Telden spec + raporun kendi 10 gizli-uç listesinden bağımsız türetme |
| 14 | §0: "9 konteyner healthy" | 9 healthy | **9 çalışıyor, 7 healthy, 2'sinde healthcheck TANIMSIZ** | `docker inspect .State.Health` — `turkiye_sinav_elasticsearch` ve `openwebui-litellm-prometheus-1` |
| 15 | §7.3: "22 sapmanın ortak kök nedeni CLAUDE.md" | 22/22 | **15/22** | Tablo makineyle ayrıştırıldı; kalan 7 → golden-flows.md (14 May), pytest.ini (10 Nis), CLAUDE.local, MEMORY, Görev #311 |
| 16 | §6.1: "ROUTER_MAPPING 152 (AST 152 = runtime 152)" | 152 = runtime | Host **152**, canlı konteyner **151** (150 yüklü) | Modül gerçekten import edilip `len()` okundu; §4.4'ün md5 farkının doğrudan sonucu |
| 17 | Özet: "doküman 1.223" | 1.223 | **1.393** (1.223 passed + 169 skipped + 1 fail); raporun §7.1'i zaten doğru | CLAUDE.md:659 ham satır |
| 18 | Özet: "orchestrator 35 modül / 7 agent" | 35/7 | "35" = `orchestrator/core/*.py` eksi `__init__` (tanım raporda yazılı değil); diğer paydalar 6/44/47/48. **"7 agent" iki AYRI enum → 14 farklı rol adı** | `pkgutil.walk_packages` + enum üye adları (`PLANNER…` vs `TURKISH_NLP…`, kesişim boş) |
| 19 | §2.1 `.git` boyutu | (skeptik "6,5 GiB, yukarı yuvarlanmış" dedi) | **Rapor haklı**: 6,64 GiB. Skeptik `git count-objects`'i `.git` dizini sandı — o yalnız pack+loose nesneleri sayar | PowerShell 7.125.645.477 bayt ≈ python 7.125.605.052 bayt |

### C. ÇÜRÜTÜLDÜ — bu ekin asıl değeri (8 manşet)

#### C1. "Yazma işlemi YOK — salt okunur" (§1 başlığı + §1.3) — **YANLIŞ**

Ölçüm penceresi içinde DB'ye **en az 134 satır INSERT** ve **~1.900 satır UPDATE** yazıldı.

```
pg_stat_user_tables (motor sayaçları, uptime 21:44:47 → pencere kapsıyor)
  exam_sessions          n_tup_ins=12    n_tup_upd=1782
  refresh_tokens         n_tup_ins=104   n_tup_upd=3
  student_answers        n_tup_ins=6
  kiro2_learning_events  n_tup_ins=6
  chat_sessions          n_tup_ins=3
  daily_quests           n_tup_ins=3     n_tup_upd=3
  users                  n_tup_upd=118
  question_bank          n_tup_ins=3     n_tup_upd=12
```

Konteyner HTTP logları (UTC 15:30–15:42) kaynağı kesinleştiriyor: 3 ayrı kaynak porttan
`POST /api/v1/osym-exam/create` ×4, `POST /api/v1/teacher/classes`, `POST /api/v1/chat/sessions`,
`POST /api/v1/placement/start` 201, `PUT /api/v1/auth/profile` 200.

**En ağır kısım:** raporun **kendi §5.2'si** paketin yazma yüzeyini "69 GET, **131 POST**, 2 PUT,
1 PATCH, 1 DELETE" diye ölçmüştü. Yani yazma riski **biliniyordu** ve aynı belgede
"hiçbir DB yazması yapılmadı" yazıldı.

**Doğru ifade:** *"git çalışma ağacına yazılmadı (`git status --short` BOŞ — bu kısım doğru);
DB'ye Golden Flow koşumları yoluyla yazıldı."*

**İkinci dereceden zarar:** kirlenen satırlar **§3.6'nın ta kendisi**. 53→59 ve 105→117
artışları "platform fiilen kullanılmıyor" sonucunun dayanağıydı.

#### C2. "DB'de kalite sızıntısı YOK" (§3.3 genellemesi) — **YANLIŞ**

Ölçülebilir çekirdek doğru (`rejected` + `is_active=true` = **0**), **sonuç yanlış**.
`rejected` kalite yargısının tek ekseni değil:

```
gate2c_demoted toplam                              836
  ...VE is_active=true                             836   <- TAMAMI aktif
  ...VE aktif VE kabul statüsünde                  834
aktif + 'demoted_at' damgalı + kabul statüsü       470
aktif + 'demoted_at' damgalı (toplam)           26.613
aktif+kabul (34.982) ama mv_safe_for_beta DIŞI   9.855
aktif (110.858) ama kapı dışı                   85.731
mv_safe_for_beta içindeki demote edilmiş satır       0   <- kapı ÇALIŞIYOR
```

Yani **açıkça demote edilmiş 834 soru** hem `is_active=true` hem kabul statüsünde duruyor.
Sızıntıyı tutan tek şey kodun `safe_for_beta_gate()` çağırması; DB tarafında **hiçbir koruma yok**.

**Ve kapıyı uygulamayan bir yol zaten var — canlı Elasticsearch:**

```
turkiye_sinav_platform: 64.270 dok / search.query_total=474 (SERVİS EDİLİYOR)
  DB'de is_active=false           25.294  (18.183 rejected + 7.100 legacy + 11 auto_high)
  gate2c_demoted dokümanı              99
  question_bank'ta HİÇ olmayan          9
  mv_safe_for_beta onaylı           3.665  (%5,7)
ES'in kendi is_active alanı: 64.270/64.270 "true"   <- 25.303 doküman YANLIŞ bayrak taşıyor
indexing.index_total = 0 (15 saattir yazma yok, snapshot bayat)
```

> **Not (dürüstlük kaydı):** `correct_answer` 64.270 dokümanın `_source`'unda duruyor,
> ancak "öğrenciye sızar" **iddia edilmiyor** — `/api/v1/elasticsearch/questions/search`
> auth'suz **401** dönüyor (kontrol kolu: `/zzz-hakem-kontrol-kolu`=404, `/health`=200).
> API katmanının alan filtrelemesi **ölçülmedi**.

#### C3. "Gerçek öğrenci trafiği: 53 / 105" — sayı düzeltildi, **niteleme çürütüldü**

```
exam_sessions distinct student_id = 1
  0d3b011a-8be9-49cb-9a87-f8a8317ccc3d = test@kiro2.com (STUDENT, 4 Mart fikstürü)
users by role: STUDENT 73 | PARENT 2 | TEACHER 1 | ADMIN 1
```

117/117 oturum **tek sentetik hesaptan**. Bugünkü 12 oturum 3 patlama halinde
(18:32 / 18:35 / 18:39), her patlamada 4 oturum saniyeler içinde — insan davranışı değil.
DB **dışı** delil: konteyner erişim logları 12 `POST /osym-exam/create`'i aynı saniyelerde
gösteriyor. **Gerçek öğrenci trafiği = 0.** 73 STUDENT hesabı var, sınav açan **1**.
Bu satırlar benimseme/kullanım kanıtı olarak **kullanılamaz**.

#### C4. "Canlı DB'de 77.336'ya karşılık gelen hiçbir katman yok" — **YANLIŞ**

```
created_at gün dağılımı:  2026-03-04 | 77.327   2026-03-23 | 20   2026-05-12 | 105.152
Mar-04 partisi created_at aralığı: 08:20:30.685146 → 08:20:30.685146  (TEK mikrosaniye)
cohort ids NOT in jsonl : 0      jsonl ids NOT in cohort : 9
```

Mekanizma da ölçüldü: `created_at DEFAULT now()`, PostgreSQL'de `now()` işlem-başlangıç
zamanıdır ve işlem boyunca sabittir; script tüm INSERT'leri tek `with engine.begin()`
içine sarar. Kontrast kontrolü: Mayıs-12 partileri timestamp başına **500** satır
(batch-commit'li başka script) — yani "tek timestamp = tek işlem" yorumu doğrulanmış imza.

#### C5. "77.336 sadece bir dataset etiketi, DB provenance'ı yok" — **YANLIŞ**

Provenance zinciri kapalı ve **zaman ekseninde** doğrulandı:

```
ingest işlemi        2026-03-04 08:20:30   (77.327 satır, 405 distinct source_book)
commit 877cb44c5     2026-03-04 08:24:28   "import 77,336 d-dataset questions"
                     govde: "77,336 inserted, 0 errors, 0 duplicates, 66.5s"
CLAUDE.md'ye ilk giriş 2026-03-05          (ingest'ten BİR GÜN SONRA → türetilmiş)
jsonl distinct book_name 405 == Mar-04 distinct source_book 405   (set eşitliği True)
pipeline_metadata 'v2_2_tier' imzası: TÜM tabloda tam 77.327 satır
git diff 877cb44c5..HEAD -- import_d_dataset.py : id mantığında DEĞİŞİKLİK YOK
```

#### C6. "golden-flows.yml yalnız main/master/develop'ta tetikleniyor; aktif dalda HİÇ koşmuyor" — **YANLIŞ**

Aktif dalda **130 koşum** var (sunucu-taraflı `?branch=` sayacı). `on: branches` satırları
**alakasız**, çünkü dosya **2026-04-12'den beri geçersiz YAML**:

```
git blame -L 172,172 -> d1506c22f8 (2026-04-12 00:28:40)
  - name: AST lint — Pydantic `user_id: int` type lie (rule-of-five)
js-yaml : "bad indentation of a mapping entry (172:43)"
PyYAML  : "mapping values are not allowed here, line 172, column 43"
bisect  : 2026-04-11'e kadar TÜM commitler PARSE_OK
```

Dört bağımsız parmak izi: (a) iki farklı YAML uygulaması aynı yerde patlıyor,
(b) GitHub'ın workflow registry'sinde `name` alanı ayrıştırılamayan **tam 2 dosya** için
dosya **YOLUNA** düşmüş (9 sağlam dosyada gerçek ad var), (c) koşumlar sıfır süreli
(created=started=updated), (d) `check-suites` → `latest_check_runs_count=0` iken kontrol
kolu health-checks **4** veriyor.

**Gerçek durum: Golden Flow birleştirme kapısı `master` DAHİL hiçbir dalda çalışmıyor.**
446 koşumun **0'ı** success; ~422'si 12 Nisan sonrası, hepsi 0 iş.
Aynı kusur `quality-gate.yml`'de de var (satır 17/18 çift `workflow_dispatch`; 290 koşum,
290 failure, 0 success) → **7 AST linter kapısının hiçbiri CI'da koşmuyor.**

> **Neden bu çürütme kritik:** ilk ölçümün okuması **metinsel olarak doğruydu** (dosyada
> gerçekten öyle yazıyor) ama sistem o satırları hiç okumuyor. İlk ölçümün tavsiyesi
> "dal filtresine feature dalını ekleyelim" olurdu ve **hiçbir şey düzeltmezdi**.

#### C7. "Health check: doküman ~9 sn yanlış, gerçek 20,1 ms — ~450x" — **DESTEKLENMİYOR**

İki ölçüm **aynı ucu ölçmemiş**. Canlı sistemde adında `health` geçen 57 yol var:

```
KONTEYNER İÇİNDEN (11 tekrar)
  /health              200  medyan   1,08 ms
  /health/ready        200  medyan  13,40 ms
  /api/v1/health       404  medyan  10,41 ms      <- negatif kontrol kolu
DERİN UÇ (5 tekrar)
  /health/detailed     200  medyan 346,0 ms   min 323,6   max 9.292,9 ms   <<< SOĞUK ÇAĞRI 9,29 sn
    govde: database 51,9 | redis 51,94 | elasticsearch unhealthy | llm_service 536,03
CLAUDE.md:682 ham satır:
  | Health Check | <1s | ~9s | 🟡 ES/Redis timeout (infra, not API) |
backend/api/health.py:158 @router.get("/health/detailed")
  asyncio.gather(database, redis, elasticsearch, llm)
```

Dokümanın kendi notu (`ES/Redis timeout`) tam olarak bu ucun bağımlılıklarını adlandırıyor.
`~450x yanlış` ibaresi **raporda ve özette düzeltilmelidir**.
Ayrıca `20,1 ms` **host** taraflı; aynı uç konteyner içinden **1,08 ms** — 20 ms'nin ~%95'i
API dışı loopback/TCP maliyeti.

> **Uyarı:** 9,29 sn **tek soğuk örnek** (5 tekrarın max'ı). Tekrar üretmek için LLM/ES
> önbelleği soğutulmalı. Yine de "~9s çürük" demek için gereken kanıt **ortadan kalktı**.

#### C8. "9 kayıt ingest sırasında hiç yazılmamış; yedekte yok, YANİ sonradan silinme DEĞİL" — **çıkarım desteksiz**

"Yedekte yok ⇒ silinmedi" bir *non-sequitur*: yedeksiz `DELETE` hiçbir iz bırakmaz.
Kök neden **DOĞRULANAMADI** (bkz. D bölümü).

### D. DOĞRULANAMADI — açıkça işaretlenir

| # | Konu | Neden ölçülemedi |
|---|---|---|
| 1 | 9 kayıp kaydın kök nedeni | İki hipotez açık. **"Hiç yazılmadı" lehine:** ingest öncesi tabloda 0 satır (`ON CONFLICT` tetiklenemezdi), tek işlem (ya hep ya hiç), parse hatası 0, çarpışma 0, commit gövdesi "77,336 inserted / 0 duplicates". **"Sonradan silindi" lehine:** en eski yedek tablo `..._20260619` — Mart–Haziran penceresinde yedek YOK; `pg_stat.n_tup_del=0` **kanıt değil** çünkü aynı satırda `n_live_tup=0` (sayaçlar sıfırlanmış). **Ayırt edici delil:** jsonl mtime `2026-03-04 20:28:57`, ingest `08:20:30` → dosya ingest'ten **~12 saat sonra** yeniden yazılmış ve **git'te takipsiz**, o sürüm kurtarılamıyor |
| 2 | Frontend 179 koşabilir dosyanın pass/fail sonucu | Tam vitest koşumu 10+ dk; yapılmadı. Uyarı: "koşabilir" ≠ "geçiyor" — rastgele seçilen kontrol dosyasında 27 testin **2'si zaten FAIL** |
| 3 | ES `correct_answer`'ının API katmanından öğrenciye ulaşıp ulaşmadığı | Uç auth arkasında (401); alan filtrelemesi ölçülmedi. **İddia edilmiyor** |
| 4 | `/health/detailed` 9,29 sn'nin tekrar üretilebilirliği | Tek soğuk örnek; LLM/ES önbelleği soğutulmadan tekrarlanamaz |
| 5 | 86 ortam-koşullu skip'in başka makinedeki davranışı | 12 dosya; "her makinede garantili" değil "bu makinede" |
| 6 | Golden Flow "0 FAIL" alt iddiası (bağımsız teyit) | Paket yeniden koşulmadı — **çünkü koşmak DB'ye yazıyor** (bkz. C1). Sunucu logları yalnız login katmanını gösterir |
| 7 | `.coveragerc` hangi test alt kümesiyle üretildi | Artefakt 27 May; koşum komutu kayıtlı değil |

### E. RAPOR METNİ ve ÖZET KUSURLARI (yumuşatılmadı)

**Rapor gövdesi:**

1. **§1 + §1.3 "Yazma işlemi YOK"** — yanlış (C1). Raporun kendi §5.2'si 131 POST ölçmüştü.
2. **§3.6 / §12 vs §10.2 md.13 çelişkisi** — gövde kesin dille "platform fiilen kullanılmıyor"
   derken ÖLÇÜLEMEYENLER "gerçek kullanıcı mı fikstür mü profillenmedi" diyor. Aynı olgu
   hem kesin hem ölçülemez ilan edilmiş. (Cevap: **fikstür**.)
3. **§7.1 satır 10 vs §10.1 md.2 çelişkisi** — coverage için gövde kesin `❌` basıyor,
   ÖLÇÜLEMEYENLER "hangi test alt kümesiyle üretildiği bilinmiyor" diyor.
4. **§7.1 satır 10 metrik karışımı** — `%53` **line**, `%39,74` **dal-dahil**. Elma-elma
   karşılaştırma `%53` vs `%43,54`. Ayrıca iki farklı **tarih** kıyaslanıyor (17 Mar iddiası
   vs 27 May artefaktı).
5. **§4.3 aritmetik tutarsızlığı** — sütun toplamı 1.246, toplam hücresi 1.236 (ham vs dedup).
6. **§0 vs §4.1 vs §12** — aynı olgu üç yerde üç farklı doğrulukta; **en yanlış sürüm §0'da**
   (kullanıcıya ilk çarpan cümle).
7. **§7.3 nedensel aşırı-iddia** — "22 sapmanın ortak kök nedeni" gerçekte 15/22. Dahası
   MEMORY satırlarında **tersine** çalışıyor: `MEMORY.md` **bugün** güncellenmiş
   (mtime 2026-07-30 07:25) ama bayat sayı taşıyor; buna karşılık `golden-flows.md` (14 May)
   ve `pytest.ini` (10 Nis) CLAUDE.md'den **daha** bayat ve tarihleri hiç ölçülmemiş.
8. **§6.1 host/konteyner etiketsiz karışımı** — `152 (AST = runtime)` host-içi geçerli;
   canlıda 151. Rapor §4.4'te konteynerin bayat olduğunu **kendisi ölçmüş**.
9. **§6.2 kaldırma/gözlem deneyi yapılmamış** — iddia doğru çıktı ama daha ilginç olgu
   kaçırılmış: özet `Failed: 0` diyor çünkü o dal `register_failed()` çağırmıyor;
   `self.failed_count` **hiç okunmayan ölü sayaç**.
10. **§6.2 satır numaraları ters** — `loader.py:137` = `tracing_example`, `:138` = `sentry_demo`.
11. **§7.1 satır 14 parantezi yanlış** — `.claude/agents/ 13` → gerçek **17** takipli `.md`
    (diskte 37).
12. **§5.1/§5.4/§10.1 kapanmamış 4 dosyalık muhasebe** — 196−17=179 iken "175 koşabilir"
    yazılmış. (Çözüldü: **179**; eksik 4, silinmiş modül import eden yetim dosyalar.)
13. **§3.4 başlık aşırısı** — "77.336 sayısının gerçek kaynağı — **çözüldü**" derken
    §10.2 md.10 "join anahtarı belirlenmedi" diyor. (Bu ek onu **gerçekten** çözdü: %99,988.)
14. **§4.2 `~450x` sabit çarpan** — yanlış uç karşılaştırılmış (C7).
15. **§0 `%83'ü rate-limit yüzünden`** — 148 skip'in **147'si** rate-limit, 1'i seed;
    doğrusu 147/178 = %82,6.
16. **§10 kapsamı eksik** — test **dosyası** paydası hiç tanımlanmamış; şu an dört değer
    dolaşımda: rapor **615**, `backend/tests/` altı **611**, `backend` altı tüm takipli
    **724**, disk tabanlı **803**. Raporun **kendi §13 "payda da bir ölçümdür"** kuralının
    gövdesinde ihlali.

**Kullanıcıya iletilen özet (rapordan SAPAN kusurlar):**

17. **"doküman 1.223"** — doküman **1.393** diyor ve **rapor bunu doğru kullanıyor**.
    Özet paydayı küçültüp farkı 12,2x yerine **13,8x** göstermiş.
18. **"coverage gerçek %39,74"** — raporun **"27 May 2026 artefaktı"** ve **"kapsamı bilinmiyor"**
    kayıtlarını tamamen düşürüp sayıyı **taze ölçüm** gibi sunmuş.
19. **"orchestrator 35/7"** — rapor bilerek **üç alternatif payda** verip "24 hiçbirine uymuyor"
    demiş; özet tek kesin sayıya **düzleştirmiş**.
20. **"pre-commit-check.py:73 …"** — bu iddia 943 satırlık raporda **HİÇ GEÇMİYOR**
    (`grep`: No matches). Sentez katmanı rapora dayanmayan malzeme eklemiş.
    *İddianın kendisi çalışma-zamanı testiyle **doğru** çıktı ve hatta **eksik**ti* — ama
    "rapora dayanıyor" izlenimi yanıltıcı.
21. **"9 konteyner healthy"** — 7 healthy, 2 healthcheck tanımsız.
22. **"~450x yanlış"** — desteklenmiyor (C7).

### F. Bu turda ORTAYA ÇIKAN yeni bulgular

**Ürün kusurları (hiçbir turda raporlanmamıştı):**

1. **`POST /api/v1/admin/content/questions` 200 OK dönüyor ama hiçbir şey kalıcı olmuyor.**
   3 çağrı, `question_bank.n_tup_ins=3`, ama toplam hâlâ 187.835; `max(created_at)`
   2026-06-22 23:55:40; bugün `updated_at` alan **0** satır. Uç "başarılı" diyor, veri yok.
2. **`DELETE /api/v1/admin/content/questions/3faf4e57-1f38-4771-a209-30839101cd2c` → 500** (3 kez).
   Hedef satır gerçek ve mevcut (`is_active=t`). Canlı admin silme yolunda 500.
3. **ES'te 9 hayalet doküman** — `question_bank`'ta HİÇ olmayan 9 id arama sonucu olarak
   servis ediliyor (hepsi AYT MATEMATİK, hepsi `correct_answer` taşıyor, legacy `questions`
   tablosunda da yok). **Hiçbir PG-taraflı kapı, audit veya `is_active=false` işlemi bunlara
   ulaşamaz** — SQL'de satırları yok. Bunlar 4 Mart ingest'inde eksik kalan 9 kaydın **aynısı**:
   `00790cdd…, 2449bfae…, 24f39cfe…, 63b1cc91…, 691fab7a…, 789fcec4…, 78bd39f8…, 994d7f11…, c879b7c7…`
4. **ES ile PG arasında artımlı senkron yolu YOK** — 64.270 doküman 19 saniyede tek toplu
   yüklemeyle yazılmış, translog 55 bayt (boş). 4 aydır biriken tüm PG kalite/silme işlemleri
   ES'e hiç yansımadı. Bu, (3) ve "ES `is_active` bayat" bulgusunun kök nedeni.
5. **#433 görevi sanılandan çok daha büyük** — `v_safe_for_beta`'daki 25.127 sorunun yalnız
   **3.665'i (%14,59)** ES'te var; **21.462 güvenli soru ES'te hiç yok**. Yani "daraltma"
   değil, indeksin %94,3'ünü atıp %85,4'ü yeni olan bir **yeniden inşa**.
6. **`human_verified` statüsü `question_bank`'ta HİÇ YOK** (6 statü var). Kod ve kurallar
   boyunca geçen `quality_review_status in ('auto_judged_high','human_verified')` filtresinin
   ikinci kolu **ölü**; "kabul" fiilen tek statüye eşit. Filtreyi okuyan herkes iki katmanlı
   bir kabul kümesi olduğunu sanıyor.
7. **RLS'te istisna SIFIR** — 79 FORCE RLS tablosunun **79'unun da** politikası
   `current_setting(...) IS NULL OR = '' OR eşleşme` kalıbında; bu kalıbı taşımayan **0**.
   Fail-closed davranan tek bir kiracı tablosu bile yok. İkinci organizasyon eklendiği an
   **79 tablo birden** açılır. GUC'u set eden tek üretim satırı `core/dependencies.py:456`
   ve bunu tetikleyen `get_current_tenant` **142 router dosyasının 2'sinde**.
   *Severity düzeltmesi:* bugün organizasyonlar tablosunda **1** satır var ve RLS'li
   tablolardaki tüm satırlar ona ait → **bugün çapraz-kiracı sızıntısı imkânsız**.
   B5 "aktif sızıntı" değil, "ikinci kiracıda açılacak tuzak".
8. **Golden Flow + quality-gate kapıları 3,5 aydır ölü** (C6) — `.claude/rules/golden-flows.md`
   "Merge block" kuralı ile sistem davranışı arasında sessiz sapma.
9. **4 yetim frontend test dosyası** — import ettikleri modüller **diskte yok**:
   `src/hooks/useOfflineMode`, `src/services/modernApiClient`, `src/services/VideoErrorHandler`(×2).
   vitest "no tests" diyor, suite genelinde sessizce kayboluyorlar.
10. **18 backend modülü hiç toplanmıyor** (10 değil), 335 test fonksiyonu. Bir kısmı gerçek
    bağımlılık kırığı: `ElasticsearchConfig` import edilemiyor; `huggingface-hub==1.19.0`
    transformers ile uyumsuz; `adaptive_test_engine`/`doc_updater_service`/
    `question_generation_engine` modülleri yok. pytest bunu tek satırda söylüyor:
    `collected 16931 items / 18 skipped`.
11. **Depo kendi coverage komutunu kendi konfigüyle üretemiyor** — `.coveragerc`
    `[run] source` listesinde **`models` yok**, oysa CLAUDE.md'nin dokümante ettiği komut
    `--cov=models` içeriyor ve artefakt 81 models dosyası taşıyor →
    `coverage report/json` "No data to report" (rc=1).
12. **`n_live_tup` ölü** — `question_bank`/`questions` için `last_analyze`, `last_autoanalyze`,
    `last_vacuum`, `last_autovacuum` **hepsi NULL**, `n_live_tup=0` (gerçek 187.835).
    `n_live_tup` okuyan her sağlık/izleme sorgusu tabloyu **BOŞ** raporlar — bu deponun
    daha önce yaşadığı "questions tablosu BOŞ" fantomunun **tam olarak aynı mekanizması**.
13. **Yedek penceresi boşluğu** — en eski yedek tablo `question_bank_vp116_status_backup_20260619`.
    2026-03-04 ile 2026-06-19 arasındaki ~3,5 ay için hiçbir yıkıcı işlemin yedeği yok;
    "her DB değişikliği backup + reversible" kuralı bu pencerede uygulanmamış.
14. **Provenance kırılganlığı** — `d-dataset/eslesmis_sorucevap.jsonl` **git'te takipsiz**
    ve diskteki sürüm ingest'ten **12 saat sonra** yeniden yazılmış. "Production jsonl = DB
    içeriği" eşitliği kanıtlanabilir değil; CLAUDE.md bunu eşit gibi sunuyor.
15. **`question_number` denetlenebilir değil** — `question_bank`'ta sorgulanabilir kolon
    değil, `DIRECT_FIELDS`'ta olduğu için `pipeline_metadata`'ya da yazılmıyor; yalnız uuid5
    hash'inin içinde gömülü. `pipeline_metadata->>'question_number'` **sessizce NULL** döner
    (bu turda bir ölçümü bozdu).
16. **`created_by` 187.835 satırın 187.770'inde NULL** (65 dolu) — ingest provenance'ı yalnız
    `created_at` + metadata imzasıyla geri kazanılabiliyor.
17. **Eş zamanlı `in_progress` sınav oturumu kısıtı yok** — tek kullanıcı için aynı saniyede
    2 açık TYT oturumu yaratılabiliyor.
18. **3 asılı pytest süreci 4,5 saattir canlı** (PID 33384/27336/34840, 16:18–17:06'dan beri),
    hepsi `tests/api/test_me_endpoint.py` üzerinde. Deadlock `test_api_batch2.py`'ye özgü
    **değil**; `--timeout` ile koşulduğunda süreç sızmıyor.
19. **Kök `pyproject.toml` `timeout_func_only=true`, `backend/pytest.ini` `False`** — depo
    kökünden koşulduğunda aynı teardown deadlock'u pytest-timeout tarafından **hiç
    yakalanmaz**, sonsuza kadar asılı kalır.
20. **SMTP anahtar adı tutarsızlığı** — `startup_validator.py:158`, `validate_production_env.py:75`,
    `backup_database.py:234` **`SMTP_HOST`** okuyor; `email_util.py:32`, `kvkk_compliance.py:812`,
    `health_audit_service.py:755` **`SMTP_SERVER`** okuyor. `.env.production`'da yalnız
    `SMTP_HOST` tanımlı → o dosya yüklense **startup validator geçer, `send_email` yine
    sessizce False döner**. `SMTP_SERVER` ve `EMAIL_FROM` depodaki **hiçbir** `.env*` dosyasında yok.
21. **`api/auth.py:2279` (veli onayı e-postası)** aynı ölü `send_email`'i kullanıyor ve dönüş
    değerini **hiç kontrol etmiyor** — şifre sıfırlamanın aksine burada hiçbir fallback/log
    yok; bildirim tamamen sessizce kayboluyor.
22. **jsonl "77.336 clean" iddiasını tam karşılamıyor** — 77.336 kayıtta yalnız **75.725
    distinct metin** var (1.611 metin-düzeyi tekrar; en sık olanı 32 kez). Kimlik üçgeni
    `book|page|qnum` benzersiz olduğu için ingest bunları elemiyor.
23. **`question_bank`'ta 2026-05-12 tarihli 105.152 satırlık ikinci dev parti** (tablonun %56'sı)
    CLAUDE.md'nin "Database & Content" bölümünde **hiç geçmiyor**. "Üretimde ne var"
    sorusunun cevabını domine eden parti dokümantasyonda görünmez.

**Alet tuzakları (kural dosyasına aday):**

24. **`/openapi.json` bu depoda rota-varlığı için GEÇERSİZ ALET** — `backend/api/auth.py`'de
    en az 10 rota `include_in_schema=False`; `/api/v1/auth/login` spec'te **YOK** ama canlı
    trafik görüyor. Doğru alet: HTTP status probu (404 = yok, 401/403/422 = var).
25. **Minify edilmiş bundle'da yerel değişken adı aramak değersizdir** — dağıtım kontrolü
    **string literal** (onay metni, `aria-label`) veya **property** adıyla yapılmalı, ve
    commit'ten ÖNCE de var olan bir literal **kontrol kolu** olarak aranmalı.
26. **`docker logs --since 15:25`** (Z'siz) yerel saat sayılır → yanlış pencere. Konteyner
    logları **UTC**, host **UTC+3**.
27. **`git count-objects -v` ≠ `.git` dizini boyutu** — yalnız pack+loose nesneleri sayar;
    `.git/lfs`, index, logs, refs hariç. Bu turda bir skeptiği yanlış yöne götürdü.
28. **mtime bayatlık kanıtı değil** — `CLAUDE.md` disk mtime'ı 2026-07-28 02:19 olduğu halde
    son commit 23 May ve çalışma ağacı temiz (içerik değişmeden dosyaya dokunulmuş).
29. **MSYS yol dönüşümü** `/app/api/me.py` → `C:/Program Files/Git/app/api/me.py` yaptı ve
    yanlış "No such file" üretti → `MSYS_NO_PATHCONV=1` gerekli.
30. **bash `/tmp` ≠ node/python `/tmp`** (MSYS temp vs `C:\tmp`) — dosya üzerinden veri
    aktarımı sessizce düştü; stdin'e geçilerek çözüldü.

### G. Metodolojik ders — §13'e 3 yeni aday

**6. ADAY — ÖLÇÜMÜN KENDİSİ SİSTEMİ DEĞİŞTİRİYOR MU?**
`.claude/rules/audit-methodology.md` "Ölçüm aletini doğrula" der; bu vaka bir adım
ötesini gösteriyor: alet **doğruydu**, ama alet **sistemi değiştirdi**. Rapor 131 POST
atan bir paketi 3 kez koşturdu, bunu ölçtü, ve aynı belgede "salt okunur" yazdı — sonra
kendi yazdığı satırları "gerçek öğrenci trafiği" diye analiz etti.
**Kural:** yazma yüzeyi ölçülen bir aleti koşmadan önce *"bu, ölçmeye çalıştığım tabloya
yazar mı?"* sorusu sorulmalı; yazıyorsa **öncesi/sonrası snapshot** alınmalı ve rapora
"ölçümün kendi yan etkisi" satırı **zorunlu** eklenmeli.

**7. ADAY — ÖZET DE BİR ÖLÇÜMDÜR.**
Bu turda özet, raporun **kendisinden** 6 yerde saptı: paydayı küçülttü (1.393→1.223),
hedge'i düzleştirdi (3 payda → tek sayı), tarih kaydını düşürdü (27 May artefaktı → "gerçek"),
ve **raporda hiç geçmeyen bir iddia ekledi** (`pre-commit-check.py`). Sentez katmanı
kanıt üretmez, kanıt **taşır**.
**Kural:** özetteki her sayı rapordaki bir satıra `grep`'lenebilmeli; grep boş dönüyorsa
o cümle **ya rapora eklenir ya özetten çıkarılır**.

**8. ADAY — KARŞILAŞTIRMANIN AYNI ŞEYİ ÖLÇTÜĞÜNÜ KANITLA.**
"~450x yanlış" ve "%53 vs %39,74" — iki yanlış, aynı kökten: **karşılaştırılan iki değerin
aynı hedefi/metriği ölçtüğü doğrulanmadı**. Biri sığ `/health` ile derin `/health/detailed`'i,
diğeri `line` ile `dal-dahil`'i (ve 17 Mart ile 27 Mayıs'ı) kıyasladı.
**Kural:** `A vs B` yazmadan önce A'nın ve B'nin **hedefini, metriğini ve tarihini** ayrı
ayrı yaz. Üçü de eşleşmiyorsa bu bir karşılaştırma değil, bir **kategori hatası**dır.

> **Turun kendi öz-eleştirisi:** skeptik tur da iki kez kendi kuralını ihlal etti —
> (a) B1-b'de "örneklem yanlılığı **gerçek**" dedi; binom testi çürüttü (z=0,97, p=0,332;
> %7,0 değeri n=300 için %95 bandı [%3,08, %8,33] **içinde**) — sayı doğrulandı, o farkın
> **açıklaması** doğrulanmadı. (b) `.git` boyutunda farklı bir kümeyi ölçen aletle raporu
> haksız yere "yukarı yuvarlamış" diye suçladı. Aynı kural (`kök neden de bir ölçümdür`)
> bu depoda **dördüncü kez** aynı yerden kırıldı.

---

*Çürütme turu: 2026-07-30, aynı gün. 6 skeptik + 3 hakem turu, ~60 iddia.*
*Sonuç: 34 ayakta, 19 düzeltildi, 8 manşet çürütüldü, 7 doğrulanamadı.*
*Bu turda DB'ye yazma yapılmadı; yalnız `POST /api/v1/admin/content/questions` ve*
*`DELETE .../questions/{id}` probları hakem turunda 3'er kez çağrıldı (kalıcı etki: yok, bkz. F1/F2).*
