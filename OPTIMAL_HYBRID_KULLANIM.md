# 🚀 Optimal Hybrid System Kullanım Kılavuzu

## Genel Bakış

Optimal Hybrid System, **Gemini 3 Pro** ve **Claude Sonnet 4.5** modellerini akıllıca birleştirerek:
- ✅ Maliyeti optimize eder
- ✅ Yanıt süresini azaltır  
- ✅ En uygun modeli otomatik seçer
- ✅ 3 katmanlı cache ile performansı artırır

## Kurulum

### 1. Gerekli Paketleri Kur

```bash
py -m pip install anthropic google-generativeai structlog redis
```

### 2. API Key'leri Ayarla

`.env` dosyasına ekle:

```env
# Google Gemini
GOOGLE_API_KEY=AIzaSy...

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...
```

**API Key Alma:**
- Gemini: https://makersuite.google.com/app/apikey
- Claude: https://console.anthropic.com/

## Temel Kullanım

### Basit Örnek

```python
import asyncio
from backend.optimal_hybrid_system import OptimalHybridSystem

async def main():
    # Sistemi başlat
    system = OptimalHybridSystem()
    
    # Soru sor
    result = await system.process_query(
        query="Python'da liste comprehension nasıl kullanılır?"
    )
    
    print(f"Cevap: {result['response']}")
    print(f"Model: {result['model']}")
    print(f"Süre: {result['duration']:.2f}s")
    print(f"Maliyet: ${result['cost']:.4f}")

asyncio.run(main())
```

### Bağlam ile Kullanım

```python
result = await system.process_query(
    query="Bu kodu optimize et",
    context={
        "file_content": "def slow_function(): ...",
        "language": "python",
        "performance_issue": "Çok yavaş çalışıyor"
    }
)
```

### Cache Kontrolü

```python
# Cache kullan (varsayılan)
result = await system.process_query(query="...", use_cache=True)

# Cache kullanma (her zaman yeni yanıt)
result = await system.process_query(query="...", use_cache=False)
```

## Model Seçimi (Otomatik)

Sistem karmaşıklığa göre otomatik model seçer:

| Karmaşıklık | Model | Kullanım |
|-------------|-------|----------|
| 0-3 | Claude Only | Basit sorular, hızlı yanıtlar |
| 4-6 | Gemini Assist | Kod analizi, orta seviye |
| 7-10 | Gemini Thinking | Mimari tasarım, detaylı analiz |

### Karmaşıklık Faktörleri

- Token sayısı (50+ kelime = +1, 100+ = +2)
- Kod içeriyor mu? (+2)
- Analiz gerektiriyor mu? (+3)
- Adım adım açıklama? (+2)
- Dosya analizi? (+2)

## Redis ile Cache (Opsiyonel)

```python
import redis.asyncio as redis

async def main():
    # Redis bağlantısı
    redis_client = await redis.from_url("redis://localhost:6379")
    
    # Sistem başlat
    system = OptimalHybridSystem(redis_client=redis_client)
    
    # Kullan
    result = await system.process_query("...")
```

**Cache Katmanları:**
- L1: Memory (100 item, anında)
- L2: Redis Hot (1 saat, ~1ms)
- L3: Redis Cold (24 saat, ~2ms)

## Routing Bilgisi

```python
from backend.optimal_hybrid_system import SmartRouter

router = SmartRouter()

# Hangi model kullanılacak?
info = router.get_routing_info(
    query="Mikroservis mimarisi tasarla",
    context={"file_content": "..."}
)

print(f"Karmaşıklık: {info['complexity']}/10")
print(f"Model: {info['model_type']}")
print(f"Tahmini Süre: {info['estimated_time']}s")
print(f"Tahmini Maliyet: ${info['estimated_cost']}")
```

## Metrik Takibi

```python
# Sistem metrikleri
metrics = system.get_metrics()

print(f"Toplam İstek: {metrics['total_requests']}")
print(f"Ortalama Süre: {metrics['avg_time']:.2f}s")
print(f"Ortalama Maliyet: ${metrics['avg_cost']:.4f}")
print(f"Cache Hit Rate: {metrics['cache_hit_rate']['total']:.1%}")
```

## Test

```bash
# Sistemi test et
py test_optimal_hybrid.py
```

**Not:** Test çalıştırmadan önce `.env` dosyasında `ANTHROPIC_API_KEY` değerini gerçek API key ile değiştirin.

## Hata Yönetimi

Sistem otomatik fallback yapar:
1. İlk model başarısız olursa → Claude'a düşer
2. Her iki model de başarısız → Hata mesajı döner

```python
try:
    result = await system.process_query("...")
except ValueError as e:
    print(f"API key eksik: {e}")
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
```

## Maliyet Optimizasyonu

### Öneriler

1. **Cache kullan**: Tekrarlayan sorularda %100 tasarruf
2. **Basit sorular için Claude**: Gemini'den 2x ucuz
3. **Token optimizasyonu**: Gereksiz metni temizle

### Örnek Maliyetler

| Model | Maliyet/İstek | Süre |
|-------|---------------|------|
| Claude Only | $0.003 | ~1.5s |
| Gemini Assist | $0.005 | ~5s |
| Gemini Thinking | $0.008 | ~15s |

## Production Kullanımı

### FastAPI Entegrasyonu

```python
from fastapi import FastAPI
from backend.optimal_hybrid_system import OptimalHybridSystem

app = FastAPI()
system = OptimalHybridSystem()

@app.post("/api/v1/ai/query")
async def ai_query(query: str, context: dict = None):
    result = await system.process_query(query, context)
    return {
        "response": result["response"],
        "model": result["model"],
        "duration": result["duration"],
        "cached": result["cached"]
    }
```

### Monitoring

```python
# Her 100 istekte bir metrik logla
if system.request_count % 100 == 0:
    metrics = system.get_metrics()
    logger.info("system_metrics", **metrics)
```

## Sorun Giderme

### API Key Hataları

```
❌ GOOGLE_API_KEY bulunamadı
```
→ `.env` dosyasına `GOOGLE_API_KEY` ekle

```
❌ ANTHROPIC_API_KEY bulunamadı
```
→ `.env` dosyasına `ANTHROPIC_API_KEY` ekle

### Model Hataları

```
❌ Gemini model yüklenemedi
```
→ API key'i kontrol et, quota'yı kontrol et

### Cache Hataları

```
❌ Redis bağlantı hatası
```
→ Redis çalışıyor mu kontrol et: `redis-cli ping`

## İleri Seviye

### Custom Complexity Analyzer

```python
from backend.optimal_hybrid_system import SmartRouter

class CustomRouter(SmartRouter):
    def analyze_complexity(self, query: str, context: dict = None) -> int:
        score = super().analyze_complexity(query, context)
        
        # Özel kurallar ekle
        if "acil" in query.lower():
            score = min(score, 3)  # Hızlı yanıt için Claude
        
        return score
```

### Custom Cache Strategy

```python
from backend.optimal_hybrid_system import MultiLayerCache

class CustomCache(MultiLayerCache):
    async def set(self, prompt: str, model: str, value: str, ttl: int = 3600):
        # Önemli sorular için daha uzun TTL
        if "önemli" in prompt.lower():
            ttl = 86400  # 24 saat
        
        await super().set(prompt, model, value, ttl)
```

## Destek

Sorularınız için:
- GitHub Issues: [proje-repo]/issues
- Dokümantasyon: `docs/`
- Örnekler: `test_optimal_hybrid.py`
