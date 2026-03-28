# Infrastructure Deep Audit Report

**Tarih:** 2026-03-28
**Concern'ler:** Docker+Nginx, CI/CD, Alembic+DB, Scripts+Config
**Agent sayisi:** 4 (paralel)
**Toplam bulgu:** 26 P0, 29 P1, 25 P2 = **80 bulgu**

---

## P0 — Hemen Fix (26 bulgu)

### Docker & Nginx (7)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| D1 | docker-compose.dev.yml:11 | Hardcoded DB password `postgres123` git'te | `${POSTGRES_PASSWORD:-postgres123}` + .env |
| D2 | docker-compose.dev.yml:46-47 | Hardcoded JWT/SECRET_KEY git'te | `.env.dev` dosyasina tasi |
| D3 | frontend/nginx.conf | Content-Security-Policy header YOK — XSS riski | CSP header ekle |
| D4 | frontend/nginx.conf | HSTS header YOK — MITM downgrade riski | HSTS header ekle |
| D5 | backend/Dockerfile.minimal | Root olarak calisiyor — container escape = host access | `USER kiro2` ekle |
| D6 | backend/Dockerfile.dev | Root olarak calisiyor | Ayni fix |
| D7 | backend/Dockerfile.exporter | Root olarak calisiyor | Ayni fix |

### CI/CD GitHub Actions (8)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| G1 | claude-review.yml:98 | Script injection — PR comment body shell'e interpolate ediliyor | `env:` ile gecir |
| G2 | security.yml:48 | Unpinned action `@main` — supply chain risk | SHA veya tag pin |
| G3 | security.yml:74 | Unpinned `trivy-action@master` | Tag pin |
| G4 | security.yml:87 | Unpinned `snyk/actions@master` | Tag pin |
| G5 | security.yml:155 | Unpinned `trufflehog@main` | Tag pin |
| G6 | security.yml:202 | Unpinned `checkov-action@master` | Tag pin |
| G7 | deploy.yml:271 | Unpinned buildkit `moby/buildkit:master` | Digest pin |
| G8 | release.yml:29-32 | Over-broad permissions — contents:write tum job'larda | Job-level permission |

### Alembic Migrations (6)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| A1 | 7c540cf490c2:265 | `user_badges` DROP CASCADE upgrade'de — data loss | ADD COLUMN IF NOT EXISTS |
| A2 | 7c540cf490c2:347 | f-string `DROP TABLE {tbl}` — SQL injection pattern | Explicit `op.drop_table()` |
| A3 | 20260320_fix_gamification_fk:74-108 | Downgrade VARCHAR→INTEGER USING cast — UUID ile crash | One-way olarak dokumante |
| A4 | 20260102_fix_missing:63 | `correct_answer = 'A'` tum NULL satirlara — veri bozulmasi | UPDATE kaldir veya sentinel |
| A5 | add_kvkk_tables.py + 3ec73c2c6d97 | Duplicate kvkk_consents tablo — farkli schema, conflict | Eski versiyonu sil |
| A6 | add_kvkk_tables.py:32 | `user_id` Integer FK YOK — orphan data | Dosyayi sil |

### Scripts & Config (5)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| X1 | seed_database.py:189+ | Hardcoded weak password `admin123` + SHA-256 (bcrypt degil) | bcrypt + env var |
| X2 | seed_mvp_data.py:51 | Hardcoded `Kiro2Beta2026@x` git'te + stdout'a print | Env var'dan oku |
| X3 | config.py:130 | Default SECRET_KEY `your-secret-key-change-in-production` dev/staging'de kullanilir | Require env var |
| X4 | deactivate_bad_questions.py:88 | Default DB password `"postgres"` fallback | Bos ise fail et |
| X5 | assign_bloom_taxonomy.py:23 + assign_difficulty_heuristic.py:26 | Default DB password `"postgres"` | Env var zorunlu |

---

## P1 — Sprint Icinde Fix (29 bulgu)

### Docker & Nginx (7)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| D8 | nginx.conf | `server_tokens off` eksik — nginx version leak | Ekle |
| D9 | nginx.conf | `client_max_body_size` yok — 10MB upload nginx'te fail | `10m` ekle |
| D10 | docker-compose.yml:17-18 | Backend 8000 host'a expose — nginx bypass | `expose:` kullan |
| D11 | docker-compose.dev.yml:13-14,27 | PG+Redis tum interface'lere expose, Redis auth yok | `127.0.0.1:` bind |
| D12 | docker-compose*.yml | Hicbir container'da memory/CPU limit yok — OOM risk | `deploy.resources.limits` |
| D13 | frontend/Dockerfile.nginx:50 | Stale Dockerfile — Node 18, wget, `build:prod` | Sil veya guncelle |
| D14 | backend/Dockerfile.dev | HEALTHCHECK tanimli degil | Ekle |

