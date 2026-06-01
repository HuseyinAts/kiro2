# 148 Math/Geo REAL_ERROR — correct_answer Düzeltme (3-sinyal)

**Tarih:** 2026-06-01
**Amaç:** 628-dispute çözümünde (`2026-06-01_dispute_blind_resolution.md`) REAL_ERROR
işaretlenen 480 sorudan MATEMATIK+GEOMETRI conf≥0.9 = **148'inde** `correct_answer`'ı,
**3 bağımsız kör sinyal** hizalanırsa düzelt. Bunlar deterministik çözülebilir →
en yüksek kesinlik.

## 3-sinyal konsensüs
- **Sinyal 1:** orig_blind (verified_core, 31 May)
- **Sinyal 2:** new_blind (628-dispute workflow, 1 Haz) — bu ikisi hizalandığı için REAL_ERROR
- **Sinyal 3:** 3. kör solve (Workflow `wf_e92ab0c7-373`, 6 batch, 148/148, ~1 dk, 627K token)
  Solver'a DB cevabı + önceki blind VERİLMEDİ (blind-safe).
- **Kural:** verify3 == blind (3/3) → `correct_answer = blind`; aksi → curator.

## Sonuç (148)
| | Sayı | Aksiyon |
|---|---|---|
| **CONFIRMED (3/3)** | **143** | `correct_answer = blind`, status=auto_judged_high, metadata `answer_corrected_3signal` |
| UNCERTAIN | 5 | 3'ü verify3="?" (cevap şıkta yok=OCR-garble), 2'si gerçek anlaşmazlık → pending/curator, correct_answer DOKUNULMADI |

143/148 = **%96.6 triple-hizalanma** — gate çalıştı (garble/şüpheli 5'i otomatik ayırdı).

## Spot-check (DB post-apply doğrulama)
- `0146d685`: C(260, imkansız) → **A(220)** ✓
- `10ae092e`: B → **D(75°)** ✓
- `7bef98ad`: C → **A(180°)** ✓

## DB Apply
Backup `question_bank_v148_correct_backup_20260601` (148 satır, **correct_answer DAHİL** — bu kez değişti).
- 143: correct_answer düzeltildi + auto_judged_high + `answer_corrected_3signal`/`answer_corrected_run=2026_06_01`
- 5: `verify3_disagree=true`, correct_answer dokunulmadı, pending

**Dairesellik önleme:** düzeltilenler `verified_provisional` (beta gold) yapılMADI — çünkü
correct_answer=blind yaptıktan sonra "blind==db" trivial olurdu (K1b). auto_judged_high'da kaldılar.

## Çözdü
K5-K8 — 143 kanıtlı-yanlış cevap düzeltildi (3 bağımsız kör sinyal + 3/3 spot-check).
Bunlar artık doğru cevaplı, kullanılabilir.

## Kalan
- 332 real_error (concept/düşük-conf) → curator manual (blind öneri ile)
- 5 uncertain + 30 split + 47 unsolv → curator/demote
- 1,251 subject_mismatch → K21 relabel (ucuz)

## Artifactlar (untracked)
`_beta_core_tmp/`: v148_solve_input.jsonl, v148_key.jsonl, v148_batches/, v148_third_solve.json,
consensus_apply_148.py, apply_148.sql. Workflow: `wf_e92ab0c7-373`.

---

## EK: 2. Tur — 135 MAT+GEO (conf<0.9) — 1 Haz 2026

148'in (conf≥0.9) ardından kalan **135 MAT+GEO real_error** (conf 0.78-0.82) aynı
3-sinyal pipeline'ıyla (Workflow `wf_28e051c2-4be`, 135/135). **Flip-flop önleme:**
148'de zaten `verify3_disagree` olan 5 id CONFIRMED'den HARİÇ tutuldu (curator'da kaldı).

| | Sayı |
|---|---|
| CONFIRMED (3/3 → correct_answer) | **127** |
| UNCERTAIN → curator | 3 |
| EXCLUDED (prev-disagree) | 5 |

127/130 = **%97.7** triple-hizalanma (148 ile tutarlı). Backup `question_bank_v135_correct_backup_20260601`.
Düzeltilenler run=`2026_06_01_r2`. Spot: 001f1380 → A (xy-min −48) ✓.

**BİRLEŞİK (148+135):** 480 real_error'ın **270'i (%56) 3-sinyal-doğrulanmış correct_answer'a kavuştu.**
MAT+GEO deterministik kısım büyük oranda bitti. Kalan 210 (202 concept + 5 prev-disagree + 3 uncertain) → curator manual.
auto_judged_high 13,085 → 13,355.
