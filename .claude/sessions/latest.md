## Session Handoff — 2026-05-16 03:15 (Session 159)
**Branch:** master
**Son commit:** `a3597e842` chore: session 159 handoff — Tier I Re-OCR apply background started
**Uncommitted:** `backend/scripts/tier_i_reocr_apply.py` (RATE_LIMIT_S 0.5→0.1 paid tier)

### Yapilanlar
- Pilot v2 50 sample %100 precision (`backend/_pilots/20260516_reocr_pilot_v2_RESULT.md`, `c63152764`)
- Production script `backend/scripts/tier_i_reocr_apply.py` (`f44dc7e61`, SQLAlchemy CAST fix, HIGH-only mode)
- Dry-run 100 sample %78 apply (`backend/_pilots/20260516_tier_i_dryrun_RESULT.md`)
- Apply test 10 sample: 8/8 HIGH UPDATE'lendi (DB UPDATE bug fix doğrulandı)
- Apply background (paid tier, PID 915+917): 61/3,326 satır işlendi, ~270/saat, ~12h tahmini
- Pixel-doğrulama 4 sample: #10 OK (DB |AE| hatalı, OCR |AB| doğru), #28 #43 WRONG (LOW elendi), #37 OK
- DB UPDATE pattern: `image_url + image_ocr_text + pipeline_metadata.tier_i_reocr` (question_text DOKUNULMAZ)

### Fail Eden Testler
- YOK (pytest çalıştırılmadı)

### Engelleyiciler
- Apply ~12h background — bu session'da tamamlanmaz, ayrı session check zorunlu
- Free tier 1/dk → paid tier 4.5/dk (6x hızlanma, hala uzun)

### Sonraki Adimlar (maks 5)
1. Apply progress check: `ps -ef | grep tier_i_reocr_apply` + `wc -l backend/_pilots/20260516_tier_i_apply_RESULT.tsv`
2. Apply tamamlandığında post-audit 50 random sample (Tier H lesson zorunlu)
3. DB final durum: aktif image_url + missing % → Plan v1 hedef <%5 doğrulama
4. MID bant ayrı pass kararı (~798 satır, substr 0.50-0.70)
5. Page-level bucket (1,667 satır, ayrı script + pilot)

### Kararlar (gelecek session tekrar tartismasin)
- HIGH-only apply (substr≥0.70) seçildi — Tier H lesson, Cerrahi Müdahale
- Re-OCR amacı **image_url bind validation**, DB question_text override DEĞİL
- Cut-off detector: DB %99 TAM (pilot v1 preview [:120] artefaktıydı, yanılsama)
- Paid tier rate limit kaldırıldı (RATE_LIMIT_S=0.1), aynı API key `AIzaSy...Q6I`
- Page-level bucket farklı strateji (sayfa screenshot → Gemini Pro), ayrı session
