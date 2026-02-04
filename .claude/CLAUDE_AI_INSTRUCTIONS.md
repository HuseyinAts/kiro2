# YKS Hazırlık Platformu - Teknofest 2025
## Claude AI Projects Instructions

## 🎯 Proje Özeti
Bu proje, Teknofest 2025 Eğitim Eylemci kategorisi için geliştirilmiş, YKS (TYT/AYT/YDT) sınavlarına hazırlanan öğrenciler için AI destekli kapsamlı bir eğitim platformudur.

## 📂 Proje Yapısı
- **Klasör Yolu**: C:\Users\husey\kiro2
- **Backend**: FastAPI + Python 3.11
- **Frontend**: React 18 + TypeScript + Vite
- **Veritabanı**: PostgreSQL + Redis + Elasticsearch
- **AI/ML**: LangChain + HuggingFace + BERTurk

## 🚀 Temel Özellikler

### 1. Hibrit Öğrenme Stili Sistemi (64 Profil)
- VARK + Felder-Silverman kombinasyonu
- V-ASVS, A-RIVG, R-ASBG, K-RIVS gibi hibrit kodlar
- Dinamik profil güncelleme
- Güven seviyesi analizi (HIGH/MEDIUM/LOW)

### 2. Sınav Motoru
- ÖSYM uyumlu TYT/AYT/YDT formatları
- IRT (Item Response Theory) kalibrasyonu
- Adaptif soru seçimi
- Detaylı performans analizi

### 3. AI Agent'lar
- RAG (Retrieval-Augmented Generation)
- Multi-agent koordinasyon
- Türkçe NLP desteği (BERTurk)
- Kişiselleştirilmiş öğrenme yolları

### 4. Entegrasyonlar
- YouTube Education API
- EBA TV entegrasyonu
- Khan Academy TR
- MEB müfredat uyumu

## 💻 Geliştirme Komutları

### Backend Başlatma
```bash
cd backend
python -m venv venv
activate_env.bat  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Başlatma
```bash
cd frontend
npm install
npm run dev
```

### Docker ile Çalıştırma
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.production.yml up -d
```

### Otomatik Kurulum (Önerilen)
```bash
# Tek komutla tam kurulum
python complete_setup_and_test.py
```

## 🔧 Önemli Servisler

### Öğrenme Stili API'leri
- `GET /api/v1/learning-style/detect/{student_id}`
- `GET /api/v1/learning-style/recommendations/{student_id}`
- `POST /api/v1/learning-style/behavioral-data/{student_id}`
- `POST /api/v1/learning-style/questionnaire/{student_id}`
- `GET /api/v1/learning-style/hybrid-codes`
- `GET /api/v1/learning-style/statistics`
- `GET /api/v1/learning-style/export/{student_id}`

### Sınav API'leri
- `POST /api/v1/sinav/olustur`
- `POST /api/v1/sinav/{sinav_id}/baslat`
- `POST /api/v1/sinav/{sinav_id}/cevap`
- `GET /api/v1/sinav/{sinav_id}/sonuc`

### RAG API'leri
- `POST /api/rag/add_educational`
- `POST /api/rag/search_educational`
- `POST /api/rag/query`

### Öğrenme Yolu API'leri
- `POST /api/learning-path/create-profile`
- `POST /api/learning-path/create-path`

## 🌍 Environment Variables

### Kritik Değişkenler
- `DATABASE_URL`: PostgreSQL bağlantısı
- `REDIS_URL`: Cache sistemi
- `ELASTICSEARCH_URL`: Arama motoru
- `OPENAI_API_KEY`: GPT-4 entegrasyonu
- `HUGGINGFACE_API_KEY`: BERTurk modeli
- `YOUTUBE_API_KEY`: Video önerileri
- `EBA_TV_API_KEY`: EBA TV entegrasyonu
- `MEB_API_KEY`: MEB servisleri
- `OSYM_API_KEY`: ÖSYM entegrasyonu

### Türkçe Karakter Desteği
- `PYTHONIOENCODING=utf-8`
- `LANG=tr_TR.UTF-8`
- `LC_ALL=tr_TR.UTF-8`

