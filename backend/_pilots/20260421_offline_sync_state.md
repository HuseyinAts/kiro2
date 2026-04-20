# Offline Sync API pilot — ADIM 0 durum raporu

**Tarih:** 2026-04-21  
**Ortam:** localhost PostgreSQL 5434, `kiro2`, Docker `kiro2-backend`  
**Yürütücü:** Composer 2 (salt okuma + terminal; **kod / migration / HTTP / git yok**)  
**Plan:** `.cursor/plans/20260421_offline_sync_activation.md` (yalnızca ADIM 0)  
**Prior knowledge:** `20260420_diary_api_state.md`, `20260420_batch_router_state.md` — `users.id` VARCHAR, `DISABLED_ROUTERS` boş, Alembic head `student_review_drift_001`, auth `POST /api/v1/auth/giris`, token alanı **`access_token`** bu raporda yeniden doğrulanmadı.

---

## Ön koşullar (activation plan §5)

| Kontrol | Bulgu |
|--------|--------|
| **Backup** | Bu ADIM 0 turunda çalıştırılmadı (talimat: insana bırakıldı). |
| **Docker** | Log çekiminde backend erişilebilir (önceki pilotlarla uyumlu). |
| **Git** | Bu turda `git` kullanılmadı. |

---

## Görev 0.1 — Router / import / log (`offline`)

| Soru | Bulgu | Anlamı |
|------|--------|--------|
| Router kaydı? | `Registered learning/offline_sync_api at /api/v1/offline` (2026-04-12, 2026-04-20, 2026-04-21 benzeri satırlar) | Import hatası yok; modül yükleniyor. |
| ImportError / Failed to import? | **Yok** | Kırmızı bayrak yok. |
| Çalışma zamanı uyarıları? | Eski loglarda `offline_sync_service` → `Question not found or inactive: gf97-synthetic-qid`; ardından `Offline results synced` ve **HTTP 200** (`POST /api/v1/offline/sync-results`) | Geçersiz/sentetik `question_id` ile `failed=1` senaryosu görülmüş; servis patlamıyor. |

---

## Görev 0.2 — `offline_sync_service.py` davranış özeti (6 madde)

Kaynak: [`backend/services/offline_sync_service.py`](backend/services/offline_sync_service.py) (tam dosya okundu).

1. **`build_sync_package` okuduğu tablolar (ORM):** `FSRSCard` → fiziksel tablo **`fsrs_cards`**; `QuestionBankItem` → **`question_bank`**. Opsiyonel filtrede `SubjectArea` enum (`models.enums_db`) kullanılıyor. **`topic_progress` sorgulanmıyor** (batch raporundaki “topic_progress önkoşulu” bu servis için geçerli değil; rastgele soru `question_bank` + `is_active`).

