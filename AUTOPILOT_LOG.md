# AUTOPILOT_LOG — öğrenci tam kapsam

**Plan:** `.cursor/plans/20260421_student_ready_autonomous_master.md`

## B-20260421-00 — F0/F3 kısmi + F1 başlangıç

- **Faz:** F0 envanter dosyası + F3 (`live_session`) + F1 (chromadb paket + volume).
- **Yapılan:**
  - `ROUTER_CATEGORIES` içine `"search"` eklendi (`backend/routers/__init__.py`).
  - `live_session_routes.py`: `live_session_participants` → `session_participants` (ORM `SessionParticipant.__tablename__` ile uyum).
  - `requirements-minimal.txt`: `chromadb` bağımlılığı (Docker minimal image için).
  - `docker-compose.yml`: `kiro2-vector-db` volume → `/app/vector_db` kalıcılığı.
  - `question_crud_api.py`: geçmişte kalmış P0 TODO yorumu kaldırıldı (endpoint zaten `get_current_user`).
  - `CAPABILITY_MATRIX.md`, bu log, `backend/_pilots/20260421_chroma_stack_state.md` oluşturuldu.
- **Test:** `python -m pytest tests/fast/ -q --maxfail=5` — `test_api_agents.py` içinde 401/200 beklentisi uyumsuzluğu (5 fail); bu blokta değiştirilen dosyalarla doğrudan ilişkili görünmüyor. Hedefli test: `pytest tests/unit/test_zero_cov_batch6.py -q --tb=no -k session_participant` (isteğe bağlı).
- **Push:** `autopilot/student-ready-20260421` → `origin` (yeni dal, takip ayarlı).
- **Docker:** `docker compose build backend` tamamlandı (chromadb + volume değişikliği imaja yansıdı).

## B-20260421-01 — Otonom düzeltme (kullanıcıya iş bırakma yok)

- Dal + commit: `a1b12e9` (9 dosya).
- Push ve backend image rebuild bu oturumda çalıştırıldı.

**Sonraki blok (B-02):** Chroma import/smoke (container `up` ile) veya offline_sync plan adımı — ajan sürdürür.

## B-20260423-00 — Faz 3 / J7 (PWA) tek başlık: prefix + matris

- **Plan maddesi:** `20260421_student_ready_autonomous_master.md` §7 F3 + §6 J7.
- **Sorun:** `pwa_sync_api` modülü kökte birleşik `APIRouter()` kullanıyor; `router.prefix` boş string iken `RouterLoader` bunu yok sayıp registry/log’da `/api/pwa-sync-api` gibi yanıltıcı önek üretiyordu.
- **Düzeltme:** `backend/routers/loader.py` — `prefix` için `is None` ayrımı; boş string → `(multi-prefix module …)`; `pwa_sync_api` modül docstring: gerçek yolların `/api/v1/sync` ve `/api/v1/push` altında olduğu açık.
- **Matris / kanıt:** `CAPABILITY_MATRIX.md` J7 **Yeşil** (health + yol notu). Health kanıtı: GF150, offline commit `2ec932f` ile uyumlu stack.
- **Test:** `pytest tests/e2e/test_golden_flows.py::test_gf150_public_journey_health_probes_not_500` (önceki oturumda yeşil; bu diff sonrası tekrar).

## B-20260423-01 — F1 + F3 health: GF150 + matris (Chroma, live-sessions, clustering)

- **Plan:** `20260421_student_ready_autonomous_master.md` F1 (Chroma) + F3; DoD §4.3.
- **Ortam:** `localhost:8000`; Chroma: `chroma_connection_mode: embedded`, `chromadb_available: true`, `document_count: 0` (search).
- **Test:** `pytest tests/e2e/test_golden_flows.py::test_gf150_public_journey_health_probes_not_500` — **PASS** (0.94s).
- **Matris:** `CAPABILITY_MATRIX.md` — J10–J13 **Yeşil (health)**; **Live session** **Yeşil (health)**; F1 §8 full ingest/uygulama ayrı blok.

## B-20260423-02 — F1: Chroma 0.5 `PersistentClient` + semantic search 500 + GF38

- **Sorun:** (1) Eski `chroma.Client(Settings(persist=…))` + 0.4 sqlite → `KeyError: '_type'`; yanlış Docker volume adı (`kiro2-vector-db` vs `kiro2_kiro2-vector-db`). (2) Chroma 0.5 `query` embedding’leri ndarray → `if arr` boolean hatası. (3) slowapi: `@limiter.limit` + `SearchResponse` Pydantic dönüşü → `response: Response` zorunlu (GF24 pattern).
- **Düzeltme:** `core/chroma_client.py` → `PersistentClient`. `api/v1/semantic_search.py` → `_coerce_embedding_list`, MMR `is None` kontrolleri, `find_similar` flatten, üç route’a `response: Response`.
- **Araç:** `backend/scripts/chroma_seed_kiro2_questions.py` — `kiro2_questions` upsert (dev; volume izin: `chown` gerekirse).
- **Test (canlı 8000):** `test_gf38_search_questions_semantic_not_500` PASS, `test_gf150` PASS; `tests/unit/services/test_semantic_search.py` 20 PASS.

## B-20260423-03 — J10–J13: GF37/47/152 + matris

- **Amaç:** J10–J13 satırında sadece health değil, `clustering` + `recommendations` + `duplicates` mutating/okuma yollarının 500 vermediğini golden flow ile kilitlemek.
- **Ek test:** `test_gf152_duplicates_check_not_500` — `POST /api/v1/duplicates/check` (ADMIN), `test_golden_flows.py`.
- **Doğrulama (canlı):** `test_gf37_clustering_auto_not_500`, `test_gf47_recommendations_not_500`, `test_gf152_*` — **PASS**.
- **Matris:** `CAPABILITY_MATRIX.md` J10–J13 sütun Son test: `553bacf` + GF150/38/37/47/152.

## B-20260423-04 — F4: recommendations `user_id` + Dalga A script

- **Güvenlik:** `api/v1/content_recommendation.py` — `POST /` ve `POST /interaction` gövdesinde `user_id` artık öğrenci için yalnızca `current_user.id`; staff (`ADMIN`, `SUPER_ADMIN`, `TEACHER`) başka kullanıcı adına. `GET .../user/{user_id}/profile` rol eşlemesi `UserRole` enum ile (önceden `"admin"` küçük harf hatalı eşleşmiyordu).
- **Test:** `tests/unit/test_content_recommendation_idor.py` (3); `test_gf47_recommendations_not_500` PASS.
- **Dalga A:** `scripts/dalga_a_mutating_openapi.py` — OpenAPI mutating TSV.
- **Matris:** F4 notu J10–J13 satırında.

## B-20260421-02 — Auth + test + Docker

- `require_role` / `require_permission`: artık gerçek `AuthorizationDependency` döndürüyor (Depends ile kullanılabilir).
- `authenticate_user` tekil örnek + `AuthorizationDependency` içinde `Depends(authenticate_user)` — test `dependency_overrides` ile uyumlu.
- `AuthorizationContext` oluştururken boş `AuthenticationContext()` kaldırıldı; IP/UA istekten alınıyor.
- `test_api_agents.py`, `test_api_monitoring.py` düzeltildi; `docker compose up -d backend` + container içi `import chromadb` OK.
- Commit/push: bu blok sonrası.
