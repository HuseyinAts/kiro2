# Structured Logging Migration Guide

Complete guide for migrating from primitive logging to structured logging with `structlog`.

## 📋 Table of Contents

- [Why Structured Logging?](#why-structured-logging)
- [Quick Start](#quick-start)
- [Migration Patterns](#migration-patterns)
- [Common Use Cases](#common-use-cases)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## 🎯 Why Structured Logging?

### Problems with Current Logging

```python
# ❌ Primitive logging - Hard to parse, search, and monitor
print(f"Error: {e}")
logger.info(f"User {user_id} logged in from {ip}")
logger.error(f"Database error: {str(e)}")
```

**Issues:**
- No structured data for filtering/aggregation
- String concatenation is slow and error-prone
- Cannot query by specific fields
- No automatic sensitive data censoring
- Difficult to integrate with monitoring tools (Elasticsearch, Datadog, etc.)

### Benefits of Structured Logging

```python
# ✅ Structured logging - Machine-readable, queryable, secure
logger.info(
    "user_login",
    user_id=user_id,
    ip_address=ip,
    success=True,
    timestamp=datetime.utcnow().isoformat()
)
```

**Benefits:**
- **Queryable**: Filter logs by `user_id`, `status_code`, `duration_ms`, etc.
- **Performant**: No string formatting overhead
- **Secure**: Automatic censoring of passwords, tokens, secrets
- **Observable**: Easy integration with ELK, Datadog, Grafana, CloudWatch
- **Consistent**: Standard format across all services
- **Contextual**: Add request_id, user_id to all logs automatically

---

## 🚀 Quick Start

### 1. Import the Logger

```python
from core.structured_logger import get_logger, log_exam_event

logger = get_logger(__name__)
```

### 2. Basic Usage

```python
# Old way ❌
print(f"Processing user {user_id}")
logger.info(f"Exam {exam_id} created by {user_id}")

# New way ✅
logger.info("processing_user", user_id=user_id)
logger.info(
    "exam_created",
    exam_id=exam_id,
    user_id=user_id,
    exam_type="tyt"
)
```

### 3. Error Logging

```python
# Old way ❌
try:
    result = do_something()
except Exception as e:
    logger.error(f"Error: {e}")
    print(f"Failed: {str(e)}")

# New way ✅
try:
    result = do_something()
except Exception as e:
    logger.exception(
        "operation_failed",
        operation="do_something",
        error_type=type(e).__name__,
        user_id=user_id
    )
```

---

## 🔄 Migration Patterns

### Pattern 1: Simple Print Statements

```python
# Before ❌
print("Starting server...")
print(f"User {user_id} logged in")
print(f"Error: {error}")

# After ✅
logger.info("server_starting")
logger.info("user_login", user_id=user_id)
logger.error("operation_error", error_message=str(error))
```

### Pattern 2: F-String Logging

```python
# Before ❌
logger.info(f"Processing exam {exam_id} for student {student_id}")
logger.error(f"Database error in {function_name}: {str(e)}")

# After ✅
logger.info(
    "processing_exam",
    exam_id=exam_id,
    student_id=student_id
)
logger.error(
    "database_error",
    function=function_name,
    error_type=type(e).__name__,
    error_message=str(e)
)
```

### Pattern 3: Exception Handling

```python
# Before ❌
try:
    result = perform_operation()
except ValueError as e:
    logger.error(f"Validation error: {e}")
except DatabaseError as e:
    logger.error(f"DB error: {e}")

# After ✅
try:
    result = perform_operation()
except ValueError as e:
    logger.exception(
        "validation_error",
        operation="perform_operation",
        input_data=safe_repr(input_data)
    )
except DatabaseError as e:
    logger.exception(
        "database_error",
        operation="perform_operation",
        table=table_name
    )
```

### Pattern 4: Contextual Logging (Recommended)

```python
# Bind context once, available in all subsequent logs
logger_with_context = logger.bind(
    request_id=request_id,
    user_id=user_id,
    session_id=session_id
)

# All logs now include context automatically
logger_with_context.info("operation_start")
logger_with_context.info("data_validated", item_count=len(items))
logger_with_context.info("operation_complete", duration_ms=elapsed)
```

---

## 💡 Common Use Cases

### 1. Exam Events

```python
from core.structured_logger import get_logger, log_exam_event

logger = get_logger(__name__)

# Old ❌
print(f"Sınav {sinav_id} oluşturuldu")
logger.info(f"Student {ogrenci_id} started exam {sinav_id}")

# New ✅
log_exam_event(
    logger,
    event_type="sinav_olusturuldu",
    sinav_id=sinav_id,
    ogrenci_id=ogrenci_id,
    sinav_tipi="tyt",
    soru_sayisi=40,
    sure_dakika=120
)

log_exam_event(
    logger,
    event_type="sinav_basladi",
    sinav_id=sinav_id,
    ogrenci_id=ogrenci_id
)
```

### 2. API Requests/Responses

```python
from core.structured_logger import log_api_request, log_api_response
import time

# Log request
log_api_request(
    logger,
    method="POST",
    path="/api/v1/exams",
    user_id=current_user.id,
    ip_address=request.client.host
)

start_time = time.time()
response = process_request()
duration_ms = (time.time() - start_time) * 1000

# Log response
log_api_response(
    logger,
    method="POST",
    path="/api/v1/exams",
    status_code=201,
    duration_ms=duration_ms,
    exam_id=response.id
)
```

### 3. Database Operations

```python
from core.structured_logger import log_database_query
import time

# Old ❌
logger.debug(f"Querying table {table_name}")
logger.debug(f"Query took {elapsed}ms")

# New ✅
start = time.time()
result = await db.execute(query)
duration_ms = (time.time() - start) * 1000

log_database_query(
    logger,
    operation="SELECT",
    table="kullanicilar",
    duration_ms=duration_ms,
    row_count=len(result),
    filters={"sinif": "12"}
)
```

### 4. Cache Operations

```python
from core.structured_logger import log_cache_operation

# Cache hit
log_cache_operation(
    logger,
    operation="get",
    cache_key=f"user:{user_id}",
    hit=True,
    ttl_seconds=3600
)

# Cache miss
log_cache_operation(
    logger,
    operation="get",
    cache_key=f"exam:{exam_id}",
    hit=False
)

# Cache set
log_cache_operation(
    logger,
    operation="set",
    cache_key=f"exam:{exam_id}",
    size_bytes=len(data)
)
```

### 5. Performance Monitoring

```python
import time

# Monitor function performance
def monitored_function():
    logger.info("function_start", function="monitored_function")

    start = time.time()
    try:
        result = expensive_operation()
        duration_ms = (time.time() - start) * 1000

        logger.info(
            "function_complete",
            function="monitored_function",
            duration_ms=duration_ms,
            result_count=len(result)
        )
        return result

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        logger.exception(
            "function_failed",
            function="monitored_function",
            duration_ms=duration_ms
        )
        raise
```

### 6. User Actions

```python
# Login
logger.info(
    "user_login",
    user_id=user.id,
    email=user.email,
    ip_address=ip,
    user_agent=user_agent,
    success=True
)

# Logout
logger.info(
    "user_logout",
    user_id=user.id,
    session_duration_minutes=session_duration
)

# Failed login
logger.warning(
    "login_failed",
    email=email,
    ip_address=ip,
    reason="invalid_password",
    attempt_count=attempt_count
)
```

---

## ✅ Best Practices

### 1. Use Meaningful Event Names

```python
# Bad ❌
logger.info("event")
logger.info("error")

# Good ✅
logger.info("user_registration_complete")
logger.error("database_connection_failed")
```

### 2. Include Relevant Context

```python
# Minimal ❌
logger.info("exam_created")

# Rich context ✅
logger.info(
    "exam_created",
    exam_id=exam.id,
    student_id=student.id,
    exam_type=exam.type,
    question_count=len(exam.questions),
    duration_minutes=exam.duration,
    created_by=teacher.id
)
```

### 3. Use Consistent Field Names

```python
# Inconsistent ❌
logger.info("event1", userId=123)
logger.info("event2", user_id=123)
logger.info("event3", uid=123)

# Consistent ✅
logger.info("event1", user_id=123)
logger.info("event2", user_id=123)
logger.info("event3", user_id=123)
```

### 4. Log at Appropriate Levels

```python
# DEBUG: Detailed diagnostic info
logger.debug("cache_lookup", key=cache_key, hit=True)

# INFO: General informational messages
logger.info("exam_submitted", exam_id=exam_id, score=85)

# WARNING: Something unexpected but handled
logger.warning("slow_query", duration_ms=2500, query=query_name)

# ERROR: Error that needs attention
logger.error("payment_failed", order_id=order_id, error=str(e))

# CRITICAL: System-level failure
logger.critical("database_unavailable", retry_count=max_retries)
```

### 5. Avoid Logging Sensitive Data

```python
# Automatically censored by structured_logger
logger.info(
    "user_auth",
    user_id=user.id,
    password="secret123",  # Automatically becomes "***REDACTED***"
    token="Bearer abc123",  # Automatically becomes "***REDACTED***"
    email=user.email  # Safe to log
)
```

### 6. Use Binding for Request Context

```python
# In middleware or request handler
request_logger = logger.bind(
    request_id=request_id,
    user_id=current_user.id,
    ip_address=request.client.host
)

# All subsequent logs include this context
request_logger.info("request_received", path=request.url.path)
request_logger.info("validation_passed", data_size=len(data))
request_logger.info("request_processed", duration_ms=elapsed)
```

---

## 📊 Querying Structured Logs

### In Elasticsearch

```json
// Find all failed login attempts for a user
{
  "query": {
    "bool": {
      "must": [
        { "match": { "event": "login_failed" }},
        { "term": { "user_id": 123 }}
      ]
    }
  }
}

// Find slow database queries
{
  "query": {
    "bool": {
      "must": [
        { "match": { "event": "database_query" }},
        { "range": { "duration_ms": { "gte": 1000 }}}
      ]
    }
  }
}

// Calculate average API response time
{
  "aggs": {
    "avg_duration": {
      "avg": { "field": "duration_ms" }
    }
  },
  "query": {
    "match": { "event": "api_response" }
  }
}
```

### In DataDog

```
// Count exam submissions by type
event:exam_submitted | count by exam_type

// Alert on high error rate
event:error_occurred | count | rate > 10/min

// Track p95 response time
event:api_response | p95(duration_ms) by path
```

---

## ❓ FAQ

### Q: Do I need to update all logs at once?

No! The new `StructuredLogger` is **backward compatible**:

```python
# Old API still works
logger.info("message", extra={"user_id": 123})

# New API preferred
logger.info("event_name", user_id=123)
```

### Q: How do I migrate a file?

1. Replace `import logging` with `from core.structured_logger import get_logger`
2. Replace `logger = logging.getLogger(__name__)` with `logger = get_logger(__name__)`
3. Update log calls to use structured format
4. Test the file

### Q: What about performance?

Structured logging with `structlog` is **faster** than f-string formatting:

```python
# Slow: String formatting happens even if log level filtered
logger.debug(f"User {user_id} data: {expensive_function()}")

# Fast: Only evaluated if debug level enabled
logger.debug("user_data", user_id=user_id, data=expensive_function())
```

### Q: How do I add request context globally?

Use middleware to bind context:

```python
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_logger = logger.bind(
        request_id=str(uuid.uuid4()),
        path=request.url.path,
        method=request.method
    )

    # Store in request state
    request.state.logger = request_logger

    response = await call_next(request)
    return response

# In route handlers
def my_route(request: Request):
    request.state.logger.info("route_accessed")
```

---

## 🎯 Migration Checklist

- [ ] Replace `print()` statements with structured logging
- [ ] Update `logger.info(f"...")` to `logger.info("event", ...)`
- [ ] Add structured data to error logs
- [ ] Use helper functions (`log_exam_event`, etc.) where applicable
- [ ] Remove string concatenation in logs
- [ ] Add timestamps with `datetime.utcnow().isoformat()`
- [ ] Use log levels appropriately (DEBUG, INFO, WARNING, ERROR)
- [ ] Add request context binding in middleware
- [ ] Test log output format (JSON in production)
- [ ] Update monitoring/alerting queries to use structured fields

---

## 📚 Additional Resources

- [Structlog Documentation](https://www.structlog.org/)
- [Twelve-Factor App Logging](https://12factor.net/logs)
- [Logging Best Practices](https://www.loggly.com/ultimate-guide/python-logging-best-practices/)
- Internal: [core/structured_logger.py](../core/structured_logger.py)

---

**Need Help?** Contact the backend team or create an issue in the project repo.
