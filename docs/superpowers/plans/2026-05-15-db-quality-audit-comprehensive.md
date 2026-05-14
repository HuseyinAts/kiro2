# KIRO2 Veritabanı Kapsamlı Kalite & Doğruluk Audit Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** KIRO2 question_bank tablosundaki tüm OCR / soru-cevap eşleşmesi / metadata verilerinin doğruluğunu, tutarlılığını ve kalitesini sistematik olarak doğrulamak.

**Architecture:** 16 ayrı doğrulama task'ı, her biri farklı bir DB aspect'i (Tier'lar, schema, cross-source validation, edge case). Her task: SQL query / Python script + sample pixel-verification + RESULT artifact. Sapma tespit edilirse FIX action önerilir, doğrulama PASS'lerse RESULT.md'e kaydedilir.

**Tech Stack:** PostgreSQL 18 (port 5434, db `kiro2`), Python 3.11+ sqlalchemy, `psql.exe` Windows path, `d-dataset/eslesmis_sorucevap.jsonl` (77K), `d-dataset/output/answer_keys_v8/answers_v8.db` (SQLite), `d-dataset/output/ocr_crops/results.jsonl` (333K).

**Audit Scope (DB Snapshot):**
- 187,834 toplam soru (167,559 aktif + 20,275 pasif)
- 152,412 image_url var (Tier A/B/C/D/E/F/G/H kümülatif)
- 420 kitap
- 8 pipeline_metadata flag tipi: `tier_c_match`, `tier_d_match`, `tier_e_match`, `tier_f_match`, `tier_g_match`, `tier_h_match`, `book_key_match`, `sanity_flags`, `ocr_quality_flag`

**Çıktı:** `backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md` (her task'ın bulgusu birleştirilmiş özet).

**Risk önceliklendirme (sample doğrulama önceliği):**
1. Tier H (49,468) — q_index_in_page yorumlama riski yüksek (en büyük scope)
2. Tier G (2,493) — sim 0.40-0.50 bucket'ında %15-20 false-positive
3. Tier F (7,441) — sim 0.50-0.70 borderline
4. Tier D (13,741) — pilot %96 ama text similarity bağımlı
5. Tier E (4,315) — q_no normalize hatası riski

---

## Task 1: DB Integrity Snapshot ve Tier Coverage

**Files:**
- Create: `backend/_pilots/audit_task01_db_snapshot.sql`
- Read: `backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md` (append)

- [ ] **Step 1: Satır sayıları ve image_url breakdown SQL'i yaz**

```sql
-- audit_task01_db_snapshot.sql
\echo '=== TASK 01: DB INTEGRITY SNAPSHOT ==='

-- 1.1 Toplam/aktif sayım
SELECT
  COUNT(*) AS toplam,
  COUNT(*) FILTER (WHERE is_active=TRUE) AS aktif,
  COUNT(*) FILTER (WHERE is_active=FALSE) AS pasif,
  COUNT(DISTINCT source_book) AS kitap_sayisi
FROM question_bank;

-- 1.2 Image URL Tier dağılımı (aktif satırlar)
SELECT
  CASE
    WHEN pipeline_metadata::jsonb -> 'tier_c_match' IS NOT NULL THEN 'C'
    WHEN pipeline_metadata::jsonb -> 'tier_d_match' IS NOT NULL THEN 'D'
    WHEN pipeline_metadata::jsonb -> 'tier_e_match' IS NOT NULL THEN 'E'
    WHEN pipeline_metadata::jsonb -> 'tier_f_match' IS NOT NULL THEN 'F'
    WHEN pipeline_metadata::jsonb -> 'tier_g_match' IS NOT NULL THEN 'G'
    WHEN pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL THEN 'H'
    WHEN question_image_url IS NOT NULL THEN 'AB_legacy'
    ELSE 'NULL'
  END AS tier,
  COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
GROUP BY 1 ORDER BY 2 DESC;

-- 1.3 has_diagram x image_url crosstab
SELECT
  pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram' AS hd,
  CASE WHEN question_image_url IS NULL THEN 'NULL' ELSE 'VAR' END AS img,
  COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
GROUP BY 1, 2 ORDER BY 1, 2;
```

- [ ] **Step 2: SQL'i çalıştır**

Run: `"C:/Program Files/PostgreSQL/18/bin/psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -P pager=off -f backend/_pilots/audit_task01_db_snapshot.sql`

Expected:
- toplam=187,834, aktif=167,559, pasif=20,275
- 6 tier (C/D/E/F/G/H + AB_legacy + NULL)
- has_diagram=true & img=VAR ≥ 44,000 (missing <%5 yansıması)

- [ ] **Step 3: Sapma kontrolü — bekleniyor:**

- AB_legacy toplam: 59,187 (Session 157 öncesi populate olmuş Tier A+B)
- Tier H: 49,468 (Session 158 son apply)
- Tier D: 13,741, F: 7,441, E: 4,315, G: 2,493, C: 16,440

- [ ] **Step 4: RESULT.md'e Task 1 bölümü yaz**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<'EOF'
## Task 1: DB Snapshot
- Toplam/aktif: <numbers>
- Tier dağılımı: <breakdown>
- has_diagram crosstab: <table>
- VERDICT: PASS / FAIL (eğer numaralar beklenmeyen)
EOF
```

- [ ] **Step 5: Commit Task 1 artifact**

```bash
git add backend/_pilots/audit_task01_db_snapshot.sql backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task01): DB integrity snapshot baseline"
```

---

## Task 2: Tier H Pixel Verification (KRİTİK — en büyük scope)

**Files:**
- Create: `backend/_pilots/audit_task02_tier_h_verify.py`

Tier H, Session 158'in son tier'ı, **49,468 satır UPDATE** ile en büyük çaplı değişikliği yaptı. `pipeline_metadata.ai_extras.q_index_in_page` field interpretation doğru muydu? **30 random sample** alıp DB question_text ile disk crop'a karşılık gelen OCR text karşılaştırılacak. Eğer disk crop için OCR yoksa, en azından filename pattern + DB metadata tutarlılığı kontrol edilecek.

- [ ] **Step 1: 30 random Tier H sample fetch script'i yaz**

```python
# backend/_pilots/audit_task02_tier_h_verify.py
import sys, os, json, unicodedata
from collections import defaultdict
from pathlib import Path
from sqlalchemy import create_engine, text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except ImportError: pass
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2").replace("postgresql+asyncpg://", "postgresql://").replace("/kiro2_db", "/kiro2")
engine = create_engine(db_url)

OCR_PATH = Path("d-dataset/output/ocr_crops/results.jsonl")

# OCR index için (book, page) → entries
ocr_idx = defaultdict(list)
with OCR_PATH.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: d = json.loads(line)
        except: continue
        book = unicodedata.normalize("NFC", (d.get("book","") or "").replace("_"," ").strip())
        try: page = int(d.get("page_num"))
        except: continue
        if not book: continue
        ocr_idx[(book, page)].append(d)

def text_sim(a, b):
    if not a or not b: return 0.0
    sa = set(unicodedata.normalize("NFC", a).lower().split())
    sb = set(unicodedata.normalize("NFC", b).lower().split())
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0

with engine.connect() as c:
    rows = list(c.execute(text("""
        SELECT id::text, source_book, source_page,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page')::int AS qip,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') AS hd,
               pipeline_metadata::jsonb -> 'tier_h_match' ->> 'crop_file' AS crop_file,
               LEFT(question_text, 200) AS qt
        FROM question_bank
        WHERE is_active=TRUE
          AND pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL
        ORDER BY md5(id::text)
        LIMIT 30
    """)))

print(f"Tier H 30 random sample, OCR text similarity karşılaştırma:")
ok = 0; suspicious = 0; no_ocr = 0
for qid, book, page, qip, hd, cf, qt in rows:
    nbook = unicodedata.normalize("NFC", book.strip())
    cands = ocr_idx.get((nbook, page), [])
    # crop_q_no'yu filename'den çıkar
    import re
    m = re.search(r"_p\d{4}_q(\d{1,3})", cf or "")
    if not m: continue
    crop_q = int(m.group(1))
    # crop_q ile q_index_in_page eşleşmeli (exact match invariant)
    if crop_q != qip:
        suspicious += 1
        print(f"  SAPMA: id={qid[:8]} qip={qip} crop_q={crop_q} (uyumsuz!)")
        continue
    # OCR'da bu crop'a karşılık gelen entry var mı?
    matching = [e for e in cands if e.get("crop_file") == cf]
    if not matching:
        no_ocr += 1
        continue
    ocr_text = matching[0].get("soru_metni", "") or ""
    sim = text_sim(qt, ocr_text)
    if sim >= 0.50:
        ok += 1
    else:
        suspicious += 1
        print(f"  DÜŞÜK SIM: id={qid[:8]} sim={sim:.3f} qip={qip} crop_q={crop_q}")
print(f"\nÖZET: ok={ok}, suspicious={suspicious}, no_ocr_text={no_ocr}")
print(f"Accuracy ratio: {ok}/{len(rows)} = {100*ok/len(rows):.1f}%")
```

- [ ] **Step 2: Çalıştır**

Run: `cd C:/Users/husey/kiro2 && python backend/_pilots/audit_task02_tier_h_verify.py`

Expected:
- 30 sample içinde `qip == crop_q` invariant %100 (yoksa script bug)
- ok ≥ 24 (%80+)
- suspicious + no_ocr_text ≤ 6

- [ ] **Step 3: Eğer suspicious > 6 ise:**

`cd C:/Users/husey/kiro2 && python -c "
from sqlalchemy import create_engine, text; import os
db_url = os.getenv('DATABASE_URL','postgresql://postgres:1470@localhost:5434/kiro2').replace('postgresql+asyncpg://','postgresql://').replace('/kiro2_db','/kiro2')
e = create_engine(db_url)
with e.connect() as c:
    r = c.execute(text(\"\"\"
        SELECT id::text, source_book, source_page,
               (pipeline_metadata::jsonb->'ai_extras'->>'q_index_in_page')::int AS qip,
               pipeline_metadata::jsonb->'tier_h_match'->>'crop_file' AS cf
        FROM question_bank WHERE pipeline_metadata::jsonb->'tier_h_match' IS NOT NULL
        ORDER BY md5(id::text) LIMIT 1
    \"\"\")).fetchone()
    print(r)
"`

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 2: Tier H Pixel Verification (49,468 satır)
- 30 sample sonuç: ok=<N>, suspicious=<M>, no_ocr=<X>
- Accuracy: <Y>%
- VERDICT: PASS (>%80) / WARN (60-80) / FAIL (<60)
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task02_tier_h_verify.py backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task02): Tier H pixel verify 30 sample"
```

---

## Task 3: Tier G Sample Verification (sim 0.40-0.50 high-risk bucket)

**Files:**
- Create: `backend/_pilots/audit_task03_tier_g_verify.py`

Tier G %15-20 false-positive bekleniyordu. Sample dağılımını ölç + 20 random satırın DB text vs OCR text Jaccard similarity'sini yeniden hesapla. Eğer mevcut `similarity` field DB'de saklı ile yeniden hesaplanan farklıysa = drift.

- [ ] **Step 1: 20 random Tier G sample analiz script'i yaz**

```python
# backend/_pilots/audit_task03_tier_g_verify.py
import sys, os, json, unicodedata
from collections import defaultdict
from pathlib import Path
from sqlalchemy import create_engine, text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except ImportError: pass
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2").replace("postgresql+asyncpg://", "postgresql://").replace("/kiro2_db", "/kiro2")
engine = create_engine(db_url)

ocr_idx = defaultdict(list)
with Path("d-dataset/output/ocr_crops/results.jsonl").open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: d = json.loads(line)
        except: continue
        book = unicodedata.normalize("NFC", (d.get("book","") or "").replace("_"," ").strip())
        try: page = int(d.get("page_num"))
        except: continue
        if book: ocr_idx[(book, page)].append(d)

def sim(a, b):
    sa = set(unicodedata.normalize("NFC", a or "").lower().split())
    sb = set(unicodedata.normalize("NFC", b or "").lower().split())
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0

with engine.connect() as c:
    rows = list(c.execute(text("""
        SELECT id::text, source_book, source_page,
               (pipeline_metadata::jsonb -> 'tier_g_match' ->> 'similarity')::float AS stored_sim,
               pipeline_metadata::jsonb -> 'tier_g_match' ->> 'crop_file' AS cf,
               pipeline_metadata::jsonb -> 'tier_g_match' ->> 'tier' AS sub_tier,
               LEFT(question_text, 300) AS qt
        FROM question_bank
        WHERE is_active=TRUE AND pipeline_metadata::jsonb -> 'tier_g_match' IS NOT NULL
        ORDER BY md5(id::text)
        LIMIT 20
    """)))

drift = 0; ok = 0
for qid, book, page, stored_sim, cf, sub_tier, qt in rows:
    nbook = unicodedata.normalize("NFC", book.strip())
    cands = ocr_idx.get((nbook, page), [])
    matched = next((e for e in cands if e.get("crop_file") == cf), None)
    if not matched:
        print(f"  NO_OCR: id={qid[:8]} sub_tier={sub_tier}")
        continue
    recomputed = sim(qt, matched.get("soru_metni", ""))
    delta = abs(recomputed - stored_sim)
    if delta > 0.05:
        drift += 1
        print(f"  DRIFT: id={qid[:8]} stored={stored_sim:.3f} recomputed={recomputed:.3f}")
    else:
        ok += 1

print(f"\nÖZET: ok={ok}, drift={drift}, total={len(rows)}")
```

- [ ] **Step 2: Çalıştır**

Run: `cd C:/Users/husey/kiro2 && python backend/_pilots/audit_task03_tier_g_verify.py`

Expected: drift ≤ 2 (similarity hesaplama deterministik olmalı)

- [ ] **Step 3: Drift > 2 ise: similarity hesaplama deterministik mi araştır**

Olası neden: Türkçe NFC normalize fonksiyonu pipeline'da farklı çalışıyor. Tier G script'i tekrar oku: `backend/scripts/tier_g_combined_recovery.py` line 130 `text_sim` fonksiyonu.

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 3: Tier G Similarity Drift Check (2,493 satır)
- 20 sample sonuç: ok=<N>, drift=<M>
- VERDICT: PASS / DRIFT (similarity recompute farklı)
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task03_tier_g_verify.py backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task03): Tier G similarity drift check"
```

---

## Task 4: Tier F Sample Re-verification (7,441 satır, sim>=0.50)

**Files:**
- Create: `backend/_pilots/audit_task04_tier_f_verify.py`

Tier F pilot %83 worst-case accuracy idi. Re-verify: 30 random sample, db_text vs ocr_text Jaccard, eğer recomputed sim < 0.50 → drift sinyali.

- [ ] **Step 1: Script yaz**

```python
# backend/_pilots/audit_task04_tier_f_verify.py
import sys, os, json, unicodedata
from collections import defaultdict
from pathlib import Path
from sqlalchemy import create_engine, text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except ImportError: pass
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2").replace("postgresql+asyncpg://", "postgresql://").replace("/kiro2_db", "/kiro2")
engine = create_engine(db_url)

ocr_idx = defaultdict(list)
with Path("d-dataset/output/ocr_crops/results.jsonl").open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: d = json.loads(line)
        except: continue
        book = unicodedata.normalize("NFC", (d.get("book","") or "").replace("_"," ").strip())
        try: page = int(d.get("page_num"))
        except: continue
        if book: ocr_idx[(book, page)].append(d)

def sim(a, b):
    sa = set(unicodedata.normalize("NFC", a or "").lower().split())
    sb = set(unicodedata.normalize("NFC", b or "").lower().split())
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0

with engine.connect() as c:
    rows = list(c.execute(text("""
        SELECT id::text, source_book, source_page,
               (pipeline_metadata::jsonb -> 'tier_f_match' ->> 'similarity')::float AS stored_sim,
               pipeline_metadata::jsonb -> 'tier_f_match' ->> 'crop_file' AS cf,
               LEFT(question_text, 300) AS qt
        FROM question_bank
        WHERE is_active=TRUE AND pipeline_metadata::jsonb -> 'tier_f_match' IS NOT NULL
        ORDER BY md5(id::text)
        LIMIT 30
    """)))

print("Tier F 30 sample re-verify:")
buckets = {"high":0, "mid":0, "low":0, "below_thresh":0}
for qid, book, page, stored_sim, cf, qt in rows:
    nbook = unicodedata.normalize("NFC", book.strip())
    cands = ocr_idx.get((nbook, page), [])
    matched = next((e for e in cands if e.get("crop_file") == cf), None)
    if not matched: continue
    r = sim(qt, matched.get("soru_metni", ""))
    if r >= 0.70: buckets["high"] += 1
    elif r >= 0.60: buckets["mid"] += 1
    elif r >= 0.50: buckets["low"] += 1
    else: buckets["below_thresh"] += 1
    if r < 0.40:
        print(f"  CRITICAL: id={qid[:8]} stored={stored_sim:.3f} recomputed={r:.3f}")

for k, n in buckets.items(): print(f"  {k}: {n}")
```

- [ ] **Step 2: Çalıştır**

Run: `cd C:/Users/husey/kiro2 && python backend/_pilots/audit_task04_tier_f_verify.py`

Expected: below_thresh ≤ 3 (originalı ≥ 0.50 ile match etmişti, threshold-altı = drift)

- [ ] **Step 3: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 4: Tier F Sample Verify
- 30 sample: high=<N>, mid=<M>, low=<X>, below=<Y>
- VERDICT: PASS (below ≤ 3) / FAIL
EOF
```

- [ ] **Step 4: Commit**

```bash
git add backend/_pilots/audit_task04_tier_f_verify.py backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task04): Tier F similarity re-verify"
```

---

## Task 5: Tier D + Tier E Re-verification (kümülatif 18,056 satır)

**Files:**
- Create: `backend/_pilots/audit_task05_tier_de_verify.py`

Tier D pilot %96 idi (sim>=0.70). Tier E q_no orphan recovery. 20 random Tier D + 20 random Tier E sample fetch + recompute similarity.

- [ ] **Step 1: Script yaz**

```python
# backend/_pilots/audit_task05_tier_de_verify.py
import sys, os, json, unicodedata
from collections import defaultdict
from pathlib import Path
from sqlalchemy import create_engine, text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except ImportError: pass
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2").replace("postgresql+asyncpg://", "postgresql://").replace("/kiro2_db", "/kiro2")
engine = create_engine(db_url)

ocr_idx = defaultdict(list)
with Path("d-dataset/output/ocr_crops/results.jsonl").open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: d = json.loads(line)
        except: continue
        book = unicodedata.normalize("NFC", (d.get("book","") or "").replace("_"," ").strip())
        try: page = int(d.get("page_num"))
        except: continue
        if book: ocr_idx[(book, page)].append(d)

def sim(a, b):
    sa = set(unicodedata.normalize("NFC", a or "").lower().split())
    sb = set(unicodedata.normalize("NFC", b or "").lower().split())
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0

for tier_flag, tier_name, low_thresh in [("tier_d_match", "Tier D", 0.70), ("tier_e_match", "Tier E", 0.70)]:
    print(f"\n=== {tier_name} ===")
    with engine.connect() as c:
        rows = list(c.execute(text(f"""
            SELECT id::text, source_book, source_page,
                   (pipeline_metadata::jsonb -> '{tier_flag}' ->> 'similarity')::float AS stored_sim,
                   pipeline_metadata::jsonb -> '{tier_flag}' ->> 'crop_file' AS cf,
                   LEFT(question_text, 300) AS qt
            FROM question_bank
            WHERE is_active=TRUE AND pipeline_metadata::jsonb -> '{tier_flag}' IS NOT NULL
            ORDER BY md5(id::text)
            LIMIT 20
        """)))
    below = 0; ok = 0
    for qid, book, page, stored_sim, cf, qt in rows:
        if stored_sim is None: continue  # E1a tier_e exact-match has no similarity
        nbook = unicodedata.normalize("NFC", book.strip())
        cands = ocr_idx.get((nbook, page), [])
        matched = next((e for e in cands if e.get("crop_file") == cf), None)
        if not matched: continue
        r = sim(qt, matched.get("soru_metni", ""))
        if r >= low_thresh:
            ok += 1
        else:
            below += 1
            print(f"  BELOW: id={qid[:8]} stored={stored_sim:.3f} recomputed={r:.3f}")
    print(f"  ok={ok}, below_thresh={below}")
```

- [ ] **Step 2: Çalıştır**

Run: `cd C:/Users/husey/kiro2 && python backend/_pilots/audit_task05_tier_de_verify.py`

Expected: her tier için below ≤ 2

- [ ] **Step 3: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 5: Tier D+E Re-verify
- Tier D 20 sample: ok=<N>, below=<M>
- Tier E 20 sample: ok=<N>, below=<M>
- VERDICT: PASS / DRIFT
EOF
```

- [ ] **Step 4: Commit**

```bash
git add backend/_pilots/audit_task05_tier_de_verify.py backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task05): Tier D+E similarity re-verify"
```

---

## Task 6: Cross-Tier Overlap Detection (aynı satırda birden fazla tier flag olmamalı)

**Files:**
- Create: `backend/_pilots/audit_task06_tier_overlap.sql`

Tier C/D/E/F/G/H apply'larında `WHERE question_image_url IS NULL` koşulu vardı. Bu invariant nedeniyle bir satırda **maksimum 1 tier flag** olmalı (aynı satıra ikinci kez UPDATE atılmamalı). Cross-tier overlap = race condition veya filtre bug.

- [ ] **Step 1: SQL yaz**

```sql
-- audit_task06_tier_overlap.sql
\echo '=== TASK 06: CROSS-TIER OVERLAP ==='

-- Aynı satırda birden fazla tier flag VAR mı?
SELECT
  id::text AS id,
  CASE WHEN pipeline_metadata::jsonb -> 'tier_c_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_d_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_e_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_f_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_g_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL THEN 1 ELSE 0 END
  AS flag_count
FROM question_bank WHERE is_active=TRUE
GROUP BY id, pipeline_metadata
HAVING (
  CASE WHEN pipeline_metadata::jsonb -> 'tier_c_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_d_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_e_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_f_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_g_match' IS NOT NULL THEN 1 ELSE 0 END +
  CASE WHEN pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL THEN 1 ELSE 0 END
) > 1
LIMIT 20;

-- Sayım
SELECT COUNT(*) AS multi_tier_satir
FROM question_bank WHERE is_active=TRUE
  AND (
    CASE WHEN pipeline_metadata::jsonb -> 'tier_c_match' IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN pipeline_metadata::jsonb -> 'tier_d_match' IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN pipeline_metadata::jsonb -> 'tier_e_match' IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN pipeline_metadata::jsonb -> 'tier_f_match' IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN pipeline_metadata::jsonb -> 'tier_g_match' IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN pipeline_metadata::jsonb -> 'tier_h_match' IS NOT NULL THEN 1 ELSE 0 END
  ) > 1;
```

- [ ] **Step 2: Çalıştır**

Run: `"C:/Program Files/PostgreSQL/18/bin/psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -P pager=off -f backend/_pilots/audit_task06_tier_overlap.sql`

Expected: `multi_tier_satir = 0` (image_url IS NULL koşulu invariant'i korur)

- [ ] **Step 3: Eğer > 0 ise:**

Race condition veya filter bug. Sample 20 satırın hangi tier kombinasyonu olduğunu incele, RESULT.md'e ekle.

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 6: Cross-Tier Overlap
- multi_tier_satir = <N>
- VERDICT: PASS (N=0) / CRITICAL (N>0)
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task06_tier_overlap.sql backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task06): cross-tier overlap invariant check"
```

---

## Task 7: Image URL Broken Link Detection

**Files:**
- Create: `backend/_pilots/audit_task07_broken_links.py`

DB'de `question_image_url = /static/crops/<book>/<file>.png` saklanır. Disk'te bu dosyalar gerçekten var mı? Broken link = pipeline-fix bug.

- [ ] **Step 1: Script yaz**

```python
# backend/_pilots/audit_task07_broken_links.py
import sys, os
from pathlib import Path
from sqlalchemy import create_engine, text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except ImportError: pass
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2").replace("postgresql+asyncpg://", "postgresql://").replace("/kiro2_db", "/kiro2")
engine = create_engine(db_url)

CROPS_ROOT = Path("d-dataset/output/crops")

# Disk file cache
disk_files = {}
for p in CROPS_ROOT.iterdir():
    if not p.is_dir(): continue
    try: disk_files[p.name] = {f.name for f in p.iterdir() if f.is_file()}
    except: disk_files[p.name] = set()

with engine.connect() as c:
    # 1000 random image_url sample (her tier'dan)
    rows = list(c.execute(text("""
        SELECT id::text, question_image_url
        FROM question_bank
        WHERE is_active=TRUE AND question_image_url IS NOT NULL
        ORDER BY md5(id::text) LIMIT 1000
    """)))

broken = 0
total = 0
for qid, url in rows:
    # /static/crops/<book_dir>/<file>
    parts = url.replace("/static/crops/", "").split("/", 1)
    if len(parts) != 2:
        broken += 1; continue
    book_dir, file_name = parts
    total += 1
    if book_dir not in disk_files or file_name not in disk_files[book_dir]:
        broken += 1
        if broken <= 5:
            print(f"  BROKEN: id={qid[:8]} url={url[:80]}")

print(f"\n{broken}/{total} broken link ({100*broken/total:.2f}%)")
```

- [ ] **Step 2: Çalıştır**

Run: `cd C:/Users/husey/kiro2 && python backend/_pilots/audit_task07_broken_links.py`

Expected: broken / total ≤ %0.5 (1000'de max 5 broken)

- [ ] **Step 3: Eğer broken > 5 ise:**

Hangi tier'ın broken link ürettiğini tespit et — script'i genişlet:
- Tier H broken (49,468 büyük scope, en muhtemel)
- Tier A/B legacy (eski mapping kaybı)

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 7: Broken Link Detection
- 1000 sample: <broken>/<total> broken (<pct>%)
- VERDICT: PASS (<%0.5) / WARN (0.5-2) / FAIL (>%2)
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task07_broken_links.py backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task07): image_url broken link check"
```

---

## Task 8: pipeline_metadata Schema Validation

**Files:**
- Create: `backend/_pilots/audit_task08_metadata_schema.sql`

Her aktif satırda `pipeline_metadata.ai_extras` mevcut olmalı (62,994 satır var, 4,565 yok). Required field'lar: `has_diagram`, `q_no`, `q_index_in_page`, `latex_required`, `subtopic`, `topic_raw`, `topic_match_quality`, `diagram_description`.

- [ ] **Step 1: SQL yaz**

```sql
-- audit_task08_metadata_schema.sql
\echo '=== TASK 08: SCHEMA VALIDATION ==='

-- 8.1 ai_extras varlığı
SELECT
  COUNT(*) AS toplam_aktif,
  COUNT(*) FILTER (WHERE pipeline_metadata::jsonb -> 'ai_extras' IS NOT NULL) AS ai_extras_var,
  COUNT(*) FILTER (WHERE pipeline_metadata::jsonb -> 'ai_extras' IS NULL) AS ai_extras_yok
FROM question_bank WHERE is_active=TRUE;

-- 8.2 Required field varlığı (sample)
SELECT
  COUNT(*) FILTER (WHERE pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram' IS NULL) AS hd_yok,
  COUNT(*) FILTER (WHERE pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' IS NULL) AS qno_yok,
  COUNT(*) FILTER (WHERE pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page' IS NULL) AS qip_yok,
  COUNT(*) FILTER (WHERE pipeline_metadata::jsonb -> 'ai_extras' ->> 'subtopic' IS NULL) AS subtopic_yok
FROM question_bank
WHERE is_active=TRUE
  AND pipeline_metadata::jsonb -> 'ai_extras' IS NOT NULL;

-- 8.3 has_diagram değerleri (must be boolean-like)
SELECT
  pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram' AS val,
  COUNT(*) AS n
FROM question_bank
WHERE is_active=TRUE
  AND pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram' IS NOT NULL
GROUP BY 1;
```

- [ ] **Step 2: Çalıştır**

Run: `"C:/Program Files/PostgreSQL/18/bin/psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -P pager=off -f backend/_pilots/audit_task08_metadata_schema.sql`

Expected:
- ai_extras_var ≥ 160K
- has_diagram değerleri sadece `true`, `false` veya `NULL` (başka string olmamalı)

- [ ] **Step 3: Sapma varsa:**

ai_extras NULL satırlar legacy ai_solve veya v2.4 era. Bu satırlar audit kapsamı dışı sayılabilir veya manuel review.

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 8: Schema Validation
- ai_extras_var: <N>, yok: <M>
- Field eksikleri: hd_yok=<N>, qno_yok=<M>
- has_diagram değerleri: <enum>
- VERDICT: PASS / WARN
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task08_metadata_schema.sql backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task08): pipeline_metadata schema validation"
```

---

## Task 9: eslesmis_sorucevap.jsonl × DB Cross-Validation

**Files:**
- Create: `backend/_pilots/audit_task09_jsonl_db_xval.py`

Production JSONL 77,336 satır. Her satırın `(book_name, page_number, question_number)` deterministic UUID ile DB'ye yazılmış. Cross-validation: jsonl entry **TÜM**'ünün DB karşılığı var mı? DB'de var olan ama jsonl'de olmayan satırlar var mı (ai_solve seed kalıntısı)?

- [ ] **Step 1: Script yaz**

```python
# backend/_pilots/audit_task09_jsonl_db_xval.py
import sys, os, json, uuid
from pathlib import Path
from sqlalchemy import create_engine, text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except ImportError: pass
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2").replace("postgresql+asyncpg://", "postgresql://").replace("/kiro2_db", "/kiro2")
engine = create_engine(db_url)

