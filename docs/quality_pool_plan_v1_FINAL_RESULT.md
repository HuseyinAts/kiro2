# Quality Pool Plan v1 — Final RESULT (Session 158 Closeout)

**Tarih:** 15 May 2026
**Status:** Faz 1 pipeline-fix **MATEMATIK BOUND**'a ulaşıldı, hedef <%5 SAĞLANMADI
**Sonraki:** Re-OCR (Faz 1.10) + Curator (Faz 3) ile <%5 ulaşılabilir

## TL;DR — DB Final Durumu

| Metrik | Pre-Session-158 | Post-Session-158 | Δ |
|---|---|---|---|
| Aktif image_url | 58,514 | **87,177** | **+28,663** |
| Coverage | %35.3 | **%52.03** | **+%16.7** |
| has_diagram=true missing | 49,313 (%100) | **4,994** | -44,319 |
| **missing %** | **%100** | **%10.13** | **-%89.87** |

**Plan v1 hedef <%5: ❌ SAĞLANMADI** (pipeline-fix matematik bound = %10).
**Beklenen yol**: Re-OCR + Curator + Judge (Fazlar 1.10, 3, 5) ile <%5 ulaşılabilir.

## Tier Bazlı Final Tablo

| Tier | Strateji | Match | Status | Audit verdict |
|---|---|---|---|---|
| A+B (legacy) | v3 + ocr_crops | 59,187 | ✓ (S<157) | not audited |
| C | exact_match disk filename | 16,440 | ✓ kalıcı (S157) | not audited, flag YAZILMAMIŞ |
| D | (book,page,q_no) + sim>=0.70 | 13,741 | ✓ kalıcı | %96 pilot |
| E | q_no orphan recovery (trailing dot strip) | 4,315 | ✓ kalıcı | uniform 0.70 |
| F | asymmetric key+sim>=0.50 | 7,441 | ✓ kalıcı | **%100 (50 sample audit)** |
| G | combined deep recovery (G1+G2+G3) | 2,493 | ✓ kalıcı | **G1 %90 (LaTeX noise), G2/G3 %100** |
| **H** | **q_index_in_page filename pattern** | **❌ 0 (rollback)** | **iptal** | **%25 audit, 49,468 satır ROLLBACK** |

**Net pipeline-fix katkı (Tier C+D+E+F+G)**: 44,430 satır + Tier A/B legacy = 87,177 aktif image_url.

## Faz 1 Görev Status

| # | Faz | Status | Detay |
|---|---|---|---|
| 1.1 | Tier C image matcher | ✅ S157 (16,440) | flag yazılmamış (audit trail gap) |
| 1.2 | Tier D image matcher | ✅ S158 (+13,741) | pilot %96 |
| 1.3 | OCR text validator | ✅ S158 (64 flag) | defansif, no UPDATE |
| 1.4 | Sanity checker | ✅ S158 (612 flag) | defansif, no UPDATE |
| 1.5 | Post-fix audit | ✅ S158 | %30 missing baseline (Tier F+G+H öncesi) |
| 1.5+ | Tier F asymmetric | ✅ S158 (+7,441) | **post-audit %100** |
| 1.5++ | Tier G combined deep | ✅ S158 (+2,493) | **post-audit %90-100** |
| 1.5+++ | Tier H q_index_in_page | ❌ S158 ROLLBACK | qip bug, iptal |
| 1.6 | Bronze migration | ⏳ Pending | quality_review_status='bronze_clean' enum |
| 1.7 | q_no orphan recovery | ✅ S158 (+4,315) | uniform 0.70 |
| 1.8 | SymPy symbolic verifier | ⏳ Pending | math template false-pos için |
| 1.9 | Book key cross-reference | ✅ S157 (16,159 flag) | A1 defansif |
| 1.10 | Re-OCR (Gemini Pro) | ⏳ Pending | kalan 4,994 has_diagram missing |

**Faz 1 completion**: 10/13 (%77). Kalan 3 görev (1.6, 1.8, 1.10) ayrı session.

## Tier H Bug — Detaylı Kök Neden

### Bulgu
- `pipeline_metadata.ai_extras.q_index_in_page` field Gemini Flash batch v4.14e tarafından atanmış
- %92.9 sayfa **0-indexed** (min(qip)=0), disk filename **1-indexed** (`_p0001_q01.png` başlangıç)
- Tier H `qip → q<qip:02d>.png` direct match yaptı → **1 offset bug**, 49,468 satırın ~%75'i yanlış crop'a bağlandı

