# KIRO2 API Error Codes Reference

Comprehensive reference for all error codes used in the KIRO2 Türkiye Üniversite Sınavları Hazırlık Platformu API.

## Table of Contents

- [HTTP Status Codes](#http-status-codes)
- [Authentication Errors (AUTH_xxx)](#authentication-errors-auth_xxx)
- [Validation Errors (VAL_xxx)](#validation-errors-val_xxx)
- [Exam Errors (EXAM_xxx)](#exam-errors-exam_xxx)
- [Learning Path Errors (LP_xxx)](#learning-path-errors-lp_xxx)
- [Permission Errors (PERM_xxx)](#permission-errors-perm_xxx)
- [Resource Errors (RES_xxx)](#resource-errors-res_xxx)
- [System Errors (SYS_xxx)](#system-errors-sys_xxx)
- [Error Response Format](#error-response-format)
- [Error Handling Best Practices](#error-handling-best-practices)

## HTTP Status Codes

KIRO2 API uses standard HTTP status codes to indicate the success or failure of API requests.

### 2xx Success

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request succeeded, no content to return |

### 4xx Client Errors

| Code | Name | Description | Common Causes |
|------|------|-------------|---------------|
| 400 | Bad Request | Invalid request data | Invalid JSON, business logic violation |
| 401 | Unauthorized | Authentication required or invalid | Missing/expired token, invalid credentials |
| 403 | Forbidden | Insufficient permissions | User lacks required role, IDOR attempt |
| 404 | Not Found | Resource doesn't exist | Invalid ID, deleted resource |
| 409 | Conflict | Resource conflict | Duplicate email, concurrent updates |
| 422 | Unprocessable Entity | Validation failed | Invalid data types, Pydantic validation error |
| 429 | Too Many Requests | Rate limit exceeded | Too many login attempts, API throttling |

### 5xx Server Errors

| Code | Name | Description | Action |
|------|------|-------------|--------|
| 500 | Internal Server Error | Unexpected server error | Retry request, contact support if persists |
| 502 | Bad Gateway | Upstream service failed | Retry request after delay |
| 503 | Service Unavailable | Service temporarily down | Retry with exponential backoff |
| 504 | Gateway Timeout | Request timeout | Reduce request complexity or batch size |

## Authentication Errors (AUTH_xxx)

### AUTH_001 - Invalid Credentials

**HTTP Status**: 401 Unauthorized

**Description**: Email or password is incorrect during login.

**Example Response**:
```json
{
  "detail": "Geçersiz e-posta veya şifre",
  "error_code": "AUTH_001",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Verify email and password are correct
- Check for typos in email/password
- Account may be locked after 5 failed attempts (wait 15 minutes)

---

### AUTH_002 - Token Expired

**HTTP Status**: 401 Unauthorized

**Description**: Access token or refresh token has expired.

**Example Response**:
```json
{
  "detail": "Geçersiz veya süresi dolmuş token",
  "error_code": "AUTH_002",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Access token expired: Use refresh token to get new access token
- Refresh token expired: User must re-authenticate (login again)

---

### AUTH_003 - Account Disabled

**HTTP Status**: 401 Unauthorized

**Description**: User account has been deactivated by admin.

**Example Response**:
```json
{
  "detail": "Hesap devre dışı bırakılmış",
  "error_code": "AUTH_003",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Contact support to reactivate account
- Check account status in admin dashboard

---

### AUTH_004 - Email Already Registered

**HTTP Status**: 400 Bad Request

**Description**: Email address is already registered in the system.

**Example Response**:
```json
{
  "detail": "Bu e-posta adresi zaten kayıtlı",
  "error_code": "AUTH_004",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Use different email address
- Try login if you already have an account
- Use password reset if you forgot password

---

### AUTH_005 - Weak Password

**HTTP Status**: 400 Bad Request

**Description**: Password doesn't meet security requirements.

**Example Response**:
```json
{
  "detail": "Şifre en az bir büyük harf içermelidir",
  "error_code": "AUTH_005",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*)
- Cannot be common password (password123, 12345678, etc.)

**Solution**:
- Use password that meets all requirements
- Example: `GucluSifre123!`

---

### AUTH_006 - Refresh Token Revoked

**HTTP Status**: 401 Unauthorized

**Description**: Refresh token has been revoked (logout, device removal, etc.).

**Example Response**:
```json
{
  "detail": "Refresh token iptal edilmiş",
  "error_code": "AUTH_006",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- User must re-authenticate (login again)
- Refresh token is invalidated after logout or device revocation

---

### AUTH_007 - Rate Limit Exceeded

**HTTP Status**: 429 Too Many Requests

**Description**: Too many failed login attempts from same IP or user.

**Example Response**:
```json
{
  "detail": "Çok fazla başarısız giriş denemesi. 15 dakika sonra tekrar deneyin.",
  "error_code": "AUTH_007",
  "timestamp": "2025-11-17T14:30:00Z",
  "retry_after": 900
}
```

**Rate Limits**:
- 5 failed login attempts per user → 15 minute block
- 10 failed attempts from same IP → 1 hour IP block

**Solution**:
- Wait for retry_after seconds before attempting again
- Verify credentials are correct
- Contact support if blocked unfairly

## Validation Errors (VAL_xxx)

### VAL_001 - Invalid Email Format

**HTTP Status**: 422 Unprocessable Entity

**Description**: Email address format is invalid.

**Example Response**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ],
  "error_code": "VAL_001"
}
```

**Solution**:
- Use valid email format: `user@example.com`
- Check for typos in email address

---

### VAL_002 - Missing Required Field

**HTTP Status**: 422 Unprocessable Entity

**Description**: Required field is missing from request body.

**Example Response**:
```json
{
  "detail": [
    {
      "loc": ["body", "ad_soyad"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "error_code": "VAL_002"
}
```

**Solution**:
- Include all required fields in request body
- Check API documentation for required fields

---

### VAL_003 - Invalid Data Type

**HTTP Status**: 422 Unprocessable Entity

**Description**: Field has incorrect data type.

**Example Response**:
```json
{
  "detail": [
    {
      "loc": ["body", "sinif_seviyesi"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ],
  "error_code": "VAL_003"
}
```

**Solution**:
- Use correct data type for field
- Check API documentation for field types

---

### VAL_004 - Value Out of Range

**HTTP Status**: 422 Unprocessable Entity

**Description**: Field value is outside allowed range.

**Example Response**:
```json
{
  "detail": [
    {
      "loc": ["body", "sinif_seviyesi"],
      "msg": "ensure this value is greater than or equal to 9",
      "type": "value_error.number.not_ge"
    }
  ],
  "error_code": "VAL_004"
}
```

**Solution**:
- Use value within allowed range
- For `sinif_seviyesi`: 9-12
- For `gunluk_calisma_hedefi`: 30-600 minutes

## Exam Errors (EXAM_xxx)

### EXAM_001 - Exam Not Found

**HTTP Status**: 404 Not Found

**Description**: Exam session with given ID doesn't exist.

**Example Response**:
```json
{
  "detail": "Sınav oturumu bulunamadı",
  "error_code": "EXAM_001",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Verify exam session ID is correct
- Check if exam was deleted
- Student may not have access to this exam

---

### EXAM_002 - Exam Already Completed

**HTTP Status**: 400 Bad Request

**Description**: Cannot modify a completed exam session.

**Example Response**:
```json
{
  "detail": "Sınav zaten tamamlanmış, değişiklik yapılamaz",
  "error_code": "EXAM_002",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Cannot submit answers to completed exam
- Create new exam session to retake exam

---

### EXAM_003 - Exam Time Expired

**HTTP Status**: 400 Bad Request

**Description**: Exam time limit has been exceeded.

**Example Response**:
```json
{
  "detail": "Sınav süresi dolmuş",
  "error_code": "EXAM_003",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Exam is automatically submitted when time expires
- Cannot submit additional answers
- View exam results and analytics

---

### EXAM_004 - Invalid Question ID

**HTTP Status**: 400 Bad Request

**Description**: Question ID doesn't exist in this exam.

**Example Response**:
```json
{
  "detail": "Geçersiz soru ID'si",
  "error_code": "EXAM_004",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Verify question ID is correct
- Question may have been removed from exam

---

### EXAM_005 - Answer Already Submitted

**HTTP Status**: 400 Bad Request

**Description**: Answer for this question has already been submitted.

**Example Response**:
```json
{
  "detail": "Bu soru için cevap zaten gönderilmiş",
  "error_code": "EXAM_005",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Use update answer endpoint to modify existing answer
- Cannot submit duplicate answers

## Learning Path Errors (LP_xxx)

### LP_001 - Learning Path Not Found

**HTTP Status**: 404 Not Found

**Description**: Learning path with given ID doesn't exist.

**Example Response**:
```json
{
  "detail": "Öğrenme yolu bulunamadı",
  "error_code": "LP_001",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Verify learning path ID is correct
- Create new learning path if deleted

---

### LP_002 - AI Agent Unavailable

**HTTP Status**: 503 Service Unavailable

**Description**: AI agent service is temporarily unavailable.

**Example Response**:
```json
{
  "detail": "AI servis geçici olarak kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
  "error_code": "LP_002",
  "timestamp": "2025-11-17T14:30:00Z",
  "retry_after": 60
}
```

**Solution**:
- Wait 60 seconds and retry
- Circuit breaker may be open due to service issues
- System will fallback to rule-based recommendations

---

### LP_003 - Invalid Student Profile

**HTTP Status**: 400 Bad Request

**Description**: Student profile data is incomplete or invalid.

**Example Response**:
```json
{
  "detail": "Öğrenci profili eksik veya geçersiz",
  "error_code": "LP_003",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Complete student profile with required fields
- Required: sinif_seviyesi, hedef_sinav, ogrenme_stili

## Permission Errors (PERM_xxx)

### PERM_001 - Insufficient Permissions

**HTTP Status**: 403 Forbidden

**Description**: User doesn't have required role for this action.

**Example Response**:
```json
{
  "detail": "Bu işlem için yetkiniz yok",
  "error_code": "PERM_001",
  "timestamp": "2025-11-17T14:30:00Z",
  "required_role": "admin"
}
```

**Solution**:
- Request elevated permissions from admin
- Action requires specific role (teacher, admin, etc.)

---

### PERM_002 - IDOR Attempt Detected

**HTTP Status**: 403 Forbidden

**Description**: Insecure Direct Object Reference (IDOR) attack detected.

**Example Response**:
```json
{
  "detail": "Bu kaynağa erişim yetkiniz yok",
  "error_code": "PERM_002",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**IDOR Prevention**:
- Students can only access their own data
- Parents can only access their children's data
- Teachers can only access their class data

**Solution**:
- Access only your own resources
- Request access through proper channels

---

### PERM_003 - Parent-Child Verification Failed

**HTTP Status**: 403 Forbidden

**Description**: Parent doesn't have verified relationship with student.

**Example Response**:
```json
{
  "detail": "Veli-öğrenci ilişkisi doğrulanmamış",
  "error_code": "PERM_003",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Complete parent-child verification process
- Student must approve parent access request
- Contact support for verification assistance

## Resource Errors (RES_xxx)

### RES_001 - Resource Not Found

**HTTP Status**: 404 Not Found

**Description**: Requested resource doesn't exist.

**Example Response**:
```json
{
  "detail": "Kaynak bulunamadı",
  "error_code": "RES_001",
  "timestamp": "2025-11-17T14:30:00Z",
  "resource_type": "student_profile",
  "resource_id": "std_123"
}
```

**Solution**:
- Verify resource ID is correct
- Resource may have been deleted
- Check if you have access to this resource

---

### RES_002 - Resource Conflict

**HTTP Status**: 409 Conflict

**Description**: Resource update conflict (concurrent modification).

**Example Response**:
```json
{
  "detail": "Kaynak eşzamanlı olarak değiştirilmiş. Lütfen sayfayı yenileyip tekrar deneyin.",
  "error_code": "RES_002",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Refresh resource to get latest version
- Retry update with fresh data
- Use optimistic locking (version field)

---

### RES_003 - Resource Quota Exceeded

**HTTP Status**: 429 Too Many Requests

**Description**: User has exceeded resource creation quota.

**Example Response**:
```json
{
  "detail": "Maksimum öğrenme yolu limiti aşıldı (max: 10)",
  "error_code": "RES_003",
  "timestamp": "2025-11-17T14:30:00Z",
  "quota_limit": 10,
  "current_usage": 10
}
```

**Solution**:
- Delete unused resources to free quota
- Upgrade to premium plan for higher limits
- Contact support for quota increase

## System Errors (SYS_xxx)

### SYS_001 - Database Connection Failed

**HTTP Status**: 500 Internal Server Error

**Description**: Cannot connect to database.

**Example Response**:
```json
{
  "detail": "Veritabanı bağlantısı başarısız",
  "error_code": "SYS_001",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- Retry request after 30 seconds
- Contact support if error persists
- Check system status page

---

### SYS_002 - Redis Cache Unavailable

**HTTP Status**: 503 Service Unavailable

**Description**: Redis cache service is unavailable.

**Example Response**:
```json
{
  "detail": "Önbellek servisi geçici olarak kullanılamıyor",
  "error_code": "SYS_002",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

**Solution**:
- System will fall back to direct database queries
- Performance may be degraded
- Retry after 60 seconds

---

### SYS_003 - External API Failure

**HTTP Status**: 502 Bad Gateway

**Description**: External API (YouTube, OpenAI, etc.) request failed.

**Example Response**:
```json
{
  "detail": "Dış servis geçici olarak kullanılamıyor",
  "error_code": "SYS_003",
  "timestamp": "2025-11-17T14:30:00Z",
  "service": "youtube_api"
}
```

**Solution**:
- Retry request after delay
- System may provide cached/fallback data
- Check external service status

---

### SYS_004 - Request Timeout

**HTTP Status**: 504 Gateway Timeout

**Description**: Request exceeded configured timeout limit.

**Example Response**:
```json
{
  "detail": "İstek zaman aşımına uğradı",
  "error_code": "SYS_004",
  "timestamp": "2025-11-17T14:30:00Z",
  "timeout_seconds": 300,
  "elapsed_seconds": 305,
  "suggestion": "Bu işlem uzun sürüyor. Lütfen daha küçük batch size kullanın."
}
```

**Timeout Limits by Endpoint**:
- Standard requests: 30 seconds
- File uploads: 300 seconds (5 minutes)
- Batch operations: 600 seconds (10 minutes)
- LLM/AI operations: 120 seconds (2 minutes)
- RAG operations: 90 seconds (1.5 minutes)

**Solution**:
- Reduce request complexity
- Use smaller batch sizes
- Split operation into multiple requests

## Error Response Format

### Standard Error Response

```json
{
  "detail": "Human-readable error message in Turkish",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

### Validation Error Response (422)

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error description",
      "type": "error_type"
    }
  ]
}
```

### Error with Additional Context

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-11-17T14:30:00Z",
  "retry_after": 60,
  "resource_id": "res_123",
  "suggestion": "Helpful suggestion for user"
}
```

## Error Handling Best Practices

### Client-Side Error Handling

```typescript
import axios, { AxiosError } from 'axios';

async function handleAPICall() {
  try {
    const response = await axios.post('/api/v1/auth/giris', data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;

      // Handle specific HTTP status codes
      if (axiosError.response?.status === 401) {
        // Unauthorized - redirect to login
        window.location.href = '/login';
      } else if (axiosError.response?.status === 422) {
        // Validation error - show field errors
        const errors = axiosError.response.data.detail;
        showValidationErrors(errors);
      } else if (axiosError.response?.status === 429) {
        // Rate limit - retry after delay
        const retryAfter = axiosError.response.data.retry_after || 60;
        setTimeout(() => handleAPICall(), retryAfter * 1000);
      } else if (axiosError.response?.status >= 500) {
        // Server error - show generic error
        showError('Sunucu hatası. Lütfen daha sonra tekrar deneyin.');
      }
    }
    throw error;
  }
}
```

### Retry Logic with Exponential Backoff

```typescript
async function retryWithBackoff(
  fn: () => Promise<any>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<any> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;

        // Don't retry client errors (4xx)
        if (status && status >= 400 && status < 500) {
          throw error;
        }

        // Retry server errors (5xx) with backoff
        if (i < maxRetries - 1) {
          const delay = baseDelay * Math.pow(2, i); // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      }
      throw error;
    }
  }
}
```

### Display User-Friendly Errors

```typescript
function getUserFriendlyError(error: any): string {
  if (!axios.isAxiosError(error)) {
    return 'Beklenmeyen bir hata oluştu';
  }

  const status = error.response?.status;
  const errorCode = error.response?.data?.error_code;
  const detail = error.response?.data?.detail;

  // Map error codes to user-friendly messages
  const errorMessages: Record<string, string> = {
    'AUTH_001': 'E-posta veya şifre hatalı',
    'AUTH_002': 'Oturumunuz sona erdi, lütfen tekrar giriş yapın',
    'AUTH_003': 'Hesabınız devre dışı bırakılmış',
    'AUTH_004': 'Bu e-posta adresi zaten kayıtlı',
    'AUTH_005': 'Şifreniz güvenlik gereksinimlerini karşılamıyor',
    'EXAM_001': 'Sınav bulunamadı',
    'EXAM_002': 'Sınav zaten tamamlanmış',
    'EXAM_003': 'Sınav süresi dolmuş',
    // ... add more mappings
  };

  if (errorCode && errorMessages[errorCode]) {
    return errorMessages[errorCode];
  }

  if (typeof detail === 'string') {
    return detail;
  }

  // Fallback to generic message based on status code
  if (status === 401) return 'Giriş gerekli';
  if (status === 403) return 'Bu işlem için yetkiniz yok';
  if (status === 404) return 'İstenen kaynak bulunamadı';
  if (status === 429) return 'Çok fazla istek gönderdiniz, lütfen bekleyin';
  if (status && status >= 500) return 'Sunucu hatası, lütfen daha sonra tekrar deneyin';

  return 'Bir hata oluştu';
}
```

## Testing Error Scenarios

### Unit Test Example (Jest)

```typescript
describe('Authentication Error Handling', () => {
  it('should handle invalid credentials (AUTH_001)', async () => {
    // Mock API response
    (axios.post as jest.Mock).mockRejectedValue({
      response: {
        status: 401,
        data: {
          detail: 'Geçersiz e-posta veya şifre',
          error_code: 'AUTH_001'
        }
      }
    });

    await expect(
      login('invalid@example.com', 'wrong_password')
    ).rejects.toThrow('Geçersiz e-posta veya şifre');
  });

  it('should handle validation errors (422)', async () => {
    (axios.post as jest.Mock).mockRejectedValue({
      response: {
        status: 422,
        data: {
          detail: [
            {
              loc: ['body', 'email'],
              msg: 'value is not a valid email address',
              type: 'value_error.email'
            }
          ]
        }
      }
    });

    await expect(
      register('invalid-email', 'Password123!')
    ).rejects.toThrow();
  });
});
```

## Related Documentation

- [Authentication Guide](./authentication.md)
- [API Reference (OpenAPI)](http://localhost:8000/docs)
- [Troubleshooting Guide](./troubleshooting.md)
- [HTTP Status Codes (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

## Support

For error-related issues:
- Search this reference for error code
- Check [Troubleshooting Guide](./troubleshooting.md)
- Review API logs for additional context
- Contact: support@kiro2.com
- GitHub Issues: https://github.com/kiro2/platform/issues

---

**Last Updated**: 2025-11-17
**Version**: 1.0.0
**Author**: KIRO2 Platform Team
