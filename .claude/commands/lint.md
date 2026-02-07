---
allowed-tools: Bash(black:*), Bash(isort:*), Bash(flake8:*), Bash(mypy:*), Bash(eslint:*), Bash(prettier:*)
description: KIRO2 kod kalitesi kontrolleri
---

## Context
- Python: black, isort, flake8, mypy
- TypeScript: eslint, prettier

## Task
Kod kalitesi kontrolleri çalıştır.

## Python Kontrolleri

```bash
cd backend

# 1. Black format kontrolü
black . --check --diff

# 2. Import sıralaması
isort . --check --diff

# 3. Flake8 lint
flake8 . --max-line-length=88 --extend-ignore=E203

# 4. Type checking
mypy . --ignore-missing-imports
```

## TypeScript Kontrolleri

```bash
cd frontend

# ESLint
npm run lint

# Type check
npm run type-check
```

## Auto-fix Modu

Sorunları otomatik düzeltmek için:

```bash
# Python
cd backend && black . && isort .

# TypeScript
cd frontend && npm run lint -- --fix
```

## Çıktı Formatı

Her araç için:
- ✅ Başarılı → "X kontrol geçti"
- ❌ Hata → Hata listesi ve fix önerisi
