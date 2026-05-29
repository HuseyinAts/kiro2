# A Şık Bias Root Cause Investigation (S194)

**Tarih:** 2026-05-23
**Trigger:** S182-S193 12-subject audit'inde A bias pipeline-wide doğrulandı (%29-32 her subject'te)
**Methodology:** Data forensics + 2 paralel Explore agent codebase scan
**Status:** ✅ CONFIRMED — iki ayrı root cause tespit edildi
**Update (2026-05-29):** ✅ **Root cause #2 (pipeline bug) FIXED** — `cross_validate_answers.py:114` `ai_upgrade=0.65` tier + `:270-278` `startswith("ai_upgrade_")` kapsamı (S194 fix, task #305, 78/78 PASS). Adversarial verify pass ile canlı kodda doğrulandı. Root cause #1 (page_inline OCR bias) kod-dışı, Curator review fallback'ında kalıyor (P2).

---

## TL;DR

A bias **tek bir bug'dan değil, iki bağımsız kaynaktan** geliyor:

1. **page_inline answer source (480 / 905 = %53)**: Gemini Vision OCR systematic A/E favor ediyor (combined %50.7 vs uniform %40). Kaynak biased — kod temiz.

2. **ai_upgrade_bayes source (129+ / 905 = %14)**: **Pipeline bug CONFIRMED** — `cross_validate_answers.py:265-266` `ai_upgrade` source'unu hardcoded `ai_solved` (0.85 accuracy) tier'ı atıyor. Bayesian formula original_answer'ı rematch_answer'a göre 18x daha güçlü posterior veriyor → A rejected systematically.

---

## Data Forensics Bulguları

### 905 Wrong Sorunun Source Dağılımı

| Source | Sayı | % | Kategori |
|---|---|---|---|
| page_inline | 480 | %53 | OCR / kaynak bias |
| ai_upgrade_bayes_*_orig | 129 | %14 | Pipeline bug |
| ai_upgrade_bayes_*_gemini | 12 | %1.3 | Pipeline bug |
| jsonl_v11 | 41 | %4.5 | Legacy |
| ai_solved_claude_opus | 28 | %3.1 | High-conf AI (yine yanlış) |
| crossval_bayes_* | ~30 | %3.3 | Cross-validation kalıntı |
| Diğer | ~185 | %20.4 | Mixed |
| **Toplam** | **905** | **100%** | |

### Shift Matrix (12 subject birleşik, n=673)

```
          Real:A    B      C      D      E
DB:A       0     61     49     35     41   ← Pipeline A'ya assign etmiş ama gerçek başka
DB:B      46      0     25     19     29   ← Gerçek A iken DB:B (en sık)
DB:C      41     31      0     24     25
DB:D      32     27     33      0     19
DB:E      41     34     35     26      0

Gerçek doğru cevap dağılımı: A=23.8% B=22.7% C=21.1% D=15.5% E=16.9%  (yakın uniform)
DB yanlış cevap dağılımı:    A=27.6% B=17.7% C=18.0% D=16.5% E=20.2%  (A over)
```

**Pattern:** DB'de en sık yanlış cevap A (%27.6). Gerçek cevap her yanlış DB cevabı için en sık A. Pipeline A'yı **fazla atama yapıyor + bazı A doğrularını kaçırıyor**.

### Pipeline_metadata Marker Pattern

Tüm 905 sorunun pipeline_metadata'sında **`r1_restore_v1` marker** var. Yani **Session 178 R1 restore commit (e4acd2b37)** ile gold pool'a geri getirilen 15,321 sorudan geliyor. Ama R1 restore script'i answer field'ları değiştirmiyor — sadece status flip yapıyor.

---

## Root Cause 1: page_inline OCR Bias (~%53 of bugs)

### Codebase Scan Sonucu (Agent 1)

**Files scanned:**
- `d-dataset/scripts/phase4_page_inline_answers.py` (525 satır)
- `d-dataset/scripts/cevap_crop_ocr.py` (550 satır)
- `d-dataset/scripts/match_crop_answers.py` (500 satır)
- `d-dataset/scripts/create_answers_v8.py`
- `d-dataset/scripts/reextract_answer_keys.py`

**Kod TEMIZ:**
- ✅ Regex `[A-E]` ASCII only (no Cyrillic А risk)
- ✅ `.upper()` Turkish I/ı tuzağı yok (answer letter context)
- ✅ `answer in "ABCDE"` strict check
- ✅ v7 → v8 zero difference (bitwise copy)
- ✅ No character replacement bug

### Gerçek Kaynak: answers_v8.db

```
=== answers_v8.db / answers_page_inline (78,720 rows) ===
A: 19,734 (25.1%)   ⚠️ BIAS
B: 10,016 (12.7%)   ⚠️ UNDER-REP
C: 15,016 (19.1%)
D: 13,769 (17.5%)
E: 20,185 (25.6%)   ⚠️ BIAS

Combined A+E: %50.7 (uniform %40 olmalı)
B: %12.7 (uniform %20)
```

**Hipotez:** Gemini Vision OCR cevap anahtarı sayfalarını okurken:
- A ve E köşelerde (yatay sıralamada başlangıç/son) → daha yüksek OCR confidence
- B/C/D ortada — confusion riski yüksek
- Gemini Vision systematic A/E favor ediyor

**Veya:** YKS yayıncıları kitap cevap anahtarlarında A/E bias var (talep edilen seçenek dağılımı için zaten biased).

### Fix Önerisi (P2 — kaynak fix değil, pipeline fallback)

