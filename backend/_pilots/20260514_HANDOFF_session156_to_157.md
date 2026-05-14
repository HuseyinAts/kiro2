# Session 156 → 157 Handoff

> **Bu doküman yeni Claude oturumunun kaldığımız yerden devam etmesi için.**
> Tüm kritik bağlam burada — yeni oturum bunu ve `MEMORY.md`'yi okuyarak başlamalı.

---

## 1. KIM, NE, NEREDE

**Sen:** KIRO2 projesinde Hüseyin'le çalışan Claude'sun. Karpathy 4 prensibe uy: önce düşün, sadelik, cerrahi müdahale, hedef-odaklı.

**Proje:** Türk YKS hazırlık platformu, FastAPI + React + PostgreSQL 18 (port 5434) + Redis. Path: `C:\Users\husey\kiro2`.

**Hüseyin'in tarzı:** Kısa direktif iletişim ("DEVAM ET", "B", "tümünü onaylıyorum"), Türkçe. Onaylar verilince tekrar sormadan ilerle. **"Acelem yok, kalite öncelik."**

**Branch:** master, son commit `41740d29a`, GitHub'a push edildi.

---

## 2. SESSION 156'DA NE YAPILDI (özet)

### Quality Pool Plan v1 İnşa Edildi

3-felsefi yaklaşım analizinden sonra Hüseyin **Çözüm 1 (Sapphire/Gold/Bronze tier) + Çözüm 3'ün audit harness'ı** birleşik stratejiyi seçti.

`docs/quality_pool_plan_v1.md` → 8 faz, ~12-13 hafta, 50 task.

### Faz 0 (Foundation) — Tamamen Bitti (9/9)

| # | Task | Çıktı dosyası |
|---|---|---|
| 0.1 #2 | Memory drift fix | `MEMORY.md` (Session 156 entry) |
| 0.2 #1 | C1+C2+C3 audit (110 sample) | `backend/_pilots/20260514_audit_C1_C2_C3_COMBINED_RESULT.md` + 3 SCORING.tsv |
| 0.3 #14 | audit_missing_image_v2 commit | `backend/_pilots/audit_missing_image_v2.py` + RESULT |
| 0.4 #10 | pg_dump backup | `backups/qb_pre_pipeline_fix_20260514.sql.gz` (gitignored) |
| 0.5 #26 | Plan v1 commit | `docs/quality_pool_plan_v1.md` |
| 0.6 #46 | Convention v3 doc | `docs/quality_review_status_convention_v3.md` + Alembic migration |
| 0.7 #47 | Pool kategori kararı | `docs/pool_categorization_decision.md` |
| 0.8 #56 | OCR truncation investigation | `docs/ocr_truncation_root_cause.md` + `.claude/rules/audit-methodology.md` |
| 0.9 #51 | Bayesian validator audit | `docs/bayesian_validator_audit_RESULT.md` |

### Push Edilen 7 Commit

```
41740d29a  feat(convention): v3 bronze_clean
674842f92  docs(decision): pool categorization
b4003e157  docs(audit): Bayesian validator audit
af711179f  docs(audit): OCR truncation + methodology rule
ee90bbab2  docs(plan): plan v1 + Faz 0.2 audit
cc5ef97b8  audit(pipeline-fix): missing-image repair potential
094712e6a  feat(quality): Convention v2 (önceki oturum)
```

---

## 3. KRİTİK BULGULAR (yeni oturum bunları bilmeli)

### A) OCR truncation YOKMUŞ (methodology hatası)

C2 audit'te %24 OCR cut-off raporlandı, ama gerçek DB-level **%2.15**. Sebep: `20260515_next_audit_templates.sql`'de `LEFT(question_text, 200)` SQL function'ı sample TSV'yi insan-okunurluk için kısaltmış. Claude bunu gerçek cut-off ile karıştırmış.

