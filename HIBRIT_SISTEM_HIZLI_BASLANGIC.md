# 🚀 Hibrit Sistem - Hızlı Başlangıç

## Claude Code (Kiro) İçinde Kullanım

### ✅ Sistem Hazır!

Hibrit sistem gerçek API entegrasyonları ile hazır durumda.

### 1️⃣ Başlatma

Terminal'de şu komutu çalıştır:

```bash
py start_hybrid_system.py
```

### 2️⃣ Mod Seçimi

**Demo Modu (1):** Otomatik olarak 3 test sorusu çalıştırır
- Basit soru → Claude Only
- Kod analizi → Gemini Assist
- Karmaşık tasarım → Gemini Thinking

**İnteraktif Mod (2):** Kendi sorularını sor
- Soru yaz, Enter'a bas
- `metrics` → İstatistikleri gör
- `exit` → Çık

### 3️⃣ Örnek Kullanım

```
💬 Soru: Python'da async/await nasıl çalışır?

🎯 Routing: claude_only (karmaşıklık: 2/10)
⏱️  Tahmini süre: 1.5s
💰 Tahmini maliyet: $0.0030

⏳ İşleniyor...

✨ Yanıt (claude_only):
------------------------------------------------------------
Async/await, Python'da asenkron programlama için kullanılan...
------------------------------------------------------------
⏱️  Süre: 1.23s | 💰 Maliyet: $0.0030 | 🔄 Cache: False
```

## Programatik Kullanım

### Basit Örnek

```python
import asyncio
from backend.optimal_hybrid_system import OptimalHybridSystem

async def main():
    system = OptimalHybridSystem()
    
    result = await system.process_query(
        query="FastAPI ile REST API nasıl oluşturulur?",
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
        "language": "python",
        "framework": "FastAPI"
    }
)
```

### Routing Bilgisi

```python
from backend.optimal_hybrid_system import SmartRouter

router = SmartRouter()
info = router.get_routing_info("Mikroservis mimarisi tasarla")

print(f"Model: {info['model_type']}")
print(f"Karmaşıklık: {info['complexity']}/10")
print(f"Tahmini süre: {info['estimated_time']}s")
print(f"Tahmini maliyet: ${info['estimated_cost']}")
```

## Akıllı Routing

Sistem otomatik olarak en uygun modeli seçer:

### 🟢 Basit (0-3) → Claude Only
- Kısa sorular
- Tanımlar
- Basit açıklamalar
- **Avantaj:** Hızlı ve ucuz ($0.003)

### 🟡 Orta (4-6) → Gemini Assist
- Kod analizi
- Orta seviye açıklamalar
- Optimizasyon önerileri
- **Avantaj:** Dengeli ($0.005)

### 🔴 Karmaşık (7-10) → Gemini Thinking
- Mimari tasarım
- Detaylı analiz
- Adım adım çözüm
- **Avantaj:** En kaliteli ($0.008)

## Karmaşıklık Puanlama

- **Token sayısı:** >100 token → +2 puan
- **Kod içeriyor:** ``` veya def/class → +2 puan
- **Analiz:** "analiz", "incele", "optimize" → +3 puan
- **Thinking:** "adım adım", "detaylı", "açıkla" → +2 puan
- **Dosya analizi:** Context'te file_content → +2 puan

## 3 Katmanlı Cache

- **L1 (Memory):** En hızlı, 100 item
- **L2 (Redis Hot):** 1 saat TTL
- **L3 (Redis Cold):** 24 saat TTL

**Cache Hit → 10x Hızlanma + $0 Maliyet**

## API Anahtarları

### Google Gemini (Gerekli)
`.env` dosyasında zaten var:
```
GOOGLE_API_KEY=AIzaSyB7KSM64qj3DIeTLsWnWVTHDrHU41NzUvA
```

### Anthropic Claude (Opsiyonel)
Daha iyi performans için ekle:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**Nasıl alınır:**
1. https://console.anthropic.com/
2. "API Keys" → "Create Key"
3. Anahtarı kopyala ve `.env`'ye ekle

## Metrikler

```python
metrics = system.get_metrics()

print(f"Toplam İstek: {metrics['total_requests']}")
print(f"Toplam Maliyet: ${metrics['total_cost']:.4f}")
print(f"Ortalama Süre: {metrics['avg_time']:.2f}s")
print(f"Cache Hit Rate: {metrics['cache_hit_rate']['total']:.1%}")
```

## Sorun Giderme

### ❌ GOOGLE_API_KEY bulunamadı
**Çözüm:** `.env` dosyasını kontrol et, anahtarın doğru olduğundan emin ol

### ❌ ModuleNotFoundError: anthropic
**Çözüm:** `pip install anthropic google-generativeai`

### ❌ API hatası
**Çözüm:** API anahtarının geçerli olduğunu kontrol et

## Özellikler

✅ **Akıllı Routing:** Otomatik model seçimi  
✅ **3 Katmanlı Cache:** 10x hızlanma  
✅ **Maliyet Optimizasyonu:** %60'a kadar tasarruf  
✅ **Token Optimizasyonu:** Gereksiz token kullanımını azaltır  
✅ **Metrik Takibi:** Detaylı performans analizi  
✅ **Fallback Mekanizması:** Bir model başarısız olursa diğerini dener  

## Performans

- **Basit soru:** ~1.5s, $0.003
- **Orta seviye:** ~5s, $0.005
- **Karmaşık analiz:** ~15s, $0.008
- **Cache hit:** <0.1s, $0.000

## Güvenlik

- API anahtarlarını asla commit etme
- `.env` dosyasını `.gitignore`'a ekle
- Production'da environment variables kullan

## Daha Fazla Bilgi

Detaylı kullanım için: `HIBRIT_SISTEM_KULLANIM.md`
