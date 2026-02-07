# Developer Setup Guide - Video Recommendation API

## Genel Bakış

Bu doküman, Video Recommendation API'yi local development ortamında kurulum ve çalıştırma adımlarını içerir.

## Sistem Gereksinimleri

### Minimum Gereksinimler

- **Python:** 3.9 veya üzeri
- **Node.js:** 16.x veya üzeri (Frontend için)
- **Redis:** 6.x veya üzeri
- **SQLite:** 3.x (development için)
- **RAM:** 4GB
- **Disk:** 2GB boş alan

### Önerilen Gereksinimler

- **Python:** 3.11
- **Node.js:** 18.x LTS
- **Redis:** 7.x
- **PostgreSQL:** 14.x (production-like setup için)
- **RAM:** 8GB
- **Disk:** 5GB boş alan

## Kurulum Adımları

### 1. Repository Clone

```bash
# Repository'yi clone et
git clone https://github.com/teknofest-2025-egitim-eylemci.git
cd teknofest-2025-egitim-eylemci
```

### 2. Backend Kurulumu

#### 2.1 Python Virtual Environment

```bash
# Backend dizinine git
cd backend

# Virtual environment oluştur
python -m venv venv

# Virtual environment'ı aktif et
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 2.2 Dependencies Kurulumu

```bash
# Requirements'ları yükle
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-test.txt

# Verify installation
pip list
```

**requirements.txt içeriği:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0
redis==5.0.1
aioredis==2.0.1
sqlalchemy==2.0.23
alembic==1.12.1
google-api-python-client==2.108.0
langdetect==1.0.9
structlog==23.2.0
prometheus-client==0.19.0
slowapi==0.1.9
httpx==0.25.2
```

#### 2.3 Environment Variables

```bash
# .env dosyası oluştur
cp .env.example .env

# .env dosyasını düzenle
nano .env
```

**.env içeriği:**
```bash
# API Keys
YOUTUBE_API_KEY=your_youtube_api_key_here

# Database
DATABASE_URL=sqlite:///./turkiye_sinav.db

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
FRONTEND_URL=http://localhost:3001

# Performance
CACHE_TTL_SECONDS=3600
MAX_PARALLEL_SEARCHES=3
REQUEST_TIMEOUT_SECONDS=20

# Quality Thresholds
MIN_RELEVANCE_SCORE=0.7
MIN_LANGUAGE_SCORE=0.8
MIN_QUALITY_SCORE=7.0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_AUTHENTICATED=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

#### 2.4 YouTube API Key Alma

1. [Google Cloud Console](https://console.cloud.google.com/) giriş yap
2. Yeni proje oluştur veya mevcut projeyi seç
3. "APIs & Services" > "Library" git
4. "YouTube Data API v3" ara ve enable et
5. "APIs & Services" > "Credentials" git
6. "Create Credentials" > "API Key" seç
7. API key'i kopyala ve `.env` dosyasına ekle

**API Key Restrictions (Önerilen):**
- Application restrictions: HTTP referrers
- API restrictions: YouTube Data API v3

#### 2.5 Database Kurulumu

```bash
# Database'i oluştur ve migrate et
python init_db.py

