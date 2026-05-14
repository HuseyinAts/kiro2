# Quality Pool Plan v1 — Kalite Piramidi + Audit Harness

**Tarih:** 14 May 2026 (Session 156)
**Yaklasim:** Cozum 1 (Sapphire/Gold/Bronze Tier) + Cozum 3'un Audit Harness bileseni
**Onkosul:** Convention v2 deploy edilmis (commit 094712e6a). v_safe_for_beta = 0.
**Felsefe:** Acelem yok, kalite + sorunsuz veri oncelik. Karpathy: once dusun, sadelik, cerrahi mudahale, hedef odakli.

---

## Yapi Ozeti

```
Tier S (Sapphire):  hedef 5-10K, %0 hata, insan-onayli, beta golden set
Tier G (Gold):      hedef 30-50K, ≤%5 hata, judge-onayli + spot audit
Tier B (Bronze):    pipeline-fix uygulanmis ama yargilanmamis, beta'da YOK
Tier C (Coal):      archived (is_active=false), kurtarilamayan

quality_review_status enum (Convention v2):
  - human_verified   → Sapphire
  - auto_judged_high → Gold
  - unverified       → Bronze (pipeline-fix sonrasi temiz olanlar)
  - rejected         → Coal
  - archived         → Coal
```

**Audit harness:** Her Pazar otomatik 30 random sample TSV uretir. Husyin scoring yapar (1 saat). Drift trend tracking. 30-gun MA hata orani <%2 hedef.

---

## Faz Detaylari

### Faz 0 — Foundation (Hafta 0, 2-3 gun)

Mevcut kayitlari/audit'leri commit + baseline dondur. Drift baselinesi olmadan harness anlamsiz.

| # | Gorev | Sukses kriteri |
|---|---|---|
| 0.1 | Memory drift fix (live DB sayilarina guncelle) | unverified=146,387, legacy_v3=18,397 |
| 0.2 | C1, C2, C3 RAW TSV'leri commit + Husyin scoring | 110 sample (30+50+30) RESULT artifact |
| 0.3 | audit_missing_image_v2.py + RESULT commit | git'te kayitli, yeniden uretilebilir |
| 0.4 | question_bank snapshot pg_dump (rollback poligonu) | backups/qb_pre_pipeline_fix.sql.gz (~150MB) |
| 0.5 | Plan v1 dokuman (bu dosya) commit | docs/quality_pool_plan_v1.md |

**Cikti:** Bilinen baseline, kayit altina alinmis sayilar, rollback mumkun.

---

### Faz 1 — Pipeline-Fix Foundation (Hafta 1-2)

49,313 missing-image satirinin %84.7'si pipeline-fix'le linklenebilir (audit kanitladi).

| # | Gorev | Sukses kriteri |
|---|---|---|
| 1.1 | Tier C image matcher script (exact_match: 16,440 satir) | --dry-run + --apply, idempotent, 100% match dogrulamali |
| 1.2 | ✅ **Tier D image matcher (TAMAMLANDI 15 May)** | Pilot %96 accuracy → full run. 13,741 satır UPDATE (D1=13,472 + D2=269). image_url 74,954 → 88,695. Script: `tier_d_image_matcher.py`, RESULT: `_pilots/20260515_tier_d_pilot_RESULT.md` |
| 1.3 | ✅ **OCR text validator (TAMAMLANDI 15 May)** | 64 satır flag (kombineli rare_ratio>=0.15 AND >=1 4-cons rare token). Corpus zaten temiz (replacement char=0), marjinal sinyal. Domain false-positive bilinen sınır (geometri etiketleri, yabancı isimler, Osmanlıca). Script: `ocr_text_validator.py` |
| 1.4 | ✅ **Sanity checker (TAMAMLANDI 15 May)** | 612 satır flag (607 duplicate_options + 5 answer_no_option, 2 placeholder_dup). Defansif flag-only (Faz 1.9 pattern). Script: `backend/scripts/sanity_checker.py` |
| 1.5 | ✅ **Post-fix audit + Tier F asymmetric (TAMAMLANDI 15 May)** | İlk audit: %30 missing. Kök neden: D_match_failed %99 (script threshold problemi, OCR/disk değil). Tier F asymmetric threshold (sim>=0.50, key match required) → +7,441 image_url. Missing: %30 → **%14.96**. RESULT: `_pilots/20260515_tier_f_root_cause_RESULT.md` |
| 1.5+ | ✅ **Tier F asymmetric threshold recovery (Session 158)** | Key match var → sim>=0.50 (gevşek). Pilot 100 sample %83 worst case accuracy (%17 unclear: ~%50 OCR error + ~%50 math template repetition). Defansif flag → judge sinyal. Script: `tier_f_recovery.py` |
| 1.6 | Bronze tier promotion: pipeline-fix gecen satirlara `quality_review_status='bronze_clean'` | Yeni status enum + migration |
| 1.7 | ✅ **q_no=invalid orphan recovery (TAMAMLANDI 15 May)** | 7,510 → 4,315 match (%57.5). E1a=2,369 (exact), E1b=1,189 (sim), E1c=17, E2=740. Threshold uniform 0.70 (Tier D pilot kalibre). Script: `qno_orphan_recovery.py` |
| 1.8 | Symbolic math verifier (SymPy) — wrong_answer 2. layer | %30+ math soru parse |
| 1.9 | ✅ **Book answer key cross-reference (TAMAMLANDI 14 May)** | A1 defansif flag. 16,159 satir flag (agree=7,425, disagree=8,734). Audit: `_pilots/20260514_book_key_audit_RESULT.md` |
| 1.10 | Re-OCR cut-off entries (Pro ile) — scope ~3.6K (revize, 17K degil) | Faz 0.8 methodology fix sonrasi |

