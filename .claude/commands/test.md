---
allowed-tools: Bash, Read, Edit
argument-hint: [test-pattern]
description: KIRO2 testlerini çalıştır
---

## Context
- Proje: KIRO2 YKS Hazırlık Platformu
- Backend: pytest (700+ test)
- Frontend: Jest + Playwright

## Task
Run tests for: $ARGUMENTS

## Test Stratejisi

### Argüman yoksa
```bash
cd backend && pytest tests/unit -v --tb=short
```

### Pattern belirtilmişse
```bash
cd backend && pytest -k "$ARGUMENTS" -v --tb=short
```

### Özel komutlar
- `unit` → Unit testler
- `integration` → Integration testler
- `coverage` → Coverage raporu
- `fast` → Son başarısız testler (`--lf`)
- `frontend` → Jest testleri

## Gereksinimler

1. Verbose output (`-v`)
2. Kısa traceback (`--tb=short`)
3. İlk hatada dur (debug için `-x`)
4. Coverage raporu göster
5. Başarısız testleri listele
