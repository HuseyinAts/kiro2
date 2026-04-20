# Batch ADIM 0 — 12 Router Durum Matrisi

**Tarih:** 2026-04-20  
**Ortam:** `localhost:5434` / `kiro2`, Docker `kiro2-backend` (healthy)  
**Kaynak plan:** `.cursor/plans/20260420_batch_router_adim0.md`  
**Prior knowledge:** `backend/_pilots/20260420_diary_api_state.md` (özetlendi; `users.id` VARCHAR, Alembic head `student_review_drift_001`, `DISABLED_ROUTERS` boş, diary drift pattern bilinir)  
**Kapsam:** Kod / migration / commit yok — salt tespit.

---

## Durma noktaları (plan §180)

| Kontrol | Sonuç |
|--------|--------|
| Docker | `kiro2-backend` Up (healthy) |
| Alembic heads | Tek: `student_review_drift_001 (head)` |
| `users.id` | `character varying` |
| `DISABLED_ROUTERS` | `{}` (boş — briefing “13 disabled” ile çelişki sürüyor) |
| UUID FK (router bağımlı tablolar) | `productive_failure_api` yolu `question_bank` + `topic_progress`: `student_id` / `id` VARCHAR. `sub_problems.id` UUID ayrı domain (reasoning); bu batch’te **PF API için K5 ihlali yok**. |

---

## Bölüm 1 — Özet matris

| # | Router | K1 Disabled? | K2 Mapping | K3 Log | K4 Tablolar | K5 Tip (id/user) | **Aşama** |
|---|--------|--------------|------------|--------|-------------|------------------|-----------|
| 1 | `api.v1.semantic_search` | Hayır | Evet — `("search", …)` | Registered `/api/v1/search` + `chromadb not available` WARNING | Chroma / embedding; zorunlu ORM tablosu yok | N/A | **D** |
| 2 | `api.clustering_api` | Hayır | Evet — `("search", …)` | Registered `/api/v1/clustering` | Embedding servis; PG şema zorunlu değil | N/A | **D** |
| 3 | `api.v1.content_recommendation` | Hayır | Evet — `("search", …)` | Registered `/api/v1/recommendations` | Chroma/servis ağırlıklı | N/A | **D** |
| 4 | `api.v1.duplicate_detection` | Hayır | Evet — `("search", …)` | Registered `/api/v1/duplicates` | Chroma/servis ağırlıklı | N/A | **D** |
| 5 | `api.productive_failure_api` | Hayır | Evet — `("learning", …)` | Registered `/api/v1/productive-failure` | `question_bank`, `topic_progress` mevcut | `topic_progress.student_id` varchar | **B** |
| 6 | `api.live_session_routes` | Hayır | Evet — `("learning", …)` | Registered `/api/v1/live-sessions` | 11 model tablosunun 11’i DB’de (`live_sessions` … `session_analytics`) | `live_sessions.id` / `host_id`, `session_participants.user_id` varchar | **E** |
| 7 | `api.v1.expert_agents_api` | Hayır | Evet — `("ai", …)` | Registered `/api/v1` | Agent / koordinasyon kodu; PG “feature tablosu” zorunlu değil | N/A | **D** |
| 8 | `api.vision_api` | Hayır | Evet — `("ai", …)` | Registered `/api/v1/vision` | LLM/Ollama; PG şema zorunlu değil | N/A | **D** |
| 9 | `api.offline_sync_api` | Hayır | Evet — `("learning", …)` | Registered `/api/v1/offline` | `question_bank` (+ FSRS akışı); çekirdek tablolar mevcut | `question_bank.id` varchar | **B** |
| 10 | `api.pwa_sync_api` | Hayır | Evet — `("learning", …)` | Registered `/api/pwa-sync-api` | `exam_sessions`, `student_answers` mevcut | `exam_sessions.id` / `student_id` varchar | **B** |
| 11 | `api.revolutionary_features` | Hayır | Evet — `("ai", …)` | Registered `/api/v1/revolutionary-features` | Servis ağırlıkla algoritmik (DB opsiyonel) | N/A | **E** |
| 12 | `api.team_challenges_api` | Hayır | Evet — `("integrations", …)` | Registered `/api/v1/challenges` | `services._deprecated.team_challenges` — kalıcı tablo yok | N/A | **E** |

**K2 notu:** `ROUTER_MAPPING` kategorisi `"search"` ama `router_registry.ROUTER_CATEGORIES` içinde `"search"` yok; [`backend/routers/__init__.py`](backend/routers/__init__.py) bilinmeyen kategoriyi **`misc`**’e düşürüyor — log satırı `misc/semantic_search` görünmesi bu yüzden (kod hatası değil, registry eksikliği).

**K6 notu (live_session):** [`live_session_routes.py`](backend/api/live_session_routes.py) ham SQL’de `live_session_participants` geçiyor; DB’de tablo adı **`session_participants`** (model ile uyumlu). Bu drift runtime’da 500 üretebilir — pilot öncesi kod/DB hizası ayrı iş.

