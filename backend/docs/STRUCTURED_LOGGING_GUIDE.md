# Structured Logging System - Teknofest 2025 Eğitim Eylemci Platformu

## 📋 Genel Bakış

Bu dokümantasyon, Teknofest 2025 Eğitim Eylemci Platformu için geliştirilmiş kapsamlı structured logging sisteminin kullanım kılavuzudur.

## 🚀 Özellikler

### ✅ Tamamlanan Özellikler

- **JSON Formatında Logging**: Tüm loglar JSON formatında structured olarak kaydedilir
- **Log Levels ve Kategoriler**: DEBUG, INFO, WARNING, ERROR, CRITICAL seviyeleri ve 12 farklı kategori
- **Request/Response Middleware**: FastAPI için otomatik HTTP request/response loglama
- **Error Tracking**: Detaylı exception loglama ve stack trace yönetimi
- **Log Rotation**: Otomatik dosya boyutu bazlı log rotation (10MB, 5 backup)
- **Performance Monitoring**: Fonksiyon çalışma süresi ve performans metrikleri
- **Database Query Logging**: Veritabanı işlemlerinin detaylı loglanması
- **Agent Activity Logging**: AI Agent aktivitelerinin takibi
- **User Action Logging**: Kullanıcı eylemlerinin detaylı kaydı
- **Log Analysis Tools**: Hata kalıpları ve performans analizi
- **CLI Management Tool**: Komut satırı log yönetim aracı
- **Retention Policies**: Otomatik log temizleme ve sıkıştırma

## 📁 Dosya Yapısı

```
backend/
├── core/
│   ├── structured_logger.py      # Ana logger sınıfı
│   ├── logging_middleware.py     # FastAPI middleware
│   ├── log_config.py            # Konfigürasyon ve yönetim
│   └── logging_integration.py   # FastAPI entegrasyonu
├── scripts/
│   └── log_manager.py           # CLI yönetim aracı
├── tests/
│   └── test_structured_logging.py  # Test dosyası
├── docs/
│   └── STRUCTURED_LOGGING_GUIDE.md  # Bu dokümantasyon
└── demo_structured_logging.py   # Demo ve örnek kullanım
```

## 🔧 Kurulum ve Konfigürasyon

### 1. Temel Kurulum

```python
from core.structured_logger import setup_logging, LogLevel

# Basit kurulum
logger = setup_logging(
    log_dir="logs",
    console_level=LogLevel.INFO,
    file_level=LogLevel.DEBUG
)
```

### 2. FastAPI Entegrasyonu

```python
from fastapi import FastAPI
from core.logging_integration import setup_fastapi_logging

app = FastAPI()

# Logging sistemini FastAPI'ye entegre et
logging_integration = setup_fastapi_logging(
    app,
    log_dir="logs",
    console_level=LogLevel.INFO,
    enable_request_logging=True,
    log_request_body=True
)
```

### 3. Environment Konfigürasyonu

```bash
# .env dosyasında
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## 📝 Kullanım Örnekleri

### 1. Temel Loglama

```python
from core.structured_logger import get_logger, LogCategory

logger = get_logger("my-service")

# Basit log
logger.info("İşlem başarılı", LogCategory.SYSTEM)

# Ek verilerle log
logger.info(
    "Kullanıcı giriş yaptı", 
    LogCategory.AUTH,
    user_id="123",
    ip_address="192.168.1.1"
)
```

### 2. Kullanıcı Eylem Loglama

```python
logger.log_user_action(
    user_id="student_123",
    action="exam_started",
    details={
        "exam_type": "TYT",
        "subject": "Matematik",
        "duration": 165
    }
)
```

### 3. Performans Loglama

```python
# Decorator ile otomatik performans loglama
from core.structured_logger import log_execution_time

@log_execution_time(LogCategory.PERFORMANCE)
async def generate_questions(count: int):
    # İş mantığı
    return questions

# Manuel performans loglama
logger.log_performance(
    operation="database_query",
    duration_ms=45.2,
    success=True,
    rows_affected=10
)
```

### 4. Exception Loglama

```python
try:
    # Riskli işlem
    result = risky_operation()
except Exception as e:
    logger.log_exception(
        "İşlem başarısız oldu",
        e,
        LogCategory.SYSTEM,
        operation_id="op_123"
    )
    raise
