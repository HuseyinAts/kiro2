## Session Handoff — 2026-04-11 Session 147
**Branch:** master
**Son commit:** cf4147b test(golden-flows): Wave 11 sweep — GF90-GF99 probes + 5 real fixes
**Uncommitted:** 0
**Pushed:** HAYIR — 4 commit ahead of origin/master, push bekliyor

### Yapilanlar — Session 147 (5 görevin tamamı)

**Görev 1 — audit_httpexception_guard.py CI gate** (commit `b20e215`):
- `.github/workflows/golden-flows.yml`'ye 6. AST linter step eklendi (`python scripts/audit_httpexception_guard.py --fail`)
- Rule-of-eight (Session 146'da eradike edilen anti-pattern) CI tarafından kalıcı koruma altına alındı

**Görev 2 — smoke test pre-commit hook** (commit `b20e215`):
- `backend/scripts/_smoke_api_imports.py`'ye `sys.exit(1)` eklendi (fail-close)
- `.pre-commit-config.yaml`'a `kiro2-api-import-smoke` lokal hook eklendi, `files:` filter `^backend/api/.*\.py$` ile sadece API değişikliğinde tetiklenir

**Görev 3 — DB dependency baseline re-run** (commit `d8ce182`):
- `docs/audits/2026-04-11_db-dependency-s147-baseline.md` yazıldı
- `audit_db_dependency.py` çıktısı: 98 MEDIUM tech debt, **HIGH=0** (Session 137 baseline 179→98 onaylandı)
- `--fail-on-high` exit 0 (CI gate temiz)

**Görev 4 — Wave 11 Golden Flow sweep (GF90-GF99)** (commit `cf4147b`):
- 10 disjoint yeni probe eklendi (`backend/tests/e2e/test_golden_flows.py`)
- **5 gerçek bug yakalandı** (hit rate %50 — Wave 10 %80'den düşüş beklendiği gibi rule-of-eight sonrası):
  - **GF41 reasoning_api/solve** (Wave 6 regression): reasoning_cache query tz-aware → tz-naive DataError. `solve_problem` exception guard widened to match `dbapierror`/`asyncpg`/`datatypemismatch` keywords + class name. Artık 503 döner.
  - **GF86/GF87 instant_feedback_api** (Wave 10 collateral): initial ORM rewrite hala `streak_tracking`/`performance_history` 3 drift'e takıldı (NOT NULL student_id yok, uuid vs varchar id, date vs DateTime). **Raw SQL `text()` + `gen_random_uuid()` + `now()` server-side ile tamamen yeniden yazıldı** — sıfır ORM churn.
  - **GF92 pdf_processing_api**: `UPLOAD_DIR = Path("backend/uploads/pdfs")` relatif path Docker CWD `/app` altında crash. `Path(__file__).parent.parent` ile anchor + import-time `try/except OSError` + runtime OSError → 503.
  - **GF94 video_analytics_service**: VideoNote + VideoCompletionMilestone asyncpg VARCHAR+UUID drift (rule-of-seven — Session 142 prophylactic sweep bu 2 modeli missledi). `id=str(uuid4())` + `user_id=str(user_id)` + `session_id=str(...) if ... else None` coerce.
  - **GF95 manipulatives_progress_api**: sync `def` + `Depends(get_db)` + async engine three-part trap (Wave 10 GF86/87 ile aynı). Tüm 5 handler `async def` + `get_async_session` + `select()` + `await db.execute()` rewrite.
  - **GF99 csrf_protection middleware**: iki parçalı bug — (a) `raise HTTPException` middleware `dispatch`'ten escape etmiyor, 500 olarak geliyor → `JSONResponse` return, (b) Bearer-auth API client'lar CSRF'lenemez → `authorization: bearer` early-return. `JSONResponse` import'u da eksikti.
- Ek olarak `backend/api/sequential_reasoning_api.py` `solve_problem` exception keyword listesi genişletildi (GF41 fix).
- **Final distribution: 116 test → 114 PASS / 0 FAIL / 2 SKIP** (GF1wB + GF4w.2 state-dependent skip'ler değişmedi).
- `.claude/rules/golden-flows.md`'ye Wave 11 tablosu + analiz paragrafı eklendi.

**Görev 5 — GF33 StudyPlan.weekly_goals relationship fix** (commit `03b467a`):
- `backend/models/study_planner.py` — `StudyPlan.weekly_goals` + `WeeklyGoal.plan` back-populates relationship eklendi
- `services/study_planner_service.py`'nin 7 call site'ı (`selectinload(StudyPlan.weekly_goals)` + `plan.weekly_goals` iteration) artık silent fallback yerine normal çalışır
- DB şeması zaten doğruydu (alembic migration `20260312_create_mega_feature_tables`); sadece ORM relationship eksikti

### Fail Eden Testler
- YOK. 116 test → 114 PASS / 0 FAIL / 2 SKIP (baseline korundu, 10 yeni Wave 11 probe hepsi geçti)

### Engelleyiciler
- YOK

### Session 147 Bulgular / Notlar
- **Wave 11 hit rate %50** (Wave 10 %80'den düşüş) — rule-of-eight eradikasyonunun beklenen etkisi. Yeni anti-pattern class: **raw ORM/DB schema drift** (4/5 bug: reasoning_cache tz, instant_feedback x3 drift, VideoNote UUID, manipulatives sync shim). GF22/GF83 optional-dep pattern hala mevcut ama baskın değil.
- **Middleware HTTPException trap**: `BaseHTTPMiddleware.dispatch()`'ten `raise HTTPException` yapmak 500'e dönüşür — FastAPI global handler sadece route handler'ları yakalar. `JSONResponse` return zorunlu. Bu bilgi KIRO2 middleware guide'a eklenmeli.
- **SQLAlchemy DBAPIError wrapping**: asyncpg hatalarını message string'i üzerinden yakalamak kırılgan — class name üzerinden `type(exc).__name__` kontrolü stricter more robust. GF41 fix'ine dahil edildi.
- **Rule-of-seven VideoAnalytics asyncpg drift**: Goal/LiveSession/EmotionalState/VideoConferenceSession/VideoWatchSession/ReasoningSession/VideoNote-VideoCompletionMilestone. Session 142 prophylactic sweep *mostly complete* — iki model gözden kaçtı. Gelecekte `Column(String, default=uuid.uuid4)` pattern'i herhangi bir yerde görülürse guaranteed asyncpg crash site olarak işaretlenmeli.
- **instant_feedback_api raw SQL bypass**: 3+ ORM drift olan tablolarda raw SQL `text()` + server-side `gen_random_uuid()`/`now()` ile yazmak, global ORM fix'ten çok daha ucuz (çünkü ORM'i düzeltmek tüm consumer'ları churn'lar). Gelecekte benzer drift görülürse bu pattern önerilir.
- **DB dependency baseline 98 MEDIUM sabit kaldı** — Wave 11 GF95 manipulatives + GF86/87 collateral rewrite ile Pattern A düzeltmeleri yapıldı ama Session 137 baseline'ı sadece `api/` alt dizini tarıyor, `services/` taramıyor (Session 145 manipulatives rewrite services layer'ı da etkiledi).

### Sonraki Adimlar (maks 5)
1. **PUSH** — 4 commit (b20e215, d8ce182, 03b467a, cf4147b) origin/master'a push.
2. **Wave 12 planning** — Feature inventory hala ~440 uncovered write-path endpoint var. Wave 11 hit rate %50 — Wave 12'de %30-40 civarı bekleniyor (yeni anti-pattern class daha zor teshis ediliyor).
3. **Middleware HTTPException rule** — `.claude/rules/middleware.md` yeni dosya: `BaseHTTPMiddleware.dispatch` içinde `raise HTTPException` yasak, `JSONResponse` return zorunlu.
4. **Rule-of-seven asyncpg audit** — `grep "Column(String.*uuid.uuid4\|default=uuid4)"` ile tüm model dosyalarını tara, kalan pattern varsa proactive fix.
5. **instant_feedback_api raw SQL bypass dokümante et** — `.claude/rules/orm-drift.md` yeni dosya: 3+ drift olan tablolarda raw SQL `text()` yaklaşımı önerilen pattern.

### Kararlar (gelecek session tekrar tartismasin)
- Session 147'nin 5 görevi tamamlandı. 4 commit hazır, push bekliyor.
- Golden Flow suite 116 test, 114 PASS / 0 FAIL / 2 SKIP baseline sabit.
- Wave 11 sonrası yeni anti-pattern class: raw ORM/DB schema drift. Wave 12'de bu aranacak.
- Rule-of-eight (bare-except 500 re-wrap) CI tarafından `audit_httpexception_guard.py --fail` ile kalıcı kilitli.
- DB dependency audit 98 MEDIUM, HIGH=0. Bir sonraki re-run ~40 baseline'a inme hedefi (`services/` alt dizini dahil).
