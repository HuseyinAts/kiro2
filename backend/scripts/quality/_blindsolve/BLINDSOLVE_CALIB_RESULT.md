# Blind-solve Kalibrasyon — RESULT (2026-06-20)

## Amac
57K unverified -> blind-solve (key gormeden coz) -> AGREE = 2-sinyal (key+blind) -> verified_provisional.
Batch-blind kalitesini + AGREE oranini olcmek icin 420-soru kalibrasyon.

## Hedef havuz (boşa solve etmeme)
direkt-kazanc = unfiltered (content-temiz) ∧ unverified ∧ NOT fallback/demoted/gate2c/tier1.
Bunlar AGREE'de status promote ile DIREKT v_safe'e girer. Sayı: **35.314** (fallback olan 16.000 ayrı, re-tag de ister).

## Kalibrasyon sonucu (420 aday, 40/agent, WAVE=3)
- **AGREE %66 (276/418)** — onceki ~%50'den yuksek (havuz daha temiz + Opus guclu).
- **Batch-blind kalite OK**: 40/agent throttle yok, 0 hata. Rate-limit cozumu burada da gecerli.
- **A-bias hafif**: solver {A97 B72 C91 D75 E83} vs DB {A80 B77 C100 D70 E91} — A az fazla, dagilim yakin = bagimsiz.
- **Conf kalibre**: conf>=0.9 -> %79 AGREE, 0.8-0.9 -> %72, <0.8 -> %48.
- **APPLY: AGREE ∧ conf>=0.80 = 205 -> verified_provisional + status=auto_judged_high.** 205/205 v_safe'e girdi.
  flag blind_solve_wave=2026-06-20-calib. backup question_bank_blindsolve_calib_backup_20260620.
  correct_answer DOKUNULMADI (yalnız status + vp flag).

## v_safe: 9.724 -> 9.929 (+205)

## Olcekleme plani (sonraki session'lar)
- direkt-kazanc 35.314 / dalga 3.000 ≈ 12 dalga. Her dalga ~%49 promote (conf>=0.80 bar) -> ~+1.470 v_safe/dalga.
- **35K tamamlanirsa ~+17.000 v_safe** (9.929 -> ~27.000).
- Pipeline hazir: export_calib.sql (rn<=N degistir) + blind batch + workflow (40/agent WAVE3 cooldown) + compare/apply.
- DISAGREE (~%34) = DB-key-hatasi VEYA solver-hatasi; 2. farkli-model sinyaliyle ayristirilabilir (gold terfi icin, P3).

## Karar
- vp bari = single-blind AGREE (onceki dalgalarla tutarli). Gold terfi 2. model ister (A-bias).
- conf>=0.80 filtresi coincidental dusuk-conf match'leri eler (kalite).
