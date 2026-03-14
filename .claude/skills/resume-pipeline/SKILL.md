# Resume Pipeline

OCR/data pipeline durumunu kontrol et ve devam et.

## Adimlar

1. Pipeline log dosyalarini kontrol et:
   - `d-dataset/processed/` klasorundeki son dosyalari listele
   - Son islem tarihini ve sayisini belirle
2. Production JSONL durumunu kontrol et:
   ```bash
   python -c "
   import json
   count = sum(1 for _ in open('d-dataset/eslesmis_sorucevap.jsonl'))
   print(f'Production: {count} soru')
   "
   ```
3. Bekleyen islemleri tespit et:
   - Yeni kitaplar islenmis mi?
   - Crop solve bekleyen var mi?
   - Validation pass mi?
4. Sonuclari ozetle — codebase kesfetmeden sadece pipeline state'i raporla
5. Varsa sonraki pipeline adimini oner
