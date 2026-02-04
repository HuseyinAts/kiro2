# 🚀 YKS Platform - Quick Reference Guide

## 📍 Hızlı Erişim Yolları

### Backend Servisleri
```bash
# Ana klasör
cd C:\Users\husey\kiro2\backend

# Servisler
cd backend/services

# Testler
cd backend/tests

# API endpoints
cd backend/api
```

### Frontend
```bash
cd C:\Users\husey\kiro2\frontend
```

## 🔥 En Sık Kullanılan Komutlar

### Backend
```bash
# Hızlı başlatma
python backend/fast_main.py

# Normal başlatma
cd backend && uvicorn main:app --reload

# Test çalıştırma
cd backend && pytest

# Coverage analizi
cd backend && python run_coverage_analysis.py
```

### Frontend
```bash
# Development
cd frontend && npm run dev

# Build
cd frontend && npm run build

# Test
cd frontend && npm run test
```

### Docker
```bash
# Tüm servisleri başlat
docker-compose up -d

# Production
docker-compose -f docker-compose.production.yml up -d

# Logları izle
docker-compose logs -f
```

## 🎯 Kritik API Endpoint'ler

### Öğrenme Stili
```http
GET /api/v1/learning-style/detect/{student_id}
GET /api/v1/learning-style/recommendations/{student_id}
POST /api/v1/learning-style/behavioral-data/{student_id}
```

### Sınav Sistemi
```http
POST /api/v1/sinav/olustur
POST /api/v1/sinav/{sinav_id}/baslat
GET /api/v1/sinav/{sinav_id}/sonuc
```

### RAG Sistemi
```http
POST /api/rag/query
POST /api/rag/add_educational
POST /api/rag/search_educational
```

## 🐛 Debug ve Troubleshooting

### Backend Debug
```python
# Debug mode
DEBUG=true python backend/main.py

# Verbose logging
LOG_LEVEL=DEBUG python backend/main.py

# Database debug
DATABASE_ECHO=true python backend/main.py
```

### Frontend Debug
```javascript
// Console'da
localStorage.setItem('debug', '*')

// Component debug
React.Profiler
React DevTools
```

## 📊 Test Coverage Hedefleri

| Modül | Mevcut | Hedef |
|-------|--------|-------|
| Services | %22 | %80 |
| API | %18 | %70 |
| Models | %35 | %90 |
| Utils | %45 | %85 |

## 🔑 Önemli Environment Variables

```bash
# Minimum gerekli
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=minimum-32-karakter
JWT_SECRET_KEY=minimum-32-karakter

# AI/ML
OPENAI_API_KEY=sk-...
HUGGINGFACE_API_KEY=hf_...

# Entegrasyonlar
YOUTUBE_API_KEY=AIza...
MEB_API_KEY=...
OSYM_API_KEY=...
```

## 🎨 Frontend Component Yapısı

```
frontend/src/
├── components/       # UI bileşenleri
├── pages/           # Sayfa component'leri  
├── services/        # API çağrıları
├── hooks/           # Custom React hooks
├── store/           # State management (Zustand)
├── utils/           # Helper fonksiyonlar
└── types/           # TypeScript type'ları
```

## 🏗️ Backend Servis Yapısı

```
backend/
├── api/             # FastAPI endpoints
├── services/        # İş mantığı
├── models/          # SQLAlchemy modeller
├── agents/          # AI agent'lar
├── integrations/    # Dış servisler
├── core/            # Core config
└── tests/           # Test dosyaları
```

## 💡 Özellik Bayrakları

```python
# .env dosyasında
ENABLE_BIONIC_READING=true
ENABLE_MULTI_AGENT_COORDINATION=true
ENABLE_CULTURAL_ADAPTATION=true
ENABLE_REVOLUTIONARY_FEATURES=true
ENABLE_PARENT_TRACKING=true
ENABLE_TEACHER_ANALYTICS=true
```

## 🔐 Güvenlik Kontrol Listesi

- [ ] JWT token validation
- [ ] Input sanitization
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CORS configuration
- [ ] Rate limiting
- [ ] API key rotation
- [ ] SSL/TLS encryption

## 📈 Performans Optimizasyonu

1. **Cache Strategy**
   - Redis: Session ve sık kullanılan data
   - Elasticsearch: Full-text search
   - Memory cache: Hot data

2. **Database Optimization**
   - Connection pooling
   - Query optimization
   - Index kullanımı
   - Async queries

3. **Frontend Optimization**
   - Code splitting
   - Lazy loading
   - Image optimization
   - PWA features

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] Test coverage > %70
- [ ] Security scan passed
- [ ] Performance test completed
- [ ] Documentation updated
- [ ] Environment variables set

### Post-deployment
- [ ] Health check passing
- [ ] Monitoring active
- [ ] Backup verified
- [ ] SSL certificate valid
- [ ] Error tracking enabled

## 📞 Acil Durumlar

### Servis Çökmesi
```bash
# Restart all services
docker-compose restart

# Check logs
docker-compose logs -f backend
```

### Database İssue
```bash
# Backup
pg_dump turkiye_sinav_db > backup.sql

# Restore
psql turkiye_sinav_db < backup.sql
```

### High Memory/CPU
```bash
# Check resource usage
docker stats

# Restart specific service
docker-compose restart backend
```

---

*Bu guide, development sırasında hızlı referans için hazırlanmıştır.*
*Detaylı bilgi için CLAUDE_AI_INSTRUCTIONS.md dosyasına bakın.*