"""
OpenAPI Configuration for Kiro2 Platform
Sprint 9: Enhanced API Documentation

Comprehensive OpenAPI configuration with metadata, tags, and examples.
"""
from typing import Dict, List

# OpenAPI Metadata
OPENAPI_METADATA = {
    "title": "Kiro2 - Türkiye Üniversite Sınavları Hazırlık Platformu API",
    "version": "1.0.0",
    "description": """
# 🎓 Kiro2 Platform API

**Kiro2**, Türk öğrencileri için YKS (TYT/AYT/YDT) üniversite giriş sınavlarına hazırlık sunan
yapay zeka destekli eğitim platformudur.

## 🌟 Temel Özellikler

### 🧠 Yapay Zeka Destekli Öğrenme
- **Adaptive Learning**: FSRS algoritması ile kişiselleştirilmiş öğrenme
- **IRT (Item Response Theory)**: Soru tepki kuramı ile yetenek ölçümü
- **ZPD (Zone of Proximal Development)**: Vygotsky teorisi ile optimal zorluk seviyesi
- **CAT (Computer Adaptive Testing)**: Gerçek zamanlı adaptif sınav motoru

### 📚 Kapsamlı İçerik
- **40,000+ ÖSYM sorusu**: Geçmiş YKS sorularının tam arşivi
- **Türkçe NLP**: Zemberek ile gelişmiş Türkçe dil işleme
- **Multimedya**: Video çözümler, görsel destekler, manipülatifler
- **Bionic Reading**: Geliştirilmiş okuma hızı ve anlama

### 📊 Gelişmiş Analitik
- **Gerçek Zamanlı Performans**: Anlık performans takibi
- **Predictive Analytics**: Başarı tahmini ve önerileri
- **Benchmark**: Türkiye geneli karşılaştırma
- **Dashboard**: Öğrenci, öğretmen ve veli panelleri

### 🔒 Güvenlik & Uyumluluk
- **KVKK Uyumlu**: Türkiye Kişisel Verilerin Korunması Kanunu
- **2FA**: TOTP tabanlı iki faktörlü kimlik doğrulama
- **Rate Limiting**: Gelişmiş hız sınırlama (FREE/PREMIUM/ADMIN)
- **JWT Authentication**: Güvenli token tabanlı kimlik doğrulama

## 🏗️ Mimari

- **Backend**: FastAPI + SQLAlchemy 2.0 + PostgreSQL
- **Cache**: Redis (multi-layer caching)
- **AI/ML**: GPT-4, BERTurk, PyTorch
- **Monitoring**: Prometheus + Grafana
- **Container**: Docker + Docker Compose

## 📖 Kullanım

### Kimlik Doğrulama
Tüm API istekleri için JWT token gereklidir (health check hariç):
```bash
curl -X POST "https://api.kiro2.com/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "user@example.com", "password": "password"}'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Authenticated İstekler
```bash
curl -X GET "https://api.kiro2.com/api/v1/user/profile" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Rate Limiting
API istekleri kullanıcı seviyesine göre sınırlandırılmıştır:
- **FREE**: 60 req/min (genel), 10 req/min (auth), 20 req/min (AI)
- **PREMIUM**: 300 req/min (genel), 30 req/min (auth), 100 req/min (AI)
- **ADMIN**: 10,000 req/min (genel)

Rate limit bilgileri response header'larında:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699876543
Retry-After: 15 (rate limit aşıldığında)
```

## 🎯 API Kategorileri

API endpointleri aşağıdaki kategorilerde organize edilmiştir:

- **Authentication**: Kullanıcı girişi, kayıt, 2FA
- **User Management**: Profil, ayarlar, tercihler
- **Exam System**: Sınav oluşturma, soru çözme, sonuçlar
- **Content**: Soru bankası, videolar, materyal
- **Learning Path**: Kişiselleştirilmiş öğrenme yolu
- **Analytics**: Performans, istatistikler, raporlar
- **KVKK**: Gizlilik, onaylar, veri hakları
- **Admin**: Yönetim, moderasyon, sistem

## 🔗 Harici Kaynaklar

- **Documentation**: https://docs.kiro2.com
- **GitHub**: https://github.com/yourusername/kiro2
- **Support**: support@kiro2.com
- **Status**: https://status.kiro2.com

## 📄 Lisans

Copyright © 2025 Kiro2 Platform. All rights reserved.
""",
    "contact": {
        "name": "Kiro2 Platform Support",
        "url": "https://kiro2.com/support",
        "email": "support@kiro2.com",
    },
    "license_info": {
        "name": "Proprietary",
        "url": "https://kiro2.com/license",
    },
    "terms_of_service": "https://kiro2.com/terms",
}

