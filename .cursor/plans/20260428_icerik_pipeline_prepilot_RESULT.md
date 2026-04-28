# RESULT — Mini-Migration (İçerik Pipeline v1.2.1 Ön-Koşulu)

**Tarih:** 28 Nisan 2026
**Durum:** PASS
**Toplam süre:** ~1 saat (önceki sohbette ~2 saat asılı kaldıktan sonra parçalı yaklaşımla)
**Plan referansı:** `.cursor/plans/20260427_icerik_pipeline_v1_2.md`
**State referansı:** `backend/_pilots/20260428_icerik_pipeline_prepilot_state.md`

---

## 1. Özet

İçerik Pipeline v1.2.1 için 3 schema objesi eklendi: `question_bank.soru_hash` (MD5 content-based deduplication kolonu), `manual_review_queue` (conflict policy Katman 3 çıktı yeri), `question_bank_staging` (pipeline batch staging). Ayrıca aktif duplicate temizliği yapıldı (Esen Aps Coğrafya kaydı `is_calib_pool=FALSE` + `is_active=FALSE`).

İlk girişim (`prepilot_pipeline_v12_20260428`, SUPERSEDED) tek transaction içinde 77K satır MD5 backfill yapmaya çalıştı — `AccessExclusiveLock on question_bank` 5+ dakika tutuldu, iki kez asılı kaldı. **Yol B** ile parçalandı: 2 alembic migration (M1 schema-only + M2 constraint+index) + 1 backfill scripti (S1, 5K batch, her batch kendi tx). Sonuç: zero downtime equivalent (her batch lock ~ms).

**Final alembic head:** `prepilot_m2_indexes_20260428`

---

## 2. Schema değişiklikleri

### M1 — `prepilot_m1_schema_20260428` (schema only, no backfill)

| Obje | Tip | Detay |
|---|---|---|
| `question_bank.soru_hash` | `VARCHAR(32) NULL` | MD5 content hash, M2'de NOT NULL olur |
| `manual_review_queue` | Tablo | UUID PK, FK question_bank/users, decision check (keep_old/replace/merge/pending) |
| `question_bank_staging` | Tablo | LIKE question_bank INCLUDING DEFAULTS + 4 staging kolonu |
| Esen Aps cleanup | UPDATE | `is_calib_pool=FALSE` (id=10e2304d-...) |

İndeksler: `idx_mrq_old_qid`, `idx_mrq_pending` (partial), `idx_qbs_status`, `idx_qbs_batch`, `idx_qbs_hash` (partial WHERE NOT NULL).

### S1 — Backfill scripti (`backend/scripts/backfill_soru_hash.py`)

Hash formülü:
`MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))`

Batch: 5000 satır, her batch kendi transaction. Idempotent (`WHERE soru_hash IS NULL`).

### M2-prep — Manuel cleanup (`backend/scripts/m2_prep_deactivate_esen_aps.sql`)

UNIQUE INDEX'in geçmesi için tek aktif duplicate çifti çözüldü: Esen Aps Coğrafya `is_active=FALSE`, Esen Tyt kanonik (TYT explicit) kalır.

### M2 — `prepilot_m2_indexes_20260428` (constraint + indexes)

| Obje | Detay |
|---|---|
| `soru_hash NOT NULL` | Backfill bittikten sonra eklendi |
| `uq_qb_soru_hash_active` | Partial UNIQUE INDEX `WHERE is_active=TRUE` |
| `idx_qb_soru_hash` | Genel non-unique INDEX (lookup performansı) |

---

## 3. Backfill istatistikleri (S1)

