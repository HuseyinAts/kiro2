# 🚀 Optimal Hybrid System Kullanım Kılavuzu

## Hızlı Başlangıç

### 1. API Anahtarlarını Ayarla

`.env` dosyasına API anahtarlarınızı ekleyin:

```bash
# Google Gemini API
GOOGLE_API_KEY=AIzaSy...  # Zaten var ✅

# Anthropic Claude API (opsiyonel ama önerilen)
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Gerekli Paketleri Yükle

```bash
pip install anthropic google-generativeai structlog
```

### 3. Sistemi Başlat

**Claude Code (Kiro) içinde:**

```bash
python start_hybrid_system.py
```

## Kullanım Modları

### 🎬 Demo Modu
Otomatik olarak 3 farklı karmaşıklık seviyesinde test soruları çalıştırır:
- Basit soru → Claude Only
- Orta seviye → Gemini Assist  
- Karmaşık analiz → Gemini Thinking

```bash
python start_hybrid_system.py
# Seçim: 1
```

### 💬 İnteraktif Mod
Kendi sorularınızı sorun:

```bash
python start_hybrid_system.py
# Seçim: 2
```

**Komutlar:**
- Soru yazın ve Enter'a basın
- `metrics` → İstatistikleri görüntüle
- `exit` veya `quit` → Çık

## Programatik Kullanım

### Basit Örnek

```python
import asyncio
from backend.optimal_hybrid_system import OptimalHybridSystem

async def main():
    # Sistemi başlat
    system = OptimalHybridSystem()
    
    # Soru sor
    result = await system.process_query(
        query="Python'da async/await nasıl çalışır?",
        use_cache=True
    )
    
    print(f"Model: {result['model']}")
    print(f"Yanıt: {result['response']}")
    print(f"Süre: {result['duration']:.2f}s")
    print(f"Maliyet: ${result['cost']:.4f}")

asyncio.run(main())
```

### Context ile Kullanım

```python
result = await system.process_query(
    query="Bu kodu optimize et",
    context={
        "file_content": "def slow_function(): ...",
        "language": "python"
    },
    use_cache=True
)
```

### Routing Bilgisi Alma

```python
from backend.optimal_hybrid_system import SmartRouter

router = SmartRouter()
info = router.get_routing_info(
    query="Mikroservis mimarisi tasarla",
    context={"project_type": "e-commerce"}
)

print(f"Model: {info['model_type']}")
print(f"Karmaşıklık: {info['complexity']}/10")
print(f"Tahmini süre: {info['estimated_time']}s")
print(f"Tahmini maliyet: ${info['estimated_cost']}")
```

### Metrikleri İzleme

```python
# Sistem metrikleri
metrics = system.get_metrics()

print(f"Toplam istek: {metrics['total_requests']}")
print(f"Toplam maliyet: ${metrics['total_cost']:.4f}")
print(f"Ortalama süre: {metrics['avg_time']:.2f}s")
print(f"Cache hit rate: {metrics['cache_hit_rate']['total']:.1%}")
```

## Akıllı Routing Nasıl Çalışır?

Sistem sorguları otomatik olarak analiz eder ve en uygun modeli seçer:

### 🟢 Basit (0-3 puan) → Claude Only
- Kısa sorular
- Tanım soruları
- Basit açıklamalar
- **Avantaj:** Hızlı ve ucuz

### 🟡 Orta (4-6 puan) → Gemini Assist
- Kod analizi
- Orta seviye açıklamalar
- Basit optimizasyonlar
- **Avantaj:** Dengeli performans

### 🔴 Karmaşık (7-10 puan) → Gemini Thinking
- Mimari tasarım
- Detaylı analiz
- Adım adım çözüm
- **Avantaj:** En kaliteli yanıt

## Karmaşıklık Puanlama

Sistem şu kriterlere göre puan verir:

- **Token sayısı:** >100 token → +2 puan
- **Kod içeriyor:** ``` veya def/class → +2 puan
- **Analiz gerektiriyor:** "analiz", "incele", "optimize" → +3 puan
- **Thinking gerektiriyor:** "adım adım", "detaylı", "açıkla" → +2 puan
- **Dosya analizi:** Context'te file_content → +2 puan

## 3 Katmanlı Cache Sistemi

### L1: Memory Cache
- **Hız:** En hızlı
- **Boyut:** 100 item
- **TTL:** Uygulama yaşam döngüsü

### L2: Redis Hot Cache
- **Hız:** Hızlı
- **TTL:** 1 saat
- **Kullanım:** Sık erişilen sorgular

### L3: Redis Cold Cache
- **Hız:** Orta
- **TTL:** 24 saat
- **Kullanım:** Eski sorgular

**Cache Hit → 10x Hızlanma + $0 Maliyet**

## Maliyet Optimizasyonu

