# Tier J Pre-Audit — GEOMETRI (n=1,727)

**Tarih:** 20260515
**Source:** question_bank WHERE pipeline_metadata.tier_i_reocr.band='high' AND subject_area='GEOMETRI'

## Drift Dağılımı (qtext vs image_ocr_text)

| Bucket | Range | n | % | Tier J Yön |
|---|---|---:|---:|---|
| high_agree | >=0.90 | 134 | 7.8 | 🟢 NO-OP — qtext ve image_ocr aynı, dokunma |
| moderate_drift | 0.70-0.90 | 339 | 19.6 | 🟡 INSPECT — örnekleme + manuel |
| substantive_drift | 0.50-0.70 | 561 | 32.5 | 🟠 LIKELY UPGRADE — image_ocr büyük olasılıkla daha doğru |
| severe_drift | <0.50 | 693 | 40.1 | 🔴 PIXEL-VERIFY ZORUNLU — yüksek değişiklik, image'a karşı doğrula |
| **TOPLAM** | | **1,727** | 100.0 | |

## Tier J Apply Önerisi

🟢 **PROCEED** — 1,254 satır drift<0.70 var, kayda değer kazanım. 30 sample pixel-verify gate + Tier J apply (geometri-only, drift<0.85 + dry-run zorunlu).

## Pixel-Verify Sample

**Random 30 sample** drift<0.85 olan satırlardan export edildi: `20260515_tier_j_pixel_sample_GEOMETRI.tsv`

Pixel-verify protokolü:
1. Her sample için crop_url'i image olarak aç
2. qtext_preview ve ocr_preview yan yana karşılaştır
3. Image'a göre hangisi doğru? → ground truth işaretle
4. Eğer image_ocr 30/30 (>%90) DOĞRU ise: Tier J apply güvenli
5. Eğer karışıksa (image_ocr ~%50-70 doğru): manuel curator queue