## 📊 Monitoring ve Metrikler
- **Coverage**: %22.11 (Hedef: %80)
- **Test Sayısı**: 102+ (Hedef: 1000+)
- **Güvenlik**: SonarCloud A seviye
- **Health Check**: GET /health
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## 🔒 Güvenlik Notları
- JWT authentication kullan
- API rate limiting aktif
- Input validation zorunlu
- SQL injection koruması
- XSS koruması
- CORS konfigürasyonu
- SSL/TLS desteği

## 🚨 Kritik Dosyalar ve Modüller

### Backend Core
- `backend/main.py` - Ana uygulama
- `backend/services/sinav_motoru_service.py` - Sınav engine
- `backend/services/learning_style/` - Öğrenme profilleri
- `backend/services/soru_bankasi_service.py` - Soru bankası
- `backend/services/zpd_maarif_service.py` - ZPD sistemi
- `backend/services/irt_morfoloji_service.py` - IRT analizi

### AI ve ML
- `backend/agents/` - AI agent'lar
- `backend/integrations/` - Dış servis entegrasyonları
- `backend/ai_ml/` - ML modelleri

### Frontend
- `frontend/src/` - React components
- `frontend/src/components/` - UI bileşenleri
- `frontend/src/services/` - API servisleri
- `frontend/src/hooks/` - Custom hooks

## 📝 TODO ve İyileştirmeler
1. Test coverage'ı %80'e çıkar
2. Memory leak sorunlarını düzelt (HttpClient)
3. Connection pooling implement et
4. Circuit breaker pattern ekle
5. Content versioning sistemi
6. Multi-tenant support ekle
7. Analytics dashboard geliştir
8. Plugin architecture oluştur

## 🎯 Performans Hedefleri
- Response time < 2 saniye
- Concurrent users > 500
- Cache hit rate > %45
- Error rate < %1
- Memory usage < 256MB
- CPU usage < 70%

## 🧪 Test Stratejisi
```bash
# Tüm testleri çalıştır
cd backend
pytest

# Coverage ile
pytest --cov=. --cov-report=html

# Spesifik testler
pytest tests/test_sinav_motoru_basic.py
pytest tests/test_learning_style_simple.py
pytest tests/test_rag.py

# Frontend testleri
cd frontend
npm run test
npm run test:coverage
```

## 📦 Deployment

### Staging
```bash
# Staging deployment
./deploy-production.sh staging
```

### Production
```bash
# Production deployment
./deploy-production.sh production
```

### Kubernetes
```bash
# K8s deployment
kubectl apply -f k8s/
```

## 🔄 CI/CD Pipeline
- GitHub Actions workflow
- Automated testing
- SonarCloud analysis
- Codecov integration
- Docker image build
- Kubernetes deployment

## 📈 Özellik Bayrakları (Feature Flags)
- `ENABLE_BIONIC_READING=true` - Bionik okuma
- `ENABLE_MULTI_AGENT_COORDINATION=true` - Multi-agent
- `ENABLE_CULTURAL_ADAPTATION=true` - Kültürel adaptasyon
- `ENABLE_REVOLUTIONARY_FEATURES=true` - Yenilikçi özellikler
- `ENABLE_PARENT_TRACKING=true` - Veli takibi
- `ENABLE_TEACHER_ANALYTICS=true` - Öğretmen analitiği

## 🤝 İletişim ve Destek
- Proje: Teknofest 2025 Eğitim Eylemci
- Kategori: Eğitim Teknolojileri
- Platform: YKS Hazırlık Sistemi
- Hedef Kitle: Lise öğrencileri (9-12. sınıf)

## 🆘 Troubleshooting

### Backend sorunları
- Log dosyası: `backend/app.log`
- Debug mode: `DEBUG=true`
- Verbose logging: `LOG_LEVEL=DEBUG`

### Frontend sorunları
- Console logs kontrol et
- Network tab incele
- React Developer Tools kullan

### Database sorunları
- Connection pool kontrol: `DATABASE_ECHO=true`
- Migration status: `alembic current`
- Database backup: `./scripts/backup_db.sh`

## 📚 Dokümantasyon
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Frontend Storybook: http://localhost:6006
- Project Wiki: ./docs/

---
*Bu dokümantasyon Claude AI tarafından projeyi daha iyi anlaması ve destek sağlaması için hazırlanmıştır.*