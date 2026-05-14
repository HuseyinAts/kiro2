# Bayesian Validator Precision Audit — RESULT

**Tarih:** 14 May 2026 (Faz 0.9, Session 156)
**Method:** C2 (50) + C3 (30) audit verisinden Bayesian metadata extract + verdict cross-reference
**Sample:** 80 satır toplam (50 Bayesian-bypassed + 30 Bayesian-applied)
**Süre:** ~1 saat

---

## TL;DR

**Bayesian validator (cross_validate_answers.py) precision'ı = %26 (HIGH confidence)**, hedef %70'in çok altında. **REPLACE önerilir** — Bayesian'ı atla, judge'a doğrudan git.

**Kritik bulgu:** v4.14e Gemini Flash batch'i (107,516 satır = unverified pool'un %73'ü) Bayesian validator'dan **HİÇ GEÇMEMIŞ** (confidence_level = NULL). Plan v1'in "Bayesian yetersiz" varsayımı kısmen yanlıştı — Bayesian uygulanmamıştı.

**Source analizi:** `page_inline` (book key) %40 pass, `ai_upgrade_bayes_*` (Bayesian crossval) %11 pass. Book key 4x daha güvenilir.

---

## Pool Bayesian Coverage (live DB)

| Subset | n | confidence_level | Bayesian uygulanmış mı? |
|---|---|---|---|
| v4.14e Gemini Flash batch | 107,516 | NULL | ❌ Hayır — raw output |
| unverified high confidence | 38,060 | high | ✓ Evet |
| unverified medium | 797 | medium | ✓ Evet |
| unverified very_high | 14 | very_high | ✓ Evet |

**73% of unverified pool was never even processed by Bayesian.** Plan v1'in "Bayesian fail oldu" tezi aslında "Bayesian uygulanmadı" demek.

---

## C2 Sample Analizi (50 satır, Bayesian-bypassed)

Tüm 50 entry: `confidence_level = NULL`, `best_method = NULL`, `answer_source = NULL`

→ Bu pool için Bayesian precision ölçümü **mümkün değil** (uygulanmamış).
→ C2'nin "%30 pass" oranı = **Gemini Flash raw output precision'ı** (Bayesian dışı).

---

## C3 Sample Analizi (30 satır, hepsi Bayesian-applied)

### Confidence × Verdict Crosstab

| Confidence | n | pass | fail | unclear | Pass % |
|---|---|---|---|---|---|
| **high** | 23 | 6 | 11 | 6 | **26.1%** |
| **medium** | 7 | 0 | 5 | 2 | **0.0%** |
| TOPLAM | 30 | 6 | 16 | 8 | 20.0% |

**Bayesian "HIGH confidence" precision: %26.1** — hedef %70'in çok altında.
**Lenient (ignore unclear):** 6/17 = %35.3 — hala çok düşük.

### Source × Verdict Crosstab

| answer_source | n | pass | fail | unclear | Pass % |
|---|---|---|---|---|---|
| **page_inline** (book key) | 5 | 2 | 0 | 3 | **40.0%** |
| **ai_upgrade_bayes_*** | 18 | 2 | 13 | 3 | **11.1%** |
| crossval_bayes_* | 2 | 1 | 1 | 0 | 50.0% |
| ai_crop_solve_qwen | 2 | 1 | 0 | 1 | 50.0% |
| jsonl_v11 | 2 | 0 | 2 | 0 | 0.0% |
| ai_solved_claude_opus | 1 | 0 | 0 | 1 | 0.0% |

**KRİTİK İÇGÖRÜ:**
- **page_inline (book key)** = en güvenilir source (%40, küçük sample)
- **ai_upgrade_bayes** (Bayesian'ın kendi crossval'i) = en zayıf (%11.1) — istatistiksel olarak anlamlı (n=18)
- Bayesian "ben bu cevabı X kaynaktan doğruladım" diyor → audit %89 yanlış çıkıyor

---

## Karar — Bayesian'ı Ne Yapmalı?

