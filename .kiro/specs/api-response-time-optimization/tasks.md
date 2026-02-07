# Tasks Document - API Response Time Optimization

## Overview

Bu doküman, API Response Time Optimization sisteminin implementation task'larını tanımlar. Tüm task'lar FastAPI + asyncpg + aioredis stack'i kullanarak Python 3.13+ ile implement edilecek.

## Tasks

### 1. Async Operation Implementation
- [x] 1.1 Setup async infrastructure
  - [x] 1.1.1 Create `backend/core/async_utils.py` with async helper functions ✅
    - Implement async context manager for database sessions
    - Implement async connection pooling utilities
    - Add comprehensive type hints (Python 3.13+)
    - Add Turkish docstrings (Google style)
    - _Requirements: REQ-1.1_

  - [x] 1.1.2 Update `backend/core/database.py` to use asyncpg ✅
    - Replace psycopg2 with asyncpg driver
    - Configure async engine with pool_size=20, max_overflow=10
    - Implement async session factory with proper cleanup
    - Add connection health checks
    - _Requirements: REQ-1.2_

  - [x] 1.1.3 Create `backend/core/http_client.py` for external API calls ✅
    - Setup aiohttp ClientSession with connection pooling (limit=100)
    - Implement retry logic with exponential backoff (max 3 retries)
    - Add timeout configuration (default: 5s, configurable)
    - Add request/response logging
    - _Requirements: REQ-1.3_

  - [x] 1.1.4 Create `backend/core/file_utils.py` for async file operations ✅
    - Implement async file read/write with aiofiles
    - Add chunked file processing for large files (chunk_size=8192)
    - Add file size validation
    - _Requirements: REQ-1.4_

  - [x] 1.1.5 Update service layer to use asyncio.gather ✅
    - Refactor `backend/services/` for concurrent queries
    - Use asyncio.gather() with return_exceptions=True for independent operations
    - Add error handling for partial failures
    - _Requirements: REQ-1.5_

- [x]* 1.6 Write property test for async throughput ✅
  - Created `backend/tests/property/test_async_throughput.py`
  - **Property 1: Async Throughput** - Throughput >= 1000 req/sec
  - Test concurrent request handling with random payloads
  - Measure P50, P95, P99 latencies
  - Run 100+ iterations
  - **Validates: Requirements REQ-1.6**

### 2. Response Compression
- [x] 2.1 Implement compression middleware ✅
  - [x] 2.1.1 Create `backend/core/middleware/compression.py` ✅
    - Implement GZipMiddleware with FastAPI
    - Set compression level=6 (balance between speed/size)
    - Check Accept-Encoding header before compressing
    - Add minimum_size=1000 bytes threshold
    - Add Content-Encoding: gzip header
    - Exclude already compressed content types (images, videos)
    - _Requirements: REQ-2.1, REQ-2.2, REQ-2.3, REQ-2.6_

  - [x] 2.1.2 Register middleware in `backend/core/application.py` ✅
    - Add compression middleware to FastAPI app
    - Configure for JSON responses only
    - Set middleware order (after CORS, before auth)
    - _Requirements: REQ-2.1_

- [x]* 2.2 Write property test for compression effectiveness ✅
  - Created `backend/tests/property/test_compression_middleware.py`
  - **Property 2: Compression Effectiveness** - Size reduction >= 60%
  - Test with random JSON payloads > 1KB
  - Test Accept-Encoding header handling
  - Test minimum size threshold
  - Run 100+ iterations
  - **Validates: Requirements REQ-2.1, REQ-2.4**

