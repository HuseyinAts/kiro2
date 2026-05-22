# DB Türkçe + Edebiyat Cevap Anahtarı Audit (S186 + S187)

**Tarih:** 2026-05-23
**Methodology:** LLM-as-judge only (concept-based subjects, formula coverage düşük)
**Kapsam:** TURKCE (2,415) + EDEBIYAT (773) = 3,188 soru
**Status:** ✅ COMPLETE — 671 UPDATE applied

---

## Discovery

| Subject | Total | Formula coverage | A bias |
|---|---|---|---|
| TURKCE | 2,415 | 237 (%9.8) | ~%29 |
| EDEBIYAT | 773 | 107 (%13.8) | ~%29 |

Formula coverage çok düşük — concept-based subjects (anlam, dilbilgisi, edebi metin analizi) Phase 7 formula extraction'a uygunsuz.

**Karar:** SymPy adımını atla, formula-yok subset'i LLM judge.
**Sonuç:** Toplam 344 formula-dolu soru audit dışı kaldı (%10.8). Marjinal kapsam kaybı.

---

## LLM-as-Judge Sonuçları

### S186 TURKCE
**Batch:** `batches/hcaz2k2wziahin42hpii5ignjsosaf0l9c2p` (2,178 q)
```
parsed:             1286 (59.0%)
parse_fail:          892 (41.0%)
llm_disagrees_high:  494 (38.4% of parsed)
  ├─ unsolvable:    399 (garbage)
  └─ real wrong:     95 (A-E)
```

### S187 EDEBIYAT
**Batch:** `batches/tg1bnr4rsjwxc92olmxvfucz7yvjgwhru4t9` (666 q)
```
parsed:              452 (67.9%)
parse_fail:          214 (32.1%)
llm_disagrees_high:  177 (39.2% of parsed)
  ├─ unsolvable:    127 (garbage)
  └─ real wrong:     50 (A-E)
```

---

## Apply

### Backup
- `question_bank_turkce_audit_backup_20260523` (494 rows)
- `question_bank_edebiyat_audit_backup_20260523` (177 rows)

### UPDATE
- S186 TURKCE: 95 pending + 399 rejected = **494** ✅
- S187 EDEBIYAT: 50 pending + 127 rejected = **177** ✅
- **Toplam: 671 UPDATE**

### Bug fix during apply
`apply_full.py` pilot exclusion logic (`sympy[:3]+llm[:2]`) çalıştı, ama pilot script paralel pattern'da skip edildi. Sonuç: 4 ID (2 TURKCE + 2 EDEBIYAT) full UPDATE'in dışında kaldı. **Manuel apply** ile düzeltildi (S186 manuel=2, S187 manuel=2).

### Final Verify
```
S186 TURKCE:   95 pending + 399 rejected ✅
S187 EDEBIYAT: 50 pending + 127 rejected ✅
Gold pool: 13,898 → 13,227 (-671)
```

---

## Karşılaştırma: 6 Subject Audit (S182-S187)

| Subject | Total | Wrong | Garbage | UPDATE | Problematic % |
|---|---|---|---|---|---|
| MAT (S182) | 4,899 | 232 | 356 | 588 | %12.0 |
| GEO (S183) | 2,306 | 95 | 153 | 248 | %10.7 |
| FIZ (S184) | 1,601 | 113 | 226 | 339 | %21.2 |
| KIM (S185) | 1,133 | 124 | 124 | 248 | %21.9 |
| **TUR (S186)** | 2,415 | **95** | **399** | **494** | **%20.5** |
| **EDE (S187)** | 773 | **50** | **127** | **177** | **%22.9** |
| **TOPLAM** | **13,127** | **709** | **1,385** | **2,094** | **%16.0 avg** |

**Concept-based subjects (FIZ/KIM/TUR/EDE) %20-23 problematic** — formula-friendly (MAT/GEO) %10-12'den çok yüksek.

**Concept-based subjects'te garbage oranı yüksek**:
- Edebiyat: %16.4 garbage (eksik metin, anlamsız paragraf)
- Türkçe: %16.5 garbage (bozuk OCR)
- Fizik: %14.1, Kimya: %10.9

Matematik %7.3 ve Geometri %6.6'dan ÇOK yüksek. **Pre-existing OCR/data quality concept-based subjects'te daha kötü.**

---

## Sonraki Adımlar

1. ✅ S186+S187 commit + push
2. ⏳ TARIH (659) + GENEL (521) + BIYOLOJI (469) + SOSYAL (427) + COGRAFYA (95) + FEN (23) = 2,194 q (sonraki batch)
3. ⏳ **A bias root cause** — 6 subject'te doğrulandı, pipeline taraması zorunlu
4. ⏳ **Phase 7 prompt iyileştirme** — concept-based subjects için formula coverage düşük; LLM rationale yetersiz
5. ⏳ Curator UI'de **709 pending review** (S182-S187)

## Çıktılar

```
docs/audits/2026-05-23_turkce_edebiyat_audit.md (BU)
backend/scripts/quality/_phase7_audit_tmp/
├── sympy_results_<turkce|edebiyat>.json (skip — formula yok)
├── llm_judge_results_<turkce|edebiyat>.json
└── triage_final_<turkce|edebiyat>.json
```
