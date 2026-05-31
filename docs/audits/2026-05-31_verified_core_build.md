# Gerçek-Doğrulanmış Çekirdek İnşası (Verified Core) — 31 May 2026

**Amaç:** Kök-neden raporundaki (K1-K24) **eldeki veriyle çözülebilir** kökleri
(K1a/K1b ölçüm, K5-K8 cevap/A-bias, K12-13 figür, K21 subject) tek workflow'la,
**dairesel olmadan** çöz. Garble (K2) / görsel-eşleşme (K3/K4) re-OCR/re-crop ister → backlog.

## Yöntem — kör çoklu-öznitelik çözüm
5,513 `student_coherent` soru, 221 batch (×25), Workflow `wf_b978142e-064` (24M token, ~70 dk,
≤5 eşzamanlı sıralı dalga). **Yapısal körlük:** solver'a DB cevabı VERİLMEDİ (cevap-anahtarı
ayrı dosyada tutuldu); kıyas Python'da yapıldı → dairesellik tuzağının (K1b) panzehiri.
Her soru: `blind_answer`, `confidence`, `needs_figure`, `true_subject`.

## Sonuç (5,513)
| Bucket | Sayı | % | Kök çözümü |
|---|---|---|---|
| **verified_gold** (blind==DB, conf≥0.7, figürsüz) | **2,734** | %50 | K1a/K1b — bağımsız doğrulanmış güvenilir çekirdek |
| cevap-hatası adayı (yüksek-conf blind≠DB) | 628 | %11 | K5-K8/A-bias — non-dairesel yakalandı → Curator |
| figure_dependent | 98 | %2 | K12/K13 |
| subject_mismatch (true≠DB) | 1,251 | %23 | K21 — yumuşak gözden-geçirme (overwrite YOK) |
| unsolvable (+48 missing) | 884 | %16 | okunabilir ≠ çözülebilir → demote |

**Ders cevap-hatası:** GENEL %18, MATEMATIK %15 (261), KİMYA %15, GEO %11 … BİYO/EDEBİYAT %5.

**Spot-check (kanıt):** GEOMETRİ id'sinde köşeler (2,3)(2,7)(6,3)(6,7) → alan 16 (blind=A, conf 0.97),
DB C=24 → **gerçek cevap-anahtarı hatası** kör solver tarafından DB görülmeden yakalandı.
TARİH/TÜRKÇE adayları tartışmalı/OCR-kesik → Curator'lık. verified_gold örnekleri temiz.

## DB Apply (metadata-only, non-destructive)
Backup `question_bank_verified_core_backup_20260531` (5,513 id+metadata). `correct_answer`/
`status`/`quality_review_status` DOKUNULMADI. Flag'ler:
- `verified_gold=true` (2,734) + `verified_core_run=2026_05_31`
- `blind_answer_dispute={blind,conf}` (628) — cevap değişmez, Curator filtresi
- `blind_needs_figure=true` (98), `blind_true_subject=<ders>` (1,251), `blind_unsolvable=true` (884)

Doğrulama: gold 2734 / dispute 628 / figure 98 / subj 1251 / unsolv 884 / backup 5513 — birebir.

## Bu neyi çözdü (eldeki veriyle)
- **K1a/K1b:** ölçüm artık dairesel değil — kör solver DB'yi görmeden çözdü, sonra kıyaslandı.
- **K5-K8 (A-bias/cevap):** 628 cevap-hatası adayı yakalandı (gerçek hatalar dahil), Curator'a.
- **K12/K13:** 98 figür-bağımlı flag.
- **K21:** 1,251 subject-şüphesi (yumuşak, insan gözden geçirir).
- **Beta için:** 386 → **2,734 gerçek-altın** (cevap-doğrulanmış) çekirdek.

## Backlog (eldeki veriyle ÇÖZÜLEMEZ — infra şart)
- K2 garble → re-OCR + upscale. K3/K4 görsel → re-crop + frontend. K23 chi-square mutasyon + Tier-H → script mühürleme.

## Sonraki
- (Opsiyonel) beta-practice kaynağını `student_coherent` (5,513) → `verified_gold` (2,734) yükselt.
- 628 cevap-hatası Curator review. 1,251 subject-mismatch gözden geçir.
- 884 unsolvable + (gold-dışı) student_coherent → ikinci tur veya re-OCR adayı.

## Artifactlar (untracked)
`backend/scripts/quality/_verify_tmp/`: verify_full.json, answer_key_full.json, full_solve/solve_*.json,
list_*.json (5 bucket), vg_*.csv, apply_verified_core.sql.
