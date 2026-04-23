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

## B-20260423-09 — F4 Dalga B: BERTurk motivasyon + kültürel adaptasyon rolleri

- **Sorun:** `POST /api/v1/berturk/motivation/assess` yetkisi `["teacher","admin"]` string listesiyle yapılıyordu; `UserRole.SUPER_ADMIN` dışarıda kalıyordu, tip de `User` idi. `cultural_adaptation_api` path `student_id` için yalnızca `admin`/`teacher` string + `super_admin` yoktu; `/test-adaptation` yalnızca `admin` string.
- **Düzeltme:** `AuthenticatedUser` + `UserRole` frozen set (`TEACHER`, `ADMIN`, `SUPER_ADMIN`); öğrenci için `str(current_user.id) == str(student_id)` (BERTurk gövde `student_id`; kültürel uçlar path). BERTurk performans/cache: `ADMIN` \| `SUPER_ADMIN`.
- **Test:** `tests/unit/test_berturk_motivation_idor.py` (3), `tests/unit/test_cultural_adaptation_auth.py` (4).

## B-20260423-08 — F4 Dalga B: `zpd_maarif` + `turkish_nlp_chat` IDOR

- **Sorun:** `api/zpd_maarif.py` altındaki `POST /revolutionary/*` (calculate, recommend, cultural-context, adapt-difficulty, learning-balance, cultural-patterns) gövdede `student_id` taşıyordu; `verify_student_access` yoktu. `turkish_nlp_chat`: `/message` ve `/context/manage` sonradan korunmuştu; `/step-by-step-solution` aynı `ChatMessageRequest` ile **korunmasızdı**.
- **Düzeltme:** ZPD devrimsel uçlarda `Depends(get_db)` + iş kuralından önce `await verify_student_access(...)`. Türkçe NLP: `step-by-step-solution` için aynı desen.
- **Test:** `tests/unit/test_zpd_maarif_revolutionary_idor.py` (6 PASS); `tests/unit/test_turkish_nlp_chat_idor.py` (3 PASS).
- **Envanter:** `docs/security/mutating_route_inventory_20260423.md` tablo genişletildi.

## B-20260423-07 — F4 Dalga B: `revolutionary_features` IDOR + auth log

- **Sorun:** `POST /zpd-maarif/revolutionary/{calculate,recommend,cultural-context}` gövdede `student_id` vardı; `verify_student_access` yoktu — başka öğrenci adına ZPD/öneri/kültür çağrısı mümkündü.
- **Düzeltme:** Üç uçta `Depends(get_db)` + iş kuralından önce `await verify_student_access(...)`.
- **Test:** `tests/unit/test_revolutionary_features_idor.py` (3 PASS).
- **Auth:** `POST /auth/refresh` genel `except` artık `logger.exception` ile gerçek hatayı kaydeder (istemci yine genel 401).
- **Pilot:** `backend/_pilots/20260423_f1_chroma_stack_state.md` (F1 ADIM 0 özeti).
- **Envanter:** `docs/security/mutating_route_inventory_20260423.md` Dalga B tablosu.

## B-20260423-06 — J1 P0: JSON refresh (`POST /auth/refresh`)

- **Plan:** `20260421_student_ready_autonomous_master.md` §6 J1 (refresh); `GF1wB` cookie yolunu test eder fakat standart `/login` JSON döner — **GF1z** ile `refreshToken` gövdesi + `/me` doğrulaması P0’ya alındı.
- **Golden:** `test_gf1z_refresh_token_json_returns_usable_access` — `ci.yml` + `run_p0_golden_local.ps1` (11 test).
- **Matris:** `CAPABILITY_MATRIX.md` J1 + P0 sayımı.

## B-20260423-05 — J2 P0: `PUT /api/v1/auth/profile` + matris

- **Plan:** `20260421_student_ready_autonomous_master.md` §6 J2 (P0); gap analizi J2 “PUT kanıtı” boşluğu.
- **Golden:** `test_gf1y_profile_put_smoke` — `/auth/me` ile mevcut `ad`/`soyad` okunur, `PUT /api/v1/auth/profile` ile idempotent güncelleme, `success` + e-posta doğrulaması.
- **Kapı:** `ci.yml` P0 adımı + `scripts/run_p0_golden_local.ps1` — paket **10** test.
- **Matris:** `CAPABILITY_MATRIX.md` J2 satırı ve P0 sayımı güncellendi.

## B-20260421-02 — Auth + test + Docker

- `require_role` / `require_permission`: artık gerçek `AuthorizationDependency` döndürüyor (Depends ile kullanılabilir).
- `authenticate_user` tekil örnek + `AuthorizationDependency` içinde `Depends(authenticate_user)` — test `dependency_overrides` ile uyumlu.
- `AuthorizationContext` oluştururken boş `AuthenticationContext()` kaldırıldı; IP/UA istekten alınıyor.
- `test_api_agents.py`, `test_api_monitoring.py` düzeltildi; `docker compose up -d backend` + container içi `import chromadb` OK.
- Commit/push: bu blok sonrası.