KIRO2_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# JSONL'den deterministic ID'ler
jsonl_ids = set()
with Path("d-dataset/eslesmis_sorucevap.jsonl").open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: d = json.loads(line)
        except: continue
        book = d.get("book_name", "")
        page = d.get("page_number")
        qno = d.get("question_number")
        if book and page is not None and qno is not None:
            key = f"{book}|{page}|{qno}"
            jsonl_ids.add(str(uuid.uuid5(KIRO2_NAMESPACE, key)))

print(f"JSONL deterministic ID sayısı: {len(jsonl_ids):,}")

# DB'deki aktif tüm ID'ler
with engine.connect() as c:
    db_ids = {r[0] for r in c.execute(text("SELECT id::text FROM question_bank WHERE is_active=TRUE"))}
print(f"DB aktif ID sayısı: {len(db_ids):,}")

only_jsonl = jsonl_ids - db_ids
only_db = db_ids - jsonl_ids
both = jsonl_ids & db_ids

print(f"\nKesişim: {len(both):,}")
print(f"JSONL'de var DB'de yok: {len(only_jsonl):,} (production gap)")
print(f"DB'de var JSONL'de yok: {len(only_db):,} (ai_solve / legacy seed)")

# DB-only sample (legacy detection)
if only_db:
    sample = list(only_db)[:5]
    with engine.connect() as c:
        r = c.execute(text("""
            SELECT id::text, source_book, source_page,
                   pipeline_metadata::jsonb ->> 'source' AS src
            FROM question_bank WHERE id::text = ANY(:ids)
        """), {"ids": sample}).fetchall()
        print("\nDB-only sample:")
        for row in r:
            print(f"  {row}")
