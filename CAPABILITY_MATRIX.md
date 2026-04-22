# KIRO2 — Capability Matrix (öğrenci tam kapsam planı)

**Plan:** `.cursor/plans/20260421_student_ready_autonomous_master.md`  
**Son güncelleme:** 2026-04-23 — Faz 3 / J7: PWA yolları netleştirildi, `loader` boş prefix log düzeltmesi  

Sütunlar: `Journey | API/Route | FE route | Son test (SHA) | Durum | Not`

| Journey | API/Route | FE route | Son test | Durum | Not |
|---------|-----------|----------|----------|-------|-----|
| J10–J13 Chroma | `api.v1.semantic_search`, clustering, recommendation, duplicate | TBD | GF150 (health) | **Sarı** | `GET /api/v1/search|duplicates|recommendations/health` + `chroma_connection_mode` (`core/chroma_client.py`) |
| J6 Offline | `api.offline_sync_api` | TBD | GF150 | Sarı | `GET /api/v1/offline/health` (auth yok, `SELECT 1`); borç: `.cursor/plans/20260423_offline_sync_debt_2_package_persist.md` |
| J7 PWA | `api.pwa_sync_api` — `GET /api/v1/sync/health`, `GET /api/v1/push/health`, `POST /api/v1/sync/*`, `POST /api/v1/push/subscribe` | `backgroundSyncService.ts`, `sw.ts` | GF150, `2ec932f`+ | **Yeşil** (health) | Public path yok: `/api/pwa-sync-api` sadece eski log yanlışlığı; `routers/loader` kök `APIRouter` için boş prefix artık default’a dönmüyor. Subscribe stub, mutating uç F4. |
| Live session | `api.live_session_routes` | TBD | GF150 | **Sarı→Yeşil aday** | `GET /api/v1/live-sessions/health` (auth yok, `SELECT 1`); `session_participants` |
| Router log | `loader` + `ROUTER_CATEGORIES` | — | — | **Yeşil** | `"search"` kategorisi eklendi |
| J3 Search CRUD | `POST .../search` question_crud | TBD | — | Yeşil | Zaten `Depends(get_current_user)`; eski TODO kaldırıldı |

**Durum:** Kırmızı / Sarı / Yeşil — plan §3 terimleri.

**Chroma notu:** Ortamda `CHROMADB_HOST` tanımlıysa duplicate / content recommendation / semantic search v1 **HttpClient** kullanır; `GET /api/v1/duplicates/health`, `GET /api/v1/recommendations/health`, `GET /api/v1/search/health` yanıtlarında `chroma_connection_mode`. MCP: `health_check` / `chromadb://health` JSON’da aynı alan (`http` \| `embedded`). Dev: `docker compose -f docker-compose.dev.yml --profile chroma up` + `.env` içinde `CHROMADB_HOST=chroma` (ağda `chroma:8000`, host `localhost:8001`).
