# MCP Server Configuration Guide
## Model Context Protocol - External Service Integration

**Version**: 1.0
**Last Updated**: 18 Ekim 2025
**Based on**: MASTER_SPEC v1.0 (REQ-1 to REQ-47)

---

## 📋 İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Sunucu Listesi](#sunucu-listesi)
3. [Kurulum ve Başlatma](#kurulum-ve-başlatma)
4. [Performans Hedefleri](#performans-hedefleri)
5. [Güvenlik ve Uyumluluk](#güvenlik-ve-uyumluluk)
6. [Sorun Giderme](#sorun-giderme)

---

## Genel Bakış

MCP Server konfigürasyonu, MASTER_SPEC gereksinimlerine göre düzenlenmiş 13 dış servis entegrasyonunu yönetir. Bu sunucular şu alanlarda kritik işlevleri yerine getirir:

### Ana Kategoriler

1. **Dış Platform Entegrasyonları** (REQ-5)
   - YouTube Education API
   - Khan Academy Türkçe
   - EBA TV Integration

2. **Video Kalite Validasyonu** (REQ-21-25)
   - Turkish Content Filter
   - Subject Relevance Scorer
   - Video Quality Validator
   - Enhanced Recommendation Engine
   - Video Recommendation Monitoring

3. **Türkçe NLP ve AI** (REQ-2, REQ-10, REQ-12)
   - Zemberek NLP Service
   - Hybrid Learning Style Detector
   - Multi-Agent Blackboard

4. **Platform Sağlığı** (REQ-26-47)
   - Platform Health Audit

---

## Sunucu Listesi

### 1. YouTube Education API

**Gereksinim**: REQ-5.1, REQ-21, REQ-22, REQ-23
**Komut**: `npx -y @modelcontextprotocol/server-youtube`
**Port**: N/A (API)

**Ortam Değişkenleri**:
```bash
YOUTUBE_API_KEY=your_api_key_here
YOUTUBE_CHANNEL_FILTER=education
YOUTUBE_LANGUAGE=tr
YOUTUBE_REGION=TR
```

**Validasyon Kuralları**:
- Minimum Türkçe skor: 70%
- Minimum konu ilgisi: 60%
- Video süresi: 5-60 dakika
- Erişilebilirlik kontrolü: Zorunlu

**Performans Hedefleri**:
- Yanıt süresi: < 2 saniye
- Batch validasyon: 10 video
- Maksimum eşzamanlı istek: 50

**Health Check**:
- Aralık: 60 saniye
- Timeout: 5 saniye
- Hata eşiği: 3 başarısız kontrol

---

### 2. Khan Academy Turkish

**Gereksinim**: REQ-5.2, REQ-3.1
**Komut**: `python -m backend.integrations.khan_academy_service`

**Ortam Değişkenleri**:
```bash
KHAN_ACADEMY_LOCALE=tr
KHAN_ACADEMY_CURRICULUM=meb_2024
```

**Performans Hedefleri**:
- Yanıt süresi: < 1 saniye
- Cache TTL: 1 saat

---

### 3. EBA TV Integration

**Gereksinim**: REQ-5.3, REQ-3.1
**Komut**: `python -m backend.integrations.ebatv_service`

**Ortam Değişkenleri**:
```bash
EBA_TV_API_URL=https://eba.gov.tr/api/v1
EBA_TV_CURRICULUM_LEVEL=lise
```

**Performans Hedefleri**:
- Yanıt süresi: < 1.5 saniye
- Cache TTL: 2 saat

---

### 4. Turkish Content Filter

**Gereksinim**: REQ-21.1, REQ-21.2, REQ-21.3, REQ-21.4
**Komut**: `python -m backend.services.turkish_content_filter`

**Ortam Değişkenleri**:
```bash
MIN_TURKISH_SCORE=0.70
TRUSTED_CHANNELS_FILE=config/trusted_turkish_channels.json
ZEMBEREK_SERVICE_URL=http://localhost:8081
```

**Performans Hedefleri**:
- Yanıt süresi: < 500ms per video
- Batch boyutu: 20 video
- Throughput: 40 video/saniye

**Validasyon Mantığı**:
1. Video başlık + açıklama Türkçe analizi
2. Güvenilir Türk eğitim kanalları listesi kontrolü
3. Dil tespiti doğruluğu
4. Minimum %70 Türkçe skor

---

### 5. Subject Relevance Scorer

**Gereksinim**: REQ-22.1, REQ-22.2, REQ-22.3
**Komut**: `python -m backend.services.subject_relevance_scorer`

**Ortam Değişkenleri**:
```bash
MIN_RELEVANCE_SCORE=0.60
MODULE_SPECIFIC_MIN_SCORE=0.80
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
ELASTICSEARCH_URL=http://localhost:9200
```

**Performans Hedefleri**:
- Yanıt süresi: < 300ms
- Embedding cache: Etkin
- Cache TTL: 24 saat

**Validasyon Mantığı**:
1. Embedding-tabanlı semantik benzerlik
2. Öğrenci profili ile konu eşleştirme
3. Modül-özel videolar için %80+ ilgi
4. Genel öneriler için %60+ ilgi

---

### 6. Video Quality Validator

**Gereksinim**: REQ-23, REQ-24, REQ-25
**Komut**: `python -m backend.services.video_quality_validator`

**Ortam Değişkenleri**:
```bash
YOUTUBE_API_KEY=your_api_key_here
CHANNEL_RELIABILITY_THRESHOLD=0.70
VIEW_COUNT_MIN=1000
LIKE_RATIO_MIN=0.80
```

**Performans Hedefleri**:
- Yanıt süresi: < 2 saniye
- Batch boyutu: 10 video
- Maksimum validasyon süresi: 5 saniye
- Fallback cache: Etkin

**Kalite Metrikleri**:
- Kanal güvenilirlik bonusu: +20%
- Altyazı desteği bonusu: +10%
- İdeal süre: 5-60 dakika
- Görüntülenme sayısı: Min 1000
- Beğeni oranı: Min %80

**Erişilebilirlik Kontrolleri**:
- YouTube API doğrulama
- Gömülebilir durum kontrolü
- Public/private/unlisted durum
- Kırık link tespiti

---

### 7. Enhanced Recommendation Engine

**Gereksinim**: REQ-4, REQ-10, REQ-21, REQ-22, REQ-23, REQ-24, REQ-25
**Komut**: `python -m backend.services.enhanced_resource_recommendation_engine`

**Bağımlılıklar**:
- turkish-content-filter
- subject-relevance-scorer
- video-quality-validator
- youtube-education-api

**Ortam Değişkenleri**:
```bash
REDIS_URL=redis://localhost:6379/0
RECOMMENDATION_CACHE_TTL=3600
MAX_RECOMMENDATIONS=50
```

**Performans Hedefleri**:
- Yanıt süresi: < 5 saniye
- Eşzamanlı validasyon: 10 video
- Cache hit rate: Min %80

**Entegrasyon Akışı**:
1. Öğrenci profili analizi (VARK+Felder, ZPD)
2. Konu ilgisi skorlama
3. Türkçe içerik filtreleme (>%70)
4. Video kalite validasyonu
5. Sıralama ve öneri (max 50 kaynak)

---

### 8. Video Recommendation Monitoring

**Gereksinim**: REQ-25.2, REQ-28, REQ-44
**Komut**: `python -m backend.services.video_recommendation_monitoring`

**Ortam Değişkenleri**:
```bash
PROMETHEUS_PORT=9090
ALERT_WEBHOOK_URL=your_webhook_url
LOG_LEVEL=INFO
```

**İzleme Metrikleri**:
- Turkish filter başarı oranı: Min %95
- Relevance scorer gecikme: Max 300ms
- Quality validator batch süresi: Max 5 saniye
- Recommendation yanıt süresi: Max 5 saniye
- API hata oranı: Max %5

**Alarm Koşulları**:
- Yanıt süresi aşımı: 1.5x hedef
- Hata oranı: > %5
- Health score: < 80
- Kanal: Slack, Email, Webhook

---

### 9. Zemberek NLP Service

**Gereksinim**: REQ-2.1, REQ-12.1, REQ-12.2
**Komut**: `java -jar services/zemberek-nlp-server.jar --port 8081`
**Port**: 8081

**Java Ayarları**:
```bash
JAVA_OPTS=-Xmx2G -Xms512M
ZEMBEREK_CACHE_ENABLED=true
```

**Performans Hedefleri**:
- Yanıt süresi: < 500ms
- Morfolojik analiz cache: 24 saat
- Maksimum eşzamanlı istek: 100

**Özellikler**:
- Morfolojik analiz
- Karmaşık kelime tespiti (ek sayısı + türetme derinliği)
- Osmanlıca/Akademik Türkçe tespiti
- Bölgesel lehçe tespiti

---

### 10. Hybrid Learning Style Detector

**Gereksinim**: REQ-10.1, REQ-10.2
**Komut**: `python -m backend.services.hybrid_learning_style_detector`

**Ortam Değişkenleri**:
```bash
VARK_FELDER_PROFILES=64
TURKISH_ZPD_ENABLED=true
MEB_MAARIF_CULTURAL_FACTORS=true
```

**Performans Hedefleri**:
- Yanıt süresi: < 3 saniye
- Minimum güven skoru: %70

**64 Profil Sistemi**:
- VARK boyutları: 4 (Visual, Auditory, Reading, Kinesthetic)
- Felder boyutları: 4 (Active/Reflective, Sensing/Intuitive, Visual/Verbal, Sequential/Global)
- Kombinasyon: 4 × 4 × 4 = 64 benzersiz profil

**Türk ZPD Uyarlamaları**:
- Grup öğrenme tercihi → ZPD genişletme
- Ramazan/sınav dönemi uyarlaması
- MEB Maarif kültürel faktörler

---

### 11. Multi-Agent Blackboard

**Gereksinim**: REQ-11.1, REQ-11.2, REQ-11.3, REQ-11.6
**Komut**: `python -m backend.agents.blackboard_coordinator`
**Port**: 8765 (WebSocket)

**Ortam Değişkenleri**:
```bash
WEBSOCKET_PORT=8765
REDIS_PUBSUB_URL=redis://localhost:6379/1
AUTO_RECONNECT_ENABLED=true
```

**Performans Hedefleri**:
- Broadcast gecikmesi: < 100ms
- Maksimum eşzamanlı agent: 50
- Mesaj kuyruğu boyutu: 10,000

**Agent Koordinasyon Kuralları**:
1. **Discovery Notification** (REQ-11.1): Yeni bilgi < 100ms broadcast
2. **Learning Style Sync** (REQ-11.2): Profil tespiti → Tüm agentler adapte
3. **Performance Data Sync** (REQ-11.3): Performans güncellemesi → Koordine yanıt
4. **Auto-Reconnect** (REQ-11.6): Bağlantı kopması → Otomatik yeniden bağlan

**Blackboard Topics**:
```python
# Agent yayını
blackboard.publish("learning_style_detected", {
    "student_id": "...",
    "profile": "Visual-Active-Sensing-Sequential",
    "confidence": 0.85
})

# Diğer agentler abone olur ve adapte olur
@blackboard.subscribe("learning_style_detected")
def adapt_to_learning_style(data):
    self.adjust_content_difficulty(data["profile"])
    self.personalize_recommendations(data["profile"])
```

---

### 12. Platform Health Audit

**Gereksinim**: REQ-26 to REQ-47 (47 gereksinim)
**Komut**: `python -m backend.analytics.health_audit_service`

**Ortam Değişkenleri**:
```bash
HEALTH_CHECK_INTERVAL_SECONDS=300
ALERT_THRESHOLD_SCORE=80
REPORT_OUTPUT_DIR=reports/health
```

**Performans Hedefleri**:
- Tam denetim süresi: < 60 saniye
- Kritik denetim süresi: < 120 saniye
- Rapor oluşturma süresi: < 10 saniye

**47 Otomatik Kontrol**:
- **Güvenlik**: Authentication, KVKK, encryption, input validation
- **Performans**: API response time, concurrent users, cache hit rate
- **Veritabanı**: Connection pool, query performance, replication
- **API**: Endpoint availability, error rates, rate limiting
- **Servisler**: External integrations, service health, dependency check
- **Altyapı**: Server resources, network latency, storage

**Çıktı Formatları**:
- HTML raporu (Türkçe)
- JSON raporu
- Markdown raporu

**Alarm Koşulu**:
- Health score < 80% → Otomatik alarm

---

## Kurulum ve Başlatma

### Ön Gereksinimler

```bash
# Python bağımlılıkları
pip install -r backend/requirements.txt

# Node.js bağımlılıkları (YouTube API için)
npm install -g @modelcontextprotocol/server-youtube

# Java (Zemberek için)
# Java 11+ gerekli

# Gerekli servisler
docker-compose up -d postgresql redis elasticsearch
```

### Ortam Değişkenleri Ayarlama

`.env` dosyası oluşturun:

```bash
# API Keys
YOUTUBE_API_KEY=your_youtube_api_key_here
ALERT_WEBHOOK_URL=your_slack_webhook_url_here

# Service URLs
ZEMBEREK_SERVICE_URL=http://localhost:8081
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200

# Performance Settings
HEALTH_CHECK_INTERVAL_SECONDS=300
RECOMMENDATION_CACHE_TTL=3600

# Validation Thresholds
MIN_TURKISH_SCORE=0.70
MIN_RELEVANCE_SCORE=0.60
CHANNEL_RELIABILITY_THRESHOLD=0.70
```

### Başlatma Sırası

MCP sunucuları şu sırayla başlatılmalıdır (`service_dependencies.startup_order`):

```bash
# 1. Temel NLP servisi
java -jar services/zemberek-nlp-server.jar --port 8081 &

# 2. Multi-agent koordinatör
python -m backend.agents.blackboard_coordinator &

# 3. Video kalite validatörleri
python -m backend.services.turkish_content_filter &
python -m backend.services.subject_relevance_scorer &
python -m backend.services.video_quality_validator &

# 4. Öneri motoru (bağımlılıkları bekler)
python -m backend.services.enhanced_resource_recommendation_engine &

# 5. İzleme servisi
python -m backend.services.video_recommendation_monitoring &

# 6. Öğrenme stili tespiti
python -m backend.services.hybrid_learning_style_detector &

# 7. Platform sağlık denetimi
python -m backend.analytics.health_audit_service &
```

### Health Check Doğrulama

Tüm servislerin sağlıklı çalıştığını doğrulayın:

```bash
# Her servis için health endpoint kontrolü
curl http://localhost:8081/health  # Zemberek
curl http://localhost:8765/health  # Blackboard
curl http://localhost:9090/health  # Monitoring

# MCP server durumlarını kontrol et
python scripts/check_mcp_health.py
```

---

## Performans Hedefleri

### API Yanıt Süreleri (REQ-7)

| Metrik | Hedef | Kritik |
|--------|-------|--------|
| API Response (p95) | < 200ms | < 500ms |
| Agent Response | < 3000ms | < 5000ms |
| Turkish NLP Analysis | < 500ms | < 1000ms |
| Video Validation (batch) | < 5s | < 10s |
| Health Audit (full) | < 60s | < 120s |
| Concurrent Users | 100K+ | N/A |

### Video Kalite Validasyon (REQ-25)

- **Turkish Filter**: < 500ms per video
- **Relevance Scorer**: < 300ms per video
- **Quality Validator**: < 2s per batch (10 videos)
- **Total Recommendation**: < 5s (end-to-end)

### Cache Hit Rate

- **YouTube metadata**: Min %80
- **Turkish content scores**: Min %85
- **Subject relevance embeddings**: Min %80
- **Learning style profiles**: Min %70

---

## Güvenlik ve Uyumluluk

### Authentication (REQ-48)

Tüm MCP sunucuları JWT doğrulama gerektirir:

```python
# Her istek header'ında
Authorization: Bearer <jwt_token>
```

### Rate Limiting (REQ-51)

```json
{
  "max_requests_per_minute": 100,
  "burst_allowance": 20
}
```

### KVKK Compliance (REQ-48)

```json
{
  "personal_data_logging": false,
  "consent_required": true,
  "data_retention_days": 730
}
```

### Input Validation (REQ-45)

- SQL injection koruması: Etkin
- XSS koruması: Etkin
- Maksimum istek boyutu: 10MB

---

## Sorun Giderme

### Yaygın Hatalar

**1. YouTube API Quota Aşımı**

```bash
Error: quota_exceeded

Çözüm:
- Fallback cache kullan
- API key rotation uygula
- Request batching optimize et
```

**2. Zemberek NLP Timeout**

```bash
Error: connection_timeout

Çözüm:
- Zemberek servisinin çalıştığını kontrol et: curl http://localhost:8081/health
- Java heap size artır: -Xmx4G
- Cache etkinleştir: ZEMBEREK_CACHE_ENABLED=true
```

**3. Low Turkish Content Score**

```bash
Warning: turkish_score=0.45 (threshold=0.70)

Çözüm:
- Trusted channels listesini güncelle
- Video başlık/açıklama analizi kontrol et
- Manuel review gerekebilir
```

**4. Recommendation Engine Slow**

```bash
Error: recommendation_timeout (>5s)

Çözüm:
- Redis cache durumunu kontrol et
- Concurrent validation sayısını azalt
- Batch size optimize et (10 → 5)
```

### Log İnceleme

```bash
# MCP sunucu logları
tail -f logs/mcp-*.log

# Performans metrikleri
curl http://localhost:9091/metrics | grep recommendation

# Health audit raporu
cat reports/health/latest.json | jq '.health_score'
```

### Destek

- **MASTER_SPEC**: `.kiro/specs/MASTER_SPEC/requirements.md`
- **Agent Steering**: `.claude/agents/master-spec-agent-steering.md`
- **Hooks**: `.kiro/hooks/`
- **İletişim**: Platform sağlık denetimi alarmları → Slack #platform-health

---

**Son Güncelleme**: 18 Ekim 2025
**Versiyon**: 1.0
**Uyumluluk**: MASTER_SPEC v1.0 (47 gereksinim, 200+ kabul kriteri)