```

- [ ] **Step 2: Çalıştır**

Run: `cd C:/Users/husey/kiro2 && python backend/_pilots/audit_task09_jsonl_db_xval.py`

Expected:
- Kesişim ≈ 77,336 (JSONL toplam)
- only_jsonl ≤ 100 (DB'ye import edilememiş satırlar marjinal)
- only_db ≈ DB toplam - 77,336 (legacy ai_solve + reocr seed)

- [ ] **Step 3: only_jsonl > 100 ise:**

`scripts/import_d_dataset.py`'de import bug var. Sample 5 satırın neden import edilmediğini incele.

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 9: JSONL × DB Cross-Validation
- Kesişim: <N>
- only_jsonl (production gap): <M>
- only_db (legacy seed): <X>
- VERDICT: PASS / IMPORT BUG
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task09_jsonl_db_xval.py backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task09): jsonl × DB cross-validation"
```

---

## Task 10: answers_v8.db × DB correct_answer Cross-Validation

**Files:**
- Create: `backend/_pilots/audit_task10_answers_xval.py`

`answers_v8.db.answers_page_inline` 78,720 entry, ~%85 doğruluk. DB'deki `correct_answer` ile bu external source'u karşılaştır. Disagreement zaten Faz 1.9'da yapılmış (`book_key_match` flag). Bu task: `book_key_match=disagree` satırlar Faz 1.9 pilot bulgusunu hala yansıtıyor mu (%87.5 SQLite doğru, %12.5 qbank doğru)?

