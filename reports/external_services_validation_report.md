# External Services Integration Validation Report
**Tarih:** 19 Ekim 2025  
**Proje:** Türkiye Üniversite Sınavları Hazırlık Platformu

---

## 📊 Executive Summary

| Servis | Durum | Response Time | Not |
|--------|-------|---------------|-----|
| **YouTube API** | ⚠️ Not Configured | - | API key gerekli |
| **Khan Academy API** | ⚠️ Status 410 | 910ms | Endpoint deprecated |
| **EBA TV** | ✅ Accessible | 654ms | Çalışıyor |
| **OpenAI API** | ⚠️ Not Configured | - | API key gerekli |
| **Zemberek NLP** | ❌ Not Running | - | Local servis çalışmıyor |
| **Wikipedia API** | ⚠️ Status 403 | - | Rate limit veya blocked |

**Sağlık Skoru:** 16.67% (1/6 servis çalışıyor)  
**Durum:** ❌ CRITICAL - Çoğu servis yapılandırılmamış veya çalışmıyor

---

## 🔍 Detaylı Analiz

### 1. YouTube Data API v3

**Durum:** ⚠️ Not Configured  
**Öncelik:** P0 - Critical

**Sorun:**
- `YOUTUBE_API_KEY` environment variable tanımlı değil
- API bağlantısı test edilemedi

**Kullanım Alanları:**
- Eğitim videoları arama
- Video metadata çekme
- Playlist yönetimi
- Video önerileri

**Çözüm:**
```bash
# .env dosyasına ekle
YOUTUBE_API_KEY=your_youtube_api_key_here

# API key almak için:
# 1. Google Cloud Console'a git
# 2. Yeni proje oluştur
# 3. YouTube Data API v3'ü etkinleştir
# 4. Credentials oluştur (API Key)
```

**Test Komutu:**
```python
import requests

api_key = "YOUR_API_KEY"
url = "https://www.googleapis.com/youtube/v3/search"
params = {
    "part": "snippet",
    "q": "matematik dersi",
    "type": "video",
    "maxResults": 10,
    "key": api_key
}

response = requests.get(url, params=params)
print(response.json())
```

**Quota Limitleri:**
- Günlük 10,000 units (free tier)
- Search query: 100 units
- Video details: 1 unit

**Öneriler:**
1. API key'i güvenli şekilde sakla (.env, secrets manager)
2. Quota monitoring ekle
3. Caching stratejisi uygula
4. Rate limiting ekle

---

### 2. Khan Academy API

**Durum:** ⚠️ Status 410 (Gone)  
**Response Time:** 910ms  
**Öncelik:** P1 - High

**Sorun:**
- API endpoint deprecated (410 Gone)
- Topic tree endpoint artık kullanılmıyor

**Kullanım Alanları:**
- Türkçe eğitim içerikleri
- Konu ağacı (topic tree)
- Alıştırma soruları
- Video içerikler

**Çözüm:**
```python
# Eski endpoint (çalışmıyor)
url = "https://www.khanacademy.org/api/v1/topictree"

# Yeni yaklaşım:
# 1. Khan Academy'nin yeni API dokümantasyonunu kontrol et
# 2. OAuth 2.0 authentication kullan
# 3. Alternatif olarak web scraping düşün (ToS'a uygun şekilde)
```

**Alternatif Çözümler:**
1. **Khan Academy Lite API:** Offline content için
2. **Direct Content Links:** Video ve exercise link'leri
3. **RSS Feeds:** Yeni içerik bildirimleri için

**Öneriler:**
1. Khan Academy ile iletişime geç (API access için)
2. Alternatif Türkçe eğitim platformları araştır
3. Content caching stratejisi uygula

---

### 3. EBA TV (MEB)

**Durum:** ✅ Accessible  
**Response Time:** 654ms  
**Öncelik:** P0 - Critical (Çalışıyor ama API yok)

**Başarılı Test:**
- EBA TV ana sayfası erişilebilir
- Response time kabul edilebilir seviyede

**Sorun:**
- EBA TV'nin public API'si yok
- Sadece web interface mevcut

**Kullanım Alanları:**
- MEB onaylı eğitim videoları
- Sınıf seviyesine göre içerik
- Müfredata uygun materyaller

**Mevcut Durum:**
```python
# Sadece web sayfası kontrolü yapılabiliyor
url = "https://www.eba.gov.tr"
response = requests.get(url)
# Status: 200 OK
```

**Çözüm Önerileri:**

**Seçenek 1: MEB ile İletişim**
- Resmi API erişimi talep et
- Eğitim kurumu olarak başvur
- API dokümantasyonu iste