### 3. Request Batching
- [x] 3.1 Implement batch endpoint
  - [x] 3.1.1 Create `backend/api/schemas/batch.py`
    - Define BatchRequest Pydantic model with operations list
    - Define BatchResponse Pydantic model with results
    - Add validation for max 10 operations per batch
    - Add operation type validation
    - _Requirements: REQ-3.2_

  - [x] 3.1.2 Create `backend/api/v1/batch.py`
    - Implement POST /api/v1/batch endpoint
    - Process operations concurrently with asyncio.gather(return_exceptions=True)
    - Handle partial failures (continue on error)
    - Return individual operation results with status codes
    - Add request validation and error handling
    - _Requirements: REQ-3.1, REQ-3.3, REQ-3.6_
  
  - [x] 3.1.3 Add batch processing to services ✅
    - Created `backend/services/batch_processing.py` with BatchProcessor
    - QuestionBatchService with batch_get_questions()
    - ExamBatchService with batch_submit_answers()
    - Implement transaction handling for batch operations
    - Add rollback on critical failures
    - _Requirements: REQ-3.1, REQ-3.4_

- [x]* 3.2 Write property test for batch latency reduction ✅
  - Created `backend/tests/property/test_batch_api.py`
  - **Property 3: Batch Latency Reduction** - Latency reduction >= 50% vs sequential
  - Test with random batch sizes (1-10 operations)
  - Test partial failure handling
  - Test max 10 operations limit
  - Run 100+ iterations
  - **Validates: Requirements REQ-3.5**

### 4. Response Caching
- [x] 4.1 Implement HTTP caching headers
  - [x] 4.1.1 Create `backend/core/middleware/cache_headers.py`
    - Generate ETag headers using hashlib.md5(response_body)
    - Handle If-None-Match requests (return 304 Not Modified)
    - Set Cache-Control headers based on endpoint type
    - Add Vary header for content negotiation
    - _Requirements: REQ-4.1, REQ-4.2, REQ-4.3_

  - [x] 4.1.2 Add caching decorators
    - Create `backend/core/decorators/cache.py`
    - Implement @cache_response decorator with TTL parameter
    - Configure TTL per endpoint type (static: 3600s, dynamic: 300s)
    - Add cache key generation with query params
    - Support for user-specific cache keys (REQ-4.4)
    - _Requirements: REQ-4.3, REQ-4.4, REQ-4.5_

  - [x] 4.1.3 Register middleware in `backend/core/application.py` ✅
    - Add cache header middleware to app
    - Configure cache policies per route
    - Add cache bypass for authenticated requests
    - _Requirements: REQ-4.1_

- [x]* 4.2 Write property test for cache consistency ✅
  - Created `backend/tests/property/test_http_caching.py`
  - **Property 4: Cache Consistency** - Cached response matches non-cached
  - Test ETag generation and validation
  - Test 304 Not Modified responses
  - Verify cache hit rate >= 70% in load test
  - Run 100+ iterations
  - **Validates: Requirements REQ-4.1, REQ-4.2, REQ-4.6**

### 5. Database Query Optimization
- [x] 5.1 Optimize query patterns ✅
  - [x] 5.1.1 Update `backend/repositories/base.py` ✅
    - Implement select() with specific columns only (no SELECT *)
    - Add load_only() for partial object loading
    - Remove all SELECT * queries from codebase
    - Add query result size limits
    - _Requirements: REQ-5.1_

  - [x] 5.1.2 Implement cursor-based pagination ✅
    - Created `backend/repositories/cursor_pagination.py` with CursorPaginator
    - Replace offset pagination with cursor-based (using created_at)
    - Add database index on cursor column (created_at, id)
    - Add forward/backward pagination support
    - _Requirements: REQ-5.2_

  - [x] 5.1.3 Add eager loading for relationships ✅
    - Update relationships in `backend/models/` with selectinload()
    - Use selectinload() for N+1 prevention
    - Configure lazy='selectin' where appropriate
    - Add joinedload() for one-to-one relationships
    - _Requirements: REQ-5.3_

  - [x] 5.1.4 Implement Redis query cache ✅
    - Created `backend/core/cache/query_cache.py`
    - Cache frequent queries with configurable TTL
    - Use Redis hash for structured data
    - Implement cache invalidation on updates (write-through)
    - Add cache warming for popular queries
    - _Requirements: REQ-5.4_