# OpenAPI Tags for API Organization
OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": """
**Kimlik Doğrulama & Yetkilendirme**

Kullanıcı girişi, kayıt, token yönetimi ve iki faktörlü kimlik doğrulama (2FA) işlemleri.

**Endpoints:**
- `POST /api/v1/auth/register` - Yeni kullanıcı kaydı
- `POST /api/v1/auth/login` - Kullanıcı girişi
- `POST /api/v1/auth/refresh` - Token yenileme
- `POST /api/v1/auth/2fa/enable` - 2FA etkinleştirme
- `POST /api/v1/auth/2fa/verify` - 2FA doğrulama

**Rate Limits:**
- FREE: 10 req/min
- PREMIUM: 30 req/min
""",
    },
    {
        "name": "User Management",
        "description": """
**Kullanıcı Yönetimi**

Kullanıcı profili, ayarları, tercihleri ve hesap yönetimi.

**Endpoints:**
- `GET /api/v1/user/profile` - Profil bilgilerini getir
- `PUT /api/v1/user/profile` - Profili güncelle
- `GET /api/v1/user/preferences` - Tercihleri getir
- `PUT /api/v1/user/preferences` - Tercihleri güncelle
- `DELETE /api/v1/user/account` - Hesabı sil

**Features:**
- Profil fotoğrafı yükleme
- Öğrenme tercihleri (VARK, Felder-Silverman)
- Bildirim ayarları
- Gizlilik ayarları
""",
    },
    {
        "name": "Exam System",
        "description": """
**Sınav Sistemi**

TYT, AYT, YDT sınavları oluşturma, çözme ve sonuç analizi.

**Exam Types:**
- **TYT**: Temel Yeterlilik Testi (120 soru)
- **AYT**: Alan Yeterlilik Testi (80 soru)
- **YDT**: Yabancı Dil Testi (80 soru)
- **Mock Exam**: Deneme sınavı
- **Adaptive Exam**: Adaptif sınav (CAT)

**Endpoints:**
- `POST /api/v1/exam/create` - Sınav oluştur
- `POST /api/v1/exam/{exam_id}/start` - Sınavı başlat
- `POST /api/v1/exam/{exam_id}/answer` - Soru cevapla
- `POST /api/v1/exam/{exam_id}/finish` - Sınavı bitir
- `GET /api/v1/exam/{exam_id}/results` - Sonuçları getir

**Features:**
- Gerçek zamanlı sınav
- Optik form desteği
- Video çözümler
- Detaylı analiz
""",
    },
    {
        "name": "Question Bank",
        "description": """
**Soru Bankası**

40,000+ ÖSYM sorusu ve gelişmiş filtreleme.

**Endpoints:**
- `GET /api/v1/questions/search` - Soru arama
- `GET /api/v1/questions/{question_id}` - Soru detayı
- `GET /api/v1/questions/similar` - Benzer sorular
- `POST /api/v1/questions/generate` - AI ile soru üretimi

**Filters:**
- Konu/alt konu
- Zorluk seviyesi (IRT parametreleri)
- Sınav türü (TYT/AYT/YDT)
- Bloom taksonomisi
- Yıl/dönem

**Features:**
- Türkçe morfolojik analiz (Zemberek)
- IRT parametreleri (a, b, c)
- Detaylı çözümler
- İstatistikler
""",
    },
    {
        "name": "Learning Path",
        "description": """
**Kişiselleştirilmiş Öğrenme Yolu**

AI destekli adaptif öğrenme yolu ve içerik önerisi.

**Algorithms:**
- **FSRS**: Spaced repetition
- **IRT**: Ability estimation (theta)
- **ZPD**: Optimal challenge level
- **CAT**: Adaptive question selection

**Endpoints:**
- `GET /api/v1/learning-path` - Öğrenme yolunu getir
- `POST /api/v1/learning-path/update` - İlerlemeyi güncelle
- `GET /api/v1/learning-path/recommendations` - Öneriler

**Features:**
- Günlük çalışma planı
- Haftalık hedefler
- Konu önceliklendirme
- Tekrar planlaması (FSRS)
""",
    },
    {
        "name": "Analytics",
        "description": """
**Performans Analizi & İstatistikler**

Detaylı performans takibi ve predictive analytics.

**Endpoints:**
- `GET /api/v1/analytics/performance` - Performans özeti
- `GET /api/v1/analytics/progress` - İlerleme grafiği
- `GET /api/v1/analytics/predictions` - Başarı tahmini
- `GET /api/v1/analytics/benchmark` - Karşılaştırma

**Metrics:**
- Soru başarı oranı
- Konu bazlı performans
- Öğrenme hızı
- Güçlü/zayıf konular
- YKS başarı tahmini

