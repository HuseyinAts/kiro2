# Video Recommendation API - Documentation Index

## Genel Bakış

Bu dizin, Video Recommendation API için kapsamlı dokümantasyon içerir. Aşağıdaki dokümanlar, API'yi kullanmak, geliştirmek ve optimize etmek için gerekli tüm bilgileri sağlar.

## 📚 Dokümantasyon Listesi

### 🚀 Başlangıç Dokümanları

#### [Developer Setup Guide](./DEVELOPER_SETUP.md)
**Hedef Kitle:** Yeni geliştiriciler, onboarding

**İçerik:**
- Sistem gereksinimleri
- Kurulum adımları (Backend, Frontend, Database, Redis)
- YouTube API key alma
- Development workflow
- Testing ve debugging
- Common development tasks

**Ne Zaman Kullanılır:** İlk kez projeye başlarken veya local development environment kurarken.

---

#### [API Documentation](./VIDEO_API.md)
**Hedef Kitle:** Frontend geliştiriciler, API kullanıcıları

**İçerik:**
- API endpoints (POST /recommendations, GET /health, GET /test)
- Request/response formatları
- Error codes ve handling
- Rate limiting
- Caching strategy
- Code examples (JavaScript, Python, cURL)
- Authentication (gelecek)

**Ne Zaman Kullanılır:** API'yi entegre ederken veya endpoint'leri kullanırken.

---

### 🏗️ Mimari Dokümanları

#### [Architecture Document](./ARCHITECTURE.md)
**Hedef Kitle:** Sistem mimarları, senior geliştiriciler

**İçerik:**
- High-level architecture
- Component architecture (Frontend, Backend, Services, Data Layer)
- Request flow
- Startup sequence
- Reliability patterns (Circuit Breaker, Retry Logic, Graceful Degradation)
- Performance optimization
- Security considerations
- Design decisions ve rationale

**Ne Zaman Kullanılır:** Sistem tasarımını anlamak veya architectural decisions yaparken.

---

#### [Architecture Diagrams](./ARCHITECTURE_DIAGRAM.md)
**Hedef Kitle:** Tüm geliştiriciler, stakeholders

**İçerik:**
- System architecture diagram
- Request flow diagram
- Cache architecture diagram
- Turkish content filtering flow
- Circuit breaker state machine
- Deployment architecture
- Error handling flow
- Monitoring architecture
- Data model diagram
- Security architecture
- Startup sequence diagram

**Ne Zaman Kullanılır:** Görsel olarak sistemi anlamak veya sunumlar için.

---

### 🔧 Operasyonel Dokümanlar

#### [Troubleshooting Guide](./TROUBLESHOOTING.md)
**Hedef Kitle:** DevOps, support engineers, geliştiriciler

**İçerik:**
- Hızlı tanı (Health check, API test, Log kontrolü)
- Yaygın sorunlar ve çözümleri
  - "Videoları 10 saniye içinde yükleyemedik"
  - Yavaş yanıt süresi
  - Rate limit hatası
  - Türkçe olmayan videolar
  - Circuit breaker açık
- Performans sorunları
- Bağlantı sorunları
- Cache sorunları
- Hata kodları
- Monitoring ve debugging
- Destek iletişim bilgileri

**Ne Zaman Kullanılır:** Production'da sorun yaşandığında veya hata ayıklarken.

---

#### [Performance Tuning Guide](./PERFORMANCE_TUNING.md)
**Hedef Kitle:** Performance engineers, senior geliştiriciler

**İçerik:**
- Performance targets ve current metrics
- Cache optimization
  - Multi-layer cache tuning
  - Cache key optimization
  - Cache invalidation strategy
- Database optimization
  - Index optimization
  - Query optimization
  - Connection pooling
- Parallel processing optimization
- Response optimization (compression, pagination)
- Rate limiting optimization
- YouTube API optimization
- Monitoring ve profiling
- Load testing
- Horizontal scaling

**Ne Zaman Kullanılır:** Performans sorunları yaşandığında veya optimization yaparken.

---

### 📊 Özelleştirilmiş Dokümanlar

#### [Multi-Layer Cache](./MULTI_LAYER_CACHE.md)
Cache stratejisi detayları

