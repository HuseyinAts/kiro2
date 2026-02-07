# Design Document - Context7 Entegrasyonu

## Architecture Overview

Context7 MCP server entegrasyonu: 7 kaynaklı (codebase, git, docs, deps, tests, issues, PRs) context aggregation. Semantic search + unified ranking ile %400 context kalitesi artışı sağlar.

## Components

### 1. Codebase Context Provider (mcp-servers/context7/providers/codebase.py)
- **Purpose**: Kod dosyalarından relevant context extraction
- **Dependencies**: sentence-transformers>=2.3.0, tree-sitter>=0.20.0
- **Key Features**:
  - Semantic search (embedding similarity)
  - AST analysis (function/class extraction)
  - Cross-reference detection
  - Redis cache (TTL: 1h)

### 2. Git History Provider (mcp-servers/context7/providers/git_history.py)
- **Purpose**: Commit history ve blame bilgisi
- **Dependencies**: gitpython>=3.1.40
- **Key Features**:
  - Commit log parsing
  - Conventional commit analysis
  - Git blame (author tracking)
  - Refactoring history (rename/move)
  - Bug fix filtering
  - Major changes highlighting

### 3. Documentation Provider (mcp-servers/context7/providers/documentation.py)
- **Purpose**: Proje dokümantasyonu
- **Dependencies**: markdown>=3.5.0
- **Key Features**:
  - README, docs/ scanning
  - Markdown parsing (heading hierarchy)
  - Code example extraction
  - OpenAPI spec prioritization
  - Tutorial formatting
  - Outdated docs detection

### 4. Dependency Provider (mcp-servers/context7/providers/dependency.py)
- **Purpose**: Library dokümantasyonu
- **Dependencies**: requests>=2.31.0
- **Key Features**:
  - requirements.txt/package.json parsing
  - PyPI/npm docs fetching
  - Version-specific docs
  - Migration guides
  - Alternative library comparison
  - Security advisory warnings

### 5. Test Context Provider (mcp-servers/context7/providers/test_context.py)
- **Purpose**: Test dosyalarından usage examples
- **Dependencies**: pytest>=7.4.0
- **Key Features**:
  - tests/ directory scanning
  - Setup/teardown extraction
  - Fixture definition inclusion
  - Mock configuration
  - Edge case highlighting
  - Missing test suggestions

### 6. Issue/PR Provider (mcp-servers/context7/providers/github_context.py)
- **Purpose**: GitHub issue/PR context
- **Dependencies**: pygithub>=2.1.0
- **Key Features**:
  - GitHub API integration
  - Issue title/body/comments
  - Code review comments
  - Reproduction steps
  - Discussion summaries
  - Resolution explanations

### 7. Context Aggregator (mcp-servers/context7/aggregator.py)
- **Purpose**: 7 kaynağı birleştirme ve ranking
- **Dependencies**: numpy>=1.26.0
- **Key Features**:
  - Unified ranking (recency + relevance + authority)
  - Top-k selection
  - Deduplication
  - Key points extraction
  - Quality scoring (completeness + accuracy)

### 8. MCP Server (mcp-servers/context7/server.py)
- **Purpose**: Context7 MCP server
- **Dependencies**: mcp>=0.9.0
- **Key Features**:
  - .mcp.json config
  - API key management
  - Rate limiting (exponential backoff)
  - Health check (7 sources)
  - Graceful degradation

## Data Flow

```
Query → Context7 MCP Server → 7 Providers (parallel)
                                    ↓
                              Aggregator
                                    ↓
                            Unified Ranking
                                    ↓
                              Top-K Selection
                                    ↓
                            Formatted Context
```

## Correctness Properties

### Property 1: Source Coverage
```python
@given(query=st.text(min_size=1))
def test_source_coverage(query):
    context = context7.get_context(query)
    assert len(context['sources']) == 7
```

### Property 2: Ranking Consistency
```python
@given(contexts=st.lists(st.dictionaries(keys=st.sampled_from(['score']), values=st.floats())))
def test_ranking_consistency(contexts):
    ranked = aggregator.rank(contexts)
    scores = [c['score'] for c in ranked]
    assert scores == sorted(scores, reverse=True)
```

### Property 3: Deduplication
```python
@given(text=st.text())
def test_deduplication(text):
    contexts = [{'text': text}, {'text': text}]
    deduplicated = aggregator.deduplicate(contexts)
    assert len(deduplicated) == 1
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Context retrieval | < 500ms | < 1s |
| Cache hit rate | >= 70% | >= 50% |
| Source availability | 7/7 | >= 5/7 |
| Context relevance | >= 90% | >= 80% |

## Security Considerations

- API key encryption
- Rate limiting (exponential backoff)
- Input sanitization
- GitHub token management

## Monitoring

- Context retrieval time (P50, P95, P99)
- Cache hit rate (%)
- Source availability (count)
- Context relevance score (%)
- AI response quality improvement (%)
