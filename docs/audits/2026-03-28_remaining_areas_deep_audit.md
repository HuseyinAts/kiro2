# Remaining Areas Deep Audit Report

**Tarih:** 2026-03-28
**Concern'ler:** Root Pollution+Docs, Celery+Analytics+Middleware, Monitoring+MainAPI+Integrations, Gamification+Mobile+Destani
**Agent sayisi:** 4 (paralel)
**Toplam bulgu:** 9 P0, 33 P1, 30 P2 = **72 bulgu**

---

## P0 — Hemen Fix (9 bulgu)

### Root Pollution & Docs (2)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| R1 | cookies*.txt (root) | Gercek JWT token'lar git'te — session hijack riski | `.gitignore`'a ekle, git history'den temizle (BFG) |
| R2 | 210+ tmpclaude-* dizin (root) | Gecici dosyalar git-tracked — gereksiz repo sisman | `.gitignore`'a `tmpclaude-*` ekle, `git rm -r --cached` |

### Celery & Analytics & Middleware (3)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| C1 | backend/middleware/*.py (5 dosya) | 5 middleware class TANIMLI ama application.py'ye BAGLANMAMIS — dead code | Wire et veya sil |
| C2 | backend/celery_app.py | `task_routes` dict import sirasinda uzerine yaziliyor — 4 task modulu kayitsiz | Dict merge (`{**base, **override}`) |
| C3 | backend/middleware/ip_middleware.py | X-Forwarded-For IP spoofing — trusted proxy listesi YOK | `trusted_proxies` allowlist ekle |

### Monitoring & Main API & Integrations (2)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| MO1 | monitoring/grafana/provisioning | Grafana admin password hardcoded (`admin123`) | Env var'dan oku |
| MO2 | monitoring/prometheus/postgres_exporter | Postgres exporter `teknofest` DB'yi hedefliyor, `kiro2` degil | Connection string duzelt |

### Gamification & Mobile & Destani (2)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| G1 | backend/api/league_api.py + daily_quest_api.py + oba_seferleri_api.py | XP/puan veren endpoint'lerde rate limiting YOK — sinirsiz XP kazanimi | `@limiter.limit("5/minute")` ekle |
| G2 | frontend/src/sw.ts:317-345 | Service Worker icinde `localStorage` kullanimi — SW'da `localStorage` erisilemez, runtime crash | `IndexedDB` (idb-keyval) veya `CacheStorage` kullan |

---

## P1 — Sprint Icinde Fix (33 bulgu)

