# Tasks Document - Zemberek-NLP MCP Server

## Overview

Bu doküman, Zemberek-NLP MCP Server'ın implementation task'larını tanımlar. FastAPI MCP server, Zemberek-Python bridge, 8 NLP tool ve caching içerir.

## Tasks

### 1. Base Infrastructure Setup

- [x] 1.1 Setup Zemberek-Python environment
  - [x] 1.1.1 Install JPype1 for Java-Python bridge
  - [x] 1.1.2 Download Zemberek JAR file
  - [x] 1.1.3 Configure JVM classpath
  - [x] 1.1.4 Test JVM initialization
  - [x]* 1.1.5 Write JVM initialization tests
  - _Requirements: 8.1, 8.2_

- [x] 1.2 Create Zemberek Bridge
  - [x] 1.2.1 Implement singleton pattern for thread-safety
  - [x] 1.2.2 Initialize TurkishMorphology
  - [x] 1.2.3 Initialize TurkishTokenizer
  - [x] 1.2.4 Initialize TurkishSpellChecker
  - [x] 1.2.5 Initialize NER
  - [x] 1.2.6 Add error handling for JVM failures
  - [x]* 1.2.7 Write bridge unit tests
  - _Requirements: 8.1, 8.2_

- [x] 1.3 Create data models with Pydantic
  - [x] 1.3.1 Define `MorphologyAnalysis` schema
  - [x] 1.3.2 Define `SpellCheckResult` schema
  - [x] 1.3.3 Define `TokenizationResult` schema
  - [x] 1.3.4 Define `NamedEntity` and `NERResult` schemas
  - [x] 1.3.5 Define `SentenceSegmentationResult` schema
  - [x] 1.3.6 Define `NormalizationResult` schema
  - [x] 1.3.7 Define MCP protocol models
  - [x]* 1.3.8 Write schema validation tests
  - _Requirements: All (data models)_

### 2. MCP Server Implementation

- [x] 2.1 Create FastAPI MCP server
  - [x] 2.1.1 Initialize FastAPI app
  - [x] 2.1.2 Implement `/tools/list` endpoint
  - [x] 2.1.3 Implement `/tools/call` endpoint
  - [x] 2.1.4 Add request validation
  - [x] 2.1.5 Add error handling middleware
  - [x] 2.1.6 Add logging middleware
  - [x]* 2.1.7 Write server tests
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 2.2 Implement tool routing
  - [x] 2.2.1 Create tool registry
  - [x] 2.2.2 Route to morphology tool
  - [x] 2.2.3 Route to lemmatization tool
  - [x] 2.2.4 Route to spell check tool
  - [x] 2.2.5 Route to tokenization tool
  - [x] 2.2.6 Route to NER tool
  - [x] 2.2.7 Route to segmentation tool
  - [x] 2.2.8 Route to normalization tool
  - [x] 2.2.9 Route to health check tool
  - [x]* 2.2.10 Write routing tests
  - _Requirements: 8.2_

### 3. NLP Tool Implementations

- [x] 3.1 Implement Morphological Analysis Tool
  - [x] 3.1.1 Create `analyze_morphology()` async function
  - [x] 3.1.2 Call Zemberek bridge for analysis
  - [x] 3.1.3 Parse root, lemma, POS, suffixes
  - [x] 3.1.4 Handle multiple analyses with confidence scores
  - [x] 3.1.5 Add proper noun detection
  - [x] 3.1.6 Integrate Redis caching
  - [x]* 3.1.7 Write tool tests
  - [x]* 3.1.8 **Property 1: Morphological Analysis Completeness** - Verify all words get analysis
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6**

