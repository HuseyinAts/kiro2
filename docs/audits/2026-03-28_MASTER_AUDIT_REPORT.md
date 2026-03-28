# KIRO2 Master Audit Report — Full Project Deep Audit

**Tarih:** 2026-03-28
**Kapsam:** TUM PROJE (backend, frontend, infrastructure, data & algorithms, remaining areas)
**Toplam Agent:** 20 paralel agent (5 faz x 4 agent)
**Toplam Bulgu:** 75 P0 + 132 P1 + 161 P2 = **368 bulgu**

---

## Ozet Tablo

| Faz | Kapsam | P0 | P1 | P2 | Toplam |
|-----|--------|----|----|----|----|
| 1. Backend | Security+Auth, Models+Schemas, Services+Algorithms, NLP+Tests | 19 | 27 | 30 | 76 |
| 2. Frontend | Security+Auth, Components+UI, Hooks+State+Utils, Performance+Build | 6 | 20 | 40 | 66 |
| 3. Infrastructure | Docker+Nginx, CI/CD, Alembic+DB, Scripts+Config | 26 | 29 | 25 | 80 |
| 4. Data & Algorithms | Orchestrator, IRT/FSRS/BKT/ZPD, d-dataset, Embedding+Vector | 15 | 23 | 36 | 74 |
| 5. Remaining Areas | Root Pollution, Celery+Middleware, Monitoring, Gamification+Mobile+Destani | 9 | 33 | 30 | 72 |
| **TOPLAM** | | **75** | **132** | **161** | **368** |

---

# BOLUM 1: TUM P0 BULGULARI (75)

## 1.1 Security & Auth Bypass (14 bulgu)

| # | Kaynak | Dosya:Satir | Aciklama | Fix |
|---|--------|-------------|----------|-----|
| S1 | Backend | api/celery_tasks_api.py:98-138 | Auth bypass — task cancel/active/stats unauthenticated | `Depends(get_current_user)` + `require_role("ADMIN")` |
| S2 | Backend | api/team_challenges_api.py:29,45,63 | Auth bypass + IDOR — user_id plain param, impersonation | `Depends(get_current_user)` ile degistir |
| S3 | Backend | api/osym_questions_api.py:1-210 | Auth bypass — 77K soru+cevap unauthenticated | `Depends(get_current_user)` tum endpoint'lere |
| S4 | Backend | api/wave2b_quality_routes.py:163,213,279 | Auth bypass — AI evaluate/batch/bertscore unprotected | Auth dependency ekle |
| S5 | Backend | api/osym_inspired_routes.py:21 | Auth bypass — AI question generation unprotected (API maliyet riski) | Auth + rate limiting |
| S6 | Infra | docker-compose.dev.yml:11 | Hardcoded DB password `postgres123` git'te | `${POSTGRES_PASSWORD:-postgres123}` + .env |
| S7 | Infra | docker-compose.dev.yml:46-47 | Hardcoded JWT/SECRET_KEY git'te | `.env.dev` dosyasina tasi |
| S8 | Infra | seed_database.py:189+ | Hardcoded weak password `admin123` + SHA-256 (bcrypt degil) | bcrypt + env var |
| S9 | Infra | seed_mvp_data.py:51 | Hardcoded `Kiro2Beta2026@x` git'te + stdout'a print | Env var'dan oku |
| S10 | Infra | config.py:130 | Default SECRET_KEY `your-secret-key-change-in-production` | Require env var |
| S11 | Infra | deactivate_bad_questions.py:88 | Default DB password `"postgres"` fallback | Bos ise fail et |
| S12 | Infra | assign_bloom_taxonomy.py:23 + assign_difficulty_heuristic.py:26 | Default DB password `"postgres"` | Env var zorunlu |
| S13 | Remaining | cookies*.txt (root) | Gercek JWT token'lar git'te — session hijack riski | `.gitignore` + BFG history temizle |
| S14 | Remaining | monitoring/grafana/provisioning | Grafana admin password hardcoded (`admin123`) | Env var'dan oku |

## 1.2 CI/CD & Container Security (15 bulgu)

| # | Kaynak | Dosya:Satir | Aciklama | Fix |
|---|--------|-------------|----------|-----|
| CI1 | Infra | claude-review.yml:98 | Script injection — PR comment body shell'e interpolate | `env:` ile gecir |
| CI2 | Infra | security.yml:48 | Unpinned action `@main` — supply chain risk | SHA pin |
| CI3 | Infra | security.yml:74 | Unpinned `trivy-action@master` | Tag pin |
| CI4 | Infra | security.yml:87 | Unpinned `snyk/actions@master` | Tag pin |
| CI5 | Infra | security.yml:155 | Unpinned `trufflehog@main` | Tag pin |
| CI6 | Infra | security.yml:202 | Unpinned `checkov-action@master` | Tag pin |
| CI7 | Infra | deploy.yml:271 | Unpinned buildkit `moby/buildkit:master` | Digest pin |
| CI8 | Infra | release.yml:29-32 | Over-broad permissions — contents:write tum job'larda | Job-level permission |
| CI9 | Infra | frontend/nginx.conf | Content-Security-Policy header YOK — XSS riski | CSP header ekle |
| CI10 | Infra | frontend/nginx.conf | HSTS header YOK — MITM downgrade riski | HSTS header ekle |
| CI11 | Infra | backend/Dockerfile.minimal | Root olarak calisiyor — container escape = host access | `USER kiro2` ekle |
| CI12 | Infra | backend/Dockerfile.dev | Root olarak calisiyor | Ayni fix |
| CI13 | Infra | backend/Dockerfile.exporter | Root olarak calisiyor | Ayni fix |
| CI14 | Remaining | 210+ tmpclaude-* dizin (root) | Gecici dosyalar git-tracked | `.gitignore` + `git rm -r --cached` |
| CI15 | Remaining | backend/middleware/ip_middleware.py | X-Forwarded-For IP spoofing — trusted proxy listesi YOK | `trusted_proxies` allowlist ekle |

## 1.3 Database & Migration Risks (6 bulgu)

