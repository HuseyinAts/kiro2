# Diary API pilot — ADIM 0 durum raporu

**Tarih:** 2026-04-20  
**Ortam:** localhost PostgreSQL 5434, `kiro2`, container `kiro2-backend`  
**Yürütücü:** Composer 2 (terminal doğrulama; uygulama kodu değiştirilmedi)

---

## Ön koşullar (plan §4)

| Kontrol | Bulgu |
|--------|--------|
| **Backup** | Başarılı. `C:\Users\husey\kiro2\backups\kiro2_pre_diary_20260420.dump` (custom format `-F c`, ~346 MB), `pg_dump` çıkış kodu 0. |
| **Git** | Dal: `master`, `origin/master`’dan **1 commit önde**. İzlenen dosyalarda değişiklik yok. **Untracked:** `.cursor/`, `.cursorignore`, `.cursorignore.txt.bak`, `AGENTS.md`. Planın “temiz çalışma ağacı” beklentisi için bu dosyaları commit/stash kararı size kalmış. |
| **Docker log (diary, son 200 satır)** | `docker logs ... --tail 200 \| Select-String diary` → eşleşme yok. |
| **Docker log (tam akış, diary_api)** | `Registered learning/diary_api at /api/v1/diary` (ör. 2026-04-20 03:43:46). Önceki günlerde `POST .../api/v1/diary/...` **200 OK** satırları var; diary ile ilgili import hatası görülmedi. |

---

## Görev 0.1 — Diary tabloları var mı?

**Evet — 8/8 `public` şemada mevcut:**

`diary_entries`, `diary_exports`, `emotional_states`, `goals`, `insights`, `learning_entries`, `peer_comparisons`, `reflections`

---

## Görev 0.2 — `users.id` ile FK / PK tipleri

| Soru | Bulgu | Anlamı |
|------|--------|--------|
| `users.id` tipi? | `character varying` | Briefing kuralı (VARCHAR user id) ile uyumlu. |
| Diary tablolarında `id`, `user_id`, `diary_entry_id`? | Hepsi `character varying` (UUID değil) | Eski disabled migration’daki UUID çelişkisi **bu veritabanında yok**; tablolar model ile uyumlu tipte. |

---

## Görev 0.3 — Alembic

| Soru | Bulgu | Anlamı |
|------|--------|--------|
| `alembic current` | `student_review_drift_001 (head)` | Tek head; çift head yok. |
| `alembic_version` | Tek satır: `student_review_drift_001` | |
| Repoda diary migration | Yalnızca `.disabled`: `20260119_add_diary_tables.py.disabled`, `c937128ce051_merge_diary_and_quality_gates.py.disabled` | **Mevcut revision grafiği diary oluşturmayı kaydetmiyor**; tablolar muhtemelen geçmişte elle/SQL veya artık takip edilmeyen yolla oluşturulmuş. **Yeni boş DB’ye sadece `alembic upgrade head` ile diary tabloları gelmeyebilir** — teknik borç / taze kurulum riski. |

---

## Görev 0.4 — Router yükleniyor mu?

| Soru | Bulgu | Anlamı |
|------|--------|--------|
| `api.diary_api` logda? | `✅ Registered learning/diary_api at /api/v1/diary` | Planın beklediği `api.diary_api` string’i logda yok; loader **`diary_api`** ve prefix **`/api/v1/diary`** ile kayıt veriyor. |
| `loader.py` | `"api.diary_api": ("learning", "api.diary_api")` mevcut | ROUTER_MAPPING’de tanımlı. |
| Briefing “13 disabled router” vs kod | `DISABLED_ROUTERS` boş + diary kayıtlı | **Bu ortamda** diary devre dışı değil; briefing ile kod **farklı zaman/branch** veya metin güncelliği çelişkisi; pilot için gerçek kaynak **canlı loader + DB**. |

---

## Aşama önerisi (insan onayı — plan §5 karar noktası)

| Aşama | Bu DB için uygun mu? | Not |
|--------|----------------------|-----|
| **A** (tablo yok) | Hayır | Tablolar var. |
| **B** (tablo var, doğru tip) | **Evet (çoğunlukla)** | VARCHAR PK/FK doğrulandı; yeni migration **zorunlu olmayabilir**. |
| **C** (yanlış tip / kısmi) | Hayır | UUID bulunamadı. |
| **D** | Kısmen | Alembic’te diary revision yok → “migration zaten uygulanmış” ifadesi **Alembic anlamında** tam doğru değil; **şema fiziksel olarak hazır**. |

**Özet öneri:** Runtime doğrulamaya (plan ADIM 5, `/api/v1/diary` yolları) geçin. Yeni kurulumlar için ileride “boş DB’de diary” hedefi varsa, ayrıca **idempotent** bir migration veya şema drift dokümantasyonu değerlendirilmeli (ADIM 2’yi otomatik atlamadan önce ürün kararı).

---

## Ham komut çıktısı özeti

- `psql` diary tablo listesi: 8 satır.  
- `psql` kolon sorgusu: 18 satır, tümü `character varying`.  
- `docker exec kiro2-backend alembic current` / `heads`: `student_review_drift_001`.  
- `docker logs kiro2-backend` (Select-String diary_api): başarılı kayıt satırları.

---

*Bu dosya plan `20260420_diary_api_activation.md` ADIM 0 çıktısıdır.*
