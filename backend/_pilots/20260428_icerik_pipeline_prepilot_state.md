# Pre-pilot state - Mini-migration: soru_hash + manual_review_queue + question_bank_staging

**Tarih:** 2026-04-28 (ADIM 0)
**Repo:** C:\Users\husey\kiro2
**Pilot tipi:** Schema migration (3 yeni schema objesi + 1-satir cleanup)
**Baglam:** Icerik Pipeline v1.2.1 on-kosulu - hash bazli conflict policy ve manual review queue gerekli
**Onceki RESULT:** .cursor/plans/20260428_paket_a_dead_data_cleanup_RESULT.md (Paket A PASS)

---

## 0.0 - Ozet saglik

| Alan | Deger |
|------|-------|
| DB host:port | host.docker.internal:5434 (host PostgreSQL 18) |
| DB name | kiro2 |
| Alembic head | diary_drift_recovery_20260422 |
| question_bank toplam | 77.445 |
| question_bank is_active=TRUE | 57.921 (Paket A sonrasi) |
| question_bank is_active=FALSE | 19.524 |
| Aktif arasinda duplicate gruplari | 1 (2 Esen Cografya, ikisi de havuzda) |
| Tum tablo duplicate satirlari | 196 (95 pasif grup + 1 aktif grup) |
| manual_review_queue tablosu | YOK |
| question_bank_staging tablosu | YOK |
| soru_hash kolonu | YOK |

---

## 0.1 - Pilot amaci (tek cumle)

Icerik Pipeline v1.2.1'in conflict policy'si icin gerekli 3 schema objesini olusturmak: (1) question_bank.soru_hash kolonu + 77K satir backfill + partial UNIQUE INDEX (aktif arasinda), (2) manual_review_queue tablosu, (3) question_bank_staging tablosu.

**Bu pilot ne DEGILDIR:**
- Ana icerik pipeline pilotu degil (o ayri, mini-migration sonrasi)
- question_bank veri degisikligi degil (sadece kolon ekleme + backfill)
- 1 satirlik hedefli cleanup (Esen Aps Cografya is_calib_pool=FALSE) - UNIQUE INDEX engelini kaldirmak icin

---

## 0.2 - Etkilenecek kayitlar

### Cleanup: 1 satir UPDATE (UNIQUE INDEX engeli icin)

ID: 10e2304d-a613-50c7-847d-d2d304571220
Source: Esen Aps Cografya Soru Bankasi sayfa 98
Mevcut: is_calib_pool=TRUE, is_calibrated=FALSE, calibration_sample_size=0, times_asked=0
Hedef: is_calib_pool=FALSE (havuzdan cikar, is_active=TRUE kalir)

Gerekce: Bu kayit ile 0d6e5dbe-57a7-51e0-a4f6-0b6d1b792e2c (Esen Tyt Cografya sayfa 90) ayni hash'e sahip; ikisi de hicbir zaman kullanilmamis (calib_sample=0, times_asked=0). Esen Tyt versiyonu daha kanonik (sinav turu explicit) -> Aps versiyonunu havuzdan cikariyoruz. Diger kayit havuzda kaliyor, denge bozulmaz.

### Backfill: 77.445 satir UPDATE (soru_hash kolonu doldurma)

Tahmini sure: 2-3 saniye (PostgreSQL native MD5 hizli)
Performans testi: 100 satir / 1.1 ms (Seq Scan)

### Yeni schema objeleri

3 yeni: 1 kolon + 1 partial unique index + 2 tablo

---

## 0.3 - Uygulanacak SQL (TASLAK, ADIM 1'de revize edilebilir)

### Adim 0.3.1 - On-kosul cleanup (1 satir)

