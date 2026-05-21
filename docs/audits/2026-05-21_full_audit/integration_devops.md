# KIRO2 Integration + DevOps Audit — 2026-05-21 Session 178

## Executive Summary

KIRO2 Docker-based stack, production-capable for 5–100 beta users ama 1K+ scale için ciddi gap'ler. CI/CD 10 workflow ile olgun ama K8s deploy aspirational. Monitoring stack (Grafana/Prometheus) production compose'a bağlı değil, alert pipeline işlevsiz.

**Toplam:** 5 P0 / 10 P1 / 10 P2 | **Production Readiness Score: 5.0/10**

---

## P0 — Beta-blocker

**I-P0-1: `.env.mvp.example` repository'de yok**
- `docker-compose.yml:5` setup template'i referans ediyor, dosya yok
- Yeni install fail eder
- Fix: Sanitized `.env.mvp.example` oluştur

**I-P0-2: CORS fallback hardcodes localhost**
- `backend/main.py:58` — ImportError fallback `allow_origins=["http://localhost:3000", "http://localhost:3001"]`
- Production domain'den tüm requestler reject olur (silent)
- Fix: Fallback'i kaldır veya `ALLOWED_ORIGINS` zorunlu kıl

**I-P0-3: Monitoring stack production compose'a bağlı değil**
- `monitoring/docker-compose.monitoring.yml` ayrı compose, farklı network
- Grafana password `teknofest2025` hardcoded
- Alertmanager `targets: []` — alert pipeline tetiklenmez
- Prometheus scrape config `backend1/2/3` hostnames eşleşmiyor (`kiro2-backend` çalışıyor)
- Fix: Monitoring stack'i ana compose'a entegre et veya prod K8s'e taşı

**I-P0-4: Redis `--maxmemory` ve eviction policy yok**
- `docker-compose.yml:49` — `redis-server --appendonly yes --save "60 1000"` (limitsiz RAM)
- Büyüme ile OOM kill veya silent fail
- Fix: `--maxmemory 512mb --maxmemory-policy allkeys-lru`

