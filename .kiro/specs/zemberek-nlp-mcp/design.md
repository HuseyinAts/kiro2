# Design Document - Zemberek-NLP MCP Server

## Overview

Zemberek-NLP MCP Server, Türkçe doğal dil işleme (NLP) için Zemberek kütüphanesini Model Context Protocol (MCP) üzerinden Claude'a entegre eden sistemdir. Morphological analysis, lemmatization, spell checking, tokenization, NER, sentence segmentation, normalization ve health check araçları sağlar. >= %90 Türkçe NLP accuracy ve < 100ms API latency hedefler.

**Temel Özellikler:**
- 8 Türkçe NLP tool (analyze, lemmatize, spell_check, tokenize, ner, segment_sentences, normalize, health_check)
- FastAPI-based MCP server
- Zemberek-Python integration via JPype
- Redis caching for frequent operations
- Async/await throughout
- Connection pooling
- Comprehensive error handling

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Desktop / Kiro                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  User Request: "Bu cümleyi analiz et"                    │  │
│  └────────────────────┬─────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                         │ MCP Protocol
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Zemberek-NLP MCP Server (FastAPI)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MCP Tool Router                                          │  │
│  │  - tools/list: Return available tools                     │  │
│  │  - tools/call: Execute tool with parameters               │  │
│  │  - Validate input schemas                                 │  │
│  │  - Route to appropriate handler                           │  │
│  └────────────────────┬─────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Tool Handlers (Async)                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Morpho   │  │ Lemma    │  │ Spell    │  │ Token    │       │
│  │ Analysis │  │ tization │  │ Check    │  │ ization  │       │
│  │ Handler  │  │ Handler  │  │ Handler  │  │ Handler  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │             │               │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐       │
│  │ NER      │  │ Sentence │  │ Normal   │  │ Health   │       │
│  │ Handler  │  │ Segment  │  │ ization  │  │ Check    │       │
│  │          │  │ Handler  │  │ Handler  │  │ Handler  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Cache Layer (Redis)                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Cache Strategy:                                          │  │
│  │  - Key: zemberek:{tool}:{hash(input)}                    │  │
│  │  - TTL: 3600s (1 hour)                                    │  │
│  │  - Check cache before Zemberek call                       │  │
│  │  - Store result after successful call                     │  │
│  └────────────────────┬─────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Zemberek-Python Bridge (JPype)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  JPype JVM Bridge                                         │  │
│  │  - Initialize JVM with Zemberek JAR                       │  │
│  │  - Create Zemberek instances:                             │  │
│  │    * TurkishMorphology                                    │  │
│  │    * TurkishSpellChecker                                  │  │
│  │    * TurkishTokenizer                                     │  │
│  │    * TurkishSentenceExtractor                             │  │
│  │  - Thread-safe access                                     │  │
│  └────────────────────┬─────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Zemberek-NLP Library (Java)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Core Zemberek Components:                                │  │
│  │  - Morphological Analyzer                                 │  │
│  │  - Lemmatizer                                             │  │
│  │  - Spell Checker with Turkish dictionary                  │  │
│  │  - Tokenizer with Turkish rules                           │  │
│  │  - Named Entity Recognizer                                │  │
│  │  - Sentence Segmenter                                     │  │
│  │  - Text Normalizer                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Response Flow                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Zemberek processes Turkish text                       │  │
│  │  2. Result converted to Python dict                       │  │
│  │  3. Cached in Redis                                       │  │
│  │  4. Formatted as MCP response                             │  │
│  │  5. Returned to Claude                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
backend/
├── mcp_servers/
│   ├── zemberek_nlp/
│   │   ├── __init__.py
│   │   ├── server.py                    # FastAPI MCP server
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── morphology.py            # Morphological analysis
│   │   │   ├── lemmatization.py         # Lemmatization
│   │   │   ├── spell_check.py           # Spell checking
│   │   │   ├── tokenization.py          # Tokenization
│   │   │   ├── ner.py                   # Named Entity Recognition
│   │   │   ├── segmentation.py          # Sentence segmentation
│   │   │   ├── normalization.py         # Text normalization
│   │   │   └── health.py                # Health check
│   │   ├── zemberek/
│   │   │   ├── __init__.py
│   │   │   ├── bridge.py                # JPype bridge to Zemberek
│   │   │   ├── morphology_analyzer.py
│   │   │   ├── spell_checker.py
│   │   │   └── tokenizer.py
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── redis_cache.py           # Redis caching
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── tool_schemas.py          # Pydantic input/output schemas
│   │   │   └── mcp_protocol.py          # MCP protocol models
│   │   └── config.py                    # Configuration
├── tests/
│   └── mcp_servers/
│       └── zemberek_nlp/
│           ├── test_tools.py
│           ├── test_zemberek_bridge.py
│           └── test_integration.py
└── requirements_zemberek.txt            # Zemberek-specific dependencies
```

## Components and Interfaces

### 1. MCP Server

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio

app = FastAPI(title="Zemberek-NLP MCP Server")

class MCPToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class MCPToolResponse(BaseModel):
    content: List[Dict[str, Any]]
    isError: bool = False

@app.post("/tools/call")
async def call_tool(request: MCPToolCall) -> MCPToolResponse:
    """
    MCP tool call endpoint
    
    Args:
        request: Tool name and arguments
        
    Returns:
        Tool execution result
    """
    try:
        # Route to appropriate tool handler
        if request.name == "zemberek_analyze":
            from .tools.morphology import analyze_morphology
            result = await analyze_morphology(request.arguments["text"])
        elif request.name == "zemberek_lemmatize":
            from .tools.lemmatization import lemmatize_text
            result = await lemmatize_text(request.arguments["text"])
        elif request.name == "zemberek_spell_check":
            from .tools.spell_check import check_spelling
            result = await check_spelling(request.arguments["text"])
        elif request.name == "zemberek_tokenize":
            from .tools.tokenization import tokenize_text
            result = await tokenize_text(request.arguments["text"])
        elif request.name == "zemberek_ner":
            from .tools.ner import extract_entities
            result = await extract_entities(request.arguments["text"])
        elif request.name == "zemberek_segment_sentences":
            from .tools.segmentation import segment_sentences
            result = await segment_sentences(request.arguments["text"])
        elif request.name == "zemberek_normalize":
            from .tools.normalization import normalize_text
            result = await normalize_text(request.arguments["text"])
        elif request.name == "zemberek_health":
            from .tools.health import health_check
            result = await health_check()
        else:
            raise HTTPException(status_code=404, detail=f"Tool not found: {request.name}")
        
        return MCPToolResponse(
            content=[{"type": "text", "text": str(result)}],
            isError=False
        )
    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            isError=True
        )

@app.get("/tools/list")
async def list_tools():
    """List all available Zemberek tools"""
    return {
        "tools": [
            {
                "name": "zemberek_analyze",
                "description": "Türkçe morphological analysis - kök, ek, tip bilgisi",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Analiz edilecek Türkçe metin"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "zemberek_lemmatize",
                "description": "Türkçe lemmatization - kelime köklerini bulma",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Lemmatize edilecek metin"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "zemberek_spell_check",
                "description": "Türkçe yazım denetimi ve düzeltme önerileri",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Kontrol edilecek metin"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "zemberek_tokenize",
                "description": "Türkçe tokenization - sözcük ayırma",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Tokenize edilecek metin"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "zemberek_ner",
                "description": "Türkçe Named Entity Recognition - özel isim tespiti",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "NER yapılacak metin"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "zemberek_segment_sentences",
                "description": "Türkçe cümle segmentasyonu",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Segment edilecek metin"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "zemberek_normalize",
                "description": "Türkçe metin normalizasyonu - informal -> formal",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Normalize edilecek metin"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "zemberek_health",
                "description": "Zemberek server health check",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }
```