**Yeni rule:** `.claude/rules/audit-methodology.md` — Audit sample TSV truncate YASAK.

**Plan etkisi:** Faz 1.10 scope ~17K → ~3.6K satır (%80 azaldı). $50-100 + 1 gün dev tasarruf.

### B) Bayesian validator REPLACE

Faz 0.9 audit: HIGH confidence precision %26 (hedef %70 altı). `ai_upgrade_bayes_*` source %11 pass.

**Karar:** Bayesian'ı drop, judge tek karar mercii. Faz 5.7 (hybrid) **DELETED**.

**Sürpriz:** v4.14e Gemini Flash batch'te (107K) Bayesian HİÇ uygulanmamış (NULL metadata). Plan v1'in ilk varsayımı kısmen yanlıştı.

### C) Pool categorization kararı (56K satır)

`docs/pool_categorization_decision.md`:
- 38,477 unverified+book_key+image → Bronze candidate (judge eligible)
- 5,272 legacy_v3 (book_key + ai_solved + crossval + ai_crop) → Bronze candidate
- **10,965 legacy_v3 (Bayesian + jsonl_v11) → REJECTED** (cost save)
- 2,160 legacy_v3 null source → pending (hold)

**Migration SQL hazır** (Convention v3 deploy sonrası çalıştırılır).

### D) Convention v3 (bronze_clean) hazır

`docs/quality_review_status_convention_v3.md` + `backend/alembic/versions/20260514_quality_review_status_v3_bronze.py`.

**Deploy zamanı:** Faz 1.6 (Bronze migration) öncesi. Faz 1.5 audit sonrası deploy edilir.

### E) Pipeline-fix %84.7 mümkün (kanıtlandı)

`audit_missing_image_v2.py` 49,313 missing-image satır incelemesi:
- 16,440 (%33.3) exact_match → URL populate yeter
- 25,337 (%51.4) page_match_other_q → text similarity matcher
- 7,510 (%15.2) q_no=null orphan
- 499K disk crop var, sadece 58.5K linked → büyük kazanç fırsatı

---

## 4. LIVE DB STATE (14 May 2026)

```
question_bank: 187,834 toplam (167,559 aktif)

Quality status dağılımı:
  unverified            146,387
  legacy_v3_unaudited    18,397
  pending                 2,775

unverified iç dağılım:
  v4.14e Gemini Flash     107,516 (no Bayesian, no image, ai_extras dolu)
  +book_key+image          38,477 (page_inline source — best non-judge subset)
  no_match no_image           379
  +crossval+image              15

v_safe_for_beta = 0 (Convention v2 deploy, henüz human_verified yok)
```

---

## 5. SIRADAKİ ADIM — FAZ 1 PIPELINE-FIX SPRINT

### TaskList Durumu

50 task, 9 completed, 41 pending. Faz 1'de 7 ana task:

| # | Task | Süre | Önemli notlar |
|---|---|---|---|
| **#18 Faz 1.1** | **Tier C image matcher (16,440 exact_match)** | **4-6 saat** | **EN KESIN KAZANIM, ÖNERİLEN İLK ADIM** |
| #54 Faz 1.9 | Book key cross-reference audit | 1-2 gün | wrong_answer'ın %40 yakalar (cheap) |
| #42 Faz 1.4 | Sanity checker (duplicate options + answer-fits) | 1 gün | Convention v3 ile birlikte deploy |
| #31 Faz 1.2 | Tier D image matcher (25,337 page_other_q) | 1.5 gün | Text similarity, Tier C'den sonra |
| #50 Faz 1.8 | Symbolic math verifier (SymPy) | 3-5 gün | Wrong_answer için 2. layer |
| #39 Faz 1.3 | OCR text validator | 1 hafta | Düşük öncelik (cut-off rate %2.15) |
| #4 Faz 1.6 | Bronze tier promotion migration | 1 gün | **BLOCKED:** Faz 0.6 deploy + Faz 1.5 sonrası |
| #48 Faz 1.7 | q_no=null orphan recovery (7,510 satır) | 1-2 gün | Faz 1.5 sonrası |