| # | Kaynak | Dosya:Satir | Aciklama | Fix |
|---|--------|-------------|----------|-----|
| DB1 | Infra | 7c540cf490c2:265 | `user_badges` DROP CASCADE upgrade'de — data loss | ADD COLUMN IF NOT EXISTS |
| DB2 | Infra | 7c540cf490c2:347 | f-string `DROP TABLE {tbl}` — SQL injection pattern | Explicit `op.drop_table()` |
| DB3 | Infra | 20260320_fix_gamification_fk:74-108 | Downgrade VARCHAR→INTEGER USING cast — UUID ile crash | One-way olarak dokumante |
| DB4 | Infra | 20260102_fix_missing:63 | `correct_answer = 'A'` tum NULL satirlara — veri bozulmasi | UPDATE kaldir veya sentinel |
| DB5 | Infra | add_kvkk_tables.py + 3ec73c2c6d97 | Duplicate kvkk_consents tablo — farkli schema, conflict | Eski versiyonu sil |
| DB6 | Infra | add_kvkk_tables.py:32 | `user_id` Integer FK YOK — orphan data | Dosyayi sil |

## 1.4 Backend Models & Services (8 bulgu)

| # | Kaynak | Dosya:Satir | Aciklama | Fix |
|---|--------|-------------|----------|-----|
| BM1 | Backend | models/content_db.py:33 | Legacy `Question` model hala tanimli ve export ediliyor | `__all__`'dan cikar |
| BM2 | Backend | models/exam_db.py:116,152 | `ExamQuestion.question_id` ve `StudentAnswer.question_id` FK constraint YOK | `ForeignKey("question_bank.id")` + migration |
| BM3 | Backend | models/osym_question.py:162 | `exam_session_id` Integer FK ama `exam_sessions.id` String (UUID) — tip uyumsuzlugu | `Column(String, ForeignKey(...))` |
| BM4 | Backend | algorithms/irt_model.py:21-27 | Broken import — `from core.irt_validators` ModuleNotFoundError | Relative import |
| BM5 | Backend | algorithms/irt_morfoloji_service.py:16 | Broken import — `from core.turkish_nlp_service` | Ayni fix |
| BM6 | Backend | algorithms/cultural_adaptation_engine.py:21 | `from hijri_converter import Gregorian` try/except YOK — ImportError crash | try/except wrap |
| BM7 | Backend | services/cat_session.py:631-650 | N+1 INSERT — 20 soruluk CAT icin 20 ayri DB round-trip | `executemany` veya multi-row INSERT |
| BM8 | Backend | services/dag_service.py:158-168 | Cartesian join — 77K question x sessions = milyonlarca satir | `DISTINCT ON` veya rewrite |

## 1.5 NLP & Encoding (6 bulgu)

| # | Kaynak | Dosya:Satir | Aciklama | Fix |
|---|--------|-------------|----------|-----|
| NL1 | Backend | core/encoding.py:152 | `normalize_turkish_text()` bare `.lower()` — I→i (YANLIS) | `normalize_tr()` kullan |
| NL2 | Backend | tests/test_exam_answer_tracking.py:88 | Legacy `Question` import — bos tablo | `QuestionBankItem` |
| NL3 | Backend | tests/slow/test_soru_bankasi_service.py:15 | Legacy `Question` import | `QuestionBankItem` |
| NL4 | Backend | tests/integration/test_end_to_end_platform.py:31 | Legacy `Question` import | `QuestionBankItem` |
| NL5 | Backend | tests/slow/test_turkish_morphology_irt_comprehensive.py:22 | Legacy `Question` import | `QuestionBankItem` |
| NL6 | Backend | tests/integration/test_end_to_end_platform.py:42,52 | Mojibake encoding bozulmasi — `"sinav"` UTF-8 NFC ile yeniden kaydet |

## 1.6 Frontend Critical (6 bulgu)

| # | Kaynak | Dosya:Satir | Aciklama | Fix |
|---|--------|-------------|----------|-----|
| FE1 | Frontend | hooks/useExamTimer.ts:120 | Stale closure — `remainingTime` interval callback'te stale | `useExamStore.getState().remainingTime` |
| FE2 | Frontend | hooks/useExamResults.ts:75-79 | Race condition — AbortController yok, stale response yeni sonucu ezer | AbortController + cleanup |
| FE3 | Frontend | Gamification/LevelDisplay.tsx:38 | Memory leak — setTimeout cleanup yok | `return () => clearTimeout(timer)` |
| FE4 | Frontend | ADHD/StreakTracker.tsx:52 | Memory leak — setTimeout cleanup yok | Ayni fix |
| FE5 | Frontend | Dyscalculia/NumberBlocks.tsx:60,102 | Memory leak — 2x setTimeout cleanup yok | useRef + cleanup |
| FE6 | Frontend | AccessibilityValidator.tsx:34 | Memory leak — setTimeout cleanup yok | Ref + cleanup |

## 1.7 Data & Algorithms (15 bulgu)