### 2. Zemberek Bridge

```python
import jpype
import jpype.imports
from jpype.types import *
from typing import List, Dict
import threading

class ZemberekBridge:
    """Thread-safe bridge to Zemberek Java library"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Start JVM with Zemberek JAR
        if not jpype.isJVMStarted():
            jpype.startJVM(
                jpype.getDefaultJVMPath(),
                f"-Djava.class.path={self._get_zemberek_jar_path()}",
                convertStrings=True
            )
        
        # Import Zemberek classes
        from zemberek.morphology import TurkishMorphology
        from zemberek.tokenization import TurkishTokenizer
        from zemberek.normalization import TurkishSpellChecker
        from zemberek.ner import NER
        
        # Initialize Zemberek components
        self.morphology = TurkishMorphology.createWithDefaults()
        self.tokenizer = TurkishTokenizer.DEFAULT
        self.spell_checker = TurkishSpellChecker.DEFAULT
        self.ner = NER.DEFAULT
        
        self._initialized = True
    
    def analyze_word(self, word: str) -> List[Dict[str, any]]:
        """
        Morphological analysis of Turkish word
        
        Args:
            word: Turkish word to analyze
            
        Returns:
            List of analysis results with root, suffixes, POS
        """
        analyses = self.morphology.analyze(word)
        results = []
        
        for analysis in analyses:
            results.append({
                "root": str(analysis.getRoot()),
                "lemma": str(analysis.getLemma()),
                "pos": str(analysis.getPos()),
                "suffixes": [str(s) for s in analysis.getSuffixes()],
                "formatted": str(analysis.formatLong())
            })
        
        return results
    
    def lemmatize(self, word: str) -> str:
        """Get lemma (root form) of Turkish word"""
        analyses = self.morphology.analyze(word)
        if analyses:
            return str(analyses[0].getLemma())
        return word
    
    def check_spelling(self, word: str) -> Dict[str, any]:
        """
        Check spelling and get suggestions
        
        Returns:
            Dict with is_correct and suggestions
        """
        is_correct = self.spell_checker.check(word)
        suggestions = []
        
        if not is_correct:
            suggestions = [str(s) for s in self.spell_checker.suggestForWord(word)]
        
        return {
            "is_correct": is_correct,
            "suggestions": suggestions[:5]  # Top 5 suggestions
        }
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize Turkish text"""
        tokens = self.tokenizer.tokenize(text)
        return [str(token.getText()) for token in tokens]
    
    def _get_zemberek_jar_path(self) -> str:
        """Get path to Zemberek JAR file"""
        import os
        return os.path.join(os.path.dirname(__file__), "zemberek-full.jar")
```

