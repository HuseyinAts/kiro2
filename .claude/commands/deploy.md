---
allowed-tools: Bash, Read
argument-hint: [staging|production]
description: Deployment işlemlerini yönet
---

## Task
KIRO2'yu belirtilen ortama deploy et: $ARGUMENTS

## Pre-deploy Checklist

### 1. Testleri Çalıştır
```bash
cd backend && pytest -x --tb=short
cd ../frontend && npm test -- --passWithNoTests
```

### 2. Lint Kontrol
```bash
cd backend && black --check . && flake8 . && mypy src/
cd ../frontend && npm run lint
```

### 3. Build Kontrol
```bash
cd frontend && npm run build
```

### 4. Migration Kontrol
```bash
cd backend && alembic history --verbose | head -10
```

## Deploy Adımları

### Staging
```bash
# 1. Git tag oluştur
git tag -a v$(date +%Y%m%d)-staging -m "Staging release"

# 2. Push
git push origin staging --tags

# 3. GitHub Actions tetiklenir
echo "GitHub Actions workflow başlatıldı..."
```

### Production
```bash
# ⚠️ UYARI: Production deploy!

# 1. Main branch'e merge
git checkout main
git merge --no-ff staging

# 2. Version tag
git tag -a v$(cat VERSION) -m "Production release"

# 3. Push
git push origin main --tags
```

## Post-deploy Kontrol

1. Health endpoint kontrol
2. Smoke testleri
3. Log monitoring
4. Sentry error check
