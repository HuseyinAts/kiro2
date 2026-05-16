## Session Handoff — 2026-05-16 (Session 161d, Faz 1.6 + 2.2 + 2.3 + 4.1-prereq) — IN PROGRESS
**Branch:** master (origin/master 1 commit behind pending push)
**Son commit (push edilmiş):** `1795fe3c9` feat(faz-2-3): drift dashboard
**Uncommitted:** Faz 4.1 stratified sample paketi

### Session 161d kapsamı (4 Faz iş)
- **Faz 1.6 Bronze promotion** (push'lu, `816c7f4ae`): 84,905 satır `bronze_clean`
- **Faz 2.2 Scoring template** (push'lu, `30515066c`): scoring_template.py + reusable guide
- **Faz 2.3 Drift dashboard** (push'lu, `1795fe3c9`): drift_dashboard.py + baseline demo
- **Faz 4.1 prereq** (commit pending): 200 stratified sample TSV ÜRETİLDİ (Hüseyin manuel scoring bekliyor)
  - `backend/scripts/quality/faz_4_1_sample.py` — strata: 50 exact + 50 fuzzy + 50 fallback + 50 v3.5_residual
  - `backend/_pilots/20260516_faz_4_1_curated_set_RAW.tsv` (200 satır, 15 kolon)
  - `backend/_pilots/20260516_faz_4_1_curated_set_RAW_SCORING.tsv` (200 satır, 18 kolon — 3 boş scoring kolonu)
  - SQL bug fix: `id::text` + `pipeline_metadata::jsonb` → `CAST(...)` syntax (Tier I lesson tekrarı)
  - Sıradaki: Hüseyin SCORING TSV doldurur (4-7 saat), sonra Faz 5.3 judge calibration

### Session 161d — Faz 1.6 Bronze tier promotion
- Alembic `qrs_v3_20260514` deploy (DB v2→v3, `bronze_clean` constraint accept)
- `backend/scripts/faz_1_6_bronze_promotion.py` — filter v1_loose
- 84,905 satır UPDATE (12 dk, 117/s), audit trail 84,905/84,905
- v_safe_for_beta=0 doğrulandı, post-state: bronze_clean=84,905 + unverified=61,482 + legacy_v3=18,397 + pending=2,775
- Convention v3 doc revize: `sanity_flags`/`ocr_quality_flag` → `quality_flags` gerçek key
- Plan v1 Faz 1.x %100 kapalı — sıradaki Faz 2.2 veya 4.1

### Session 161b ek iş (Faz 5.8 partial)
- `backend/scripts/tier_i_geometri_retry.py` — BLOCK_NONE safety + 334 error retry script
- Pilot n=20: %45 gemini_error, %20 applied_high, %50 toplam hata → **NO-GO production retry**
- Bonus: 4 HIGH UPDATE DB'de kalıcı (audit trail `safety_mode=block_none, retry_pass=2`)
- Finding: BLOCK_NONE yetersiz, `finish_reason != STOP` derin SDK sorunu — `candidates[0].content.parts[0].text` bypass gerek
- Error count drift düzeltildi: memory "311" → gerçek **334**
- RESULT: `backend/_pilots/20260516_tier_i_geometri_retry_pilot_RESULT.md`

### Yapilanlar
- `docs/llm_judge_spec.md` + `backend/scripts/judge/{__init__,prompt_v1,client,aggregator,runner}.py` — Faz 5.5+5.1+5.2 (`2a25347ba`)
- Tier I apply tamam: 3,008 satır 74.2 dk (9.3x speedup), 1,770 HIGH UPDATE — `backend/scripts/tier_i_reocr_apply_threaded.py` (`b41270231`)
- Tier I pixel-verify n=12 (R1 geometri 7 + R2 non-geometri 5): URL 12/12 ✅, image_ocr 11/12, qtext 10/12 (`b41270231`+`def215db7`)
- `backend/scripts/tier_j_qtext_audit.py` v1 + `tier_j_qtext_audit_v2.py` format-aware: 270 false positive elendi, ~860 gerçek content drift (`def215db7`+`01f7e7684`)
- Tier J pixel-verify n=60 (R3+R4): %40 image_ocr_better, %10 KRİTİK math errors (∥/⊥/=/<) (`fd6fecfa6`+`b388a0bee`)
- Tier J heuristic apply: 85 satır UPDATE (broken_text_o 51 + italic_i 39 + truncation 2), pipeline_metadata.tier_j_qtext audit trail — `backend/scripts/tier_j_apply_heuristic.py` (`d69628a16`)
- Memory: `~/.claude/.../memory/{feedback_smoke_test_checkpoint_trap,project_tier_i_subject_asymmetric}.md`

### Fail Eden Testler
- YOK (pytest çalıştırılmadı, sadece script-level smoke + multimodal pixel-verify)

### Engelleyiciler
- Faz 6.1 judge pilot Faz 4.1 (200 manuel curated set) blocker — bu insan iş
- Geometri safety_blocked 311 satır retry için Session 162+ `safety_settings=BLOCK_NONE` config
- ANTHROPIC_API_KEY env'de yok (judge runner için gerekli)

### Sonraki Adimlar (maks 5)
1. **Faz 4.1**: 200 manuel curated set (50 exact+50 fuzzy+50 fallback+50 v3.5 residual) — Hüseyin manuel iş
2. **Faz 6.1 judge pilot**: 1,000 satır = 445 GEOMETRI Tier J kalanı + 555 random Bronze, ~$10-20, ~1.5h
3. **MID bant pilot**: `tier_i_reocr_apply_threaded.py --substr-apply 0.50 --limit 50` script edit + apply (~25 dk)
4. **Geometri safety retry**: 311 satır `safety_settings=BLOCK_NONE` ile Session 161+ Faz 5.8

### Kararlar (gelecek session tekrar tartismasin)
- Tier I HIGH apply onaylı (URL 12/12 + image_ocr 11/12 = production'da kalıyor)
- MID/LOW band ertele (gerçek kanıt yok, judge pipeline için bırakıldı)
- Tier J SUBJECT-ASYMMETRIC: GEOMETRI-only (KIMYA Tier I OCR typo riski, sözel Tier I scope dışı)
- Tier J blind apply YASAK: 60 sample evidence — %53-60 format_only (LaTeX→Unicode = beta UI render kaybı)
- Strategy A heuristic conservative (85/1727=%4.9): broken LaTeX + italic-I objectively wrong patterns
- Strategy C judge için Faz 4.1 önkoşul, Session 162+
