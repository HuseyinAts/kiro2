# KIRO2 — Capability Matrix (öğrenci tam kapsam planı)

**Plan:** `.cursor/plans/20260421_student_ready_autonomous_master.md`  
**Son güncelleme:** 2026-04-23 — F4: `POST /recommendations` + `/interaction` `user_id` IDOR kapatıldı; Dalga A script; Chroma smokes (GF37/38/47/150/152)  

Sütunlar: `Journey | API/Route | FE route | Son test (SHA) | Durum | Not`

| Journey | API/Route | FE route | Son test | Durum | Not |
|---------|-----------|----------|----------|-------|-----|
| J10–J13 Chroma | `api.v1.semantic_search`, clustering, recommendation, duplicate | TBD | F4+GF150/38/37/47/152 | **Yeşil (health+API smoke)** | F4: `content_recommendation` gövde `user_id` yalnızca kendisi veya staff (admin/super_admin/öğretmen). Profil `GET .../user/{id}/profile` rol kontrolü `UserRole` ile düzeltildi. Health: GF150. Arama GF38, clustering GF37, recommendations GF47, duplicates/check GF152. Tohum: `scripts/chroma_seed_kiro2_questions.py`. |
| J6 Offline | `api.offline_sync_api` | TBD | `c401e35` | **Yeşil** | `GET /api/v1/offline/health` (200, DB ping). Canlı: S1 `sync-status`, S2 `sync-package?limit=5` → `package_id` + `total_questions=5` (2026-04-23). `tests/unit/services/test_offline_sync_service.py` (6 PASS). Tam HTTP matrisi (S1–S6): `.cursor/plans/20260420_offline_sync_debt_2_RESULT.md` (Round 2). Plan: `.cursor/plans/20260423_offline_sync_debt_2_package_persist.md`. |
| J7 PWA | `api.pwa_sync_api` — `GET /api/v1/sync/health`, `GET /api/v1/push/health`, `POST /api/v1/sync/*`, `POST /api/v1/push/subscribe` | `backgroundSyncService.ts`, `sw.ts` | GF150, `2ec932f`+ | **Yeşil** (health) | Public path yok: `/api/pwa-sync-api` sadece eski log yanlışlığı; `routers/loader` kök `APIRouter` için boş prefix artık default’a dönmüyor. Subscribe stub, mutating uç F4. |
| Live session | `api.live_session_routes` | TBD | `44f9fc6` + GF150 | **Yeşil** (health) | `GET /api/v1/live-sessions/health` 200, `database: true` (GF150). ORM/ tablo: `session_participants` (önceki pilot); tam oturum journey F4+ |
| Router log | `loader` + `ROUTER_CATEGORIES` | — | — | **Yeşil** | `"search"` kategorisi eklendi |
| J3 Search CRUD | `POST .../search` question_crud | TBD | — | Yeşil | Zaten `Depends(get_current_user)`; eski TODO kaldırıldı |

**Durum:** Kırmızı / Sarı / Yeşil — plan §3 terimleri.

**Chroma notu:** Ortamda `CHROMADB_HOST` tanımlıysa duplicate / content recommendation / semantic search v1 **HttpClient** kullanır; `GET /api/v1/duplicates/health`, `GET /api/v1/recommendations/health`, `GET /api/v1/search/health` yanıtlarında `chroma_connection_mode`. MCP: `health_check` / `chromadb://health` JSON’da aynı alan (`http` \| `embedded`). Dev: `docker compose -f docker-compose.dev.yml --profile chroma up` + `.env` içinde `CHROMADB_HOST=chroma` (ağda `chroma:8000`, host `localhost:8001`).
