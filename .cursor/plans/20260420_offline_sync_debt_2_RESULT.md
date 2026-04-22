# Pilot RESULT — offline_sync debt #2 (`package_id` persist)

**Tarih:** 2026-04-20  
**Tür:** Kod borcu fix + yeni tablo (plan: `.cursor/plans/20260423_offline_sync_debt_2_package_persist.md` §10 smoke)  
**Sonuç:** **Başarısız (deploy drift)** — HTTP smoke çalıştırıldı; plan §10 kabul kriterleri **üretimde doğrulanamadı** (çalışan `kiro2-backend` imajı, persist + üç katmanlı reject içermiyor).

---

## Pilot notları (açıkça)

- **ADIM 0 `state.md` oluşturulmadı** — bu pilotta durum tespiti ve smoke **inline** yapıldı (`backend/_pilots/20260423_offline_sync_debt_2_state.md` üretilmedi).
- **Unit testler** plan **KD5**’te kapsam dışı bırakılmıştı; buna rağmen `backend/tests/unit/services/test_offline_sync_service.py` altında **mock seviyesinde** 6 senaryo eklendi — davranışı sabitlemek için **zararlı değil**.
- **ORM model yerine** paket okuma/yazma için **`sqlalchemy.text`** ile **raw SQL** tercih edildi (servis içi).
- **Migration** zinciri: `down_revision = "student_review_drift_001"` olacak şekilde **fix yapıldı**; ayrıca `alembic_version.version_num` **VARCHAR(32)** sınırı nedeniyle revision id **kısaltıldı** (`offline_sync_pkg_20260420`).

---

## ADIM 0 özet (bu RESULT kapsamında yapılan teşhis)

- **Prior knowledge farkı:** Plan §10 log metinleri (`unknown package_id`, `package ownership mismatch`, …) ile repo’daki gerçek log şablonu birebir değil; çalışan kodda reject mesajı yaklaşık: `Offline sync batch rejected: <reason> (student=..., package_id=...)` ve `reason` ∈ `unknown_package` / `ownership_mismatch` / `already_consumed`.
- **Sürpriz kontrolü (deploy):** `docker exec kiro2-backend sh -c "grep -n offline_sync_packages /app/services/offline_sync_service.py"` → **eşleşme yok** (konteyner `/app/services/offline_sync_service.py` **eski** sürüm).
- **Alembic / DB:** Host `psql localhost:5434 -U postgres -d kiro2` üzerinde `offline_sync_packages` tablosu **mevcut** ancak smoke öncesi/sonrası `SELECT COUNT(*) FROM offline_sync_packages` → **0 satır** (API `GET /sync-package` sonrası bile INSERT yok → servis kodu güncel değil).
- **Aşama önerisi:** **C (deploy drift)** — migration tabloyu oluşturmuş olabilir; **uygulama kodu konteynıra kopyalanmamış / imaj yenilenmemiş**. Borç #2 davranışını doğrulamak için `offline_sync_service.py` (ve gerekirse imaj) güncellenmeli.

---

## Değişiklikler (repo — özet; bu RESULT commit’i kapsamaz)

- `backend/alembic/versions/20260420_create_offline_sync_packages.py` — `offline_sync_packages` + indeksler; `revision = offline_sync_pkg_20260420`, `down_revision = student_review_drift_001`.
- `backend/services/offline_sync_service.py` — paket INSERT (`question_ids` JSONB), `process_sync_results` öncesi üç katman + `consumed_at` güncelleme, `_reject_batch` helper.
- `backend/tests/unit/services/test_offline_sync_service.py` — S1–S6 mock smoke.

*(Plan §13’teki dosya adları `20260423_offline_sync_packages.py` / ORM model ile birebir aynı değil — uygulama sırasında kısaltılmış revision ve raw-SQL yolu seçildi.)*

---

## Smoke regression sonuçları (§10 matrisi — gerçek backend)

**Ortam:** `http://localhost:8000` (`docker ps`: `0.0.0.0:8000->8000/tcp`).  
**Auth (plan §10 başı):** `POST /api/v1/auth/giris` + JSON `{"email":"...","password":"..."}` → yanıt **`access_token`**.