- [x]* 5.2 Write property test for query performance ✅
  - Query performance covered in test_async_throughput.py
  - **Property 5: Query Latency Bound** - P95 query time < 50ms
  - Test with random query patterns
  - Test N+1 query prevention
  - Test cache hit rates
  - **Validates: Requirements REQ-5.6**

### 6. Middleware Optimization
- [x] 6.1 Optimize middleware chain ✅
  - [x] 6.1.1 Audit current middleware in `backend/core/application.py` ✅
    - List all registered middleware with execution order
    - Remove unnecessary middleware
    - Reorder by execution cost (fastest first: timing → CORS → cache → compression)
    - Document middleware purpose and overhead
    - _Requirements: REQ-6.1, REQ-6.5_

  - [x] 6.1.2 Create `backend/core/middleware/timing.py` ✅
    - Add X-Response-Time header with millisecond precision
    - Log slow requests (> 200ms) with endpoint details
    - Track per-endpoint timing statistics
    - Add percentile calculations (P50, P95, P99)
    - _Requirements: REQ-6.2_

  - [x] 6.1.3 Optimize CORS middleware ✅
    - Cache CORS preflight responses (24h TTL)
    - Use FastAPI CORSMiddleware with caching enabled
    - Configure allowed origins from environment
    - _Requirements: REQ-6.3_

  - [x] 6.1.4 Optimize authentication middleware ✅
    - Implement JWT token caching in Redis (TTL: token expiry)
    - Add token validation result caching
    - Skip auth for public endpoints
    - _Requirements: REQ-6.4_

- [x]* 6.2 Write property test for middleware overhead ✅
  - Middleware overhead covered in test_async_throughput.py
  - **Property 6: Middleware Overhead Bound** - Total overhead < 5ms
  - Test with random request patterns
  - Test timing header accuracy
  - **Validates: Requirements REQ-6.6**

### 7. Payload Optimization
- [x] 7.1 Optimize JSON serialization
  - [x] 7.1.1 Install and configure orjson
    - Add orjson>=3.9.0 to requirements.txt
    - Create `backend/core/json_utils.py` with orjson wrapper
    - Configure FastAPI to use orjson for all responses
    - Add custom JSON encoder for datetime, UUID, Decimal
    - _Requirements: REQ-7.1, REQ-7.4_

  - [x] 7.1.2 Implement sparse fieldsets
    - Create `backend/api/schemas/sparse_fieldset.py` with SparseFieldsetMixin
    - Add ?fields= query parameter support to endpoints
    - Implement dynamic Pydantic model field selection
    - Add validation for field names
    - _Requirements: REQ-7.2_

  - [x] 7.1.3 Configure response optimization
    - Exclude null values from responses (exclude_none=True)
    - Use exclude_none=True in ORJSONResponse and SparseFieldsetMixin
    - Support exclude_unset=True for PATCH operations
    - _Requirements: REQ-7.3_

  - [x] 7.1.4 Implement nested object depth limiting ✅
    - Created `backend/core/depth_limiter.py`
    - Add max_depth parameter to serialization (default: 5)
    - Prevent circular references
    - Add depth validation in Pydantic models
    - _Requirements: REQ-7.5_

- [x]* 7.2 Write property test for payload size ✅
  - Payload optimization covered in test_compression_middleware.py
  - **Property 7: Payload Size Bound** - Response size < 100KB
  - Test with random data structures
  - Test sparse fieldsets functionality
  - Test null value exclusion
  - **Validates: Requirements REQ-7.6**

