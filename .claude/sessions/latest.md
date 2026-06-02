## Session Handoff — 2026-06-02 (akşam)
**Branch:** master | **Son commit:** `556ee05e6` | **Push:** EDİLMEDİ (7 commit master'da bekliyor)
**Uncommitted:** sadece bu handoff (temp script'ler gitignore'da, diskte)

### Yapılanlar — İçerik kalite çarkı (Gemini'siz, Claude-Workflow kör-solve)
"Elimdeki veriyi analiz et + beyin fırtınası" → seçenek 1 (içerik çarkı). 9 Workflow, ~28M token, 7 commit.

- **L1 (`5c2599f0`):** 997 student_coherent aday kör-solve → AGREE 420→**beta promote** / UNSOLVABLE 193→flag / DISAGREE 334→dispute. Pilot %59.6 + spot 15/15. Beta 2,689→3,109.
- **L1d (`ebbf0a8e`):** 334 dispute → 2. bağımsız kör-solve (628-deseni). FALSE_DISPUTE 55→beta / REAL_ERROR 143 (2-sinyal DB hatası) / UNSOLVABLE 57 / SPLIT 39. Beta 3,109→3,164.
- **L1d-3 (`810227d3`):** 143 REAL_ERROR'ın MAT+GEO=30 → 3. kör-solve → **25 correct_answer DÜZELTİLDİ** (3-sinyal + elle 4/4 teyit).
- **Retry (`3696e0f2`):** ertelenen 90→30 çözüldü, +5 beta. 60 kalıcı erteleme.
- **Curator (`556ee05e`):** 123 concept REAL_ERROR → `pending` + `dispute_suggestion`. Worklist: `backend/scripts/quality/_l1_curator_tmp/curator_worklist_123_FULL.csv` (tam şıklar, Excel/UTF-8 BOM, `karar_accept_reject` kolonu boş).

**SONUÇ: beta 2,689→3,169 (+480, +%17.9) + 25 DB hatası düzeltildi + 123 curator'a.** correct_answer sadece 25'te değişti (hepsi 3-sinyal+elle). 7 backup tablo (`question_bank_l1*_20260602`).

### State
- Beta (verified_provisional): **3,169** | DB PG 5434 sağlıklı | correct_answer integrity: tüm apply'larda fark=0
- 7 backup tablo rollback hazır

### Fail Eden Testler
- YOK (DB-only iş, kod değişmedi). Spot-check elle 4/4 + 15/15 pilot.

### Engelleyiciler / Workflow dersleri (KRİTİK — MEMORY'de)
- **Workflow 16+ eşzamanlı agent → 529 rate-limit → 0 token.** Çözüm: sıralı dalga ≤6 (`for`+`await parallel(chunk)`).
- **Workflow `schema`/StructuredOutput bu harness'ta güvenilmez** (15/15 fail). Çözüm: schema YOK → düz JSON text → workflow JS'inde `JSON.parse`.
- Gemini'siz havuz ~997 ile TÜKENDİ; 60 soru workflow-dirençli.

### Sonraki Adımlar (maks 5)
1. **Hüseyin: 123 curator worklist** doldur (accept/reject) → toplu apply VEYA /admin/curator (frontend rebuild gerek).
2. **60 kalıcı-ertelenen** → manuel/curator.
3. **Gemini key rotate → 61K garble re-OCR** — en büyük kilit, hâlâ bloke (AUP).
4. `git push` (7 commit bekliyor).
5. Beta gerçek-öğrenci sürüyor — yeni flag → A1 + L1 pattern tekrarla.

### Kararlar
- Çok-sinyalli kör-solve: 1=provisional / 2=dispute sınıf / 3+insan=kalıcı düzeltme. Dairesellik panzehiri.
- 2-sinyal-yanlış soru gold'da kalmaz (628 deseni: auto_judged_high→pending).
- Tüm DB değişikliği non-destructive: metadata flag + backup; correct_answer sadece 3-sinyal+elle (25).