# Verify database
sqlite3 turkiye_sinav.db
> .tables
> .schema video_cache
> .quit
```

**Database Schema:**
```sql
CREATE TABLE video_cache (
    id INTEGER PRIMARY KEY,
    video_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    exam_type TEXT NOT NULL,
    language TEXT NOT NULL,
    quality_score REAL NOT NULL,
    relevance_score REAL NOT NULL,
    language_score REAL NOT NULL,
    difficulty_match REAL NOT NULL,
    overall_score REAL NOT NULL,
    metadata TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_video_subject ON video_cache(subject, difficulty, exam_type);
CREATE INDEX idx_video_quality ON video_cache(quality_score DESC);
CREATE INDEX idx_video_language ON video_cache(language);
CREATE INDEX idx_video_updated ON video_cache(last_updated DESC);
CREATE INDEX idx_video_search ON video_cache(
    subject, difficulty, exam_type, language, quality_score DESC
);
```

#### 2.6 Redis Kurulumu

**Option 1: Local Redis**
```bash
# Windows (Chocolatey)
choco install redis-64

# Mac (Homebrew)
brew install redis

# Linux (Ubuntu)
sudo apt-get install redis-server

# Start Redis
redis-server

# Verify
redis-cli ping
# Expected: PONG
```

**Option 2: Docker Redis**
```bash
# Run Redis container
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Verify
docker exec -it redis redis-cli ping
# Expected: PONG
```

**Option 3: Redis Cloud (Free Tier)**
1. [Redis Cloud](https://redis.com/try-free/) hesap oluştur
2. Free database oluştur
3. Connection string'i kopyala
4. `.env` dosyasına ekle:
```bash
REDIS_URL=redis://default:password@redis-12345.c1.us-east-1-1.ec2.cloud.redislabs.com:12345
```

### 3. Frontend Kurulumu

```bash
# Frontend dizinine git
cd ../frontend

# Dependencies yükle
npm install

# .env dosyası oluştur
cp .env.example .env

# .env dosyasını düzenle
nano .env
```

**.env içeriği:**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_ANALYTICS=false
VITE_SENTRY_DSN=
```

### 4. Backend'i Başlatma

```bash
# Backend dizinine git
cd backend

# Virtual environment aktif
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# Development mode ile başlat
uvicorn main:app --reload --port 8000

# Alternatif: Multiple workers ile
uvicorn main:app --workers 4 --port 8000

# Alternatif: Debug mode ile
uvicorn main:app --reload --log-level debug --port 8000
```

**Not (Entrypoint):**
- Aktif çalışma yolu `backend/main.py` -> `backend/core/application.py` -> `backend/routers/loader.py`.
- `backend/main_old.py` legacy yol olarak durur; default çalışma hattında kullanılmaz.

**Beklenen Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Health Check:**
```bash
# API test
curl http://localhost:8000/api/youtube/test

# Health check
curl http://localhost:8000/api/youtube/health

# OpenAPI docs
open http://localhost:8000/docs
```

### 4.1 Veri Seed (Opsiyonel ama Önerilir)

Repo içindeki SQLite snapshot’ları demo amaçlıdır. Gerçekçi veri için seed çalıştırın:

```bash
python backend/scripts/manage_db.py seed dev
# veya
python backend/scripts/manage_db.py seed prod
```

### 5. Frontend'i Başlatma

```bash
# Frontend dizinine git
cd frontend

# Development server başlat
npm run dev

# Alternatif: Specific port ile
npm run dev -- --port 3001
```

**Beklenen Output:**
```
  VITE v4.5.0  ready in 1234 ms

  ➜  Local:   http://localhost:3001/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

**Browser'da Aç:**
```
http://localhost:3001
```

## Development Workflow

### 1. Code Changes

**Backend:**
```bash
# Hot reload aktif, değişiklikler otomatik yüklenir
# backend/services/video_recommendation_service.py dosyasını düzenle
# Uvicorn otomatik restart eder
```

**Frontend:**
```bash
# Hot reload aktif, değişiklikler otomatik yüklenir
# frontend/src/main.tsx dosyasını düzenle
# Vite otomatik refresh eder
```

### 2. Testing

**Backend Unit Tests:**
```bash
cd backend

# Tüm testleri çalıştır
pytest

# Specific test file
pytest tests/test_video_recommendation_service.py

# Coverage ile
pytest --cov=services --cov-report=html

# Verbose mode
pytest -v

# Stop on first failure
pytest -x
```

**Backend Integration Tests:**
```bash
# Integration tests
pytest tests/integration/

# Specific integration test
pytest tests/integration/test_video_api_integration.py
```

**Frontend Tests:**
```bash
cd frontend

# Unit tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

**E2E Tests:**
```bash
cd frontend

# Playwright tests
npm run test:e2e

# Specific test
npm run test:e2e -- video-loading.spec.ts

# Debug mode
npm run test:e2e -- --debug
```

### 3. Linting & Formatting

**Backend:**
```bash
cd backend

# Black formatter
black .

# Flake8 linter
flake8 .

# MyPy type checker
mypy .

# isort import sorter
isort .

# All in one
black . && isort . && flake8 . && mypy .
```

**Frontend:**
```bash
cd frontend

# ESLint
npm run lint

# Prettier
npm run format

# Type check
npm run type-check

# All in one
npm run lint && npm run format && npm run type-check
```

### 4. Database Migrations

**Create Migration:**
```bash
cd backend

# Auto-generate migration
alembic revision --autogenerate -m "Add new column to video_cache"

# Manual migration
alembic revision -m "Custom migration"
```

**Apply Migration:**
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade abc123

# Downgrade
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### 5. Debugging

**Backend Debugging (VS Code):**

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

**Frontend Debugging (VS Code):**

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Chrome: Frontend",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3001",
      "webRoot": "${workspaceFolder}/frontend/src"
    }
  ]
}
```

**Python Debugger (pdb):**
```python
# Breakpoint ekle
import pdb; pdb.set_trace()

# Veya Python 3.7+
breakpoint()
```

**Browser DevTools:**
```javascript
// Console'da debug
console.log('Debug:', data);

// Breakpoint
debugger;

// Network tab'da request/response kontrol et
```

## Common Development Tasks

### Task 1: Yeni Endpoint Ekleme

```python
# backend/api/youtube_routes.py

@router.post("/new-endpoint")
async def new_endpoint(
    request: NewRequest,
    service: VideoRecommendationService = Depends(get_service)
):
    """
    Yeni endpoint açıklaması
    """
    result = await service.new_method(request)
    return result