```sql
UPDATE question_bank
SET is_calib_pool = FALSE,
    updated_at = NOW(),
    pipeline_metadata = (COALESCE(pipeline_metadata::jsonb, '{}'::jsonb) ||
                         '{"prepilot_dedup_at":"2026-04-28","reason":"unique_index_conflict_with_id_0d6e5dbe"}'::jsonb)::json
WHERE id = '10e2304d-a613-50c7-847d-d2d304571220';
-- Beklenen: UPDATE 1
```

### Adim 0.3.2 - Yeni kolon ekleme + backfill

```sql
ALTER TABLE question_bank
ADD COLUMN soru_hash VARCHAR(32);

UPDATE question_bank
SET soru_hash = MD5(LOWER(TRIM(question_text)) || '|' ||
                    option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' ||
                    COALESCE(option_e, ''));
-- Beklenen: UPDATE 77445

-- Hicbir kayit NULL kalmamali
SELECT COUNT(*) FROM question_bank WHERE soru_hash IS NULL;
-- Beklenen: 0

-- Index (partial - sadece aktif kayitlar uzerinde unique)
CREATE UNIQUE INDEX uq_qb_soru_hash_active
ON question_bank (soru_hash)
WHERE is_active = TRUE;
-- Beklenen: CREATE INDEX (basarili, cunku 0.3.1 ile aktif duplicate kalmadi)

-- Hash lookup'lari icin genel index (non-unique, full table)
CREATE INDEX idx_qb_soru_hash ON question_bank (soru_hash);
```

### Adim 0.3.3 - manual_review_queue tablosu

```sql
CREATE TABLE manual_review_queue (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  old_question_id VARCHAR NOT NULL REFERENCES question_bank(id),
  new_payload_json JSONB NOT NULL,
  reason          TEXT NOT NULL,
  source_book     VARCHAR,
  source_page     INT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_at     TIMESTAMPTZ,
  reviewed_by     VARCHAR REFERENCES users(id),
  decision        VARCHAR CHECK (decision IN ('keep_old', 'replace', 'merge', 'pending'))
);

CREATE INDEX idx_mrq_old_qid ON manual_review_queue (old_question_id);
CREATE INDEX idx_mrq_decision ON manual_review_queue (decision) WHERE decision = 'pending' OR decision IS NULL;
```

### Adim 0.3.4 - question_bank_staging tablosu

```sql
CREATE TABLE question_bank_staging (
  -- question_bank ile AYNI 73 kolon (LIKE clause ile)
  LIKE question_bank INCLUDING DEFAULTS,

  -- Staging-specific kolonlar
  staging_id        UUID DEFAULT gen_random_uuid(),
  staging_status    VARCHAR NOT NULL DEFAULT 'pending'
                    CHECK (staging_status IN ('pending', 'validated', 'conflict_kept_old', 'conflict_replaced', 'failed')),
  staging_batch_id  VARCHAR NOT NULL,
  staging_created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE question_bank_staging ADD PRIMARY KEY (staging_id);

CREATE INDEX idx_qbs_status ON question_bank_staging (staging_status);
CREATE INDEX idx_qbs_batch ON question_bank_staging (staging_batch_id);
CREATE INDEX idx_qbs_hash ON question_bank_staging (soru_hash) WHERE soru_hash IS NOT NULL;
```

---

## 0.4 - Alembic migration script

Migration adi: 20260428_add_soru_hash_and_pipeline_v12_tables
Down revision: diary_drift_recovery_20260422
Olusturma: alembic revision -m "add_soru_hash_and_pipeline_v12_tables" (manuel olarak elle yazilacak, autogenerate KULLANILMAYACAK - CLAUDE.md kurali)

Upgrade SQL: yukaridaki 0.3.1 + 0.3.2 + 0.3.3 + 0.3.4 sirasiyla
Downgrade SQL:
```sql
DROP TABLE IF EXISTS question_bank_staging CASCADE;
DROP TABLE IF EXISTS manual_review_queue CASCADE;
DROP INDEX IF EXISTS uq_qb_soru_hash_active;
DROP INDEX IF EXISTS idx_qb_soru_hash;
ALTER TABLE question_bank DROP COLUMN IF EXISTS soru_hash;
-- NOT: 0.3.1 cleanup geri alinmaz (1 satir, manual ihtiyac olursa Huseyin)
```

