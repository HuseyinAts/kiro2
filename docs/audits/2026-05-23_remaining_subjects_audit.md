# DB Kalan 6 Subject Cevap Anahtarı Audit (S188-S193)

**Tarih:** 2026-05-23
**Methodology:** LLM-only batch (6 paralel)
**Kapsam:** TARIH + GENEL + BIYOLOJI + SOSYAL + COGRAFYA + FEN = 2,194 soru
**Status:** ✅ COMPLETE — 453 UPDATE applied

---

## Per-Subject Sonuçlar

| Subject | Total | LLM batch | Wrong | Garbage | UPDATE | Problematic % |
|---|---|---|---|---|---|---|
| **TARIH (S188)** | 659 | 592 | 104 | 105 | 209 | **%31.7** ⚠️ |
| **GENEL (S189)** | 521 | 189 | 15 | 36 | 51 | %9.8 |
| **BIYOLOJI (S190)** | 469 | 400 | 45 | 66 | 111 | %23.7 |
| **SOSYAL (S191)** | 427 | 412 | 19 | 24 | 43 | %10.1 |
| **COGRAFYA (S192)** | 95 | 91 | 8 | 25 | 33 | **%34.7** ⚠️ |
| **FEN (S193)** | 23 | 21 | 5 | 1 | 6 | %26.1 |
| **TOPLAM** | **2,194** | **1,705** | **196** | **257** | **453** | **%20.6** |

**TARIH ve COGRAFYA en yüksek problematic** (%31.7, %34.7). Tarih sorularında muhtemelen Phase 7 prompt OCR-broken metinleri tutmuş; coğrafya küçük örnek (95 q) ama %35 oranı dramatik.

---

## Batch IDs

| Subject | Batch |
|---|---|
| TARIH | `batches/nf6vqt2c9ioyrcatfujqk4qkuyinazfrprjv` |
| GENEL | `batches/rvhhungl89ky8jiamhmop65cdeprdli4ukut` |
| BIYOLOJI | `batches/246c0kg56biiladu9rs1cggz83ux5u8nht2f` |
| SOSYAL | `batches/n8xewyn3rzbchns6gkusqowgaozgvvslhiuo` |
| COGRAFYA | `batches/c96xygmssob4t437b9z9guxuqufeciregnjm` |
| FEN | `batches/wi3l4ux8mqzv00um6blkpdyj4an3z8byrbr7` |

Toplam maliyet: ~$1 (6 paralel batch)

---

## Apply Execution

Tek-shot bulk Python (6 subject × triage + backup + UPDATE) — single transaction per subject.

```
TARIH:    104 pending + 105 rejected ✅ (backup question_bank_tarih_audit_backup_20260523)
GENEL:     15 pending +  36 rejected ✅
BIYOLOJI:  45 pending +  66 rejected ✅
SOSYAL:    19 pending +  24 rejected ✅
COGRAFYA:   8 pending +  25 rejected ✅
FEN:        5 pending +   1 rejected ✅
TOTAL:    196 pending + 257 rejected = 453 UPDATE
```

Gold pool: 13,227 → **12,774** (-453)

---

## 12-Subject Birleşik Final (S182-S193)

| Subject | Total | UPDATE | Prob % |
|---|---|---|---|
| MAT (S182) | 4,899 | 588 | %12.0 |
| GEO (S183) | 2,306 | 248 | %10.7 |
| FIZ (S184) | 1,601 | 339 | %21.2 |
| KIM (S185) | 1,133 | 248 | %21.9 |
| TUR (S186) | 2,415 | 494 | %20.5 |
| EDE (S187) | 773 | 177 | %22.9 |
| TAR (S188) | 659 | 209 | %31.7 |
| GEN (S189) | 521 | 51 | %9.8 |
| BIO (S190) | 469 | 111 | %23.7 |
| SOS (S191) | 427 | 43 | %10.1 |
| COG (S192) | 95 | 33 | %34.7 |
| FEN (S193) | 23 | 6 | %26.1 |
| **TOTAL** | **15,321** | **2,547** | **%16.6 avg** |

**Gold pool: 15,321 → 12,774 (-2,547 = -%16.6)**
**Pending: 905 (curator review)**
**Rejected: 1,642 (garbage downgrade)**

---

## Kategoriler

### Düşük problematik (formula-friendly, kavram olmayan)
- GENEL %9.8 (genel kültür, basit yapı)
- SOSYAL %10.1 (politik/ekonomi)
- GEO %10.7 (sayısal geometri)
- MAT %12.0 (aritmetik+denklem)

### Orta problematik (mixed)
- FIZ %21.2
- TUR %20.5
- KIM %21.9
- EDE %22.9
- BIO %23.7
- FEN %26.1

### Yüksek problematik ⚠️
- **TAR %31.7** (OCR-broken tarih metinleri)
- **COG %34.7** (küçük örnek ama dramatik)

**Pattern doğrulandı:** OCR'a bağımlı concept-heavy subjects (tarih, coğrafya, fizik, kimya, edebiyat) yüksek problematic. Sayısal/yapısal subjects (mat, geo, sosyal, genel) daha temiz.

---

## Sonraki Adımlar

1. ✅ S188-S193 commit + push
2. ⏳ Curator UI'de **905 pending review** (S182-S193 toplam)
3. ⏳ **A bias root cause** — 12 subject'te doğrulandı, pipeline scan kritik
4. ⏳ Phase 7 prompt iyileştirme — concept-based subjects için
5. ⏳ Re-OCR planı — TAR + COG yüksek garbage oranı, OCR re-run değerli
