# MCP Services Setup Guide

## Genel Bakış

Bu kılavuz, Kiro platformunun 19 MCP (Model Context Protocol) sunucusunu başlatma ve yönetme işlemlerini açıklar.

## Hızlı Başlangıç

### 1. Ortam Değişkenlerini Ayarlama

```powershell
# .env.mcp.example dosyasını .env.mcp olarak kopyalayın
Copy-Item .env.mcp.example .env.mcp

# API anahtarlarınızı .env.mcp dosyasına ekleyin
# Önemli: Asla gerçek API anahtarlarını commit etmeyin!
```

### 2. Docker Servislerini Başlatma

```powershell
# Redis, Elasticsearch, PostgreSQL, Prometheus başlatılır
docker-compose up -d redis elasticsearch postgres prometheus
```

### 3. MCP Sunucularını Başlatma

```powershell
# Tüm MCP sunucularını doğru sırayla başlatır
.\scripts\start_mcp_services.ps1
```

### 4. Sağlık Kontrolü

```powershell
# Tüm servislerin durumunu kontrol edin
python .\scripts\check_mcp_health.py
```

## Scriptler

### start_mcp_services.ps1

MCP sunucularını bağımlılık sırasına göre başlatır.

**Kullanım:**
```powershell
# Normal başlatma (Docker + MCP)
.\scripts\start_mcp_services.ps1

# Docker'ı atla (sadece MCP sunucuları)
.\scripts\start_mcp_services.ps1 -SkipDocker

# Health check'i atla (hızlı başlatma)
.\scripts\start_mcp_services.ps1 -SkipHealthCheck
```

**Başlatma Sırası:**
1. **Zemberek NLP Service** (port 8081) - Türkçe NLP için temel servis
2. **Multi-Agent Blackboard** (port 8765) - Agent koordinasyonu
3. **Video Quality Validators** - Paralel olarak başlar:
   - Turkish Content Filter
   - Subject Relevance Scorer
   - Video Quality Validator
4. **Enhanced Recommendation Engine** - Validatörlere bağımlı
5. **Video Recommendation Monitoring** (port 9091)
6. **Hybrid Learning Style Detector**
7. **Platform Health Audit**

**Loglar:**
- Konum: `logs/*.log`
- Format: Her servis için ayrı log dosyası
- Hata logları: `logs/*.log.err`

**PID Dosyaları:**
- Konum: `.mcp_pids/*.pid`
- Kullanım: Servisleri durdurmak için

### stop_mcp_services.ps1

MCP sunucularını güvenli bir şekilde durdurur.

**Kullanım:**
```powershell
# Sadece MCP sunucularını durdur
.\scripts\stop_mcp_services.ps1

# MCP + Docker servislerini durdur
.\scripts\stop_mcp_services.ps1 -StopDocker

# Zorla durdur (graceful shutdown olmadan)
.\scripts\stop_mcp_services.ps1 -Force
```

**Ne Yapar:**
- PID dosyalarını okur ve servisleri durdurur
- Eski PID dosyalarını temizler
- Logları arşivler (timestamp ile)
- İsteğe bağlı olarak Docker servislerini durdurur

### check_mcp_health.py

Tüm servislerin sağlık durumunu kontrol eder.

**Kullanım:**
```powershell
python .\scripts\check_mcp_health.py
```

**Kontrol Edilen Şeyler:**
- ✅ Docker servisleri (Redis, Elasticsearch, PostgreSQL, Prometheus)
- ✅ MCP sunucuları (PID kontrolü)
- ✅ Port dinleme durumu (8081, 8765, 9091)
- ✅ Log dosyalarında hata analizi

**Çıktı:**
- Terminal: Renkli durum raporu
- JSON rapor: `reports/health/health_check_YYYYMMDD_HHMMSS.json`
- Latest rapor: `reports/health/latest.json`

**Health Score:**
- **80-100%**: Sistem sağlıklı ✅
- **50-79%**: Bazı sorunlar var ⚠️
- **0-49%**: Sistem sağlıksız ❌

## Gereksinimler

### Yazılım Gereksinimleri

```powershell
# Python 3.10+
python --version

# Java 11+ (Zemberek için)
java -version

# Docker Desktop (Windows)
docker --version
docker-compose --version

# PowerShell 5.1+ (Windows'ta varsayılan)
$PSVersionTable.PSVersion
```

### Python Paketleri

```powershell
# Backend bağımlılıklarını yükle
pip install -r backend/requirements.txt

# Ek paketler (health check için)
pip install requests redis
```

### Java Bağımlılıkları

Zemberek NLP servisini kullanmak için:
```powershell
# Zemberek JAR dosyasını indirin ve yerleştirin
# Konum: services/zemberek-nlp-server.jar
```

## Servis Detayları

### 1. Docker Servisleri

| Servis | Port | Durum Kontrolü |
|--------|------|----------------|
| Redis | 6379 | `redis-cli ping` |
| Elasticsearch | 9200 | `curl http://localhost:9200/_cluster/health` |
| PostgreSQL | 5432 | `psql -h localhost -U postgres` |
| Prometheus | 9090 | `curl http://localhost:9090/-/healthy` |

### 2. MCP Sunucuları

#### Dış Platform Entegrasyonları
- **youtube-education-api**: YouTube eğitim videoları
- **khan-academy-turkish**: Khan Academy Türkçe içerik
- **eba-tv-integration**: EBA TV entegrasyonu