---

## 0.5 - Dogrulama sorgulari (post-apply)

```sql
-- 1. Cleanup uygulandi mi
SELECT id, is_calib_pool FROM question_bank WHERE id = '10e2304d-a613-50c7-847d-d2d304571220';
-- Beklenen: is_calib_pool = FALSE

-- 2. Soru_hash kolonu var mi, hepsi dolu mu
SELECT
  COUNT(*) FILTER (WHERE soru_hash IS NOT NULL) AS hash_filled,
  COUNT(*) FILTER (WHERE soru_hash IS NULL) AS hash_null,
  COUNT(DISTINCT soru_hash) AS distinct_hashes
FROM question_bank;
-- Beklenen: hash_filled=77445, hash_null=0, distinct_hashes=77249 (96 grup duplicate, hepsi pasif)

-- 3. UNIQUE INDEX (partial) calisir mi - aktif arasinda duplicate yok
WITH dup AS (
  SELECT soru_hash FROM question_bank WHERE is_active = TRUE
  GROUP BY soru_hash HAVING COUNT(*) > 1
)
SELECT COUNT(*) AS active_dup_groups FROM dup;
-- Beklenen: 0

-- 4. manual_review_queue ve question_bank_staging tablolari
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('manual_review_queue', 'question_bank_staging');
-- Beklenen: 2 satir

-- 5. Alembic head guncellendi mi
SELECT version_num FROM alembic_version;
-- Beklenen: 20260428_add_soru_hash_and_pipeline_v12_tables (yeni revision)
```

---

## 0.6 - Geri alma plani (rollback)

Migration alembic ile uygulandi -> alembic downgrade -1 ile geri alinabilir.

```bash
docker exec kiro2-backend alembic downgrade diary_drift_recovery_20260422
```

Cleanup (0.3.1) geri alimi: backup yok, ama UPDATE'i ters cevirmek kolay:
```sql
UPDATE question_bank SET is_calib_pool = TRUE WHERE id = '10e2304d-a613-50c7-847d-d2d304571220';
```

---

## 0.7 - Riskler

| # | Risk | Olasilik | Etki | Onlem |
|---|------|----------|------|-------|
| RA1 | Backfill 77K satirda yavas (target: <10sn) | Dusuk | Dusuk | EXPLAIN gosterdi: 100 satir 1.1ms, lineer scale = 850ms |
| RA2 | Cleanup yapilmadan UNIQUE INDEX olusturmaya calisilir, fail | Dusuk | Orta | 0.3.1 0.3.2'den ONCE calisir, sira garantili |
| RA3 | Backend pipeline_metadata json/jsonb tip uyusmazligi | Dusuk | Dusuk | 0.3.1'de cast pattern Paket A'da test edildi |
| RA4 | manual_review_queue tablosunda gen_random_uuid() yok | Dusuk | Dusuk | PostgreSQL 13+ standart, KIRO2 PostgreSQL 18 kullaniyor |
| RA5 | question_bank_staging LIKE question_bank ile constraint cakismasi | Orta | Dusuk | LIKE INCLUDING DEFAULTS kullaniliyor; PRIMARY KEY ayri eklenecek |
| RA6 | Alembic autogenerate kullanmak istenirse | Dusuk | Yuksek | CLAUDE.md kurali: kullanilmaz (kalici yasak); manuel yazim sart |
| RA7 | Mini-migration sonrasi pipeline v1.2.1 schema mismatch | Dusuk | Yuksek | INSERT sablonu Bolum 5.5'te zaten 73 kolon icin yazildi, hash ekleniyor |
| RA8 | Pasif kayitlar arasinda duplicate (95 grup), partial INDEX gormez | Bilinen | Yok | Partial WHERE is_active=TRUE kullaniyoruz, kabul edilen davranis |