2. **`process_sync_results` yazdığı tablolar:** Doğrudan **INSERT yok**. Akış: `question_bank` üzerinde **SELECT** (doğrulama); eşleşen **`fsrs_cards`** satırı bulunursa ORM ile **güncelleme** (`db.add(card)`), `await db.commit()`. **`student_answers` tablosuna yazılmıyor`** — activation plan §298–296 ve `offline_sync_api.py` docstring’indeki “`student_answers`'a kayıt” beklentisi **mevcut kodla uyumsuz** (davranış sürprizi).

3. **`get_sync_status` sorguladığı tablolar:** Yalnız **`fsrs_cards`** (`count` due, `max(last_review)`).

4. **`package_id`:** `build_sync_package` içinde `str(uuid.uuid4())` üretilip yanıtta dönüyor; **veritabanına persist edilmiyor**; `process_sync_results` içinde `package_id` parametresi **audit için alınıyor fakat hiçbir tabloya yazılmıyor** (tamamen uçucu).

5. **FSRS tablosunun kesin adı (bu servis için):** `FSRSCard.__tablename__` = **`fsrs_cards`** (`/app/models/fsrs_models.py`). Aynı dosyada ayrıca `fsrs_reviews`, `fsrs_schedules`, `fsrs_student_profiles`, `fsrs_study_sessions`, `fsrs_subject_stats` tanımlı; offline sync kodu **doğrudan yalnızca `FSRSCard` / `fsrs_cards`** kullanıyor.

6. **Import / circular risk:** FSRS ve `QuestionBankItem` **fonksiyon gövdesinde** lazy import; üst seviyede DB model yok → **circular risk düşük**. `SubjectArea` sadece `subject` filtresi verildiğinde import edilir.

**Sürprizler (endpoint dışı / dokümantasyon):**

- `process_sync_results` başarılı sayım (`synced`) **INSERT olmadan** artıyor; cevap kalıcı olarak yalnızca FSRS kart güncellemesiyle ilişkilendirilebiliyor (kart bulunamazsa yine de `synced` artar — satır 227 `synced += 1` commit öncesi, kart yokken de).
- FSRS eşlemesi: `FSRSCard.front_text.contains(question_id)` — `front_text` içinde `question_id` substring aranıyor; veri şekline bağlı **kırılgan**.

---

## Görev 0.3 — Tablo varlığı + FK/PK tipleri

**`$q` listesi** (plan + 0.2 çıkarımı):  
`question_bank`, `student_answers`, `topic_progress`, `fsrs_reviews`, `fsrs_cards`, `student_fsrs_cards`, `fsrs_schedules`, `fsrs_student_profiles`, `fsrs_study_sessions`, `fsrs_subject_stats`, `user_item_fsrs`

| Sonuç | Tablolar |
|--------|----------|
| **Mevcut (10)** | `question_bank`, `student_answers`, `topic_progress`, `fsrs_cards`, `fsrs_reviews`, `fsrs_schedules`, `fsrs_student_profiles`, `fsrs_study_sessions`, `fsrs_subject_stats`, `user_item_fsrs` |
| **Eksik** | `student_fsrs_cards` (sorgu listesinde yok) |

**`$q2` + ek notlar (`information_schema.columns`):**

| `table_name` | `column_name` | `data_type` |
|--------------|---------------|-------------|
| `fsrs_cards` | `id`, `student_id` | `character varying` |
| `fsrs_reviews` | `id`, `card_id`, `student_id` | `character varying` |
| `question_bank` | `id` | `character varying` |
| `student_answers` | `id`, `question_id`, `exam_session_id` | `character varying` |
| `topic_progress` | `student_id` | `character varying` |
| `topic_progress` | `id` | **`integer`** (PK; kullanıcı FK’si değil) |

**`student_answers`:** `student_id` kolonu **yok**; öğrenci bağlantısı `exam_session_id` üzerinden (varchar). Plan örneğindeki `WHERE student_id='...'` şeması bu tabloyla **doğrudan uyuşmuyor**.

**Aşama C tetikleyicisi:** İncelenen `id` / `student_id` / `question_id` / `card_id` için **uuid tipi yok** (hepsi varchar veya `topic_progress.id` integer PK).

---

## Görev 0.4 — Alembic + repo dosyaları

| Soru | Bulgu |
|------|--------|
| `alembic current` | `student_review_drift_001 (head)` |
| `alembic history` \| fsrs/offline | Örnek zincir satırları: `freeze_baseline_20260401 -> 20260401_add_missing_tables` (“Add missing tables: **fsrs_cards**, …”), `20260401_fix_fsrs_reviews_fk`, `20260406_create_missing_tables -> user_item_fsrs_001` (“Create **user_item_fsrs** table”), … `dungeon_progress_001` |
| `versions/*fsrs*` | `20260401_fix_fsrs_reviews_fk.py`, `20260410_create_user_item_fsrs.py` |
| `versions/*offline*` | **0 dosya** |
| `_archive/*fsrs*` | **0 dosya** |

**Drift notu:** FSRS ve ilgili tablolar için migration satırları history’de görünüyor; diary ile aynı **“fiziksel tablo vs revision”** ayrımı yeni kurulumda yine kontrol edilmeli (briefing ders 9).

---

## Briefing uyumu (yalnızca istenen bölümler)

| Bölüm | Bu pilota etkisi |
|--------|------------------|
| **MİGRASYON YAZARKEN ÖĞRENİLEN DERSLER** | user FK’lerde VARCHAR kuralı bu DB’de `fsrs_cards` / `fsrs_reviews` / `question_bank` ile uyumlu; autogenerate yasak ve drift farkındalığı korunmalı. |
| **PİLOT ARTIFACT SİSTEMİ** | Bu dosya `_pilots/20260421_offline_sync_state.md` ADIM 0 çıktısı; sonraki adımlar insan onayı + ayrı `RESULT` (plan §6). |

---

## Aşama önerisi (insan onayı — plan §6 karar tablosu)

| Aşama | Bu ortam için uygun mu? | Not |
|--------|--------------------------|-----|
| **A** (gerekli tablo eksik) | **Hayır** | `fsrs_cards`, `question_bank`, `student_answers`, `topic_progress` ve diğer FSRS yan tabloları mevcut. |
| **B** (tablolar var, VARCHAR uyumlu) | **Evet** | Okuma/yazma yollarında kullanılan ana FK’ler varchar; yeni tablo migration’ı **şema açısından** zorunlu görünmüyor. |
| **C** (UUID / kural ihlali) | **Hayır** | Seçilen kolonlarda uuid yok. |
| **D** (belirsiz / circular) | **Kısmen** | **Kod–plan–docstring üçlü çelişkisi:** `student_answers` persist yok; `package_id` DB’de yok; FSRS eşleme kırılgan. Smoke ADIM 2.5 DB doğrulaması önce **davranış kararı** gerektirir. |

**Özet öneri (Composer 2):** Şema için **Aşama B** ile ilerlenebilir; ancak activation planındaki **POST smoke + `student_answers` satırı** beklentisi için önce **Aşama D maddesini** (servisi düzelt / planı revize / “sadece FSRS” olarak dokümante et) **insan onayı** ile netleştirin. Onay olmadan migration, `alembic upgrade`, HTTP smoke, `loader.py` / `routers/__init__.py` / `DISABLED_ROUTERS` değişikliği yapılmamalıdır.

---

## Ham komut çıktısı özeti

- `docker logs … Select-String offline` — kayıt + eski `sync-results` 200 + uyarı satırları.  
- `docker exec … grep FSRSCard/fsrs_cards` — `fsrs_cards` kesin.  
- `psql` `$q` — 10 tablo, `student_fsrs_cards` yok.  
- `psql` `$q2` + `student_answers` kolon listesi — varchar özeti + `topic_progress.id` integer.  
- `alembic current` + `history | Select-String fsrs|offline` — head + FSRS migration satırları.  
- `Get-ChildItem … *fsrs*` / `*offline*` / `_archive` — 2 fsrs migration, offline yok, arşiv fsrs yok.

---

*Bu dosya plan `20260421_offline_sync_activation.md` ADIM 0 çıktısıdır.*