- [ ] **Step 1: Script yaz**

```python
# backend/_pilots/audit_task10_answers_xval.py
import sys, os, sqlite3
from sqlalchemy import create_engine, text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except ImportError: pass
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2").replace("postgresql+asyncpg://", "postgresql://").replace("/kiro2_db", "/kiro2")
engine = create_engine(db_url)

# answers_v8.db
sqlite_path = "d-dataset/output/answer_keys_v8/answers_v8.db"
sqlite_keys = {}
conn = sqlite3.connect(sqlite_path)
for book, page, qno, ans in conn.execute("SELECT book_name, page_number, question_number, answer FROM answers_page_inline"):
    sqlite_keys[(book, page, qno)] = ans
conn.close()
print(f"SQLite keys: {len(sqlite_keys):,}")

with engine.connect() as c:
    rows = list(c.execute(text("""
        SELECT source_book, source_page,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no')::int AS q_no,
               correct_answer
        FROM question_bank
        WHERE is_active=TRUE
          AND pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' ~ '^[0-9]+$'
          AND correct_answer IS NOT NULL
    """)))

agree = 0; disagree = 0; no_key = 0
for book, page, qno, ans in rows:
    key = (book, page, qno)
    if key not in sqlite_keys:
        no_key += 1; continue
    if sqlite_keys[key] == ans:
        agree += 1
    else:
        disagree += 1

print(f"\nDB aktif numeric-qno: {len(rows):,}")
print(f"  agree:    {agree:,}")
print(f"  disagree: {disagree:,}")
print(f"  no_key:   {no_key:,}")
matched = agree + disagree
if matched > 0:
    print(f"  agree ratio: {100*agree/matched:.1f}%")
```