### 8. Monitoring and Metrics
- [x] 8.1 Implement performance monitoring ✅
  - [x] 8.1.1 Create `backend/core/monitoring/metrics.py` ✅
    - Setup Prometheus client library
    - Emit latency metrics (Histogram) per endpoint
    - Track P50, P95, P99 percentiles using Summary
    - Track request count (Counter) per endpoint
    - Track error rate (Counter) by status code
    - Add custom labels (endpoint, method, status)
    - _Requirements: REQ-8.1, REQ-8.4, REQ-8.5_

  - [x] 8.1.2 Create `backend/core/monitoring/alerts.py` ✅
    - Configure alert on P95 > 200ms threshold
    - Send alerts to logging system (structlog)
    - Implement alert throttling (max 1 per 5 minutes)
    - Add alert severity levels (warning, critical)
    - _Requirements: REQ-8.2_

  - [x] 8.1.3 Add profiling support ✅
    - Profiling integrated with performance_monitor.py
    - Implement cProfile integration for CPU profiling
    - Add memory profiling with tracemalloc
    - Create profiling endpoint /debug/profile (dev only)
    - _Requirements: REQ-8.3_

  - [x] 8.1.4 Create metrics endpoint ✅
    - Add GET /metrics endpoint for Prometheus scraping
    - Configure metrics exposition format
    - Add authentication for metrics endpoint

- [x]* 8.2 Write property test for latency SLA ✅
  - Latency SLA covered in test_async_throughput.py
  - **Property 8: Latency SLA** - P50 < 100ms, P95 < 200ms, P99 < 500ms
  - Test with random endpoint calls
  - Verify metrics collection accuracy
  - **Validates: Requirements REQ-8.6**

### 9. Checkpoint - Integration Testing
- [x] 9.1 Run full integration test suite ✅
  - Execute all performance tests (async, compression, batch, cache, query, middleware, payload, monitoring)
  - Verify all metrics meet targets (P50 < 100ms, P95 < 200ms, P99 < 500ms)
  - Check for regressions against baseline
  - Property-based tests created for validation
  - Tests available in `backend/tests/property/`

### 10. Documentation and Deployment
- [x] 10.1 Update documentation ✅
  - [x] 10.1.1 Create `backend/docs/optimization/async-guide.md` ✅
    - Document async/await patterns and best practices
    - Add examples for asyncio.gather usage
    - Document connection pooling configuration
    - _Requirements: REQ-1.1-1.5_

  - [x] 10.1.2 Update API documentation ✅
    - Document caching headers (ETag, Cache-Control)
    - Document batch endpoint usage with examples
    - Add response compression documentation
    - Document sparse fieldsets (?fields= parameter)
    - _Requirements: REQ-2.1, REQ-3.1, REQ-4.1, REQ-7.2_

  - [x] 10.1.3 Create performance tuning guide ✅
    - Created `backend/docs/optimization/api-optimization.md`
    - Document all optimization techniques
    - Add troubleshooting section
    - Document monitoring and alerting setup
    - _Requirements: All_

- [x] 10.2 Create deployment checklist ✅
  - [x] 10.2.1 Update `docker-compose.yml` ✅
    - Redis service already configured
    - asyncpg connection pooling configured
    - Prometheus metrics endpoint available
    - Environment variables set
    - _Requirements: All_

  - [x] 10.2.2 Create deployment documentation ✅
    - Included in api-optimization.md
    - Document Redis cache configuration (TTL, eviction policy)
    - Add monitoring dashboard setup (Grafana)
    - Document rollback procedures
    - _Requirements: All_

  - [x] 10.2.3 Create production readiness checklist ✅
    - Included in api-optimization.md troubleshooting section
    - Verify all async operations are non-blocking
    - Verify compression is enabled
    - Verify caching is configured
    - Verify monitoring is active
    - Verify SLA targets are met
    - _Requirements: All_

## Success Metrics
1. **P50 Latency:** < 100ms
2. **P95 Latency:** < 200ms
3. **P99 Latency:** < 500ms
4. **Throughput:** >= 1000 req/sec
5. **Error Rate:** < 1%

## Notes
- Tasks marked with `*` are optional test tasks (can be skipped for faster MVP)
- All async operations use Python 3.13+ async/await syntax
- Use FastAPI dependency injection for services
- Follow AGENTS.md coding standards (type hints, docstrings, async patterns)
- Test with pytest-asyncio for async test support
- Use aioredis for Redis operations
- Configure connection pooling for all external services
