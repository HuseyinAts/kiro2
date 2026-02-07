# Zemberek-NLP MCP Server

Zemberek-NLP MCP Server, Claude ile Turkce dogal dil isleme (NLP) yetenekleri saglayan bir Model Context Protocol (MCP) sunucusudur. Zemberek kutuphanesini JPype uzerinden dogrudan kullanir.

## Ozellikler

### 8 NLP Araci

| Arac | Aciklama | Ornek Kullanim |
|------|----------|----------------|
| `zemberek_morphology` | Morfolojik analiz | "kitaplarımızda" → kok, ek, tip |
| `zemberek_lemmatization` | Lemmatizasyon | "kitaplar" → "kitap" |
| `zemberek_spell_check` | Yazim kontrolu | "yanliz" → yanlis, oneriler |
| `zemberek_tokenization` | Token ayirma | "Merhaba dunya!" → ["Merhaba", "dunya", "!"] |
| `zemberek_segmentation` | Cumle bolme | Metni cumlelere ayirir |
| `zemberek_normalization` | Metin normalizasyonu | "yalniz" → "yalnız" |
| `zemberek_ner` | Varlik tanima | Isim, yer, organizasyon cikarimi |
| `zemberek_health` | Saglik kontrolu | Servis durumu |

## Kurulum

### Gereksinimler

1. **Python 3.11+**
2. **JDK 11 veya 17** (JAVA_HOME ayarli olmali)
3. **Zemberek JAR** (otomatik indirilebilir)

### Adim 1: Bagimliliklari Yukle

```bash
cd backend
pip install -r requirements_zemberek.txt
```

Veya manuel:

```bash
pip install JPype1>=1.5.0 fastmcp>=0.3.0 pydantic>=2.5.0 httpx>=0.25.0 redis>=5.0.0
```

### Adim 2: Zemberek JAR Indir

```bash
python scripts/download_zemberek_jar.py
```

Varsayilan konum: `backend/lib/zemberek/zemberek-full.jar`

### Adim 3: Ortam Degiskenlerini Ayarla

```bash
# Windows
set JAVA_HOME=C:\Program Files\Java\jdk-17
set ZEMBEREK_JAR_PATH=lib/zemberek/zemberek-full.jar

# Linux/Mac
export JAVA_HOME=/usr/lib/jvm/java-17
export ZEMBEREK_JAR_PATH=lib/zemberek/zemberek-full.jar
```

### Adim 4: MCP Sunucusunu Baslat

```bash
cd backend
python -m mcp_servers.zemberek_nlp.server
```

## Konfigurasyon

Ortam degiskenleri veya `.env` dosyasi ile:

```ini
# JPype Ayarlari
ZEMBEREK_USE_JPYPE=true
JAVA_HOME=/usr/lib/jvm/java-17
ZEMBEREK_JAR_PATH=lib/zemberek/zemberek-full.jar
JPYPE_JVM_OPTIONS=-Xmx512m,-Xms256m

# HTTP Fallback (JPype basarisiz olursa)
ZEMBEREK_URL=http://localhost:8081
ZEMBEREK_HTTP_TIMEOUT=10.0

# Redis Cache
ZEMBEREK_REDIS_URL=redis://localhost:6379
ZEMBEREK_CACHE_TTL=3600

# Loglama
ZEMBEREK_LOG_LEVEL=INFO
```

## Kullanim Ornekleri

### Claude ile MCP Uzerinden

Claude Desktop'ta `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zemberek": {
      "command": "python",
      "args": ["-m", "mcp_servers.zemberek_nlp.server"],
      "cwd": "/path/to/backend"
    }
  }
}
```

### Python API

```python
from mcp_servers.zemberek_nlp.tools import MorphologyHandler
from mcp_servers.zemberek_nlp.config import ZemberekConfig
from mcp_servers.zemberek_nlp.bridge import get_bridge

# Bridge baslat
config = ZemberekConfig()
bridge = get_bridge(config)
bridge.initialize()

# Arac kullan
handler = MorphologyHandler(bridge=bridge, config=config)
result = await handler.execute(text="kitaplarımızda")

print(result)
# {
#   "text": "kitaplarımızda",
#   "word_analyses": [...],
#   "total_words": 1,
#   "backend": "jpype"
# }
```

### Dogrudan Bridge Kullanimi

```python
from mcp_servers.zemberek_nlp.bridge import ZemberekJPypeBridge

bridge = ZemberekJPypeBridge()
bridge.initialize()

# Morfolojik analiz
analyses = bridge.analyze_word("kitaplarımızda")
for a in analyses:
    print(f"Kok: {a['root']}, Tip: {a['pos']}, Ekler: {a['suffixes']}")

# Lemmatizasyon
lemma = bridge.lemmatize("kitaplar")  # "kitap"

