# Judge Pipeline Cost Projection v1

**Tarih:** 15 May 2026 (Session 160, Faz 5.6)
**Scope:** Bronze pool (80-146K satır) Judge maliyet hesaplaması
**Prereq:** [Convention v3](quality_review_status_convention_v3.md), [Plan v1](quality_pool_plan_v1.md)
**Reproducible:** Token sample n=20, formula bölümünde yeniden hesap için SQL+kod

---

## Özet

| Senaryo | Per-call | 80K Bronze | 100K | 146K |
|---|---|---|---|---|
| Gemini Pro solo (text) | $0.00194 | **$155** | $194 | $283 |
| Opus solo (text) | $0.0165 | $1,320 | $1,650 | $2,409 |
| **Opus + Pro double (text)** ⭐ | $0.0184 | **$1,475** | **$1,844** | **$2,692** |
| Opus + Pro double (with image) | $0.0257 | $2,055 | $2,569 | $3,750 |
| Math judge hybrid (Faz 5.8) | $0.05 | $4,000 | $5,000 | $7,300 |

**Önerilen:** Opus + Pro double check (text-only) → **$1,475-$2,692** total. Image input opsiyonel, %25-40 ek maliyet.

---

## 1. Pool Size Senaryoları

Convention v3 migration roadmap'inden (Faz 1.6 sonrası):

| Senaryo | Pool Size | Kaynak |
|---|---|---|
| Conservative (Bronze realistic) | **~80K** | Plan v1 Faz 6.3 "Judge full run (Bronze ~80K)" |
| Moderate | 100K | Pipeline-fix %70 başarı (mid estimate) |
| Worst case (no filtering) | **146,387** | Mevcut `unverified` count (15 May DB) |

Convention v3 Faz 1.6 sonrası Bronze pool 80-100K aralığında bekleniyor (pipeline-fix geçemeyenler `unverified` veya `rejected` olur).

---

## 2. Token Sample Analizi

**Sample:** 20 random `unverified` satır + image (Bronze proxy), seed `42_seed`.

**Tokenization estimation:** Turkish text ~3.5 char/token (Latin + Turkish-specific + LaTeX karışık).

```
AVG question_text chars  : 279
AVG options chars (sum)  : 72   ← çoğu LaTeX/şekil-referanslı, kısa
AVG correct_answer chars : 1    ← A/B/C/D/E
AVG INPUT TOKENS / call  : 351  ← (279+72+1)/3.5 + 250 prompt overhead
ASSUMED OUTPUT TOKENS    : 150  ← JSON verdict + 1-2 cümle reasoning
```

**Outlier:** 1 satır 564 input tokens (uzun problem statement). p95 ~450 tokens.

**Reasoning:** Geometri sorularında option metinleri çok kısa (şekil referansı). Sözel ders sorularında option uzunluğu 3-5x artar — gerekirse subject-stratified sample (gelecek revizyon).

---

## 3. Pricing (2026-05 itibariyle)

