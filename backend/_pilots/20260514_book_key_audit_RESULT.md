# Book Key Cross-Reference Audit RESULT

**Tarih:** 14 May 2026 (Session 157, Faz 1.9 pilot)
**Method:** `answers_v8.answers_page_inline` (78,720 satır, source=page_inline OCR conf=0.85) ↔ `question_bank.correct_answer` (167K aktif)
**Çıktı:** A1 defansif flag stratejisi onayı + Plan v1 etki revizyonu

---

## TL;DR

- **Coverage:** 92,293 qbank joinable satır × 78,720 SQLite key → 16,159 match (%17.5). 76,134 (%82.5) no_key.
- **Match kalitesi:** agree=7,425 (%45.9), disagree=8,734 (%54.1).
- **8-sample pixel-doğrulama:** 7/8 SQLite doğru, 1/8 qbank doğru → SQLite confidence %87.5, qbank confidence %12.5.
- **KARAR:** **A1 defansif strateji** — agree=high-conf flag, disagree=needs_review flag.
  A2 (SQLite ile UPDATE correct_answer) reddedildi: ~1,090 satır yanlış UPDATE riski beta-safe değil.
- **Plan v1 revize:** "Wrong_answer %40 yakalama" → gerçek **%13** (~7,600 satır pre-flag of ~57K toplam).

---

## Methodology

| Item | Detay |
|---|---|
| Pilot script | Ad-hoc Python, `sqlite3` + `sqlalchemy` (read-only) |
| Sample SQL (qbank) | `WHERE is_active=TRUE AND source_book IS NOT NULL AND source_page IS NOT NULL AND ai_extras.q_no ~ '^[0-9]+$' AND correct_answer IS NOT NULL` |
| Sample SQL (sqlite) | `SELECT book_name, page_number, question_number, answer FROM answers_page_inline` (78,720 row, full scan) |
| Join key | `(book_name, page_number, question_number)` triple — naive (no normalize) |
| Naive vs normalized | 398/410 books overlap NAIVE = 398 NORMALIZE → no benefit |
| Manuel doğrulama | PDF screenshot crop alt-orta strip (x:20-85%, y:85-95%) × 3x LANCZOS upscale |
| Sample seed | 123 (random.shuffle for cross-book coverage) |
| Reproducible | Evet — script tek tek satır işliyor, deterministic dict |

**audit-methodology.md uyum:** Truncate yapılmadı, full text export. Sample bias not edildi (5/8 Mikro Geometri overrepresent).

---

## Pilot Sonuçları

```
qbank_total:   92,293
matched:       16,159 (17.5%)
no_key:        76,134 (82.5%)
  -> agree:    7,425 (45.9%)
  -> disagree: 8,734 (54.1%)
```

**Status breakdown** (matched satırlar yalnız `unverified` populasyonunda — `legacy_v3_unaudited` ve `pending` SQLite ile join etmiyor; muhtemelen book_name normalize farkı):

| status | matched | agree | disagree | agree% |
|---|---|---|---|---|
| unverified | 16,159 | 7,425 | 8,734 | 45.9% |
| legacy_v3_unaudited | 0 | 0 | 0 | — |
| pending | 0 | 0 | 0 | — |

---

## Naive Book Match Analizi

```
SQLite unique books: 410
qbank unique books:  416
NAIVE intersection:  398 (97.1% / 95.7%)
NORMALIZED:          398 (no extra benefit)
```

**SQLite-only books (12):** Encoding bozuk olanlar console artifact + 12 kitap question_bank'ta yok (yeni eklenmiş veya silinmiş).
**qbank-only books (18):** Smoke test + 2024-2025 yeni eklemeler + ASCII fallback adlı kitaplar.

→ **Naive join yeterli, NFC/Turkish-fold normalize gereksiz.**

---

## 8-Sample Pixel-Doğrulama

Her sample PDF screenshot `sayfa_NNNN.png` alt strip crop + 3x upscale ile manuel okundu. Cevap satırı format `1.X 2.X 3.X ...`.