| # | Kaynak | Dosya:Satir | Aciklama | Fix |
|---|--------|-------------|----------|-----|
| DA1 | Data | alembic/004:181-184 | HNSW index YANLIS tabloda (`question_embeddings`) — 77K seqscan | `question_bank(embedding)` uzerinde index olustur |
| DA2 | Data | models/question_bank.py | `embedding` kolonu SQLAlchemy model'de YOK — autogenerate silebilir | `embedding = mapped_column(Vector(768))` ekle |
| DA3 | Data | agents/question_classifier.py:204,249 | Embedding oncesi NFC normalization yok | `unicodedata.normalize("NFC", ...)` |
| DA4 | Data | agents/question_classifier.py:227 | Turkish `.lower()` — "I"→"i" (yanlis) | Turkish-safe lowercase |
| DA5 | Data | agents/question_classifier.py:158 | Model mismatch — `MiniLM-L12-v2` (384d) vs production `nomic-embed-text` (768d) | Ayni model kullan |
| DA6 | Data | fsrs_service.py:246-269 | FSRS batch review race condition — `SELECT FOR UPDATE` yok | `FOR UPDATE` ekle veya Redis lock |
| DA7 | Data | cat_session.py:408-562 | submit_answer'da duplicate question_id kontrolu yok — replay saldirisi | `if question_id in answered_ids: raise` |
| DA8 | Data | algorithms/irt_model.py:22 | Broken import `from core.irt_validators` — ModuleNotFoundError | Dead code arsivle |
| DA9 | Data | fsrs_engine.py:302 | FSRS state'te stability guncelleme eski `state.stability` kullanir | `new.stability` kullan |
| DA10 | Data | eslesmis_sorucevap.jsonl | 74 farkli field semasi — canonical schema enforce edilmiyor | Schema normalization pass |
| DA11 | Data | eslesmis_sorucevap.jsonl:29567,53238,63220 | 3 kayit answer not in options | Sil veya duzelt |
| DA12 | Data | eslesmis_sorucevap.jsonl | 919 kayit UPPERCASE confidence_level — validation bypass | `.lower()` normalize |
| DA13 | Data | graph.py:159+282 | LoopGuardrail TANIMLI ama graph'a BAGLANMAMIS — sonsuz dongu riski | `guardrail.check(state)` ekle |
| DA14 | Data | graph.py:109 | `MemorySaver()` import fail → None → `None()` TypeError | Guard ekle |
| DA15 | Data | graph.py:283-285 | "blocked" status quality_check'e geciyor, tum gate'ler bosuna calisir | Early-return |

## 1.8 Remaining Areas (5 bulgu)