**Cikti:** ~+41,777 image-link, OCR/sanity flag'leri, Bronze tier oluşumu (~80-100K satir), 16,159 book_key_match flag.

---

### Faz 2 — Audit Harness (Hafta 2-3, Faz 1 ile paralel)

Drift detection sürekli aktif olmali. Faz 1 başlamadan kurulmali ki "before/after" karşilaştirma mumkun.

| # | Gorev | Sukses kriteri |
|---|---|---|
| 2.1 | Audit harness script (haftalik 30 random sample TSV, reproducible seed) | backend/scripts/quality/weekly_audit.py |
| 2.2 | Husyin scoring template + shortcut (TSV'de verdict, error_type, notes kolonlari hazir) | 1 satir = 1 dakika scoring hedef |
| 2.3 | Drift dashboard (markdown rapor, hafta-haftaya hata orani trend) | docs/quality_audits/weekly_*.md auto-generated |
| 2.4 | 30-gun MA tracker | rolling average, >5% alarm trigger |
| 2.5 | Windows Task Scheduler (Pazar 09:00 audit otomatik) | weekly run cron-like setup |
| 2.6 | İlk 4 hafta baseline scoring (Husyin haftada 30 sample) | 120 sample, hata orani baseline |

**Cikti:** Her hafta otomatik audit, Husyin 1 saat/hafta scoring, drift trend goruluyor.

---

### Faz 3 — Curator UI (Hafta 3-5)

Sapphire growth machine. Manuel curator olmadan Sapphire 0 satir kalir.

| # | Gorev | Sukses kriteri |
|---|---|---|
| 3.1 | Backend endpoints (GET unverified queue with filter, POST verdict) | /api/v1/curator/* (admin-only) |
| 3.2 | React sayfa minimum (admin/labs altinda) | Soru + secenekler + cevap + book + page goruntu |
| 3.3 | Klavye shortcuts (1-5 cevap, Y/N verify/reject, A archive) | Husyin saatte 30-50 satir hedef |
| 3.4 | Queue management (subject, has_diagram, error_type filter) | Husyin spesifik strata curate edebilir |
| 3.5 | Curator audit: 50 sample re-curate (kendi kendini test) | Inter-rater consistency >%95 |
| 3.6 | Audit log (kim, ne zaman, neyi onayladi) | reviewed_by + reviewed_at field populate |

**Cikti:** Sapphire growth machine hazir. Husyin gunluk 30-50 satir curate edebilir.

---

### Faz 4 — Sapphire Build + Sanity Cleanup (Hafta 5-7)

Sapphire'e 200 manuel curated set + sanity-fail satirlar manuel review.

| # | Gorev | Sukses kriteri |
|---|---|---|
| 4.1 | 200 manuel curated set (judge calibration onkosulu) | Stratified sample: 50 exact, 50 fuzzy, 50 fallback, 50 v3.5 residual |
| 4.2 | Sanity-fail satirlar (Faz 1.4'ten) manuel review | duplicate options + answer mismatch fix |
| 4.3 | Curator velocity check (gercek saatte kac satir?) | Hedef: 30-50/saat, gercek olcum |
| 4.4 | Sapphire pool dogrulama (random 50 sample inter-rater) | Husyin tekrar bakar, 0 hata |
| 4.5 | Sapphire'i v_safe_for_beta'ya ekle (D4 view update) | view = 200 satir (ilk versiyon) |

**Cikti:** Sapphire = 200+ satir, beta-eligible (kucuk pool, ama %100 temiz).

---

### Faz 5 — LLM Judge Calibration (Hafta 7-9)

200 set'i kullanarak judge prompt + threshold kalibre.

| # | Gorev | Sukses kriteri |
|---|---|---|
| 5.1 | Judge prompt design (Opus + Pro double check) | YAML config, versioned |
| 5.2 | Judge prototype (single-question test) | 200 set'te dry-run, raw output kaydedilir |
| 5.3 | Threshold calibration (precision-recall curve) | F1 ≥ 0.85 hedef, threshold belirlenir |
| 5.4 | Holdout test (50 yeni curated set, judge bilmeden) | Generalization dogrulama |
| 5.5 | Judge spec dokumani | docs/llm_judge_spec.md |
| 5.6 | Cost projection (146K satir × tahmini token) | Faz 6 maliyet onayi |

**Cikti:** Production-ready judge prototype, F1 ≥ 0.85 garantili.

---

### Faz 6 — Gold Production Run (Hafta 9-11)

Bronze tier'i (pipeline-fix gecmis ~80K satir) judge ile yargilatip Gold'a yukselt.

| # | Gorev | Sukses kriteri |
|---|---|---|
| 6.1 | Judge pilot run (1,000 satir) | Dry-run, sonuc rapor |
| 6.2 | Pilot audit (100 sample, judge dogru mu?) | Inter-rater >%95 |
| 6.3 | Judge full run (Bronze ~80K) | auto_judged_high status update |
| 6.4 | Gold quality audit (random 100 sample, post-judge) | Hata orani ≤%5 |
| 6.5 | Gold'i v_safe_for_beta'ya ekle | view = Sapphire + Gold = ~30-50K |
| 6.6 | Reject pile audit (judge'un fail dedikleri 30 sample) | False negative kontrol |

**Cikti:** v_safe_for_beta = 30-50K satir (Sapphire + Gold), audit-validated.

---

### Faz 7 — Beta Launch + Surekli Operasyon (Hafta 11+)

Beta acilir. Audit harness sürekli aktif. Compound learning baslar.

| # | Gorev | Sukses kriteri |
|---|---|---|
| 7.1 | Beta soft launch (5-10 ogrenci, 1 hafta) | Yapayl trafik test |
| 7.2 | Student feedback flag mekanizmasi | "bu soru hatali" raporu → judge re-evaluation |
| 7.3 | Aylik retrospective (30-gun MA + drift trend) | Quality dashboard rapor |
| 7.4 | Curator quota: gunluk 30-50 satir Sapphire büyütücüsü | Sapphire +200/hafta hedef |
| 7.5 | Judge re-calibration (her 1000 yeni Sapphire'de) | F1 drift onleme |

**Cikti:** Beta canli, kalite kompound iyilesir, sürdürülebilir sistem.

---

## Quality KPI'lari (REVISED 14 May — C1+C2+C3 audit sonrası)

| Faz | KPI | Hedef (revize) | Önceki | Gerekçe (audit) |
|---|---|---|---|---|
| 1 | missing_diagram audit dilimi | **<%10** | <%5 | Baseline %32 → %85 fix sonrası %5 + unclear payı |
| 2 | Audit harness uptime | 4/4 hafta | aynı | — |
| 3 | Curator velocity | **20-40 satir/saat** | 30-50 | Defansif (audit Hüseyin için zorlu çıktı) |
| 4 | Sapphire inter-rater | **>%90** | >%95 | İlk denemede daha gerçekçi |
| 5 | Judge F1 (200+50 set) | **≥0.80 ilk, ≥0.85 stretch** | ≥0.85 | Türkçe LLM judge benchmark yok |
| 6 | Gold post-judge audit hata | **≤%8 ilk, ≤%5 3 ay sonra** | ≤%5 | Compound iyileşme realistic |
| 7 | 30-gün MA error | **<%5 ilk 3 ay, <%2 6 ay sonra** | <%2 sustained | Beta gerçek trafikle |

### Yeni KPI'lar (3 ek metric, audit'in ortaya çıkardığı)

| Metric | Hedef | Faz | Ölçüm |
|---|---|---|---|
| Bayesian validator precision | >%70 | **0.9 (yeni)** | Audit ile ölç → hibrit/replace karar |
| OCR truncation oranı (yeni ingest) | <%5 | **0.8 + 1.10 (yeni)** | Re-OCR sonrası ölç |
| Symbolic math coverage | >%30 math sorusu | **1.8 (yeni)** | SymPy parse rate |

### Audit kanıtı (110 sample, C1+C2+C3 birleşik)

| Metric | Değer | Kaynak |
|---|---|---|
| Toplam pass oranı | %22.7 | 25/110 |
| Toplam non-pass | %77.3 | 85/110 |
| wrong_answer hata payı | %25.9 (22/85) | C2 dominant |
| missing_diagram hata payı | %32.9 (28/85) | C1 dominant |
| ocr cut-off hata payı | %21.2 (18/85) | C2'de %24, endemic |
| garbage_text hata payı | %10.6 (9/85) | C3 dominant |
| incomplete hata payı | %9.4 (8/85) | C2'de incomplete data |

---

## Toplam (REVISED)

| Boyut | Önceki | **Revize** | Değişim |
|---|---|---|---|
| Süre (başlangıç → beta) | ~11 hafta | **~12-13 hafta** | +1-2 hafta (yeni 7 task) |
| LLM API toplam | ~$500-1,500 | **~$600-1,700** | +$50-200 re-OCR + $200-400 math re-solve |
| İnsan emek (Hüseyin) | ~80-120 saat | **~95-135 saat** | +10-15 saat yeni audit'ler |
| Beta-safe pool | ~30-50K | **~30-55K** | +5K symbolic katkı (book key flag, pool katkı YOK) |
| wrong_answer yakalama | ~%85-90 | **~%90-95** | 4-katmanlı (book→symbolic→bayesian→judge). Book key pre-flag: %13 (~7,600 satır), pilot kanıt |
| OCR cut-off pool | belirsiz | **~3.6K satır re-OCR** | Faz 1.10 (Faz 0.8 methodology fix sonrası, %80 azalma) |
| Judge cost save (Faz 5/6) | implicit | **~$50** | book key agree (7,425) bypass adayı |
| Geri alınabilirlik | Yüksek | aynı | — |

---

## Riskler ve Mitigasyonlar

| Risk | Olasilik | Etki | Mitigasyon |
|---|---|---|---|
| Curator burnout | Yuksek | Yuksek | Quota cards, batch by subject, opsiyonel ek curator |
| Judge halusinasyon | Orta | Yuksek | Opus+Pro double, threshold konservatif, spot audit |
| Audit harness disipline kaybi | Orta | Yuksek | Cron + alert, haftalik retrospective |
| Tier C/D yanlis image populate | Orta | Yuksek | --dry-run zorunlu, pilot 100 manuel dogrulama |
| Sanity check false negative | Dusuk | Orta | Conservative regex, periyodik review |
| Faz suresi kayma | Yuksek | Dusuk | Acelem yok prensibi, kompound iyilesme |

---

## Bagimililik Grafigi

```
Faz 0 (Foundation)
  ├→ Faz 1 (Pipeline-Fix)
  ├→ Faz 2 (Audit Harness)  ← paralel
  └→ Faz 3 (Curator UI)
       ├→ Faz 4 (Sapphire Build)
       └→ Faz 5 (Judge Calib)
            └→ Faz 6 (Gold Production)
                 └→ Faz 7 (Beta + Continuous)
```

---

## Referanslar

- `backend/_pilots/20260514_audit_RESULT.md` — 100+30 stratified audit
- `backend/_pilots/20260515_missing_image_v2_RESULT.md` — pipeline-fix potansiyeli
- `backend/_pilots/20260514_book_key_audit_RESULT.md` — Faz 1.9 pilot + 8 sample pixel-doğrulama
- `docs/quality_pool_roadmap.md` — onceki roadmap (Cozum E1-E4 yollari)
- `docs/quality_review_status_convention.md` — Convention v2
- `backend/scripts/populate_image_urls.py` — Tier A+B referans (JSONL-driven)
- `backend/scripts/populate_image_urls_tier_c.py` — Tier C exact_match (DB-driven, +16,440 satır, 14 May)
- `backend/scripts/book_key_cross_reference.py` — Faz 1.9 flag (16,159 satır, 14 May)
- `backend/scripts/cross_validate_answers.py` — Bayesian validation referans (Faz 0.9'da REPLACE kararı)

*Plan v1 — gozden gecirilecek (sonraki bolumde elestiri).*
