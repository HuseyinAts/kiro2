# KIRO2 DB Comprehensive Audit RESULT

**Tarih:** 15 May 2026 (Session 158)
**Plan:** `docs/superpowers/plans/2026-05-15-db-quality-audit-comprehensive.md`
**Scope:** 187,834 satır, 167,559 aktif, 8 pipeline tier, 3 external data source

## Genel Verdict (rolling, her task tamamlandıkça güncelleniyor)

| Task | Konu | Verdict | Detay |
|---|---|---|---|
| 1 | DB Snapshot | ⚠️ PARTIAL PASS | tier_c_match flag YAZILMAMIŞ (audit trail boşluğu, fonksiyonel OK) |
| 2 | Tier H Pixel | ❌❌ KRITIK FAIL → **ROLLBACK YAPILDI** | KÖK NEDEN: DB qip %92.9 sayfa 0-indexed, disk filename 1-indexed. v1 offset bug → 49,468 rollback. v2 (offset-aware) pilot da %75 yanlış (q_index_in_page Gemini-assigned, deterministic değil). **Tier H konsepti iptal**. Missing %2.51 → %10.13 geri döndü. |
| 3 | Tier G Drift | ⏳ | pending |
| 4 | Tier F Verify | ⏳ | pending |
| 5 | Tier D+E | ⏳ | pending |
| 6 | Cross-Tier Overlap | ⏳ | pending |
| 7 | Broken Links | ⏳ | pending |
| 8 | Schema | ⏳ | pending |
| 9 | JSONL × DB | ⏳ | pending |
| 10 | answers_v8 × DB | ⏳ | pending |
| 11 | Sanity Flags | ⏳ | pending |
| 12 | Case Convention | ⏳ | pending |
| 13 | correct_answer | ⏳ | pending |
| 14 | Duplicate Detect | ⏳ | pending |
| 15 | Book Mapping | ⏳ | pending |
| 16 | Aggregate | ⏳ | pending |

---

## Task 1: DB Integrity Snapshot

**Sonuç:**
- Toplam: 187,834 (aktif 167,559, pasif 20,275), 420 kitap
- Tier dağılımı (aktif image_url'i olanlar):
  - AB_legacy: 59,187 (Tier A+B + Tier C 16,440 dahil çünkü flag YAZILMAMIŞ)
  - H: 49,468 | D: 13,741 | F: 7,441 | E: 4,315 | G: 2,493
  - NULL (image_url yok): 30,914
- has_diagram crosstab: false/VAR=45,711, true/NULL=1,237 (missing %2.51 ✓), true/VAR=48,076
- **Toplam image_url**: 136,645 aktif + 15,767 pasif = 152,412
- **Aritmetik**: 58,514 (pre-S157) + 93,898 (Tier C+D+E+F+G+H) - 50 (delta noise) ≈ 152,412 ✓

**BULGU**: `tier_c_match` flag yazılmamış. Tier C script'i (populate_image_urls_tier_c.py) sadece image_url update ediyor, pipeline_metadata flag yok. Audit trail boşluğu ama fonksiyonel etki yok.

**VERDICT**: ⚠️ PARTIAL PASS. Action item: Tier C için retrospective flag eklenebilir (`SET pipeline_metadata = jsonb_set(..., '{tier_c_match}', ...)` for image_url'i Session 157 timeframe'inden gelen satırlar).


## Task 2: Tier H Pixel Verify — DETAYLI BULGU

### Aşama A: İlk Sample Audit (30 random, Jaccard threshold ≥0.30)
- Sonuç: 11/30 OK, 19/30 low_sim
- **Audit yöntemi YANILTICI**: paragraf-soru kitaplarında DB=sadece soru, OCR=paragraf+soru → Jaccard düşük ama match doğru olabilir

### Aşama B: Substring Overlap (4+ word DB → OCR)
- Sonuç: 11/30 (%37) word match ≥4
- Sample analiz: 5/5 NO_MATCH sample tamamen farklı sorular gösterdi

### Aşama C: Page-Level Invariant (100 sayfa)
- db_max == disk_max: 3/100 (%3) ❌
- **disk_more: 95/100 (DB undercount)** — Gemini Flash sayım yanlış mı?

### Aşama D: min(qip) Dağılımı (24,103 sayfa)
- **min=0: 22,383 (%92.9)** ← DB qip 0-INDEXED!
- min=1: 1,109 (%4.6)
- min≥2: 611 (%2.5)

### Aşama E: Sample 9b58ba21 Pixel Karşılaştırma
- DB: "Bu parçanın anlatımında..." (paragraf-soru formatı, DB=sadece soru)
- OCR: paragraf full text
- → İlk Jaccard yanıltıcı, ama gerçek text farklı sorular

### Aşama F: ROLLBACK (49,468 satır)
- image_url=NULL set
- tier_h_match → tier_h_rollback flag
- Backup TSV: `_pilots/20260515_tier_h_pre_rollback_backup.tsv`

### Aşama G: v2 Pilot (offset-aware, qip+offset)
- Offset hist: +1:12675, 0:3332, -1:1584 (offset değişken)
- 25 sample manuel doğrulama: 5/25 OK, 18/25 FARKLI sorular
- **q_index_in_page güvenilir mapping field değil** (Gemini-assigned, sayım yanlış)

### Karar
- Tier H konsepti **iptal**
- v2 apply YAPILMADI
- Plan v1 hedef revize: pipeline-fix bound = **%10 missing**, <%5 için Re-OCR + Curator
- Critical lesson: q_index_in_page tabanlı mapping güvenilir değil

