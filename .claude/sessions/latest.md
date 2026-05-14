## Session Handoff — 2026-05-16 (Session 159)
**Branch:** master (pushed: c0f70904d, NEW commits ahead: c63152764, f44dc7e61)
**Production apply:** ⚠️ BACKGROUND DEVAM EDİYOR (PID 397, ~11 saat süre)

### Yapılanlar (8 ana adım)

1. **Re-OCR feasibility audit** (4,994 satır):
   - %66.5 (3,326) direct bucket: jsonl key match + disk crop var
   - %33.4 (1,667) page-level bucket: jsonl yok
   - Output: `backend/_pilots/audit_re_ocr_feasibility.py` + RESULT

2. **Cut-off detector** (DB question_text analizi):
   - %98.9 (4,939) DB TAM (yanılsama açılığa kavuştu)
   - %0.4 (18) gerçek cut-off
   - **Kritik insight**: Re-OCR amacı DB override DEĞİL, image_url bind validation

3. **Re-OCR pilot v1** (30 sample) — YANILTICI sonuç (preview [:120] artefaktı)

4. **Re-OCR pilot v2** (50 sample, full DB tail görünür):
   - HIGH bant (substr≥0.70): 34/34 OK (%100)
   - MID bant (substr 0.50-0.70): 9/9 OK (%100)
   - substr≥0.50 threshold: 43/43 precision **%100**

5. **Pixel-doğrulama** 4 kritik sample:
   - #10 (HIGH): DB |AE|=2 hatalı, OCR |AB|=2 doğru → crop doğru ✓
   - #28 (LOW): Venn vs fonksiyon → WRONG, elendi ✓
   - #37 (HIGH): Limit içerik aynı, LaTeX render farkı → OK ✓
   - #43 (LOW): Manyetik yön vs çerçeve → WRONG, elendi ✓

6. **Production batch script** (`backend/scripts/tier_i_reocr_apply.py`):
   - Modes: --dry-run, --apply, --resume, --limit
   - HIGH-only mode (SUBSTR_APPLY=0.70)
   - SQLAlchemy `::` cast bug FIX (CAST() syntax)
   - DB UPDATE: image_url + image_ocr_text (question_text DOKUNULMAZ)
   - pipeline_metadata.tier_i_reocr audit trail
   - Backup TSV + checkpoint resume

7. **Dry-run 100 sample** (deterministic seed=42):
   - HIGH: 54 (%54), MID: 24 (%24), LOW: 12 (%12), ERROR: 10 (%10)
   - HIGH-only apply rate: %54
   - Cost: $0.30 (test)

8. **Apply başlatıldı** (background, ~11 saat):
   - 10 sample test PASS (8/8 HIGH UPDATE'lendi, 0 db_error)
   - Tam scale 3,316 kalan satır background apply
   - Process: PID 397, `nohup python ... --apply --resume`
   - LIVE log: `backend/_pilots/20260516_tier_i_apply_LIVE.log`
   - RESULT TSV: `backend/_pilots/20260516_tier_i_apply_RESULT.tsv`

### Commit Geçmişi (bu session)
- `c63152764` feat(reocr-pilot): Faz 1.10 pilot — 50 sample %100 precision
- `f44dc7e61` feat(tier-i-reocr): production batch script + dry-run validation
- ⚠️ Push EDİLMEDİ — apply tamamlandıktan sonra push (sonuçlarla birlikte)

### DB Durumu (Session 159 başlangıç → son apply'a kadar)
- Aktif image_url: **87,177** (Session 158 sonu) → **87,185+** (10 sample apply sonrası)
- has_diagram=true missing: 4,994 → 4,984 (10 high band UPDATE)
- Apply tamamlanınca: ~87,185 + (3,316 × %54 × %90 success) = ~88,800+
- Final missing tahmin: ~3,200 (%6.4 direct only, page eklenirse %3.74)

### Apply Monitoring (ayrı session check)
```bash
# Process kontrol
ps -ef | grep tier_i_reocr_apply

# Progress
wc -l backend/_pilots/20260516_tier_i_apply_RESULT.tsv

# Last 10 sonuç
tail backend/_pilots/20260516_tier_i_apply_RESULT.tsv

# Live log
tail -20 backend/_pilots/20260516_tier_i_apply_LIVE.log

# DB durum
psql -p 5434 -d kiro2 -c "SELECT COUNT(*) FILTER (WHERE pipeline_metadata->'tier_i_reocr' IS NOT NULL) FROM question_bank WHERE is_active = TRUE;"
```

### Fail Eden Testler
- YOK (pytest çalıştırılmadı)

### Engelleyiciler
- Apply ~11 saat — bu session'da tamamlanmaz
- Gemini Pro free tier rate limit (~5 RPM, ~12 sn/call)
- Error rate %10 (dry-run) — production'da ~330 satır kaybı, retry pass adayı

### Sonraki Adımlar (ayrı session)

1. **Apply check** (1-2 saat sonra):
   - Process hala çalışıyor mu? (PID 397)
   - TSV satır sayısı (3,316 hedef)
   - Stats: applied_high, low_skip, error counts

2. **Apply tamamlandığında**:
   - Post-audit 50 random sample (Tier H lesson zorunlu)
   - DB final durum: aktif image_url, missing % hesapla
   - Backup TSV doğrula (rollback için)
   - Plan v1 hedef <%5 kontrolü

3. **MID bant kararı**:
   - HIGH apply sonucuna göre MID için yeni pass (~798 satır, ~3 saat)
   - Veya Faz 3 Curator UI'a bırak

4. **Page-level bucket** (1,667 satır, ayrı strateji):
   - Sayfa screenshot → Gemini Pro extract q_no
   - Page bucket pilot (~30 sample) + apply
   - Pilot v2'de %80 high precision verdi

5. **Error retry pass** (~330 satır):
   - apply RESULT'tan error olanlar topla
   - 2. dene Gemini call
   - Çoğu safety filter geçici, retry %80+ kurtarır

### Kararlar (gelecek session tekrar tartışmasın)
- HIGH-only apply (substr≥0.70) ile başla — Tier H lesson, en cerrahi
- MID bant ayrı pass (pilot 9/9 OK ama 9 sample CI dar)
- Page-level ayrı script (farklı görsel kaynak, farklı strateji)
- DB question_text DOKUNULMAZ (Sample #10 DB hatası bulundu ama düzeltim Faz 3 Curator işi)
- Error retry pass apply sonrası (idempotent, --resume ile)

### Önemli Notlar
- Apply background nohup detached — Claude session sonu apply'ı kesmez
- Checkpoint dosyası 10 ID ile başladı, her 50 satırda update
- Backup TSV per-row pre-state (rollback için yeterli)
- Plan v1 hedef <%5: HIGH-only %54 apply ile DIREKTLY sağlanmaz (%6.4 direct), AMA page-level eklenirse %3.74 KESIN sağlanır