```

### 5. API Çağrı Loglama

```python
logger.log_api_call(
    method="POST",
    endpoint="/api/v1/exam/start",
    status_code=200,
    duration_ms=150.0,
    user_id="student_123"
)
```

### 6. Agent Aktivite Loglama

```python
logger.log_agent_activity(
    agent_name="LearningPathAgent",
    activity="generate_learning_path",
    student_id="student_123",
    success=True,
    path_length=8
)
```

## 🏷️ Log Kategorileri

| Kategori | Açıklama | Örnek Kullanım |
|----------|----------|----------------|
| `SYSTEM` | Sistem olayları | Uygulama başlatma/kapanma |
| `AUTH` | Kimlik doğrulama | Kullanıcı giriş/çıkış |
| `EXAM` | Sınav işlemleri | Sınav başlatma/bitirme |
| `LEARNING` | Öğrenme aktiviteleri | Öğrenme yolu oluşturma |
| `API` | API çağrıları | HTTP request/response |
| `DATABASE` | Veritabanı işlemleri | SQL sorguları |
| `CACHE` | Cache işlemleri | Redis hit/miss |
| `AGENT` | AI Agent aktiviteleri | Agent koordinasyonu |
| `CONTENT` | İçerik yönetimi | Video/soru yükleme |
| `PERFORMANCE` | Performans metrikleri | Yavaş işlemler |
| `SECURITY` | Güvenlik olayları | Şüpheli aktiviteler |
| `USER_ACTION` | Kullanıcı eylemleri | Sınav başlatma, soru çözme |

## 📊 Log Seviyeleri

| Seviye | Açıklama | Ne Zaman Kullanılır |
|--------|----------|-------------------|
| `DEBUG` | Detaylı debug bilgisi | Development ortamında |
| `INFO` | Genel bilgi | Normal işlem akışı |
| `WARNING` | Uyarı | Potansiyel problemler |
| `ERROR` | Hata | İşlem hataları |
| `CRITICAL` | Kritik hata | Sistem çökmesi |

## 🔍 Log Analizi

### 1. Hata Analizi

```python
from core.log_config import get_log_analyzer

analyzer = get_log_analyzer()

# Son 24 saatteki hataları analiz et
error_patterns = analyzer.analyze_error_patterns(hours=24)

print(f"Toplam hata: {error_patterns['total_errors']}")
print(f"En çok görülen hata: {error_patterns['top_errors'][0]}")
```

### 2. Performans Analizi

```python
# Performans metriklerini al
perf_metrics = analyzer.get_performance_metrics(hours=24)

print(f"Ortalama yanıt süresi: {perf_metrics['avg_response_time']:.2f}ms")
print(f"Yavaş istekler: {len(perf_metrics['slow_requests'])}")
```

## 🛠️ CLI Yönetim Aracı

### Kurulum

```bash
cd backend
py scripts/log_manager.py --help
```

### Komutlar

#### Dashboard - Genel Durum

```bash
py scripts/log_manager.py dashboard --log-dir logs
```

#### Log Dosya Boyutları

```bash
py scripts/log_manager.py sizes --log-dir logs
```

#### Hata Analizi

```bash
py scripts/log_manager.py analyze-errors --hours 24 --output errors.json
```

#### Performans Analizi

```bash
py scripts/log_manager.py analyze-performance --hours 24 --output performance.json
```

#### Log Temizleme

```bash
# Dry-run (sadece göster)
py scripts/log_manager.py cleanup --retention-days 30 --dry-run

# Gerçek temizlik
py scripts/log_manager.py cleanup --retention-days 30
```

#### Log Sıkıştırma

```bash
py scripts/log_manager.py compress --days-old 7
```

#### Canlı Log Takibi

```bash
# Tüm logları göster
py scripts/log_manager.py tail-logs --hours 1 --tail 50

# Sadece ERROR seviyesi
py scripts/log_manager.py tail-logs --level ERROR --hours 1

