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

## B-20260423-17 — F4: moderasyon `check-status` IDOR (okuma)

- **Sorun:** `GET /api/v1/moderation/check-status/{user_id}` her giriş yapmış kullanıcıya **herhangi bir** `user_id` için mute/ban özetini döndürüyordu (gizlilik + hesap numaralandırma).
- **Düzeltme:** `moderation_api.check_user_status` — path `user_id` yalnızca `current_user.id` ile eşleşirse veya rol `ADMIN` / `SUPER_ADMIN` ise.
- **Test:** `tests/unit/test_moderation_check_status_auth.py` (3).

## B-20260423-16 — F4: `ask-question` student_id + `verify_student_access` rol normalizasyonu

- **Sorun:** `POST /api/v1/ask-question` gövdesindeki `student_id` performans takibi için kullanılıyordu; başka öğrenci ID’si ile çağrı engellenmiyordu. `verify_student_access` yalnızca `UserRole` enum eşlemesi yapınca ORM `User.role` string (`"teacher"`) personelde 403 üretiyordu.
- **Düzeltme:** `expert_agents_api.ask_question` — `student_id` doluysa `verify_student_access` + `get_db`. `learning_path_auth` — ayrıcalıklı roller için slug kümesi (`teacher` / `admin` / `super_admin` / `superadmin`) ve enum ile birleşik kontrol.
- **Test:** `tests/unit/test_learning_path_auth_roles.py` (3).

## B-20260423-15 — F4 Dalga B: `enhanced_chat` student_id IDOR

- **Sorun:** `POST /message` ve `POST /stream` gövdesindeki `student_id` doğrulanmıyordu; `GET /history/{student_id}` path parametresi sorguda yanlışlıkla yok sayılıp anonimde path ile sızıntı riski vardı. Ek uç: `message-with-attachment` öğrenci bağlamı taşımıyordu.
- **Düzeltme:** `verify_student_access` + `get_learning_path_profile_user_id` (`learning_path_auth`); geçmiş listesi öğrenme yolu profilinin platform `user_id` değeriyle (`chat_sessions.user_id`). Auth varken attachment için Form `student_id` zorunlu.
- **Golden:** `test_gf24_*` önce `POST /learning-path/create-profile` ile gerçek `student_id` alıyor.
- **Test:** `tests/unit/test_enhanced_chat_student_guard.py` (3).

## B-20260423-14 — F4: `rate_limit_config` rol → tier hizası

- **Sorun:** `get_user_tier_from_roles` yalnızca `"admin"` / `"superadmin"` string eşlemesi yapıyordu; **`super_admin`** ve **`UserRole` enum** öğeleri ADMIN tier’a düşmüyordu; öğretmen rolü FREE kalıyordu.
- **Düzeltme:** `backend/core/rate_limit_config.py` — slug normalizasyonu, `advanced_rate_limiter` ile aynı admin kümesi; `teacher` / `premium` slug + `is_premium` → PREMIUM.
- **Test:** `tests/unit/test_rate_limit_config.py` (5).
- **Not:** Önceki turda Redis tabanlı `resolve_user_tier_for_rate_limit` ile API/middleware hizalanmıştı; bu patch Task 51.2 yolunu da aynı kurallara çeker.

## B-20260423-13 — F4: enhanced users + quality-gates + content-management auth

- **enhanced_user_management_api:** `get_current_user` artık `AuthenticatedUser` ile hizalı; `require_admin` / `require_admin_or_self` **`UserRole`** (`ADMIN`, `SUPER_ADMIN`); self erişimde **`str(id)`** karşılaştırması.
- **quality_gates_api:** Override onay **`TEACHER`/`ADMIN`/`SUPER_ADMIN`**; silmede talep eden veya **`ADMIN`/`SUPER_ADMIN`** (önceden yalnızca tam `"admin"` string).
- **content_management:** Sahte **`MockUser`** ve `role in ["admin","teacher"]` kaldırıldı; gerçek **`AuthenticatedUser`** + staff seti.
- **Test:** `tests/unit/test_enhanced_user_management_auth.py` (4).

## B-20260423-12 — F4: analytics student path + rol enum sweep (video, bionic, content, ES)

- **analytics:** `GET /student/{student_id}` artık yalnızca `users.id` ile değil; **`verify_student_access`** ile learning-path `student_id` sahipliğini de kabul ediyor.
- **elasticsearch:** `GET /admin/indices/stats` — `UserRole` ile `ADMIN`/`SUPER_ADMIN`.
- **video_solution:** `AuthenticatedUser` + yükleme dışı işlemler için **`ADMIN`/`SUPER_ADMIN`** (önceden yalnızca `"admin"` string).
- **bionic_reading:** `/stats` ve tam cache temizliği — **`ADMIN`/`SUPER_ADMIN`**.
- **content_api:** makale güncelle/sil — yazar veya **`ADMIN`/`SUPER_ADMIN`**.
- **Test:** `tests/unit/test_analytics_student_access.py` (4).

## B-20260423-11 — F4: exam session IDOR + ES analytics + FERPA/COPPA

- **exam_performance:** `exam_session_id` ile dönen tüm detay/zayıflık/öneri/karşılaştırma GET’leri servis düzeyinde sahiplik kontrolü yapmıyordu; `_assert_exam_session_authorized` eklendi (sahip veya `TEACHER`/`ADMIN`/`SUPER_ADMIN`).
- **elasticsearch:** `GET /analytics/user/{user_id}` artık `UserRole` staff seti + `str` self; `super_admin` ve öğretmen dahil.
- **ferpa_coppa_compliance_api:** COPPA talep/doğrulama/geri çekme, çocuk durumu GET, FERPA talep ve erişim logu — veli+`parent_child`, personel veya öğrenci kendi kaydı; rastgele `child_id`/`consent_id` ile yazma/okuma engellendi.
- **Test:** `test_exam_performance_session_guard.py` (3), `test_ferpa_coppa_guards.py` (1).

## B-20260423-10 — F4 Dalga B: parent-social IDOR + IRT recommend + exam trends

- **parent_social_api:** `ParentSocialSettings` ilk GET/PUT ile rastgele `student_id` için satır açılıyordu; aktivite/bayrak uçları bu satıra bakarak veri dönebiliyordu. Tüm `{student_id}` yollarında **`UserRole.PARENT`** + **`parent_child` onaylı kayıt** zorunlu.
- **irt_morfoloji:** `POST /recommend-questions` gövde `student_id` için staff, `users.id` eşleşmesi veya `verify_student_access`.
- **exam_performance:** `improvement-trends` yetkisi `role.value != "admin"` yerine **`TEACHER`/`ADMIN`/`SUPER_ADMIN`** + `str` id karşılaştırması.
- **Test:** `test_parent_social_access.py` (3), `test_irt_morfoloji_recommend_idor.py` (2), `test_exam_performance_improvement_auth.py` (1).

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
