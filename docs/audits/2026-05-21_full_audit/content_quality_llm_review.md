# KIRO2 LLM Rationale Content Quality — DEEP AUDIT

**Date:** 2026-05-21
**Auditor:** Sub-agent (manual sample review against live PostgreSQL `kiro2` @ port 5434)
**Scope:** Phase 7 LLM rationale content quality — Gemini Flash latest + Qwen3:8b + gpt-4o-mini
**Method:** Real DB read-only queries; 50-row random sample (md5 ordering), per-option rationale review (250 rationale rows total), aggregate statistics across all 408,720 rows.

---

## TL;DR — Production Risk Verdict

| Dimension | Verdict | Beta-Safe? |
|-----------|---------|------------|
| Coverage (Q with rationales) | 81,745 / 81,776 (%99.96) | YES |
| Per-option completeness (5/5) | 408,720 row, only 2 incomplete | YES |
| Exactly one correct per Q | 99.998% (1 zero-correct outlier) | YES |
| Length / non-trivial rationale | Gemini 100%, Qwen 6% under 40 char | PARTIAL — Qwen low-effort |
| Factual correctness | **CRITICAL DEFECT** — Hemingway/Stendhal hallucination retained | NO without filter |
| Misconception tags | `misconception_tag` column **ALL NULL** (0 / 408,720) | NO — column populated but empty |
| `question_bank.misconception_tags` JSON | **ALL NULL** in auto_judged_high | NO — schema present but unused |
| `solution_steps` JSON | **ALL NULL** in auto_judged_high | NO — never populated |
| `similar_question_ids` JSON | **ALL NULL** in auto_judged_high | NO — never populated |
| `reviewed_at` timestamp | **ALL NULL** in auto_judged_high | NO — audit trail gap |
| Math sympy verification (`verified_by_sympy`) | 0 / 31,034 SymPy-verified | NO — flag set but no execution proof |
| Turkish naturalness | Gemini PASS, Qwen MIXED, gpt-4o-mini PASS | YES |
| OCR artifact propagation | Found in question text, NOT amplified in rationales | LOW RISK |

**Overall:** **Conditional beta-safe**. Rationale infrastructure is solid (5/5 completeness, exactly-one-correct, Turkish quality OK for Gemini). However:
1. **Multiple Phase 7 schema columns (`misconception_tags`, `solution_steps`, `similar_question_ids`, `reviewed_at`) are 100% NULL** in `auto_judged_high` despite memory claiming "Faz 6 Gold = 81,776".
2. **Confirmed Gemini hallucination of correct answer** (Hemingway as Stendhal's substitute, Pürranameler as Fütüvvetnameler's substitute) — model marks `is_correct=t` for the wrong option and writes a fabricated justification.
3. **Qwen rationales are low-effort generic filler** ("Bu seçenek yanlış bir şekilde belirtir") with no instructional value.

---

## 1. Phase 7 Coverage Reality vs Memory Claim

Memory claims: "Phase 7 Gemini Batch API: 81,657/81,776 (%99.85) Gold gold rows"

Live DB state (2026-05-21 query, `quality_review_status = 'auto_judged_high' AND is_active = TRUE`):

| Status | Q count | With rationales |
|--------|---------|-----------------|
| unverified | 61,482 | **77** (%0.1) |
| rejected | 54,126 | 48,942 (%90) |
| pending | 36,433 | 32,726 (%90) |
| **auto_judged_high** | **15,321** | **0 (%0)** |
| bronze_clean | 197 | 0 (%0) |

**Critical anomaly:** The 15,321 currently active auto_judged_high (= "Gold") questions have **ZERO rationale rows** in `question_option_rationales`. The 408,720 rationales live attached to `rejected` and `pending` questions instead.

Cross-check by generator distinct-question counts:
- gemini-flash-latest: 67,708 distinct questions
- qwen3:8b: 14,027 distinct questions
- gpt-4o-mini: 10 distinct questions
- Total distinct Q with rationales: 81,745 ≈ memory's 81,776 (the count exists, just NOT in `auto_judged_high`).

**Interpretation:** The Faz 6 status reclassification (memory: "auto_judged_high=81,776") has not been reconciled with the rationale storage; either (a) the rationale Q set was generated before status flip and is now disconnected, or (b) the status counts in memory are stale.

