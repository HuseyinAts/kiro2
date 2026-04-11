## Session Handoff — 2026-04-11 Session 145
**Branch:** master
**Son commit:** 20808ae chore: session 137 handoff (Wave 10 commit pending)
**Uncommitted:** 7 dosya (golden-flows.md, MEMORY.md, latest.md, learning_style.py, hybrid_question_generation.py, curriculum_compliance.py, instant_feedback_api.py, advanced_reports.py, team_challenges_api.py, test_golden_flows.py)

### Yapilanlar — Golden Flow Wave 10 Sweep (GF80-GF89) — 8/10 bug (80% hit rate, rekor)
- `backend/tests/e2e/test_golden_flows.py` — 10 yeni probe (GF80-GF89) disjoint top-10'dan.
- **GF81/GF82 fix** `backend/api/learning_style.py` — 2 handler (update_behavioral_data, submit_questionnaire) bare `except Exception` `verify_student_access`'in HTTPException(403)'ünü 500'e wrap ediyordu. `except HTTPException: raise` guard eklendi.
- **GF83 fix** `backend/api/hybrid_question_generation.py` — API key yoksa fail-fast 503 eklendi. Ayrıca `except HTTPException: raise` guard.
- **GF85 fix** `backend/api/curriculum_compliance.py` — `get_curriculum_system()` `await get_database_service()` çağrıyordu ama `get_database_service` FastAPI async generator (`yield`). `TypeError: object async_generator can't be used in 'await'`. Handler try bloğundan ÖNCE patlıyordu → HTTPException guard çalışmadı. Fix: generator wrapper'ları bypass et, `db_manager` + `cache_manager` singleton'larını doğrudan kullan.
- **GF86/GF87 fix** `backend/api/instant_feedback_api.py` — 4 handler sync `def` + `Depends(get_db)` + `AsyncSession` backing = `greenlet_spawn has not been called`. Tam rewrite: `async def` + `get_async_session` + `select()` + `await db.execute()` + tüm 4 handler'a `except HTTPException: raise`. **Kritik ders: `get_db` deprecated SYNC shim'dir. Handler'ı async yapmak YETMEZ, dependency'yi de `get_async_session`'a çevir.**
- **GF88 fix** `backend/api/advanced_reports.py` — `generate_pdf_report` bare except `get_advanced_exam_report`'un 404'ünü 500'e wrap ediyordu. Guard eklendi.
- **GF89 fix** `backend/api/team_challenges_api.py` — 5 adet `from ..services.team_challenges import` relative import beyond top-level. Service `_deprecated/` altına taşınmış. Fix: `from services._deprecated.team_challenges import`. 3 write handler'da `int(current_user.id)` → `str(current_user.id)`.
- `.claude/rules/golden-flows.md` — Wave 10 tablosu (GF80-GF89) + rule-of-eight commentary + `get_db` sync shim trap commentary eklendi.

### Fail Eden Testler
- YOK. **106 test → 104 PASS, 0 FAIL, 2 SKIP** (GF1wB refresh-token persist + GF4w.2 FSRS no due card — state-dependent, degismedi)

### Engelleyiciler
- YOK

### Session 145 Bulgular / Notlar
- **Rule-of-eight**: Optional-dep/HTTPException propagation anti-pattern artık 8 confirmed occurrence: GF22/GF56/GF57/GF77/GF81/GF82/GF85/GF88. Bare `except Exception` kullanan HER handler'a `except HTTPException: raise` guard eklenmeli. Pre-commit lint kuralı yazılabilir.
- **`get_db` sync shim trap**: `core.database.get_db` deprecated shim (docstring warning: "Any `db: AsyncSession = Depends(get_db)` with an `await db.*` call will raise MissingGreenlet"). GF86/87 fix ikinci iterasyonda anlaşıldı: sync `def` → `async def` YETMEZ, `Depends(get_db)` → `Depends(get_async_session)` de gerekli. Pattern aynı GF7wA/GF8wA sync-handler+async-session trap ama bir layer daha derinde.
- **Async generator dep misuse**: GF85 root cause. `await get_database_service()` çağrıldı ama dep `async def` + `yield` (async generator). TypeError handler try bloğundan önce FastAPI dep resolution'da patladı. Starlette default 500 "Dahili sunucu hatası" dönüyordu — handler'ın kendi hata mesajı değil. İpucu: Docker logs full traceback'i göster.
- **Wave 10 hit rate rekor**: 10 probe → 8 gerçek bug (80%). Önceki wave'ler 2-5 bug. Sebep: 6 farklı anti-pattern denk geldi (3× bare-except, 1× async-generator-dep, 1× `get_db` shim misuse, 1× relative import, ADHD rule ve asyncpg VARCHAR sweeps önceki wave'lerde yakalandı).
- **Docker cp + restart iteration**: Wave 8-9'daki gibi. `docker restart kiro2-backend` 10s, kod COPY ile bake edildi. `docker cp file kiro2-backend:/app/... && docker restart kiro2-backend` pattern'i.

### Sonraki Adimlar (maks 5)
1. **Wave 11** — feature-inventory'den disjoint top-10 (GF90-GF99), ~440 uncovered kaldı. 2-5 bug bekleniyor. Rule-of-eight ile bazı sweep'ler hızlanabilir.
2. **Rule-of-eight pre-commit lint**: `grep "except Exception" backend/api/*.py` + manuel `except HTTPException: raise` kontrol. Otomatik linter yaz.
3. **`get_db` sweep**: `grep "Depends(get_db)" backend/api/*.py | grep -l "async def"` — sync shim ile async handler eşleşmelerini bul. 98 MEDIUM tech debt (Session 137) içinde benzer dosyalar var.
4. **GF33 `weekly_goals` gercek fix** — Session 140 bonus, hala pending.
5. **MVP beta launch** — E2E 7/7 PASS, blocker yok.

### Kararlar (gelecek session tekrar tartismasin)
- Wave 10 complete: 106 test (96 onceki + 10 Wave 10). 104 PASS / 0 FAIL / 2 SKIP.
- Rule-of-eight kuruldu: bare `except Exception` → MUTLAKA `except HTTPException: raise` guard öncesi.
- `get_db` yasaklı (sync shim). Yeni async handler'lar `get_async_session` kullanmak zorunda.
- Async generator dep `await ...()` ile çağrılamaz — `Depends(...)` veya `async for x in gen(): ...` kullan.
- GF85 çözümü şablon: Optional global singleton wrapper ihtiyacında `get_database_service()`/`get_cache_service()` wrapper'ları yerine module-level `db_manager` / `cache_manager` doğrudan kullan.