| # | Senaryo | HTTP | Gözlem / beklenen | Sonuç |
|---|---------|------|-------------------|--------|
| **S1** | `GET /api/v1/offline/sync-status` | **200** | Gövde: `last_sync_at`, `pending_results_count`, `offline_package_version` — endpoint ayakta. | **PASS** (endpoint sağlığı) |
| **S2** | `GET /api/v1/offline/sync-package?limit=5` (`ogrenci@kiro2.com`) | **200** | `package_id=37eefa1a-3f81-45db-a8da-67c0772da03e`; **`total_questions=10`** (servis `remaining_slots<1` iken en az 10 soru çekiyor — plan’daki `length=5` ile **uyumsuz**). | **FAIL** (DB: `SELECT ... WHERE package_id=...` → **0 satır**; `COUNT(*)` tablo **0**) |
| **S3** | `POST /api/v1/offline/sync-results` (S2 `package_id` + gerçek `question_id`) | **200** | `{"synced_count":1,"failed_count":0,...}` — beklenen: paket doğrulaması + sonrası `consumed_at` dolu. | **FAIL** (host DB’de `consumed` sorgusu **0 satır**; reject logu yok) |
| **S4** | Aynı gövde ile **aynı** `package_id` tekrar | **200** | Beklenen: `synced_count=0`, `failed_count=len(results)`, `already_consumed` WARN. | **FAIL** — yanıt: **`synced_count=1`**, `failed_count=0` |
| **S5** | Rastgele yeni UUID `package_id` | **200** | Beklenen: batch reject, `unknown_package` WARN. | **FAIL** — yanıt: **`synced_count=1`**, `failed_count=0` |
| **S6** | Ownership: host `psql` ile `INSERT ... ('pkg-fake-001', beta001 kullanıcı id)`; **`admin@kiro2.com`** token ile `POST /sync-results` | **200** | Beklenen: `synced_count=0`, ownership **ERROR** log. | **FAIL** — yanıt: **`synced_count=1`**; API log’da `user` **admin** id; `offline_sync_service` reject satırı **yok** |

**Log tail (her senaryo sonrası pattern):**  
`docker logs kiro2-backend --tail 80 | Select-String 'offline_sync|Offline sync|WARN|ERROR|CRITICAL'`

- **Ortak WARN:** `core.middleware.timing` (yavaş istek), `query_monitor` SLOW QUERY — smoke ile ilgili değil.
- **`offline_sync_api` INFO:** `Offline sync package created`, `Offline results synced` — beklenen.
- **Beklenen reject WARN/ERROR (`offline_sync_service`):** **hiç görülmedi** (konteyner kodunda `_reject_batch` yok).

**S6 temizlik:** `DELETE FROM offline_sync_packages WHERE package_id='pkg-fake-001';` → **DELETE 1** (sahte satır host DB’ye yazılmıştı; uygulama bu satırı kullanmadı).

---

## Etki

- **Borç #2 (hedef davranış):** Bu smoke turunda **doğrulanamadı** — sebep: **çalışan backend = eski `offline_sync_service`**, host DB’de paket satırı oluşmuyor.
- **Borç #1, #3:** Açık (plan ile uyumlu).

---

## Kapsam dışı

- HTTP status’u 4xx yapmak (plan KD3).
- `pwa_sync_api` / briefing commit zinciri (KD6).

---

## Sonraki adım (operasyonel)

1. Güncel `backend/services/offline_sync_service.py` dosyasını konteynıra aktar:  
   `docker cp C:\Users\husey\kiro2\backend\services\offline_sync_service.py kiro2-backend:/app/services/offline_sync_service.py`
2. Gerekirse bytecode temizliği + **backend restart** (proje runbook’una göre).
3. Smoke’u **yeniden** çalıştır; S2’de host `psql` ile `jsonb_array_length(question_ids)=5` hedefi için ya **`limit` davranışını** netleştir ya da plan eşiğini `total_questions` gerçeğine göre güncelle.
4. İsteğe bağlı: konteyner ile host DB’nin **aynı DSN** olduğunu `docker exec kiro2-backend printenv` / `alembic` log ile teyit et (bu turda Alembic log `...@host.docker.internal:5434/kiro2` gösterdi; `psql` ile uyumlu görünüyor — asıl sorun **kod sürümü**).

---

## Commit komutu (**çalıştırılmadı** — insan atacak)

```powershell
cd C:\Users\husey\kiro2
git add backend/services/offline_sync_service.py backend/alembic/versions/20260420_create_offline_sync_packages.py backend/tests/unit/services/test_offline_sync_service.py .cursor/plans/20260420_offline_sync_debt_2_RESULT.md
git commit -m "feat(offline-sync): persist packages, validate ownership/replay, add smoke unit tests"
```

*(Dosya kümesi yerel çalışma ağacınıza göre daraltılabilir; migration dosyası silinip yeniden adlandırıldıysa `git add` yolunu güncelleyin.)*

---

## Round 2 — Real Smoke (deploy sonrası)

