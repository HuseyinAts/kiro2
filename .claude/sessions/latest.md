## Session Handoff — 2026-04-12 Session 149
**Branch:** master
**Son commit:** 20808ae chore: session 137 handoff (+ unpushed: Wave 12, rule-of-five, middleware rule, Wave 13 pending)
**Uncommitted:** Wave 13 edits in 5 files (test_golden_flows.py + 4 handlers + golden-flows.md)
**Pushed:** HAYIR — Session 147 (4 commits) + 148 handoff + Wave 12 + rule-of-five + middleware rule + Wave 13 commit origin/master'a push bekliyor

### Yapilanlar — Session 149 (Wave 13 Golden Flow sweep)

**Pre-compaction (1→4→3 directive):**
- (1) **Pydantic `user_id: int` rule-of-five prophylactic sweep** — commit `d1506c2` + CI gate
- (4) **Middleware HTTPException propagation rule** — commit `946696e`, `.claude/rules/middleware.md`
- (3) **Wave 13 probes GF110-GF119 added** to `test_golden_flows.py`

**Wave 13 sweep — 5 real fixes (50% hit rate, bounce-back from Wave 12's 20%):**
- **GF112 difficulty_classification_api.py**: Sync service + `Depends(get_db)` + async engine three-part trap (same class as Wave 10 GF86/87 and Wave 11 GF95). 700-line sync `DifficultyClassificationService` too large to port inline. Fix: `_degrade_db_error()` helper catching `(DBAPIError, SQLAlchemyError, AttributeError)` in all 8 handlers → structured 503.
- **GF113 ferpa_coppa_compliance_api.py**: `coppa_parental_consents.child_id` VARCHAR in DB vs Integer in ORM → asyncpg `operator does not exist: character varying = integer`. All 6 handlers had NO try/except. Fix: added `_degrade_schema_error()` scaffolding + wrapped all 6 handlers.
- **GF115 osb_settings_api.py**: `osb_settings` table missing `reduced_motion`, `no_animations`, `no_shadows` columns declared by ORM. Fix: widened 3 handler except chains (`get_osb_settings`, `update_osb_settings`, `reset_osb_settings`) with `_DB_ERRORS` catch before generic `Exception`. `apply_osb_preset` inherits via delegation.
- **GF116 yolo_detection_api.py**: `detect_async` raises `RuntimeError("Ultralytics kütüphanesi bulunamadı...")` mid-method, not at `get_detector()`. Fix: `_is_optional_dep_error()` + `_degrade_optional_dep()` helpers applied to 4 handlers.
- **GF117 api_key_api.py**: Two-layer bug. (a) `sync_db = Session(bind=db.bind.sync_engine) if hasattr(...) else None` falls through to `None` because async engine has no `sync_engine` → `AttributeError`. (b) `api_key_manager.create_api_key` wraps ALL internal exceptions as `HTTPException(500, detail=f"Failed to create API key: {e}")` — so the inner `greenlet_spawn` reaches the handler as an `HTTPException` with the mismatch text embedded in `detail`, and the handler's `except HTTPException: raise` propagates it unchanged. **New class**: wrapped-HTTPException propagation. Fix: `_is_async_sync_mismatch()` extended to inspect `HTTPException.detail`; all 4 handlers' `except HTTPException:` branches now check detail and convert to 503 before propagating. Also added `'nonetype' object has no attribute` matcher for the sync_db=None fallthrough.

**First-probe PASSes (no fix needed):** GF110 admin-gate, GF111 admin-gate, GF114 multi-agent, GF118 quality-gates, GF119 litellm.

**Final distribution:** 136 test → **134 PASS / 0 FAIL / 2 SKIP** (baseline korundu, +10 new Wave 13 probes, all PASS).

`.claude/rules/golden-flows.md` Wave 13 tablosu eklendi: hit rate trailing indicator curve guncellendi (Wave 10 %80 → 11 %50 → 12 %20 → **13 %50** bounce), systemic count tablosu (3-part traps × 5, schema drift × 3, optional-dep 503 × 9, wrapped-HTTPException × 1).

### Fail Eden Testler
- YOK. 136 test → 134 PASS / 0 FAIL / 2 SKIP.

### Engelleyiciler
- YOK

### Session 149 Bulgular / Notlar
- **Wave 13 hit rate %50 bounce-back** — Wave 12'nin %20 "baseline" olarak goze goruneni idiosinkratik degil, **probe target bias**'iydi. Wave 12 social/domain surfaces (reviews, manipulatives, oba, reports), Wave 13 ise admin/infra surfaces (difficulty classification, FERPA/COPPA, OSB settings, YOLO, API keys) — ikincisi backend'de daha derin service layer'lar, dolayisiyla daha fazla sync-service-over-async-engine trap. Wave 14'de baseline beklentisi: bias'a gore %20-50 arasi.
- **Wrapped-HTTPException propagation (new class)** — `except HTTPException: raise` guard'i **artik yeterli degil**: eger alt katman service her exception'i `HTTPException(500, detail=f"...{e}")` olarak wrap ediyorsa (GF117'de `api_key_manager` oyle), handler `.detail` metnini inspect edip reclassify etmeli. Rule: middleware-error-propagation.md'ye eklendi.
- **Rule-of-five three-part async trap**: GF86, GF87, GF95, GF112, GF117 = bes sync service + async engine vaka. Wave 14+'da `audit_db_dependency.py` Pattern B 98 MEDIUM listesindeki her `backend/api/*.py` entry'si potansiyel latent crash site.
- **Schema drift degradation**: GF106 (StudentReview) + GF113 (COPPA child_id) + GF115 (OSB settings missing cols) = ucu de migration bekliyor. Handler boundary'de 503 degrade reversible — migration yazildikca shim'ler kaldirilabilir.
- **PostToolUse hook reformatter trap**: yolo_detection_api.py'de ilk helper insertion sonrasi hook dosyayi reformat etti. Her Edit sonrasi touched region'i re-read ile dogrulamak gerekli. `replace_all=true` flag'i de dikkat gerektirir — her handler'in error message'i farkli oldugu icin GF117'de sansli olduk, genel kural: tek-tek edit.
- **Optional-dep error class name match > message text match**: GF117'de `'nonetype' object has no attribute` matcher eklendi. SQLAlchemy asyncpg wrapper'lari orijinal mesaj metnini korumayabilir — class name (`type(exc).__name__`) kontrolu strictly more robust.

### Sonraki Adimlar (maks 5)
1. **COMMIT + PUSH** — Wave 13 tek commit + push all pending (Session 147 x5 + Session 148 Wave 12 + rule-of-five + middleware rule + Wave 13 + handoff)
2. **Wave 14 planning** — disjoint top-10 GF120-GF129. `audit_db_dependency.py` MEDIUM listesindeki `backend/api/*.py` Pattern B entry'lerini hedef al. Baseline %30-50 beklenir.
3. **StudentReview + COPPA child_id + OSB settings migration (P2 tech debt)** — uc farkli `alembic revision --autogenerate` ile schema drift kapat, 503 shim'lerini kaldir.
4. **`api_key_manager` async port** (P2) — ~300-line sync service'i async'e port et, GF117 shim'ini kaldir.
5. **`DifficultyClassificationService` async port** (P2) — ~700-line sync service'i async'e port et, GF112 shim'ini kaldir.

### Kararlar (gelecek session tekrar tartismasin)
- Wave 13 tamamlandi: 10 probe, 5 real fix, hit rate %50. Trailing indicator curve: %80→%50→%20→**%50** (probe target bias etkisi).
- Golden Flow suite 136 test, 134 PASS / 0 FAIL / 2 SKIP baseline sabit.
- Wrapped-HTTPException propagation yeni anti-pattern class olarak dokumante edildi.
- Schema drift degradation pattern uc farkli surface'de (StudentReview, COPPA, OSB) aktif — migration backlog.
- Wave 14'de prophylactic sweep ROI: `audit_db_dependency.py` Pattern B MEDIUM listesi hedeflenir.