| # | Kitap | Sample | qb | SQLite | **Gerçek (pixel)** | Doğru kim |
|---|---|---|---|---|---|---|
| 1 | Mikro Orijinal-2025-Ayt-Geometri | p287 q01 | B | E | **E** | SQLite ✓ |
| 2 | Mikro Orijinal-2025-Ayt-Geometri | p287 q02 | B | D | **D** | SQLite ✓ |
| 3 | Mikro Orijinal-2025-Ayt-Geometri | p292 q03 | D | C | **C** | SQLite ✓ |
| 4 | Mikro Orijinal-2025-Ayt-Geometri | p296 q01 | C | D | **D** | SQLite ✓ |
| 5 | Mikro Orijinal-2025-Ayt-Geometri | p296 q02 | D | A | **A** | SQLite ✓ |
| 6 | 345 Tyt Biyoloji Soru Bankası | p178 q02 | B | E | **E** | SQLite ✓ |
| 7 | 345 Tyt Ayt Geometri Soru Bankası | p47 q06 | A | C | **A** | **qbank ✓** |
| 8 | Full Matematik 2022-2023 Tyt Ayt Geometri | p151 q07 | C | D | **D** | SQLite ✓ |
| (skip) | ACİL-2025-TYT, Sure Edebiyat 2025 | — | — | — | offset | — |

**Sample bias:** 5/8 = Mikro Geometri 2025 (pilot script ardışık iteration sample sortu). Diğer 3 sample farklı kitap+konu+yayınevi → çapraz teyit.

**ACİL/Sure skip nedeni:** Bu kitaplarda **PDF page ≠ içerik page offset** var (örn ACİL `sayfa_0320.png` içeriği p315). Doğru sayfayı bulmak ek 5+ dk gerektirdi, atlandı. Pilot script bu offset'i bilmediği için bu kitaplar zaten naive matching'te düşük performans göstermiş olabilir.

---

## Key Bulgular

1. **Mismatch'in çoğu qbank wrong (%87.5)** — Gemini Flash AI üretimi (107K v4.14e batch, no Bayesian) sistematik hata gösteriyor.
2. **SQLite tek başına ground truth değil (%12.5 yanlış)** — page_inline OCR conf=0.85 etiketli ama gerçek doğruluk daha düşük.
3. **Mikro Geometri 2025 sistematik qbank wrong pattern** (5/5) — bu kitap özelinde Gemini Flash'ın geometri sorularında zayıflığı veya batch-spesifik hata.
4. **PDF page ≠ içerik page offset** bazı kitaplarda (ACİL, Sure). Pilot script bu offset'i bilmediği için bu kitaplar matching'te yanılır.
5. **legacy_v3_unaudited / pending status'ları SQLite ile join etmiyor** — book_name normalize farkı muhtemel sebep, ek inceleme Faz 2.x audit'inde.

---

## Strateji Kararı: A1 (Defansif)

| | A1 Defansif (SEÇİLDİ) | A2 Agresif (REDDEDİLDİ) |
|---|---|---|
| agree (7,425) | `book_key_match=agree` flag, judge bypass adayı | aynı |
| disagree (8,734) | `book_key_match=disagree` flag, judge'a YÜKSEK öncelik | SQLite ile UPDATE `correct_answer` |
| Risk | Judge'a +8K satır zorunlu (cost +$50) | %12.5 × 8,734 = ~1,090 satır yanlış UPDATE → beta'ya bozuk soru |
| Karpathy uyum | "önce sadelik" + "cerrahi müdahale" | spekülatif değişiklik, dataset bozulur |
| Geri alınabilir | flag → toggle | UPDATE → backup restore gerekir |

**A2 reddedildi:** Beta soft launch'a 1,090 yanlış cevap kabul edilemez. Faz 0.2 audit %34 wrong_answer baseline'ı zaten yüksek; agresif fix bunu daha kötüleştirir.

---

## Plan v1 Etki Revizyonu

