## Session Handoff — 2026-06-21 (Pool A wave 1-3)
**Branch:** feature/self-evolution-optimization
**Uncommitted:** temiz (data blobs gitignored)

### Yapilanlar
- Direkt-kazanç kuruyunca KARAR: **Pool A (16K fallback)** seçildi (Pool B=335 ölü).
- Re-tag ZORUNLU: v_safe view `topic_match_quality='fallback'` HARD-gate (bypass YANLIŞ — fallback=yanlış konu).
- **Combined single-pass**: tek agent/batch kör-çöz + ders-doğrula + konu-seç. Promote barı = subjOk ∧ topic-in-list ∧ blind-AGREE ∧ conf≥0.80. correct_answer/is_active ASLA.
- Pilot (150): subjOK %97 / topicOK %92 / AGREE %62 / promote %43, spot 5/5.
- **3 OTONOM DALGA (1600/dalga, 40/agent, retry-on-deficient, 0 rate-limit):**
  - w1 (seed0.41): promote 637 → v_safe 23.617→24.254
  - w2 (seed0.53): promote 576 → 24.830
  - w3 (seed0.59): promote 616 → **25.446**
  - **KÜMÜLATİF +1.829.** Backup'lar `question_bank_poolA_w{1,2,3}_backup_20260621`.
- KÖK-NEDEN bug (w1): view content-signal clause `verified_provisional` flag ŞART; ilk apply kaçırdı (v_safe 0 arttı) → forward-fix + apply_wave.py'ye eklendi (w2/w3 sorunsuz).
- **Kalan fallback-unverified (blind_seen'siz): 11.301** (~7 dalga → ~+4.300 potansiyel).

### Fail Eden Testler
- YOK (kod değişikliği yok; DB promote + reçete script)

### Engelleyiciler
- YOK. Kullanıcı "w3 bitince dur" dedi → durduruldu.

### Sonraki Adimlar (maks 5)
1. Pool A devam (w4+, seed 0.61.. — reçete `_poolA_retag/POOLA_RESULT.md`, workflow script poola-wave1 scriptPath reuse, `apply_wave.py w<N>`).
2. Non-promote bucket'lar (her dalga ~490 dispute/~160 unsolvable) → 2.farklı-model 3.sinyal (A-bias).
3. Beta E2E smoke (25.446 havuz).
4. DISAGREE havuzu → gold terfi (2.model).

### Kararlar
- vp barı = single-blind AGREE∧conf≥0.80; promote yalnız primary_topic_id+status+pipeline_metadata; correct_answer ASLA.
- Promote metadata `verified_provisional=true` ŞART (view content-signal). apply_wave.py'de var (wave_num parametreli).
- export filtresi blind_seen dışlar; seedler: w1=0.41 w2=0.53 w3=0.59 (sonraki 0.61+).
- PG18 5434 manuel: `pg_ctl -D "C:/Program Files/PostgreSQL/18/data" -l C:/Users/husey/pg18_manual_start.log start`.

### Kararlar
- vp barı = single-blind AGREE∧conf≥0.80; promote yalnız primary_topic_id+status+pipeline_metadata; correct_answer ASLA.
- Promote metadata `verified_provisional=true` ŞART (view content-signal clause). apply_wave.py'de var artık.
- export filtresi blind_seen dışlar; her dalga setseed değiştir (w1=0.41 kullanıldı).
- PG18 5434 manuel: `pg_ctl -D "C:/Program Files/PostgreSQL/18/data" -l C:/Users/husey/pg18_manual_start.log start`.