### Root Pollution & Docs (6)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| R3 | root (333 dosya) | 333 git-tracked dosya root'ta — proje yapisi kirli | Alt dizinlere tasi veya `.gitignore` |
| R4 | root (207 .py) | 207 Python dosyasi root'ta — backend/'a ait | Tasi veya arsivle |
| R5 | seed_database.py + seed_mvp_data.py | Hardcoded weak password'lar (admin123, Kiro2Beta2026@x) root script'lerde | Env var'dan oku |
| R6 | docs/ (stale) | Birden fazla obsolete doc — guncellenmemis referanslar | Audit + guncelle veya sil |
| R7 | root *.bat/*.sh | Windows batch + shell script'ler root'ta dagitik | scripts/ altina topla |
| R8 | root *.jsonl (>50MB) | Buyuk JSONL dosyalari git-tracked (LFS olmadan) | git-lfs track et |

### Celery & Analytics & Middleware (8)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| C4 | backend/celery_app.py | Celery beat schedule tanimli ama beat worker BASLATILMIYOR | Docker compose'a celery-beat service ekle |
| C5 | backend/tasks/ (4 modul) | 4 task modulu register edilmemis — import path eksik | `celery_app.conf.include` listesine ekle |
| C6 | backend/analytics/ (8 modul) | Analytics pipeline 8 modul — hicbiri API'ye baglanmamis | Router ekle veya dead code olarak arsivle |
| C7 | backend/middleware/cache_middleware.py | Cache middleware implement edilmis ama application.py'de YOK | Wire et veya sil |
| C8 | backend/middleware/metrics_middleware.py | Metrics middleware mevcut ama baglanmamis | Wire et veya sil |
| C9 | backend/middleware/logging_middleware.py | Structured logging middleware baglanmamis | Wire et |
| C10 | backend/tasks/analytics_tasks.py | Analytics Celery task'lari tanimli ama worker yok | Celery worker baslatma dokumante et |
| C11 | backend/analytics/dashboard_service.py | Analytics dashboard servisi API endpoint'i olmadan | Endpoint ekle veya kaldir |

### Monitoring & Main API & Integrations (10)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| MO3 | monitoring/prometheus/ | Duplicate Prometheus config — 2 farkli scrape config | Birlestir |
| MO4 | monitoring/alertmanager/ | AlertManager rule'lari teknofest referansi — stale branding | `kiro2` olarak guncelle |
| MO5 | monitoring/grafana/dashboards/ | Dashboard JSON'lari teknofest metrikleri icin — kiro2 metrikleri eksik | Guncelle |
| MO6 | backend/api/ (2 orphan router) | 2 API router dosyasi register edilmemis — endpoint'ler erisilemez | Include et veya sil |
| MO7 | backend/analytics/ | Analytics moduller API'ye baglanmamis — dead code | Router bagla veya arsivle |
| MO8 | alembic/versions/ | Algorithm migration'lar (BKT, FSRS tablolari) Alembic dosyasi olarak MEVCUT DEGIL | Migration olustur veya dokumante et |
| MO9 | monitoring/docker-compose.monitoring.yml | Monitoring stack compose'u ana compose'dan ayri — entegrasyon belirsiz | Ana compose'a merge veya README ekle |
| MO10 | backend/api/integration_*.py | External integration endpoint'leri (Zoom, Google Classroom) stub | Stub olarak label'la veya kaldir |
| MO11 | monitoring/grafana/ | Grafana provisioning data source URL localhost — Docker icinden erisilemez | Docker network hostname kullan |
| MO12 | backend/core/telemetry.py | OpenTelemetry setup mevcut ama application.py'de devre disi | Enable et veya kaldir |

### Gamification & Mobile & Destani (9)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| G3 | mobile/push_notification_system.py:284-288 | SQLite CREATE TABLE icinde MySQL-style INDEX syntax — crash | Ayri CREATE INDEX statement kullan |
| G4 | frontend/public/manifest.json:14-72 | Icon type `image/png` ama gercek dosyalar SVG — PWA install bozuk | PNG olustur veya type'i `image/svg+xml` yap |
| G5 | frontend/public/manifest.json:14 | `/icons/icon-192.png` path yok, dosyalar `/images/` altinda | Path duzelt |
| G6 | backend/api/pwa_sync_api.py:40-91 | 4 PWA sync endpoint tamamen stub — veri sync olmuyor | Gercek implementasyon yaz |
| G7 | mobile/*.py (5 dosya) | Tum mobile/ dizini spec/mock — prod kullanilabilir degil | `docs/specs/mobile/`'a tasi |
| G8 | frontend/package.json | three.js + @react-three (1.5MB+) yuklu ama 0 import — bundle bloat | `npm uninstall three @react-three/fiber @react-three/drei` |
| G9 | frontend/src/sw.ts:277 | `syncExamResults()` URL `/api/sync/exam-results` — v1 prefix eksik, endpoint ismi yanlis | `/api/v1/sync/exam-sessions` yap |
| G10 | frontend/src/sw.ts:299 | `syncLearningAnalytics()` URL `/api/sync/analytics` — backend'de mevcut degil, 404 | Backend'e ekle veya SW'dan kaldir |
| G11 | backend/api/duel_api.py | Duel matchmaking kuyrugunda TTL yok — oyuncu sonsuza kadar bekler | Redis key TTL (60s) ekle |

---

## P2 — Teknik Borc (30 bulgu)

### Root Pollution & Docs (9)

| # | Dosya | Aciklama |
|---|-------|----------|
| R9 | root *.py (207 dosya) | Pipeline/utility script'ler root'ta — dizin yapisi kirli |
| R10 | root *.log | Log dosyalari git-tracked |
| R11 | root __pycache__/ | Cache dizinleri git'te |
| R12 | docs/brainstorms/ | 10+ brainstorm raporu — guncelligi belirsiz |
| R13 | docs/research/ | Arastirma raporlari — referans olarak saklanabilir |
| R14 | root backup_*.py | Backup script'leri root'ta dagitik |
| R15 | root analyze_*.py | Analiz script'leri duzenli dizine tasinmali |
| R16 | root test_*.py (root) | Test dosyalari backend/tests/ disinda |
| R17 | .claude/sessions/ | Session dosyalari buyuyebilir — temizleme politikasi yok |

### Celery & Analytics & Middleware (7)

| # | Dosya | Aciklama |
|---|-------|----------|
| C12 | backend/celery_app.py | Celery broker Redis URL hardcoded |
| C13 | backend/tasks/cleanup_tasks.py | Temizlik task'lari (stale session, expired token) tanimli ama calismaz |
| C14 | backend/analytics/event_tracker.py | Event tracking mevcut ama frontend SDK entegrasyonu yok |
| C15 | backend/analytics/report_generator.py | Rapor uretici — cikti formati belirsiz |
| C16 | backend/middleware/compression_middleware.py | Gzip middleware — nginx zaten yapiyor, duplicate |
| C17 | backend/analytics/funnel_analyzer.py | Funnel analizi — veri kaynagi belirsiz |
| C18 | backend/tasks/email_tasks.py | Email task — SMTP config yok |

### Monitoring & Main API & Integrations (8)

| # | Dosya | Aciklama |
|---|-------|----------|
| MO13 | monitoring/ (tum dizin) | Monitoring stack hicbir zaman production'da calistirilmamis |
| MO14 | monitoring/alertmanager/rules/ | Alert rule'lari generic — KIRO2 spesifik metrik yok |
| MO15 | backend/api/webhook_api.py | Webhook endpoint — hicbir external service baglanmamis |
| MO16 | backend/core/feature_flags.py | Feature flag sistemi — sadece in-memory, persist yok |
| MO17 | backend/api/admin_api.py | Admin panel endpoint'leri — frontend karsiligi belirsiz |
| MO18 | monitoring/docker-compose.monitoring.yml | Monitoring compose'da volume path'ler hardcoded |
| MO19 | backend/core/health_check.py | Health check Elasticsearch timeout — ES kullanilmiyor |
| MO20 | backend/api/export_api.py | Data export endpoint — KVKK uyumlulugu dogrulanmamis |

### Gamification & Mobile & Destani (6)

| # | Dosya | Aciklama |
|---|-------|----------|
| G12 | backend/api/duel_api.py | Duel reconnect/timeout yok — baglanti kopmasinda oyun askida |
| G13 | backend/api/offline_sync_api.py:137 | Lazy import — servis yoksa belirsiz 503 |
| G14 | frontend/src/features/realm/RealmMap.tsx:136 | `Math.random()` render icinde — her re-render'da yildizlar degisir |
| G15 | frontend/src/sw.ts:162-172 | `skipWaiting()` kayitsiz sartsiz — aktif tab'lardaki islemleri bozabilir |
| G16 | backend/api/cozum_duellosu_api.py:29 | XP sabitleri hardcoded — ayarlanabilir degil |
| G17 | mobile/push_notification_system.py:246 | Karisik sync/async pattern — `sqlite3.connect` sync ama class async |

---

## Konsensus (2+ agent hemfikir)

| Konu | Agent'lar | Guvenilirlik |
|------|-----------|-------------|
| **Dead code yaygin (middleware, analytics, monitoring)** | Celery+Middleware + Monitoring | YUKSEK — 5 middleware + 8 analytics + monitoring stack |
| **Hardcoded credentials** | Root Pollution + Monitoring | YUKSEK — cookies.txt JWT, Grafana admin123, seed passwords |
| **Stale "teknofest" branding** | Monitoring + Root Pollution | YUKSEK — Prometheus, AlertManager, Grafana hepsi eski isim |
| **Celery configured but not running** | Celery + Monitoring | YUKSEK — task'lar tanimli, worker/beat baslatilmiyor |
| **Mobile/PWA stub durumunda** | Gamification+Mobile (pwa_sync stub) + Celery (analytics disconnected) | ORTA — frontend SW mevcut ama backend entegrasyonu eksik |
| **Rate limiting eksik (XP abuse)** | Gamification + Backend audit (S1-S5 auth) | ORTA — gamification + genel API rate limit yetersiz |

---

## Oncelikli Aksiyon Plani

### Faz 1 — Acil (Bu hafta)
1. **cookies*.txt temizle** (R1): JWT token'lar git'ten sil, BFG ile history temizle
2. **SW localStorage fix** (G2): IndexedDB'ye gecir — crash onleme
3. **XP rate limiting** (G1): 5 endpoint'e `@limiter.limit()` ekle
4. **Middleware wire veya sil** (C1): 5 dead middleware karari ver
5. **IP spoofing fix** (C3): trusted proxy allowlist

### Faz 2 — Sprint (Bu ay)
6. **Root pollution temizle** (R3-R4): 207 .py + 333 dosya organize et
7. **Celery worker baslat** (C4-C5): docker-compose'a service ekle, task'lari register et
8. **Grafana/Prometheus fix** (MO1-MO5): teknofest→kiro2, hardcoded cred kaldir
9. **PWA manifest fix** (G4-G5): Icon path + type duzelt
10. **three.js kaldir** (G8): 1.5MB+ bundle tasarrufu

### Faz 3 — Teknik Borc (Sonraki sprint)
11. **Analytics pipeline wire** (C6, C11): 8 modul API'ye bagla veya arsivle
12. **mobile/ dizini tasi** (G7): docs/specs/mobile/ altina
13. **Monitoring stack test** (MO13): Docker'da calistir, dashboard'lari dogrula
14. **SW sync URL fix** (G9-G10): Endpoint path'leri backend ile sync et
15. **tmpclaude-* temizle** (R2): .gitignore + git rm cached

---

## Metrikler

| Kategori | P0 | P1 | P2 | Toplam |
|----------|----|----|----|--------|
| Root Pollution & Docs | 2 | 6 | 9 | 17 |
| Celery & Analytics & Middleware | 3 | 8 | 7 | 18 |
| Monitoring & Main API & Integrations | 2 | 10 | 8 | 20 |
| Gamification & Mobile & Destani | 2 | 9 | 6 | 17 |
| **TOPLAM** | **9** | **33** | **30** | **72** |

---

## Pozitif Bulgular

- Gamification API'ler calisiyor — 7 router register edilmis, auth mevcut, DB migration tamamlanmis
- Duel SSE stream implement edilmis (Redis pub/sub)
- KIRO Destani frontend component'leri (RealmMap, NPCDialog, ChemEquilibrium) calisir durumda
- Bilge Alp NPC backend SSE streaming + auth aktif
- Service Worker Workbox ile iyi yapilandirilmis (NetworkFirst/CacheFirst/StaleWhileRevalidate)
- offline_sync_api.py 3 gercek endpoint (sync-package, sync-results, sync-status)
- Session 111 F0-F6 social features tamamen entegre (20 model, 45 endpoint, 77 test PASS)

---

*Audit by: 4 parallel agents (Claude Opus 4.6)*
*Rapor: docs/audits/2026-03-28_remaining_areas_deep_audit.md*