#### [Structured Logging Guide](./STRUCTURED_LOGGING_GUIDE.md)
Logging best practices ve implementation

#### [Metrics System](./METRICS_SYSTEM.md)
Prometheus metrics ve monitoring

#### [Database Optimization Guide](./DATABASE_OPTIMIZATION_GUIDE.md)
Database performance tuning

#### [Monitoring & Alerting Setup](./MONITORING_ALERTING_SETUP.md)
Monitoring infrastructure kurulumu

---

## 🎯 Kullanım Senaryoları

### Senaryo 1: Yeni Geliştirici Onboarding

**Adımlar:**
1. [Developer Setup Guide](./DEVELOPER_SETUP.md) - Local environment kurulumu
2. [API Documentation](./VIDEO_API.md) - API'yi anlama
3. [Architecture Document](./ARCHITECTURE.md) - Sistem mimarisini öğrenme
4. [Architecture Diagrams](./ARCHITECTURE_DIAGRAM.md) - Görsel olarak sistemi anlama

**Tahmini Süre:** 2-4 saat

---

### Senaryo 2: API Entegrasyonu

**Adımlar:**
1. [API Documentation](./VIDEO_API.md) - Endpoint'leri öğrenme
2. Code examples - Implementation
3. [Troubleshooting Guide](./TROUBLESHOOTING.md) - Sorun giderme

**Tahmini Süre:** 1-2 saat

---

### Senaryo 3: Production Sorun Giderme

**Adımlar:**
1. [Troubleshooting Guide](./TROUBLESHOOTING.md) - Hızlı tanı
2. Health check endpoint - Servis durumu kontrolü
3. Logs - Hata analizi
4. Metrics - Performance analizi
5. [Performance Tuning Guide](./PERFORMANCE_TUNING.md) - Optimization (gerekirse)

**Tahmini Süre:** 30 dakika - 2 saat

---

### Senaryo 4: Performance Optimization

**Adımlar:**
1. [Performance Tuning Guide](./PERFORMANCE_TUNING.md) - Optimization stratejileri
2. Load testing - Benchmark
3. Profiling - Bottleneck tespiti
4. Implementation - Optimization uygulama
5. Monitoring - Impact ölçümü

**Tahmini Süre:** 1-2 gün

---

### Senaryo 5: Architectural Decision

**Adımlar:**
1. [Architecture Document](./ARCHITECTURE.md) - Mevcut mimari
2. [Architecture Diagrams](./ARCHITECTURE_DIAGRAM.md) - Görsel analiz
3. Design discussion - Alternatifler
4. Decision - Trade-offs değerlendirme
5. Documentation update - Karar dokümante etme

**Tahmini Süre:** 2-4 saat

---

## 📖 Doküman Kategorileri

### Başlangıç (Getting Started)
- ✅ [Developer Setup Guide](./DEVELOPER_SETUP.md)
- ✅ [API Documentation](./VIDEO_API.md)

### Mimari (Architecture)
- ✅ [Architecture Document](./ARCHITECTURE.md)
- ✅ [Architecture Diagrams](./ARCHITECTURE_DIAGRAM.md)

### Operasyonel (Operations)
- ✅ [Troubleshooting Guide](./TROUBLESHOOTING.md)
- ✅ [Performance Tuning Guide](./PERFORMANCE_TUNING.md)
- ✅ [Monitoring & Alerting Setup](./MONITORING_ALERTING_SETUP.md)

### Teknik Detaylar (Technical Details)
- ✅ [Multi-Layer Cache](./MULTI_LAYER_CACHE.md)
- ✅ [Structured Logging Guide](./STRUCTURED_LOGGING_GUIDE.md)
- ✅ [Metrics System](./METRICS_SYSTEM.md)
- ✅ [Database Optimization Guide](./DATABASE_OPTIMIZATION_GUIDE.md)

---

## 🔍 Hızlı Referans

### Sık Kullanılan Komutlar

```bash
# Backend başlatma
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Frontend başlatma
cd frontend
npm run dev

# Health check
curl http://localhost:8000/api/youtube/health

# API test
curl http://localhost:8000/api/youtube/test

# Tests çalıştırma
pytest
npm run test

# Logs görüntüleme
tail -f backend/app.log

# Redis kontrolü
redis-cli ping

# Database kontrolü
sqlite3 backend/turkiye_sinav.db ".tables"
```