# Sadece AUTH kategorisi
py scripts/log_manager.py tail-logs --category auth --hours 1
```

## 📋 JSON Log Formatı

### Örnek Log Kaydı

```json
{
  "timestamp": "2025-09-20T06:01:16.346228+00:00",
  "level": "INFO",
  "logger": "teknofest-platform",
  "message": "Kullanıcı sınav başlattı",
  "module": "exam_service",
  "function": "start_exam",
  "line": 45,
  "thread": 8800,
  "process": 18036,
  "request_id": "e6638fd7-79ad-4391-bcfc-d71f334b30a6",
  "category": "exam",
  "service": "teknofest-egitim-platformu",
  "user_id": "student_123",
  "exam_id": "exam_456",
  "exam_type": "TYT",
  "duration_minutes": 165
}
```

### Exception Log Örneği

```json
{
  "timestamp": "2025-09-20T06:01:16.349242+00:00",
  "level": "ERROR",
  "logger": "teknofest-platform",
  "message": "Sınav başlatma hatası",
  "category": "exam",
  "user_id": "student_123",
  "exception_type": "DatabaseConnectionError",
  "exception_message": "Connection timeout",
  "stack_trace": "Traceback (most recent call last):\n  File..."
}
```

## 🔒 Güvenlik ve Gizlilik

### Hassas Veri Gizleme

Sistem otomatik olarak şu alanları gizler:

- `password`, `sifre`, `parola`
- `token`, `secret`, `key`
- `auth`, `anahtar`, `gizli`

```python
# Otomatik gizleme
log_data = {
    "username": "student123",
    "password": "secret123",  # → "***HIDDEN***"
    "email": "student@example.com"
}
```

## 📈 Performans Optimizasyonu

### 1. Log Rotation

- Dosya boyutu: 10MB maksimum
- Backup sayısı: 5 dosya
- Otomatik sıkıştırma: 7 gün sonra

### 2. Async Logging

```python
# Async fonksiyonlar için
@log_execution_time(LogCategory.PERFORMANCE)
async def async_operation():
    await some_async_work()
```

### 3. Filtreleme

```python
from core.structured_logger import LogFilter

# Sadece ERROR ve üstü
filter = LogFilter()
error_filter = filter.add_level_filter(LogLevel.ERROR)

# Sadece belirli kategoriler
category_filter = filter.add_category_filter([
    LogCategory.AUTH, 
    LogCategory.SECURITY
])
```

## 🚨 Monitoring ve Alerting

### 1. Hata Eşikleri

- **WARNING**: 10+ hata/saat
- **CRITICAL**: 50+ hata/saat
- **Yavaş İstekler**: >2 saniye

### 2. Otomatik Temizlik

```python
# Production ortamında otomatik aktif
integration.setup_periodic_cleanup(retention_days=30)
```

## 🧪 Test Etme

### Unit Testler

```bash
cd backend
py -m pytest tests/test_structured_logging.py -v
```

### Demo Çalıştırma

```bash
cd backend
py demo_structured_logging.py
```

## 🔧 Troubleshooting

### Yaygın Sorunlar

#### 1. Log Dosyası Oluşmuyor

```python
# Log dizininin var olduğundan emin olun
from pathlib import Path
Path("logs").mkdir(exist_ok=True)
```

#### 2. JSON Parse Hatası

```python
# Türkçe karakter desteği için
import json
json.dumps(data, ensure_ascii=False)
```

#### 3. Performans Sorunları

```python
# Log seviyesini ayarlayın
logger.setLevel(logging.INFO)  # DEBUG'ı kapatın
```

## 📚 İleri Seviye Kullanım

### 1. Custom Formatter

```python
from core.structured_logger import JSONFormatter

class CustomFormatter(JSONFormatter):
    def format(self, record):
        # Özel formatınızı ekleyin
        return super().format(record)
```

### 2. Custom Middleware

```python
from core.logging_middleware import RequestResponseLoggingMiddleware

class CustomLoggingMiddleware(RequestResponseLoggingMiddleware):
    async def dispatch(self, request, call_next):
        # Özel mantığınızı ekleyin
        return await super().dispatch(request, call_next)
```

### 3. Log Aggregation

```python
# ELK Stack entegrasyonu için
logger.info(
    "Event occurred",
    LogCategory.SYSTEM,
    elk_index="teknofest-logs",
    elk_type="application"
)
```

## 📞 Destek

Sorularınız için:
- **Dokümantasyon**: Bu dosya
- **Demo**: `demo_structured_logging.py`
- **Testler**: `tests/test_structured_logging.py`
- **CLI Yardım**: `py scripts/log_manager.py --help`

---

**Teknofest 2025 Eğitim Eylemci Platformu**  
*Structured Logging System v1.0*