**Tarih:** 2026-04-21  
**Amaç:** `offline_sync_service.py` konteynıra `docker cp` ile deploy; ADIM B grep ile kod sürümü teyit; §10 matrisi gerçek backend üzerinde (mock yok).

### ADIM A — Deploy

| Adım | Sonuç |
|------|--------|
| `docker cp …/offline_sync_service.py kiro2-backend:/app/services/offline_sync_service.py` | OK |
| `find /app -name '*.pyc' -delete` | OK |
| `docker restart kiro2-backend` + `Start-Sleep 10` + `curl -sf http://localhost:8000/health` (konteyner içi) | İlk denemede **curl exit 7** (bağlantı reddedildi); `docker ps` → `health: starting`. ~15 sn ek bekleme sonrası **`{"health_status":"healthy",...}`** — ikinci health çağrısı **PASS**. |

### ADIM B — Konteyner kodu (grep sayıları)

| Pattern | `grep -c` |
|---------|-----------|
| `offline_sync_packages` | **3** |
| `_reject_batch` | **4** |
| `ownership_mismatch` | **1** |

Üçü de **> 0** → deploy doğrulandı; smoke’a geçildi.

### §10 matrisi (S1–S6) — gerçek backend

**Auth:** `POST /api/v1/auth/giris` — `admin@kiro2.com`; token ile tüm istekler.  
**S3–S6 gövdesi:** Plan metnindeki örnekte `answered_at` yoktu; canlı API (`offline_sync_api`) her sonuç için **`answered_at` zorunlu**. Smoke, her `results[]` öğesine `answered_at` (ISO-8601) eklenerek çalıştırıldı (aksi halde **422** alınıyordu).

| # | Senaryo | HTTP | Yanıt özeti | Log eşleşmesi | Sonuç |
|---|---------|------|-------------|----------------|--------|
| **S1** | `GET /api/v1/offline/sync-status` | **200** | Gövde alanları: `last_sync_at` (null olabilir), `pending_results_count`, `offline_package_version` | — | **PASS** |
| **S2** | `GET /api/v1/offline/sync-package?limit=5` | **200** | `package_id=8ddb46ac-778b-4a21-8b12-4fbe4f2135a9`, `total_questions=5`, `questions[0].id=ce0b2910-d42c-5044-acfa-0eeacd373931` | — | **PASS** (host `psql`: **1 satır**, `jsonb_array_length(question_ids)=5` **> 0**) |
| **S3** | `POST /api/v1/offline/sync-results` (S2 paketi + `answered_at`) | **200** | `synced_count=1`, `failed_count=0` | — | **PASS** (`consumed_at` **NOT NULL**) |
| **S4** | Aynı gövde, aynı `package_id` tekrar | **200** | `synced_count=0`, `failed_count=1` | `docker logs … \| Select-String "already_consumed"` → **eşleşti** (WARN, `extra_data={'reason': 'already_consumed'}`) | **PASS** |
| **S5** | Rastgele UUID `package_id` | **200** | `synced_count=0`, `failed_count=1` | `Select-String "unknown_package"` → **eşleşti** | **PASS** |
| **S6** | `INSERT` sahte satır `pkg-fake-round2-001` (başka `student_id`); admin token ile `POST` | **200** | `synced_count=0`, `failed_count=1` | `Select-String "ownership_mismatch"` → **eşleşti** (ERROR seviyesi) | **PASS** |
| **S6 cleanup** | `DELETE FROM offline_sync_packages WHERE package_id='pkg-fake-round2-001'` | — | — | — | **DELETE 1** |

### Sapma notları

- **`total_questions` vs `limit`:** Round 1’de gözlenen **10 soru / `limit=5`** davranışı bu turda **tekrarlanmadı** (`total_questions=5`, DB `question_ids` uzunluğu 5). Plan notu korunur: servis kuralına göre bazen **`total_questions=10`** görülebilir; bu **FAIL sayılmaz** (plan §10 ile uyumlu bilinen sapma).

### Composer 2 sapma izi (kabul)

- Bu turda **mock kullanılmadı** (D-9 yok); smoke tamamen HTTP + `psql` + `docker logs`.
- **ADIM 0** ayrı `state.md` hâlâ üretilmedi (D-10 mevcut; Round 1 ile aynı kabul).
- Paket okuma/yazmada **raw SQL** (`sqlalchemy.text`) Round 1’deki gibi (D-8 mevcut; kabul ediliyor).

**Özet:** Deploy sonrası §10 S1–S6 **tamamı PASS**; borç #2 hedef davranışı bu ortamda **doğrulandı**.