---

## 2. 50-Sample Manual Review

50 random questions selected via `ORDER BY md5(id::text) LIMIT 50` from `question_bank` where rationales exist. Below: 7 detailed reviews (covering all major subject areas), then aggregate per-subject scoring.

### Sample 1 — MATEMATIK, ID `dca8e3ae` (Etiket fiyatı problemi)

**Question:** Etiket fiyatı 540 TL olan ürünlere etiketleme yapılırken bu ürünlerin bazılarına etiket fiyatı yanlışlıkla 450 TL olarak basılmıştır. Bu etiketleme sonucu satılan ürünlerden normalde göre %8 daha az kazanç elde edilmiştir. Buna göre, kaç adet ürün doğru etiketleme ile satılmış olabilir?
**Correct:** C = 26. Sympy `expected_answer_sympy = "13*k"` (parametric, plausible).
**Rationales (gemini-flash-latest):**
- A (24, f): "Doğru etiketlenen ürün sayısı 13'ün katı olmalıdır, ancak 24 sayısı 13'e tam bölünmez."
- B (25, f): "Doğru etiketlenen ürün sayısı 13'ün katı olmak zorunda olduğundan 25 seçeneği yanlıştır."
- **C (26, t): "Elde edilen 13y = 12x denklemine göre doğru etiketlenen ürün sayısı 13'ün katı olan 26 olabilir."**
- D (27, f): "Doğru etiketlenen ürün sayısı 13'ün tam katı olmalıdır, bu yüzden 27 olamaz."
- E (28, f): "Doğru etiketlenen ürün sayısı 13'ün katı olmalıdır, ancak 28 sayısı bu şartı sağlamaz."

**Verdict:** PASS. The reasoning correctly identifies the "13'ün katı" constraint, but the four distractor rationales are repetitive (all say same thing). Instructionally adequate.

### Sample 2 — EDEBIYAT, ID `75068323` ("Romantizm döneminde gerçekçilik")

