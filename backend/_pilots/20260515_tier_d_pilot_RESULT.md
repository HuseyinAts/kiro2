# Tier D Image Matcher — Pilot RESULT

**Tarih:** 15 May 2026 (Session 158)
**Script:** `backend/scripts/tier_d_image_matcher.py`
**Pilot TSV:** `backend/_pilots/20260515_tier_d_pilot_RESULT.tsv`
**Plan v1 referans:** Faz 1.2

## TL;DR

- **Accuracy: %96** (96 ok / 1 wrong / 3 unclear)
- **Plan v1 gate (%95+): PASS** → full run onaylandi
- Threshold 0.70, D1+D2 fallback aktif

## Pilot konfigürasyon

| Parametre | Değer |
|---|---|
| Similarity threshold | 0.70 (Jaccard, NFC normalize) |
| D2 fallback | aktif (aynı page'de en yüksek similarity) |
| Sample N | 100 |
| Random seed | 42 |

## Sonuç dağılımı

| Verdict | n | Açıklama |
|---|---|---|
| ok | 96 | DB ve OCR text aynı soru |
| wrong | 1 | Yanlış match (false positive) |
| unclear | 3 | Borderline (OCR varyasyonu vs farklı soru) |

## False positive analizi

### wrong (1 satır)

**id=`74cf7fed-4140-5b5e-8a88-89a61976050a`** (sim=0.776, D1)
- Book: `Full Matematik-Tyt-Matematik Soru Bankası`, page=27, db_q_no=9, ocr_soru_no=9, crop_q_no=2
- DB text: "Yukarıdaki tabloda **6 rakamından** başlanarak çapraz gidilmeden..."
- OCR text: "Yukarıdaki tabloda **9 rakamından** başlanarak çapraz gidilmeden..."
- **Root cause**: Math template repetition — sayfa aynı şablonu kullanan birden fazla soru içeriyor (6 vs 9 rakamından başlayan iki versiyon). Jaccard %77.6 yüksek çünkü template ortak ama parametre farklı = farklı soru.

### unclear (3 satır)

**id=`91adde2b-ba9e-518c-957a-7a33aa2e75ca`** (sim=0.765, D1)
- DB: "$-Q$ yükünün A noktasındaki elektriksel potansiyeli 20 volt..."
- OCR: "+Q yükünün A noktasındaki elektriksel potansiyeli 20 volt..."
- Yük işareti `-Q` vs `+Q` — fizik problemi için kritik fark. OCR'da zayıf `-` karakteri mi yutuldu, yoksa farklı soru mu emin değil.

**id=`56db9d93-0290-5104-9a51-330e380adefc`** (sim=0.857, D1)
- DB: "...Kenarları düz aynalarda..."
- OCR: "...Gelen ışın ... Yansıyan..."
- İlk cümle aynı ama devamlar farklı görünüyor.

**id=`e0f301c7-0f9a-509a-b01c-d3429bdf6859`** (sim=0.704, D1)
- DB: "P ağırlığındaki çocuk il(e)"
- OCR: "O noktasındaki 3P ağırlığında"
- Sayı/varlık farkı: P (çocuk) vs 3P. Borderline, threshold sınırında.

## Risk bucket analizi

0.70-0.80 similarity bucket'ında **1 wrong + 3 unclear = 4/32 sorunlu** (~%12.5). Yüksek similarity bucket'larında (0.85+) sorun bulunmadı.

**Karar**: 0.70 threshold ile devam. False-positive %1, unclear %3 toplam ~%4 risk kabul edilebilir (Plan v1 hedef %95+ geçildi). Bu satırlar `pipeline_metadata.tier_d_match.similarity` ile flag'leniyor — judge sonradan düşük-sim'leri öncelikli inceleyebilir.

## Methodology

Audit yöntemi (Karpathy "ezbere yorum yapma" + audit-methodology.md):
1. TSV'deki `db_text_preview` (ilk 100 char) vs `ocr_text_preview` (ilk 100 char)
2. Anahtar kelimeler, sayılar, varlık adları, yapı karşılaştırması
3. Math template repetition için ek dikkat (sayfada aynı şablon farklı parametreler)
4. Conservative: emin olunmayan durumlar `unclear` (silent assume `ok` etme)

Audit eden: Claude (Session 158). Pixel-level görsel doğrulama (crop PNG açma) yapılmadı — sadece text preview karşılaştırması. Full apply sonrası random 30 sample re-audit Plan v1 Faz 1.5'te yapılacak.

## Sonraki adım

`python scripts/tier_d_image_matcher.py --apply` ile full run:
- 13,741 satır UPDATE (12,955 D1 + 269 D2 + 517 D1_q_shifted_extra)
- `question_image_url` populate
- `pipeline_metadata.tier_d_match` flag (tier, similarity, ocr_soru_no, crop_q_no, crop_file, audit_date)
