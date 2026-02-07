# Plan: Taxonomy Calibration Script

## Overview
Create a calibration script that runs **36,967 real OCR'd YKS questions** from `d-dataset/eslesmis_sorucevap.jsonl` through `TaxonomyClassifier` (v2). Produces distribution stats, anomaly flags, dead-pattern detection, and per-book-subject analysis.

## Data Source
- **Primary:** `C:\Users\husey\kiro2\d-dataset\eslesmis_sorucevap.jsonl` (22 MB, 36,967 records)
- **Format:** JSONL with fields: `book_name`, `text`, `options` (dict A-E), `quality_score`, `confidence_level`
- **Subject detection:** Extract from `book_name` (e.g. "Matematik", "Türkçe", "Fizik", "Kimya", "Biyoloji", "Tarih", "Coğrafya", "Edebiyat", "İngilizce")
- **Quality filter:** Only `is_valid == true` and `quality_score >= 50`
- **Exclude:** English-language questions (İngilizce books)
- **Note:** Some OCR texts are garbled/truncated — classifier will still produce results, these show up as low-confidence

## New File
### `scripts/taxonomy_calibration.py`

**Steps:**
1. Read JSONL line by line (memory efficient, no full load)
2. Parse each record, extract subject from `book_name`
3. Skip İngilizce books and `is_valid == false`
4. Build input: `text + " " + " ".join(options.values())`
5. Run `classifier.classify(input_text)` → SOLO + Marzano
6. Independently scan all SOLO_BUNDLES + MARZANO_BUNDLES patterns to count hits (dead pattern detection)
7. Collect stats by subject, by book

**Reports (7 sections):**

### 1. Summary
Total questions, filtered count, subject breakdown

### 2. SOLO Distribution by Subject
```
Subject      | N     | L2   | L3   | L4   | L5   | Avg Conf
Matematik    | 15000 | 45%  | 30%  | 20%  | 5%   | 0.78
```

### 3. Marzano Distribution by Subject
```
Subject      | N     | Ret  | Comp | Ana  | Util | Meta | Self | Avg Conf
```

### 4. Anomalies
- Dominant level >80% for a subject
- Low confidence (avg < 0.6) for a subject
- L5/metacognitive/self-system unexpectedly high

### 5. Dead Patterns
Patterns from SOLO_BUNDLES/MARZANO_BUNDLES that matched 0 of 36K questions

### 6. Top & Bottom 20 Questions by Confidence
Show best/worst classified examples

### 7. Per-Book Summary (top 10 books by question count)
```
Book Name                              | N    | Dominant SOLO | Dominant Marzano
```

**Also saves JSON output** to `d-dataset/output/taxonomy_calibration_results.json` for later analysis.

## Modified Files
None. Standalone script.

## Verification
```bash
cd C:\Users\husey\kiro2 && python scripts/taxonomy_calibration.py
```
Should process ~30K+ questions, print 7 report sections, save JSON output.