---

## 0.8 - Acik sorular (Huseyin onayi bekliyor)

**B1.** Esen Aps Cografya cleanup (0.3.1): is_calib_pool=FALSE mi yoksa is_active=FALSE mi?
- Onerim: is_calib_pool=FALSE (kayit aktif kalir, sadece havuzdan cikar). Diger Esen Tyt versiyonu havuzda zaten var, denge etkilenmez.

**B2.** UNIQUE INDEX kapsami: partial (WHERE is_active=TRUE) mi yoksa full table mi?
- Onerim: Partial. Full table 196 dup yuzunden fail eder. Partial daha temiz, aktif kayitlari korur.
- Alternatif: Full table icin once 196 dup'i temizle (ek 1 saatlik is, gereksiz).

**B3.** soru_hash kolonu NOT NULL mi olsun, NULL'a izin verilsin mi?
- Onerim: Backfill sonrasi NOT NULL constraint ekle. Yeni INSERT'ler hash hesaplamadan gelmemeli.
- Alternatif: Trigger ile otomatik hash hesabi; ama daha karmasik.

**B4.** Migration dosyasi nereye? backend/alembic/versions/ icine yazip docker cp ile container'a gonderilecek (CLAUDE.md kurali: "Migration dosyalari local'de yaratilip docker cp ile container'a").
- Onerim: Standart KIRO2 deploy cycle.

**B5.** Bu pilot tek transaction mi, yoksa adim adim mi?
- Onerim: Alembic ile tek migration -> alembic upgrade tek transaction'da calisir. PostgreSQL'in DDL'leri transactional olmasi avantaj.

---

## 0.9 - Kabul kriterleri (PASS/FAIL)

**PASS:**
- 0.3.1 UPDATE = 1 satir
- 0.3.2 ADD COLUMN basarili, UPDATE 77445 satir, soru_hash NULL = 0
- 0.3.2 UNIQUE INDEX olusturuldu (cleanup sonrasi 0 active dup)
- 0.3.3 manual_review_queue var
- 0.3.4 question_bank_staging var (76+ kolon: 73 + staging_*)
- alembic_version = yeni revision
- Backend health 5/5
- /api/v1/osym/statistics hala 57921 donuyor (Paket A statu degismedi)

**FAIL (geri al):**
- ALTER TABLE basarisiz (constraint conflict)
- Backfill UPDATE < 77445 (bazi satirlar atlandi)
- UNIQUE INDEX fail (active duplicate kaldi)
- Tablo CREATE basarisiz (LIKE conflict, gen_random_uuid yok vb.)

---

## 0.10 - Siradaki adimlar

1. Huseyin: Bu state.md'yi gozden gecir, B1-B5 sorularini cevapla
2. Claude: Cevaplara gore state.md guncelle, alembic migration script yaz
3. Huseyin: Migration dosyasini local'de yaz, docker cp ile container'a gonder
4. Huseyin: alembic upgrade head, smoke test
5. Claude: Mini-migration RESULT raporu
6. -> Ana icerik pipeline pilotu (v1.2.1 - 500 sayfa Matematik)

---

## 0.11 - Plan disi birakilan eksiklikler (referans)

Sistematik DB taramasinda bulunan ama mini-migration kapsami disinda olanlar:
- K4 (66 bos topic): Pipeline v1.2 ile cozulecek
- K5 (cross-subject FK bozuklugu): Paket B (opsiyonel)
- K6 (irt_a/b/c kullanilmamis): Paket C
- K7 (duplicate index'ler): Paket C
- K9 (briefing v16 outdated): Briefing v17 ayri is
- K10 (root topic subject_area=NULL): Paket C

Bu pilot sadece mini-migration'i (3 schema objesi + 1 cleanup) cozer.

---

**Versiyon:** v1 (2026-04-28, ADIM 0 ilk yazim)
**Huseyin onayi bekliyor.**