⚠️ **Pricing dinamik** — provider sayfalarından doğrula:
- [Anthropic API](https://www.anthropic.com/pricing)
- [Google AI](https://ai.google.dev/pricing)

| Model | Input $/M | Output $/M | Vision (per image) |
|---|---|---|---|
| Claude Opus 4.7 | $15.00 | $75.00 | ~$0.0048 |
| Claude Sonnet 4.6 | $3.00 | $15.00 | ~$0.0048 |
| Gemini 2.5 Pro (≤200K) | $1.25 | $10.00 | ~$0.0025 |
| Gemini 2.5 Pro (200K+) | $2.50 | $15.00 | ~$0.0025 |

**Knowledge cutoff:** Ocak 2026. Opus 4.7 pricing Opus 4.0 ile aynı varsayıldı (en yakın referans).

---

## 4. Per-Call Cost Matrix

**Formül:** `cost = (input_tokens × in_price/M) + (output_tokens × out_price/M) + image_price`

**Sabitler:** input=351, output=150, image_count=0 or 1

```
Opus 4.7 text-only:
  351 × $15/M  + 150 × $75/M  = $0.00527 + $0.01125 = $0.01652

Opus 4.7 + image:
  $0.01652 + $0.0048 (image) = $0.02132

Gemini 2.5 Pro text-only:
  351 × $1.25/M + 150 × $10/M  = $0.000439 + $0.0015 = $0.001939

Gemini 2.5 Pro + image:
  $0.001939 + $0.0025 (image) = $0.004439

Opus + Pro double (text):
  $0.01652 + $0.001939 = $0.018459

Opus + Pro double (with image):
  $0.02132 + $0.004439 = $0.025759
```

---

## 5. Total Cost Matrix

### 5.1 Text-only (image hariç, sadece question_text + options)

| Pool size | Pro solo | Opus solo | **Opus + Pro** | Math hybrid (Faz 5.8) |
|---|---:|---:|---:|---:|
| 80K | $155 | $1,322 | **$1,477** | $4,000 |
| 100K | $194 | $1,652 | **$1,846** | $5,000 |
| 146K | $283 | $2,412 | **$2,695** | $7,300 |

### 5.2 With image input

| Pool size | Pro solo | Opus solo | Opus + Pro | Math hybrid |
|---|---:|---:|---:|---:|
| 80K | $355 | $1,706 | $2,061 | $4,500 |
| 100K | $444 | $2,132 | $2,576 | $5,625 |
| 146K | $648 | $3,113 | $3,761 | $8,213 |

### 5.3 Math judge hybrid (Faz 5.8) — re-solve + symbolic check

- Re-solve = LLM generates solution path → output ~500 tokens (3x normal)
- Symbolic check = SymPy local (maliyet $0)
- Per-call: Opus 351 in + 500 out = $0.00527 + $0.0375 = **$0.04277**
- Sadece **math-flagged satırlar** (Bronze'un ~%50-60'ı): 50K × $0.04277 = ~$2,138 add-on
- Total math-heavy run: ~$4,000-$5,000 (Bronze 80K, %50 math)

---

## 6. Disagreement Buffer (curator review)

Plan v1 strateji: **Opus + Pro double check**, disagree → curator manuel.

| Disagree rate (varsayım) | Curator queue (80K pool) | İnsan saat (Faz 4.3 velocity 30/h) |
|---|---:|---:|
| %5 (high agreement) | 4,000 | **133 saat** (~17 iş günü) |
| %7.5 (moderate) | 6,000 | 200 saat (~25 iş günü) |
| %10 (high disagreement) | 8,000 | 267 saat (~34 iş günü) |

**API cost-only kıyas:** Disagree edenler 2x judge çağrısı görmedi (zaten 2 model çalıştı). Curator buffer **insan kaynağı** maliyetidir, API değil.

---

## 7. Önerilen Strateji

### Tier 1: Pilot (Faz 6.1)
- **1,000 satır × Opus + Pro double (text)** = $18.50
- Audit: 100 sample manuel check (Faz 6.2)
- Karar: agreement rate %95+ ise full run; %90-95 ise prompt revize + pilot 2; <%90 ise strateji değişimi

### Tier 2: Full run (Faz 6.3)
- **Bronze 80K × Opus + Pro double (text-only)** = **$1,477**
- ⏱️ Süre: paralel 5-10 worker, ~24-48 saat
- Disagree buffer: ~6,000 curator queue (Faz 7.4 günlük 30-50 hızında 4-6 ay)

### Tier 3: Math-specific (opsiyonel, Faz 5.8)
- **40K math-flagged × hybrid (re-solve+SymPy)** = ~$1,710 add-on
- Math soruları için accuracy %10-15 daha iyi (LiveBench math benchmark)
- ROI: math doğruluğu kritikse uygula

**TOPLAM ÖNERİ:** Tier 1 ($18.50) → Tier 2 ($1,477) → opsiyonel Tier 3 (+$1,710). **Max budget: ~$3,200.**

---

## 8. Hassaslık & Risk

### Sensitivity
- ⚠️ Input token average %20 sapabilir (sözel ders 5x daha uzun option metni)
- ⚠️ Image kullanımı kararı 25-40% maliyet farkı
- ⚠️ Disagree rate %5'ten %15'e çıkarsa curator yükü 3x

### Risk
- **Pricing değişimi:** Provider 6 aylık ortalama %10-20 değişiklik
- **Pool size patlaması:** Curator workflow başlatılırsa `human_verified` artar, Bronze pool küçülür → cost düşer
- **Math judge ROI:** Faz 5.8 prototype audit'i tamamlanmadan tam adoption riskli

---

## 9. Reproducibility

### Sample seçimi
```sql
SELECT id::text, question_text, option_a, option_b, option_c, option_d, option_e,
       correct_answer, question_image_url
FROM question_bank
WHERE is_active = TRUE
  AND quality_review_status = 'unverified'
  AND question_image_url IS NOT NULL
ORDER BY md5(id::text || '42_seed')
LIMIT 20;
```

### Token estimation
```python
def est_tokens(chars: int) -> float:
    return chars / 3.5  # Turkish mixed

input_tokens = est_tokens(q_text + sum(options) + correct_answer) + 250  # prompt overhead
```

### Cost formula
```python
def cost_call(in_tok, out_tok, in_price_M, out_price_M, image_price=0):
    return (in_tok * in_price_M + out_tok * out_price_M) / 1_000_000 + image_price

# Opus + Pro double (text)
opus = cost_call(351, 150, 15, 75)
pro  = cost_call(351, 150, 1.25, 10)
print(f"{opus + pro:.4f}")  # $0.0185 / call
```

### Provider sayfası (her revize öncesi kontrol)
- Anthropic: `https://www.anthropic.com/pricing` (Claude Opus 4.x)
- Google: `https://ai.google.dev/pricing` (Gemini 2.5 Pro)

---

## 10. Sıradaki Adımlar

1. **Bu doc commit** (Faz 5.6 completed mark)
2. **Faz 5.1 (Judge prompt design)** — Opus + Pro prompt'ları yaz, double-check format
3. **Faz 5.2 (Judge prototype)** — 50 satır mock run, latency + agreement ölçü
4. **Faz 6.1 (Pilot 1,000)** — $18.50 risk, audit-driven full run kararı

---

*Faz 5.6 cost projection v1. Pricing güncellenirse v2 revize. Token sample n=20 → revize için n=50-100 önerilir.*
