# Pool Categorization Decision

**Tarih:** 14 May 2026 (Faz 0.7, Session 156)
**Input data:** Faz 0.2 audit (110 sample) + Faz 0.9 audit (Bayesian precision %26)
**Karar:** legacy_v3_unaudited (18,397) + unverified_with_image (38,492) için tier ataması

---

## Mevcut Pool Dağılımı (live DB)

```
question_bank (167,559 aktif):
├─ unverified              146,387
│  ├─ v4.14e Gemini Flash   107,516 (no Bayesian, no image)
│  ├─ +book_key+image        38,477 ← BU KARAR (Faz 0.7 hedefi)
│  └─ +crossval+image            15
├─ legacy_v3_unaudited      18,397 ← BU KARAR (Faz 0.7 hedefi)
└─ pending                    2,775

Toplam karar verilecek: 56,874 satır
```

---

## Karar Çerçevesi

Her satır 4 yola düşer:

| Yol | Status | Açıklama |
|---|---|---|
| **A) Bronze candidate** | `unverified` (or new `bronze_clean`) | Pipeline-fix uygulanmış, judge eligible |
| **B) Direct reject** | `rejected` | Audit verisi yetersiz/zayıf gösteriyor, judge cost'u boşa |
| **C) Hold for inspection** | `pending` | Ek araştırma gerekli |
| **D) Sapphire fast-track** | `human_verified` | Tek tek manuel onay (small batch) |

---

## Subset 1: unverified_with_image (38,492 satır)

### Source breakdown

| Source | n | % |
|---|---|---|
| **page_inline + image** | 38,477 | %99.96 |
| crossval + image | 15 | %0.04 |

→ **Esasen tek tip pool: book key match + image var.**

### Audit sinyali (Faz 0.9)

`page_inline` source: precision %40 (n=5 sample) — non-judge sources arasında en iyi

### Karar

✅ **A) Bronze candidate (38,477 satır) → judge eligible**

**Sebep:** Book key match + image = en iyi pre-judge sinyal. Audit %40 pass = significant Gold conversion potansiyeli.

**Beklenen outcome:** ~15,000-18,000 Gold tier (judge ≥%40 pass)

---

## Subset 2: legacy_v3_unaudited (18,397 satır)

### Source breakdown

| Source | n | % | Audit sinyali (Faz 0.9) | Karar |
|---|---|---|---|---|
| **B_bayesian_upgrade** | 9,834 | 53.5% | %11 pass (n=18) | ❌ **REJECT** |
| **A_book_key_only** (page_inline) | 2,624 | 14.3% | %40 pass (n=5) | ✅ **Bronze** |
| Z_other_or_null | 2,160 | 11.7% | Bilinmiyor | ⏸ Hold (pending) |
| E_legacy_v11 (jsonl_v11) | 1,131 | 6.1% | %0 pass (n=2) | ❌ **REJECT** |
| D_ai_solved (Opus/etc) | 1,062 | 5.8% | %0 pass (n=1) → küçük sample | ✅ **Bronze** (cautious) |
| C_crossval | 979 | 5.3% | %50 pass (n=2) | ✅ **Bronze** |
| F_ai_crop (Qwen) | 607 | 3.3% | %50 pass (n=2) | ✅ **Bronze** |

### Karar — sub-strategy

**B (Bayesian upgrade) → REJECT (`rejected` status):**
- 9,834 satır
- Audit kanıtı: %11 pass (n=18 anlamlı)
- Judge'a göndermek %89 wasted call
- Cost saving: ~$30-50

**A (Book key) → Bronze candidate (`unverified` korunur):**
- 2,624 satır
- Aynı subset 1'le aynı stratejide

**E (jsonl_v11) → REJECT:**
- 1,131 satır
- Audit %0 (n=2, küçük ama sinyal kötü)
- Defensively reject (cost saving $5-10)

**D, C, F → Bronze candidate:**
- 2,648 satır toplam
- Sample küçük ama signal mixed (%0-%50)
- Judge'a gönder, sonuca göre re-evaluate

**Z (other_or_null) → Hold:**
- 2,160 satır
- Source kayıt eksik = bilinmeyen kalite
- Pending status'a tut, daha derin analiz Faz 1'de

### Tier dağılımı (legacy_v3 için)

| Karar | n | % |
|---|---|---|
| ✅ Bronze candidate (judge eligible) | 5,272 | 28.7% |
| ❌ Reject (cost save) | 10,965 | 59.6% |
| ⏸ Hold pending inspection | 2,160 | 11.7% |

---

## Subset 3: v4.14e Gemini Flash (107,516, kapsam dışı ama referans)

**Mevcut karar (Plan v1):** Bronze candidate → judge

