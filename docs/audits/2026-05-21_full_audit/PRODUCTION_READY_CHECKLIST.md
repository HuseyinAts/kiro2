# KIRO2 Production-Ready Checklist — 2026-05-21 (Sentez)

## Genel Bakış

3 paralel audit (Backend + Frontend + Integration/DevOps) sonucu sentez:

| Kategori | Backend | Frontend | Integration | **TOPLAM** |
|---|---|---|---|---|
| 🔴 P0 (beta blocker) | 5 | 2 | 5 | **12** |
| 🟡 P1 (production quality) | 8 | 5 | 10 | **23** |
| 🟢 P2 (improvement) | 6 | 11 | 10 | **27** |
| Toplam | 19 | 18 | 25 | **62** |

**Production Readiness Score:**
- Backend: 6.5/10 (algoritmalar + Curator UI güçlü, auth/middleware sorunları)
- Frontend: 7.0/10 (modern stack, dual route + SSE bug + monolithic page)
- Integration/DevOps: 5.0/10 (CI/CD olgun, monitoring/deployment aspirational)
- **Genel: 6.2/10** — 5-10 öğrenci beta-capable, 100+ için P0+P1 fix gerekli

---

## 🔴 P0 — Beta-Blocker (12 item, sıralı öncelik)

### Auth / Security (4 item — en kritik)

1. **[B-P0-1]** `api/soru_bankasi.py:244,459,492` — 3 endpoint auth eksik (anonim IDOR)
   - **Effort:** 30 dk | **Risk:** YKS soru bankası leak
2. **[B-P0-3]** `seed_admin.py:84` — Hardcoded `Admin123!` password git'te
   - **Effort:** 15 dk | **Risk:** Repo erişiminde admin compromise
3. **[B-P0-4]** 53+ quality script — `postgres:1470` DSN fallback
   - **Effort:** 1 saat | **Risk:** DB password ifşası
4. **[F-P0-1]** `frontend/services/chatService.ts:108` — SSE missing `credentials: 'include'`
   - **Effort:** 5 dk | **Risk:** Production'da chat 401 silently

### Middleware Pattern (2 item — runtime errors)

5. **[B-P0-2]** `core/api_optimizer.py:131` — Middleware `raise HTTPException` → 500
   - **Effort:** 15 dk | **Risk:** Rate limit aşımı 500 olarak ulaşır
6. **[B-P0-5]** `core/auth_rate_limiting.py:155,183` — Tutarsız HTTPException pattern
   - **Effort:** 45 dk | **Risk:** Caller doğrudan çağırırsa crash

### Frontend Routing (1 item)

7. **[F-P0-2]** Dual parent dashboard routes + eager ParentDashboard
   - `/veli-takip` + `/parent-new` + `/parent/dashboard` koexist; path-naming rule ihlali
   - **Effort:** 30 dk | **Risk:** UX confusion + bundle bloat

### Infrastructure (5 item — install/runtime)

8. **[I-P0-1]** `.env.mvp.example` repository'de yok → yeni install fail
   - **Effort:** 20 dk | **Risk:** New environment setup imkansız
9. **[I-P0-2]** `backend/main.py:58` — CORS fallback localhost-only
   - **Effort:** 10 dk | **Risk:** Production domain'den silent reject
10. **[I-P0-4]** Redis `--maxmemory` ve eviction yok → unbounded RAM
    - **Effort:** 5 dk | **Risk:** OOM kill production
11. **[I-P0-5]** `celery-beat` healthcheck disabled → silent failure
    - **Effort:** 30 dk | **Risk:** Scheduled job crash undetected
12. **[I-P0-3]** Monitoring stack disconnected, Grafana `teknofest2025` password
    - **Effort:** 2 saat | **Risk:** Production blind (no metrics, no alerts)

---

## 🟡 P1 — Production-Quality (23 item, kategorize)

### Backend (8)

- **[B-P1-1]** `enhanced_user_management_api.py:64` — Deprecated `KullaniciServisi` in-memory üretimde (30 dk)
- **[B-P1-2]** Migration multi-head verify + merge (15 dk)
- **[B-P1-3]** `api_optimizer.py:124` — `X-User-ID` header trust → rate limit bypass (20 dk)
- **[B-P1-4]** `soru_bankasi_service.py:20` — Legacy enum import (10 dk)
- **[B-P1-5]** TR-named files audit (`veli.py`, `ogretmen.py`) auth pattern (1 saat)
- **[B-P1-6]** `bkt_service.py:get_params()` — None subject_slug defensive guard (5 dk)
- **[B-P1-7]** `irt_model.py` — Empty list edge case (15 dk)
- **[B-P1-8]** `question_bank.py` ORM — `QuestionDifficultyLevel` enum case verify (15 dk)

### Frontend (5)

- **[F-P1-1]** `package.json:32` — `react-query: "^3.39.3"` → pin `"3.39.3"` (1 dk)
- **[F-P1-2]** 341 `any` occurrences — production'da ~150-180 (sprint)
- **[F-P1-3]** `authStore.ts:319-327` — `isAuthenticated` persist → stale auth flash (10 dk)
- **[F-P1-4]** `ModernLearningPathPage.tsx` 1,165 satır → split (4 saat)
- **[F-P1-5]** StudyRooms orphaned components → delete or wire (1 saat)

### Integration/DevOps (10)

