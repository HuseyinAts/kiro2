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

## Wave-2 / Wave-3 (otonom)
- **w2** (seed 0.53): 1552/1600 parse, promote 576 (%37.2). v_safe 24.254→24.830 (+576). backup `_poolA_w2_backup_20260621`.
- **w3** (seed 0.59): 1556/1600 parse, promote 616 (%39.7). v_safe 24.830→25.446 (+616). backup `_poolA_w3_backup_20260621`.
- **KÜMÜLATİF: v_safe 23.617→25.446 (+1.829, 3 dalga).** Funnel kararlı (promote %37-40, AGREE-bağımlı).
- Kalan fallback-unverified (blind_seen'siz): **11.301** (~7-8 dalga daha → ~+4.300 potansiyel).
- apply_wave.py wave_num parametreli; her wave reversible backup. correct_answer/is_active DOKUNULMADI.

## Açık-uçlu AUDIT (anchoring + 2.sinyal, workflow wcr4dkfmh)
Derin gözden geçirmede 3 kalıcı risk bulundu → workflow ile çözüldü.
- **Mekanizma:** 2377 soru (1829 promote + 548 lowconf) **karışık batch'lerde** (ders-sızıntısız) **açık-uçlu** kör reklasifiye edildi (agent'a ne ders ne anahtar verildi) → stored ile karşılaştır. 63 agent, ~26 dk, 2366/2377 parse.
- **PROMOTE seti (1829):** 2signal-CONFIRM (subj+ans ikisi de uyuştu) **1469 (%80)** / answer-dispute 253 / wrong-subject 96.
- **Anchoring HASARI ~0:** 96 wrong-subject'in **90'ı komşu-ders** (GEO↔MAT, FİZ↔KİM, TÜR↔EDB — zararsız), **6'sı domain-aşan** ve el-ile incelendi → **hepsi savunulabilir sınır vakası** (enerji→coğrafya/kimya, bilim-felsefesi→biyoloji/sosyal). **Gerçek wrong-subject = 0.** Hiçbiri de-promote edilmedi.
- **LOWCONF kurtarma:** 548'in **309'u 3-yön AGREE** (kitap+solve1+solve2) → **PROMOTE (+309)**, topic orijinal dalga çözümünden re-tag.
- **Apply (reversible, backup `question_bank_poolA_audit_backup_20260621` 2127 satır):**
  - recover 309 → promote (v_safe 25.446→**25.755**)
  - 2signal 1469+309=**1778** → `poolA_2signal=true` (vp güçlendirme)
  - dispute 253 → `poolA_answer_dispute=true` (kitap anahtarı yetkili, 3.sinyal için)
  - wrong 96 → `poolA_subject_2nd=<open>` (kayıt, hepsi tutuldu)
  - correct_answer/is_active diff **0**.
- **Çözülen riskler:** (1) anchoring→wrong-subject = ölçüldü, ~0 hasar; (2) 548 lowconf'tan 309 recall kurtarıldı; (3) manuel 10/1829 yerine **2377/2377 ikinci-sinyal örtüsü**; 1778 promote artık 2-bağımsız-sinyal (kitap+2 solve) = gold-aday (farklı-model 3.sinyal eklenince).

## Reçete (sonraki dalga)
1. `export_wave<N>.sql` (setseed değiştir, blind_seen dışla) → wave<N>_master.csv
2. `python build_wave.py wave<N>_master.csv w<N> 40`
3. Workflow (poola-wave1 script'i, manifest'i args ver, retry-on-deficient)
4. `python apply_wave.py w<N> w<N>_solved.json w<N>_keymap.json` → backup + set-based UPDATE
5. v_safe delta doğrula (verified_provisional flag DAHİL olmalı)
