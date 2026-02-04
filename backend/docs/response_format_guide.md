# API Response Format Standardization Guide

## Overview

This guide documents the standardized API response format implemented across all endpoints in the Türkiye Üniversite Sınavları Hazırlık Platformu (Turkish University Exam Preparation Platform). The standardization ensures consistent, predictable, and well-structured responses for all client interactions.

## 🎯 Key Benefits

- **Consistency**: All endpoints follow the same response structure
- **Predictability**: Clients can reliably parse and handle responses
- **Error Handling**: Comprehensive and standardized error information
- **Internationalization**: Built-in Turkish language support
- **Debugging**: Request tracing and metadata for troubleshooting
- **API Evolution**: Version-aware responses for future compatibility

## 📋 Standard Response Structure

### Base Response Format

```json
{
  "success": boolean,
  "status": "success" | "error" | "warning" | "info",
  "message": "Human-readable status message in Turkish",
  "data": any | null,
  "errors": ErrorDetail[] | null,
  "meta": {
    "timestamp": "ISO 8601 timestamp",
    "request_id": "unique request identifier",
    "api_version": "API version",
    "processing_time_ms": number
  }
}
```

### Response Types

#### 1. Success Response

Used for successful operations that return data:

```json
{
  "success": true,
  "status": "success",
  "message": "İşlem başarıyla tamamlandı",
  "data": {
    "id": "user_12345",
    "username": "ahmet_ozkan",
    "email": "ahmet@example.com",
    "role": "student"
  },
  "errors": null,
  "meta": {
    "timestamp": "2025-01-25T10:30:00Z",
    "request_id": "req_abc123",
    "api_version": "v1",
    "processing_time_ms": 45.2
  }
}
```

#### 2. Error Response

Used for failed operations with detailed error information:

```json
{
  "success": false,
  "status": "error", 
  "message": "İstenen kaynak bulunamadı",
  "data": null,
  "errors": [
    {
      "code": "not_found_error",
      "message": "Kullanıcı ID 'user_999' bulunamadı",
      "field": null,
      "details": {
        "resource_type": "user",
        "resource_id": "user_999"
      }
    }
  ],
  "meta": {
    "timestamp": "2025-01-25T10:30:00Z",
    "request_id": "req_xyz789",
    "api_version": "v1",
    "processing_time_ms": 23.1
  }
}
```

#### 3. Paginated Response

Used for list operations with pagination:

```json
{
  "success": true,
  "status": "success",
  "message": "Veriler başarıyla getirildi",
  "data": [
    {"id": "q_001", "question_text": "2 + 2 = ?", "subject": "Matematik"},
    {"id": "q_002", "question_text": "Türkiye'nin başkenti?", "subject": "Coğrafya"}
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 147,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  },
  "meta": {
    "timestamp": "2025-01-25T10:30:00Z",
    "request_id": "req_page123",
    "api_version": "v1",
    "processing_time_ms": 89.4
  }
}
```

## 🔧 Implementation

### Using Response Builder

The `ResponseBuilder` class provides a fluent API for constructing responses:

```python
from backend.core.response_models import ResponseBuilder, ErrorType, ErrorDetail

# Success response
response = (ResponseBuilder()
           .success("Kullanıcı başarıyla oluşturuldu")
           .with_data(user_data)
           .with_meta(request_id=request_id, processing_time_ms=45.2)
           .build())

# Error response
error_detail = ErrorDetail(
    code=ErrorType.VALIDATION_ERROR.value,
    message="E-posta formatı geçersiz",
    field="email"
)

response = (ResponseBuilder()
           .error("Veri doğrulama hatası")
           .with_errors([error_detail])
           .with_meta(request_id=request_id)
           .build())

# Paginated response
response = (ResponseBuilder()
           .success("Sorular listelendi")
           .with_data(questions)
           .with_pagination(page=1, page_size=20, total_items=147)
           .with_meta(request_id=request_id)
           .build())
```

### Convenience Functions

For quick response creation:

```python
from backend.core.response_models import (
    success_response, error_response, paginated_response,
    turkish_success_response, turkish_error_response
)

# Quick success response
response = success_response(
    data=user_data,
    message="Kullanıcı oluşturuldu",
    request_id=request_id
)

# Turkish localized response
response = turkish_success_response(
    data=user_data,
    message_key="data_created",
    request_id=request_id
)

# Quick error response
response = error_response(
    message="Hata oluştu",
    errors=[error_detail],
    request_id=request_id
)
```

### FastAPI Endpoint Integration

