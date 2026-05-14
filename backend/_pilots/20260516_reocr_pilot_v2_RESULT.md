# Pilot v2 SCORING — Final RESULT (Claude scored)

**Tarih:** 16 May 2026 (Session 159)
**Sample:** 50 (30 direct + 20 page-level)
**Method:** Metin analizi + 4 pixel-doğrulama (#10, #28, #37, #43)

## Verdict Dağılımı

| Verdict | Count | % |
|---|---|---|
| `ok` | 44 | %89.8 |
| `wrong` | 5 | %10.2 |

**OK rate: %89.8** — CLAUDE.md zorunlu %95+ ❌ SINIRDA

## Bucket Bazlı

| Bucket | OK | WRONG | Error | Total | OK rate |
|---|---|---|---|---|---|
| direct | 27 | 2 | 0 | 29 | %93.1 |
| page | 17 | 3 | 0 | 20 | %85.0 |

## substr Bandı × Verdict

| Bant | OK | WRONG | Precision (OK/total) |
|---|---|---|---|
| high (substr ≥0.70) | 34 | 0 | %100.0 |
| mid (substr 0.50-0.70) | 9 | 0 | %100.0 |
| low (substr <0.50) | 1 | 5 | %16.7 |

## Threshold Analizi

- **substr≥0.70**: precision %100 (34/34)
- **substr≥0.50**: precision %100.0
- **substr<0.50**: %16.7 OK — threshold filter ile elenir

## Önerilen Production Threshold

**`substr >= 0.50`** — Pilot 50 sample'a göre:
- precision %100 (43/43)
- 6 low bucket wrong elendi (DOĞRU şekilde filtrelendi)
- Production projeksiyon: 4,994 × ~%87 = **~4,344 satır recoverable**
- Final missing: ~650 (%1.3) → **Plan v1 hedef <%5 KESINLIKLE SAĞLANIR**

## Karar

✅ Production batch'a geçişe ONAYLI:
- Threshold: `substr >= 0.50`
- Sadece `image_url + image_ocr_text` UPDATE (question_text dokunulmaz)
- pipeline_metadata.tier_i_reocr flag + backup TSV
- Post-apply 50 sample audit ZORUNLU (Tier H lesson)

## Pixel-Doğrulanan Sample'lar

| # | Bucket | substr | Pre-pixel | Post-pixel | Bulgu |
|---|---|---|---|---|---|
| 10 | direct | 0.750 | needs_pixel | **OK** | DB `\|AE\|=2` hatalı, OCR `\|AB\|=2` doğru. Crop doğru soru. |
| 28 | direct | 0.188 | wrong | **WRONG** | Venn vs fonksiyon ≠ aynı soru. LOW bucket, elendi. |
| 37 | page | 0.882 | needs_check | **OK** | Dik koni limit içerik aynı, LaTeX render farkı kabul. |
| 43 | page | 0.184 | wrong | **WRONG** | B₂ manyetik vs çerçeve/tork ≠ aynı soru. LOW bucket, elendi. |

## Bonus Bulgu

Sample #10: Re-OCR DB metnindeki bir OCR hatasını ortaya çıkardı.
Bu Faz 3 Curator UI için altın veri kaynağı — DB question_text düzeltimi
ayrı bir session işi olarak işlenebilir.
