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

## B-20260421-02 — Auth + test + Docker

- `require_role` / `require_permission`: artık gerçek `AuthorizationDependency` döndürüyor (Depends ile kullanılabilir).
- `authenticate_user` tekil örnek + `AuthorizationDependency` içinde `Depends(authenticate_user)` — test `dependency_overrides` ile uyumlu.
- `AuthorizationContext` oluştururken boş `AuthenticationContext()` kaldırıldı; IP/UA istekten alınıyor.
- `test_api_agents.py`, `test_api_monitoring.py` düzeltildi; `docker compose up -d backend` + container içi `import chromadb` OK.
- Commit/push: bu blok sonrası.
