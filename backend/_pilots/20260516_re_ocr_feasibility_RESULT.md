# Re-OCR Feasibility Audit — 16 May 2026

**Total missing satır**: 4,994

## Bucket Dağılımı

| Bucket | Count | % | Re-OCR Strategy |
|---|---|---|---|
| `jsonl_var_metin_var_disk_var` | 3,323 | %66.5 | ✅ **Disk crop var, OCR var ama sim<0.50 → Re-OCR ile düzelt** |
| `jsonl_yok` | 1,667 | %33.4 | ⚠️ jsonl'da yok → Page-level Re-OCR (full sayfa görseli işle) |
| `jsonl_var_metin_bos_disk_var` | 3 | %0.1 | ✅ **Disk crop var, OCR boş → Direct Re-OCR (en kolay)** |
| `jsonl_var_disk_yok` | 1 | %0.0 | ⚠️ Disk eksik — jsonl ile silinmiş crop? Skip veya page Re-OCR |

## jsonl Global Stats

- Total jsonl rows: 333,690
- Empty OCR (soru_metni=""): 12,891 (%3.9)

## Top 10 Book (en çok missing)

| Book | match/total | match_rate |
|---|---|---|
| C1CELL-2024-TYT-AYT-Geometri Soru Bankası | 244/265 | %92.1 |
| Mikro-2024-Tyt Ayt-Geometri Soru Bankası | 224/244 | %91.8 |
| Orijinal-2024-Geometri Soru Bankası | 195/229 | %85.2 |
| 345 2025 Tyt Ayt Geometri Soru Bankası 1 | 176/228 | %77.2 |
| 2020-2021-Acil-Tyt Ayt Geometrinin ilacı Soru Bankası | 216/225 | %96.0 |
| 2023-2024-ACİL-TYT-AYT-Geometrinin İlacı | 188/216 | %87.0 |
| CAP-2022-2023-TYT AYT-Geometri Soru Bankası | 133/213 | %62.4 |
| 345 Tyt Ayt Geometri Soru Bankası | 188/208 | %90.4 |
| Orijinal-Tyt Ayt Geometri Soru Bankası | 178/206 | %86.4 |
| Aktif Ogrenme 2025 Tyt Fizik Soru Bankası | 94/166 | %56.6 |
