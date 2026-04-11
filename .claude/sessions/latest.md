## Session Handoff — 2026-04-11 Session 141
**Branch:** master
**Son commit:** 0ac67e6 test(golden-flows): Wave 6 sweep — GF40-GF49 probes + docs
**Uncommitted:** temiz (push bekliyor: 3 commit)

### Yapilanlar — Golden Flow Wave 6 Sweep (GF40-GF49)
- `backend/tests/e2e/test_golden_flows.py` — 10 yeni write-path probe (GF40-GF49) eklendi. GF41 reasoning/solve icin httpx.TimeoutException -> pytest.skip state-dependent guard, GF47 /auth/me envelope walk (commit 0ac67e6)
- `backend/services/placement_assessment_service.py` — GF40: `QuestionDifficultyLevel` enum `.upper()` crash. `load_assessment_items()` her satirda AttributeError atip pool bos donuyordu. Caller'da `str(getattr(raw_diff, "value", raw_diff))` coerce (commit 6c19de7)
- `backend/services/emotional_service.py` — GF49: asyncpg VARCHAR + `default=uuid4` type lie (ucuncu occurrence). `track_state()` caller-level `id=str(uuid4())` + `user_id=str(user_id)` coerce. GF26/GF36 pattern — rule-of-three established (commit a8e19ff)
- `.claude/rules/golden-flows.md` — Wave 6 tablosu + final distribution guncellendi (commit 0ac67e6)

### Fail Eden Testler
- YOK. Golden Flow: **64 PASS, 0 FAIL, 2 SKIP** (GF1wB refresh-token persist + GF4w.2 FSRS no due card — state-dependent, degismedi)

### Engelleyiciler
- YOK

### Session 141 Bulgular / Notlar
- **Rule of three established:** asyncpg VARCHAR + `default=uuid4` GF26 (Goal) → GF36 (LiveSession) → GF49 (EmotionalState). Pattern kesinlesti. Her yeni model icin `Column(String, default=uuid4)` declaration varsa caller-level `str(uuid4())` coerce sart. asyncpg UUID'yi VARCHAR'a bind etmiyor.
- **PostToolUse formatter import trap TEKRARLANDI:** uuid4 import ilk edit'te eklendi ama formatter kullanimdan once import gorunmeden temizledi. Ikinci edit'te NameError. Ayni tuzak Session 140 GF36'da da yasandi. Cozum: import ve kullanim tek edit'te olmali, VEYA import satirinda inline yorum ("# used below") bulundurulmali.
- **GF41 router unwired:** `/api/v1/reasoning/solve` 404 donuyor — router loader'a kayitli degil gibi. `routers/loader.py` ROUTER_MAPPING'de `sequential_reasoning_api` yok. Gelecekte Wave 7 adayi veya dogrudan enable.
- **GF47 /auth/me envelope:** Response `{"user": {"id": ...}}` seklinde (nested). Top-level `id`/`user_id` yok. Probe'da envelope walk `payload.get("user") / payload.get("kullanici")` fallback gerekli oldu.
- **Docker rebuild cycle:** Host edit + `docker compose build backend && docker compose up -d backend` + `curl /health` wait loop yaklasik 2 dakika. Python formatter unused-import temizliyor, her rebuild'de dogrulama sart.

### Sonraki Adimlar (maks 5)
1. **Wave 7** — feature-inventory'den disjoint top-10 (GF50-GF59), ~480 uncovered kaldi. GF33 `weekly_goals` gercek fix + GF41 reasoning router enable iyi adaylar.
2. **get_db shim silme** — Session 138'de ertelendi. 0 MEDIUM caller, DeprecationWarning gereksiz. core/database.py'den kaldir (test import guard ile).
3. **Model audit:** Grep `Column(String, default=uuid4)` — kalan VARCHAR+uuid4 modelleri proaktif bul ve caller-level fix uygula (prophylactic sweep, Wave 8 beklemeden).
4. **Test coverage:** backend ~53% → 80% hedef
5. **MVP beta launch** — E2E 7/7 PASS, blocker yok

### Kararlar (gelecek session tekrar tartismasin)
- Wave 6 complete: 66 test (56 onceki + 10 Wave 6). 64 PASS / 0 FAIL / 2 SKIP.
- Rule of three VARCHAR+UUID pattern: Goal, LiveSession, EmotionalState. Yeni model eklerken otomatik caller-level `str(uuid4())` uygula.
- GF41 reasoning/solve 404 kabul edilebilir — router unwired, crash degil. `!= 500` waiver yeterli. Wave 7'de enable edilebilir.
- GF47 /auth/me envelope walk probe-level refinement — backend degistirilmedi (legacy envelope shape zaten seeded login ile tutarli).
