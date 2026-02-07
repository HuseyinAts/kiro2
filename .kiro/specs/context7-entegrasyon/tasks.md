# Implementation Tasks - Context7 Entegrasyonu

## Phase 1: Codebase Context Provider (REQ-1)

### 1.1 Setup Semantic Search
- [ ] 1.1.1 Install sentence-transformers>=2.3.0, tree-sitter>=0.20.0
- [ ] 1.1.2 Create mcp-servers/context7/providers/codebase.py
- [ ] 1.1.3 Load paraphrase-multilingual-mpnet-base-v2 model
- [ ] 1.1.4 Implement semantic_search() method
- [ ] 1.1.5 Add Turkish docstrings (Google style)
- [ ] 1.1.6 Add comprehensive type hints (Python 3.13+)

### 1.2 Implement AST Analysis
- [ ] 1.2.1 Setup tree-sitter parsers (Python, TypeScript, JavaScript)
- [ ] 1.2.2 Extract functions/classes from files
- [ ] 1.2.3 Calculate relevance score (embedding similarity)
- [ ] 1.2.4 Detect cross-references (imports, calls)

### 1.3 Implement Caching
- [ ] 1.3.1 Install redis>=5.0.0
- [ ] 1.3.2 Cache key: context7:code:{file_hash}
- [ ] 1.3.3 Set TTL: 1 hour (3600s)
- [ ] 1.3.4 Implement cache warming

### 1.4 Test Codebase Provider
- [ ] 1.4.1 Write unit test: test_semantic_search()
- [ ] 1.4.2 Write unit test: test_ast_extraction()
- [ ]* 1.4.3 Write property test: test_relevance_scoring() - Run 100+ iterations
- [ ] 1.4.4 Verify retrieval time < 500ms

## Phase 2: Git History Provider (REQ-2)

### 2.1 Implement Git Integration
- [ ] 2.1.1 Install gitpython>=3.1.40
- [ ] 2.1.2 Create mcp-servers/context7/providers/git_history.py
- [ ] 2.1.3 Implement get_commit_history() method
- [ ] 2.1.4 Parse conventional commits
- [ ] 2.1.5 Add Turkish docstrings (Google style)
- [ ] 2.1.6 Add comprehensive type hints (Python 3.13+)

### 2.2 Implement Git Blame
- [ ] 2.2.1 Implement get_blame() method
- [ ] 2.2.2 Extract author information
- [ ] 2.2.3 Track refactoring history (rename/move)
- [ ] 2.2.4 Filter bug fix commits

### 2.3 Test Git Provider
- [ ] 2.3.1 Write unit test: test_commit_parsing()
- [ ] 2.3.2 Write integration test: test_blame_tracking()
- [ ]* 2.3.3 Write property test: test_history_completeness() - Run 100+ iterations

## Phase 3-8: Remaining Providers
[Similar structure for Documentation, Dependency, Test, Issue/PR providers]

## Phase 9: Context Aggregator (REQ-7)

### 9.1 Implement Unified Ranking
- [ ] 9.1.1 Install numpy>=1.26.0
- [ ] 9.1.2 Create mcp-servers/context7/aggregator.py
- [ ] 9.1.3 Implement rank_contexts() method
- [ ] 9.1.4 Score: recency (0.3) + relevance (0.5) + authority (0.2)
- [ ] 9.1.5 Add Turkish docstrings (Google style)
- [ ] 9.1.6 Add comprehensive type hints (Python 3.13+)

### 9.2 Implement Deduplication
- [ ] 9.2.1 Calculate text similarity (cosine)
- [ ] 9.2.2 Remove duplicates (similarity > 0.95)
- [ ] 9.2.3 Merge metadata

### 9.3 Test Aggregator
- [ ] 9.3.1 Write unit test: test_ranking()
- [ ]* 9.3.2 Write property test: test_deduplication() - Run 100+ iterations
- [ ] 9.3.3 Verify aggregation time < 100ms

## Phase 10: MCP Server (REQ-8)

### 10.1 Create MCP Server
- [ ] 10.1.1 Install mcp>=0.9.0
- [ ] 10.1.2 Create mcp-servers/context7/server.py
- [ ] 10.1.3 Define tools: get_context, search_code, get_history
- [ ] 10.1.4 Add Turkish docstrings (Google style)
- [ ] 10.1.5 Add comprehensive type hints (Python 3.13+)

### 10.2 Implement Configuration
- [ ] 10.2.1 Read .mcp.json config
- [ ] 10.2.2 Validate required fields
- [ ] 10.2.3 Load API keys from environment
- [ ] 10.2.4 Setup rate limiting (exponential backoff)

### 10.3 Test MCP Server
- [ ] 10.3.1 Write integration test: test_get_context()
- [ ] 10.3.2 Write integration test: test_health_check()
- [ ]* 10.3.3 Write property test: test_source_coverage() - Run 100+ iterations
- [ ] 10.3.4 Verify all 7 sources active

## Success Criteria
- [ ] Context relevance >= 90%
- [ ] Retrieval time < 500ms
- [ ] Cache hit rate >= 70%
- [ ] Source coverage = 7/7
- [ ] AI response quality improvement >= 300%