#### Video Kalite Validasyonu
- **turkish-content-filter**: %70+ Türkçe içerik filtresi
- **subject-relevance-scorer**: Konu ilgisi skorlama
- **video-quality-validator**: Video kalite kontrolü
- **enhanced-recommendation-engine**: Öneri motoru
- **video-recommendation-monitoring**: İzleme servisi (port 9091)

#### Türkçe NLP ve AI
- **zemberek-nlp-service**: Türkçe NLP (port 8081)
- **hybrid-learning-style-detector**: Öğrenme stili tespiti
- **multi-agent-blackboard**: Agent koordinasyonu (port 8765)

#### İzleme ve Sağlık
- **platform-health-audit**: Platform sağlık denetimi
- **prometheus-metrics-exporter**: Metrik toplama (port 9091)
- **grafana-dashboard-provisioner**: Dashboard yönetimi
- **elasticsearch-apm**: APM izleme
- **sentry-error-tracking**: Hata izleme
- **database-backup-scheduler**: Veritabanı yedekleme
- **alerting-notification-service**: Alarm bildirimleri
- **log-aggregation-service**: Log toplama

## Sorun Giderme

### Docker Servisleri Başlamıyor

```powershell
# Docker servislerinin durumunu kontrol edin
docker-compose ps

# Logları inceleyin
docker-compose logs redis
docker-compose logs elasticsearch

# Yeniden başlatın
docker-compose restart redis elasticsearch
```

### MCP Sunucuları Başlamıyor

```powershell
# Logları kontrol edin
Get-Content logs\zemberek-nlp.log.err
Get-Content logs\blackboard-coordinator.log.err

# PID dosyalarını temizleyin
Remove-Item .mcp_pids\*.pid -Force

# Tekrar başlatın
.\scripts\start_mcp_services.ps1
```

### Port Zaten Kullanımda

```powershell
# Windows'ta port kullanımını kontrol edin
netstat -ano | findstr :8081
netstat -ano | findstr :8765

# Process'i sonlandırın (PID ile)
Stop-Process -Id <PID> -Force
```

### Python Modülleri Bulunamıyor

```powershell
# PYTHONPATH ayarlayın
$env:PYTHONPATH = "C:\Users\husey\kiro2"

# Veya backend dizininden çalıştırın
cd backend
python -m services.turkish_content_filter
```

### Java OutOfMemoryError

```powershell
# Zemberek için daha fazla heap ayırın
# .env.mcp dosyasında:
JAVA_OPTS=-Xmx4G -Xms1G
```

### Elasticsearch Yellow/Red Status

```powershell
# Cluster durumunu kontrol edin
curl http://localhost:9200/_cluster/health?pretty

# Index durumunu kontrol edin
curl http://localhost:9200/_cat/indices?v

# Replica sayısını azaltın (development için)
curl -X PUT "localhost:9200/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "number_of_replicas": 0
  }
}
'
```

## Performans Optimizasyonu

### Redis Cache

```powershell
# Redis memory kullanımını kontrol edin
docker exec turkiye_sinav_redis redis-cli INFO memory

# Cache temizleme
docker exec turkiye_sinav_redis redis-cli FLUSHDB
```

### Elasticsearch

```powershell
# Heap size artırın (docker-compose.yml)
# ES_JAVA_OPTS=-Xms1g -Xmx1g
```

### Database Connection Pool

`.env.mcp` dosyasında:
```
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
```

## Güvenlik

### API Anahtarları

⚠️ **UYARI**: Asla API anahtarlarını commit etmeyin!

```powershell
# Güçlü secret üretme
python -c "import secrets; print(secrets.token_urlsafe(32))"

# .env.mcp dosyasına ekleyin
YOUTUBE_API_KEY=your_actual_key_here
GRAFANA_API_KEY=your_actual_key_here
```

### Logların Güvenliği

```powershell
# Hassas bilgileri loglardan çıkarın
# logs/ dizinini .gitignore'a ekleyin (zaten ekli)
```

## Monitoring

### Prometheus Metrikleri

```powershell
# Metrik endpoint'i
curl http://localhost:9091/metrics

# Prometheus UI
Start-Process http://localhost:9090
```

### Grafana Dashboards

```powershell
# Grafana UI
Start-Process http://localhost:3001

# Varsayılan login: admin / changeme_grafana_password
```

### Health Reports

```powershell
# Latest health raporu
Get-Content reports\health\latest.json | ConvertFrom-Json

# Belirli bir zaman dilimi
Get-ChildItem reports\health\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

## Otomatik Başlatma (İsteğe Bağlı)

Windows başlangıcında otomatik başlatma için Task Scheduler kullanın:

```powershell
# Task Scheduler açın
taskschd.msc

# Yeni görev oluşturun:
# - Trigger: At startup
# - Action: PowerShell.exe -File "C:\Users\husey\kiro2\scripts\start_mcp_services.ps1"
# - Run with highest privileges: ✅
```

## İletişim ve Destek

- **MASTER_SPEC**: `.kiro/specs/MASTER_SPEC/requirements.md`
- **Agent Steering**: `.claude/agents/master-spec-agent-steering.md`
- **MCP README**: `.kiro/settings/MCP_SERVER_README.md`
- **Platform Health**: Slack #platform-health

## Versiyon Geçmişi

- **v1.0** (2025-10-18): İlk sürüm
  - 19 MCP sunucu konfigürasyonu
  - Docker entegrasyonu
  - Health check sistemi
  - Otomatik başlatma scriptleri
