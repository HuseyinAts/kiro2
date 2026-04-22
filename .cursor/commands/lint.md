# Lint — Kod Kalitesi Kontrolü

KIRO2 için Python ve TypeScript kod kalitesi kontrolleri.

## Python (Backend)

Modern toolchain — `ruff` hem `black` hem `flake8`'i ikame eder:

```bash
cd backend

# 1. Ruff check (eski flake8 yerine)
ruff check . --select=E,F,W,I --ignore=E501

# 2. Ruff format (eski black yerine)
ruff format --check .

# 3. Type checking
mypy backend/ --no-error-summary
```

Not: KIRO2 hook'u (`.cursor/hooks/post-edit-ruff.py`) düzenleme sonrası
otomatik ruff çalıştırıyor. Lint komut çoğu zaman zaten-temiz gösterir.

## TypeScript (Frontend)

```bash
cd frontend

# ESLint
npm run lint

# Type check
npx tsc --noEmit

# Prettier (eğer setup varsa)
npx prettier --check "src/**/*.{ts,tsx,json,css}"
```

## Auto-fix Modu

Kullanıcı `/lint fix` diye çağırırsa düzelt:

```bash
# Python
cd backend && ruff check --fix . && ruff format .

# TypeScript
cd frontend && npm run lint -- --fix
```

## Rapor Formatı

```markdown
## Lint Raporu — [TARIH]

### Python (backend/)
- ruff check: ✅ PASS / ❌ N hata
- ruff format: ✅ PASS / ❌ N dosya format dışı
- mypy: ✅ PASS / ❌ N hata (baseline: X)

### TypeScript (frontend/)
- eslint: ✅ PASS / ❌ N hata
- tsc: ✅ PASS / ❌ N hata

### Aksiyon Gerekli
- [varsa: "/lint fix ile otomatik düzelt"]
- [manuel fix gerekiyorsa liste]
```

## Mypy Baseline

KIRO2'de mypy strict değil. "Yeni hata baseline üstüne çıkmamalı" kuralı.
Mevcut baseline:
```bash
mypy backend/ 2>&1 | grep "Found.*errors" | awk '{print $2}'
```

Son ölçümü `progress.md`'de tutulur.
