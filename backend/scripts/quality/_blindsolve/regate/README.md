# blind_solve Bulk RE-GATE — sonraki seans driver'ı

Amaç: gevşek v1 pipeline'ının promote ettiği 16.344 bulk'u **v2 mantığıyla yeniden
süz** (coherence-clean AND gemma3==qwen3==stored), failleri v_safe'ten geri çek.
Beklenen: ~%40-50 düşer, v_safe ~25.855 → ~17-19K *temiz*. Reversible. Bkz:
`docs/audits/2026-06-23_blindsolve_rootcause.md`.

## Ön koşullar
- DB ayakta: `postgresql-x64-18` (port 5434). Durmuşsa RunAs ile başlat.
- `kiro2-ollama` container ayakta; modeller: `gemma3:12b-it-qat`, `qwen3:14b`
  (yoksa: `docker exec kiro2-ollama ollama pull <tag>`). Solver container'a bağlanır (localhost:11434).
- `correct_answer` / `is_active` ASLA değişmez. Tüm DB yazımı reversible (exclusion + backup).

## Adımlar

### 1) Export + split  (CPU, ~1 dk)
```powershell
cd C:\Users\husey\kiro2
& "C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2 -f "C:\Users\husey\kiro2\backend\scripts\quality\_blindsolve\regate\export.sql"
python backend\scripts\quality\_blindsolve\regate\split.py
```
Beklenen: `total_rows≈16344 batches≈818`.

### 2) İki modelle kör-çöz  (GPU-yoğun, ~7-8 saat/MODEL — chunk'lı)
> Resume-safe: Ctrl+C → aynı komut kaldığından devam. Isınırsa `--cooldown 8 --max-new N` ile parçala.
```powershell
cd C:\Users\husey\kiro2\backend\scripts\quality
# gemma3
python ollama_blind_solve.py --batch-dir _blindsolve\regate\batches --model gemma3:12b-it-qat --cooldown 8
New-Item -ItemType Directory -Force "_blindsolve/regate/preds_gemma" | Out-Null
Move-Item "_blindsolve/regate/batches/preds_*.json" "_blindsolve/regate/preds_gemma/" -Force
# qwen3
python ollama_blind_solve.py --batch-dir _blindsolve\regate\batches --model qwen3:14b --cooldown 8
New-Item -ItemType Directory -Force "_blindsolve/regate/preds_qwen" | Out-Null
Move-Item "_blindsolve/regate/batches/preds_*.json" "_blindsolve/regate/preds_qwen/" -Force
```
Doğrula: `preds_gemma` ve `preds_qwen` her biri ~818 dosya.

### 3) Re-gate aggregate  (CPU)
```powershell
cd C:\Users\husey\kiro2
python backend\scripts\quality\_blindsolve\regate\regate.py
```
Üretir: `keep_ids.json`, `demote_ids.json`, `opus_keep.txt`(25), `opus_demote.txt`(25),
`D_regate_demote.sql`. Eksik pred varsa DURUR (modeli bitir).

### 4) Opus doğrulama (KAPI)  — bu seansta/Cowork'te Opus çözer
- `opus_keep.txt` → KEEP set'i gerçekten temiz mi? (precision ≥%95 hedef)
- `opus_demote.txt` → over-demote mu? (demote edilenlerin çoğu gerçekten bozuk/yanlış olmalı)
- İkisi de geçerse Adım 5. Geçmezse eşiği/coherence kuralını ayarla.

### 5) Demote uygula  (reversible, DB yazımı)
```powershell
& "C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2 -v ON_ERROR_STOP=1 -f "C:\Users\husey\kiro2\backend\scripts\quality\_blindsolve\regate\D_regate_demote.sql"
```
Sonra **v_safe view'a exclusion ekle** (gate2c/D6 deseni):
- Canlı tanımı al: `pg_get_viewdef('v_safe_for_beta', true)` (EZBERDEN YAZMA).
- `AND id NOT IN (SELECT id FROM blindsolve_regate_demoted)`'i **bayrak-grubu parantezinin DIŞINA** ekle (gate2c_demoted satırının yanına, ayrı AND).
- Rollback dosyası yaz (eski viewdef).
- Apply sonrası: `SELECT count(*) FROM v_safe_for_beta` (≈ 25.855 − demote) ve
  `SELECT count(*) FROM v_safe_for_beta WHERE id IN (SELECT id FROM blindsolve_regate_demoted)` = **0** (leak yok).

## Disposition
- Demote edilenler **silinmez** → v_safe dışı, "review" havuzunda kalır (zor≠yanlış).
- KEEP = coherence-clean + 3-yönlü mutabakat → güvenilir beta alt-kümesi.
- Gelecek dalgalar `aggregate_wave_v2.py` (v1 DEĞİL) kullanmalı.

## Notlar
- bash VM güvenilmez → host PowerShell, human-in-loop.
- ~818 batch × 20 = 16.344. İki model ≈ 2× tek-model süresi; gece/parça parça çalıştır.
- Tüm artefaktlar (`batches/`, `preds_*`, `master.csv`) transient — commit etme; sadece
  `export.sql/split.py/regate.py/README.md` + (sonradan) `D_regate_demote.sql` + rollback commit edilir.
