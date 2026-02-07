# Zemberek-NLP MCP Server - Gelistirici Rehberi

Bu dokuman, Zemberek-NLP MCP Server'in gelistirilmesi ve genisletilmesi icin teknik detaylar icerir.

## Mimari Genel Bakis

```
mcp_servers/zemberek_nlp/
├── __init__.py           # Modul baslangic
├── server.py             # MCP sunucu entry point
├── config.py             # Pydantic konfigurasyonu
├── bridge/               # JPype Bridge modulu
│   ├── __init__.py
│   ├── jpype_bridge.py   # Thread-safe singleton
│   └── exceptions.py     # Ozel hatalar
├── tools/                # 8 NLP araci
│   ├── __init__.py
│   ├── base.py           # BaseToolHandler
│   ├── morphology.py
│   ├── lemmatization.py
│   ├── spell_check.py
│   ├── tokenization.py
│   ├── segmentation.py
│   ├── normalization.py
│   ├── ner.py
│   └── health.py
├── cache/                # Redis cache
│   ├── __init__.py
│   └── redis_cache.py
└── models/               # Pydantic modelleri
    ├── __init__.py
    └── responses.py
```

## Temel Bilesenler

### 1. JPype Bridge (Singleton Pattern)

JPype bridge, thread-safe singleton olarak implemente edilmistir:

```python
class ZemberekJPypeBridge:
    _instance: Optional["ZemberekJPypeBridge"] = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls) -> "ZemberekJPypeBridge":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        with self._lock:
            if self._initialized:
                return
            # JVM baslat, Zemberek yukle
            self._start_jvm()
            self._load_zemberek()
            self._initialized = True
```

**Neden Singleton?**
- JVM process basina tek instance
- Bellek verimli kullanim
- Thread-safe erisim

### 2. Async Uyumluluk

JPype cagrilari blocking'dir. Async uyumluluk icin `asyncio.to_thread()` kullanilir:

```python
async def analyze_word_async(self, word: str) -> List[Dict[str, Any]]:
    """Non-blocking async wrapper."""
    return await asyncio.to_thread(self.analyze_word, word)
```

### 3. BaseToolHandler

Tum araclar BaseToolHandler'dan turetilir:

```python
class BaseToolHandler(ABC):
    tool_name: str  # Override gerekli

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Ana giris noktasi - cache + fallback yonetimi."""
        # 1. Cache kontrol
        cached = await self._check_cache(**kwargs)
        if cached:
            return {**cached, "cached": True}

        # 2. JPype -> HTTP fallback
        result = await self._execute_with_fallback(**kwargs)

        # 3. Cache kaydet
        await self._save_to_cache(result, **kwargs)

        return result

    @abstractmethod
    async def _call_jpype(self, **kwargs) -> Dict[str, Any]:
        """Alt siniflar override eder."""
        pass

    @abstractmethod
    async def _call_backend(self, **kwargs) -> Dict[str, Any]:
        """HTTP fallback - alt siniflar override eder."""
        pass
```

### 4. JPype -> HTTP Fallback

```python
async def _execute_with_fallback(self, **kwargs) -> Dict[str, Any]:
    if self._use_jpype:
        try:
            result = await self._call_jpype(**kwargs)
            result["backend"] = "jpype"
            return result
        except Exception as e:
            logger.warning(f"JPype failed: {e}, falling back to HTTP")

    result = await self._call_backend(**kwargs)
    result["backend"] = "http"
    return result
```

## Yeni Arac Ekleme

### Adim 1: Tool Handler Olustur

```python
# tools/new_tool.py
from .base import BaseToolHandler

class NewToolHandler(BaseToolHandler):
    tool_name = "new_tool"

    async def _call_jpype(self, text: str, **kwargs) -> Dict[str, Any]:
        if not self.bridge:
            raise RuntimeError("JPype bridge not initialized")

        # Zemberek API cagrisi
        result = await self.bridge.some_method_async(text)

        return {
            "text": text,
            "result": result,
        }

    async def _call_backend(self, text: str, **kwargs) -> Dict[str, Any]:
        # HTTP fallback
        response = await self._post("/new-endpoint", {"text": text})
        return response
```

### Adim 2: Bridge'e Method Ekle

```python
# bridge/jpype_bridge.py
def new_method(self, text: str) -> Any:
    """Yeni Zemberek fonksiyonu."""
    # Java API cagrisi
    return self._zemberek_component.someMethod(text)

async def new_method_async(self, text: str) -> Any:
    return await asyncio.to_thread(self.new_method, text)
```

### Adim 3: Server'a Kaydet

```python
# server.py
from .tools.new_tool import NewToolHandler

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    handlers = {
        # ... mevcut handler'lar
        "zemberek_new_tool": NewToolHandler,
    }
    # ...
```

### Adim 4: Test Yaz

```python
# tests/mcp_servers/zemberek_nlp/test_new_tool.py
class TestNewToolHandler:
    @pytest.mark.asyncio
    async def test_call_jpype(self, mock_config, mock_bridge):
        handler = NewToolHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="test")

        assert "result" in result
```