- [x] 3.2 Implement Lemmatization Tool
  - [x] 3.2.1 Create `lemmatize_text()` async function
  - [x] 3.2.2 Extract lemma from morphological analysis
  - [x] 3.2.3 Handle context-aware selection for multiple roots
  - [x] 3.2.4 Return infinitive form for verbs
  - [x] 3.2.5 Return singular nominative for nouns
  - [x] 3.2.6 Validate lemma against Turkish dictionary
  - [x] 3.2.7 Optimize for batch processing (>= 1000 word/sec)
  - [x]* 3.2.8 Write tool tests
  - [x]* 3.2.9 **Property 2: Lemmatization Consistency** - Verify deterministic results
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

- [x] 3.3 Implement Spell Check Tool
  - [x] 3.3.1 Create `check_spelling()` async function
  - [x] 3.3.2 Check word against Turkish dictionary
  - [x] 3.3.3 Generate suggestions with edit distance <= 2
  - [x] 3.3.4 Use n-gram probability for context-aware correction
  - [x] 3.3.5 Support custom dictionary additions
  - [x] 3.3.6 Handle diacritic errors (ı/i, ş/s, ğ/g)
  - [x] 3.3.7 Optimize for < 100ms per sentence
  - [x]* 3.3.8 Write tool tests
  - [x]* 3.3.9 **Property 3: Spell Check Accuracy** - Verify dictionary words pass
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

- [x] 3.4 Implement Tokenization Tool
  - [x] 3.4.1 Create `tokenize_text()` async function
  - [x] 3.4.2 Detect word boundaries correctly
  - [x] 3.4.3 Handle punctuation (sentence-final vs mid-word)
  - [x] 3.4.4 Preserve abbreviations ("Dr.", "vb.")
  - [x] 3.4.5 Preserve number formats ("1.000.000")
  - [x] 3.4.6 Handle URL/email as single tokens
  - [x] 3.4.7 Support BPE subword tokenization (IMPLEMENTED - uses HuggingFace tokenizers + BERTurk)
  - [x]* 3.4.8 Write tool tests
  - [x]* 3.4.9 **Property 4: Tokenization Boundary Correctness** - Verify reconstruction
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

- [x] 3.5 Implement Named Entity Recognition Tool
  - [x] 3.5.1 Create `extract_entities()` async function
  - [x] 3.5.2 Detect person, location, organization entities
  - [x] 3.5.3 Group multi-word entities
  - [x] 3.5.4 Classify entity types with >= 85% accuracy
  - [x] 3.5.5 Handle Turkish-specific entities ("İstanbul", "Türkiye")
  - [x] 3.5.6 Support entity linking to knowledge base
  - [x] 3.5.7 Support fine-tuning for domain-specific entities
  - [x]* 3.5.8 Write tool tests
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6**

- [x] 3.6 Implement Sentence Segmentation Tool
  - [x] 3.6.1 Create `segment_sentences()` async function
  - [x] 3.6.2 Detect sentence boundaries correctly
  - [x] 3.6.3 Handle abbreviations without false positives
  - [x] 3.6.4 Parse nested quotations
  - [x] 3.6.5 Handle ellipsis ("...") as sentence-final
  - [x] 3.6.6 Segment dialog with speaker turns
  - [x] 3.6.7 Achieve >= 98% accuracy
  - [x]* 3.6.8 Write tool tests
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**

- [x] 3.7 Implement Normalization Tool
  - [x] 3.7.1 Create `normalize_text()` async function
  - [x] 3.7.2 Convert informal to formal ("naber" -> "ne haber")
  - [x] 3.7.3 Fix repeated characters ("çoooook" -> "çok")
  - [x] 3.7.4 Convert emoji/emoticon to text
  - [x] 3.7.5 Detect and suggest formal equivalents for slang
  - [x] 3.7.6 Apply Turkish uppercase rules (I/İ, i/ı)
  - [x] 3.7.7 Support crowdsourced normalization dictionary updates
  - [x]* 3.7.8 Write tool tests
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**

- [x] 3.8 Implement Health Check Tool
  - [x] 3.8.1 Create `health_check()` async function
  - [x] 3.8.2 Test Zemberek library availability
  - [x] 3.8.3 Test JVM status
  - [x] 3.8.4 Test Redis connection
  - [x] 3.8.5 Return service status and version
  - [x]* 3.8.6 Write health check tests
  - **Validates: Requirements 8.6**