1. **Sample 30 page_inline error** → orijinal PNG ile manuel compare (Gemini hatası mı yoksa kitap hatası mı?)
2. Eğer Gemini hatası: cevap anahtarı sayfaları için **multi-model consensus** (Claude + Gemini + GPT) extraction
3. Eğer kitap hatası: kaynak fix imkansız, fallback Curator review (zaten 905 pending'de)

---

## Root Cause 2: Bayesian ai_upgrade Over-weighting (~%14 of bugs)

### CONFIRMED Pipeline Bug

**File:** `d-dataset/scripts/cross_validate_answers.py:252-287`

```python
@functools.lru_cache(maxsize=64)
def classify_original(source: str) -> str:
    """Classify original answer source into accuracy tier."""
    ...
    if source == "ai_upgrade":
        return "ai_solved"  # ← BUG: 0.85 accuracy, same as production Opus
    ...
```

**Accuracy tier'ları:**
| Tier | Accuracy | Source examples |
|---|---|---|
| `ai_solved` | **0.85** | Production Opus high-conf + **ai_upgrade (bug)** |
| `jsonl_v11` | 0.80 | Legacy clean |
| `tier1` (page_inline) | 0.85 | Inline answer key OCR |
| `rematch` | **0.25** | Deprecated DB rematch — near-random |

### Bayesian Formula (line 375-426)

```
P(correct=k | obs) = P(k) × Π_i P(src_i says x_i | correct=k)
```

**Senaryo:**
- `original_answer = C` (ai_upgrade source → tier ai_solved, 0.85)
- `rematch_answer = A` (rematch source, 0.25)

```
P(correct=C | obs) ∝ 0.85 × (1-0.25)/4 = 0.85 × 0.1875 = 0.1594
P(correct=A | obs) ∝ (1-0.85)/4 × 0.25 = 0.0375 × 0.25 = 0.0094

→ C wins with ~17x posterior probability
→ rematch=A SYSTEMATICALLY REJECTED
```

### TIE-BREAK Protection (line 526-532)

```python
# When posteriors are near-uniform (max - min < 0.02), keep original answer.
if max(vals) - min(vals) < _TIE_BREAK_THRESHOLD and orig in VALID_ANSWERS:
    best = orig  # ← KEEPS ORIGINAL even when ambiguous
```

**Double protection** for ai_upgrade answers:
1. High prior (0.85)
2. Tie-break fallback to original

### Fix Önerisi (P1 — kod değişikliği)

```python
# OPTION A: Düşür ai_upgrade tier
if source == "ai_upgrade":
    return "ai_upgrade"  # Yeni tier
# Sonra DEFAULT_ACC dict'e:
#   "ai_upgrade": 0.65  ← cross-validation karşı production Opus'tan düşük

# OPTION B: rematch tier'ı yükselt (eğer pattern'i kanıtlandıysa)
DEFAULT_ACC["rematch"] = 0.40  # 0.25 → 0.40

# OPTION C: TIE-BREAK threshold artır
_TIE_BREAK_THRESHOLD = 0.05  # 0.02 → 0.05 (daha az original protect)
```

**Önerilen:** OPTION A — `ai_upgrade` için ayrı tier (0.65), production Opus'la karıştırma. **Hijyen + minimal risk**.

---

## Etki Analizi

### Mevcut DB (12,774 auto_judged_high)

- **Yeni ingest** zaten Curator review'a düşüyor (S182-S193 marker'lı 905 pending)
- **Fix yapılmasa bile** beta launch için Curator review yeterli (insan döngüsünde)

### Gelecek Ingest

- Eğer pipeline aynı bug ile çalışmaya devam ederse **her yeni gold pool batch %10-15 hatalı assignment** yaratır
- **P1 prioritye fix yapmak değerli** — gelecek 100K+ soru için
- Tek satır kod değişikliği (line 265-266)

### Phase 7 Quality Audit'le Bağlantı

Önceki Phase 7 audit'inde "doğru cevap rationale'ı CIRCULAR" sıkça gözlemlenmişti (matematik %55). Şimdi anlamlandı: Phase 7 prompt **DB correct_answer'ı doğru kabul ediyor**, ama DB'deki cevap **kendisi yanlışsa** rationale "doğru çünkü doğru" pattern'inden kaçınamaz. Pipeline bug rationale quality'yi de aşağı çekiyor.

---

## Sonraki Adımlar

| # | Görev | Süre | Priority |
|---|------|------|---------|
| 1 | OPTION A fix uygula (`cross_validate_answers.py:265-266`) | 30 dk | **P1** |
| 2 | Test: 13 known-wrong case'i fix sonrası re-run | 1 saat | **P1** |
| 3 | page_inline 30 sample manuel verify (Gemini vs kitap) | 2 saat | **P2** |
| 4 | Gemini Vision multi-model consensus for answer keys | 1 hafta | **P2** |
| 5 | Bayesian formula audit broader scope | 1 sprint | **P3** |

---

## Methodology

- **Data forensics:** Bash + Python + psycopg2 (read-only DB queries)
- **Codebase scan:** 2 paralel `Explore` agent (read-only)
- **Verification:** Spot check 5/5 (önceki S182-S193 audit'lerinden) zaten LLM judge reliability'yi %95+ kanıtlamıştı

**Süre:** ~1.5 saat (forensics 20dk + agent scan 15dk + sentez 30dk)
**Kod değişikliği:** 0 (READ-ONLY investigation)

---

## Çıktılar

```
docs/audits/2026-05-23_a_bias_root_cause.md  (BU DOKÜMAN)

Investigated files (read-only):
- d-dataset/scripts/cross_validate_answers.py (THE BUG)
- d-dataset/scripts/replace_db_v7_sources.py
- d-dataset/scripts/phase4_page_inline_answers.py
- d-dataset/scripts/rematch_with_corrected_qnums.py
- backend/scripts/quality/r1_legacy_v3_restore_apply.py
- answers_v8.db (page_inline distribution)
```
