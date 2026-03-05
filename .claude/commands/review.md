---
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(ruff:*), Bash(pytest:*)
description: Son kod degisikliklerini incele
---

## Context
- Recent changes: !`git diff HEAD~3 --stat`

## Task
Kod degisikliklerini incele ve geri bildirim ver.

## KRITIK: Sonsuz Dongu Onleme

**ONCE lint ve test calistir.** Geciyorsa "kod calismiyor" deme.

```bash
cd backend && ruff check . --select=E,F,W --ignore=E501 2>&1 | head -20
cd backend && python -m pytest tests/unit/ -x --tb=short -q 2>&1 | tail -10
```

**SADECE kanitlanabilir sorunlari raporla:**
- CRITICAL = lint fail, test fail, kesin runtime crash (AttributeError/TypeError)
- WARNING = spesifik senaryo ile tetiklenen sorun
- ONERI = iyilestirme (opsiyonel)

**RAPORLAMA:**
- Teorik/varsayimsal sorunlari
- Onceki review'da duzeltilmis seyleri
- Degistirilmemis satirlardaki sorunlari
- Docstring/type hint eksikligi (degismeyen kodda)

## Inceleme Kriterleri

### 1. Guvenlik (kanit zorunlu)
- SQL injection: raw f-string query GOSTER
- Hardcoded credentials: satir numarasi GOSTER
- JWT bypass: exploit senaryosu GOSTER

### 2. Performans
- N+1 query (sorgu ornegi goster)
- Memory leak (nesne referansi goster)

### 3. Kod Kalitesi (sadece degisen satirlar)
- Type hints
- DRY ihlali

### 4. KIRO2 Ozel
- authStore.ts kullan (useAuth.ts DEGIL)
- UTF-8 + NFC Turkce normalization
- DB port: 5434

## Cikti Formati

```markdown
### Lint: PASS/FAIL
### Test: PASS/FAIL

### CRITICAL (merge engeli)
- [dosya:satir] Sorun + KANIT

### WARNING
- [dosya:satir] Sorun + senaryo

### ONERI
- [dosya:satir] Iyilestirme

### SONUC: Commit edilebilir mi? EVET/HAYIR
```

0 critical + 0 warning = "Kod temiz, commit edilebilir." Yapay bulgu URETME.
