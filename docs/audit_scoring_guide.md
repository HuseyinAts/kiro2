# Audit Scoring Guide — Reusable Template

**Tarih:** 16 May 2026 (Plan v1 Faz 2.2)
**Önkoşul:** Bir audit harness (Faz 2.1, C1/C2/C3 audit'leri, weekly_audit) `*_RAW.tsv` çıktısı üretmiş.
**Hedef:** Manuel scoring iş akışını standartlaştır — her hafta/sample aynı tip çıktı.

---

## İş Akışı (3 adım)

```
1. RAW.tsv → SCORING.tsv      (script üretir, 3 boş kolon append)
2. SCORING.tsv'yi doldur      (Excel/LibreOffice/text editor)
3. SCORING.tsv → SUMMARY.md   (script özet üretir, validation içerir)
```

### Adım 1 — Hazırla (otomatik)

```bash
python -m backend.scripts.quality.scoring_template --prepare <RAW>.tsv
```

Sonuç: `<RAW>_SCORING.tsv` (orijinal kolonlar + `verdict` + `error_type` + `notes`).

### Adım 2 — Doldur (manuel, ~30-50 satır/saat)

Excel/LibreOffice'te aç → **"Veri" > "Metinden Sütunlara" > Tab delimiter** seç (multi-line cells doğru gözüksün). Son 3 kolonu doldur:

| Kolon | Zorunlu | İçerik |
|---|---|---|
| `verdict` | ✅ | `pass` / `fail` / `unclear` — küçük harf, başka değer YASAK |
| `error_type` | verdict=fail/unclear için ✅ | Aşağıdaki taksonomi tablosundan biri |
| `notes` | opsiyonel | Serbest Türkçe, kısa (1-2 cümle) |

### Adım 3 — Özetle (otomatik)

```bash
python -m backend.scripts.quality.scoring_template --summarize <RAW>_SCORING.tsv

# Strata bazında kır (örn. subject_area, source_book):
python -m backend.scripts.quality.scoring_template --summarize <RAW>_SCORING.tsv --strata-col subject_area

# RESULT.md'ye yaz:
python -m backend.scripts.quality.scoring_template --summarize <RAW>_SCORING.tsv --output RESULT.md
```

Script otomatik **validation** yapar: invalid verdict, invalid error_type, inconsistent satırlar (pass + error_type dolu veya fail/unclear + boş error_type).

---

## Taksonomi

### `verdict` (3 değer + boş)

| verdict | Anlam | Beta'ya etki |
|---|---|---|
| `pass` | Audit hedefi karşılandı (örn. cevap doğru, diyagram gereksiz) | Beta'ya alınabilir |
| `fail` | Audit hedefi karşılanmadı (problem tespit edildi) | Reject veya re-curate |
| `unclear` | Karar veremedim (kitaba bakmam lazım, hesaplayamadım) | Curator queue'ya at |
| `_empty` | Henüz skor verilmedi | İşlem bekliyor |

### `error_type` (8 değer + boş)

`verdict ∈ {fail, unclear}` ise zorunlu:

| error_type | Anlam | Örnek |
|---|---|---|
| `missing_diagram` | Görsel gerekli ama `question_image_url` boş | "Boyalı A alanı" — şekil yok |
| `ocr` | Soru metni OCR bozulması, eksik harf, anlamsız | "matematik" → "matemat,k" |
| `wrong_answer` | Cevap matematik/mantık olarak yanlış | "3·4=12" cevap "D=14" |
| `incomplete` | Soru eksik bilgi (hesaplanamaz) | "log a=2 verilmiş, log b sorulmuş ama verilmemiş" |
| `wrong_topic` | `subject_area` soru içeriğiyle uyuşmuyor | TARIH etiketli ama kimya |
| `duplicate_option` | Şıklarda tekrarlı cevap | A=10, C=10 |
| `garbage_text` | Soru tamamen anlamsız/saçma | "perişanın davranışları nasıldır?" |
| `other` | Yukarıdakiler dışı — `notes` ile açıkla | — |

`verdict=pass` ise `error_type` BOŞ olmalı (script inconsistency uyarısı verir).

---

## Workflow Tips

1. **Sırayla gitme zorunluluğu yok** — önce kolaylar (text-only matematik, kısa Türkçe), sonra zorlar (geometri, görsel).
2. **Şüphede `unclear`** — false pass'tan iyidir, curator queue'ya atılır.
3. **`notes` serbest** — kısa Türkçe, kuşkunu yazabilirsin: "B doğru görünüyor, A saçma".
4. **Strata sample'ı dengeli olsun** — `--strata-col` ile her stratada en az 5-10 örnek beklenir; az ise bias olur.
5. **Source crop'lara bak (opsiyonel)** — kararsızsan `d-dataset/output/crops/<book>/p<page>_*.png` aç.

---

## Hız Beklentisi (Faz 2.6 baseline)

- Hedef: **30-50 satır/saat** (Plan v1 revize: 20-40)
- 30 satırlık haftalık audit → ~45 dakika
- 200 satırlık Faz 4.1 curated set → ~4-7 saat (birden fazla seansa böl)
- Yorgunluk: 50+ satır tek seansta hata oranı artar; 30 satır seans + mola.

---

## Validation Uyarıları

`--summarize` çıktısında ⚠️ görünürse:

| Uyarı | Sebep | Düzeltme |
|---|---|---|
| **Invalid verdict** | `Pass` (büyük harf), `geçti`, vs | TSV'i edit: küçük harf, tam değer |
| **Invalid error_type** | Tanımsız değer (örn. `missing_image`) | Taksonomi tablosuna uygunlu seç |
| **Inconsistent: pass + error_type** | Yanlışlıkla error_type kaldı | error_type kolonunu boş yap |
| **Inconsistent: fail + empty error_type** | Skor eksik | error_type'ı doldur |

---

## Integration Points

- **Faz 2.1 (Audit Harness):** RAW TSV üretir → Faz 2.2 hazırlar
- **Faz 2.3 (Drift Dashboard):** `--summarize` çıktısını input alır (multi-hafta birleşimi)
- **Faz 2.4 (30-gün MA):** Hafta-bazlı verdict % zaman serisi
- **Faz 4.1 (200 Curated Set):** Bu template'i kullanır, stratified TSV'ye 3 kolon ekler
- **Faz 5.3 (Judge Calibration):** Manuel scoring ground truth → judge F1 hesabı

---

## Test (sanity check)

Mevcut `backend/_pilots/20260515_audit_C1_SCORING.tsv` üzerinde:

```bash
python -m backend.scripts.quality.scoring_template --summarize \
  backend/_pilots/20260515_audit_C1_SCORING.tsv
```

Beklenen: verdict dağılımı (pass/fail/unclear), 0 invalid, 0 inconsistent.

---

## Referans

- `backend/scripts/quality/scoring_template.py` — script
- `backend/_pilots/20260515_SCORING_GUIDE.md` — orijinal C1/C2/C3 specific guide (legacy)
- Plan v1 Faz 2.2 (`docs/quality_pool_plan_v1.md`)