```python
from fastapi import APIRouter, Request, HTTPException, status
from backend.core.response_models import SuccessResponse, ErrorResponse
from backend.core.exceptions import ValidationError, NotFoundError

router = APIRouter()

@router.post(
    "/users",
    response_model=SuccessResponse[UserResponse], 
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: UserCreate,
    request: Request
) -> SuccessResponse[UserResponse]:
    try:
        user = await user_service.create_user(user_data)
        
        return turkish_success_response(
            data=UserResponse.from_orm(user),
            message_key="data_created",
            custom_message=f"Kullanıcı {user.username} oluşturuldu",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except ValidationError as e:
        raise e  # Handled by global exception handler
    except Exception as e:
        raise BusinessLogicError(f"Kullanıcı oluşturma hatası: {str(e)}")
```

## 🔍 Error Types and Codes

### Standard Error Types

| Error Type | Code | HTTP Status | Description |
|------------|------|-------------|-------------|
| `VALIDATION_ERROR` | `validation_error` | 400 | Input validation failed |
| `AUTHENTICATION_ERROR` | `authentication_error` | 401 | Authentication required |
| `AUTHORIZATION_ERROR` | `authorization_error` | 403 | Insufficient permissions |
| `NOT_FOUND_ERROR` | `not_found_error` | 404 | Resource not found |
| `BUSINESS_LOGIC_ERROR` | `business_logic_error` | 422 | Business rule violation |
| `RATE_LIMIT_ERROR` | `rate_limit_error` | 429 | Rate limit exceeded |
| `INTERNAL_SERVER_ERROR` | `internal_server_error` | 500 | Unexpected server error |
| `EXTERNAL_SERVICE_ERROR` | `external_service_error` | 502 | External service failure |
| `DATABASE_ERROR` | `database_error` | 503 | Database operation failed |
| `MAINTENANCE_ERROR` | `maintenance_error` | 503 | Service under maintenance |

### Error Detail Structure

```json
{
  "code": "error_type_code",
  "message": "Human-readable error message in Turkish",
  "field": "field_name_for_validation_errors",
  "details": {
    "additional": "error context",
    "resource_id": "related_resource_identifier"
  }
}
```

### Validation Error Details

For validation errors, additional fields provide context:

```json
{
  "code": "validation_error",
  "message": "Bu alan zorunludur",
  "field": "email",
  "rejected_value": null,
  "constraint": "required",
  "details": {
    "expected_type": "string",
    "validation_rule": "email_format"
  }
}
```

## 🌐 Turkish Language Support

### Predefined Messages

The system includes predefined Turkish messages for common operations:

```python
TURKISH_MESSAGES = {
    "success": "İşlem başarıyla tamamlandı",
    "error": "Bir hata oluştu",
    "validation_error": "Veri doğrulama hatası",
    "not_found": "İstenen kaynak bulunamadı",
    "unauthorized": "Yetkilendirme gerekli",
    "forbidden": "Bu işlem için yetkiniz bulunmamaktadır",
    "data_created": "Veri başarıyla oluşturuldu",
    "data_updated": "Veri başarıyla güncellendi",
    "data_deleted": "Veri başarıyla silindi"
}
```

### Usage

```python
# Using message keys
response = turkish_success_response(
    data=data,
    message_key="data_created"
)

# Using custom messages
response = turkish_success_response(
    data=data,
    custom_message="Kullanıcı başarıyla kaydedildi"
)
```

## 📄 Pagination

### Pagination Metadata

```json
{
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 147,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

### Pagination Usage

```python
@router.get("/questions", response_model=PaginatedResponse[List[QuestionResponse]])
async def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    request: Request
):
    questions, total = await question_service.get_paginated_questions(page, page_size)
    
    return paginated_response(
        data=[QuestionResponse.from_orm(q) for q in questions],
        page=page,
        page_size=page_size,
        total_items=total,
        message="Sorular listelendi",
        request_id=getattr(request.state, 'request_id', None)
    )
```

## 🛡️ Middleware Integration

### Response Formatting Middleware

Automatically formats responses that don't use the standardized format:

```python
from backend.core.response_middleware import ResponseFormatterMiddleware

app.add_middleware(
    ResponseFormatterMiddleware,
    enable_auto_formatting=True,
    turkish_messages=True,
    excluded_paths=["/docs", "/redoc", "/openapi.json"]
)
```

### Exception Handlers

Global exception handlers ensure consistent error responses:

```python
from backend.core.exception_handlers import setup_exception_handlers