### 4. Caching Layer Implementation

- [x] 4.1 Create Redis cache module
  - [x] 4.1.1 Initialize Redis connection with aioredis
  - [x] 4.1.2 Implement `get_cache()` async function
  - [x] 4.1.3 Implement `set_cache()` async function with TTL
  - [x] 4.1.4 Use namespace: `zemberek:{tool}:{hash(input)}`
  - [x] 4.1.5 Set TTL to 3600s (1 hour)
  - [x] 4.1.6 Add cache hit/miss metrics
  - [x]* 4.1.7 Write cache tests
  - [x]* 4.1.8 **Property 5: Cache Consistency** - Verify cached = non-cached results
  - _Requirements: 1.6, 2.6, 3.6, 8.4_

- [x] 4.2 Integrate caching in all tools
  - [x] 4.2.1 Add cache check before Zemberek call
  - [x] 4.2.2 Store result after successful call
  - [x] 4.2.3 Add `cached` flag to responses
  - [x]* 4.2.4 Test cache integration
  - _Requirements: All tools (caching)_

### 5. Performance Optimization

- [x] 5.1 Optimize JVM initialization
  - [x] 5.1.1 Initialize JVM once at server startup
  - [x] 5.1.2 Reuse Zemberek instances across requests
  - [x] 5.1.3 Add connection pooling for thread safety
  - [x]* 5.1.4 Benchmark initialization time
  - _Requirements: 8.4, 8.5_

- [x] 5.2 Optimize API latency
  - [x] 5.2.1 Use async/await for all I/O
  - [x] 5.2.2 Implement request batching
  - [x] 5.2.3 Add response compression
  - [x] 5.2.4 Optimize cache key generation
  - [x]* 5.2.5 **Property 6: API Latency** - Verify < 10ms for cached ops
  - [x]* 5.2.6 Benchmark P50, P95, P99 latencies
  - _Requirements: 8.5_

### 6. Property-Based Testing

- [x]* 6.1 **Property 1: Morphological Analysis Completeness**
  - [x]* 6.1.1 Generate random Turkish words
  - [x]* 6.1.2 Verify all words get at least one analysis
  - **Validates: Requirements 1.1, 1.2, 1.3**

- [x]* 6.2 **Property 2: Lemmatization Consistency**
  - [x]* 6.2.1 Generate inflected Turkish words
  - [x]* 6.2.2 Verify same lemma regardless of call order
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x]* 6.3 **Property 3: Spell Check Accuracy**
  - [x]* 6.3.1 Use Turkish dictionary words
  - [x]* 6.3.2 Verify is_correct=True for all
  - **Validates: Requirements 3.1, 3.2, 3.5**

- [x]* 6.4 **Property 4: Tokenization Boundary Correctness**
  - [x]* 6.4.1 Generate random Turkish text
  - [x]* 6.4.2 Verify token concatenation = original text
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [x]* 6.5 **Property 5: Cache Consistency**
  - [x]* 6.5.1 Run same operation cached and non-cached
  - [x]* 6.5.2 Verify results match exactly
  - **Validates: Requirements 1.6, 2.6, 3.6**

- [x]* 6.6 **Property 6: API Latency**
  - [x]* 6.6.1 Measure cached operation latency
  - [x]* 6.6.2 Verify < 10ms for 99% of requests
  - **Validates: Requirements 3.6, 8.5**

### 7. MCP Integration Testing

- [x]* 7.1 Test with Claude Desktop
  - [x]* 7.1.1 Configure MCP server in Claude Desktop
  - [x]* 7.1.2 Test all 8 tools via Claude
  - [x]* 7.1.3 Verify Turkish text processing
  - [x]* 7.1.4 Verify error handling
  - _Requirements: All (integration)_