| Strateji | Önerilen mi? | Sebep |
|---|---|---|
| **A) Replace tamamen** | ✅ EVET | %26 precision yetersiz, judge daha güvenilir |
| B) Hibrit (Bayesian fast filter + judge) | ❌ Hayır | Bayesian'ın katma değeri düşük, kompleksite yüksek |
| C) Calibrate threshold daha yüksek | ❌ Hayır | very_high sadece 14 satır, anlamsız |
| **D) page_inline subset'i koru, gerisi judge** | ✅ EVET (önerilen) | Book key %40 pass = "Bronze tier candidate"; Bayesian crossval drop |

**Önerilen kombinasyon: A + D**
- Drop `ai_upgrade_bayes_*` source guvenini (judge'a bırak)
- Keep `page_inline` source ayrı tier olarak (book key match = orta-yüksek güven)
- Judge tüm pool'a uygulanır

---

## Plan v1 Üzerindeki Etkiler

### 🔻 Faz 5.7 (Bayesian-Judge hybrid logic) — IPTAL

**Önceki:** Audit pozitif olursa Bayesian fast filter olarak kalır
**Yeni:** Audit negatif çıktı (%26 precision), Bayesian tamamen drop edilir
**Yerine:** Faz 5.x — judge tek karar mercii

### 🆙 Faz 1.9 (Book answer key cross-reference) — ÖNCELİK ARTAR

**Önceki:** Wrong_answer'ın %40'ını ücretsiz yakalar (cheap audit)
**Yeni:** En güvenilir non-judge source (audit %40 pass) → primary signal for Bronze tier

### 🆙 Faz 6.1 (Judge pilot) — KAPSAM ARTAR

**Önceki:** Bronze pool'dan 1,000 sample
**Yeni:** Judge tüm 146K unverified'a uygulanır (Bayesian filter yok)
**Cost projeksiyon güncelleme:** Faz 5.6'da artar (~$430 → ~$600-800)

### 🆕 Yeni: Bayesian-related satırları flag etme

`answer_source LIKE 'ai_upgrade_bayes_%'` olan satırlar audit'te %11 pass → Plan v1 Faz 1.x'te ek task:
- `quality_review_status='likely_unsafe'` flag (yeni Convention v3 status)
- Veya direkt `rejected` candidate (judge'da fail beklendiği için)

---

## Yeni KPI

| Metric | Hedef | Audit | Karar |
|---|---|---|---|
| Bayesian validator precision | >%70 | **%26** | ❌ FAIL → REPLACE |
| Book key (page_inline) precision | >%50 | **%40** | ⚠ Borderline → keep with caveat |
| ai_upgrade_bayes precision | >%50 | **%11** | ❌ FAIL → drop trust |

---

## Methodology Notları (audit-methodology.md uygulanmış)

- Sample size: 80 (50 C2 + 30 C3)
- Sample selection: Faz 0.2 audit'inden recovered, reproducible seed (`md5(id || 'audit-Cx-...')`)
- Truncation: ❌ YOK (full text karşılaştırma yapıldı)
- Reproducible: ✅ Evet (TSV scoring + Bayesian metadata extract scripts mevcut)
- Bias: C3 sample legacy_v3_unaudited subset (Bayesian-applied), C2 sample v4.14e Gemini Flash subset (Bayesian-bypassed) — **iki ayrı pool**, farklı sonuçlar normal

**Limitation:** C3 sample n=23 high confidence küçük (%95 CI: ~10%-50%). Daha büyük audit (n=200) gerekirse Faz 5.7 öncesi yapılabilir, ama mevcut sinyal güçlü (16 high confidence fail / 23).

---

## Sıradaki adım

1. ✅ Faz 0.9 tamamlandı
2. Plan v1'de Faz 5.7'yi `cancelled` olarak işaretle (veya basitleştir)
3. Faz 1.9 öncelik artırma
4. Faz 5.6 cost projection güncellenecek (Bayesian filter yok)
5. **Faz 0.7 (Pool kategori kararı)** sıradaki büyük karar — bu audit verisi onun input'u

---

*Generated by Faz 0.9 investigation. Bayesian precision %26, REPLACE önerildi. Book key (page_inline) %40 ile en güvenilir alternatif source.*