---

## Bölüm 2 — Aşama sınıflandırması

### Aşama A — Tablo yok, migration lazım

- Bu 12 router için **net A yok** (hepsi yüklü; çoğunda tablo ya yok sayılabilir ya da mevcut).

### Aşama B — Tablolar var, Alembic drift olası (diary pattern)

- `api.productive_failure_api` — `question_bank`, `topic_progress`; VARCHAR uyumlu. (Genel Alembic–şema drift’i prior knowledge’da anlatıldı.)
- `api.offline_sync_api` — çekirdek soru/öğrenci tabloları mevcut.
- `api.pwa_sync_api` — `exam_sessions`, `student_answers` mevcut.

### Aşama C — Tablolar var, kullanıcı FK’sinde UUID (bu batch K5 sorusu)

- **Yok** (incelenen PF / live_session / PWA anahtar kolonlarında `user_id`/`student_id` varchar).

### Aşama D — Dış bağımlılık (Chroma, agent deploy, vision runtime)

- `api.v1.semantic_search`, `api.clustering_api`, `api.v1.content_recommendation`, `api.v1.duplicate_detection` — log’da Chroma yok uyarısı.
- `api.v1.expert_agents_api` — `agents.*` import / deploy.
- `api.vision_api` — Ollama/Qwen vb. runtime.

### Aşama E — Belirsiz / manuel inceleme

- `api.live_session_routes` — tablolar tam; **SQL tablo adı** (`live_session_participants` vs `session_participants`) incelenmeli.
- `api.revolutionary_features` — hesaplama ağırlıklı; hangi endpoint’lerin kalıcı DB yazdığı ayrı tarama.
- `api.team_challenges_api` — deprecated in-memory servis; pilot “tablo + migration” modeline uymuyor.

---

## Bölüm 3 — Sonraki pilot önerisi

## Sonraki pilot önerisi

**En uygun:** `api.offline_sync_api` (alternatif eşdeğer: `api.pwa_sync_api`)  
**Neden:** Aşama **B** — Chroma/YOLO dışı; `question_bank` / `exam_sessions` zaten VARCHAR uyumlu; diary pilotundan küçük ve izole smoke test yazılabilir.  
**Aşama:** B  
**Tablo sayısı:** Offline paket FSRS + soru sorguları (çok tabloya dokunabilir ama endpoint yüzeyi dar).  
**Bilinmeyenler:** FSRS kart tablolarının tam listesi endpoint başına ayrı `psql` ile doğrulanmalı; Alembic drift genel kuralı geçerli.

İkinci sıra: `api.productive_failure_api` (B, fakat `topic_progress` önkoşulu — öğrencide kayıt yoksa `stored: false`).  
**Kaçınılması iyi:** `live_session_routes` (E, SQL adı riski) ve Chroma dörtlüsü (D) önce altyapı kararı.

---

## Bölüm 4 — Briefing düzeltme notları

| Konu | Bulgu |
|------|--------|
| “13 disabled router” | `DISABLED_ROUTERS` **boş**; `ROUTER_MAPPING` bu 12’yi içeriyor — briefing tarih / branch uyumsuz. |
| `search` kategorisi | `ROUTER_MAPPING` `"search"` kullanıyor; registry’de yok → log’da **`misc/`** prefix — dokümantasyonda “search kategorisi” denmemeli veya `ROUTER_CATEGORIES`’e `search` eklenmeli (kod değişikliği bu raporun dışında). |
| `pwa_sync_api` prefix | Log: `Registered … at /api/pwa-sync-api` — standart `/api/v1/...` ile hizalı değil; frontend/README uyumu kontrol edilmeli. |
| Token alanı | Diary pilotunda: `TokenYaniti.access_token` — briefing örnekleri `.token` kullanıyorsa güncellenmeli. |
| `sub_problems` / `solution_steps` | Briefing PF notu bu tabloları anıyor; **F9 servisi** `question_bank` + `topic_progress` kullanıyor — isim çakışması karışıklık yaratıyor. |

---

## Bölüm 5 — Ham komut özeti

- `docker ps` — backend healthy.  
- `docker exec … alembic heads` — tek head `student_review_drift_001`.  
- `psql` — `users.id` varchar.  
- `Select-String loader.py` — 12 router `ROUTER_MAPPING`’de.  
- `docker logs kiro2-backend` — 12 için `Registered …`; `semantic_search` için `chromadb not available` WARNING.  
- `psql information_schema` — live session 11 tablo + `sub_problems`/`solution_steps` (PF dışı) + `question_bank`/`topic_progress`/`exam_sessions`/`student_answers` doğrulandı.  
- `information_schema.columns` — seçilen `id` / `user_id` / `student_id` / `host_id` tipleri özetlendi (`sub_problems.id` uuid ayrı not).

---

*Çıktı yolu: `backend/_pilots/20260420_batch_router_state.md` — [`README.md`](README.md) isimlendirme kuralına uygun.*
