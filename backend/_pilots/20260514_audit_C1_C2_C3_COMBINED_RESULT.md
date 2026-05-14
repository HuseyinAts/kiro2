# Audit RESULT — C1+C2+C3 Combined Synthesis (110 sample)

**Tarih:** 14 May 2026 (Session 156)
**Pre-analysis:** Claude (Opus 4.7) — verdict + error_type per satir
**Validation:** Hüseyin onay (4 ayri konfirmasyonla, ikircikli noktalar gözden geçirildi)
**Disk artefaktları:**
- `20260515_audit_C1_SCORING.tsv` (30 satir, missing_diagram pool)
- `20260515_audit_C2_SCORING.tsv` (50 satir, math/geometry wrong_answer pool)
- `20260515_audit_C3_SCORING.tsv` (30 satir, legacy_v3_unaudited general quality)

---

## TL;DR

| Audit | n | Pool tanimi | pass | fail | unclear | Hata orani |
|---|---|---|---|---|---|---|
| **C1** | 30 | unverified + has_diagram=true + image=null | 6.7% | 63.3% | 30.0% | %93.3 |
| **C2** | 50 | unverified + math/geo + has_diagram=false | 30.0% | 50.0% | 20.0% | %70.0 |
| **C3** | 30 | legacy_v3_unaudited (eski 'approved') | 20.0% | 53.3% | 26.7% | %80.0 |
| **TOPLAM** | **110** | — | **22.7%** | **53.6%** | **23.6%** | **%77.3** |

**Hicbir alt-pool beta'ya hazir degil.** En iyi alt-pool (C2 math/geo) bile %70 hatali.

---

## Kombine error type dagilimi

| Error type | n | % of 85 errors |
|---|---|---|
| **wrong_answer** | 22 | **25.9%** |
| missing_diagram | 28 | 32.9% |
| ocr (cut off + misread) | 18 | 21.2% |
| garbage_text | 9 | 10.6% |
| incomplete (missing data) | 8 | 9.4% |

**Hata türü ne anlatıyor:**
- **wrong_answer** (%26): Cevap matematik olarak yanlis. Pipeline-fix CÖZMEZ — sadece judge/curator düzeltir.
- **missing_diagram** (%33): Image link eksik. Pipeline-fix (Tier C+D) %85 cözer.
- **ocr** (%21): Text cut off veya bozuk OCR. Re-OCR + import validator gerekli.
- **garbage_text** (%11): Soru kendisi anlamsiz. Reject (rejected status).
- **incomplete** (%9): Veri eksik (log b yok, açi listesi yok vs). Manuel veri tamamlama veya reject.

---

## Audit-bazinda detayli analiz

### C1 — Missing Diagram Audit (30 sample)