77.345 satır işlendi (100 satır dry test'te manuel doldurulmuştu, idempotent script onları atladı).

| Batch | Satır | Süre |
|---|---|---|
| 1 | 5000 | 18.81s |
| 2 | 5000 | 96.87s |
| 3 | 5000 | 84.14s |
| 4 | 5000 | 47.15s |
| 5 | 5000 | 5.93s |
| 6 | 5000 | 56.53s |
| 7 | 5000 | 11.10s |
| 8-15 | 5000 each | 0.20-0.88s (cache ısındı) |
| 16 | 2345 | 24.75s (final + checkpoint) |
| 17 | 0 | 0.29s (idempotent terminate) |
| **Toplam** | **77.345** | **349.1s (~5.8 dk)** |

**Pattern:** İlk 7 batch yavaş (disk write cache + WAL flush ısınma), 8-15 RAM cache hızlı, 16 son checkpoint. Toplam süre eski tek-tx ile aynı, ama lock her batch sonrası bırakıldığı için backend kesintisiz okuma yapabildi.

---

## 4. Cleanup kayıtları

### Esen Aps Coğrafya çifti

Aynı hash: `545b4665ac29fa9d1fe7de8dcd175b03`. İkisi de aynı saniyede oluşturulmuş `2026-03-04 08:20:30`, Esen tarafından aynı dosya iki kez upload edilmiş gibi.

| | Aps (silinen) | Tyt (kalan) |
|---|---|---|
| `id` | `10e2304d-a613-50c7-847d-d2d304571220` | `0d6e5dbe-57a7-51e0-a4f6-0b6d1b792e2c` |
| `source_book` | Esen Aps Cografya Soru Bankası | Esen Tyt Cografya Soru Bankası |
| `source_page` | 98 | 90 |
| `is_calib_pool` (M1 sonrası) | FALSE | TRUE |
| `is_active` (M2-prep sonrası) | FALSE | TRUE |
| `pipeline_metadata` | `prepilot_dedup_at` + `m2_prep_deactivate_at` | (değişmedi) |

Kanonik karar: TYT versiyonu sınav türü explicit, daha standart. Kullanım istatistikleri ikisinde de sıfır (`times_asked=0`), seçim arbitrer ama izlenebilir.

---

## 5. Sapma analizi (öğrenmeler)

### 5.1 SUPERSEDED migration tek-tx 77K backfill — yanlış tasarım

İlk versiyon (`prepilot_pipeline_v12_20260428`) tüm DDL + 77K UPDATE'i tek transaction'a koymuştu. Sonuç: AccessExclusiveLock 5+ dk tutuldu, alembic upgrade 2 kez asılı kaldı, kullanıcı zinciri kıramadı (rollback değil, hung). Önceki sohbet bu yüzden "alembic çıktısı kesildi" varsaydı, gerçekte transaction commit'lenmemişti, bekliyordu.

**Doğrusu:** Migration sadece schema değiştirmeli (saniyeler), backfill ayrı script ile batch'lenmeli, NOT NULL+UNIQUE constraint backfill sonrası ayrı migration ile gelmeli.

### 5.2 Migration yorumu vs canlı sistem — "96 grup" → 145 grup

SUPERSEDED dosyanın yorumu "96 grup pasif duplicate var" diyordu. Gerçek: **145 pasif duplicate grup** (toplam 196 fazla satır, distinct=77.249). Yorum ezbere yazılmış, sayım yapılmamış. M2 yorumu canlı sayımla yenilendi.

**KIRO2 prensibi #1 ihlali (ezbere yazma).** Migration yorumlarındaki tüm "veri durumu" iddiaları canlı sistem sorgusuyla doğrulanmalı.

### 5.3 FK tip uyumsuzluğu hipotezi yanlıştı

Devir notunda billing migration'da `user_id VARCHAR(36) REFERENCES users(id)` ile `users.id = VARCHAR` arasında FK tip uyumsuzluğu hipotezi vardı. Gerçek: PostgreSQL FK için tipler **uyumlu** olmalı, **birebir aynı** değil. `varchar(36)` ile `varchar` aynı `varchar` tipine resolve eder, FK çalışır. Billing migration sağlamdı, hata kaynağı değildi. Asıl problem 77K tek-tx backfill'di.

### 5.4 alembic_version VARCHAR(32) overflow (yapısal düzelti)

Billing revision adı 34 karakter, kolon kapasitesi 32. Önceki sohbette `ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)` ile çözüldü. **Bu kalıcı bir düzelti.** Gelecekte revision adlarını 64'ün altında tutmak hayati.

### 5.5 PowerShell `\"` JSON escape — patlıyor

`psql -c` ile inline JSON-içerikli SQL çalıştırmak PowerShell'in çift tırnak escape'iyle çakışıyor. **Çözüm:** Her zaman `Set-Content` ile `@'...'@` here-string kullanıp `psql -f dosya.sql`. KIRO2 standardına ekleme: "Türkçe SQL için zaten `psql -f` zorunlu, JSON-içerikli SQL için de aynı."

### 5.6 `docker cp` parent klasör yoksa hata atar

Yeni bir dizin (`/app/scripts`) için önce `docker exec --user root mkdir -p` gerekir.

### 5.7 PowerShell here-string + büyük markdown — clipboard kopuyor

Bu RESULT dosyası ilk yapıştırma denemesinde here-string açılışı koptu (250+ satır markdown). Çözüm: base64 encode + tek satır decode. Veya parçalı `Add-Content`. Veya doğrudan editor.

---

## 6. Doğrulama snapshot'ı

### DB

| Sütun | Değer |
|---|---|
| `alembic_version` | `prepilot_m2_indexes_20260428` |
| `question_bank` toplam | 77.445 |
| `question_bank` aktif | 57.920 |
| `question_bank` inaktif | 19.525 |
| `soru_hash` NULL | 0 |
| `soru_hash` distinct | 77.249 |
| Toplam duplicate gruplar | 145 (hepsi pasif) |
| Aktif duplicate gruplar | 0 |
| `manual_review_queue` | 0 satır (boş, hazır) |
| `question_bank_staging` | 0 satır (boş, hazır) |
| `billing_subscriptions` | 0 satır (boş, hazır) |
| `_bak_paketA_20260428_questions` | 6.532 satır (Paket A backup, 2026-05-28 DROP) |

### Backend

| Endpoint | Sonuç |
|---|---|
| `GET /health` | 5/5 components healthy |
| `POST /api/v1/auth/giris` (admin) | Token alındı |
| `GET /api/v1/osym/statistics` | total=57.920, with_answers=57.920, without_answers=0 |

**Zero regression.** Backend yeni schema'yı sorunsuz kullanıyor.

---

## 7. Öğrenmeler — KIRO2 standardına eklenecekler

1. **Migration tasarımı:** Büyük tabloda backfill migration içinde tek-tx olarak yapılmaz. Schema-only migration → ayrı batch script → constraint migration. Bu üç-aşama yaklaşımı KIRO2 standart pattern olmalı.
2. **Migration yorumlarındaki sayılar canlı sistemden doğrulanır:** Ezbere "X grup duplicate var" yazılmaz.
3. **PowerShell + JSON-içerikli SQL = `psql -f` zorunlu.** Inline `-c` kullanma.
4. **`docker cp` parent klasör otomatik yaratmaz** — yeni dizin için önce `mkdir -p`.
5. **alembic_version kolonu VARCHAR(64) güvenli.** Revision adı 64 karakteri geçmemeli.
6. **PG FK tip uyumluluğu:** `varchar(N)` ↔ `varchar` uyumlu, panik etmeye gerek yok.
7. **Büyük markdown dosyalarını PowerShell here-string ile yazma.** Base64 decode veya editor kullan.

---

## 8. Sırada — Pipeline v1.2.1 ana pilot

DB ön-koşulu kapandı. Sıradaki: 500 sayfa Matematik kitabı pilot.

| | |
|---|---|
| Plan | `.cursor/plans/20260427_icerik_pipeline_v1_2.md` (584 satır, hazır) |
| Hedef | Tek kitaptan ucu uca: OCR → AI extract → validation → staging → conflict policy → manual review → question_bank insert |
| Ön-koşul durumu | Tüm DB schema hazır |
| Beklenen süre | 1-2 hafta (uçtan uca) |

Devamı için yeni bir state.md gerekir: `backend/_pilots/20260428_icerik_pipeline_v1_2_pilot_state.md`. Plan'dan tasklara dönüştürülecek.

### Briefing güncellemesi (ayrı iş)

`KIRO2_SESSION_BRIEFING.md` v17 yazımı sıraya alındı:
- Paket A sonuçları (active 64.199 → 57.921)
- Mini-migration sonuçları (active 57.921 → 57.920, head güncellendi, 3 yeni tablo, soru_hash kolonu)
- fsrs_cards: 0 → 57 (briefing outdated)
- exam_sessions: 73 → 186 (briefing outdated)