- [x]* 7.2 Test performance
  - [x]* 7.2.1 Test with 100 concurrent requests
  - [x]* 7.2.2 Verify P95 latency < 100ms
  - [x]* 7.2.3 Verify cache hit rate > 50%
  - _Requirements: 8.5_

### 8. Documentation

- [x] 8.1 Write user documentation
  - [x] 8.1.1 Installation guide (JPype, Zemberek JAR)
  - [x] 8.1.2 Configuration guide (MCP server setup)
  - [x] 8.1.3 Tool reference with examples
  - [x] 8.1.4 Troubleshooting guide (JVM issues)
  - _Requirements: All (documentation)_

- [x] 8.2 Write developer documentation
  - [x] 8.2.1 Architecture overview
  - [x] 8.2.2 Adding new tools guide
  - [x] 8.2.3 API reference
  - [x] 8.2.4 Performance tuning guide
  - _Requirements: All (developer docs)_

### 9. Deployment

- [x] 9.1 Package for distribution
  - [x] 9.1.1 Create `requirements_zemberek.txt`
  - [x] 9.1.2 Include Zemberek JAR in package
  - [x] 9.1.3 Create Docker image
  - [x] 9.1.4 Test installation
  - _Requirements: All (packaging)_

- [x] 9.2 Deploy MCP server
  - [x] 9.2.1 Configure server port and host
  - [x] 9.2.2 Set up systemd service
  - [x] 9.2.3 Configure logging
  - [x] 9.2.4 Monitor server health
  - _Requirements: All (deployment)_

**Checkpoint:** All tasks completed ✅

## Notes

**Constraints:**
- JVM must initialize successfully
- All operations must be async
- API latency < 100ms (P95)
- Turkish NLP accuracy >= 90%
- Cache hit rate > 50%

**Dependencies:**
- jpype1 (Java-Python bridge)
- zemberek-python
- fastapi
- pydantic 2.x
- aioredis
- uvicorn

**Testing Philosophy:**
- Unit tests for each tool
- Property tests for NLP correctness
- Integration tests with Claude Desktop
- Minimum 100 iterations per property test

## Success Metrics

1. **Morphological Analysis Accuracy:** >= 95%
2. **Spell Check Precision:** >= 90%
3. **Tokenization Accuracy:** >= 98%
4. **NER F1-Score:** >= 85%
5. **API Latency (P95):** < 100ms
6. **Cached Operation Latency:** < 10ms
7. **Cache Hit Rate:** > 50%

## Implementation Summary

**Completed by Claude Code on 2026-01-16:**

### Phase 1: JPype Bridge
- `bridge/jpype_bridge.py` - Thread-safe singleton JVM bridge
- `bridge/exceptions.py` - Custom exceptions
- `scripts/download_zemberek_jar.py` - JAR download script
- `config.py` - JPype configuration

### Phase 2: Tool Refactoring
- All 8 tools updated with `_call_jpype()` method
- JPype → HTTP fallback pattern implemented

### Phase 3-6: Testing
- Property-based tests (6 tests, 100+ iterations)
- Unit tests for bridge and tools
- Integration tests for MCP and concurrent load

### Phase 7: Documentation
- `README.md` - User documentation
- `DEVELOPMENT.md` - Developer guide

### Phase 8: Deployment
- `requirements_zemberek.txt`
- `Dockerfile.zemberek`
- `zemberek-mcp.service` (systemd)
- `docker-compose.zemberek.yml`

### Phase 9: Advanced Features
- `tools/entity_linker.py` - KB linking
- `training/` - NER trainer, Dictionary trainer
- `models/` - Pydantic schemas

### Phase 10: BPE Subword Tokenization (REQ-4.6) - Completed 2026-01-16
- `tools/bpe_tokenizer.py` - HuggingFace tokenizers + BERTurk integration
- `tokenization.py` updated with `use_subword` parameter
- `tool_schemas.py` updated with `subword_tokens` field
- `server.py` updated with `use_subword` parameter in zemberek_tokenize tool
- `test_bpe_tokenization.py` - Unit and property tests