Bu subset Faz 0.7 kapsamı dışı (zaten Plan v1'de net), ama referans için:
- All have ai_extras (has_diagram, topic_match_quality, etc.)
- No Bayesian, no confidence
- C2 audit: %30 raw pass

→ Aynen Plan v1'deki yola devam. Judge'a gönder, ~%30 → ~32K Gold candidate.

---

## Konsolide Karar Tablosu

| Subset | n | Karar | Yeni status | Beklenen Gold |
|---|---|---|---|---|
| unverified+book_key+image | 38,477 | Bronze candidate | unverified (judge için hazır) | ~15K (40%) |
| legacy_v3 book_key | 2,624 | Bronze candidate | unverified (status güncellemesi) | ~1K (40%) |
| legacy_v3 D/C/F | 2,648 | Bronze candidate | unverified (status güncellemesi) | ~500-1K (mixed) |
| legacy_v3 Z (null) | 2,160 | Hold | pending | TBD |
| legacy_v3 B (bayesian) | 9,834 | REJECT | rejected | 0 |
| legacy_v3 E (v11) | 1,131 | REJECT | rejected | 0 |
| **TOPLAM** | **56,874** | mix | — | **~16-17K Gold** |

**Cost saving (rejected: 10,965):** judge $30-50 tasarruf
**Hold (pending: 2,160):** Faz 1 sonrası tekrar değerlendirme

---

## Migration SQL (önerilen, Convention v3 ile birlikte)

```sql
BEGIN;

-- legacy_v3 → unverified migration (Bronze candidate olanlar)
UPDATE question_bank
SET quality_review_status = 'unverified', updated_at = NOW()
WHERE quality_review_status = 'legacy_v3_unaudited'
  AND pipeline_metadata::jsonb ->> 'answer_source' IN ('page_inline', 'ai_solved_claude_opus')
  AND pipeline_metadata::jsonb ->> 'answer_source' NOT LIKE 'ai_upgrade_bayes_%';
-- Beklenen: ~5,272 satır

-- legacy_v3 Bayesian → rejected
UPDATE question_bank
SET quality_review_status = 'rejected', updated_at = NOW()
WHERE quality_review_status = 'legacy_v3_unaudited'
  AND pipeline_metadata::jsonb ->> 'answer_source' LIKE 'ai_upgrade_bayes_%';
-- Beklenen: ~9,834 satır

-- legacy_v3 jsonl_v11 → rejected
UPDATE question_bank
SET quality_review_status = 'rejected', updated_at = NOW()
WHERE quality_review_status = 'legacy_v3_unaudited'
  AND pipeline_metadata::jsonb ->> 'answer_source' = 'jsonl_v11';
-- Beklenen: ~1,131 satır

-- legacy_v3 other/null → pending (hold)
UPDATE question_bank
SET quality_review_status = 'pending', updated_at = NOW()
WHERE quality_review_status = 'legacy_v3_unaudited';
-- Beklenen: ~2,160 satır (kalanlar)

-- Sonuç sayım
SELECT quality_review_status, COUNT(*)
FROM question_bank
WHERE is_active = TRUE
GROUP BY quality_review_status;

COMMIT;
```

**Önkoşul:** Convention v3 (Faz 0.6) `rejected` status'unu CHECK constraint'e eklemiş olmalı.

---

## Plan v1 Üzerindeki Etkiler

### Faz 6.1 Judge Pilot — Pool Stratifikasyon Güncel

**Önceki:** 1,000 random sample (700 v4.14e + 300 legacy_v3)
**Yeni:**
- 700 v4.14e Gemini Flash
- 200 unverified+book_key+image (en yüksek pass beklenen)
- 100 legacy_v3 Bronze candidate

### Faz 6.3 Judge Full Run — Kapsam Daraldı

**Önceki:** Bronze ~80K
**Yeni:** Judge eligible = 107,516 + 38,477 + 5,272 = **151,265** satır
**Cost (revize):** $600-1,000 → orijinal tahminin biraz üstünde ama rejected pool sayesinde ~$30-50 tasarruf

### Yeni Migration: Faz 1.6.5 (önerilen)

Plan v1'e ek task: **Faz 1.6.5 — legacy_v3 source-based migration**

Convention v3 deploy sonrasi, Faz 1.6 (Bronze tier) ile birlikte yapılabilir. ~12K satır status değişikliği (~10K reject + 2K pending).

---

## Riskler

| Risk | Mitigasyon |
|---|---|
| Bayesian-rejected pool'da gerçek Gold candidate var | %11 precision audit n=18, küçük ama anlamlı; %95 CI: %3-25 → kaybedilen ~%10 (1K satır) — kabul edilebilir |
| Z (null source) hold bekleyen güncellenmez | Faz 5 sonrası audit, görüldüğü gibi reject veya judge |
| Migration geri alınamaz | rejected → unverified kolay revert; backup zaten var (Faz 0.4 pg_dump) |

---

## Sıradaki adım

1. ✅ Faz 0.7 tamamlandı (karar dokümanı yazıldı)
2. Migration SQL Convention v3 (Faz 0.6) ile birlikte deploy edilir
3. Sonraki: **Faz 0.6 Convention v3 doc** (4-6 saat) — son Faz 0 görevi
4. Veya: doğrudan Faz 1.x sprint'lere geç (Tier C image matcher, vs)

---

*Generated by Faz 0.7. Audit-driven decisions; ~10,965 satır rejected (cost save), 56K toplam karar verildi.*