| Metric | Plan v1 iddia | Pilot gerçek |
|---|---|---|
| "Match coverage" | implicit ~50% | %17.5 (76K no_key) |
| "Wrong_answer %40 yakalama" | %40 of qbank wrong → ~22.7K satır pre-flag | 8,734 disagree × %87 = ~7,600 satır → **%13 yakalama** |
| Audit baseline (Faz 0.2 C2) | qbank %34 wrong → ~57K toplam | aynı |
| Judge cost save | "$150-300" | agree 7,425 bypass × ~$0.007/judge = **$50** |
| Curator değer | implicit | disagree 8,734 → curator priority queue (yüksek değer) |

**Yeni değer önerisi:** "%13 wrong_answer pre-flag + %4.4 high-conf bypass + curator priority queue". Plan v1'in "ucuz kazanım" iddiası **kalitatif olarak doğru** ama nicel olarak abartılmış.

---

## Implementation Notları (Sonraki Adım)

**Script:** `backend/scripts/book_key_cross_reference.py`

**Pattern (Tier C kanonik formatına uygun):**
```python
# Phase 1: SQLite RAM dict
sqlite_dict[(book, page, qno)] = {"answer": "E", "confidence": 0.85}

# Phase 2: question_bank fetch (joinable subset)
for qb_row in fetch_qbank():
    key = (qb_row.source_book, qb_row.source_page, qb_row.q_no)
    if key in sqlite_dict:
        sqlite_ans = sqlite_dict[key]["answer"]
        flag = "agree" if sqlite_ans == qb_row.correct_answer else "disagree"
        results.append({
            "id": qb_row.id,
            "book_key_match": {
                "status": flag,
                "sqlite_answer": sqlite_ans,
                "qbank_answer": qb_row.correct_answer,
                "source": "answers_v8.page_inline",
                "audit_date": "2026-05-14",
            }
        })

# Phase 3: JSONB merge UPDATE (idempotent)
UPDATE question_bank
SET pipeline_metadata = jsonb_set(
    pipeline_metadata::jsonb,
    '{book_key_match}',
    :flag_jsonb,
    TRUE
)
WHERE id = :id
```

**Idempotency:** `jsonb_set ... CREATE_IF_MISSING=true` → aynı satır tekrar yazılırsa overwrite (yeni audit_date ile).

**Hedef etki:** 16,159 satıra `book_key_match` field eklenir. Faz 5/6 judge config:
- agree → judge bypass (high-conf, only 5% spot-check sample audit)
- disagree → judge öncelikli queue + curator review priority

---

## Reproducibility

```bash
# Pilot rerun (read-only, no DB write)
cd C:/Users/husey/kiro2/backend
python -c "$(cat ../docs/audits/2026-05-14_book_key_pilot_inline.txt)"

# Manuel pixel-doğrulama (8 sample crops)
ls C:/Users/husey/kiro2/backend/_pilots/_tmp_answer_inline/
# - p0287_answer_inline.png, p0292_answer_inline.png, p0296_answer_inline.png (Mikro Geometri)
# - 345_Tyt_Biyoloji_p0178_inline.png
# - 345_Tyt_Ayt_Geometri_p0047_inline.png
# - Full_Matematik_2022_2023_p0151_inline.png
```

---

## İlişkili Dosyalar

- `.claude/rules/audit-methodology.md` — bu RESULT'in uyduğu kural
- `docs/quality_pool_plan_v1.md` — Faz 1.9 etki rakamları **revize edilecek** (sonraki adım)
- `backend/scripts/book_key_cross_reference.py` — implement (sonraki adım)
- `backend/_pilots/20260515_audit_C1_C2_C3_COMBINED_RESULT.md` — qbank %34 wrong_answer baseline
- `backend/_pilots/20260515_missing_image_v2_RESULT.md` — Tier C complement audit
- `backend/_pilots/_tmp_answer_inline/` — 8 sample crop görselleri (gitignored, manuel inceleme)

---

*Generated by Session 157 Faz 1.9 pilot. Read-only audit.*