### 3. Morphological Analysis Tool

```python
from pydantic import BaseModel
from typing import List, Dict
import hashlib
import json

class MorphologyResult(BaseModel):
    word: str
    analyses: List[Dict[str, any]]
    cached: bool = False

async def analyze_morphology(text: str) -> MorphologyResult:
    """
    Perform morphological analysis on Turkish text
    
    Args:
        text: Turkish text to analyze
        
    Returns:
        Morphological analysis results
    """
    from ..cache.redis_cache import get_cache, set_cache
    from ..zemberek.bridge import ZemberekBridge
    
    # Check cache
    cache_key = f"zemberek:morphology:{hashlib.md5(text.encode()).hexdigest()}"
    cached_result = await get_cache(cache_key)
    
    if cached_result:
        return MorphologyResult(**json.loads(cached_result), cached=True)
    
    # Analyze with Zemberek
    bridge = ZemberekBridge()
    words = text.split()
    all_analyses = []
    
    for word in words:
        analyses = bridge.analyze_word(word)
        all_analyses.append({
            "word": word,
            "analyses": analyses
        })
    
    result = MorphologyResult(
        word=text,
        analyses=all_analyses,
        cached=False
    )
    
    # Cache result
    await set_cache(cache_key, result.json(), ttl=3600)
    
    return result
```

