# Session Handoff — 2026-06-21 (blind-solve wave 21-25, DİREKT-KAZANÇ POOL KURUDU)

**Branch:** `feature/self-evolution-optimization`
**Son commit:** `feat(quality): blind-solve wave25 v_safe promote (pool kurudu)`
**Working tree:** temiz. **TÜM commit'ler LOCAL — push EDİLMEDİ** (feature branch).
**Infra:** PG18 5434 `pg_ctl` ile manuel açık (restart'ta DÜŞER → `pg_ctl -D "C:/Program Files/PostgreSQL/18/data" -l C:/Users/husey/pg18_manual_start.log start`). Backend/frontend DOWN.

## ⭐ BU SESSION: v_safe 20.907 → 23.617 (+2.710, 5 dalga) — DİREKT-KAZANÇ POOL TÜKENDİ

| Dalga | seed | solved | AGREE | promote | v_safe |
|---|---|---|---|---|---|
| w21 | 0.43 | 1590 | %72.6 | +619 | 21.526 |
| w22 | 0.47 | 1476 | %63.8 | +580 | 22.106 |
| w23 | 0.03 | 1474 | %66.3 | +565 | 22.671 |
| w24 | 0.17 | 1508 | %68.4 | +623 | 23.294 |
| w25 | 0.73 | 846  | %73.6 | +323 | 23.617 |

- blind_total: 11.183 → **13.893** (+2.710).
- Tüm değişiklikler **reversible** (her dalga `question_bank_blindsolve_w<N>_backup_20260621`), **correct_answer/is_active DOKUNULMADI** (yalnız `quality_review_status='auto_judged_high'` + `pipeline_metadata` flag).
- **DİREKT-KAZANÇ POOL = 0** (export filtresiyle kalan aday doğrulandı = 0). Bu havuz (unfiltered ∧ content-temiz ∧ status-only-blocked ∧ NOT fallback/demoted/gate2c/tier1) bitti.

## SONRAKİ İŞ (ROI sıralı) — bu seans BLOKE değil, yeni karar gerek
1. **Fallback'li ~16K unverified** — direkt-kazanç havuzundan çıkarılmıştı (fallback topic-tag). Önce topic re-tag (S20 Haz reçetesi: `_vp_unlock/`), sonra blind-solve. Re-tag + solve birleşik.
2. **Geniş unverified evreni** — direkt-kazanç filtresinin dışladığı tier1/demoted/gate2c havuzları. Her birinin AYRI gerekçesi var (view-bloke). Tier1 unlock zaten yapıldı (D8 view); demoted/gate2c için ayrı audit gerek.
3. **PUSH** — tüm session commit'leri LOCAL; `git push` (kullanıcı isterse).
4. **DISAGREE havuzu** (~%30/dalga) — 2. FARKLI-model sinyaliyle ayrış (gold terfi; A-bias var, single-blind gold için yetmez).
5. **Beta E2E smoke** — 23.617 havuzla AYT simülasyonu (backend up gerek).

## REÇETE (yeniden gerekirse — _blindsolve/ kalıcı)
`cd backend/scripts/quality/_blindsolve` → her dalga:
1. `sed 's/setseed(0.59)/setseed(<YENİ>)/; s/wave20_master.csv/wave<N>_master.csv/' export_wave20.sql > export_wave<N>.sql` (export <50 satır = pool kurudu)
2. `psql -f export_wave<N>.sql` → 1600 csv (KEY dahil)
3. `python split_wave.py <N>` → w<N>batches/ (KEY YOK=kör) + w<N>manifest.json
4. Workflow scriptPath=`blind_solve_wave.js`, args=w<N>manifest İÇERİĞİ (JSON array). WAVE=3, ~40dk.
5. Sonucu (`result.rows`) → `w<N>_solved.json` (Write). NOT: output wrapper JSON, `result.rows` çıkar.
6. `python aggregate_wave.py <N>` → apply_w<N>.sql + flag_seen_w<N>.sql
7. `psql -f apply_w<N>.sql` + `psql -f flag_seen_w<N>.sql` → commit → verify.

KULLANILMIŞ seed: 0.05 0.07 0.13 0.17 0.19 0.23 0.29 0.31 0.37 0.42 0.43 0.47 0.49 0.53 0.59 0.61 0.67 0.71 0.73 0.77 0.83 0.89 0.91 + 0.03

## RATE-LIMIT (memory: reference_workflow-rate-limit-batching)
1. **529 "Server temporarily limiting"** = RPM throttle → büyük-batch (40/agent) + WAVE=3. Bu seansta 5 dalganın HİÇBİRİNDE 529/session-limit VURULMADI (her dalga ~40dk temiz koştu).
2. **"session limit · resets HH:MM"** = token kotası → reset bekle.

## Doğrulama (yeni session açılışında)
```sql
SELECT count(*) FROM v_safe_for_beta;  -- 23.617 olmalı
SELECT count(*) FROM question_bank WHERE pipeline_metadata::jsonb ? 'blind_solve_wave';  -- 13.893
```

## Kararlar (tekrar tartışma)
- vp barı = single-blind AGREE∧conf≥0.80. Gold terfi 2. farklı-model şart (A-bias hafif).
- promote yalnız status + pipeline_metadata flag; **correct_answer ASLA**.
- Direkt-kazanç havuzu bitti → sonraki büyüme fallback re-tag VEYA farklı havuz audit gerektiriyor (otonom değil, karar gerek).

---
*Güncellendi: 2026-06-21 — wave 21-25 otonom çok-dalga; direkt-kazanç pool 0'a indi (+2.710 v_safe).*