| # | Kaynak | Dosya:Satir | Aciklama | Fix |
|---|--------|-------------|----------|-----|
| RA1 | Remaining | backend/middleware/*.py (5 dosya) | 5 middleware class TANIMLI ama application.py'ye BAGLANMAMIS | Wire et veya sil |
| RA2 | Remaining | backend/celery_app.py | `task_routes` dict import sirasinda uzerine yaziliyor — 4 task kayitsiz | Dict merge |
| RA3 | Remaining | monitoring/prometheus/postgres_exporter | Postgres exporter `teknofest` DB hedefliyor, `kiro2` degil | Connection string duzelt |
| RA4 | Remaining | backend/api/league_api.py + daily_quest + oba_seferleri | XP endpoint'lerde rate limiting YOK — sinirsiz XP | `@limiter.limit("5/minute")` |
| RA5 | Remaining | frontend/src/sw.ts:317-345 | SW'da `localStorage` kullanimi — erisilemez, runtime crash | `IndexedDB` kullan |

---

# BOLUM 2: TUM P1 BULGULARI (132)

## 2.1 Backend P1 (27)

### Security & Auth (5)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| S6 | api/sentry_demo.py:237 | IDOR — user_id Query param | `Depends(get_current_user)` |
| S7 | core/application.py:189-196 | CSRF exempt_paths=["/api/v1/"] — TUM API unprotected | Frontend X-CSRF-Token, exempt kaldir |
| S8 | api/enhanced_chat.py:674 | SSRF redirect bypass — `follow_redirects=True` private IP atlar | `follow_redirects=False` |
| S9 | api/celery_tasks_api.py:78-80 | Stack trace leakage — full traceback response'ta | Admin-only veya kaldir |
| S10 | api/encryption_management.py:226 | Encryption key API response'ta doner | Key'i cikar, vault'a yaz |

### Models & Schemas (7)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| M4 | enums_db.py:16 vs question_bank.py:388 | exam_type case mismatch — enum lowercase, DB UPPERCASE | Tek convention |
| M5 | curriculum.py:30 vs enums_db.py:16 | Duplicate ExamType enum — farkli member set | Birini sil |
| M6 | learning_path_models.py:130+ (40 yer) | `default=datetime.now` timezone YOK — naive datetime | `server_default=func.now()` |
| M7 | content_db.py:130 | `Question.is_active` maps to column `aktif` — standart disi | Deprecate |
| M8 | gamification.py:239 | `Duel.winner_id` Integer ama `users.id` String (UUID) | `Column(String)` |
| M9 | gamification.py:299 | `StudentAbility.subject_id` Integer PK, FK yok | FK ekle |
| M10 | learning_path_models.py:78 | `user_id` nullable=True — orphan profil riski | `nullable=False` + migration |

### Services & Algorithms (6)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| V6 | cat_session.py:170-172 | Redis None check yok — AttributeError | `if self.redis:` guard |
| V7 | placement_service.py:262-266 | Redis None guard yok — except pass hatayi yutar | Explicit None check |
| V8 | fsrs_service.py:234-270 | N+1 batch — 20 review = 40 DB call | Batch SELECT + UPSERT |
| V9 | cat_session.py:579-675 | DB commit fail ama Redis "completed" — inconsistent state | try/except + Redis revert |
| V10 | irt_model.py:46-48 | IRT param bounds uyumsuz — `[0.2,4.0]` vs `[0.3,3.0]` | Tek source of truth |
| V11 | dag_service.py:96-103 | `NULL AS subject_id` — tum topic'ler "None" | Gercek kolonu sec |

### NLP & Tests (9)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| N7 | turkish_nlp_chat_system.py:325+ (5 yer) | Bare `.lower()` | `normalize_tr()` |
| N8 | turkish_exam_middleware.py:137+ (6 yer) | Bare `.lower()` | `normalize_tr()` |
| N9 | turkish_nlp_service.py:297 | Bare `.lower()` | `normalize_tr()` |
| N10 | turkish_nlp_service.py:420 | Bare `.lower()` | `normalize_tr()` |
| N11 | turkish_exam_event_handlers.py:515 | Bare `.lower()` | `normalize_tr()` |
| N12 | enhanced_turkish_nlp.py:333+ (9 yer) | 9x bare `.lower()`, 0 NFC — ana NLP motoru! | `normalize_tr()` |
| N13 | youtube/nlp.py:127,203,204 | Bare `.lower()` | `normalize_tr()` |
| N14 | 19 dosya, 60 occurrence | Deprecated `AsyncClient(app=app)` — httpx 0.27+ | `ASGITransport(app=app)` |
| N15 | turkish_nlp_chat_system.py + middleware | NFC normalization yok | `unicodedata.normalize("NFC")` |

## 2.2 Frontend P1 (20)

### Security & Auth (7)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| FS1 | revolutionaryFeaturesService.ts:383+ | 8 fetch'te `credentials:'include'` EKSIK | Ekle |
| FS2 | chatService.ts:299,365,392 | 3 fetch'te credentials eksik | Ekle |
| FS3 | fsrsService.ts:117,157,375,412 | 4 fetch'te credentials eksik | Ekle |
| FS4 | multiAgentService.ts:80,174,208,382 | 4 fetch'te credentials eksik | Ekle |
| FS5 | fsrsService.ts:199,234,269 | IDOR — student_id query param | Backend'den derive |
| FS6 | revolutionaryFeaturesService.ts:35+ | IDOR — studentId URL path'te | Backend ownership verify |
| FS7 | Dashboard/NotificationPanel.tsx:306 | Open redirect — `notification.eylem_url` dogrulanmadan | Domain allowlist |

### Components (4)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| FC5 | Exam/Results/ + Results/Tabs/ | Duplicate component'ler — 2 yerde | Tek kaynaktan import |
| FC6 | Exam/*.tsx | 3 nesil ayni arayuz — 1011L, 266L, 744L | Eski 2'sini deprecated'e tasi |
| FC7 | App.tsx | Sayfa seviyesi ErrorBoundary YOK | Exam/LP/Chat/Dashboard'a wrapper |
| FC8 | 24 dead component dizin/dosya | Import edilmeyen ~100+ .tsx dosya | `_deprecated/`'e tasi |

### Hooks & State (4)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| FH3 | useExamWebSocket.ts:85-150 | Render-loop — inline callback dep'leri | useRef pattern |
| FH4 | useGamification.ts:132+ | 8 parallel API call, AbortController yok | AbortController + cleanup |
| FH5 | useLearningPath.ts:447-453 | Suppressed exhaustive-deps | useRef stable ref |
| FH6 | useWebSocket.ts:200-207 | Infinite reconnect loop riski | Ref pattern |

### Performance (5)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| FP1 | App.tsx:20 | ParentDashboard eager import | `React.lazy()` |
| FP2 | App.tsx:7 + PageTransition.tsx:6 | framer-motion (~32KB gz) critical path'te | CSS transition veya lazy |
| FP3 | ModernLoginPage.tsx:23 | framer-motion login'de eager | CSS animation |
| FP4 | 193 dosya | MUI icons barrel import | Path import: `@mui/icons-material/School` |
| FP5 | package.json | `lodash` (full, 500KB) — sadece 1 dosyada debounce | `lodash/debounce` |

## 2.3 Infrastructure P1 (29)

### Docker & Nginx (7)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| D8 | nginx.conf | `server_tokens off` eksik | Ekle |
| D9 | nginx.conf | `client_max_body_size` yok — 10MB upload fail | `10m` ekle |
| D10 | docker-compose.yml:17-18 | Backend 8000 host'a expose — nginx bypass | `expose:` kullan |
| D11 | docker-compose.dev.yml:13-14,27 | PG+Redis tum interface'lere expose, Redis auth yok | `127.0.0.1:` bind |
| D12 | docker-compose*.yml | Hicbir container'da memory/CPU limit yok | `deploy.resources.limits` |
| D13 | frontend/Dockerfile.nginx:50 | Stale Dockerfile — Node 18, wget, `build:prod` | Sil veya guncelle |
| D14 | backend/Dockerfile.dev | HEALTHCHECK tanimli degil | Ekle |

### CI/CD (7)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| G9 | claude-ci.yml:88 | `ruff check \|\| true` — quality gate dekoratif | `\|\| true` kaldir |
| G10 | claude-ci.yml:134,139 | `npm run lint \|\| true` + `tsc \|\| true` | Kaldir |
| G11 | ci.yml:19 | Node 18 ama Vite 7 Node 20+ gerektiriyor | `20` yap |
| G12 | release.yml:27 | Node 18 | `20` yap |
| G13 | ci.yml:420 | Docker build `refs/heads/main` ama branch `master` — calismaz | `master` yap |
| G14 | deploy.yml:160 | super-linter `DEFAULT_BRANCH: main` — kirik | `master` yap |
| G15 | quality-gates.yml (4 yer) | `actions/setup-python@v4` stale | v5 upgrade |

### Alembic (8)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| A7 | 4aec28c6c9e0:20-26 | upgrade+downgrade `pass` — dead orphan | Sil |
| A8 | 0df6ae499ee4:24 | Merge migration 5 head'e bagli | Head'leri dogrula |
| A9 | env.py:21 | Absolute import — dual MetaData riski | Dogrula |
| A10 | env.py:75 | `alembic.ini` URL bos string — sessiz fail | Comment ekle |
| A11 | b49a86e335e5:252 | `quiz_questions.question_id` FK → `questions.id` (BOS tablo) | `question_bank` yap |
| A12 | 20260312 (2 dosya) | Ayni `down_revision` — branch split | Linear chain yap |
| A13 | e73a8e0797c1:884,903 | Base schema FK → `questions` (BOS) | `question_bank` yap |
| A14 | add_taxonomy_and_quality:22-31 | `sorular` tablosu — muhtemelen yok | Disable et |

### Scripts & Config (7)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| X6 | config.py:112-113 | Pool 200/overflow 300 default — dev'de 500 connection | `20/30` default |
| X7 | seed_database.py:864-866 | SHA-256 password hash — auth bcrypt bekliyor | bcrypt kullan |
| X8 | production_seed.py:302 | Ayni SHA-256 sorunu | Ayni fix |
| X9 | import_clean_questions.py:38 | Fallback DB `kiro2_db` — dogru `kiro2` | Duzelt |
| X10 | coverage_dashboard.py:35 | Hardcoded Flask secret | `os.urandom(32).hex()` |
| X11 | application.py:56 | DATABASE_URL ilk 30 char logda — password gorunebilir | Credentials strip |
| X12 | application.py:183-184 | CORS allow_methods/headers=["*"] | Explicit liste |

## 2.4 Data & Algorithms P1 (23)

### Orchestrator (5)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| O4 | routing.py:362-396 | 8 specialist agent tanimli ama factory'de YOK | Fallback mapping |
| O5 | llm_gateway.py:325 | Cost limit asilinca RuntimeError — fallback yok | Sonnet→haiku fallback |
| O6 | policy_engine.py:487-535 | Policy routing_rules agent isimleriyle UYUMSUZ | Sync et |
| O7 | graph.py:349-352 | Review router DAIMA "complete" donuyor | Review logic implement |
| O8 | self_improvement.py:326 | Engine graph'a BAGLANMAMIS | Wire veya kaldir |

### Algorithms (8)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| AL5 | irt_engine.py:75-84 | IRT a/b/c parametre validation YOK | `__post_init__` clamp |
| AL6 | irt_engine.py:231-237 | ZPD filtresi [0.40,0.85] — CLAUDE.md [0.15,0.85] | Senkronize |
| AL7 | turkish_optimized_fsrs.py:429 | FSRS retrievability uyumsuz — dead code | Arsivle |
| AL8 | algorithms/ (4 dosya) | Dual FSRS implementasyonu | `_archived/` tasi |
| AL9 | turkish_zpd_maarif_system.py:398 | ZPD theta=0 icin ZPD=0 (paradoks) | Minimum floor |
| AL10 | cat_session.py:455-475 | Default a=1,b=0,c=0.25 — theta saptirir | Warning log |
| AL11 | irt_engine.py | ItemParams parametre validation yok | `__post_init__` ekle |
| AL12 | placement_service.py:430 | Placement sonucu SADECE Redis'te (TTL 300s) | DB'ye UPSERT |

### d-dataset Pipeline (4)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| DD4 | import_d_dataset.py:211 | quality_score=None → 0.0 — unscored vs bad ayirt edilemez | Sentinel deger |
| DD5 | validate_sample.py:515-526 | 111MB JSONL full memory load (~1.2GB RAM) | Streaming/generator |
| DD6 | backups/ | v3.5 backup YOK | Hemen olustur |
| DD7 | validate_sample.py:42 | PASS_THRESHOLD 95% — CLAUDE.md "100% PASS" | 1.0 yap |

### Embedding + Vector + NLP (6)
| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| E6 | question_crud_api.py:931 + photo_ask_service.py:135 | Embedding dimension validation yok | `len(embedding) != 768` check |
| E7 | (yok) | Text guncellendikten sonra embedding re-generate yok — stale | `embedding = NULL` set |
| E8 | (yok) | Query embedding cache yok | Redis cache + TTL |
| E9 | question_classifier.py:186-191 | Model yuklenemezse sessiz fallback | Health sub-check |
| E10 | turkish_bionic_reading.py:104 | `.lower()` Turkish-safe degil | Turkish lowercase |
| E11 | generate_embeddings.py:144 | Text 2000 char truncate — kalite kaybi | Log + limit review |

## 2.5 Remaining Areas P1 (33)

### Root Pollution & Docs (6)
| # | Dosya | Aciklama | Fix |
|---|-------|----------|-----|
| R3 | root (333 dosya) | Root'ta 333 git-tracked dosya | Alt dizinlere tasi |
| R4 | root (207 .py) | 207 Python dosyasi root'ta | backend/'a tasi |
| R5 | seed scripts | Hardcoded weak password'lar root script'lerde | Env var |
| R6 | docs/ (stale) | Obsolete doc referanslari | Guncelle veya sil |
| R7 | root *.bat/*.sh | Shell script'ler dagitik | scripts/ altina |
| R8 | root *.jsonl | Buyuk JSONL git-tracked (LFS yok) | git-lfs |

### Celery & Analytics & Middleware (8)
| # | Dosya | Aciklama | Fix |
|---|-------|----------|-----|
| C4 | celery_app.py | Beat schedule tanimli ama worker baslatilmiyor | Docker service ekle |
| C5 | backend/tasks/ (4 modul) | 4 task register edilmemis | `include` listesine ekle |
| C6 | backend/analytics/ (8 modul) | Pipeline API'ye baglanmamis | Router ekle |
| C7 | middleware/cache_middleware.py | Mevcut ama application.py'de YOK | Wire veya sil |
| C8 | middleware/metrics_middleware.py | Mevcut ama baglanmamis | Wire veya sil |
| C9 | middleware/logging_middleware.py | Baglanmamis | Wire |
| C10 | tasks/analytics_tasks.py | Celery task tanimli ama worker yok | Worker baslat |
| C11 | analytics/dashboard_service.py | API endpoint'i yok | Ekle veya kaldir |

### Monitoring & Integrations (10)
| # | Dosya | Aciklama | Fix |
|---|-------|----------|-----|
| MO3 | prometheus/ | Duplicate scrape config | Birlestir |
| MO4 | alertmanager/ | teknofest referansi — stale | kiro2 guncelle |
| MO5 | grafana/dashboards/ | teknofest metrikleri | Guncelle |
| MO6 | backend/api/ (2 orphan) | Register edilmemis router | Include veya sil |
| MO7 | backend/analytics/ | Dead code | Wire veya arsivle |
| MO8 | alembic/versions/ | Algorithm migration Alembic'te YOK | Olustur |
| MO9 | docker-compose.monitoring.yml | Ana compose'dan ayri | Merge veya README |
| MO10 | api/integration_*.py | Stub endpoint'ler | Label veya kaldir |
| MO11 | grafana/ | Data source localhost — Docker'dan erisilemez | Docker hostname |
| MO12 | core/telemetry.py | OpenTelemetry devre disi | Enable veya kaldir |

### Gamification & Mobile & Destani (9)
| # | Dosya | Aciklama | Fix |
|---|-------|----------|-----|
| G3 | push_notification_system.py:284 | MySQL-style INDEX syntax SQLite'da crash | CREATE INDEX ayri |
| G4 | manifest.json:14-72 | Icon type png ama dosya SVG | PNG olustur veya type duzelt |
| G5 | manifest.json:14 | `/icons/` path yok, dosyalar `/images/` | Path duzelt |
| G6 | pwa_sync_api.py:40-91 | 4 endpoint tamamen stub | Gercek impl yaz |
| G7 | mobile/*.py (5 dosya) | Spec/mock — prod degil | docs/specs/'e tasi |
| G8 | package.json | three.js 1.5MB+ 0 import — bloat | npm uninstall |
| G9 | sw.ts:277 | Sync URL v1 prefix eksik + endpoint isim yanlis | Duzelt |
| G10 | sw.ts:299 | Analytics sync URL backend'de yok — 404 | Ekle veya kaldir |
| G11 | duel_api.py | Matchmaking kuyruk TTL yok — sonsuz bekleme | Redis TTL 60s |

---

# BOLUM 3: TUM P2 BULGULARI (161)

## 3.1 Backend P2 (30)

### Security (8)
- S11: turkish_nlp.py NLP endpoint auth yok
- S12: text_simplification.py auth yok
- S13: yolo_detection_api.py auth yok, file validation yok
- S14: vision_api.py auth yok — LLM maliyeti
- S15: CORS allow_methods/headers=["*"]
- S16: osym_questions_api.py raw asyncpg.connect() — ORM bypass
- S17: database_optimizer.py `text(f"ANALYZE {table}")` — SQL injection
- S18: question_crud_api.py f-string text() — injection riski

### Models (8)
- M11: `Question` legacy `__all__`'da
- M12: 3x difficulty enum, 3x exam type enum — kaos
- M13: Schema divergence — enum vs string
- M14: `datetime.utcnow` deprecated Python 3.12+
- M15: user_badge.py sadece re-import
- M16: JSONB default=list/dict — schema validation yok
- M17: JSONB kolonlar structure enforcement yok
- M18: `EgitimIcerigi = "EducationalContent"` string, class degil

### Services (9)
- V12: `ORDER BY RANDOM()` 77K row — full scan
- V13: `ORDER BY RANDOM() LIMIT 80` 77K row
- V14: Mastery cache invalidation yok — 5dk stale
- V15: Hardcoded exam date — module load evaluate
- V16: `datetime.utcnow()` deprecated
- V17: `get_user_mastery()` return unused
- V18: turkish_optimized_fsrs.py dead code
- V19: irt_model.py dead code (4PL)
- V20: irt_calibrator.py docstring yanlis tablo

### NLP & Tests (5)
- N16: turkish_nlp_service.py hardcoded Zemberek URL
- N17: test_circuit_breaker.py 5x `asyncio.sleep(1.1)` — flaky
- N18: 59 dosya `skipif(True)` — permanent skip
- N19: 94 dosya `pytest.skip(allow_module_level=True)` — 153 dosya skipped
- N20: encoding.py `normalize_turkish_text` duplicate yanlis impl

## 3.2 Frontend P2 (40)

### Security (7)
- S8: MermaidThoughtTree.tsx `.innerHTML = svg` sanitize yok
- S9: utils/lazyLoad.tsx `new Function()` — CSP unsafe-eval
- S10: offlineStorageService.ts credentials eksik
- S11: NetworkDetector.ts credentials eksik
- S12: test/e2e/mvp-smoke.spec.ts hardcoded test password
- S13: ADHD test localStorage token pattern
- S14: .migration-backup/ eski token dosyalari git'te

### Components (6)
- C9: 20+ dosya 120 occurrence `any` type
- C10: 80+ dosya `key={index}` anti-pattern
- C11: 25+ dosya inline `style={{}}`
- C12: 6 dosya `dangerouslySetInnerHTML`
- C13: TextToSpeech.tsx setTimeout cleanup yok
- C14: EbaTV/*.tsx hardcoded placeholder URL

### Hooks & State (14)
- H7-H14: 8 dead hook/util (0 import)
- H15-H18: `any` type 4 hook'ta yaygin
- H19: `loadResults` useCallback degil
- H20: useStudentProfile AbortController yok

### Performance (13)
- P6: three.js + @react-three ~500KB unused
- P7: d3 ~200KB unused
- P8: mermaid ~800KB unused
- P9-P18: framer-motion 64 dosya, console.log kalintilari, react-window unused, Dexie sync yuklemesi, fetch override her request URL parse, vb.

## 3.3 Infrastructure P2 (25)

### Docker (6)
- D15-D20: Log rotation yok, gzip eksik MIME, test exclude, proxy timeout 3600s, volume mount override, gereksiz wget

### CI/CD (5)
- G16-G20: timeout-minutes yok, health-check 5dk (8640/ay), main branch ref, duplicate CI, kubeconfig temizlenmez

### Alembic (6)
- A15-A20: Downgrade bare except, raw SQL 14 tablo, IF EXISTS guard yok, no-op migration, FK index eksik, 4 bagimsiz branch root

### Scripts (8)
- X13-X20: Tutarsiz DB connection, default password, email redaction kapali, test DB stale, destructive default, legacy model, CSRF exempt, port collision

## 3.4 Data & Algorithms P2 (36)

### Orchestrator (12)
- O9-O20: `field()` non-dataclass, hardcoded endpoint, duplicate pricing, CostTracker disconnected, state mutation race, undefined methods (2), iteration 2x, missing configs, JSON parse→success, opaque error, numpy dependency

### Algorithms (8)
- AL13-AL20: Gereksiz hesaplama, dead code 4 dosya, birim test eksik, underflow threshold, stability guncellenmez, duplicate risk, AYT formul sapma, naif lineer YKS score

### d-dataset (7)
- DD8-DD14: Hardcoded Windows path, output overwrite, duplicate key last wins, ON CONFLICT DO NOTHING, full memory load, 98 stale script, 2348 low confidence kayit

### Embedding (9)
- E12-E20: HNSW ef_search default, f-string SQL, triple CAST, ARRAY vs Vector, string serialization, hardcoded Ollama URL, model auto-download, coverage monitoring yok, retry logic yok

## 3.5 Remaining Areas P2 (30)

### Root Pollution (9)
- R9-R17: 207 root .py, log dosyalari git'te, __pycache__ git'te, stale brainstorms, backup script dagitik, root test dosyalari, session dosya buyumesi

### Celery & Middleware (7)
- C12-C18: Broker URL hardcoded, cleanup task calismaz, event tracking frontend SDK yok, rapor formati belirsiz, duplicate gzip, funnel veri kaynagi belirsiz, email SMTP yok

### Monitoring (8)
- MO13-MO20: Stack hic calistirilmamis, alert rule generic, webhook baglanmamis, feature flag persist yok, admin frontend belirsiz, volume hardcoded, ES timeout, export KVKK dogrulanmamis

### Gamification & Mobile (6)
- G12-G17: Duel reconnect yok, lazy import 503, Math.random() render, skipWaiting kayitsiz, XP hardcoded, sync/async karisik

---

# BOLUM 4: CROSS-CUTTING TEMALAR

## 4.1 En Kritik Temalar (Tum Fazlarda Tekrarlayan)

| # | Tema | Etkilenen Fazlar | Toplam Bulgu | Oncelik |
|---|------|-----------------|--------------|---------|
| 1 | **Auth bypass / IDOR** | Backend, Infra, Remaining | 14+ P0, 8+ P1 | ACİL |
| 2 | **Hardcoded secrets** | Infra, Remaining, Backend | 12+ P0 | ACİL |
| 3 | **Turkish .lower() bozuklugu** | Backend, Data&Algo | 20+ yer, 6+ P1 | ACİL |
| 4 | **Dead code / disconnected modules** | Frontend, Remaining, Data&Algo, Backend | 40+ dosya | YUKSEK |
| 5 | **Missing rate limiting** | Backend, Remaining | 8+ endpoint | YUKSEK |
| 6 | **Root container (no USER)** | Infra | 3 Dockerfile | YUKSEK |
| 7 | **Unpinned CI actions** | Infra | 5+ action | YUKSEK |
| 8 | **N+1 query pattern** | Backend, Data&Algo | 4+ servis | ORTA |
| 9 | **Stale branding (teknofest)** | Remaining (monitoring) | 5+ dosya | ORTA |
| 10 | **Legacy Question model** | Backend, Data&Algo | 4 test + export | ORTA |

## 4.2 Konsensus Matrisi (2+ Agent Hemfikir)

| Konu | Hemfikir Agent Sayisi | Guvenilirlik |
|------|----------------------|-------------|
| Auth bypass yaygin | 4 (Backend Security + NLP + Infra Scripts + Remaining) | COK YUKSEK |
| Hardcoded secrets | 4 (Infra Docker + Scripts + Remaining Root + Monitoring) | COK YUKSEK |
| Dead code yaygin | 5 (Frontend Comp + Hooks + Perf + Remaining Celery + Data Algo) | COK YUKSEK |
| Turkish .lower() | 3 (Backend NLP + Data Embedding + Data Algo) | YUKSEK |
| N+1 query | 2 (Backend Services + Data Algo) | YUKSEK |
| Duplicate enum/model | 2 (Backend Models + Services) | YUKSEK |
| credentials:'include' eksik | 2 (Frontend Security + Hooks) | YUKSEK |
| Celery configured not running | 2 (Remaining Celery + Monitoring) | YUKSEK |

---

# BOLUM 5: BIRLESIK ONCELIKLI AKSIYON PLANI

## Faz 1 — ACİL (Bu hafta) — 20 aksiyon

### Security & Auth (7)
1. **Auth bypass fix** (S1-S5): 5 API dosyasina `Depends(get_current_user)` — exploit edilebilir
2. **CI script injection** (CI1): claude-review.yml env var — exploit edilebilir
3. **Action pinning** (CI2-CI6): 5 action SHA pin — supply chain risk
4. **CSP + HSTS header** (CI9-CI10): nginx.conf — XSS/MITM
5. **Root container fix** (CI11-CI13): 3 Dockerfile'a USER directive
6. **cookies*.txt temizle** (S13): JWT token'lar git'ten sil + BFG
7. **XP rate limiting** (RA4): gamification endpoint'lere limiter

### Data Integrity (5)
8. **HNSW index question_bank'a** (DA1): 77K seqscan → 21ms
9. **FSRS race condition** (DA6): SELECT FOR UPDATE
10. **CAT replay guard** (DA7): duplicate question_id reject
11. **3 bozuk cevap** (DA11): answer not in options — sil
12. **LoopGuardrail wire** (DA13): sonsuz dongu onleme

### Frontend (3)
13. **useExamTimer stale closure** (FE1): sinav zamanlayici
14. **useExamResults race condition** (FE2): AbortController
15. **SW localStorage fix** (RA5): IndexedDB'ye gecir

### Backend (5)
16. **DAG cartesian join** (BM8): milyonlarca satir rewrite
17. **DAG NULL subject_id** (V11): tum topic kirik
18. **FK constraint** (BM2): orphan data onleme
19. **MemorySaver guard** (DA14): TypeError onleme
20. **Middleware karar** (RA1): 5 dead middleware wire veya sil

## Faz 2 — SPRINT (Bu ay) — 25 aksiyon

### Security (5)
21. **Hardcoded secrets temizle** (S6-S12): .env dosyalarina tasi
22. **SHA-256 → bcrypt** (X7-X8): seed + production_seed
23. **CSRF fix** (S7): exempt_paths kaldir
24. **SSRF redirect** (S8): `follow_redirects=False`
25. **credentials:'include'** (FS1-FS4): 19 fetch cagrisina ekle

### Turkish NLP (2)
26. **Turkish .lower() batch fix** (N7-N13): 6 dosya, 30+ yer — `normalize_tr()`
27. **NFC normalization** (DA3, N15): question_classifier + NLP

### Infrastructure (6)
28. **Node 18 → 20** (G11-G12): ci.yml + release.yml
29. **Quality gates fix** (G9-G10): `|| true` kaldir
30. **Dead migration temizle** (A5-A7): kvkk + orphan sil
31. **FK → question_bank** (A11, A13): base schema duzelt
32. **Celery worker baslat** (C4-C5): docker-compose service + task register
33. **Grafana/Prometheus fix** (MO1-MO5): teknofest→kiro2, cred kaldir

### Data & Algorithms (5)
34. **embedding kolonu model'e** (DA2): autogenerate koruma
35. **Placement DB persist** (AL12): Redis TTL veri kaybi
36. **ZPD aralik sync** (AL6): [0.40,0.85] vs [0.15,0.85]
37. **confidence_level normalize** (DA12): 919 kayit
38. **v3.5 backup** (DD6): disaster recovery

### Frontend (4)
39. **Dead code temizligi**: 24 component + 6 hook → `_deprecated/`
40. **Page-level ErrorBoundary** (FC7): Exam, LP, Chat, Dashboard
41. **framer-motion lazy** (FP2-FP3): 32KB initial tasarrufu
42. **three.js + d3 + mermaid kaldir** (G8, P6-P8): 2.5MB+ tasarrufu

### Backend (3)
43. **N+1 batch** (BM7, V8): CAT + FSRS multi-row
44. **Redis null guard** (V6, V7): 2 servis
45. **IDOR fix** (FS5-FS6): student_id backend'den derive

## Faz 3 — TEKNIK BORC (Sonraki sprint) — 20+ aksiyon

46. **httpx migration** (N14): 19 dosya ASGITransport
47. **Enum consolidation** (M5, M12): tek canonical per concept
48. **Dead code arsivle** (AL14, V18, V19): algorithms/ 4+ dosya
49. **Question model deprecation** (M1, M11): export + test migration
50. **Root pollution temizle** (R3-R4): 207 .py + scripts organize
51. **Schema normalization** (DA10): 74 farkli schema → canonical
52. **Embedding cache** (E8): Redis TTL sorgu cache
53. **Production algoritma testleri** (AL15): irt_engine + fsrs_engine
54. **8 specialist agent** (O4): routing dead-end implement
55. **Analytics pipeline wire** (C6): 8 modul bagla veya arsivle
56. **Shared _db_utils.py** (X13): 8 script DB birlestir
57. **Missing FK indexes** (A19): mega_feature 8+ index
58. **main → master** (G13-G14, G18): tum workflow branch fix
59. **Duplicate CI merge** (G19): ci.yml + claude-ci.yml birlestir
60. **mobile/ dizini tasi** (G7): docs/specs/ altina
61. **Monitoring stack test** (MO13): Docker'da calistir
62. **any type audit** (C9, H15-H18): 120+ yer interface tanimlari
63. **key={index} fix** (C10): dinamik listelerde stable ID
64. **lodash → lodash/debounce** (FP5): 70KB tasarrufu
65. **MUI icons path import** (FP4): dev DX iyilestirme

---

# BOLUM 6: POZITIF BULGULAR

Tum fazlarda tespit edilen olumlu noktalar:

### Backend
- localStorage auth production code'da TEMIZ — migration tamamlanmis
- Route protection: Login/register/404 haric tum route'lar ProtectedRoute icinde
- authStore token saklamiyor — sadece display bilgisi persist

### Frontend
- dangerouslySetInnerHTML tum 6 kullanim DOMPurify ile sanitize ediliyor
- 50+ sayfa React.lazy() ile lazy-loaded
- dayjs kullaniliyor (moment.js DEGIL)
- Dashboard Promise.all ile paralel fetch — waterfall yok
- Vite config iyi tuned: terser console strip, CSS code split

### Data & Algorithms
- d-dataset NFC normalization %100 temiz
- Import script idempotent (deterministic UUID + ON CONFLICT)
- UTF-8 encoding tutarli
- Bayesian cross-validation iyi kalibre
- generate_embeddings.py prefix kullanimi dogru (`search_document:`)
- fsrs_engine.py FSRS v6 power-law decay dogru implement
- IRT 3PL formulu matematiksel olarak dogru
- EAP theta estimation quadrature ile — yakinsama garanti

### Infrastructure
- Docker stack calisiyor — E2E 7/7 PASS (Session 77)
- nginx proxy dogru yapilandirilmis (API + static)
- Health check endpoint mevcut

### Remaining Areas
- Gamification API'ler calisiyor — 7 router, auth, DB migration, SSE duel stream
- KIRO Destani component'ler render ediliyor, route'lar tanimli
- Bilge Alp NPC SSE streaming + auth aktif
- Service Worker Workbox ile iyi yapilandirilmis
- F0-F6 social features tamamen entegre (20 model, 45 endpoint, 77 test PASS)

---

# BOLUM 7: RISK MATRISI

| Risk | Olasilik | Etki | Skor | Ilk Aksiyon |
|------|----------|------|------|-------------|
| Auth bypass ile veri sizintisi | YUKSEK | KRITIK | 10 | Faz 1 #1 |
| CI script injection ile supply chain | ORTA | KRITIK | 8 | Faz 1 #2-3 |
| FSRS race condition ile veri kaybi | ORTA | YUKSEK | 7 | Faz 1 #9 |
| Hardcoded secret exposure | YUKSEK | YUKSEK | 9 | Faz 1 #6, Faz 2 #21 |
| XP abuse ile gamification bozulmasi | YUKSEK | ORTA | 6 | Faz 1 #7 |
| SW crash (localStorage) | YUKSEK | ORTA | 6 | Faz 1 #15 |
| 77K seqscan performans | ORTA | ORTA | 5 | Faz 1 #8 |
| Turkish text mismatch | YUKSEK | DUSUK | 4 | Faz 2 #26-27 |
| Dead code maintenance burden | DUSUK | DUSUK | 2 | Faz 3 |

---

*Full Project Deep Audit: 20 parallel agents, 5 phases, 368 findings*
*Raporlar: docs/audits/2026-03-28_*.md*
*Audit by: Claude Opus 4.6*
*Tarih: 2026-03-28*