### v2 (offset-aware) de başarısız
- min(qip)'e göre offset hesaplandı (page bazlı)
- Pilot 25 sample: 5 OK, 18 farklı sorular → q_index_in_page deterministic mapping field DEĞİL
- v2 apply YAPILMADI

### Tier H konsepti İPTAL
- q_index_in_page tabanlı mapping güvenilir değil
- Gelecek pipeline-fix script'leri **çift sinyal** (key match + text similarity) kullanmalı

## Diğer Tier'ların Doğruluğu — Audit Tier H bug'ından sonra

| Tier | Sinyal yapısı | Sample audit | Verdict |
|---|---|---|---|
| C | Single (filename exact) | not audited | Risk düşük (deterministic) |
| D | Double (key+sim>=0.70) | %96 pilot | ✓ güvenli |
| E | Double (key+sim>=0.70 or exact) | uniform | ✓ güvenli |
| F | Double (key+sim>=0.50) | %100 (50 sample) | ✓ güvenli |
| G1 | Double (key+sim>=0.40) | %90 (LaTeX noise) | ✓ güvenli |
| G2/G3 | Double (page-best+sim>=0.55) | %100 | ✓ güvenli |
| H | **Single (filename pattern only)** | **%25** | **❌ iptal** |

**Lesson learned**: Tek-sinyal mapping (yalnız filename pattern, text validation yok) **fundamental hata**. Tüm pipeline-fix script'leri **çift sinyal** kullanmalı.

## Pipeline-Fix Matematik Sınırı

Kalan **4,994 has_diagram=true missing** dağılımı:
- sim<0.50 bucket: 5,021 (önceki Tier F öncesi)
- no_key_match: 1,367
- no_qno: 977
- no_page_ocr: 11

Bu satırlar için **OCR text yok veya çok bozuk**, ya da **disk crop yok**. Pipeline-fix script'leri ile yakalanamaz.

### <%5 hedef için yol

1. **Faz 1.10 Re-OCR (Gemini Pro)** — tahmini ~1,500-3,000 satır kurtarılır → missing **~%4-6**
2. **Faz 3 Curator UI** — kalan ~2,000 satır manuel review → missing **<%3**
3. **Faz 5/6 Judge** — düşük-conf flag'li (sim 0.40-0.60) satırları doğrula → kalite artar

## Audit Framework — Reusable Pattern

Bu session'da yaratılan audit tooling gelecekte template:
- `audit_task01_db_snapshot.sql` — DB integrity baseline
- `audit_task02_tier_h_verify.py` — Jaccard + invariant test
- `audit_task02b_tier_h_substring.py` — substring overlap (paragraf-soru durumu için)
- `audit_task03_tier_g_substring.py` — Tier G sub-tier audit
- `audit_task04_tier_f_substring.py` — Tier F audit
- `audit_min_qip.sql` — Page-level invariant detection

**Reusable pattern**: Her yeni tier apply ÖNCESI, sample 30-50 + substring overlap audit ZORUNLU.

## Plan v1 Revize — Sonraki Sessions için

### Kısa vade (1-2 session)
- Faz 1.10 Re-OCR (Gemini Pro, ~$15 maliyet, ~4,994 satır işle)
- Faz 1.6 Bronze tier migration (`quality_review_status='bronze_clean'` enum)

### Orta vade (3-5 session)
- Faz 3 Curator UI (admin/labs, React sayfa + endpoint)
- Faz 2 Audit harness (haftalık 30 sample tracking)

### Uzun vade
- Faz 5/6 Judge calibration + full run
- Faz 7 Beta soft launch + feedback loop

## Karpathy Lesson

Bu session 3 büyük disiplin dersi verdi:

1. **Sample doğrulama**: filename pattern + text karşılaştırma çift gerekli. Tier H'te text atlandı, sonuç felaket.
2. **Gemini-assigned field güvensiz**: deterministic varsayma. q_index_in_page bunun klasik örneği.
3. **Audit framework çalıştı**: production'a yanlış veri yansımadan rollback yapıldı. **Audit zorunlu**, not optional.

> "Önce Düşün, Sonra Kodla — Cerrahi Müdahale — Hedef Odaklı Yürütme"

Tier H bu prensiplere atıfla yapıldı ama uygulanmadı. Audit dürüstçe başarısızlığı raporladı, rollback ile düzeltildi.

---

*Final RESULT: 15 May 2026 Session 158 closeout.*
*Audit RESULT: `backend/_pilots/20260515_DB_COMPREHENSIVE_AUDIT_RESULT.md`*
