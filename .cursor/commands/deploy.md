# Deploy

KIRO2'yu belirtilen ortama deploy et. Kullanıcı `staging` veya `production`
belirtecek.

## Pre-Deploy Checklist (Zorunlu)

Sırayla çalıştır, birinde fail olursa dur:

### 1. Testler
```bash
cd backend && pytest -x --tb=short
cd ../frontend && npm test -- --run
```

### 2. Lint
```bash
cd backend && ruff check . && ruff format --check .
cd backend && mypy backend/ --no-error-summary
cd ../frontend && npm run lint
```

### 3. Build
```bash
cd frontend && npm run build
```

### 4. Migration Durumu
```bash
cd backend && alembic current
cd backend && alembic heads  # tek head göstermeli
cd backend && alembic history --verbose | head -10
```

Eğer migration pending ise: "Deploy öncesi migration uygulanacak" uyarısı ver.

## Staging Deploy

```bash
# Tag
git tag -a "v$(date +%Y%m%d%H%M)-staging" -m "Staging: <kısa açıklama>"

# Push (CI tetiklenir)
git push origin staging
git push origin --tags

# GitHub Actions workflow izle
gh run watch
```

## Production Deploy (DIKKAT)

⚠️ `.claude/rules/security.md` ve `AGENTS.md`'deki production kuralları:
- Main branch'e doğrudan push YASAK
- Force push YASAK
- Staging'de minimum 24 saat test yapılmış olmalı

```bash
# 1. Main'e merge (no-ff zorunlu, history korunur)
git checkout main
git pull --ff-only origin main
git merge --no-ff staging -m "release: $(cat VERSION)"

# 2. Version tag
git tag -a "v$(cat VERSION)" -m "Production release v$(cat VERSION)"

# 3. Push
git push origin main
git push origin --tags
```

## Post-Deploy Kontrol

```bash
# Health check
curl -s https://<env>.kiro2.com/health | jq

# Smoke test (smoke-test.sh varsa)
bash scripts/smoke-test.sh <env>

# Sentry son 15 dk hatalar
# (dashboard'dan manuel kontrol)
```

## Rollback Planı

Hata durumunda:

```bash
# Son tag'e geri dön
git revert HEAD
git push origin main

# Veya tag ile
git checkout <önceki_tag>
git push --force-with-lease origin main  # sadece olağanüstü durumda
```

Migration rollback için:
```bash
cd backend && alembic downgrade -1
```

## PowerShell Not

KIRO2'de `deploy_all.ps1` scripti var, yerel deployment için kullanılabilir.
Komut sonrası kullanıcı `deploy_all.ps1` talep ederse o script'i çağır,
yukarıdaki manuel adımları atlayabilirsin.