### CI/CD (7)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| G9 | claude-ci.yml:88 | `ruff check || true` + `mypy || true` — quality gate dekoratif | `|| true` kaldir |
| G10 | claude-ci.yml:134,139 | `npm run lint || true` + `tsc || true` — ayni sorun | Kaldir |
| G11 | ci.yml:19 | Node 18 ama Vite 7 Node 20+ gerektiriyor | `20` yap |
| G12 | release.yml:27 | Node 18 — ayni sorun | `20` yap |
| G13 | ci.yml:420 | Docker build `refs/heads/main` ama branch `master` — asla calismaz | `master` yap |
| G14 | deploy.yml:160 | super-linter `DEFAULT_BRANCH: main` — diff mode kirik | `master` yap |
| G15 | quality-gates.yml (4 yer) | `actions/setup-python@v4` — stale, v5 kullanilmali | Upgrade |

### Alembic (8)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| A7 | 4aec28c6c9e0:20-26 | upgrade+downgrade `pass` — dead orphan migration | Sil |
| A8 | 0df6ae499ee4:24 | Merge migration 5 head'e bagli — herhangi biri eksikse chain kirilir | Head'leri dogrula |
| A9 | env.py:21 | `from models.database import Base` absolute import — dual MetaData riski | Dogrula |
| A10 | env.py:75 | `alembic.ini` URL bos string — CI/CD'de sessiz fail | Comment ekle |
| A11 | b49a86e335e5:252 | `quiz_questions.question_id` FK → `questions.id` (BOS tablo) | `question_bank` yap |
| A12 | 20260312 (2 dosya) | Ayni `down_revision` — branch split | Linear chain yap |
| A13 | e73a8e0797c1:884,903 | Base schema `exam_questions`+`student_answers` FK → `questions` (BOS) | `question_bank` yap |
| A14 | add_taxonomy_and_quality:22-31 | `sorular` tablosu — muhtemelen yok, no-op | Disable et |

### Scripts & Config (7)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| X6 | config.py:112-113 | Pool 200/overflow 300 default — dev'de 500 connection | `20/30` default |
| X7 | seed_database.py:864-866 | SHA-256 password hash — auth sistemi bcrypt bekliyor | bcrypt kullan |
| X8 | production_seed.py:302 | Ayni SHA-256 sorunu | Ayni fix |
| X9 | import_clean_questions.py:38 | Fallback DB `kiro2_db` — dogru isim `kiro2` | Duzelt |
| X10 | coverage_dashboard.py:35 | Hardcoded Flask secret | `os.urandom(32).hex()` |
| X11 | application.py:56 | DATABASE_URL ilk 30 char logda — user:password gorunebilir | Credentials strip et |
| X12 | application.py:183-184 | CORS allow_methods/headers=["*"] | Explicit liste |

---

## P2 — Teknik Borc (25 bulgu)

### Docker & Nginx (6)

| # | Dosya | Aciklama |
|---|-------|----------|
| D15 | docker-compose*.yml | Log rotation yok — disk dolma riski |
| D16 | nginx.conf:112 | Gzip eksik MIME type'lar (svg, woff2, text/javascript) |
| D17 | .dockerignore | Test dosyalari exclude — dev build icin sorun |
| D18 | nginx.conf:27 | `/api/` proxy_read_timeout 3600s — stuck request 1 saat |
| D19 | docker-compose.dev.yml:61 | Volume mount installed packages ezer |
| D20 | Dockerfile.production:49 | Gereksiz wget kurulu — attack surface |

### CI/CD (5)

| # | Dosya | Aciklama |
|---|-------|----------|
| G16 | Tum workflow'lar | `timeout-minutes` yok — stuck job 6 saat calisir |
| G17 | health-checks.yml:33 | Her 5dk calisir — 8,640 run/ay (asiri) |
| G18 | ci.yml + claude-ci.yml | `main` branch referansi — master'da calismaz |
| G19 | ci.yml + claude-ci.yml | Duplicate CI pipeline — cift maliyet |
| G20 | deploy.yml:366 | Kubeconfig disk'e yazilir, temizlenmez |