- [ ] **Step 2: Çalıştır**

Run: `cd C:/Users/husey/kiro2 && python backend/_pilots/audit_task10_answers_xval.py`

Expected:
- matched ≈ 16,000 (Faz 1.9'da 16,159 idi)
- agree / matched ≈ %46 (Faz 1.9'da %46 agree, %54 disagree)

- [ ] **Step 3: Eğer matched yaklaşık 16K değilse:**

Faz 1.9 ile sapma var. `pipeline_metadata::jsonb -> 'book_key_match'` field'ı yazıldığı kadar mevcut mu?

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 10: answers_v8 × DB Cross-Validation
- matched: <N> / DB aktif numeric-qno: <M>
- agree: <X>, disagree: <Y>
- agree ratio: <pct>%
- VERDICT: PASS (Faz 1.9 ile uyumlu) / DRIFT
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task10_answers_xval.py backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task10): answers_v8 × DB correct_answer xval"
```

---

## Task 11: Sanity Flags Pixel Verification (612 satır)

**Files:**
- Create: `backend/_pilots/audit_task11_sanity_verify.py`

Faz 1.4'te 607 duplicate_options + 5 answer_no_option flag yazıldı. Re-verify: bu satırlarda gerçekten dup option VAR mı veya correct_answer karşılığı boş mu?

- [ ] **Step 1: Script yaz**

```python
# backend/_pilots/audit_task11_sanity_verify.py
import sys, os
from sqlalchemy import create_engine, text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except ImportError: pass
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2").replace("postgresql+asyncpg://", "postgresql://").replace("/kiro2_db", "/kiro2")
engine = create_engine(db_url)

# 1. duplicate_options flag'li satırlarda gerçek dup VAR mı?
print("=== duplicate_options doğrulama ===")
with engine.connect() as c:
    rows = list(c.execute(text("""
        SELECT id::text, option_a, option_b, option_c, option_d, option_e,
               pipeline_metadata::jsonb -> 'sanity_flags' -> 'duplicate_options' AS dups
        FROM question_bank
        WHERE pipeline_metadata::jsonb -> 'sanity_flags' ? 'duplicate_options'
    """)))

real_dup = 0; flag_drift = 0
opts_map = {"A":0, "B":1, "C":2, "D":3, "E":4}
for qid, a, b, c_, d, e, dups in rows:
    opts = [a, b, c_, d, e]
    actually_dup = False
    if dups:
        for pair in dups:
            x_idx = opts_map.get(pair[0])
            y_idx = opts_map.get(pair[1])
            if x_idx is not None and y_idx is not None:
                vx = opts[x_idx] or ""
                vy = opts[y_idx] or ""
                if vx and vy and vx == vy:
                    actually_dup = True
                    break
    if actually_dup:
        real_dup += 1
    else:
        flag_drift += 1
print(f"  total: {len(rows)}, real_dup: {real_dup}, drift: {flag_drift}")

# 2. answer_no_option flag'li satırlarda gerçek miss VAR mı?
print("\n=== answer_no_option doğrulama ===")
with engine.connect() as c:
    rows = list(c.execute(text("""
        SELECT id::text, correct_answer,
               option_a, option_b, option_c, option_d, option_e
        FROM question_bank
        WHERE (pipeline_metadata::jsonb -> 'sanity_flags' ->> 'answer_no_option')::bool IS TRUE
    """)))
real_miss = 0; drift = 0
for qid, ans, a, b, c_, d, e in rows:
    opts_map_local = {"A": a, "B": b, "C": c_, "D": d, "E": e}
    correct_opt = opts_map_local.get(ans)
    if correct_opt is None or len(correct_opt.strip()) == 0:
        real_miss += 1
    else:
        drift += 1
print(f"  total: {len(rows)}, real_miss: {real_miss}, drift: {drift}")
```

- [ ] **Step 2: Çalıştır**

Run: `cd C:/Users/husey/kiro2 && python backend/_pilots/audit_task11_sanity_verify.py`

Expected: drift = 0 (her iki kategori için)

- [ ] **Step 3: Drift > 0 ise:**

Faz 1.4 sanity script'inde bug. Drift örneklerini incele.

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 11: Sanity Flags Verify
- duplicate_options: <real>/<total>, drift=<M>
- answer_no_option: <real>/<total>, drift=<M>
- VERDICT: PASS (drift=0) / FAIL
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task11_sanity_verify.py backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task11): sanity_flags pixel verify"
```

---

## Task 12: subject_area / exam_type Turkish Case Audit

**Files:**
- Create: `backend/_pilots/audit_task12_case_convention.sql`

`.claude/rules/case-convention.md` zorunlu: `question_bank.subject_area` UPPERCASE (MATEMATIK, TURKCE...), `exam_type` UPPERCASE (TYT, AYT). Türkçe locale trap: `I→ı` ile case mismatch.

- [ ] **Step 1: SQL yaz**

```sql
-- audit_task12_case_convention.sql
\echo '=== TASK 12: CASE CONVENTION ==='

-- 12.1 subject_area değerleri
SELECT subject_area, COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
GROUP BY 1 ORDER BY n DESC;

-- 12.2 exam_type değerleri
SELECT exam_type, COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
GROUP BY 1 ORDER BY n DESC;

-- 12.3 Convention sapma kontrol (lowercase veya mixed case)
SELECT subject_area, COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
  AND subject_area <> UPPER(subject_area)
GROUP BY 1;

SELECT exam_type, COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
  AND exam_type <> UPPER(exam_type)
GROUP BY 1;

-- 12.4 Turkish dotless trap: "matematık" (ı) veya "matematik"
SELECT subject_area, LENGTH(subject_area) AS len, COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
  AND (subject_area LIKE '%ı%' OR subject_area LIKE '%İ%')
GROUP BY 1, 2;
```

- [ ] **Step 2: Çalıştır**

Run: `"C:/Program Files/PostgreSQL/18/bin/psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -P pager=off -f backend/_pilots/audit_task12_case_convention.sql`

Expected:
- Tüm subject_area = UPPERCASE (MATEMATIK, FIZIK, KIMYA, BIYOLOJI, TURKCE, EDEBIYAT, TARIH, COGRAFYA, FELSEFE, DIN, SOSYAL)
- Tüm exam_type = TYT veya AYT
- Mixed case = 0
- Türkçe `ı`/`İ` = 0 (tüm ASCII olmalı)

- [ ] **Step 3: Sapma varsa:**

case-convention.md ihlali. Düzeltme: `UPDATE question_bank SET subject_area = UPPER(subject_area) WHERE subject_area <> UPPER(subject_area)`.

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 12: Case Convention
- subject_area enum: <list>
- exam_type enum: <list>
- Mixed case: <N>
- Türkçe trap: <M>
- VERDICT: PASS / FAIL
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task12_case_convention.sql backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task12): case convention check"
```

---

## Task 13: correct_answer A-E Range + Option Consistency

**Files:**
- Create: `backend/_pilots/audit_task13_correct_answer.sql`

`correct_answer` sadece A-E olmalı. Bunun haricinde "T", "F", "DOĞRU", "1" gibi değerler varsa OCR hatası.

- [ ] **Step 1: SQL yaz**

```sql
-- audit_task13_correct_answer.sql
\echo '=== TASK 13: correct_answer RANGE ==='

