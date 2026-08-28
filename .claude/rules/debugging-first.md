---
name: debugging-first
description: Bug fix oncesi ZORUNLU root cause gate
trigger: always
priority: critical
---

# Bug Fix Gate

Bug, hata, fix, 503, 500, error, bozuk, calismıyor gibi bir istek geldiginde:
Edit veya Write CAGIRMADAN ONCE asagidaki blogu kullaniciya GOSTER.

**Root Cause Analysis:**
| Soru | Cevap |
|------|-------|
| Hata ne? | [curl/pytest/log ciktisi — tahmin degil, gercek output] |
| Root cause? | [dosya:satir — neden bozuk] |
| Dogru tablo mu? | [question_bank=prod ~187K / questions=36.381 legacy, BOS DEGIL] |
| Altyapi OK mu? | [pg_isready -p 5434, redis-cli ping, curl /health] |
| Fix scope? | [dosya listesi, max 3 dosya] |

Kurallar:
- 503/500 → ONCE altyapi kontrol et (%75 infra sorunu)
- 200 + bos data → yanlis tablo veya is_active filtresi eksik
- Fix ONCESI fail eden test bul. Yoksa ONCE test yaz, SONRA fix.
- 3+ dosya → plan mode'a gec