### Sık Kullanılan Endpoint'ler

```bash
# Video önerileri
POST http://localhost:8000/api/youtube/recommendations

# Sağlık kontrolü
GET http://localhost:8000/api/youtube/health

# API testi
GET http://localhost:8000/api/youtube/test

# Metrics
GET http://localhost:8000/metrics

# OpenAPI docs
GET http://localhost:8000/docs
```

### Sık Karşılaşılan Sorunlar

| Sorun | Doküman | Bölüm |
|-------|---------|-------|
| Backend başlamıyor | [Troubleshooting](./TROUBLESHOOTING.md) | Backend Başlamıyor |
| CORS hatası | [Troubleshooting](./TROUBLESHOOTING.md) | CORS Hatası |
| Yavaş yanıt | [Performance Tuning](./PERFORMANCE_TUNING.md) | Cache Optimization |
| Rate limit | [API Documentation](./VIDEO_API.md) | Rate Limiting |
| Türkçe olmayan videolar | [Troubleshooting](./TROUBLESHOOTING.md) | Türkçe Olmayan Videolar |

---

## 📝 Doküman Güncelleme

### Güncelleme Prosedürü

1. **Değişiklik Yap:** Dokümanı düzenle
2. **Review:** Code review sürecinden geçir
3. **Test:** Örnekleri test et
4. **Commit:** Anlamlı commit message ile commit et
5. **Deploy:** Documentation site'a deploy et

### Doküman Versiyonlama

Dokümanlar API versiyonu ile senkronize tutulur:
- **v1.0.0:** İlk production release
- **v1.1.0:** Minor updates
- **v2.0.0:** Breaking changes

### Katkıda Bulunma

Doküman iyileştirmeleri için:
1. Issue aç (documentation label ile)
2. Pull request oluştur
3. Review bekle
4. Merge sonrası otomatik deploy

---

## 🔗 Harici Kaynaklar

### Framework Documentation
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Redis](https://redis.io/docs/)
- [SQLite](https://www.sqlite.org/docs.html)

### API Documentation
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [Google Cloud Console](https://console.cloud.google.com/)

### Tools
- [Postman](https://www.postman.com/)
- [Grafana](https://grafana.com/docs/)
- [Prometheus](https://prometheus.io/docs/)

---

## 📞 Destek

### Sorularınız mı var?

**Slack Channels:**
- #video-api-dev (Geliştirici soruları)
- #video-api-support (Genel sorular)
- #video-api-incidents (Acil durumlar)

**Email:**
- dev@teknofest-egitim.com (Geliştirici soruları)
- support@teknofest-egitim.com (Genel destek)
- oncall@teknofest-egitim.com (Acil durumlar)

**GitHub:**
- [Issues](https://github.com/teknofest-2025-egitim-eylemci/issues)
- [Discussions](https://github.com/teknofest-2025-egitim-eylemci/discussions)

---

## 📅 Son Güncelleme

**Tarih:** 1 Kasım 2024  
**Versiyon:** 1.0.0  
**Güncelleyen:** Video API Team

---

## ✅ Doküman Tamamlanma Durumu

- [x] API Documentation
- [x] Architecture Document
- [x] Architecture Diagrams
- [x] Troubleshooting Guide
- [x] Developer Setup Guide
- [x] Performance Tuning Guide
- [x] Documentation Index (bu dosya)

**Toplam:** 7/7 doküman tamamlandı ✅

---

## 🎉 Başarıyla Tamamlandı!

Video Recommendation API dokümantasyonu eksiksiz olarak hazırlanmıştır. Tüm gereksinimler (Requirements 12.1, 12.2, 12.3, 12.6, 12.7, 12.8, 12.9) karşılanmıştır.

**Kapsanan Konular:**
- ✅ API endpoint documentation (OpenAPI/Swagger)
- ✅ Architecture diagrams
- ✅ Troubleshooting guide
- ✅ Developer setup guide
- ✅ Performance tuning guide
- ✅ Request/response examples
- ✅ Error codes ve solutions
- ✅ Monitoring ve debugging

**Sonraki Adımlar:**
1. Dokümanları review et
2. Örnekleri test et
3. Team ile paylaş
4. Production'a deploy et