- **[I-P1-1]** Container resource limits ekle (30 dk)
- **[I-P1-2]** ORM drift 203 HIGH sprint (sprint)
- **[I-P1-3]** Dockerfile.minimal → Dockerfile (full multi-stage) (1 saat)
- **[I-P1-4]** K8s deploy.yml gerçekleştir veya disable (sprint)
- **[I-P1-5]** Log rotation `RotatingFileHandler` (15 dk)
- **[I-P1-6]** VITE_DEMO_PASSWORD runtime'a taşı (30 dk)
- **[I-P1-7]** External volumes setup docs (10 dk)
- **[I-P1-8]** mypy `|| true` kaldır (5 dk + fix gerekli)
- **[I-P1-9]** Turkish path drift migration plan (sprint)
- **[I-P1-10]** `db_pool_size=15` `.env.mvp`'de (5 dk)

---

## 🟢 P2 — Improvement (27 item — defer to backlog)

Detaylı listeler:
- Backend: `backend.md` — test coverage %53→80, BKT/IRT parametrik test, Phase 7 GEMINI_API_KEY check vb.
- Frontend: `frontend.md` — TanStack Query v5 migration, OSB DB sync, NFC normalization, `apiHelpers` dual wrapper, PWA start_url vb.
- Integration: `integration_devops.md` — OTel Jaeger, Grafana pin, CDN, automated backup, codegen vb.

---

## 🌐 Cross-Cutting Concerns (3 audit'ten ortak temalar)

### 1. Auth Hardening Sprint (P0)
Backend (3 endpoint auth) + Frontend (SSE credentials) + Integration (.env.mvp.example) → tek koordineli sprint:
- B-P0-1, B-P0-3, B-P0-4, F-P0-1, I-P0-1, I-P0-2 → 1 gün

### 2. Middleware Pattern Cleanup
2 middleware HTTPException ihlali → çapraz lesson aktif:
- B-P0-2, B-P0-5 → middleware sınıfları audit (.claude/rules/middleware.md)

### 3. Monitoring & Observability
3 farklı bulgu aynı root cause:
- I-P0-3 (Grafana/Prometheus disconnect)
- I-P1-5 (log rotation)
- I-P2-1 (OTel Jaeger)
- Beta 100+ için zorunlu

### 4. Type / Schema Consistency
- Frontend manual type defs (I-P2-5)
- Backend ORM drift HIGH=203 (B-P1-2, I-P1-2)
- Frontend `any` sprawl (F-P1-2)
- → OpenAPI codegen pipeline gelecek sprint için bütünsel çözüm

### 5. Dockerfile Divergence
- Production `Dockerfile.minimal` (1 worker)
- CI build `Dockerfile` (full)
- → "Works in CI, broken in prod" risk

---

## 🚀 Beta-Launch Sprint Plan (1-2 gün)

**Day 1: Auth + Security (3 saat)**
1. ✅ B-P0-1 soru_bankasi auth (30dk)
2. ✅ B-P0-3 seed_admin env var (15dk)
3. ✅ B-P0-4 script DSN sweep (1 saat)
4. ✅ F-P0-1 chatService SSE credentials (5dk)
5. ✅ I-P0-2 CORS fallback (10dk)
6. ✅ I-P0-1 .env.mvp.example (20dk)

**Day 1: Middleware + Infra (1.5 saat)**
7. ✅ B-P0-2 api_optimizer middleware (15dk)
8. ✅ B-P0-5 auth_rate_limiting refactor (45dk)
9. ✅ I-P0-4 Redis maxmemory (5dk)
10. ✅ I-P0-5 celery-beat healthcheck (30dk)
11. ✅ I-P0-3 Monitoring stack connect (2 saat)

**Day 1: Frontend (45dk)**
12. ✅ F-P0-2 Dual parent routes consolidate (30dk)

**Day 2: P1 critical (4 saat)**
- B-P1-1 KullaniciServisi remove
- B-P1-2 Migration head verify
- F-P1-1 react-query pin
- F-P1-3 authStore persist clean
- I-P1-1 Resource limits
- I-P1-5 Log rotation
- I-P1-10 db_pool_size

**Day 2 sonu:** **Beta-ready** (P0 = 0, kritik P1 = 0)

---

## 📊 100+ Öğrenci Hazırlığı (Hafta 2-4)

**P1 kalanlar (~6 saat sprint):**
- I-P1-3 Dockerfile full (4 worker)
- I-P1-2 ORM 41 inverse-rule fix
- I-P1-4 K8s gerçekleştir
- F-P1-4 ModernLearningPathPage split

**Yeni infra:**
- PgBouncer (connection pool)
- Nginx reverse proxy + `/static/crops`
- Alertmanager Slack
- Automated pg_dump (cron)
- ELK / structured logging shipping

---

## 🌍 10K Öğrenci Roadmap (Q3-Q4 2026)

1. PostgreSQL read replica
2. CDN (Cloudflare R2)
3. Redis Sentinel/Cluster
4. K8s production cluster
5. Blue-green migration patterns
6. PII Fernet encryption zorunlu
7. Backend horizontal scale (exam session → Redis)
8. Rate limit 10K tuning
9. OpenAPI → TypeScript codegen
10. Load testing (k6/Locust) baseline

---

## 📁 Detay Raporlar

- [backend.md](./backend.md) — Backend findings (19 item)
- [frontend.md](./frontend.md) — Frontend findings (18 item)
- [integration_devops.md](./integration_devops.md) — Integration findings (25 item)

## 🎯 Net Yargı

KIRO2 **5-10 öğrenci private beta için hazır** (Curator UI canlı, v_safe_for_beta=12,362 soru, Golden Flow 164 PASS). **12 P0 finding fix edilirse 1 hafta içinde production-ready private beta** mümkün. **100+ öğrenci için P1 sprint gerekli**. **10K öğrenci için scaling roadmap** Q3-Q4 2026'ya planlanmalı.

**Audit toplam efor (P0 fix):** ~6 saat | **P1 sprint:** ~6-8 saat | **Net beta-launch hazırlık:** 1-2 gün
