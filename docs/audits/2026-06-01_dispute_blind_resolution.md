# 628 Dispute — Kör Re-Solve + Konsensüs Çözümü

**Tarih:** 2026-06-01
**Amaç:** verified_core build'in (31 May) işaretlediği 628 `blind_answer_dispute`
sorusunu (blind≠DB, high-conf) **2. bağımsız kör sinyalle** çöz. Bunlar hâlâ
`auto_judged_high` (canlı gold pool) idi — yanlışsa öğrenci yanlış cevap görüyor.

## Yöntem — non-dairesel 2-sinyal konsensüs
- **Sinyal 1:** orig_blind (verified_core kör-solve, 31 May).
- **Sinyal 2:** yeni kör LLM re-solve (Workflow `wf_c963b789-982`, 26 batch × 25,
  5'erli sıralı dalga, 627/628 çözüldü, 2.8M token, ~9 dk).
  Solver'a DB cevabı VERİLMEDİ (blind-safe export; key ayrı dosyada).
- **Konsensüs:**
  - `new == orig_blind ≠ db` → **REAL_ERROR** (2 bağımsız solve DB'ye karşı hemfikir)
  - `new == db` → **FALSE_DISPUTE** (yeni sinyal DB ile uyuştu — konservatif: dispute temizle, terfi YOK)
  - `new ≠ ikisi de` → **SPLIT** (3-yön ayrışma → curator manual)
  - `new == "?"` → **UNSOLVABLE** (figür/garble)

## Sonuç (628)
| Verdict | Sayı | Aksiyon |
|---|---|---|
| **REAL_ERROR** | **480** | status → pending (curator); canlı gold'dan çıktı |
| FALSE_DISPUTE | 69 | dispute flag temizlendi, auto_judged_high'da kaldı |
| SPLIT | 30 | status → pending (curator manual) |
| UNSOLVABLE | 47 | dispute_verdict işaretlendi (figür/garble) |
| MISSING | 2 | yeni cevap yok, dokunulmadı |

**Yeni kör-solve cevap dağılımı:** A 128 / E 120 / D 117 / C 114 / B 101 / ? 47 —
**A-bias YOK** (orig pipeline A-bias'ının aksine), bağımsızlık göstergesi.

## Spot-check (manuel, kanıt)
2/2 net-çözülebilir matematik DB hatası DOĞRULANDI:
- `001f1380`: 4x−3y=−48, xy min → parabol min x=−6 → **−48 (A)**, DB=D(12) **YANLIŞ**.
- `0146d685`: lcm=200, gcd=20, a+b → çiftler {220,140}, **260 (DB=C) İMKANSIZ**, A=220 doğru.

## DB Apply (non-destructive)
Backup `question_bank_dispute_resolve_backup_20260601` (628 id+status+metadata).
`correct_answer` **DOKUNULMADI** (curator karar verecek). Metadata: `dispute_verdict`
+ `dispute_run=2026_06_01`. Doğrulama (birebir uyumlu):
- auto_judged_high 13,595 → **13,085** (−510)
- pending 36,517 → **37,027** (+510)
- blind_answer_dispute 628 → **559** (−69 false_dispute)

## Korelasyonlu-hata değerlendirmesi
480/628 (%76) yüksek; ama (a) 628 zaten blind≠db ön-seçilmişti, (b) yeni solve %76
reproduce etti, (c) spot-check 2/2 net matematik DB hatası, (d) yeni solve A-bias
göstermiyor. → REAL_ERROR sınıfı güvenilir. Yine de auto-overwrite YAPILMADI —
curator review zorunlu (K23 disiplini).

## Çözdü
K5-K8 (cevap-hatası) — 480 canlı yanlış cevap gold pool'dan çıkarıldı + curator'a.
Kalan: 480'i curator onayıyla correct_answer düzelt (veya reject). 30 split + 47
unsolvable curator/demote.

## Artifactlar (untracked, `backend/scripts/quality/_beta_core_tmp/`)
dispute_solve_input.jsonl, dispute_key.jsonl, dispute_batches/, dispute_new_answers.json,
consensus_apply.py, apply_dispute.sql. Workflow: `wf_c963b789-982`.