**Question:** "----, romantizm akımının etkili olduğu bir dönemde yaşamasına rağmen gerçekçiliğin öncüleri ve kurucuları arasında yer almıştır." (Boşluk + "Kırmızı ve Siyah" referansı OCR'da yarım kalmış)
**DB correct_answer:** E = Hemingway
**Rationales (gemini-flash-latest):**
- A (Stendhal, f): "Stendhal, realizmin öncüsü ve Kırmızı ve Siyah'ın yazarı olmasına rağmen sorunun kurgusu gereği doğru cevap olarak kabul edilmemiştir."
- B (Balzac, f): "Balzac, realizm akımının kurucularından biri olsa da paragrafta tanıtılan yazar ve eserle doğrudan uyuşmamaktadır."
- C (Tolstoy, f): "Tolstoy, Rus realizminin en önemli temsilcilerinden biri olup Kırmızı ve Siyah adlı eserin yazarı değildir."
- D (Turgenev, f): "Turgenev, Rus edebiyatında realizmin öncülerinden biri olup paragrafta verilen eser ve özelliklerle eşleşmemektedir."
- **E (Hemingway, t): "Hemingway, modern edebiyatın realist temsilcilerinden biri olup soruda verilen anahtar bilgiler doğrultusunda doğru cevap olarak belirlenmiştir."**

**Verdict: CRITICAL FAIL.** This is a textbook LLM hallucination. The factually correct answer is **A (Stendhal)** — he wrote "Kırmızı ve Siyah" (Le Rouge et le Noir) in 1830. The model:
1. Trusts the (wrong) `correct_answer = E` field blindly.
2. Justifies `is_correct=t` for Hemingway with an empty, circular sentence ("soruda verilen anahtar bilgiler doğrultusunda doğru cevap olarak belirlenmiştir") — content-free.
3. Worse: rationale A explicitly admits Stendhal "Kırmızı ve Siyah'ın yazarı olmasına rağmen sorunun kurgusu gereği doğru cevap olarak kabul edilmemiştir" — the model **sees the inconsistency and rationalizes around it instead of flagging**.

This matches the exact failure mode memory documented ("gpt-4o-mini factual hata yaptığı kanıtlandı (Hemingway→Stendhal 'Kırmızı ve Siyah' hatası)") — but here it's **gemini-flash-latest reproducing the same hallucination**. The root cause is upstream OCR mis-extracting the correct_answer field, and the LLM is incapable of cross-checking against world knowledge.

### Sample 5 — TURKCE, ID `5583485e` (Ahi teşkilatı yazılı belgeleri)

**Question:** Esnaf teşkilatlarının kurallarını anlatan, mistik nesir eserlere ne ad verilir?
**DB correct_answer:** A = pürranamenler  
**Real-world correct answer:** D = **fütüvvetnameler** (Ahi teşkilatının yazılı esasları = fütüvvetnameler; this is high-school edebiyat curriculum). "Pürranameler" is not a recognized Turkish literary term.

**Rationales (gemini-flash-latest):**
- **A (pürranameler, t): "Pürranameler, Selçuklu ve Osmanlı'da ahi teşkilatının kurallarını ve işleyişini anlatan mistik nesir eserlerdir."**
- D (fütüvvetnameler, f): "Fütüvvetnameler, ahilik teşkilatının esaslarını anlatan eserler olup bu soruda **çeldirici** olarak kullanılmıştır."

**Verdict: CRITICAL FAIL.** Exact same failure mode as Sample 2:
1. The model fabricates a definition for a non-existent term ("pürranameler") to justify the wrong correct_answer.
2. It **explicitly labels the correct answer (fütüvvetnameler) as "çeldirici" (distractor)**, then justifies why it's wrong using the actual definition that should have been the correct answer.
3. This is a knowable, citable error — high-school edebiyat textbooks teach fütüvvetname = ahi rules.

This and Sample 2 are the same systematic risk: **garbage correct_answer in → confidently-wrong rationale out**.

### Sample 33 — FIZIK, ID `14385b8c` (Momentum / itme)

**Question:** Top'a vurulan futbol, kale direğine 9 birim hızla çarpıyor, 3 birim hızla geri fırlıyor → itmenin büyüklüğü?
**Correct:** A = 1 m·s (DB).
**Rationales (gemini-flash-latest):**
- A (1, t): "İtme, momentum değişimine eşit olup son momentum ile ilk momentum vektörlerinin farkı alınarak büyüklüğü 1 m·s olarak bulunur."
- B (√2, f): "Vektörel çıkarma işlemi yerine yanlış açıyla bileşenlerine ayırma veya hatalı trigonometrik hesaplama yapılması bu yanlış seçeneğe yönlendirir."

**Verdict: WARN.** The CORRECT rationale claims "büyüklüğü 1 m·s" but physically `|p_son - p_ilk|` for a 9-unit incoming + 3-unit outgoing collision must be at least 6m (1D) or more (angled). The numerical answer A=1 is suspect — likely OCR pulled wrong value from "1 m·s" candidate set. **The LLM did not detect this physics impossibility**. Same failure pattern as Sample 2.

### Sample 8 — FIZIK, ID `7df38e74` (Compton olayı)

**Question:** Compton olayında gelen ve saçılan foton için (I) Hız büyüklüğü, (II) Enerji, (III) Dalga boyu — hangileri eşit OLABİLİR?
**DB correct:** D = II ve III
**Rationales (gemini-flash-latest):**
- A (Yalnız I, f): "Fotonların hız büyüklükleri ortama göre değişebileceğinden, gelen ve saçılan fotonun hızları her zaman eşit olmayabilir."
- D (II ve III, t): "Çarpışma sürecinde gelen ve saçılan fotonların enerjileri ile dalga boyları belirli koşullarda eşit kalabilir."

**Verdict: WARN.** Physics-wise sketchy. In a Compton scattering event by definition there IS energy transfer (Δλ ≠ 0 for any θ > 0), so II and III cannot be "eşit" unless we permit the limiting case θ = 0 (no scattering). The rationale dodges with "belirli koşullarda eşit kalabilir" — vague phrasing, doesn't explain WHICH conditions. Not pedagogically valuable.

Also note the **rationale A is scientifically wrong**: photon hız büyüklüğü is always c in vacuum, independent of "ortam". Mid-air vs vacuum is irrelevant to YKS-level Compton context. Model adds a fabricated nuance that contradicts curriculum.

### Sample 13 — BIYOLOJI, ID `4bc87f00` (ATP)

**Question:** ATP üretim/tüketim — I, II, III ifadelerinin hangileri doğru?
**Correct:** E = I, II ve III
**Rationales (gemini-flash-latest):** All five rationales follow the pattern "X öncülünün de doğru olduğunu göz ardı eder" for distractors and provide a coherent justification for E.

**Verdict: PASS.** Solid pedagogically — each distractor rationale identifies which premise was wrongly excluded. Good instructional value.

### Sample 35 — MATEMATIK, ID `14abe450` (Qwen rationale)

**Question:** f(x) grafiği verilmiş — yerel min, mutlak min, ekstremum yokluğu hakkında 3 ifade.
**Correct:** C = I ve II
**Rationales (qwen3:8b):**
- A (Yalnız I, f): "I doğrudur, II ve III yanlış."
- B (Yalnız II, f): "II doğrudur, I ve III yanlış."
- **C (I ve II, t): "I ve II doğrudur, III yanlış."**
- D (II ve III, f): "II ve III doğrudur, I yanlış."
- E (I, II, III, f): "I, II ve III doğrudur."

**Verdict: FAIL.** Qwen rationales are **mechanical permutation echo** of the choice text. Zero pedagogical content. No explanation of *why* each premise is true/false. A student reading these learns nothing — they only learn what the answer is, not how to derive it.

**This is representative of Qwen output across the sample.** See Sample 17 (qwen3:8b, "1000 dakika yeterli olmaz" / "1250 dakika yeterli olmaz") and Sample 45 (qwen3:8b, "Alan hesaplamalarında eksiklik olabilir" — for the marked CORRECT option, which is even worse: the *correct* rationale admits "eksiklik olabilir").

### Sample 45 — GEOMETRI, ID `ea71644a` (Paralelkenar alan)

**Question:** ABCD paralelkenar boyalı alan?
**Correct:** C = 105 cm²
**Rationales (qwen3:8b):**
- A (85, f): "Paralelkenarın alanını yanlış hesaplamış olabilir."
- B (95, f): "Doğru cevap, alan hesaplamaları doğru yapılmış." **(!! Says B is correct, but is_correct=f)**
- **C (105, t): "Alan hesaplamalarında eksiklik olabilir."** **(!! Says CORRECT option is "eksik")**
- D (125, f): "Alan hesaplamalarında hata yapmış olabilir."
- E (130, f): "Alan hesaplamalarında hatalı oran kullanmış olabilir."

**Verdict: CRITICAL FAIL (data integrity).**
- Rationale text for B claims B is correct ("Doğru cevap"), but `is_correct = f`. Direct contradiction between rationale prose and `is_correct` flag.
- Rationale for C (the marked-correct option) says "eksiklik olabilir" — admits incompleteness for the supposedly-right answer.
- Effectively negative pedagogical value; could mislead students.

---

## 3. Misconception Tag Taxonomy

Per-column population:

| Column | Total rows | Non-NULL | Non-empty |
|--------|-----------|----------|-----------|
| `question_option_rationales.misconception_tag` | 408,720 | **0** | **0** |
| `question_bank.misconception_tags` (JSON) | 187,834 | **0** in auto_judged_high (15,321) | n/a |

**Verdict:** The misconception tag taxonomy **does not exist in the live database**. The schema columns are present but never populated. The Phase 7 plan in CLAUDE.local.md and MEMORY.md document a misconception taxonomy (e.g. "limit hatası", "türev kuralı yanlış"), but no rows carry such data.

**Beta impact:** Any frontend feature that depends on misconception tags (adaptive distractor analysis, error pattern detection in `useStudentProfile`, BKT misconception parameter input) will receive NULL/empty payloads. Either:
- (a) Disable misconception UI features, or
- (b) Re-run Phase 7 with misconception extraction enabled, or
- (c) Derive misconception tags from the existing `rationale` text via post-processing.

---

## 4. Solution Steps + Similar Questions + Reviewed-At

In the 15,321 `auto_judged_high` rows:

| Column | Non-NULL count |
|--------|---------------|
| `solution_steps` (JSON) | **0** |
| `misconception_tags` (JSON) | **0** |
| `similar_question_ids` (JSON) | **0** |
| `reviewed_at` (timestamp) | **0** |

All four are 100% NULL. The Session 178 ORM additions exist in schema (`models/question.py`) but the Phase 7 batch pipeline does NOT write to them. The `question_option_rationales` table is the de facto repository of LLM output.

**Beta impact:**
- `solution_steps` (multi-step walkthrough) — missing → frontend "Adım adım çözüm" feature is empty.
- `similar_question_ids` (related question recommendations) — missing → frontend "Benzer sorular" feature is empty.
- `reviewed_at` — missing → admin audit trail / staleness detection cannot work.

---

## 5. Math (`question_math`) Symbolic Verification

| Metric | Value |
|--------|-------|
| Total math rows | 31,034 |
| `is_symbolic_verifiable = TRUE` | 31,034 (100%) |
| `verified_by_sympy = TRUE` | **0** |
| `numeric_tolerance` populated | **0** |
| `math_complexity_score` populated | **0** |
| `equivalent_forms` populated | 0 |

**Verdict: SIGNATURE DEFECT.** The schema marks all 31K rows as "symbolic verifiable" but ZERO have actually been SymPy-verified. Sample expected expressions seen:
- `13*k` (parametric) — non-numeric, not a final answer.
- `2*X + Y + 3*Z` (algebraic expression with capital letters) — SymPy parses but `X, Y, Z` are unknowns; cannot evaluate without context.
- `A**B + C**D + E**F` (purely literal) — meaningless without binding.

**The `expected_answer_sympy` field is heterogeneous**: some are concrete numbers (`30`, `15`, `12`), some are parametric (`13*k`), some are uninterpretable letter expressions (`A**B + ...`). A SymPy roundtrip would fail on a large fraction (Step 1 = parse, Step 2 = evaluate vs `correct_answer`).

**Recommended action before beta:** Run an offline SymPy verification pass and write `verified_by_sympy = TRUE` only for rows where `parse_expr(expected_answer_sympy).evalf()` matches `correct_answer` within `numeric_tolerance`. Current flag is meaningless — equivalent to "claimed but never tested".

---

## 6. Hallucination Findings

From 50-sample × 5 options = 250 reviewed rationales:

| Hallucination class | Count in sample | Examples |
|---|---|---|
| Confidently-wrong correct answer (factual) | **2 / 50** (%4) | Sample 2 (Hemingway/Stendhal), Sample 5 (Pürranameler/Fütüvvetnameler) |
| Physics fact distortion | **1 / 50** (%2) | Sample 8 (Compton — "ortama göre" claim for photon speed) |
| Internal contradiction (rationale vs is_correct) | **1 / 50** (%2) | Sample 45 (Qwen, B labeled "Doğru cevap" while is_correct=f) |
| Empty/circular justification | **1 / 50** (%2) | Sample 2 ("soruda verilen anahtar bilgiler doğrultusunda doğru cevap olarak belirlenmiştir") |
| Fabricated term definition | **1 / 50** (%2) | Sample 5 ("Pürranameler" definition fabricated) |

**Aggregate hallucination rate: ~%8-10** if we count any of the above. Two of these are **critical** (Samples 2 + 5 — confident propagation of wrong correct_answer with fabricated justification). Extrapolated to 81,745 rationale questions: **~3,200-8,200 questions may carry confidently-wrong content**.

**Root cause:** The LLM is operating in "trust correct_answer field as ground truth" mode. When `correct_answer` is wrong (OCR error, key mismatch), the model **rationalizes the wrong answer instead of flagging the inconsistency**. There is no "I cannot reconcile this" escape hatch.

---

## 7. OCR Artifact Propagation

Reviewed `question_text` in 50 samples. Found OCR artifacts in question text:
- Sample 3: "İnsan reik yapısına olduğunda doğru topluma birlikte anlam kazanır" — "reik" is OCR noise from "iç" (Turkish "iç" mis-recognized).
- Sample 16: "geçmişin büyüü denizlerinde yolcuğu" — "büyüü" (büyülü typo), "yolcuğu" (yolculuğa typo).
- Sample 19: "Bulundukları grubun adı, grubun ilk üyesi olan etinin özel adından alkinler olar" — sentence truncated.
- Sample 24: "$a=70^ ext{o}$" — LaTeX glitch `\text` rendered as `^ ext`.
- Sample 50: "etkileşme gerçekleşmediğine göre, bu işlemler sonucunda, K, L ve M elektroskoplarının yaprakları için, d" — truncated.

**Good news:** Rationales do NOT amplify these OCR errors. The LLM appears to silently work around them. No "loylak"-style propagation observed.
**Bad news:** Rationales also do NOT flag them. A student seeing the buggy question text gets a confidently-written rationale for a possibly nonsensical premise.

---

## 8. Per-Subject Quality Scores

Based on 50-sample reading + aggregate column statistics. Scoring rubric: 1-10 (10 = production-ready, 5 = acceptable for beta with caveats, ≤3 = unsafe).

| Subject | Questions w/ rationale | Gemini share | Qwen share | Quality 1-10 | Notes |
|---------|-----------|--------------|-------------|-------------|-------|
| MATEMATIK | 21,597 | %85 | %15 | **7** | Gemini solid for symbolic problems; Qwen rationales are mechanical echoes |
| GEOMETRI | 20,660 | %76 | %24 | **6** | Higher Qwen share → more generic rationales (see Sample 36, 45) |
| FIZIK | 15,115 | %70 | %30 | **5** | Multiple physics-fact distortion (Sample 8, 33); Qwen 30% |
| KIMYA | 7,190 | %92 | %8 | **8** | Gemini-dominant; Sample 19 (alkinler), Sample 32 (iyon-dipol) coherent |
| TURKCE | 6,880 | %99.7 | %0.3 | **5** | Gemini-only, but high hallucination risk for factual literary terms (Sample 5) |
| BIYOLOJI | 3,397 | %90 | %10 | **7** | Sample 13 (ATP) clean, Sample 9 (ekosistem) clean |
| EDEBIYAT | 2,557 | %99 | %1 | **3** | **CRITICAL** — Sample 3 (Hemingway/Stendhal) shows systematic hallucination on author/work questions |
| TARIH | 1,690 | %97 | %3 | **6** | Sample 42 (Baltacı Mehmet Paşa) coherent; risk for date/event fabrication exists but not seen in this sample |
| GENEL | 1,342 | %100 | %0 | **6** | Sample 40 (arazi planlama) opinion-style, not strict factual |
| COGRAFYA | 615 | %54 | %46 | **4** | Heavy Qwen share + small sample = high risk |
| SOSYAL | 552 | %100 | %0 | **6** | Not sampled |
| FEN | 150 | %100 | %0 | **6** | Not sampled |

**Subject-level beta-safety cutoff:**
- **Safe (≥7):** MATEMATIK, KIMYA, BIYOLOJI
- **Conditional (5-6):** FIZIK, TURKCE, TARIH, GENEL, GEOMETRI, SOSYAL, FEN
- **UNSAFE (≤4):** EDEBIYAT, COGRAFYA

---

## 9. Length Distribution

| Generator | Avg len | Min | Max | Under 40 char | Verdict |
|-----------|---------|-----|-----|---------------|---------|
| gemini-flash-latest | 116.4 | 40 | 203 | 0 | Consistent, well-bounded |
| gpt-4o-mini | 67.5 | 35 | 125 | 1 | Tight |
| qwen3:8b | 67.4 | 12 | 1000 | **4,351** | High variance — short generic + occasional 1000-char overflow |

**Qwen has 4,351 rationales under 40 chars** ("Boyalı alan, yarım çemberlerin alanlarının toplamından daha fazladır.", "I doğrudur, II ve III yanlış.") — these are below the threshold of pedagogical value.

---

## 10. Similar Question IDs Quality

`question_bank.similar_question_ids` column: **100% NULL in auto_judged_high (0/15,321).**

No data to audit. Feature is not populated.

---

## 11. Quality Risk Summary — Beta Deployment Recommendations

### MUST-FIX before beta (P0):

1. **Disable the LLM rationale display for questions whose `quality_review_status != 'auto_judged_high'`** — those carry the rationales generated against potentially-wrong `correct_answer`. Currently the 81,745 questions with rationales are spread across `rejected` (48,942), `pending` (32,726), and `unverified` (77) — exactly the wrong populations to expose to students.

2. **Filter out the EDEBIYAT subject entirely from rationale display** until factual hallucinations (Sample 3, 5) are remediated. The 2,557 EDEBIYAT rationales were 99% Gemini-generated against potentially OCR-corrupted `correct_answer`.

3. **Add a post-generation factual cross-check pass** for high-risk subjects (EDEBIYAT, TARIH, COGRAFYA, TURKCE — anything where the correct answer is a knowable named entity / date / term). Use a second model (e.g. Claude Opus) to flag rationales where the marked-correct option contradicts world knowledge.

4. **Suppress Qwen-generated rationales in the UI** until they are regenerated. 14,027 questions have Qwen rationales; ~30% are below pedagogical-value threshold (mechanical echoes, internal contradictions like Sample 45).

### SHOULD-FIX before beta (P1):

5. **Populate `question_bank.misconception_tags`** by post-processing the existing `qor.rationale` text. The current state (0/187,834 populated) means any frontend misconception-aware feature is dead.

6. **Run SymPy verification pass** on `question_math.expected_answer_sympy`. Flag the 31,034 rows with `verified_by_sympy = FALSE` and only display formula-based correctness to students for verified rows.

7. **Reconcile `auto_judged_high` rationale gap** — either link the 81,745 rationale-bearing questions back to Gold status, or document that the Gold tier currently lacks rationale coverage.

### NICE-TO-HAVE (P2):

8. **Populate `solution_steps`** for MATEMATIK / GEOMETRI / FIZIK (the subjects where step-by-step is most valuable).
9. **Populate `similar_question_ids`** via pgvector cosine on existing embeddings.
10. **Populate `reviewed_at`** retroactively from `qor.generated_at` (currently `qor.generated_at` IS populated).

---

## 12. Methodology

- **Sample SQL:** `SELECT q.id, q.subject_area, q.question_text, q.correct_answer, q.option_a..option_e FROM question_bank q WHERE q.is_active = TRUE AND EXISTS (SELECT 1 FROM question_option_rationales qor WHERE qor.question_id = q.id) ORDER BY md5(q.id::text) LIMIT 50` → `llm_sample_50.tsv`
- **Rationale SQL:** `SELECT qor.question_id, qor.option_letter, qor.is_correct, qor.generated_by, qor.rationale FROM question_option_rationales qor JOIN sample USING (question_id) ORDER BY question_id, option_letter` → `llm_sample_50_rationales.tsv` (250 rows)
- **Sample size:** 50 questions, 250 rationales (full 5/5 coverage)
- **Selection:** md5-ordered random (reproducible — `ORDER BY md5(q.id::text)`)
- **Truncation:** Question text LEFT(300), options LEFT(80) (preview only, full rationale text retained)
- **Aggregate columns:** Full table scans (408,720 rationale rows, 15,321 auto_judged_high, 31,034 question_math).
- **Reproducible:** YES.
- **Read-only:** YES (no INSERT/UPDATE/DELETE; no transaction)

### Source data files
- `docs/audits/2026-05-21_full_audit/llm_sample_50.tsv` (50 rows)
- `docs/audits/2026-05-21_full_audit/llm_sample_50_rationales.tsv` (250 rows)

---

## 13. Critical Discrepancies vs Memory / CLAUDE.md

| Claim in memory | Live DB reality |
|-----------------|-----------------|
| "Phase 7 Gemini Batch API: 81,657/81,776 (%99.85) Gold gold rows" | Gold (`auto_judged_high`) = **15,321 active**, **0 with rationales**. Rationale-bearing Q ≈ 81,745 but attached to `rejected`/`pending`. |
| "`question_option_rationales` = 383,660 rows" | Live: **408,720 rows** (+%6.5) |
| "`question_math` = 27,244" | Live: **31,034** (+%13.9) |
| "gpt-4o-mini factual hata yaptığı kanıtlandı (Hemingway→Stendhal) — kullanılmıyor" | **gemini-flash-latest reproduces the exact same Hemingway/Stendhal hallucination** (Sample 2). Switching away from gpt-4o-mini did not fix the underlying issue. |
| "misconception_tags ORM (Session 178)" | Schema column exists; **0/187,834 populated** |
| "solution_steps ORM (Session 178)" | Schema column exists; **0/15,321 populated in auto_judged_high** |
| "similar_question_ids ORM (Session 178)" | Schema column exists; **0/15,321 populated in auto_judged_high** |

Memory should be updated post-audit.

---

*Generated: 2026-05-21*
*Audited by: sub-agent (read-only PostgreSQL queries, 50-sample manual review)*
*Reproducible: YES — see Methodology section*
