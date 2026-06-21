# Pool A — fallback re-tag + blind-solve (2026-06-21)

## Amaç
Direkt-kazanç havuzu kurudu (v_safe 23.617). Sonraki kaldıraç: **16.000 fallback-unverified**
soru. Bunlar `topic_match_quality='fallback'` olduğu için v_safe view'i HARD-gate'liyor
(yanlış konu → yanlış derste servis). Unlike tier1-unlock, view-bypass YANLIŞ olur.
Çözüm: re-tag (geçerli topic) + blind-solve (AGREE) → birlikte promote.

## Mekanizma — combined single-pass (2-pass yerine, rate-efficient)
Tek agent/batch: (1) kör çöz, (2) ders doğrula, (3) topic listesinden konu seç.
Promote barı = subjOk=Y ∧ topic in-list ∧ blind-AGREE(stored key) ∧ conf≥0.80.
correct_answer/is_active ASLA dokunulmaz — yalnız primary_topic_id + status + pipeline_metadata.

## Kalibrasyon pilotu (150, 25×6 STEM+TURKCE)
- 100/150 döndü (FIZIK/TURKCE batch parse-drop). Funnel: subjOK %97, topicOK %92,
  AGREE %62, **promotable %43**. Spot-check **5/5 doğru** (el ile yeniden çözüldü).
- Per-subject AGREE: BIYOLOJI 84% · GEOMETRI 64% · KIMYA 60% · MATEMATIK 40% (math drag).

## Wave-1 (1600, 10 ders, 40/agent, retry-on-deficient)
- 48 agent, ~34 dk, 0 rate-limit. **1599/1600 parse** (retry pass parse-drop'u çözdü: 50→1).
- Funnel (1596 işlendi): **promote 637 (%39.9)** / blind_dispute 508 / lowconf 196 /
  unsolvable 128 / topic_unresolved 94 / subject_mismatch 33.
- **v_safe 23.617 → 24.254 (+637).** Tüm 637 promote v_safe'e girdi (other-gate kaybı=0).
- Backup: `question_bank_poolA_w1_backup_20260621` (1596 satır, reversible).
- 1596 soru `blind_seen` flag'li → sonraki dalgalar dışlar. Kalan fallback ~14.400.

## KÖK-NEDEN dersi (apply bug, yakalandı + düzeltildi)
İlk apply v_safe'i 0 artırdı. Teşhis: view'in content-signal clause'u
`verified_provisional / student_coherent / consensus_2signal_run / ...` flag'lerinden
BİRİNİ şart koşuyor. İlk apply `blind_solve_wave` set etti ama `verified_provisional` DEĞİL.
Blind-solve wave'leri (w1-25) `verified_provisional=true` set ediyordu — kaçırılmıştı.
Forward-fix: 637 promote'a `verified_provisional=true` eklendi → hepsi v_safe'e girdi.
`apply_wave.py` düzeltildi (gelecek dalgalar için flag eklendi). vp barı semantik olarak
DOĞRU flag (single-blind AGREE∧conf≥0.80).

## Non-promote bucket'ları (sonraki 2.-sinyal işi için flag'li)
- blind_dispute 508: kör cevap ≠ stored key (A-bias dikkat; farklı-model 3.sinyal gerek)
- unsolvable 128: figür-bağımlı
- lowconf 196 / topic_unresolved 94 / subject_mismatch 33

## Reçete (sonraki dalga)
1. `export_wave<N>.sql` (setseed değiştir, blind_seen dışla) → wave<N>_master.csv
2. `python build_wave.py wave<N>_master.csv w<N> 40`
3. Workflow (poola-wave1 script'i, manifest'i args ver, retry-on-deficient)
4. `python apply_wave.py w<N> w<N>_solved.json w<N>_keymap.json` → backup + set-based UPDATE
5. v_safe delta doğrula (verified_provisional flag DAHİL olmalı)