## Test Yapisi

### Test Kategorileri

```
tests/
├── unit/
│   └── test_jpype_bridge.py       # Bridge unit testleri
├── mcp_servers/
│   └── zemberek_nlp/
│       └── test_tools_jpype.py    # Tool handler testleri
├── property/
│   └── test_zemberek_jpype.py     # Property-based testler
├── integration/
│   ├── test_mcp_claude_integration.py  # MCP entegrasyon
│   └── test_concurrent_load.py    # Load testler
└── fixtures/
    └── turkish_words.py           # Test verileri
```

### Test Calistirma

```bash
# Tum testler
pytest tests/ -v

# Sadece unit testler
pytest tests/unit/ -v

# Property testler (100 iterasyon)
pytest tests/property/ -v

# Integration testler
pytest tests/integration/ -v

# Coverage ile
pytest --cov=mcp_servers/zemberek_nlp --cov-report=html

# Paralel calistirma
pytest -n auto
```

### Mock Olusturma

```python
@pytest.fixture
def mock_bridge():
    """Mock JPype bridge."""
    bridge = MagicMock()
    bridge.is_initialized = True

    async def mock_analyze(word):
        return [{"root": word, "lemma": word, "pos": "Noun", "suffixes": []}]

    bridge.analyze_word_async = AsyncMock(side_effect=mock_analyze)
    return bridge
```

## Hata Yonetimi

### Ozel Exception'lar

```python
# bridge/exceptions.py
class ZemberekError(Exception):
    """Temel Zemberek hatasi."""
    pass

class JVMInitializationError(ZemberekError):
    """JVM baslatma hatasi."""
    pass

class JVMNotStartedError(ZemberekError):
    """JVM baslatilmamis hatasi."""
    pass

class AnalysisError(ZemberekError):
    """Analiz hatasi."""
    def __init__(self, word: str, message: str = ""):
        self.word = word
        self.message = message or f"Analysis failed for: {word}"
```

### Hata Yonetim Stratejisi

1. **JPype Hatalari** → HTTP fallback
2. **HTTP Hatalari** → Varsayilan sonuc veya hata
3. **Cache Hatalari** → Cache'siz devam

```python
try:
    result = await self._call_jpype(**kwargs)
except JVMNotStartedError:
    logger.error("JVM not started")
    result = await self._call_backend(**kwargs)
except AnalysisError as e:
    logger.warning(f"Analysis error for {e.word}")
    result = {"error": str(e)}
```

## Performans Optimizasyonu

### 1. Batch Processing

```python
async def _lemmatize_batch_parallel(
    self, words: List[str], batch_size: int = 10
) -> List[str]:
    """Paralel batch lemmatizasyon."""
    results = []

    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[self.bridge.lemmatize_async(w) for w in batch]
        )
        results.extend(batch_results)

    return results
```

### 2. Cache Stratejisi

- **TTL:** Sonuc tipine gore (morphology: 1 saat, spell: 24 saat)
- **Key Format:** `{tool}:{hash(input)}`
- **Eviction:** LRU

### 3. JVM Memory Ayarlari

```python
jpype_jvm_options: List[str] = [
    "-Xmx512m",    # Max heap
    "-Xms256m",    # Initial heap
    "-XX:+UseG1GC",  # G1 garbage collector
]
```

## Windows Ozellikleri

### Class Path

Windows'ta class path seperatoru `;` olmalidir:

```python
def _build_classpath(self) -> str:
    separator = ";" if os.name == "nt" else ":"
    return separator.join(self._jar_paths)
```

### JVM Yolu

```python
def _find_jvm_path(self) -> str:
    if os.name == "nt":
        # Windows: JAVA_HOME/bin/server/jvm.dll
        return os.path.join(
            os.environ["JAVA_HOME"], "bin", "server", "jvm.dll"
        )
    else:
        # Linux: libjvm.so
        return jpype.getDefaultJVMPath()
```

## CI/CD Entegrasyonu

### GitHub Actions

```yaml
# .github/workflows/zemberek-tests.yml
name: Zemberek Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements_zemberek.txt
      - run: python scripts/download_zemberek_jar.py
      - run: pytest tests/mcp_servers/zemberek_nlp/ -v
```

## Debugging

### JVM Debug

```python
# Debug loglama aktif
import logging
logging.getLogger("jpype").setLevel(logging.DEBUG)

# JVM debug options
jpype_jvm_options = [
    "-Xmx512m",
    "-verbose:gc",  # GC loglama
    "-XX:+PrintGCDetails",
]
```

### Bridge Debug

```python
# Bridge durumu kontrol
bridge = get_bridge(config)
print(f"Initialized: {bridge.is_initialized}")
print(f"Health: {bridge.get_health()}")
```

## Kaynaklar

- [Zemberek API Docs](https://github.com/ahmetaa/zemberek-nlp/wiki)
- [JPype User Guide](https://jpype.readthedocs.io/en/latest/userguide.html)
- [FastMCP Documentation](https://fastmcp.readthedocs.io/)
- [Pydantic v2 Migration](https://docs.pydantic.dev/latest/migration/)