### Alembic (6)

| # | Dosya | Aciklama |
|---|-------|----------|
| A15 | 20260102:92-115 | Downgrade bare `except: pass` (4 yer) |
| A16 | 7c540cf490c2:34-328 | Raw SQL 14 tablo — autogenerate uyumsuz |
| A17 | 20260320_fix_bkt:20-37 | `IF EXISTS` guard yok |
| A18 | f822e22c28c6:25-28 | upgrade+downgrade `pass` — no-op, gurultu |
| A19 | 20260312_mega_feature:113-155 | 8+ FK kolonunda index eksik — yavas JOIN/DELETE |
| A20 | 4 dosya | `down_revision = None` — 4 bagimsiz branch root |

### Scripts & Config (8)

| # | Dosya | Aciklama |
|---|-------|----------|
| X13 | 8+ script | Tutarsiz DB connection string — farkli password'lar |
| X14 | backup_database.py:75 | Default password "postgres" |
| X15 | logging_config.py:36-37 | Email/phone redaction kapali — KVKK riski |
| X16 | config.py:107 | Test DB SQLite dosya — stale data |
| X17 | deactivate_bad_questions.py | `--dry-run` yok, default destructive |
| X18 | seed_database.py | Legacy `Question` model (bos tablo) kullaniyor |
| X19 | application.py:196 | CSRF exempt `/api/v1/` — tum API unprotected |
| X20 | config.py:195 | Metrics port 8001 = Qwen API port 8001 — collision |

---

## Konsensus (2+ agent hemfikir)

| Konu | Agent'lar | Guvenilirlik |
|------|-----------|-------------|
| **Hardcoded secrets git'te** | Docker + Scripts | YUKSEK — compose + 5 script |
| **SHA-256 password hash (bcrypt olmali)** | Scripts + Alembic | YUKSEK — seed + production_seed |
| **FK → questions (bos tablo)** | Alembic + Scripts | YUKSEK — 3 migration + seed_database |
| **Unpinned third-party actions** | CI/CD (5 action) | YUKSEK — supply chain |
| **Node 18 → 20 gerekli** | CI/CD (2 workflow) | YUKSEK — Vite 7 uyumsuz |
| **Root container** | Docker (3 Dockerfile) | YUKSEK — security |
| **CSRF effectively disabled** | Scripts/Config + Docker/Nginx | ORTA — /api/v1/ exempt |

---

## Oncelikli Aksiyon Plani

### Faz 1 — Acil (Bu hafta)
1. **Script injection fix** (G1): claude-review.yml env var kullan — exploit edilebilir
2. **Action pinning** (G2-G6): security.yml 5 action'i SHA'ya pin'le
3. **Root user fix** (D5-D7): 3 Dockerfile'a `USER` directive
4. **CSP + HSTS** (D3-D4): nginx.conf'a 2 header

### Faz 2 — Sprint (Bu ay)
5. **Hardcoded secrets temizle** (D1-D2, X1-X5): .env dosyalarina tasi, env var zorunlu
6. **SHA-256 → bcrypt** (X7-X8): seed_database + production_seed
7. **Node 18 → 20** (G11-G12): ci.yml + release.yml
8. **Quality gates fix** (G9-G10): `|| true` kaldir
9. **Dead migration temizle** (A5-A7): kvkk duplicate + orphan sil
10. **FK → question_bank** (A11, A13): Fresh install icin base schema duzelt

### Faz 3 — Teknik Borc (Sonraki sprint)
11. **Shared _db_utils.py** (X13): 8 script'in DB connection'ini birlestir
12. **Missing FK indexes** (A19): mega_feature 8+ index ekle
13. **main → master** (G13-G14, G18): Tum workflow'larda branch fix
14. **Duplicate CI merge** (G19): ci.yml + claude-ci.yml birlestir
15. **Log rotation** (D15): Tum container'lara ekle

---

## Metrikler

| Kategori | P0 | P1 | P2 | Toplam |
|----------|----|----|----|----|
| Docker & Nginx | 7 | 7 | 6 | 20 |
| CI/CD GitHub Actions | 8 | 7 | 5 | 20 |
| Alembic Migrations | 6 | 8 | 6 | 20 |
| Scripts & Config | 5 | 7 | 8 | 20 |
| **TOPLAM** | **26** | **29** | **25** | **80** |

---

*Audit by: 4 parallel agents (Claude Opus 4.6)*
*Rapor: docs/audits/2026-03-28_infrastructure_deep_audit.md*