## Data Models

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class MorphologyAnalysis(BaseModel):
    root: str = Field(..., description="Kelime kökü")
    lemma: str = Field(..., description="Lemma (sözlük formu)")
    pos: str = Field(..., description="Part of speech (isim, fiil, etc.)")
    suffixes: List[str] = Field(default_factory=list, description="Ekler")
    formatted: str = Field(..., description="Formatlanmış analiz")

class SpellCheckResult(BaseModel):
    word: str = Field(..., description="Kontrol edilen kelime")
    is_correct: bool = Field(..., description="Yazım doğru mu")
    suggestions: List[str] = Field(default_factory=list, description="Düzeltme önerileri")

class TokenizationResult(BaseModel):
    text: str = Field(..., description="Orijinal metin")
    tokens: List[str] = Field(..., description="Token'lar")
    token_count: int = Field(..., description="Token sayısı")

class NamedEntity(BaseModel):
    text: str = Field(..., description="Entity metni")
    type: str = Field(..., description="Entity tipi (PERSON, LOCATION, ORGANIZATION)")
    start: int = Field(..., description="Başlangıç pozisyonu")
    end: int = Field(..., description="Bitiş pozisyonu")

class NERResult(BaseModel):
    text: str = Field(..., description="Orijinal metin")
    entities: List[NamedEntity] = Field(..., description="Bulunan entity'ler")

class SentenceSegmentationResult(BaseModel):
    text: str = Field(..., description="Orijinal metin")
    sentences: List[str] = Field(..., description="Cümleler")
    sentence_count: int = Field(..., description="Cümle sayısı")

class NormalizationResult(BaseModel):
    original: str = Field(..., description="Orijinal metin")
    normalized: str = Field(..., description="Normalize edilmiş metin")
    changes: List[Dict[str, str]] = Field(default_factory=list, description="Yapılan değişiklikler")
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: Morphological Analysis Completeness
*For any* valid Turkish word, *the morphology analyzer SHALL return at least one analysis.*

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Lemmatization Consistency
*For any* inflected Turkish word, *the lemmatizer SHALL return the same lemma regardless of call order.*

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 3: Spell Check Accuracy
*For any* correctly spelled Turkish word in dictionary, *the spell checker SHALL return is_correct=True.*

**Validates: Requirements 3.1, 3.2, 3.5**

### Property 4: Tokenization Boundary Correctness
*For any* Turkish text, *the concatenation of tokens SHALL equal the original text (preserving whitespace).*

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 5: Cache Consistency
*For any* identical input, *cached results SHALL match non-cached results.*

**Validates: Requirements 1.6, 2.6, 3.6**

### Property 6: API Latency
*For any* cached operation, *the response time SHALL be < 10ms.*

**Validates: Requirements 3.6, 8.5**

## Error Handling

```python
class ZemberekError(Exception):
    """Base exception for Zemberek operations"""
    pass

class JVMInitializationError(ZemberekError):
    """JVM initialization failed"""
    pass

class AnalysisError(ZemberekError):
    """Analysis operation failed"""
    pass

# Error handling in tools
async def analyze_morphology(text: str) -> MorphologyResult:
    try:
        # ... analysis logic ...
    except JVMInitializationError as e:
        logger.error(f"JVM initialization failed: {e}")
        raise HTTPException(status_code=503, detail="Zemberek service unavailable")
    except AnalysisError as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Testing Strategy

### Unit Tests
- Test each tool independently
- Test Zemberek bridge initialization
- Test cache operations
- Test error handling

### Property-Based Tests
- Generate random Turkish text
- Verify morphological analysis completeness
- Verify lemmatization consistency
- Verify tokenization boundary correctness

### Integration Tests
- Test full MCP server workflow
- Test with Claude Desktop
- Test performance with large texts

**Test Configuration**: Minimum 100 iterations per property test

## Performance Considerations

- **JVM Initialization**: Initialize once, reuse across requests
- **Connection Pooling**: Thread-safe singleton pattern for Zemberek bridge
- **Redis Caching**: Cache frequent operations (TTL: 1 hour)
- **Async Operations**: All I/O operations use async/await
- **Target Latency**: < 100ms (P95), < 10ms for cached operations