# Setup handlers
handlers = setup_exception_handlers(app, turkish_messages=True)
```

## 🔧 Validation and Testing

### Response Validators

Use the validation utilities to ensure response compliance:

```python
from backend.core.response_validators import ResponseValidator, ResponseTester

# Validate response structure
validator = ResponseValidator()
is_valid = validator.validate_response_structure(response_data)

# Test specific response types
tester = ResponseTester()
failures = tester.assert_success_response(response_data)
```

### Testing Utilities

```python
from backend.core.response_validators import ResponseTestCase

# Create test case
test_case = ResponseTestCase("API Response Tests")

# Test success response
test_case.test_response(
    response_data,
    "User Creation Success",
    "assert_success_response"
)

# Get test report
report = test_case.get_test_report()
```

### Command Line Tools

Use the response format checker tool:

```bash
# Check a response file
python tools/response_format_checker.py --file response.json

# Check API endpoint
python tools/response_format_checker.py --url https://api.example.com/users

# Generate test examples
python tools/api_response_examples.py --all --pretty
```

## 📊 Monitoring and Debugging

### Request Tracing

Every response includes metadata for debugging:

- `request_id`: Unique identifier for request tracing
- `processing_time_ms`: Processing time in milliseconds  
- `timestamp`: Response generation timestamp
- `api_version`: API version for compatibility tracking

### Logging Integration

The middleware automatically logs:

- Request details (method, URL, headers)
- Response status and processing time
- Error details and stack traces
- Performance metrics

## 🚀 Best Practices

### 1. Always Use Standardized Responses

```python
# ✅ Good
return turkish_success_response(
    data=result,
    message_key="data_created"
)

# ❌ Bad
return {"status": "ok", "result": result}
```

### 2. Provide Meaningful Error Messages

```python
# ✅ Good
raise ValidationError("E-posta formatı geçersiz", field="email")

# ❌ Bad  
raise ValidationError("Invalid input")
```

### 3. Include Request Context

```python
# ✅ Good
return success_response(
    data=data,
    request_id=getattr(request.state, 'request_id', None)
)
```

### 4. Use Appropriate Error Types

```python
# ✅ Good
if not user_exists:
    raise NotFoundError("Kullanıcı bulunamadı")

if not has_permission:
    raise AuthorizationError("Bu işlem için yetkiniz yok")
```

### 5. Validate Pagination Parameters

```python
# ✅ Good
if page < 1:
    raise ValidationError("Sayfa numarası 1'den küçük olamaz", field="page")

if page_size > 100:
    raise ValidationError("Sayfa boyutu 100'den büyük olamaz", field="page_size")
```

## 🔄 Migration Guide

### Existing Endpoints

To migrate existing endpoints:

1. **Update response model types:**
   ```python
   # Before
   @router.get("/users")
   async def get_users():
       return {"users": users}
   
   # After
   @router.get("/users", response_model=SuccessResponse[List[UserResponse]])
   async def get_users(request: Request):
       return success_response(
           data=[UserResponse.from_orm(u) for u in users],
           request_id=getattr(request.state, 'request_id', None)
       )
   ```

2. **Replace manual error handling:**
   ```python
   # Before
   if not user:
       raise HTTPException(status_code=404, detail="User not found")
   
   # After
   if not user:
       raise NotFoundError("Kullanıcı bulunamadı")
   ```

3. **Add pagination for list endpoints:**
   ```python
   # Before
   return {"questions": questions}
   
   # After
   return paginated_response(
       data=questions,
       page=page,
       page_size=page_size,
       total_items=total
   )
   ```

## 🧪 Testing Your Responses

### Unit Tests

```python
def test_user_creation_response():
    response_data = {
        "success": True,
        "status": "success",
        "message": "Kullanıcı oluşturuldu",
        "data": {"id": "u_123", "username": "test"}
    }
    
    tester = ResponseTester()
    failures = tester.assert_success_response(response_data)
    assert failures == []
```

### Integration Tests

```python
def test_api_endpoint_response_format():
    response = client.post("/api/v1/users", json=user_data)
    
    result = validate_api_endpoint_response(
        response.json(),
        "/api/v1/users",
        "success"
    )
    
    assert result["validation_passed"] == True
```

## 📚 Additional Resources

- [Response Models API Reference](../core/response_models.py)
- [Response Validators Documentation](../core/response_validators.py)
- [Exception Handlers Guide](../core/exception_handlers.py)
- [Middleware Configuration](../core/response_middleware.py)
- [Testing Utilities](../tests/test_response_format.py)

---

For questions or contributions to this guide, please contact the development team or create an issue in the project repository.