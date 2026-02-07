---
allowed-tools: Bash, Read
description: Check d-dataset processing status
---

## D-Dataset Status

Check answer extraction progress:

```bash
# Count OCR questions
find C:/Users/husey/d-dataset/outputs -name "*.json" -type f 2>/dev/null | wc -l

# Count extracted answers  
sqlite3 C:/Users/husey/d-dataset/answers_v9.db "SELECT COUNT(*) FROM answers;" 2>/dev/null || echo "Database not found"

# Recent processing
ls -lt C:/Users/husey/d-dataset/outputs | head -10
```

## Match Rate
Current: **0.11%** (2,436/75,745)  
Target: **66%+**

## Priority Books
- ACİL, CAP, Bilgi Sarmalı (highest quality)
- 725 YOLO answer key crops unprocessed
- 251 books with 0 answers

Show current progress.
