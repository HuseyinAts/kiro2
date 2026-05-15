# Tier I (Faz 1.10) Re-OCR Apply — Final Result

**Tarih:** 15-16 May 2026 (Sessions 159-161)
**Mode:** ThreadPool 10 worker, paid Gemini Pro tier, HIGH-only (substr ≥ 0.70)
**Plan:** [Quality Pool Plan v1](../../../docs/quality_pool_plan_v1.md) Faz 1.10
**Spec:** Re-OCR cut-off entries → image_url + image_ocr_text refresh

---

## 1. Apply Sonuçları

| Metrik | Değer |
|---|---:|
| Toplam satır işlendi | **3,008** |
| Süre | 74.2 dakika |
| Speedup vs sequential | **9.3x** (sequential ~11.7h tahmin) |
| **applied_high (DB UPDATE)** | **1,770** (%58.8) |
| mid_skip (substr 0.50-0.70) | 514 (%17.1) |
| low_skip (substr < 0.50) | 383 (%12.7) |
| gemini_error (Geometri safety) | 311 (%10.3) |
| json_fail | 29 (%1.0) |
| db_update_error | 1 (%0.0) |

### Maliyet
~$5.50 (revized estimate, Session 160 token sample analysis).

### Pre-Apply Workflow
- Sequential PID 23732 durduruldu (4.36/dk × 3008 = 11.5h ETA → kabul edilemez)
- ThreadPool versiyon (`tier_i_reocr_apply_threaded.py`, commit `c5220794f`) hazırlandı
- Smoke test 20 sample: 1.1 dk, %0 error, kalite sequential ile aynı
- Checkpoint reconstruction (smoke `--resume` olmadan checkpoint sildi → RESULT TSV'den 318 ID rebuild)
- Full apply background (PID 11580): 74.2 dk, 9.3x speedup

---

## 2. Post-Audit (Otomatik)

`backend/scripts/tier_i_postaudit.py --sample-size 50`

| Otomatik kontrol | Skor |
|---|---:|
| URL aligned | 50/50 (%100) |
| URL mismatch | 0/50 |
| Flag missing (`pipeline_metadata.tier_i_reocr.date`) | 0/50 |
| Crop dosyası diskte | 50/50 |

Not: Otomatik checks sadece DB state'i doğrular (URL pointer + flag + crop existence). **Semantic accuracy** insan pixel-verify gerektirir.

---

## 3. Pixel-Verify (Insan, n=7, Claude multimodal)

**Sample:** Random seed=42, ilk 7 satır. **Bias uyarısı:** 7/7 geometri kitabı çıktı (LaTeX-ağır subject, OCR worst-case).

| # | id (kısa) | Kitap (kısaltma) | Sayfa | Q | substr | URL✓ | image_ocr ✓ | qtext ✓ | Cevap ✓ |
|---|---|---|---:|---:|---:|---|---|---|---|
| 1 | ef8fcadf | Mikro Geometri 2025 | 154 | 7 | 0.92 | ✅ | ✅ | ✅ | ✅ C |
| 2 | 94ce6dfa | Acil Geometrinin İlacı 20-21 | 46 | 8 | 0.91 | ✅ | ✅ | ⚠️ minor (\|EDI\| typo) | ✅ C |
| 3 | c9040bff | C1CELL Geometri 2024 | 245 | 12 | 0.78 | ✅ | ✅ | 🔴 LEGACY ERR (A(ABCD) vs A(KBC)) | ✅ D |
| 4 | bbed309e | 345 Geometri 2025_1 | 303 | 13 | 1.00 | ✅ | ✅ | ✅ | ✅ E |
| 5 | bae71618 | 345 Geometri | 363 | 7 | 0.80 | ✅ | ✅ | ✅ | ✅ E |
| 6 | 9d71a398 | Orijinal Trigonometri | 25 | 9 | 0.87 | ✅ | ✅ | ✅ | ✅ B |
| 7 | e341cd59 | ACİL Geometrinin İlacı 23-24 | 84 | 10 | 0.91 | ✅ | ✅ | 🔴 LEGACY ERR (\|KI\| vs \|BK\|) | ✅ A |

### 3.1 Skor

| Doğrulama | Skor |
|---|---:|
| URL binding (Tier H rollback dersi) | **7/7** ✅ |
| `image_ocr_text` (Tier I yeni yazdı) image ile uyumlu | **7/7** ✅ |
| `correct_answer` image'deki seçenek ile aynı | **7/7** ✅ |
| `question_text` (legacy, Tier I dokunmadı) image ile uyumlu | 5/7 + 1 minor + 2 substantive |

### 3.2 KRİTİK BULGU

**Tier I image_ocr_text legacy question_text'i AŞTI.**

Sample 3 ve 7'de:
- `question_text` (eski pipeline çıktısı, Tier I dokunmadı) → ❌ image ile uyuşmuyor
- `image_ocr_text` (Tier I bu apply'da yazdı) → ✅ image ile uyuyor

Tier I sadece URL bind etmedi, aynı zamanda **legacy question_text hatalarını açığa çıkaran high-quality ground truth** üretti. Bu yeni kategori iş fırsatı: **Tier J — question_text correction from image_ocr_text**.

---

## 4. Karar Tablosu

| Konu | Karar | Gerekçe |
|---|---|---|
| HIGH apply (1,770 satır) | ✅ **PRODUCTION'DA TUTULSUN** | URL binding 7/7, image_ocr_text 7/7 doğrulandı |
| MID bant (514 satır) | ⏸️ **Pilot ile ölç (script edit + 50 sample)** | Önceki "ertele" kararı yanlış varsayımdan; doğrudan kanıt yok |
| LOW + safety_blocked (694 satır) | 📋 **Backlog** | LOW: judge'a bırak. Safety: Faz 5.8 retry pile (`safety_settings=BLOCK_NONE`) |
| Faz 1.10 (task #55) | ✅ **COMPLETED** | Birincil hedef (URL binding) gerçekleşti |
| **YENİ: question_text drift audit** | 🆕 **Faz J pre-audit** | Tüm 1,770 Tier I satırında question_text vs image_ocr_text similarity ölç |
| **YENİ: Tier J apply (drift varsa)** | 🆕 **Karar audit sonrası** | Pixel-verify + SUBSTR_APPLY kapısı (Tier H dersleri) |
| Sample bias risk | ⚠️ **Non-geometri spot-check (5-7 sample)** | 7/7 geometri → %100 LaTeX-ağır, sözel kanıt eksik |

---

## 5. Sıradaki Adımlar (priority sırası)

1. ✅ Bu RESULT commit
2. **Non-geometri stratified spot-check** (5-7 sample, ~10 dk) — bias riski çürüt
3. **question_text drift audit** (read-only SQL, ~15 dk) — Tier J fizibilite ölç
4. MID bant pilot script edit (`--substr-apply` arg eklenmeli, ~10 dk) + 50-sample apply (~12 dk)
5. Tier J script (drift rate yüksekse) — `tier_j_qtext_correction.py` (Tier I template'i klonla, target field swap)

---

## 6. Lessons Learned (gelecek kararları besler)

1. **substr metric URL binding için yeterli, semantic content için yetersiz** — substr 0.78 + 0.91'de bile critical 3-4 karakter hataları olabilir (geometri segment etiketleri)
2. **question_text ve image_ocr_text DİZİL — "DB metni" tek alan değil** — postaudit RAW'da `db_q_text_preview` ≠ `db_ocr_preview`. Pixel-verify yorumlarken hangi alanın hangi pipeline çıktısı olduğunu bilmek ŞART
3. **Sample bias takip** — random seed=42, 7/7 geometri çıktı. Stratified sampling yoksa subject-level error rate gizli kalır
4. **Karpathy "Önce Düşün" — yanlış yorum risk düşük yatırımdı bile** — ilk Pixel-verify yorumum "Tier I OCR'da %29 hata" yanlış başladı (question_text ≠ image_ocr_text). Bir adım daha düşünüp DB schema'yı doğrulamak hatayı yakaladı
5. **9.3x speedup** ThreadPool migration başarısı kanıtlandı (10 worker, paid Gemini Pro). Future Tier J/K için template hazır

---

## 7. Referans Dosyalar

- Apply RESULT TSV (3,008 satır + smoke 20): `20260516_tier_i_apply_RESULT.tsv`
- Apply BACKUP TSV (1,770 + smoke 14 = 1,784 backup row): `20260516_tier_i_BACKUP_apply.tsv`
- Apply checkpoint: `checkpoint_tier_i.json` (3,008 processed_ids)
- Apply background log: `20260516_tier_i_apply_THREADED.log`
- Post-audit n=50 RAW: `20260516_tier_i_postaudit_n50_RAW.tsv`
- Threaded script: `backend/scripts/tier_i_reocr_apply_threaded.py` (commit `c5220794f`)
- Post-audit script: `backend/scripts/tier_i_postaudit.py` (commit `bcef5c8c4`)

---

*Faz 1.10 tamamlandı. Tier J yeni keşif — pre-audit Session 161+ devam eder.*