-- 13.1 correct_answer dağılımı
SELECT correct_answer, COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
GROUP BY 1 ORDER BY n DESC;

-- 13.2 Geçersiz değerler (A-E dışı, NULL hariç)
SELECT correct_answer, COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
  AND correct_answer NOT IN ('A','B','C','D','E')
  AND correct_answer IS NOT NULL
GROUP BY 1;

-- 13.3 NULL sayısı
SELECT COUNT(*) AS null_count
FROM question_bank WHERE is_active=TRUE
  AND correct_answer IS NULL;
```

- [ ] **Step 2: Çalıştır**

Run: `"C:/Program Files/PostgreSQL/18/bin/psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -P pager=off -f backend/_pilots/audit_task13_correct_answer.sql`

Expected:
- correct_answer ∈ {A, B, C, D, E}
- Geçersiz = 0
- NULL = 0 (Session 158 sanity check'te 0 idi)

- [ ] **Step 3: Eğer geçersiz/NULL > 0 ise:**

Üretim verisi integrity ihlali. INSERT script'lerinde validation eksik veya import bug.

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 13: correct_answer Range
- A: <N>, B: <N>, C: <N>, D: <N>, E: <N>
- Geçersiz: <N>, NULL: <N>
- VERDICT: PASS / FAIL
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task13_correct_answer.sql backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task13): correct_answer A-E range check"
```

---

## Task 14: Duplicate Question Detection (content-based)

**Files:**
- Create: `backend/_pilots/audit_task14_dup_detect.sql`

Aynı sorunun iki kere DB'de olması = pipeline race condition veya import bug. `soru_hash` field (varsa) veya `question_text` MD5 üzerinden duplicate tespit.

- [ ] **Step 1: SQL yaz**

```sql
-- audit_task14_dup_detect.sql
\echo '=== TASK 14: DUPLICATE DETECTION ==='