**Visualizations:**
- Zaman serisi grafikleri
- Isı haritaları
- Radar charts
- Trend analizi
""",
    },
    {
        "name": "Content",
        "description": """
**İçerik Yönetimi**

Video çözümler, EBA içerikleri, Khan Academy ve multimedya.

**Content Types:**
- Video çözümler
- EBA TV içerikleri
- Khan Academy dersleri
- PDF dökümanlar
- İnteraktif simülasyonlar

**Endpoints:**
- `GET /api/v1/content/videos` - Video listesi
- `GET /api/v1/content/eba` - EBA içerikleri
- `GET /api/v1/content/khan` - Khan Academy
- `GET /api/v1/content/search` - İçerik arama

**Features:**
- Semantic search
- Video transkriptleri
- Türkçe altyazı
- İzleme geçmişi
""",
    },
    {
        "name": "KVKK",
        "description": """
**KVKK Uyumluluk**

Kişisel Verilerin Korunması Kanunu (GDPR) uyumluluğu.

**Rights:**
- **Madde 5**: Açık rıza
- **Madde 7**: Bilgilendirilme
- **Madde 11**: Veri sahibi hakları
- **Madde 12**: Veri güvenliği

**Endpoints:**
- `GET /api/v1/kvkk/consents` - Onayları getir
- `POST /api/v1/kvkk/consent` - Onay ver/geri çek
- `GET /api/v1/kvkk/privacy/export` - Verilerimi indir
- `DELETE /api/v1/kvkk/privacy/delete` - Verilerimi sil
- `GET /api/v1/kvkk/audit-log` - Denetim kaydı

**Features:**
- Granular consent management
- Data export (JSON/PDF)
- Right to be forgotten
- Audit logging
""",
    },
    {
        "name": "Admin",
        "description": """
**Yönetim Paneli**

Sistem yönetimi, moderasyon ve raporlama (yalnızca admin).

**Endpoints:**
- `GET /api/v1/admin/users` - Kullanıcı listesi
- `GET /api/v1/admin/statistics` - Sistem istatistikleri
- `POST /api/v1/admin/questions/review` - Soru onay
- `GET /api/v1/admin/audit` - Denetim logları

**Features:**
- Kullanıcı yönetimi
- İçerik moderasyonu
- Sistem izleme
- Bulk operations

**Permissions:**
- ADMIN role required
- Rate limit: 10,000 req/min
""",
    },
    {
        "name": "Health & Monitoring",
        "description": """
**Sistem Sağlığı & İzleme**

Health check, metrics ve sistem durumu.

**Endpoints:**
- `GET /health` - Basit health check
- `GET /health/detailed` - Detaylı health check
- `GET /metrics` - Prometheus metrics

**No Authentication Required**

**Components Checked:**
- Database (PostgreSQL)
- Cache (Redis)
- Elasticsearch
- AI Services
- External APIs
""",
    },
]

# API Servers Configuration
OPENAPI_SERVERS = [
    {
        "url": "https://api.kiro2.com",
        "description": "Production server",
    },
    {
        "url": "https://staging-api.kiro2.com",
        "description": "Staging server",
    },
    {
        "url": "http://localhost:8000",
        "description": "Local development server",
    },
]

# External Documentation
OPENAPI_EXTERNAL_DOCS = {
    "description": "Kiro2 Platform Full Documentation",
    "url": "https://docs.kiro2.com",
}


def get_openapi_config() -> Dict:
    """
    Get complete OpenAPI configuration

    Returns:
        Dict: OpenAPI configuration dictionary
    """
    return {
        **OPENAPI_METADATA,
        "openapi_tags": OPENAPI_TAGS,
        "servers": OPENAPI_SERVERS,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }


def get_openapi_tags() -> List[Dict]:
    """
    Get OpenAPI tags for API organization

    Returns:
        List[Dict]: List of OpenAPI tags
    """
    return OPENAPI_TAGS


# JWT Security Scheme for OpenAPI
OPENAPI_SECURITY_SCHEMES = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": """
JWT Bearer Token kimlik dogrulama.

Token almak icin:
1. `POST /api/v1/auth/giris` endpoint'ine istek gonder
2. Donen `access_token` degerini kullan

Ornek:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Token suresi: 24 saat (configurable)
Refresh token: 7 gun
""",
    },
}

# Global Security Requirement (applied to all authenticated endpoints)
OPENAPI_SECURITY = [{"BearerAuth": []}]


def get_security_schemes() -> Dict:
    """
    Get OpenAPI security schemes

    Returns:
        Dict: Security schemes configuration
    """
    return OPENAPI_SECURITY_SCHEMES