**I-P0-5: `celery-beat` healthcheck disabled**
- `docker-compose.yml:115` — `healthcheck: disable: true`
- Scheduled task crash silent
- Fix: Enable healthcheck (custom CMD veya `celery -A celery_worker beat --schedule`'a `--pidfile` ekle ve `cat /var/run/...`)

---

## P1 — Production-quality

**I-P1-1: Resource limits yok**
- 0 container'da `deploy.resources.limits` veya `mem_limit`
- Windows host'ta misbehaving Celery worker OOM
- Fix: backend `mem_limit: 1g`, celery `512m`, redis `256m` minimum

**I-P1-2: ORM Schema drift HIGH=203 baseline kabul edilmiş**
- `audit_orm_schema_drift.py --fail` SADECE growth'ı engelliyor
- 41 `inverse-rule-of-seven` aktif tablolarda → 22 tablo prod risk
- Fix: Dedicated migration sprint, özellikle `kiro2_learning_events` gibi hot tablolar

**I-P1-3: Dockerfile.minimal (prod) vs Dockerfile (full) divergence**
- Production compose `Dockerfile.minimal` (1 worker, pip)
- `Dockerfile` multi-stage 4 worker (KULLANILMIYOR)
- CI `docker build -t kiro2-scan:latest .` `-f` yok → full Dockerfile, prod minimal — image divergence
- Fix: Production'u `Dockerfile`'a taşı veya `Dockerfile.minimal`'ı sil

**I-P1-4: K8s deploy aspirational**
- `deploy.yml` placeholder domains (`staging.kiro2.example.com`, `kiro2.example.com`)
- `KUBE_CONFIG`, `PROD_KUBE_CONFIG` secret'lar listede ama K8s cluster yok
- `health-checks.yml` `api.kiro2.com` cron'u her 5dk Slack alert üretir (domain yok)
- Fix: K8s setup yap veya bu workflow'ları geçici olarak disable et

**I-P1-5: Log rotation yok**
- `main.py:29` `FileHandler("kiro2_backend.log")` rotation'sız
- 24/7 beta'da disk dolar
- Volume `/app/logs` mount ama log dosyası `/app/kiro2_backend.log` (path mismatch)
- Fix: `RotatingFileHandler` veya stdout-only + Docker log driver

**I-P1-6: VITE_DEMO_PASSWORD image layer'a baked**
- `frontend/Dockerfile:24` build arg → image history'de görünür
- `docker history` ile çıkarılabilir
- Fix: Demo password runtime env'den oku, image'a embed etme

**I-P1-7: External volumes undocumented**
- `redis-data` ve `turkiye_sinav_network` `external: true` ama pre-create scripti yok
- Yeni dev fresh install fail eder
- Fix: README'ye `docker volume create kiro2_redis-data && docker network create turkiye_sinav_network` ekle

**I-P1-8: mypy soft-fail**
- `quality-gate.yml:97` — `mypy . --ignore-missing-imports --no-strict-optional || true`
- Type error PR'ı bloklamıyor
- Fix: `|| true` kaldır, gerekirse `--ignore-modules` kullan

**I-P1-9: Turkish path drift baseline kabul (22 endpoint)**
- `/api/v1/ogretmen/*`, `/api/v1/veli/*` vb. — frontend 404 üretiyor
- `audit_path_drift.py --fail` SADECE growth'ı engelliyor
- Fix: Migration plan, English canonical'a geç + redirect middleware

**I-P1-10: Connection pool > DB max_connections**
- `database.py:153` — pool_size=50, max_overflow=100 (150 total)
- PostgreSQL default `max_connections=100`
- PgBouncer yok
- Beta için: `db_pool_size=15` `.env.mvp`'de ayarla

---

## P2 — Improvement

**I-P2-1: OpenTelemetry → Jaeger eksik** — `JaegerExporter` config var, Jaeger container yok
**I-P2-2: Grafana `:latest` tag** — non-reproducible build
**I-P2-3: Prometheus scrape config eşleşmiyor** — `backend1/2/3` hostname'leri (`kiro2-backend` çalışıyor)
**I-P2-4: `redis_cache.py` deprecated migration eksik** — kısmi geçiş, 66 dosya hala cache pattern
**I-P2-5: Frontend type defs manual** — `openapi-typescript` codegen yok
**I-P2-6: SSE rate-limit exemption explicit değil** — bağlantı cap yok
**I-P2-7: CDN yok `/static/crops`** — 87K image FastAPI StaticFiles'tan, 100+ concurrent için darboğaz
**I-P2-8: Celery worker = backend image** — gereksiz attack surface
**I-P2-9: Branch protection bilinmiyor** — GitHub settings audit edilmedi
**I-P2-10: pg_dump backup cadence yok** — manuel only, otomatik script yok

---

## Production Readiness Scorecard

| Domain | Score (0-10) | Notes |
|---|---|---|
| Docker stack | 5 | Beta-capable; no limits, no eviction |
| Backend-Frontend contract | 5 | Cookie auth OK; manual types; Turkish drift |
| Secrets management | 6 | Demo password leak; .env.mvp.example missing |
| CI/CD | 7 | 10 workflow + 7 AST lint; K8s aspirational |
| Database | 5 | 203 HIGH drift; pool > max_conn; backup eksik |
| Caching | 5 | Redis standalone OK; no maxmemory |
| Observability | 4 | structlog OK; Prometheus/Grafana detached |
| Monitoring | 3 | Alert rules var, Alertmanager target boş |
| Deployment | 4 | Local OK; K8s placeholder |
| Security | 7 | Comprehensive scanning; demo password issue |
| Performance | 5 | Async OK; 1 worker prod; no CDN |
| Documentation | 4 | CLAUDE.md good; no README/runbook |

**Overall: 5.0/10**

---

## Beta-launch Specific Risks

### 5–10 öğrenci (mevcut hedef)
**Çalışan:** Full auth, question bank, Golden Flows 164 PASS, Celery async
**Düzeltilmesi gerekenler (P0+P1 kritik):**
1. `.env.mvp.example` (I-P0-1) — kritik
2. CORS production domain (I-P0-2)
3. Redis maxmemory (I-P0-4)
4. celery-beat healthcheck (I-P0-5)
5. Volume creation docs (I-P1-7)
6. Log rotation (I-P1-5) — 1 hafta DEBUG'da disk dolar
7. `db_pool_size=15` (I-P1-10)

### 100–1000 öğrenci
1. PgBouncer
2. Nginx reverse proxy + static file serving
3. Dockerfile (full) → 4 worker
4. Prometheus + Grafana bağlantı + Alertmanager Slack
5. Automated pg_dump backup
6. ORM 41 inverse-rule-of-seven fix
7. Log rotation veya ELK
8. SSE withCredentials

### 10K öğrenci (scaling roadmap)
1. PostgreSQL read replica
2. CDN (Cloudflare R2, AWS S3+CF)
3. Redis Sentinel/Cluster HA
4. K8s deployment (deploy.yml complete)
5. Blue-green migration
6. PII encryption at rest (Fernet zorunlu)
7. Horizontal backend (osym_exam_engine Redis-backed)
8. Rate limit 10K tuning
9. OpenAPI → TypeScript codegen