-- 14.1 Aynı soru_hash kaç defa
SELECT soru_hash, COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE AND soru_hash IS NOT NULL
GROUP BY 1 HAVING COUNT(*) > 1
ORDER BY n DESC LIMIT 10;

-- 14.2 Aynı question_text (case-insensitive normalized)
SELECT md5(LOWER(TRIM(question_text))) AS hash, COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
  AND LENGTH(question_text) > 50
GROUP BY 1 HAVING COUNT(*) > 1
ORDER BY n DESC LIMIT 10;

-- 14.3 (source_book, source_page, q_no) triple unique mi?
SELECT source_book, source_page,
       pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' AS qno,
       COUNT(*) AS n
FROM question_bank WHERE is_active=TRUE
  AND pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' ~ '^[0-9]+$'
GROUP BY 1, 2, 3 HAVING COUNT(*) > 1
ORDER BY n DESC LIMIT 10;
```

- [ ] **Step 2: Çalıştır**

Run: `"C:/Program Files/PostgreSQL/18/bin/psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -P pager=off -f backend/_pilots/audit_task14_dup_detect.sql`

Expected:
- 14.1: soru_hash uniqueness — duplicate sayısı ≤ 100 (acceptable noise)
- 14.2: text hash duplicate ≤ 200 (legitimate cases: aynı soru farklı versiyon)
- 14.3: triple (book, page, qno) duplicate = 0 (deterministic UUID ile garantili)

- [ ] **Step 3: Eğer triple duplicate > 0 ise:**

UUID generation bozulmuş. Sample örneği incele.

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 14: Duplicate Detection
- soru_hash dup: <N>
- text hash dup: <M>
- (book,page,qno) triple dup: <X>
- VERDICT: PASS (triple=0) / FAIL
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task14_dup_detect.sql backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task14): duplicate question detection"
```

---

## Task 15: Book Name Normalization Audit (DB ↔ disk)

**Files:**
- Create: `backend/_pilots/audit_task15_book_mapping.py`

DB `source_book` vs disk `<book_dir_name>` mapping: space ↔ underscore + lowercase + NFC. Eğer DB'de bir kitap adı disk'te bulunmuyorsa = tier'lar bu satırları kaçırır (Session 158 audit'inde A_no_book_dir=10 satır vardı).

- [ ] **Step 1: Script yaz**

```python
# backend/_pilots/audit_task15_book_mapping.py
import sys, os
from pathlib import Path
from sqlalchemy import create_engine, text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
except ImportError: pass
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2").replace("postgresql+asyncpg://", "postgresql://").replace("/kiro2_db", "/kiro2")
engine = create_engine(db_url)

