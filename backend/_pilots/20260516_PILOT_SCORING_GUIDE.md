# Pilot v2 Scoring Rehberi — 50 Sample Pixel-Doğrulama

**TSV:** `backend/_pilots/20260516_reocr_pilot_v2_SCORING.tsv`

## Amaç

Re-OCR pilot 50 sample (30 direct + 20 page-level). Her satır için:
- **Crop görseli açılıp DB sorusuyla pixel-bazda karşılaştırılır**
- "Doğru bind" / "Yanlış bind" / "Kısmi" verdict yazılır

Tier H lesson: pre-apply 50 sample %95+ accuracy ZORUNLU.

## Sütunlar

| Sütun | Anlam |
|---|---|
| `idx` | 1-50 sıra |
| `bucket` | `direct` (crop dosyası direkt) / `page` (sayfa görseli) |
| `id` | DB uuid |
| `book`, `page`, `q_no` | Kitap, sayfa, soru numarası |
| `image_path` | Açılacak görsel dosya yolu |
| `db_len` | DB question_text uzunluğu (karakter) |
| `db_tail80` | DB metnin son 80 karakteri |
| `ocr_text_full` | Re-OCR Gemini Pro çıktısı (tam) |
| `jaccard` | Word-level Jaccard similarity (full) |
| `substr_pct` | OCR kelimelerinin DB'de bulunma oranı |
| **`verdict_huseyin`** | **DOLDURACAK: `ok`/`wrong`/`partial`** |

## Verdict Tanımları

| Verdict | Anlam |
|---|---|
| `ok` | Crop görseli DB sorusunun crop'u, image_url BIND edilebilir |
| `wrong` | Crop görseli farklı soru, BIND yapılMAZ |
| `partial` | Crop kısmen doğru (örn: yarısı kesik), karar belirsiz |

## Scoring Adımları (her satır için ~15 sn)

1. **`image_path` sütundaki yolu kopyala** (örn: `d-dataset/output/crops/Aktif.../sayfa_0336_q06.png`)
2. **Windows Explorer'da görseli aç** veya doğrudan path'i resim viewer'a sürükle
3. **Crop görseldeki SORU metnini** `db_tail80` ile karşılaştır
   - `db_tail80` = DB'deki sorunun son 80 karakteri (genelde "kaçtır?" gibi soru sonu)
   - Crop görseldeki soru bu DB metnini içeriyor mu?
4. **`ocr_text_full`** sütununda Gemini Pro'nun crop'tan okuduğu metin var — bağlam için kullan
5. **Verdict yaz:**
   - Crop = DB sorusu → `ok`
   - Crop ≠ DB sorusu (farklı içerik) → `wrong`
   - Crop yarısı kesik / kısmen doğru → `partial`

## Hızlı Yargı Kuralları

| Pattern | Öneri |
|---|---|
| `substr_pct >= 0.80` ve OCR sonu DB tail ile uyumlu | Muhtemelen `ok` |
| `substr_pct >= 0.50` ama OCR'da DB'de olmayan kavramlar | Muhtemelen `wrong` |
| `bucket=page` ve sim >=0.70 | Genelde `ok` (Pro tam sayfada doğru soruyu buldu) |
| OCR çok kısa (<30 char) | Muhtemelen `partial` (crop incomplete) |

## Hedefler

- **%95+ ok** → threshold belirlenir, production batch
- **%80-95 ok** → threshold yükselt (>=0.70), partial production
- **<%80 ok** → strateji yeniden değerlendir, Re-OCR güvensiz

## Sonraki Adım

Scoring tamamlanınca, ben TSV'yi yeniden okuyup:
1. Verdict dağılımı raporu
2. substr threshold optimizasyonu (Precision-Recall trade-off)
3. Production batch hazırlığı (3,323 + 1,667 satır)

Tahmini scoring süresi: 50 sample × ~15 sn = **~12 dakika**.