**Seçenek 2: Web Scraping (Dikkatli)**
- robots.txt'i kontrol et
- Rate limiting uygula
- User-Agent belirt
- Yasal uygunluğu kontrol et

**Seçenek 3: Manuel Content Curation**
- EBA TV video link'lerini manuel topla
- Database'de sakla
- Periyodik olarak güncelle

**Örnek Implementation:**
```python
# EBA TV video embed
eba_video_url = "https://www.eba.gov.tr/video/12345"

# Frontend'de göster
<iframe src={eba_video_url} />
```

**Öneriler:**
1. MEB ile resmi API için görüşme başlat
2. Mevcut video link'lerini database'de sakla
3. Content update stratejisi belirle

---

### 4. OpenAI API (GPT-4)

**Durum:** ⚠️ Not Configured  
**Öncelik:** P0 - Critical

**Sorun:**
- `OPENAI_API_KEY` environment variable tanımlı değil
- API bağlantısı test edilemedi

**Kullanım Alanları:**
- AI Chat Assistant
- Soru üretimi
- Çözüm açıklamaları
- Kişiselleştirilmiş öğrenme yolları
- Türkçe dil işleme

**Çözüm:**
```bash
# .env dosyasına ekle
OPENAI_API_KEY=sk-your_openai_api_key_here

# API key almak için:
# 1. https://platform.openai.com/ adresine git
# 2. Hesap oluştur
# 3. API Keys bölümünden yeni key oluştur
# 4. Billing bilgilerini ekle
```

**Test Komutu:**
```python
import openai

openai.api_key = "YOUR_API_KEY"

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Matematik sorusu oluştur"}
    ]
)

print(response.choices[0].message.content)
```

**Maliyet Optimizasyonu:**
- GPT-4: $0.03/1K tokens (input), $0.06/1K tokens (output)
- GPT-3.5-turbo: $0.0015/1K tokens (input), $0.002/1K tokens (output)
- Caching stratejisi uygula
- Token usage monitoring ekle

**Öneriler:**
1. API key'i güvenli şekilde sakla
2. Rate limiting ve retry logic ekle
3. Token usage tracking
4. Cost monitoring dashboard
5. Fallback stratejisi (GPT-3.5 turbo)

---

### 5. Zemberek NLP

**Durum:** ❌ Not Running  
**Öncelik:** P1 - High

**Sorun:**
- Local Zemberek NLP servisi çalışmıyor
- `http://localhost:8080` erişilemiyor

**Kullanım Alanları:**
- Türkçe dil işleme
- Kelime analizi
- Yazım denetimi
- Morfolojik analiz
- Cümle ayrıştırma

**Çözüm:**

**Seçenek 1: Docker ile Çalıştır**
```bash
# Zemberek Docker image
docker pull ahmetaa/zemberek-nlp-server

# Container başlat
docker run -d -p 8080:8080 ahmetaa/zemberek-nlp-server

# Test et
curl http://localhost:8080/health
```

**Seçenek 2: Java ile Çalıştır**
```bash
# Zemberek JAR indir
wget https://github.com/ahmetaa/zemberek-nlp/releases/download/v0.17.1/zemberek-full.jar

# Servisi başlat
java -jar zemberek-full.jar --server --port 8080
```

**Seçenek 3: Python Library Kullan**
```python
# zemberek-python wrapper
pip install zemberek-python

from zemberek import TurkishMorphology

morphology = TurkishMorphology.create_with_defaults()
analysis = morphology.analyze("kitaplar")
```

**API Endpoints:**
```
GET  /health                    # Health check
POST /tokenize                  # Tokenization
POST /morphology/analyze        # Morphological analysis
POST /morphology/stem           # Stemming
POST /normalization/normalize   # Text normalization
```

**Öneriler:**
1. Docker compose'a ekle
2. Health check monitoring
3. Fallback stratejisi (OpenAI için)
4. Performance testing

---

### 6. Wikipedia API

**Durum:** ⚠️ Status 403 (Forbidden)  
**Öncelik:** P2 - Medium

**Sorun:**
- Wikipedia API 403 hatası veriyor
- Muhtemelen rate limit veya User-Agent eksikliği

**Kullanım Alanları:**
- Konu açıklamaları
- Ek bilgi kaynakları
- Referans materyaller

**Çözüm:**
```python
import requests

url = "https://tr.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "format": "json",
    "list": "search",
    "srsearch": "matematik",
    "srlimit": 10
}

headers = {
    "User-Agent": "TurkiyeSinavApp/1.0 (contact@example.com)"
}

response = requests.get(url, params=params, headers=headers)
```

**Wikipedia API Best Practices:**
1. User-Agent header ekle (zorunlu)
2. Rate limiting uygula (max 200 req/sec)
3. Caching kullan
4. API etiquette'e uy