```

**Test Ekle:**
```python
# backend/tests/test_youtube_routes.py

@pytest.mark.asyncio
async def test_new_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/youtube/new-endpoint",
            json={"key": "value"}
        )
        assert response.status_code == 200
```

### Task 2: Yeni Service Method Ekleme

```python
# backend/services/video_recommendation_service.py

async def new_method(self, request: NewRequest) -> Result:
    """
    Yeni method açıklaması
    """
    # Implementation
    pass
```

**Test Ekle:**
```python
# backend/tests/test_video_recommendation_service.py

@pytest.mark.asyncio
async def test_new_method():
    service = VideoRecommendationService(...)
    result = await service.new_method(request)
    assert result is not None
```

### Task 3: Cache Strategy Değiştirme

```python
# backend/services/video_recommendation_service.py

# TTL değiştir
await self.cache.set(
    cache_key,
    recommendations,
    ttl=7200  # 2 saat
)

# Cache key generation değiştir
def _generate_cache_key(self, profile: StudentProfile) -> str:
    # Yeni key generation logic
    pass
```

### Task 4: Filtering Logic Güncelleme

```python
# backend/services/turkish_content_filter.py

# Threshold değiştir
MIN_LANGUAGE_SCORE = 0.9  # 0.8 → 0.9

# Yeni filter ekle
def _new_filter(self, video: Video) -> bool:
    # New filter logic
    pass
```

### Task 5: Frontend Component Ekleme

```typescript
// frontend/src/components/NewComponent.tsx

import React from 'react';

interface NewComponentProps {
  data: any;
}

export const NewComponent: React.FC<NewComponentProps> = ({ data }) => {
  return (
    <div>
      {/* Component content */}
    </div>
  );
};
```

## Troubleshooting

### Backend Başlamıyor

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Çözüm:**
```bash
# Virtual environment aktif mi kontrol et
which python  # Linux/Mac
where python  # Windows

# Requirements tekrar yükle
pip install -r requirements.txt
```

**Problem:** `redis.exceptions.ConnectionError`

**Çözüm:**
```bash
# Redis çalışıyor mu?
redis-cli ping

# Redis başlat
redis-server

# Docker ile
docker start redis
```

### Frontend Başlamıyor

**Problem:** `Error: Cannot find module 'vite'`

**Çözüm:**
```bash
# node_modules temizle ve tekrar yükle
rm -rf node_modules package-lock.json
npm install
```

**Problem:** `CORS error in browser console`

**Çözüm:**
```python
# backend/main.py
# Frontend URL'ini CORS'a ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    ...
)
```

### Tests Başarısız

**Problem:** `AssertionError in tests`

**Çözüm:**
```bash
# Test database kullan
export DATABASE_URL=sqlite:///./test.db

# Cache temizle
redis-cli FLUSHDB

# Verbose mode ile çalıştır
pytest -v -s
```

## Best Practices

### Code Style

**Python:**
- PEP 8 style guide
- Type hints kullan
- Docstrings yaz (Google style)
- Max line length: 88 (Black default)

**TypeScript:**
- ESLint rules
- Prettier formatting
- Strict mode
- Interface > Type

### Git Workflow

```bash
# Feature branch oluştur
git checkout -b feature/new-feature

# Changes commit et
git add .
git commit -m "feat: Add new feature"

# Push et
git push origin feature/new-feature

# Pull request oluştur
# GitHub'da PR aç
```

**Commit Message Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: Yeni özellik
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

### Code Review Checklist

- [ ] Code style guide'a uygun
- [ ] Tests yazıldı ve geçiyor
- [ ] Documentation güncellendi
- [ ] Breaking changes yok
- [ ] Performance impact değerlendirildi
- [ ] Security considerations yapıldı
- [ ] Error handling eklendi
- [ ] Logging eklendi

## Additional Resources

### Documentation

- [API Documentation](./VIDEO_API.md)
- [Architecture](./ARCHITECTURE.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
- [Performance Tuning](./PERFORMANCE_TUNING.md)

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [YouTube Data API](https://developers.google.com/youtube/v3)

### Tools

- **API Testing:** Postman, Insomnia, HTTPie
- **Database:** DBeaver, SQLite Browser
- **Redis:** RedisInsight, redis-cli
- **Monitoring:** Grafana, Prometheus
- **Logging:** Kibana, Elasticsearch

## Support

**Questions?**
- Slack: #video-api-dev
- Email: dev@teknofest-egitim.com
- GitHub Discussions: [Link]

**Found a bug?**
- GitHub Issues: [Link]
- Include: Steps to reproduce, expected vs actual behavior, logs

**Want to contribute?**
- Read CONTRIBUTING.md
- Fork repository
- Create feature branch
- Submit pull request
