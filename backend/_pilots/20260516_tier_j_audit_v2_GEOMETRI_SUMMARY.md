# Tier J Pre-Audit v2 — Format-Aware (GEOMETRI, n=1,727)

**Tarih:** 20260516
**v1 referans:** `_pilots/20260515_tier_j_audit_GEOMETRI_RAW.tsv` (substring_overlap, LaTeX-aware DEĞİL)
**v2 yeni:** Format-aware (LaTeX → Unicode normalize, sonra similarity)

## v1 vs v2 Drift Dağılımı

| Bucket | Range | v1 n | v1 % | v2 n | v2 % | Delta |
|---|---|---:|---:|---:|---:|---:|
| high_agree | >=0.90 | 134 | 7.8 | 404 | 23.4 | ++270 |
| moderate | 0.70-0.90 | 339 | 19.6 | 463 | 26.8 | ++124 |
| substantive | 0.50-0.70 | 561 | 32.5 | 560 | 32.4 | -1 |
| severe | <0.50 | 693 | 40.1 | 300 | 17.4 | -393 |

## v1 → v2 Transition Matrix

Önemli: v1'de drift gösteren satırların kaçı v2 ile high_agree'ye yükseldi?

| v1 bucket | v2 bucket | n |
|---|---|---:|
| severe_drift | v2_substantive | 334 |
| severe_drift | v2_severe | 297 |
| substantive_drift | v2_moderate | 237 |
| substantive_drift | v2_substantive | 211 |
| moderate_drift | v2_moderate | 162 |
| moderate_drift | v2_high_agree | 162 |
| high_agree | v2_high_agree | 121 |
| substantive_drift | v2_high_agree | 110 |
| severe_drift | v2_moderate | 51 |
| moderate_drift | v2_substantive | 15 |
| high_agree | v2_moderate | 13 |
| severe_drift | v2_high_agree | 11 |
| substantive_drift | v2_severe | 3 |

## Format-Bias Düzeltmesi

- **v1 drift>0.10 ('not high_agree')**: 1,593 satır (92.2%)
- **v2 drift>0.10 ('not high_agree')**: 1,323 satır (76.6%)
- **Format-bias false positive**: 270 satır artık no-drift

## Tier J Apply Önerisi (v2)

🟢 **JUDGE-FIRST** — v2 860 satır gerçek content drift, manuel/heuristic için fazla. Strateji C (judge pipeline ~$25 cost) önerilen.

## Pixel-Verify v2 Sample

Random 30 sample v2 drift<0.85'ten export edildi: `20260516_tier_j_pixel_sample_v2_GEOMETRI.tsv`

**Bu sample önceki Round 3 (n=30) sample'ından FARKLI** — v2 normalization format-bias'ı düzelttiği için yeni gerçek content drift satırlarını öne çıkarır.
