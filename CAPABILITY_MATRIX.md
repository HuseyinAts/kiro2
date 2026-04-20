# KIRO2 — Capability Matrix (öğrenci tam kapsam planı)

**Plan:** `.cursor/plans/20260421_student_ready_autonomous_master.md`  
**Son güncelleme:** 2026-04-21 — F0/F1 başlangıç  

Sütunlar: `Journey | API/Route | FE route | Son test (SHA) | Durum | Not`

| Journey | API/Route | FE route | Son test | Durum | Not |
|---------|-----------|----------|----------|-------|-----|
| J10–J13 Chroma | `api.v1.semantic_search`, clustering, recommendation, duplicate | TBD | 2392983+ | **Sarı** | SemanticSearchService.initialize True (container); HTTP smoke sırada |
| J6 Offline | `api.offline_sync_api` | TBD | — | Sarı | Borç planları: `.cursor/plans/20260423_offline_sync_debt_2_package_persist.md` |
| J7 PWA | `api.pwa_sync_api` | TBD | — | Sarı | Prefix `/api/pwa-sync-api` |
| Live session | `api.live_session_routes` | TBD | — | **Sarı→Yeşil aday** | `session_participants` tablo adı düzeltildi (kod) |
| Router log | `loader` + `ROUTER_CATEGORIES` | — | — | **Yeşil** | `"search"` kategorisi eklendi |
| J3 Search CRUD | `POST .../search` question_crud | TBD | — | Yeşil | Zaten `Depends(get_current_user)`; eski TODO kaldırıldı |

**Durum:** Kırmızı / Sarı / Yeşil — plan §3 terimleri.

**Chroma notu:** Şu an embedded `chromadb.Client(persist_directory=/app/vector_db)` yolu; ayrı Chroma server container henüz **HttpClient** ile bağlanmadı — F1 devamında `chromadb.HttpClient` + compose servisi değerlendirilecek.
