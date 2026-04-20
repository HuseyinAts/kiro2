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
- **Push:** Ortamda `origin` ve kimlik doğrulama hazırsa `git push` (kullanıcı/CI).

**Sonraki blok önerisi (B-01):** Chroma ADIM 0 doğrulama (import + `initialize()`), ardından ingest veya `HttpClient` + compose `chroma` servisi kararı.