### Önerilen Sıra (yeni oturum için)

**Önce şunu yapılabilir hızlı kazanç paketi:**

1. **#18 Tier C image matcher** (4-6 saat)
   - `backend/scripts/populate_image_urls.py`'a 3. tier ekle
   - Pattern: `<book>_p<page:04d>_q<qno:02d>.png` exact match
   - --dry-run zorunlu, --apply onaylı
   - Beklenen: +16,440 satıra `question_image_url` populate
   - **Ön doğrulama:** `audit_missing_image_v2.py` zaten kanıtladı, %100 match

2. **#54 Book key cross-reference audit** (1-2 gün)
   - answers_v8.db (88K cevap key) ile question_bank.correct_answer karşılaştır
   - Match → `pipeline_metadata.book_key_match=true` flag
   - Mismatch → `wrong_answer` candidate
   - **Etki:** Faz 5/6 judge cost azalır, wrong_answer'ın %40'ı yakalanır

3. **#42 Sanity checker** (1 gün) + **Convention v3 deploy**
   - Duplicate options detection
   - Answer A-E içinde kontrol
   - `pipeline_metadata.sanity_flags` field eklenir
   - Convention v3 Alembic migration ile birlikte deploy edilebilir

Bu 3 task ~4-5 gün, hepsi bittikten sonra Faz 1.5 audit (#3) çalıştırılır, sonra Faz 1.6 Bronze migration (#4).

---

## 6. KRİTİK DOSYALAR (REFERENS)

### Plan & Karar
- `docs/quality_pool_plan_v1.md` — KANONIK PLAN, KPI revize edilmiş
- `docs/quality_review_status_convention_v3.md` — Convention spec
- `docs/pool_categorization_decision.md` — 56K satır tier karar
- `docs/bayesian_validator_audit_RESULT.md` — Bayesian REPLACE kararı
- `docs/ocr_truncation_root_cause.md` — Methodology hata kanıtı

### Audit Artefaktları
- `backend/_pilots/20260514_audit_C1_C2_C3_COMBINED_RESULT.md` — 110 sample sentez
- `backend/_pilots/20260515_audit_C{1,2,3}_SCORING.tsv` — pre-analysis scoring
- `backend/_pilots/_apply_C{1,2,3}_scoring.py` — idempotent re-apply
- `backend/_pilots/audit_missing_image_v2.py` + RESULT — pipeline-fix kanıt
- `backend/_pilots/20260515_SCORING_GUIDE.md` — gelecek audit'ler için rubric

### Code/Migration
- `backend/alembic/versions/20260515_quality_review_status_v2_convention.py` — v2 (deployed)
- `backend/alembic/versions/20260514_quality_review_status_v3_bronze.py` — v3 (HAZIR, deploy bekliyor)
- `backend/migrations/D2_legacy_approved_downgrade.sql` — v2 data migration (deployed)
- `backend/migrations/D4_safe_for_beta_human_verified_only.sql` — v2 view (deployed)
- `backend/scripts/populate_image_urls.py` — Tier A+B mevcut, Tier C+D buraya eklenecek

### Rules
- `.claude/rules/audit-methodology.md` — YENİ, audit TSV truncate yasağı
- `.claude/rules/case-convention.md` — Subject identifier kuralı
- `.claude/rules/debugging-first.md` — Root cause analysis tablosu
- `.claude/rules/golden-flows.md` — CI gate kuralı

---

## 7. RECOMMENDED FIRST COMMANDS (YENİ OTURUM)

```bash
# 1. State doğrulama
git log --oneline -5
git status -sb

# 2. Live DB state quick check
PGPASSWORD=1470 "/c/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2 -c "
SELECT quality_review_status, COUNT(*) FROM question_bank
WHERE is_active = TRUE GROUP BY quality_review_status ORDER BY 2 DESC;"

# 3. TaskList oku
# (Claude tool: TaskList)

# 4. Önerilen ilk task
# Tool: TaskUpdate #18 in_progress
# Read: backend/scripts/populate_image_urls.py (Tier A+B mevcut, Tier C ekle)
# Read: backend/_pilots/20260515_missing_image_v2_RESULT.md (16,440 exact_match listesi)
```

---

## 8. WORKFLOW REMINDERS

### Karpathy
- Önce düşün — varsayım yapma, DB'den/koddan doğrula (audit methodology error öğrettiği gibi)
- Önce sadelik — istenmedikçe abstraction ekleme
- Cerrahi müdahale — sadece task scope'una dokun
- Hedef-odaklı — verifiable success criteria

### Insan-döngüsü
- Hüseyin: "DEVAM ET" / "ONAYLIYORUM" / "B" gibi kısa onaylar
- Plan değişikliği için onay zorunlu
- Mekanik yürütme onay sonrası akar

### Hard rules
- DB port 5434 (native PG18, kiro2 db)
- `question_bank` (167K aktif) ✅, `questions` (boş, legacy) ❌ kullanma
- `KullaniciServisi` DEPRECATED, `db_manager.get_session()` kullan
- Türkçe SQL: `psql -f dosya.sql` (inline `-c` Türkçe karakteri bozar)
- Türkçe commit mesajı: `.commit_msg_tmp.txt` + `git commit -F` veya HEREDOC

### Audit/test rules
- Audit sample TSV'de `LEFT(text, N)` YASAK (yeni rule)
- Sample bulgularını DB-level evren ile doğrula
- Methodology bölümü her RESULT'a zorunlu

---

## 9. SORULAR (yeni oturum sorabilir)

**S: "Şu an neredeyiz?"**
A: Faz 0 tamam (9/9). Faz 1 sprint başlıyor. 50 task, 41 pending. Önerilen ilk: #18 Tier C image matcher.

**S: "Quality pool stratejisi nedir?"**
A: Sapphire/Gold/Bronze tier + audit harness. Detay: `docs/quality_pool_plan_v1.md`. Bayesian REPLACE, judge tek karar mercii.

**S: "v_safe_for_beta neden 0?"**
A: Convention v2 sadece `human_verified` + `auto_judged_high` kabul ediyor. Curator UI henüz yok (Faz 3), judge henüz yok (Faz 5). İlk Sapphire Faz 4'te (~200 satır), ilk Gold Faz 6'da (~30-50K).

**S: "Bayesian validator değiştirilmeli mi?"**
A: Evet, REPLACE kararı verildi (Faz 0.9 audit %26 precision). Faz 5.7 hybrid iptal. Detay: `docs/bayesian_validator_audit_RESULT.md`.

**S: "Cost projection?"**
A: ~$600-1,700 toplam LLM API + ~95-135 saat insan emek (curator). Beta-safe pool sonu: 30-55K. Detay: `docs/quality_pool_plan_v1.md` Toplam bölümü.

---

## 10. KAPANIŞ NOTU

Bu oturum 1 günde **9 task tamamladı**, **3 strateji-değiştirici karar aldı** (audit methodology, Bayesian REPLACE, pool categorization), **1 yeni rule yazdı**, **5 commit push etti**. Faz 0 foundation katı kuruldu.

Faz 1 sprint'leri data-driven: her büyük task öncesi audit çıktısı zaten elimde. Tier C image matcher en kesin kazanım, oradan başlamak risk-free.

**Yeni oturum açıldığında:** bu dosyayı + `.claude/sessions/latest.md` + `MEMORY.md` Session 156 entry'sini oku, sonra `TaskList` çalıştır, #18 ile başla.

🎉 İyi çalışmalar.

---

*Generated by Session 156 closing. Detailed handoff for Session 157 continuation.*