# Yazim kontrolu
result = bridge.check_spelling("yalniz")
print(f"Dogru mu: {result['is_correct']}")  # False
print(f"Oneriler: {result['suggestions']}")  # ["yalnız"]
```

## Arac Detaylari

### zemberek_morphology

Turkce kelimelerin morfolojik analizini yapar.

**Giris:**
```json
{"text": "evlerimizde"}
```

**Cikis:**
```json
{
  "text": "evlerimizde",
  "word_analyses": [
    {
      "word": "evlerimizde",
      "analyses": [
        {
          "root": "ev",
          "lemma": "ev",
          "pos": "Noun",
          "suffixes": ["ler", "imiz", "de"],
          "is_proper_noun": false,
          "confidence": 1.0
        }
      ]
    }
  ],
  "total_words": 1,
  "backend": "jpype"
}
```

### zemberek_lemmatization

Kelimelerin kok hallerini (lemma) bulur.

**Giris:**
```json
{"text": "kitaplar evler arabalar", "batch": true}
```

**Cikis:**
```json
{
  "text": "kitaplar evler arabalar",
  "lemmas": [
    {"word": "kitaplar", "lemma": "kitap"},
    {"word": "evler", "lemma": "ev"},
    {"word": "arabalar", "lemma": "araba"}
  ],
  "total_words": 3,
  "throughput_wps": 1500.5
}
```

### zemberek_spell_check

Yazim hatalarini tespit eder ve duzeltme onerir.

**Giris:**
```json
{"text": "yalniz guzle nasilsin"}
```

**Cikis:**
```json
{
  "text": "yalniz guzle nasilsin",
  "words": [
    {"word": "yalniz", "is_correct": false, "suggestions": ["yalnız"]},
    {"word": "guzle", "is_correct": false, "suggestions": ["güzel", "güzle"]},
    {"word": "nasilsin", "is_correct": false, "suggestions": ["nasılsın"]}
  ],
  "accuracy": 0.0,
  "error_count": 3
}
```

### zemberek_tokenization

Metni token'lara ayirir.

**Giris:**
```json
{"text": "Dr. Ahmet https://example.com adresini ziyaret etti."}
```

**Cikis:**
```json
{
  "text": "Dr. Ahmet https://example.com adresini ziyaret etti.",
  "tokens": ["Dr.", "Ahmet", "https://example.com", "adresini", "ziyaret", "etti", "."],
  "token_count": 7,
  "has_url": true,
  "has_abbreviation": true
}
```

### zemberek_segmentation

Metni cumlelere boler.

**Giris:**
```json
{"text": "Merhaba! Nasilsin? Ben iyiyim."}
```

**Cikis:**
```json
{
  "sentences": [
    {"text": "Merhaba!", "index": 0},
    {"text": "Nasilsin?", "index": 1},
    {"text": "Ben iyiyim.", "index": 2}
  ],
  "sentence_count": 3,
  "has_question": true,
  "has_dialog": false
}
```

### zemberek_normalization

Metni normalize eder (diacritic duzeltme, tekrar eden karakterler).

**Giris:**
```json
{"text": "coook guzel yalniz"}
```

**Cikis:**
```json
{
  "original": "coook guzel yalniz",
  "normalized": "çok güzel yalnız",
  "changes": [
    {"type": "repeated", "from": "coook", "to": "çok"},
    {"type": "diacritic", "from": "guzel", "to": "güzel"},
    {"type": "diacritic", "from": "yalniz", "to": "yalnız"}
  ]
}
```

### zemberek_ner

Metinden varlik (entity) cikarir.

**Giris:**
```json
{"text": "Ahmet Istanbul'da Koc Universitesi'nde calisiyor."}
```

**Cikis:**
```json
{
  "entities": [
    {"text": "Ahmet", "type": "PERSON", "start": 0, "end": 5},
    {"text": "Istanbul", "type": "LOCATION", "start": 6, "end": 14},
    {"text": "Koc Universitesi", "type": "ORGANIZATION", "start": 18, "end": 34}
  ],
  "entity_count": 3
}
```

### zemberek_health

Servis saglik durumunu kontrol eder.

**Cikis:**
```json
{
  "status": "healthy",
  "backend_mode": "jpype",
  "jpype_initialized": true,
  "jvm_memory_mb": 256,
  "components": {
    "morphology": true,
    "spell_checker": true,
    "tokenizer": true,
    "sentence_extractor": true,
    "normalizer": true,
    "ner": true
  },
  "cache": {
    "connected": true,
    "hit_rate": 0.75
  }
}
```

## Performans

| Metrik | Hedef | Tipik |
|--------|-------|-------|
| Morfolojik Analiz | < 10ms/kelime | 2-5ms |
| Lemmatizasyon | < 5ms/kelime | 1-3ms |
| Yazim Kontrolu | < 15ms/kelime | 5-10ms |
| Tokenizasyon | < 20ms/cumle | 5-15ms |
| Cache Hit | < 1ms | 0.1-0.5ms |
| P95 Latency | < 100ms | 50-80ms |

## Sorun Giderme

### JVM Baslatma Hatasi

```
JVMInitializationError: JVM initialization failed
```

**Cozum:**
1. JAVA_HOME dogru ayarli mi kontrol et
2. JDK 11 veya 17 yuklu mu kontrol et
3. 32-bit/64-bit uyumu kontrol et

### Zemberek JAR Bulunamadi

```
FileNotFoundError: Zemberek JAR not found
```

**Cozum:**
```bash
python scripts/download_zemberek_jar.py
```

### Redis Baglanti Hatasi

```
ConnectionError: Cannot connect to Redis
```

**Cozum:**
- Redis servisini baslat
- ZEMBEREK_REDIS_URL dogru mu kontrol et
- Cache olmadan calisir (performans duser)

### Windows'ta Class Path Hatasi

```
ClassNotFoundException: zemberek.morphology.TurkishMorphology
```

**Cozum:**
- JAR yolunda bosluk olmasin
- Yol seperatoru `;` (noktalı virgul) olmali

## Lisans

Bu proje MIT lisansi altindadir. Zemberek kutuphanesi Apache 2.0 lisansi altindadir.

## Kaynaklar

- [Zemberek GitHub](https://github.com/ahmetaa/zemberek-nlp)
- [JPype Dokumantasyonu](https://jpype.readthedocs.io/)
- [MCP Protokolu](https://modelcontextprotocol.io/)