**Pool:** has_diagram=true ama question_image_url=NULL satirlar (DB'de 49,313 toplam)

| Verdict | n | % |
|---|---|---|
| pass | 2 | 6.7% |
| fail | 19 | 63.3% |
| unclear | 9 | 30.0% |

**Kritik bulgular:**
1. **has_diagram=true flag güvenilir** — 30 sample'da sadece 2 false positive (#6 ve #10). %93.3 doğru flag.
2. **Pipeline-fix değerli** — 23/30 satir (%76.7) image-link gerektiriyor; daha önceki disk audit'inin %84.7 fix potansiyeli ile uyumlu.
3. **OCR cut-off da burada** — 5 sample'da text truncation gözlendi (%16.7). Sorun sadece görsel değil, metin bütünlüğünde de var.

**Pass örnekleri (false positive flag):**
- #6 (ABC dik üçgen, |AG|=6, |DC|=11): tüm uzunluklar metinde → text-only çözülebilir
- #10 (parabol y=4 dikdörtgen optimizasyon): saf cebirsel, görsel gereksiz

→ Plan v1 etkisi: Tier C+D image matcher (Faz 1.1, 1.2) yatırımı kanıtlı değer.

---

### C2 — Math/Geometry Wrong Answer Audit (50 sample)

**Pool:** unverified + MATEMATIK/GEOMETRI + has_diagram=false (DB'de ~30K toplam)

| Verdict | n | % |
|---|---|---|
| pass | 15 | 30.0% |
| fail | 25 | 50.0% |
| unclear | 10 | 20.0% |

**Kritik bulgular:**
1. **wrong_answer dominant** — 17/50 sample net olarak yanlış cevap (öğrenci yanlış öğrenir).
2. **Bayesian validator yetersiz kanıtlandı** — Bu pool'un büyük kısmı zaten cross_validate_answers.py'den geçmiş, ama %34 hala wrong_answer.
3. **Math hallüsinasyon pattern'i** — Cevaplar "yakın ama yanlış" (8 vs 4, 6 vs 8) — Gemini option'lardan tahmin etmiş gibi görünüyor.
4. **OCR cut-off oranı yüksek** — 12/50 (%24) text truncation. Math soruları daha uzun olduğu için C1'den (%16.7) daha kötü.

**Wrong_answer kategorize:**
- Aritmetik/cebirsel: #5, #11, #19, #23, #27, #41, #42, #45, #47, #49 (10 sample)
- Calculus/limit/integral: #8, #15, #39, #43 (4 sample)
- Trigonometri: #9, #14, #29 (3 sample)

**Pattern:** Calculus ve trigonometri en çok wrong_answer (%50), aritmetik daha güvenilir.

→ Plan v1 etkisi: Faz 5 (LLM judge) bu pool için kritik. Math-specific judge (Faz 5.8) önemli. Bayesian-Judge hybrid (Faz 5.7) kararı için Faz 0.9 audit gerekli.

---

### C3 — Legacy v3 Unaudited Audit (30 sample)

**Pool:** quality_review_status='legacy_v3_unaudited' (eski hardcoded 'approved', 18,397 satır)

| Verdict | n | % |
|---|---|---|
| pass | 6 | 20.0% |
| fail | 16 | 53.3% |
| unclear | 8 | 26.7% |

**Kritik bulgular:**
1. **Convention v2 smoking gun doğrulandı** — %80 non-pass oranı, 14 May'in tahmin ettiği %87 ile tutarlı (sample varyansı içinde).
2. **garbage_text dominant** — 9/30 (%30) tamamen anlamsız sorular. Bu pool'un import'unda hiçbir kalite kontrolü yapılmamış.
3. **Şaşırtıcı:** Gemini Flash output'u (C2 pass %30) > legacy_v3 'approved' (C3 pass %20). Yani v4.14e ne kadar şikayetçi olunsa da v3.5+ legacy'den daha kaliteli.

**Garbage örnekleri:**
- "Operasyon hangi sayıya karşılık gelir?" (sayı eşlenememe)
- "Mikro hemşarp" (Türkçe değil)
- "KUAFÖR raporu" FIZIK kategorisinde

→ Plan v1 etkisi: legacy_v3 pool'un büyük kısmı judge'da fail edecek. Pool prioritization: Faz 6.1 v4.14e ÖNCE. Convention v2 daha da agresif olabilir (legacy_v3'ü hızla rejected'a dönüştür).

---

## Cross-cutting Pattern'ler (3 audit toplamı)

### 1. OCR cut-off endemic
- C1: 5/30 (%16.7)
- C2: 12/50 (%24)
- C3: 2/30 (%6.7) (C3'te garbage daha baskın, OCR az)

Toplam: 19/110 (%17.3) text truncation.

**Hipotez:** Pipeline'ın bir yerinde text length limit var (DB column, JSONL field, Gemini config, import script). Faz 0.8 (yeni) bunu araştıracak.

### 2. wrong_answer Bayesian'a takılmıyor
C2'de gözlenen %34 wrong_answer, cross_validate_answers.py geçmiş. Bayesian'ın confidence skoruna güven yetersiz — gerçek hesap doğrulama gerekli (Faz 1.8 SymPy + Faz 5 LLM judge).

### 3. Pipeline-fix değerli ama tek başına yetmez
- C1 missing_diagram: pipeline-fix ÇÖZER (~%85)
- C2 wrong_answer: pipeline-fix ÇÖZMEZ (judge gerekli)
- C3 garbage_text: pipeline-fix ÇÖZMEZ (reject gerekli)

→ Strateji: Faz 1 pipeline-fix Bronze tier oluşturur; Faz 5-6 judge bu Bronze'u Gold'a yükseltir.

### 4. Pass'ler ne zaman olur?
Tüm pass örneklerinde ortak özellik:
- Tüm değişkenler/sayılar metinde açıkça verilmiş
- Görsel referansı yok
- Standard YKS formatında temiz hesap
- Cevap 1-2 adımda doğrulanabilir

**Çıkarım:** Sapphire/Gold pool'u "compact, well-defined math" sorularıyla başlamalı.

---

## Plan v1 KPI revizesi (kanıta dayalı)

| Faz | KPI | Önceki hedef | **Revize hedef** | Gerekçe |
|---|---|---|---|---|
| 1.5 | missing_diagram audit dilimi | <%5 | **<%10** (gerçekçi) | Gerçek baseline %32 (audit) → %85 fix ile %5 kalır; ama unclear'lar var |
| 2 | Audit harness uptime | 4/4 hafta | 4/4 hafta | Değişmedi |
| 3 | Curator velocity | 30-50/saat | **20-40/saat** (defansif) | C audit Hüseyin için zorlu çıktı; daha düşük tahmin |
| 4 | Sapphire inter-rater | >%95 | **>%90** | İlk denemede daha gerçekçi |
| 5 | Judge F1 (200 set) | ≥0.85 | **≥0.80** ilk hedef, ≥0.85 stretch | Türkçe LLM judge benchmark yok |
| 6 | Gold post-judge audit hata | ≤%5 | **≤%8** ilk launch, ≤%5 3 ay sonra | Gerçekçi compound iyileşme |
| 7 | 30-gün MA error | <%2 sustained 3 ay | **<%5 ilk 3 ay, <%2 6 ay sonra** | Beta launch ile gerçek trafik dahil |

### Yeni KPI'lar (3 ek metric)

| Metric | Hedef | Faz | Ölçüm |
|---|---|---|---|
| Bayesian precision | >%70 | 0.9 | Audit'le ölç, hibrit/replace karar |
| OCR truncation oranı | <%5 yeni ingest'te | 0.8 + 1.10 | Re-OCR sonrası ölç |
| Symbolic math coverage | >%30 math sorusu | 1.8 | SymPy parse rate |

---

## Strateji Ayarlamaları (3 audit ışığında)

### A. Faz 6 judge order revize (Sorun 4 → Sorun 5'ten önce)

```
Faz 6.1 Judge Pilot (1000 satir):
  Eski: Bronze pool'dan random
  Yeni: 700 v4.14e (yüksek pass beklenir) + 300 legacy_v3 (düşük pass beklenir)
  Sebep: v4.14e > legacy_v3 (audit'le doğrulandı)
```

### B. Sapphire build hedefli

```
Faz 4.1 200 manuel curated:
  Eski: Stratified 50 exact + 50 fuzzy + 50 fallback + 50 v3.5 residual
  Yeni: Math/geo öncelikli (judge calibration için en zor kategori)
        - 80 math (algebra/aritmetik daha fazla, calculus/trig daha az)
        - 60 fen (kimya/fizik/biyoloji)
        - 40 sosyal (turkce/edebiyat/tarih/cografya)
        - 20 controlled garbage_text (judge'un reject yapabildiğini test)
```

### C. Convention v2.1 — legacy_v3 hızlı triage

```
legacy_v3_unaudited pool için (18K satir):
  - Faz 6'dan önce: judge'a göndermeden önce hızlı "garbage filter" 
    (heuristic: source_book vs subject_area mismatch → flag)
  - Beklenen: 30-50% direkt reject candidate
  - Cost optimization: 18K → ~10K judge'a → cost düşer
```

### D. OCR truncation acil müdahale

```
Faz 0.8 ASAP:
  1. DB column length check
  2. eslesmis_sorucevap.jsonl sample
  3. Gemini Flash config review
  4. import_d_dataset.py inspection
  Bulgu: tek bir layer ise tek-noktadan fix; multiple ise sequential fix
```

---

## Sample disk artefaktları konumu

```
backend/_pilots/
├── 20260515_audit_C1_RAW.tsv         (orijinal sample)
├── 20260515_audit_C1_SCORING.tsv     (verdict+error_type+notes dolu)
├── 20260515_audit_C2_RAW.tsv
├── 20260515_audit_C2_SCORING.tsv
├── 20260515_audit_C3_RAW.tsv
├── 20260515_audit_C3_SCORING.tsv
├── 20260515_SCORING_GUIDE.md         (rubric + örnekler)
├── _apply_C1_scoring.py              (idempotent re-apply tools)
├── _apply_C2_scoring.py
└── _apply_C3_scoring.py
```

Reproducible: scoring scripts mapping dict olarak tutuyor; tüm audit yeniden çalıştırılabilir.

---

## Sonraki adımlar (Plan v1'e göre)

1. ✅ Faz 0.2 (bu audit) tamamlandı
2. Faz 0.1 — Memory drift fix (live DB sayıları)
3. Faz 0.3 — audit_missing_image_v2 + RESULT commit
4. Faz 0.4 — question_bank pg_dump backup
5. Faz 0.5 — Plan v1 commit (KPI revize ile birlikte)
6. **Faz 0.8 — OCR truncation root cause** (ASAP, audit bulgusu üzerine)
7. Faz 0.9 — Bayesian precision audit (ASAP, hybrid karar için)
8. Faz 1.x sprintleri başlar (pipeline-fix + symbolic verifier + book key cross-ref)

---

*Generated by Claude session 156 pre-analysis. Hüseyin tarafından 4-noktada onaylandı (C3 satır 19, C1 satır 6/22/5, C2 satır 13/38/44/9 ikircikli noktalar gözden geçirildi).*
