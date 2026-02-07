---
name: deploy-production
description: Uygulamayı production ortamına deploy eder. CI/CD pipeline'ı tetikler, sağlık kontrolleri yapar. SADECE kullanıcı tarafından tetiklenebilir.
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Production Deployment: $ARGUMENTS

⚠️ **DİKKAT**: Bu işlem production ortamını etkiler!

Bu skill SADECE kullanıcı tarafından `/deploy-production` komutuyla tetiklenebilir.
Claude otomatik olarak bu skill'i çağıramaz.

## Pre-Deployment Checklist

### 1. Kod Kalitesi ✅
```bash
# Backend
cd backend && ruff check . --select=E,F,W
cd backend && mypy --ignore-missing-imports main.py
cd backend && pytest -x --tb=short -q

# Frontend
cd frontend && npm run lint
cd frontend && npm run type-check
cd frontend && npm test
```

### 2. Güvenlik Kontrolü ✅
```bash
# Secrets kontrolü
git diff --cached --name-only | xargs -I {} sh -c 'grep -l "API_KEY\|PASSWORD\|SECRET" {} && exit 1 || true'

# Dependency vulnerability scan
pip-audit
npm audit
```

### 3. Test Coverage ✅
```bash
# Minimum coverage: %60
pytest --cov=backend --cov-fail-under=60
```

### 4. Build Kontrolü ✅
```bash
# Docker build
docker build -t kiro2-backend:latest -f Dockerfile.production .
docker build -t kiro2-frontend:latest -f frontend/Dockerfile .
```

## Deployment Adımları

### Environment: $ARGUMENTS

```bash
# 1. Tag oluştur
git tag -a v$(date +%Y%m%d-%H%M%S) -m "Production release"

# 2. Docker images push
docker push kiro2-backend:latest
docker push kiro2-frontend:latest

# 3. Kubernetes deploy (veya docker-compose)
kubectl apply -f k8s/production/
# veya
docker-compose -f docker-compose.production.yml up -d

# 4. Health check
curl -f https://api.kiro2.com/health || exit 1
curl -f https://kiro2.com/ || exit 1

# 5. Smoke tests
pytest tests/smoke/ --env=production
```

## Rollback Planı

Deployment başarısız olursa:

```bash
# 1. Önceki tag'e dön
git checkout v<previous-version>

# 2. Önceki images'ları deploy et
kubectl rollout undo deployment/kiro2-backend
kubectl rollout undo deployment/kiro2-frontend

# 3. Veritabanı rollback (gerekirse)
alembic downgrade -1
```

## Notification

Deployment sonrası bildirim:

```bash
# Slack notification
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"🚀 KIRO2 deployed to production!"}' \
  $SLACK_WEBHOOK_URL

# Email notification
echo "KIRO2 deployment complete" | mail -s "Deployment" team@kiro2.com
```

## Monitoring

Deploy sonrası izlenecekler:

- [ ] Error rate < 1%
- [ ] Response time < 500ms
- [ ] Memory usage stable
- [ ] Database connections normal
- [ ] Redis cache hit rate > 80%

## Komut Kullanımı

```bash
# Staging deploy
/deploy-production staging

# Production deploy
/deploy-production production

# Sadece health check
/deploy-production health-check

# Rollback
/deploy-production rollback v20260125-120000
```

## KIRO2 Spesifik Kontroller

### Database Migration
```bash
# Migration durumunu kontrol et
alembic current
alembic history

# Bekleyen migration varsa
alembic upgrade head
```

### Redis Cache
```bash
# Cache'i temizle (dikkatli!)
redis-cli -p 6379 FLUSHDB
```

### Elasticsearch Index
```bash
# Index durumunu kontrol et
curl localhost:9200/_cat/indices
```

## Güvenlik Notları

- Production secrets ASLA commit edilmez
- `.env.production` dosyası gitignore'da
- API keys environment variable olarak inject edilir
- Database credentials Kubernetes secrets'da

## Exit Codes

| Code | Anlam |
|------|-------|
| 0 | Deployment başarılı |
| 1 | Build hatası |
| 2 | Test hatası (BLOCKING) |
| 3 | Health check başarısız |
| 4 | Rollback gerekli |

---

**Son Kontrol**: Bu işlemi gerçekleştirmek istediğinize emin misiniz?

```
/deploy-production $ARGUMENTS --confirm
```