CROPS_ROOT = Path("d-dataset/output/crops")
disk_dirs = {p.name for p in CROPS_ROOT.iterdir() if p.is_dir()}
disk_dirs_lower = {d.lower() for d in disk_dirs}

# DB'deki tüm unique source_book
with engine.connect() as c:
    db_books = [r[0] for r in c.execute(text("""
        SELECT DISTINCT source_book FROM question_bank
        WHERE is_active=TRUE AND source_book IS NOT NULL
    """))]
print(f"DB unique kitap: {len(db_books):,}")
print(f"Disk dir: {len(disk_dirs):,}")

unmatched = []
for book in db_books:
    cand = book.replace(" ", "_")
    if cand not in disk_dirs and cand.lower() not in disk_dirs_lower:
        unmatched.append(book)
print(f"\nUnmatched DB books: {len(unmatched)}")
for b in unmatched[:10]:
    safe = b.encode("ascii","replace").decode("ascii")
    print(f"  {safe}")
```

- [ ] **Step 2: Çalıştır**

Run: `cd C:/Users/husey/kiro2 && python backend/_pilots/audit_task15_book_mapping.py`

Expected: unmatched ≤ 5 kitap (Session 158'de 1 kitap "Esen 2025 Aps Ayt Matemat,k" idi)

- [ ] **Step 3: Eğer unmatched > 5 ise:**

Bu kitapların satırları Tier C/D/E/F/G/H tarafından kaçırılıyor (disk dir bulunmuyor). Tier H için book name encoding/normalize fonksiyonu revize edilebilir.

- [ ] **Step 4: RESULT.md'e ekle**

```bash
cat >> backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md <<EOF
## Task 15: Book Name Normalization
- DB kitap: <N>, disk dir: <M>
- Unmatched: <X>
- VERDICT: PASS (≤5) / FAIL
EOF
```

- [ ] **Step 5: Commit**

```bash
git add backend/_pilots/audit_task15_book_mapping.py backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task15): book name DB ↔ disk normalization"
```

---

## Task 16: Final Aggregate Report

**Files:**
- Modify: `backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md` (özet bölümü ekle)

15 task'ın sonuçlarını birleştir, genel verdict ver.

- [ ] **Step 1: RESULT.md'in başına özet bölümü ekle**

```bash
# Önce mevcut içeriği oku
head -5 backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
```

- [ ] **Step 2: Özet section'ı manuel yaz (template doldur)**

```markdown
# KIRO2 DB Comprehensive Audit RESULT

**Tarih:** 15 May 2026
**Scope:** 187,834 toplam satır, 167,559 aktif, 8 pipeline tier, 3 external data source

## Genel Verdict

| Task | Konu | Verdict | Detay |
|---|---|---|---|
| 1 | DB Snapshot | <PASS/FAIL> | ... |
| 2 | Tier H | <PASS/FAIL> | ... |
| 3 | Tier G drift | <PASS/FAIL> | ... |
| 4 | Tier F verify | <PASS/FAIL> | ... |
| 5 | Tier D+E verify | <PASS/FAIL> | ... |
| 6 | Cross-tier overlap | <PASS/FAIL> | ... |
| 7 | Broken links | <PASS/FAIL> | ... |
| 8 | Schema validation | <PASS/FAIL> | ... |
| 9 | JSONL × DB xval | <PASS/FAIL> | ... |
| 10 | answers_v8 × DB | <PASS/FAIL> | ... |
| 11 | Sanity flags | <PASS/FAIL> | ... |
| 12 | Case convention | <PASS/FAIL> | ... |
| 13 | correct_answer | <PASS/FAIL> | ... |
| 14 | Duplicate detect | <PASS/FAIL> | ... |
| 15 | Book mapping | <PASS/FAIL> | ... |

## Critical Findings
- ...

## Action Items
- ...
```

- [ ] **Step 3: Tüm FAIL'lerden action item çıkar**

Manuel: her FAIL için 1 GitHub issue veya Plan v1 task ekle.

- [ ] **Step 4: Final commit**

```bash
git add backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md
git commit -m "audit(task16): comprehensive DB audit aggregate report"
```

- [ ] **Step 5: Plan v1'e audit completion note ekle**

```bash
# docs/quality_pool_plan_v1.md'e ekle:
# "## Comprehensive DB Audit (15 May 2026)
#  RESULT: `backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md`
#  Verdict: <X/15 PASS>, <Y/15 FAIL>"
```

---

## Self-Review

**1. Spec coverage:**
- Tier C/D/E/F/G/H verification: Task 2, 3, 4, 5 ✓
- Cross-tier integrity: Task 6 ✓
- Broken link: Task 7 ✓
- Schema: Task 8 ✓
- External sources (jsonl, answers_v8): Task 9, 10 ✓
- Sanity flags (Faz 1.4): Task 11 ✓
- Case convention: Task 12 ✓
- correct_answer range: Task 13 ✓
- Duplicate: Task 14 ✓
- Book mapping: Task 15 ✓
- Aggregate report: Task 16 ✓

**Gap:** OCR text validator flag (64 satır, Faz 1.3) için dedicated task yok. Bu marjinal (defansif flag-only) — RESULT'a not olarak eklenir.

**2. Placeholder scan:** Yok. Her step kesin SQL/Python kodu içeriyor.

**3. Type consistency:**
- `pipeline_metadata::jsonb` tüm task'larda
- `tier_<x>_match` flag pattern uniform
- `similarity` numeric, `crop_file` text, `audit_date` ISO string

**Önemli not:** Task 6 (cross-tier overlap) hem invariant test, hem de Session 158'in `image_url IS NULL` filter doğruluğunun delili. Eğer multi_tier > 0 ise: önceki tier UPDATE'leri image_url'i set etmiş ama sonraki tier'a image_url IS NULL filter rağmen geçmiş — race condition.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-15-db-quality-audit-comprehensive.md`. Two execution options:

**1. Subagent-Driven (recommended)** — Her task fresh subagent ile çalışır, between-task review. 16 task / ~80 dakika.

**2. Inline Execution** — Bu session'da batch execute, checkpoint review per 4 task.

**Which approach?**
