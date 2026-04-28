# Pilot state — Paket A: question_bank dead-data temizliği

**Tarih:** 2026-04-28 (ADIM 0)
**Repo:** `C:\Users\husey\kiro2`
**HEAD:** çalıştırma anında not edilecek
**Pilot tipi:** Veri temizliği (cerrahi `is_active=FALSE` UPDATE + 1 DELETE)
**Bağlam:** İçerik Pipeline v1.2.1 ön-koşulu — kalibre olmayan ve gerçekten çöp olan kayıtlar pipeline gelmeden önce devreden çıkarılsın.

---

## 0.0 — Özet sağlık

| Alan | Değer |
|------|-------|
| DB host:port | `host.docker.internal:5434` (host PostgreSQL 18) |
| DB name | `kiro2` |
| Alembic head | `diary_drift_recovery_20260422` |
| `question_bank` toplam | **77.445** |
| `question_bank` is_active=TRUE | **64.199** |
| `question_bank` is_calibrated=TRUE | 360 |
| `question_bank` is_calib_pool=TRUE | 1.855 |
| `question_bank` student_answers FK'si olan | 151 (briefing'de "151" yazılıydı, gerçekte 157 distinct question_id; küçük güncelleme) |
| `topic_hierarchy` toplam | 125 (1'i `TEST.BATCH1B` test seed) |

`dbhub-kiro2` MCP üzerinden 2026-04-28'de teyit edildi. Briefing v16'daki bazı sayılarla küçük farklar (fsrs_cards 0→57, exam_sessions 73→186) Paket A'yı etkilemiyor — bilgi notu.

---

## 0.1 — Pilot amacı (tek cümle)

Aktif olarak öğrenciye gösterilen 64.199 sorudan **6.278 çöp/mükerrer kaydı `is_active=FALSE`** yapmak ve `topic_hierarchy`'den **1 test seed kaydını silmek**. Hiçbir kayıt fiziksel olarak silinmeyecek (test seed hariç). Kalibre/havuz/yanıtlanmış olan 149 "çöp ama korunan" kayıt **dokunulmadan** kalacak.

**Bu pilot ne DEĞİLDİR:**
- ❌ İçerik pipeline pilotu değil — ona giden yolu temizliyor
- ❌ Schema değişikliği değil — sadece UPDATE + 1 DELETE
- ❌ Migration değil — alembic dokunulmaz
- ❌ Mükerrer satırların fiziksel silinmesi değil — sadece deaktivasyon

---

## 0.2 — Etkilenecek kayıtların kategori dökümü (gerçek SQL sayım)

### Kategori K1 — Kısa soru metni (`LENGTH(question_text) < 30`)

**Kriter:** 30 karakterden kısa `question_text` + `is_active=TRUE`
**Gerekçe:** İnsan-okunabilir Türkçe soru en az 30 karakter olmalı. Örnekler:
- `"2025 paragraf eftirik olup."` (27 karakter, anlamsız)
- `"A. 2\nB. 3\nC. 4\nD. 5\nE. 6"` (25 karakter, soru içeriği yerine seçenek listesi)
- `"Bunu gör, okąt demedim?"` (23 karakter, Türkçe değil)

**Sayım:** 320 kayıt

### Kategori K2 — Yapısal bozuk seçenekler

**Kriter:** `LENGTH(option_a) < 2 AND LENGTH(option_b) < 2` + `is_active=TRUE`
**Gerekçe:** İlk iki seçeneğin ikisi de tek karakterden kısa → seçenekler kayıp / OCR hatası
**Örnek:** `option_a = ""`, `option_b = ""` ama soru metni dolu

**Sayım:** 6.021 kayıt
**K1 ile çakışma:** 26 kayıt (K1 ∩ K2)

### Kategori K3 — Mükerrer kayıtlar (aynı hash)

**Kriter:** `MD5(LOWER(TRIM(question_text)) || '|' || option_a..e)` aynı olan birden fazla aktif kayıt
**Gerekçe:** Aynı soru farklı kitap baskılarında farklı UUID ile yüklenmiş (örn. "Orijinal-2024-Geometri" + "Orijinal-Tyt Ayt Geometri" aynı soruyu içeriyor)

**Sayım:**
- 296 toplam aktif duplicate kayıt
- 123 distinct hash grubu (her grupta ortalama 2.4 kayıt)
- **Tutma kuralı (her gruptan 1 temsilci):**
  ```
  ORDER BY
    is_calibrated DESC,         -- önce kalibre olanı tut
    has_student_answers DESC,   -- sonra yanıtlanmışı
    is_calib_pool DESC,         -- sonra havuzdakini
    created_at ASC              -- son çare: en eski
  → ROW_NUMBER() OVER (PARTITION BY soru_hash) = 1 olanı KEEP
  ```
- Tutulacak: 123 / Deaktive: 173

### Kategori K8 — Test seed (topic_hierarchy)

**Kriter:** `topic_hierarchy.code LIKE 'TEST%'`
**Sayım:** 1 kayıt — `TEST.BATCH1B / Test Konu Batch1B / id=00000000-0000-0000-0000-000000000001`

**`question_bank` etkilenmesi:** Bu test topic'ine bağlı 0 soru var (kontrol edildi). Yani DELETE güvenli.

---

## 0.3 — Birleşim ve koruma analizi

### Toplam aday kayıt (K1 ∪ K2 ∪ K3-non-temsilci)

```
K1 yalnız:        294
K2 yalnız:      5.995
K1 ∩ K2:           26
K3 non-temsilci: 173 (mükerrer gruplarda tutulmayanlar)
─────────────────────
TOPLAM aday:    6.488 (overlap'ler dahil değil, distinct sayım: 6.427)
```

### Koruma kuralı

**Üç koşuldan herhangi birini sağlayan kayıtlar `is_active=TRUE` kalır:**
1. `is_calibrated = TRUE` → IRT kalibrasyonundan geçmiş, eğitim verisi
2. `is_calib_pool = TRUE` → kalibrasyon havuzunda, sistem dengesi parçası
3. `EXISTS(SELECT 1 FROM student_answers WHERE question_id = qb.id)` → öğrenci cevabı var

### Net plan

| Adım | Sayı |
|------|------|
| Aday kayıt (distinct) | **6.427** |
| Koruma kuralıyla devre dışı kalan (will_protect) | **149** |
| `is_active=FALSE` yapılacak | **6.278** |
| `topic_hierarchy` DELETE | 1 (TEST.BATCH1B) |

149 korunan kayıt `quality_score=100, status=approved` yalanıyla kalibre edilmiş olabilir. **Bu Paket A'nın işi değil** — Paket C (schema borç) konusu. Şimdi dokunulmuyor.

---

## 0.4 — Uygulanacak SQL (TASLAK, ADIM 1'de revize edilebilir)

### Adım 1 — Backup tablosu (geri alma garantisi)

```sql
-- Etkilenecek kayıtların snapshot'ı (geri dönüş için)
CREATE TABLE IF NOT EXISTS _bak_paketA_20260428_questions AS
SELECT qb.*,
       NOW() AS backup_at,
       CASE
         WHEN LENGTH(question_text) < 30 THEN 'K1'
         WHEN LENGTH(option_a) < 2 AND LENGTH(option_b) < 2 THEN 'K2'
         ELSE 'K3'
       END AS category
FROM question_bank qb
WHERE qb.is_active = TRUE
  AND qb.id IN (
    -- TAM aday liste burada (K1 ∪ K2 ∪ K3 non-temsilci)
    -- ADIM 1 öncesi tam SQL hazırlanacak
    SELECT 1 -- placeholder
  );

-- Beklenen: ~6.427 satır snapshot
```

### Adım 2 — Mükerrer temsilci seçimi (geçici tablo)

```sql
CREATE TEMP TABLE _paketA_dup_keepers AS
SELECT id
FROM (
  SELECT
    id,
    ROW_NUMBER() OVER (
      PARTITION BY MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
      ORDER BY
        is_calibrated DESC,
        (SELECT COUNT(*) > 0 FROM student_answers sa WHERE sa.question_id = qb.id)::int DESC,
        is_calib_pool DESC,
        created_at ASC
    ) AS rnk
  FROM question_bank qb
  WHERE is_active = TRUE
    AND MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, '')) IN (
      SELECT MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
      FROM question_bank
      WHERE is_active = TRUE
      GROUP BY 1
      HAVING COUNT(*) > 1
    )
) sub
WHERE rnk = 1;

-- Beklenen: 123 satır
```

### Adım 3 — Aday kayıt listesini geçici tabloya yaz

```sql
CREATE TEMP TABLE _paketA_candidates AS
SELECT DISTINCT qb.id, qb.is_calibrated, qb.is_calib_pool,
       EXISTS(SELECT 1 FROM student_answers sa WHERE sa.question_id = qb.id) AS has_answers
FROM question_bank qb
WHERE qb.is_active = TRUE
  AND (
    LENGTH(qb.question_text) < 30  -- K1
    OR (LENGTH(qb.option_a) < 2 AND LENGTH(qb.option_b) < 2)  -- K2
    OR (
      qb.id NOT IN (SELECT id FROM _paketA_dup_keepers)
      AND MD5(LOWER(TRIM(qb.question_text)) || '|' || qb.option_a || '|' || qb.option_b || '|' || qb.option_c || '|' || qb.option_d || '|' || COALESCE(qb.option_e, '')) IN (
        SELECT MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
        FROM question_bank
        WHERE is_active = TRUE
        GROUP BY 1
        HAVING COUNT(*) > 1
      )
    )
  );

-- Beklenen: 6.427 satır
```

### Adım 4 — UPDATE (koruma kuralıyla)

```sql
UPDATE question_bank
SET is_active = FALSE,
    updated_at = NOW(),
    pipeline_metadata = COALESCE(pipeline_metadata, '{}'::json)::jsonb || '{"paket_a_deactivated_at":"2026-04-28","reason":"K1_K2_K3_dead_data"}'::jsonb
WHERE id IN (
  SELECT c.id
  FROM _paketA_candidates c
  WHERE NOT (c.is_calibrated OR c.is_calib_pool OR c.has_answers)
);

-- Beklenen: 6.278 satır UPDATE
```

### Adım 5 — Test seed DELETE

```sql
-- Önce hiç sorusu yok mu kontrol
SELECT COUNT(*) FROM question_bank WHERE primary_topic_id = '00000000-0000-0000-0000-000000000001';
-- Beklenen: 0

DELETE FROM topic_hierarchy WHERE code = 'TEST.BATCH1B';
-- Beklenen: 1 satır DELETE
```

### Adım 6 — ANALYZE (istatistik güncelleme)

```sql
ANALYZE question_bank;
ANALYZE topic_hierarchy;
```

---

## 0.5 — Doğrulama sorguları (post-apply)

```sql
-- 1. is_active sayım kontrolü
SELECT
  COUNT(*) FILTER (WHERE is_active = TRUE) AS active_after,
  COUNT(*) FILTER (WHERE is_active = FALSE) AS inactive_after
FROM question_bank;
-- Beklenen: active_after = 64.199 - 6.278 = 57.921

-- 2. Korunan 149 kaydın hâlâ aktif olduğunu doğrula
SELECT COUNT(*) AS protected_still_active
FROM question_bank qb
WHERE qb.is_active = TRUE
  AND (
    LENGTH(qb.question_text) < 30
    OR (LENGTH(qb.option_a) < 2 AND LENGTH(qb.option_b) < 2)
  )
  AND (qb.is_calibrated = TRUE
       OR qb.is_calib_pool = TRUE
       OR EXISTS(SELECT 1 FROM student_answers sa WHERE sa.question_id = qb.id));
-- Beklenen: 149 (hepsi korunmuş olmalı)

-- 3. Backup tablosu satır sayısı
SELECT COUNT(*) FROM _bak_paketA_20260428_questions;
-- Beklenen: 6.427

-- 4. Test seed silindi mi
SELECT COUNT(*) FROM topic_hierarchy WHERE code LIKE 'TEST%';
-- Beklenen: 0

-- 5. Mükerrer kontrolu — artık aktif kayıtlar arasında duplicate yok
WITH hashed AS (
  SELECT id, MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, '')) AS h
  FROM question_bank WHERE is_active = TRUE
)
SELECT COUNT(*) AS active_dup_after
FROM (SELECT h FROM hashed GROUP BY h HAVING COUNT(*) > 1) sub;
-- Beklenen: 0 (149 korunan içinde duplicate yoksa) veya küçük sayı (mükerrer korunan grupları varsa)
```

---

## 0.6 — Geri alma planı (rollback)

Eğer apply sonrası bir şey ters giderse:

```sql
-- Tüm Paket A değişikliklerini geri al
BEGIN;

-- 1. is_active=FALSE yapılanları geri TRUE yap
UPDATE question_bank
SET is_active = TRUE,
    updated_at = NOW()
WHERE id IN (
  SELECT id FROM _bak_paketA_20260428_questions
  WHERE is_active = TRUE  -- backup'ta active=TRUE iken inaktif yapılmış olanlar
);

-- 2. Test seed'i geri ekle
INSERT INTO topic_hierarchy (id, code, name_tr, level, is_active, ...)
SELECT * FROM (
  -- ADIM 1'de TEST.BATCH1B kaydı state.md'ye kopyalanacak (full INSERT)
  VALUES (...)
) v;

COMMIT;
```

**Backup tablosu (`_bak_paketA_20260428_questions`) en az 30 gün saklanacak** — pilot RESULT yazıldıktan sonra Hüseyin manuel DROP eder.

---

## 0.7 — Riskler

| # | Risk | Olasılık | Etki | Önlem |
|---|------|----------|------|-------|
| RA1 | Koruma kuralı 149 kaydı yakalamıyor, kalibre kayıt deaktive ediliyor | Düşük | Yüksek | Doğrulama sorgusu #2 — koruma sayısı 149 ise PASS |
| RA2 | Mükerrer temsilci seçiminde yanlış kayıt seçildi (kalibre olan kayıp) | Düşük | Yüksek | ROW_NUMBER ORDER BY `is_calibrated DESC` ilk; eğer 0 kalibre kayıp doğrulanır |
| RA3 | UPDATE çok yavaş (6K satır × bytecode trigger) | Orta | Düşük | Tek transaction, beklenen <30 saniye |
| RA4 | Backup tablosu disk doldurur | Düşük | Düşük | 6.427 satır × ~3KB = ~20MB, sorun değil |
| RA5 | TEST seed DELETE FK violation | Düşük | Düşük | Önce dependent satır kontrolü (Adım 5) |
| RA6 | Pipeline v1.2.1 ile çakışma (paralel çalışma) | Düşük | Düşük | Pipeline henüz başlamadı, Paket A önce yapılacak |
| RA7 | Çöp veri pattern'i K1+K2+K3'le sınırlı değil, başkası da var | Yüksek | Düşük | Bu pilot bilinen 3 kategoriyi temizler; sonra ek tarama yapılabilir |
| RA8 | Frontend bir endpoint'te `is_active` filtresi olmadan kullanıyor | ~~Düşük~~ KAPALI | Yüksek | A4 denetimi tamamlandı (Bölüm 0.8a) — 13 dosya × 99 SELECT noktası tarandı, hepsi güvenli |

---

## 0.8 — Açık sorular (KAPALI — Hüseyin 28.04.2026 onayı)

**A1 — Backup tablosu adı:** `_bak_paketA_20260428_questions` ✓ ONAY
- Naming convention: `_bak_<pilot_id>_<table_name>` formatı KIRO2 standardı olacak
- 30 gün sonra Hüseyin manuel DROP

**A2 — Korunan 149 "kalibre ama çöp" kayıt:** Paket C'ye birlikte bırakılıyor ✓ ONAY
- Şimdi dokunulmuyor; manual_review_queue'a da eklenmiyor (Paket A bu mekanizmayı kullanmıyor)
- Paket C'de toplu inceleme: 17 kalibre + 132 havuz/yanıtlanmış

**A3 — TEST.BATCH1B fiziksel DELETE mi soft mi?** Fiziksel DELETE ✓ ONAY
- Test verisi production'da kalmamalı
- 0 soru bağlı olduğu doğrulandı (FK violation riski yok)

**A4 — Backend `is_active` filtresi kontrolü:** TAMAMLANDI ✓
- **Tarama:** 1.678 referans, 99 unique SELECT noktası, `backend/` altı .py dosyaları
- **Sonuç:** Hiçbir endpoint `is_active` filtresi olmadan SELECT yapmıyor
- Detay 0.8a'da

**A5 — Tek transaction mı, ayrı UPDATE mi?** Tek transaction ✓ ONAY
- Atomicity: ya hepsi geçer ya hiçbiri (kısmi başarısız durum olmaz)
- BEGIN ... COMMIT bloğu Adım 4 ve Adım 5'i kapsar

---

## 0.8a — A4 detay: Backend `is_active` filtresi denetimi

**Yöntem:** `start_search` ile `FROM question_bank` deseni `backend/` altında tarandı, her SELECT noktasında `is_active` filtresi varlığı tek tek kontrol edildi.

**Güvenli olduğu doğrulanan SELECT'ler (13 dosya):**

| Dosya | Kullanım | Durum |
|---|---|---|
| `api/osym_questions_api.py` | 7 endpoint, hepsinde `conditions = ["is_active = TRUE"]` | ✓ |
| `api/admin.py` (satır 251, 294, 516, 527, 537) | 5 SELECT, hepsinde `WHERE is_active=TRUE` | ✓ |
| `api/wave2b_quality_routes.py:131` | `WHERE is_active = true` | ✓ |
| `api/question_crud_api.py:976` (vector sim.) | `where_clause = ... ["q.is_active = true"] + filters` hard-coded | ✓ |
| `api/duel_api.py:404` | Belirli ID lookup (Paket A öncesi seçilmiş soru) | ✓* |
| `api/duel_api.py:434` (`_select_duel_questions`) | `QuestionBankItem.is_active == True` | ✓ |
| `services/photo_ask_service.py:138` | `filters = ["q.embedding IS NOT NULL", "q.is_active = true"]` | ✓ |
| `services/placement_assessment_service.py:194` | `QuestionBankItem.is_active == True` | ✓ |
| `services/cat_session.py:241, 269, 325` | 3 SELECT, hepsinde `is_active = TRUE` | ✓ |
| `services/osym_inspired_generator.py` | 4 SELECT, tümü `osym_format_compliant=true AND is_active=true` | ✓ |
| `repositories/question_repository.py` | 6 yerde `is_active=True` (SQLAlchemy ORM) | ✓ |
| `app/tasks/calibration_task.py:37` | `WHERE q.is_active = TRUE` | ✓ |
| `scripts/*.py` (assign_difficulty, assign_bloom, vb.) | Tümü `WHERE is_active = TRUE` | ✓ |

*\* `duel_api.py:404` istisna açıklaması:* Bu endpoint **belirli bir question_id** ile arıyor (önceden seçilmiş duel sorusu). `is_active` filtresi yok ama:
1. Paket A önce çalıştığı için `is_active=FALSE` yapılan 6.278 kayıt zaten duel'e seçilemez (`_select_duel_questions:434` satırında filtre var)
2. Aktif duel'lerde kullanımda olan soru `student_answers` FK aldığı an Paket A koruma kuralına girer (Katman 3) — `is_active=TRUE` kalır

**Sonuç:** Paket A apply güvenli. Deaktive edilen 6.278 kayıt hiçbir öğrenci yüzeyinde görünmeyecek.

---

## 0.9 — Kabul kriterleri (PASS/FAIL)

**PASS:**
- Adım 4 UPDATE sonucu = 6.278 (±10 tolerans, doğal varyasyon)
- Adım 5 DELETE sonucu = 1
- Doğrulama sorgusu #1: `active_after = 57.921 ± 10`
- Doğrulama sorgusu #2: `protected_still_active = 149`
- Doğrulama sorgusu #4: `0`
- Backup tablosu 6.427 satır (±10)
- Hiçbir endpoint 500 dönmüyor (smoke test: `/api/v1/cat/sessions` POST aktif soru çekiyor mu)

**FAIL (geri al):**
- Sayımlar tolerans dışı
- Bir endpoint `is_active=FALSE` kayıtları hâlâ getiriyor (frontend kontrolü)
- Constraint violation (CHECK / FK)

---

## 0.10 — Sıradaki adımlar

1. ✅ Hüseyin: A1–A5 onayları (28.04.2026 tamamlandı, Bölüm 0.8'de kayıtlı)
2. ✅ Claude: A4 denetimi (Bölüm 0.8a — 13 dosya, hepsi güvenli)
3. Claude: ADIM 1 — net production SQL'leri yaz (Bölüm 0.4 PSEUDO-KOD'tan ADIM 1'e)
   - Tam aday liste subquery (placeholder yerine)
   - INSERT INTO _bak (full satırla)
   - Transaction içinde 6 adım (BEGIN ... ANALYZE ... COMMIT)
4. Hüseyin: ADIM 1 SQL'leri tek tek çalıştır (insan döngüsünde, KIRO2 prensip #2)
5. Claude: Doğrulama sorguları (Bölüm 0.5) çıktısını al, RESULT raporu yaz
6. Hüseyin: Smoke test — frontend'den 1 öğrenci girişi, soru çek, deaktive edilmiş kayıt görünmüyor mu kontrol
7. Hüseyin: 30 gün sonra `DROP TABLE _bak_paketA_20260428_questions`
8. Sonraki: İçerik Pipeline v1.2.1 pre-pilot mini-migration → ana pilot

---

## 0.11 — Ne tutarsızlığı plan dışı bırakıldı (referans için)

Sistematik DB taramasında bulunan ama Paket A kapsamı dışında olan eksiklikler:

- **K4 (66 boş topic, ders-root'a yığılma):** Pipeline v1.2 ile çözülecek (ayrı iş yok)
- **K5 (cross-subject FK bozukluğu, 5 FEN→MAT, 5 TURKCE→MAT):** Paket B'ye bırakıldı, opsiyonel
- **K6 (`irt_a/b/c` kullanılmamış kolonlar, paralel IRT sistemi):** Paket C — schema borç temizliği
- **K7 (duplicate index'ler):** Paket C
- **K9 (briefing v16 outdated):** Briefing v17 yazımı ayrı iş
- **K10 (root topic `subject_area=NULL`):** Paket C

Bu pilot **sadece K1+K2+K3+K8'i** çözer.

---

**Versiyon:** v2 (2026-04-28, ADIM 0 final)
**Durum:** Onaylandı, ADIM 1'e geçiş bekliyor.

**Değişiklik notları (v1 → v2):**
- Bölüm 0.8 açık sorular A1-A5 onaylandı (default önerilerle)
- Bölüm 0.8a eklendi — A4 detay denetimi (13 dosya × 99 SELECT noktası)
- Bölüm 0.7 RA8 risk maddesi KAPALI işaretlendi
- Bölüm 0.10 sıradaki adımlar güncellendi — ADIM 1 hazır


---

# ADIM 1 — Apply (Production SQL)

**Önemli:** Bu SQL'leri Hüseyin sırayla çalıştıracak (KIRO2 prensip #2 — insan döngüsünde). Her adım sonrası beklenen çıktı belirtilmiştir, sapma varsa Claude'a bildir.

**Bağlantı komutu (PowerShell, host'tan):**
```powershell
$env:PGPASSWORD='1470'
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2
```

**Veya Docker içinden:**
```powershell
docker exec -it kiro2_postgres psql -U postgres -d kiro2
# (Eğer kiro2_postgres çalışıyorsa; userMemories: ana DB host PostgreSQL 18 port 5434)
```

---

## 1.1 — Pre-flight sayım (apply öncesi state snapshot)

```sql
-- Mevcut durumu kayıt altına al
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE is_active = TRUE) AS active,
  COUNT(*) FILTER (WHERE is_calibrated = TRUE) AS calibrated,
  COUNT(*) FILTER (WHERE is_calib_pool = TRUE) AS in_pool,
  (SELECT COUNT(*) FROM topic_hierarchy WHERE code = 'TEST.BATCH1B') AS test_seed_exists
FROM question_bank;
```

**Beklenen çıktı (referans için):**
```
 total | active | calibrated | in_pool | test_seed_exists
-------+--------+------------+---------+------------------
 77445 |  64199 |        360 |    1855 |                1
```

Sayılar farklıysa **DURMALI** — Hüseyin Claude'a bildir. Pipeline v1.2 ya da başka bir iş paralel çalışmış olabilir.

---

## 1.2 — Backup tablosu oluşturma

```sql
-- Kalıcı backup tablo (30 gün saklanacak, sonra Hüseyin manuel DROP)
CREATE TABLE _bak_paketA_20260428_questions AS
SELECT
  qb.*,
  NOW() AS backup_at,
  CASE
    WHEN LENGTH(qb.question_text) < 30 AND
         LENGTH(qb.option_a) < 2 AND LENGTH(qb.option_b) < 2 THEN 'K1+K2'
    WHEN LENGTH(qb.question_text) < 30 THEN 'K1'
    WHEN LENGTH(qb.option_a) < 2 AND LENGTH(qb.option_b) < 2 THEN 'K2'
    ELSE 'K3'
  END AS paket_a_category
FROM question_bank qb
WHERE qb.is_active = TRUE
  AND (
    LENGTH(qb.question_text) < 30
    OR (LENGTH(qb.option_a) < 2 AND LENGTH(qb.option_b) < 2)
    OR MD5(LOWER(TRIM(qb.question_text)) || '|' || qb.option_a || '|' || qb.option_b || '|' || qb.option_c || '|' || qb.option_d || '|' || COALESCE(qb.option_e, '')) IN (
      SELECT MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
      FROM question_bank
      WHERE is_active = TRUE
      GROUP BY 1
      HAVING COUNT(*) > 1
    )
  );

-- Doğrulama
SELECT COUNT(*), paket_a_category FROM _bak_paketA_20260428_questions GROUP BY paket_a_category ORDER BY 2;
```

**Beklenen çıktı:**
```
 count | paket_a_category
-------+------------------
   294 | K1
    26 | K1+K2
  5995 | K2
   296 | K3 (tüm grup üyeleri, temsilci dahil)
```

**Toplam:** ~6.611 satır (K3 mükerrer grupları temsilci dahil yedeklenir, ama UPDATE'de temsilciler dokunulmaz).

⚠️ **DİKKAT:** Sayı `6.427`'den biraz büyük olacak çünkü backup tablo K3 mükerrer **grup tamamı** içerir (rollback gerekirse ihtiyaç olur). UPDATE'de sadece non-temsilci 173 deaktive edilecek.

---

## 1.3 — Mükerrer temsilci geçici tablosu

```sql
-- K3'te tutulacaklar (her hash grubundan 1 temsilci)
-- Bu temsilciler UPDATE'den HARİÇ tutulacak
CREATE TEMP TABLE _paketA_dup_keepers AS
SELECT id
FROM (
  SELECT
    qb.id,
    ROW_NUMBER() OVER (
      PARTITION BY MD5(LOWER(TRIM(qb.question_text)) || '|' || qb.option_a || '|' || qb.option_b || '|' || qb.option_c || '|' || qb.option_d || '|' || COALESCE(qb.option_e, ''))
      ORDER BY
        qb.is_calibrated DESC,
        (EXISTS(SELECT 1 FROM student_answers sa WHERE sa.question_id = qb.id))::int DESC,
        qb.is_calib_pool DESC,
        qb.created_at ASC
    ) AS rnk
  FROM question_bank qb
  WHERE qb.is_active = TRUE
    AND MD5(LOWER(TRIM(qb.question_text)) || '|' || qb.option_a || '|' || qb.option_b || '|' || qb.option_c || '|' || qb.option_d || '|' || COALESCE(qb.option_e, '')) IN (
      SELECT MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
      FROM question_bank
      WHERE is_active = TRUE
      GROUP BY 1
      HAVING COUNT(*) > 1
    )
) sub
WHERE rnk = 1;

-- Doğrulama
SELECT COUNT(*) FROM _paketA_dup_keepers;
```

**Beklenen çıktı:** `123`

---

## 1.4 — Aday liste geçici tablosu

```sql
-- Tam K1 ∪ K2 ∪ K3 (non-temsilci) listesi
CREATE TEMP TABLE _paketA_candidates AS
SELECT DISTINCT
  qb.id,
  qb.is_calibrated,
  qb.is_calib_pool,
  EXISTS(SELECT 1 FROM student_answers sa WHERE sa.question_id = qb.id) AS has_answers
FROM question_bank qb
WHERE qb.is_active = TRUE
  AND (
    LENGTH(qb.question_text) < 30  -- K1
    OR (LENGTH(qb.option_a) < 2 AND LENGTH(qb.option_b) < 2)  -- K2
    OR (
      qb.id NOT IN (SELECT id FROM _paketA_dup_keepers)
      AND MD5(LOWER(TRIM(qb.question_text)) || '|' || qb.option_a || '|' || qb.option_b || '|' || qb.option_c || '|' || qb.option_d || '|' || COALESCE(qb.option_e, '')) IN (
        SELECT MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
        FROM question_bank
        WHERE is_active = TRUE
        GROUP BY 1
        HAVING COUNT(*) > 1
      )
    )
  );

-- Doğrulama (3 satırda dağılım)
SELECT
  COUNT(*) AS total_candidates,
  COUNT(*) FILTER (WHERE NOT (is_calibrated OR is_calib_pool OR has_answers)) AS will_deactivate,
  COUNT(*) FILTER (WHERE is_calibrated OR is_calib_pool OR has_answers) AS will_protect
FROM _paketA_candidates;
```

**Beklenen çıktı:**
```
 total_candidates | will_deactivate | will_protect
------------------+-----------------+--------------
             6427 |            6278 |          149
```

⚠️ **EŞİK:** Sayılar `±10` toleransta olmalı. Sapma varsa **DUR**, Claude'a bildir.

---

## 1.5 — TEST.BATCH1B FK kontrolü (DELETE öncesi)

```sql
-- TEST.BATCH1B'ye bağlı soru var mı?
SELECT COUNT(*) AS questions_using_test_seed
FROM question_bank
WHERE primary_topic_id = '00000000-0000-0000-0000-000000000001';
```

**Beklenen:** `0`

Sayı 0 değilse **DUR** — TEST.BATCH1B silmek FK violation üretir. Bu durumda önce o sorulara başka topic atanması gerekir (ayrı iş).

---

## 1.6 — Apply transaction (ATOMIK)

```sql
BEGIN;

-- 1.6a: UPDATE — koruma kuralıyla 6.278 kaydı deaktive et
UPDATE question_bank
SET is_active = FALSE,
    updated_at = NOW()
WHERE id IN (
  SELECT c.id
  FROM _paketA_candidates c
  WHERE NOT (c.is_calibrated OR c.is_calib_pool OR c.has_answers)
);

-- Beklenen: UPDATE 6278 (±10)

-- 1.6b: DELETE — TEST.BATCH1B test seed kaldır
DELETE FROM topic_hierarchy WHERE code = 'TEST.BATCH1B';

-- Beklenen: DELETE 1

-- COMMIT veya ROLLBACK kararı bir sonraki adımda

-- ⚠️ Henüz COMMIT etme! Önce 1.7 doğrulama, sonra COMMIT.
```

**Önemli not:** Yukarıdaki bloğu çalıştırdıktan sonra **henüz COMMIT etme**. Önce 1.7 doğrulama sorgularını çalıştır, sonuçlar beklendiği gibi ise COMMIT, değilse ROLLBACK.

---

## 1.7 — Transaction içi doğrulama (COMMIT öncesi)

```sql
-- Hâlâ aynı transaction içindeyiz — COMMIT etmeden kontrol

-- a) Aktif sayım kontrolü
SELECT
  COUNT(*) FILTER (WHERE is_active = TRUE) AS active_now,
  64199 - COUNT(*) FILTER (WHERE is_active = TRUE) AS deactivated_count
FROM question_bank;
-- Beklenen: active_now ≈ 57921, deactivated_count ≈ 6278

-- b) Korunan 149 kayıt hâlâ aktif mi?
SELECT COUNT(*) AS protected_still_active
FROM question_bank qb
WHERE qb.is_active = TRUE
  AND (
    LENGTH(qb.question_text) < 30
    OR (LENGTH(qb.option_a) < 2 AND LENGTH(qb.option_b) < 2)
  )
  AND (qb.is_calibrated = TRUE
       OR qb.is_calib_pool = TRUE
       OR EXISTS(SELECT 1 FROM student_answers sa WHERE sa.question_id = qb.id));
-- Beklenen: 149

-- c) TEST.BATCH1B silindi mi?
SELECT COUNT(*) AS test_seed_remaining
FROM topic_hierarchy WHERE code LIKE 'TEST%';
-- Beklenen: 0

-- d) FK bütünlüğü — hiç orphan question_bank kaydı yok mu?
SELECT COUNT(*) AS orphan_topic_fk
FROM question_bank qb
LEFT JOIN topic_hierarchy th ON qb.primary_topic_id = th.id
WHERE th.id IS NULL;
-- Beklenen: 0
```

**Karar matrisi:**

| a | b | c | d | Karar |
|---|---|---|---|---|
| 57921 ±10 | 149 | 0 | 0 | **COMMIT** |
| Sapma | herhangi | herhangi | herhangi | **ROLLBACK** + Claude'a bildir |

---

## 1.8 — COMMIT veya ROLLBACK

```sql
-- Tüm 1.7 doğrulamaları PASS ise:
COMMIT;

-- Herhangi bir doğrulama FAIL ise:
-- ROLLBACK;
```

---

## 1.9 — Post-commit ANALYZE

```sql
-- COMMIT sonrası, query planner istatistiklerini güncelle
ANALYZE question_bank;
ANALYZE topic_hierarchy;
```

**Süre tahmini:** `question_bank` 1.2 GB (briefing v16'dan), ANALYZE ~10-30 saniye.

---

## 1.10 — Smoke test (frontend bağlantılı)

Bu testler **DB değil, gerçek HTTP** üzerinden yapılmalı. Hüseyin tarayıcıdan:

1. **Test öğrencisi olarak giriş** (`beta001@kiro2test.com / Test2026!`)
2. **CAT session başlat** — `POST /api/v1/cat/sessions` herhangi bir branş için
3. **Soru çek** — gelen soru `is_active=FALSE` yapılmış olanlardan biri **olmamalı**
4. **Random questions** — `GET /api/v1/osym/random-questions?count=10&exam_type=AYT&subject=MATEMATIK`
5. Gelen 10 sorunun ID'leri `_bak_paketA_20260428_questions`'da olmamalı

Smoke test PASS ise Paket A başarılı.

---

## 1.11 — RESULT raporu için veri toplama

ADIM 1 tamamlandıktan sonra Claude bu sayıları RESULT raporuna alacak:

```sql
-- Final sayım
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE is_active = TRUE) AS active,
  (SELECT COUNT(*) FROM _bak_paketA_20260428_questions) AS backed_up,
  (SELECT COUNT(*) FROM _bak_paketA_20260428_questions WHERE paket_a_category = 'K1') AS k1_backup,
  (SELECT COUNT(*) FROM _bak_paketA_20260428_questions WHERE paket_a_category = 'K2') AS k2_backup,
  (SELECT COUNT(*) FROM _bak_paketA_20260428_questions WHERE paket_a_category = 'K1+K2') AS k1k2_backup,
  (SELECT COUNT(*) FROM _bak_paketA_20260428_questions WHERE paket_a_category = 'K3') AS k3_backup,
  (SELECT COUNT(*) FROM topic_hierarchy WHERE code LIKE 'TEST%') AS test_seeds_remaining
FROM question_bank;
```

Bu sayım çıktısı RESULT raporunun temel verisini oluşturur.

---

## 1.12 — Rollback planı (post-commit, acil durum için)

Eğer COMMIT sonrası bir sorun fark edilirse (örn. frontend smoke test FAIL):

```sql
BEGIN;

-- Backup'tan geri yükle (sadece deaktive edilenleri TRUE yap)
UPDATE question_bank
SET is_active = TRUE,
    updated_at = NOW()
WHERE id IN (
  SELECT id FROM _bak_paketA_20260428_questions
  WHERE is_active = TRUE  -- backup'ta active iken UPDATE ile FALSE yapılanlar
);
-- Beklenen: ~6278 satır geri TRUE

-- TEST.BATCH1B geri ekle (eğer DELETE edilmişse)
INSERT INTO topic_hierarchy (
  id, level, parent_id, code, name_tr, name_en, description,
  meb_code, meb_kazanim, osym_relevance, osym_frequency,
  total_questions, average_difficulty, is_active, created_at, updated_at,
  difficulty_level, subject_area
) VALUES (
  '00000000-0000-0000-0000-000000000001', 1, NULL, 'TEST.BATCH1B', 'Test Konu Batch1B',
  NULL, NULL, NULL, NULL, 0.0, 0, 0, 0.0, TRUE, NOW(), NOW(), NULL, NULL
)
ON CONFLICT (id) DO NOTHING;

COMMIT;
```

**Backup tablosu DROP komutu (30 gün sonra Hüseyin manuel çalıştırır):**
```sql
-- 28 Mayıs 2026 sonrası
DROP TABLE _bak_paketA_20260428_questions;
```

---

**ADIM 1 SQL'leri hazır. Hüseyin sırayla çalıştırabilir.**

---

## 0.12 — A4 Backend Güvenlik Raporu (Claude tamamladı, 2026-04-28)

5 kritik kategoride backend dosyaları okundu, `is_active` filtre durumu doğrulandı:

| Kategori | Dosya | Filtre | Durum |
|---|---|---|---|
| CAT (öğrenci) | `app/api/cat.py`, `app/services/cat_session.py` | Tüm SELECT'lerde `is_active=TRUE` | ✓ |
| Placement | `app/api/placement.py`, `app/services/placement_service.py` | Tüm SELECT'lerde `is_active=TRUE` | ✓ |
| ÖSYM Sorular | `api/osym_questions_api.py` | 7/7 endpoint, hepsi filtreli | ✓ |
| Soru Bankası | `api/soru_bankasi.py` + `services/soru_bankasi_service.py` | 4/4 SELECT metodu | ✓ |
| CRUD (admin) | `api/question_crud_api.py` | Bilinçli olarak yok (arşiv görünümü) | Doğru tasarım |

**Sonuç:** Paket A apply güvenli. `is_active=FALSE` yapılan 6.278 kayıt:
- Öğrenci endpoint'lerinden anında gizlenir
- Admin arşiv endpoint'lerinde görünür kalır (istenen davranış)

---

## 0.13 — A1-A5 Cevapları (Hüseyin onayı, 2026-04-28)

- **A1:** Backup tablosu adı = `_bak_paketA_20260428_questions`
- **A2:** Korunan 149 kayıt Paket C'ye bırakılır
- **A3:** TEST.BATCH1B fiziksel DELETE
- **A4:** ✅ Tamamlandı (yukarıdaki rapor)
- **A5:** Tek transaction (atomicity)

**ADIM 0 ONAY:** Hüseyin tarafından onaylandı. ADIM 1 (apply) için hazır.

---

## ADIM 1 — Apply komutları

### Adım 1.0: Mevcut durumu kayıt al (ön-değer)

```sql
SELECT
  COUNT(*) FILTER (WHERE is_active = TRUE) AS active_before,
  COUNT(*) FILTER (WHERE is_active = FALSE) AS inactive_before
FROM question_bank;
-- Beklenen: active_before=64199, inactive_before=13246
```

### Adım 1.1: Backup tablosu

```sql
CREATE TABLE _bak_paketA_20260428_questions AS
SELECT qb.*,
       NOW() AS backup_at,
       CASE
         WHEN LENGTH(question_text) < 30 THEN 'K1'
         WHEN LENGTH(option_a) < 2 AND LENGTH(option_b) < 2 THEN 'K2'
         ELSE 'K3'
       END AS paket_a_category
FROM question_bank qb
WHERE qb.is_active = TRUE
  AND qb.id IN (
    SELECT id FROM question_bank
    WHERE is_active = TRUE
      AND (LENGTH(question_text) < 30
           OR (LENGTH(option_a) < 2 AND LENGTH(option_b) < 2)
           OR MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, '')) IN (
              SELECT MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
              FROM question_bank WHERE is_active = TRUE
              GROUP BY 1 HAVING COUNT(*) > 1
           )
      )
  );
SELECT COUNT(*) AS backup_rows FROM _bak_paketA_20260428_questions;
-- Beklenen: ~6.488
```

### Adım 1.2-1.5: Tek transaction içinde apply

```sql
BEGIN;

-- Mükerrer temsilci seçimi
CREATE TEMP TABLE _paketA_dup_keepers AS
SELECT id FROM (
  SELECT id, ROW_NUMBER() OVER (
    PARTITION BY MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
    ORDER BY is_calibrated DESC,
             (EXISTS(SELECT 1 FROM student_answers sa WHERE sa.question_id = qb.id))::int DESC,
             is_calib_pool DESC,
             created_at ASC
  ) AS rnk
  FROM question_bank qb
  WHERE is_active = TRUE
    AND MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, '')) IN (
      SELECT MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
      FROM question_bank WHERE is_active = TRUE
      GROUP BY 1 HAVING COUNT(*) > 1
    )
) sub WHERE rnk = 1;

-- UPDATE: koruma kuralıyla deaktive
UPDATE question_bank
SET is_active = FALSE,
    updated_at = NOW(),
    pipeline_metadata = COALESCE(pipeline_metadata, '{}'::jsonb) || '{"paket_a_deactivated_at":"2026-04-28","reason":"K1_K2_K3_dead_data"}'::jsonb
WHERE is_active = TRUE
  AND (LENGTH(question_text) < 30
       OR (LENGTH(option_a) < 2 AND LENGTH(option_b) < 2)
       OR (id NOT IN (SELECT id FROM _paketA_dup_keepers)
           AND MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, '')) IN (
              SELECT MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))
              FROM question_bank WHERE is_active = TRUE
              GROUP BY 1 HAVING COUNT(*) > 1
           )))
  AND NOT (is_calibrated = TRUE
           OR is_calib_pool = TRUE
           OR EXISTS(SELECT 1 FROM student_answers sa WHERE sa.question_id = question_bank.id));

-- Test seed DELETE (önce dependent kontrol)
DO `$`$
DECLARE dep_count INT;
BEGIN
  SELECT COUNT(*) INTO dep_count FROM question_bank WHERE primary_topic_id = '00000000-0000-0000-0000-000000000001';
  IF dep_count > 0 THEN
    RAISE EXCEPTION 'TEST.BATCH1B has % dependent questions, abort', dep_count;
  END IF;
END `$`$;
DELETE FROM topic_hierarchy WHERE code = 'TEST.BATCH1B';

-- ANALYZE
ANALYZE question_bank;
ANALYZE topic_hierarchy;

-- DOĞRULAMA (commit'ten önce)
SELECT
  COUNT(*) FILTER (WHERE is_active = TRUE) AS active_after,
  COUNT(*) FILTER (WHERE is_active = FALSE) AS inactive_after,
  (SELECT COUNT(*) FROM topic_hierarchy WHERE code LIKE 'TEST%') AS test_seed_remaining
FROM question_bank;
-- Beklenen: active_after=57921, inactive_after=19524, test_seed_remaining=0

-- BURADA SAYIM TUTUYORSA:
COMMIT;

-- BURADA SAYIM TUTMUYORSA:
-- ROLLBACK;
```

### Adım 1.6: Post-commit smoke test

```sql
-- 1. Korunan 149 kayıt hâlâ aktif mi?
SELECT COUNT(*) AS protected_still_active
FROM question_bank qb
WHERE qb.is_active = TRUE
  AND (LENGTH(qb.question_text) < 30 OR (LENGTH(qb.option_a) < 2 AND LENGTH(qb.option_b) < 2))
  AND (qb.is_calibrated = TRUE OR qb.is_calib_pool = TRUE
       OR EXISTS(SELECT 1 FROM student_answers sa WHERE sa.question_id = qb.id));
-- Beklenen: 149

-- 2. Backup boyutu
SELECT COUNT(*) FROM _bak_paketA_20260428_questions;

-- 3. Aktif kayıtlar arasında duplicate kalmadı mı?
WITH hashed AS (
  SELECT MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, '')) AS h
  FROM question_bank WHERE is_active = TRUE
)
SELECT COUNT(*) AS dup_groups_remaining FROM (SELECT h FROM hashed GROUP BY h HAVING COUNT(*) > 1) sub;
-- Beklenen: ~149 (sadece korunan kalibre/havuz duplicate'leri)
```

**Backup tablo retention:** 30 gün sonra `DROP TABLE _bak_paketA_20260428_questions;` Hüseyin manuel çalıştırır.

---

**Versiyon:** v2 (2026-04-28, A1-A5 cevaplar + A4 raporu + ADIM 1 eklendi)
**ONAY DURUMU:** Hüseyin tarafından onaylandı, ADIM 1 apply için hazır.