### Model Maliyetleri (Tahmini)
- **Claude Only:** ~$0.003 / istek
- **Gemini Assist:** ~$0.005 / istek
- **Gemini Thinking:** ~$0.008 / istek

### Tasarruf Stratejileri
1. **Cache kullanın:** Tekrarlayan sorgularda %100 tasarruf
2. **Basit sorular için Claude:** %60 daha ucuz
3. **Token optimizasyonu:** Gereksiz metni temizle

## Redis ile Kullanım (Opsiyonel)

```python
import redis.asyncio as redis
from backend.optimal_hybrid_system import OptimalHybridSystem

async def main():
    # Redis bağlantısı
    redis_client = await redis.from_url("redis://localhost:6379")
    
    # Sistemi Redis ile başlat
    system = OptimalHybridSystem(redis_client=redis_client)
    
    # Kullan
    result = await system.process_query("Soru...")
    
    # Cache hit rate'i kontrol et
    metrics = system.get_metrics()
    print(f"Cache Hit Rate: {metrics['cache_hit_rate']['total']:.1%}")

asyncio.run(main())
```

## Sorun Giderme

### ❌ API Anahtarı Bulunamadı
```
⚠️ GOOGLE_API_KEY bulunamadı
```
**Çözüm:** `.env` dosyasına API anahtarınızı ekleyin

### ❌ Model Yüklenemedi
```
❌ Gemini model yüklenemedi
```
**Çözüm:** API anahtarınızın geçerli olduğundan emin olun

### ❌ Import Hatası
```
ModuleNotFoundError: No module named 'anthropic'
```
**Çözüm:** `pip install anthropic google-generativeai`

## API Anahtarı Alma

### Google Gemini
1. https://makersuite.google.com/app/apikey
2. "Create API Key" tıklayın
3. Anahtarı kopyalayın

### Anthropic Claude
1. https://console.anthropic.com/
2. "API Keys" bölümüne gidin
3. "Create Key" tıklayın
4. Anahtarı kopyalayın

## Örnek Çıktı

```
🔑 API Anahtarları Kontrolü
============================================================
✅ GOOGLE_API_KEY: AIzaSyB7KSM64qj3DIe...
✅ ANTHROPIC_API_KEY: sk-ant-api03-xyz...

🤖 Optimal Hybrid System - İnteraktif Mod
============================================================

💬 Soru: Python'da decorator nedir?

🎯 Routing: claude_only (karmaşıklık: 2/10)
⏱️  Tahmini süre: 1.5s
💰 Tahmini maliyet: $0.0030

⏳ İşleniyor...

✨ Yanıt (claude_only):
------------------------------------------------------------
Decorator, Python'da bir fonksiyonu veya sınıfı değiştirmek 
için kullanılan özel bir syntax'tır...
------------------------------------------------------------
⏱️  Süre: 1.23s | 💰 Maliyet: $0.0030 | 🔄 Cache: False

💬 Soru: metrics

📊 Sistem Metrikleri:
   Toplam İstek: 1
   Toplam Maliyet: $0.0030
   Ortalama Süre: 1.23s
   Cache Hit Rate: 0.0%
```

## İleri Seviye Kullanım

### Custom Routing Stratejisi

```python
from backend.optimal_hybrid_system import SmartRouter, ComplexityLevel

router = SmartRouter()

# Threshold'ları özelleştir
router.complexity_thresholds = {
    ComplexityLevel.SIMPLE: 2,    # Daha az Claude
    ComplexityLevel.MEDIUM: 5,    # Daha fazla Gemini Assist
    ComplexityLevel.COMPLEX: 8    # Daha az Thinking mode
}
```

### Token Optimizasyonu

```python
from backend.optimal_hybrid_system import TokenOptimizer

optimizer = TokenOptimizer()

# Prompt'u optimize et
optimized = optimizer.optimize_prompt(
    prompt="Çok uzun bir prompt...",
    max_tokens=2000
)

print(f"Orijinal: {optimizer.count_tokens(prompt)} token")
print(f"Optimize: {optimizer.count_tokens(optimized)} token")
```

## Performans İpuçları

1. **Cache'i aktif tutun:** `use_cache=True` (varsayılan)
2. **Context'i minimize edin:** Sadece gerekli bilgiyi gönderin
3. **Batch işlemler:** Birden fazla soru için aynı sistemi kullanın
4. **Redis kullanın:** Dağıtık sistemlerde cache paylaşımı için

## Güvenlik

- API anahtarlarını asla commit etmeyin
- `.env` dosyasını `.gitignore`'a ekleyin
- Production'da environment variables kullanın
- Rate limiting uygulayın

## Destek

Sorun yaşarsanız:
1. `python start_hybrid_system.py` çalıştırın
2. API anahtarlarını kontrol edin
3. Hata mesajlarını okuyun
4. Gerekirse `.env` dosyasını güncelleyin