**Öneriler:**
1. User-Agent header ekle
2. Request throttling
3. Content caching (24 saat)
4. Alternatif: Wikidata API

---

## 🚨 Kritik Sorunlar

### 1. API Key'leri Eksik (CRITICAL)
**Etkilenen Servisler:** YouTube, OpenAI  
**Öncelik:** P0

**Çözüm:**
```bash
# .env dosyası oluştur
cat > .env << EOF
YOUTUBE_API_KEY=your_youtube_key
OPENAI_API_KEY=your_openai_key
ZEMBEREK_URL=http://localhost:8080
EOF

# .env.example güncelle
cat > .env.example << EOF
YOUTUBE_API_KEY=
OPENAI_API_KEY=
ZEMBEREK_URL=http://localhost:8080
EOF
```

### 2. Zemberek NLP Servisi Çalışmıyor (HIGH)
**Etki:** Türkçe NLP özellikleri kullanılamıyor  
**Öncelik:** P1

**Çözüm:**
```yaml
# docker-compose.yml'e ekle
services:
  zemberek:
    image: ahmetaa/zemberek-nlp-server
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3. Khan Academy API Deprecated (HIGH)
**Etki:** Khan Academy entegrasyonu çalışmıyor  
**Öncelik:** P1

**Çözüm:**
1. Khan Academy ile iletişime geç
2. Alternatif API araştır
3. Direct content linking kullan

---

## ✅ Öneriler

### Kısa Vadeli (1-2 Gün)

1. **API Key'leri Yapılandır**
   - YouTube API key al ve .env'e ekle
   - OpenAI API key al ve .env'e ekle
   - Test et

2. **Zemberek NLP'yi Başlat**
   - Docker ile çalıştır
   - Health check ekle
   - Test et

3. **Wikipedia API'yi Düzelt**
   - User-Agent header ekle
   - Rate limiting uygula
   - Test et

### Orta Vadeli (1 Hafta)

1. **Khan Academy Alternatifi**
   - Yeni API araştır
   - Direct content linking implement et
   - Test et

2. **EBA TV Entegrasyonu**
   - MEB ile görüşme başlat
   - Manuel content curation
   - Database'e ekle

3. **Monitoring ve Alerting**
   - Service health checks
   - API quota monitoring
   - Error alerting

### Uzun Vadeli (1 Ay)

1. **API Gateway**
   - Merkezi API gateway kur
   - Rate limiting
   - Caching
   - Monitoring

2. **Fallback Stratejileri**
   - Her servis için fallback
   - Graceful degradation
   - User notification

3. **Cost Optimization**
   - API usage analytics
   - Caching stratejisi
   - Quota management

---

## 📋 Action Items

| # | Task | Priority | Deadline | Owner |
|---|------|----------|----------|-------|
| 1 | YouTube API key al ve yapılandır | P0 | Bugün | DevOps |
| 2 | OpenAI API key al ve yapılandır | P0 | Bugün | DevOps |
| 3 | Zemberek NLP Docker'da başlat | P1 | 2 gün | Backend Team |
| 4 | Wikipedia API User-Agent ekle | P2 | 3 gün | Backend Team |
| 5 | Khan Academy alternatifi araştır | P1 | 1 hafta | Backend Team |
| 6 | EBA TV için MEB ile görüşme | P1 | 1 hafta | Product Team |
| 7 | Service monitoring dashboard | P2 | 2 hafta | DevOps |
| 8 | API cost tracking | P2 | 2 hafta | DevOps |

---

## 📎 Ekler

### A. Validation Script
Script: `scripts/validate_external_services.py`  
Kullanım: `python scripts/validate_external_services.py`

### B. JSON Report
Detaylı JSON rapor: `external_services_validation_report.json`

### C. API Documentation Links
- YouTube: https://developers.google.com/youtube/v3
- OpenAI: https://platform.openai.com/docs
- Wikipedia: https://www.mediawiki.org/wiki/API:Main_page
- Zemberek: https://github.com/ahmetaa/zemberek-nlp

### D. Environment Variables Template
```bash
# .env.example
YOUTUBE_API_KEY=
OPENAI_API_KEY=
ZEMBEREK_URL=http://localhost:8080
KHAN_ACADEMY_CLIENT_ID=
KHAN_ACADEMY_CLIENT_SECRET=
```

---

**Rapor Oluşturan:** External Services Validator v1.0  
**Sonraki İnceleme:** API key'ler yapılandırıldıktan sonra (ASAP)

**Genel Değerlendirme:** ❌ CRITICAL - Çoğu external servis yapılandırılmamış. Acil aksiyon gerekli.
